#!/usr/bin/env python3
"""
RNR Solutions - Quick OpenAPI Test
Test the FastAPI application and OpenAPI JSON generation directly
"""

import sys
import os
import json
import logging
from fastapi.testclient import TestClient

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    # Import the FastAPI app
    from api.main import app
    
    print("========================================")
    print("RNR IoT Platform - OpenAPI Direct Test")
    print("Testing OpenAPI JSON generation locally")
    print("========================================")
    
    # Create test client
    client = TestClient(app)
    
    print("1. Testing health endpoint...")
    try:
        response = client.get("/health")
        if response.status_code == 200:
            print("✓ Health endpoint works")
            print(f"  Response: {response.json()}")
        else:
            print(f"✗ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Health endpoint error: {e}")
    
    print("\n2. Testing OpenAPI JSON generation...")
    try:
        response = client.get("/openapi.json")
        if response.status_code == 200:
            print("✓ OpenAPI endpoint works")
            
            # Parse the JSON
            openapi_data = response.json()
            
            # Check for OpenAPI version
            if 'openapi' in openapi_data:
                print(f"✓ OpenAPI version found: {openapi_data['openapi']}")
            else:
                print("✗ OpenAPI version field missing!")
                
            # Check for required fields
            required_fields = ['info', 'paths']
            for field in required_fields:
                if field in openapi_data:
                    print(f"✓ {field} section found")
                else:
                    print(f"✗ {field} section missing")
            
            # Show some statistics
            print(f"✓ OpenAPI JSON size: {len(response.content)} bytes")
            if 'paths' in openapi_data:
                print(f"✓ Number of API paths: {len(openapi_data['paths'])}")
            
            # Save to file for inspection
            with open('openapi_test_output.json', 'w') as f:
                json.dump(openapi_data, f, indent=2)
            print("✓ OpenAPI JSON saved to openapi_test_output.json")
            
            # Validate JSON structure
            try:
                json.dumps(openapi_data)
                print("✓ OpenAPI JSON is valid")
            except Exception as e:
                print(f"✗ OpenAPI JSON validation error: {e}")
                
        else:
            print(f"✗ OpenAPI endpoint failed: {response.status_code}")
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"✗ OpenAPI endpoint error: {e}")
    
    print("\n3. Testing docs endpoint...")
    try:
        response = client.get("/docs")
        if response.status_code == 200:
            print("✓ Docs endpoint works")
            print(f"  Response size: {len(response.content)} bytes")
        else:
            print(f"✗ Docs endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Docs endpoint error: {e}")
    
    print("\n========================================")
    print("OpenAPI Direct Test Complete!")
    print("========================================")
    
    if os.path.exists('openapi_test_output.json'):
        print("\nTo manually inspect the OpenAPI JSON:")
        print("1. Open openapi_test_output.json in VS Code")
        print("2. Check line 16 and around it for any syntax issues")
        print("3. Look for the 'openapi' field at the top")
        print("\nThe parser error 'line 16' might be from:")
        print("- A malformed JSON structure")
        print("- Missing commas or brackets")
        print("- Invalid characters in the JSON")
    
except ImportError as e:
    print(f"✗ Failed to import FastAPI app: {e}")
    print("Make sure you're in the correct directory and dependencies are installed")
    
    # Try to show what we can find
    print("\nLet's check what's available:")
    backend_path = os.path.join(os.path.dirname(__file__), 'backend')
    if os.path.exists(backend_path):
        print(f"✓ Backend directory exists: {backend_path}")
        api_path = os.path.join(backend_path, 'api')
        if os.path.exists(api_path):
            print(f"✓ API directory exists: {api_path}")
            main_path = os.path.join(api_path, 'main.py')
            if os.path.exists(main_path):
                print(f"✓ main.py exists: {main_path}")
            else:
                print(f"✗ main.py not found: {main_path}")
        else:
            print(f"✗ API directory not found: {api_path}")
    else:
        print(f"✗ Backend directory not found: {backend_path}")

except Exception as e:
    print(f"✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
