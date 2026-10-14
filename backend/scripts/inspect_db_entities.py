import sys
import os
import sqlite3

db_path = r"D:\OFFLINE DATA\disease_catalog\master_disease_catalog.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT name, icd10, hallmarks_json, synonyms_json FROM diseases WHERE name LIKE '%Heroin%' OR name = 'Heart Attack'")
for r in cur.fetchall():
    print(f"Name: {r[0]} | ICD10: {r[1]} | Hallmarks: {r[2]} | Synonyms: {r[3]}")
