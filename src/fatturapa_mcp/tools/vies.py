"""
fatturapa_mcp.tools.vies
~~~~~~~~~~~~~~~~~~~~~~~~~
MCP tool: verify_piva_vies — verifies a VAT number against the EU VIES REST API.
"""

import time
from typing import Any, TypedDict

import httpx
from mcp.server.fastmcp import Context

from fatturapa_mcp.utils.logging import ctx_log, elapsed_ms

# FastMCP injects a Context[ServerSessionT, LifespanContextT, RequestT]; the type
# parameters are internal to the server session and not needed by tool implementations.
_Ctx = Context[Any, Any, Any]

# EU VIES REST API v2 — https://ec.europa.eu/taxation_customs/vies/
_VIES_URL = (
    "https://ec.europa.eu/taxation_customs/vies/rest-api"
    "/ms/{country_code}/vat/{vat_number}"
)
_TIMEOUT_SECONDS = 10.0
# VIES returns "---" when the member state does not disclose the field.
_UNDISCLOSED = "---"


class VerifyPivaViesResult(TypedDict):
    """Structured result returned by verify_piva_vies."""

    valid: bool
    name: str | None
    address: str | None
    source: str


async def verify_piva_vies(
    country_code: str,
    vat_number: str,
    ctx: _Ctx | None = None,
) -> VerifyPivaViesResult:
    """Verify a VAT number against the EU VIES (VAT Information Exchange System).

    Calls the official EU VIES REST endpoint with a configurable timeout.
    On timeout or service unavailability, returns a degraded response with
    source="unavailable" rather than raising — the caller must handle this case.

    Args:
        country_code: Two-letter ISO 3166-1 alpha-2 country code (e.g., "IT").
        vat_number: VAT number without the country prefix (e.g., "12345678901").
        ctx: Optional MCP context for structured log emission.

    Returns:
        A VerifyPivaViesResult with keys:
            valid (bool): Whether VIES confirmed the VAT number as active.
            name (str | None): Registered business name, if disclosed by VIES.
            address (str | None): Registered address, if disclosed by VIES.
            source (str): "vies" if live response, "unavailable" if service down.
    """
    start = time.monotonic()
    await ctx_log(ctx, "verify_piva_vies.start", country_code=country_code.upper())

    # Step 1 — prepare request
    if ctx:
        await ctx.report_progress(1, 4)

    url = _VIES_URL.format(country_code=country_code.upper(), vat_number=vat_number)

    # Step 2 — network call
    if ctx:
        await ctx.report_progress(2, 4)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.get(url)
            response.raise_for_status()
            data: dict[str, object] = response.json()
    except (httpx.HTTPError, httpx.TimeoutException, ValueError):
        result = VerifyPivaViesResult(
            valid=False, name=None, address=None, source="unavailable"
        )
        await ctx_log(
            ctx,
            "verify_piva_vies.done",
            level="warning",
            valid=False,
            source="unavailable",
            elapsed_ms=elapsed_ms(start),
        )
        return result

    # Step 3 — parse response
    if ctx:
        await ctx.report_progress(3, 4)

    is_valid = bool(data.get("isValid", False))
    raw_name = data.get("name")
    raw_address = data.get("address")
    name = (
        str(raw_name)
        if isinstance(raw_name, str) and raw_name != _UNDISCLOSED
        else None
    )
    address = (
        str(raw_address)
        if isinstance(raw_address, str) and raw_address != _UNDISCLOSED
        else None
    )
    result = VerifyPivaViesResult(
        valid=is_valid, name=name, address=address, source="vies"
    )
    await ctx_log(
        ctx,
        "verify_piva_vies.done",
        valid=is_valid,
        has_name=name is not None,
        has_address=address is not None,
        elapsed_ms=elapsed_ms(start),
    )

    # Step 4 — completion
    if ctx:
        await ctx.report_progress(4, 4)

    return result
