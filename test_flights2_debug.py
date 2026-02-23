#!/usr/bin/env python3.12
"""
Debug script to test round trip flight data flow
"""
import os
import sys
import django

# Setup Django environment for backend service
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'microservices/backend-service'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from flight.models import Flight, Place, Week
from flight.serializers import FlightSerializer
from datetime import datetime

# Test parameters
origin_code = 'DFW'
destination_code = 'ORD'
depart_date_str = '2025-01-24'  # Friday
return_date_str = '2025-01-26'  # Sunday

try:
    # Parse dates
    depart_date = datetime.strptime(depart_date_str, '%Y-%m-%d').date()
    return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()
    
    print(f"[TEST] Depart date: {depart_date} (weekday: {depart_date.weekday()})")
    print(f"[TEST] Return date: {return_date} (weekday: {return_date.weekday()})")
    
    # Get places
    origin = Place.objects.get(code__iexact=origin_code)
    destination = Place.objects.get(code__iexact=destination_code)
    
    print(f"[TEST] Origin: {origin.code} - {origin.city}")
    print(f"[TEST] Destination: {destination.code} - {destination.city}")
    
    # Search outbound flights
    depart_flight_day = Week.objects.get(number=depart_date.weekday())
    flights = Flight.objects.filter(
        origin=origin,
        destination=destination,
        depart_day=depart_flight_day,
        airline__icontains='American Airlines'
    ).exclude(economy_fare=0).order_by('economy_fare')
    
    print(f"\n[TEST] Found {flights.count()} outbound flights")
    if flights.exists():
        flight = flights.first()
        print(f"[TEST] First outbound flight: {flight.id}")
        print(f"[TEST]   - depart_time: {flight.depart_time} (type: {type(flight.depart_time)})")
        print(f"[TEST]   - arrival_time: {flight.arrival_time} (type: {type(flight.arrival_time)})")
        serialized = FlightSerializer(flight).data
        print(f"[TEST] Serialized outbound flight: {serialized}")
    
    # Search return flights
    return_flight_day = Week.objects.get(number=return_date.weekday())
    flights2 = Flight.objects.filter(
        origin=destination,
        destination=origin,
        depart_day=return_flight_day,
        airline__icontains='American Airlines'
    ).exclude(economy_fare=0).order_by('economy_fare')
    
    print(f"\n[TEST] Found {flights2.count()} return flights")
    if flights2.exists():
        flight2 = flights2.first()
        print(f"[TEST] First return flight: {flight2.id}")
        print(f"[TEST]   - depart_time: {flight2.depart_time} (type: {type(flight2.depart_time)})")
        print(f"[TEST]   - arrival_time: {flight2.arrival_time} (type: {type(flight2.arrival_time)})")
        serialized2 = FlightSerializer(flight2).data
        print(f"[TEST] Serialized return flight: {serialized2}")
        print(f"[TEST] Serialized depart_time: '{serialized2.get('depart_time')}' (type: {type(serialized2.get('depart_time'))})")
        print(f"[TEST] Serialized arrival_time: '{serialized2.get('arrival_time')}' (type: {type(serialized2.get('arrival_time'))})")
        
        # Test slicing
        dt = serialized2.get('depart_time')
        at = serialized2.get('arrival_time')
        if dt:
            print(f"[TEST] depart_time[:5] = '{dt[:5]}'")
        if at:
            print(f"[TEST] arrival_time[:5] = '{at[:5]}'")
    
except Exception as e:
    print(f"[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()
