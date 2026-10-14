import sqlite3
import json

db_path = r"D:\OFFLINE DATA\disease_catalog\master_disease_catalog.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT id, hallmarks_json, synonyms_json FROM diseases WHERE name = 'Heroin'")
row = cur.fetchone()
if row:
    print("Current Heroin row:", row)
    hallmarks = json.loads(row[1]) if row[1] else []
    clean_hallmarks = [h for h in hallmarks if len(h) >= 3 and h.lower() != "h"]
    print("Clean hallmarks:", clean_hallmarks)
    cur.execute("UPDATE diseases SET hallmarks_json = ? WHERE id = ?", (json.dumps(clean_hallmarks), row[0]))
    conn.commit()
    print("Heroin hallmarks updated successfully in master_disease_catalog.db!")
conn.close()
