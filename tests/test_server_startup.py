"""
Test di avvio del server MCP.

Esistono perché server.py era escluso dalla coverage e nessun test lo
importava: la CI era verde su Python 3.11 mentre il server, su 3.11, non si
avviava (Pydantic rifiutava typing.TypedDict). Questi test eseguono il punto
in cui i tool vengono registrati, in-process e poi via stdio come un client reale.
"""

import sys
from importlib.metadata import version

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

EXPECTED_TOOLS = {
    "validate_invoice",
    "extract_invoice_data",
    "lookup_sdi_error",
    "check_piva",
    "verify_piva_vies",
    "find_invoice_anomalies",
    "generate_invoice_report",
}


async def test_server_registers_all_tools() -> None:
    from fatturapa_mcp.server import mcp

    tools = await mcp.list_tools()
    assert {t.name for t in tools} == EXPECTED_TOOLS


async def test_tool_schemas_do_not_expose_ctx() -> None:
    """Context è iniettato da FastMCP: non deve comparire nello schema del tool."""
    from fatturapa_mcp.server import mcp

    for tool in await mcp.list_tools():
        assert "ctx" not in tool.inputSchema.get("properties", {}), tool.name


async def test_stdio_handshake_declares_package_version() -> None:
    """Avvia il server come farebbe Claude Desktop e controlla l'handshake."""
    params = StdioServerParameters(
        command=sys.executable,
        args=["-c", "from fatturapa_mcp.server import main; main()"],
    )
    async with (
        stdio_client(params) as (read, write),
        ClientSession(read, write) as session,
    ):
        info = await session.initialize()
        assert info.serverInfo.name == "fatturapa-mcp-server"
        assert info.serverInfo.version == version("fatturapa-mcp-server")
        tools = await session.list_tools()
        assert {t.name for t in tools.tools} == EXPECTED_TOOLS
