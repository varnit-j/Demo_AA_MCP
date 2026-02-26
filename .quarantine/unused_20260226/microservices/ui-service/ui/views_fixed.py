
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone
import json
import requests
from django.conf import settings
from datetime import datetime
import math
import re
from decimal import Decimal
from . import loyalty_tracker

# Fee and Surcharge variable
FEE = 50.0

# Helper function to make API calls to backend service
def call_backend_api(endpoint, method='GET', data=None, timeout=10, retries=3):
    """
    Make API calls to the backend service with proper error handling
    
    Args:
        endpoint: API endpoint (without protocol/domain)
        method: HTTP method (GET, POST, etc.)
        data: Request data
        timeout: Request timeout in seconds
        retries: Number of retry attempts
    
    Returns:
        JSON response dict or None on failure
    """
    backend_url = settings.BACKEND_SERVICE_URL
    url = f"{backend_url}/{endpoint}"
    
    print(f"[DEBUG] API CALL: {method} {url}")
    if data:
        print(f"[DEBUG] Request data keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
    
    for attempt in range(retries):
        try:
            print(f"[DEBUG] Attempt {attempt + 1}/{retries}")
            
            if method == 'GET':
                response = requests.get(url, params=data, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, timeout=timeout)
            else:
                print(f"[DEBUG] Unsupported method: {method}")
                return None
            
            print(f"[DEBUG] Response status: {response.status_code}")
            
            # Handle successful responses (including 202 Accepted for async operations)
            if response.status_code in [200, 201, 202]:
                try:
                    result = response.json()
                    print(f"[DEBUG] API Success - Response keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
                    return result
                except json.JSONDecodeError as e:
                    print(f"[DEBUG] JSON decode error: {e}")
                    print(f"[DEBUG] Raw response: {response.text[:200]}")
                    return None
            
            # Handle error responses with status codes
            elif response.status_code == 404:
                print(f"[DEBUG] API returned 404 - Endpoint not found: {url}")
                return None
            elif response.status_code == 500:
                print(f"[DEBUG] API returned 500 - Server error")
                if attempt < retries - 1:
                    print(f"[DEBUG] Retrying...")
                    continue
                return None
            elif response.status_code == 400:
                print(f"[DEBUG] API returned 400 - Bad request")
                try:
                    error_data = response.json()
                    print(f"[DEBUG] Error details: {error_data}")
                except:
                    print(f"[DEBUG] Response body: {response.text[:200]}")
                return None
            else:
                print(f"[DEBUG] API returned {response.status_code}")
                print(f"[DEBUG] Response: {response.text[:200]}")
                return None
        
        except requests.exceptions.Timeout:
            print(f"[DEBUG] Request timeout (attempt {attempt + 1}/{retries})")
            if attempt < retries -