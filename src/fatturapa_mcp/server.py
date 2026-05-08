"""
fatturapa_mcp.server
~~~~~~~~~~~~~~~~~~~~
MCP server entry point for FatturaPA/SDI tools.
"""

from mcp.server.fastmcp import FastMCP

from fatturapa_mcp.tools.check_piva import check_piva
from fatturapa_mcp.tools.extract import extract_invoice_data
from fatturapa_mcp.tools.sdi_errors import lookup_sdi_error
from fatturapa_mcp.tools.validate import validate_invoice
from fatturapa_mcp.tools.vies import verify_piva_vies

mcp = FastMCP("fatturapa-mcp-server")

mcp.tool()(validate_invoice)
mcp.tool()(extract_invoice_data)
mcp.tool()(lookup_sdi_error)
mcp.tool()(check_piva)
mcp.tool()(verify_piva_vies)


def main() -> None:  # pragma: no cover
    """Start the MCP server."""
    mcp.run()


if __name__ == "__main__":  # pragma: no cover
    main()
