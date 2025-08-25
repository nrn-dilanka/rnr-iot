#!/bin/bash

echo "🐰 RabbitMQ Queue Management Dashboard"
echo "====================================="

echo ""
echo "🔗 QUICK ACCESS:"
echo "URL: http://localhost:15672"
echo "Username: rnr_iot_user"
echo "Password: rnr_iot_2025!"
echo "VHost: rnr_iot_vhost"

echo ""
echo "📊 CURRENT QUEUE STATUS:"
# Only show queue name and active consumers to avoid displaying queued message counts
docker exec rnr_iot_rabbitmq rabbitmqctl list_queues name consumers -p rnr_iot_vhost

echo ""
echo "🔄 EXCHANGES:"
docker exec rnr_iot_rabbitmq rabbitmqctl list_exchanges name type -p rnr_iot_vhost

echo ""
echo "🔗 BINDINGS:"
docker exec rnr_iot_rabbitmq rabbitmqctl list_bindings source_name destination_name routing_key -p rnr_iot_vhost

echo ""
echo "🖥️ MANAGEMENT COMMANDS:"
echo ""
echo "1. View Queue Details (no queued counts):"
echo "   docker exec rnr_iot_rabbitmq rabbitmqctl list_queues name consumers -p rnr_iot_vhost"
echo ""
echo "2. Purge Queue (CAREFUL!):"
echo "   docker exec rnr_iot_rabbitmq rabbitmqctl purge_queue device_data -p rnr_iot_vhost"
echo ""
echo "3. Create New Queue:"
echo "   docker exec rnr_iot_rabbitmq rabbitmqctl declare queue name=my_queue durable=true -p rnr_iot_vhost"
echo ""
echo "4. Delete Queue:"
echo "   docker exec rnr_iot_rabbitmq rabbitmqctl delete_queue my_queue -p rnr_iot_vhost"
echo ""
echo "5. Monitor Real-time:"
echo "   watch -n 2 'docker exec rnr_iot_rabbitmq rabbitmqctl list_queues -p rnr_iot_vhost'"

echo ""
echo "🌐 WEB UI FEATURES:"
echo "• Queues Tab - View/manage all queues"
echo "• Exchanges Tab - Message routing configuration"  
echo "• Connections Tab - Active connections monitoring"
echo "• Admin Tab - User and vhost management"

echo ""
echo "⚠️  SAFETY TIPS:"
echo "• Always backup before making changes"
echo "• Test operations in development first"
echo "• Monitor memory usage regularly"
echo "• Use web UI for visual management"
