-- Migration: Add failed login tracking and lockout columns to user_logins
-- Run this in your Supabase SQL editor or via psql against the project's database.

BEGIN;

-- Add integer counter for failed login attempts (default 0)
ALTER TABLE IF EXISTS public.user_logins
    ADD COLUMN IF NOT EXISTS failed_attempts INTEGER DEFAULT 0 NOT NULL;

-- Add timestamp for lockout expiry (nullable)
ALTER TABLE IF EXISTS public.user_logins
    ADD COLUMN IF NOT EXISTS locked_until TIMESTAMPTZ NULL;

-- Optional index to help queries that filter locked accounts
CREATE INDEX IF NOT EXISTS idx_user_logins_locked_until ON public.user_logins(locked_until);

COMMIT;

-- Notes:
-- 1) This migration is idempotent (uses IF NOT EXISTS) and safe to re-run.
-- 2) After applying, update application logic to check `locked_until` and
--    increment/reset `failed_attempts` as appropriate.
