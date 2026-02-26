import os
import django
import sys

sys.path.insert(0, 'd:\\varnit\\demo\\2101_f\\2101_UI_Chang\\AA_Flight_booking_UI_DEMO\\microservices\\ui-service')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ui.settings')
django.setup()

from django.test import RequestFactory
from ui.views import flight

# Simulate form submission for one-way flight search
factory = RequestFactory()

# One-way flight search
print('=== TEST ONE-WAY FLIGHT SEARCH ===')
request = factory.get('/flight?Origin=DFW&Destination=ORD&DepartDate=2026-02-15&SeatClass=economy&TripType=1')
response = flight(request)
print(f'Response status: {response.status_code}')

# Try to parse the context
if hasattr(response, 'context_data'):
    print(f'Context flights: {len(response.context_data.get("flights", []))}')

print('\n=== TEST ROUND-TRIP FLIGHT SEARCH ===')
request = factory.get('/flight?Origin=DFW&Destination=ORD&DepartDate=2026-02-15&ReturnDate=2026-02-18&SeatClass=economy&TripType=2')
response = flight(request)
print(f'Response status: {response.status_code}')

if hasattr(response, 'context_data'):
    print(f'Context outbound flights: {len(response.context_data.get("flights", []))}')
    print(f'Context return flights: {len(response.context_data.get("flights2", []))}')
