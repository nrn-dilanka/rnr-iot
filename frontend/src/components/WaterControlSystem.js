import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Switch,
  Button,
  Progress,
  Slider,
  Select,
  Input,
  Table,
  Tag,
  Modal,
  Form,
  TimePicker,
  notification,
  Divider,
  Badge,
  Alert,
  Tabs,
  message
} from 'antd';
import {
  ExperimentOutlined,
  FireOutlined,
  DashboardOutlined,
  ControlOutlined,
  ScheduleOutlined,
  SettingOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  AlertOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  PlusOutlined,
  ReloadOutlined
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
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import moment from 'moment';
import { waterControlAPI } from '../services/api';
import WebSocketService from '../services/WebSocketService';

const { Option } = Select;
const { TabPane } = Tabs;

const WaterControlSystem = () => {
  // State management
  const [waterSystems, setWaterSystems] = useState([]);
  const [waterSchedules, setWaterSchedules] = useState([]);
  const [waterAlerts, setWaterAlerts] = useState([]);
  const [waterUsageData, setWaterUsageData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedSystem, setSelectedSystem] = useState(null);
  const [form] = Form.useForm();
  const wsService = WebSocketService.getInstance();

  // Load initial data
  useEffect(() => {
    loadWaterSystems();
    loadWaterSchedules();
    loadWaterUsageData();
    loadWaterAlerts();
    
    // Setup WebSocket connection and listeners
    setupWebSocketListeners();
    
    return () => {
      // Cleanup WebSocket listeners on unmount
      wsService.unsubscribe('water_system_update', handleWaterSystemUpdate);
      wsService.unsubscribe('water_schedule_update', handleWaterScheduleUpdate);
      wsService.unsubscribe('water_alert', handleWaterAlert);
      wsService.unsubscribe('water_usage_update', handleWaterUsageUpdate);
    };
  }, []);

  const setupWebSocketListeners = () => {
    // Connect to WebSocket if not already connected
    if (!wsService.isConnected()) {
      wsService.connect(
        () => console.log('Water Control WebSocket connected'),
        () => console.log('Water Control WebSocket disconnected'),
        (error) => console.error('Water Control WebSocket error:', error)
      );
    }

    // Subscribe to water-related events
    wsService.subscribe('water_system_update', handleWaterSystemUpdate);
    wsService.subscribe('water_schedule_update', handleWaterScheduleUpdate);
    wsService.subscribe('water_alert', handleWaterAlert);
    wsService.subscribe('water_usage_update', handleWaterUsageUpdate);
  };

  const handleWaterSystemUpdate = (data) => {
    console.log('Real-time water system update:', data);
    setWaterSystems(prevSystems => 
      prevSystems.map(system => 
        system.id === data.system_id ? data.data : system
      )
    );
  };

  const handleWaterScheduleUpdate = (data) => {
    console.log('Real-time water schedule update:', data);
    setWaterSchedules(prevSchedules => 
      prevSchedules.map(schedule => 
        schedule.id === data.schedule_id ? data.data : schedule
      )
    );
  };

  const handleWaterAlert = (data) => {
    console.log('Real-time water alert:', data);
    setWaterAlerts(prevAlerts => [data.data, ...prevAlerts]);
    
    // Show notification for new alerts
    if (!data.data.acknowledged) {
      notification[data.data.type === 'warning' ? 'warning' : 'info']({
        message: 'Water System Alert',
        description: data.data.message,
        duration: 5,
      });
    }
  };

  const handleWaterUsageUpdate = (data) => {
    console.log('Real-time water usage update:', data);
    setWaterUsageData(prevData => [...prevData, ...data.data.usage_data]);
  };

  // Periodic data refresh for consistency
  useEffect(() => {
    const interval = setInterval(() => {
      // Refresh data every 30 seconds to ensure consistency
      loadWaterSystems();
      loadWaterSchedules();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const loadWaterSystems = async () => {
    try {
      setLoading(true);
      console.log('Loading water systems...');
      const response = await waterControlAPI.getSystems();
      console.log('Water systems response:', response);
      // Handle different response structures
      const systems = response.systems || response.data || [];
      console.log('Parsed systems:', systems);
      setWaterSystems(Array.isArray(systems) ? systems : []);
    } catch (error) {
      console.error('Error loading water systems:', error);
      message.error('Failed to load water systems');
      // Use mock data as fallback
      setWaterSystems([
        {
          id: 1,
          name: 'Main Irrigation System',
          type: 'irrigation',
          status: 'active',
          flow_rate: 15.5,
          pressure: 2.3,
          temperature: 22.5,
          ph: 7.2,
          tds: 450,
          valve: { status: 'open', position: 75 },
          pump: { status: 'running', speed: 80, power: 1.2 },
          lastUpdate: new Date()
        },
        {
          id: 2,
          name: 'Greenhouse Water Supply',
          type: 'supply',
          status: 'active',
          flowRate: 8.2,
          pressure: 1.8,
          temperature: 24.1,
          ph: 6.8,
          tds: 380,
          valve: { status: 'open', position: 60 },
          pump: { status: 'running', speed: 65, power: 0.8 },
          lastUpdate: new Date()
        },
        {
          id: 3,
          name: 'Drainage System',
          type: 'drainage',
          status: 'standby',
          flowRate: 0,
          pressure: 0.5,
          temperature: 18.9,
          ph: null,
          tds: null,
          valve: { status: 'closed', position: 0 },
          pump: { status: 'stopped', speed: 0, power: 0 },
          lastUpdate: new Date()
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const loadWaterSchedules = async () => {
    try {
      const response = await waterControlAPI.getSchedules();
      // Handle different response structures
      const schedules = response.schedules || response.data || [];
      setWaterSchedules(Array.isArray(schedules) ? schedules : []);
    } catch (error) {
      console.error('Error loading schedules:', error);
      // Use mock data as fallback
      setWaterSchedules([
        {
          id: 1,
          name: 'Morning Irrigation',
          systemId: 1,
          startTime: '06:00',
          duration: 30,
          flowRate: 20,
          frequency: 'daily',
          enabled: true,
          lastRun: new Date(Date.now() - 2 * 60 * 60 * 1000),
          nextRun: new Date(Date.now() + 22 * 60 * 60 * 1000)
        },
        {
          id: 2,
          name: 'Evening Irrigation',
          systemId: 1,
          startTime: '18:00',
          duration: 25,
          flowRate: 18,
          frequency: 'daily',
          enabled: true,
          lastRun: new Date(Date.now() - 6 * 60 * 60 * 1000),
          nextRun: new Date(Date.now() + 18 * 60 * 60 * 1000)
        }
      ]);
    }
  };

  const loadWaterUsageData = async () => {
    try {
      const response = await waterControlAPI.getUsageData();
      // Handle different response structures
      const usageData = response.usage_data || response.data || [];
      setWaterUsageData(Array.isArray(usageData) ? usageData : []);
    } catch (error) {
      console.error('Error loading usage data:', error);
      // Use mock data as fallback
      setWaterUsageData([
        { time: '00:00', irrigation: 0, supply: 15, drainage: 5 },
        { time: '06:00', irrigation: 120, supply: 25, drainage: 8 },
        { time: '12:00', irrigation: 80, supply: 35, drainage: 12 },
        { time: '18:00', irrigation: 150, supply: 20, drainage: 6 },
        { time: '24:00', irrigation: 0, supply: 18, drainage: 4 }
      ]);
    }
  };

  const loadWaterAlerts = async () => {
    try {
      // Note: This would be a separate alerts API endpoint
      setWaterAlerts([
        {
          id: 1,
          type: 'warning',
          message: 'Low water pressure detected in Greenhouse Supply',
          timestamp: new Date(Date.now() - 15 * 60 * 1000),
          systemId: 2,
          acknowledged: false
        },
        {
          id: 2,
          type: 'info',
          message: 'Scheduled irrigation completed successfully',
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
          systemId: 1,
          acknowledged: true
        }
      ]);
    } catch (error) {
      console.error('Error loading alerts:', error);
    }
  };

  // Manual control functions
  const handleValveControl = async (systemId, action) => {
    try {
      const system = waterSystems.find(s => s.id === systemId);
      if (!system) return;

      // Call the API to control the valve
      const response = await waterControlAPI.controlValve(systemId, action);
      
      // Update local state with response data
      setWaterSystems(prev => prev.map(sys => {
        if (sys.id === systemId) {
          return {
            ...sys,
            valve_position: response.system.valve_position,
            valve_status: response.system.valve_status,
            updated_at: response.system.updated_at
          };
        }
        return sys;
      }));
      
      message.success(`Valve ${action}ed successfully`);
    } catch (error) {
      console.error('Error controlling valve:', error);
      message.error(`Failed to ${action} valve`);
    }
  };

  const handlePumpControl = async (systemId, action, speed = null) => {
    try {
      const system = waterSystems.find(s => s.id === systemId);
      if (!system) return;

      // Call API to control pump
      const response = await waterControlAPI.controlPump(systemId, action, speed);
      
      // Update local state with response data
      setWaterSystems(prev => prev.map(sys => {
        if (sys.id === systemId) {
          return {
            ...sys,
            pump_speed: response.system.pump_speed,
            pump_status: response.system.pump_status,
            pump_power: response.system.pump_power,
            updated_at: response.system.updated_at
          };
        }
        return sys;
      }));
      
      message.success(`Pump ${action}ed successfully`);
    } catch (error) {
      console.error('Error controlling pump:', error);
      message.error(`Failed to ${action} pump`);
    }
  };

  const handleFlowRateChange = async (systemId, value) => {
    try {
      // Update system configuration via API
      const system = waterSystems.find(s => s.id === systemId);
      if (system) {
        await waterControlAPI.updateSystem(systemId, { ...system, flowRate: value });
      }
      
      setWaterSystems(prev => prev.map(system => {
        if (system.id === systemId) {
          return {
            ...system,
            flowRate: value,
            lastUpdate: new Date()
          };
        }
        return system;
      }));
    } catch (error) {
      console.error('Error updating flow rate:', error);
      message.error('Failed to update flow rate');
    }
  };

  const handleScheduleToggle = async (scheduleId, enabled) => {
    try {
      if (enabled) {
        await waterControlAPI.activateSchedule(scheduleId);
      } else {
        await waterControlAPI.deactivateSchedule(scheduleId);
      }
      
      setWaterSchedules(prev => prev.map(schedule => {
        if (schedule.id === scheduleId) {
          return { ...schedule, enabled };
        }
        return schedule;
      }));
      
      message.success(`Schedule ${enabled ? 'enabled' : 'disabled'} successfully`);
    } catch (error) {
      console.error('Error toggling schedule:', error);
      message.error('Failed to update schedule');
    }
  };

  const handleManualRun = async (scheduleId) => {
    try {
      const schedule = waterSchedules.find(s => s.id === scheduleId);
      if (schedule) {
        // Trigger manual run via API
        await waterControlAPI.activateSchedule(scheduleId);
        
        message.info(`${schedule.name} is now running manually`);
        
        // Update schedule last run time
        setWaterSchedules(prev => prev.map(s => {
          if (s.id === scheduleId) {
            return { ...s, lastRun: new Date() };
          }
          return s;
        }));
      }
    } catch (error) {
      console.error('Error running manual schedule:', error);
      message.error('Failed to run schedule manually');
    }
  };

  const getSystemStatusColor = (status) => {
    switch (status) {
      case 'active': return 'green';
      case 'standby': return 'orange';
      case 'error': return 'red';
      case 'maintenance': return 'blue';
      default: return 'default';
    }
  };

  const getValveStatusColor = (status) => {
    switch (status) {
      case 'open': return 'green';
      case 'closed': return 'red';
      case 'partial': return 'orange';
      default: return 'default';
    }
  };

  const getPumpStatusColor = (status) => {
    switch (status) {
      case 'running': return 'green';
      case 'stopped': return 'red';
      case 'error': return 'red';
      default: return 'default';
    }
  };

  // Water system table columns
  const systemColumns = [
    {
      title: 'System',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <div>
          <strong>{text}</strong>
          <br />
          <Tag color={getSystemStatusColor(record.status)}>{record.status.toUpperCase()}</Tag>
        </div>
      )
    },
    {
      title: 'Flow Rate',
      dataIndex: 'flowRate',
      key: 'flowRate',
      render: (value) => `${value} L/min`
    },
    {
      title: 'Pressure',
      dataIndex: 'pressure',
      key: 'pressure',
      render: (value) => `${value} bar`
    },
    {
      title: 'Valve',
      key: 'valve',
      render: (_, record) => (
        <div>
          <Tag color={getValveStatusColor(record.valve.status)}>
            {record.valve.status.toUpperCase()}
          </Tag>
          <br />
          <Progress percent={record.valve.position} size="small" />
        </div>
      )
    },
    {
      title: 'Pump',
      key: 'pump',
      render: (_, record) => (
        <div>
          <Tag color={getPumpStatusColor(record.pump.status)}>
            {record.pump.status.toUpperCase()}
          </Tag>
          <br />
          <small>{record.pump.power} kW</small>
        </div>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <div>
          <Button.Group size="small">
            <Button 
              icon={<ControlOutlined />}
              onClick={() => {
                setSelectedSystem(record);
                setModalVisible(true);
              }}
            >
              Control
            </Button>
            <Button 
              icon={<SettingOutlined />}
              onClick={() => {
                notification.info({
                  message: 'System Settings',
                  description: `Opening settings for ${record.name}`
                });
              }}
            >
              Settings
            </Button>
          </Button.Group>
        </div>
      )
    }
  ];

  // Schedule table columns
  const scheduleColumns = [
    {
      title: 'Schedule Name',
      dataIndex: 'name',
      key: 'name'
    },
    {
      title: 'System',
      dataIndex: 'systemId',
      key: 'systemId',
      render: (systemId) => {
        const system = waterSystems.find(s => s.id === systemId);
        return system ? system.name : 'Unknown';
      }
    },
    {
      title: 'Time',
      dataIndex: 'startTime',
      key: 'startTime'
    },
    {
      title: 'Duration',
      dataIndex: 'duration',
      key: 'duration',
      render: (value) => `${value} min`
    },
    {
      title: 'Status',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled) => (
        <Badge 
          status={enabled ? 'success' : 'default'} 
          text={enabled ? 'Enabled' : 'Disabled'} 
        />
      )
    },
    {
      title: 'Next Run',
      dataIndex: 'nextRun',
      key: 'nextRun',
      render: (date) => moment(date).format('MMM DD, HH:mm')
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <div>
          <Switch
            checked={record.enabled}
            onChange={(enabled) => handleScheduleToggle(record.id, enabled)}
            size="small"
          />
          <Button
            size="small"
            icon={<PlayCircleOutlined />}
            onClick={() => handleManualRun(record.id)}
            style={{ marginLeft: 8 }}
          >
            Run Now
          </Button>
        </div>
      )
    }
  ];

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>
          <ExperimentOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
          Water Control System
        </h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <Badge 
            status={wsService.isConnected() ? "processing" : "error"} 
            text={wsService.isConnected() ? "Real-time Connected" : "Offline"} 
          />
          <Button 
            icon={<ReloadOutlined />} 
            onClick={() => {
              loadWaterSystems();
              loadWaterSchedules();
              loadWaterUsageData();
            }}
            title="Refresh Data"
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Alert Messages */}
      {waterAlerts.filter(alert => !alert.acknowledged).length > 0 && (
        <Alert
          message="System Alerts"
          description={
            <div>
              {waterAlerts.filter(alert => !alert.acknowledged).map(alert => (
                <div key={alert.id} style={{ marginBottom: '4px' }}>
                  <Tag color={alert.type === 'warning' ? 'orange' : 'blue'}>
                    {alert.type.toUpperCase()}
                  </Tag>
                  {alert.message}
                  <small style={{ marginLeft: '8px', color: '#999' }}>
                    {moment(alert.timestamp).fromNow()}
                  </small>
                </div>
              ))}
            </div>
          }
          type="warning"
          showIcon
          closable
          style={{ marginBottom: '16px' }}
        />
      )}

      <Tabs defaultActiveKey="overview" type="card">
        <TabPane 
          tab={<span><DashboardOutlined />Overview</span>} 
          key="overview"
        >
          {/* System Overview Cards */}
          <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="Total Systems"
                  value={waterSystems.length}
                  prefix={<ExperimentOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="Active Systems"
                  value={waterSystems.filter(s => s.status === 'active').length}
                  prefix={<CheckCircleOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="Total Flow Rate"
                  value={waterSystems.reduce((sum, s) => sum + s.flowRate, 0)}
                  suffix="L/min"
                  prefix={<FireOutlined />}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <Card>
                <Statistic
                  title="Active Schedules"
                  value={waterSchedules.filter(s => s.enabled).length}
                  prefix={<ClockCircleOutlined />}
                  valueStyle={{ color: '#faad14' }}
                />
              </Card>
            </Col>
          </Row>

          {/* Water Usage Chart */}
          <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
            <Col span={24}>
              <Card title="Daily Water Usage" extra={<Button icon={<ReloadOutlined />}>Refresh</Button>}>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={waterUsageData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Area type="monotone" dataKey="irrigation" stackId="1" stroke="#8884d8" fill="#8884d8" />
                    <Area type="monotone" dataKey="supply" stackId="1" stroke="#82ca9d" fill="#82ca9d" />
                    <Area type="monotone" dataKey="drainage" stackId="1" stroke="#ffc658" fill="#ffc658" />
                  </AreaChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          </Row>

          {/* Water Systems Table */}
          <Row>
            <Col span={24}>
              <Card title="Water Systems Status">
                <Table
                  columns={systemColumns}
                  dataSource={waterSystems}
                  rowKey="id"
                  size="middle"
                  pagination={false}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane 
          tab={<span><ControlOutlined />Manual Control</span>} 
          key="control"
        >
          <div style={{ marginBottom: '16px' }}>
            <Alert 
              message={`Debug: Found ${waterSystems.length} water systems`} 
              type="info" 
              showIcon 
            />
          </div>
          <Row gutter={[16, 16]}>
            {waterSystems.map(system => (
              <Col xs={24} lg={8} key={system.id}>
                <Card 
                  title={system.name}
                  extra={<Tag color={getSystemStatusColor(system.status)}>{system.status.toUpperCase()}</Tag>}
                >
                  <div style={{ marginBottom: '16px' }}>
                    <h4>Valve Control</h4>
                    <div style={{ marginBottom: '8px' }}>
                      Position: <Progress percent={system.valve_position || 0} size="small" />
                      Status: <Tag color={system.valve_status === 'open' ? 'green' : 'red'}>
                        {(system.valve_status || 'closed').toUpperCase()}
                      </Tag>
                    </div>
                    <Button.Group>
                      <Button 
                        type={system.valve_status === 'open' ? 'primary' : 'default'}
                        onClick={() => handleValveControl(system.id, 'open')}
                      >
                        Open
                      </Button>
                      <Button 
                        type={system.valve_status === 'closed' ? 'primary' : 'default'}
                        onClick={() => handleValveControl(system.id, 'close')}
                      >
                        Close
                      </Button>
                    </Button.Group>
                  </div>

                  <div style={{ marginBottom: '16px' }}>
                    <h4>Pump Control</h4>
                    <div style={{ marginBottom: '8px' }}>
                      Speed: {system.pump_speed || 0}% | Power: {(system.pump_power || 0).toFixed(1)} kW
                      <br />
                      Status: <Tag color={system.pump_status === 'running' ? 'green' : 'orange'}>
                        {(system.pump_status || 'stopped').toUpperCase()}
                      </Tag>
                    </div>
                    <Button.Group>
                      <Button 
                        type={system.pump_status === 'running' ? 'primary' : 'default'}
                        icon={<PlayCircleOutlined />}
                        onClick={() => handlePumpControl(system.id, 'start')}
                      >
                        Start
                      </Button>
                      <Button 
                        type={system.pump_status === 'stopped' ? 'primary' : 'default'}
                        icon={<StopOutlined />}
                        onClick={() => handlePumpControl(system.id, 'stop')}
                      >
                        Stop
                      </Button>
                    </Button.Group>
                  </div>

                  <div>
                    <h4>Flow Rate Control</h4>
                    <Slider
                      min={0}
                      max={30}
                      value={system.flow_rate || 0}
                      onChange={(value) => handleFlowRateChange(system.id, value)}
                      marks={{
                        0: '0',
                        15: '15',
                        30: '30 L/min'
                      }}
                    />
                  </div>

                  <Divider />
                  
                  <div>
                    <Row gutter={8}>
                      <Col span={12}>
                        <Statistic title="Temperature" value={system.temperature} suffix="°C" />
                      </Col>
                      <Col span={12}>
                        <Statistic title="Pressure" value={system.pressure} suffix="bar" />
                      </Col>
                    </Row>
                    {system.ph && (
                      <Row gutter={8} style={{ marginTop: '8px' }}>
                        <Col span={12}>
                          <Statistic title="pH Level" value={system.ph} />
                        </Col>
                        <Col span={12}>
                          <Statistic title="TDS" value={system.tds} suffix="ppm" />
                        </Col>
                      </Row>
                    )}
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        </TabPane>

        <TabPane 
          tab={<span><ScheduleOutlined />Scheduling</span>} 
          key="scheduling"
        >
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Card 
                title="Water Schedules" 
                extra={
                  <Button type="primary" icon={<PlusOutlined />}>
                    Add Schedule
                  </Button>
                }
              >
                <Table
                  columns={scheduleColumns}
                  dataSource={waterSchedules}
                  rowKey="id"
                  size="middle"
                />
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>

      {/* Control Modal */}
      <Modal
        title={`Control ${selectedSystem?.name}`}
        visible={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        {selectedSystem && (
          <div>
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Card size="small" title="Valve Control">
                  <Progress percent={selectedSystem.valve.position} />
                  <div style={{ marginTop: '8px' }}>
                    <Button.Group>
                      <Button onClick={() => handleValveControl(selectedSystem.id, 'open')}>
                        Open
                      </Button>
                      <Button onClick={() => handleValveControl(selectedSystem.id, 'close')}>
                        Close
                      </Button>
                    </Button.Group>
                  </div>
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small" title="Pump Control">
                  <div>Speed: {selectedSystem.pump.speed}%</div>
                  <div>Power: {selectedSystem.pump.power} kW</div>
                  <div style={{ marginTop: '8px' }}>
                    <Button.Group>
                      <Button 
                        icon={<PlayCircleOutlined />}
                        onClick={() => handlePumpControl(selectedSystem.id, 'start')}
                      >
                        Start
                      </Button>
                      <Button 
                        icon={<StopOutlined />}
                        onClick={() => handlePumpControl(selectedSystem.id, 'stop')}
                      >
                        Stop
                      </Button>
                    </Button.Group>
                  </div>
                </Card>
              </Col>
            </Row>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default WaterControlSystem;
