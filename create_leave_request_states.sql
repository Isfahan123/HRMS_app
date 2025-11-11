-- Migration: create_leave_request_states table
-- Run this on your Postgres / Supabase instance to enable storing per-leave selected states
-- You can execute this using psql or via Supabase SQL editor

CREATE TABLE IF NOT EXISTS leave_request_states (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    leave_request_id UUID NOT NULL,
    state TEXT NOT NULL,
    -- Whether observances (astronomical/natural observances) were included when selecting holidays
    show_observances BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leave_request_states_leave_request_id ON leave_request_states(leave_request_id);
