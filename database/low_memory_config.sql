-- RNR Solutions IoT Platform - PostgreSQL Low Memory Configuration
-- Optimized for 2GB RAM systems

-- Set PostgreSQL configuration for low memory usage
ALTER SYSTEM SET shared_buffers = '64MB';
ALTER SYSTEM SET effective_cache_size = '128MB';
ALTER SYSTEM SET maintenance_work_mem = '16MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 50;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Set work memory for queries
ALTER SYSTEM SET work_mem = '2MB';

-- Set autovacuum settings for low memory
ALTER SYSTEM SET autovacuum_max_workers = 2;
ALTER SYSTEM SET autovacuum_work_mem = '16MB';

-- Set connection limits
ALTER SYSTEM SET max_connections = 20;

-- Apply the configuration
SELECT pg_reload_conf();

-- Create optimized indexes for better performance with limited memory
\c rnr_iot_platform;

-- Add any additional low-memory optimizations here
-- Example: Set specific table storage parameters if needed
-- ALTER TABLE your_table SET (fillfactor = 90);
