-- Create the raw schema
CREATE SCHEMA IF NOT EXISTS raw;

-- 1. HTTP request logs
CREATE TABLE raw.api_request_logs (
    request_uuid UUID PRIMARY KEY,
    request_started_at TIMESTAMPTZ,
    request_finished_at TIMESTAMPTZ,
    request_duration_ms BIGINT,
    status VARCHAR,
    error_type VARCHAR,
    http_status_code INTEGER,
    loaded_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2. Raw vehicle positions from the Olho Vivo API
CREATE TABLE raw.raw_vehicle_positions (
    request_uuid UUID NOT NULL,
    fetched_at TIMESTAMPTZ,
    cl BIGINT,
    p VARCHAR,
    a BOOLEAN,
    ta VARCHAR,
    py DOUBLE,
    px DOUBLE,
    loaded_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
