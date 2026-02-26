#!/usr/bin/env python3.12
import os
import sys
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.insert(0, 'microservices/backend-service')

django.setup()

from flight.models import Flight, Place, Week
from rest_framework.serializers import ModelSerializer

class PlaceSerializer(ModelSerializer):
    class Meta:
        model = Place
        fields = ['id', 'name', 'code']

class FlightSerializer(ModelSerializer):
    origin = PlaceSerializer()
    destination = PlaceSerializer()
    class Meta:
        model = Flight
        fields = ['id', 'flight_number', 'airline', 'plane', 'origin', 'destination', 
                 'depart_time', 'arrival_time', 'depart_day', 'economy_fare', 
                 'business_fare', 'first_fare']

# Test parameters
origin_code = 'DFW'
destination_code = 'ORD'
depart_date_str = '2025-01-24'
return_date_str = '2025-01-26'
seat_class = 'economy'
trip_type = '2'

print(f"\n[TEST] Testing flight search with:")
print(f"  origin={origin_code}, destination={destination_code}")
print(f"  depart_date={depart_date_str}, return_date={return_date_str}")
print(f"  seat_class={seat_class}, trip_type={trip_type}")
print(f"  trip_type == '2': {trip_type == '2'}")
print(f"  type(trip_type): {type(trip_type)}")

# Parse dates
depart_date = datetime.strptime(depart_date_str, '%Y-%m-%d').date()
return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()

origin = Place.objects.get(code=origin_code)
destination = Place.objects.get(code=destination_code)
flight_day = Week.objects.get(number=depart_date.weekday())
return_flight_day = Week.objects.get(number=return_date.weekday())

print(f"\n[TEST] Database lookup:")
print(f"  origin: {origin} (week: {flight_day})")
print(f"  destination: {destination}")
print(f"  return_flight_day: {return_flight_day}")

# Search outbound flights
flights = Flight.objects.filter(
    origin=origin,
    destination=destination,
    depart_day=flight_day,
    airline__icontains='American Airlines'
).exclude(economy_fare=0).order_by('economy_fare')

print(f"\n[TEST] Outbound flights found: {flights.count()}")
for f in flights:
    print(f"  - {f.flight_number} ({f.plane}): ${f.economy_fare}")

# Search return flights
if trip_type == '2' and return_date:
    print(f"\n[TEST] Processing return flights (trip_type='2' is True)")
    flights2_queryset = Flight.objects.filter(
        origin=destination,  # Swapped
        destination=origin,  # Swapped
        depart_day=return_flight_day,
        airline__icontains='American Airlines'
    ).exclude(economy_fare=0).order_by('economy_fare')
    
    print(f"  Return flights query:")
    print(f"    origin={destination.code}, destination={origin.code}")
    print(f"    depart_day={return_flight_day}, airline contains 'American Airlines'")
    print(f"  Return flights found: {flights2_queryset.count()}")
    for f in flights2_queryset:
        print(f"    - {f.flight_number} ({f.plane}): ${f.economy_fare}")
else:
    print(f"\n[TEST] NOT processing return flights (trip_type='2' condition is False!)")
    print(f"  trip_type={trip_type}, return_date={return_date}")
