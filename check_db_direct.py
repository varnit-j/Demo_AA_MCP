"""
Direct database check without Django shell
"""
import sqlite3
import sys

db_path = "db.sqlite3"

try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("DATABASE ANALYSIS")
    print("="*80)
    
    # Check Places
    print("\n1. PLACES IN DATABASE:")
    cursor.execute("SELECT * FROM flight_place ORDER BY code")
    places = cursor.fetchall()
    print(f"Total places: {len(places)}")
    for place in places:
        print(f"  {place['code']}: {place['city']}, {place['country']}")
    
    # Check NYC specifically
    print("\n2. NYC/LAX PLACES:")
    cursor.execute("SELECT * FROM flight_place WHERE code IN ('NYC', 'LAX')")
    nyc_lax = cursor.fetchall()
    print(f"Found: {len(nyc_lax)} places")
    for p in nyc_lax:
        print(f"  {p['code']}: {p['airport']}")
    
    # Check Weeks
    print("\n3. WEEKS (Weekdays):")
    cursor.execute("SELECT * FROM flight_week ORDER BY number")
    weeks = cursor.fetchall()
    for w in weeks:
        print(f"  {w['number']}: {w['name']}")
    
    # Check Flights - NYC to LAX
    print("\n4. FLIGHTS (NYC -> LAX):")
    cursor.execute("""
        SELECT f.id, f.origin_id, f.destination_id, f.airline, f.economy_fare, f.business_fare, f.first_fare,
               p1.code as origin, p2.code as destination
        FROM flight_flight f
        JOIN flight_place p1 ON f.origin_id = p1.id
        JOIN flight_place p2 ON f.destination_id = p2.id
        WHERE p1.code='NYC' AND p2.code='LAX'
    """)
    flights = cursor.fetchall()
    print(f"NYC -> LAX flights: {len(flights)}")
    for f in flights:
        print(f"  ID:{f['id']}, {f['origin']}->{f['destination']}, {f['airline']}, Econ:${f['economy_fare']}")
    
    # Check Flights - LAX to NYC
    print("\n5. FLIGHTS (LAX -> NYC):")
    cursor.execute("""
        SELECT f.id, f.origin_id, f.destination_id, f.airline, f.economy_fare, f.business_fare, f.first_fare,
               p1.code as origin, p2.code as destination
        FROM flight_flight f
        JOIN flight_place p1 ON f.origin_id = p1.id
        JOIN flight_place p2 ON f.destination_id = p2.id
        WHERE p1.code='LAX' AND p2.code='NYC'
    """)
    flights = cursor.fetchall()
    print(f"LAX -> NYC flights: {len(flights)}")
    for f in flights:
        print(f"  ID:{f['id']}, {f['origin']}->{f['destination']}, {f['airline']}, Econ:${f['economy_fare']}")
    
    # Check Flight-Week relationship
    print("\n6. FLIGHT-WEEK MAPPINGS:")
    cursor.execute("""
        SELECT COUNT(*) as total FROM flight_flight_depart_day
    """)
    result = cursor.fetchone()
    print(f"Total flight-week mappings: {result['total']}")
    
    # Check specific flight
    if len(flights) > 0:
        flight_id = flights[0]['id']
        cursor.execute("""
            SELECT w.number, w.name FROM flight_week w
            JOIN flight_flight_depart_day fd ON w.id = fd.week_id
            WHERE fd.flight_id = ?
        """, (flight_id,))
        weeks_for_flight = cursor.fetchall()
        print(f"\nFlight {flight_id} operates on: {len(weeks_for_flight)} days")
        for w in weeks_for_flight:
            print(f"  Day {w['number']}: {w['name']}")
    
    # Check total flights in DB
    print("\n7. TOTAL FLIGHTS IN DATABASE:")
    cursor.execute("SELECT COUNT(*) as total FROM flight_flight")
    result = cursor.fetchone()
    print(f"Total: {result['total']}")
    
    conn.close()
    print("\n" + "="*80)
    
except sqlite3.Error as e:
    print(f"Database error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
