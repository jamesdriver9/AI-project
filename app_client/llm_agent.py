import asyncio
import os
import sys
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

# --- GLOBALS ---
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcp-server:8000/sse")

# UPDATED: The "Universal Analyst" instructions
UNIVERSAL_ANALYST_PROMPT = """
You are a Universal Data Analyst powered by a Spark Data Lake. 
You have access to multiple tables and sources.

OPERATING PROCEDURES:
1. NEVER assume you know what tables or columns exist.
2. ALWAYS start by calling 'list_available_tables' to see what data is currently on disk.
3. Use 'get_table_schema' for the relevant table to identify correct column names.
4. Write your Spark SQL query based ONLY on the schema you just discovered.
5. If the user asks for a chart, provide a JSON breakdown between [CHART_START] and [CHART_END] using 'Category' and 'Amount' keys.
6. Never assume different tables have the same schema. Always check first!
7. For EVERY NEW USER REQUEST, you MUST start by calling 'list_available_tables'.

VISUALIZATION PROTOCOL:
1. If a user asks for a "chart", "graph", or "plot", perform the SQL query normally.
2. Ensure your SQL output is a clean list of JSON objects.
3. After the data, simply state: "RENDER_CHART: [Type]" (Types: BAR, LINE, SCATTER, PIE).

"You are a Data Lake Navigator. For visualization:\n"
    "1. Run the SQL query.\n"
    "2. Place the RAW JSON result lines between [CHART_START] and [CHART_END].\n"
    "3. Do NOT add commas between the JSON objects, just new lines.\n"
    "4. Do NOT say 'RENDER_CHART' inside the brackets."
"""

async def get_agent_app(client: MultiServerMCPClient):
    """Initializes the agent by discovering tools from the MCP Server."""
    # This now discovers list_available_tables, get_table_schema, etc.
    mcp_tools = await client.get_tools()
    
    # --- BULLETPROOF KEY CHECK ---
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError("❌ API Key is missing from environment variables!")

    model = ChatGoogleGenerativeAI(
        # 'gemini-2.5-flash' is the stable production model in 2026
        model="gemini-2.5-flash", 
        google_api_key=api_key, 
        temperature=0
    )
    memory = MemorySaver()

    # Using 'prompt' for the system instructions
    return create_react_agent(
        model, 
        tools=mcp_tools, 
        checkpointer=memory,
        prompt=UNIVERSAL_ANALYST_PROMPT
    )

async def run_agent():
    """CLI/Service mode for the agent."""
    print(f"🔌 Connecting to Multi-Source MCP Server at {MCP_SERVER_URL}...")
    
    client = MultiServerMCPClient({
        "data_lake": {"url": MCP_SERVER_URL, "transport": "sse"}
    })
    
    try:
        app = await get_agent_app(client)
        print("✅ Agent Online & Multi-Source Tools Discovered.")

        if sys.stdin.isatty():
            # Interactive CLI Mode
            while True:
                try:
                    user_input = input("\nQuery: ").strip()
                    if not user_input: continue
                    if user_input.lower() in ["exit", "quit"]: break
                    
                    # We use a static thread_id for CLI testing; Streamlit uses dynamic ones
                    result = await app.ainvoke(
                        {"messages": [("user", user_input)]}, 
                        {"configurable": {"thread_id": "mcp_universal_session"}}
                    )
                    print("\nAgent:", result["messages"][-1].content)
                except (EOFError, KeyboardInterrupt):
                    break
        else:
            # Service Mode (Docker)
            print("🚀 Running in background mode...")
            while True: 
                await asyncio.sleep(3600)
                
    except Exception as e:
        print(f"❌ Failed to start agent: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(run_agent())
    except KeyboardInterrupt:
        print("\n👋 Engine Shutdown.")