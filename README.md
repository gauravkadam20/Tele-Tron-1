# 🤖 Tele-Tron-1

**Tele-Tron-1** is an autonomous **Natural Language to SQL (NL-to-SQL)** intelligence engine designed for supply chain and logistics analytics. Powered by **Google Gemini** models, **SQLite** with engine-level read-only security, and an interactive **Streamlit** dashboard.

---

## ✨ Features

- **Natural Language to SQL**: Translates complex logistics questions into precise SQLite queries.
- **Semantic Business Catalog**: Grounded domain dictionary mapping all 26 supply chain metrics, units, and executive categories for high accuracy.
- **Transparent Assumptions Callouts**: Explains business interpretations and threshold choices made by the model.
- **Automated Business Insights**: Synthesizes tabular results into executive summaries with key metrics, comparisons, and actionable insights.
- **Engine-Level Read-Only Security**: Uses SQLite URI `mode=ro` to guarantee that destructive queries (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, etc.) cannot execute at the C-engine level.
- **AST / Token Safety Filter**: Pre-execution validation blocking stacked queries, administration commands, and multi-statement injection while avoiding false positives on substring matches.
- **Memory Safety Limits**: Automatically injects safety `LIMIT` caps to prevent unbounded queries from overwhelming memory or UI rendering.
- **Self-Correction Retry Loop**: Automatically passes SQLite syntax or schema errors back to Gemini for guided query correction.
- **Interactive Streamlit Web Dashboard**: Explore schema, view semantic definitions, inspect generated SQL, download CSV exports, and generate charts dynamically.
- **Cached Schema Inspection**: In-memory caching of table metadata and column types via `PRAGMA table_info`.

---

## 🏗️ Architecture

```
User Question
      │
      ▼
┌─────────────────────────┐
│     Prompt Builder      │ ◄─── Cached Schema & Column Types (PRAGMA table_info)
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│    Gemini LLM Call      │ (gemini-3.5-flash-lite / gemini-3.1-flash-lite)
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│     SQL Cleaner         │ Extracts clean query from code fences / text
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│     is_safe_query()     │ Rejects non-SELECT / DDL / stacked queries
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ SQLite Engine (mode=ro) │ ──► On failure ──► Self-correction feedback loop
└───────────┬─────────────┘
            │ (pandas DataFrame)
            ▼
┌─────────────────────────┐
│   synthesize_answer()   │ LLM generates natural language business summary
└───────────┬─────────────┘
            │
            ▼
┌───────────────────────────┐
│ QueryResult / UI Display  │ (Summary + SQL + Data Table + Visual Charts)
└───────────────────────────┘
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- A Google Gemini API key ([Get an API key here](https://aistudio.google.com/))

### 2. Installation
Clone the repository and install dependencies:

```bash
git clone https://github.com/gauravkadam20/Side-Projects.git
cd Tele-Tron-1
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the project root:

```env
GOOGLE_API_KEY="your-google-gemini-api-key"
GEMINI_MODEL="gemini-3.5-flash-lite"
```

*(Note: `.env` is listed in `.gitignore` and will never be committed to Git).*

### 4. Database Setup (Optional)
If you need to re-import the logistics dataset:

```bash
python Database/setup_db.py
```

---

## 🖥️ Running the Application

### Option A: Interactive Streamlit Web Dashboard
Launch the web UI:

```bash
# Recommended (works regardless of Windows PATH settings):
python -m streamlit run app.py

# Or directly if Streamlit is in your PATH:
streamlit run app.py
```

Open `http://localhost:8501` in your browser to start querying your data interactively.

### Option B: Command Line Interface
Run the demo script:

```bash
python main.py
```

---

## 🧪 Running Tests

The test suite covers safety guards, AST validation, CTE query support, read-only engine enforcement, and end-to-end question answering:

```bash
python test_askdata.py
```

---

## 📂 Project Structure

```
Tele-Tron-1/
├── .env                   # Local secrets (never committed)
├── .gitignore             # Git ignore configuration
├── requirements.txt       # Production dependencies
├── README.md              # Project documentation
├── app.py                 # Streamlit web dashboard
├── askdata.py             # Core NL-to-SQL engine, safety checks & synthesizer
├── config.py              # Environment configuration & Gemini client factory
├── data_dictionary.py     # Semantic business catalog & domain metadata
├── main.py                # Command-line entrypoint demonstration
├── test_askdata.py        # Unit & integration test suite
├── Database/
│   ├── setup_db.py        # Ingestion script (CSV -> SQLite)
│   └── logistics.db       # SQLite database (git-ignored)
└── Data/
    └── Raw/               # Raw logistics CSV dataset (git-ignored)
```
