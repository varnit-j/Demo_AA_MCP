#!/usr/bin/env python3.12
"""
Test runner script for AA Flight Booking System
Runs all tests with coverage reporting
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'capstone.settings')

# Setup Django
django.setup()

def run_tests():
    """Run all tests with coverage"""
    import subprocess
    
    # Install test dependencies if needed
    try:
        import pytest
        import pytest_django
        import pytest_cov
        import coverage
    except ImportError:
        print("Installing test dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pytest', 'pytest-django', 'pytest-cov', 'coverage'])
    
    # Run tests with coverage
    test_command = [
        sys.executable, '-m', 'pytest',
        'test/',
        '--verbose',
        '--tb=short',
        '--cov=flight',
        '--cov=apps',
        '--cov-report=html:test/htmlcov',
        '--cov-report=term-missing',
        '--cov-report=xml:test/coverage.xml',
        '--cov-fail-under=80'
    ]
    
    print("Running tests with coverage...")
    result = subprocess.run(test_command, cwd=project_root)
    
    if result.returncode == 0:
        print("\n✅ All tests passed!")
        print("📊 Coverage report generated in test/htmlcov/")
    else:
        print("\n❌ Some tests failed!")
    
    return result.returncode

if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)