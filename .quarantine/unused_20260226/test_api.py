"""
Test script to verify round trip flight search API
Run in browser: http://localhost:8000/flight/?Origin=NYC&Destination=LAX&TripType=2&DepartDate=2026-02-10&ReturnDate=2026-02-17&SeatClass=economy
"""

import requests
import json

BASE_URL = "http://localhost:8000"

# Test 1: Round trip flight search
print("\n" + "="*80)
print("TEST 1: ROUND TRIP FLIGHT SEARCH")
print("="*80)

params = {
    'Origin': 'DFW',
    'Destination': 'ORD',
    'TripType': '2',  # Round trip
    'DepartDate': '2026-02-10',
    'ReturnDate': '2026-02-17',
    'SeatClass': 'economy'
}

url = f"{BASE_URL}/flight"
print(f"\nRequest URL: {url}")
print(f"Parameters: {params}")

try:
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    print(f"Content Length: {len(response.content)} bytes")
    
    # Check if response contains both flights_div
    content = response.text
    
    outbound_count = content.count('id="flights_div"')
    return_count = content.count('id="flights_div2"')
    
    print(f"\nOutbound flights div (flights_div): {outbound_count} found")
    print(f"Return flights div (flights_div2): {return_count} found")
    
    # Check for individual flight boxes
    outbound_flights = content.count('each-flight-div-box')
    print(f"Total flight boxes found: {outbound_flights}")
    
    # Check for wrapper
    wrapper_count = content.count('round-trip-panels-wrapper')
    print(f"Round trip wrapper: {wrapper_count} found")
    
    # Check for panel-half class
    panel_half = content.count('panel-half')
    print(f"Panel-half classes: {panel_half} found")
    
    # Save response to file for manual inspection
    with open('response.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("\nFull response saved to response.html")
    
    # Extract key context variables
    if 'flights2' in content:
        print("\n✓ flights2 variable exists in response")
    else:
        print("\n✗ flights2 variable NOT found in response")
        
    if 'query-result-div-2' in content:
        print("✓ query-result-div-2 exists in response")
    else:
        print("✗ query-result-div-2 NOT found in response")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
