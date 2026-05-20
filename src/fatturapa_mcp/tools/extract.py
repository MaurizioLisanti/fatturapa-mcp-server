"""
fatturapa_mcp.tools.extract
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
MCP tool: extract_invoice_data — extracts key fields from a valid FatturaPA XML.
"""

import time
from typing import Any, TypedDict

from lxml import etree
from mcp.server.fastmcp import Context

from fatturapa_mcp.tools.validate import _SAFE_PARSER
from fatturapa_mcp.utils.logging import ctx_log, elapsed_ms

# FastMCP injects a Context[ServerSessionT, LifespanContextT, RequestT]; the type
# parameters are internal to the server session and not needed by tool implementations.
_Ctx = Context[Any, Any, Any]


class LineItem(TypedDict):
    """One line entry from DatiBeniServizi/DettaglioLinee."""

    line_number: int | None
    description: str | None
    quantity: float | None
    unit_price: float | None
    total_price: float | None
    vat_rate: float | None


class ExtractResult(TypedDict):
    """Structured result returned by extract_invoice_data."""

    invoice_number: str | None
    invoice_date: str | None
    document_type: str | None
    currency: str | None
    total_amount: float | None
    supplier_name: str | None
    supplier_piva: str | None
    supplier_tax_code: str | None
    customer_name: str | None
    customer_piva: str | None
    customer_tax_code: str | None
    line_items: list[LineItem]


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


def _parse_int(text: str | None) -> int | None:
    """Convert a decimal string to int; return None if absent or unparseable."""
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _extract_name(parent: etree._Element | None, party_path: str) -> str | None:
    """Return Denominazione, or Nome+Cognome, from a party's DatiAnagrafici."""
    if parent is None:
        return None
    da = parent.find(f"{party_path}/DatiAnagrafici")
    if da is None:
        return None
    denominazione = da.findtext("Anagrafica/Denominazione")
    if denominazione:
        return denominazione
    nome = da.findtext("Anagrafica/Nome") or ""
    cognome = da.findtext("Anagrafica/Cognome") or ""
    full = f"{nome} {cognome}".strip()
    return full or None


def _extract_piva(parent: etree._Element | None, party_path: str) -> str | None:
    """Return IdPaese+IdCodice concatenated from a party's IdFiscaleIVA, or None."""
    if parent is None:
        return None
    da = parent.find(f"{party_path}/DatiAnagrafici")
    if da is None:
        return None
    paese = da.findtext("IdFiscaleIVA/IdPaese") or ""
    codice = da.findtext("IdFiscaleIVA/IdCodice")
    if not codice:
        return None
    return f"{paese}{codice}".strip() or None


def _extract_tax_code(parent: etree._Element | None, party_path: str) -> str | None:
    """Return CodiceFiscale from a party's DatiAnagrafici, or None."""
    if parent is None:
        return None
    da = parent.find(f"{party_path}/DatiAnagrafici")
    return da.findtext("CodiceFiscale") if da is not None else None


def _extract_total(
    dgd: etree._Element | None,
    body: etree._Element | None,
) -> float | None:
    """Return total amount: ImportoTotaleDocumento or sum of DatiRiepilogo entries."""
    if dgd is not None:
        total = _parse_float(dgd.findtext("ImportoTotaleDocumento"))
        if total is not None:
            return total
    if body is None:
        return None
    amounts = [
        _parse_float(el.findtext("ImponibileImporto"))
        for el in body.findall("DatiBeniServizi/DatiRiepilogo")
    ]
    taxes = [
        _parse_float(el.findtext("Imposta"))
        for el in body.findall("DatiBeniServizi/DatiRiepilogo")
    ]
    summands = [v for v in amounts + taxes if v is not None]
    return sum(summands) if summands else None


def _extract_line_items(bodies: list[etree._Element]) -> list[LineItem]:
    """Aggregate line items from all FatturaElettronicaBody sections."""
    items: list[LineItem] = []
    for body in bodies:
        for line in body.findall("DatiBeniServizi/DettaglioLinee"):
            items.append(
                {
                    "line_number": _parse_int(line.findtext("NumeroLinea")),
                    "description": line.findtext("Descrizione"),
                    "quantity": _parse_float(line.findtext("Quantita")),
                    "unit_price": _parse_float(line.findtext("PrezzoUnitario")),
                    "total_price": _parse_float(line.findtext("PrezzoTotale")),
                    "vat_rate": _parse_float(line.findtext("AliquotaIVA")),
                }
            )
    return items


# ---------------------------------------------------------------------------
# Public tool
# ---------------------------------------------------------------------------


async def extract_invoice_data(
    xml_content: str,
    ctx: _Ctx | None = None,
) -> ExtractResult:
    """Extract key fields from a validated FatturaPA XML document.

    Parses the header and first body section to return structured invoice
    metadata. Never logs or persists XML content — only derived values are
    returned. Missing fields yield None rather than raising KeyError.

    Args:
        xml_content: Raw XML string of a validated FatturaPA document.
        ctx: Optional MCP context for structured log emission.

    Returns:
        An ExtractResult TypedDict with supplier, customer, invoice header
        fields, and aggregated line_items from all body sections.

    Raises:
        lxml.etree.XMLSyntaxError: If xml_content is not well-formed XML.
    """
    start = time.monotonic()
    await ctx_log(ctx, "extract_invoice_data.start", xml_length=len(xml_content))

    # Step 1 — parse input
    if ctx:
        await ctx.report_progress(1, 3)

    root = etree.fromstring(xml_content.encode("utf-8"), _SAFE_PARSER)

    # Step 2 — extract fields
    if ctx:
        await ctx.report_progress(2, 3)

    header = root.find("FatturaElettronicaHeader")
    bodies = root.findall("FatturaElettronicaBody")
    body = bodies[0] if bodies else None
    dgd = body.find("DatiGenerali/DatiGeneraliDocumento") if body is not None else None
    result: ExtractResult = {
        "invoice_number": dgd.findtext("Numero") if dgd is not None else None,
        "invoice_date": dgd.findtext("Data") if dgd is not None else None,
        "document_type": dgd.findtext("TipoDocumento") if dgd is not None else None,
        "currency": dgd.findtext("Divisa") if dgd is not None else None,
        "total_amount": _extract_total(dgd, body),
        "supplier_name": _extract_name(header, "CedentePrestatore"),
        "supplier_piva": _extract_piva(header, "CedentePrestatore"),
        "supplier_tax_code": _extract_tax_code(header, "CedentePrestatore"),
        "customer_name": _extract_name(header, "CessionarioCommittente"),
        "customer_piva": _extract_piva(header, "CessionarioCommittente"),
        "customer_tax_code": _extract_tax_code(header, "CessionarioCommittente"),
        "line_items": _extract_line_items(bodies),
    }
    # Step 3 — completion
    if ctx:
        await ctx.report_progress(3, 3)

    await ctx_log(
        ctx,
        "extract_invoice_data.done",
        has_invoice_number=result["invoice_number"] is not None,
        line_count=len(result["line_items"]),
        elapsed_ms=elapsed_ms(start),
    )
    return result
