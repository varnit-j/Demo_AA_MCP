# Round Trip Payment and Loyalty Fixes

## Problem Statement
- Payment was only processing ONE flight fare instead of BOTH for round trip bookings
- Loyalty points were not being aligned with round trip bookings
- Booking history and loyalty dashboard needed updates for round trip support

## Root Cause Analysis

### Payment Processing Bug
**Location:** [microservices/ui-service/ui/views.py](microservices/ui-service/ui/views.py) - `book()` view

**Issue:** The code was:
1. Extracting only `flight1` ID from POST data
2. NOT extracting `flight2` ID
3. Calculating fare based on ONLY flight1
4. Passing only flight1 data to payment template

### Impact
- Round trip bookings were charged for only the outbound flight
- Return flight was essentially free
- Total payment was 50% of what should have been charged

## Solutions Implemented

### 1. Fixed booking_data extraction to include both flights

**File:** [microservices/ui-service/ui/views.py](microservices/ui-service/ui/views.py) - Lines 430-453

**Change:**
```python
# BEFORE: Only extracted flight1
booking_data = {
    'flight_id': request.POST.get('flight1'),
    # ... rest of data
}

# AFTER: Extract both flights
booking_data = {
    'flight_id': request.POST.get('flight1'),
    'flight_id_2': request.POST.get('flight2') if request.POST.get('flight2') else None,
    # ... rest of data
}
```

### 2. Fixed flight data retrieval for payment (Async path)

**File:** [microservices/ui-service/ui/views.py](microservices/ui-service/ui/views.py) - Lines 608-619

**Change:**
```python
# BEFORE: Only retrieved flight1
flight_data = call_backend_api(f'api/flights/{flight_id}/')

# AFTER: Retrieve both flights
flight_data = call_backend_api(f'api/flights/{flight_id}/')
flight_data_2 = None
if flight2_id:
    flight_data_2 = call_backend_api(f'api/flights/{flight2_id}/')
```

### 3. Fixed fare calculation to sum both flights

**File:** [microservices/ui-service/ui/views.py](microservices/ui-service/ui/views.py) - Lines 622-637

**Change:**
```python
# BEFORE: Only calculated flight1 fare
if seat_class == 'first':
    fare = flight_data.get('first_fare', 0)
elif seat_class == 'business':
    fare = flight_data.get('business_fare', 0)
else:
    fare = flight_data.get('economy_fare', 0)

# AFTER: Sum both flights
if seat_class == 'first':
    fare = flight_data.get('first_fare', 0)
    if flight_data_2:
        fare += flight_data_2.get('first_fare', 0)
elif seat_class == 'business':
    fare = flight_data.get('business_fare', 0)
    if flight_data_2:
        fare += flight_data_2.get('business_fare', 0)
else:
    fare = flight_data.get('economy_fare', 0)
    if flight_data_2:
        fare += flight_data_2.get('economy_fare', 0)
```

### 4. Updated payment context to include both flights

**File:** [microservices/ui-service/ui/views.py](microservices/ui-service/ui/views.py) - Lines 645-656

**Change:**
```python
# BEFORE: Only included flight1
payment_context = {
    'booking_reference': correlation_id,
    'flight': flight_data,
    'fare': total_fare,
    # ...
}

# AFTER: Include both flights
payment_context = {
    'booking_reference': correlation_id,
    'flight': flight_data,
    'flight_2': flight_data_2 if flight_data_2 else None,
    'fare': total_fare,
    # ...
}
```

### 5. Applied same fixes to sync booking path

**File:** [microservices/ui-service/ui/views.py](microservices/ui-service/ui/views.py) - Lines 683-736

Applied identical fixes for the sync booking result path to ensure consistency.

## Loyalty Points Alignment

### Current Implementation
Loyalty points are already correctly aligned:

1. **Points Earning:** [flight/views.py](flight/views.py) Lines 620-643
   - Calculates 2% of USD fare amount
   - Awards points for BOTH flights in round trip
   - Separate transactions for each flight (ticket)

2. **Points Redemption:** [microservices/ui-service/templates/flight/payment.html](microservices/ui-service/templates/flight/payment.html)
   - Users can redeem points against total fare (both flights)
   - 1 point = $0.01
   - Can use up to max available points

3. **Dashboard:** [apps/loyalty/views.py](apps/loyalty/views.py)
   - Shows total points balance accumulated from all bookings
   - Includes round trip bookings automatically

### Booking History
- Bookings are stored per-ticket basis
- Each flight in a round trip is a separate ticket with its own reference number
- Loyalty dashboard shows all bookings/transactions

## Testing the Fixes

### Test Scenario: Round Trip DFW → ORD → DFW

1. **Search Round Trip:**
   - Outbound: $150 (economy)
   - Return: $140 (economy)
   - Fee: $10
   - Expected Total: $300

2. **Review & Payment:**
   - Fare summary should show: $150 + $140 = $290 + $10 fee = $300
   - Both flights should be included in booking

3. **Points Calculation:**
   - Outbound points: int($150 * 0.02) = 3 points
   - Return points: int($140 * 0.02) = 2 points
   - Total points earned: 5 points
   - Points value: $0.05

4. **Redemption:**
   - User can redeem up to 5 points = $0.05 off
   - If 5 points used: Payment becomes $299.95

## Files Modified

| File | Lines | Change |
|------|-------|--------|
| [microservices/ui-service/ui/views.py](microservices/ui-service/ui/views.py) | 430-453 | Extract flight2 from POST |
| [microservices/ui-service/ui/views.py](microservices/ui-service/ui/views.py) | 608-619 | Retrieve flight2 data (async) |
| [microservices/ui-service/ui/views.py](microservices/ui-service/ui/views.py) | 622-637 | Calculate total fare (async) |
| [microservices/ui-service/ui/views.py](microservices/ui-service/ui/views.py) | 645-656 | Add flight_2 to context (async) |
| [microservices/ui-service/ui/views.py](microservices/ui-service/ui/views.py) | 683-736 | Same fixes for sync path |

## Verification Steps

1. Run backend service on port 8001
2. Run UI service on port 8000
3. Search for round trip flight (DFW → ORD → DFW)
4. Proceed to fare summary - verify both flights shown
5. Proceed to payment - verify fare includes both flights
6. Complete payment with test card
7. Verify booking confirmed for both flights
8. Check loyalty dashboard for combined points
9. Verify booking history shows both flights

## Expected Behavior After Fixes

✅ Payment processes BOTH flights
✅ Fare summary shows sum of both flight fares + fee
✅ Loyalty points earned for BOTH flights
✅ Booking history shows both flights as separate tickets
✅ Points can be redeemed against total fare
✅ Dashboard shows all loyalty transactions

