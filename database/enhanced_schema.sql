-- Enhanced RNR Solutions IoT Platform Database Schema for Industrial Management
-- Extends the existing schema with new tables for advanced enterprise features

-- Create crop profiles table
CREATE TABLE IF NOT EXISTS crop_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    scientific_name VARCHAR(150),
    category VARCHAR(50), -- vegetables, fruits, herbs, etc.
    growth_stages JSONB NOT NULL, -- Array of growth stage objects
    optimal_conditions JSONB NOT NULL, -- Temperature, humidity, etc. ranges
    nutrient_schedule JSONB, -- NPK requirements by growth stage
    harvest_indicators JSONB, -- Visual and measurable harvest indicators
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create greenhouse zones table
CREATE TABLE IF NOT EXISTS greenhouse_zones (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    area_sqm DECIMAL(8,2), -- Area in square meters
    location_coordinates JSONB, -- GPS or relative coordinates
    crop_profile_id INTEGER REFERENCES crop_profiles(id),
    planting_date DATE,
    expected_harvest_date DATE,
    current_growth_stage VARCHAR(50),
    zone_config JSONB, -- Zone-specific configuration
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Enhanced sensor data table with zone support
CREATE TABLE IF NOT EXISTS enhanced_sensor_data (
    id BIGSERIAL PRIMARY KEY,
    node_id TEXT NOT NULL,
    zone_id INTEGER REFERENCES greenhouse_zones(id),
    sensor_type VARCHAR(50) NOT NULL, -- temperature, humidity, soil_moisture, etc.
    sensor_location VARCHAR(100), -- Specific location within zone
    value DECIMAL(10,4) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    quality_score DECIMAL(3,2) DEFAULT 1.0, -- Data quality indicator (0-1)
    calibration_applied BOOLEAN DEFAULT FALSE,
    raw_value DECIMAL(10,4), -- Original uncalibrated value
    metadata JSONB, -- Additional sensor-specific data
    received_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(node_id) REFERENCES nodes(node_id) ON DELETE CASCADE
);

-- Environmental conditions summary table
CREATE TABLE IF NOT EXISTS environmental_conditions (
    id BIGSERIAL PRIMARY KEY,
    zone_id INTEGER REFERENCES greenhouse_zones(id),
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    temperature_avg DECIMAL(5,2),
    temperature_min DECIMAL(5,2),
    temperature_max DECIMAL(5,2),
    humidity_avg DECIMAL(5,2),
    humidity_min DECIMAL(5,2),
    humidity_max DECIMAL(5,2),
    soil_moisture_avg DECIMAL(5,2),
    soil_moisture_min DECIMAL(5,2),
    soil_moisture_max DECIMAL(5,2),
    light_intensity_avg DECIMAL(8,2),
    co2_level_avg DECIMAL(6,2),
    ph_level_avg DECIMAL(4,2),
    ec_level_avg DECIMAL(6,2),
    conditions_score DECIMAL(3,2), -- Overall conditions score (0-1)
    ai_analysis JSONB -- AI-generated analysis and recommendations
);

-- Automation rules table
CREATE TABLE IF NOT EXISTS automation_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    zone_id INTEGER REFERENCES greenhouse_zones(id),
    rule_type VARCHAR(50) NOT NULL, -- irrigation, climate, lighting, etc.
    conditions JSONB NOT NULL, -- Rule conditions in JSON format
    actions JSONB NOT NULL, -- Actions to execute
    schedule JSONB, -- Time-based scheduling
    priority INTEGER DEFAULT 5, -- Rule priority (1-10)
    enabled BOOLEAN DEFAULT TRUE,
    ai_enhanced BOOLEAN DEFAULT FALSE,
    last_triggered TIMESTAMPTZ,
    trigger_count INTEGER DEFAULT 0,
    created_by INTEGER, -- User ID who created the rule
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Alert system table
CREATE TABLE IF NOT EXISTS system_alerts (
    id BIGSERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL, -- critical, warning, info
    category VARCHAR(50) NOT NULL, -- environmental, equipment, crop, system
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    zone_id INTEGER REFERENCES greenhouse_zones(id),
    node_id TEXT REFERENCES nodes(node_id),
    severity INTEGER NOT NULL, -- 1-10 scale
    status VARCHAR(20) DEFAULT 'active', -- active, acknowledged, resolved
    auto_actions JSONB, -- Automatic actions taken
    recommended_actions JSONB, -- AI-recommended actions
    escalation_path JSONB, -- Escalation configuration
    acknowledged_by INTEGER, -- User ID who acknowledged
    acknowledged_at TIMESTAMPTZ,
    resolved_by INTEGER, -- User ID who resolved
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Energy monitoring table
CREATE TABLE IF NOT EXISTS energy_monitoring (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    solar_generation_kwh DECIMAL(8,4) DEFAULT 0,
    grid_consumption_kwh DECIMAL(8,4) DEFAULT 0,
    battery_level_percent DECIMAL(5,2) DEFAULT 0,
    battery_capacity_kwh DECIMAL(8,4) DEFAULT 0,
    total_consumption_kwh DECIMAL(8,4) NOT NULL,
    device_breakdown JSONB, -- Consumption by device type
    cost_per_kwh DECIMAL(6,4) DEFAULT 0,
    carbon_footprint_kg DECIMAL(8,4) DEFAULT 0,
    efficiency_score DECIMAL(3,2) DEFAULT 0 -- Energy efficiency score (0-1)
);

-- Crop growth tracking table
CREATE TABLE IF NOT EXISTS crop_growth_tracking (
    id BIGSERIAL PRIMARY KEY,
    zone_id INTEGER REFERENCES greenhouse_zones(id) NOT NULL,
    measurement_date DATE NOT NULL,
    growth_stage VARCHAR(50) NOT NULL,
    plant_height_cm DECIMAL(6,2),
    leaf_count INTEGER,
    stem_diameter_mm DECIMAL(5,2),
    fruit_count INTEGER DEFAULT 0,
    estimated_yield_kg DECIMAL(8,3),
    health_score DECIMAL(3,2), -- Plant health score (0-1)
    growth_rate_score DECIMAL(3,2), -- Growth rate compared to optimal (0-1)
    notes TEXT,
    images JSONB, -- Array of image URLs/paths
    measured_by INTEGER, -- User ID who took measurements
    ai_analysis JSONB, -- AI-generated growth analysis
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Weather integration data table
CREATE TABLE IF NOT EXISTS weather_data (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(50) NOT NULL, -- openweather, weatherapi, etc.
    location_name VARCHAR(100),
    coordinates JSONB, -- lat, lng
    current_conditions JSONB NOT NULL,
    forecast_24h JSONB,
    forecast_7d JSONB,
    weather_alerts JSONB,
    agricultural_insights JSONB, -- AI-generated insights for agriculture
    data_quality DECIMAL(3,2) DEFAULT 1.0 -- Data quality score (0-1)
);

-- Business analytics exports table
CREATE TABLE IF NOT EXISTS business_exports (
    id SERIAL PRIMARY KEY,
    export_name VARCHAR(200) NOT NULL,
    export_type VARCHAR(50) NOT NULL, -- csv, excel, pdf, json, matlab
    date_range_start TIMESTAMPTZ NOT NULL,
    date_range_end TIMESTAMPTZ NOT NULL,
    data_categories JSONB NOT NULL, -- Array of data categories included
    filters JSONB, -- Export filters applied
    file_path VARCHAR(500),
    file_size_bytes BIGINT,
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    exported_by INTEGER NOT NULL, -- User ID
    shared_with JSONB, -- Array of user IDs with access
    download_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_enhanced_sensor_data_zone_id ON enhanced_sensor_data(zone_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_sensor_data_sensor_type ON enhanced_sensor_data(sensor_type);
CREATE INDEX IF NOT EXISTS idx_enhanced_sensor_data_received_at ON enhanced_sensor_data(received_at);
CREATE INDEX IF NOT EXISTS idx_environmental_conditions_zone_id ON environmental_conditions(zone_id);
CREATE INDEX IF NOT EXISTS idx_environmental_conditions_timestamp ON environmental_conditions(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_alerts_status ON system_alerts(status);
CREATE INDEX IF NOT EXISTS idx_system_alerts_severity ON system_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_system_alerts_created_at ON system_alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_crop_growth_tracking_zone_id ON crop_growth_tracking(zone_id);
CREATE INDEX IF NOT EXISTS idx_crop_growth_tracking_measurement_date ON crop_growth_tracking(measurement_date);
CREATE INDEX IF NOT EXISTS idx_energy_monitoring_timestamp ON energy_monitoring(timestamp);
CREATE INDEX IF NOT EXISTS idx_weather_data_timestamp ON weather_data(timestamp);

-- Insert sample crop profiles
INSERT INTO crop_profiles (name, scientific_name, category, growth_stages, optimal_conditions, nutrient_schedule) VALUES
('Tomato', 'Solanum lycopersicum', 'vegetables', 
 '[
   {"stage": "seedling", "duration_days": 14, "description": "Initial growth phase"},
   {"stage": "vegetative", "duration_days": 35, "description": "Leaf and stem development"},
   {"stage": "flowering", "duration_days": 21, "description": "Flower formation"},
   {"stage": "fruiting", "duration_days": 45, "description": "Fruit development and ripening"}
 ]',
 '{
   "temperature": {"min": 18, "max": 26, "optimal": 22},
   "humidity": {"min": 60, "max": 70, "optimal": 65},
   "soil_moisture": {"min": 40, "max": 70, "optimal": 55},
   "light_hours": 14,
   "co2_ppm": {"min": 400, "max": 800, "optimal": 600},
   "ph": {"min": 6.0, "max": 7.0, "optimal": 6.5}
 }',
 '{
   "seedling": {"N": 50, "P": 30, "K": 40},
   "vegetative": {"N": 120, "P": 50, "K": 80},
   "flowering": {"N": 80, "P": 80, "K": 120},
   "fruiting": {"N": 60, "P": 100, "K": 150}
 }'
),
('Lettuce', 'Lactuca sativa', 'vegetables',
 '[
   {"stage": "seedling", "duration_days": 10, "description": "Initial growth phase"},
   {"stage": "vegetative", "duration_days": 25, "description": "Leaf development"},
   {"stage": "mature", "duration_days": 15, "description": "Ready for harvest"}
 ]',
 '{
   "temperature": {"min": 15, "max": 22, "optimal": 18},
   "humidity": {"min": 50, "max": 60, "optimal": 55},
   "soil_moisture": {"min": 50, "max": 80, "optimal": 65},
   "light_hours": 12,
   "co2_ppm": {"min": 350, "max": 600, "optimal": 450},
   "ph": {"min": 6.0, "max": 7.0, "optimal": 6.2}
 }',
 '{
   "seedling": {"N": 40, "P": 25, "K": 30},
   "vegetative": {"N": 80, "P": 40, "K": 60},
   "mature": {"N": 60, "P": 35, "K": 70}
 }'
) ON CONFLICT DO NOTHING;

-- Insert sample greenhouse zones
INSERT INTO greenhouse_zones (name, description, area_sqm, crop_profile_id, planting_date, current_growth_stage) VALUES
('Zone A - Tomatoes', 'Main tomato growing area with optimal climate control', 25.0, 1, CURRENT_DATE - INTERVAL '30 days', 'vegetative'),
('Zone B - Lettuce', 'Leafy greens section with hydroponic system', 15.0, 2, CURRENT_DATE - INTERVAL '20 days', 'vegetative'),
('Zone C - Mixed Herbs', 'Herb garden with various aromatic plants', 10.0, NULL, CURRENT_DATE - INTERVAL '15 days', 'vegetative')
ON CONFLICT DO NOTHING;