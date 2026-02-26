
import requests
import sys
from datetime import datetime, timedelta

def test_flight_search_scenarios():
    """Comprehensive test of flight search fix"""
    
    base_url = "http://127.0.0.1:8000/flight/"
    
    # Test scenarios
    test_cases = [
        {
            'name': 'One-way DFW→ORD (Economy)',
            'params': {
                'Origin': 'DFW',
                'Destination': 'ORD',
                'TripType': '1',
                'DepartDate': '2026-02-15',
                'SeatClass': 'economy'
            },
            'should_show_flights': True,
            'expected_trip_type': '1'
        },
        {
            'name': 'One-way DFW→ORD (Business)',
            'params': {
                'Origin': 'DFW',
                'Destination': 'ORD',
                'TripType': '1',
                'DepartDate': '2026-02-15',
                'SeatClass': 'business'
            },
            'should_show_flights': True,
            'expected_trip_type': '1'
        },
        {
            'name': 'Round-trip DFW⇄ORD (Economy)',
            'params': {
                'Origin': 'DFW',
                'Destination': 'ORD',
                'TripType': '2',
                'DepartDate': '2026-02-15',
                'ReturnDate': '2026-02-20',
                'SeatClass': 'economy'
            },
            'should_show_flights': True,
            'expected_trip_type': '2'
        },
        {
            'name': 'One-way ORD→DFW (Economy)',
            'params': {
                'Origin': 'ORD',
                'Destination': 'DFW',
                'TripType': '1',
                'DepartDate': '2026-02-16',
                'SeatClass': 'economy'
            },
            'should_show_flights': True,
            'expected_trip_type': '1'
        }
    ]
    
    print("🔍 COMPREHENSIVE FLIGHT SEARCH VALIDATION")
    print("=" * 60)
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📍 Test {i}: {test_case['name']}")
        print("-" * 40)
        
        try:
            response = requests.get(base_url, params=test_case['params'], timeout=10)
            
            if response.status_code == 200:
                content = response.text.lower()
                
                # Check for error messages
                has_no_flights_error = "sorry, no flight" in content or "cannot find any flights" in content
                
                # Check for flight display elements
                has_flight_elements = (
                    "flight-company" in content or 
                    "flight-time" in content or 
                    "book flight" in content
                )
                
                # Validate results
                if test_case['should_show_flights']:
                    if has_no_flights_error:
                        print(f"❌ FAILED: Shows 'No flights found' error")
                        all_passed = False
                    elif has_flight_elements:
                        print(f"✅ PASSED: Flights are displayed correctly")
                    else:
                        print(f"⚠️  UNCLEAR: No clear error or flight elements found")
                        all_passed = False
                else:
                    if has_no_flights_error:
                        print(f"