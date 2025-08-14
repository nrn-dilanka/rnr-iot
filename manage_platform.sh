#!/bin/bash

# IoT Platform Setup and Run Script
echo "🚀 Starting IoT Platform Setup..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js and try again."
    exit 1
fi

# Check if Python is installed
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ Python is not installed. Please install Python and try again."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Function to run setup steps
setup_platform() {
    echo "📦 Setting up backend dependencies..."
    cd backend
    
    # Install Python dependencies
    if command -v python3 &> /dev/null; then
        python3 -m pip install -r requirements.txt
    else
        python -m pip install -r requirements.txt
    fi
    
    cd ..
    
    echo "📦 Setting up frontend dependencies..."
    cd frontend
    npm install
    cd ..
    
    echo "🐳 Starting Docker services..."
    docker-compose up -d postgres rabbitmq
    
    # Wait for services to be ready
    echo "⏳ Waiting for services to start..."
    sleep 10
    
    echo "🗄️ Setting up database..."
    # You may need to run database migrations here
    
    echo "✅ Setup complete!"
}

# Function to start the platform
start_platform() {
    echo "🚀 Starting IoT Platform..."
    
    # Start backend services
    echo "🔧 Starting backend services..."
    docker-compose up -d
    
    # Start frontend development server
    echo "🌐 Starting frontend development server..."
    cd frontend
    npm start &
    FRONTEND_PID=$!
    
    cd ..
    
    echo "✅ Platform started successfully!"
    echo ""
    echo "📱 Frontend: http://localhost:3000"
    echo "🔧 Backend API: http://localhost:8000"
    echo "📊 RabbitMQ Management: http://localhost:15672 (guest/guest)"
    echo ""
    echo "Press Ctrl+C to stop the platform"
    
    # Wait for interrupt
    trap "echo '🛑 Stopping platform...'; kill $FRONTEND_PID; docker-compose down; exit" INT
    wait
}

# Function to show status
show_status() {
    echo "📊 IoT Platform Status:"
    echo ""
    
    # Check Docker services
    echo "🐳 Docker Services:"
    docker-compose ps
    echo ""
    
    # Check if frontend is running
    if pgrep -f "npm start" > /dev/null; then
        echo "🌐 Frontend: ✅ Running"
    else
        echo "🌐 Frontend: ❌ Not running"
    fi
    
    # Check backend API
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "🔧 Backend API: ✅ Running"
    else
        echo "🔧 Backend API: ❌ Not running"
    fi
    
    # Check database
    if docker-compose exec -T postgres pg_isready > /dev/null 2>&1; then
        echo "🗄️ Database: ✅ Running"
    else
        echo "🗄️ Database: ❌ Not running"
    fi
    
    # Check RabbitMQ
    if curl -s http://localhost:15672 > /dev/null 2>&1; then
        echo "📡 RabbitMQ: ✅ Running"
    else
        echo "📡 RabbitMQ: ❌ Not running"
    fi
}

# Function to stop the platform
stop_platform() {
    echo "🛑 Stopping IoT Platform..."
    
    # Stop frontend
    pkill -f "npm start" 2>/dev/null || true
    
    # Stop Docker services
    docker-compose down
    
    echo "✅ Platform stopped"
}

# Function to show logs
show_logs() {
    echo "📝 Showing platform logs..."
    docker-compose logs -f
}

# Function to clean up
cleanup_platform() {
    echo "🧹 Cleaning up IoT Platform..."
    
    # Stop all services
    stop_platform
    
    # Remove Docker volumes (optional)
    read -p "Do you want to remove all data (database, etc.)? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        echo "✅ All data removed"
    fi
    
    # Clean up frontend
    cd frontend
    rm -rf node_modules package-lock.json 2>/dev/null || true
    cd ..
    
    echo "✅ Cleanup complete"
}

# Main menu
case "${1:-}" in
    "setup")
        setup_platform
        ;;
    "start")
        start_platform
        ;;
    "stop")
        stop_platform
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "cleanup")
        cleanup_platform
        ;;
    *)
        echo "🏭 IoT Platform Management Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  setup     - Install dependencies and set up the platform"
        echo "  start     - Start the IoT platform"
        echo "  stop      - Stop the IoT platform"
        echo "  status    - Show platform status"
        echo "  logs      - Show platform logs"
        echo "  cleanup   - Clean up and remove all data"
        echo ""
        echo "Example:"
        echo "  $0 setup    # First time setup"
        echo "  $0 start    # Start the platform"
        echo ""
        ;;
esac
