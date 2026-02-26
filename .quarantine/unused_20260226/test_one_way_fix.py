import requests
import sys

def test_flight_search():
    """Test one-way vs round-trip flight search"""
    
    base_url = "http://127.0.0.1:8000/flight/"
    
    # Test one-way flight search (the issue we're fixing)
    one_way_params = {
        'Origin': 'DFW',
        'Destination': 'ORD', 
        'TripType': '1',
        'DepartDate': '2026-02-15',
        'SeatClass': 'economy'
    }
    
    # Test round-trip flight search (should work)
    round_trip_params = {
        'Origin': 'DFW',
        'Destination': 'ORD',
        'TripType': '2', 
        'DepartDate': '2026-02-15',
        'ReturnDate': '2026-02-20',
        'SeatClass': 'economy'
    }
    
    print("🔍 Testing One-Way Flight Search Fix...")
    print("=" * 50)
    
    try:
        # Test one-way search
        print("📍 Testing ONE-WAY search (DFW → ORD)...")
        response = requests.get(base_url, params=one_way_params, timeout=10)
        
        if response.status_code == 200:
            content = response.text.lower()
            if "sorry, no flight" in content or "cannot find any flights" in content:
                print("❌ ONE-WAY SEARCH FAILED: Still showing 'No flights found'")
                return False
            else:
                print("✅ ONE-WAY SEARCH SUCCESS: Flights are being displayed")
                
        else:
            print(f"❌ ONE-WAY SEARCH ERROR: HTTP {response.status_code}")
            return False
            
        # Test round-trip search for comparison
        print("\n📍 Testing ROUND-TRIP search (DFW ⇄ ORD)...")
        response = requests.get(base_url, params=round_trip_params, timeout=10)
        
        if response.status_code == 200:
            content = response.text.lower()
            if "sorry, no flight" in content:
                print("❌ ROUND-TRIP SEARCH FAILED: Unexpected failure")
                return False
            else:
                print("✅ ROUND-TRIP SEARCH SUCCESS: Flights are being displayed")
        else:
            print(f"❌ ROUND-TRIP SEARCH ERROR: HTTP {response.status_code}")
            return False
            
        print("\n🎉 SUCCESS: Both one-way and round-trip searches are working!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ CONNECTION ERROR: {e}")
        print("💡 Make sure the UI service is running on port 8000")
        return False

if __name__ == "__main__":
    success = test_flight_search()
    sys.exit(0 if success else 1)