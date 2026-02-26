#!/usr/bin/env python3.12
import os
import sys
import django
from django.core.management import execute_from_command_line

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# Run the development server
if __name__ == '__main__':
    sys.argv = ['manage.py', 'runserver', '0.0.0.0:8001']
    try:
        execute_from_command_line(sys.argv)
    except KeyboardInterrupt:
        print("\n\nServer stopped")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
