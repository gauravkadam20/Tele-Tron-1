import unittest
import sqlite3
import pandas as pd
from pathlib import Path

from askdata import (
    is_safe_query,
    clean_sql_and_assumptions,
    enforce_safety_limit,
    get_schema,
    get_readonly_connection,
    ask_database,
    QueryResult,
)
from data_dictionary import get_data_dictionary_prompt, LOGISTICS_DATA_DICTIONARY
from config import DB_PATH


class TestAskDataSafety(unittest.TestCase):
    def test_safe_select_queries(self):
        self.assertTrue(is_safe_query("SELECT * FROM logistics_data LIMIT 5"))
        self.assertTrue(is_safe_query("SELECT AVG(shipping_costs), COUNT(*) FROM logistics_data;"))
        self.assertTrue(is_safe_query("select route_risk_level, delay_probability from logistics_data where delay_probability > 0.5"))

    def test_cte_queries_allowed(self):
        cte_query = """
        WITH high_risk AS (
            SELECT * FROM logistics_data WHERE route_risk_level > 3
        )
        SELECT AVG(delay_probability) FROM high_risk;
        """
        self.assertTrue(is_safe_query(cte_query))

    def test_keywords_in_literals_and_words_allowed(self):
        # 'updated' should not trigger 'update'
        self.assertTrue(is_safe_query("SELECT * FROM logistics_data WHERE cargo_condition_status = 'updated'"))
        # 'drop' inside a quoted literal
        self.assertTrue(is_safe_query("SELECT * FROM logistics_data WHERE risk_classification = 'drop'"))
        # column names or aliases with substrings like 'alteration'
        self.assertTrue(is_safe_query("SELECT shipping_costs AS alteration_cost FROM logistics_data"))

    def test_destructive_queries_blocked(self):
        self.assertFalse(is_safe_query("DROP TABLE logistics_data"))
        self.assertFalse(is_safe_query("DELETE FROM logistics_data"))
        self.assertFalse(is_safe_query("UPDATE logistics_data SET shipping_costs = 0"))
        self.assertFalse(is_safe_query("INSERT INTO logistics_data (shipping_costs) VALUES (10)"))
        self.assertFalse(is_safe_query("ALTER TABLE logistics_data ADD COLUMN test_col TEXT"))
        self.assertFalse(is_safe_query("TRUNCATE TABLE logistics_data"))

    def test_stacked_queries_blocked(self):
        self.assertFalse(is_safe_query("SELECT * FROM logistics_data; DROP TABLE logistics_data;"))
        self.assertFalse(is_safe_query("SELECT 1; DELETE FROM logistics_data;"))

    def test_admin_commands_blocked(self):
        self.assertFalse(is_safe_query("ATTACH DATABASE ':memory:' AS test_db"))
        self.assertFalse(is_safe_query("PRAGMA journal_mode = WAL"))

    def test_engine_level_readonly_enforcement(self):
        """Verifies SQLite itself rejects writes even if an unsafe query reached the connection."""
        with get_readonly_connection(DB_PATH) as conn:
            cursor = conn.cursor()
            with self.assertRaises(sqlite3.OperationalError):
                cursor.execute("UPDATE logistics_data SET shipping_costs = 9999 WHERE 1=1")


class TestSafetyLimitsAndDataDictionary(unittest.TestCase):
    def test_enforce_safety_limit_appends_default(self):
        sql = "SELECT * FROM logistics_data WHERE delay_probability > 0.5"
        capped_sql, is_capped = enforce_safety_limit(sql, default_limit=100)
        self.assertTrue(is_capped)
        self.assertTrue(capped_sql.endswith("LIMIT 100;"))

    def test_enforce_safety_limit_preserves_smaller_limit(self):
        sql = "SELECT * FROM logistics_data LIMIT 10;"
        capped_sql, is_capped = enforce_safety_limit(sql, default_limit=100)
        self.assertFalse(is_capped)
        self.assertIn("LIMIT 10", capped_sql)

    def test_enforce_safety_limit_caps_excessive_limit(self):
        sql = "SELECT * FROM logistics_data LIMIT 5000;"
        capped_sql, is_capped = enforce_safety_limit(sql, default_limit=100, max_limit=500)
        self.assertTrue(is_capped)
        self.assertIn("LIMIT 500", capped_sql)

    def test_data_dictionary_completeness(self):
        self.assertIn("delay_probability", LOGISTICS_DATA_DICTIONARY)
        self.assertIn("shipping_costs", LOGISTICS_DATA_DICTIONARY)
        self.assertIn("risk_classification", LOGISTICS_DATA_DICTIONARY)
        prompt_text = get_data_dictionary_prompt()
        self.assertIn("Low Risk", prompt_text)
        self.assertIn("High Risk", prompt_text)


class TestSqlAndAssumptionsExtraction(unittest.TestCase):
    def test_extract_sql_and_assumptions(self):
        raw = """ASSUMPTIONS: Assumed high delay means delay_probability >= 0.70.
SQL:
```sql
SELECT * FROM logistics_data WHERE delay_probability >= 0.70;
```"""
        sql, assumptions = clean_sql_and_assumptions(raw)
        self.assertEqual(sql, "SELECT * FROM logistics_data WHERE delay_probability >= 0.70;")
        self.assertIn("delay_probability >= 0.70", assumptions)

    def test_extract_plain_sql(self):
        raw = "```sql\nSELECT COUNT(*) FROM logistics_data;\n```"
        sql, assumptions = clean_sql_and_assumptions(raw)
        self.assertEqual(sql, "SELECT COUNT(*) FROM logistics_data;")
        self.assertTrue(len(assumptions) > 0)


class TestSchemaInspection(unittest.TestCase):
    def test_schema_contains_table_and_columns(self):
        schema = get_schema()
        self.assertIn("Table: logistics_data", schema)
        self.assertIn("shipping_costs", schema)
        self.assertIn("delay_probability", schema)


class TestEndToEndAskDatabase(unittest.TestCase):
    def test_unsafe_prompt_blocked(self):
        with self.assertRaises(ValueError) as ctx:
            ask_database("Delete all records from the table")
        self.assertIn("Blocked unsafe query", str(ctx.exception))

    def test_valid_question_with_summary_and_assumptions(self):
        result = ask_database("What are the top 3 routes by average shipping cost?")
        self.assertIsInstance(result, QueryResult)
        self.assertIsNotNone(result.data)
        self.assertGreater(len(result.data), 0)
        self.assertTrue(result.sql.lower().startswith("select"))
        self.assertTrue(len(result.summary) > 0)
        self.assertTrue(len(result.assumptions) > 0)


if __name__ == "__main__":
    unittest.main()
