import os
import django
import sys

sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from flight.simple_views import flight_search
from django.test import RequestFactory
import json

factory = RequestFactory()

# Debug the exact comparison logic
print('=== DEBUGGING trip_type COMPARISON ===')

# Fetch with trip_type='2' (clean)
request = factory.get('/api/flights/search/?origin=DFW&destination=ORD&depart_date=2026-02-15&return_date=2026-02-18&seat_class=economy&trip_type=2')
response = flight_search(request)
data = json.loads(response.content)
print(f'trip_type="2" (clean): outbound={len(data.get("flights", []))}, return={len(data.get("flights2", []))}')
print(f'  Return date in response: {data.get("return_date")}')

# Fetch with different return date (Sunday 2026-02-15 was depart, 2026-02-18 is return)
print('\n=== Testing different return dates ===')
for ret_date in ['2026-02-16', '2026-02-17', '2026-02-18', '2026-02-22']:
    url = f'/api/flights/search/?origin=DFW&destination=ORD&depart_date=2026-02-15&return_date={ret_date}&seat_class=economy&trip_type=2'
    request = factory.get(url)
    response = flight_search(request)
    data = json.loads(response.content)
    ret_flights = len(data.get("flights2", []))
    out_flights = len(data.get("flights", []))
    print(f'return_date={ret_date} ({ret_date[5:]}): outbound={out_flights}, return={ret_flights}')
