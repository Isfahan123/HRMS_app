-- Create a singleton table to store payroll calculation settings
-- Stores the global calculation method (fixed vs variable) and the active variable config name

CREATE TABLE IF NOT EXISTS public.payroll_settings (
    id BIGINT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    calculation_method TEXT NOT NULL DEFAULT 'fixed', -- 'fixed' or 'variable'
    active_variable_config TEXT NOT NULL DEFAULT 'default',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Ensure updated_at auto-updates on change
CREATE OR REPLACE FUNCTION public.update_payroll_settings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_payroll_settings_updated_at ON public.payroll_settings;
CREATE TRIGGER trigger_update_payroll_settings_updated_at
    BEFORE UPDATE ON public.payroll_settings
    FOR EACH ROW
    EXECUTE FUNCTION public.update_payroll_settings_updated_at();

-- Seed default row if table is empty
INSERT INTO public.payroll_settings (id, calculation_method, active_variable_config)
VALUES (1, 'fixed', 'default')
ON CONFLICT (id) DO NOTHING;
