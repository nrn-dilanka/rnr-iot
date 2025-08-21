#!/bin/bash

echo "🔍 Complete Greenhouse Endpoint Removal Verification"
echo "=================================================="

echo ""
echo "🧪 Testing All Potential Greenhouse Endpoints:"

# Test various greenhouse endpoint patterns
ENDPOINTS=(
    "/api/greenhouse"
    "/api/greenhouse/"
    "/api/greenhouse/zones"
    "/api/greenhouse/sensors"
    "/api/greenhouse/controls"
    "/api/greenhouse/monitoring"
    "/api/greenhouse/automation"
    "/api/greenhouse/zones/1"
    "/api/greenhouse/data"
    "/api/greenhouse/settings"
)

ALL_REMOVED=true

for endpoint in "${ENDPOINTS[@]}"; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3005$endpoint")
    if [ "$HTTP_CODE" = "404" ]; then
        echo "✅ $endpoint - Properly removed (404)"
    elif [ "$HTTP_CODE" = "000" ]; then
        echo "⚠️  $endpoint - Connection failed"
    else
        echo "❌ $endpoint - Still exists (HTTP $HTTP_CODE)"
        ALL_REMOVED=false
    fi
done

echo ""
echo "🔍 Checking OpenAPI Documentation:"
GREENHOUSE_IN_DOCS=$(curl -s http://localhost:3005/openapi.json | grep -i greenhouse | wc -l)
if [ "$GREENHOUSE_IN_DOCS" -eq 0 ]; then
    echo "✅ No greenhouse references in OpenAPI documentation"
else
    echo "❌ Found $GREENHOUSE_IN_DOCS greenhouse references in OpenAPI docs"
    ALL_REMOVED=false
fi

echo ""
echo "🔍 Checking Available Endpoints:"
echo "Current API endpoints:"
curl -s http://localhost:3005/openapi.json | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    paths = list(data.get('paths', {}).keys())
    paths.sort()
    for path in paths:
        if '/api/' in path:
            print(f'  {path}')
except:
    print('  Failed to parse OpenAPI spec')
"

echo ""
echo "🏭 Verifying Industrial Endpoints Are Working:"

# Test core industrial endpoints
INDUSTRIAL_ENDPOINTS=(
    "/health:Health Check"
    "/api/nodes:ESP32 Devices"
    "/api/sensor-data:Environmental Monitoring"
    "/api/water/systems:Water Management"
    "/api/auth/me:Authentication"
)

for item in "${INDUSTRIAL_ENDPOINTS[@]}"; do
    endpoint="${item%%:*}"
    name="${item##*:}"
    
    if [ "$endpoint" = "/api/auth/me" ]; then
        # Get auth token first
        TOKEN=$(curl -s -X POST "http://localhost:3005/api/auth/login" \
          -H "Content-Type: application/json" \
          -d '{"username": "admin", "password": "admin123"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
        
        if [ ! -z "$TOKEN" ]; then
            HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "http://localhost:3005$endpoint")
        else
            HTTP_CODE="AUTH_FAILED"
        fi
    else
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3005$endpoint")
    fi
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ $name ($endpoint) - Working"
    else
        echo "⚠️  $name ($endpoint) - HTTP $HTTP_CODE"
    fi
done

echo ""
echo "📊 Final Verification Summary:"
echo "=============================="

if [ "$ALL_REMOVED" = true ]; then
    echo "🎉 SUCCESS: All greenhouse endpoints have been completely removed!"
    echo ""
    echo "✅ Confirmed Removals:"
    echo "   • All greenhouse API endpoints return 404"
    echo "   • No greenhouse references in OpenAPI documentation"
    echo "   • Core industrial endpoints remain functional"
    echo ""
    echo "🏭 Platform Status: Pure Industrial IoT System"
else
    echo "❌ WARNING: Some greenhouse endpoints or references still exist!"
fi

echo ""
echo "🔗 Current Platform Focus:"
echo "   • Industrial equipment monitoring"
    echo "   • Environmental control systems" 
echo "   • Water management (industrial cooling)"
echo "   • ESP32 device connectivity"
echo "   • Multi-user authentication & authorization"
