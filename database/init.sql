-- RNR Solutions IoT Platform Database Schema
-- Enterprise-grade IoT device management database
-- © 2025 RNR Solutions. All rights reserved.
-- Initialize the database with required tables for RNR IoT Platform

-- Create the nodes table for RNR IoT device management
CREATE TABLE IF NOT EXISTS nodes (
    id SERIAL PRIMARY KEY,
    node_id TEXT UNIQUE NOT NULL,
    name TEXT,
    mac_address TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMPTZ
);

-- Create the firmware table
CREATE TABLE IF NOT EXISTS firmware (
    id SERIAL PRIMARY KEY,
    version TEXT NOT NULL,
    file_name TEXT,
    file_url TEXT,
    uploaded_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create the node_firmware junction table
CREATE TABLE IF NOT EXISTS node_firmware (
    node_id TEXT,
    firmware_id INT,
    assigned_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(node_id) REFERENCES nodes(node_id) ON DELETE CASCADE,
    FOREIGN KEY(firmware_id) REFERENCES firmware(id) ON DELETE CASCADE,
    PRIMARY KEY(node_id, firmware_id)
);

-- Create the sensor_data table
CREATE TABLE IF NOT EXISTS sensor_data (
    id BIGSERIAL PRIMARY KEY,
    node_id TEXT,
    data JSONB,
    received_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(node_id) REFERENCES nodes(node_id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_nodes_node_id ON nodes(node_id);
CREATE INDEX IF NOT EXISTS idx_nodes_last_seen ON nodes(last_seen);
CREATE INDEX IF NOT EXISTS idx_sensor_data_node_id ON sensor_data(node_id);
CREATE INDEX IF NOT EXISTS idx_sensor_data_received_at ON sensor_data(received_at);
CREATE INDEX IF NOT EXISTS idx_sensor_data_data ON sensor_data USING GIN(data);

-- Insert sample firmware version
INSERT INTO firmware (version, file_name, file_url) 
VALUES ('1.0.0', 'firmware_v1.0.0.bin', '/uploads/firmware_v1.0.0.bin')
ON CONFLICT DO NOTHING;
