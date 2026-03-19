import streamlit as st
import os
import pandas as pd
import json

# --- 1. PAGE CONFIG & CSS ---
st.set_page_config(page_title="AI Finance Agent", layout="wide")

# Custom CSS for Font Sizes and Styling
st.markdown("""
    <style>
    /* 1. MAKE TAB HEADERS BIGGER */
    .stTabs [data-baseweb="tab"] {
        height: 60px; /* Increased height to fit larger text */
        white-space: pre-wrap;
        gap: 5000px !important;
        display: flex;
        background-color: transparent;
        border-radius: 5px;
        color: #888; 
        font-size: 26px !important;  /* <--- Increased font size */
        font-weight: 700 !important; /* Bold headers */
        letter-spacing: 1px;        /* Spaced out for clarity */
    }
    
    /* 1. YOUR CHARACTER BUBBLE (The User) */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        background-color: #1E1E2E !important; /* Deep Indigo/Slate Background */
        border-radius: 15px;
        border: 1px solid #7E57C2; /* Purple Border to contrast the Green */
        margin-bottom: 10px;
    }

    /* YOUR AVATAR ICON COLOR */
    [data-testid="stChatMessageAvatarUser"] {
        background-color: #7E57C2 !important; /* Vibrant Purple Icon */
        color: white !important;
    }
            
    /* 2. STYLE THE ASSISTANT (AI) MESSAGE BUBBLE */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
        background-color: #00FFAA11 !important; /* Subtle Green Tint */
        border-radius: 15px;
        border: 1px solid #00FFAA; /* Glowing Green Border */
        box-shadow: 0px 0px 10px #00FFAA33; /* Neon Glow */
    }
    
    /* 3. OPTIONAL: Change the actual Icon Background color */
    [data-testid="stChatMessageAvatarAssistant"] {
        background-color: #00FFAA !important;
        color: black !important;
    }
    
    [data-testid="stChatMessageAvatarUser"] {
        background-color: #555 !important;
    }

    /* 2. STYLE THE ACTIVE TAB (The one you are currently on) */
    .stTabs [aria-selected="true"] {
        color: #00FFAA !important; 
        border-bottom: 3px solid #00FFAA !important;
        background-color: #00FFAA11 !important; 
    }

    /* 3. ENSURE CONTENT INSIDE TABS IS ALSO LARGE */
    .stTabs [data-testid="stVerticalBlock"] {
        font-size: 22px !important;
    }
            
    /* TYPING ANIMATION STYLES */
    @keyframes pulse {
        0% { opacity: 0.4; transform: scale(0.98); }
        50% { opacity: 1; transform: scale(1); shadow: 0 0 10px #00FFAA; }
        100% { opacity: 0.4; transform: scale(0.98); }
    }

    .typing-indicator {
        color: #00FFAA;
        font-family: monospace;
        font-size: 20px;
        font-weight: bold;
        padding: 10px;
        animation: pulse 1.5s infinite ease-in-out;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HEADER SECTION ---
col1, col2 = st.columns([3, 1])

with col1:
    st.title("AI Financial Data Agent")
    st.caption("Powered by Gemini 2.5 & PySpark Engine")

with col2:
    st.markdown("<br>", unsafe_allow_html=True) # Align with title
    # Custom glowing badge with BIGGER font
    st.markdown("""
        <div style="text-align: right;">
            <span style="
                background-color: #00FFAA22; 
                color: #00FFAA; 
                padding: 10px 25px; 
                border-radius: 30px; 
                border: 2px solid #00FFAA; 
                font-weight: 1000; 
                font-family: monospace;
                font-size: 24px;  /* <--- Increased font size */
                box-shadow: 0px 0px 15px #00FFAA55; /* Optional: Adds a subtle glow */
            ">
                ● SYSTEM: ONLINE
            </span>
        </div>
        """, unsafe_allow_html=True)

# --- 3. SIDEBAR with EXPORT ---
with st.sidebar:
    st.header("System Status")
    st.success("✅ UI Engine: Online")
    
    st.markdown("---")
    st.header("📥 Export Results")
    
    if "last_result_df" in st.session_state and st.session_state.last_result_df is not None:
        csv = st.session_state.last_result_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Last Query as CSV",
            data=csv,
            file_name=f"finance_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
            mime='text/csv',
        )
    else:
        st.info("Run a query to enable CSV download.")

    st.markdown("---")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.session_state.last_result_df = None
        st.rerun()

# --- 4. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_result_df" not in st.session_state:
    st.session_state.last_result_df = None

# --- 5. TABS INTERFACE ---
tab1, tab2 = st.tabs(["💬 AI Chat", "📈 Historical Insights"])

with tab1:
    # Display chat history within Tab 1
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # CHAT LOGIC
    if prompt := st.chat_input("Ask about your finances..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            
            try:
                from llm_agent import get_agent_app
                app = get_agent_app()
                config = {"configurable": {"thread_id": "streamlit_session_001"}, "recursion_limit": 15}
                
                # 1. STREAMING PHASE
                for chunk in app.stream({"messages": [("user", prompt)]}, config):
                    if "agent" in chunk:
                        last_msg = chunk["agent"]["messages"][-1]
                        content = last_msg.content
                        text_chunk = "".join([str(c.get("text", c)) if isinstance(c, dict) else str(c) for c in content]) if isinstance(content, list) else str(content)
                        full_response += text_chunk
                        response_placeholder.markdown(full_response + "▌")
                
                # 2. POST-PROCESSING (Markers Logic)
                if "[CHART_START]" in full_response and "[CHART_END]" in full_response:
                    text_part = full_response.split("[CHART_START]")[0].strip()
                    json_raw = full_response.split("[CHART_START]")[1].split("[CHART_END]")[0].strip()
                    json_clean = json_raw.replace("```json", "").replace("```", "").strip()
                    
                    response_placeholder.markdown(text_part)
                    st.session_state.messages.append({"role": "assistant", "content": text_part})
                    
                    try:
                        chart_dict = json.loads(json_clean)
                        df_chart = pd.DataFrame(chart_dict["data"])
                        st.write("### 📊 Automated Visualization")
                        st.bar_chart(df_chart, x=df_chart.columns[0], y=df_chart.columns[1])
                        st.session_state.last_result_df = df_chart
                    except Exception as e:
                        st.error(f"Failed to parse chart data. Error: {e}")
                        st.code(json_clean)
                else:
                    response_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    if any(w in full_response.lower() for w in ["total", "list", "summary"]):
                        st.session_state.last_result_df = pd.DataFrame([{"query": prompt, "response": full_response}])

            except Exception as e:
                st.error(f"Engine Error: {e}")

with tab2:
    st.subheader("Quick Stats")
    # Custom styling for metrics makes these pop!
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        st.metric(label="Total Processed Transactions", value="1.2M", delta="+5% this week")
    with m_col2:
        st.metric(label="Data Source", value="Parquet/Spark", delta="Sync OK")