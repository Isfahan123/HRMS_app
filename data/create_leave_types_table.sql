-- Migration: create leave_types table
-- Safe creation (will not error if extension already exists)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Table definition
CREATE TABLE IF NOT EXISTS public.leave_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    requires_document BOOLEAN NOT NULL DEFAULT FALSE,
    deduct_from TEXT NOT NULL DEFAULT 'annual' CHECK (deduct_from IN ('annual','sick','unpaid','none')),
    default_duration NUMERIC(5,2), -- suggested typical duration in days (optional)
    max_duration NUMERIC(5,2),     -- hard upper cap (optional)
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order INT NOT NULL DEFAULT 100,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Helpful composite index for active ordering
CREATE INDEX IF NOT EXISTS idx_leave_types_active_order ON public.leave_types(is_active, sort_order);

-- Trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION public.leave_types_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_leave_types_updated_at
BEFORE UPDATE ON public.leave_types
FOR EACH ROW
EXECUTE FUNCTION public.leave_types_set_updated_at();

-- Seed a few defaults if table empty (id generated automatically)
INSERT INTO public.leave_types (code, name, description, deduct_from, requires_document, sort_order)
SELECT s.code, s.name, s.description, s.deduct_from, s.requires_document, s.sort_order
FROM (
    VALUES
        ('annual','Annual Leave','Paid annual leave','annual',FALSE,10),
        ('sick','Sick Leave','Outpatient sick leave','sick',TRUE,20),
        ('hospitalization','Hospitalization','Inpatient hospital stay (counts toward sick entitlement)','sick',TRUE,30),
        ('emergency','Emergency Leave','Unexpected urgent matters','annual',FALSE,40),
        ('unpaid','Unpaid Leave','Leave without pay','unpaid',FALSE,50),
        ('others','Others','Miscellaneous leave type','annual',FALSE,90)
) AS s(code,name,description,deduct_from,requires_document,sort_order)
LEFT JOIN public.leave_types lt ON lt.code = s.code
WHERE lt.code IS NULL;