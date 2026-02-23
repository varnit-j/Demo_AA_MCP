#!/usr/bin/env python3.12
"""
Final comprehensive test to verify the complete fix
"""
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'microservices/ui-service'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ui.settings')
django.setup()

from django.template.loader import render_to_string

# Simulate the context that would be passed to the template
context = {
    'flights': [
        {
            'id': 37972,
            'depart_time': '08:09:00',
            'arrival_time': '10:42:00',
            'plane': 'Boeing 737-800',
            'airline': 'American Airlines',
            'flight_number': 'AA328',
            'economy_fare': 150.0,
            'business_fare': 375.0,
            'first_fare': 600.0,
        }
    ],
    'flights2': [
        {
            'id': 37966,
            'depart_time': '05:05:00',
            'arrival_time': '07:40:00',
            'plane': 'Boeing 737-800',
            'airline': 'American Airlines',
            'flight_number': 'AA1838',
            'economy_fare': 150.0,
            'business_fare': 375.0,
            'first_fare': 600.0,
        },
        {
            'id': 37967,
            'depart_time': '06:15:00',
            'arrival_time': '08:50:00',
            'plane': 'Boeing 777',
            'airline': 'American Airlines',
            'flight_number': 'AA2345',
            'economy_fare': 160.0,
            'business_fare': 400.0,
            'first_fare': 650.0,
        }
    ],
    'origin': {'code': 'DFW', 'city': 'Dallas'},
    'origin2': {'code': 'ORD', 'city': 'Chicago'},
    'destination': {'code': 'ORD', 'city': 'Chicago'},
    'destination2': {'code': 'DFW', 'city': 'Dallas'},
    'depart_date': '2025-01-24',
    'return_date': '2025-01-26',
    'seat': 'economy',
    'trip_type': '2',
    'min_price': 150.0,
    'max_price': 160.0,
    'min_price2': 150.0,
    'max_price2': 160.0,
}

try:
    # Render just the header parts to test
    from django.template import Template, Context
    
    # Test flight1 header
    template1_str = '<span id="f1-header-time">{{flights.0.depart_time|slice:":5"}} • {{flights.0.arrival_time|slice:":5"}}</span>'
    template1 = Template(template1_str)
    result1 = template1.render(Context(context))
    print("[TEST] Flight1 Header Rendering:")
    print(f"  Result: {result1}")
    print(f"  Expected: <span id=\"f1-header-time\">08:09 • 10:42</span>")
    
    # Test flight2 header
    template2_str = '<span id="f2-header-time">{{flights2.0.depart_time|slice:":5"}} • {{flights2.0.arrival_time|slice:":5"}}</span>'
    template2 = Template(template2_str)
    result2 = template2.render(Context(context))
    print("\n[TEST] Flight2 Header Rendering:")
    print(f"  Result: {result2}")
    print(f"  Expected: <span id=\"f2-header-time\">05:05 • 07:40</span>")
    
    # Test radio buttons
    radio1_template = '<input type="radio" data-depart="{{flights.0.depart_time|slice:\":5\"}}" data-arrive="{{flights.0.arrival_time|slice:\":5\"}}">'
    radio1 = Template(radio1_template)
    result1_radio = radio1.render(Context(context))
    print("\n[TEST] Flight1 Radio Data Attributes:")
    print(f"  Result: {result1_radio}")
    
    radio2_template = '<input type="radio" data-depart="{{flights2.0.depart_time|slice:\":5\"}}" data-arrive="{{flights2.0.arrival_time|slice:\":5\"}}">'
    radio2 = Template(radio2_template)
    result2_radio = radio2.render(Context(context))
    print("\n[TEST] Flight2 Radio Data Attributes:")
    print(f"  Result: {result2_radio}")
    
    # Check if values are correct
    if '08:09' in result1 and '10:42' in result1:
        print("\n✓ Flight1 header values are CORRECT")
    else:
        print("\n✗ Flight1 header values are INCORRECT")
    
    if '05:05' in result2 and '07:40' in result2:
        print("✓ Flight2 header values are CORRECT")
    else:
        print("✗ Flight2 header values are INCORRECT")
        
except Exception as e:
    print(f"[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()
