"""
fatturapa_mcp.tools.report
~~~~~~~~~~~~~~~~~~~~~~~~~~~
MCP tool: generate_invoice_report — aggregates FatturaPA invoices into a report.
"""

import time
from datetime import UTC, datetime
from typing import Any, TypeAlias, TypedDict

from mcp.server.fastmcp import Context

from fatturapa_mcp.tools.anomalies import FindAnomaliesResult, find_invoice_anomalies
from fatturapa_mcp.tools.extract import ExtractResult, extract_invoice_data
from fatturapa_mcp.utils.logging import ctx_log, elapsed_ms

# FastMCP injects a Context[ServerSessionT, LifespanContextT, RequestT]; the type
# parameters are internal to the server session and not needed by tool implementations.
_Ctx = Context[Any, Any, Any]

# Processed per-invoice pair: (extracted fields, anomaly results).
_InvoicePair: TypeAlias = tuple[ExtractResult, FindAnomaliesResult]


class PartyEntry(TypedDict):
    """Aggregated supplier or customer entry across all invoices."""

    name: str
    piva: str
    invoice_count: int
    total_amount: float


class BySeverity(TypedDict):
    """Anomaly counts split by severity level."""

    error: int
    warning: int


class AnomaliesSummary(TypedDict):
    """Aggregated anomaly statistics across the full invoice batch."""

    total_anomalies: int
    clean_invoices: int
    by_severity: BySeverity
    by_code: dict[str, int]


class InvoiceReportResult(TypedDict):
    """Structured result returned by generate_invoice_report."""

    title: str
    generated_at: str
    total_invoices: int
    valid_invoices: int
    invalid_invoices: int
    total_amount: float
    total_vat: float
    currency: str
    suppliers: list[PartyEntry]
    customers: list[PartyEntry]
    anomalies_summary: AnomaliesSummary
    errors: list[str]


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _compute_vat(extract: ExtractResult) -> float:
    """Compute total VAT from line items (sum of total_price * vat_rate / 100)."""
    total = 0.0
    for item in extract["line_items"]:
        price = item["total_price"]
        rate = item["vat_rate"]
        if price is not None and rate is not None:
            total += price * rate / 100
    return round(total, 2)


def _update_party(
    registry: dict[str, PartyEntry],
    name: str | None,
    piva: str | None,
    amount: float,
) -> None:
    """Upsert a party entry in the registry, accumulating invoice count and amount."""
    key = f"{name or ''}|{piva or ''}"
    if key in registry:
        registry[key]["invoice_count"] += 1
        registry[key]["total_amount"] = round(registry[key]["total_amount"] + amount, 2)
    else:
        registry[key] = {
            "name": name or "",
            "piva": piva or "",
            "invoice_count": 1,
            "total_amount": round(amount, 2),
        }


def _build_anomalies_summary(
    anomaly_results: list[FindAnomaliesResult],
) -> AnomaliesSummary:
    """Build aggregated anomaly statistics from a list of per-invoice results."""
    total = 0
    clean = 0
    errors = 0
    warnings = 0
    by_code: dict[str, int] = {}
    for ar in anomaly_results:
        total += ar["anomalies_found"]
        if ar["is_clean"]:
            clean += 1
        for a in ar["anomalies"]:
            if a["severity"] == "error":
                errors += 1
            else:
                warnings += 1
            by_code[a["code"]] = by_code.get(a["code"], 0) + 1
    return {
        "total_anomalies": total,
        "clean_invoices": clean,
        "by_severity": {"error": errors, "warning": warnings},
        "by_code": by_code,
    }


def _aggregate(
    pairs: list[_InvoicePair],
    parse_errors: list[str],
    title: str | None,
) -> InvoiceReportResult:
    """Build the final InvoiceReportResult from processed pairs and parse errors."""
    suppliers: dict[str, PartyEntry] = {}
    customers: dict[str, PartyEntry] = {}
    total_amount = 0.0
    total_vat = 0.0
    currency = "EUR"
    anomaly_results: list[FindAnomaliesResult] = []
    for extract, anomalies in pairs:
        raw = extract["total_amount"]
        amount = raw if raw is not None else 0.0
        total_amount += amount
        total_vat += _compute_vat(extract)
        if extract["currency"]:
            currency = extract["currency"]
        _update_party(
            suppliers, extract["supplier_name"], extract["supplier_piva"], amount
        )
        _update_party(
            customers, extract["customer_name"], extract["customer_piva"], amount
        )
        anomaly_results.append(anomalies)
    return {
        "title": title or "Invoice Report",
        "generated_at": datetime.now(UTC).isoformat(),
        "total_invoices": len(pairs) + len(parse_errors),
        "valid_invoices": len(pairs),
        "invalid_invoices": len(parse_errors),
        "total_amount": round(total_amount, 2),
        "total_vat": round(total_vat, 2),
        "currency": currency,
        "suppliers": list(suppliers.values()),
        "customers": list(customers.values()),
        "anomalies_summary": _build_anomalies_summary(anomaly_results),
        "errors": parse_errors,
    }


# ---------------------------------------------------------------------------
# Public tool
# ---------------------------------------------------------------------------


async def generate_invoice_report(
    xml_contents: list[str],
    title: str | None = None,
    ctx: _Ctx | None = None,
) -> InvoiceReportResult:
    """Aggregate a batch of FatturaPA XML documents into a structured report.

    Processes each invoice through extract_invoice_data and
    find_invoice_anomalies, then aggregates the results into totals,
    supplier/customer breakdowns, and an anomaly summary.  Documents that
    cannot be parsed are counted separately in the *errors* list; they do not
    affect the monetary totals.  Never logs or persists XML content.

    Progress notifications: one step per invoice (1..N), then a final step
    (N+1) for the aggregation phase.

    Args:
        xml_contents: List of raw FatturaPA XML strings to process.
        title: Optional report title; defaults to ``"Invoice Report"``.
        ctx: Optional MCP context for structured log emission.

    Returns:
        An InvoiceReportResult TypedDict with aggregated statistics, party
        breakdowns (suppliers/customers), and an anomaly summary.
    """
    start = time.monotonic()
    await ctx_log(ctx, "generate_invoice_report.start", invoice_count=len(xml_contents))

    total_steps = len(xml_contents) + 1
    pairs: list[_InvoicePair] = []
    parse_errors: list[str] = []

    for i, xml in enumerate(xml_contents, start=1):
        if ctx:
            await ctx.report_progress(i, total_steps)
        try:
            extract = await extract_invoice_data(xml)
            anomalies = await find_invoice_anomalies(xml)
            pairs.append((extract, anomalies))
        except Exception as exc:  # report must survive unparseable invoices
            parse_errors.append(f"Invoice {i}: {type(exc).__name__}: {exc}")

    if ctx:
        await ctx.report_progress(total_steps, total_steps)

    result = _aggregate(pairs, parse_errors, title)
    await ctx_log(
        ctx,
        "generate_invoice_report.done",
        total_invoices=result["total_invoices"],
        valid_invoices=result["valid_invoices"],
        elapsed_ms=elapsed_ms(start),
    )
    return result
