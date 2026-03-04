import sqlite3
import os

db_path = "data/akquise.db"
print(f"Connecting to {db_path}...")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT id, name, email FROM leads WHERE email LIKE 'info@%' AND email NOT LIKE '%.'")
rows = cursor.fetchall()

print(f"Found {len(rows)} fake emails to remove:")
for row in rows[:5]:
    print(f" - {row[1]}: {row[2]}")

if len(rows) > 0:
    cursor.execute("DELETE FROM leads WHERE email LIKE 'info@%' AND email NOT LIKE '%.' AND source != 'Manuell'")
    print(f"Deleted {cursor.rowcount} fake emails.")
    conn.commit()

conn.close()
print("Done.")
