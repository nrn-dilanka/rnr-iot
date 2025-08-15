#!/bin/bash
# RNR Solutions - OpenAPI Version Fix and Test Script for Ubuntu
# Bash script to restart services and test the OpenAPI fix

echo "=========================================="
echo "RNR IoT Platform - OpenAPI Version Fix"
echo "Fixing missing OpenAPI version field"
echo "=========================================="

# Function to test endpoint
test_endpoint() {
    local url=$1
    local name=$2
    local timeout=${3:-30}
    
    echo -n "Testing $name... "
    
    if response=$(curl -s -w "%{http_code}" --max-time $timeout "$url" 2>/dev/null); then
        http_code="${response: -3}"
        response_body="${response%???}"
        
        if [ "$http_code" = "200" ]; then
            echo "✓ Success (200)"
            echo "$response_body"
            return 0
        else
            echo "✗ Failed ($http_code)"
            return 1
        fi
    else
        echo "✗ Connection failed"
        return 1
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo ""
echo "Checking prerequisites..."
echo "=========================================="

if ! command_exists docker; then
    echo "✗ Docker is not installed or not in PATH"
    exit 1
fi

if ! command_exists docker-compose; then
    echo "✗ Docker Compose is not installed or not in PATH"
    exit 1
fi

if ! command_exists curl; then
    echo "✗ curl is not installed"
    echo "Install with: sudo apt update && sudo apt install curl"
    exit 1
fi

if ! command_exists jq; then
    echo "⚠ jq is not installed (optional but recommended)"
    echo "Install with: sudo apt update && sudo apt install jq"
    JQ_AVAILABLE=false
else
    JQ_AVAILABLE=true
fi

echo "✓ Prerequisites check passed"

# Step 1: Stop existing containers
echo ""
echo "1. Stopping existing containers..."
echo "=========================================="

if docker-compose down; then
    echo "✓ Containers stopped successfully"
else
    echo "⚠ Error stopping containers (may not be running)"
fi

# Step 2: Rebuild and start containers
echo ""
echo "2. Building and starting containers..."
echo "=========================================="

echo "Building containers (this may take a few minutes)..."
if docker-compose up --build -d; then
    echo "✓ Containers started successfully"
else
    echo "✗ Error starting containers"
    echo "Checking logs..."
    docker-compose logs --tail=20
    exit 1
fi

# Step 3: Wait for services to be ready
echo ""
echo "3. Waiting for services to be ready..."
echo "=========================================="

max_wait_time=120  # 2 minutes
wait_time=0
interval=5

while [ $wait_time -lt $max_wait_time ]; do
    sleep $interval
    wait_time=$((wait_time + interval))
    echo "Waiting... ($wait_time/$max_wait_time seconds)"
    
    if curl -s -f http://localhost:8000/health >/dev/null 2>&1; then
        echo "✓ API server is ready!"
        break
    fi
    
    if [ $wait_time -ge $max_wait_time ]; then
        echo "✗ Timeout waiting for API server to be ready"
        echo "Checking container logs..."
        docker-compose logs rnr_api_server --tail=20
        exit 1
    fi
done

# Step 4: Test OpenAPI endpoint
echo ""
echo "4. Testing OpenAPI endpoint..."
echo "=========================================="

echo "Fetching OpenAPI JSON..."
openapi_response=$(curl -s http://localhost:8000/openapi.json)
openapi_size=${#openapi_response}

echo "OpenAPI JSON size: $openapi_size characters"

if [ $openapi_size -gt 1000 ]; then
    echo "✓ OpenAPI JSON appears to be complete"
    
    # Check if response is valid JSON
    if echo "$openapi_response" | python3 -m json.tool >/dev/null 2>&1; then
        echo "✓ OpenAPI JSON is valid"
        
        # Check for OpenAPI version field
        if echo "$openapi_response" | grep -q '"openapi"'; then
            openapi_version=$(echo "$openapi_response" | grep -o '"openapi":"[^"]*"' | head -1)
            echo "✓ OpenAPI version field found: $openapi_version"
            
            # Extract just the version number
            version_number=$(echo "$openapi_version" | cut -d'"' -f4)
            if [[ $version_number =~ ^3\.[0-9]+\.[0-9]+$ ]]; then
                echo "✓ Valid OpenAPI 3.x version format: $version_number"
            else
                echo "⚠ OpenAPI version format may be invalid: $version_number"
            fi
        else
            echo "✗ OpenAPI version field is missing!"
        fi
        
        # Check for required sections
        if echo "$openapi_response" | grep -q '"info"'; then
            echo "✓ Info section found"
        else
            echo "✗ Info section missing"
        fi
        
        if echo "$openapi_response" | grep -q '"paths"'; then
            echo "✓ Paths section found"
        else
            echo "✗ Paths section missing"
        fi
        
        # Check for components (OpenAPI 3.x)
        if echo "$openapi_response" | grep -q '"components"'; then
            echo "✓ Components section found"
        else
            echo "⚠ Components section not found (may be optional)"
        fi
        
    else
        echo "✗ OpenAPI JSON is invalid"
        echo "First 500 characters:"
        echo "$openapi_response" | head -c 500
        echo "..."
        echo "Last 200 characters:"
        echo "$openapi_response" | tail -c 200
        exit 1
    fi
else
    echo "✗ OpenAPI JSON appears to be truncated or missing"
    echo "Response received: $openapi_response"
    exit 1
fi

# Step 5: Test Swagger UI endpoints
echo ""
echo "5. Testing Swagger UI endpoints..."
echo "=========================================="

echo "Testing direct Swagger UI..."
curl -s -o /dev/null -w "Direct Swagger UI: %{http_code}\n" http://localhost:8000/docs

echo "Testing direct OpenAPI endpoint..."
curl -s -o /dev/null -w "Direct OpenAPI: %{http_code}\n" http://localhost:8000/openapi.json

echo "Testing health endpoint..."
curl -s -o /dev/null -w "Health endpoint: %{http_code}\n" http://localhost:8000/health

# Step 6: Test through nginx proxy (if available)
echo ""
echo "6. Testing through nginx proxy..."
echo "=========================================="

if curl -s -f http://localhost/api/health >/dev/null 2>&1; then
    echo "✓ Nginx proxy is available"
    
    echo "Testing proxied endpoints..."
    curl -s -o /dev/null -w "Proxied Health: %{http_code}\n" http://localhost/api/health
    curl -s -o /dev/null -w "Proxied OpenAPI: %{http_code}\n" http://localhost/api/openapi.json
    curl -s -o /dev/null -w "Proxied Swagger UI: %{http_code}\n" http://localhost/api/docs
else
    echo "⚠ Nginx proxy not available or not configured"
    echo "Services are accessible directly on port 8000"
fi

# Step 7: Get external IP and test external access
echo ""
echo "7. Testing external access..."
echo "=========================================="

if public_ip=$(curl -s --max-time 10 ifconfig.me 2>/dev/null); then
    echo "Public IP: $public_ip"
    
    echo "Testing external endpoints..."
    curl -s -o /dev/null -w "External Health: %{http_code}\n" "http://$public_ip/api/health" 2>/dev/null || echo "External Health: Network error"
    curl -s -o /dev/null -w "External OpenAPI: %{http_code}\n" "http://$public_ip/api/openapi.json" 2>/dev/null || echo "External OpenAPI: Network error"
    curl -s -o /dev/null -w "External Swagger UI: %{http_code}\n" "http://$public_ip/api/docs" 2>/dev/null || echo "External Swagger UI: Network error"
else
    echo "⚠ Could not determine public IP"
    public_ip="YOUR_SERVER_IP"
fi

# Step 8: Display results and instructions
echo ""
echo "=========================================="
echo "OpenAPI Version Fix Complete! 🎉"
echo "=========================================="
echo ""
echo "Fix Applied:"
echo "✓ Added openapi_version='3.1.0' to FastAPI configuration"
echo "✓ This ensures Swagger UI can properly parse the API definition"
echo ""
echo "Access URLs:"
echo "📚 Direct Swagger UI: http://localhost:8000/docs"
echo "🔌 Direct OpenAPI Schema: http://localhost:8000/openapi.json"
echo "🔧 Health Check: http://localhost:8000/health"
echo ""
echo "If nginx is configured:"
echo "📚 Proxied Swagger UI: http://localhost/api/docs"
echo "🔌 Proxied OpenAPI Schema: http://localhost/api/openapi.json"
echo ""
echo "External URLs (replace with your server IP):"
echo "📚 External Swagger UI: http://$public_ip/api/docs"
echo "🔌 External OpenAPI Schema: http://$public_ip/api/openapi.json"
echo ""
echo "The Swagger UI should now load without the version field error!"
echo ""
echo "Troubleshooting:"
echo "- If you still see issues, clear browser cache and hard refresh"
echo "- Check container logs: docker-compose logs rnr_api_server"
echo "- Verify all containers are running: docker-compose ps"
echo "- Test the raw OpenAPI JSON: curl -s http://localhost:8000/openapi.json | head -20"
echo ""
echo "Container status:"
docker-compose ps
echo "=========================================="
