#!/usr/bin/env python3.12
"""
Simple script to start all microservices with Python 3.12
"""

import os
import sys
import subprocess
import time

def start_service(service_name, service_path, port):
    """Start a single microservice"""
    print(f"Starting {service_name} on port {port}...")
    
    if not os.path.exists(service_path):
        print(f"  ERROR: {service_path} not found")
        return None
    
    # Install dependencies if requirements.txt exists
    req_file = os.path.join(service_path, 'requirements.txt')
    if os.path.exists(req_file):
        print(f"  Installing dependencies for {service_name}...")
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', req_file
            ], check=True, capture_output=True)
            print(f"  Dependencies installed")
        except subprocess.CalledProcessError:
            print(f"  WARNING: Failed to install dependencies")
    
    # Run migrations
    print(f"  Running migrations for {service_name}...")
    try:
        subprocess.run([
            sys.executable, 'manage.py', 'migrate'
        ], cwd=service_path, check=True, capture_output=True)
        print(f"  Migrations completed")
    except subprocess.CalledProcessError:
        print(f"  WARNING: Migrations failed")
    
    # Start the service
    try:
        process = subprocess.Popen([
            sys.executable, 'manage.py', 'runserver', f'127.0.0.1:{port}'
        ], cwd=service_path)
        
        print(f"  {service_name} started successfully (PID: {process.pid})")
        return process
        
    except Exception as e:
        print(f"  ERROR: Failed to start {service_name}: {e}")
        return None

def main():
    print("Flight Booking Microservices Startup")
    print("Using Python 3.12")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('microservices'):
        print("ERROR: Please run from project root directory")
        return False
    
    # Define services with their paths and ports
    services = [
        ('Backend Service', 'microservices/backend-service', 8001),
        ('Payment Service', 'microservices/payment-service', 8002),
        ('Loyalty Service', 'microservices/loyalty-service', 8003),
        ('UI Service', 'microservices/ui-service', 8000),
    ]
    
    processes = []
    
    # Start each service
    for service_name, service_path, port in services:
        print(f"\n--- {service_name} ---")
        process = start_service(service_name, service_path, port)
        if process:
            processes.append((service_name, process, port))
            time.sleep(3)  # Give service time to start
    
    # Summary
    print(f"\n" + "=" * 50)
    print("STARTUP COMPLETE")
    print(f"Started {len(processes)} services:")
    
    for service_name, process, port in processes:
        print(f"  {service_name}: http://localhost:{port} (PID: {process.pid})")
    
    if processes:
        print(f"\nAll services are running!")
        print(f"Main UI available at: http://localhost:8000")
        print(f"\nPress Ctrl+C to stop all services")
        
        try:
            # Keep script running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\nStopping all services...")
            for service_name, process, port in processes:
                print(f"  Stopping {service_name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
            print("All services stopped.")
    else:
        print("No services were started successfully.")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)