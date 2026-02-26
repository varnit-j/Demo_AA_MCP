"""Check Dallas-Chicago flights"""
import sqlite3
import datetime

conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()

# Dallas = DFW, Chicago = ORD
print("="*80)
print("DALLAS (DFW) <-> CHICAGO (ORD) FLIGHTS")
print("="*80)

# Check DFW -> ORD
cursor.execute("""
    SELECT f.id, f.economy_fare, f.airline FROM flight_flight f
    JOIN flight_place p1 ON f.origin_id = p1.id
    JOIN flight_place p2 ON f.destination_id = p2.id
    WHERE p1.code='DFW' AND p2.code='ORD'
    LIMIT 5
""")
flights = cursor.fetchall()
print(f"\nDFW -> ORD flights: {len(flights)}")
for f in flights:
    print(f"  Flight ID: {f[0]}, Fare: ${f[1]}, Airline: {f[2]}")

# Check ORD -> DFW
cursor.execute("""
    SELECT f.id, f.economy_fare, f.airline FROM flight_flight f
    JOIN flight_place p1 ON f.origin_id = p1.id
    JOIN flight_place p2 ON f.destination_id = p2.id
    WHERE p1.code='ORD' AND p2.code='DFW'
    LIMIT 5
""")
flights = cursor.fetchall()
print(f"ORD -> DFW flights: {len(flights)}")
for f in flights:
    print(f"  Flight ID: {f[0]}, Fare: ${f[1]}, Airline: {f[2]}")

# Check February 10, 2026 (Tuesday = weekday 1)
feb10 = datetime.date(2026, 2, 10)
feb17 = datetime.date(2026, 2, 17)
print(f"\nFebruary 10, 2026 is: {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][feb10.weekday()]}")
print(f"February 17, 2026 is: {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][feb17.weekday()]}")

# Check flights on those specific days
cursor.execute("""
    SELECT COUNT(*) FROM flight_flight f
    JOIN flight_place p1 ON f.origin_id = p1.id
    JOIN flight_place p2 ON f.destination_id = p2.id
    JOIN flight_flight_depart_day fd ON f.id = fd.flight_id
    WHERE p1.code='DFW' AND p2.code='ORD' AND fd.week_id = ?
""", (feb10.weekday(),))
count = cursor.fetchone()[0]
print(f"\nDFW -> ORD on {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][feb10.weekday()]}: {count}")

cursor.execute("""
    SELECT COUNT(*) FROM flight_flight f
    JOIN flight_place p1 ON f.origin_id = p1.id
    JOIN flight_place p2 ON f.destination_id = p2.id
    JOIN flight_flight_depart_day fd ON f.id = fd.flight_id
    WHERE p1.code='ORD' AND p2.code='DFW' AND fd.week_id = ?
""", (feb17.weekday(),))
count = cursor.fetchone()[0]
print(f"ORD -> DFW on {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][feb17.weekday()]}: {count}")

conn.close()
print("\n" + "="*80)
