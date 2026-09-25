import os
import re
import time
import sqlite3
import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Dict, Any, Generator, Tuple
import pandas as pd
from config import DB_PATH, DEFAULT_MODEL, get_client, client
from data_dictionary import get_data_dictionary_prompt

# Suppress SDK deprecation/info warnings regarding direct AFC in generate_content
warnings.filterwarnings(
    "ignore",
    message=".*Direct use of automatic function calling.*",
    category=UserWarning,
)

_SCHEMA_CACHE: Optional[str] = None


class QueryResult:
    """Encapsulates the result of a natural language database query with business assumptions."""

    def __init__(
        self,
        question: str,
        sql: str,
        data: pd.DataFrame,
        summary: str = "",
        assumptions: str = "",
        is_safety_capped: bool = False,
        error: Optional[str] = None,
    ):
        self.question = question
        self.sql = sql
        self.data = data
        self.df = data  # Alias for convenience
        self.summary = summary
        self.assumptions = assumptions
        self.is_safety_capped = is_safety_capped
        self.error = error

    def __str__(self) -> str:
        parts = []
        if self.assumptions:
            parts.append(f"--- Assumptions & Interpretation ---\n{self.assumptions}\n")
        if self.summary:
            parts.append(f"--- Summary ---\n{self.summary}\n")
        parts.append(f"--- Generated SQL ---\n{self.sql}\n")
        if self.data is not None:
            capped_notice = " (Safety Cap Enforced: max 100 rows)" if self.is_safety_capped else ""
            parts.append(f"--- Data ({len(self.data)} rows{capped_notice}) ---")
            if len(self.data) > 0:
                parts.append(self.data.to_string(index=False, max_rows=10))
            else:
                parts.append("[Empty Result Set]")
        return "\n".join(parts)

    def __repr__(self) -> str:
        return f"<QueryResult rows={len(self.data) if self.data is not None else 0} sql='{self.sql}'>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "sql": self.sql,
            "assumptions": self.assumptions,
            "summary": self.summary,
            "is_safety_capped": self.is_safety_capped,
            "rows_count": len(self.data) if self.data is not None else 0,
            "data": self.data.to_dict(orient="records") if self.data is not None else [],
        }


@contextmanager
def get_readonly_connection(db_path: Path = DB_PATH) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for a read-only SQLite connection enforced at the SQLite C-engine level."""
    resolved_path = Path(db_path).resolve().as_posix()
    db_uri = f"file:{resolved_path}?mode=ro"
    conn = sqlite3.connect(db_uri, uri=True)
    try:
        yield conn
    finally:
        conn.close()


def is_safe_query(sql: str) -> bool:
    """Validates that the SQL query is strictly read-only and safe to execute.

    Permits SELECT and CTE (WITH ... SELECT) queries while guarding against:
    - Destructive DDL/DML keywords (DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE, etc.)
    - Stacked queries / multi-statement injection via semicolons
    - Administrative operations (ATTACH, DETACH, VACUUM, PRAGMA)
    - False positives on keywords embedded inside words (e.g. 'updated') or string literals
    """
    if not sql or not isinstance(sql, str):
        return False

    # Remove comments
    cleaned = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)

    # Strip quoted string literals to avoid false positives on words within strings
    stripped = re.sub(r"'(''|[^'])*'", "''", cleaned)
    stripped = re.sub(r'"(""|[^"])*"', '""', stripped).strip()

    if not stripped:
        return False

    # Prevent stacked queries (multiple semicolon-delimited statements)
    statements = [s.strip() for s in stripped.rstrip(";").split(";") if s.strip()]
    if len(statements) != 1:
        return False

    stmt = statements[0].lower()

    # Must begin with SELECT or WITH (for CTE queries)
    if not (stmt.startswith("select") or stmt.startswith("with")):
        return False

    # Block destructive and administrative keywords as whole tokens
    dangerous_patterns = [
        r"\bdrop\b",
        r"\bdelete\b",
        r"\bupdate\b",
        r"\binsert\b",
        r"\balter\b",
        r"\btruncate\b",
        r"\battach\b",
        r"\bdetach\b",
        r"\bvacuum\b",
        r"\breindex\b",
        r"\breplace\b",
        r"\bcreate\b",
        r"\bpragma\b",
        r"\bgrant\b",
        r"\brevoke\b",
        r"\binto\s+outfile\b",
        r"\binto\s+dumpfile\b",
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, stmt):
            return False

    return True


def enforce_safety_limit(sql: str, default_limit: int = 100, max_limit: int = 500) -> Tuple[str, bool]:
    """Enforces an upper-bound safety LIMIT on SELECT queries to protect memory and UI responsiveness.
    
    Returns:
        (capped_sql, is_capped)
    """
    sql_clean = sql.strip().rstrip(";")

    # Check if a LIMIT clause already exists
    limit_match = re.search(r"\blimit\s+(\d+)\b", sql_clean, re.IGNORECASE)
    if limit_match:
        existing_limit = int(limit_match.group(1))
        if existing_limit > max_limit:
            # Cap excessive limit
            capped_sql = re.sub(r"\blimit\s+\d+\b", f"LIMIT {max_limit}", sql_clean, flags=re.IGNORECASE) + ";"
            return capped_sql, True
        return sql_clean + ";", False

    # Append default limit to protect against unbounded scans
    return f"{sql_clean} LIMIT {default_limit};", True


def get_schema(db_path: Path = DB_PATH, force_refresh: bool = False) -> str:
    """Extracts and caches the database schema using PRAGMA metadata."""
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE and not force_refresh:
        return _SCHEMA_CACHE

    schema_parts = []
    with get_readonly_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]

        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            col_defs = [f"{col[1]} ({col[2]})" for col in columns]
            schema_parts.append(f"Table: {table}\nColumns: {', '.join(col_defs)}")

    _SCHEMA_CACHE = "\n\n".join(schema_parts)
    return _SCHEMA_CACHE


def clean_sql_and_assumptions(raw_response: str) -> Tuple[str, str]:
    """Extracts SQL query and business assumptions from the model's structured response."""
    # Extract assumptions if present
    assumptions = ""
    assump_match = re.search(
        r"ASSUMPTIONS:\s*(.*?)(?=\n\s*(?:SQL:?|```)|$)",
        raw_response,
        re.DOTALL | re.IGNORECASE,
    )
    if assump_match:
        assumptions = assump_match.group(1).strip()

    if not assumptions:
        assumptions = "Direct mapping from question parameters."

    # Extract clean SQL
    match = re.search(r"```(?:sql)?\s*([\s\S]*?)\s*```", raw_response, re.IGNORECASE)
    if match:
        sql = match.group(1).strip()
    else:
        # Strip any ASSUMPTIONS prefix if raw
        sql = re.sub(r"^ASSUMPTIONS:.*?(?=(?:SELECT|WITH))\s*", "", raw_response, flags=re.DOTALL | re.IGNORECASE)
        sql = re.sub(r"^SQL:\s*", "", sql, flags=re.IGNORECASE).strip()

    sql = re.sub(r"^sql\s+", "", sql, flags=re.IGNORECASE).strip()
    return sql, assumptions


def _call_gemini_api(prompt: str, model: str = DEFAULT_MODEL, retries: int = 3, backoff: float = 2.0) -> str:
    """Helper to call Gemini API with exponential backoff on transient errors."""
    active_client = client or get_client()
    last_error = None

    for attempt in range(retries):
        try:
            response = active_client.models.generate_content(
                model=model,
                contents=prompt,
            )
            if response and response.text:
                return response.text
            raise ValueError("Empty response received from Gemini API.")
        except Exception as e:
            last_error = e
            sleep_time = backoff * (attempt + 1)
            time.sleep(sleep_time)

    raise RuntimeError(f"Gemini API request failed after {retries} retries: {last_error}")


def generate_sql(
    question: str,
    schema: str,
    error_context: Optional[str] = None,
    model: str = DEFAULT_MODEL,
) -> Tuple[str, str]:
    """Generates a SQLite query and business assumptions from natural language with domain semantics."""
    correction_prompt = ""
    if error_context:
        correction_prompt = f"""
IMPORTANT: A previous query attempt failed with this error:
{error_context}
Fix the issue and generate a corrected SQLite query.
"""

    data_dictionary = get_data_dictionary_prompt()

    prompt = f"""You are Tele-Tron-1, an expert SQLite data analyst for supply chain and logistics.
Given this database schema and semantic business catalog:

{data_dictionary}

{correction_prompt}

User Question:
"{question}"

Format your response strictly as follows:
ASSUMPTIONS: <1-2 clear sentences explaining any business assumptions, threshold selections, or category mappings made. If none, write 'Direct standard query.'>
SQL:
```sql
<Single valid SQLite SELECT query>
```
"""
    raw_response = _call_gemini_api(prompt, model=model)
    return clean_sql_and_assumptions(raw_response)


def synthesize_answer(
    question: str,
    sql: str,
    assumptions: str,
    df: pd.DataFrame,
    model: str = DEFAULT_MODEL,
) -> str:
    """Synthesizes a concise natural language explanation based on the SQL query results and assumptions."""
    row_count = len(df)
    if row_count == 0:
        preview = "No rows returned."
    else:
        preview = df.head(10).to_string(index=False)

    prompt = f"""You are Tele-Tron-1, a professional logistics and supply chain business analyst.
The user asked: "{question}"
Assumptions applied: {assumptions}
Executed SQLite Query:
{sql}

Query Results ({row_count} total rows):
{preview}

Provide a concise, direct natural language answer (1-3 sentences) summarizing the business findings.
Reference key figures, metrics, or comparisons where appropriate. Do not repeat the raw SQL query.
"""
    try:
        return _call_gemini_api(prompt, model=model).strip()
    except Exception as e:
        return f"Query returned {row_count} row(s), but summary generation encountered an error: {e}"


def ask_database(
    question: str,
    summarize: bool = True,
    max_correction_attempts: int = 2,
    model: str = DEFAULT_MODEL,
    db_path: Path = DB_PATH,
) -> QueryResult:
    """Translates a natural language question into SQL, validates safety, enforces memory caps,
    executes against SQLite, applies self-correction on syntax/schema errors, and generates an explanatory summary.
    """
    schema = get_schema(db_path=db_path)
    last_error: Optional[str] = None
    sql = ""
    assumptions = ""
    is_safety_capped = False
    df: Optional[pd.DataFrame] = None

    for attempt in range(max_correction_attempts + 1):
        sql, assumptions = generate_sql(
            question=question,
            schema=schema,
            error_context=last_error,
            model=model,
        )

        if not is_safe_query(sql):
            raise ValueError(f"Blocked unsafe query: {sql}")

        # Enforce memory and UI safety limit
        sql, is_safety_capped = enforce_safety_limit(sql, default_limit=100, max_limit=500)

        try:
            with get_readonly_connection(db_path) as conn:
                df = pd.read_sql(sql, conn)
            # Query succeeded
            break
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as db_err:
            last_error = f"Query: {sql}\nSQLite Error: {db_err}"
            if attempt == max_correction_attempts:
                raise RuntimeError(
                    f"Execution failed after {max_correction_attempts} correction attempts.\n{last_error}"
                ) from db_err

    summary = ""
    if summarize and df is not None:
        summary = synthesize_answer(
            question=question,
            sql=sql,
            assumptions=assumptions,
            df=df,
            model=model,
        )

    return QueryResult(
        question=question,
        sql=sql,
        data=df,
        summary=summary,
        assumptions=assumptions,
        is_safety_capped=is_safety_capped,
    )