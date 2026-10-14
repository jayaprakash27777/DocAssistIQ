import sqlite3
import json

db_path = r"D:\OFFLINE DATA\disease_catalog\master_disease_catalog.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT id, hallmarks_json FROM diseases WHERE name = 'Heart Attack'")
row = cur.fetchone()
if row:
    print("Current Heart Attack hallmarks:", row[1])
    # Keep specific ischemic hallmarks
    GENERIC_NON_ISCHEMIC = {"fatigue", "vomiting", "nausea", "weakness", "dizziness", "epigastric pain", "pale appearance", "anxiety"}
    hallmarks = json.loads(row[1]) if row[1] else []
    clean_hallmarks = [h for h in hallmarks if h.lower() not in GENERIC_NON_ISCHEMIC]
    print("Refined Heart Attack hallmarks:", clean_hallmarks)
    cur.execute("UPDATE diseases SET hallmarks_json = ? WHERE id = ?", (json.dumps(clean_hallmarks), row[0]))
    conn.commit()
    print("Heart Attack hallmarks updated successfully in master_disease_catalog.db!")
conn.close()
