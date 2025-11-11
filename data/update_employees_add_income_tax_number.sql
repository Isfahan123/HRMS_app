-- Add income_tax_number to employees if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name   = 'employees'
          AND column_name  = 'income_tax_number'
    ) THEN
        ALTER TABLE public.employees
        ADD COLUMN income_tax_number text NULL;
    END IF;
END $$;

-- Optional: index (non-unique) for lookups
CREATE INDEX IF NOT EXISTS idx_employees_income_tax_number
    ON public.employees USING btree (income_tax_number);
