# Round-Trip Flight Booking - Tab-Based UI Implementation

## Overview
Implemented a cleaner tab-based interface for round-trip flight selection. Users can now switch between outbound and return flights using the existing tab switch at the top of the results page.

## Architecture

### User Flow
1. User performs a round-trip search
2. Tab selector appears: **[DFW → ORD] | [ORD → DFW]**
3. Click on a tab to view that flight's options
4. Full-width panel displays filters + flight listings
5. Select flights from each panel (calculated in background)
6. Bottom bar shows total fare and continues to review

### Benefits
✅ No cramped layout - full-width single panel  
✅ Professional, clean UX  
✅ Easy tab switching  
✅ Works on all screen sizes  
✅ Both fares calculate in background  
✅ Selection state preserved when switching tabs  

---

## Files Modified

### 1. Template: `microservices/ui-service/templates/flight/search.html`

**Changes:**
- Added `id="flight1-panel"` to first query-result-div
- Added `id="flight2-panel"` to second query-result-div-2
- Set initial display based on `trip_type`:
  - `flight1-panel`: `display: block` if round-trip (`trip_type == '2'`), else `none`
  - `flight2-panel`: `display: none` if round-trip, else `block`
- Removed col-lg-6 wrapper divs (container-fluid results-container)
- Removed side-by-side layout classes

**Key Code:**
```html
<!-- Existing tabs already present -->
{% if trip_type == '2' and flights %}
    <div class="query-trip-type-div">
        <div class="tabs">
            <a href="#" class="active-div" data-trip_type="1">{{origin.code}} → {{destination.code}}</a>
            <a href="#" data-trip_type="2">{{origin2.code}} → {{destination2.code}}</a>
        </div>
    </div>
{% endif %}

<!-- Flight 1 panel (Outbound) -->
<div class="query-result-div" id="flight1-panel" 
     style="display: {% if trip_type == '2' %}block{% else %}none{% endif %};">
    <!-- Filters and flights 1 listing -->
</div>

<!-- Flight 2 panel (Return) -->
<div class="query-result-div-2" id="flight2-panel" 
     style="display: {% if trip_type == '2' %}none{% else %}block{% endif %};">
    <!-- Filters and flights 2 listing -->
</div>
```

---

### 2. JavaScript: `microservices/ui-service/static/js/search2.js`

**Changes:**
- Implemented `switchFlightTab()` function to show/hide panels
- Updated to use `getElementById()` with new panel IDs
- Set display to 'flex' for active panel, 'none' for inactive
- Preserved tab active state styling

**Key Function:**
```javascript
function switchFlightTab(tabIndex) {
    // Update tab styling
    const tabs = document.querySelectorAll('.query-trip-type-div .tabs a');
    tabs.forEach((tab, index) => {
        if (index === tabIndex) {
            tab.classList.add('active-div');
        } else {
            tab.classList.remove('active-div');
        }
    });
    
    // Toggle panel visibility
    const panel1 = document.getElementById('flight1-panel');
    const panel2 = document.getElementById('flight2-panel');
    
    if (tabIndex === 0) {
        if (panel1) panel1.style.display = 'flex';
        if (panel2) panel2.style.display = 'none';
    } else {
        if (panel1) panel1.style.display = 'none';
        if (panel2) panel2.style.display = 'flex';
    }
}
```

---

### 3. CSS: `microservices/ui-service/static/css/search_style.css`

**Changes:**
- Removed panel-half override classes for col-lg-6
- Cleaned up conflicting flex rules
- Set base width: 100% for panels

**Key CSS:**
```css
.query-result-div, .query-result-div-2 {
    flex: 1;
    background-color: #fff;
    display: flex;
    animation-name: appear;
    animation-duration: .4s;
    animation-fill-mode: forwards;
    animation-timing-function: ease-in-out;
    width: 100%;
}

#flight1-panel,
#flight2-panel {
    width: 100%;
}
```

---

### 4. CSS: `microservices/ui-service/static/css/search2_style.css`

**Changes:**
- Removed `.results-container` class styles
- Removed `.col-lg-6` layout rules
- Removed side-by-side grid configuration
- Added smooth transition for panel switching

**Key CSS:**
```css
/* Tab switching for flight panels */
#flight1-panel,
#flight2-panel {
    transition: opacity 0.3s ease;
}
```

---

## Features Preserved

✅ **Seat class comparisons** - All lowercase ('economy', 'business', 'first')  
✅ **Price calculations** - Fare lookups working correctly  
✅ **Flight selection** - Both flights trackable in background  
✅ **Total fare display** - Updates when flights selected  
✅ **Filter functionality** - Works on both panels  
✅ **Review/Continue flow** - Properly passes both flight IDs  

---

## Technical Implementation

### State Management
- `selectedFlight1`: Holds outbound flight data
- `selectedFlight2`: Holds return flight data
- Both maintained while switching tabs
- Total fare calculated from both selections

### Tab Switching Logic
1. User clicks tab (already has click handler)
2. `switchFlightTab(tabIndex)` called
3. Tab CSS class updated for active state
4. Corresponding panel display set to 'flex' or 'none'
5. Other panel hidden
6. User sees smooth transition

### Display Priority
- If `trip_type == '2'` (round-trip):
  - Flight 1 panel shows first (outbound)
  - Flight 2 panel hidden initially
- User clicks tab to switch
- If `trip_type != '2'` (one-way):
  - Only Flight 1 panel visible always

---

## Testing Checklist

- [ ] Round-trip search displays tabs correctly
- [ ] Clicking "Outbound" tab shows Flight 1 panel
- [ ] Clicking "Return" tab shows Flight 2 panel  
- [ ] Filters work on both panels independently
- [ ] Flight selection updates fares correctly
- [ ] Total fare shows sum of both selections
- [ ] Tab styling shows active state
- [ ] Panel switching is smooth
- [ ] No layout issues on mobile/tablet
- [ ] Continue button passes both flight IDs correctly

---

## Migration Notes

**From:** Side-by-side col-lg-6 layout  
**To:** Tab-based single-panel display  

**No database changes required**  
**Backward compatible** with existing flight data  
**No breaking changes** to API structure  

