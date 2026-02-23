import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capstone.settings')
django.setup()

from flight.models import Flight, Place, Week
from datetime import datetime

print("\n" + "="*80)
print("CHECKING FLIGHT DATA")
print("="*80)

try:
    total = Flight.objects.count()
    print(f"\nTotal flights in database: {total}")
    
    # Check places
    nyc = Place.objects.get(code='NYC')
    lax = Place.objects.get(code='LAX')
    print(f"\nNYC: {nyc}")
    print(f"LAX: {lax}")
    
    # Feb 10, 2026 weekday check
    feb10 = datetime(2026, 2, 10)
    weekday = feb10.weekday()
    print(f"\nFeb 10, 2026 weekday: {weekday}")
    
    week = Week.objects.get(number=weekday)
    print(f"Week object: {week}")
    
    # Outbound flights NYC->LAX
    print(f"\n--- OUTBOUND (NYC -> LAX) ---")
    outbound = Flight.objects.filter(
        origin=nyc,
        destination=lax,
        depart_day=week,
        airline__icontains='American'
    ).exclude(economy_fare=0)
    print(f"Found {outbound.count()} outbound flights")
    for f in outbound[:3]:
        print(f"  {f.id}: {f.depart_time} -> {f.arrival_time} ${f.economy_fare}")
    
    # Return flights LAX->NYC (same day of week)
    print(f"\n--- RETURN (LAX -> NYC) ---")
    return_flights = Flight.objects.filter(
        origin=lax,
        destination=nyc,
        depart_day=week,
        airline__icontains='American'
    ).exclude(economy_fare=0)
    print(f"Found {return_flights.count()} return flights")
    for f in return_flights[:3]:
        print(f"  {f.id}: {f.depart_time} -> {f.arrival_time} ${f.economy_fare}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
