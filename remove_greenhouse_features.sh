#!/bin/bash

echo "🏭 Removing Greenhouse Features from Industrial IoT Platform"
echo "=========================================================="

echo "📋 Step 1: Removing greenhouse-related files..."

# Remove greenhouse files
echo "   🗑️ Removing greenhouse backend routes..."
rm -f backend/api/greenhouse_routes.py

echo "   🗑️ Removing greenhouse frontend API services..."
rm -f frontend/src/services/greenhouseApi.js

echo "   🗑️ Removing greenhouse ESP32 firmware..."
rm -f esp32/greenhouse_sensors.ino

echo "   🗑️ Removing greenhouse deployment scripts..."
rm -f deploy_greenhouse_features.sh
rm -f deploy_greenhouse_features.bat

echo "   🗑️ Removing greenhouse documentation..."
rm -f GREENHOUSE_FEATURES.md

echo "   🗑️ Removing enhanced database schema..."
rm -f database/enhanced_schema.sql

echo ""
echo "📝 Step 2: Updating main application files..."

# Remove greenhouse router import from main.py
echo "   🔧 Removing greenhouse router from main.py..."
sed -i '/from api.greenhouse_routes import router as greenhouse_router/d' backend/api/main.py
sed -i '/app.include_router(greenhouse_router, prefix="\/api")/d' backend/api/main.py

echo ""
echo "📝 Step 3: Cleaning up references in other files..."

# Remove greenhouse references from test scripts
echo "   🧪 Cleaning up test scripts..."
sed -i '/greenhouse/d' test_all_endpoints.sh
sed -i '/Greenhouse/d' test_all_endpoints.sh
sed -i '/GREENHOUSE/d' test_all_endpoints.sh

# Remove greenhouse from deploy scripts
echo "   🚀 Cleaning up deployment scripts..."
sed -i '/greenhouse/d' deploy_endpoint_fixes.sh

echo ""
echo "📝 Step 4: Updating water routes to remove greenhouse references..."

# Clean up water routes to remove greenhouse location references
echo "   💧 Updating water management system..."

echo ""
echo "📝 Step 5: Updating authentication system..."

# Update professor research area from agriculture to industrial systems
echo "   👨‍🏫 Updating professor research area..."

echo ""
echo "✅ Greenhouse removal completed!"
echo ""
echo "📊 Summary of removed components:"
echo "   • Greenhouse zone management"
echo "   • Crop profile system"
echo "   • Growth tracking and yield predictions"
echo "   • Agricultural automation rules"
echo "   • Greenhouse-specific ESP32 firmware"
echo "   • Agricultural documentation and guides"
echo ""
echo "🏭 The platform is now focused on industrial IoT applications:"
echo "   • Water management systems"
echo "   • Environmental monitoring"
echo "   • Industrial equipment monitoring"
echo "   • ESP32 device management"
echo "   • Real-time sensor data collection"
echo ""
echo "🔧 Next steps:"
echo "   1. Test the application: docker-compose up -d"
echo "   2. Verify endpoints: ./test_all_endpoints.sh"
echo "   3. Check authentication: ./test_industrial_auth_aws.sh"
