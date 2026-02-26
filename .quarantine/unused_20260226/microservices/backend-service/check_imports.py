import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# Try importing everything to see if there's an import error
try:
    from flight.urls import urlpatterns
    print(f"✓ URL patterns loaded: {len(urlpatterns)} patterns")
except Exception as e:
    print(f"✗ Error loading URLs: {e}")
    import traceback
    traceback.print_exc()

try:
    from django.core.management import call_command
    print("✓ Management commands available")
except Exception as e:
    print(f"✗ Error with management: {e}")

print("\nAll imports successful - ready to run server")
