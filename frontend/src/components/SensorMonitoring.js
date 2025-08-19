import React, { useState, useEffect } from 'react';
import { 
  Row, 
  Col, 
  Card, 
  Statistic, 
  Progress, 
  Alert, 
  Badge, 
  Descriptions,
  Button,
  Divider,
  Tag,
  Space,
  Switch
} from 'antd';
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
  Bar
} from 'recharts';
import {
  FireOutlined,
  CloudOutlined,
  ExperimentOutlined,
  RadarChartOutlined,
  WifiOutlined,
  SettingOutlined,
  AlertOutlined,
  EyeOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { sensorDataAPI } from '../services/api';
import WebSocketService from '../services/WebSocketService';
import moment from 'moment';

const SensorMonitoring = ({ nodeId }) => {
  const [sensorData, setSensorData] = useState([]);
  const [currentReadings, setCurrentReadings] = useState({
    temperature: 0,
    humidity: 0,
    humidity_mq: 0,
    humidity_mq_raw: 0,
    gas_sensor: 0,
    servo_angle: 0,
    wifi_rssi: 0,
    uptime: 0
  });
  const [alerts, setAlerts] = useState([]);
  const [realTimeEnabled, setRealTimeEnabled] = useState(true);
  const [loading, setLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);

  // Sensor thresholds for alerts
  const thresholds = {
    temperature: { min: 10, max: 40 },
    humidity: { min: 20, max: 80 },
    humidity_mq: { min: 20, max: 80 },
    gas_sensor: { min: 0, max: 100 }, // Adjust based on your sensor
    wifi_rssi: { min: -80, max: -30 }
  };

  useEffect(() => {
    loadSensorData();
    if (realTimeEnabled) {
      initializeWebSocket();
    }

    const interval = setInterval(() => {
      if (realTimeEnabled) {
        checkAlerts();
      }
    }, 5000);

    return () => {
      clearInterval(interval);
      const wsService = WebSocketService.getInstance();
      wsService.unsubscribe('sensor_data', handleSensorUpdate);
    };
  }, [nodeId, realTimeEnabled]);

  const initializeWebSocket = () => {
    const wsService = WebSocketService.getInstance();
    
    wsService.connect(
      () => setWsConnected(true),
      () => setWsConnected(false),
      (error) => console.error('Sensor WebSocket error:', error)
    );

    wsService.subscribe('sensor_data', handleSensorUpdate);
  };

  const loadSensorData = async () => {
    try {
      setLoading(true);
      const response = await sensorDataAPI.getSensorData(100);
      const rawData = response.data;
      
      // Filter by nodeId if specified
      const filteredData = nodeId 
        ? rawData.filter(item => item.node_id === nodeId)
        : rawData;

      const transformedData = filteredData.map(item => ({
        time: moment(item.received_at).format('HH:mm:ss'),
        timestamp: item.received_at,
        temperature: item.data.temperature || 0,
        humidity: item.data.humidity || 0,
        humidity_mq: item.data.humidity_mq || 0,
        humidity_mq_raw: item.data.humidity_mq_raw || 0,
        gas_sensor: item.data.gas_sensor || 0,
        servo_angle: item.data.servo_angle || 0,
        wifi_rssi: item.data.wifi_rssi || 0,
        uptime: item.data.uptime || 0,
        nodeId: item.node_id
      })).reverse();
      
      setSensorData(transformedData);
      
      // Set current readings from latest data
      if (transformedData.length > 0) {
        const latest = transformedData[transformedData.length - 1];
        setCurrentReadings({
          temperature: latest.temperature,
          humidity: latest.humidity,
          humidity_mq: latest.humidity_mq,
          humidity_mq_raw: latest.humidity_mq_raw,
          gas_sensor: latest.gas_sensor,
          servo_angle: latest.servo_angle,
          wifi_rssi: latest.wifi_rssi,
          uptime: latest.uptime
        });
      }
      
    } catch (error) {
      console.error('Error loading sensor data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSensorUpdate = (data) => {
    if (nodeId && data.node_id !== nodeId) return;

    const newReading = {
      time: moment().format('HH:mm:ss'),
      timestamp: new Date().toISOString(),
      temperature: data.data?.temperature || data.temperature || 0,
      humidity: data.data?.humidity || data.humidity || 0,
      humidity_mq: data.data?.humidity_mq || data.humidity_mq || 0,
      humidity_mq_raw: data.data?.humidity_mq_raw || data.humidity_mq_raw || 0,
      gas_sensor: data.data?.gas_sensor || data.gas_sensor || 0,
      servo_angle: data.data?.servo_angle || data.servo_angle || 0,
      wifi_rssi: data.data?.wifi_rssi || data.wifi_rssi || 0,
      uptime: data.data?.uptime || data.uptime || 0,
      nodeId: data.node_id
    };

    setSensorData(prevData => [...prevData, newReading].slice(-100));
    setCurrentReadings({
      temperature: newReading.temperature,
      humidity: newReading.humidity,
      humidity_mq: newReading.humidity_mq,
      humidity_mq_raw: newReading.humidity_mq_raw,
      gas_sensor: newReading.gas_sensor,
      servo_angle: newReading.servo_angle,
      wifi_rssi: newReading.wifi_rssi,
      uptime: newReading.uptime
    });
  };

  const checkAlerts = () => {
    const newAlerts = [];
    
    // Temperature alert
    if (currentReadings.temperature < thresholds.temperature.min || 
        currentReadings.temperature > thresholds.temperature.max) {
      newAlerts.push({
        type: 'warning',
        message: `Temperature out of range: ${currentReadings.temperature}°C`,
        sensor: 'temperature'
      });
    }

    // Gas sensor alert
    if (currentReadings.gas_sensor > thresholds.gas_sensor.max) {
      newAlerts.push({
        type: 'error',
        message: `High gas level detected: ${currentReadings.gas_sensor}`,
        sensor: 'gas'
      });
    }

    // WiFi signal alert
    if (currentReadings.wifi_rssi < thresholds.wifi_rssi.min) {
      newAlerts.push({
        type: 'warning',
        message: `Weak WiFi signal: ${currentReadings.wifi_rssi} dBm`,
        sensor: 'wifi'
      });
    }

    setAlerts(newAlerts);
  };

  const getSensorStatus = (value, sensor) => {
    const threshold = thresholds[sensor];
    if (!threshold) return 'normal';
    
    if (value < threshold.min || value > threshold.max) {
      return 'warning';
    }
    return 'normal';
  };

  const getSignalStrength = (rssi) => {
    if (rssi > -50) return { text: 'Excellent', color: '#52c41a' };
    if (rssi > -60) return { text: 'Good', color: '#1890ff' };
    if (rssi > -70) return { text: 'Fair', color: '#fa8c16' };
    return { text: 'Poor', color: '#ff4d4f' };
  };

  return (
    <div>
      {/* Header with controls */}
      <Card style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <Badge 
                status={wsConnected ? 'processing' : 'error'} 
                text={wsConnected ? 'Live Data' : 'Disconnected'} 
              />
              {nodeId && <Tag color="blue">Node: {nodeId}</Tag>}
            </Space>
          </Col>
          <Col>
            <Space>
              <span>Real-time:</span>
              <Switch 
                checked={realTimeEnabled} 
                onChange={setRealTimeEnabled}
                size="small"
              />
              <Button 
                icon={<ReloadOutlined />} 
                onClick={loadSensorData}
                size="small"
              >
                Refresh
              </Button>
            </Space>
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
                action={
                  <Button size="small" type="text">
                    Dismiss
                  </Button>
                }
              />
            ))}
          </Col>
        </Row>
      )}

      {/* Current Sensor Readings */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={8} lg={6}>
          <Card>
            <Statistic
              title="Temperature"
              value={currentReadings.temperature}
              suffix="°C"
              prefix={<FireOutlined />}
              valueStyle={{ 
                color: getSensorStatus(currentReadings.temperature, 'temperature') === 'warning' 
                  ? '#ff4d4f' : '#1677ff' 
              }}
            />
            <Progress 
              percent={Math.min((currentReadings.temperature / 50) * 100, 100)} 
              size="small" 
              showInfo={false}
              strokeColor={getSensorStatus(currentReadings.temperature, 'temperature') === 'warning' 
                ? '#ff4d4f' : '#1677ff'}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} md={8} lg={6}>
          <Card>
            <Statistic
              title="Humidity (Simulated)"
              value={currentReadings.humidity}
              suffix="%"
              prefix={<CloudOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
            <Progress 
              percent={currentReadings.humidity} 
              size="small" 
              showInfo={false}
              strokeColor="#52c41a"
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} md={8} lg={6}>
          <Card>
            <Statistic
              title="MQ Humidity Sensor"
              value={currentReadings.humidity_mq}
              suffix="%"
              prefix={<ExperimentOutlined />}
              valueStyle={{ color: '#13c2c2' }}
            />
            <Progress 
              percent={currentReadings.humidity_mq} 
              size="small" 
              showInfo={false}
              strokeColor="#13c2c2"
            />
            <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
              Raw: {currentReadings.humidity_mq_raw}
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} md={8} lg={6}>
          <Card>
            <Statistic
              title="Gas Sensor"
              value={currentReadings.gas_sensor}
              prefix={<RadarChartOutlined />}
              valueStyle={{ 
                color: getSensorStatus(currentReadings.gas_sensor, 'gas_sensor') === 'warning' 
                  ? '#ff4d4f' : '#ff7300'
              }}
            />
            <Progress 
              percent={Math.min((currentReadings.gas_sensor / 1000) * 100, 100)} 
              size="small" 
              showInfo={false}
              strokeColor={getSensorStatus(currentReadings.gas_sensor, 'gas_sensor') === 'warning' 
                ? '#ff4d4f' : '#ff7300'}
            />
          </Card>
        </Col>
      </Row>

      {/* Device Status */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12}>
          <Card title="Device Status" size="small">
            <Descriptions column={1} size="small">
              <Descriptions.Item label="Servo Angle">
                <Space>
                  <span>{currentReadings.servo_angle}°</span>
                  <Progress 
                    type="circle" 
                    percent={(currentReadings.servo_angle / 180) * 100} 
                    size={40}
                    format={() => `${currentReadings.servo_angle}°`}
                  />
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="WiFi Signal">
                <Space>
                  <span style={{ color: getSignalStrength(currentReadings.wifi_rssi).color }}>
                    {currentReadings.wifi_rssi} dBm
                  </span>
                  <Tag color={getSignalStrength(currentReadings.wifi_rssi).color}>
                    {getSignalStrength(currentReadings.wifi_rssi).text}
                  </Tag>
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="Uptime">
                {Math.floor(currentReadings.uptime / 1000)} seconds
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>

        <Col xs={24} sm={12}>
          <Card title="Sensor Health" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Badge 
                  status={getSensorStatus(currentReadings.temperature, 'temperature') === 'normal' ? 'success' : 'error'}
                  text={`Temperature: ${getSensorStatus(currentReadings.temperature, 'temperature')}`}
                />
              </div>
              <div>
                <Badge 
                  status={getSensorStatus(currentReadings.gas_sensor, 'gas_sensor') === 'normal' ? 'success' : 'error'}
                  text={`Gas Sensor: ${getSensorStatus(currentReadings.gas_sensor, 'gas_sensor')}`}
                />
              </div>
              <div>
                <Badge 
                  status={getSensorStatus(currentReadings.wifi_rssi, 'wifi_rssi') === 'normal' ? 'success' : 'error'}
                  text={`WiFi Signal: ${getSensorStatus(currentReadings.wifi_rssi, 'wifi_rssi')}`}
                />
              </div>
              <div>
                <Badge 
                  status="processing"
                  text={`Data Points: ${sensorData.length}`}
                />
              </div>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Detailed Charts */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="Temperature & Humidity Trends" style={{ height: 400 }}>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={sensorData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis yAxisId="temp" />
                <YAxis yAxisId="humidity" orientation="right" />
                <Tooltip />
                <Area
                  yAxisId="humidity"
                  type="monotone"
                  dataKey="humidity"
                  fill="#52c41a"
                  stroke="#52c41a"
                  fillOpacity={0.3}
                  name="Simulated Humidity (%)"
                />
                <Area
                  yAxisId="humidity"
                  type="monotone"
                  dataKey="humidity_mq"
                  fill="#13c2c2"
                  stroke="#13c2c2"
                  fillOpacity={0.2}
                  name="MQ Humidity (%)"
                />
                <Line
                  yAxisId="temp"
                  type="monotone"
                  dataKey="temperature"
                  stroke="#1677ff"
                  strokeWidth={2}
                  dot={false}
                  name="Temperature (°C)"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="Gas Sensor & Device Monitoring" style={{ height: 400 }}>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={sensorData}>
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
    </div>
  );
};

export default SensorMonitoring;
