import sqlite3
import json

db_path = r"D:\OFFLINE DATA\disease_catalog\master_disease_catalog.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT id, name, hallmarks_json, data_json FROM diseases WHERE name = 'Idiopathic intracranial hypertension'")
row = cur.fetchone()
if row:
    print("Name:", row[1])
    print("Hallmarks:", row[2])
    data = json.loads(row[3]) if row[3] else {}
    print("Cardinal symptoms:", data.get("cardinal_symptoms"))
    print("Data keys:", list(data.keys()))
else:
    print("Row not found!")
conn.close()
