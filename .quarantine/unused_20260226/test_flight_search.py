import os
import sys
import django

# Add backend-service to path
sys.path.insert(0, 'd:\\varnit\\demo\\2101_f\\2101_UI_Chang\\AA_Flight_booking_UI_DEMO\\microservices\\backend-service')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from flight.simple_views import flight_search
from django.test import RequestFactory
import json

# Test one-way search
factory = RequestFactory()
request = factory.get('/api/flights/search/?origin=DFW&destination=ORD&depart_date=2026-02-15&seat_class=economy&trip_type=1')

response = flight_search(request)
print('One-Way Response Status:', response.status_code)

data = json.loads(response.content)
print('One-Way Flights:', len(data.get('flights', [])))
for f in data.get('flights', [])[:2]:
    print(f"  - {f['flight_number']}: {f['depart_time']}")

# Test round-trip search
request2 = factory.get('/api/flights/search/?origin=DFW&destination=ORD&depart_date=2026-02-15&return_date=2026-02-18&seat_class=economy&trip_type=2')

response2 = flight_search(request2)
print('\nRound-Trip Response Status:', response2.status_code)

data2 = json.loads(response2.content)
print('Round-Trip Outbound Flights:', len(data2.get('flights', [])))
print('Round-Trip Return Flights:', len(data2.get('flights2', [])))
