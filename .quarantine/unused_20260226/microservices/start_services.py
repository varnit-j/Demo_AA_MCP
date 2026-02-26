#!/usr/bin/env python3
"""
Script to start available microservices
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n[INFO] {description}")
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"[SUCCESS] {description}")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    print("Flight Booking Microservices Startup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('docker-compose.yml'):
        print("[ERROR] docker-compose.yml not found. Please run from microservices directory.")
        sys.exit(1)
    
    # Check what services we have
    services_available = []
    
    if os.path.exists('backend-service'):
        services_available.append('backend-service')
        print("[OK] Backend Service found")
    
    if os.path.exists('payment-service'):
        services_available.append('payment-service')
        print("[OK] Payment Service found")
    else:
        print("[WARN] Payment Service not found")
    
    if os.path.exists('loyalty-service'):
        services_available.append('loyalty-service')
        print("[OK] Loyalty Service found")
    else:
        print("[WARN] Loyalty Service not found")
    
    if os.path.exists('ui-service'):
        services_available.append('ui-service')
        print("[OK] UI Service found")
    else:
        print("[WARN] UI Service not found")
    
    print(f"\nAvailable services: {len(services_available)}/4")
    
    # Start available services
    if services_available:
        print(f"\nStarting available services: {', '.join(services_available)}")
        
        # Start database first
        run_command("docker-compose up -d postgres", "Starting PostgreSQL database")
        
        # Start available services
        for service in services_available:
            run_command(f"docker-compose up -d {service}", f"Starting {service}")
        
        print("\nService Status:")
        run_command("docker-compose ps", "Checking service status")
        
        print("\nService URLs:")
        if 'backend-service' in services_available:
            print("   Backend Service: http://localhost:8001")
        if 'payment-service' in services_available:
            print("   Payment Service: http://localhost:8002")
        if 'loyalty-service' in services_available:
            print("   Loyalty Service: http://localhost:8003")
        if 'ui-service' in services_available:
            print("   UI Service: http://localhost:8000")
        
    else:
        print("[ERROR] No services found to start!")

if __name__ == "__main__":
    main()