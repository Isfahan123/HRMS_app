-- Creates the YTD relief accumulation table to track per-item claims across the year for cycle enforcement.

CREATE TABLE IF NOT EXISTS public.relief_ytd_accumulated (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  employee_id UUID NOT NULL,
  year INT NOT NULL,
  item_key TEXT NOT NULL,
  claimed_ytd DECIMAL(12,2) DEFAULT 0.00,
  last_claim_year INT,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (employee_id, year, item_key)
);

CREATE OR REPLACE FUNCTION public.update_relief_ytd_accumulated_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_relief_ytd_accumulated ON public.relief_ytd_accumulated;
CREATE TRIGGER trg_update_relief_ytd_accumulated
BEFORE UPDATE ON public.relief_ytd_accumulated
FOR EACH ROW
EXECUTE FUNCTION public.update_relief_ytd_accumulated_updated_at();

-- Optional: enable RLS and add policies according to your security model
-- ALTER TABLE public.relief_ytd_accumulated ENABLE ROW LEVEL SECURITY;