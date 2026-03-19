from fastmcp import FastMCP
import os

# Initialize FastMCP
mcp = FastMCP("FinanceEngine")

@mcp.tool()
async def query_finance_data(query: str) -> str:
    """
    Use this tool to query financial data from the Spark engine.
    """
    # For now, a placeholder to test connection
    return f"Spark engine received query: {query}. Data connection is active."

# --- THE FIX IS HERE ---
# Do NOT use make_sse_app() or http_app() if they cause AttributeErrors.
# Use the built-in .run() with sse transport.
if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8000)