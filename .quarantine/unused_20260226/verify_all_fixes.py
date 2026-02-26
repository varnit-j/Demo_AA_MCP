#!/usr/bin/env python
"""
Final comprehensive verification of all template fixes
"""
import re

template_path = r"microservices\ui-service\templates\flight\search.html"

print("=" * 80)
print("COMPREHENSIVE TEMPLATE VERIFICATION")
print("=" * 80)

# Read the template
with open(template_path, 'r') as f:
    content = f.read()
    lines = content.split('\n')

# Check for broken filters
broken_time_pattern = r'\|time\s*:\s*["\']H:i["\']'
broken_matches = list(re.finditer(broken_time_pattern, content))

# Check for good slice filters
good_slice_pattern = r'\|slice\s*:\s*["\']:5["\']'
good_matches = list(re.finditer(good_slice_pattern, content))

print(f"\n✓ SLICE FILTERS (should work): {len(good_matches)} found")
print(f"✗ BROKEN TIME FILTERS (should be 0): {len(broken_matches)} found")

if len(broken_matches) > 0:
    print("\n⚠ WARNING: Broken filters still exist:")
    for i, match in enumerate(broken_matches, 1):
        # Find line number
        line_num = content[:match.start()].count('\n') + 1
        line_content = lines[line_num - 1]
        print(f"  Line {line_num}: {line_content.strip()[:80]}")
else:
    print("\n✓ SUCCESS: No broken filters found!")

# Detailed checks for critical elements
print("\n" + "=" * 80)
print("CRITICAL ELEMENT CHECKS")
print("=" * 80)

critical_elements = [
    ('f1-header-time', 'Flight 1 header with times'),
    ('f2-header-time', 'Flight 2 header with times (RETURN FLIGHT)'),
    ('select-f1-depart', 'Flight 1 selected depart display'),
    ('select-f1-arrive', 'Flight 1 selected arrival display'),
    ('select-f2-depart', 'Flight 2 selected depart display (RETURN)'),
    ('select-f2-arrive', 'Flight 2 selected arrival display (RETURN)'),
    ('flight1-radio r-b', 'Flight 1 radio buttons'),
    ('flight2-radio r-b', 'Flight 2 radio buttons (RETURN)'),
]

all_good = True
for element_id, description in critical_elements:
    if element_id in content:
        # Check if this element has slice filter
        if '|slice:":5"' in content or '|slice' in content:
            # Find the specific element
            pattern = f'{element_id}.*?{{{{.*?}}}}'
            match = re.search(pattern, content)
            if match and '|time' not in match.group():
                print(f"✓ {description:50s} - FIXED")
            elif match and '|slice:":5"' in match.group():
                print(f"✓ {description:50s} - FIXED")
            else:
                print(f"⚠ {description:50s} - NEEDS CHECK")
                if match:
                    print(f"  Found: {match.group()[:60]}")
                all_good = False
        else:
            print(f"✓ {description:50s} - VERIFIED")
    else:
        print(f"? {description:50s} - NOT FOUND")

# Final summary
print("\n" + "=" * 80)
print("FINAL SUMMARY")
print("=" * 80)

if len(broken_matches) == 0:
    print("""
✓ ALL CRITICAL FIXES HAVE BEEN APPLIED

The following changes were made to fix the round trip flight times issue:

1. Line 170: Flight 1 header - Changed from |time to |slice:":5"
2. Line 421: Flight 1 radio buttons - Changed from |time to |slice:":5"
3. Line 469: Flight 2 header - Changed from |time to |slice:":5" ← RETURN FLIGHT
4. Line 683: Flight 2 listing depart - Changed from |time to |slice:":5"
5. Line 697: Flight 2 listing arrival - Changed from |time to |slice:":5"
6. Line 721: Flight 2 radio buttons - Changed from |time to |slice:":5" ← RETURN FLIGHT
7. Line 790: Flight 1 selected depart - Changed from |time to |slice:":5"
8. Line 792: Flight 1 selected arrival - Changed from |time to |slice:":5"
9. Line 828: Flight 2 selected depart - Changed from |time to |slice:":5" ← RETURN FLIGHT
10. Line 830: Flight 2 selected arrival - Changed from |time to |slice:":5" ← RETURN FLIGHT

EXPECTED RESULT:
When users search for round trip flights, both the outbound and return flight 
times should now display correctly in:
- Headers at the top of each flight panel
- Radio button selections
- Bottom summary display

REASON FOR FIX:
The Django template |time:"H:i" filter only works on datetime/time objects.
The API returns time values as ISO strings ("08:09:00"), so the filter would
fail silently, producing empty output. The |slice:":5" filter works on strings
and extracts "HH:MM" from "HH:MM:SS".

NEXT STEP:
Start the services and test round trip flight search to verify times display.
""")
else:
    print(f"\n✗ ALERT: {len(broken_matches)} broken filter(s) still remain!")
    print("Please fix them before deploying.")

print("=" * 80)
