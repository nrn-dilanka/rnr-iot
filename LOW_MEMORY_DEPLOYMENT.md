# RNR Solutions IoT Platform - Low Memory Deployment Guide

## 🚨 **2GB RAM Optimization Guide**

This guide is specifically designed for AWS EC2 instances with 2GB RAM (t3.micro, t2.small, etc.).

## 📊 **Memory Allocation Strategy**

| Service | Memory Limit | Memory Reservation | Purpose |
|---------|-------------|-------------------|---------|
| PostgreSQL | 384MB | 256MB | Database |
| RabbitMQ | 256MB | 128MB | Message Broker |
| API Server | 512MB | 256MB | Backend API |
| Worker Service | 384MB | 192MB | Background Tasks |
| Frontend | 384MB | 192MB | React App |
| **Total** | **1.92GB** | **1.024GB** | **All Services** |

*Note: This leaves ~80MB for system overhead and nginx*

## 🔧 **Optimizations Applied**

### **System Level:**
- ✅ 1GB Swap file creation
- ✅ Kernel memory optimization (`vm.swappiness=10`)
- ✅ Reduced cache pressure
- ✅ Memory overcommit enabled

### **Docker Level:**
- ✅ Alpine Linux base images (smaller footprint)
- ✅ Resource limits on all containers
- ✅ Sequential startup to prevent memory spikes
- ✅ Build-time optimizations

### **Application Level:**
- ✅ Python bytecode writing disabled
- ✅ Node.js memory limit set to 256MB
- ✅ PostgreSQL optimized for 64MB shared buffers
- ✅ RabbitMQ memory watermark set to 40%
- ✅ Single worker processes

## 🚀 **Deployment Instructions**

### **Step 1: Check System Requirements**

```bash
# Check available memory
free -h

# Check disk space (need at least 10GB)
df -h

# Ensure you have at least 1.5GB available memory
```

### **Step 2: Deploy with Low Memory Script**

```bash
# Use the optimized deployment script
sudo chmod +x deploy_low_memory.sh
sudo ./deploy_low_memory.sh
```

This script will:
- Create swap file if needed
- Configure kernel for low memory
- Start services sequentially with delays
- Monitor resource usage

### **Step 3: Monitor Performance**

```bash
# Monitor memory usage
./monitor_memory.sh

# Check container stats
docker stats

# View system memory
free -h && cat /proc/meminfo | grep -E "(MemTotal|MemFree|MemAvailable|SwapTotal|SwapFree)"
```

## ⚠️ **Performance Expectations**

### **What to Expect:**
- ✅ Platform will run successfully with 2GB RAM
- ✅ Basic functionality will work normally
- ✅ Up to 10 concurrent IoT devices supported
- ⚠️ Slower response times during high load
- ⚠️ Limited concurrent users (1-3 recommended)

### **What May Struggle:**
- ❌ Large file uploads (>50MB)
- ❌ Heavy data analytics
- ❌ Many concurrent API requests (>10/sec)
- ❌ Complex AI/ML operations

## 🛠️ **Troubleshooting**

### **Service Keeps Crashing (OOM - Out of Memory)**

```bash
# Check which service is using too much memory
docker stats --no-stream

# Restart services one by one
docker compose restart rnr_postgres
sleep 10
docker compose restart rnr_rabbitmq
sleep 10
docker compose restart rnr_api_server
sleep 10
docker compose restart rnr_worker_service
sleep 10
docker compose restart rnr_frontend
```

### **System is Slow/Unresponsive**

```bash
# Check swap usage
swapon --show

# Check if swap is being used heavily
cat /proc/swaps

# Restart the heaviest service
docker compose restart rnr_api_server

# If still slow, restart all services
sudo ./deploy_low_memory.sh
```

### **Database Connection Issues**

```bash
# Check PostgreSQL memory settings
docker exec rnr_iot_postgres psql -U rnr_iot_user -d rnr_iot_platform -c "SHOW shared_buffers;"

# Apply low memory configuration
docker exec rnr_iot_postgres psql -U rnr_iot_user -d rnr_iot_platform -f /docker-entrypoint-initdb.d/low_memory_config.sql
```

## 📈 **Scaling Recommendations**

### **Immediate Improvements:**
1. **Upgrade to t3.small (2 vCPU, 2GB)** - Better CPU performance
2. **Add more swap** - Increase swap to 2GB if needed
3. **Use external database** - RDS PostgreSQL (t3.micro)

### **Production Scaling:**
1. **t3.medium (2 vCPU, 4GB)** - Recommended minimum for production
2. **t3.large (2 vCPU, 8GB)** - Ideal for production with multiple users
3. **External services:**
   - Amazon RDS for PostgreSQL
   - Amazon MQ for RabbitMQ
   - Amazon ElastiCache for caching

## 🔍 **Monitoring Commands**

```bash
# Real-time memory monitoring
watch -n 1 'free -h && echo "" && docker stats --no-stream'

# Check service logs for memory issues
docker compose logs rnr_api_server | grep -i "memory\|oom\|killed"

# System resource summary
echo "=== System Resources ===" && \
free -h && echo "" && \
df -h / && echo "" && \
docker system df

# Process memory usage
ps aux --sort=-%mem | head -10
```

## 🎯 **Performance Tuning Tips**

### **Database Optimization:**
```sql
-- Connect to database and run:
VACUUM ANALYZE;
REINDEX DATABASE rnr_iot_platform;

-- Check table sizes
SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables WHERE schemaname='public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### **Application Optimization:**
```bash
# Reduce log levels to save memory
export LOG_LEVEL=WARNING

# Limit API workers
export MAX_WORKERS=1

# Reduce connection pools
export DB_POOL_SIZE=5
export RABBITMQ_POOL_SIZE=3
```

## 🚨 **Emergency Procedures**

### **If System Becomes Unresponsive:**

```bash
# 1. SSH to the server (may be slow)
ssh -i your-key.pem ubuntu@your-ec2-ip

# 2. Stop all containers
sudo docker compose down

# 3. Clear memory
sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches

# 4. Check memory
free -h

# 5. Restart services slowly
sudo ./deploy_low_memory.sh
```

### **If SSH Connection Fails:**
1. Reboot EC2 instance from AWS Console
2. Wait 2-3 minutes for system to stabilize
3. SSH back in and run: `sudo ./deploy_low_memory.sh`

## 📞 **Support & Optimization**

The platform has been optimized to run on 2GB RAM, but for production use:

**Minimum Recommended:**
- **Development/Testing:** t3.micro (1 vCPU, 1GB) with this guide
- **Small Production:** t3.small (1 vCPU, 2GB)
- **Production:** t3.medium (2 vCPU, 4GB) or larger

**Cost vs Performance:**
- t3.micro: ~$8/month (limited performance)
- t3.small: ~$16/month (good for 5-10 devices)
- t3.medium: ~$30/month (production ready, 50+ devices)

Remember: The low-memory optimizations trade some performance for compatibility with smaller instances.
