#!/usr/bin/env python3.12
"""
Wrapper script to run backend server with better error reporting
"""
import os
import sys
import subprocess

os.chdir('d:\\varnit\\demo\\2101_f\\2101_UI_Chang\\AA_Flight_booking_UI_DEMO\\microservices\\backend-service')

# Run with unbuffered output
cmd = [
    sys.executable,
    'manage.py',
    'runserver',
    '0.0.0.0:8001',
    '--nothreading',
    '--noreload'
]

print(f"Starting backend server with command: {' '.join(cmd)}")
print(f"Working directory: {os.getcwd()}")
print("=" * 80)

result = subprocess.run(cmd)
sys.exit(result.returncode)
