import os
import json
from datetime import datetime
from dotenv import load_dotenv

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_experimental.agents import create_spark_dataframe_agent
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

# --- 1. SCHEMA GUARD & AUTO-WIPE ---
FINGERPRINT_PATH = "data/schema_fingerprint.json"
CHECKPOINT_DB = "checkpoints.sqlite"

def sync_schema_and_memory(current_df):
    """Nukes memory if schema changes (e.g., adding the 'date' column)."""
    current_columns = current_df.columns
    old_columns = []
    
    if os.path.exists(FINGERPRINT_PATH):
        try:
            with open(FINGERPRINT_PATH, "r") as f:
                old_columns = json.load(f)
        except: pass
            
    if set(current_columns) != set(old_columns):
        print(f"⚠️ SCHEMA CHANGE: {old_columns} -> {current_columns}")
        if os.path.exists(CHECKPOINT_DB):
            os.remove(CHECKPOINT_DB)
            print("🗑️ Memory wiped to prevent iteration loops.")
        
        os.makedirs("data", exist_ok=True)
        with open(FINGERPRINT_PATH, "w") as f:
            json.dump(current_columns, f)

# --- 2. DATA SETUP ---
spark = SparkSession.builder.appName("FinanceAgent").getOrCreate()
# Ensure the file exists before reading
if not os.path.exists("data/financials.parquet"):
    print("❌ Error: data/financials.parquet not found. Run update_data.py first!")
    exit(1)

df = spark.read.parquet("data/financials.parquet")
sync_schema_and_memory(df)

# --- 3. THE TOOL (Spark Worker) ---
# Flash-Lite is cheaper for the "internal" Spark work
llm_worker = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)
spark_agent = create_spark_dataframe_agent(llm_worker, df, allow_dangerous_code=True)

def query_finance_data(user_query: str) -> str:
    """
    USE THIS for all math, data analysis, and schema questions about the financial dataset.
    This tool has access to the category, amount, and date columns.
    """
    # 1. This is where the dynamic 'df.columns' belongs!
    # It gets sent to the Spark Worker every time the tool is called.
    prompt = f"Available Data Columns: {df.columns}. User Query: {user_query}"
    
    # 2. Execute the spark agent
    response = spark_agent.invoke({"input": prompt})
    
    clean_text = response.get("output", "No data returned.")
    if isinstance(clean_text, list) and len(clean_text) > 0:
        clean_text = clean_text[0].get('text', str(clean_text[0]))

    # Audit Log
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "query": user_query,
        "result": str(clean_text)[:500],
        "agent": "spark-worker-v1"
    }
    
    with open("data/audit_log.jsonl", "a") as f:
        f.write(json.dumps(audit_entry) + "\n")

    return str(clean_text)

# --- 4. THE AGENT (Gemini 2.5 Flash) ---
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0,
    thinking_budget=2000 # Tier 1 allows higher reasoning budget
)
memory = MemorySaver()

# In LangGraph 1.0+, max_iterations is moved to the stream/invoke call
app = create_react_agent(
    model, 
    tools=[query_finance_data], 
    checkpointer=memory
)

# --- 5. RUN LOOP ---
config = {"configurable": {"thread_id": "tier1_test_session"}, "recursion_limit": 15}

print("\n✅ Finance Agent Online (Tier 1 Limits Active)")
while True:
    user_input = input("\nQuery: ").strip()
    if user_input.lower() in ['exit', 'quit']: break

    print(">>> Thinking...", flush=True)
    
    try:
        final_usage = None
        # recursion_limit here replaces 'max_iterations'
        for chunk, metadata in app.stream(
            {"messages": [("user", user_input)]}, 
            config, 
            stream_mode="messages"
        ):
            if metadata.get("langgraph_node") == "agent" and chunk.content:
                print(chunk.content, end="", flush=True)
                
            if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                final_usage = chunk.usage_metadata

        if final_usage:
            print(f"\n{'-'*30}")
            print(f"📊 Tokens: {final_usage.get('total_tokens')} | Reasoning: {final_usage.get('output_token_details', {}).get('reasoning', 0)}")

    except Exception as e:
        print(f"\n❌ Error: {e}")