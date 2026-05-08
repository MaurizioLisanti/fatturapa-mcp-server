"""
fatturapa_mcp.tools.validate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
MCP tool: validate_invoice — validates a FatturaPA XML against XSD schemas v1.2/v1.3.
"""

from pathlib import Path
from typing import TypedDict

from lxml import etree

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


def validate_invoice(xml_content: str) -> ValidateResult:
    """Validate a FatturaPA XML document against the appropriate XSD schema.

    Auto-detects schema version (v1.2 or v1.3) from the XML namespace.
    Returns a structured result without logging any XML content.

    Args:
        xml_content: Raw XML string of the FatturaPA document.

    Returns:
        A ValidateResult with keys:
            valid (bool): Whether the document passed XSD validation.
            version (str): Detected schema version ("1.2", "1.3", or "unknown").
            errors (list[str]): Validation error messages, empty if valid.
    """
    try:
        root = etree.fromstring(xml_content.encode("utf-8"), _SAFE_PARSER)
    except etree.XMLSyntaxError as exc:
        return {"valid": False, "version": "unknown", "errors": [str(exc)]}

    tag = root.tag
    ns = tag[1 : tag.index("}")] if tag.startswith("{") else ""

    version = _NS_TO_VERSION.get(ns)
    if version is None:
        return {
            "valid": False,
            "version": "unknown",
            "errors": [f"Unrecognised FatturaPA namespace: {ns!r}"],
        }

    xsd_path = _SCHEMAS_DIR / _VERSION_TO_XSD[version]
    if not xsd_path.is_file():
        return {
            "valid": False,
            "version": version,
            "errors": [
                f"XSD schema not found: {xsd_path}. "
                "See src/fatturapa_mcp/schemas/README.md for download instructions."
            ],
        }

    xsd_doc = etree.parse(str(xsd_path), _SAFE_PARSER)
    schema = etree.XMLSchema(xsd_doc)
    valid = schema.validate(root)
    # lxml-stubs omits __iter__ on _ErrorLog; the runtime type is _ListErrorLog.
    errors = [str(e) for e in schema.error_log]  # type: ignore[attr-defined]

    return {"valid": valid, "version": version, "errors": errors}
