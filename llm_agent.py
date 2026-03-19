import os
import json
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents import create_spark_dataframe_agent
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

# --- GLOBALS (Placeholders for Lazy Loading) ---
_spark = None
_spark_agent = None
_app = None
PARQUET_PATH = "data/financials.parquet"

# --- NEW: SYSTEM PROMPT FOR CHARTS ---
FINANCE_PROMPT = """
You are a expert Financial Data Analyst. 

RULES:
1. If the user asks for a chart, graph, or breakdown:
   - Provide a text analysis first.
   - Then, include the data between [CHART_START] and [CHART_END] markers.
   - Use JSON format: {"type": "bar", "data": [{"Category": "Food", "Amount": 100}, ...]}
   - Do NOT use triple backticks (```).
"""

# --- 1. LAZY SPARK INITIALIZER ---
def get_spark_objects():
    """Starts Spark and the Spark Worker only when the first query hits."""
    global _spark, _spark_agent
    
    if _spark is None:
        print("⚡ Spark engine starting (First run only)...")
        _spark = SparkSession.builder \
            .appName("FinanceAgent") \
            .config("spark.sql.adaptive.enabled", "true") \
            .getOrCreate()
        
        if not os.path.exists(PARQUET_PATH):
            print(f"❌ Error: {PARQUET_PATH} missing.")
            return None, None

        df = _spark.read.parquet(PARQUET_PATH)
        
        # Initialize the Spark Worker Agent
        llm_worker = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)
        _spark_agent = create_spark_dataframe_agent(llm_worker, df, allow_dangerous_code=True)
        print("✅ Spark Worker Ready.")
        
    return _spark, _spark_agent

# --- 2. THE TOOL (Calls Lazy Spark) ---
def query_finance_data(user_query: str) -> str:
    """Standard tool for the Main Agent to talk to Spark."""
    _, spark_worker = get_spark_objects()
    if not spark_worker:
        return "Error: Financial data file not found on server."
    
    prompt = f"User Query: {user_query}"
    response = spark_worker.invoke({"input": prompt})
    return str(response.get("output", "No data returned."))

# --- 3. LAZY MAIN AGENT (Now with Prompt) ---
def get_agent_app():
    global _app
    if _app is None:
        model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
        memory = MemorySaver()
        _app = create_react_agent(
            model, 
            tools=[query_finance_data], 
            checkpointer=memory,
            prompt=FINANCE_PROMPT  # Ensure this is 'prompt' and not 'state_modifier'
        )
    return _app

# --- 4. EXECUTION ---
def run_agent():
    print("\n✅ Finance Engine Online (Lazy Mode)")
    if sys.stdin.isatty():
        # CLI Mode (for local testing)
        app = get_agent_app()
        while True:
            try:
                user_input = input("\nQuery: ").strip()
                if not user_input: continue
                for chunk in app.stream({"messages": [("user", user_input)]}, {"configurable": {"thread_id": "test"}}):
                    if "agent" in chunk: print(chunk["agent"]["messages"][-1].content)
            except (EOFError, KeyboardInterrupt): break
    else:
        # Docker Service Mode
        while True: time.sleep(60)

if __name__ == "__main__":
    run_agent()