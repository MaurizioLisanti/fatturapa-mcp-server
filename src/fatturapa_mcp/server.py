"""
fatturapa_mcp.server
~~~~~~~~~~~~~~~~~~~~
MCP server entry point for FatturaPA/SDI tools.
"""

from mcp.server.fastmcp import FastMCP

from fatturapa_mcp.tools.anomalies import find_invoice_anomalies
from fatturapa_mcp.tools.check_piva import check_piva
from fatturapa_mcp.tools.extract import extract_invoice_data
from fatturapa_mcp.tools.sdi_errors import lookup_sdi_error
from fatturapa_mcp.tools.validate import validate_invoice
from fatturapa_mcp.tools.vies import verify_piva_vies
from fatturapa_mcp.utils.roots import get_allowed_roots

mcp = FastMCP("fatturapa-mcp-server")

mcp.tool()(validate_invoice)
mcp.tool()(extract_invoice_data)
mcp.tool()(lookup_sdi_error)
mcp.tool()(check_piva)
mcp.tool()(verify_piva_vies)
mcp.tool()(find_invoice_anomalies)


@mcp.resource("fatturapa://roots")
def list_allowed_roots() -> str:
    """Expose the configured file-system roots that tools may read from.

    Returns a newline-separated list of allowed directory paths, or a
    human-readable notice when no restrictions are configured.  Clients can
    read this resource to discover which paths are accessible before calling
    validate_invoice or extract_invoice_data with a file_path argument.

    Returns:
        Newline-separated root paths, or ``"(unrestricted)"`` when none are set.
    """
    roots = get_allowed_roots()
    return "\n".join(str(r) for r in roots) if roots else "(unrestricted)"


def main() -> None:  # pragma: no cover
    """Start the MCP server."""
    mcp.run()


if __name__ == "__main__":  # pragma: no cover
    main()
