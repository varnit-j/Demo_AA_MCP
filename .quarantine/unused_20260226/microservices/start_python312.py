#!/usr/bin/env python3.12
"""
Start all microservices using Python 3.12
"""

import os
import sys
import subprocess
import time
import threading
from pathlib import Path

class ServiceManager:
    def __init__(self):
        self.services = {
            'backend-service': {
                'path': 'microservices/backend-service',
                'port': 8001,
                'process': None
            },
            'payment-service': {
                'path': 'microservices/payment-service', 
                'port': 8002,
                'process': None
            },
            'loyalty-service': {
                'path': 'microservices/loyalty-service',
                'port': 8003,
                'process': None
            },
            'ui-service': {
                'path': 'microservices/ui-service',
                'port': 8000,
                'process': None
            }
        }
        
    def install_dependencies(self, service_name, service_info):
        """Install dependencies for a service"""
        req_file = os.path.join(service_info['path'], 'requirements.txt')
        if os.path.exists(req_file):
            print(f"Installing dependencies for {service_name}...")
            try:
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '-r', req_file
                ], check=True, capture_output=True)
                print(f"  Dependencies installed for {service_name}")
                return True
            except subprocess.CalledProcessError as e:
                print(f"  ERROR: Failed to install dependencies for {service_name}")
                print(f"  {e.stderr.decode() if e.stderr else 'Unknown error'}")
                return False
        else:
            print(f"  No requirements.txt found for {service_name}")
            return True
    
    def migrate_database(self, service_name, service_info):
        """Run database migrations for a service"""
        print(f"Running migrations for {service_name}...")
        try:
            result = subprocess.run([
                sys.executable, 'manage.py', 'migrate'
            ], cwd=service_info['path'], check=True, capture_output=True, text=True)
            print(f"  Migrations completed for {service_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  WARNING: Migration failed for {service_name}")
            print(f"  {e.stderr if e.stderr else 'Unknown error'}")
            # Don't fail completely - service might still work
            return True
    
    def start_service(self, service_name, service_info):
        """Start a single service"""
        print(f"Starting {service_name} on port {service_info['port']}...")
        
        try:
            # Start the Django development server
            process = subprocess.Popen([
                sys.executable, 'manage.py', 'runserver', f"127.0.0.1:{service_info['port']}"
            ], cwd=service_info['path'], 
               stdout=subprocess.PIPE, 
               stderr=subprocess.PIPE,
               text=True)
            
            service_info['process'] = process
            print(f"  {service_name} started (PID: {process.pid})")
            return True
            
        except Exception as e:
            print(f"  ERROR: Failed to start {service_name}: {e}")
            return False
    
    def check_service_health(self, service_name, service_info):
        """Check if service is responding"""
        import urllib.request
        import urllib.error
        
        url = f"http://127.0.0.1:{service_info['port']}"
        try:
            with urllib.request.urlopen(url, timeout=5