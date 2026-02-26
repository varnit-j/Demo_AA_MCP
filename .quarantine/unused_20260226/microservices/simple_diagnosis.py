#!/usr/bin/env python3.12
"""
Simple diagnostic script for microservices startup issues
"""

import os
import sys
import subprocess

def check_django():
    """Check Django availability"""
    print("=== Django Check ===")
    try:
        result = subprocess.run([
            sys.executable, '-c', 'import django; print("Django version:", django.VERSION)'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("OK: Django is available")
            print(result.stdout.strip())
            return True
        else:
            print("ERROR: Django not available")
            print(result.stderr.strip())
            return False
    except Exception as e:
        print(f"ERROR: Django check failed: {e}")
        return False

def check_ports():
    """Check port configurations"""
    print("\n=== Port Configuration Check ===")
    
    # Read UI service settings to check port mappings
    ui_settings = 'microservices/ui-service/ui/settings.py'
    if os.path.exists(ui_settings):
        with open(ui_settings, 'r') as f:
            content = f.read()
        
        print("UI Service port mappings:")
        for line in content.split('\n'):
            if 'SERVICE_URL' in line and 'localhost:' in line:
                print(f"  {line.strip()}")
        
        # Check if ports match README specification
        # README: Backend (8001), Payment (8002), Loyalty (8003), UI (8000)
        payment_correct = 'PAYMENT_SERVICE_URL' in content and 'localhost:8002' in content
        loyalty_correct = 'LOYALTY_SERVICE_URL' in content and 'localhost:8003' in content
        backend_correct = 'BACKEND_SERVICE_URL' in content and 'localhost:8001' in content
        
        if payment_correct and loyalty_correct and backend_correct:
            print("OK: Port configuration matches README specification")
            return True
        else:
            print("ERROR: Port configuration doesn't match README!")
            if not payment_correct:
                print("  Payment service should be on port 8002")
            if not loyalty_correct:
                print("  Loyalty service should be on port 8003")
            if not backend_correct:
                print("  Backend service should be on port 8001")
            return False
    else:
        print("ERROR: UI service settings not found")
        return False

def main():
    print("Microservices Diagnostic Tool")
    print("=" * 40)
    
    django_ok = check_django()
    ports_ok = check_ports()
    
    print("\n" + "=" * 40)
    print("SUMMARY:")
    print(f"  Django: {'OK' if django_ok else 'ERROR'}")
    print(f"  Ports: {'OK' if ports_ok else 'ERROR'}")
    
    if not django_ok:
        print("\nRECOMMENDATION: Install Django first")
        print("  pip install Django==3.1.2")
    
    if not ports_ok:
        print("\nRECOMMENDATION: Fix port configuration conflicts")
        print("  Update UI service settings to match README ports")
    
    return django_ok and ports_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)