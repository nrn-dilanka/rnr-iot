import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  Space,
  Popconfirm,
  message,
  Tag,
  Divider,
  Row,
  Col,
  Switch,
  Tooltip,
  Alert
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SyncOutlined,
  ExperimentOutlined,
  ThunderboltOutlined,
  DashboardOutlined,
  SettingOutlined,
  BugOutlined
} from '@ant-design/icons';
import { nodeAPI, sensorAPI } from '../services/api';

const { Option } = Select;
const { TextArea } = Input;

const SensorManagement = () => {
  const [sensors, setSensors] = useState([]);
  const [nodes, setNodes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingSensor, setEditingSensor] = useState(null);
  const [form] = Form.useForm();

  const sensorTypes = [
    { value: 'temperature', label: 'Temperature', icon: '🌡️', unit: '°C' },
    { value: 'humidity', label: 'Humidity', icon: '💧', unit: '%' },
    { value: 'pressure', label: 'Pressure', icon: '🔵', unit: 'hPa' },
    { value: 'gas', label: 'Gas Sensor', icon: '💨', unit: 'ppm' },
    { value: 'light', label: 'Light Sensor', icon: '💡', unit: 'lux' },
    { value: 'motion', label: 'Motion/PIR', icon: '🚶', unit: 'bool' },
    { value: 'ultrasonic', label: 'Ultrasonic Distance', icon: '📏', unit: 'cm' },
    { value: 'soil_moisture', label: 'Soil Moisture', icon: '🌱', unit: '%' },
    { value: 'ph', label: 'pH Sensor', icon: '⚗️', unit: 'pH' },
    { value: 'current', label: 'Current Sensor', icon: '⚡', unit: 'A' },
    { value: 'voltage', label: 'Voltage Sensor', icon: '🔋', unit: 'V' },
    { value: 'vibration', label: 'Vibration', icon: '📳', unit: 'g' },
    { value: 'sound', label: 'Sound Level', icon: '🔊', unit: 'dB' },
    { value: 'custom', label: 'Custom Sensor', icon: '🔧', unit: 'custom' }
  ];

  const pinTypes = [
    { value: 'analog', label: 'Analog Pin (ADC)' },
    { value: 'digital', label: 'Digital Pin' },
    { value: 'pwm', label: 'PWM Pin' },
    { value: 'i2c', label: 'I2C Bus' },
    { value: 'spi', label: 'SPI Bus' },
    { value: 'uart', label: 'UART/Serial' },
    { value: 'virtual', label: 'Virtual/Calculated' }
  ];

  const esp32Pins = [
    // Analog Pins
    { value: 'A0', label: 'A0 (GPIO36)', type: 'analog' },
    { value: 'A3', label: 'A3 (GPIO39)', type: 'analog' },
    { value: 'A4', label: 'A4 (GPIO32)', type: 'analog' },
    { value: 'A5', label: 'A5 (GPIO33)', type: 'analog' },
    { value: 'A6', label: 'A6 (GPIO34)', type: 'analog' },
    { value: 'A7', label: 'A7 (GPIO35)', type: 'analog' },
    // Digital Pins
    { value: 'D2', label: 'D2 (GPIO2)', type: 'digital' },
    { value: 'D4', label: 'D4 (GPIO4)', type: 'digital' },
    { value: 'D5', label: 'D5 (GPIO5)', type: 'digital' },
    { value: 'D12', label: 'D12 (GPIO12)', type: 'digital' },
    { value: 'D13', label: 'D13 (GPIO13)', type: 'digital' },
    { value: 'D14', label: 'D14 (GPIO14)', type: 'digital' },
    { value: 'D15', label: 'D15 (GPIO15)', type: 'digital' },
    { value: 'D16', label: 'D16 (GPIO16)', type: 'digital' },
    { value: 'D17', label: 'D17 (GPIO17)', type: 'digital' },
    { value: 'D18', label: 'D18 (GPIO18)', type: 'digital' },
    { value: 'D19', label: 'D19 (GPIO19)', type: 'digital' },
    { value: 'D21', label: 'D21 (GPIO21) - SDA', type: 'i2c' },
    { value: 'D22', label: 'D22 (GPIO22) - SCL', type: 'i2c' },
    { value: 'D23', label: 'D23 (GPIO23)', type: 'digital' },
    { value: 'D25', label: 'D25 (GPIO25)', type: 'pwm' },
    { value: 'D26', label: 'D26 (GPIO26)', type: 'pwm' },
    { value: 'D27', label: 'D27 (GPIO27)', type: 'digital' }
  ];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // Load nodes and sensor configurations
      const [nodesResponse, sensorsResponse] = await Promise.all([
        nodeAPI.getNodes(),
        sensorAPI.getSensors()
      ]);
      
      setNodes(nodesResponse.data || []);
      setSensors(sensorsResponse.data || []);
    } catch (error) {
      console.error('Error loading data:', error);
      message.error('Failed to load sensor data');
    } finally {
      setLoading(false);
    }
  };

  const handleAddSensor = () => {
    setEditingSensor(null);
    form.resetFields();
    form.setFieldsValue({
      enabled: true,
      calibration_offset: 0,
      calibration_scale: 1,
      update_interval: 1000
    });
    setModalVisible(true);
  };

  const handleEditSensor = (sensor) => {
    setEditingSensor(sensor);
    form.setFieldsValue(sensor);
    setModalVisible(true);
  };

  const handleDeleteSensor = async (sensorId) => {
    try {
      await sensorAPI.deleteSensor(sensorId);
      setSensors(prev => prev.filter(s => s.id !== sensorId));
      message.success('Sensor deleted successfully');
    } catch (error) {
      console.error('Error deleting sensor:', error);
      message.error('Failed to delete sensor');
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingSensor) {
        // Update existing sensor
        const response = await sensorAPI.updateSensor(editingSensor.id, values);
        setSensors(prev => prev.map(s => 
          s.id === editingSensor.id ? response.data : s
        ));
        message.success('Sensor updated successfully');
      } else {
        // Add new sensor
        const response = await sensorAPI.createSensor(values);
        setSensors(prev => [...prev, response.data]);
        message.success('Sensor added successfully');
      }
      
      setModalVisible(false);
      form.resetFields();
    } catch (error) {
      console.error('Error saving sensor:', error);
      message.error('Failed to save sensor configuration');
    }
  };

  const handleModalCancel = () => {
    setModalVisible(false);
    form.resetFields();
    setEditingSensor(null);
  };

  const generateArduinoCode = (sensor) => {
    const sensorConfig = sensorTypes.find(t => t.value === sensor.type);
    let code = `// ${sensor.name} Configuration\n`;
    code += `const int ${sensor.name.replace(/\s+/g, '_').toLowerCase()}_pin = ${sensor.pin.replace(/[AD]/, '')};\n`;
    code += `float ${sensor.name.replace(/\s+/g, '_').toLowerCase()}_value = 0;\n\n`;
    
    if (sensor.pin_type === 'analog') {
      code += `// Read ${sensor.name}\n`;
      code += `${sensor.name.replace(/\s+/g, '_').toLowerCase()}_value = analogRead(${sensor.name.replace(/\s+/g, '_').toLowerCase()}_pin);\n`;
      if (sensor.calibration_scale !== 1 || sensor.calibration_offset !== 0) {
        code += `${sensor.name.replace(/\s+/g, '_').toLowerCase()}_value = (${sensor.name.replace(/\s+/g, '_').toLowerCase()}_value * ${sensor.calibration_scale}) + ${sensor.calibration_offset};\n`;
      }
    } else {
      code += `${sensor.name.replace(/\s+/g, '_').toLowerCase()}_value = digitalRead(${sensor.name.replace(/\s+/g, '_').toLowerCase()}_pin);\n`;
    }
    
    return code;
  };

  const columns = [
    {
      title: 'Sensor',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>{sensorTypes.find(t => t.value === record.type)?.icon}</span>
            <strong>{text}</strong>
            {!record.enabled && <Tag color="red">Disabled</Tag>}
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {sensorTypes.find(t => t.value === record.type)?.label}
          </div>
        </div>
      )
    },
    {
      title: 'Node',
      dataIndex: 'node_id',
      key: 'node_id',
      render: (nodeId) => (
        <Tag color="blue">{nodeId}</Tag>
      )
    },
    {
      title: 'Pin Configuration',
      key: 'pin_config',
      render: (_, record) => (
        <div>
          <Tag color="green">{record.pin}</Tag>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {pinTypes.find(p => p.value === record.pin_type)?.label}
          </div>
        </div>
      )
    },
    {
      title: 'Update Rate',
      dataIndex: 'update_interval',
      key: 'update_interval',
      render: (interval) => `${interval}ms`
    },
    {
      title: 'Range',
      key: 'range',
      render: (_, record) => {
        const unit = sensorTypes.find(t => t.value === record.type)?.unit;
        return `${record.threshold_min} - ${record.threshold_max} ${unit}`;
      }
    },
    {
      title: 'Status',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled) => (
        <Tag color={enabled ? 'green' : 'red'}>
          {enabled ? 'Active' : 'Inactive'}
        </Tag>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title="Edit Sensor">
            <Button 
              size="small" 
              icon={<EditOutlined />}
              onClick={() => handleEditSensor(record)}
            />
          </Tooltip>
          <Tooltip title="Generate Arduino Code">
            <Button 
              size="small" 
              icon={<BugOutlined />}
              onClick={async () => {
                try {
                  const response = await sensorAPI.generateCode(record.id, 'arduino');
                  Modal.info({
                    title: `Arduino Code for ${record.name}`,
                    content: (
                      <pre style={{ 
                        backgroundColor: '#f5f5f5', 
                        padding: '12px', 
                        borderRadius: '4px',
                        fontSize: '12px',
                        overflow: 'auto',
                        maxHeight: '400px'
                      }}>
                        {response.data.code}
                      </pre>
                    ),
                    width: 600
                  });
                } catch (error) {
                  console.error('Error generating code:', error);
                  message.error('Failed to generate code');
                }
              }}
            />
          </Tooltip>
          <Popconfirm
            title="Delete this sensor?"
            onConfirm={() => handleDeleteSensor(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Tooltip title="Delete Sensor">
              <Button 
                size="small" 
                danger 
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card 
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ExperimentOutlined />
            <span>Sensor Management</span>
          </div>
        }
        extra={
          <Space>
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={handleAddSensor}
            >
              Add Sensor
            </Button>
            <Button 
              icon={<SyncOutlined />}
              onClick={loadData}
              loading={loading}
            >
              Refresh
            </Button>
          </Space>
        }
      >
        <Alert
          message="Sensor Configuration System"
          description="Configure and manage sensors for your ESP32 nodes. Add new sensors, set pin configurations, calibration values, and generate Arduino code automatically."
          type="info"
          showIcon
          style={{ marginBottom: '16px' }}
        />

        <Table
          dataSource={sensors}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1000 }}
        />
      </Card>

      <Modal
        title={editingSensor ? 'Edit Sensor' : 'Add New Sensor'}
        visible={modalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        width={800}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            enabled: true,
            calibration_offset: 0,
            calibration_scale: 1,
            update_interval: 1000
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="Sensor Name"
                rules={[{ required: true, message: 'Please enter sensor name' }]}
              >
                <Input placeholder="e.g., Living Room Temperature" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="type"
                label="Sensor Type"
                rules={[{ required: true, message: 'Please select sensor type' }]}
              >
                <Select placeholder="Select sensor type">
                  {sensorTypes.map(type => (
                    <Option key={type.value} value={type.value}>
                      <span>{type.icon} {type.label} ({type.unit})</span>
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="node_id"
                label="Target Node"
                rules={[{ required: true, message: 'Please select target node' }]}
              >
                <Select placeholder="Select ESP32 node">
                  {nodes.map(node => (
                    <Option key={node.node_id} value={node.node_id}>
                      {node.node_id} {node.name && `(${node.name})`}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="enabled"
                label="Enable Sensor"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
          </Row>

          <Divider>Pin Configuration</Divider>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="pin_type"
                label="Pin Type"
                rules={[{ required: true, message: 'Please select pin type' }]}
              >
                <Select placeholder="Select pin type">
                  {pinTypes.map(type => (
                    <Option key={type.value} value={type.value}>
                      {type.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="pin"
                label="ESP32 Pin"
                rules={[{ required: true, message: 'Please select pin' }]}
              >
                <Select placeholder="Select ESP32 pin">
                  {esp32Pins.map(pin => (
                    <Option key={pin.value} value={pin.value}>
                      {pin.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider>Sensor Settings</Divider>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="update_interval"
                label="Update Interval (ms)"
                rules={[{ required: true, message: 'Please enter update interval' }]}
              >
                <InputNumber min={100} max={60000} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="threshold_min"
                label="Minimum Value"
                rules={[{ required: true, message: 'Please enter minimum value' }]}
              >
                <InputNumber style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="threshold_max"
                label="Maximum Value"
                rules={[{ required: true, message: 'Please enter maximum value' }]}
              >
                <InputNumber style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Divider>Calibration</Divider>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="calibration_offset"
                label="Calibration Offset"
                tooltip="Value added to raw sensor reading"
              >
                <InputNumber style={{ width: '100%' }} step={0.1} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="calibration_scale"
                label="Calibration Scale"
                tooltip="Value multiplied with raw sensor reading"
              >
                <InputNumber style={{ width: '100%' }} step={0.1} min={0.01} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="description"
            label="Description"
          >
            <TextArea 
              rows={3} 
              placeholder="Optional description for this sensor configuration..."
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default SensorManagement;
