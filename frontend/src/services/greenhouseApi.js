import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    console.log(`Greenhouse API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`Greenhouse API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error(`Greenhouse API Error: ${error.response?.status} ${error.config?.url}`, error.response?.data);
    return Promise.reject(error);
  }
);

export const greenhouseAPI = {
  // Zone Management
  getZones: () => api.get('/greenhouse/zones'),
  getZone: (zoneId) => api.get(`/greenhouse/zones/${zoneId}`),
  createZone: (zoneData) => api.post('/greenhouse/zones', zoneData),
  updateZone: (zoneId, zoneData) => api.put(`/greenhouse/zones/${zoneId}`, zoneData),
  deleteZone: (zoneId) => api.delete(`/greenhouse/zones/${zoneId}`),

  // Crop Profile Management
  getCropProfiles: () => api.get('/greenhouse/crop-profiles'),
  createCropProfile: (profileData) => api.post('/greenhouse/crop-profiles', profileData),

  // Growth Tracking
  getZoneGrowthData: (zoneId, days = 30) => api.get(`/greenhouse/zones/${zoneId}/growth-data?days=${days}`),
  addGrowthMeasurement: (measurementData) => api.post('/greenhouse/growth-measurements', measurementData),

  // Yield Predictions
  getYieldPrediction: (zoneId) => api.get(`/greenhouse/zones/${zoneId}/yield-prediction`),

  // Automation Rules
  getAutomationRules: () => api.get('/greenhouse/automation-rules'),
  createAutomationRule: (ruleData) => api.post('/greenhouse/automation-rules', ruleData),
  toggleAutomationRule: (ruleId) => api.put(`/greenhouse/automation-rules/${ruleId}/toggle`),

  // Alert System
  getAlerts: (status = null) => {
    const params = status ? { status } : {};
    return api.get('/greenhouse/alerts', { params });
  },
  createAlert: (alertData) => api.post('/greenhouse/alerts', alertData),
  acknowledgeAlert: (alertId) => api.put(`/greenhouse/alerts/${alertId}/acknowledge`),

  // Environmental Analysis
  getEnvironmentalAnalysis: (zoneId) => api.get(`/greenhouse/zones/${zoneId}/environmental-analysis`),

  // Dashboard Summary
  getDashboardSummary: () => api.get('/greenhouse/dashboard-summary'),
};

export const environmentalAPI = {
  // Environmental Monitoring
  getCurrentConditions: (zoneId) => api.get(`/greenhouse/zones/${zoneId}/environmental-conditions`),
  getEnvironmentalHistory: (zoneId, hours = 24) => 
    api.get(`/greenhouse/zones/${zoneId}/environmental-history?hours=${hours}`),
  
  // Sensor Management
  getSensorStatus: (zoneId) => api.get(`/greenhouse/zones/${zoneId}/sensors`),
  calibrateSensor: (sensorId, calibrationData) => 
    api.post(`/greenhouse/sensors/${sensorId}/calibrate`, calibrationData),
  
  // Thresholds and Alerts
  getOptimalRanges: (cropType) => api.get(`/greenhouse/crop-profiles/${cropType}/optimal-ranges`),
  updateThresholds: (zoneId, thresholds) => 
    api.put(`/greenhouse/zones/${zoneId}/thresholds`, thresholds),
};

export const automationAPI = {
  // Automation Control
  executeRule: (ruleId) => api.post(`/greenhouse/automation-rules/${ruleId}/execute`),
  pauseRule: (ruleId) => api.put(`/greenhouse/automation-rules/${ruleId}/pause`),
  resumeRule: (ruleId) => api.put(`/greenhouse/automation-rules/${ruleId}/resume`),
  
  // Emergency Controls
  emergencyStop: (zoneId) => api.post(`/greenhouse/zones/${zoneId}/emergency-stop`),
  emergencyStopAll: () => api.post('/greenhouse/emergency-stop-all'),
  
  // Manual Overrides
  overrideIrrigation: (zoneId, duration, intensity) => 
    api.post(`/greenhouse/zones/${zoneId}/override-irrigation`, { duration, intensity }),
  overrideClimate: (zoneId, settings) => 
    api.post(`/greenhouse/zones/${zoneId}/override-climate`, settings),
  overrideLighting: (zoneId, settings) => 
    api.post(`/greenhouse/zones/${zoneId}/override-lighting`, settings),
};

export const analyticsAPI = {
  // Predictive Analytics
  getGrowthPredictions: (zoneId) => api.get(`/greenhouse/zones/${zoneId}/growth-predictions`),
  getHarvestForecast: (zoneId) => api.get(`/greenhouse/zones/${zoneId}/harvest-forecast`),
  getResourceOptimization: (zoneId) => api.get(`/greenhouse/zones/${zoneId}/resource-optimization`),
  
  // Performance Analytics
  getZonePerformance: (zoneId, period = '30d') => 
    api.get(`/greenhouse/zones/${zoneId}/performance?period=${period}`),
  getComparisonAnalysis: (zoneIds) => 
    api.post('/greenhouse/analytics/compare-zones', { zone_ids: zoneIds }),
  
  // Trend Analysis
  getEnvironmentalTrends: (zoneId, metric, period = '7d') => 
    api.get(`/greenhouse/zones/${zoneId}/trends/${metric}?period=${period}`),
  getGrowthTrends: (zoneId, period = '30d') => 
    api.get(`/greenhouse/zones/${zoneId}/growth-trends?period=${period}`),
};

export const energyAPI = {
  // Energy Monitoring
  getCurrentEnergyUsage: () => api.get('/greenhouse/energy/current'),
  getEnergyHistory: (hours = 24) => api.get(`/greenhouse/energy/history?hours=${hours}`),
  getEnergyBreakdown: () => api.get('/greenhouse/energy/breakdown'),
  
  // Sustainability Metrics
  getCarbonFootprint: (period = '30d') => api.get(`/greenhouse/energy/carbon-footprint?period=${period}`),
  getEfficiencyMetrics: () => api.get('/greenhouse/energy/efficiency'),
  getSustainabilityScore: () => api.get('/greenhouse/energy/sustainability-score'),
  
  // Energy Optimization
  getOptimizationRecommendations: () => api.get('/greenhouse/energy/optimization-recommendations'),
  applyEnergyOptimization: (optimizationId) => 
    api.post(`/greenhouse/energy/apply-optimization/${optimizationId}`),
};

export const weatherAPI = {
  // Weather Integration
  getCurrentWeather: () => api.get('/greenhouse/weather/current'),
  getWeatherForecast: (days = 7) => api.get(`/greenhouse/weather/forecast?days=${days}`),
  getWeatherAlerts: () => api.get('/greenhouse/weather/alerts'),
  
  // Agricultural Insights
  getAgriculturalForecast: () => api.get('/greenhouse/weather/agricultural-forecast'),
  getGrowingConditionsForecast: (zoneId) => 
    api.get(`/greenhouse/zones/${zoneId}/growing-conditions-forecast`),
};

export const researchAPI = {
  // Data Export
  exportData: (exportConfig) => api.post('/greenhouse/research/export', exportConfig),
  getExportHistory: () => api.get('/greenhouse/research/exports'),
  downloadExport: (exportId) => api.get(`/greenhouse/research/exports/${exportId}/download`),
  
  // Research Analytics
  generateReport: (reportConfig) => api.post('/greenhouse/research/generate-report', reportConfig),
  getResearchInsights: (zoneId, analysisType) => 
    api.get(`/greenhouse/zones/${zoneId}/research-insights?type=${analysisType}`),
  
  // Collaboration
  shareData: (shareConfig) => api.post('/greenhouse/research/share', shareConfig),
  getSharedData: () => api.get('/greenhouse/research/shared'),
};

export const deviceAPI = {
  // Device Discovery
  discoverDevices: (networkRange = null) => 
    api.post('/greenhouse/devices/discover', { network_range: networkRange }),
  getDiscoveredDevices: () => api.get('/greenhouse/devices/discovered'),
  
  // Device Integration
  integrateDevice: (deviceConfig) => api.post('/greenhouse/devices/integrate', deviceConfig),
  getIntegratedDevices: () => api.get('/greenhouse/devices/integrated'),
  removeDevice: (deviceId) => api.delete(`/greenhouse/devices/${deviceId}`),
  
  // Device Control
  sendDeviceCommand: (deviceId, command) => 
    api.post(`/greenhouse/devices/${deviceId}/command`, command),
  getDeviceStatus: (deviceId) => api.get(`/greenhouse/devices/${deviceId}/status`),
  updateDeviceConfig: (deviceId, config) => 
    api.put(`/greenhouse/devices/${deviceId}/config`, config),
};

// Utility functions
export const formatSensorValue = (value, unit, precision = 1) => {
  if (value === null || value === undefined) return 'N/A';
  return `${Number(value).toFixed(precision)} ${unit}`;
};

export const getSensorStatusColor = (value, optimalRange) => {
  if (!optimalRange) return '#52c41a';
  
  const { min, max, optimal } = optimalRange;
  if (value < min || value > max) return '#ff4d4f';
  if (Math.abs(value - optimal) / optimal > 0.1) return '#faad14';
  return '#52c41a';
};

export const calculateHealthScore = (conditions, optimalRanges) => {
  if (!conditions || !optimalRanges) return 0;
  
  let totalScore = 0;
  let validConditions = 0;
  
  Object.keys(conditions).forEach(key => {
    if (optimalRanges[key] && conditions[key] !== null) {
      const value = conditions[key];
      const range = optimalRanges[key];
      
      let score = 1.0;
      if (value < range.min || value > range.max) {
        score = 0.3;
      } else if (Math.abs(value - range.optimal) / range.optimal > 0.1) {
        score = 0.7;
      }
      
      totalScore += score;
      validConditions++;
    }
  });
  
  return validConditions > 0 ? totalScore / validConditions : 0;
};

export default api;