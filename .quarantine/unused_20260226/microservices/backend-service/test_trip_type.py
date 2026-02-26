import os
import django
import sys

sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from flight.simple_views import flight_search
from django.test import RequestFactory
import json

# Test one-way search with different trip_type values
factory = RequestFactory()

# Test 1: trip_type as string '1'
print('=== TEST 1: trip_type as string "1" ===')
request = factory.get('/api/flights/search/?origin=DFW&destination=ORD&depart_date=2026-02-15&seat_class=economy&trip_type=1')
response = flight_search(request)
data = json.loads(response.content)
print(f'One-Way (trip_type=1): {len(data.get("flights", []))} flights')

# Test 2: trip_type with extra spaces
print('\n=== TEST 2: trip_type with spaces "1 " ===')
request = factory.get('/api/flights/search/?origin=DFW&destination=ORD&depart_date=2026-02-15&seat_class=economy&trip_type=1%20')
response = flight_search(request)
data = json.loads(response.content)
print(f'One-Way (trip_type="1 "): {len(data.get("flights", []))} flights')

# Test 3: Check round-trip with whitespace on trip_type
print('\n=== TEST 3: round-trip with spaces "2 " ===')
request = factory.get('/api/flights/search/?origin=DFW&destination=ORD&depart_date=2026-02-15&return_date=2026-02-18&seat_class=economy&trip_type=2%20')
response = flight_search(request)
data = json.loads(response.content)
print(f'Round-Trip (trip_type="2 "): {len(data.get("flights", []))} outbound flights')
print(f'Round-Trip (trip_type="2 "): {len(data.get("flights2", []))} return flights')
