import sqlite3
import json

db_path = r"D:\OFFLINE DATA\disease_catalog\master_disease_catalog.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

targets = [
    "Cholecystitis", "Acute cholecystitis", "Gallstone", "Biliary colic",
    "Thrombotic thrombocytopenic purpura",
    "Whipple disease",
    "Strongyloidiasis",
    "Relapsing polychondritis",
    "Periodic paralysis", "Hypokalemic periodic paralysis",
    "Amyloidosis", "AL amyloidosis",
    "Renal infarction",
    "Hemolytic uremic syndrome",
    "Pheochromocytoma",
    "Pituitary apoplexy", "Sheehan syndrome",
    "Cushing's syndrome", "Cushing syndrome",
    "Behçet disease", "Behcet disease"
]

for t in targets:
    cur.execute("SELECT id, name, hallmarks_json FROM diseases WHERE name = ? OR name LIKE ? LIMIT 3", (t, f"%{t}%"))
    rows = cur.fetchall()
    print(f"=== Target: {t} (found {len(rows)}) ===")
    for r in rows:
        h = json.loads(r[2]) if r[2] else []
        print(f"  ID {r[0]}: {r[1]} -> Hallmarks ({len(h)}): {h[:8]}")
