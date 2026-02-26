#!/usr/bin/env python3.12
"""
Debug script to test template rendering for flights2
"""
import os
import sys
import django

# Setup Django environment for UI service
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'microservices/ui-service'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ui.settings')
django.setup()

from django.template import Template, Context
from django.template.loader import render_to_string

# Simulate flights2 data
flights2_data = [
    {
        'id': 37966,
        'origin': {'id': 12838, 'city': 'Chicago', 'code': 'ORD'},
        'destination': {'id': 12842, 'city': 'Dallas', 'code': 'DFW'},
        'depart_time': '05:05:00',
        'arrival_time': '07:40:00',
        'plane': 'Boeing 737-800',
        'airline': 'American Airlines',
        'flight_number': 'AA1838',
        'economy_fare': 150.0,
        'business_fare': 375.0,
        'first_fare': 600.0
    },
    {
        'id': 37967,
        'origin': {'id': 12838, 'city': 'Chicago', 'code': 'ORD'},
        'destination': {'id': 12842, 'city': 'Dallas', 'code': 'DFW'},
        'depart_time': '06:15:00',
        'arrival_time': '08:50:00',
        'plane': 'Boeing 777',
        'airline': 'American Airlines',
        'flight_number': 'AA2345',
        'economy_fare': 160.0,
        'business_fare': 400.0,
        'first_fare': 650.0
    }
]

seat = 'economy'
trip_type = '2'

# Test template rendering
template_str = '''
{% for flight2 in flights2 %}
<input type="radio" class="flight2-radio r-b" name="test2" value="{{flight2.id}}" 
    data-plane='{{flight2.plane}}' 
    data-depart='{{flight2.depart_time|slice:":5"}}' 
    data-arrive='{{flight2.arrival_time|slice:":5"}}' 
    data-fare="{% if seat == 'economy' %} {{flight2.economy_fare}} {% elif seat == 'business' %} {{flight2.business_fare}} {% else %} {{flight2.first_fare}} {% endif %}" 
    {% if forloop.counter == 1 %}checked{% endif %}>
{% endfor %}
'''

context = Context({
    'flights2': flights2_data,
    'seat': seat,
    'trip_type': trip_type
})

template = Template(template_str)
result = template.render(context)

print("[TEST] Rendered HTML:")
print(result)
print("\n[TEST] Checking attributes:")
for i, flight in enumerate(flights2_data, 1):
    depart_sliced = flight['depart_time'][:5]
    arrive_sliced = flight['arrival_time'][:5]
    print(f"\nFlight {i}:")
    print(f"  Original depart_time: {flight['depart_time']}")
    print(f"  After slice [:5]: {depart_sliced}")
    print(f"  Original arrival_time: {flight['arrival_time']}")
    print(f"  After slice [:5]: {arrive_sliced}")
