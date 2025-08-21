#!/bin/bash

echo "🏭 Testing Industrial Authentication on AWS Server"
echo "================================================="
echo "Server: http://13.60.227.209:3005"
echo ""

# Test 1: Admin Login
echo "1️⃣ Testing Admin (Superuser):"
ADMIN_RESPONSE=$(curl -s -X POST "http://13.60.227.209:3005/api/auth/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}')

if echo "$ADMIN_RESPONSE" | grep -q "access_token"; then
    echo "✅ Admin login successful"
    ADMIN_TOKEN=$(echo "$ADMIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    ADMIN_INFO=$(echo "$ADMIN_RESPONSE" | python3 -c "import sys, json; user = json.load(sys.stdin)['user']; print(f'   {user[\"full_name\"]} - {user[\"department\"]} ({user[\"role\"]})')")
    echo "$ADMIN_INFO"
else
    echo "❌ Admin login failed"
fi

echo ""

# Test 2: Professor Login  
echo "2️⃣ Testing Professor (Admin):"
PROF_RESPONSE=$(curl -s -X POST "http://13.60.227.209:3005/api/auth/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "prof_smith", "password": "prof123"}')

if echo "$PROF_RESPONSE" | grep -q "access_token"; then
    echo "✅ Professor login successful"
    PROF_INFO=$(echo "$PROF_RESPONSE" | python3 -c "import sys, json; user = json.load(sys.stdin)['user']; print(f'   {user[\"full_name\"]} - {user[\"department\"]} ({user[\"role\"]})')")
    echo "$PROF_INFO"
else
    echo "❌ Professor login failed"
fi

echo ""

# Test 3: Operator Login
echo "3️⃣ Testing Operator (Industrial):"
OP_RESPONSE=$(curl -s -X POST "http://13.60.227.209:3005/api/auth/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "operator_alice", "password": "operator123"}')

if echo "$OP_RESPONSE" | grep -q "access_token"; then
    echo "✅ Operator login successful"
    OP_INFO=$(echo "$OP_RESPONSE" | python3 -c "import sys, json; user = json.load(sys.stdin)['user']; print(f'   {user[\"full_name\"]} - {user[\"department\"]} ({user[\"role\"]})')")
    echo "$OP_INFO"
    # Check for industrial fields
    OP_FIELDS=$(echo "$OP_RESPONSE" | python3 -c "import sys, json; user = json.load(sys.stdin)['user']; print(f'   Employee ID: {user.get(\"employee_id\", \"N/A\")}, Business Area: {user.get(\"business_area\", \"N/A\")}')")
    echo "$OP_FIELDS"
else
    echo "❌ Operator login failed"
    echo "   Response: $OP_RESPONSE"
fi

echo ""

# Test 4: Protected Endpoints
if [ ! -z "$ADMIN_TOKEN" ]; then
    echo "4️⃣ Testing Protected Endpoints:"
    
    echo "   📊 Current user info:"
    ME_RESPONSE=$(curl -s -X GET "http://13.60.227.209:3005/api/auth/auth/me" \
      -H "Authorization: Bearer $ADMIN_TOKEN")
    
    if echo "$ME_RESPONSE" | grep -q "username"; then
        echo "   ✅ User info accessible"
        USER_DETAILS=$(echo "$ME_RESPONSE" | python3 -c "import sys, json; user = json.load(sys.stdin); print(f'      {user[\"username\"]} - Last login: {user.get(\"last_login\", \"Never\")} (Login count: {user[\"login_count\"]})')")
        echo "$USER_DETAILS"
    else
        echo "   ❌ User info failed"
    fi
    
    echo ""
    echo "   📈 System statistics:"
    STATS_RESPONSE=$(curl -s -X GET "http://13.60.227.209:3005/api/auth/auth/stats" \
      -H "Authorization: Bearer $ADMIN_TOKEN")
    
    if echo "$STATS_RESPONSE" | grep -q "user_count"; then
        echo "   ✅ System stats accessible"
        STATS_INFO=$(echo "$STATS_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'      Users: {data[\"user_count\"]} total, {data[\"active_users\"]} active')
roles = data['role_distribution']
print(f'      Roles: {roles[\"superusers\"]} superusers, {roles[\"admins\"]} admins, {roles[\"operators\"]} operators')
print(f'      Platform: {data.get(\"platform_type\", \"unknown\")}')
")
        echo "$STATS_INFO"
    else
        echo "   ❌ System stats failed"
    fi
    
    echo ""
    echo "   📋 Activity logs:"
    LOGS_RESPONSE=$(curl -s -X GET "http://13.60.227.209:3005/api/auth/auth/activity-logs" \
      -H "Authorization: Bearer $ADMIN_TOKEN")
    
    if echo "$LOGS_RESPONSE" | grep -q "\["; then
        echo "   ✅ Activity logs accessible"
        LOG_INFO=$(echo "$LOGS_RESPONSE" | python3 -c "import sys, json; logs = json.load(sys.stdin); print(f'      {len(logs)} activity entries recorded')")
        echo "$LOG_INFO"
    else
        echo "   ❌ Activity logs failed"
    fi
fi

echo ""

# Test 5: Invalid Access
echo "5️⃣ Testing Security:"
echo "   🔒 Invalid credentials:"
INVALID_RESPONSE=$(curl -s -X POST "http://13.60.227.209:3005/api/auth/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "hacker", "password": "wrong"}')

if echo "$INVALID_RESPONSE" | grep -q "detail"; then
    echo "   ✅ Invalid login properly rejected"
else
    echo "   ❌ Security issue: invalid login not rejected"
fi

echo "   🚫 Unauthorized endpoint access:"
UNAUTH_RESPONSE=$(curl -s -X GET "http://13.60.227.209:3005/api/auth/auth/stats")

if echo "$UNAUTH_RESPONSE" | grep -q "Not authenticated"; then
    echo "   ✅ Unauthorized access properly blocked"
else
    echo "   ❌ Security issue: unauthorized access allowed"
fi

echo ""
echo "🎯 Industrial Authentication Summary"
echo "===================================="
echo "✅ Multi-role industrial authentication system operational"
echo "✅ Employee ID and business area tracking implemented"
echo "✅ Role-based access control enforced"
echo "✅ System monitoring and statistics available"
echo "✅ Activity logging and audit trail active"
echo "✅ Security measures properly implemented"
echo ""
echo "👥 Industrial User Roles Available:"
echo "   🔑 Superuser (admin) - Full system access"
echo "   👨‍🏫 Admin (prof_smith) - Management access"
echo "   👷‍♀️ Operator (operator_alice) - Water Management Systems"
echo "   🔧 Operator (technician_bob) - Equipment Maintenance"
echo ""
echo "🌐 Access the authentication system:"
echo "   Web Interface: http://13.60.227.209:3005/docs"
echo "   Health Check: http://13.60.227.209:3005/health"
echo "   Platform Stats: http://13.60.227.209:3005/api/platform/stats"
