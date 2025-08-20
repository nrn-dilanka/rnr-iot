-- Database migration script to ensure proper schema
-- Run this to fix missing columns in the nodes table

-- Add missing columns if they don't exist
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS is_active VARCHAR(50) DEFAULT 'true';
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'offline';

-- Verify the schema
\d nodes;

-- Show current data
SELECT COUNT(*) as total_nodes FROM nodes;
SELECT COUNT(*) as total_sensor_data FROM sensor_data;

-- Create missing indexes if needed
CREATE INDEX IF NOT EXISTS idx_nodes_status ON nodes(status);
CREATE INDEX IF NOT EXISTS idx_nodes_is_active ON nodes(is_active);

COMMIT;
