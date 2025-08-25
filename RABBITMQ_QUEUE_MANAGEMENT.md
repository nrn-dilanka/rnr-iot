# 🐰 RabbitMQ Queue Management Guide

## 📊 Current Queue Status

### Active Queues
- **Queue Name**: `device_data`
- **Messages**: 0 (no pending messages)
- **Consumers**: 1 (active consumer connected)
- **Memory**: 22,120 bytes
- **State**: running

### Queue Bindings
- **Exchange**: `amq.topic`
- **Routing Key**: `devices.*.data`
- **Destination**: `device_data` queue

## 🌐 WEB INTERFACE ACCESS (RECOMMENDED)

### Login Credentials
- **URL**: http://localhost:15672
- **Username**: `rnr_iot_user`
- **Password**: `rnr_iot_2025!`
- **Virtual Host**: `rnr_iot_vhost`

### Web UI Features
1. **Queues Tab** - View all queues, messages, and consumer details
2. **Exchanges Tab** - Manage message routing
3. **Bindings Tab** - Configure queue-exchange relationships
4. **Connections Tab** - Monitor active connections
5. **Channels Tab** - View communication channels

## 🖥️ COMMAND LINE MANAGEMENT

### View Queues
```bash
# Basic queue info
docker exec rnr_iot_rabbitmq rabbitmqctl list_queues name messages consumers -p rnr_iot_vhost

# Detailed queue info
docker exec rnr_iot_rabbitmq rabbitmqctl list_queues name messages consumers memory state -p rnr_iot_vhost

# Queue with message rates
docker exec rnr_iot_rabbitmq rabbitmqctl list_queues name messages consumers message_bytes -p rnr_iot_vhost
```

### Manage Queues
```bash
# Create a new queue
docker exec rnr_iot_rabbitmq rabbitmqctl declare queue name=my_new_queue durable=true -p rnr_iot_vhost

# Delete a queue
docker exec rnr_iot_rabbitmq rabbitmqctl delete_queue my_queue_name -p rnr_iot_vhost

# Purge all messages from a queue
docker exec rnr_iot_rabbitmq rabbitmqctl purge_queue device_data -p rnr_iot_vhost
```

### View Exchanges
```bash
# List all exchanges
docker exec rnr_iot_rabbitmq rabbitmqctl list_exchanges name type -p rnr_iot_vhost

# List bindings
docker exec rnr_iot_rabbitmq rabbitmqctl list_bindings source_name destination_name routing_key -p rnr_iot_vhost
```

### Monitor Connections
```bash
# List connections
docker exec rnr_iot_rabbitmq rabbitmqctl list_connections name host port state -p rnr_iot_vhost

# List consumers
docker exec rnr_iot_rabbitmq rabbitmqctl list_consumers queue_name channel_pid consumer_tag -p rnr_iot_vhost
```

## 🔧 QUEUE MANAGEMENT OPERATIONS

### 1. Message Publishing (Test)
```bash
# Publish a test message to device_data queue
docker exec rnr_iot_rabbitmq rabbitmqadmin -u rnr_iot_user -p rnr_iot_2025! -V rnr_iot_vhost publish exchange=amq.topic routing_key=devices.test.data payload="Hello IoT Device"
```

### 2. Queue Monitoring
```bash
# Monitor queue in real-time
watch -n 2 'docker exec rnr_iot_rabbitmq rabbitmqctl list_queues name messages consumers -p rnr_iot_vhost'
```

### 3. Get Queue Details
```bash
# Get specific queue info
docker exec rnr_iot_rabbitmq rabbitmqctl list_queue_bindings device_data -p rnr_iot_vhost
```

## 🚀 INDUSTRIAL IOT QUEUE PATTERNS

### Current Setup
- **Pattern**: Topic Exchange with wildcard routing
- **Routing Key**: `devices.*.data` (matches devices.ESP32_001.data, devices.sensor_hub.data, etc.)
- **Use Case**: Route sensor data from multiple IoT devices to the same processing queue

### Common Queue Operations for IoT
1. **Device Registration**: Create device-specific queues
2. **Data Aggregation**: Funnel all device data to processing queues
3. **Alert Routing**: Route critical alerts to priority queues
4. **Dead Letter Handling**: Manage failed message processing

## 📈 MONITORING & TROUBLESHOOTING

### Health Checks
```bash
# Check RabbitMQ status
docker exec rnr_iot_rabbitmq rabbitmqctl status

# Check cluster status
docker exec rnr_iot_rabbitmq rabbitmqctl cluster_status

# Check memory usage
docker exec rnr_iot_rabbitmq rabbitmqctl status | grep -A 5 "Memory"
```

### Performance Monitoring
```bash
# Queue memory usage
docker exec rnr_iot_rabbitmq rabbitmqctl list_queues name memory -p rnr_iot_vhost

# Connection details
docker exec rnr_iot_rabbitmq rabbitmqctl list_connections user state channels -p rnr_iot_vhost
```

## ⚠️ IMPORTANT NOTES

1. **Backup**: Always backup before major queue changes
2. **Monitoring**: Use the web UI for real-time monitoring
3. **Testing**: Test queue operations in development first
4. **Security**: Restrict access to production queues
5. **Scaling**: Monitor memory usage as queues grow

## 🔗 Quick Access Commands

```bash
# Open RabbitMQ Management UI
# http://localhost:15672

# Quick queue status
docker exec rnr_iot_rabbitmq rabbitmqctl list_queues -p rnr_iot_vhost

# Emergency queue purge
docker exec rnr_iot_rabbitmq rabbitmqctl purge_queue device_data -p rnr_iot_vhost
```

---
**Login Info**: `rnr_iot_user` / `rnr_iot_2025!` at http://localhost:15672
