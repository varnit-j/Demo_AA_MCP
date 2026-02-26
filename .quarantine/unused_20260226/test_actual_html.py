#!/usr/bin/env python3.12
"""
Test to check the actual rendered HTML for flights2
"""
import os
import sys
import requests

# Make request to the flight search API
url = "http://localhost:8000/flight"
params = {
    'Origin': 'DFW',
    'Destination': 'ORD',
    'DepartDate': '2025-01-24',
    'ReturnDate': '2025-01-26',
    'SeatClass': 'economy',
    'TripType': '2'
}

try:
    print("[TEST] Making request to", url)
    print("[TEST] Params:", params)
    
    response = requests.get(url, params=params, timeout=10)
    print(f"[TEST] Status code: {response.status_code}")
    
    # Find the flight2-radio input elements in the HTML
    html = response.text
    
    # Look for flight2-radio elements
    import re
    flight2_radios = re.findall(r'<input[^>]*class="[^"]*flight2-radio[^"]*"[^>]*>', html)
    
    print(f"\n[TEST] Found {len(flight2_radios)} flight2-radio elements")
    for i, radio in enumerate(flight2_radios[:3], 1):
        print(f"\n[TEST] Flight2 Radio {i}:")
        print(radio)
        
        # Extract data attributes
        data_depart = re.search(r"data-depart='([^']*)'", radio)
        data_arrive = re.search(r"data-arrive='([^']*)'", radio)
        data_plane = re.search(r"data-plane='([^']*)'", radio)
        
        if data_depart:
            print(f"  data-depart: '{data_depart.group(1)}'")
        if data_arrive:
            print(f"  data-arrive: '{data_arrive.group(1)}'")
        if data_plane:
            print(f"  data-plane: '{data_plane.group(1)}'")
    
    # Also check flight1-radio
    flight1_radios = re.findall(r'<input[^>]*class="[^"]*flight1-radio[^"]*"[^>]*>', html)
    print(f"\n[TEST] Found {len(flight1_radios)} flight1-radio elements")
    for i, radio in enumerate(flight1_radios[:1], 1):
        print(f"\n[TEST] Flight1 Radio {i}:")
        print(radio)
        
        # Extract data attributes
        data_depart = re.search(r"data-depart='([^']*)'", radio)
        data_arrive = re.search(r"data-arrive='([^']*)'", radio)
        
        if data_depart:
            print(f"  data-depart: '{data_depart.group(1)}'")
        if data_arrive:
            print(f"  data-arrive: '{data_arrive.group(1)}'")
    
except requests.exceptions.ConnectionError:
    print("[ERROR] Could not connect to http://localhost:8000")
    print("[ERROR] Please make sure the UI service is running on port 8000")
except Exception as e:
    print(f"[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()
