import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Gemini AI package
import google.generativeai as genai

# Configure Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY environment variable not set")
    raise ValueError("GEMINI_API_KEY environment variable not set")

genai.configure(api_key=GEMINI_API_KEY)

class GeminiAIService:
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def analyze_esp32_data(self, sensor_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze ESP32 sensor data using Gemini AI
        """
        try:
            # Prepare data for AI analysis
            data_summary = self._prepare_sensor_data_summary(sensor_data)
            
            prompt = f"""
            As an IoT data analyst AI, analyze the following ESP32 sensor data and provide insights:
            
            Sensor Data Summary:
            {data_summary}
            
            Please analyze this data and provide:
            1. Anomaly detection (temperature, humidity, gas levels)
            2. Pattern recognition and trends
            3. Recommendations for device management
            4. Firmware update suggestions based on performance
            5. Risk assessment and alerts
            
            Provide your response in JSON format with the following structure:
            {{
                "anomalies": [
                    {{
                        "type": "temperature/humidity/gas/performance",
                        "severity": "low/medium/high/critical",
                        "device_id": "device_identifier",
                        "value": "current_value",
                        "threshold": "expected_range",
                        "recommendation": "suggested_action"
                    }}
                ],
                "trends": [
                    {{
                        "metric": "temperature/humidity/gas",
                        "direction": "increasing/decreasing/stable",
                        "confidence": "high/medium/low",
                        "prediction": "future_outlook"
                    }}
                ],
                "recommendations": [
                    {{
                        "type": "maintenance/firmware/configuration",
                        "priority": "high/medium/low",
                        "action": "specific_recommendation",
                        "devices": ["affected_device_ids"]
                    }}
                ],
                "overall_health": "excellent/good/fair/poor/critical",
                "risk_level": "low/medium/high/critical"
            }}
            """
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=2048,
                    response_mime_type="application/json"
                )
            )
            
            # Parse the JSON response
            try:
                analysis_result = json.loads(response.text)
                return analysis_result
            except json.JSONDecodeError:
                logger.error(f"Failed to parse AI response as JSON: {response.text}")
                return self._create_fallback_analysis()
                
        except Exception as e:
            logger.error(f"Error in Gemini AI analysis: {str(e)}")
            return self._create_fallback_analysis()
    
    def recommend_firmware_action(self, device_performance: Dict[str, Any], available_firmware: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get AI recommendation for firmware management
        """
        try:
            prompt = f"""
            As an IoT firmware management AI, analyze the following device performance data and available firmware versions:
            
            Device Performance:
            {json.dumps(device_performance, indent=2)}
            
            Available Firmware:
            {json.dumps(available_firmware, indent=2)}
            
            Determine if firmware updates are needed and provide recommendations in JSON format:
            {{
                "update_needed": true/false,
                "recommended_firmware": "firmware_id_or_null",
                "priority": "low/medium/high/critical",
                "reasoning": "explanation_for_recommendation",
                "estimated_improvement": "expected_benefits",
                "rollback_risk": "low/medium/high",
                "deployment_timing": "immediate/scheduled/maintenance_window"
            }}
            """
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=1024,
                    response_mime_type="application/json"
                )
            )
            
            try:
                recommendation = json.loads(response.text)
                return recommendation
            except json.JSONDecodeError:
                logger.error(f"Failed to parse firmware recommendation as JSON: {response.text}")
                return self._create_fallback_firmware_recommendation()
                
        except Exception as e:
            logger.error(f"Error in firmware recommendation: {str(e)}")
            return self._create_fallback_firmware_recommendation()
    
    def generate_maintenance_report(self, system_overview: Dict[str, Any]) -> str:
        """
        Generate comprehensive maintenance report using AI
        """
        try:
            prompt = f"""
            As an IoT system maintenance specialist, generate a comprehensive maintenance report based on the following system overview:
            
            System Overview:
            {json.dumps(system_overview, indent=2)}
            
            Generate a detailed maintenance report covering:
            1. System health summary
            2. Critical issues requiring immediate attention
            3. Preventive maintenance recommendations
            4. Performance optimization suggestions
            5. Long-term system improvement roadmap
            
            Format the report in clear, professional language suitable for technical teams.
            """
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.4,
                    max_output_tokens=3000
                )
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating maintenance report: {str(e)}")
            return "Unable to generate maintenance report due to AI service error."
    
    def _prepare_sensor_data_summary(self, sensor_data: List[Dict[str, Any]]) -> str:
        """
        Prepare sensor data summary for AI analysis
        """
        if not sensor_data:
            return "No sensor data available"
        
        summary = {
            "total_readings": len(sensor_data),
            "devices": list(set([data.get('node_id', 'unknown') for data in sensor_data])),
            "time_range": {
                "start": sensor_data[-1].get('received_at', 'unknown') if sensor_data else 'unknown',
                "end": sensor_data[0].get('received_at', 'unknown') if sensor_data else 'unknown'
            },
            "sample_readings": sensor_data[:5],  # First 5 readings as sample
            "metrics": self._calculate_basic_metrics(sensor_data)
        }
        
        return json.dumps(summary, indent=2, default=str)
    
    def _calculate_basic_metrics(self, sensor_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate basic metrics from sensor data
        """
        if not sensor_data:
            return {}
        
        temps = []
        humidity = []
        gas = []
        
        for data in sensor_data:
            sensor_values = data.get('data', {})
            if 'temperature' in sensor_values:
                temps.append(sensor_values['temperature'])
            if 'humidity' in sensor_values:
                humidity.append(sensor_values['humidity'])
            if 'gas' in sensor_values:
                gas.append(sensor_values['gas'])
        
        metrics = {}
        if temps:
            metrics['temperature'] = {
                'avg': sum(temps) / len(temps),
                'min': min(temps),
                'max': max(temps),
                'count': len(temps)
            }
        if humidity:
            metrics['humidity'] = {
                'avg': sum(humidity) / len(humidity),
                'min': min(humidity),
                'max': max(humidity),
                'count': len(humidity)
            }
        if gas:
            metrics['gas'] = {
                'avg': sum(gas) / len(gas),
                'min': min(gas),
                'max': max(gas),
                'count': len(gas)
            }
        
        return metrics
    
    def _create_fallback_analysis(self) -> Dict[str, Any]:
        """
        Create fallback analysis when AI service fails
        """
        return {
            "anomalies": [],
            "trends": [],
            "recommendations": [
                {
                    "type": "maintenance",
                    "priority": "medium",
                    "action": "AI service unavailable - perform manual data review",
                    "devices": []
                }
            ],
            "overall_health": "unknown",
            "risk_level": "medium"
        }
    
    def _create_fallback_firmware_recommendation(self) -> Dict[str, Any]:
        """
        Create fallback firmware recommendation when AI service fails
        """
        return {
            "update_needed": False,
            "recommended_firmware": None,
            "priority": "low",
            "reasoning": "AI service unavailable - manual review recommended",
            "estimated_improvement": "Unknown",
            "rollback_risk": "medium",
            "deployment_timing": "manual_review"
        }

# Initialize global AI service instance
gemini_ai_service = GeminiAIService()
