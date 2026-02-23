#!/usr/bin/env python3.12
import os
import sys
import django

# Add project to path
sys.path.insert(0, r'd:\varnit\demo\2101_f\2101_UI_Chang\AA_Flight_booking_UI_DEMO')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capstone.settings')
django.setup()

from flight.models import Flight, Place, Week
from datetime import datetime

print("\n" + "="*80)
print("FLIGHT BOOKING SYSTEM - DATABASE VERIFICATION")
print("="*80)

# Check flights count
total_flights = Flight.objects.count()
print(f"\nTotal Flights in Database: {total_flights}")

# Check places
places = Place.objects.all()
print(f"\nAvailable Airports: {places.count()}")
for place in places[:10]:
    print(f"  - {place.code}: {place.city}, {place.country}")

# Check weeks
weeks = Week.objects.all()
print(f"\nWeek Days: {weeks.count()}")
for week in weeks:
    print(f"  - Day {week.number}: {week.name}")

# Test search: NYC to LAX
print("\n" + "-"*80)
print("TEST CASE 1: NYC to LAX (Economy)")
print("-"*80)

try:
    nyc = Place.objects.get(code='NYC')
    lax = Place.objects.get(code='LAX')
    
    # Feb 10, 2026 is a Monday (weekday = 0)
    feb10 = datetime(2026, 2, 10)
    day_of_week = feb10.weekday()
    week = Week.objects.get(number=day_of_week)
    
    print(f"NYC: {nyc}")
    print(f"LAX: {lax}")
    print(f"Feb 10, 2026 weekday: {day_of_week} ({week.name})")
    
    outbound = Flight.objects.filter(
        origin=nyc,
        destination=lax,
        depart_day=week,
        airline__icontains='American Airlines'
    ).exclude(economy_fare=0)
    
    print(f"\nOutbound Flights (NYC→LAX): {outbound.count()}")
    for flight in outbound[:5]:
        print(f"  - {flight.id}: {flight.airline} {flight.plane} ({flight.depart_time}-{flight.arrival_time}) ${flight.economy_fare}")
    
    # Return flights
    # Feb 17, 2026 is also a Monday (weekday = 0)
    feb17 = datetime(2026, 2, 17)
    day_of_week_return = feb17.weekday()
    week_return = Week.objects.get(number=day_of_week_return)
    
    print(f"\nFeb 17, 2026 weekday: {day_of_week_return} ({week_return.name})")
    
    return_flights = Flight.objects.filter(
        origin=lax,
        destination=nyc,
        depart_day=week_return,
        airline__icontains='American Airlines'
    ).exclude(economy_fare=0)
    
    print(f"\nReturn Flights (LAX→NYC): {return_flights.count()}")
    for flight in return_flights[:5]:
        print(f"  - {flight.id}: {flight.airline} {flight.plane} ({flight.depart_time}-{flight.arrival_time}) ${flight.economy_fare}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
