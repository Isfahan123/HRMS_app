-- Migration: create calendar_holidays table
-- Stores authoritative holiday entries used by the Calendar UI
-- Apply this using psql or Supabase SQL editor

CREATE TABLE IF NOT EXISTS calendar_holidays (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    date DATE NOT NULL,
    name TEXT NOT NULL,
    state TEXT NULL, -- NULL implies nationwide
    is_national BOOLEAN DEFAULT FALSE,
    is_observance BOOLEAN DEFAULT FALSE,
    source TEXT DEFAULT 'admin', -- e.g. 'admin' or 'calendarific'
    created_by TEXT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_calendar_holidays_date ON calendar_holidays (date);
CREATE INDEX IF NOT EXISTS idx_calendar_holidays_state ON calendar_holidays (state);

-- Optional trigger to keep updated_at current on updates
CREATE OR REPLACE FUNCTION update_calendar_holidays_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_calendar_holidays_updated_at ON calendar_holidays;
CREATE TRIGGER trigger_update_calendar_holidays_updated_at
BEFORE UPDATE ON calendar_holidays
FOR EACH ROW
EXECUTE FUNCTION update_calendar_holidays_updated_at();
