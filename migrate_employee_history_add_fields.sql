-- Migration: add job_title, department, functional_group, employment_type to employee_history
-- Run this once against your Postgres/Supabase database to add the new columns.

ALTER TABLE IF EXISTS public.employee_history
    ADD COLUMN IF NOT EXISTS job_title text,
    ADD COLUMN IF NOT EXISTS position text,
    ADD COLUMN IF NOT EXISTS department text,
    ADD COLUMN IF NOT EXISTS functional_group text,
    ADD COLUMN IF NOT EXISTS employment_type text;

-- Optional: create index if you will frequently query by employee_id (already present in original migration)
-- CREATE INDEX IF NOT EXISTS idx_employee_history_employee_id ON public.employee_history (employee_id);

-- Note: If supabase.table('employee_history').insert(payload) previously raised errors complaining about unknown
-- columns, running this migration will allow payloads that include those keys to be stored without being stripped.
