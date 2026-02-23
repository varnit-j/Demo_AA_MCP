# Round Trip Booking - Quick Testing Guide

## All Issues Fixed ✅

### Issue 1: Return Flight Times Not Showing ✅
- **Status**: FIXED
- **Verification**: Search for round trip - both flight panels show departure/arrival times
- **What Changed**: Template filter changed from `|time:"H:i"` to `|slice:":5"`

### Issue 2: Payment Only Processing One Flight ✅
- **Status**: FIXED  
- **Verification**: Total fare = Flight1 + Flight2 + Fee
- **What Changed**: book() view now extracts and processes both flight IDs

### Issue 3: Loyalty Points Only for One Flight ✅
- **Status**: FIXED
- **Verification**: Points = 4% of total payment (both flights combined)
- **What Changed**: Points awarded once per complete booking, not per ticket

### Issue 4: SAGA Checkboxes Always Visible ✅
- **Status**: FIXED
- **Verification**: Click "⚙️ Advanced Options" to show/hide test checkboxes
- **What Changed**: Hidden by default, toggleable button added

---

## Testing Steps

### 1️⃣ Round Trip Search
```
1. Go to search page
2. Select:
   - Origin: DFW
   - Destination: ORD  
   - Depart Date: 2026-02-11
   - Return Date: 2026-02-12
   - Trip Type: Round Trip
3. Click Search

✅ Expected: 
   - Flight1 panel shows times (e.g., "08:09 • 10:42")
   - Flight2 panel shows times (e.g., "05:05 • 07:40")
```

### 2️⃣ Select Flights
```
1. In flight1 panel: Select first flight (click radio button)
2. Click flight2 tab
3. In flight2 panel: Select first flight (click radio button)
4. Both should display selected times in header

✅ Expected:
   - Header updates for each flight
   - Times show correctly
```

### 3️⃣ Review Fare Summary
```
1. Stay on same page
2. Look at right panel "Fare Summary"

✅ Expected:
   - Base Fare = Flight1_fare + Flight2_fare
   - Fee = $20
   - Total = Base Fare + Fee
   Example:
   - Base Fare: $150 + $120 = $270
   - Fee: $20
   - Total: $290
```

### 4️⃣ Proceed to Payment
```
1. Scroll down and click "Proceed to payment"
2. Add passenger details
3. Check "⚙️ Advanced Options" button (should not show checkboxes)
4. Click button to reveal SAGA test options (if testing)
5. Click button again to hide them

✅ Expected:
   - Form accepts passenger info
   - SAGA options hidden by default
   - Button toggles visibility smoothly
```

### 5️⃣ Payment Page
```
1. Check amount displayed

✅ Expected:
   - Amount = Total Fare
   - Example: $290 (matches fare summary)
```

### 6️⃣ Complete Booking
```
1. Complete payment
2. Redirect to bookings page
3. Check booking history

✅ Expected:
   - See both flights listed
   - Departure flight: DFW→ORD
   - Return flight: ORD→DFW
   - Total fare shows correctly
   - Status shows: CONFIRMED
```

### 7️⃣ Loyalty Points
```
1. Go to Loyalty Dashboard
2. Check points earned

✅ Expected:
   - Points = 4% of total payment
   - Example: 4% of $270 = 10.8 ≈ 11 points
   - Points showing in account balance
```

---

## Key Verification Points

| Point | Before | After | Status |
|-------|--------|-------|--------|
| Flight2 times display | ❌ Blank | ✅ "05:05 • 07:40" | FIXED |
| Payment amount | ❌ Flight1 only | ✅ Flight1 + Flight2 | FIXED |
| Loyalty points | ❌ Per ticket | ✅ Total payment | FIXED |
| SAGA checkboxes | ❌ Always visible | ✅ Toggle button | FIXED |

---

## One-Way Booking (Verify Not Broken)

```
1. Go to search page
2. Select:
   - Origin: DFW
   - Destination: ORD
   - Depart Date: 2026-02-11
   - Trip Type: One Way
3. Select flight
4. Proceed to payment

✅ Expected:
   - Only flight1 shown
   - Fare = Single flight fare + fee
   - Points = 4% of that amount
   - Everything works as before
```

---

## Troubleshooting

### Times Still Not Showing?
- Clear browser cache (Ctrl+Shift+Delete)
- Restart Django server
- Check template file: `/microservices/ui-service/templates/flight/search.html`

### Payment Amount Wrong?
- Check that both flight1 and flight2 hidden fields have values
- Verify backend returns correct fare data
- Check logs: `python manage.py runserver` output

### Points Not Awarded?
- Check loyalty service is running (port 8003)
- Verify user has loyalty account created
- Check logs for LoyaltyService errors

### SAGA Button Not Working?
- Check browser console for JavaScript errors
- Verify button ID is `toggleSagaDemo`
- Check if `toggleSagaDemoSection()` function exists

---

## File Locations for Reference

```
Templates:
- microservices/ui-service/templates/flight/search.html (time filters)
- microservices/ui-service/templates/flight/book.html (SAGA toggle)

Views:
- microservices/ui-service/ui/views.py (payment processing)
- flight/views.py (loyalty points)

Database:
- db.sqlite3 (bookings, loyalty transactions)
```

---

## Success Criteria

✅ All of the following must pass:

1. Round trip search displays both flight times
2. Fare summary shows total for both flights
3. Payment processes full amount (both flights + fee)
4. Loyalty points awarded = 4% of total
5. SAGA checkboxes hidden by default, toggle on button click
6. One-way bookings still work
7. Booking history shows all bookings correctly
8. Dashboard shows accumulated loyalty points

---

**Status**: READY FOR TESTING  
**Date**: February 9, 2026  
**All Issues**: ✅ FIXED
