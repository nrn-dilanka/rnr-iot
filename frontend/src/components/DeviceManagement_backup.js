import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Space,
  Badge,
  Dropdown,
  notification,
  Popconfirm,
  Card,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ControlOutlined,
  ReloadOutlined,
  MoreOutlined,
} from '@ant-design/icons';
import { nodeAPI } from '../services/api';
import WebSocketService from '../services/WebSocketService';
import moment from 'moment';

const DeviceManagement = () => {
  const [nodes, setNodes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [controlModalVisible, setControlModalVisible] = useState(false);
  const [editingNode, setEditingNode] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [form] = Form.useForm();
  // Real-time status tracking
  const [nodeStatus, setNodeStatus] = useState({}); // {node_id: 'online'|'offline'}

  useEffect(() => {
    loadNodes();

    // Set up WebSocket listeners for real-time status updates
    const wsService = WebSocketService.getInstance();
    
    // Listen for node status updates
    const handleNodeStatus = (data) => {
      if (data.type === 'node_status') {
        console.log('Real-time node status update:', data);
        setNodeStatus(prev => ({
          ...prev,
          [data.node_id]: data.status
        }));
      }
    };

    // Listen for sensor data which indicates a node is online
    const handleSensorData = (data) => {
      if (data.type === 'sensor_data') {
        console.log('Sensor data received from:', data.node_id);
        setNodeStatus(prev => ({
          ...prev,
          [data.node_id]: 'online'
        }));
      }
    };

    wsService.subscribe('node_status', handleNodeStatus);
    wsService.subscribe('sensor_data', handleSensorData);

    return () => {
      wsService.unsubscribe('node_status', handleNodeStatus);
      wsService.unsubscribe('sensor_data', handleSensorData);
    };
  }, []);

  const loadNodes = async () => {
    try {
      setLoading(true);
      const response = await nodeAPI.getNodes();
      console.log('DeviceManagement API response:', response);
      
      // Ensure we always have an array
      const nodeData = response?.data || response || [];
      console.log('DeviceManagement node data:', nodeData);
      
      // Make sure it's an array
      if (Array.isArray(nodeData)) {
        setNodes(nodeData);
      } else {
        console.error('Node data is not an array:', nodeData);
        setNodes([]);
      }
    } catch (error) {
      console.error('Error loading nodes:', error);
      notification.error({
        message: 'Error',
        description: 'Failed to load devices'
      });
      setNodes([]); // Ensure nodes is always an array on error
    } finally {
      setLoading(false);
    }
  };

  const handleAddNode = () => {
    setEditingNode(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEditNode = (node) => {
    setEditingNode(node);
    form.setFieldsValue(node);
    setModalVisible(true);
  };

  const handleDeleteNode = async (nodeId) => {
    try {
      await nodeAPI.deleteNode(nodeId);
      notification.success({
        message: 'Success',
        description: 'Device deleted successfully',
      });
      loadNodes();
    } catch (error) {
      notification.error({
        message: 'Error',
        description: 'Failed to delete device',
      });
    }
  };

  const handleControlNode = (node) => {
    setSelectedNode(node);
    setControlModalVisible(true);
  };

  const handleSubmit = async (values) => {
    try {
      if (editingNode) {
        await nodeAPI.updateNode(editingNode.id, values);
        notification.success({
          message: 'Success',
          description: 'Device updated successfully',
        });
      } else {
        await nodeAPI.createNode(values);
        notification.success({
          message: 'Success',
          description: 'Device added successfully',
        });
      }
      setModalVisible(false);
      form.resetFields();
      loadNodes();
    } catch (error) {
      notification.error({
        message: 'Error',
        description: `Failed to ${editingNode ? 'update' : 'add'} device`,
      });
    }
  };

  const handleSendCommand = async (command) => {
    try {
      await nodeAPI.sendAction(selectedNode.node_id, { action: command });
      notification.success({
        message: 'Success',
        description: `Command "${command}" sent successfully`,
      });
      setControlModalVisible(false);
    } catch (error) {
      notification.error({
        message: 'Error',
        description: 'Failed to send command',
      });
    }
  };

  // Get real-time node status
  const getNodeStatus = (nodeId, lastSeen) => {
    // Check real-time status first
    if (nodeStatus[nodeId]) {
      return nodeStatus[nodeId];
    }
    
    // Fallback to timestamp-based detection
    if (!lastSeen) return 'offline';
    const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
    return new Date(lastSeen) > fiveMinutesAgo ? 'online' : 'offline';
  };

  const columns = [
    {
      title: 'Node ID',
      dataIndex: 'node_id',
      key: 'node_id',
      render: (text) => <span style={{ fontFamily: 'monospace' }}>{text}</span>,
    },
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'MAC Address',
      dataIndex: 'mac_address',
      key: 'mac_address',
      render: (text) => text || 'N/A',
    },
    {
      title: 'Status',
      key: 'status',
      render: (_, record) => {
        const status = getNodeStatus(record.node_id, record.last_seen);
        return (
          <Badge 
            status={status === 'online' ? 'success' : 'error'} 
            text={status === 'online' ? 'Online' : 'Offline'} 
          />
        );
      },
    },
    {
      title: 'Last Seen',
      dataIndex: 'last_seen',
      key: 'last_seen',
      render: (text) => text ? moment(text).fromNow() : 'Never',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => {
        const dropdownItems = [
          {
            key: 'edit',
            label: 'Edit',
            icon: <EditOutlined />,
            onClick: () => handleEditNode(record),
          },
          {
            key: 'control',
            label: 'Control',
            icon: <ControlOutlined />,
            onClick: () => handleControlNode(record),
          },
          {
            key: 'delete',
            label: 'Delete',
            icon: <DeleteOutlined />,
            danger: true,
            onClick: () => handleDeleteNode(record.id),
          },
        ];

        return (
          <Space>
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => handleEditNode(record)}
            >
              Edit
            </Button>
            <Dropdown
              menu={{
                items: dropdownItems,
              }}
              trigger={['click']}
            >
              <Button type="link" icon={<MoreOutlined />} />
            </Dropdown>
          </Space>
        );
      },
    },
  ];

  return (
    <div>
      <Card>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
          <h2>Device Management</h2>
          <Space>
            <Button icon={<ReloadOutlined />} onClick={loadNodes} loading={loading}>
              Refresh
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAddNode}>
              Add Device
            </Button>
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={nodes}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `${range[0]}-${range[1]} of ${total} devices`,
          }}
        />
      </Card>

      {/* Add/Edit Device Modal */}
      <Modal
        title={editingNode ? 'Edit Device' : 'Add Device'}
        open={modalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            name="node_id"
            label="Node ID"
            rules={[{ required: true, message: 'Please enter node ID' }]}
          >
            <Input placeholder="e.g., ESP32_001" />
          </Form.Item>
          <Form.Item
            name="name"
            label="Device Name"
            rules={[{ required: true, message: 'Please enter device name' }]}
          >
            <Input placeholder="e.g., Living Room Sensor" />
          </Form.Item>
          <Form.Item name="mac_address" label="MAC Address">
            <Input placeholder="e.g., AA:BB:CC:DD:EE:FF" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Control Device Modal */}
      <Modal
        title={`Control Device: ${selectedNode?.name || selectedNode?.node_id}`}
        open={controlModalVisible}
        onCancel={() => setControlModalVisible(false)}
        footer={null}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Button block onClick={() => handleSendCommand('REBOOT')}>
            Reboot Device
          </Button>
          <Button block onClick={() => handleSendCommand('STATUS_REQUEST')}>
            Request Status
          </Button>
          <Button block onClick={() => handleSendCommand('RESET_CONFIG')}>
            Reset Configuration
          </Button>
        </Space>
      </Modal>
    </div>
  );
};

export default DeviceManagement;
