"""
fatturapa_mcp.tools.vies
~~~~~~~~~~~~~~~~~~~~~~~~~
MCP tool: verify_piva_vies — verifies a VAT number against the EU VIES REST API.
"""

from typing import TypedDict

import httpx

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
) -> VerifyPivaViesResult:
    """Verify a VAT number against the EU VIES (VAT Information Exchange System).

    Calls the official EU VIES REST endpoint with a configurable timeout.
    On timeout or service unavailability, returns a degraded response with
    source="unavailable" rather than raising — the caller must handle this case.

    Args:
        country_code: Two-letter ISO 3166-1 alpha-2 country code (e.g., "IT").
        vat_number: VAT number without the country prefix (e.g., "12345678901").

    Returns:
        A VerifyPivaViesResult with keys:
            valid (bool): Whether VIES confirmed the VAT number as active.
            name (str | None): Registered business name, if disclosed by VIES.
            address (str | None): Registered address, if disclosed by VIES.
            source (str): "vies" if live response, "unavailable" if service down.
    """
    url = _VIES_URL.format(
        country_code=country_code.upper(),
        vat_number=vat_number,
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.get(url)
            response.raise_for_status()
            data: dict[str, object] = response.json()
    except (httpx.HTTPError, httpx.TimeoutException, ValueError):
        return VerifyPivaViesResult(
            valid=False,
            name=None,
            address=None,
            source="unavailable",
        )

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

    return VerifyPivaViesResult(
        valid=is_valid,
        name=name,
        address=address,
        source="vies",
    )
