"""
fatturapa_mcp.tools.validate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
MCP tool: validate_invoice — validates a FatturaPA XML against XSD schemas v1.2/v1.3.
"""

import time
from pathlib import Path
from typing import Any, TypedDict

from lxml import etree
from mcp.server.fastmcp import Context

from fatturapa_mcp.utils.logging import ctx_log, elapsed_ms
from fatturapa_mcp.utils.roots import get_allowed_roots, is_path_allowed

# FastMCP injects a Context[ServerSessionT, LifespanContextT, RequestT]; the type
# parameters are internal to the server session and not needed by tool implementations.
_Ctx = Context[Any, Any, Any]

_SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"

_NS_TO_VERSION: dict[str, str] = {
    "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.2": "1.2",
    "http://ivaservizi.agenziaentrate.gov.it/docs/xsd/fatture/v1.3": "1.3",
}

_VERSION_TO_XSD: dict[str, str] = {
    "1.2": "FatturaPA_v1.2.xsd",
    "1.3": "FatturaPA_v1.3.xsd",
}

# resolve_entities=False prevents XXE; no_network=True blocks external DTD fetch.
_SAFE_PARSER: etree.XMLParser = etree.XMLParser(resolve_entities=False, no_network=True)


class ValidateResult(TypedDict):
    """Structured result returned by validate_invoice."""

    valid: bool
    version: str
    errors: list[str]


async def validate_invoice(
    xml_content: str = "",
    ctx: _Ctx | None = None,
    file_path: str | None = None,
) -> ValidateResult:
    """Validate a FatturaPA XML document against the appropriate XSD schema.

    Auto-detects schema version (v1.2 or v1.3) from the XML namespace.
    Returns a structured result without logging any XML content.

    When *file_path* is given the document is read from disk; the path is
    checked against the roots configured in ``FATTURAPA_ALLOWED_ROOTS`` before
    any read is attempted.  Pass *xml_content* directly to skip file I/O.

    Args:
        xml_content: Raw XML string of the FatturaPA document.
        ctx: Optional MCP context for structured log emission.
        file_path: Optional filesystem path to read the document from.
            Checked against allowed roots before reading.

    Returns:
        A ValidateResult with keys:
            valid (bool): Whether the document passed XSD validation.
            version (str): Detected schema version ("1.2", "1.3", or "unknown").
            errors (list[str]): Validation error messages, empty if valid.

    Raises:
        PermissionError: If *file_path* is outside the configured allowed roots.
        ValueError: If neither *xml_content* nor *file_path* is provided.
    """
    if file_path is not None:
        if not is_path_allowed(file_path, get_allowed_roots()):
            raise PermissionError("Access denied: path is outside allowed roots.")
        xml_content = Path(file_path).read_text(encoding="utf-8")
    elif not xml_content:
        raise ValueError("Provide either xml_content or file_path.")

    start = time.monotonic()
    await ctx_log(ctx, "validate_invoice.start", xml_length=len(xml_content))

    # Step 1 — parse input
    if ctx:
        await ctx.report_progress(1, 3)

    try:
        root = etree.fromstring(xml_content.encode("utf-8"), _SAFE_PARSER)
    except etree.XMLSyntaxError as exc:
        result: ValidateResult = {
            "valid": False,
            "version": "unknown",
            "errors": [str(exc)],
        }
        await ctx_log(
            ctx,
            "validate_invoice.done",
            level="error",
            valid=False,
            elapsed_ms=elapsed_ms(start),
        )
        return result

    tag = root.tag
    ns = tag[1 : tag.index("}")] if tag.startswith("{") else ""
    version = _NS_TO_VERSION.get(ns)
    if version is None:
        result = {
            "valid": False,
            "version": "unknown",
            "errors": [f"Unrecognised FatturaPA namespace: {ns!r}"],
        }
        await ctx_log(
            ctx,
            "validate_invoice.done",
            level="error",
            valid=False,
            elapsed_ms=elapsed_ms(start),
        )
        return result

    xsd_path = _SCHEMAS_DIR / _VERSION_TO_XSD[version]
    if not xsd_path.is_file():
        result = {
            "valid": False,
            "version": version,
            "errors": [
                f"XSD schema not found: {xsd_path}. "
                "See src/fatturapa_mcp/schemas/README.md for download instructions."
            ],
        }
        await ctx_log(
            ctx,
            "validate_invoice.done",
            level="warning",
            valid=False,
            version=version,
            elapsed_ms=elapsed_ms(start),
        )
        return result

    # Step 2 — XSD validation
    if ctx:
        await ctx.report_progress(2, 3)

    xsd_doc = etree.parse(str(xsd_path), _SAFE_PARSER)
    schema = etree.XMLSchema(xsd_doc)
    valid = schema.validate(root)
    # lxml-stubs omits __iter__ on _ErrorLog; the runtime type is _ListErrorLog.
    errors = [str(e) for e in schema.error_log]  # type: ignore[attr-defined]
    result = {"valid": valid, "version": version, "errors": errors}
    await ctx_log(
        ctx,
        "validate_invoice.done",
        valid=valid,
        version=version,
        error_count=len(errors),
        elapsed_ms=elapsed_ms(start),
    )

    # Step 3 — completion
    if ctx:
        await ctx.report_progress(3, 3)

    return result
