import os
import warnings
import operator
from typing import Annotated, TypedDict, List
from dotenv import load_dotenv

# 1. SILENCE NOISE & LOAD ENV
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.types import RetryPolicy
from langchain_core.messages import BaseMessage, HumanMessage
from pyspark.sql import SparkSession
from langchain_experimental.agents import create_spark_dataframe_agent

# 2. SPARK SETUP
spark = SparkSession.builder.appName("FinanceAgent").getOrCreate()
# Assume your 5M row CSV is in the /app/data folder
df = spark.read.csv("data/big_financial_data.csv", header=True, inferSchema=False)
df.cache()  # Cache it in memory for faster access during the agent's lifetime

# 3. INTERNAL SPARK WORKER (The "Tool")
# Use gemini-2.5-flash-lite here if you want to save your "Pro" quota
llm_worker = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)

spark_agent = create_spark_dataframe_agent(
    llm_worker, 
    df, 
    allow_dangerous_code=True,
    number_of_head_rows=1, # Default is usually 3-5; 1 is enough for the AI
    include_df_in_prompt=True
)
def query_finance_data(user_query: str) -> str:
    """Queries the 5 million row Spark dataframe."""
    response = spark_agent.invoke({"input": user_query})
    return str(response["output"])

tools = [query_finance_data]

# 4. LANGGRAPH STATE & NODES
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]

# --- THE ORCHESTRATOR ---
# We use the standard Flash here for the "Reasoning"
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0).bind_tools(tools)

def call_model(state: AgentState):
    # Only send the last 3 messages to the AI
    # (The system prompt, the last tool result, and the current question)
    truncated_messages = state["messages"][-3:] 
    return {"messages": [model.invoke(truncated_messages)]}

tool_node = ToolNode(tools)

# 5. RETRY POLICY (The Fix for your 429 Error)
# This tells the graph: "If Google says I'm exhausted, wait 35s and try again."
gemini_retry_policy = RetryPolicy(
    retry_on=lambda e: "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e),
    initial_interval=35.0,  # Replaces wait_min
    max_interval=65.0,      # Replaces wait_max
    max_attempts=3,
)

# 6. BUILD THE GRAPH
workflow = StateGraph(AgentState)

# Add the retry policy specifically to the 'agent' node
workflow.add_node("agent", call_model, retry=gemini_retry_policy)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")

def should_continue(state: AgentState):
    if state["messages"][-1].tool_calls:
        return "tools"
    return END

workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

app = workflow.compile()

# 7. MAIN LOOP

if __name__ == "__main__":
    print("--- LangGraph Finance Agent (v2026.1) ---")
    try:
        while True:
            # Clear the buffer
            user_input = input("\nQuery (or 'exit'): ").strip()
            if not user_input: continue
            if user_input.lower() in ['exit', 'quit']: break
            
            print(f">>> Processing: {user_input}") # DEBUG 1
            
            inputs = {"messages": [HumanMessage(content=user_input)]}
            
            # Using version='v2' for better 2026 streaming support
            stream_found = False
            for chunk in app.stream(inputs, stream_mode="values", version="v2"):
                stream_found = True
                if "messages" in chunk:
                    msg = chunk["messages"][-1]
                    if msg.content:
                        print(f"\n[Response]: {msg.content}")
                    elif hasattr(msg, 'tool_calls') and msg.tool_calls:
                        print("\n[Status]: (Agent is calling Spark...)")

            if not stream_found:
                print("!!! Error: Graph did not emit any events. Check if 'app' is compiled correctly.")
                
    except KeyboardInterrupt:
        print("\nStopping agent...")
    finally:
        spark.stop()