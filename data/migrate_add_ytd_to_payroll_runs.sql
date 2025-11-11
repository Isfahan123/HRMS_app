-- Migration: Add YTD snapshot columns to payroll_runs for auditing/payslip display
-- Safely add columns if they do not exist

ALTER TABLE public.payroll_runs ADD COLUMN IF NOT EXISTS ytd_as_of_year integer;
ALTER TABLE public.payroll_runs ADD COLUMN IF NOT EXISTS ytd_as_of_month integer;

ALTER TABLE public.payroll_runs ADD COLUMN IF NOT EXISTS accumulated_gross_salary_ytd numeric(14,2) DEFAULT 0;
ALTER TABLE public.payroll_runs ADD COLUMN IF NOT EXISTS accumulated_net_salary_ytd numeric(14,2) DEFAULT 0;
ALTER TABLE public.payroll_runs ADD COLUMN IF NOT EXISTS accumulated_basic_salary_ytd numeric(14,2) DEFAULT 0;
ALTER TABLE public.payroll_runs ADD COLUMN IF NOT EXISTS accumulated_allowances_ytd numeric(14,2) DEFAULT 0;
ALTER TABLE public.payroll_runs ADD COLUMN IF NOT EXISTS accumulated_overtime_ytd numeric(14,2) DEFAULT 0;
ALTER TABLE public.payroll_runs ADD COLUMN IF NOT EXISTS accumulated_bonus_ytd numeric(14,2) DEFAULT 0;

ALTER TABLE public.payroll_runs ADD COLUMN IF NOT EXISTS accumulated_epf_employee_ytd numeric(14,2) DEFAULT 0;
ALTER TABLE public.payroll_runs ADD COLUMN IF NOT EXISTS accumulated_socso_employee_ytd numeric(14,2) DEFAULT 0;
ALTER TABLE public.payroll_runs ADD COLUMN IF NOT EXISTS accumulated_eis_employee_ytd numeric(14,2) DEFAULT 0;

ALTER TABLE public.payroll_runs ADD COLUMN IF NOT EXISTS accumulated_pcb_ytd numeric(14,2) DEFAULT 0;
ALTER TABLE public.payroll_runs ADD COLUMN IF NOT EXISTS accumulated_zakat_ytd numeric(14,2) DEFAULT 0;
ALTER TABLE public.payroll_runs ADD COLUMN IF NOT EXISTS accumulated_tax_reliefs_ytd numeric(14,2) DEFAULT 0;

COMMENT ON COLUMN public.payroll_runs.ytd_as_of_year IS 'YTD snapshot year used for PCB (previous month)';
COMMENT ON COLUMN public.payroll_runs.ytd_as_of_month IS 'YTD snapshot month used for PCB (previous month)';
COMMENT ON COLUMN public.payroll_runs.accumulated_gross_salary_ytd IS 'Gross income accumulated up to the snapshot month (exclusive)';
COMMENT ON COLUMN public.payroll_runs.accumulated_pcb_ytd IS 'PCB accumulated up to the snapshot month (exclusive)';
COMMENT ON COLUMN public.payroll_runs.accumulated_tax_reliefs_ytd IS 'Other LP1 reliefs accumulated up to the snapshot month (exclusive)';
