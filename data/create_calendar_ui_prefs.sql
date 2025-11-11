-- Migration: create calendar_ui_prefs table
-- Stores UI preferences for the calendar tab (per-user optional)
-- Apply this using psql or Supabase SQL editor

CREATE TABLE IF NOT EXISTS calendar_ui_prefs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_email TEXT NULL, -- NULL implies global/default preferences
    prefs JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_calendar_ui_prefs_user_email ON calendar_ui_prefs(user_email);
