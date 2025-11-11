-- Migration: add rebate_threshold to tax_rates_config (optional)
-- Safe to run multiple times; will only add the column if missing.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'tax_rates_config' AND column_name = 'rebate_threshold'
    ) THEN
        ALTER TABLE public.tax_rates_config
        ADD COLUMN rebate_threshold DECIMAL(12,2) DEFAULT 35000.00;
    END IF;
END $$;

-- Note: Existing rows will have the default 35000.00 value; adjust as needed.
