import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Select,
  Button,
  Table,
  Modal,
  message,
  Space,
  Tag,
  Switch,
  InputNumber,
  Divider,
  Row,
  Col,
  Alert,
  Tabs,
  Typography,
  Upload,
  Progress
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CodeOutlined,
  ExperimentOutlined,
  UploadOutlined,
  DownloadOutlined,
  ThunderboltOutlined,
  SettingOutlined
} from '@ant-design/icons';
// import { sensorAPI, firmwareAPI } from '../services/api';

const { Option } = Select;
const { TextArea } = Input;
const { TabPane } = Tabs;
const { Title, Text } = Typography;

const DynamicSensorManager = () => {
  const [sensors, setSensors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingSensor, setEditingSensor] = useState(null);
  const [form] = Form.useForm();
  const [codeModalVisible, setCodeModalVisible] = useState(false);
  const [generatedCode, setGeneratedCode] = useState('');
  const [selectedSensor, setSelectedSensor] = useState(null);
  const [firmwareUploading, setFirmwareUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Predefined sensor types with their configurations
  const sensorTypes = {
    temperature: {
      name: 'Temperature Sensor',
      pins: ['A0', 'A1', 'A2', 'A3', '2', '3', '4', '5'],
      pinType: 'analog',
      defaultCode: `
// Temperature Sensor (DS18B20/LM35)
float readTemperature() {
  int sensorValue = analogRead({{PIN}});
  float voltage = sensorValue * (5.0 / 1023.0);
  float temperature = (voltage - 0.5) * 100.0; // For LM35
  return temperature * {{SCALE}} + {{OFFSET}};
}`
    },
    humidity: {
      name: 'Humidity Sensor',
      pins: ['A0', 'A1', 'A2', 'A3', '25', '26', '27'],
      pinType: 'analog',
      defaultCode: `
// Humidity Sensor (DHT22/MQ-series)
float readHumidity() {
  int sensorValue = analogRead({{PIN}});
  float humidity = map(sensorValue, 0, 4095, 0, 100);
  return constrain(humidity * {{SCALE}} + {{OFFSET}}, 0, 100);
}`
    },
    gas: {
      name: 'Gas Sensor',
      pins: ['A0', 'A1', 'A2', 'A3', '34', '35', '36'],
      pinType: 'analog',
      defaultCode: `
// Gas Sensor (MQ-2/MQ-135)
int readGasSensor() {
  int sensorValue = analogRead({{PIN}});
  // Apply calibration
  int calibratedValue = sensorValue * {{SCALE}} + {{OFFSET}};
  return constrain(calibratedValue, 0, 4095);
}`
    },
    motion: {
      name: 'Motion Sensor',
      pins: ['2', '3', '4', '5', '12', '13', '14', '15'],
      pinType: 'digital',
      defaultCode: `
// Motion Sensor (PIR)
bool readMotionSensor() {
  return digitalRead({{PIN}}) == HIGH;
}`
    },
    light: {
      name: 'Light Sensor',
      pins: ['A0', 'A1', 'A2', 'A3', '34', '35', '36'],
      pinType: 'analog',
      defaultCode: `
// Light Sensor (LDR/Photoresistor)
int readLightSensor() {
  int sensorValue = analogRead({{PIN}});
  int lightLevel = map(sensorValue, 0, 4095, 0, 100);
  return lightLevel * {{SCALE}} + {{OFFSET}};
}`
    },
    ultrasonic: {
      name: 'Ultrasonic Sensor',
      pins: ['2', '3', '4', '5', '12', '13', '14', '15'],
      pinType: 'digital',
      defaultCode: `
// Ultrasonic Sensor (HC-SR04)
// Trigger pin: {{PIN}}, Echo pin: {{PIN}+1
float readUltrasonicDistance() {
  digitalWrite({{PIN}}, LOW);
  delayMicroseconds(2);
  digitalWrite({{PIN}}, HIGH);
  delayMicroseconds(10);
  digitalWrite({{PIN}}, LOW);
  
  long duration = pulseIn({{PIN}}+1, HIGH);
  float distance = (duration * 0.034) / 2;
  return distance * {{SCALE}} + {{OFFSET}};
}`
    },
    pressure: {
      name: 'Pressure Sensor',
      pins: ['21', '22', 'SDA', 'SCL'],
      pinType: 'i2c',
      defaultCode: `
// Pressure Sensor (BMP280/BME280)
#include <Wire.h>
#include <Adafruit_BMP280.h>

Adafruit_BMP280 bmp;

float readPressure() {
  float pressure = bmp.readPressure() / 100.0F; // hPa
  return pressure * {{SCALE}} + {{OFFSET}};
}`
    },
    sound: {
      name: 'Sound Sensor',
      pins: ['A0', 'A1', 'A2', 'A3', '34', '35', '36'],
      pinType: 'analog',
      defaultCode: `
// Sound Sensor (Microphone)
int readSoundLevel() {
  int sensorValue = analogRead({{PIN}});
  int soundLevel = map(sensorValue, 0, 4095, 0, 100);
  return soundLevel * {{SCALE}} + {{OFFSET}};
}`
    }
  };

  useEffect(() => {
    loadSensors();
  }, []);

  const loadSensors = async () => {
    try {
      setLoading(true);
      // Mock data - replace with actual API when available
      // const response = await sensorAPI.getSensors();
      // setSensors(response.data || []);
      
      const mockSensors = [
        {
          id: 1,
          name: 'Living Room Temperature',
          type: 'temperature',
          pin: 'A0',
          pin_type: 'analog',
          node_id: 'ESP32_001',
          enabled: true,
          update_interval: 2000,
          calibration_scale: 1.0,
          calibration_offset: 0.0
        },
        {
          id: 2,
          name: 'Kitchen Gas Sensor',
          type: 'gas',
          pin: '34',
          pin_type: 'analog',
          node_id: 'ESP32_001',
          enabled: true,
          update_interval: 1000,
          calibration_scale: 1.0,
          calibration_offset: 0.0
        }
      ];
      setSensors(mockSensors);
    } catch (error) {
      message.error('Failed to load sensors');
      console.error('Error loading sensors:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddSensor = () => {
    setEditingSensor(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEditSensor = (sensor) => {
    setEditingSensor(sensor);
    form.setFieldsValue(sensor);
    setModalVisible(true);
  };

  const handleSaveSensor = async (values) => {
    try {
      setLoading(true);
      
      if (editingSensor) {
        // Mock update - replace with actual API when available
        // await sensorAPI.updateSensor(editingSensor.id, values);
        const updatedSensors = sensors.map(s => 
          s.id === editingSensor.id ? { ...s, ...values } : s
        );
        setSensors(updatedSensors);
        message.success('Sensor updated successfully');
      } else {
        // Mock create - replace with actual API when available
        // await sensorAPI.createSensor(values);
        const newSensor = {
          id: Date.now(),
          ...values
        };
        setSensors([...sensors, newSensor]);
        message.success('Sensor added successfully');
      }
      
      setModalVisible(false);
      // loadSensors(); // Uncomment when using real API
    } catch (error) {
      message.error('Failed to save sensor');
      console.error('Error saving sensor:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSensor = async (sensorId) => {
    try {
      // Mock delete - replace with actual API when available
      // await sensorAPI.deleteSensor(sensorId);
      const updatedSensors = sensors.filter(s => s.id !== sensorId);
      setSensors(updatedSensors);
      message.success('Sensor deleted successfully');
      // loadSensors(); // Uncomment when using real API
    } catch (error) {
      message.error('Failed to delete sensor');
      console.error('Error deleting sensor:', error);
    }
  };

  const handleGenerateCode = async (sensor) => {
    try {
      setSelectedSensor(sensor);
      
      // Mock code generation - replace with actual API when available
      // const response = await sensorAPI.generateCode(sensor.id, 'arduino');
      // setGeneratedCode(response.data.code);
      
      const sensorType = sensorTypes[sensor.type];
      if (sensorType) {
        let code = sensorType.defaultCode;
        code = code.replace(/{{PIN}}/g, sensor.pin);
        code = code.replace(/{{SCALE}}/g, sensor.calibration_scale || 1.0);
        code = code.replace(/{{OFFSET}}/g, sensor.calibration_offset || 0.0);
        
        // Add full Arduino sketch
        const fullCode = `
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// WiFi Configuration
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// MQTT Configuration
const char* mqtt_server = "192.168.8.105";
const int mqtt_port = 1883;
const char* mqtt_user = "iotuser";
const char* mqtt_password = "iotpassword";

WiFiClient espClient;
PubSubClient client(espClient);

String node_id = "${sensor.node_id}";
String data_topic = "devices/" + node_id + "/data";

${code}

void setup() {
  Serial.begin(115200);
  
  // Initialize sensor pin
  pinMode(${sensor.pin}, ${sensor.pin_type === 'analog' ? 'INPUT' : 'INPUT'});
  
  // Initialize WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  
  // Initialize MQTT
  client.setServer(mqtt_server, mqtt_port);
  
  Serial.println("${sensor.name} initialized!");
}

void loop() {
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();
  
  // Read sensor data
  ${sensor.type === 'temperature' ? 'float sensorValue = readTemperature();' :
    sensor.type === 'humidity' ? 'float sensorValue = readHumidity();' :
    sensor.type === 'gas' ? 'int sensorValue = readGasSensor();' :
    sensor.type === 'motion' ? 'bool sensorValue = readMotionSensor();' :
    sensor.type === 'light' ? 'int sensorValue = readLightSensor();' : 'float sensorValue = 0;'}
  
  // Publish sensor data
  StaticJsonDocument<200> doc;
  doc["sensor_name"] = "${sensor.name}";
  doc["sensor_type"] = "${sensor.type}";
  doc["value"] = sensorValue;
  doc["node_id"] = node_id;
  doc["timestamp"] = millis();
  
  String payload;
  serializeJson(doc, payload);
  
  client.publish(data_topic.c_str(), payload.c_str());
  
  Serial.print("${sensor.name}: ");
  Serial.println(sensorValue);
  
  delay(${sensor.update_interval || 2000});
}

void reconnectMQTT() {
  while (!client.connected()) {
    if (client.connect(node_id.c_str(), mqtt_user, mqtt_password)) {
      Serial.println("MQTT connected");
    } else {
      delay(5000);
    }
  }
}
`;
        
        setGeneratedCode(fullCode);
        setCodeModalVisible(true);
      }
    } catch (error) {
      message.error('Failed to generate code');
      console.error('Error generating code:', error);
    }
  };

  const handleDownloadCode = () => {
    const element = document.createElement('a');
    const file = new Blob([generatedCode], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `${selectedSensor?.name || 'sensor'}_code.ino`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const handleFlashFirmware = async (sensor) => {
    try {
      setFirmwareUploading(true);
      setUploadProgress(0);
      
      // Mock firmware generation - replace with actual API when available
      // const codeResponse = await sensorAPI.generateCode(sensor.id, 'arduino');
      
      // Simulate firmware compilation and upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          const newProgress = prev + 10;
          if (newProgress >= 100) {
            clearInterval(progressInterval);
            return 100;
          }
          return newProgress;
        });
      }, 500);
      
      // Simulate firmware upload to ESP32
      setTimeout(async () => {
        try {
          // Mock firmware upload - replace with actual API when available
          // await firmwareAPI.uploadToDevice(sensor.node_id, codeResponse.data.code);
          
          message.success(`Firmware with ${sensor.name} flashed successfully to ESP32!`);
          setUploadProgress(0);
        } catch (error) {
          message.error('Failed to flash firmware');
          console.error('Firmware flash error:', error);
        } finally {
          setFirmwareUploading(false);
        }
      }, 5000);
      
    } catch (error) {
      message.error('Failed to prepare firmware');
      console.error('Error preparing firmware:', error);
      setFirmwareUploading(false);
    }
  };

  const handleSensorTypeChange = (sensorType) => {
    const typeConfig = sensorTypes[sensorType];
    if (typeConfig) {
      form.setFieldsValue({
        pin_type: typeConfig.pinType,
        pin: typeConfig.pins[0]
      });
    }
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <ExperimentOutlined style={{ color: '#1890ff' }} />
          <strong>{text}</strong>
        </Space>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type) => (
        <Tag color="blue">{sensorTypes[type]?.name || type}</Tag>
      ),
    },
    {
      title: 'Pin',
      dataIndex: 'pin',
      key: 'pin',
      render: (pin, record) => (
        <Tag color={record.pin_type === 'analog' ? 'orange' : 'green'}>
          {record.pin_type === 'analog' ? 'A' : 'D'}{pin}
        </Tag>
      ),
    },
    {
      title: 'Node ID',
      dataIndex: 'node_id',
      key: 'node_id',
      render: (nodeId) => (
        <Text code>{nodeId}</Text>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled) => (
        <Tag color={enabled ? 'success' : 'default'}>
          {enabled ? 'Enabled' : 'Disabled'}
        </Tag>
      ),
    },
    {
      title: 'Update Interval',
      dataIndex: 'update_interval',
      key: 'update_interval',
      render: (interval) => `${interval}ms`,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            icon={<EditOutlined />}
            size="small"
            onClick={() => handleEditSensor(record)}
          />
          <Button
            icon={<CodeOutlined />}
            size="small"
            onClick={() => handleGenerateCode(record)}
          />
          <Button
            icon={<ThunderboltOutlined />}
            size="small"
            type="primary"
            loading={firmwareUploading}
            onClick={() => handleFlashFirmware(record)}
          >
            Flash
          </Button>
          <Button
            icon={<DeleteOutlined />}
            size="small"
            danger
            onClick={() => handleDeleteSensor(record.id)}
          />
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card 
        title={
          <Space>
            <ExperimentOutlined />
            Dynamic Sensor Manager
          </Space>
        }
        extra={
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={handleAddSensor}
          >
            Add Sensor
          </Button>
        }
      >
        <Alert
          message="Dynamic Sensor Management"
          description="Add, configure, and manage sensors dynamically. Generate Arduino code and flash firmware to your ESP32 devices in real-time."
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        {firmwareUploading && (
          <Card style={{ marginBottom: 16 }}>
            <Title level={5}>Flashing Firmware...</Title>
            <Progress 
              percent={uploadProgress} 
              status={uploadProgress === 100 ? 'success' : 'active'}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
            />
            <Text type="secondary">
              {uploadProgress < 30 && 'Compiling sensor code...'}
              {uploadProgress >= 30 && uploadProgress < 60 && 'Preparing firmware...'}
              {uploadProgress >= 60 && uploadProgress < 90 && 'Uploading to ESP32...'}
              {uploadProgress >= 90 && 'Finalizing installation...'}
            </Text>
          </Card>
        )}

        <Table
          columns={columns}
          dataSource={sensors}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* Add/Edit Sensor Modal */}
      <Modal
        title={editingSensor ? 'Edit Sensor' : 'Add New Sensor'}
        visible={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveSensor}
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
                <Select
                  placeholder="Select sensor type"
                  onChange={handleSensorTypeChange}
                >
                  {Object.entries(sensorTypes).map(([key, value]) => (
                    <Option key={key} value={key}>
                      {value.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="pin"
                label="Pin"
                rules={[{ required: true, message: 'Please select pin' }]}
              >
                <Select placeholder="Select pin">
                  {form.getFieldValue('type') && 
                    sensorTypes[form.getFieldValue('type')]?.pins.map(pin => (
                      <Option key={pin} value={pin}>{pin}</Option>
                    ))
                  }
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="pin_type"
                label="Pin Type"
                rules={[{ required: true }]}
              >
                <Select disabled>
                  <Option value="analog">Analog</Option>
                  <Option value="digital">Digital</Option>
                  <Option value="i2c">I2C</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="node_id"
                label="Node ID"
                rules={[{ required: true, message: 'Please enter node ID' }]}
              >
                <Input placeholder="ESP32 Node ID" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="update_interval"
                label="Update Interval (ms)"
                initialValue={1000}
              >
                <InputNumber min={100} max={60000} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="calibration_scale"
                label="Calibration Scale"
                initialValue={1.0}
              >
                <InputNumber step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="calibration_offset"
                label="Calibration Offset"
                initialValue={0.0}
              >
                <InputNumber step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="threshold_min"
                label="Minimum Threshold"
              >
                <InputNumber style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="threshold_max"
                label="Maximum Threshold"
              >
                <InputNumber style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="description"
            label="Description"
          >
            <TextArea rows={3} placeholder="Optional description of the sensor" />
          </Form.Item>

          <Form.Item
            name="enabled"
            label="Enable Sensor"
            valuePropName="checked"
            initialValue={true}
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>

      {/* Code Generation Modal */}
      <Modal
        title={`Generated Code for ${selectedSensor?.name}`}
        visible={codeModalVisible}
        onCancel={() => setCodeModalVisible(false)}
        width={800}
        footer={[
          <Button key="download" icon={<DownloadOutlined />} onClick={handleDownloadCode}>
            Download Code
          </Button>,
          <Button key="close" onClick={() => setCodeModalVisible(false)}>
            Close
          </Button>,
        ]}
      >
        <pre style={{ 
          background: '#f5f5f5', 
          padding: '16px', 
          borderRadius: '4px',
          maxHeight: '400px',
          overflow: 'auto'
        }}>
          <code>{generatedCode}</code>
        </pre>
      </Modal>
    </div>
  );
};

export default DynamicSensorManager;
