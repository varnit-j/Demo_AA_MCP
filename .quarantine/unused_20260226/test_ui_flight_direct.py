import os
import sys
import django

sys.path.insert(0, 'd:\\varnit\\demo\\2101_f\\2101_UI_Chang\\AA_Flight_booking_UI_DEMO\\microservices\\ui-service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ui.settings')
django.setup()

from django.test import RequestFactory
from ui.views import flight

# Test ONE-WAY search
print("=" * 80)
print("TEST 1: ONE-WAY FLIGHT SEARCH")
print("=" * 80)
factory = RequestFactory()
request = factory.get('/flight?Origin=DFW&Destination=ORD&DepartDate=2026-02-15&SeatClass=economy&TripType=1')
response = flight(request)
print(f"Response status code: {response.status_code}")
print(f"Response type: {type(response)}")

# Test ROUND-TRIP search
print("\n" + "=" * 80)
print("TEST 2: ROUND-TRIP FLIGHT SEARCH")
print("=" * 80)
request2 = factory.get('/flight?Origin=DFW&Destination=ORD&DepartDate=2026-02-15&ReturnDate=2026-02-18&SeatClass=economy&TripType=2')
response2 = flight(request2)
print(f"Response status code: {response2.status_code}")
print(f"Response type: {type(response2)}")
