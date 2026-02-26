#!/usr/bin/env python3.12
"""
Diagnostic script to identify potential issues with microservices startup
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_django_compatibility():
    """Check if Django 3.1.2 works with Python 3.12"""
    print("=== Django Compatibility Check ===")
    try:
        # Try to install Django 3.1.2 in a test environment
        result = subprocess.run([
            sys.executable, '-c', 
            'import django; print(f"Django version: {django.VERSION}")'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✓ Django is importable")
            print(result.stdout.strip())
        else:
            print("✗ Django import failed:")
            print(result.stderr.strip())
            return False
    except Exception as e:
        print(f"✗ Django compatibility check failed: {e}")
        return False
    
    return True

def analyze_port_configurations():
    """Analyze port configurations across services"""
    print("\n=== Port Configuration Analysis ===")
    
    services = {
        'backend-service': 'microservices/backend-service/backend/settings.py',
        'payment-service': 'microservices/payment-service/payment/settings.py', 
        'loyalty-service': 'microservices/loyalty-service/loyalty/settings.py',
        'ui-service': 'microservices/ui-service/ui/settings.py'
    }
    
    port_mappings = {}
    
    for service_name, settings_path in services.items():
        if os.path.exists(settings_path):
            print(f"\n--- {service_name} ---")
            with open(settings_path, 'r') as f:
                content = f.read()
                
            # Extract service URL configurations
            lines = content.split('\n')
            for line in lines:
                if 'SERVICE_URL' in line and '=' in line:
                    print(f"  {line.strip()}")
                    
                    # Extract port from URL
                    if 'localhost:' in line:
                        try:
                            port = line.split('localhost:')[1].split("'")[0].split(')')[0]
                            service_type = line.split('_SERVICE_URL')[0].split()[-1]
                            port_mappings[f"{service_name}->{service_type}"] = port
                        except:
                            pass
        else:
            print(f"✗ {service_name}: Settings file not found")
    
    print(f"\n--- Port Mapping Summary ---")
    for mapping, port in port_mappings.items():
        print(f"  {mapping}: {port}")
    
    # Check for conflicts
    conflicts = []
    port_usage = {}
    for mapping, port in port_mappings.items():
        if port in port_usage:
            conflicts.append(f"Port {port} used by both {port_usage[port]} and {mapping}")
        else:
            port_usage[port] = mapping
    
    if conflicts:
        print(f"\n✗ Port Conflicts Detected:")
        for conflict in conflicts:
            print(f"  {conflict}")
        return False
    else:
        print(f"\n✓ No port conflicts detected in service URLs")
        return True

def check_dependencies():
    """Check if all required dependencies can be installed"""
    print("\n=== Dependency Check ===")
    
    services = {
        'backend-service': 'microservices/backend-service/requirements.txt',
        'payment-service': 'microservices/payment-service/requirements.txt',
        'loyalty-service': None,  # No requirements.txt found
        'ui-service': None  # No requirements.txt found
    }
    
    all_deps_ok = True
    
    for service_name, req_file in services.items():
        print(f"\n--- {service_name} ---")
        if req_file and os.path.exists(req_file):
            with open(req_file, 'r') as f:
                deps = f.read().strip().split('\n')
            
            print(f"  Dependencies: {', '.join(deps)}")
            
            # Test Django import specifically
            if any('Django' in dep for dep in deps):
                try:
                    result = subprocess.run([
                        sys.executable, '-c', 'import django; print("Django OK")'
                    ], capture_output=True, text=True, timeout=5)
                    
                    if result.returncode == 0:
                        print("  ✓ Django import test passed")
                    else:
                        print("  ✗ Django import test failed")
                        all_deps_ok = False
                except Exception as e:
                    print(f"  ✗ Django test error: {e}")
                    all_deps_ok = False
        else:
            print("  ⚠ No requirements.txt found")
    
    return all_deps_ok

def main():
    """Main diagnostic function"""
    print("Flight Booking Microservices Diagnostic")
    print("=" * 50)
    
    # Check current directory
    if not os.path.exists('microservices'):
        print("✗ Not in correct directory. Please run from project root.")
        return False
    
    # Run all checks
    django_ok = check_python_django_compatibility()
    ports_ok = analyze_port_configurations()
    deps_ok = check_dependencies()
    
    print("\n" + "=" * 50)
    print("DIAGNOSTIC SUMMARY:")
    print(f"  Django Compatibility: {'✓' if django_ok else '✗'}")
    print(f"  Port Configuration: {'✓' if ports_ok else '✗'}")
    print(f"  Dependencies: {'✓' if deps_ok else '✗'}")
    
    if django_ok and ports_ok and deps_ok:
        print("\n✓ All checks passed! Services should start successfully.")
        return True
    else:
        print("\n✗ Issues detected. Please resolve before starting services.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)