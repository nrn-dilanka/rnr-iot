import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, notification } from 'antd';
import {
  DashboardOutlined,
  CloudUploadOutlined,
  ApiOutlined,
  RobotOutlined,
  ExperimentOutlined,
  ControlOutlined,
  MonitorOutlined,
  SettingOutlined,
  BarChartOutlined,
  SecurityScanOutlined,
  ClusterOutlined
} from '@ant-design/icons';

import Dashboard from './components/Dashboard';
import FirmwareManagement from './components/FirmwareManagement';
import ESP32Manager from './components/ESP32Manager';
import RealtimeESP32Dashboard from './components/RealtimeESP32Dashboard';
import SensorManagement from './components/SensorManagement';
// import SensorMonitoring from './components/SensorMonitoring';
// import EnhancedSensorDashboard from './components/EnhancedSensorDashboard';
import DynamicSensorManager from './components/DynamicSensorManager_new';
import AIAgentManager from './components/AIAgentManager';
import WaterControlSystem from './components/WaterControlSystem';
import AdvancedEnvironmentalDashboard from './components/AdvancedEnvironmentalDashboard';
import CropManagementDashboard from './components/CropManagementDashboard';
import WebSocketService from './services/WebSocketService';

const { Header, Sider, Content } = Layout;

// Main application component
const MainApplication = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // All menu items (no authentication filtering)
  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: 'Enterprise Dashboard',
    },
    {
      key: '/device-management',
      icon: <RobotOutlined />,
      label: 'Device Management',
    },
    {
      key: '/real-time-monitoring',
      icon: <MonitorOutlined />,
      label: 'Real-time Monitoring',
    },
    {
      key: '/environmental-monitoring',
      icon: <ExperimentOutlined />,
      label: 'Environmental Control',
    },
    {
      key: '/industrial-automation',
      icon: <ControlOutlined />,
      label: 'Industrial Automation',
    },
    {
      key: '/sensor-networks',
      icon: <ClusterOutlined />,
      label: 'Sensor Networks',
    },
    {
      key: '/analytics-reports',
      icon: <BarChartOutlined />,
      label: 'Analytics & Reports',
    },
    {
      key: '/ai-agent',
      icon: <SecurityScanOutlined />,
      label: 'AI Analytics',
    },
    {
      key: '/sensors',
      icon: <ExperimentOutlined />,
      label: 'Sensor Management',
    },
    {
      key: '/dynamic-sensors',
      icon: <SettingOutlined />,
      label: 'Dynamic Configuration',
    },
    {
      key: '/esp32',
      icon: <RobotOutlined />,
      label: 'ESP32 Manager',
    },
    {
      key: '/realtime',
      icon: <ApiOutlined />,
      label: 'Real-time Monitor',
    },
    {
      key: '/firmware',
      icon: <CloudUploadOutlined />,
      label: 'Firmware Management',
    }
  ];

  useEffect(() => {
    // Initialize WebSocket connection
    const wsService = WebSocketService.getInstance();
    
    wsService.connect(
      () => {
        setWsConnected(true);
        notification.success({
          message: 'Connected',
          description: 'Real-time connection established',
          duration: 2,
        });
      },
      () => {
        setWsConnected(false);
        notification.error({
          message: 'Disconnected',
          description: 'Lost real-time connection',
          duration: 2,
        });
      },
      (error) => {
        setWsConnected(false);
        notification.error({
          message: 'Connection Error',
          description: 'Failed to establish real-time connection',
          duration: 3,
        });
      }
    );

    return () => {
      wsService.disconnect();
    };
  }, []);

  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider 
        collapsible 
        collapsed={collapsed} 
        onCollapse={setCollapsed}
        theme="dark"
      >
        <div style={{ 
          height: '64px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          borderBottom: '1px solid #001529'
        }}>
          <h3 style={{ 
            color: 'white', 
            margin: 0, 
            fontSize: collapsed ? '14px' : '16px',
            fontWeight: 'bold'
          }}>
            {collapsed ? 'RNR' : 'RNR Solutions IoT'}
          </h3>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout>
        <Header style={{ 
          padding: '0 24px', 
          background: '#fff',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <div>
            <h2 style={{ margin: 0, color: '#1890ff' }}>
              RNR Solutions IoT Platform
            </h2>
            <small style={{ color: '#666', fontSize: '12px' }}>Enterprise IoT Management System</small>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span style={{ 
              color: wsConnected ? '#52c41a' : '#ff4d4f',
              fontSize: '12px',
              fontWeight: 'bold'
            }}>
              {wsConnected ? '● CONNECTED' : '● DISCONNECTED'}
            </span>
            <span style={{ fontSize: '14px', color: '#666' }}>
              Administrator Access
            </span>
          </div>
        </Header>
        <Content style={{ margin: '24px 16px', padding: 24, background: '#fff' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/device-management" element={<ESP32Manager />} />
            <Route path="/real-time-monitoring" element={<RealtimeESP32Dashboard />} />
            <Route path="/environmental-monitoring" element={<AdvancedEnvironmentalDashboard />} />
            <Route path="/industrial-automation" element={<WaterControlSystem />} />
            <Route path="/sensor-networks" element={<SensorManagement />} />
            <Route path="/analytics-reports" element={<CropManagementDashboard />} />
            <Route path="/ai-agent" element={<AIAgentManager />} />
            <Route path="/sensors" element={<SensorManagement />} />
            <Route path="/dynamic-sensors" element={<DynamicSensorManager />} />
            <Route path="/esp32" element={<ESP32Manager />} />
            <Route path="/realtime" element={<RealtimeESP32Dashboard />} />
            <Route path="/firmware" element={<FirmwareManagement />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
};

function App() {
  return <MainApplication />;
}

export default App;
