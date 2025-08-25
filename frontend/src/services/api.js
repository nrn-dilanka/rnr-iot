import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error(`API Error: ${error.response?.status} ${error.config?.url}`, error.response?.data);
    return Promise.reject(error);
  }
);

export const nodeAPI = {
  // Get all nodes
  getNodes: () => api.get('/nodes'),
  
  // Get specific node
  getNode: (nodeId) => api.get(`/nodes/${nodeId}`),
  
  // Create new node
  createNode: (nodeData) => api.post('/nodes', nodeData),
  
  // Update node
  updateNode: (nodeId, nodeData) => api.put(`/nodes/${nodeId}`, nodeData),
  
  // Delete node
  deleteNode: (nodeId) => api.delete(`/nodes/${nodeId}`),
  
  // Send action to node
  sendAction: (nodeId, action) => api.post(`/nodes/${nodeId}/actions`, action),
  
  // Send servo control command
  sendServoCommand: (nodeId, angle) => api.post(`/nodes/${nodeId}/actions`, {
    action: "SERVO_CONTROL",
    angle: angle
  }),
  
  // Send reboot command
  sendRebootCommand: (nodeId) => api.post(`/nodes/${nodeId}/actions`, {
    action: "REBOOT"
  }),

  // Send real model control command
  sendRealModelCommand: (nodeId, state) => api.post(`/nodes/${nodeId}/actions`, {
    action: "REAL_MODEL_CONTROL",
    state: state
  }),

  // Send relay control command
  sendRelayCommand: (nodeId, relayNumber, state) => api.post(`/nodes/${nodeId}/actions`, {
    action: "RELAY_CONTROL",
    relay: relayNumber,
    state: state
  }),
};

export const firmwareAPI = {
  // Get all firmware versions
  getFirmware: () => api.get('/firmware'),
  
  // Upload firmware
  uploadFirmware: (formData) => api.post('/firmware/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
  
  // Deploy firmware
  deployFirmware: (deploymentData) => api.post('/firmware/deploy', deploymentData),
};

export const sensorAPI = {
  // Get all sensor configurations
  getSensors: (nodeId = null) => {
    const params = nodeId ? { node_id: nodeId } : {};
    return api.get('/sensors', { params });
  },
  
  // Get specific sensor configuration
  getSensor: (sensorId) => api.get(`/sensors/${sensorId}`),
  
  // Create new sensor configuration
  createSensor: (sensorData) => api.post('/sensors', sensorData),
  
  // Update sensor configuration
  updateSensor: (sensorId, sensorData) => api.put(`/sensors/${sensorId}`, sensorData),
  
  // Delete sensor configuration
  deleteSensor: (sensorId) => api.delete(`/sensors/${sensorId}`),
  
  // Generate code for sensor
  generateCode: (sensorId, language = 'arduino') => 
    api.post(`/sensors/${sensorId}/generate-code`, { sensor_id: sensorId, language }),
};

export const sensorDataAPI = {
  // Get all sensor data
  getSensorData: (limit = 100, nodeId = null) => {
    const params = { limit };
    if (nodeId) params.node_id = nodeId;
    return api.get('/sensor-data', { params });
  },
  
  // Get sensor data for specific node
  getNodeSensorData: (nodeId, limit = 100) => {
    return api.get(`/nodes/${nodeId}/sensor-data`, { params: { limit } });
  },
};

export const waterControlAPI = {
  // Water Systems Management
  getSystems: () => api.get('/water/systems'),
  getSystem: (systemId) => api.get(`/water/systems/${systemId}`),
  createSystem: (systemData) => api.post('/water/systems', systemData),
  updateSystem: (systemId, systemData) => api.put(`/water/systems/${systemId}`, systemData),
  deleteSystem: (systemId) => api.delete(`/water/systems/${systemId}`),
  
  // System Status and Control
  getSystemStatus: (systemId) => api.get(`/water/systems/${systemId}/status`),
  enableSystem: (systemId) => api.post(`/water/systems/${systemId}/enable`),
  disableSystem: (systemId) => api.post(`/water/systems/${systemId}/disable`),
  
  // Valve Control
  controlValve: (systemId, action, position = null) => {
    const data = { action };
    if (position !== null) data.position = position;
    return api.post(`/water/systems/${systemId}/valve`, data);
  },
  
  // Pump Control
  controlPump: (systemId, action, speed = null) => {
    const data = { action };
    if (speed !== null) data.speed = speed;
    return api.post(`/water/systems/${systemId}/pump`, data);
  },
  
  // Scheduling
  getSchedules: () => api.get('/water/schedules'),
  createSchedule: (scheduleData) => api.post('/water/schedules', scheduleData),
  updateSchedule: (scheduleId, scheduleData) => api.put(`/water/schedules/${scheduleId}`, scheduleData),
  deleteSchedule: (scheduleId) => api.delete(`/water/schedules/${scheduleId}`),
  runSchedule: (scheduleId) => api.post(`/water/schedules/${scheduleId}/run`),
  
  // Alerts
  getAlerts: () => api.get('/water/alerts'),
  acknowledgeAlert: (alertId) => api.put(`/water/alerts/${alertId}/acknowledge`),
  
  // Analytics and Usage
  getUsageAnalytics: () => api.get('/water/analytics/usage'),
  getSystemHealth: () => api.get('/water/health'),
  
  // Emergency Controls
  emergencyStop: (systemId) => api.post(`/water/systems/${systemId}/emergency-stop`),
  emergencyStopAll: () => api.post('/water/emergency-stop-all'),
};

export default api;
