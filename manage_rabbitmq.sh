#!/bin/bash
# RabbitMQ Queue Management Helper Script

echo "🐰 RabbitMQ Queue Management for RNR IoT Platform"
echo "=================================================="

# Check if RabbitMQ is running
if ! docker ps | grep -q rnr_iot_rabbitmq; then
    echo "❌ RabbitMQ container not running"
    echo "   Starting RabbitMQ..."
    docker-compose up -d rnr_rabbitmq
    sleep 10
fi

echo "✅ RabbitMQ is running"
echo ""

# Display menu
echo "Select an action:"
echo "1) 📋 List all queues"
echo "2) 🔄 List all exchanges" 
echo "3) 📊 Show queue details"
echo "4) 🚀 Setup IoT queues"
echo "5) 🧹 Purge a queue"
echo "6) 📈 Live monitoring dashboard"
echo "7) 🌐 Open RabbitMQ Management UI"
echo "8) 🔌 Start ESP32 simulator"
echo "9) 🛑 Stop ESP32 simulator"
echo "0) 🚪 Exit"
echo ""

read -p "Enter your choice (0-9): " choice

case $choice in
    1)
        echo "📋 Listing all queues..."
        python3 rabbitmq_queue_manager.py --action list-queues
        ;;
    2)
        echo "🔄 Listing all exchanges..."
        python3 rabbitmq_queue_manager.py --action list-exchanges
        ;;
    3)
        read -p "Enter queue name: " queue_name
        echo "📊 Getting details for queue '$queue_name'..."
        python3 rabbitmq_queue_manager.py --action queue-info --name "$queue_name"
        ;;
    4)
        echo "🚀 Setting up IoT platform queues..."
        python3 rabbitmq_queue_manager.py --action setup-iot
        ;;
    5)
        read -p "Enter queue name to purge: " queue_name
        echo "🧹 Purging queue '$queue_name'..."
        python3 rabbitmq_queue_manager.py --action purge-queue --name "$queue_name"
        ;;
    6)
        echo "📈 Starting live monitoring dashboard..."
        echo "   Press Ctrl+C to stop monitoring"
        python3 rabbitmq_monitor.py --monitor
        ;;
    7)
        echo "🌐 Opening RabbitMQ Management UI..."
        echo "   URL: http://16.171.30.3:15672"
        echo "   Username: rnr_iot_user"
        echo "   Password: rnr_iot_2025!"
        
        # Try to open in browser
        if command -v xdg-open >/dev/null 2>&1; then
            xdg-open "http://16.171.30.3:15672"
        elif command -v firefox >/dev/null 2>&1; then
            firefox "http://16.171.30.3:15672" &
        elif command -v chromium-browser >/dev/null 2>&1; then
            chromium-browser "http://16.171.30.3:15672" &
        else
            echo "   Please open the URL manually in your browser"
        fi
        ;;
    8)
        echo "🔌 Starting ESP32 simulator..."
        echo "   This will simulate 4 ESP32 devices sending sensor data"
        python3 test_esp32_realtime.py &
        ESP32_PID=$!
        echo "   ESP32 simulator started with PID: $ESP32_PID"
        echo "   To stop, run: kill $ESP32_PID"
        echo "   Or use option 9 in this menu"
        ;;
    9)
        echo "🛑 Stopping ESP32 simulator..."
        pkill -f test_esp32_realtime.py
        echo "   ESP32 simulator stopped"
        ;;
    0)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice. Please select 0-9."
        ;;
esac

echo ""
echo "Press Enter to continue..."
read
