import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Alert,
  Button,
  Select,
  DatePicker,
  Table,
  Tag,
  Badge,
  Tabs,
  Tooltip,
  notification
} from 'antd';
import {
  FireOutlined,
  EnvironmentOutlined,
  SunOutlined,
  CloudOutlined,
  ExperimentOutlined,
  AlertOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  ReloadOutlined,
  SettingOutlined
} from '@ant-design/icons';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  RadialBarChart,
  RadialBar,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import moment from 'moment';
import WebSocketService from '../services/WebSocketService';

const { Option } = Select;
const { TabPane } = Tabs;
const { RangePicker } = DatePicker;

const AdvancedEnvironmentalDashboard = () => {
  const [zones, setZones] = useState([]);
  const [selectedZone, setSelectedZone] = useState(null);
  const [environmentalData, setEnvironmentalData] = useState([]);
  const [currentConditions, setCurrentConditions] = useState({});
  const [sensorAlerts, setSensorAlerts] = useState([]);
  const [optimalRanges, setOptimalRanges] = useState({});
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState([
    moment().subtract(24, 'hours'),
    moment()
  ]);

  const wsService = WebSocketService.getInstance();

  useEffect(() => {
    loadZones();
    loadEnvironmentalData();
    setupWebSocketListeners();
    
    return () => {
      wsService.unsubscribe('environmental_update', handleEnvironmentalUpdate);
      wsService.unsubscribe('sensor_alert', handleSensorAlert);
    };
  }, []);

  useEffect(() => {
    if (selectedZone) {
      loadZoneData(selectedZone);
    }
  }, [selectedZone, dateRange]);

  const setupWebSocketListeners = () => {
    wsService.subscribe('environmental_update', handleEnvironmentalUpdate);
    wsService.subscribe('sensor_alert', handleSensorAlert);
  };

  const handleEnvironmentalUpdate = (data) => {
    console.log('Environmental update received:', data);
    
    // Update current conditions
    setCurrentConditions(prev => ({
      ...prev,
      [data.zone_id]: {
        ...prev[data.zone_id],
        [data.sensor_type]: {
          value: data.value,
          unit: data.unit,
          timestamp: data.timestamp,
          quality_score: data.quality_score
        }
      }
    }));

    // Add to historical data
    setEnvironmentalData(prev => [...prev.slice(-100), {
      timestamp: data.timestamp,
      zone_id: data.zone_id,
      sensor_type: data.sensor_type,
      value: data.value,
      unit: data.unit
    }]);
  };

  const handleSensorAlert = (alert) => {
    console.log('Sensor alert received:', alert);
    setSensorAlerts(prev => [alert, ...prev.slice(0, 9)]);
    
    notification[alert.severity === 'critical' ? 'error' : 'warning']({
      message: 'Environmental Alert',
      description: alert.message,
      duration: alert.severity === 'critical' ? 0 : 5,
    });
  };

  const loadZones = async () => {
    try {
      // Mock data - replace with actual API call
      const mockZones = [
        {
          id: 1,
          name: 'Zone A - Tomatoes',
          crop_type: 'Tomato',
          area_sqm: 25.0,
          current_growth_stage: 'vegetative',
          planting_date: '2025-06-28'
        },
        {
          id: 2,
          name: 'Zone B - Lettuce',
          crop_type: 'Lettuce',
          area_sqm: 15.0,
          current_growth_stage: 'vegetative',
          planting_date: '2025-07-08'
        },
        {
          id: 3,
          name: 'Zone C - Mixed Herbs',
          crop_type: 'Mixed Herbs',
          area_sqm: 10.0,
          current_growth_stage: 'mature',
          planting_date: '2025-07-13'
        }
      ];
      
      setZones(mockZones);
      if (mockZones.length > 0) {
        setSelectedZone(mockZones[0].id);
      }
    } catch (error) {
      console.error('Error loading zones:', error);
    }
  };

  const loadEnvironmentalData = async () => {
    try {
      setLoading(true);
      
      // Mock environmental data - replace with actual API call
      const mockData = generateMockEnvironmentalData();
      setEnvironmentalData(mockData);
      
      // Mock current conditions
      const mockCurrentConditions = {
        1: {
          temperature: { value: 24.5, unit: '°C', quality_score: 0.95 },
          humidity: { value: 65.2, unit: '%', quality_score: 0.98 },
          soil_moisture: { value: 55.8, unit: '%', quality_score: 0.92 },
          light_intensity: { value: 15000, unit: 'lux', quality_score: 0.89 },
          co2_level: { value: 420, unit: 'ppm', quality_score: 0.94 },
          ph_level: { value: 6.8, unit: 'pH', quality_score: 0.96 }
        },
        2: {
          temperature: { value: 18.2, unit: '°C', quality_score: 0.97 },
          humidity: { value: 58.1, unit: '%', quality_score: 0.95 },
          soil_moisture: { value: 68.3, unit: '%', quality_score: 0.91 },
          light_intensity: { value: 12000, unit: 'lux', quality_score: 0.88 },
          co2_level: { value: 380, unit: 'ppm', quality_score: 0.93 },
          ph_level: { value: 6.2, unit: 'pH', quality_score: 0.94 }
        }
      };
      
      setCurrentConditions(mockCurrentConditions);
      
      // Mock optimal ranges
      setOptimalRanges({
        temperature: { min: 18, max: 26, optimal: 22 },
        humidity: { min: 60, max: 70, optimal: 65 },
        soil_moisture: { min: 40, max: 70, optimal: 55 },
        light_intensity: { min: 10000, max: 20000, optimal: 15000 },
        co2_level: { min: 400, max: 800, optimal: 600 },
        ph_level: { min: 6.0, max: 7.0, optimal: 6.5 }
      });
      
    } catch (error) {
      console.error('Error loading environmental data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadZoneData = async (zoneId) => {
    // Load zone-specific data based on date range
    console.log(`Loading data for zone ${zoneId} from ${dateRange[0].format()} to ${dateRange[1].format()}`);
  };

  const generateMockEnvironmentalData = () => {
    const data = [];
    const now = moment();
    
    for (let i = 24; i >= 0; i--) {
      const timestamp = now.clone().subtract(i, 'hours');
      data.push({
        time: timestamp.format('HH:mm'),
        timestamp: timestamp.toISOString(),
        temperature: 20 + Math.random() * 8,
        humidity: 55 + Math.random() * 20,
        soil_moisture: 45 + Math.random() * 25,
        light_intensity: Math.max(0, 8000 + Math.random() * 12000 - (i > 18 || i < 6 ? 10000 : 0)),
        co2_level: 380 + Math.random() * 200,
        ph_level: 6.0 + Math.random() * 1.0
      });
    }
    
    return data;
  };

  const isInOptimalRange = (value, sensorType) => {
    const range = optimalRanges[sensorType];
    if (!range) return true;
    return value >= range.min && value <= range.max;
  };

  const getConditionStatus = (value, sensorType) => {
    const range = optimalRanges[sensorType];
    if (!range) return 'success';
    
    if (value < range.min || value > range.max) return 'error';
    if (Math.abs(value - range.optimal) / range.optimal > 0.1) return 'warning';
    return 'success';
  };

  const renderZoneSelector = () => (
    <Card size="small" style={{ marginBottom: 16 }}>
      <Row align="middle" justify="space-between">
        <Col>
          <Select
            value={selectedZone}
            onChange={setSelectedZone}
            style={{ width: 250 }}
            placeholder="Select Zone"
          >
            {zones.map(zone => (
              <Option key={zone.id} value={zone.id}>
                {zone.name} ({zone.crop_type})
              </Option>
            ))}
          </Select>
        </Col>
        <Col>
          <RangePicker
            value={dateRange}
            onChange={setDateRange}
            showTime
            format="MMM DD HH:mm"
          />
        </Col>
        <Col>
          <Button
            icon={<ReloadOutlined />}
            onClick={loadEnvironmentalData}
            loading={loading}
          >
            Refresh
          </Button>
        </Col>
      </Row>
    </Card>
  );

  const renderCurrentConditions = () => {
    const zoneConditions = currentConditions[selectedZone] || {};
    
    return (
      <Card title="Current Environmental Conditions" style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={8} lg={4}>
            <Card size="small">
              <Statistic
                title="Temperature"
                value={zoneConditions.temperature?.value || 0}
                suffix={zoneConditions.temperature?.unit || '°C'}
                prefix={<FireOutlined />}
                valueStyle={{
                  color: getConditionStatus(zoneConditions.temperature?.value, 'temperature') === 'success' 
                    ? '#52c41a' : '#ff4d4f'
                }}
              />
              <Progress
                percent={Math.round((zoneConditions.temperature?.quality_score || 0) * 100)}
                size="small"
                format={percent => `${percent}% quality`}
              />
            </Card>
          </Col>
          
          <Col xs={24} sm={12} md={8} lg={4}>
            <Card size="small">
              <Statistic
                title="Humidity"
                value={zoneConditions.humidity?.value || 0}
                suffix={zoneConditions.humidity?.unit || '%'}
                prefix={<EnvironmentOutlined  />}
                valueStyle={{
                  color: getConditionStatus(zoneConditions.humidity?.value, 'humidity') === 'success' 
                    ? '#52c41a' : '#ff4d4f'
                }}
              />
              <Progress
                percent={Math.round((zoneConditions.humidity?.quality_score || 0) * 100)}
                size="small"
                format={percent => `${percent}% quality`}
              />
            </Card>
          </Col>
          
          <Col xs={24} sm={12} md={8} lg={4}>
            <Card size="small">
              <Statistic
                title="Soil Moisture"
                value={zoneConditions.soil_moisture?.value || 0}
                suffix={zoneConditions.soil_moisture?.unit || '%'}
                prefix={<EnvironmentOutlined  />}
                valueStyle={{
                  color: getConditionStatus(zoneConditions.soil_moisture?.value, 'soil_moisture') === 'success' 
                    ? '#52c41a' : '#ff4d4f'
                }}
              />
              <Progress
                percent={Math.round((zoneConditions.soil_moisture?.quality_score || 0) * 100)}
                size="small"
                format={percent => `${percent}% quality`}
              />
            </Card>
          </Col>
          
          <Col xs={24} sm={12} md={8} lg={4}>
            <Card size="small">
              <Statistic
                title="Light Intensity"
                value={zoneConditions.light_intensity?.value || 0}
                suffix={zoneConditions.light_intensity?.unit || 'lux'}
                prefix={<SunOutlined />}
                valueStyle={{
                  color: getConditionStatus(zoneConditions.light_intensity?.value, 'light_intensity') === 'success' 
                    ? '#52c41a' : '#ff4d4f'
                }}
              />
              <Progress
                percent={Math.round((zoneConditions.light_intensity?.quality_score || 0) * 100)}
                size="small"
                format={percent => `${percent}% quality`}
              />
            </Card>
          </Col>
          
          <Col xs={24} sm={12} md={8} lg={4}>
            <Card size="small">
              <Statistic
                title="CO₂ Level"
                value={zoneConditions.co2_level?.value || 0}
                suffix={zoneConditions.co2_level?.unit || 'ppm'}
                prefix={<CloudOutlined />}
                valueStyle={{
                  color: getConditionStatus(zoneConditions.co2_level?.value, 'co2_level') === 'success' 
                    ? '#52c41a' : '#ff4d4f'
                }}
              />
              <Progress
                percent={Math.round((zoneConditions.co2_level?.quality_score || 0) * 100)}
                size="small"
                format={percent => `${percent}% quality`}
              />
            </Card>
          </Col>
          
          <Col xs={24} sm={12} md={8} lg={4}>
            <Card size="small">
              <Statistic
                title="pH Level"
                value={zoneConditions.ph_level?.value || 0}
                precision={1}
                prefix={<ExperimentOutlined />}
                valueStyle={{
                  color: getConditionStatus(zoneConditions.ph_level?.value, 'ph_level') === 'success' 
                    ? '#52c41a' : '#ff4d4f'
                }}
              />
              <Progress
                percent={Math.round((zoneConditions.ph_level?.quality_score || 0) * 100)}
                size="small"
                format={percent => `${percent}% quality`}
              />
            </Card>
          </Col>
        </Row>
      </Card>
    );
  };

  const renderEnvironmentalCharts = () => (
    <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
      <Col xs={24} lg={12}>
        <Card title="Temperature & Humidity Trends">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={environmentalData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis yAxisId="temp" orientation="left" />
              <YAxis yAxisId="humidity" orientation="right" />
              <RechartsTooltip />
              <Line
                yAxisId="temp"
                type="monotone"
                dataKey="temperature"
                stroke="#ff7300"
                strokeWidth={2}
                name="Temperature (°C)"
              />
              <Line
                yAxisId="humidity"
                type="monotone"
                dataKey="humidity"
                stroke="#1890ff"
                strokeWidth={2}
                name="Humidity (%)"
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </Col>
      
      <Col xs={24} lg={12}>
        <Card title="Soil Moisture & Light Intensity">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={environmentalData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis yAxisId="soil" orientation="left" />
              <YAxis yAxisId="light" orientation="right" />
              <RechartsTooltip />
              <Line
                yAxisId="soil"
                type="monotone"
                dataKey="soil_moisture"
                stroke="#52c41a"
                strokeWidth={2}
                name="Soil Moisture (%)"
              />
              <Line
                yAxisId="light"
                type="monotone"
                dataKey="light_intensity"
                stroke="#faad14"
                strokeWidth={2}
                name="Light Intensity (lux)"
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </Col>
      
      <Col xs={24} lg={12}>
        <Card title="CO₂ Levels">
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={environmentalData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <RechartsTooltip />
              <Area
                type="monotone"
                dataKey="co2_level"
                stroke="#722ed1"
                fill="#722ed1"
                fillOpacity={0.3}
                name="CO₂ (ppm)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      </Col>
      
      <Col xs={24} lg={12}>
        <Card title="pH Level Stability">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={environmentalData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis domain={[5.5, 7.5]} />
              <RechartsTooltip />
              <Line
                type="monotone"
                dataKey="ph_level"
                stroke="#13c2c2"
                strokeWidth={2}
                name="pH Level"
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </Col>
    </Row>
  );

  const renderSensorAlerts = () => (
    <Card title="Recent Sensor Alerts" style={{ marginBottom: 16 }}>
      {sensorAlerts.length === 0 ? (
        <Alert
          message="No Recent Alerts"
          description="All environmental sensors are operating within normal parameters."
          type="success"
          showIcon
        />
      ) : (
        <div>
          {sensorAlerts.map((alert, index) => (
            <Alert
              key={index}
              message={alert.title}
              description={`${alert.message} - ${moment(alert.timestamp).fromNow()}`}
              type={alert.severity === 'critical' ? 'error' : 'warning'}
              showIcon
              style={{ marginBottom: 8 }}
              action={
                <Button size="small" onClick={() => console.log('Handle alert:', alert)}>
                  View Details
                </Button>
              }
            />
          ))}
        </div>
      )}
    </Card>
  );

  const selectedZoneInfo = zones.find(z => z.id === selectedZone);

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1>
          <ExperimentOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
          Advanced Environmental Monitoring
        </h1>
        {selectedZoneInfo && (
          <div style={{ marginTop: '8px' }}>
            <Tag color="blue">{selectedZoneInfo.crop_type}</Tag>
            <Tag color="green">{selectedZoneInfo.current_growth_stage}</Tag>
            <Tag>{selectedZoneInfo.area_sqm} m²</Tag>
            <span style={{ marginLeft: '16px', color: '#666' }}>
              Planted: {moment(selectedZoneInfo.planting_date).format('MMM DD, YYYY')} 
              ({moment().diff(moment(selectedZoneInfo.planting_date), 'days')} days ago)
            </span>
          </div>
        )}
      </div>

      {renderZoneSelector()}
      {renderCurrentConditions()}
      {renderSensorAlerts()}
      {renderEnvironmentalCharts()}
    </div>
  );
};

export default AdvancedEnvironmentalDashboard;