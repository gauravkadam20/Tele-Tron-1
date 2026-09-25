import streamlit as st
import pandas as pd
from config import DB_PATH, DEFAULT_MODEL
from askdata import ask_database, get_schema, get_readonly_connection, clear_query_cache, get_cache_size, QueryResult
from chart_engine import render_dynamic_visualization, detect_best_chart_type, has_gps_coordinates

# 1. Page Configuration
st.set_page_config(
    page_title="Tele-Tron-1 | Autonomous Logistics AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Custom CSS styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.2rem;
    }
    .summary-card {
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        border-left: 5px solid #2563EB;
        border-radius: 6px;
        padding: 14px 18px;
        margin-top: 8px;
        margin-bottom: 12px;
        color: #1E293B;
        font-size: 1.05rem;
        line-height: 1.6;
    }
    .badge-cache {
        background-color: #DCFCE7;
        color: #166534;
        font-size: 0.82rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 9999px;
        display: inline-block;
        margin-bottom: 6px;
    }
    .badge-live {
        background-color: #E0E7FF;
        color: #3730A3;
        font-size: 0.82rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 9999px;
        display: inline-block;
        margin-bottom: 6px;
    }
    </style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=3600)
def load_dataset_kpis():
    """Fetches high-level metrics for the logistics dataset."""
    try:
        with get_readonly_connection() as conn:
            query = """
            SELECT 
                COUNT(*) AS total_records,
                AVG(shipping_costs) AS avg_cost,
                AVG(delay_probability) AS avg_delay,
                AVG(supplier_reliability_score) AS avg_reliability
            FROM logistics_data;
            """
            df = pd.read_sql(query, conn)
            return df.iloc[0]
    except Exception:
        return None


# 3. Session State Initialization
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "pending_prompt" not in st.session_state:
    st.session_state["pending_prompt"] = None


# 4. Sidebar Configuration
with st.sidebar:
    st.image(
        "https://cdn-icons-png.flaticon.com/512/2830/2830312.png",
        width=65,
    )
    st.title("Tele-Tron-1 Core")

    # Security & Engine Status
    st.markdown("### 🔒 Security Status")
    st.success("Read-Only SQLite Engine (`mode=ro`)")

    # Model Selection
    st.markdown("### 🤖 Intelligence Core")
    available_models = [
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite-preview",
        "gemini-3-flash-preview",
        "gemini-2.5-pro",
    ]
    selected_model = st.selectbox(
        "Active Gemini Model",
        options=available_models,
        index=0 if DEFAULT_MODEL not in available_models else available_models.index(DEFAULT_MODEL),
        help="Model powering SQL translation and executive synthesis.",
    )

    # Cache Controls
    st.markdown("### ⚡ Performance & Cache")
    cache_count = get_cache_size()
    st.caption(f"Cached queries in memory: **{cache_count}**")
    if st.button("🧹 Clear Query Cache", use_container_width=True):
        purged = clear_query_cache()
        st.toast(f"Cleared {purged} cached query entries!", icon="⚡")
        st.rerun()

    # Chat Conversation Controls
    st.markdown("### 💬 Conversational Session")
    st.caption(f"Turns in active memory: **{len(st.session_state['messages'])}**")
    if st.button("🔄 Reset Conversation", use_container_width=True):
        st.session_state["messages"] = []
        st.session_state["pending_prompt"] = None
        st.toast("Conversation reset!", icon="🧹")
        st.rerun()

    # Database Schema & Semantic Catalog
    st.markdown("### 🗄️ Database & Domain Catalog")
    with st.expander("View Table Schema & Columns", expanded=False):
        try:
            schema_text = get_schema()
            st.code(schema_text, language="markdown")
        except Exception as e:
            st.warning(f"Could not load schema: {e}")

    with st.expander("View Semantic Data Dictionary & Units", expanded=False):
        try:
            from data_dictionary import get_data_dictionary_prompt
            st.markdown(get_data_dictionary_prompt())
        except Exception as e:
            st.warning(f"Could not load dictionary: {e}")

    # Interactive Sample Prompts
    st.markdown("### 💡 Quick Prompt Starters")
    starter_prompts = [
        ("🗺️ High Risk GPS Fleet Map", "Show GPS coordinates and delay probability for top 15 high-risk shipments"),
        ("📊 Cost by Risk Classification", "Compare average shipping costs across all risk classifications"),
        ("🎯 Congestion vs Fuel Burn", "What is the relationship between traffic congestion level and fuel consumption rate?"),
        ("⏱️ Highest Delay Shipments", "Show top 5 shipments with highest delay probability and weather severity"),
        ("🛡️ Safety Filter Test", "DROP TABLE logistics_data;"),
    ]

    for label, query in starter_prompts:
        if st.button(label, key=f"btn_{hash(label)}", use_container_width=True):
            st.session_state["pending_prompt"] = query


# 5. Header & Executive KPIs
st.markdown('<div class="main-header">🤖 Tele-Tron-1</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Autonomous Natural Language to SQL Intelligence with Multi-Turn Conversational Memory & GPS Telematics Mapping.</div>',
    unsafe_allow_html=True,
)

kpis = load_dataset_kpis()
if kpis is not None:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Monitored Shipments", f"{int(kpis['total_records']):,}")
    with col2:
        st.metric("Avg Freight Cost", f"${kpis['avg_cost']:.2f}")
    with col3:
        st.metric("Avg Delay Probability", f"{kpis['avg_delay'] * 100:.1f}%")
    with col4:
        st.metric("Fleet Supplier Reliability", f"{kpis['avg_reliability']:.2f} / 1.0")

st.divider()


# 6. Render Existing Chat Messages
for idx, msg in enumerate(st.session_state["messages"]):
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(f"**{msg['content']}**")
        else:
            # Assistant Response
            result: QueryResult = msg.get("result")
            if result:
                # Cache Badge
                if result.from_cache:
                    st.markdown('<span class="badge-cache">⚡ Instant Cached Result ($0 Cost)</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="badge-live">⏱️ Fresh LLM Execution</span>', unsafe_allow_html=True)

                # Business Assumptions
                if result.assumptions:
                    st.info(f"💡 **Business Interpretation & Assumptions:** {result.assumptions}")

                # Executive Summary
                if result.summary:
                    st.markdown(f'<div class="summary-card">{result.summary}</div>', unsafe_allow_html=True)

                # SQL Query Viewer
                with st.expander("🔍 View Generated SQLite Query", expanded=False):
                    st.code(result.sql, language="sql")

                # Results Data Table
                if result.data is not None and len(result.data) > 0:
                    capped_badge = " *(🛡️ Memory Safety Cap Enforced: max 100 rows)*" if result.is_safety_capped else ""
                    st.markdown(f"**Data Results ({len(result.data)} rows){capped_badge}**")
                    st.dataframe(result.data, use_container_width=True)

                    # CSV Download
                    csv_bytes = result.data.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Export CSV",
                        data=csv_bytes,
                        file_name=f"teletron_results_{idx}.csv",
                        mime="text/csv",
                        key=f"dl_{idx}",
                    )

                    # Dynamic Visual Chart / GPS Map
                    chart_type, fig_or_metrics = render_dynamic_visualization(result.data)
                    if chart_type in ["map", "line", "bar", "scatter"] and fig_or_metrics:
                        st.markdown(f"**Interactive Visualization ({chart_type.upper()})**")
                        st.plotly_chart(fig_or_metrics, use_container_width=True)
                    elif chart_type == "kpi" and isinstance(fig_or_metrics, dict):
                        st.markdown("**Metric Summary**")
                        kpi_cols = st.columns(len(fig_or_metrics))
                        for col, (k, v) in zip(kpi_cols, fig_or_metrics.items()):
                            with col:
                                val_str = f"{v:.2f}" if isinstance(v, float) else str(v)
                                st.metric(k.replace("_", " ").title(), val_str)
                elif result.data is not None:
                    st.info("The query executed successfully but returned 0 rows matching criteria.")
            else:
                st.markdown(msg["content"])


# 7. Chat Input & Execution Logic
user_prompt = st.chat_input("Ask a question, follow-up, or explore GPS fleet routes...")

# Support sidebar quick starter button click
if st.session_state["pending_prompt"]:
    user_prompt = st.session_state["pending_prompt"]
    st.session_state["pending_prompt"] = None

if user_prompt and user_prompt.strip():
    clean_prompt = user_prompt.strip()

    # Append user question to history
    st.session_state["messages"].append({
        "role": "user",
        "content": clean_prompt,
    })

    with st.chat_message("user"):
        st.markdown(f"**{clean_prompt}**")

    # Prepare conversational context from past turns
    chat_history_payload = []
    for m in st.session_state["messages"][:-1]:
        if m["role"] == "user":
            chat_history_payload.append({"question": m["content"]})
        elif m["role"] == "assistant" and "result" in m:
            res: QueryResult = m["result"]
            if chat_history_payload:
                chat_history_payload[-1]["sql"] = res.sql
                chat_history_payload[-1]["assumptions"] = res.assumptions
                chat_history_payload[-1]["summary"] = res.summary

    # Run Analysis
    with st.chat_message("assistant"):
        with st.spinner("Analyzing question, generating safe SQLite query, and calculating insights..."):
            try:
                result = ask_database(
                    question=clean_prompt,
                    summarize=True,
                    chat_history=chat_history_payload,
                    use_cache=True,
                    model=selected_model,
                )

                # Store assistant response in history
                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": result.summary,
                    "result": result,
                })

                # Display Results
                if result.from_cache:
                    st.markdown('<span class="badge-cache">⚡ Instant Cached Result ($0 Cost)</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="badge-live">⏱️ Fresh LLM Execution</span>', unsafe_allow_html=True)

                if result.assumptions:
                    st.info(f"💡 **Business Interpretation & Assumptions:** {result.assumptions}")

                if result.summary:
                    st.markdown(f'<div class="summary-card">{result.summary}</div>', unsafe_allow_html=True)

                with st.expander("🔍 View Generated SQLite Query", expanded=False):
                    st.code(result.sql, language="sql")

                if result.data is not None and len(result.data) > 0:
                    capped_badge = " *(🛡️ Memory Safety Cap Enforced: max 100 rows)*" if result.is_safety_capped else ""
                    st.markdown(f"**Data Results ({len(result.data)} rows){capped_badge}**")
                    st.dataframe(result.data, use_container_width=True)

                    # CSV Download
                    csv_bytes = result.data.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Export CSV",
                        data=csv_bytes,
                        file_name="teletron_query_results.csv",
                        mime="text/csv",
                        key=f"dl_current_{len(st.session_state['messages'])}",
                    )

                    # Dynamic Visual Chart / GPS Map
                    chart_type, fig_or_metrics = render_dynamic_visualization(result.data)
                    if chart_type in ["map", "line", "bar", "scatter"] and fig_or_metrics:
                        st.markdown(f"**Interactive Visualization ({chart_type.upper()})**")
                        st.plotly_chart(fig_or_metrics, use_container_width=True)
                    elif chart_type == "kpi" and isinstance(fig_or_metrics, dict):
                        st.markdown("**Metric Summary**")
                        kpi_cols = st.columns(len(fig_or_metrics))
                        for col, (k, v) in zip(kpi_cols, fig_or_metrics.items()):
                            with col:
                                val_str = f"{v:.2f}" if isinstance(v, float) else str(v)
                                st.metric(k.replace("_", " ").title(), val_str)
                elif result.data is not None:
                    st.info("The query executed successfully but returned 0 rows matching your criteria.")

            except ValueError as val_err:
                st.error(f"🛡️ **Security Alert: Destructive Action Blocked**\n\n{val_err}")
                st.info("Tele-Tron-1 runs in read-only mode and blocks destructive queries (DROP, DELETE, UPDATE, INSERT, ALTER).")
                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": f"🛡️ **Security Alert: Query Blocked**\n\n{val_err}",
                })
            except Exception as e:
                st.error(f"❌ **Execution Error:**\n\n{e}")
                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": f"❌ **Execution Error:** {e}",
                })
