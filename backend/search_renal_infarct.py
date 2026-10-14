import sqlite3

db_path = r"D:\OFFLINE DATA\disease_catalog\master_disease_catalog.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT id, name, icd10 FROM diseases WHERE icd10 LIKE 'D59.3%' OR name LIKE '%hemolytic%uremic%'")
rows = cur.fetchall()
print(f"Found {len(rows)} matching:")
for r in rows:
    print(r)
