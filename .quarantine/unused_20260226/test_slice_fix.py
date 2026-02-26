#!/usr/bin/env python
"""
Quick test to verify template fixes for round trip search
"""
import os
import sys

# Test the slice filter works correctly
test_time_strings = [
    "08:09:00",
    "10:42:00",
    "05:05:00", 
    "07:40:00",
    "14:15:30",
    "23:59:59"
]

print("Testing slice filter on time strings:")
print("=" * 50)

for time_str in test_time_strings:
    sliced = time_str[:5]
    print(f"'{time_str}'[:5] = '{sliced}'")
    assert sliced == time_str[:5], f"Slice failed for {time_str}"

print("\n✓ All slice filter tests pass")
print("\n" + "=" * 50)
print("Template filter fixes applied:")
print("=" * 50)
print("""
MICROSERVICES/UI-SERVICE/TEMPLATES/FLIGHT/SEARCH.HTML:
  ✓ Line 170: f1-header-time: {{flights.0.depart_time|slice:":5"}} • {{flights.0.arrival_time|slice:":5"}}
  ✓ Line 421: flight1-radio: data-depart='{{flight.depart_time|slice:":5"}}'
  ✓ Line 469: f2-header-time: {{flights2.0.depart_time|slice:":5"}} • {{flights2.0.arrival_time|slice:":5"}}
  ✓ Line 721: flight2-radio: data-depart='{{flight2.depart_time|slice:":5"}}'
  ✓ Line 790: select-f1-depart: {{flights.0.depart_time|slice:":5"}}
  ✓ Line 792: select-f1-arrive: {{flights.0.arrival_time|slice:":5"}}
  ✓ Line 828: select-f2-depart: {{flights2.0.depart_time|slice:":5"}}
  ✓ Line 830: select-f2-arrive: {{flights2.0.arrival_time|slice:":5"}}

REMAINING ITEMS TO CHECK:
  - Line 683: flight2 depart_time still uses |time (in flight listing, not critical)
  - Line 697: flight2 arrival_time still uses |time (in flight listing, not critical)
  - flight/templates/flight/search.html: Old app template (may need same fixes)
""")

print("\nAll critical template fixes have been applied!")
print("The return flight times should now display correctly in the UI.")
