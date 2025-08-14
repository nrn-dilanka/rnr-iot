import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  message,
  Row,
  Col,
  Statistic,
  Progress,
  Switch,
  Typography,
  Alert,
  Badge,
  Tooltip,
  Divider
} from 'antd';
import {
  WifiOutlined,
  DisconnectOutlined,
  ReloadOutlined,
  ThunderboltOutlined,
  RobotOutlined,
  SignalFilled,
  FireOutlined,
  ExperimentOutlined,
  EyeOutlined,
  PauseCircleOutlined,
  PlayCircleOutlined
} from '@ant-design/icons';
import { nodeAPI } from '../services/api';
import WebSocketService from '../services/WebSocketService';
import moment from 'moment';

const { Title, Text } = Typography;

const RealtimeESP32Dashboard = () => {
  const [nodes, setNodes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [realtimeEnabled, setRealtimeEnabled] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [nodeStatus, setNodeStatus] = useState({});
  const [sensorData, setSensorData] = useState({});
  const [lastUpdate, setLastUpdate] = useState(null);
  const [messageCount, setMessageCount] = useState(0);
  const [dataRate, setDataRate] = useState(0);
  const messageCountRef = useRef(0);
  const lastRateUpdate = useRef(Date.now());

  // Load nodes data
  const loadNodes = async () => {
    setLoading(true);
    try {
      const data = await nodeAPI.getNodes();
      // Ensure data is always an array
      const nodesArray = Array.isArray(data) ? data : [];
      setNodes(nodesArray);
      message.success(`Loaded ${nodesArray.length} ESP32 devices`);
    } catch (error) {
      console.error('Error loading nodes:', error);
      message.error('Failed to load ESP32 devices');
      // Set to empty array on error
      setNodes([]);
    } finally {
      setLoading(false);
    }
  };

  // Initialize WebSocket connection
  useEffect(() => {
    if (realtimeEnabled) {
      initializeWebSocket();
    } else {
      disconnectWebSocket();
    }

    return () => {
      disconnectWebSocket();
    };
  }, [realtimeEnabled]);

  // Load initial data
  useEffect(() => {
    loadNodes();
  }, []);

  // Calculate data rate every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      const timeDiff = (now - lastRateUpdate.current) / 1000;
      const rate = Math.round(messageCountRef.current / timeDiff);
      setDataRate(rate);
      messageCountRef.current = 0;
      lastRateUpdate.current = now;
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const initializeWebSocket = () => {
    console.log('🔌 Initializing ESP32 Real-time WebSocket...');
    const wsService = WebSocketService.getInstance();
    
    wsService.connect(
      () => {
        console.log('✅ ESP32 Dashboard WebSocket connected');
        setWsConnected(true);
        message.success('Real-time updates connected');
      },
      () => {
        console.log('❌ ESP32 Dashboard WebSocket disconnected');
        setWsConnected(false);
        message.warning('Real-time updates disconnected');
      },
      (error) => {
        console.error('🚨 ESP32 Dashboard WebSocket error:', error);
        setWsConnected(false);
        message.error('Real-time connection error');
      }
    );

    // Subscribe to real-time events
    wsService.subscribe('sensor_data', handleSensorDataUpdate);
    wsService.subscribe('node_status', handleNodeStatusUpdate);
  };

  const disconnectWebSocket = () => {
    const wsService = WebSocketService.getInstance();
    wsService.unsubscribe('sensor_data', handleSensorDataUpdate);
    wsService.unsubscribe('node_status', handleNodeStatusUpdate);
    wsService.disconnect();
    setWsConnected(false);
  };

  const handleSensorDataUpdate = (data) => {
    if (data.type === 'sensor_data') {
      console.log('📡 Real-time ESP32 sensor data:', data.node_id);
      
      // Update node status to online
      setNodeStatus(prev => ({
        ...prev,
        [data.node_id]: 'online'
      }));

      // Store latest sensor data
      setSensorData(prev => ({
        ...prev,
        [data.node_id]: {
          ...data.data,
          received_at: new Date().toISOString()
        }
      }));

      setLastUpdate(new Date());
      messageCountRef.current++;
      setMessageCount(prev => prev + 1);
    }
  };

  const handleNodeStatusUpdate = (data) => {
    if (data.type === 'node_status') {
      console.log('🔄 Real-time ESP32 status update:', data);
      setNodeStatus(prev => ({
        ...prev,
        [data.node_id]: data.status
      }));
      setLastUpdate(new Date());
    }
  };

  // Get real-time status with fallback
  const getNodeStatus = (nodeId, lastSeen) => {
    // Check real-time status first
    if (nodeStatus[nodeId]) {
      return nodeStatus[nodeId];
    }
    
    // Fallback to timestamp-based detection
    if (!lastSeen) return 'offline';
    const now = moment();
    const lastSeenTime = moment(lastSeen);
    const minutesSinceLastSeen = now.diff(lastSeenTime, 'minutes');
    
    return minutesSinceLastSeen <= 2 ? 'online' : 'offline';
  };

  // Get signal strength indicator
  const getSignalStrength = (rssi) => {
    if (!rssi) return 0;
    if (rssi >= -30) return 100;
    if (rssi >= -50) return 75;
    if (rssi >= -70) return 50;
    if (rssi >= -90) return 25;
    return 10;
  };

  // Table columns
  const columns = [
    {
      title: 'Device Info',
      key: 'info',
      render: (_, record) => {
        const latestData = sensorData[record.node_id];
        const status = getNodeStatus(record.node_id, record.last_seen);
        
        return (
          <Space direction="vertical" size="small">
            <Space>
              <Badge 
                status={status === 'online' ? 'success' : 'error'} 
                text={
                  <Text strong style={{ color: status === 'online' ? '#52c41a' : '#ff4d4f' }}>
                    {record.name || 'Unnamed Device'}
                  </Text>
                }
              />
              {status === 'online' && <Tag color="green" icon={<ThunderboltOutlined />}>LIVE</Tag>}
            </Space>
            <Text type="secondary" style={{ fontSize: '12px' }}>{record.node_id}</Text>
            {latestData && (
              <Text type="secondary" style={{ fontSize: '11px' }}>
                Last data: {moment(latestData.received_at).fromNow()}
              </Text>
            )}
          </Space>
        );
      },
    },
    {
      title: 'Sensor Data',
      key: 'sensors',
      render: (_, record) => {
        const latestData = sensorData[record.node_id];
        
        if (!latestData) {
          return <Text type="secondary">No data</Text>;
        }
        
        return (
          <Space direction="vertical" size="small">
            <Space>
              <Text>🌡️ {latestData.temperature || 'N/A'}°C</Text>
              <Text>💧 {latestData.humidity || 'N/A'}%</Text>
            </Space>
            <Space>
              <Text>🌬️ Gas: {latestData.gas_sensor || 'N/A'}</Text>
              <Text>🔧 Servo: {latestData.servo_angle || 'N/A'}°</Text>
            </Space>
          </Space>
        );
      },
    },
    {
      title: 'Connection',
      key: 'connection',
      render: (_, record) => {
        const latestData = sensorData[record.node_id];
        const signalStrength = getSignalStrength(latestData?.wifi_rssi);
        
        return (
          <Space direction="vertical" size="small">
            {latestData?.wifi_rssi && (
              <Tooltip title={`Signal: ${latestData.wifi_rssi} dBm`}>
                <Space>
                  <SignalFilled style={{ color: signalStrength > 50 ? '#52c41a' : signalStrength > 25 ? '#faad14' : '#ff4d4f' }} />
                  <Progress 
                    percent={signalStrength} 
                    size="small" 
                    showInfo={false}
                    strokeColor={signalStrength > 50 ? '#52c41a' : signalStrength > 25 ? '#faad14' : '#ff4d4f'}
                  />
                  <Text style={{ fontSize: '12px' }}>{signalStrength}%</Text>
                </Space>
              </Tooltip>
            )}
            {latestData?.uptime && (
              <Text type="secondary" style={{ fontSize: '11px' }}>
                Uptime: {Math.floor(latestData.uptime / 1000)}s
              </Text>
            )}
          </Space>
        );
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => {
        const isOnline = getNodeStatus(record.node_id, record.last_seen) === 'online';
        return (
          <Space>
            <Button
              type="primary"
              size="small"
              disabled={!isOnline}
              onClick={() => {
                message.info(`Sending test command to ${record.name || record.node_id}`);
              }}
            >
              Test
            </Button>
            <Button
              icon={<ReloadOutlined />}
              size="small"
              disabled={!isOnline}
              onClick={() => {
                message.info(`Refreshing ${record.name || record.node_id}`);
              }}
            >
              Refresh
            </Button>
          </Space>
        );
      },
    },
  ];

  // Calculate statistics
  const onlineCount = Array.isArray(nodes) ? nodes.filter(node => 
    getNodeStatus(node.node_id, node.last_seen) === 'online'
  ).length : 0;
  
  const offlineCount = Array.isArray(nodes) ? nodes.length - onlineCount : 0;
  const connectionRate = Array.isArray(nodes) && nodes.length > 0 ? Math.round((onlineCount / nodes.length) * 100) : 0;

  return (
    <div>
      {/* Header Controls */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Title level={3}>
            <RobotOutlined /> Real-time ESP32 Dashboard
          </Title>
        </Col>
        <Col span={12} style={{ textAlign: 'right' }}>
          <Space>
            <Text>Real-time Updates:</Text>
            <Switch
              checked={realtimeEnabled}
              onChange={setRealtimeEnabled}
              checkedChildren={<PlayCircleOutlined />}
              unCheckedChildren={<PauseCircleOutlined />}
            />
            <Button 
              icon={<ReloadOutlined />} 
              onClick={loadNodes}
              loading={loading}
            >
              Refresh Devices
            </Button>
          </Space>
        </Col>
      </Row>

      {/* Status Alert */}
      {realtimeEnabled && (
        <Alert
          message={
            <Space>
              <Badge status={wsConnected ? 'success' : 'error'} />
              <Text>
                {wsConnected ? '🔴 LIVE' : 'Disconnected'} - 
                {wsConnected && lastUpdate && ` Last update: ${moment(lastUpdate).format('HH:mm:ss')}`}
                {wsConnected && ` | Messages: ${messageCount} | Rate: ${dataRate}/5s`}
              </Text>
            </Space>
          }
          type={wsConnected ? 'success' : 'warning'}
          style={{ marginBottom: 16 }}
          showIcon
        />
      )}

      {/* Statistics Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total ESP32 Devices"
              value={Array.isArray(nodes) ? nodes.length : 0}
              prefix={<RobotOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Online Now"
              value={onlineCount}
              prefix={<WifiOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Offline"
              value={offlineCount}
              prefix={<DisconnectOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Connection Rate"
              value={connectionRate}
              suffix="%"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ 
                color: connectionRate === 100 ? '#52c41a' : 
                       connectionRate > 70 ? '#faad14' : '#ff4d4f' 
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* Real-time Data Rate Indicator */}
      {realtimeEnabled && wsConnected && (
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col span={24}>
            <Card size="small">
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic
                    title="Data Rate"
                    value={dataRate}
                    suffix="msg/5s"
                    prefix={<FireOutlined />}
                    valueStyle={{ fontSize: '16px' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="Total Messages"
                    value={messageCount}
                    prefix={<ExperimentOutlined />}
                    valueStyle={{ fontSize: '16px' }}
                  />
                </Col>
                <Col span={12}>
                  <div style={{ paddingTop: 8 }}>
                    <Text type="secondary">
                      Real-time performance: {dataRate > 10 ? '🚀 High' : dataRate > 5 ? '⚡ Normal' : '🐌 Low'} throughput
                    </Text>
                  </div>
                </Col>
              </Row>
            </Card>
          </Col>
        </Row>
      )}

      {/* ESP32 Devices Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={Array.isArray(nodes) ? nodes : []}
          rowKey="node_id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          scroll={{ x: true }}
          title={() => (
            <Space>
              <EyeOutlined />
              <Text strong>Real-time ESP32 Device Monitor</Text>
              {wsConnected && <Tag color="green">LIVE UPDATES</Tag>}
            </Space>
          )}
        />
      </Card>
    </div>
  );
};

export default RealtimeESP32Dashboard;
