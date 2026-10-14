import sqlite3
import json

db_path = r"D:\OFFLINE DATA\disease_catalog\master_disease_catalog.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT id, name, hallmarks_json FROM diseases WHERE name LIKE '%thrombotic thrombocytopenic%' OR name LIKE '%cholecyst%' OR name LIKE '%gallstone%'")
rows = cur.fetchall()
for r in rows:
    h = json.loads(r[2]) if r[2] else []
    print(f"ID {r[0]}: {r[1]} -> Hallmarks: {h}")
