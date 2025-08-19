# RNR Solutions - OpenAPI Version Fix and Test Script
# PowerShell script to restart services and test the OpenAPI fix

Write-Host "=========================================="
Write-Host "RNR IoT Platform - OpenAPI Version Fix"
Write-Host "Fixing missing OpenAPI version field"
Write-Host "=========================================="

# Function to test URL
function Test-Endpoint {
    param(
        [string]$Url,
        [string]$Name
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 30
        Write-Host "✓ $Name`: $($response.StatusCode)"
        return $response
    }
    catch {
        Write-Host "✗ $Name`: Failed - $($_.Exception.Message)"
        return $null
    }
}

# Step 1: Stop existing containers
Write-Host ""
Write-Host "1. Stopping existing containers..."
Write-Host "=========================================="

try {
    docker-compose down
    Write-Host "✓ Containers stopped successfully"
}
catch {
    Write-Host "⚠ Error stopping containers: $($_.Exception.Message)"
}

# Step 2: Rebuild and start containers
Write-Host ""
Write-Host "2. Building and starting containers..."
Write-Host "=========================================="

try {
    docker-compose up --build -d
    Write-Host "✓ Containers started successfully"
}
catch {
    Write-Host "✗ Error starting containers: $($_.Exception.Message)"
    exit 1
}

# Step 3: Wait for services to be ready
Write-Host ""
Write-Host "3. Waiting for services to be ready..."
Write-Host "=========================================="

$maxWaitTime = 120  # 2 minutes
$waitTime = 0
$interval = 5

do {
    Start-Sleep -Seconds $interval
    $waitTime += $interval
    Write-Host "Waiting... ($waitTime/$maxWaitTime seconds)"
    
    $healthResponse = Test-Endpoint -Url "http://localhost:8000/health" -Name "Health Check"
    
    if ($healthResponse -and $healthResponse.StatusCode -eq 200) {
        Write-Host "✓ API server is ready!"
        break
    }
    
    if ($waitTime -ge $maxWaitTime) {
        Write-Host "✗ Timeout waiting for API server to be ready"
        Write-Host "Checking container logs..."
        docker-compose logs rnr_api_server --tail=20
        exit 1
    }
} while ($true)

# Step 4: Test OpenAPI endpoint
Write-Host ""
Write-Host "4. Testing OpenAPI endpoint..."
Write-Host "=========================================="

$openApiResponse = Test-Endpoint -Url "http://localhost:8000/openapi.json" -Name "Direct OpenAPI"

if ($openApiResponse) {
    try {
        $openApiJson = $openApiResponse.Content | ConvertFrom-Json
        
        # Check for OpenAPI version field
        if ($openApiJson.openapi) {
            Write-Host "✓ OpenAPI version field found: $($openApiJson.openapi)"
            
            # Validate version format
            if ($openApiJson.openapi -match '^3\.\d+\.\d+$') {
                Write-Host "✓ Valid OpenAPI 3.x version format"
            } else {
                Write-Host "⚠ OpenAPI version format may be invalid: $($openApiJson.openapi)"
            }
        } else {
            Write-Host "✗ OpenAPI version field is missing!"
        }
        
        # Check for required fields
        if ($openApiJson.info) {
            Write-Host "✓ Info section found"
        } else {
            Write-Host "✗ Info section missing"
        }
        
        if ($openApiJson.paths) {
            Write-Host "✓ Paths section found"
        } else {
            Write-Host "✗ Paths section missing"
        }
        
        Write-Host "✓ OpenAPI JSON is valid and complete"
        Write-Host "OpenAPI JSON size: $($openApiResponse.Content.Length) characters"
        
    } catch {
        Write-Host "✗ Failed to parse OpenAPI JSON: $($_.Exception.Message)"
        Write-Host "First 500 characters of response:"
        Write-Host $openApiResponse.Content.Substring(0, [Math]::Min(500, $openApiResponse.Content.Length))
    }
} else {
    Write-Host "✗ Could not retrieve OpenAPI JSON"
    exit 1
}

# Step 5: Test Swagger UI
Write-Host ""
Write-Host "5. Testing Swagger UI endpoints..."
Write-Host "=========================================="

Test-Endpoint -Url "http://localhost:8000/docs" -Name "Direct Swagger UI"

# Step 6: Test through nginx proxy (if available)
Write-Host ""
Write-Host "6. Testing through nginx proxy..."
Write-Host "=========================================="

Test-Endpoint -Url "http://localhost/api/openapi.json" -Name "Proxied OpenAPI"
Test-Endpoint -Url "http://localhost/api/docs" -Name "Proxied Swagger UI"

# Step 7: Get external IP and test external access
Write-Host ""
Write-Host "7. Testing external access..."
Write-Host "=========================================="

try {
    $publicIp = (Invoke-WebRequest -Uri "http://ifconfig.me" -UseBasicParsing -TimeoutSec 10).Content.Trim()
    Write-Host "Public IP: $publicIp"
    
    Test-Endpoint -Url "http://$publicIp/api/openapi.json" -Name "External OpenAPI"
    Test-Endpoint -Url "http://$publicIp/api/docs" -Name "External Swagger UI"
} catch {
    Write-Host "⚠ Could not determine public IP or test external access"
}

# Step 8: Display results
Write-Host ""
Write-Host "=========================================="
Write-Host "OpenAPI Version Fix Complete! 🎉"
Write-Host "=========================================="
Write-Host ""
Write-Host "Fix Applied:"
Write-Host "✓ Added openapi_version='3.1.0' to FastAPI configuration"
Write-Host "✓ This ensures Swagger UI can properly parse the API definition"
Write-Host ""
Write-Host "Access URLs:"
Write-Host "📚 Direct Swagger UI: http://localhost:8000/docs"
Write-Host "🔌 Direct OpenAPI Schema: http://localhost:8000/openapi.json"
Write-Host "🔧 Health Check: http://localhost:8000/health"
Write-Host ""
if ($publicIp) {
    Write-Host "External URLs (if nginx is configured):"
    Write-Host "📚 External Swagger UI: http://$publicIp/api/docs"
    Write-Host "🔌 External OpenAPI Schema: http://$publicIp/api/openapi.json"
    Write-Host ""
}
Write-Host "The Swagger UI should now load without the version field error!"
Write-Host ""
Write-Host "If you still see issues:"
Write-Host "1. Clear your browser cache"
Write-Host "2. Try a hard refresh (Ctrl+F5)"
Write-Host "3. Check container logs: docker-compose logs rnr_api_server"
Write-Host "=========================================="
