-- Migration: Add work_status column to employees table
-- This column tracks the current work status of an employee
-- Run this migration to fix the missing work_status column

ALTER TABLE IF EXISTS public.employees
    ADD COLUMN IF NOT EXISTS work_status text DEFAULT 'On Duty';

-- Add comment for documentation
COMMENT ON COLUMN public.employees.work_status IS 'Current work status: On Duty, On Leave, On Sick Leave, On Unpaid Leave, On Suspension, On Business Trip';

-- Update existing employees to have default status
UPDATE public.employees 
SET work_status = 'On Duty' 
WHERE work_status IS NULL;
