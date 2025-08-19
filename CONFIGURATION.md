# RNR Solutions IoT Platform Configuration Parameters

This document lists all the configuration parameters used in the RNR Solutions IoT Platform.

## Environment Files

### Main Project (.env)
Contains global configuration parameters for the entire platform.

### Frontend (frontend/.env)
Contains React-specific environment variables for the frontend application.

### Backend (backend/.env)
Contains API server and worker service specific environment variables.

## Configuration Parameters

### 🗄️ Database Configuration
```bash
DATABASE_URL=postgresql://iotuser:iotpassword@postgres:5432/iot_platform
POSTGRES_DB=iot_platform
POSTGRES_USER=iotuser
POSTGRES_PASSWORD=iotpassword
```

### 🐰 RabbitMQ Configuration
```bash
RABBITMQ_URL=amqp://iotuser:iotpassword@rabbitmq:5672/iot_vhost
RABBITMQ_DEFAULT_USER=iotuser
RABBITMQ_DEFAULT_PASS=iotpassword
RABBITMQ_DEFAULT_VHOST=iot_vhost
```

### 🌐 API Server Configuration
```bash
API_HOST=0.0.0.0
API_PORT=8000
API_URL=http://api_server:8000
UPLOAD_DIR=/app/uploads
```

### 🎨 Frontend Configuration
```bash
REACT_APP_API_URL=http://192.168.8.108:8000/api
REACT_APP_WS_URL=ws://192.168.8.108:8000/ws
REACT_APP_VERSION=1.0.0
GENERATE_SOURCEMAP=false
```

### 🤖 AI Service Configuration
```bash
GEMINI_API_KEY=AIzaSyAs2JqPjvUcWeg5K2Vxeto7j37GzUzABUY
```

### 🔐 Security Configuration
```bash
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET=your-jwt-secret-change-in-production
```

### 🛠️ Development Settings
```bash
DEBUG=true
LOG_LEVEL=INFO
```

## Docker Services Configuration

### Service Ports
- **Frontend**: 3000 (HTTP)
- **API Server**: 8000 (HTTP)
- **PostgreSQL**: 5432 (Database)
- **RabbitMQ AMQP**: 5672 (Message Queue)
- **RabbitMQ MQTT**: 1883 (IoT Device Communication)
- **RabbitMQ Management**: 15672 (Web UI)

### Volume Mounts
- `rabbitmq_data`: RabbitMQ persistent data
- `postgres_data`: PostgreSQL database files
- `firmware_uploads`: Firmware file uploads

### Network Configuration
- **Network Name**: `iot_network`
- **Driver**: `bridge`

## Important Notes

### 🚨 Security Considerations
1. **Change default passwords** in production environments
2. **Update SECRET_KEY and JWT_SECRET** with secure random values
3. **Restrict database access** to necessary services only
4. **Use HTTPS** in production deployments

### 🌍 Network Configuration
- Update IP addresses (`192.168.8.108`) to match your local network
- For localhost development, use `localhost` instead of IP addresses
- For production, use proper domain names or load balancer IPs

### 🔧 Customization
- Modify `GEMINI_API_KEY` with your own Google AI API key
- Adjust `UPLOAD_DIR` for custom file storage locations
- Configure `LOG_LEVEL` based on your debugging needs

## Quick Setup Commands

```bash
# Copy environment files
cp .env.example .env

# Update IP addresses in environment files
# Edit .env, frontend/.env, and backend/.env

# Build and start the platform
docker-compose up --build -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f [service_name]
```

## Troubleshooting

### Common Issues
1. **Port conflicts**: Ensure ports 3000, 8000, 5432, 5672, 1883, 15672 are available
2. **Network connectivity**: Verify IP addresses match your network configuration
3. **Environment variables**: Check that all required variables are set in .env files
4. **Service dependencies**: Ensure database and RabbitMQ are healthy before starting API server

### Health Checks
- PostgreSQL: `docker exec iot_postgres pg_isready -U iotuser -d iot_platform`
- RabbitMQ: `docker exec iot_rabbitmq rabbitmq-diagnostics ping`
- API Server: `curl http://localhost:8000/health` (if health endpoint exists)
