import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, notification } from 'antd';
import {
  DashboardOutlined,
  CloudUploadOutlined,
  ApiOutlined,
  RobotOutlined,
  ExperimentOutlined,
  StarOutlined,
  UserOutlined,
  SettingOutlined
} from '@ant-design/icons';

import Dashboard from './components/Dashboard';
import FirmwareManagement from './components/FirmwareManagement';
import ESP32Manager from './components/ESP32Manager';
import RealtimeESP32Dashboard from './components/RealtimeESP32Dashboard';
import SensorManagement from './components/SensorManagement';
import SensorMonitoring from './components/SensorMonitoring';
import EnhancedSensorDashboard from './components/EnhancedSensorDashboard';
import DynamicSensorManager from './components/DynamicSensorManager_new';
import AIAgentManager from './components/AIAgentManager';
import WaterControlSystem from './components/WaterControlSystem';
import WebSocketService from './services/WebSocketService';
import Login, { AuthProvider, useAuth } from './components/Login';
import UniversityDashboard from './components/UniversityDashboard';

const { Header, Sider, Content } = Layout;

// Auth-aware content component
const AuthenticatedContent = () => {
  const { user } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Dynamic menu items based on user permissions
  const getMenuItems = () => {
    const allMenuItems = [
      {
        key: '/university-dashboard',
        icon: <UserOutlined />,
        label: 'University Dashboard',
      },
      {
        key: '/',
        icon: <DashboardOutlined />,
        label: 'System Dashboard',
      },
      {
        key: '/water-control',
        icon: <ExperimentOutlined />,
        label: 'Water Control System',
      },
      {
        key: '/ai-agent',
        icon: <StarOutlined />,
        label: 'AI Agent Manager',
      },
      {
        key: '/sensors',
        icon: <ExperimentOutlined />,
        label: 'Sensor Management',
      },
      {
        key: '/sensor-monitoring',
        icon: <ExperimentOutlined />,
        label: 'Sensor Monitoring',
      },
      {
        key: '/enhanced-sensors',
        icon: <ExperimentOutlined />,
        label: 'Enhanced Sensors',
      },
      {
        key: '/dynamic-sensors',
        icon: <ExperimentOutlined />,
        label: 'Dynamic Sensor Manager',
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

    // Filter menu items based on user role
    if (user?.role === 'student') {
      return allMenuItems.filter(item => 
        ['/university-dashboard', '/', '/water-control', '/sensors', '/sensor-monitoring'].includes(item.key)
      );
    }
    
    return allMenuItems;
  };
  
  const menuItems = getMenuItems();

  useEffect(() => {
    // Initialize WebSocket connection with authentication
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
  }, [user]);

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
            {collapsed ? 'URP' : 'University Research Platform'}
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
              University IoT Research Platform
            </h2>
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
              {user?.full_name} ({user?.role})
            </span>
          </div>
        </Header>
        <Content style={{ margin: '24px 16px', padding: 24, background: '#fff' }}>
          <Routes>
            <Route path="/university-dashboard" element={<UniversityDashboard />} />
            <Route path="/" element={<Dashboard />} />
            <Route path="/ai-agent" element={<AIAgentManager />} />
            <Route path="/sensors" element={<SensorManagement />} />
            <Route path="/sensor-monitoring" element={<SensorMonitoring />} />
            <Route path="/enhanced-sensors" element={<EnhancedSensorDashboard />} />
            <Route path="/dynamic-sensors" element={<DynamicSensorManager />} />
            <Route path="/water-control" element={<WaterControlSystem />} />
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
  return (
    <AuthProvider>
      <AuthenticatedApp />
    </AuthProvider>
  );
}

// Main authenticated app component
const AuthenticatedApp = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        background: '#f0f2f5'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div className="loading-spinner"></div>
          <p>Loading University Platform...</p>
        </div>
      </div>
    );
  }

  // If user is not authenticated, show login
  if (!user) {
    return <Login />;
  }

  // If user is authenticated, show the main application
  return <AuthenticatedContent />;
};

export default App;
