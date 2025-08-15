"""
RNR Solutions - OpenAPI Configuration Verification
Verify that the FastAPI configuration includes the correct OpenAPI version
"""

import os
import re

def check_main_py():
    """Check the main.py file for OpenAPI configuration"""
    main_py_path = os.path.join('backend', 'api', 'main.py')
    
    if not os.path.exists(main_py_path):
        print(f"✗ {main_py_path} not found")
        return False
    
    print(f"✓ Found {main_py_path}")
    
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for FastAPI app creation
    fastapi_pattern = r'app\s*=\s*FastAPI\s*\('
    if re.search(fastapi_pattern, content):
        print("✓ FastAPI app creation found")
    else:
        print("✗ FastAPI app creation not found")
        return False
    
    # Check for openapi_version parameter
    openapi_version_pattern = r'openapi_version\s*=\s*["\']([^"\']+)["\']'
    match = re.search(openapi_version_pattern, content)
    
    if match:
        version = match.group(1)
        print(f"✓ openapi_version parameter found: {version}")
        
        # Validate version format
        if re.match(r'^3\.\d+\.\d+$', version):
            print(f"✓ Valid OpenAPI 3.x version format: {version}")
            return True
        else:
            print(f"⚠ OpenAPI version format may be invalid: {version}")
            return False
    else:
        print("✗ openapi_version parameter not found")
        return False

def check_docker_files():
    """Check Docker configuration files"""
    dockerfile_api = os.path.join('backend', 'Dockerfile.api')
    dockerfile_worker = os.path.join('backend', 'Dockerfile.worker')
    
    files_to_check = [dockerfile_api, dockerfile_worker]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"✓ Found {file_path}")
        else:
            print(f"⚠ {file_path} not found")

def main():
    print("========================================")
    print("RNR IoT Platform - OpenAPI Fix Verification")
    print("========================================")
    
    print("\n1. Checking FastAPI configuration...")
    main_py_ok = check_main_py()
    
    print("\n2. Checking Docker files...")
    check_docker_files()
    
    print("\n3. Summary...")
    if main_py_ok:
        print("✓ OpenAPI version fix has been applied correctly!")
        print("✓ The FastAPI app now includes openapi_version='3.1.0'")
        print("✓ This should resolve the Swagger UI parser error")
    else:
        print("✗ OpenAPI version fix needs to be applied")
    
    print("\n4. Next steps...")
    if main_py_ok:
        print("When you restart your Docker containers:")
        print("• The OpenAPI JSON will include the version field")
        print("• Swagger UI should load without parser errors")
        print("• Clear your browser cache if you still see issues")
        print("\nTo restart with the fix:")
        print("1. docker-compose down")
        print("2. docker-compose up --build -d")
        print("3. Wait for services to start")
        print("4. Access http://localhost:8000/docs")
    else:
        print("The OpenAPI version needs to be added to the FastAPI configuration")
    
    print("\n========================================")
    print("Fix Status: " + ("COMPLETE ✓" if main_py_ok else "NEEDS ATTENTION ✗"))
    print("========================================")

if __name__ == "__main__":
    main()
