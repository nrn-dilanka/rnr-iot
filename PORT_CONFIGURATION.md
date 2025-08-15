# RNR Solutions IoT Platform - Port Configuration Guide

## 📋 **Complete Port Overview**

### **🌐 External/Public Ports (Internet Accessible)**

| Port | Service | Protocol | Purpose | Required |
|------|---------|----------|---------|----------|
| **80** | nginx | HTTP | Web traffic, API proxy | ✅ **Required** |
| **443** | nginx | HTTPS | Secure web traffic | ✅ **Production** |
| **1883** | RabbitMQ | MQTT | IoT device connections | ✅ **Required** |
| **22** | SSH | TCP | Server administration | ⚠️ **Restrict to your IP** |

### **🔒 Internal/Development Ports (Should be restricted)**

| Port | Service | Protocol | Purpose | Access |
|------|---------|----------|---------|---------|
| **3000** | Frontend | HTTP | React development server | 🔒 **Dev only** |
| **8000** | API Server | HTTP | Direct API access | 🔒 **Dev only** |
| **15672** | RabbitMQ | HTTP | Management interface | 🔒 **Admin only** |
| **15432** | PostgreSQL | TCP | Database connections | 🔒 **Internal only** |
| **5672** | RabbitMQ | AMQP | Message queue protocol | 🔒 **Internal only** |

## 🏗️ **Architecture Flow**

```
Internet → AWS Security Group → EC2 Instance
                                      ↓
                               nginx (Port 80/443)
                                      ↓
                    ┌─────────────────┼─────────────────┐
                    ↓                 ↓                 ↓
              Frontend (3000)    API Server (8000)  Static Files
                    ↓                 ↓
                    └─────────────────┼─────────────────┘
                                      ↓
                            Internal Services:
                            ├─ PostgreSQL (15432)
                            ├─ RabbitMQ AMQP (5672)
                            └─ RabbitMQ MQTT (1883)
```

## 🔐 **Security Configuration**

### **AWS Security Group (Production)**

**Inbound Rules:**
```
SSH         | TCP | 22   | YOUR_IP_ONLY    | Administration
HTTP        | TCP | 80   | 0.0.0.0/0       | Web traffic
HTTPS       | TCP | 443  | 0.0.0.0/0       | Secure web
MQTT        | TCP | 1883 | 0.0.0.0/0       | IoT devices
```

**Outbound Rules:**
```
All Traffic | All | All  | 0.0.0.0/0       | Internet access
```

### **AWS Security Group (Development)**

**Additional Inbound Rules:**
```
RabbitMQ UI | TCP | 15672| YOUR_IP_ONLY    | Management
Frontend    | TCP | 3000 | YOUR_IP_ONLY    | Development
API Direct  | TCP | 8000 | YOUR_IP_ONLY    | Development
```

### **UFW Firewall (Ubuntu)**

```bash
# Basic production setup
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 1883/tcp

# Development additions
sudo ufw allow from YOUR_IP to any port 15672
sudo ufw allow from YOUR_IP to any port 3000
sudo ufw allow from YOUR_IP to any port 8000
```

## 🌍 **Access URLs**

Replace `YOUR_SERVER_IP` with your actual EC2 public IP address.

### **Production URLs (Always Available)**
- **Frontend**: `http://YOUR_SERVER_IP`
- **API**: `http://YOUR_SERVER_IP/api`
- **WebSocket**: `ws://YOUR_SERVER_IP/ws`
- **MQTT**: `mqtt://YOUR_SERVER_IP:1883`

### **Development URLs (Restricted Access)**
- **Direct Frontend**: `http://YOUR_SERVER_IP:3000`
- **Direct API**: `http://YOUR_SERVER_IP:8000`
- **RabbitMQ Management**: `http://YOUR_SERVER_IP:15672`
  - Username: `rnr_iot_user`
  - Password: `rnr_iot_2025!`

### **Admin URLs (Internal Only)**
- **PostgreSQL**: `postgresql://rnr_iot_user:rnr_iot_2025!@YOUR_SERVER_IP:15432/rnr_iot_platform`

## 🔍 **Port Checking Commands**

### **Check All Open Ports**
```bash
# On your server
sudo netstat -tlnp | grep LISTEN

# Or using ss
sudo ss -tlnp | grep LISTEN
```

### **Check Specific Service Ports**
```bash
# Check nginx
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443

# Check Docker services
docker ps --format "table {{.Names}}\t{{.Ports}}"

# Check RabbitMQ specifically
sudo netstat -tlnp | grep -E ':(5672|15672|1883)'

# Check PostgreSQL
sudo netstat -tlnp | grep :15432
```

### **Test External Connectivity**
```bash
# From your local machine
telnet YOUR_SERVER_IP 80
telnet YOUR_SERVER_IP 1883
curl http://YOUR_SERVER_IP
```

## 🚨 **Troubleshooting Port Issues**

### **Port Already in Use**
```bash
# Find what's using a port
sudo lsof -i :PORT_NUMBER
sudo fuser -n tcp PORT_NUMBER

# Kill process using port
sudo fuser -k PORT_NUMBER/tcp
```

### **Cannot Bind to Port**
```bash
# Check if port is available
sudo netstat -tlnp | grep :PORT_NUMBER

# For ports < 1024, ensure running as root
sudo docker-compose up -d
```

### **Firewall Blocking**
```bash
# Check UFW status
sudo ufw status

# Check iptables
sudo iptables -L

# Temporarily disable for testing
sudo ufw disable
```

### **AWS Security Group Issues**
1. Go to AWS EC2 Console
2. Select your instance
3. Go to Security Groups
4. Edit inbound rules
5. Add required ports

## 📊 **Port Monitoring**

### **Real-time Port Monitoring**
```bash
# Monitor all connections
watch -n 1 'sudo netstat -tuln'

# Monitor Docker containers
watch -n 1 'docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"'

# Monitor specific ports
watch -n 1 'sudo netstat -tlnp | grep -E ":(80|443|1883|3000|8000|15672|15432)"'
```

### **Log Analysis**
```bash
# nginx access logs
sudo tail -f /var/log/nginx/access.log

# Docker container logs
docker logs -f rnr_iot_api_server
docker logs -f rnr_iot_rabbitmq

# System logs for port issues
sudo journalctl -u nginx -f
```

## ⚡ **Quick Port Check Script**

Use the provided script to check all ports:
```bash
chmod +x check_ports.sh
sudo ./check_ports.sh
```

## 🎯 **Production vs Development**

### **Production (Minimal Exposure)**
```
External: 80, 443, 1883, 22 (restricted)
Internal: All other services via nginx proxy
```

### **Development (More Access)**
```
External: 80, 443, 1883, 22, 3000, 8000, 15672 (restricted)
Internal: 15432, 5672
```

## 📞 **Emergency Port Recovery**

If you lose access to your server:

1. **AWS Console** → EC2 → Security Groups → Edit Rules
2. **Temporarily allow all traffic** from your IP: `0.0.0.0/0` for port 22
3. **SSH in and fix** the firewall/port configuration
4. **Restore proper security** rules

Remember: Always test connectivity after making security changes!
