#!/bin/bash

echo "🔍 AWS Endpoint Diagnostics"
echo "=========================="

echo "1. Testing remote endpoint connectivity:"
curl -v "http://13.60.227.209:3005/api/nodes" 2>&1 | head -20

echo -e "\n2. Testing remote health endpoint:"
curl -s "http://13.60.227.209:3005/health" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f'Status: {data.get(\"status\", \"N/A\")}')
    print(f'Database: {data.get(\"database\", \"N/A\")}')
    print(f'Error: {data.get(\"error\", \"None\")}')
except Exception as e:
    print(f'Parse error: {e}')
"

echo -e "\n3. Testing remote database test endpoint:"
curl -s "http://13.60.227.209:3005/api/database/test" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f'Database Status: {data.get(\"database_status\", \"N/A\")}')
    print(f'Error: {data.get(\"error\", \"None\")}')
    print(f'Error Type: {data.get(\"error_type\", \"None\")}')
except Exception as e:
    print(f'Parse error: {e}')
"

echo -e "\n4. Checking if server is responding at all:"
timeout 5 curl -s "http://13.60.227.209:3005/" > /dev/null && echo "✅ Server is responding" || echo "❌ Server not responding"

echo -e "\n5. Testing different endpoints:"
echo "- /health:"
timeout 3 curl -s "http://13.60.227.209:3005/health" | grep -o '"status":"[^"]*"' || echo "No response"

echo "- /api/nodes:"
timeout 3 curl -s "http://13.60.227.209:3005/api/nodes" | head -100 || echo "No response"

echo -e "\n🎯 Diagnostic Complete!"
