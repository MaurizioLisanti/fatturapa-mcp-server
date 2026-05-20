"""
fatturapa_mcp.tools.check_piva
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
MCP tool: check_piva — validates an Italian VAT number (P.IVA) via checksum.
"""

import time
from typing import Any, TypedDict

from mcp.server.fastmcp import Context

from fatturapa_mcp.utils.logging import ctx_log, elapsed_ms

# FastMCP injects a Context[ServerSessionT, LifespanContextT, RequestT]; the type
# parameters are internal to the server session and not needed by tool implementations.
_Ctx = Context[Any, Any, Any]


class CheckPivaResult(TypedDict):
    """Structured result returned by check_piva."""

    valid: bool
    piva: str
    reason: str | None


async def check_piva(
    piva: str,
    ctx: _Ctx | None = None,
) -> CheckPivaResult:
    """Validate an Italian VAT number using the official MEF checksum algorithm.

    Performs format validation and the Ministry of Economy checksum algorithm.
    No network call — fully local computation.

    Args:
        piva: Italian VAT number string. May include or omit the "IT" prefix.
              Expected: 11 digits after stripping prefix and whitespace.
        ctx: Optional MCP context for structured log emission.

    Returns:
        A CheckPivaResult with keys:
            valid (bool): Whether the P.IVA passes format and checksum checks.
            piva (str): Normalised P.IVA (11 digits, no prefix).
            reason (str | None): Failure reason if valid is False, else None.
    """
    start = time.monotonic()
    await ctx_log(ctx, "check_piva.start", input_length=len(piva.strip()))

    # Step 1 — normalise input
    if ctx:
        await ctx.report_progress(1, 3)

    normalised = piva.strip().upper()
    if normalised.startswith("IT"):
        normalised = normalised[2:]

    if not normalised.isdigit():
        result = CheckPivaResult(
            valid=False, piva=normalised, reason="La P.IVA deve contenere solo cifre."
        )
        await ctx_log(ctx, "check_piva.done", valid=False, elapsed_ms=elapsed_ms(start))
        return result

    if len(normalised) != 11:
        result = CheckPivaResult(
            valid=False,
            piva=normalised,
            reason=f"La P.IVA deve essere di 11 cifre; fornite {len(normalised)}.",
        )
        await ctx_log(ctx, "check_piva.done", valid=False, elapsed_ms=elapsed_ms(start))
        return result

    # Step 2 — checksum computation
    if ctx:
        await ctx.report_progress(2, 3)

    digits = [int(c) for c in normalised]

    # Sum digits at odd positions (1,3,5,7,9 → 0-indexed: 0,2,4,6,8)
    s_odd = sum(digits[i] for i in range(0, 10, 2))

    # Process digits at even positions (2,4,6,8,10 → 0-indexed: 1,3,5,7,9)
    s_even = 0
    for i in range(1, 10, 2):
        doubled = digits[i] * 2
        s_even += doubled - 9 if doubled >= 10 else doubled

    expected_check = (10 - (s_odd + s_even) % 10) % 10
    if digits[10] != expected_check:
        reason = (
            f"Checksum non valido: cifra di controllo attesa {expected_check},"
            f" trovata {digits[10]}."
        )
        result = CheckPivaResult(valid=False, piva=normalised, reason=reason)
        await ctx_log(ctx, "check_piva.done", valid=False, elapsed_ms=elapsed_ms(start))
        return result

    # Step 3 — completion
    if ctx:
        await ctx.report_progress(3, 3)

    result = CheckPivaResult(valid=True, piva=normalised, reason=None)
    await ctx_log(ctx, "check_piva.done", valid=True, elapsed_ms=elapsed_ms(start))
    return result
