#!/usr/bin/env python3.12
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.insert(0, os.getcwd())

django.setup()

from django.test import Client

client = Client()

# Test round trip request
response = client.get('/api/flights/search/?origin=DFW&destination=ORD&depart_date=2025-01-24&seat_class=economy&trip_type=2&return_date=2025-01-26')

print(f"\n[API TEST]")
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"Response keys: {list(data.keys())}")
    print(f"\nDetailed response:")
    for key in data.keys():
        if isinstance(data[key], list):
            print(f"  {key}: {len(data[key])} items")
            if data[key]:
                print(f"    First item keys: {list(data[key][0].keys())}")
        elif isinstance(data[key], dict):
            print(f"  {key}: {list(data[key].keys())}")
        else:
            print(f"  {key}: {data[key]}")
else:
    print(f"Error: {response.content}")
