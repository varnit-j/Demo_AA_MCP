
# Round Trip Flight Booking Implementation Plan

## Overview
This document provides a detailed implementation plan to fix the round trip flight booking functionality. The current system only works for one-way flights, and we need to implement proper support for round trip bookings with split panels showing both outbound and return flights.

## Current Issues Identified

### 1. Backend API Issues
- The `flight_search` function in `microservices/backend-service/flight/views.py` only searches for outbound flights
- No logic to search for return flights when `trip_type=2`
- Missing return flight data in API response

### 2. Frontend Template Issues
- The `search.html` template has placeholders for `flights2` but they're never populated
- The tabs for switching between outbound/return flights exist but don't function
- Radio button selection logic doesn't properly handle both flights

### 3. JavaScript Issues
- The `search.js` only handles filtering for the second panel, not selection logic
- Missing logic to update the selection summary when users pick flights
- No validation to ensure both flights are selected before proceeding

### 4. Booking Flow Issues
- The `review` function expects both `flight1Id` and `flight2Id` but the frontend doesn't provide them correctly
- The selection form at the bottom of search.html has hardcoded values instead of dynamic selection

## Implementation Steps

### Step 1: Update Backend API (microservices/backend-service/flight/views.py)

**Modify the `flight_search` function to handle round trip searches:**

```python
@api_view(['GET'])
@permission_classes([AllowAny])
def flight_search(request):
    # Get parameters directly from request
    origin_code = request.GET.get('origin', '').upper()
    destination_code = request.GET.get('destination', '').upper()
    depart_date_str = request.GET.get('depart_date', '')
    seat_class = request.GET.get('seat_class', 'economy')
    trip_type = request.GET.get('trip_type', '1')  # Add trip_type parameter
    return_date_str = request.GET.get('return_date', '')  # Add return_date parameter
    
    # Basic validation
    if not origin_code or not destination_code or not depart_date_str:
        return Response({'error': 'Missing required parameters: origin, destination, depart_date'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Validate return date for round trip
    if trip_type == '2' and not return_date_str:
        return Response({'error': 'Return date is required for round trip'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Parse dates
        depart_date = datetime.strptime(depart_date_str, '%Y-%m-%d').date()
        return_date = None
        if trip_type == '2':
            return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()
        
        origin = Place.objects.get(code=origin_code)
        destination = Place.objects.get(code=destination_code)
        flight_day = Week.objects.get(number=depart_date.weekday())
        
        # Search outbound flights
        flights = Flight.objects.filter(
            origin=origin,
            destination=destination,
            depart_day=flight_day,
            airline__icontains='American Airlines'
        )
        
        if seat_class == 'economy':
            flights = flights.exclude(economy_fare=0).order_by('economy_fare')
        elif seat_class == 'business':
            flights = flights.exclude(business_fare=0).order_by('business_fare')
        elif seat_class == 'first':
            flights = flights.exclude(first_fare=0).order_by('first_fare')
        
        # Search return flights for round trip
        flights2 = []
        origin2 = None
        destination