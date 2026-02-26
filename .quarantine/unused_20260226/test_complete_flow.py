#!/usr/bin/env python3.12
"""
Comprehensive flow debug script to trace the complete round trip flow
"""
import os
import sys
import django
import json

# Setup backend Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'microservices/backend-service'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from flight.models import Flight, Place, Week
from flight.serializers import FlightSerializer, PlaceSerializer
from datetime import datetime
from rest_framework.serializers import ModelSerializer

print("="*80)
print("COMPREHENSIVE ROUND TRIP FLOW DEBUG")
print("="*80)

# Test parameters
origin_code = 'DFW'
destination_code = 'ORD'
depart_date_str = '2025-01-24'
return_date_str = '2025-01-26'
seat_class = 'economy'
trip_type = '2'

print(f"\n[STEP 1] Input Parameters:")
print(f"  Origin: {origin_code}")
print(f"  Destination: {destination_code}")
print(f"  Depart Date: {depart_date_str}")
print(f"  Return Date: {return_date_str}")
print(f"  Seat Class: {seat_class}")
print(f"  Trip Type: {trip_type}")

try:
    # Parse dates
    depart_date = datetime.strptime(depart_date_str, '%Y-%m-%d').date()
    return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()
    
    # Get places
    origin = Place.objects.get(code__iexact=origin_code)
    destination = Place.objects.get(code__iexact=destination_code)
    
    print(f"\n[STEP 2] Backend - Fetch Flight Data:")
    print(f"  Origin: {origin.code} - {origin.city}")
    print(f"  Destination: {destination.code} - {destination.city}")
    
    # Search outbound flights
    depart_flight_day = Week.objects.get(number=depart_date.weekday())
    flights_queryset = Flight.objects.filter(
        origin=origin,
        destination=destination,
        depart_day=depart_flight_day,
        airline__icontains='American Airlines'
    ).exclude(economy_fare=0).order_by('economy_fare')
    
    print(f"  Found {flights_queryset.count()} outbound flights")
    
    # Serialize outbound flights
    flights_serialized = FlightSerializer(flights_queryset, many=True).data
    print(f"  Serialized {len(flights_serialized)} outbound flights")
    
    if flights_serialized:
        flight1 = flights_serialized[0]
        print(f"\n  First outbound flight (serialized):")
        print(f"    - ID: {flight1.get('id')}")
        print(f"    - depart_time: '{flight1.get('depart_time')}' (type: {type(flight1.get('depart_time')).__name__})")
        print(f"    - arrival_time: '{flight1.get('arrival_time')}' (type: {type(flight1.get('arrival_time')).__name__})")
        print(f"    - airline: '{flight1.get('airline')}'")
        print(f"    - plane: '{flight1.get('plane')}'")
        
        # Test string slicing
        dt = flight1.get('depart_time')
        at = flight1.get('arrival_time')
        print(f"    - depart_time[:5]: '{dt[:5] if dt else 'None'}'")
        print(f"    - arrival_time[:5]: '{at[:5] if at else 'None'}'")
    
    # Search return flights
    return_flight_day = Week.objects.get(number=return_date.weekday())
    flights2_queryset = Flight.objects.filter(
        origin=destination,
        destination=origin,
        depart_day=return_flight_day,
        airline__icontains='American Airlines'
    ).exclude(economy_fare=0).order_by('economy_fare')
    
    print(f"\n  Found {flights2_queryset.count()} return flights")
    
    # Serialize return flights
    flights2_serialized = FlightSerializer(flights2_queryset, many=True).data
    print(f"  Serialized {len(flights2_serialized)} return flights")
    
    if flights2_serialized:
        flight2 = flights2_serialized[0]
        print(f"\n  First return flight (serialized):")
        print(f"    - ID: {flight2.get('id')}")
        print(f"    - depart_time: '{flight2.get('depart_time')}' (type: {type(flight2.get('depart_time')).__name__})")
        print(f"    - arrival_time: '{flight2.get('arrival_time')}' (type: {type(flight2.get('arrival_time')).__name__})")
        print(f"    - airline: '{flight2.get('airline')}'")
        print(f"    - plane: '{flight2.get('plane')}'")
        
        # Test string slicing
        dt = flight2.get('depart_time')
        at = flight2.get('arrival_time')
        print(f"    - depart_time[:5]: '{dt[:5] if dt else 'None'}'")
        print(f"    - arrival_time[:5]: '{at[:5] if at else 'None'}'")
    
    # Build API response
    response_data = {
        'flights': flights_serialized,
        'flights2': flights2_serialized,
        'origin': PlaceSerializer(origin).data,
        'origin2': PlaceSerializer(destination).data,
        'destination': PlaceSerializer(destination).data,
        'destination2': PlaceSerializer(origin).data,
        'depart_date': depart_date,
        'return_date': return_date,
        'seat_class': seat_class,
        'trip_type': trip_type
    }
    
    print(f"\n[STEP 3] Backend - API Response Structure:")
    print(f"  'flights' count: {len(response_data['flights'])}")
    print(f"  'flights2' count: {len(response_data['flights2'])}")
    print(f"  'origin': {response_data['origin']['code']}")
    print(f"  'destination': {response_data['destination']['code']}")
    print(f"  'origin2': {response_data['origin2']['code']}")
    print(f"  'destination2': {response_data['destination2']['code']}")
    
    # Simulate UI service processing
    print(f"\n[STEP 4] UI Service - Process Response:")
    flights = response_data.get('flights', [])
    flights2 = response_data.get('flights2', [])
    
    print(f"  Received {len(flights)} flights")
    print(f"  Received {len(flights2)} return flights")
    
    # Convert time display (as UI service does)
    for flight in flights:
        if 'depart_time' in flight and flight['depart_time']:
            flight['depart_time_display'] = flight['depart_time'][:5]
        if 'arrival_time' in flight and flight['arrival_time']:
            flight['arrival_time_display'] = flight['arrival_time'][:5]
    
    for flight in flights2:
        if 'depart_time' in flight and flight['depart_time']:
            flight['depart_time_display'] = flight['depart_time'][:5]
        if 'arrival_time' in flight and flight['arrival_time']:
            flight['arrival_time_display'] = flight['arrival_time'][:5]
    
    if flights:
        print(f"\n  First flight after processing:")
        print(f"    - depart_time: {flights[0].get('depart_time')}")
        print(f"    - depart_time_display: {flights[0].get('depart_time_display')}")
        print(f"    - arrival_time: {flights[0].get('arrival_time')}")
        print(f"    - arrival_time_display: {flights[0].get('arrival_time_display')}")
    
    if flights2:
        print(f"\n  First return flight after processing:")
        print(f"    - depart_time: {flights2[0].get('depart_time')}")
        print(f"    - depart_time_display: {flights2[0].get('depart_time_display')}")
        print(f"    - arrival_time: {flights2[0].get('arrival_time')}")
        print(f"    - arrival_time_display: {flights2[0].get('arrival_time_display')}")
    
    # Simulate template rendering
    print(f"\n[STEP 5] Template Rendering:")
    
    from django.template import Template, Context
    
    # Test header rendering
    header_template = '{{flights.0.depart_time|slice:":5"}} • {{flights.0.arrival_time|slice:":5"}}'
    header = Template(header_template)
    result1 = header.render(Context({'flights': flights}))
    print(f"  Flight1 header: {result1}")
    
    header_template2 = '{{flights2.0.depart_time|slice:":5"}} • {{flights2.0.arrival_time|slice:":5"}}'
    header2 = Template(header_template2)
    result2 = header2.render(Context({'flights2': flights2}))
    print(f"  Flight2 header: {result2}")
    
    # Test radio button rendering
    radio_template = 'data-depart="{{flights.0.depart_time|slice:":5"}}" data-arrive="{{flights.0.arrival_time|slice:":5"}}"'
    radio = Template(radio_template)
    result_radio1 = radio.render(Context({'flights': flights}))
    print(f"\n  Flight1 radio attrs: {result_radio1}")
    
    radio_template2 = 'data-depart="{{flights2.0.depart_time|slice:":5"}}" data-arrive="{{flights2.0.arrival_time|slice:":5"}}"'
    radio2 = Template(radio_template2)
    result_radio2 = radio2.render(Context({'flights2': flights2}))
    print(f"  Flight2 radio attrs: {result_radio2}")
    
    # Summary
    print(f"\n[STEP 6] VALIDATION:")
    if '05:05' in result2 and '07:40' in result2:
        print(f"  ✓ Return flight header RENDERING CORRECTLY")
    else:
        print(f"  ✗ Return flight header NOT RENDERING - got: '{result2}'")
    
    if 'data-depart="' in result_radio2:
        depart_val = result_radio2.split('data-depart="')[1].split('"')[0]
        arrive_val = result_radio2.split('data-arrive="')[1].split('"')[0]
        print(f"  ✓ Return flight radio data-depart='{depart_val}' data-arrive='{arrive_val}'")
        if depart_val and arrive_val and depart_val != '' and arrive_val != '':
            print(f"  ✓ Return flight radio data attributes ARE POPULATED")
        else:
            print(f"  ✗ Return flight radio data attributes ARE EMPTY")
    else:
        print(f"  ✗ Return flight radio data attributes not found")
    
except Exception as e:
    print(f"\n[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("END DEBUG")
print("="*80)
