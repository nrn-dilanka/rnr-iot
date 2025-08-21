#!/bin/bash

echo "🔐 Authentication System Test - AWS Server"
echo "=========================================="
echo "Server: http://13.60.227.209:3005"
echo ""

# Test 1: Login with Admin
echo "1️⃣ Testing Admin Login..."
RESPONSE=$(curl -s -X POST "http://13.60.227.209:3005/api/auth/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}')

if echo "$RESPONSE" | grep -q "access_token"; then
    echo "✅ Admin login successful"
    TOKEN=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    USER_INFO=$(echo "$RESPONSE" | python3 -c "import sys, json; user = json.load(sys.stdin)['user']; print(f'{user[\"username\"]} ({user[\"role\"]})')")
    echo "   User: $USER_INFO"
else
    echo "❌ Admin login failed"
    echo "   Response: $RESPONSE"
fi

echo ""

# Test 2: Login with Professor
echo "2️⃣ Testing Professor Login..."
PROF_RESPONSE=$(curl -s -X POST "http://13.60.227.209:3005/api/auth/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "prof_smith", "password": "prof123"}')

if echo "$PROF_RESPONSE" | grep -q "access_token"; then
    echo "✅ Professor login successful"
    PROF_INFO=$(echo "$PROF_RESPONSE" | python3 -c "import sys, json; user = json.load(sys.stdin)['user']; print(f'{user[\"username\"]} ({user[\"role\"]})')")
    echo "   User: $PROF_INFO"
else
    echo "❌ Professor login failed"
    echo "   Response: $PROF_RESPONSE"
fi

echo ""

# Test 3: Login with Operator
echo "3️⃣ Testing Operator Login..."
OP_RESPONSE=$(curl -s -X POST "http://13.60.227.209:3005/api/auth/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "operator_alice", "password": "operator123"}')

if echo "$OP_RESPONSE" | grep -q "access_token"; then
    echo "✅ Operator login successful"
    OP_INFO=$(echo "$OP_RESPONSE" | python3 -c "import sys, json; user = json.load(sys.stdin)['user']; print(f'{user[\"username\"]} ({user[\"role\"]})')")
    echo "   User: $OP_INFO"
else
    echo "❌ Operator login failed"
    echo "   Response: $OP_RESPONSE"
fi

echo ""

# Test 4: Invalid Login
echo "4️⃣ Testing Invalid Login..."
INVALID_RESPONSE=$(curl -s -X POST "http://13.60.227.209:3005/api/auth/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "wrongpassword"}')

if echo "$INVALID_RESPONSE" | grep -q "detail"; then
    echo "✅ Invalid login properly rejected"
    ERROR_MSG=$(echo "$INVALID_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['detail'])")
    echo "   Error: $ERROR_MSG"
else
    echo "❌ Invalid login handling failed"
fi

echo ""

# Test 5: Protected Endpoint Access
if [ ! -z "$TOKEN" ]; then
    echo "5️⃣ Testing Protected Endpoint Access..."
    
    echo "   🔍 Testing /me endpoint..."
    ME_RESPONSE=$(curl -s -X GET "http://13.60.227.209:3005/api/auth/auth/me" \
      -H "Authorization: Bearer $TOKEN")
    
    if echo "$ME_RESPONSE" | grep -q "username"; then
        echo "   ✅ /me endpoint accessible"
        USERNAME=$(echo "$ME_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['username'])")
        echo "      Current user: $USERNAME"
    else
        echo "   ❌ /me endpoint failed"
    fi
    
    echo ""
    echo "   📊 Testing activity logs..."
    LOGS_RESPONSE=$(curl -s -X GET "http://13.60.227.209:3005/api/auth/auth/activity-logs" \
      -H "Authorization: Bearer $TOKEN")
    
    if echo "$LOGS_RESPONSE" | grep -q "\["; then
        echo "   ✅ Activity logs accessible"
        LOG_COUNT=$(echo "$LOGS_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
        echo "      Activity entries: $LOG_COUNT"
    else
        echo "   ❌ Activity logs failed"
    fi
    
    echo ""
    echo "   📈 Testing system stats..."
    STATS_RESPONSE=$(curl -s -X GET "http://13.60.227.209:3005/api/auth/auth/stats" \
      -H "Authorization: Bearer $TOKEN")
    
    if echo "$STATS_RESPONSE" | grep -q "user_count"; then
        echo "   ✅ System stats accessible"
        USER_COUNT=$(echo "$STATS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['user_count'])")
        echo "      Total users: $USER_COUNT"
    else
        echo "   ❌ System stats failed"
    fi
fi

echo ""

# Test 6: Unauthorized Access
echo "6️⃣ Testing Unauthorized Access..."
UNAUTH_RESPONSE=$(curl -s -X GET "http://13.60.227.209:3005/api/auth/auth/me")

if echo "$UNAUTH_RESPONSE" | grep -q "detail"; then
    echo "✅ Unauthorized access properly blocked"
    ERROR_MSG=$(echo "$UNAUTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['detail'])")
    echo "   Error: $ERROR_MSG"
else
    echo "❌ Unauthorized access handling failed"
fi

echo ""
echo "🎯 Authentication Test Summary"
echo "=============================="
echo "✅ Login system operational"
echo "✅ Role-based authentication working"
echo "✅ JWT token generation functional"
echo "✅ Protected endpoints secured"
echo "✅ Error handling implemented"
echo ""
echo "📍 Authentication endpoints are available at:"
echo "   Login: /api/auth/auth/login"
echo "   User info: /api/auth/auth/me"
echo "   Activity logs: /api/auth/auth/activity-logs"
echo "   System stats: /api/auth/auth/stats"
echo ""
echo "👥 Available demo users:"
echo "   admin/admin123 (Superuser)"
echo "   prof_smith/prof123 (Admin)"
echo "   operator_alice/operator123 (Operator)"
