# RNR Solutions IoT Platform - AWS EC2 Ubuntu Setup Guide

## Overview

This guide will help you deploy the RNR Solutions IoT Platform on AWS EC2 Ubuntu with nginx as a reverse proxy.

## Architecture

```
Internet → AWS Security Group → nginx (Port 80/443) → Docker Services
                                                    ├── Frontend (React) :3000
                                                    ├── API Server :8000
                                                    ├── Worker Service
                                                    ├── PostgreSQL :15432
                                                    └── RabbitMQ :5672/:15672/:1883
```

## Prerequisites

### AWS EC2 Instance Requirements

- **Instance Type**: t3.medium or larger (recommended t3.large for production)
- **Operating System**: Ubuntu 22.04 LTS or Ubuntu 20.04 LTS
- **Storage**: At least 20GB SSD
- **Memory**: Minimum 4GB RAM (8GB recommended)

### AWS Security Group Configuration

Configure your security group with the following inbound rules:

| Type | Protocol | Port Range | Source | Description |
|------|----------|------------|--------|-------------|
| SSH | TCP | 22 | Your IP | SSH access |
| HTTP | TCP | 80 | 0.0.0.0/0 | Web traffic |
| HTTPS | TCP | 443 | 0.0.0.0/0 | Secure web traffic |
| Custom TCP | TCP | 1883 | 0.0.0.0/0 | MQTT for IoT devices |

## Installation Steps

### Step 1: Connect to Your EC2 Instance

```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

### Step 2: Upload Project Files

Upload your project files to the EC2 instance using SCP or git:

**Option A: Using Git (Recommended)**
```bash
git clone https://github.com/your-username/rnr-iot.git
cd rnr-iot
```

**Option B: Using SCP**
```bash
# From your local machine
scp -i your-key.pem -r /path/to/rnr-iot ubuntu@your-ec2-public-ip:~/
```

### Step 3: Run the Setup Script

```bash
sudo chmod +x setup_aws_ubuntu.sh
sudo ./setup_aws_ubuntu.sh
```

This script will:
- Update the system
- Install nginx, Docker, and Docker Compose
- Configure firewall rules
- Set up log rotation
- Create environment file template

### Step 4: Configure Environment Variables

Edit the `.env` file with your actual configuration:

```bash
nano .env
```

Update the following variables:
```env
# Replace with your EC2 public IP or domain
REACT_APP_API_URL=http://YOUR_EC2_PUBLIC_IP/api
REACT_APP_WS_URL=ws://YOUR_EC2_PUBLIC_IP/ws

# Update with your actual Gemini API key
GEMINI_API_KEY=your_actual_gemini_api_key

# Database and RabbitMQ passwords (change for production)
DATABASE_URL=postgresql://rnr_iot_user:YOUR_SECURE_PASSWORD@localhost:15432/rnr_iot_platform
RABBITMQ_URL=amqp://rnr_iot_user:YOUR_SECURE_PASSWORD@localhost:5672/rnr_iot_vhost
```

### Step 5: Update Nginx Configuration

Edit the nginx configuration with your domain or EC2 public IP:

```bash
sudo nano nginx.conf
```

Replace `localhost` in the `server_name` directive:
```nginx
server_name your-domain.com;  # or your EC2 public IP
```

### Step 6: Deploy the Platform

```bash
sudo chmod +x deploy_aws_platform.sh
sudo ./deploy_aws_platform.sh
```

This script will:
- Build and start all Docker containers
- Install nginx configuration
- Start all services
- Verify deployment

## Post-Deployment Configuration

### Verify Installation

1. **Check service status**:
   ```bash
   ./monitor_platform.sh
   ```

2. **Access the platform**:
   - Frontend: `http://your-ec2-public-ip`
   - API: `http://your-ec2-public-ip/api`
   - RabbitMQ Management: `http://your-ec2-public-ip/rabbitmq`

### SSL Certificate Setup (Production)

For production deployment, set up SSL certificates using Let's Encrypt:

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Test automatic renewal
sudo certbot renew --dry-run
```

Update your nginx configuration to use HTTPS by uncommenting the SSL server block.

## Monitoring and Maintenance

### View Logs

```bash
# Application logs
docker-compose logs -f rnr_api_server
docker-compose logs -f rnr_frontend
docker-compose logs -f rnr_worker_service

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# System logs
sudo journalctl -u nginx -f
```

### Platform Management Commands

```bash
# Stop the platform
docker-compose down

# Start the platform
docker-compose up -d

# Restart specific service
docker-compose restart rnr_api_server

# Update platform (rebuild and restart)
sudo ./deploy_aws_platform.sh

# Check system status
./monitor_platform.sh
```

### Database Management

```bash
# Access PostgreSQL
docker exec -it rnr_iot_postgres psql -U rnr_iot_user -d rnr_iot_platform

# Backup database
docker exec rnr_iot_postgres pg_dump -U rnr_iot_user rnr_iot_platform > backup.sql

# Restore database
docker exec -i rnr_iot_postgres psql -U rnr_iot_user -d rnr_iot_platform < backup.sql
```

## Security Considerations

### Production Security Checklist

- [ ] Change default passwords in docker-compose.yml
- [ ] Set up SSL certificates
- [ ] Restrict RabbitMQ management access
- [ ] Configure proper firewall rules
- [ ] Enable automatic security updates
- [ ] Set up monitoring and alerting
- [ ] Regular security audits

### Firewall Configuration

```bash
# Check current rules
sudo ufw status

# Allow specific IP for SSH (recommended)
sudo ufw delete allow ssh
sudo ufw allow from YOUR_IP to any port 22

# Block RabbitMQ management from public access
sudo ufw deny 15672
```

## Troubleshooting

### Common Issues

1. **Port conflicts**:
   ```bash
   sudo netstat -tlnp | grep -E ':(80|443|3000|8000)'
   ```

2. **Docker service issues**:
   ```bash
   docker-compose ps
   docker-compose logs [service_name]
   ```

3. **Nginx configuration errors**:
   ```bash
   sudo nginx -t
   sudo systemctl status nginx
   ```

4. **Memory issues**:
   ```bash
   free -h
   docker stats
   ```

### Performance Optimization

For high-traffic production deployments:

1. **Increase instance size** to t3.large or t3.xlarge
2. **Use RDS** for PostgreSQL instead of containerized database
3. **Set up Application Load Balancer** for multiple instances
4. **Configure CloudWatch** for monitoring
5. **Use ElastiCache** for Redis caching

## Support

For issues and support:
- Check logs using the monitoring script
- Review the troubleshooting section
- Ensure all prerequisites are met
- Verify security group configuration

## Version Information

- Platform Version: 2.0.0
- Nginx Version: Latest stable
- Docker Compose Version: v2.x
- Ubuntu Version: 20.04/22.04 LTS
