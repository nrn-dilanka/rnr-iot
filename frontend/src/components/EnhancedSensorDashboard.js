import React, { useState, useEffect } from 'react';
import { 
  Row, 
  Col, 
  Card, 
  Statistic, 
  Alert, 
  Button, 
  Tag, 
  Space,
  Divider,
  Typography,
  Descriptions,
  Progress
} from 'antd';
import {
  FireOutlined,
  CloudOutlined,
  ExperimentOutlined,
  RadarChartOutlined,
  SettingOutlined,
  WifiOutlined,
  ReloadOutlined,
  AlertOutlined
} from '@ant-design/icons';
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
  ComposedChart,
  Bar,
  Cell,
  PieChart,
  Pie
} from 'recharts';
import { sensorDataAPI } from '../services/api';
import WebSocketService from '../services/WebSocketService';
import moment from 'moment';

const { Title, Text } = Typography;

const EnhancedSensorDashboard = () => {
  const [sensorData, setSensorData] = useState([]);
  const [currentReadings, setCurrentReadings] = useState({});
  const [sensorStats, setSensorStats] = useState({});
  const [loading, setLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [activeNodes, setActiveNodes] = useState([]);

  useEffect(() => {
    loadSensorData();
    initializeWebSocket();

    const interval = setInterval(() => {
      calculateSensorStats();
    }, 5000);

    return () => {
      clearInterval(interval);
      const wsService = WebSocketService.getInstance();
      wsService.unsubscribe('sensor_data', handleRealtimeUpdate);
    };
  }, []);

  const initializeWebSocket = () => {
    const wsService = WebSocketService.getInstance();
    
    wsService.connect(
      () => setWsConnected(true),
      () => setWsConnected(false),
      (error) => console.error('Enhanced Dashboard WebSocket error:', error)
    );

    wsService.subscribe('sensor_data', handleRealtimeUpdate);
  };

  const loadSensorData = async () => {
    try {
      setLoading(true);
      const response = await sensorDataAPI.getSensorData(200);
      const rawData = response.data || [];
      
      const transformedData = rawData.map(item => ({
        id: item.id,
        nodeId: item.node_id,
        timestamp: item.received_at,
        time: moment(item.received_at).format('HH:mm:ss'),
        temperature: item.data?.temperature || 0,
        humidity: item.data?.humidity || 0,
        humidity_mq: item.data?.humidity_mq || 0,
        humidity_mq_raw: item.data?.humidity_mq_raw || 0,
        gas_sensor: item.data?.gas_sensor || 0,
        servo_angle: item.data?.servo_angle || 0,
        wifi_rssi: item.data?.wifi_rssi || 0,
        uptime: item.data?.uptime || 0,
        light_state: item.data?.light_state || false,
        fan_state: item.data?.fan_state || false,
        smart_mode: item.data?.smart_mode || false
      })).reverse();

      setSensorData(transformedData);
      
      // Get unique nodes
      const nodes = [...new Set(transformedData.map(d => d.nodeId))];
      setActiveNodes(nodes);
      
      // Set current readings (latest for each node)
      const latestReadings = {};
      nodes.forEach(nodeId => {
        const nodeData = transformedData.filter(d => d.nodeId === nodeId);
        if (nodeData.length > 0) {
          latestReadings[nodeId] = nodeData[nodeData.length - 1];
        }
      });
      setCurrentReadings(latestReadings);
      
      calculateSensorStats(transformedData);
      
    } catch (error) {
      console.error('Error loading enhanced sensor data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRealtimeUpdate = (data) => {
    const newReading = {
      nodeId: data.node_id,
      timestamp: new Date().toISOString(),
      time: moment().format('HH:mm:ss'),
      temperature: data.data?.temperature || data.temperature || 0,
      humidity: data.data?.humidity || data.humidity || 0,
      humidity_mq: data.data?.humidity_mq || data.humidity_mq || 0,
      humidity_mq_raw: data.data?.humidity_mq_raw || data.humidity_mq_raw || 0,
      gas_sensor: data.data?.gas_sensor || data.gas_sensor || 0,
      servo_angle: data.data?.servo_angle || data.servo_angle || 0,
      wifi_rssi: data.data?.wifi_rssi || data.wifi_rssi || 0,
      uptime: data.data?.uptime || data.uptime || 0,
      light_state: data.data?.light_state || data.light_state || false,
      fan_state: data.data?.fan_state || data.fan_state || false,
      smart_mode: data.data?.smart_mode || data.smart_mode || false
    };

    setSensorData(prev => [...prev, newReading].slice(-200));
    
    setCurrentReadings(prev => ({
      ...prev,
      [data.node_id]: newReading
    }));
  };

  const calculateSensorStats = (data = sensorData) => {
    if (!data.length) return;

    // Calculate overall averages
    const totalReadings = data.length;
    const stats = {
      avgTemperature: (data.reduce((sum, d) => sum + d.temperature, 0) / totalReadings).toFixed(1),
      avgHumidity: (data.reduce((sum, d) => sum + d.humidity, 0) / totalReadings).toFixed(1),
      avgHumidityMQ: (data.reduce((sum, d) => sum + d.humidity_mq, 0) / totalReadings).toFixed(1),
      avgGasSensor: (data.reduce((sum, d) => sum + d.gas_sensor, 0) / totalReadings).toFixed(0),
      avgWifiRssi: (data.reduce((sum, d) => sum + d.wifi_rssi, 0) / totalReadings).toFixed(0),
      maxTemperature: Math.max(...data.map(d => d.temperature)).toFixed(1),
      minTemperature: Math.min(...data.map(d => d.temperature)).toFixed(1),
      maxGasSensor: Math.max(...data.map(d => d.gas_sensor)),
      totalDataPoints: totalReadings,
      activeNodesCount: activeNodes.length
    };

    setSensorStats(stats);
  };

  const getSensorAlerts = () => {
    const alerts = [];
    
    Object.values(currentReadings).forEach(reading => {
      if (reading.temperature > 35) {
        alerts.push({
          type: 'warning',
          message: `High temperature detected on ${reading.nodeId}: ${reading.temperature}°C`
        });
      }
      
      if (reading.gas_sensor > 100) {
        alerts.push({
          type: 'error',
          message: `High gas level on ${reading.nodeId}: ${reading.gas_sensor}`
        });
      }
      
      if (reading.wifi_rssi < -80) {
        alerts.push({
          type: 'warning',
          message: `Weak WiFi signal on ${reading.nodeId}: ${reading.wifi_rssi} dBm`
        });
      }
    });
    
    return alerts;
  };

  const getNodeStatusData = () => {
    const now = new Date();
    const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000);
    
    const online = Object.values(currentReadings).filter(reading => 
      new Date(reading.timestamp) > fiveMinutesAgo
    ).length;
    
    const offline = activeNodes.length - online;
    
    return [
      { name: 'Online', value: online, color: '#52c41a' },
      { name: 'Offline', value: offline, color: '#ff4d4f' }
    ];
  };

  const alerts = getSensorAlerts();
  const nodeStatusData = getNodeStatusData();

  return (
    <div>
      <Title level={2}>Enhanced Sensor Dashboard</Title>
      
      {/* Status Header */}
      <Card style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <Tag color={wsConnected ? 'green' : 'red'}>
                {wsConnected ? 'Live Data Connected' : 'Disconnected'}
              </Tag>
              <Text>Active Nodes: {activeNodes.length}</Text>
              <Text>Data Points: {sensorStats.totalDataPoints || 0}</Text>
            </Space>
          </Col>
          <Col>
            <Button icon={<ReloadOutlined />} onClick={loadSensorData} loading={loading}>
              Refresh Data
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Alerts */}
      {alerts.length > 0 && (
        <Row style={{ marginBottom: 16 }}>
          <Col span={24}>
            {alerts.map((alert, index) => (
              <Alert
                key={index}
                message={alert.message}
                type={alert.type}
                showIcon
                style={{ marginBottom: 8 }}
                closable
              />
            ))}
          </Col>
        </Row>
      )}

      {/* Overall Statistics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Average Temperature"
              value={sensorStats.avgTemperature || 0}
              suffix="°C"
              prefix={<FireOutlined />}
              valueStyle={{ color: '#1677ff' }}
            />
            <Text type="secondary">
              Range: {sensorStats.minTemperature}°C - {sensorStats.maxTemperature}°C
            </Text>
          </Card>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Average Humidity"
              value={sensorStats.avgHumidity || 0}
              suffix="%"
              prefix={<CloudOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
            <Text type="secondary">Simulated Sensor</Text>
          </Card>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="MQ Humidity Average"
              value={sensorStats.avgHumidityMQ || 0}
              suffix="%"
              prefix={<ExperimentOutlined />}
              valueStyle={{ color: '#13c2c2' }}
            />
            <Text type="secondary">Hardware Sensor</Text>
          </Card>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Average Gas Level"
              value={sensorStats.avgGasSensor || 0}
              prefix={<RadarChartOutlined />}
              valueStyle={{ color: '#ff7300' }}
            />
            <Text type="secondary">Max: {sensorStats.maxGasSensor || 0}</Text>
          </Card>
        </Col>
      </Row>

      {/* Current Node Status */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {Object.entries(currentReadings).map(([nodeId, reading]) => (
          <Col xs={24} md={12} lg={8} key={nodeId}>
            <Card 
              title={`Node: ${nodeId.substring(0, 8)}...`}
              size="small"
              extra={<Tag color="blue">Live</Tag>}
            >
              <Row gutter={[8, 8]}>
                <Col span={12}>
                  <Statistic
                    title="Temp"
                    value={reading.temperature}
                    suffix="°C"
                    precision={1}
                    valueStyle={{ fontSize: 16 }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Gas"
                    value={reading.gas_sensor}
                    valueStyle={{ fontSize: 16 }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Humidity"
                    value={reading.humidity}
                    suffix="%"
                    precision={1}
                    valueStyle={{ fontSize: 16 }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="MQ Humid"
                    value={reading.humidity_mq}
                    suffix="%"
                    precision={1}
                    valueStyle={{ fontSize: 16 }}
                  />
                </Col>
              </Row>
              
              <Divider style={{ margin: '8px 0' }} />
              
              <Space>
                <Tag color={reading.light_state ? 'green' : 'default'}>
                  💡 {reading.light_state ? 'ON' : 'OFF'}
                </Tag>
                <Tag color={reading.fan_state ? 'blue' : 'default'}>
                  🌀 {reading.fan_state ? 'ON' : 'OFF'}
                </Tag>
                <Tag color={reading.smart_mode ? 'purple' : 'default'}>
                  🤖 {reading.smart_mode ? 'AUTO' : 'MANUAL'}
                </Tag>
              </Space>
            </Card>
          </Col>
        ))}
      </Row>

      {/* Charts Section */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="Real-time Sensor Trends" style={{ height: 400 }}>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={sensorData.slice(-50)}>
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
                  name="Temperature (°C)"
                />
                <Line
                  type="monotone"
                  dataKey="humidity"
                  stroke="#52c41a"
                  strokeWidth={2}
                  dot={false}
                  name="Humidity (%)"
                />
                <Line
                  type="monotone"
                  dataKey="humidity_mq"
                  stroke="#13c2c2"
                  strokeWidth={2}
                  dot={false}
                  name="MQ Humidity (%)"
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="Gas Sensor & Device Status" style={{ height: 400 }}>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={sensorData.slice(-50)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis yAxisId="gas" />
                <YAxis yAxisId="servo" orientation="right" />
                <Tooltip />
                <Bar
                  yAxisId="gas"
                  dataKey="gas_sensor"
                  fill="#ff7300"
                  fillOpacity={0.7}
                  name="Gas Sensor"
                />
                <Line
                  yAxisId="servo"
                  type="monotone"
                  dataKey="servo_angle"
                  stroke="#722ed1"
                  strokeWidth={2}
                  dot={false}
                  name="Servo Angle (°)"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Node Status Distribution */}
      <Row gutter={[16, 16]}>
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
          <Card title="System Overview" style={{ height: 300 }}>
            <Descriptions column={1} size="small">
              <Descriptions.Item label="Total Active Nodes">
                {activeNodes.length}
              </Descriptions.Item>
              <Descriptions.Item label="Total Data Points">
                {sensorStats.totalDataPoints}
              </Descriptions.Item>
              <Descriptions.Item label="Average Temperature Range">
                {sensorStats.minTemperature}°C - {sensorStats.maxTemperature}°C
              </Descriptions.Item>
              <Descriptions.Item label="Average WiFi Signal">
                {sensorStats.avgWifiRssi} dBm
              </Descriptions.Item>
              <Descriptions.Item label="Connection Status">
                <Tag color={wsConnected ? 'green' : 'red'}>
                  {wsConnected ? 'Connected' : 'Disconnected'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Active Alerts">
                <Tag color={alerts.length > 0 ? 'orange' : 'green'}>
                  {alerts.length} Alert{alerts.length !== 1 ? 's' : ''}
                </Tag>
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default EnhancedSensorDashboard;
