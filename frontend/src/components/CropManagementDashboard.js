import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Timeline,
  Progress,
  Button,
  Table,
  Tag,
  Statistic,
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  InputNumber,
  Upload,
  message,
  Tabs,
  Alert,
  Badge,
  Tooltip
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CameraOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  LineChartOutlined,
  BarChartOutlined,
  CalendarOutlined,
  BranchesOutlined
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
  RadialBar
} from 'recharts';
import moment from 'moment';

const { Option } = Select;
const { TabPane } = Tabs;
const { TextArea } = Input;

const CropManagementDashboard = () => {
  const [zones, setZones] = useState([]);
  const [selectedZone, setSelectedZone] = useState(null);
  const [cropProfiles, setCropProfiles] = useState([]);
  const [growthData, setGrowthData] = useState([]);
  const [yieldPredictions, setYieldPredictions] = useState({});
  const [modalVisible, setModalVisible] = useState(false);
  const [measurementModalVisible, setMeasurementModalVisible] = useState(false);
  const [loading, setLoading] = useState(true);
  const [form] = Form.useForm();
  const [measurementForm] = Form.useForm();

  useEffect(() => {
    loadZones();
    loadCropProfiles();
    loadGrowthData();
    loadYieldPredictions();
  }, []);

  useEffect(() => {
    if (selectedZone) {
      loadZoneGrowthData(selectedZone);
    }
  }, [selectedZone]);

  const loadZones = async () => {
    try {
      // Mock data - replace with actual API call
      const mockZones = [
        {
          id: 1,
          name: 'Zone A - Tomatoes',
          crop_profile_id: 1,
          crop_type: 'Tomato',
          area_sqm: 25.0,
          planting_date: '2025-06-28',
          expected_harvest_date: '2025-09-15',
          current_growth_stage: 'vegetative',
          plant_count: 20,
          health_score: 0.92,
          growth_progress: 45
        },
        {
          id: 2,
          name: 'Zone B - Lettuce',
          crop_profile_id: 2,
          crop_type: 'Lettuce',
          area_sqm: 15.0,
          planting_date: '2025-07-08',
          expected_harvest_date: '2025-08-22',
          current_growth_stage: 'vegetative',
          plant_count: 30,
          health_score: 0.88,
          growth_progress: 60
        },
        {
          id: 3,
          name: 'Zone C - Mixed Herbs',
          crop_profile_id: null,
          crop_type: 'Mixed Herbs',
          area_sqm: 10.0,
          planting_date: '2025-07-13',
          expected_harvest_date: '2025-08-27',
          current_growth_stage: 'mature',
          plant_count: 15,
          health_score: 0.95,
          growth_progress: 85
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

  const loadCropProfiles = async () => {
    try {
      // Mock crop profiles - replace with actual API call
      const mockProfiles = [
        {
          id: 1,
          name: 'Tomato',
          scientific_name: 'Solanum lycopersicum',
          category: 'vegetables',
          growth_stages: [
            { stage: 'seedling', duration_days: 14, description: 'Initial growth phase' },
            { stage: 'vegetative', duration_days: 35, description: 'Leaf and stem development' },
            { stage: 'flowering', duration_days: 21, description: 'Flower formation' },
            { stage: 'fruiting', duration_days: 45, description: 'Fruit development and ripening' }
          ],
          optimal_conditions: {
            temperature: { min: 18, max: 26, optimal: 22 },
            humidity: { min: 60, max: 70, optimal: 65 },
            soil_moisture: { min: 40, max: 70, optimal: 55 }
          }
        },
        {
          id: 2,
          name: 'Lettuce',
          scientific_name: 'Lactuca sativa',
          category: 'vegetables',
          growth_stages: [
            { stage: 'seedling', duration_days: 10, description: 'Initial growth phase' },
            { stage: 'vegetative', duration_days: 25, description: 'Leaf development' },
            { stage: 'mature', duration_days: 15, description: 'Ready for harvest' }
          ],
          optimal_conditions: {
            temperature: { min: 15, max: 22, optimal: 18 },
            humidity: { min: 50, max: 60, optimal: 55 },
            soil_moisture: { min: 50, max: 80, optimal: 65 }
          }
        }
      ];
      
      setCropProfiles(mockProfiles);
    } catch (error) {
      console.error('Error loading crop profiles:', error);
    }
  };

  const loadGrowthData = async () => {
    try {
      setLoading(true);
      
      // Mock growth data - replace with actual API call
      const mockGrowthData = generateMockGrowthData();
      setGrowthData(mockGrowthData);
      
    } catch (error) {
      console.error('Error loading growth data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadZoneGrowthData = async (zoneId) => {
    // Load zone-specific growth data
    console.log(`Loading growth data for zone ${zoneId}`);
  };

  const loadYieldPredictions = async () => {
    try {
      // Mock yield predictions - replace with actual API call
      const mockPredictions = {
        1: {
          predicted_yield_kg: 45.2,
          confidence: 0.87,
          harvest_date: '2025-09-15',
          quality_grade: 'A',
          market_value: 135.60
        },
        2: {
          predicted_yield_kg: 18.5,
          confidence: 0.92,
          harvest_date: '2025-08-22',
          quality_grade: 'A+',
          market_value: 74.00
        },
        3: {
          predicted_yield_kg: 8.3,
          confidence: 0.78,
          harvest_date: '2025-08-27',
          quality_grade: 'A',
          market_value: 49.80
        }
      };
      
      setYieldPredictions(mockPredictions);
    } catch (error) {
      console.error('Error loading yield predictions:', error);
    }
  };

  const generateMockGrowthData = () => {
    const data = [];
    const startDate = moment().subtract(30, 'days');
    
    for (let i = 0; i <= 30; i++) {
      const date = startDate.clone().add(i, 'days');
      data.push({
        date: date.format('MMM DD'),
        plant_height: 15 + (i * 2) + Math.random() * 5,
        leaf_count: Math.floor(8 + (i * 0.5) + Math.random() * 3),
        stem_diameter: 3 + (i * 0.2) + Math.random() * 0.5,
        health_score: Math.max(0.7, 0.95 - Math.random() * 0.1)
      });
    }
    
    return data;
  };

  const getStageColor = (stage) => {
    const colors = {
      seedling: 'green',
      vegetative: 'blue',
      flowering: 'orange',
      fruiting: 'red',
      mature: 'purple'
    };
    return colors[stage] || 'default';
  };

  const getHealthScoreColor = (score) => {
    if (score >= 0.9) return '#52c41a';
    if (score >= 0.7) return '#faad14';
    return '#ff4d4f';
  };

  const handleAddMeasurement = async (values) => {
    try {
      console.log('Adding measurement:', values);
      // Add API call to save measurement
      message.success('Growth measurement added successfully');
      setMeasurementModalVisible(false);
      measurementForm.resetFields();
      loadGrowthData();
    } catch (error) {
      console.error('Error adding measurement:', error);
      message.error('Failed to add measurement');
    }
  };

  const renderZoneSelector = () => (
    <Card size="small" style={{ marginBottom: 16 }}>
      <Row align="middle" justify="space-between">
        <Col>
          <Select
            value={selectedZone}
            onChange={setSelectedZone}
            style={{ width: 300 }}
            placeholder="Select Zone"
          >
            {zones.map(zone => (
              <Option key={zone.id} value={zone.id}>
                <div>
                  <strong>{zone.name}</strong>
                  <br />
                  <small>{zone.crop_type} • {zone.plant_count} plants</small>
                </div>
              </Option>
            ))}
          </Select>
        </Col>
        <Col>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setMeasurementModalVisible(true)}
          >
            Add Measurement
          </Button>
        </Col>
      </Row>
    </Card>
  );

  const renderZoneOverview = () => {
    const zone = zones.find(z => z.id === selectedZone);
    if (!zone) return null;

    const prediction = yieldPredictions[selectedZone] || {};
    const cropProfile = cropProfiles.find(p => p.id === zone.crop_profile_id);

    return (
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} lg={16}>
          <Card title={`${zone.name} Overview`}>
            <Row gutter={[16, 16]}>
              <Col xs={12} sm={6}>
                <Statistic
                  title="Plant Count"
                  value={zone.plant_count}
                  prefix={<BranchesOutlined />}
                />
              </Col>
              <Col xs={12} sm={6}>
                <Statistic
                  title="Health Score"
                  value={Math.round(zone.health_score * 100)}
                  suffix="%"
                  valueStyle={{ color: getHealthScoreColor(zone.health_score) }}
                />
              </Col>
              <Col xs={12} sm={6}>
                <Statistic
                  title="Growth Progress"
                  value={zone.growth_progress}
                  suffix="%"
                />
              </Col>
              <Col xs={12} sm={6}>
                <Statistic
                  title="Days Since Planting"
                  value={moment().diff(moment(zone.planting_date), 'days')}
                  prefix={<CalendarOutlined />}
                />
              </Col>
            </Row>
            
            <div style={{ marginTop: 16 }}>
              <div style={{ marginBottom: 8 }}>
                <strong>Current Growth Stage:</strong>
                <Tag color={getStageColor(zone.current_growth_stage)} style={{ marginLeft: 8 }}>
                  {zone.current_growth_stage.toUpperCase()}
                </Tag>
              </div>
              
              <div style={{ marginBottom: 8 }}>
                <strong>Expected Harvest:</strong>
                <span style={{ marginLeft: 8 }}>
                  {moment(zone.expected_harvest_date).format('MMM DD, YYYY')} 
                  ({moment(zone.expected_harvest_date).fromNow()})
                </span>
              </div>
              
              <Progress
                percent={zone.growth_progress}
                strokeColor={{
                  '0%': '#108ee9',
                  '100%': '#87d068',
                }}
                format={percent => `${percent}% Complete`}
              />
            </div>
          </Card>
        </Col>
        
        <Col xs={24} lg={8}>
          <Card title="Yield Prediction" style={{ height: '100%' }}>
            <div style={{ textAlign: 'center' }}>
              <Statistic
                title="Predicted Yield"
                value={prediction.predicted_yield_kg || 0}
                suffix="kg"
                prefix={<TrophyOutlined />}
                valueStyle={{ color: '#52c41a', fontSize: '24px' }}
              />
              
              <div style={{ marginTop: 16 }}>
                <div style={{ marginBottom: 8 }}>
                  <strong>Confidence:</strong>
                  <Progress
                    percent={Math.round((prediction.confidence || 0) * 100)}
                    size="small"
                    style={{ marginLeft: 8, width: 100, display: 'inline-block' }}
                  />
                </div>
                
                <div style={{ marginBottom: 8 }}>
                  <strong>Quality Grade:</strong>
                  <Tag color="gold" style={{ marginLeft: 8 }}>
                    {prediction.quality_grade || 'N/A'}
                  </Tag>
                </div>
                
                <div>
                  <strong>Est. Market Value:</strong>
                  <span style={{ marginLeft: 8, color: '#52c41a', fontWeight: 'bold' }}>
                    ${prediction.market_value || 0}
                  </span>
                </div>
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    );
  };

  const renderGrowthTimeline = () => {
    const zone = zones.find(z => z.id === selectedZone);
    const cropProfile = cropProfiles.find(p => p.id === zone?.crop_profile_id);
    
    if (!cropProfile) return null;

    const plantingDate = moment(zone.planting_date);
    let currentDate = plantingDate.clone();

    return (
      <Card title="Growth Timeline" style={{ marginBottom: 16 }}>
        <Timeline>
          {cropProfile.growth_stages.map((stage, index) => {
            const stageEndDate = currentDate.clone().add(stage.duration_days, 'days');
            const isCompleted = moment().isAfter(stageEndDate);
            const isCurrent = moment().isBetween(currentDate, stageEndDate);
            
            const timelineItem = (
              <Timeline.Item
                key={index}
                color={isCompleted ? 'green' : isCurrent ? 'blue' : 'gray'}
                dot={isCurrent ? <ClockCircleOutlined /> : isCompleted ? <CheckCircleOutlined /> : null}
              >
                <div>
                  <h4 style={{ margin: 0 }}>
                    {stage.stage.charAt(0).toUpperCase() + stage.stage.slice(1)} Stage
                    {isCurrent && <Badge status="processing" text="Current" style={{ marginLeft: 8 }} />}
                    {isCompleted && <Badge status="success" text="Completed" style={{ marginLeft: 8 }} />}
                  </h4>
                  <p style={{ margin: '4px 0', color: '#666' }}>{stage.description}</p>
                  <p style={{ margin: '4px 0', fontSize: '12px', color: '#999' }}>
                    Duration: {stage.duration_days} days 
                    ({currentDate.format('MMM DD')} - {stageEndDate.format('MMM DD')})
                  </p>
                  {isCurrent && (
                    <Progress
                      percent={Math.round((moment().diff(currentDate, 'days') / stage.duration_days) * 100)}
                      size="small"
                      style={{ marginTop: 8 }}
                    />
                  )}
                </div>
              </Timeline.Item>
            );
            
            currentDate = stageEndDate;
            return timelineItem;
          })}
        </Timeline>
      </Card>
    );
  };

  const renderGrowthCharts = () => (
    <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
      <Col xs={24} lg={12}>
        <Card title="Plant Height Growth">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={growthData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <RechartsTooltip />
              <Line
                type="monotone"
                dataKey="plant_height"
                stroke="#52c41a"
                strokeWidth={2}
                name="Height (cm)"
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </Col>
      
      <Col xs={24} lg={12}>
        <Card title="Leaf Count Development">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={growthData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <RechartsTooltip />
              <Bar
                dataKey="leaf_count"
                fill="#1890ff"
                name="Leaf Count"
              />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </Col>
      
      <Col xs={24} lg={12}>
        <Card title="Stem Diameter Growth">
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={growthData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <RechartsTooltip />
              <Area
                type="monotone"
                dataKey="stem_diameter"
                stroke="#722ed1"
                fill="#722ed1"
                fillOpacity={0.3}
                name="Diameter (mm)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      </Col>
      
      <Col xs={24} lg={12}>
        <Card title="Health Score Trend">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={growthData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis domain={[0, 1]} />
              <RechartsTooltip />
              <Line
                type="monotone"
                dataKey="health_score"
                stroke="#faad14"
                strokeWidth={2}
                name="Health Score"
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </Col>
    </Row>
  );

  const renderMeasurementModal = () => (
    <Modal
      title="Add Growth Measurement"
      visible={measurementModalVisible}
      onCancel={() => setMeasurementModalVisible(false)}
      onOk={() => measurementForm.submit()}
      width={600}
    >
      <Form
        form={measurementForm}
        layout="vertical"
        onFinish={handleAddMeasurement}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="measurement_date"
              label="Measurement Date"
              rules={[{ required: true, message: 'Please select measurement date' }]}
            >
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="growth_stage"
              label="Growth Stage"
              rules={[{ required: true, message: 'Please select growth stage' }]}
            >
              <Select placeholder="Select growth stage">
                <Option value="seedling">Seedling</Option>
                <Option value="vegetative">Vegetative</Option>
                <Option value="flowering">Flowering</Option>
                <Option value="fruiting">Fruiting</Option>
                <Option value="mature">Mature</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>
        
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item
              name="plant_height_cm"
              label="Plant Height (cm)"
            >
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="leaf_count"
              label="Leaf Count"
            >
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="stem_diameter_mm"
              label="Stem Diameter (mm)"
            >
              <InputNumber min={0} step={0.1} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>
        
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item
              name="fruit_count"
              label="Fruit Count"
            >
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="estimated_yield_kg"
              label="Estimated Yield (kg)"
            >
              <InputNumber min={0} step={0.1} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item
              name="health_score"
              label="Health Score (0-1)"
            >
              <InputNumber min={0} max={1} step={0.1} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>
        
        <Form.Item
          name="notes"
          label="Notes"
        >
          <TextArea rows={3} placeholder="Additional observations..." />
        </Form.Item>
        
        <Form.Item
          name="images"
          label="Photos"
        >
          <Upload
            listType="picture-card"
            multiple
            beforeUpload={() => false}
          >
            <div>
              <CameraOutlined />
              <div style={{ marginTop: 8 }}>Upload</div>
            </div>
          </Upload>
        </Form.Item>
      </Form>
    </Modal>
  );

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1>
          <BranchesOutlined style={{ marginRight: '8px', color: '#52c41a' }} />
          Crop Management & Growth Tracking
        </h1>
      </div>

      {renderZoneSelector()}
      {renderZoneOverview()}
      {renderGrowthTimeline()}
      {renderGrowthCharts()}
      {renderMeasurementModal()}
    </div>
  );
};

export default CropManagementDashboard;