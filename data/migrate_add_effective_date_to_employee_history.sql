-- Migration: Add missing columns to employee_history table
-- This migration adds columns for both salary change tracking and employment history tracking
-- Run this migration to fix errors: 
--   - "column employee_history.effective_date does not exist"
--   - "column employee_history.start_date does not exist"

-- Add columns for employment history tracking (previous jobs, companies, positions)
ALTER TABLE IF EXISTS public.employee_history
    ADD COLUMN IF NOT EXISTS company text,
    ADD COLUMN IF NOT EXISTS job_title text,
    ADD COLUMN IF NOT EXISTS position text,
    ADD COLUMN IF NOT EXISTS department text,
    ADD COLUMN IF NOT EXISTS functional_group text,
    ADD COLUMN IF NOT EXISTS employment_type text,
    ADD COLUMN IF NOT EXISTS start_date date,
    ADD COLUMN IF NOT EXISTS end_date date,
    ADD COLUMN IF NOT EXISTS notes text,
    ADD COLUMN IF NOT EXISTS attachments jsonb,
    ADD COLUMN IF NOT EXISTS city_place_id text,
    ADD COLUMN IF NOT EXISTS admin_notes text,
    ADD COLUMN IF NOT EXISTS updated_at timestamptz;

-- Add columns for salary change tracking
ALTER TABLE IF EXISTS public.employee_history
    ADD COLUMN IF NOT EXISTS effective_date date,
    ADD COLUMN IF NOT EXISTS change_type varchar(100),
    ADD COLUMN IF NOT EXISTS change_amount decimal(12, 2),
    ADD COLUMN IF NOT EXISTS change_percentage decimal(5, 2),
    ADD COLUMN IF NOT EXISTS created_by varchar(255),
    ADD COLUMN IF NOT EXISTS employee_name varchar(255);

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_employee_history_start_date ON public.employee_history (start_date);
CREATE INDEX IF NOT EXISTS idx_employee_history_effective_date ON public.employee_history (effective_date);
CREATE INDEX IF NOT EXISTS idx_employee_history_email_effective ON public.employee_history (employee_email, effective_date DESC);

-- Add comments for documentation
COMMENT ON COLUMN public.employee_history.start_date IS 'Start date of employment period (used for employment history)';
COMMENT ON COLUMN public.employee_history.end_date IS 'End date of employment period (used for employment history)';
COMMENT ON COLUMN public.employee_history.effective_date IS 'Date when the change becomes effective (used for salary changes)';
COMMENT ON COLUMN public.employee_history.change_type IS 'Type of change: salary_adjustment, promotion, increment, etc.';
COMMENT ON COLUMN public.employee_history.change_amount IS 'Amount of change (e.g., salary increase/decrease)';
COMMENT ON COLUMN public.employee_history.change_percentage IS 'Percentage of change';
