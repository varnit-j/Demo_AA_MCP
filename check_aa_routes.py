"""Check American Airlines DFW-ORD flights"""
import sqlite3

conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()

print("="*80)
print("AMERICAN AIRLINES: DALLAS <-> CHICAGO")
print("="*80)

# Check DFW -> ORD American
cursor.execute("""
    SELECT f.id, f.economy_fare, f.airline FROM flight_flight f
    JOIN flight_place p1 ON f.origin_id = p1.id
    JOIN flight_place p2 ON f.destination_id = p2.id
    WHERE p1.code='DFW' AND p2.code='ORD' AND f.airline LIKE '%American%'
""")
flights = cursor.fetchall()
print(f"\nDFW -> ORD (American Airlines): {len(flights)}")
for f in flights:
    print(f"  Flight ID: {f[0]}, Fare: ${f[1]}, Airline: {f[2]}")

# Check ORD -> DFW American
cursor.execute("""
    SELECT f.id, f.economy_fare, f.airline FROM flight_flight f
    JOIN flight_place p1 ON f.origin_id = p1.id
    JOIN flight_place p2 ON f.destination_id = p2.id
    WHERE p1.code='ORD' AND p2.code='DFW' AND f.airline LIKE '%American%'
""")
flights = cursor.fetchall()
print(f"ORD -> DFW (American Airlines): {len(flights)}")
for f in flights:
    print(f"  Flight ID: {f[0]}, Fare: ${f[1]}, Airline: {f[2]}")

# Find a route that HAS American Airlines flights
cursor.execute("""
    SELECT DISTINCT p1.code, p2.code, COUNT(*) as cnt
    FROM flight_flight f
    JOIN flight_place p1 ON f.origin_id = p1.id
    JOIN flight_place p2 ON f.destination_id = p2.id
    WHERE f.airline LIKE '%American%'
    GROUP BY p1.code, p2.code
    ORDER BY cnt DESC
    LIMIT 5
""")
routes = cursor.fetchall()
print(f"\nTop American Airlines routes:")
for r in routes:
    print(f"  {r[0]} -> {r[1]}: {r[2]} flights")

conn.close()
print("\n" + "="*80)
