import streamlit as st
import asyncio
import os
import json
import logging
import re
import pandas as pd
import plotly.express as px
from datetime import datetime
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from llm_agent import get_agent_app 

load_dotenv()

# --- 0. LOGGING SETUP ---
logging.basicConfig(
    filename='signatures.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# --- 1. UTILITY FUNCTIONS ---
def parse_and_log_response(raw_content):
    clean_text = ""
    if isinstance(raw_content, list):
        for part in raw_content:
            if isinstance(part, dict):
                if "extras" in part and "signature" in part["extras"]:
                    logging.info(f"Signature Detected: {part['extras']['signature']}")
                if part.get("type") == "text":
                    clean_text += part.get("text", "")
            elif hasattr(part, 'content'):
                if isinstance(part.content, list):
                    for item in part.content:
                        if isinstance(item, dict) and 'text' in item:
                            clean_text += item['text']
                else:
                    clean_text += str(part.content)
        return clean_text.strip() if clean_text else "⚠️ Data unreadable."
    return str(raw_content).strip()

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# --- 2. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# --- 3. CORE AGENT LOGIC ---
async def get_response(user_input):
    mcp_url = os.getenv("MCP_SERVER_URL", "http://mcp-server:8000/sse")
    client = MultiServerMCPClient({
        "finance": {"url": mcp_url, "transport": "sse", "timeout": 60.0}
    })

    # --- ✨ SLIDING WINDOW MEMORY LOGIC ---
    # We only grab the last 2 messages (1 User, 1 Assistant) to save tokens
    # This gives context without sending the entire history
    history_context = []
    if len(st.session_state.messages) >= 2:
        last_exchange = st.session_state.messages[-2:]
        for m in last_exchange:
            # We strip out raw JSON from the history to save even MORE tokens
            clean_history = re.sub(r"\[CHART_START\].*?\[CHART_END\]", "[Data Table]", m["content"], flags=re.DOTALL)
            history_context.append((m["role"], clean_history))

    dynamic_instructions = (
        "You are a Data Lake Navigator. Use the provided context from the previous query "
        "if the user asks a follow-up. For visualizations, output JSON between [CHART_START] and [CHART_END]."
    )
    
    # Construct the message list: System + History (max 2) + Current Input
    payload = [("system", dynamic_instructions)]
    payload.extend(history_context)
    payload.append(("user", user_input))
    
    try:
        agent = await get_agent_app(client)
        result = await agent.ainvoke(
            {"messages": payload}, 
            {"configurable": {"thread_id": st.session_state.thread_id}, "recursion_limit": 25}
        )
        final_msg = result["messages"][-1]
        return parse_and_log_response(final_msg.content)
    except Exception as e:
        return f"❌ **Connection Error:** {str(e)}"

# --- 4. UI LAYOUT ---
st.set_page_config(page_title="Spark Intelligence", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; }
    [data-testid="stChatMessageAssistant"] { border: 2px solid #39FF14 !important; background-color: rgba(57, 255, 20, 0.05) !important; }
    .main-title { color: #39FF14 !important; text-shadow: 0 0 15px #39FF14; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1 class="main-title">Spark Finance Intelligence</h1>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<h2 style="color: #39FF14;">🖥️ System Health</h2>', unsafe_allow_html=True)
    if st.button("🔄 Refresh Data Lake Status"):
        with st.spinner("Scanning..."):
            res = run_async(get_response("SYSTEM_ACTION: list_available_tables"))
            st.info(res)

    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# --- 5. DISPLAY CHAT (THE SINGLE SOURCE OF TRUTH) ---
for i, msg in enumerate(st.session_state.messages):
    avatar = "👤" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        clean_text = re.sub(r"\[CHART_START\].*?\[CHART_END\]", "", msg["content"], flags=re.DOTALL)
        color_style = 'style="color: #39FF14;"' if msg["role"] == "assistant" else ""
        st.markdown(f'<div {color_style}>{clean_text}</div>', unsafe_allow_html=True)

        chart_match = re.search(r"\[CHART_START\]\s*(.*?)\s*\[CHART_END\]", msg["content"], re.DOTALL)
        if chart_match:
            try:
                chart_json = chart_match.group(1).strip()
                json_lines = [json.loads(line) for line in chart_json.split('\n') if line.strip()]
                df_plot = pd.DataFrame(json_lines)
                
                if not df_plot.empty:
                    # User Query is always 1 message back from the chart message
                    user_query = st.session_state.messages[i-1]["content"].lower() if i > 0 else ""
                    is_line = "line" in user_query or "trend" in user_query
                    
                    plot_func = px.line if is_line else px.bar
                    fig = plot_func(
                        df_plot, x=df_plot.columns[0], y=df_plot.columns[1],
                        template="plotly_dark", color_discrete_sequence=['#39FF14'],
                        title=f"{df_plot.columns[1]} Analysis"
                    )
                    if is_line: fig.update_traces(line=dict(width=3))
                    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Chart Render Failed: {e}")

# --- 6. USER INTERACTION ---
if prompt := st.chat_input("Ask for a chart of total amount by city..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant", avatar="🤖"):
        with st.status("🏗️ Analyzing Data Lake...", expanded=True) as status:
            try:
                response = run_async(get_response(prompt))
                status.update(label="✅ Analysis Complete", state="complete")
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
            except Exception as e:
                status.update(label="❌ Error", state="error")
                st.error(f"Agent Error: {e}")