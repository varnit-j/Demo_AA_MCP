"""
Test to inspect template rendering directly
"""
import requests
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:8000"

params = {
    'Origin': 'DFW',
    'Destination': 'ORD',
    'TripType': '2',
    'DepartDate': '2026-02-10',
    'ReturnDate': '2026-02-17',
    'SeatClass': 'economy'
}

response = requests.get(f"{BASE_URL}/flight", params=params)
soup = BeautifulSoup(response.text, 'html.parser')

print("="*80)
print("TEMPLATE RENDERING ANALYSIS")
print("="*80)

# Find trip-identifier value
trip_id = soup.find('input', {'id': 'trip-identifier'})
if trip_id:
    print(f"\nTrip Identifier Value: {trip_id.get('value')}")
else:
    print("\nTrip Identifier NOT FOUND")

# Find query-result-div
qrd = soup.find('div', {'class': lambda x: x and 'query-result-div' in x})
if qrd:
    print(f"\nquery-result-div classes: {qrd.get('class')}")
    print(f"query-result-div style: {qrd.get('style')}")
    print(f"query-result-div inner text (first 100 chars): {qrd.get_text()[:100]}")
else:
    print("\nquery-result-div NOT FOUND")

# Find query-result-div-2
qrd2_list = soup.find_all('div', {'class': lambda x: x and 'query-result-div-2' in x})
if qrd2_list:
    qrd2 = qrd2_list[0]
    print(f"\nquery-result-div-2 classes: {qrd2.get('class')}")
    print(f"query-result-div-2 style: {qrd2.get('style')}")
    has_panel_half = 'panel-half' in (qrd2.get('class') or [])
    print(f"query-result-div-2 has panel-half: {has_panel_half}")
else:
    print("\nquery-result-div-2 NOT FOUND")

# Find round-trip-panels-wrapper
wrapper = soup.find('div', {'class': lambda x: x and 'round-trip-panels-wrapper' in (x or [])})
if wrapper:
    print(f"\nround-trip-panels-wrapper FOUND")
    print(f"  Classes: {wrapper.get('class')}")
else:
    print("\nround-trip-panels-wrapper NOT FOUND")

# Check for flights and flights2 divs
flights_div = soup.find('div', {'id': 'flights_div'})
flights_div2 = soup.find('div', {'id': 'flights_div2'})

print(f"\nFlights div (outbound): {'FOUND' if flights_div else 'NOT FOUND'}")
if flights_div:
    boxes = flights_div.find_all('div', {'class': lambda x: x and 'each-flight-div-box' in (x or [])})
    print(f"  Flight boxes in outbound: {len(boxes)}")

print(f"Flights div2 (return): {'FOUND' if flights_div2 else 'NOT FOUND'}")
if flights_div2:
    boxes2 = flights_div2.find_all('div', {'class': lambda x: x and 'each-flight-div-box' in (x or [])})
    print(f"  Flight boxes in return: {len(boxes2)}")

print("\n" + "="*80)
