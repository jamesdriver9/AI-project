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

FINANCE_PROMPT = """
You are an expert Financial Data Analyst. 
Use the connected MCP tools to query Spark data.
Always provide clear summaries. 
Include data between [CHART_START] and [CHART_END] for any visual breakdown requested.
"""

async def get_agent_app(client: MultiServerMCPClient):
    """Initializes the agent by discovering tools from the MCP Server."""
    mcp_tools = await client.get_tools()
    
    # --- BULLETPROOF KEY CHECK ---
    # Check both common environment variable names
    
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
    # If the above is empty, check for the other common name
         api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
         raise ValueError("❌ API Key is missing from environment variables!")

    model = ChatGoogleGenerativeAI(
    # 'gemini-2.5-flash' is the stable production model in March 2026
    model="gemini-2.5-flash", 
    google_api_key=api_key, 
    temperature=0
)
    # ------------------------------

    memory = MemorySaver()
    
    return create_react_agent(
        model, 
        tools=mcp_tools, 
        checkpointer=memory,
        prompt=FINANCE_PROMPT
    )

async def run_agent():
    """CLI/Service mode for the agent."""
    print(f"🔌 Connecting to Finance MCP Server at {MCP_SERVER_URL}...")
    
    # Initialize the client (non-context manager style)
    client = MultiServerMCPClient({
        "finance": {"url": MCP_SERVER_URL, "transport": "sse"}
    })
    
    try:
        app = await get_agent_app(client)
        print("✅ Agent Online & Tools Discovered.")

        if sys.stdin.isatty():
            # Interactive CLI Mode
            while True:
                try:
                    user_input = input("\nQuery: ").strip()
                    if not user_input: continue
                    if user_input.lower() in ["exit", "quit"]: break
                    
                    result = await app.ainvoke(
                        {"messages": [("user", user_input)]}, 
                        {"configurable": {"thread_id": "mcp_test_session"}}
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