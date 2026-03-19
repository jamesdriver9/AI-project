import streamlit as st
import asyncio
import os
import json
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

# Fixed import: removed folder prefix for Docker compatibility
from llm_agent import get_agent_app  

load_dotenv()

# --- 1. SESSION STATE SETUP ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "user_session_1"

# --- 2. ASYNC WRAPPER ---
def run_async(coro):
    """Runs the async agent call inside the sync Streamlit thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

async def get_response(user_input):
    """Connects to MCP with a retry mechanism for Spark initialization."""
    mcp_url = os.getenv("MCP_SERVER_URL", "http://mcp-server:8000/sse")
    
    # Initialize the client
    client = MultiServerMCPClient({
        "finance": {"url": mcp_url, "transport": "sse"}
    })
    
    # --- ADDED: CONNECTION RETRY LOGIC ---
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # This triggers the actual network handshake
            agent = await get_agent_app(client)
            
            # Invoke the agent
            result = await agent.ainvoke(
                {"messages": [("user", user_input)]}, 
                {"configurable": {"thread_id": st.session_state.thread_id}}
            )
            return result["messages"][-1].content
            
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2)  # Wait 2 seconds before retrying
                continue
            else:
                raise Exception(f"Spark Engine is still warming up or unreachable: {e}")

# --- 3. UI LAYOUT ---
st.set_page_config(page_title="Finance AI", page_icon="💰", layout="centered")
st.title("💰 AI Finance Agent (MCP + Spark)")
st.sidebar.markdown("### Status")
st.sidebar.success("Connected to Finance Engine")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("Ask about your spending..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("⚡ Spark Engine Querying...", expanded=True) as status:
            try:
                # Execute the async response call
                response = run_async(get_response(prompt))
                status.update(label="✅ Analysis Complete", state="complete", expanded=False)
            except Exception as e:
                status.update(label="❌ Connection Error", state="error")
                response = f"I encountered an error communicating with the agent: {e}"
            
        st.markdown(response)
        
        # --- 4. DATA VISUALIZATION CHECK ---
        # If the agent returned a JSON chart block, render it
        if "[CHART_START]" in response:
            try:
                raw_json = response.split("[CHART_START]")[1].split("[CHART_END]")[0]
                chart_info = json.loads(raw_json)
                
                if chart_info["type"] == "bar":
                    st.subheader("Visual Breakdown")
                    st.bar_chart(
                        data=chart_info["data"], 
                        x="Category", 
                        y="Amount", 
                        color="#00FFAA"
                    )
            except Exception as e:
                st.error(f"Failed to render chart: {e}")

        # Save assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": response})