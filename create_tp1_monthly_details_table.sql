-- Creates the TP1 monthly details table to store per-employee monthly TP1 relief inputs and snapshots.

CREATE TABLE IF NOT EXISTS public.tp1_monthly_details (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  employee_id UUID NOT NULL,
  year INT NOT NULL,
  month INT NOT NULL,
  -- Snapshot JSON of the full TP1 inputs for the month (UI values)
  details JSONB DEFAULT '{}'::jsonb,
  -- Base LP1 (cash) component persisted for traceability (excludes pcb-only)
  other_reliefs_monthly DECIMAL(12,2) DEFAULT 0.00,
  -- SOCSO+EIS LP1 (pcb-only) component for this month (not included in cash deductions)
  socso_eis_lp1_monthly DECIMAL(12,2) DEFAULT 0.00,
  -- Zakat for the month (if captured in this flow)
  zakat_monthly DECIMAL(12,2) DEFAULT 0.00,
  -- Optional: final LP1 used for PCB (including pcb-only) for audit/debug
  lp1_total_for_pcb DECIMAL(12,2),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (employee_id, year, month)
);

CREATE OR REPLACE FUNCTION public.update_tp1_monthly_details_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_tp1_monthly_details ON public.tp1_monthly_details;
CREATE TRIGGER trg_update_tp1_monthly_details
BEFORE UPDATE ON public.tp1_monthly_details
FOR EACH ROW EXECUTE FUNCTION public.update_tp1_monthly_details_updated_at();

-- Optional: enable RLS and add policies according to your security model
-- ALTER TABLE public.tp1_monthly_details ENABLE ROW LEVEL SECURITY;