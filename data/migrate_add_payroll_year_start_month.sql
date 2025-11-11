-- Add payroll_year_start_month to payroll_settings for arbitrary payroll-year windows
ALTER TABLE IF EXISTS public.payroll_settings
ADD COLUMN IF NOT EXISTS payroll_year_start_month integer NOT NULL DEFAULT 1;

-- Constrain to 1..12
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'chk_payroll_settings_year_start_month'
  ) THEN
    ALTER TABLE public.payroll_settings
    ADD CONSTRAINT chk_payroll_settings_year_start_month CHECK (payroll_year_start_month >= 1 AND payroll_year_start_month <= 12);
  END IF;
END $$;