import datetime

from mcp.server.fastmcp import FastMCP


mcp = FastMCP("mcp-excel-server")

@mcp.tool()
def get_datetime() -> datetime.datetime:
    """Use this tool when the user wants to know today's date."""
    return datetime.datetime.now(datetime.timezone.utc)

if __name__ == "__main__":
    print("Starting the MCP Server")
    mcp.run()