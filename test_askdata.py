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
    clear_query_cache,
    get_cache_size,
    QueryResult,
)
from data_dictionary import get_data_dictionary_prompt, LOGISTICS_DATA_DICTIONARY
from chart_engine import (
    detect_best_chart_type,
    has_gps_coordinates,
    render_dynamic_visualization,
    build_bar_chart,
    build_gps_fleet_map,
)
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
        self.assertTrue(is_safe_query("SELECT * FROM logistics_data WHERE cargo_condition_status = 'updated'"))
        self.assertTrue(is_safe_query("SELECT * FROM logistics_data WHERE risk_classification = 'drop'"))
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


class TestQueryCache(unittest.TestCase):
    def setUp(self):
        clear_query_cache()

    def test_cache_hit_and_purge(self):
        self.assertEqual(get_cache_size(), 0)
        # Execute query first time (fresh)
        res1 = ask_database("What is the average shipping cost across all records?", summarize=False)
        self.assertFalse(res1.from_cache)
        self.assertGreaterEqual(get_cache_size(), 1)

        # Execute same query second time (cached)
        res2 = ask_database("What is the average shipping cost across all records?", summarize=False)
        self.assertTrue(res2.from_cache)
        self.assertEqual(len(res1.data), len(res2.data))

        # Clear cache
        purged = clear_query_cache()
        self.assertGreaterEqual(purged, 1)
        self.assertEqual(get_cache_size(), 0)


class TestChartEngine(unittest.TestCase):
    def test_detect_gps_coordinates(self):
        df_gps = pd.DataFrame({
            "vehicle_gps_latitude": [40.7128, 34.0522],
            "vehicle_gps_longitude": [-74.0060, -118.2437],
            "delay_probability": [0.8, 0.3],
        })
        has_gps, lat, lon = has_gps_coordinates(df_gps)
        self.assertTrue(has_gps)
        self.assertEqual(lat, "vehicle_gps_latitude")
        self.assertEqual(lon, "vehicle_gps_longitude")
        self.assertEqual(detect_best_chart_type(df_gps), "map")

        fig = build_gps_fleet_map(df_gps, lat, lon)
        self.assertIsNotNone(fig)

    def test_detect_kpi_type(self):
        df_kpi = pd.DataFrame({"total_orders": [1200], "avg_cost": [450.50]})
        self.assertEqual(detect_best_chart_type(df_kpi), "kpi")

    def test_detect_categorical_bar(self):
        df_cat = pd.DataFrame({
            "risk_classification": ["Low Risk", "Moderate Risk", "High Risk"],
            "avg_cost": [100.0, 200.0, 300.0],
        })
        self.assertEqual(detect_best_chart_type(df_cat), "bar")
        fig = build_bar_chart(df_cat)
        self.assertIsNotNone(fig)

    def test_detect_time_series_line(self):
        df_time = pd.DataFrame({
            "timestamp": ["2021-01-01", "2021-01-02", "2021-01-03"],
            "fuel_burn": [5.1, 5.8, 6.2],
        })
        self.assertEqual(detect_best_chart_type(df_time), "line")

    def test_detect_scatter_plot(self):
        df_scatter = pd.DataFrame({
            "traffic_congestion": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "fuel_consumption": [2.1, 2.5, 3.2, 3.8, 4.2, 5.0, 5.5, 6.1, 6.8, 7.5],
        })
        self.assertEqual(detect_best_chart_type(df_scatter), "scatter")


class TestMultiTurnContext(unittest.TestCase):
    def test_ask_database_with_chat_history(self):
        history = [
            {
                "question": "What are the top 3 routes by highest delay probability?",
                "sql": "SELECT route_risk_level, delay_probability FROM logistics_data ORDER BY delay_probability DESC LIMIT 3;",
                "summary": "The top 3 routes feature delay probabilities of 90% or higher.",
            }
        ]
        result = ask_database(
            question="What is the average shipping cost for those specific routes?",
            chat_history=history,
            summarize=True,
        )
        self.assertIsInstance(result, QueryResult)
        self.assertIsNotNone(result.data)
        self.assertTrue(result.sql.lower().startswith("select"))


if __name__ == "__main__":
    unittest.main()
