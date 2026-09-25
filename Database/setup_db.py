import sqlite3
import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import BASE_DIR, DB_PATH

csv_path = BASE_DIR / "Data" / "Raw" / "dynamic_supply_chain_logistics_dataset.csv"

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(csv_path)
conn = sqlite3.connect(DB_PATH)
df.to_sql("logistics_data", conn, if_exists="replace", index=False)
conn.commit()
conn.close()

print(f"Imported {len(df)} rows into {DB_PATH}")