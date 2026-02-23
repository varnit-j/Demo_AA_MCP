"""Check American Airlines flights"""
import sqlite3

conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()

# Check American Airlines flights
cursor.execute("""
    SELECT COUNT(*) FROM flight_flight WHERE airline LIKE '%American%'
""")
count = cursor.fetchone()[0]
print(f"Total American Airlines flights: {count}")

# Check available airlines
cursor.execute("""
    SELECT DISTINCT airline FROM flight_flight ORDER BY airline
""")
airlines = cursor.fetchall()
print(f"\nAvailable airlines: {len(airlines)}")
for a in airlines:
    cursor.execute("SELECT COUNT(*) FROM flight_flight WHERE airline = ?", (a[0],))
    c = cursor.fetchone()[0]
    print(f"  {a[0]}: {c} flights")

conn.close()
