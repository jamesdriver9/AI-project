import os
import sys
from typing import Annotated, TypedDict
from dotenv import load_dotenv

# Core LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# Standard LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from src.finance_agent import FinanceAgent

load_dotenv()

# --- 1. DEFINE THE STATE ---
class AgentState(TypedDict):
    # This keeps track of all messages in the chat
    messages: Annotated[list, add_messages]

# --- 2. SETUP TOOLS & MODEL ---
finance_logic = FinanceAgent()
tools = [
    finance_logic.analyze_financial_data,
    finance_logic.predict_future_spending,
    finance_logic.create_anomaly_chart
]
tool_node = ToolNode(tools)

# Bind the tools to Gemini (The 2026 way)
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key=os.getenv("GOOGLE_API_KEY")
).bind_tools(tools)

# --- 3. DEFINE THE LOGIC NODES ---
def call_model(state: AgentState):
    """Decides what the AI should do next."""
    messages = state['messages']
    response = model.invoke(messages)
    return {"messages": [response]}

def should_continue(state: AgentState):
    """Determines if we need to call a tool or finish."""
    last_message = state['messages'][-1]
    if not last_message.tool_calls:
        return "end"
    return "tools"

# --- 4. BUILD THE GRAPH ---
workflow = StateGraph(AgentState)

# Add our "stations"
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

# Connect the dots
workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "end": END,
        "tools": "tools"
    }
)
workflow.add_edge("tools", "agent") # After tool runs, go back to agent

# Compile the app
app = workflow.compile()

# --- 5. INTERACTIVE LOOP ---
def main():
    print("\n--- LangGraph Finance Agent Online ---")
    print("Type 'exit' to quit.\n")
    
    # Persistent thread for memory (in-memory for now)
    thread_config = {"configurable": {"thread_id": "1"}}
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            sys.exit(0)
        
        # Stream the response (so you see the "thinking")
        for event in app.stream(
            {"messages": [HumanMessage(content=user_input)]},
            thread_config,
            stream_mode="updates"
     ):     
            for node_name, value in event.items():
                # We only care about the 'agent' node's text output
                if node_name == "agent" and "messages" in value:
                    last_msg = value["messages"][-1]
                    
                    # 1. Handle List-style content (The 2026 Gemini Standard)
                    if isinstance(last_msg.content, list):
                        for block in last_msg.content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                print(f"\nAgent: {block['text']}\n")
                    
                    # 2. Handle String-style content (Fallback)
                    elif isinstance(last_msg.content, str) and last_msg.content:
                        print(f"\nAgent: {last_msg.content}\n")

if __name__ == "__main__":
    main()