-- Migration: Add effective_date column to employee_history table
-- This column is used for salary change tracking in employee_history records
-- Run this migration to fix the error: "column employee_history.effective_date does not exist"

ALTER TABLE IF EXISTS public.employee_history
    ADD COLUMN IF NOT EXISTS effective_date date;

-- Add index for better query performance when ordering by effective_date
CREATE INDEX IF NOT EXISTS idx_employee_history_effective_date ON public.employee_history (effective_date);

-- Optional: Create index for composite queries
CREATE INDEX IF NOT EXISTS idx_employee_history_email_effective ON public.employee_history (employee_email, effective_date DESC);

-- Add additional columns that are used by salary history tracking
ALTER TABLE IF EXISTS public.employee_history
    ADD COLUMN IF NOT EXISTS change_type varchar(100),
    ADD COLUMN IF NOT EXISTS change_amount decimal(12, 2),
    ADD COLUMN IF NOT EXISTS change_percentage decimal(5, 2),
    ADD COLUMN IF NOT EXISTS created_by varchar(255),
    ADD COLUMN IF NOT EXISTS employee_name varchar(255);

-- Add comments for documentation
COMMENT ON COLUMN public.employee_history.effective_date IS 'Date when the change becomes effective (used for salary changes)';
COMMENT ON COLUMN public.employee_history.change_type IS 'Type of change: salary_adjustment, promotion, increment, etc.';
COMMENT ON COLUMN public.employee_history.change_amount IS 'Amount of change (e.g., salary increase/decrease)';
COMMENT ON COLUMN public.employee_history.change_percentage IS 'Percentage of change';
