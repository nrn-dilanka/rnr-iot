#!/bin/bash

# Enhanced Greenhouse Features Deployment Script
# This script helps deploy the new greenhouse monitoring and control features

set -e  # Exit on any error

echo "🌱 Enhanced Greenhouse Features Deployment Script"
echo "=================================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running from correct directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the IoT-Platform root directory"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_header "Checking Prerequisites"

if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

if ! command_exists psql; then
    print_warning "PostgreSQL client (psql) not found. Database migration will be skipped."
    SKIP_DB_MIGRATION=true
else
    SKIP_DB_MIGRATION=false
fi

print_status "Prerequisites check completed"

# Function to backup database
backup_database() {
    print_header "Creating Database Backup"
    
    if [ "$SKIP_DB_MIGRATION" = true ]; then
        print_warning "Skipping database backup (psql not available)"
        return
    fi
    
    BACKUP_DIR="backups"
    mkdir -p "$BACKUP_DIR"
    
    BACKUP_FILE="$BACKUP_DIR/iot_platform_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    # Get database connection details from docker-compose.yml or .env
    DB_HOST=${DB_HOST:-localhost}
    DB_PORT=${DB_PORT:-5432}
    DB_NAME=${DB_NAME:-iot_platform}
    DB_USER=${DB_USER:-iotuser}
    
    print_status "Creating backup: $BACKUP_FILE"
    
    if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE"; then
        print_status "Database backup created successfully"
    else
        print_warning "Database backup failed, but continuing with deployment"
    fi
}

# Function to apply database migrations
apply_database_migrations() {
    print_header "Applying Database Migrations"
    
    if [ "$SKIP_DB_MIGRATION" = true ]; then
        print_warning "Skipping database migration (psql not available)"
        print_warning "Please manually apply database/enhanced_schema.sql to your database"
        return
    fi
    
    if [ ! -f "database/enhanced_schema.sql" ]; then
        print_error "Enhanced schema file not found: database/enhanced_schema.sql"
        exit 1
    fi
    
    # Get database connection details
    DB_HOST=${DB_HOST:-localhost}
    DB_PORT=${DB_PORT:-5432}
    DB_NAME=${DB_NAME:-iot_platform}
    DB_USER=${DB_USER:-iotuser}
    
    print_status "Applying enhanced schema to database..."
    
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "database/enhanced_schema.sql"; then
        print_status "Database migrations applied successfully"
    else
        print_error "Database migration failed"
        exit 1
    fi
}

# Function to install frontend dependencies
install_frontend_dependencies() {
    print_header "Installing Frontend Dependencies"
    
    if [ ! -d "frontend" ]; then
        print_error "Frontend directory not found"
        exit 1
    fi
    
    cd frontend
    
    if [ -f "package.json" ]; then
        print_status "Installing npm dependencies..."
        
        if command_exists npm; then
            npm install
            print_status "Frontend dependencies installed"
        elif command_exists yarn; then
            yarn install
            print_status "Frontend dependencies installed with Yarn"
        else
            print_warning "Neither npm nor yarn found. Please install frontend dependencies manually."
        fi
    else
        print_warning "package.json not found in frontend directory"
    fi
    
    cd ..
}

# Function to install backend dependencies
install_backend_dependencies() {
    print_header "Installing Backend Dependencies"
    
    if [ ! -d "backend" ]; then
        print_error "Backend directory not found"
        exit 1
    fi
    
    cd backend
    
    if [ -f "requirements.txt" ]; then
        print_status "Installing Python dependencies..."
        
        # Check if virtual environment exists
        if [ -d "venv" ]; then
            print_status "Using existing virtual environment"
            source venv/bin/activate
        elif command_exists python3; then
            print_status "Creating virtual environment"
            python3 -m venv venv
            source venv/bin/activate
        else
            print_warning "Python3 not found. Please install backend dependencies manually."
            cd ..
            return
        fi
        
        pip install -r requirements.txt
        print_status "Backend dependencies installed"
        deactivate
    else
        print_warning "requirements.txt not found in backend directory"
    fi
    
    cd ..
}

# Function to build and start services
build_and_start_services() {
    print_header "Building and Starting Services"
    
    print_status "Stopping existing services..."
    docker-compose down
    
    print_status "Building services..."
    docker-compose build
    
    print_status "Starting services..."
    docker-compose up -d
    
    print_status "Waiting for services to start..."
    sleep 10
    
    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        print_status "Services started successfully"
    else
        print_warning "Some services may not have started correctly"
        docker-compose ps
    fi
}

# Function to verify deployment
verify_deployment() {
    print_header "Verifying Deployment"
    
    # Check if backend is responding
    print_status "Checking backend health..."
    if curl -s http://localhost:8000/health > /dev/null; then
        print_status "Backend is responding"
    else
        print_warning "Backend may not be responding on port 8000"
    fi
    
    # Check if frontend is accessible
    print_status "Checking frontend accessibility..."
    if curl -s http://localhost:3000 > /dev/null; then
        print_status "Frontend is accessible"
    else
        print_warning "Frontend may not be accessible on port 3000"
    fi
    
    # Check database connection
    if [ "$SKIP_DB_MIGRATION" = false ]; then
        print_status "Checking database connection..."
        DB_HOST=${DB_HOST:-localhost}
        DB_PORT=${DB_PORT:-5432}
        DB_NAME=${DB_NAME:-iot_platform}
        DB_USER=${DB_USER:-iotuser}
        
        if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
            print_status "Database connection successful"
        else
            print_warning "Database connection failed"
        fi
    fi
}

# Function to show post-deployment information
show_post_deployment_info() {
    print_header "Post-Deployment Information"
    
    echo ""
    echo "🎉 Greenhouse features deployment completed!"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Access the platform at: http://localhost:3000"
    echo "2. Log in with your existing credentials"
    echo "3. Navigate to 'Environmental Monitoring' to see new features"
    echo "4. Navigate to 'Crop Management' for growth tracking"
    echo "5. Configure your ESP32 devices with the new firmware"
    echo ""
    echo "📖 Documentation:"
    echo "- Feature documentation: GREENHOUSE_FEATURES.md"
    echo "- API documentation: http://localhost:8000/docs"
    echo "- Database schema: database/enhanced_schema.sql"
    echo ""
    echo "🔧 ESP32 Configuration:"
    echo "- Upload esp32/greenhouse_sensors.ino to your ESP32 devices"
    echo "- Update WiFi and MQTT credentials in the firmware"
    echo "- Configure sensor pins according to your hardware setup"
    echo ""
    echo "⚠️  Important Notes:"
    echo "- Backup created in: backups/ directory"
    echo "- New database tables have been added"
    echo "- WebSocket connections now support greenhouse events"
    echo "- Role-based access is enforced for new features"
    echo ""
    
    if [ "$SKIP_DB_MIGRATION" = true ]; then
        echo "🚨 Manual Action Required:"
        echo "- Apply database/enhanced_schema.sql to your database manually"
        echo "- Ensure PostgreSQL client tools are installed for future deployments"
        echo ""
    fi
}

# Function to handle cleanup on error
cleanup_on_error() {
    print_error "Deployment failed. Cleaning up..."
    docker-compose down
    exit 1
}

# Set trap for cleanup on error
trap cleanup_on_error ERR

# Main deployment process
main() {
    echo "Starting deployment process..."
    echo ""
    
    # Ask for confirmation
    read -p "This will deploy enhanced greenhouse features. Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 0
    fi
    
    # Load environment variables if .env exists
    if [ -f ".env" ]; then
        print_status "Loading environment variables from .env"
        export $(cat .env | grep -v '^#' | xargs)
    fi
    
    # Execute deployment steps
    backup_database
    apply_database_migrations
    install_frontend_dependencies
    install_backend_dependencies
    build_and_start_services
    verify_deployment
    show_post_deployment_info
    
    print_status "Deployment completed successfully! 🎉"
}

# Run main function
main "$@"