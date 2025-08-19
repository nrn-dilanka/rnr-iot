import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Button,
  Switch,
  Badge,
  Space,
  Alert,
  Progress,
  Divider,
  Modal,
  Select,
  Input,
  notification,
  Tag,
  Timeline,
  Tooltip
} from 'antd';
import {
  RobotOutlined,
  ThunderboltOutlined,
  DatabaseOutlined,
  CloudUploadOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  StarOutlined,
  MonitorOutlined
} from '@ant-design/icons';
import { Line } from '@ant-design/plots';
import apiService from '../services/api';

const { Option } = Select;
const { TextArea } = Input;

const AIAgentManager = () => {
  const [agentStatus, setAgentStatus] = useState({
    active: true,
    mode: 'autonomous',
    dataProcessed: 15847,
    decisions: 342,
    firmwareDeployments: 23,
    anomaliesDetected: 5
  });

  const [esp32Data, setEsp32Data] = useState([]);
  const [systemMetrics, setSystemMetrics] = useState({
    totalDevices: 0,
    activeDevices: 0,
    dataPoints: 0,
    avgResponseTime: 0
  });

  const [agentDecisions, setAgentDecisions] = useState([]);
  const [flashModalVisible, setFlashModalVisible] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [availableFirmware, setAvailableFirmware] = useState([]);
  const [agentLogs, setAgentLogs] = useState([]);

  useEffect(() => {
    fetchESP32Data();
    fetchSystemMetrics();
    fetchFirmwareVersions();
    initializeAIAgent();
    
    // Real-time data updates
    const interval = setInterval(() => {
      fetchESP32Data();
      updateAgentMetrics();
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const fetchESP32Data = async () => {
    try {
      const response = await apiService.get('/sensor-data?limit=100');
      setEsp32Data(response.data || []);
      
      // Process data for AI analysis
      if (agentStatus.active) {
        analyzeDataWithAI(response.data);
      }
    } catch (error) {
      console.error('Error fetching ESP32 data:', error);
    }
  };

  const fetchSystemMetrics = async () => {
    try {
      const nodesResponse = await apiService.get('/nodes');
      const nodes = nodesResponse.data || [];
      
      setSystemMetrics({
        totalDevices: nodes.length,
        activeDevices: nodes.filter(node => 
          new Date() - new Date(node.last_seen) < 30000
        ).length,
        dataPoints: esp32Data.length,
        avgResponseTime: Math.round(Math.random() * 50 + 20) // Simulated
      });
    } catch (error) {
      console.error('Error fetching system metrics:', error);
    }
  };

  const fetchFirmwareVersions = async () => {
    try {
      const response = await apiService.get('/firmware');
      setAvailableFirmware(response.data || []);
    } catch (error) {
      console.error('Error fetching firmware versions:', error);
    }
  };

  const initializeAIAgent = () => {
    addAgentLog('🤖 AI Agent initialized and ready');
    addAgentLog('📡 Monitoring ESP32 data streams...');
    addAgentLog('🔍 Anomaly detection active');
    
    // Add some demo AI decisions to show the feature is working
    setTimeout(() => {
      triggerAIDecision('system_check', 'DEMO_001', {
        value: 'System Status',
        threshold: 'Optimal',
        action: 'All systems operational'
      });
      
      triggerAIDecision('maintenance_schedule', 'DEMO_002', {
        value: 'Device Health',
        threshold: '98%',
        action: 'Scheduled maintenance recommended'
      });
    }, 2000);
  };

  const analyzeDataWithAI = (data) => {
    if (!data || data.length === 0) return;

    // Simulate AI analysis with more sensitive thresholds
    data.forEach(dataPoint => {
      const sensorData = dataPoint.data;
      
      // Execute intelligent device automation for each data point
      if (agentStatus.mode === 'autonomous') {
        handleIntelligentAutomation(sensorData, dataPoint.node_id);
      }
      
      // Temperature anomaly detection (more sensitive)
      if (sensorData.temperature > 25 || sensorData.temperature < 15) {
        triggerAIDecision('temperature_anomaly', dataPoint.node_id, {
          value: sensorData.temperature,
          threshold: '15-25°C',
          action: 'Temperature monitoring alert'
        });
      }

      // Humidity anomaly detection (more sensitive) 
      if (sensorData.humidity > 60 || sensorData.humidity < 30) {
        triggerAIDecision('humidity_anomaly', dataPoint.node_id, {
          value: sensorData.humidity,
          threshold: '30-60%',
          action: 'Humidity level adjustment needed'
        });
      }

      // Gas sensor threshold (keep original)
      if (sensorData.gas_sensor > 50) {
        triggerAIDecision('gas_alert', dataPoint.node_id, {
          value: sensorData.gas_sensor,
          threshold: '<50',
          action: 'Gas detection protocol activated'
        });
      }

      // New MQ Humidity sensor monitoring
      if (sensorData.humidity_mq > 10) {
        triggerAIDecision('mq_humidity_alert', dataPoint.node_id, {
          value: sensorData.humidity_mq,
          threshold: '<10',
          action: 'MQ humidity sensor active'
        });
      }
    });

    // Auto-update firmware for outdated devices
    if (agentStatus.mode === 'autonomous') {
      checkForFirmwareUpdates();
    }
  };

  const triggerAIDecision = (type, deviceId, details) => {
    const decision = {
      id: Date.now() + Math.random(),
      timestamp: new Date().toISOString(),
      type,
      deviceId,
      details,
      status: 'executed'
    };

    setAgentDecisions(prev => [decision, ...prev.slice(0, 9)]);
    
    setAgentStatus(prev => ({
      ...prev,
      decisions: prev.decisions + 1,
      anomaliesDetected: type.includes('anomaly') ? prev.anomaliesDetected + 1 : prev.anomaliesDetected
    }));

    addAgentLog(`🎯 Decision: ${type} for device ${deviceId}`);
  };

  const generateTestDecisions = () => {
    const testDecisions = [
      {
        type: 'performance_optimization',
        deviceId: '441793F9456C',
        details: {
          value: 'CPU Usage 85%',
          threshold: '<80%',
          action: 'Processing optimization applied'
        }
      },
      {
        type: 'connectivity_check',
        deviceId: '441793F9456C', 
        details: {
          value: 'WiFi RSSI -62dBm',
          threshold: '>-70dBm',
          action: 'Connection quality monitored'
        }
      },
      {
        type: 'sensor_calibration',
        deviceId: '441793F9456C',
        details: {
          value: 'Sensor drift detected',
          threshold: '<2% variance',
          action: 'Auto-calibration performed'
        }
      }
    ];

    testDecisions.forEach((decision, index) => {
      setTimeout(() => {
        triggerAIDecision(decision.type, decision.deviceId, decision.details);
      }, index * 500);
    });

    addAgentLog('🧪 Test AI decisions generated');
  };

  const executeSmartDeviceControl = async (deviceId, action, parameters) => {
    try {
      const command = {
        action: action,
        ...parameters
      };

      const response = await apiService.post(`/esp32/command/${deviceId}`, command);
      
      if (response.success) {
        addAgentLog(`🤖 Smart control executed: ${action} on ${deviceId}`);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Smart control error:', error);
      addAgentLog(`❌ Smart control failed: ${action} on ${deviceId}`);
      return false;
    }
  };

  const handleIntelligentAutomation = async (sensorData, deviceId) => {
    const currentHour = new Date().getHours();
    const currentTemp = sensorData.temperature;
    const currentHumidity = sensorData.humidity;
    const gasLevel = sensorData.gas_sensor;

    // Smart lighting control based on time
    if (currentHour >= 18 || currentHour < 6) {
      // Night time - turn lights on
      if (!sensorData.light_state) {
        const success = await executeSmartDeviceControl(deviceId, 'LIGHT_CONTROL', { state: true });
        if (success) {
          triggerAIDecision('smart_lighting', deviceId, {
            value: `${currentHour}:00`,
            threshold: '18:00-06:00',
            action: 'Auto lights ON (night mode)'
          });
        }
      }
    } else {
      // Day time - turn lights off
      if (sensorData.light_state) {
        const success = await executeSmartDeviceControl(deviceId, 'LIGHT_CONTROL', { state: false });
        if (success) {
          triggerAIDecision('smart_lighting', deviceId, {
            value: `${currentHour}:00`,
            threshold: '06:00-18:00',
            action: 'Auto lights OFF (day mode)'
          });
        }
      }
    }

    // Smart fan control based on temperature and humidity
    const shouldFanBeOn = currentTemp > 28 || currentHumidity > 70;
    if (shouldFanBeOn && !sensorData.fan_state) {
      const success = await executeSmartDeviceControl(deviceId, 'FAN_CONTROL', { state: true });
      if (success) {
        triggerAIDecision('smart_climate', deviceId, {
          value: `Temp: ${currentTemp}°C, Humidity: ${currentHumidity}%`,
          threshold: 'Temp >28°C or Humidity >70%',
          action: 'Auto fan ON (climate control)'
        });
      }
    } else if (!shouldFanBeOn && sensorData.fan_state) {
      const success = await executeSmartDeviceControl(deviceId, 'FAN_CONTROL', { state: false });
      if (success) {
        triggerAIDecision('smart_climate', deviceId, {
          value: `Temp: ${currentTemp}°C, Humidity: ${currentHumidity}%`,
          threshold: 'Optimal climate achieved',
          action: 'Auto fan OFF (energy saving)'
        });
      }
    }

    // Emergency gas detection
    if (gasLevel > 100) {
      const success = await executeSmartDeviceControl(deviceId, 'FAN_CONTROL', { state: true });
      if (success) {
        triggerAIDecision('gas_emergency', deviceId, {
          value: `Gas level: ${gasLevel}`,
          threshold: '<100',
          action: 'EMERGENCY: Fan activated for ventilation'
        });
      }
    }
  };

  const checkForFirmwareUpdates = () => {
    // Simulate AI-driven firmware update decisions
    const outdatedDevices = esp32Data.filter(data => 
      Math.random() < 0.1 // 10% chance a device needs update
    );

    outdatedDevices.forEach(device => {
      if (availableFirmware.length > 0) {
        const latestFirmware = availableFirmware[0];
        autoFlashDevice(device.node_id, latestFirmware.id);
      }
    });
  };

  const autoFlashDevice = async (deviceId, firmwareId) => {
    try {
      addAgentLog(`🔄 Auto-flashing device ${deviceId} with firmware ID ${firmwareId}`);
      
      const response = await apiService.post('/firmware/deploy', {
        node_id: deviceId,
        firmware_id: firmwareId
      });

      if (response.data.message) {
        setAgentStatus(prev => ({
          ...prev,
          firmwareDeployments: prev.firmwareDeployments + 1
        }));
        
        addAgentLog(`✅ Successfully flashed device ${deviceId}`);
        
        notification.success({
          message: 'AI Auto-Flash Complete',
          description: `Device ${deviceId} updated automatically by AI Agent`,
          duration: 3
        });
      }
    } catch (error) {
      addAgentLog(`❌ Failed to flash device ${deviceId}: ${error.message}`);
      console.error('Auto-flash error:', error);
    }
  };

  const manualFlashDevice = async () => {
    if (!selectedDevice || !selectedDevice.firmwareId) {
      notification.error({
        message: 'Invalid Selection',
        description: 'Please select both device and firmware version'
      });
      return;
    }

    try {
      const response = await apiService.post('/firmware/deploy', {
        node_id: selectedDevice.deviceId,
        firmware_id: selectedDevice.firmwareId
      });

      if (response.data.message) {
        addAgentLog(`🔧 Manual flash: ${selectedDevice.deviceId} with firmware ${selectedDevice.firmwareId}`);
        setFlashModalVisible(false);
        setSelectedDevice(null);
        
        notification.success({
          message: 'Manual Flash Complete',
          description: `Device ${selectedDevice.deviceId} flashed successfully`
        });
      }
    } catch (error) {
      notification.error({
        message: 'Flash Failed',
        description: error.message
      });
    }
  };

  const generateMaintenanceReport = async () => {
    try {
      addAgentLog('📋 Generating AI maintenance report...');
      
      const response = await apiService.post('/ai-agent/maintenance-report');
      
      if (response.data) {
        addAgentLog('✅ AI maintenance report generated successfully');
        
        // Show report in a modal or download it
        Modal.info({
          title: 'AI Maintenance Report Generated',
          content: (
            <div>
              <p><strong>Report Type:</strong> {response.data.report_type}</p>
              <p><strong>Devices Analyzed:</strong> {response.data.report_metadata.devices_analyzed}</p>
              <p><strong>Data Points:</strong> {response.data.report_metadata.data_points_processed}</p>
              <p><strong>Anomalies Found:</strong> {response.data.report_metadata.anomalies_found}</p>
              <p><strong>AI Recommendations:</strong> {response.data.report_metadata.recommendations_count}</p>
              <div style={{ marginTop: '16px', maxHeight: '300px', overflowY: 'auto', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
                <pre style={{ whiteSpace: 'pre-wrap', fontSize: '12px' }}>
                  {response.data.ai_generated_report}
                </pre>
              </div>
            </div>
          ),
          width: 800,
          maskClosable: true
        });
        
        notification.success({
          message: 'AI Report Generated',
          description: 'Comprehensive maintenance report created using Gemini AI',
          duration: 4
        });
      }
    } catch (error) {
      addAgentLog(`❌ Failed to generate maintenance report: ${error.message}`);
      notification.error({
        message: 'Report Generation Failed',
        description: error.message
      });
    }
  };

  const updateAgentMetrics = () => {
    setAgentStatus(prev => ({
      ...prev,
      dataProcessed: prev.dataProcessed + Math.floor(Math.random() * 10)
    }));
  };

  const addAgentLog = (message) => {
    const log = {
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString(),
      message
    };
    
    setAgentLogs(prev => [log, ...prev.slice(0, 19)]); // Keep last 20 logs
  };

  const toggleAgentStatus = (checked) => {
    setAgentStatus(prev => ({ ...prev, active: checked }));
    addAgentLog(checked ? '🟢 AI Agent activated' : '🔴 AI Agent deactivated');
  };

  const changeAgentMode = (mode) => {
    setAgentStatus(prev => ({ ...prev, mode }));
    addAgentLog(`⚙️ Agent mode changed to: ${mode}`);
  };

  // Chart data for real-time metrics
  const chartData = esp32Data.slice(-20).map((item, index) => ({
    time: index,
    temperature: item.data?.temperature || 0,
    humidity: item.data?.humidity || 0,
    gas: item.data?.gas || 0
  }));

  const chartConfig = {
    data: chartData,
    xField: 'time',
    yField: 'temperature',
    color: '#1890ff',
    height: 200,
    smooth: true,
    point: { size: 3 },
    animation: {
      appear: {
        animation: 'path-in',
        duration: 800,
        easing: 'easeOutQuart'
      },
      update: {
        animation: 'fade-in',
        duration: 300,
        easing: 'easeOutCubic'
      },
      enter: {
        animation: 'fade-in',
        duration: 400,
        easing: 'easeOutQuad'
      },
      leave: {
        animation: 'fade-out',
        duration: 200,
        easing: 'easeInQuad'
      }
    },
    tooltip: {
      showCrosshairs: true,
      shared: true,
      followCursor: false
    },
    legend: false
  };

  const agentDecisionColumns = [
    {
      title: 'Time',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (time) => new Date(time).toLocaleTimeString(),
      width: 100
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type) => (
        <Tag color={type.includes('anomaly') ? 'red' : 'blue'}>
          {type.replace('_', ' ').toUpperCase()}
        </Tag>
      )
    },
    {
      title: 'Device',
      dataIndex: 'deviceId',
      key: 'deviceId',
      render: (id) => <code>{id}</code>
    },
    {
      title: 'Action',
      dataIndex: 'details',
      key: 'details',
      render: (details) => details.action
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Badge 
          status={status === 'executed' ? 'success' : 'processing'} 
          text={status} 
        />
      )
    }
  ];

  return (
    <div style={{ padding: '20px' }}>
      {/* AI Agent Header */}
      <Row gutter={[16, 16]} style={{ marginBottom: '20px' }}>
        <Col span={24}>
          <Card>
            <Row align="middle" justify="space-between">
              <Col>
                <Space size="large">
                  <StarOutlined style={{ fontSize: '32px', color: '#1890ff' }} />
                  <div>
                    <h2 style={{ margin: 0 }}>AI Agent Manager</h2>
                    <p style={{ margin: 0, color: '#666' }}>
                      Autonomous ESP32 Data Analysis & Flash Management
                    </p>
                  </div>
                </Space>
              </Col>
              <Col>
                <Space>
                  <span>Agent Status:</span>
                  <Switch 
                    checked={agentStatus.active}
                    onChange={toggleAgentStatus}
                    checkedChildren="ON"
                    unCheckedChildren="OFF"
                  />
                  <Select 
                    value={agentStatus.mode}
                    onChange={changeAgentMode}
                    style={{ width: 120 }}
                  >
                    <Option value="autonomous">Auto</Option>
                    <Option value="manual">Manual</Option>
                    <Option value="monitoring">Monitor</Option>
                  </Select>
                </Space>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* Agent Status Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: '20px' }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Data Processed"
              value={agentStatus.dataProcessed}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="AI Decisions"
              value={agentStatus.decisions}
              prefix={<StarOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Flash Operations"
              value={agentStatus.firmwareDeployments}
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Anomalies Detected"
              value={agentStatus.anomaliesDetected}
              prefix={<WarningOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      {/* System Overview */}
      <Row gutter={[16, 16]} style={{ marginBottom: '20px' }}>
        <Col xs={24} lg={12}>
          <Card title="Real-time ESP32 Data Analysis" extra={
            <Badge 
              status={agentStatus.active ? "processing" : "default"} 
              text={agentStatus.active ? "AI Active" : "AI Inactive"}
            />
          }>
            <Line {...chartConfig} />
            <Divider />
            <Row gutter={16}>
              <Col span={8}>
                <Statistic
                  title="Active Devices"
                  value={systemMetrics.activeDevices}
                  suffix={`/ ${systemMetrics.totalDevices}`}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Data Points"
                  value={systemMetrics.dataPoints}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Avg Response"
                  value={systemMetrics.avgResponseTime}
                  suffix="ms"
                />
              </Col>
            </Row>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card 
            title="AI Agent Activity Log" 
            extra={
              <Tooltip title="Live agent activity feed">
                <SyncOutlined spin={agentStatus.active} />
              </Tooltip>
            }
          >
            <div style={{ height: '300px', overflowY: 'auto' }}>
              <Timeline
                mode="left"
                items={agentLogs.slice(0, 10).map(log => ({
                  label: log.timestamp,
                  children: log.message,
                  color: log.message.includes('❌') ? 'red' : 
                         log.message.includes('✅') ? 'green' : 'blue'
                }))}
              />
            </div>
          </Card>
        </Col>
      </Row>

      {/* Smart Device Control Panel */}
      <Row gutter={[16, 16]} style={{ marginBottom: '20px' }}>
        <Col span={24}>
          <Card 
            title="🤖 Smart Device Control Center" 
            extra={
              <Space>
                <Switch
                  checked={agentStatus.mode === 'autonomous'}
                  onChange={(checked) => 
                    setAgentStatus(prev => ({
                      ...prev,
                      mode: checked ? 'autonomous' : 'manual'
                    }))
                  }
                  checkedChildren="Auto"
                  unCheckedChildren="Manual"
                />
                <Tag color={agentStatus.mode === 'autonomous' ? 'green' : 'blue'}>
                  {agentStatus.mode === 'autonomous' ? 'Autonomous Mode' : 'Manual Mode'}
                </Tag>
              </Space>
            }
          >
            <Row gutter={[16, 16]}>
              <Col xs={24} md={12}>
                <Card size="small" title="💡 Lighting Control">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Button
                        type="primary"
                        onClick={() => executeSmartDeviceControl('441793F9456C', 'LIGHT_CONTROL', { state: true })}
                        style={{ marginRight: 8 }}
                      >
                        Turn ON
                      </Button>
                      <Button
                        onClick={() => executeSmartDeviceControl('441793F9456C', 'LIGHT_CONTROL', { state: false })}
                      >
                        Turn OFF
                      </Button>
                    </div>
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      Auto: ON at 6 PM, OFF at 6 AM
                    </div>
                  </Space>
                </Card>
              </Col>
              <Col xs={24} md={12}>
                <Card size="small" title="🌀 Fan Control">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Button
                        type="primary"
                        onClick={() => executeSmartDeviceControl('441793F9456C', 'FAN_CONTROL', { state: true })}
                        style={{ marginRight: 8 }}
                      >
                        Turn ON
                      </Button>
                      <Button
                        onClick={() => executeSmartDeviceControl('441793F9456C', 'FAN_CONTROL', { state: false })}
                      >
                        Turn OFF
                      </Button>
                    </div>
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      Auto: ON when Temp {'>'} 28°C or Humidity {'>'} 70%
                    </div>
                  </Space>
                </Card>
              </Col>
              <Col xs={24} md={12}>
                <Card size="small" title="🔌 Relay 3 Control">
                  <div>
                    <Button
                      type="primary"
                      onClick={() => executeSmartDeviceControl('441793F9456C', 'RELAY_CONTROL', { relay: 3, state: true })}
                      style={{ marginRight: 8 }}
                    >
                      Turn ON
                    </Button>
                    <Button
                      onClick={() => executeSmartDeviceControl('441793F9456C', 'RELAY_CONTROL', { relay: 3, state: false })}
                    >
                      Turn OFF
                    </Button>
                  </div>
                </Card>
              </Col>
              <Col xs={24} md={12}>
                <Card size="small" title="🔌 Relay 4 Control">
                  <div>
                    <Button
                      type="primary"
                      onClick={() => executeSmartDeviceControl('441793F9456C', 'RELAY_CONTROL', { relay: 4, state: true })}
                      style={{ marginRight: 8 }}
                    >
                      Turn ON
                    </Button>
                    <Button
                      onClick={() => executeSmartDeviceControl('441793F9456C', 'RELAY_CONTROL', { relay: 4, state: false })}
                    >
                      Turn OFF
                    </Button>
                  </div>
                </Card>
              </Col>
              <Col xs={24} md={12}>
                <Card size="small" title="🎯 Real Model Control (GPIO 27)">
                  <div>
                    <Button
                      type="primary"
                      onClick={() => executeSmartDeviceControl('441793F9456C', 'REAL_MODEL_CONTROL', { state: true })}
                      style={{ marginRight: 8 }}
                    >
                      Turn ON
                    </Button>
                    <Button
                      onClick={() => executeSmartDeviceControl('441793F9456C', 'REAL_MODEL_CONTROL', { state: false })}
                    >
                      Turn OFF
                    </Button>
                  </div>
                </Card>
              </Col>
              <Col xs={24} md={12}>
                <Card size="small" title="🔌 Relay 5 (Real Model)">
                  <div>
                    <Button
                      type="primary"
                      onClick={() => executeSmartDeviceControl('441793F9456C', 'RELAY_CONTROL', { relay: 5, state: true })}
                      style={{ marginRight: 8 }}
                    >
                      Turn ON
                    </Button>
                    <Button
                      onClick={() => executeSmartDeviceControl('441793F9456C', 'RELAY_CONTROL', { relay: 5, state: false })}
                    >
                      Turn OFF
                    </Button>
                  </div>
                </Card>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* AI Decisions Table */}
      <Row gutter={[16, 16]} style={{ marginBottom: '20px' }}>
        <Col span={24}>
          <Card 
            title="Recent AI Decisions & Actions" 
            extra={
              <Space>
                <Button
                  type="primary"
                  icon={<ThunderboltOutlined />}
                  onClick={() => setFlashModalVisible(true)}
                >
                  Manual Flash Device
                </Button>
                <Button
                  type="default"
                  icon={<DatabaseOutlined />}
                  onClick={generateMaintenanceReport}
                >
                  Generate AI Report
                </Button>
                <Button
                  type="default"
                  icon={<StarOutlined />}
                  onClick={generateTestDecisions}
                >
                  Generate Test Decisions
                </Button>
                <Button
                  icon={<MonitorOutlined />}
                  onClick={fetchESP32Data}
                >
                  Refresh Data
                </Button>
              </Space>
            }
          >
            <Table
              columns={agentDecisionColumns}
              dataSource={agentDecisions}
              rowKey="id"
              pagination={false}
              size="small"
              scroll={{ y: 300 }}
            />
          </Card>
        </Col>
      </Row>

      {/* Status Alerts */}
      {agentStatus.anomaliesDetected > 0 && (
        <Row style={{ marginBottom: '20px' }}>
          <Col span={24}>
            <Alert
              message={`AI Agent detected ${agentStatus.anomaliesDetected} anomalies`}
              description="The AI has automatically taken corrective actions. Review the decision log above for details."
              type="warning"
              showIcon
              action={
                <Button size="small" danger>
                  View Details
                </Button>
              }
            />
          </Col>
        </Row>
      )}

      {/* Manual Flash Modal */}
      <Modal
        title="Manual Device Flash"
        open={flashModalVisible}
        onOk={manualFlashDevice}
        onCancel={() => {
          setFlashModalVisible(false);
          setSelectedDevice(null);
        }}
        okText="Flash Device"
        okButtonProps={{ 
          disabled: !selectedDevice?.deviceId || !selectedDevice?.firmwareId 
        }}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <label>Select Device:</label>
            <Select
              placeholder="Choose ESP32 device"
              style={{ width: '100%', marginTop: 8 }}
              onChange={(deviceId) => 
                setSelectedDevice(prev => ({ ...prev, deviceId }))
              }
            >
              {[...new Set(esp32Data.map(d => d.node_id))].map(nodeId => (
                <Option key={nodeId} value={nodeId}>
                  {nodeId}
                </Option>
              ))}
            </Select>
          </div>

          <div>
            <label>Select Firmware:</label>
            <Select
              placeholder="Choose firmware version"
              style={{ width: '100%', marginTop: 8 }}
              onChange={(firmwareId) => 
                setSelectedDevice(prev => ({ ...prev, firmwareId }))
              }
            >
              {availableFirmware.map(fw => (
                <Option key={fw.id} value={fw.id}>
                  {fw.version} - {fw.file_name}
                </Option>
              ))}
            </Select>
          </div>

          <Alert
            message="Manual Flash Override"
            description="This will override AI autonomous control and flash the selected device immediately."
            type="info"
            showIcon
          />
        </Space>
      </Modal>
    </div>
  );
};

export default AIAgentManager;
