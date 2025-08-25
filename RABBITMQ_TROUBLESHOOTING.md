# RabbitMQ Startup Troubleshooting Guide

## 🚨 **RabbitMQ Failed to Become Ready - Solution Steps**

### **Quick Fix (Try this first):**

```bash
# 1. Stop and remove the problematic container
sudo docker compose stop rnr_rabbitmq
sudo docker rm rnr_iot_rabbitmq

# 2. Clear any cached data (optional but recommended)
sudo docker volume rm rnr-iot_rnr_rabbitmq_data || true

# 3. Start with clean state
sudo docker compose up -d rnr_rabbitmq

# 4. Wait and check (be patient - RabbitMQ takes time to start)
sleep 30
sudo docker logs rnr_iot_rabbitmq
```

### **Comprehensive Fix (if quick fix doesn't work):**

```bash
# Run the automated troubleshooting script
sudo chmod +x fix_rabbitmq_startup.sh
sudo ./fix_rabbitmq_startup.sh
```

## 🔍 **Common Causes and Solutions:**

### **1. Memory Issues (Most Common)**

**Symptoms:**
- Container starts but service doesn't respond
- Out of memory errors in logs
- Container keeps restarting

**Solution:**
```bash
# Check available memory
free -h

# If less than 500MB available, create/increase swap
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Add to /etc/fstab for persistence
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### **2. Configuration File Issues**

**Symptoms:**
- RabbitMQ fails to start
- Configuration errors in logs

**Solution:**
```bash
# Check if config files exist
ls -la ./rabbitmq/

# If missing, create them:
mkdir -p ./rabbitmq

# Create enabled_plugins
echo '[rabbitmq_management,rabbitmq_mqtt].' > ./rabbitmq/enabled_plugins

# Create basic rabbitmq.conf
cat > ./rabbitmq/rabbitmq.conf << 'EOF'
vm_memory_high_watermark.relative = 0.4
disk_free_limit.absolute = 50MB
channel_max = 256
connection_max = 100
mqtt.default_user = rnr_iot_user
mqtt.default_pass = rnr_iot_2025!
mqtt.vhost = rnr_iot_vhost
mqtt.exchange = amq.topic
mqtt.prefetch = 10
mqtt.allow_anonymous = false
log.console.level = info
management.tcp.port = 15672
EOF
```

### **3. Port Conflicts**

**Symptoms:**
- Port binding errors
- Cannot start on specific ports

**Solution:**
```bash
# Check what's using RabbitMQ ports
sudo netstat -tlnp | grep -E ':(5672|15672|1883)'

# If ports are in use, stop conflicting services or change ports
# To change ports, edit docker-compose.yml:
# - "5673:5672"    # Use different external port
# - "15673:15672"  # Use different external port
# - "1884:1883"    # Use different external port
```

### **4. Docker Resource Limits**

**Symptoms:**
- Container gets killed by Docker
- Resource limit exceeded errors

**Solution:**
```bash
# Reduce memory limits temporarily
cat > docker-compose.override.yml << 'EOF'
services:
  rnr_rabbitmq:
    deploy:
      resources:
        limits:
          memory: 200M
        reservations:
          memory: 100M
EOF

# Start with reduced limits
sudo docker compose up -d rnr_rabbitmq
```

### **5. Volume/Permission Issues**

**Symptoms:**
- Permission denied errors
- Cannot write to volume

**Solution:**
```bash
# Fix permissions
sudo chown -R 999:999 ./rabbitmq/
sudo chmod -R 755 ./rabbitmq/

# Remove and recreate volume if needed
sudo docker volume rm rnr-iot_rnr_rabbitmq_data
sudo docker compose up -d rnr_rabbitmq
```

## 🛠️ **Step-by-Step Manual Diagnosis:**

### **Step 1: Check Container Status**
```bash
sudo docker ps -a | grep rabbitmq
```

### **Step 2: Check Container Logs**
```bash
sudo docker logs rnr_iot_rabbitmq
```

### **Step 3: Check Resource Usage**
```bash
sudo docker stats rnr_iot_rabbitmq --no-stream
```

### **Step 4: Test Inside Container**
```bash
# If container is running but service not ready
sudo docker exec rnr_iot_rabbitmq rabbitmq-diagnostics ping
sudo docker exec rnr_iot_rabbitmq rabbitmq-diagnostics status
```

### **Step 5: Check Configuration Loading**
```bash
sudo docker exec rnr_iot_rabbitmq cat /etc/rabbitmq/rabbitmq.conf
sudo docker exec rnr_iot_rabbitmq rabbitmq-plugins list
```

## ⚡ **Emergency Recovery:**

If nothing works, use this nuclear option:

```bash
# 1. Stop everything
sudo docker compose down

# 2. Remove all RabbitMQ data
sudo docker volume rm rnr-iot_rnr_rabbitmq_data

# 3. Remove config files and recreate
rm -rf ./rabbitmq/
mkdir -p ./rabbitmq

# 4. Create minimal config
echo '[rabbitmq_management,rabbitmq_mqtt].' > ./rabbitmq/enabled_plugins

cat > ./rabbitmq/rabbitmq.conf << 'EOF'
vm_memory_high_watermark.relative = 0.6
mqtt.default_user = rnr_iot_user
mqtt.default_pass = rnr_iot_2025!
mqtt.vhost = rnr_iot_vhost
mqtt.allow_anonymous = false
EOF

# 5. Use basic RabbitMQ image if alpine doesn't work
# Edit docker-compose.yml and change:
# image: rabbitmq:3-management

# 6. Start with increased timeout
sudo docker compose up -d rnr_rabbitmq
sleep 60  # Wait longer
sudo docker logs rnr_iot_rabbitmq
```

## 📞 **If All Else Fails:**

1. **Check system requirements**: Ensure at least 1GB RAM available
2. **Try different RabbitMQ version**: Use `rabbitmq:3.9-management-alpine`
3. **Use external RabbitMQ**: Consider AWS MQ or CloudAMQP
4. **Increase instance size**: Upgrade to t3.small or larger

## 🎯 **Expected Startup Time:**

- **Normal startup**: 30-60 seconds
- **First startup**: 60-120 seconds
- **Low memory systems**: 120-180 seconds

**Be patient!** RabbitMQ can take several minutes to start on low-memory systems.
