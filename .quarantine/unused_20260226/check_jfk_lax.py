"""Check JFK-LAX flights"""
import sqlite3

conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()

# Check JFK -> LAX
cursor.execute("""
    SELECT COUNT(*) FROM flight_flight f
    JOIN flight_place p1 ON f.origin_id = p1.id
    JOIN flight_place p2 ON f.destination_id = p2.id
    WHERE p1.code='JFK' AND p2.code='LAX'
""")
count = cursor.fetchone()[0]
print(f"JFK -> LAX flights: {count}")

# Check LAX -> JFK
cursor.execute("""
    SELECT COUNT(*) FROM flight_flight f
    JOIN flight_place p1 ON f.origin_id = p1.id
    JOIN flight_place p2 ON f.destination_id = p2.id
    WHERE p1.code='LAX' AND p2.code='JFK'
""")
count = cursor.fetchone()[0]
print(f"LAX -> JFK flights: {count}")

# Check date for February 10, 2026
import datetime
feb10_2026 = datetime.date(2026, 2, 10)  # This will be a Tuesday (weekday 1)
print(f"\nFebruary 10, 2026 is a {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][feb10_2026.weekday()]}")

# Check flights on Tuesday (day 1)
cursor.execute("""
    SELECT COUNT(*) FROM flight_flight f
    JOIN flight_place p1 ON f.origin_id = p1.id
    JOIN flight_place p2 ON f.destination_id = p2.id
    JOIN flight_flight_depart_day fd ON f.id = fd.flight_id
    WHERE p1.code='JFK' AND p2.code='LAX' AND fd.week_id = 1
""")
count = cursor.fetchone()[0]
print(f"JFK -> LAX flights on Tuesday: {count}")

conn.close()
