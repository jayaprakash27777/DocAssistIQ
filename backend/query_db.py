import sqlite3

conn = sqlite3.connect('backend/master_disease_catalog.db')
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
print("Tables:", tables)

for t in tables:
    tname = t[0]
    c.execute(f"PRAGMA table_info({tname})")
    cols = [col[1] for col in c.fetchall()]
    print(f"Table {tname}: {cols}")
