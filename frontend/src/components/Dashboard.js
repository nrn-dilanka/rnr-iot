import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Table, Badge, Alert, Button, Progress, Divider } from 'antd';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import {
  WifiOutlined,
  DisconnectOutlined,
  ThunderboltOutlined,
  SettingOutlined,
  ReloadOutlined,
  EyeOutlined
} from '@ant-design/icons';
import { nodeAPI, sensorDataAPI } from '../services/api';
import WebSocketService from '../services/WebSocketService';
import moment from 'moment';

const Dashboard = () => {
  const [nodes, setNodes] = useState([]);
  const [sensorData, setSensorData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [realtimeEnabled, setRealtimeEnabled] = useState(true);
  const [systemHealth, setSystemHealth] = useState({
    cpu: 0,
    memory: 0,
    disk: 0,
    network: 0
  });
  const [metrics, setMetrics] = useState({
    totalNodes: 0,
    onlineNodes: 0,
    offlineNodes: 0,
    averageTemperature: 0,
    averageHumidity: 0,
    averageHumidityMQ: 0,
    averageGasSensor: 0,
    currentServoAngle: 0,
    averageWifiRssi: 0,
    totalMessages: 0,
    messagesPerMinute: 0,
  });

  useEffect(() => {
    console.log('🚀 Dashboard component initializing...');
    loadNodes();
    loadSensorData();
    initializeWebSocket();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      if (realtimeEnabled) {
        console.log('🔄 Auto-refreshing dashboard data...');
        loadNodes();
        loadSensorData();
        updateSystemHealth();
      }
    }, 30000);

    return () => {
      clearInterval(interval);
      const wsService = WebSocketService.getInstance();
      wsService.unsubscribe('sensor_data', handleSensorDataUpdate);
      wsService.unsubscribe('node_status', handleNodeStatusUpdate);
      wsService.unsubscribe('system_health', handleSystemHealthUpdate);
    };
  }, [realtimeEnabled]);

  const initializeWebSocket = () => {
    console.log('🔌 Initializing WebSocket connection...');
    const wsService = WebSocketService.getInstance();
    
    wsService.connect(
      () => {
        console.log('✅ Dashboard WebSocket connected');
        setWsConnected(true);
      },
      () => {
        console.log('❌ Dashboard WebSocket disconnected');
        setWsConnected(false);
      },
      (error) => {
        console.error('🚨 Dashboard WebSocket error:', error);
        setWsConnected(false);
      }
    );

    // Subscribe to real-time data
    wsService.subscribe('sensor_data', handleSensorDataUpdate);
    wsService.subscribe('node_status', handleNodeStatusUpdate);
    wsService.subscribe('system_health', handleSystemHealthUpdate);
  };

  const loadNodes = async () => {
    try {
      setLoading(true);
      const response = await nodeAPI.getNodes();
      console.log('Dashboard API response:', response);
      
      // Ensure we always have an array
      const nodeList = response?.data || response || [];
      console.log('Dashboard node data:', nodeList);
      
      // Make sure it's an array
      if (Array.isArray(nodeList)) {
        setNodes(nodeList);
        updateMetrics(nodeList);
      } else {
        console.error('Node data is not an array:', nodeList);
        setNodes([]);
        updateMetrics([]);
      }
    } catch (error) {
      console.error('Error loading nodes:', error);
      setNodes([]); // Ensure nodes is always an array on error
      updateMetrics([]);
    } finally {
      setLoading(false);
    }
  };

  const loadSensorData = async () => {
    try {
      const response = await sensorDataAPI.getSensorData(50); // Get last 50 sensor readings
      const rawData = response.data;
      
      // Transform the data for charts
      const transformedData = rawData.map(item => ({
        time: moment(item.received_at).format('HH:mm:ss'),
        temperature: item.data.temperature || 0,
        humidity: item.data.humidity || 0,
        humidity_mq: item.data.humidity_mq || 0,
        humidity_mq_raw: item.data.humidity_mq_raw || 0,
        gas_sensor: item.data.gas_sensor || 0,
        servo_angle: item.data.servo_angle || 0,
        wifi_rssi: item.data.wifi_rssi || 0,
        nodeId: item.node_id,
        timestamp: item.received_at,
        uptime: item.data.uptime || 0,
        light_state: item.data.light_state || false,
        fan_state: item.data.fan_state || false,
        relay3_state: item.data.relay3_state || false,
        relay4_state: item.data.relay4_state || false,
        real_model_state: item.data.real_model_state || false,
        smart_mode: item.data.smart_mode || false
      })).reverse(); // Reverse to show oldest to newest
      
      setSensorData(transformedData);
      console.log('Loaded sensor data:', transformedData.length, 'records');
    } catch (error) {
      console.error('Error loading sensor data:', error);
    }
  };

  const handleSensorDataUpdate = (data) => {
    console.log('📡 Received sensor data update:', data.node_id);
    setLastUpdate(new Date());
    
    // Update sensor data for charts
    setSensorData(prevData => {
      const newData = [...prevData, {
        time: moment().format('HH:mm:ss'),
        temperature: data.data?.temperature || data.temperature || 0,
        humidity: data.data?.humidity || data.humidity || 0,
        humidity_mq: data.data?.humidity_mq || data.humidity_mq || 0,
        humidity_mq_raw: data.data?.humidity_mq_raw || data.humidity_mq_raw || 0,
        gas_sensor: data.data?.gas_sensor || data.gas_sensor || 0,
        servo_angle: data.data?.servo_angle || data.servo_angle || 0,
        wifi_rssi: data.data?.wifi_rssi || data.wifi_rssi || 0,
        nodeId: data.node_id,
        timestamp: data.timestamp || new Date().toISOString(),
        uptime: data.data?.uptime || data.uptime || 0,
        light_state: data.data?.light_state || data.light_state || false,
        fan_state: data.data?.fan_state || data.fan_state || false,
        relay3_state: data.data?.relay3_state || data.relay3_state || false,
        relay4_state: data.data?.relay4_state || data.relay4_state || false,
        real_model_state: data.data?.real_model_state || data.real_model_state || false,
        smart_mode: data.data?.smart_mode || data.smart_mode || false
      }];
      
      // Keep only last 100 data points for better visualization
      return newData.slice(-100);
    });

    // Update node last_seen and increment message count
    setNodes(prevNodes => {
      const updatedNodes = prevNodes.map(node => {
        if (node.node_id === data.node_id) {
          return { 
            ...node, 
            last_seen: new Date().toISOString(),
            message_count: (node.message_count || 0) + 1
          };
        }
        return node;
      });
      
      // Also update metrics when nodes change
      setTimeout(() => updateMetrics(updatedNodes), 100);
      
      return updatedNodes;
    });

    // Update total message counter
    setMetrics(prevMetrics => ({
      ...prevMetrics,
      totalMessages: prevMetrics.totalMessages + 1,
      messagesPerMinute: prevMetrics.messagesPerMinute + 1
    }));
  };

  const handleNodeStatusUpdate = (data) => {
    console.log('🔄 Received node status update:', data);
    setNodes(prevNodes => {
      const updatedNodes = prevNodes.map(node => {
        if (node.node_id === data.node_id) {
          return { ...node, ...data };
        }
        return node;
      });
      
      // Update metrics when node status changes
      setTimeout(() => updateMetrics(updatedNodes), 100);
      
      return updatedNodes;
    });
  };

  const handleSystemHealthUpdate = (data) => {
    console.log('Received system health update:', data);
    setSystemHealth({
      cpu: data.cpu_usage || 0,
      memory: data.memory_usage || 0,
      disk: data.disk_usage || 0,
      network: data.network_usage || 0
    });
  };

  const updateMetrics = (nodeList) => {
    console.log('📊 Updating metrics with nodes:', nodeList?.length || 0);
    
    if (!nodeList || !Array.isArray(nodeList)) {
      console.warn('⚠️ Invalid node list for metrics update:', nodeList);
      return;
    }

    const now = new Date();
    const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000);
    
    const onlineNodes = nodeList.filter(node => 
      node.last_seen && new Date(node.last_seen) > fiveMinutesAgo
    );
    
    console.log(`📈 Node stats: Total: ${nodeList.length}, Online: ${onlineNodes.length}`);
    
    // Calculate averages from recent sensor data (last 20 points)
    const recentData = sensorData.slice(-20);
    const totalTemperature = recentData.reduce((sum, data) => sum + (data.temperature || 0), 0);
    const totalHumidity = recentData.reduce((sum, data) => sum + (data.humidity || 0), 0);
    const totalHumidityMQ = recentData.reduce((sum, data) => sum + (data.humidity_mq || 0), 0);
    const totalGasSensor = recentData.reduce((sum, data) => sum + (data.gas_sensor || 0), 0);
    const totalWifiRssi = recentData.reduce((sum, data) => sum + (data.wifi_rssi || 0), 0);
    
    const averageTemperature = recentData.length > 0 ? totalTemperature / recentData.length : 0;
    const averageHumidity = recentData.length > 0 ? totalHumidity / recentData.length : 0;
    const averageHumidityMQ = recentData.length > 0 ? totalHumidityMQ / recentData.length : 0;
    const averageGasSensor = recentData.length > 0 ? totalGasSensor / recentData.length : 0;
    const averageWifiRssi = recentData.length > 0 ? totalWifiRssi / recentData.length : 0;
    
    // Get the most recent servo angle
    const currentServoAngle = recentData.length > 0 ? recentData[recentData.length - 1].servo_angle || 0 : 0;

    const newMetrics = {
      totalNodes: nodeList.length,
      onlineNodes: onlineNodes.length,
      offlineNodes: nodeList.length - onlineNodes.length,
      averageTemperature: averageTemperature.toFixed(1),
      averageHumidity: averageHumidity.toFixed(1),
      averageHumidityMQ: averageHumidityMQ.toFixed(1),
      averageGasSensor: averageGasSensor.toFixed(0),
      currentServoAngle: currentServoAngle,
      averageWifiRssi: averageWifiRssi.toFixed(0),
      totalMessages: 0, // We'll increment this in real-time
      messagesPerMinute: 0,
    };

    console.log('📊 New metrics calculated:', newMetrics);

    setMetrics(prevMetrics => ({
      ...prevMetrics,
      ...newMetrics
    }));
  };

  const updateSystemHealth = () => {
    // Simulate system health data - in production, this would come from your backend
    setSystemHealth({
      cpu: Math.random() * 100,
      memory: Math.random() * 100,
      disk: Math.random() * 100,
      network: Math.random() * 100
    });
  };

  const toggleRealtime = () => {
    setRealtimeEnabled(!realtimeEnabled);
  };

  const refreshData = () => {
    loadNodes();
    updateSystemHealth();
  };

  const getNodeStatus = (lastSeen) => {
    if (!lastSeen) return 'offline';
    const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
    return new Date(lastSeen) > fiveMinutesAgo ? 'online' : 'offline';
  };

  const recentNodesColumns = [
    {
      title: 'Node ID',
      dataIndex: 'node_id',
      key: 'node_id',
      width: 150,
      render: (nodeId) => (
        <span style={{ fontFamily: 'monospace' }}>{nodeId}</span>
      ),
    },
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (name) => name || 'Unnamed Device',
    },
    {
      title: 'Status',
      dataIndex: 'last_seen',
      key: 'status',
      width: 100,
      render: (lastSeen) => {
        const status = getNodeStatus(lastSeen);
        return (
          <Badge 
            status={status === 'online' ? 'success' : 'error'} 
            text={status === 'online' ? 'Online' : 'Offline'} 
          />
        );
      },
    },
    {
      title: 'Messages',
      dataIndex: 'message_count',
      key: 'message_count',
      width: 100,
      render: (count) => count || 0,
    },
    {
      title: 'Last Seen',
      dataIndex: 'last_seen',
      key: 'last_seen',
      width: 120,
      render: (lastSeen) => lastSeen ? moment(lastSeen).fromNow() : 'Never',
    },
  ];

  // Data for charts
  const nodeStatusData = [
    { name: 'Online', value: metrics.onlineNodes, color: '#52c41a' },
    { name: 'Offline', value: metrics.offlineNodes, color: '#ff4d4f' }
  ];

  const systemHealthData = [
    { name: 'CPU', value: systemHealth.cpu },
    { name: 'Memory', value: systemHealth.memory },
    { name: 'Disk', value: systemHealth.disk },
    { name: 'Network', value: systemHealth.network }
  ];

  return (
    <div>
      {/* Real-time Status Bar */}
      <Card style={{ marginBottom: 16 }}>
        <Row align="middle" justify="space-between">
          <Col>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                {wsConnected ? (
                  <WifiOutlined style={{ color: '#52c41a', fontSize: 16 }} />
                ) : (
                  <DisconnectOutlined style={{ color: '#ff4d4f', fontSize: 16 }} />
                )}
                <span>
                  {wsConnected ? 'Real-time Connected' : 'Real-time Disconnected'}
                </span>
              </div>
              {lastUpdate && (
                <div style={{ fontSize: 12, color: '#666' }}>
                  Last Update: {moment(lastUpdate).format('HH:mm:ss')}
                </div>
              )}
            </div>
          </Col>
          <Col>
            <div style={{ display: 'flex', gap: 8 }}>
              <Button
                type={realtimeEnabled ? 'primary' : 'default'}
                icon={<EyeOutlined />}
                onClick={toggleRealtime}
                size="small"
              >
                Real-time {realtimeEnabled ? 'ON' : 'OFF'}
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={refreshData}
                size="small"
              >
                Refresh
              </Button>
            </div>
          </Col>
        </Row>
      </Card>

      {/* Main Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Nodes"
              value={metrics.totalNodes}
              prefix={<SettingOutlined />}
              valueStyle={{ color: '#1677ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Online Nodes"
              value={metrics.onlineNodes}
              prefix={<WifiOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Avg Temperature"
              value={metrics.averageTemperature}
              suffix="°C"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Avg Humidity"
              value={metrics.averageHumidity}
              suffix="%"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Additional Sensor Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="MQ Humidity"
              value={metrics.averageHumidityMQ}
              suffix="%"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#13c2c2' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Gas Sensor"
              value={metrics.averageGasSensor}
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#ff7300' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Servo Angle"
              value={metrics.currentServoAngle}
              suffix="°"
              prefix={<SettingOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="WiFi Signal"
              value={metrics.averageWifiRssi}
              suffix="dBm"
              prefix={<WifiOutlined />}
              valueStyle={{ color: '#fa541c' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Messages"
              value={metrics.totalMessages}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Device States */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24}>
          <Card title="🎯 Device Control States" size="small">
            <Row gutter={[16, 16]}>
              <Col xs={12} sm={6} md={4}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', marginBottom: '8px' }}>
                    {sensorData.length > 0 && sensorData[sensorData.length - 1]?.light_state ? '💡' : '🔴'}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>Light</div>
                  <div style={{ fontSize: '14px', fontWeight: 'bold' }}>
                    {sensorData.length > 0 && sensorData[sensorData.length - 1]?.light_state ? 'ON' : 'OFF'}
                  </div>
                </div>
              </Col>
              <Col xs={12} sm={6} md={4}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', marginBottom: '8px' }}>
                    {sensorData.length > 0 && sensorData[sensorData.length - 1]?.fan_state ? '🌀' : '🔴'}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>Fan</div>
                  <div style={{ fontSize: '14px', fontWeight: 'bold' }}>
                    {sensorData.length > 0 && sensorData[sensorData.length - 1]?.fan_state ? 'ON' : 'OFF'}
                  </div>
                </div>
              </Col>
              <Col xs={12} sm={6} md={4}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', marginBottom: '8px' }}>
                    {sensorData.length > 0 && sensorData[sensorData.length - 1]?.relay3_state ? '🔌' : '🔴'}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>Relay 3</div>
                  <div style={{ fontSize: '14px', fontWeight: 'bold' }}>
                    {sensorData.length > 0 && sensorData[sensorData.length - 1]?.relay3_state ? 'ON' : 'OFF'}
                  </div>
                </div>
              </Col>
              <Col xs={12} sm={6} md={4}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', marginBottom: '8px' }}>
                    {sensorData.length > 0 && sensorData[sensorData.length - 1]?.relay4_state ? '🔌' : '🔴'}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>Relay 4</div>
                  <div style={{ fontSize: '14px', fontWeight: 'bold' }}>
                    {sensorData.length > 0 && sensorData[sensorData.length - 1]?.relay4_state ? 'ON' : 'OFF'}
                  </div>
                </div>
              </Col>
              <Col xs={12} sm={6} md={4}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', marginBottom: '8px' }}>
                    {sensorData.length > 0 && sensorData[sensorData.length - 1]?.real_model_state ? '🎯' : '🔴'}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>Real Model</div>
                  <div style={{ fontSize: '14px', fontWeight: 'bold' }}>
                    {sensorData.length > 0 && sensorData[sensorData.length - 1]?.real_model_state ? 'ON' : 'OFF'}
                  </div>
                </div>
              </Col>
              <Col xs={12} sm={6} md={4}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', marginBottom: '8px' }}>
                    {sensorData.length > 0 && sensorData[sensorData.length - 1]?.smart_mode ? '🤖' : '🔴'}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>Smart Mode</div>
                  <div style={{ fontSize: '14px', fontWeight: 'bold' }}>
                    {sensorData.length > 0 && sensorData[sensorData.length - 1]?.smart_mode ? 'ON' : 'OFF'}
                  </div>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* System Health */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24}>
          <Card title="System Health" size="small">
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={6}>
                <div>
                  <div style={{ marginBottom: 8 }}>CPU Usage</div>
                  <Progress 
                    percent={Math.round(systemHealth.cpu)} 
                    status={systemHealth.cpu > 80 ? 'exception' : 'active'}
                    size="small"
                  />
                </div>
              </Col>
              <Col xs={24} sm={6}>
                <div>
                  <div style={{ marginBottom: 8 }}>Memory Usage</div>
                  <Progress 
                    percent={Math.round(systemHealth.memory)} 
                    status={systemHealth.memory > 80 ? 'exception' : 'active'}
                    size="small"
                  />
                </div>
              </Col>
              <Col xs={24} sm={6}>
                <div>
                  <div style={{ marginBottom: 8 }}>Disk Usage</div>
                  <Progress 
                    percent={Math.round(systemHealth.disk)} 
                    status={systemHealth.disk > 90 ? 'exception' : 'active'}
                    size="small"
                  />
                </div>
              </Col>
              <Col xs={24} sm={6}>
                <div>
                  <div style={{ marginBottom: 8 }}>Network Usage</div>
                  <Progress 
                    percent={Math.round(systemHealth.network)} 
                    status={systemHealth.network > 90 ? 'exception' : 'active'}
                    size="small"
                  />
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* Charts Section */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="Temperature Trends (Real-time)" style={{ height: 400 }}>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={sensorData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="temperature" 
                  stroke="#1677ff" 
                  strokeWidth={2} 
                  dot={false}
                  connectNulls={false}
                  animationDuration={600}
                  animationEasing="ease-out"
                  animationBegin={0}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        
        <Col xs={24} lg={12}>
          <Card title="Humidity Trends (Real-time)" style={{ height: 400 }}>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={sensorData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Area 
                  type="monotone" 
                  dataKey="humidity" 
                  stroke="#52c41a" 
                  fill="#52c41a" 
                  fillOpacity={0.3}
                  animationDuration={800}
                  animationEasing="ease-in-out"
                  animationBegin={100}
                  name="Simulated Humidity (%)"
                />
                <Area 
                  type="monotone" 
                  dataKey="humidity_mq" 
                  stroke="#13c2c2" 
                  fill="#13c2c2" 
                  fillOpacity={0.2}
                  animationDuration={800}
                  animationEasing="ease-in-out"
                  animationBegin={200}
                  name="MQ Humidity (%)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Gas Sensor and Servo Charts */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="Gas Sensor Readings (Real-time)" style={{ height: 400 }}>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={sensorData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="gas_sensor" 
                  stroke="#ff7300" 
                  strokeWidth={2} 
                  dot={false}
                  connectNulls={false}
                  animationDuration={500}
                  animationEasing="ease-out"
                  animationBegin={0}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        
        <Col xs={24} lg={12}>
          <Card title="Servo Angle & WiFi Signal" style={{ height: 400 }}>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={sensorData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Line 
                  yAxisId="left"
                  type="monotone" 
                  dataKey="servo_angle" 
                  stroke="#722ed1" 
                  strokeWidth={2} 
                  dot={false}
                  name="Servo Angle (°)"
                  animationDuration={700}
                  animationEasing="ease-in-out"
                  animationBegin={0}
                />
                <Line 
                  yAxisId="right"
                  type="monotone" 
                  dataKey="wifi_rssi" 
                  stroke="#fa541c" 
                  strokeWidth={2} 
                  dot={false}
                  name="WiFi RSSI (dBm)"
                  animationDuration={700}
                  animationEasing="ease-in-out"
                  animationBegin={150}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Additional Charts */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} md={12}>
          <Card title="Node Status Distribution" style={{ height: 300 }}>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={nodeStatusData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                  label={(entry) => `${entry.name}: ${entry.value}`}
                >
                  {nodeStatusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        <Col xs={24} md={12}>
          <Card title="System Resource Usage" style={{ height: 300 }}>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={systemHealthData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(value) => [`${value.toFixed(1)}%`, 'Usage']} />
                <Bar 
                  dataKey="value" 
                  fill="#1677ff"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Node Activity Table */}
      <Row gutter={[16, 16]}>
        <Col xs={24}>
          <Card 
            title="Real-time Node Activity" 
            extra={
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Badge 
                  status={realtimeEnabled ? 'processing' : 'default'} 
                  text={realtimeEnabled ? 'Live' : 'Paused'} 
                />
                {sensorData.length > 0 && (
                  <span style={{ fontSize: 12, color: '#666' }}>
                    {sensorData.length} data points
                  </span>
                )}
              </div>
            }
          >
            {!wsConnected && (
              <Alert
                message="Real-time connection lost"
                description="Attempting to reconnect to WebSocket server..."
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}
            
            <Table
              columns={recentNodesColumns}
              dataSource={nodes}
              rowKey="id"
              loading={loading}
              pagination={{ 
                pageSize: 10,
                showTotal: (total, range) => 
                  `${range[0]}-${range[1]} of ${total} nodes`
              }}
              scroll={{ x: 600 }}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
