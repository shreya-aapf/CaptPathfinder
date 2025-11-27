-- =====================================================
-- CaptPathfinder Initial Schema
-- =====================================================
-- This script sets up all tables for the senior exec detection system.
-- Run this against your Supabase/PostgreSQL database.

-- Set timezone to America/New_York
ALTER DATABASE postgres SET timezone TO 'America/New_York';

-- =====================================================
-- 1. Field Registry
-- =====================================================
CREATE TABLE IF NOT EXISTS field_registry (
    id SERIAL PRIMARY KEY,
    field_name TEXT UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert Job Title field
INSERT INTO field_registry (field_name, is_active)
VALUES ('Job Title', TRUE)
ON CONFLICT (field_name) DO NOTHING;

-- =====================================================
-- 2. Events Raw (Short-lived audit + processing queue)
-- =====================================================
CREATE TABLE IF NOT EXISTS events_raw (
    id BIGSERIAL PRIMARY KEY,
    event_id TEXT,
    user_id TEXT NOT NULL,
    username TEXT,
    profile_field TEXT,
    value TEXT,
    old_value TEXT,
    received_at TIMESTAMPTZ DEFAULT NOW(),
    idempotency_key TEXT UNIQUE NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_events_raw_user_id ON events_raw(user_id);
CREATE INDEX IF NOT EXISTS idx_events_raw_processed ON events_raw(processed) WHERE NOT processed;
CREATE INDEX IF NOT EXISTS idx_events_raw_received_at ON events_raw(received_at);

-- =====================================================
-- 3. User State (Persistent - only senior execs)
-- =====================================================
CREATE TABLE IF NOT EXISTS user_state (
    user_id TEXT PRIMARY KEY,
    username TEXT,
    title TEXT,
    seniority_level TEXT CHECK (seniority_level IN ('vp', 'csuite')),
    country TEXT,
    company TEXT,
    joined_at TIMESTAMPTZ,  -- Community signup date
    first_detected_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_state_seniority ON user_state(seniority_level);
CREATE INDEX IF NOT EXISTS idx_user_state_joined_at ON user_state(joined_at);

-- =====================================================
-- 4. Detections (For digest + reporting)
-- =====================================================
CREATE TABLE IF NOT EXISTS detections (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    username TEXT,
    title TEXT,
    seniority_level TEXT CHECK (seniority_level IN ('vp', 'csuite')),
    country TEXT,
    company TEXT,
    joined_at TIMESTAMPTZ,  -- Community signup date
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    rules_version TEXT DEFAULT 'v1',
    included_in_digest BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_detections_user_id ON detections(user_id);
CREATE INDEX IF NOT EXISTS idx_detections_detected_at ON detections(detected_at);
CREATE INDEX IF NOT EXISTS idx_detections_included_in_digest ON detections(included_in_digest) WHERE NOT included_in_digest;

-- =====================================================
-- 5. Digests
-- =====================================================
CREATE TABLE IF NOT EXISTS digests (
    id BIGSERIAL PRIMARY KEY,
    week_start DATE,
    week_end DATE,
    channel TEXT CHECK (channel IN ('email', 'teams')),
    payload JSONB,
    sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    sent_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_digests_sent ON digests(sent) WHERE NOT sent;
CREATE INDEX IF NOT EXISTS idx_digests_channel ON digests(channel);
CREATE INDEX IF NOT EXISTS idx_digests_week ON digests(week_start, week_end);

-- =====================================================
-- 6. Reports (Month-end)
-- =====================================================
CREATE TABLE IF NOT EXISTS reports (
    id BIGSERIAL PRIMARY KEY,
    month_label TEXT NOT NULL,  -- e.g., "2025-11"
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    rules_version TEXT DEFAULT 'v1',
    file_uri TEXT,
    summary JSONB
);

CREATE INDEX IF NOT EXISTS idx_reports_month_label ON reports(month_label);

-- =====================================================
-- Helper Functions
-- =====================================================

-- Function to purge old events (housekeeping)
CREATE OR REPLACE FUNCTION purge_old_events()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM events_raw
    WHERE received_at < NOW() - INTERVAL '14 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RAISE NOTICE 'Purged % old events', deleted_count;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Schema complete
-- =====================================================

