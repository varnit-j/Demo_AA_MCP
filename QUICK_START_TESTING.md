# Round Trip Flight Booking - Quick Start Testing Guide

## 🚀 Starting the Application

### Step 1: Start Django Server
```bash
cd d:\varnit\demo\2101_f\2101_UI_Chang\AA_Flight_booking_UI_DEMO
python3.12 manage.py runserver 0.0.0.0:8000
```

Expected output:
```
Starting development server at http://0.0.0.0:8000/
```

### Step 2: Access Application
Open browser to: `http://localhost:8000/`

---

## ✅ Testing Round Trip Booking

### Test 1: Search Round Trip Flight
1. **Home Page**
   - Click "Round Trip" option
   - Enter:
     - From: NYC (New York)
     - To: LAX (Los Angeles)
     - Depart: 2026-02-10
     - Return: 2026-02-17
     - Cabin: Economy
   - Click Search

2. **Expected Result**
   - Two panels displayed side-by-side
   - Left panel: NYC → LAX flights
   - Right panel: LAX → NYC flights
   - Both show available flights and prices
   - Tab indicator shows active panel

### Test 2: Select Flights
1. **In Search Results**
   - Click radio button on outbound flight (left panel)
     - Example: AA101 (09:00-12:30, $299)
   - Click radio button on return flight (right panel)
     - Example: AA205 (14:00-17:15, $289)

2. **Expected Result**
   - Selection summary updates
   - Shows both flight details
   - Total price: $588 (299 + 289)
   - "Continue" button enabled

### Test 3: Proceed to Booking
1. **Click "Continue" Button**
   - Should navigate to passenger booking page
   - Shows both flight details

2. **Enter Passenger Information**
   - Name: John Doe
   - Gender: Male
   - Email: john@example.com
   - Mobile: 1234567890 (10 digits)
   - Country Code: +1 (USA)

3. **Expected Result**
   - Form accepts input for both flights
   - Displays both flight details
   - No errors on validation

### Test 4: Payment
1. **Proceed to Payment Page**
   - Shows total: $688 (588 + $100 fee)
   - Loyalty points available (if logged in)
   - Both tickets shown

2. **Enter Payment Details**
   - Card: 4532015112830366
   - Name: John Doe
   - Exp: 12/25
   - CVV: 123

3. **Expected Result**
   - Payment processes
   - Redirected to confirmation
   - Shows both booking references

### Test 5: Verify Loyalty Points
1. **Check User Account**
   - Go to user dashboard
   - View "My Bookings"
   - See both tickets with CONFIRMED status

2. **Check Loyalty Points**
   - Points awarded for both flights
   - Example: 9 points (2% of ~$450 USD equivalent)

3. **Expected Result**
   - Both tickets in "My Bookings"
   - Points balance increased
   - Separate reference numbers for each flight

---

## 🔍 Visual Verification

### Layout Check
- [ ] Two flight panels visible side-by-side
- [ ] Left panel: outbound flights
- [ ] Right panel: return flights
- [ ] Tab indicator shows active panel
- [ ] Prices display correctly in both panels

### Selection Check
- [ ] Clicking radio button updates selection summary
- [ ] Both flights shown in summary
- [ ] Total price = flight1 + flight2
- [ ] "Continue" button active

### Booking Check
- [ ] Both flight details shown
- [ ] Passenger form accepts input
- [ ] No duplicate passenger entries needed
- [ ] Same passenger for both flights

### Payment Check
- [ ] Total fare combines both flights
- [ ] Loyalty points available for redemption
- [ ] Payment processes successfully
- [ ] Both tickets confirmed

---

## 🐛 Debugging Tips

### Check Browser Console
```javascript
// Verify flight selection values
console.log(document.querySelector('#flt1').value);  // Should be flight1 ID
console.log(document.querySelector('#flt2').value);  // Should be flight2 ID

// Verify price calculation
console.log(document.querySelector('#select-total-fare').innerText);  // Should be sum
```

### Check Network Tab
- Verify API call includes `TripType=2`
- Check response includes `flights` and `flights2`
- Monitor payment request parameters

### Check Database
```bash
python3.12 manage.py shell
```

```python
from flight.models import Ticket
from django.contrib.auth.models import User

user = User.objects.get(username='your_username')
tickets = Ticket.objects.filter(user=user).order_by('-booking_date')[:5]

for ticket in tickets:
    print(f"Ref: {ticket.ref_no}, Flight: {ticket.flight}, Status: {ticket.status}")
```

### Check Loyalty Points
```python
from apps.loyalty.models import LoyaltyAccount, PointTransaction

account = LoyaltyAccount.objects.get(user=user)
print(f"Current Points: {account.current_points_balance}")

transactions = PointTransaction.objects.filter(account=account).order_by('-created_at')[:5]
for trans in transactions:
    print(f"Type: {trans.type}, Amount: {trans.points_amount}, Desc: {trans.description}")
```

---

## ❌ Common Issues & Solutions

### Issue: Only one panel showing
**Solution**: 
- Clear browser cache: Ctrl+Shift+Delete
- Verify `trip_type=2` in URL
- Check browser console for JS errors

### Issue: Price not calculating
**Solution**:
- Check data-fare attributes in HTML (should be numeric)
- Verify getFareValue() function in search2.js
- Check console for parsing errors

### Issue: Second ticket not created
**Solution**:
- Check form has both ticket IDs in hidden inputs
- Verify `ticket2` parameter in POST request
- Check database for ticket creation errors

### Issue: Loyalty points not awarded
**Solution**:
- Verify LoyaltyService is installed
- Check apps.loyalty exists in installed apps
- Monitor debug logs in payment view

---

## 📊 Test Data

### Sample Airports
- NYC: New York (LaGuardia)
- LAX: Los Angeles (LAX)
- DEL: Delhi (Indira Gandhi)
- BOM: Mumbai (Bombay)

### Sample Flight Times
- Morning: 06:00 - 12:00
- Afternoon: 12:00 - 18:00
- Evening: 18:00 - 23:59

### Sample Fares (in INR)
- Economy: ₹3,000 - ₹8,000
- Business: ₹8,000 - ₹20,000
- First: ₹20,000 - ₹50,000

---

## 📋 Acceptance Criteria

**Round trip booking is working correctly when:**

1. ✅ Both outbound and return flights visible simultaneously
2. ✅ User can select different flights from each panel
3. ✅ Total price correctly sums both flights
4. ✅ Two separate tickets created in database
5. ✅ Both tickets show CONFIRMED status
6. ✅ Loyalty points awarded for both flights
7. ✅ No JavaScript errors in console
8. ✅ Responsive layout on mobile devices
9. ✅ Payment processes for combined fare
10. ✅ User receives both confirmation emails/references

---

## 🎓 Key Learning Points

1. **Flex Layout**: CSS `display: flex` with `gap: 0` shows both panels side-by-side
2. **JavaScript State**: Multiple radio buttons track selection for each flight
3. **Price Calculation**: Client-side calculation after removing currency filters
4. **Loyalty Integration**: Points awarded per ticket, not per booking
5. **Data Flow**: Same passenger list for both flights (improvement opportunity)

---

## 📞 Support

If issues persist:

1. Check ROUND_TRIP_FIX_SUMMARY.md for detailed technical changes
2. Review ROUND_TRIP_VERIFICATION.md for implementation details
3. Enable DEBUG=True in settings.py for detailed logging
4. Check Django error page for detailed stack traces

---

Last Updated: February 6, 2026
Status: ✅ Ready for Testing

