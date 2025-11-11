-- Create tiers table
CREATE TABLE IF NOT EXISTS leave_caps_tiers (
  id TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  min_years NUMERIC NOT NULL DEFAULT 0,
  max_years NUMERIC NOT NULL DEFAULT 9999
);

-- Create caps table (one row per tier + leave_type)
CREATE TABLE IF NOT EXISTS leave_caps (
  id BIGSERIAL PRIMARY KEY,
  tier_id TEXT NOT NULL REFERENCES leave_caps_tiers(id) ON DELETE CASCADE,
  leave_type TEXT NOT NULL,
  cap INTEGER NOT NULL DEFAULT 0,
  UNIQUE (tier_id, leave_type)
);

-- Indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_leave_caps_tier_id ON leave_caps (tier_id);
