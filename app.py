import streamlit as st
import pandas as pd
from config import DB_PATH, DEFAULT_MODEL
from askdata import ask_database, get_schema, get_readonly_connection, QueryResult

# 1. Page Configuration
st.set_page_config(
    page_title="Tele-Tron-1 | Logistics AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Custom CSS for polished interface
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
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px 16px;
        text-align: center;
    }
    .summary-card {
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        border-left: 5px solid #2563EB;
        border-radius: 6px;
        padding: 16px 20px;
        margin-top: 10px;
        margin-bottom: 15px;
        color: #1E293B;
        font-size: 1.05rem;
        line-height: 1.6;
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
    except Exception as e:
        return None


# 3. Sidebar Configuration
with st.sidebar:
    st.image(
        "https://cdn-icons-png.flaticon.com/512/2830/2830312.png",
        width=70,
    )
    st.title("Tele-Tron-1 Core")

    # Engine Status
    st.markdown("### 🔒 Security Status")
    st.success("Read-Only SQLite Engine (Active)")

    # Model Selection
    st.markdown("### 🤖 Model Selection")
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
        help="Select which Gemini model will generate SQL and executive summaries.",
    )

    # Database Schema & Semantic Dictionary Viewer
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
            catalog_text = get_data_dictionary_prompt()
            st.markdown(catalog_text)
        except Exception as e:
            st.warning(f"Could not load dictionary: {e}")

    # Sample Questions
    st.markdown("### 💡 Sample Questions")
    sample_queries = [
        "What are the top 3 risk classifications by average shipping cost?",
        "Show the average delay probability and shipping cost for high vs low route risk levels.",
        "Which 5 records have the highest delay probability along with weather condition severity?",
        "What is the average fuel consumption rate by traffic congestion level?",
        "Delete all records from the table",  # Safety demonstration
    ]

    for sq in sample_queries:
        if st.button(f"👉 {sq[:42]}...", key=f"btn_{hash(sq)}", use_container_width=True):
            st.session_state["query_input"] = sq


# 4. Header & Top KPIs
st.markdown('<div class="main-header">🤖 Tele-Tron-1</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Autonomous Logistics Intelligence Engine powered by Google Gemini & SQLite.</div>',
    unsafe_allow_html=True,
)

kpis = load_dataset_kpis()
if kpis is not None:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Shipments", f"{int(kpis['total_records']):,}")
    with col2:
        st.metric("Avg Shipping Cost", f"${kpis['avg_cost']:.2f}")
    with col3:
        st.metric("Avg Delay Probability", f"{kpis['avg_delay'] * 100:.1f}%")
    with col4:
        st.metric("Supplier Reliability", f"{kpis['avg_reliability']:.2f} / 1.0")

st.divider()

# 5. Query Input Section
if "query_input" not in st.session_state:
    st.session_state["query_input"] = ""

query_text = st.text_input(
    "Ask a question about your logistics & supply chain data:",
    value=st.session_state["query_input"],
    placeholder="e.g. What are the top 3 routes by highest delay probability?",
)

run_button = st.button("🚀 Analyze Data", type="primary")

# 6. Query Processing & Visualization
if run_button and query_text.strip():
    with st.spinner("Analyzing question, generating safe SQL, and querying database..."):
        try:
            result = ask_database(
                question=query_text.strip(),
                summarize=True,
                model=selected_model,
            )

            # Business Assumptions & Executive Summary
            if result.assumptions:
                st.info(f"💡 **Business Interpretation & Assumptions:** {result.assumptions}")

            st.markdown("### 📊 Executive Summary")
            st.markdown(
                f'<div class="summary-card">{result.summary}</div>',
                unsafe_allow_html=True,
            )

            # SQL Code Viewer
            with st.expander("🔍 View Generated SQL Query", expanded=True):
                st.code(result.sql, language="sql")

            # Data Table & Metrics
            capped_badge = " *(🛡️ Memory Safety Cap Enforced)*" if result.is_safety_capped else ""
            st.markdown(f"### 📋 Query Results ({len(result.data)} rows){capped_badge}")

            if len(result.data) > 0:
                st.dataframe(result.data, use_container_width=True)

                # Export CSV button
                csv_data = result.data.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download Results as CSV",
                    data=csv_data,
                    file_name="logistics_query_results.csv",
                    mime="text/csv",
                )

                # Automatic Chart Visualization if applicable
                numeric_cols = result.data.select_dtypes(include=["number"]).columns.tolist()
                text_cols = result.data.select_dtypes(include=["object", "string", "category"]).columns.tolist()

                if len(result.data) <= 50 and len(numeric_cols) > 0:
                    st.markdown("### 📈 Visual Chart")
                    chart_df = result.data.copy()
                    if text_cols:
                        # Use first categorical column as index for plotting
                        cat_col = text_cols[0]
                        chart_df = chart_df.set_index(cat_col)[numeric_cols]
                    st.bar_chart(chart_df)
            else:
                st.info("The query executed successfully but returned 0 rows matching your criteria.")

        except ValueError as val_err:
            st.error(f"🛡️ **Security Alert: Query Blocked**\n\n{val_err}")
            st.info("The system enforces read-only access and rejects destructive operations (DROP, DELETE, UPDATE, INSERT, ALTER, etc.).")
        except Exception as e:
            st.error(f"❌ **Query Execution Error:**\n\n{e}")

elif run_button:
    st.warning("Please enter a question to analyze.")
