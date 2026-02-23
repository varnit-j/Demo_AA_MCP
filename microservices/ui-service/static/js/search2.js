// Round trip flight search functionality
document.addEventListener("DOMContentLoaded", () => {
    console.log("[DEBUG] search2.js loaded for round trip functionality");
    
    // Initialize round trip functionality
    initializeRoundTripTabs();
    initializeFlightSelection();
    
    // Initialize existing functionality from search.js
    if (typeof flight_duration === 'function') flight_duration();
    if (typeof flight_duration2 === 'function') flight_duration2();
    if (typeof filter_price === 'function') filter_price();
    if (typeof filter_price2 === 'function') filter_price2();
});

// Global variables to track selected flights
let selectedFlight1 = null;
let selectedFlight2 = null;

function initializeRoundTripTabs() {
    const tabs = document.querySelectorAll('.query-trip-type-div .tabs a');
    if (tabs.length === 0) return;
    
    console.log("[DEBUG] Initializing round trip tabs");
    
    tabs.forEach((tab, index) => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            switchFlightTab(index);
        });
    });
}

function switchFlightTab(tabIndex) {
    console.log(`[DEBUG] Switching to tab ${tabIndex}`);
    
    // Update tab appearance
    const tabs = document.querySelectorAll('.query-trip-type-div .tabs a');
    tabs.forEach((tab, index) => {
        if (index === tabIndex) {
            tab.classList.add('active-div');
        } else {
            tab.classList.remove('active-div');
        }
    });
    
    // Show/hide flight panels
    const panel1 = document.getElementById('flight1-panel');
    const panel2 = document.getElementById('flight2-panel');
    
    if (tabIndex === 0) {
        // Show outbound flight
        console.log("[DEBUG] Showing flight1 panel");
        if (panel1) panel1.style.display = 'flex';
        if (panel2) panel2.style.display = 'none';
    } else {
        // Show return flight
        console.log("[DEBUG] Showing flight2 panel");
        if (panel1) panel1.style.display = 'none';
        if (panel2) panel2.style.display = 'flex';
        
        // When switching to flight2 tab, ensure event listeners are attached
        setTimeout(() => {
            console.log("[DEBUG] Re-attaching flight2 radio listeners after tab switch");
            attachFlight2Listeners();
            
            // Ensure first flight2 is selected and header is updated
            const flight2Radios = document.querySelectorAll('.flight2-radio');
            if (flight2Radios.length > 0) {
                const checkedRadio = Array.from(flight2Radios).find(r => r.checked);
                const radioToUse = checkedRadio || flight2Radios[0];
                console.log("[DEBUG] Updating flight2 header for selected radio:", radioToUse.value);
                selectFlight2(radioToUse);
            }
        }, 50);
    }
}

function selectFlight1(radioElement) {
    // Parse fare value - remove extra spaces
    const fareStr = (radioElement.dataset.fare || '0').trim().replace(/\s+/g, '');
    const fareValue = parseFloat(fareStr) || 0;
    
    selectedFlight1 = {
        id: radioElement.value,
        plane: radioElement.dataset.plane || 'Unknown',
        depart: radioElement.dataset.depart || '00:00',
        arrive: radioElement.dataset.arrive || '00:00',
        fare: fareValue,
        fareDisplay: '$' + fareValue.toFixed(2)
    };
    
    console.log("[DEBUG] selectFlight1 called:", selectedFlight1);
    
    // Update flight1 panel header with times
    const f1HeaderTime = document.getElementById('f1-header-time');
    if (f1HeaderTime) {
        f1HeaderTime.textContent = selectedFlight1.depart + ' • ' + selectedFlight1.arrive;
        console.log("[DEBUG] Updated f1-header-time to:", selectedFlight1.depart + ' • ' + selectedFlight1.arrive);
    } else {
        console.log("[DEBUG] f1-header-time element not found");
    }
    
    updateSelectionSummary();
}

function selectFlight2(radioElement) {
    // Parse fare value - remove extra spaces
    const fareStr = (radioElement.dataset.fare || '0').trim().replace(/\s+/g, '');
    const fareValue = parseFloat(fareStr) || 0;
    
    const depart = radioElement.dataset.depart || '00:00';
    const arrive = radioElement.dataset.arrive || '00:00';
    
    console.log("[DEBUG] selectFlight2 raw data:");
    console.log("[DEBUG]   radioElement:", radioElement);
    console.log("[DEBUG]   radioElement.value:", radioElement.value);
    console.log("[DEBUG]   dataset.depart (raw):", radioElement.dataset.depart);
    console.log("[DEBUG]   dataset.arrive (raw):", radioElement.dataset.arrive);
    console.log("[DEBUG]   dataset.plane (raw):", radioElement.dataset.plane);
    
    selectedFlight2 = {
        id: radioElement.value,
        plane: radioElement.dataset.plane || 'Unknown',
        depart: depart,
        arrive: arrive,
        fare: fareValue,
        fareDisplay: '$' + fareValue.toFixed(2)
    };
    
    console.log("[DEBUG] selectFlight2 called:", selectedFlight2);
    console.log("[DEBUG] selectFlight2 data-depart from radio:", radioElement.dataset.depart);
    console.log("[DEBUG] selectFlight2 data-arrive from radio:", radioElement.dataset.arrive);
    
    // Update flight2 panel header with times
    const f2HeaderTime = document.getElementById('f2-header-time');
    console.log("[DEBUG] Looking for f2-header-time element:", f2HeaderTime);
    
    if (f2HeaderTime) {
        const newText = selectedFlight2.depart + ' • ' + selectedFlight2.arrive;
        f2HeaderTime.textContent = newText;
        f2HeaderTime.innerHTML = newText; // Try both methods
        console.log("[DEBUG] Updated f2-header-time to:", newText);
        console.log("[DEBUG] f2-header-time innerHTML is now:", f2HeaderTime.innerHTML);
        console.log("[DEBUG] f2-header-time textContent is now:", f2HeaderTime.textContent);
    } else {
        console.log("[DEBUG] f2-header-time element NOT found");
        // Try to find it with a broader search
        const allSpans = document.querySelectorAll('span[id*="header"]');
        console.log("[DEBUG] Found " + allSpans.length + " spans with 'header' in id");
        allSpans.forEach(span => console.log("[DEBUG] Found span id:", span.id, "content:", span.textContent));
    }
    
    updateSelectionSummary();
}

function updateSelectionSummary() {
    // Update hidden form fields for submission
    const flt1Input = document.getElementById('flt1');
    const flt2Input = document.getElementById('flt2');
    
    if (flt1Input && selectedFlight1) {
        flt1Input.value = selectedFlight1.id;
    }
    
    if (flt2Input && selectedFlight2) {
        flt2Input.value = selectedFlight2.id;
    }
    
    // Update selection display elements
    updateDisplayElements();
}

function updateDisplayElements() {
    if (selectedFlight1) {
        const elements = {
            'select-f1-plane': selectedFlight1.plane,
            'select-f1-depart': selectedFlight1.depart,
            'select-f1-arrive': selectedFlight1.arrive,
            'select-f1-fare': selectedFlight1.fareDisplay
        };
        
        Object.keys(elements).forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = elements[id];
        });
    }
    
    if (selectedFlight2) {
        const elements = {
            'select-f2-plane': selectedFlight2.plane,
            'select-f2-depart': selectedFlight2.depart,
            'select-f2-arrive': selectedFlight2.arrive,
            'select-f2-fare': selectedFlight2.fareDisplay
        };
        
        Object.keys(elements).forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = elements[id];
        });
    }
    
    // Update total fare
    if (selectedFlight1 && selectedFlight2) {
        const totalFare = selectedFlight1.fare + selectedFlight2.fare;
        const totalDisplay = '$' + totalFare.toFixed(2);
        console.log(`[DEBUG] Total fare: ${selectedFlight1.fare} + ${selectedFlight2.fare} = ${totalFare}`);
        
        const totalEl1 = document.getElementById('select-total-fare');
        if (totalEl1) {
            totalEl1.textContent = totalDisplay;
            console.log(`[DEBUG] Updated select-total-fare to: ${totalDisplay}`);
        }
        
        const totalEl2 = document.getElementById('select-total-fare-media');
        if (totalEl2) {
            totalEl2.textContent = totalDisplay;
            console.log(`[DEBUG] Updated select-total-fare-media to: ${totalDisplay}`);
        }
    } else if (selectedFlight1) {
        const totalDisplay = '$' + selectedFlight1.fare.toFixed(2);
        console.log(`[DEBUG] Only flight1 selected: ${totalDisplay}`);
        
        const totalEl1 = document.getElementById('select-total-fare');
        if (totalEl1) totalEl1.textContent = totalDisplay;
        
        const totalEl2 = document.getElementById('select-total-fare-media');
        if (totalEl2) totalEl2.textContent = totalDisplay;
    }
}

function attachFlight2Listeners() {
    console.log("[DEBUG] Attaching flight2 radio listeners");
    const flight2Radios = document.querySelectorAll('.flight2-radio');
    console.log("[DEBUG] Found " + flight2Radios.length + " flight2 radio buttons for listener attachment");
    
    if (flight2Radios.length === 0) {
        console.warn("[DEBUG] WARNING: No flight2 radios found!");
        return;
    }
    
    flight2Radios.forEach((radio, index) => {
        console.log("[DEBUG] Attaching listener to flight2 radio #" + index + " with id:", radio.value);
        
        // Change event listener
        const changeListener = (e) => {
            if (e.target.checked) {
                console.log("[DEBUG] flight2 radio changed event:", e.target.value);
                selectFlight2(e.target);
            }
        };
        
        // Click event listener
        const clickListener = (e) => {
            console.log("[DEBUG] flight2 radio clicked, checking state");
            // Ensure it's checked
            setTimeout(() => {
                if (radio.checked) {
                    console.log("[DEBUG] flight2 radio now checked after click:", e.target.value);
                    selectFlight2(e.target);
                }
            }, 10);
        };
        
        radio.addEventListener('change', changeListener);
        radio.addEventListener('click', clickListener);
        
        // Also add input event for extra compatibility
        radio.addEventListener('input', changeListener);
    });
}

function initializeFlightSelection() {
    console.log("[DEBUG] Initializing flight selection");
    
    // Add event listeners to outbound flight radio buttons
    const flight1Radios = document.querySelectorAll('.flight1-radio');
    console.log("[DEBUG] Found " + flight1Radios.length + " flight1 radio buttons");
    flight1Radios.forEach((radio, index) => {
        console.log("[DEBUG] Adding listeners to flight1 radio " + index);
        // Listen to both 'change' and 'click' for better compatibility
        radio.addEventListener('change', (e) => {
            if (e.target.checked) {
                console.log("[DEBUG] flight1 radio changed:", e.target.value);
                selectFlight1(e.target);
            }
        });
        radio.addEventListener('click', (e) => {
            // Force check the radio immediately on click
            e.target.checked = true;
            if (e.target.checked) {
                console.log("[DEBUG] flight1 radio clicked:", e.target.value);
                selectFlight1(e.target);
            }
        });
    });
    
    // Attach flight2 listeners using the new function
    attachFlight2Listeners();
    
    // Select first flights by default if available
    if (flight1Radios.length > 0) {
        console.log("[DEBUG] Setting first flight1 as checked");
        flight1Radios[0].checked = true;
        selectFlight1(flight1Radios[0]);
    }
    
    const flight2Radios = document.querySelectorAll('.flight2-radio');
    if (flight2Radios.length > 0) {
        console.log("[DEBUG] Setting first flight2 as checked");
        flight2Radios[0].checked = true;
        selectFlight2(flight2Radios[0]);
    }
}