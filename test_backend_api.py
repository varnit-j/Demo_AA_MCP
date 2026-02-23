"""Test backend API directly"""
import requests
import json

backend_url = "http://127.0.0.1:8001"

params = {
    'origin': 'DFW',
    'destination': 'ORD',
    'trip_type': '2',
    'depart_date': '2026-02-08',
    'return_date': '2026-02-09',
    'seat_class': 'economy'
}

print("Testing backend API: /api/flights/search/")
print(f"URL: {backend_url}/api/flights/search/")
print(f"Params: {params}\n")

try:
    response = requests.get(f"{backend_url}/api/flights/search/", params=params, timeout=10)
    print(f"Status: {response.status_code}")
    
    data = response.json()
    print(f"\nResponse keys: {list(data.keys())}")
    print(f"Number of outbound flights: {len(data.get('flights', []))}")
    print(f"Number of return flights: {len(data.get('flights2', []))}")
    
    if data.get('flights2'):
        print(f"\nFirst return flight: {json.dumps(data['flights2'][0], indent=2)}")
    else:
        print("\nNo flights2 in response!")
        print(f"Full response: {json.dumps(data, indent=2)[:500]}")
        
except Exception as e:
    print(f"Error: {e}")
