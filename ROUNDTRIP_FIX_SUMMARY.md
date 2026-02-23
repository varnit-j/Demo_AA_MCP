# Round Trip Flight Booking Fix - Issue & Solution

## PROBLEM IDENTIFIED
Round trip flights (TripType='2') were not displaying both outbound and return flights in the UI, even though:
- Database had American Airlines flights from DFW to ORD and back
- Backend flight() view was called with correct parameters
- Template had structures for both flight panels

## ROOT CAUSE ANALYSIS
**File:** `flight/views.py`, function `flight()`, lines 160-210

**The Bug:**
```python
# Original buggy code
def flight(request):
    # ... parameter extraction ...
    
    if trip_type == '2':
        # These variables ARE set correctly here
        origin2 = Place.objects.get(code=d_place.upper())  
        destination2 = Place.objects.get(code=o_place.upper())
        flightday2 = Week.objects.get(number=return_date.weekday())
        # ... logging ...
    
    # Then immediately AFTER the if block:
    flights2 = []  # Line 186 - Initialize flights2
    origin2 = None  # Line 187 - OVERWRITE origin2 to None!!!
    destination2 = None  # Line 188 - OVERWRITE destination2 to None!!!
    
    # When querying for return flights:
    if trip_type == '2':
        flights2 = Flight.objects.filter(
            depart_day=flightday2,
            origin=origin2,  # Now this is None!
            destination=destination2,  # Now this is None!
            ...
        )
        # Result: Query returns 0 flights because origin_id and destination_id are NULL
```

**Why This Happened:**
- The initialization of `flights2`, `origin2`, `destination2` was done AFTER setting them in the trip_type check
- This created a variable shadowing issue that overwrote the correctly computed values
- The query for return flights then failed to find any matches

## SOLUTION IMPLEMENTED
**File:** `flight/views.py`, function `flight()`, lines 160-200

**The Fix:**
Reorganized variable initialization to happen BEFORE the trip_type check:

```python
def flight(request):
    # ... parameter extraction ...
    
    # Initialize ALL variables FIRST (before any conditional logic)
    flights2 = []
    origin2 = None
    destination2 = None
    flightday2 = None
    max_price2 = 0
    min_price2 = 0
    
    # Get common flight details
    seat = request.GET.get('SeatClass')
    flightday = Week.objects.get(number=depart_date.weekday())
    destination = Place.objects.get(code=d_place.upper())
    origin = Place.objects.get(code=o_place.upper())
    
    # NOW handle round trip - these values stick and aren't overwritten
    if trip_type == '2':
        returndate = request.GET.get('ReturnDate')
        return_date = datetime.strptime(returndate, "%Y-%m-%d")
        flightday2 = Week.objects.get(number=return_date.weekday())
        origin2 = Place.objects.get(code=d_place.upper())
        destination2 = Place.objects.get(code=o_place.upper())
    
    # Query for flights using the now-correct values
    if seat == 'economy':
        flights = Flight.objects.filter(...)
        if trip_type == '2':
            flights2 = Flight.objects.filter(
                depart_day=flightday2,
                origin=origin2,  # Now correctly set!
                destination=destination2,  # Now correctly set!
                ...
            )
```

## HOW THIS FIXES THE UI
With the correct `flights2` queryset:
1. Backend passes `flights2` to template context with actual flight data
2. Template condition `{% if trip_type == '2' and flights and flights2 %}` evaluates to TRUE
3. `round-trip-panels-wrapper` div renders with both panels
4. `query-result-div` gets `panel-half` class for 50% width
5. `query-result-div-2` gets `panel-half` class and `display: block` (not hidden)
6. `flights_div2` renders with return flight options
7. JavaScript can handle selection of both flights

## DATA VERIFIED
- Dallas (DFW) has 12 American Airlines flights to Chicago (ORD)
- Chicago (ORD) has 11 American Airlines flights back to Dallas (DFW)
- Both operate on Tuesday (Feb 10, 2026 and Feb 17, 2026)
- All flights have economy_fare > 0 and are properly structured

## TEMPLATE STRUCTURE VERIFIED
- `<div class="round-trip-panels-wrapper">` - wrapper for side-by-side layout
- `<div class="query-result-div panel-half">` - outbound flights (50% width)
- `<div class="query-result-div-2 panel-half">` - return flights (50% width)
- Both have `<div id="flights_div">` and `<div id="flights_div2">` for flight boxes
- Proper loop structures: `{% for flight in flights %}` and `{% for flight2 in flights2 %}`
- Selection divs show both `select-f1-` and `select-f2-` fare/time information
- Total fare calculation: `flights.0.economy_fare | add:flights2.0.economy_fare`

## EXPECTED BEHAVIOR AFTER FIX
1. User searches for round trip: DFW -> ORD, Feb 10-17, 2026
2. Backend queries and finds both flights successfully
3. Template renders with both flight panels side-by-side
4. Each panel shows filterable list of 12 and 11 flights respectively
5. User can select one flight from each panel
6. Total fare is calculated and displayed
7. Selection proceeds to booking/payment flow
