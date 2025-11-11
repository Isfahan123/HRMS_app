-- Migration: Add username column and switch login to username-based auth
-- Safe to re-run: uses IF NOT EXISTS and exception-guarded DDL

-- 1) Add column if missing
ALTER TABLE IF EXISTS public.user_logins
    ADD COLUMN IF NOT EXISTS username text;

-- 2) Backfill existing rows: default username from email (before '@')
UPDATE public.user_logins
SET username = COALESCE(NULLIF(username, ''), split_part(email, '@', 1))
WHERE username IS NULL OR username = '';

-- Normalize to lowercase
UPDATE public.user_logins
SET username = lower(username)
WHERE username IS NOT NULL;

-- 3) Add unique constraint on username (guard against duplicates)
DO $$
BEGIN
    ALTER TABLE public.user_logins
        ADD CONSTRAINT user_logins_username_key UNIQUE (username);
EXCEPTION WHEN duplicate_object THEN
    -- constraint already exists
    NULL;
END $$;

-- 4) Set NOT NULL after backfill
ALTER TABLE public.user_logins
    ALTER COLUMN username SET NOT NULL;

-- 5) Create index for quick lookups
CREATE INDEX IF NOT EXISTS idx_user_logins_username
    ON public.user_logins USING btree (username);

-- 6) Trigger to always lowercase username on insert/update
CREATE OR REPLACE FUNCTION public.lowercase_username()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.username IS NOT NULL THEN
        NEW.username = lower(NEW.username);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS lowercase_username_user_logins_trigger ON public.user_logins;
CREATE TRIGGER lowercase_username_user_logins_trigger
    BEFORE INSERT OR UPDATE ON public.user_logins
    FOR EACH ROW
    EXECUTE FUNCTION public.lowercase_username();
