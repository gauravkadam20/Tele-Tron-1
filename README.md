# 🤖 Tele-Tron-1: Autonomous Logistics AI Intelligence Engine

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Google Gemini](https://img.shields.io/badge/LLM-Google%20Gemini-8E75C2.svg)](https://aistudio.google.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite%20(mode=ro)-003B57.svg)](https://www.sqlite.org/)
[![Plotly](https://img.shields.io/badge/Charts-Plotly%20Interactive-3F4F75.svg)](https://plotly.com/)

**Tele-Tron-1** is an enterprise-grade **Natural Language to SQL (NL-to-SQL)** intelligence engine designed for complex supply chain, freight telematics, and logistics analytics. 

Powered by **Google Gemini** models, **SQLite** with engine-level read-only security (`mode=ro`), an interactive **Streamlit Copilot** chat interface, and a **Plotly Dynamic Visualization & GPS Fleet Telematics Engine**.

---

![Tele-Tron-1 Pipeline Overview](docs/assets/teletron-pipeline-overview.jpg)

---

## ✨ Key Capabilities

### 🧠 Conversational Intelligence & Precision
- **Natural Language to SQL**: Converts complex business questions into precise, optimized SQLite queries.
- **Multi-Turn Conversational Memory**: Retains conversational context across follow-ups, allowing supply chain analysts to drill down into prior queries and filters seamlessly.
- **Semantic Business Catalog**: Ground-truth domain dictionary mapping all 26 logistics metrics, units (`USD`, `Days`, `Hours`, `°C`), valid ranges, and executive risk categories (`Low Risk`, `Moderate Risk`, `High Risk`).
- **Transparent Assumptions Callouts**: Explains business interpretations and threshold choices made during query generation.
- **Executive Insight Summaries**: Synthesizes tabular result sets into actionable business bullet points, comparisons, and takeaway metrics.

### 📊 Dynamic Visualizations & GPS Telematics Mapping
- **GPS Fleet Telematics Map**: Automatically detects latitude/longitude coordinates and plots interactive fleet location points on OpenStreetMap with risk color-coding and shipment telemetry tooltips.
- **Time-Series Trend Lines**: Automatically plots chronological telemetry trends over time.
- **Categorical Bar Charts**: Compares operational metrics (costs, delays, demand) across corridor or risk tiers.
- **Correlation Scatter Plots**: Identifies relationships between numeric variables (e.g. traffic congestion level vs fuel burn rate).
- **Single-Row KPI Metric Cards**: Highlights single aggregate metrics cleanly.

### 🔒 Enterprise Security & Engine Guardrails
- **Engine-Level Read-Only Security**: Mounts SQLite with URI parameter `mode=ro`, guaranteeing that destructive actions (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, etc.) cannot execute at the C-engine level.
- **AST / Token Safety Gatekeeper**: Pre-execution AST validation blocking stacked queries, multi-statement semicolons, and administrative commands (`ATTACH`, `PRAGMA`) while allowing safe keywords in string literals.
- **Self-Correction Retry Loop**: Automatically captures syntax or schema errors and passes them back to Gemini for self-healing repair (up to 2 retries).
- **Memory Safety Caps**: Automatically injects safety `LIMIT 100` on open-ended queries and caps excessive limits at `500` rows maximum to protect RAM and browser responsiveness.
- **Zero-Latency In-Memory Query Caching**: Caches recurring queries in memory for 1 hour (TTL), returning instant answers at **$0 LLM token cost** with live cache purging controls.

---

## 🏗️ Illustrated 4-Stage Architecture

Tele-Tron-1 processes user queries through a 4-stage pipeline illustrated below:

| Stage 1: Data Ingestion | Stage 2: Security Gatekeeper |
| :---: | :---: |
| ![Stage 1: Ingestion](docs/assets/01-data-ingestion.jpg) | ![Stage 2: Security Gatekeeper](docs/assets/02-security-gatekeeper.jpg) |
| **Sensor Chaos to Read-Only Vault**: Raw IoT streams are normalized and stored behind an engine-level `mode=ro` lock. | **Dual-Tier Query Protection**: AST token filter drops destructive queries into a blocked chute while safe `SELECT`s pass. |

| Stage 3: Query Generation | Stage 4: Synthesis |
| :---: | :---: |
| ![Stage 3: Self-Healing Engine](docs/assets/03-self-healing-engine.jpg) | ![Stage 4: Insight Synthesizer](docs/assets/04-insight-synthesizer.jpg) |
| **Semantic Catalog & Self-Correction**: References domain dictionary; self-heals unexpected SQLite errors on the fly. | **Memory Safety Cap & Executive Synthesizer**: Trims massive result sets and stamps out actionable summaries & charts. |

> 📖 For complete architectural specifications and data flow diagrams, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10 or higher
- A Google Gemini API key ([Get an API key here](https://aistudio.google.com/))

### 2. Installation
Clone the repository and install the production dependencies:

```bash
git clone https://github.com/gauravkadam20/Tele-Tron-1.git
cd Tele-Tron-1
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the project root:

```env
GOOGLE_API_KEY="your-google-gemini-api-key"
GEMINI_MODEL="gemini-3.5-flash-lite"
```

*(Note: `.env` is listed in `.gitignore` and is never committed to version control).*

### 4. Database Setup (Optional)
If you need to re-import or initialize the logistics dataset:

```bash
python Database/setup_db.py
```

---

## 🖥️ Running the Application

### Option A: Interactive Streamlit Web Copilot (Recommended)
Launch the web interface:

```bash
# Recommended cross-platform launcher:
python -m streamlit run app.py

# Or directly if Streamlit is in your PATH:
streamlit run app.py
```

Open `http://localhost:8501` in your browser. The dashboard includes:
* **Conversational Chat Feed** with multi-turn memory.
* **Executive KPI Cards** (Total Shipments, Avg Freight Cost, Avg Delay, Supplier Reliability).
* **Interactive GPS OpenStreetMap** for fleet coordinates.
* **Dynamic Plotly Visualizations** (Bar, Line, Scatter, KPI Cards).
* **Collapsible SQLite Query Inspector**.
* **One-Click CSV Result Exporter**.
* **Sidebar Controls**: Cache purger, conversation reset, database schema inspector, and semantic data dictionary viewer.

### Option B: Command Line Interface (CLI)
Run the demonstration script:

```bash
python main.py
```

The CLI demonstrates:
1. Turn 1 business query execution.
2. Turn 2 contextual multi-turn follow-up.
3. In-memory cache hit ($0 cost, 0 latency).
4. Guardrail intercept of destructive queries.

---

## 💡 Example Queries to Try

| Category | Example Question |
| :--- | :--- |
| **GPS Fleet Mapping** | *"Show GPS coordinates and delay probability for top 15 high-risk shipments"* |
| **Cost Analysis** | *"What are the top 3 risk classifications by average shipping cost, and what is their average delay probability?"* |
| **Multi-Turn Follow-Up** | *"What are the historical demand levels for those specific risk tiers?"* |
| **Correlation Analysis** | *"What is the relationship between traffic congestion level and fuel consumption rate?"* |
| **Operational Risk** | *"Show top 5 shipments with highest delay probability and weather condition severity"* |
| **Security Guardrail Test** | *"Delete all records from the table"* *(Blocked with safety alert)* |

---

## 🧪 Verification & Test Suite

The test suite includes 20 comprehensive unit and integration tests covering:
- **AST / Token Safety Validation**: Destructive keywords, stacked queries, admin commands, and literals.
- **Engine-Level Read-Only Security**: Direct write attempt verification against `mode=ro`.
- **Memory Safety Limits**: Enforced `LIMIT 100` and maximum `500` row capping.
- **Semantic Business Catalog**: Dictionary completeness and domain rule checks.
- **Query Caching**: Cache insertion, instant cache hits, data parity, and cache purging.
- **Chart Engine Heuristics**: Automatic detection of GPS maps, lines, bars, scatter plots, and KPI cards.
- **Multi-Turn Conversational Memory**: Contextual prompt assembly and follow-up query execution.

Run the test suite:

```bash
python test_askdata.py
```

Output:
```text
Ran 20 tests in 6.305s

OK
```

---

## 📂 Project Structure

```
Tele-Tron-1/
├── .env                   # Local API keys and environment settings (git-ignored)
├── .gitignore             # Git ignore configuration
├── requirements.txt       # Production dependencies (pandas, google-genai, streamlit, plotly)
├── README.md              # Project overview, quickstart & feature guide
├── ARCHITECTURE.md        # Technical architectural specification & flow diagrams
├── app.py                 # Streamlit web copilot & conversational dashboard
├── askdata.py             # Core NL-to-SQL compiler, safety filter, caching & synthesizer
├── chart_engine.py        # Heuristic visualization & OpenStreetMap GPS mapping engine
├── config.py              # Environment configuration & Gemini SDK client factory
├── data_dictionary.py     # Semantic business catalog & domain metadata definitions
├── main.py                # Console entrypoint demonstrating multi-turn chat & caching
├── test_askdata.py        # Unit and integration test suite (20 tests)
├── docs/
│   └── assets/            # Hand-drawn architecture illustrations
├── Database/
│   ├── setup_db.py        # Dataset ingestion script (CSV -> SQLite)
│   └── logistics.db       # SQLite database (git-ignored)
└── Data/
    └── Raw/               # Raw telematics CSV dataset (git-ignored)
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
