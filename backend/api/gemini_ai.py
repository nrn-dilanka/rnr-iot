import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException

import google.generativeai as genai

logger = logging.getLogger(__name__)

class GeminiAIService:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyAs2JqPjvUcWeg5K2Vxeto7j37GzUzABUY")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("Gemini AI Service initialized")
        
    def analyze_esp32_data(self, sensor_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze sensor data using Gemini AI to provide insights and recommendations
        """
        try:
            # Prepare the sensor data summary
            data_summary = self._prepare_sensor_data_summary(sensor_data)
            
            prompt = f"""
            As an IoT expert, analyze the following ESP32 sensor data and provide insights:
            
            Sensor Data Summary:
            {json.dumps(data_summary, indent=2)}
            
            Please provide:
            1. Overall system health assessment
            2. Any anomalies or patterns detected
            3. Recommendations for optimization
            4. Potential issues or alerts
            5. Performance summary
            
            Respond in JSON format with the following structure:
            {{
                "health_score": 0-100,
                "status": "good/warning/critical",
                "insights": ["insight1", "insight2"],
                "recommendations": ["rec1", "rec2"],
                "alerts": ["alert1", "alert2"],
                "summary": "brief summary"
            }}
            """
            
            # Generate content using Gemini
            response = self.model.generate_content(prompt)
            
            # Parse the response
            try:
                # Clean the response text to extract JSON
                response_text = response.text.strip()
                if response_text.startswith('```json'):
                    response_text = response_text.replace('```json', '').replace('```', '').strip()
                
                analysis_result = json.loads(response_text)
                
                # Validate the response structure
                required_fields = ['health_score', 'status', 'insights', 'recommendations', 'alerts', 'summary']
                for field in required_fields:
                    if field not in analysis_result:
                        analysis_result[field] = [] if field in ['insights', 'recommendations', 'alerts'] else "Not available"
                
                return analysis_result
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse Gemini response as JSON: {response.text}")
                return {
                    "health_score": 50,
                    "status": "unknown",
                    "insights": ["Unable to parse AI analysis"],
                    "recommendations": ["Check sensor data format"],
                    "alerts": [],
                    "summary": "AI analysis failed - manual review recommended"
                }
                
        except Exception as e:
            logger.error(f"Error in Gemini AI analysis: {str(e)}")
            return {
                "health_score": 0,
                "status": "error",
                "insights": [f"Analysis failed: {str(e)}"],
                "recommendations": ["Check Gemini AI service configuration"],
                "alerts": ["AI analysis unavailable"],
                "summary": "Unable to perform AI analysis"
            }
    
    def analyze_device_performance(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze individual device performance using Gemini AI
        """
        try:
            prompt = f"""
            As an IoT device expert, analyze this ESP32 device performance data:
            
            Device Data:
            {json.dumps(device_data, indent=2)}
            
            Provide analysis in JSON format:
            {{
                "performance_score": 0-100,
                "status": "excellent/good/fair/poor/critical",
                "issues": ["issue1", "issue2"],
                "optimizations": ["opt1", "opt2"],
                "maintenance_needed": true/false,
                "summary": "device analysis summary"
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            try:
                response_text = response.text.strip()
                if response_text.startswith('```json'):
                    response_text = response_text.replace('```json', '').replace('```', '').strip()
                
                return json.loads(response_text)
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse device analysis response: {response.text}")
                return {
                    "performance_score": 50,
                    "status": "unknown",
                    "issues": ["Unable to analyze device data"],
                    "optimizations": ["Check device configuration"],
                    "maintenance_needed": False,
                    "summary": "Analysis unavailable"
                }
                
        except Exception as e:
            logger.error(f"Error in device performance analysis: {str(e)}")
            return {
                "performance_score": 0,
                "status": "error",
                "issues": [f"Analysis failed: {str(e)}"],
                "optimizations": ["Check AI service"],
                "maintenance_needed": True,
                "summary": "Device analysis failed"
            }
    
    def generate_recommendations(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate optimization recommendations based on analysis data
        """
        try:
            prompt = f"""
            Based on this IoT system analysis, provide optimization recommendations:
            
            Analysis Data:
            {json.dumps(analysis_data, indent=2)}
            
            Generate recommendations in JSON format:
            {{
                "immediate_actions": ["action1", "action2"],
                "short_term_improvements": ["improvement1", "improvement2"],
                "long_term_strategy": ["strategy1", "strategy2"],
                "cost_optimization": ["cost_saving1", "cost_saving2"],
                "security_recommendations": ["security1", "security2"],
                "priority_level": "high/medium/low"
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            try:
                response_text = response.text.strip()
                if response_text.startswith('```json'):
                    response_text = response_text.replace('```json', '').replace('```', '').strip()
                
                return json.loads(response_text)
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse recommendations response: {response.text}")
                return {
                    "immediate_actions": ["Review system manually"],
                    "short_term_improvements": ["Update configurations"],
                    "long_term_strategy": ["Plan system upgrade"],
                    "cost_optimization": ["Monitor resource usage"],
                    "security_recommendations": ["Review access controls"],
                    "priority_level": "medium"
                }
                
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return {
                "immediate_actions": [f"Error: {str(e)}"],
                "short_term_improvements": ["Check AI service"],
                "long_term_strategy": ["Ensure service reliability"],
                "cost_optimization": ["Optimize service usage"],
                "security_recommendations": ["Review system security"],
                "priority_level": "high"
            }
    
    def _prepare_sensor_data_summary(self, sensor_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Prepare sensor data summary for AI analysis
        """
        if not sensor_data:
            return {
                "total_readings": 0,
                "devices": {},
                "time_range": "No data available",
                "summary": "No sensor data to analyze"
            }
        
        # Group data by device
        devices = {}
        timestamps = []
        
        for reading in sensor_data:
            device_id = reading.get('device_id', 'unknown')
            timestamp = reading.get('timestamp', 'unknown')
            
            if timestamp != 'unknown':
                timestamps.append(timestamp)
            
            if device_id not in devices:
                devices[device_id] = {
                    'readings_count': 0,
                    'temperature': [],
                    'humidity': [],
                    'humidity_mq': [],  # MQ humidity sensor from GPIO 25
                    'humidity_mq_raw': [],  # Raw ADC values from MQ sensor
                    'gas_level': [],
                    'gas_sensor': [],  # Raw gas sensor values
                    'last_seen': timestamp
                }
            
            devices[device_id]['readings_count'] += 1
            
            # Collect sensor values
            if 'temperature' in reading:
                devices[device_id]['temperature'].append(reading['temperature'])
            if 'humidity' in reading:
                devices[device_id]['humidity'].append(reading['humidity'])
            if 'humidity_mq' in reading:
                devices[device_id]['humidity_mq'].append(reading['humidity_mq'])
            if 'humidity_mq_raw' in reading:
                devices[device_id]['humidity_mq_raw'].append(reading['humidity_mq_raw'])
            if 'gas_level' in reading:
                devices[device_id]['gas_level'].append(reading['gas_level'])
            if 'gas_sensor' in reading:
                devices[device_id]['gas_sensor'].append(reading['gas_sensor'])
        
        # Calculate statistics for each device
        for device_id, data in devices.items():
            for sensor_type in ['temperature', 'humidity', 'humidity_mq', 'humidity_mq_raw', 'gas_level', 'gas_sensor']:
                values = data[sensor_type]
                if values:
                    data[f'{sensor_type}_avg'] = sum(values) / len(values)
                    data[f'{sensor_type}_min'] = min(values)
                    data[f'{sensor_type}_max'] = max(values)
                    data[f'{sensor_type}_latest'] = values[-1]
                else:
                    data[f'{sensor_type}_avg'] = None
                    data[f'{sensor_type}_min'] = None
                    data[f'{sensor_type}_max'] = None
                    data[f'{sensor_type}_latest'] = None
        
        return {
            "total_readings": len(sensor_data),
            "active_devices": len(devices),
            "devices": devices,
            "time_range": f"{min(timestamps) if timestamps else 'N/A'} to {max(timestamps) if timestamps else 'N/A'}",
            "data_quality": "good" if len(sensor_data) > 10 else "limited"
        }
    
    def generate_maintenance_report(self, system_overview: Dict[str, Any]) -> str:
        """
        Generate a comprehensive maintenance report using Gemini AI
        """
        try:
            prompt = f"""
            As a professional IoT system analyst, generate a comprehensive maintenance report based on this system data:
            
            System Overview:
            {json.dumps(system_overview, indent=2)}
            
            Please provide a detailed maintenance report in markdown format covering:
            
            1. EXECUTIVE SUMMARY
            2. SYSTEM HEALTH OVERVIEW
            3. DEVICE STATUS ANALYSIS
            4. ANOMALY ANALYSIS & RISK ASSESSMENT
            5. PERFORMANCE TRENDS
            6. MAINTENANCE RECOMMENDATIONS
            7. PREVENTIVE MEASURES
            8. NEXT STEPS & ACTION ITEMS
            
            Make the report professional, actionable, and include specific recommendations with priority levels.
            Use technical language appropriate for IoT system administrators.
            """
            
            response = self.model.generate_content(prompt)
            
            # Return the generated report text
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating maintenance report: {str(e)}")
            return f"""
# IoT Platform Maintenance Report
## Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### SYSTEM STATUS: ERROR
**Issue**: Unable to generate AI-powered maintenance report.
**Error**: {str(e)}

### BASIC SYSTEM OVERVIEW:
- **Total Devices**: {system_overview.get('total_devices', 'Unknown')}
- **Active Devices**: {system_overview.get('active_devices', 'Unknown')}
- **Data Points**: {system_overview.get('total_data_points', 'Unknown')}
- **Report Generation**: Failed - Manual review required

### RECOMMENDATIONS:
1. Check Gemini AI service configuration
2. Verify API key validity
3. Review system logs for detailed error information
4. Perform manual system assessment

### NEXT STEPS:
- Contact system administrator for AI service troubleshooting
- Consider manual maintenance review in the interim
            """

# Create a global instance
gemini_ai_service = GeminiAIService()
