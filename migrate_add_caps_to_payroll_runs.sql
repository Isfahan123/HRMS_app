-- Migration: Add cap snapshot columns to payroll_runs for auditing/reporting

-- EPF mandatory relief (B17) cap tracking
ALTER TABLE public.payroll_runs ADD COLUMN IF NOT EXISTS epf_relief_cap_annual DECIMAL(10,2) DEFAULT 4000.00;
ALTER TABLE public.payroll_runs ADD COLUMN IF NOT EXISTS epf_relief_used_ytd DECIMAL(12,2) DEFAULT 0.00;
ALTER TABLE public.payroll_runs ADD COLUMN IF NOT EXISTS epf_relief_remaining DECIMAL(12,2) DEFAULT 0.00;

-- SOCSO+EIS LP1 (B20) cap tracking (PCB-only)
ALTER TABLE public.payroll_runs ADD COLUMN IF NOT EXISTS socso_eis_lp1_cap_annual DECIMAL(10,2) DEFAULT 350.00;
ALTER TABLE public.payroll_runs ADD COLUMN IF NOT EXISTS socso_eis_lp1_claimed_ytd DECIMAL(12,2) DEFAULT 0.00;
ALTER TABLE public.payroll_runs ADD COLUMN IF NOT EXISTS socso_eis_lp1_remaining DECIMAL(12,2) DEFAULT 0.00;

COMMENT ON COLUMN public.payroll_runs.epf_relief_cap_annual IS 'Annual cap for mandatory EPF relief (B17), typically RM4,000';
COMMENT ON COLUMN public.payroll_runs.epf_relief_used_ytd IS 'EPF relief counted up to previous month (min(accumulated_epf_ytd, cap))';
COMMENT ON COLUMN public.payroll_runs.epf_relief_remaining IS 'Remaining EPF relief at time of this run (cap - used_ytd; not including current month K2 shaping)';

COMMENT ON COLUMN public.payroll_runs.socso_eis_lp1_cap_annual IS 'Annual cap for B20 (SOCSO+EIS employee), typically RM350 for PCB-only';
COMMENT ON COLUMN public.payroll_runs.socso_eis_lp1_claimed_ytd IS 'B20 (SOCSO+EIS) claimed up to previous month (elapsed months only)';
COMMENT ON COLUMN public.payroll_runs.socso_eis_lp1_remaining IS 'Remaining B20 cap at time of this run (cap - claimed_ytd)';
