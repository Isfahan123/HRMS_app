-- Table to store Potongan Bulan Semasa (monthly deductions) per employee, per month
CREATE TABLE IF NOT EXISTS public.payroll_monthly_deductions (
    id uuid PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    employee_id uuid NOT NULL REFERENCES public.employees(id) ON DELETE CASCADE,
    year int NOT NULL,
    month int NOT NULL CHECK (month BETWEEN 1 AND 12),

    -- Monthly rebate/deductions (keep focused; extend as needed)
    zakat_monthly numeric(12,2) NOT NULL DEFAULT 0.00,
    religious_travel_monthly numeric(12,2) NOT NULL DEFAULT 0.00,

    -- Optional: store extra deduction types captured in dialog
    other_deductions_amount numeric(12,2) NOT NULL DEFAULT 0.00,

    -- Audit
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(employee_id, year, month)
);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_updated_at_payroll_monthly_deductions ON public.payroll_monthly_deductions;
CREATE TRIGGER set_updated_at_payroll_monthly_deductions
BEFORE UPDATE ON public.payroll_monthly_deductions
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Indexes
CREATE INDEX IF NOT EXISTS idx_pmd_employee ON public.payroll_monthly_deductions(employee_id);
CREATE INDEX IF NOT EXISTS idx_pmd_year_month ON public.payroll_monthly_deductions(year, month);
