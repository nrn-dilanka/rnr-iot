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
import moment from 'moment';

const DeviceManagement = () => {
  const [nodes, setNodes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [controlModalVisible, setControlModalVisible] = useState(false);
  const [editingNode, setEditingNode] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadNodes();
  }, []);

  const loadNodes = async () => {
    try {
      setLoading(true);
      console.log('Loading nodes...');
      const response = await nodeAPI.getNodes();
      console.log('API Response:', response);
      console.log('Response data:', response.data);
      console.log('Response data type:', typeof response.data);
      console.log('Is array:', Array.isArray(response.data));
      setNodes(response.data || []);
    } catch (error) {
      console.error('Error loading nodes:', error);
      notification.error({
        message: 'Error',
        description: `Failed to load nodes: ${error.message}`,
      });
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
        description: 'Node deleted successfully',
      });
      loadNodes();
    } catch (error) {
      console.error('Error deleting node:', error);
      notification.error({
        message: 'Error',
        description: 'Failed to delete node',
      });
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingNode) {
        // Update existing node
        await nodeAPI.updateNode(editingNode.node_id, values);
        notification.success({
          message: 'Success',
          description: 'Node updated successfully',
        });
      } else {
        // Create new node
        await nodeAPI.createNode(values);
        notification.success({
          message: 'Success',
          description: 'Node created successfully',
        });
      }
      
      setModalVisible(false);
      form.resetFields();
      loadNodes();
    } catch (error) {
      console.error('Error saving node:', error);
      notification.error({
        message: 'Error',
        description: 'Failed to save node',
      });
    }
  };

  const getNodeStatus = (lastSeen) => {
    if (!lastSeen) return 'offline';
    const now = moment();
    const lastSeenTime = moment(lastSeen);
    const minutesSinceLastSeen = now.diff(lastSeenTime, 'minutes');
    return minutesSinceLastSeen <= 5 ? 'online' : 'offline';
  };

  const getActionMenuItems = (node) => [
    {
      key: 'control',
      icon: <ControlOutlined />,
      label: 'Control',
      onClick: () => {
        setSelectedNode(node);
        setControlModalVisible(true);
      },
    },
    {
      key: 'edit',
      icon: <EditOutlined />,
      label: 'Edit',
      onClick: () => handleEditNode(node),
    },
    {
      key: 'delete',
      icon: <DeleteOutlined />,
      label: 'Delete',
      danger: true,
      onClick: () => handleDeleteNode(node.node_id),
    },
  ];

  const columns = [
    {
      title: 'Node ID',
      dataIndex: 'node_id',
      key: 'node_id',
      width: 200,
      ellipsis: true,
    },
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (name) => name || 'Unnamed Device',
    },
    {
      title: 'MAC Address',
      dataIndex: 'mac_address',
      key: 'mac_address',
      width: 150,
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
      title: 'Last Seen',
      dataIndex: 'last_seen',
      key: 'last_seen',
      width: 150,
      render: (lastSeen) => 
        lastSeen ? moment(lastSeen).format('MMM DD, HH:mm') : 'Never',
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (createdAt) => moment(createdAt).format('MMM DD, YYYY'),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<ControlOutlined />}
            onClick={() => {
              setSelectedNode(record);
              setControlModalVisible(true);
            }}
          >
            Control
          </Button>
          <Dropdown
            menu={{ items: getActionMenuItems(record) }}
            trigger={['click']}
          >
            <Button size="small" icon={<MoreOutlined />} />
          </Dropdown>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2>Device Management</h2>
          <Space>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={loadNodes}
              loading={loading}
            >
              Refresh
            </Button>
            <Button 
              type="primary" 
              icon={<PlusOutlined />} 
              onClick={handleAddNode}
            >
              Add Node
            </Button>
          </Space>
        </div>

        {/* Debug Information */}
        <div style={{ marginBottom: 16, padding: 8, backgroundColor: '#f0f0f0', fontSize: '12px' }}>
          <strong>Debug Info:</strong> 
          Nodes count: {nodes?.length || 0}, 
          Loading: {loading ? 'Yes' : 'No'}, 
          Nodes type: {typeof nodes}, 
          Is Array: {Array.isArray(nodes) ? 'Yes' : 'No'}
        </div>

        <Table
          columns={columns}
          dataSource={nodes}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} of ${total} nodes`,
          }}
          scroll={{ x: 1000 }}
        />
      </Card>

      {/* Add/Edit Node Modal */}
      <Modal
        title={editingNode ? 'Edit Node' : 'Add New Node'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        width={500}
      >
        <Form
          form={form}
          layout="vertical"
          requiredMark={false}
        >
          <Form.Item
            name="node_id"
            label="Node ID"
            rules={[
              { required: true, message: 'Please enter a node ID' },
              { min: 3, message: 'Node ID must be at least 3 characters' },
            ]}
          >
            <Input 
              placeholder="e.g., ESP32_001" 
              disabled={!!editingNode}
            />
          </Form.Item>

          <Form.Item
            name="name"
            label="Device Name"
            rules={[
              { required: true, message: 'Please enter a device name' },
            ]}
          >
            <Input placeholder="e.g., Living Room Sensor" />
          </Form.Item>

          <Form.Item
            name="mac_address"
            label="MAC Address (Optional)"
          >
            <Input 
              placeholder="e.g., 44:17:93:F9:45:6C" 
              style={{ textTransform: 'uppercase' }}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* Control Modal */}
      <Modal
        title={`Control ${selectedNode?.name || selectedNode?.node_id}`}
        open={controlModalVisible}
        onCancel={() => setControlModalVisible(false)}
        footer={[
          <Button 
            key="close" 
            onClick={() => setControlModalVisible(false)}
          >
            Close
          </Button>
        ]}
        width={600}
      >
        {selectedNode && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <h4>Device Information</h4>
              <p><strong>Node ID:</strong> {selectedNode.node_id}</p>
              <p><strong>Name:</strong> {selectedNode.name}</p>
              <p><strong>MAC Address:</strong> {selectedNode.mac_address || 'N/A'}</p>
              <p><strong>Status:</strong> 
                <Badge 
                  status={getNodeStatus(selectedNode.last_seen) === 'online' ? 'success' : 'error'} 
                  text={getNodeStatus(selectedNode.last_seen) === 'online' ? 'Online' : 'Offline'} 
                  style={{ marginLeft: 8 }}
                />
              </p>
              <p><strong>Last Seen:</strong> {selectedNode.last_seen ? moment(selectedNode.last_seen).format('MMMM DD, YYYY HH:mm:ss') : 'Never'}</p>
            </div>

            <div>
              <h4>Quick Actions</h4>
              <Space wrap>
                <Button 
                  type="primary" 
                  onClick={() => {
                    notification.info({ message: 'Restart command sent to device' });
                  }}
                >
                  Restart Device
                </Button>
                <Button 
                  onClick={() => {
                    notification.info({ message: 'Status update requested' });
                  }}
                >
                  Request Status
                </Button>
                <Button 
                  onClick={() => {
                    notification.info({ message: 'Calibration command sent' });
                  }}
                >
                  Calibrate Sensors
                </Button>
              </Space>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default DeviceManagement;
