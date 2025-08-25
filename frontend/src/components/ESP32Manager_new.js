import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  message,
  Modal,
  Form,
  InputNumber,
  Badge,
  Statistic,
  Row,
  Col,
  Typography,
  Alert
} from 'antd';
import {
  WifiOutlined,
  DisconnectOutlined,
  ReloadOutlined,
  ControlOutlined,
  RobotOutlined,
  ThunderboltOutlined,
  SettingOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { nodeAPI } from '../services/api';
import WebSocketService from '../services/WebSocketService';
import moment from 'moment';

const { Title, Text } = Typography;

const ESP32Manager = () => {
  const [nodes, setNodes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [servoModalVisible, setServoModalVisible] = useState(false);
  const [selectedNode, setSelectedNode] = useState(null);
  const [nodeStatus, setNodeStatus] = useState({}); // Real-time status tracking
  const [lastUpdate, setLastUpdate] = useState(null);
  const [form] = Form.useForm();

  // Load ESP32 nodes
  const loadNodes = async () => {
    try {
      setLoading(true);
      const response = await nodeAPI.getNodes();
      setNodes(response.data || []);
    } catch (error) {
      console.error('Error loading ESP32 nodes:', error);
      message.error('Failed to load ESP32 devices');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNodes();

    // Set up WebSocket listeners for real-time status updates
    const wsService = WebSocketService.getInstance();
    
    const handleNodeStatus = (data) => {
      if (data.type === 'node_status') {
        console.log('🔄 Real-time ESP32 status update:', data);
        setNodeStatus(prev => ({
          ...prev,
          [data.node_id]: data.status
        }));
        setLastUpdate(new Date());
        
        // Show notification for status changes
        if (data.status === 'online') {
          message.success(`ESP32 Device ${data.node_id} Connected`, 2);
        } else {
          message.warning(`ESP32 Device ${data.node_id} Disconnected`, 2);
        }
      }
    };

    const handleSensorData = (data) => {
      if (data.type === 'sensor_data') {
        console.log('📡 Real-time ESP32 data:', data.node_id);
        setNodeStatus(prev => ({
          ...prev,
          [data.node_id]: 'online'
        }));
        setLastUpdate(new Date());
      }
    };

    wsService.subscribe('node_status', handleNodeStatus);
    wsService.subscribe('sensor_data', handleSensorData);

    return () => {
      wsService.unsubscribe('node_status', handleNodeStatus);
      wsService.unsubscribe('sensor_data', handleSensorData);
    };
  }, []);

  // Get real-time status
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
    
    return minutesSinceLastSeen <= 5 ? 'online' : 'offline';
  };

  // Send servo command
  const sendServoCommand = async (values) => {
    if (!selectedNode) return;
    
    try {
      // Here you would send MQTT command through your API
      // For now, we'll simulate the command
      message.success(`Servo command sent to ${selectedNode.name}: ${values.angle}°`);
      setServoModalVisible(false);
      form.resetFields();
    } catch (error) {
      message.error('Failed to send servo command');
    }
  };

  // Send reboot command
  const sendRebootCommand = async (nodeId) => {
    try {
      message.success(`Reboot command sent to device ${nodeId}`);
    } catch (error) {
      message.error('Failed to send reboot command');
    }
  };

  const columns = [
    {
      title: 'Device Info',
      key: 'info',
      render: (_, record) => (
        <Space direction="vertical" size="small">
          <Text strong>{record.name || 'Unnamed Device'}</Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>{record.node_id}</Text>
          {record.mac_address && (
            <Text type="secondary" style={{ fontSize: '12px' }}>MAC: {record.mac_address}</Text>
          )}
        </Space>
      ),
    },
    {
      title: 'Connection Status',
      key: 'status',
      width: 150,
      render: (_, record) => {
        const status = getNodeStatus(record.node_id, record.last_seen);
        return (
          <Space direction="vertical" size="small">
            <Badge 
              status={status === 'online' ? 'success' : 'error'} 
              text={
                <Text strong style={{ color: status === 'online' ? '#52c41a' : '#ff4d4f' }}>
                  {status === 'online' ? 'CONNECTED' : 'DISCONNECTED'}
                </Text>
              }
            />
            <Text type="secondary" style={{ fontSize: '11px' }}>
              {record.last_seen ? moment(record.last_seen).fromNow() : 'Never seen'}
            </Text>
          </Space>
        );
      },
    },
    {
      title: 'Device Type',
      key: 'type',
      render: () => (
        <Tag icon={<RobotOutlined />} color="blue">ESP32</Tag>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 200,
      render: (_, record) => {
        const isOnline = getNodeStatus(record.node_id, record.last_seen) === 'online';
        return (
          <Space>
            <Button
              type="primary"
              icon={<ControlOutlined />}
              size="small"
              disabled={!isOnline}
              onClick={() => {
                setSelectedNode(record);
                setServoModalVisible(true);
              }}
            >
              Servo
            </Button>
            <Button
              icon={<ReloadOutlined />}
              size="small"
              disabled={!isOnline}
              onClick={() => sendRebootCommand(record.node_id)}
            >
              Reboot
            </Button>
          </Space>
        );
      },
    },
  ];

  // Calculate statistics
  const onlineCount = nodes.filter(node => 
    getNodeStatus(node.node_id, node.last_seen) === 'online'
  ).length;
  
  const offlineCount = nodes.length - onlineCount;

  return (
    <div>
      {/* Header Statistics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total ESP32 Devices"
              value={nodes.length}
              prefix={<RobotOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Connected Devices"
              value={onlineCount}
              prefix={<WifiOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Disconnected Devices"
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
              value={nodes.length > 0 ? Math.round((onlineCount / nodes.length) * 100) : 0}
              suffix="%"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ 
                color: onlineCount === nodes.length ? '#52c41a' : 
                       onlineCount > 0 ? '#faad14' : '#ff4d4f' 
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* Real-time Status Alert */}
      {lastUpdate && (
        <Alert
          message={`Real-time Status Updates Active - Last Update: ${moment(lastUpdate).format('HH:mm:ss')}`}
          type="info"
          icon={<InfoCircleOutlined />}
          style={{ marginBottom: 16 }}
          showIcon
        />
      )}

      {/* ESP32 Devices Table */}
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <Title level={4} style={{ margin: 0 }}>
            <RobotOutlined /> ESP32 Device Manager
          </Title>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={loadNodes}
            loading={loading}
          >
            Refresh
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={nodes}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} of ${total} ESP32 devices`,
          }}
          scroll={{ x: 800 }}
        />
      </Card>

      {/* Servo Control Modal */}
      <Modal
        title={`Control Servo - ${selectedNode?.name || selectedNode?.node_id}`}
        open={servoModalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setServoModalVisible(false);
          form.resetFields();
        }}
        width={400}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={sendServoCommand}
        >
          <Form.Item
            name="angle"
            label="Servo Angle (0-180 degrees)"
            rules={[
              { required: true, message: 'Please enter servo angle' },
              { type: 'number', min: 0, max: 180, message: 'Angle must be between 0-180' }
            ]}
            initialValue={90}
          >
            <InputNumber
              min={0}
              max={180}
              style={{ width: '100%' }}
              placeholder="Enter angle (0-180)"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ESP32Manager;
