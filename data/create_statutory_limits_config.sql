-- Create a small, focused table for statutory ceilings (EPF/SOCSO/EIS)
CREATE TABLE IF NOT EXISTS public.statutory_limits_config (
    id serial PRIMARY KEY,
    config_name varchar(100) NOT NULL UNIQUE,
    epf_ceiling numeric(10, 2) NOT NULL DEFAULT 6000.00,
    socso_ceiling numeric(10, 2) NOT NULL DEFAULT 6000.00,
    eis_ceiling numeric(10, 2) NOT NULL DEFAULT 6000.00,
    is_active boolean DEFAULT true,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_statutory_limits_config_name ON public.statutory_limits_config (config_name);
CREATE INDEX IF NOT EXISTS idx_statutory_limits_active ON public.statutory_limits_config (is_active);

-- Trigger to keep updated_at fresh (assumes a function update_updated_at_column() exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'update_statutory_limits_config_updated_at'
    ) THEN
        CREATE TRIGGER update_statutory_limits_config_updated_at
        BEFORE UPDATE ON public.statutory_limits_config
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END$$;

-- Seed default row (idempotent)
INSERT INTO public.statutory_limits_config (config_name)
VALUES ('default')
ON CONFLICT (config_name) DO NOTHING;
