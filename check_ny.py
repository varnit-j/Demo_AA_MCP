"""Check New York airports"""
import sqlite3

conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()

cursor.execute("SELECT code, airport, city FROM flight_place WHERE city LIKE '%New%' OR code IN ('JFK', 'LGA', 'EWR')")
results = cursor.fetchall()

print("New York Area Airports:")
for r in results:
    print(f"  {r[0]}: {r[1]} ({r[2]})")

conn.close()
