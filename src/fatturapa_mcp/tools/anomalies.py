"""
fatturapa_mcp.tools.anomalies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
MCP tool: find_invoice_anomalies — detects inconsistencies in a FatturaPA XML.
"""

import time
from datetime import date
from pathlib import Path
from typing import Any, Literal, TypedDict

from lxml import etree
from mcp.server.fastmcp import Context

from fatturapa_mcp.tools.check_piva import check_piva
from fatturapa_mcp.tools.validate import _SAFE_PARSER
from fatturapa_mcp.utils.logging import ctx_log, elapsed_ms
from fatturapa_mcp.utils.roots import get_allowed_roots, is_path_allowed

# FastMCP injects a Context[ServerSessionT, LifespanContextT, RequestT]; the type
# parameters are internal to the server session and not needed by tool implementations.
_Ctx = Context[Any, Any, Any]

# Maximum allowed rounding gap for monetary comparisons (€0.02).
_TOLERANCE: float = 0.02


class AnomalyResult(TypedDict):
    """One detected anomaly in the invoice."""

    code: str
    severity: Literal["error", "warning"]
    description: str
    detail: str


class FindAnomaliesResult(TypedDict):
    """Structured result returned by find_invoice_anomalies."""

    anomalies_found: int
    anomalies: list[AnomalyResult]
    warnings: list[AnomalyResult]
    errors: list[AnomalyResult]
    is_clean: bool


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _parse_float(text: str | None) -> float | None:
    """Convert a decimal string to float; return None if absent or unparseable."""
    if text is None:
        return None
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return None


def _anomaly(
    code: str,
    severity: Literal["error", "warning"],
    description: str,
    detail: str,
) -> AnomalyResult:
    """Build an AnomalyResult dict from its four fields."""
    return {
        "code": code,
        "severity": severity,
        "description": description,
        "detail": detail,
    }


def _check_total_mismatch(
    dgd: etree._Element | None,
    body: etree._Element | None,
) -> AnomalyResult | None:
    """Return TOTAL_MISMATCH if ImportoTotaleDocumento != sum(DatiRiepilogo)."""
    if dgd is None or body is None:
        return None
    declared = _parse_float(dgd.findtext("ImportoTotaleDocumento"))
    if declared is None:
        return None
    summands: list[float] = []
    for r in body.findall("DatiBeniServizi/DatiRiepilogo"):
        imp = _parse_float(r.findtext("ImponibileImporto"))
        tax = _parse_float(r.findtext("Imposta"))
        if imp is not None:
            summands.append(imp)
        if tax is not None:
            summands.append(tax)
    computed = sum(summands)
    if abs(declared - computed) > _TOLERANCE:
        return _anomaly(
            "TOTAL_MISMATCH",
            "error",
            "Totale documento incoerente",
            f"ImportoTotaleDocumento={declared}, somma righe={computed:.2f}",
        )
    return None


def _check_vat_mismatch(body: etree._Element | None) -> list[AnomalyResult]:
    """Return VAT_MISMATCH for each DatiRiepilogo where aliquota*imponibile != imposta.

    Only rows where all three numeric fields are present are checked.
    """
    if body is None:
        return []
    results: list[AnomalyResult] = []
    for i, r in enumerate(body.findall("DatiBeniServizi/DatiRiepilogo"), start=1):
        aliquota = _parse_float(r.findtext("AliquotaIVA"))
        imponibile = _parse_float(r.findtext("ImponibileImporto"))
        imposta = _parse_float(r.findtext("Imposta"))
        if aliquota is None or imponibile is None or imposta is None:
            continue
        expected = round(aliquota * imponibile / 100, 2)
        if abs(expected - imposta) > _TOLERANCE:
            results.append(
                _anomaly(
                    "VAT_MISMATCH",
                    "error",
                    "IVA incoerente",
                    f"DatiRiepilogo[{i}]: attesa={expected:.2f},"
                    f" dichiarata={imposta:.2f}",
                )
            )
    return results


def _check_future_date(dgd: etree._Element | None) -> AnomalyResult | None:
    """Return FUTURE_DATE if the invoice date is strictly after today."""
    if dgd is None:
        return None
    raw = dgd.findtext("Data")
    if not raw:
        return None
    try:
        invoice_date = date.fromisoformat(raw.strip())
    except ValueError:
        return None
    if invoice_date > date.today():
        return _anomaly(
            "FUTURE_DATE",
            "warning",
            "Data fattura futura",
            f"Data={raw.strip()}, oggi={date.today().isoformat()}",
        )
    return None


def _check_dest_code(header: etree._Element | None) -> AnomalyResult | None:
    """Return MISSING_DEST_CODE if CodiceDestinatario is absent or '0000000'."""
    if header is None:
        return None
    code: str | None = header.findtext("DatiTrasmissione/CodiceDestinatario")
    if code is not None and code.strip() not in ("", "0000000"):
        return None
    detail = (
        f"CodiceDestinatario={code!r}"
        if code is not None
        else "CodiceDestinatario assente"
    )
    return _anomaly(
        "MISSING_DEST_CODE",
        "warning",
        "Codice destinatario mancante o sospetto",
        detail,
    )


def _check_incomplete_lines(body: etree._Element | None) -> list[AnomalyResult]:
    """Return INCOMPLETE_LINE for each DettaglioLinee missing description or amount."""
    if body is None:
        return []
    results: list[AnomalyResult] = []
    for line in body.findall("DatiBeniServizi/DettaglioLinee"):
        num = line.findtext("NumeroLinea") or "?"
        desc = line.findtext("Descrizione")
        amount = line.findtext("PrezzoTotale")
        if not desc or not amount:
            missing = ", ".join(
                name
                for name, val in [("Descrizione", desc), ("PrezzoTotale", amount)]
                if not val
            )
            results.append(
                _anomaly(
                    "INCOMPLETE_LINE",
                    "warning",
                    "Riga fattura incompleta",
                    f"Linea {num}: campi mancanti: {missing}",
                )
            )
    return results


def _check_negative_amount(dgd: etree._Element | None) -> AnomalyResult | None:
    """Return NEGATIVE_AMOUNT if total < 0 and document type is not TD04."""
    if dgd is None:
        return None
    amount = _parse_float(dgd.findtext("ImportoTotaleDocumento"))
    doc_type = dgd.findtext("TipoDocumento") or ""
    if amount is not None and amount < 0 and doc_type != "TD04":
        return _anomaly(
            "NEGATIVE_AMOUNT",
            "warning",
            "Importo negativo non giustificato",
            f"ImportoTotaleDocumento={amount}, TipoDocumento={doc_type!r}",
        )
    return None


def _check_missing_payment(bodies: list[etree._Element]) -> AnomalyResult | None:
    """Return MISSING_PAYMENT if no DatiPagamento section is found in any body."""
    for body in bodies:
        if body.find("DatiPagamento") is not None:
            return None
    return _anomaly(
        "MISSING_PAYMENT",
        "warning",
        "Pagamento mancante",
        "Nessun elemento DatiPagamento trovato nel documento",
    )


async def _run_party_checks(header: etree._Element | None) -> list[AnomalyResult]:
    """Validate Italian P.IVA (checksum only) for supplier and customer."""
    if header is None:
        return []
    results: list[AnomalyResult] = []
    parties: list[tuple[str, str]] = [
        ("CedentePrestatore", "fornitore"),
        ("CessionarioCommittente", "cliente"),
    ]
    for party_path, role in parties:
        da = header.find(f"{party_path}/DatiAnagrafici")
        if da is None:
            continue
        paese = da.findtext("IdFiscaleIVA/IdPaese") or ""
        codice = da.findtext("IdFiscaleIVA/IdCodice")
        if paese.upper() != "IT" or not codice:
            continue
        piva_result = await check_piva(f"IT{codice}", ctx=None)
        if not piva_result["valid"]:
            reason = piva_result["reason"] or "checksum error"
            results.append(
                _anomaly(
                    "INVALID_PIVA",
                    "error",
                    "P.IVA formalmente non valida",
                    f"P.IVA {role} ({codice}): {reason}",
                )
            )
    return results


def _run_document_checks(
    dgd: etree._Element | None,
    header: etree._Element | None,
    bodies: list[etree._Element],
    body: etree._Element | None,
) -> list[AnomalyResult]:
    """Run document-level checks: totals, VAT, date, dest code, amounts, payment."""
    collected: list[AnomalyResult] = []
    total_check = _check_total_mismatch(dgd, body)
    if total_check is not None:
        collected.append(total_check)
    collected += _check_vat_mismatch(body)
    future_check = _check_future_date(dgd)
    if future_check is not None:
        collected.append(future_check)
    dest_check = _check_dest_code(header)
    if dest_check is not None:
        collected.append(dest_check)
    neg_check = _check_negative_amount(dgd)
    if neg_check is not None:
        collected.append(neg_check)
    payment_check = _check_missing_payment(bodies)
    if payment_check is not None:
        collected.append(payment_check)
    return collected


def _build_result(collected: list[AnomalyResult]) -> FindAnomaliesResult:
    """Assemble the final FindAnomaliesResult from a flat anomaly list."""
    errors = [a for a in collected if a["severity"] == "error"]
    warnings = [a for a in collected if a["severity"] == "warning"]
    return {
        "anomalies_found": len(collected),
        "anomalies": collected,
        "warnings": warnings,
        "errors": errors,
        "is_clean": len(collected) == 0,
    }


# ---------------------------------------------------------------------------
# Public tool
# ---------------------------------------------------------------------------


async def find_invoice_anomalies(
    xml_content: str = "",
    ctx: _Ctx | None = None,
    file_path: str | None = None,
) -> FindAnomaliesResult:
    """Detect inconsistencies and anomalies in a FatturaPA XML document.

    Checks eight anomaly categories: document total mismatch, VAT calculation
    error, future invoice date, invalid Italian P.IVA checksum, missing or
    suspicious destination code, incomplete line items, unjustified negative
    amount, and missing payment data.  Never logs or persists XML content.

    When *file_path* is given the document is read from disk; the path is
    checked against the roots configured in ``FATTURAPA_ALLOWED_ROOTS`` before
    any read is attempted.  Pass *xml_content* directly to skip file I/O.

    Args:
        xml_content: Raw XML string of the FatturaPA document.
        ctx: Optional MCP context for structured log emission.
        file_path: Optional filesystem path to read the document from.
            Checked against allowed roots before reading.

    Returns:
        A FindAnomaliesResult with keys:
            anomalies_found (int): Total number of anomalies detected.
            anomalies (list): All anomaly records.
            warnings (list): Only warning-severity anomalies.
            errors (list): Only error-severity anomalies.
            is_clean (bool): True when no anomalies are found.

    Raises:
        PermissionError: If *file_path* is outside the configured allowed roots.
        ValueError: If neither *xml_content* nor *file_path* is provided.
        lxml.etree.XMLSyntaxError: If the XML is not well-formed.
    """
    if file_path is not None:
        if not is_path_allowed(file_path, get_allowed_roots()):
            raise PermissionError("Access denied: path is outside allowed roots.")
        xml_content = Path(file_path).read_text(encoding="utf-8")
    elif not xml_content:
        raise ValueError("Provide either xml_content or file_path.")

    start = time.monotonic()
    await ctx_log(ctx, "find_invoice_anomalies.start", xml_length=len(xml_content))

    # Step 1 — parse XML
    if ctx:
        await ctx.report_progress(1, 4)
    root = etree.fromstring(xml_content.encode("utf-8"), _SAFE_PARSER)
    header = root.find("FatturaElettronicaHeader")
    bodies = root.findall("FatturaElettronicaBody")
    body = bodies[0] if bodies else None
    dgd = body.find("DatiGenerali/DatiGeneraliDocumento") if body is not None else None

    # Step 2 — document-level checks
    if ctx:
        await ctx.report_progress(2, 4)
    collected = _run_document_checks(dgd, header, bodies, body)

    # Step 3 — line-item checks
    if ctx:
        await ctx.report_progress(3, 4)
    collected += _check_incomplete_lines(body)

    # Step 4 — party P.IVA checks
    if ctx:
        await ctx.report_progress(4, 4)
    collected += await _run_party_checks(header)

    result = _build_result(collected)
    await ctx_log(
        ctx,
        "find_invoice_anomalies.done",
        anomalies_found=result["anomalies_found"],
        is_clean=result["is_clean"],
        elapsed_ms=elapsed_ms(start),
    )
    return result
