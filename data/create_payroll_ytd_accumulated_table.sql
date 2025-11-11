-- Create table for Year-to-Date (YTD) accumulated payroll data
-- This replaces manual entry of accumulated data in payroll_dialog.py

-- Create YTD accumulated data table
CREATE TABLE public.payroll_ytd_accumulated (
    -- Primary identifiers
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    employee_email TEXT NOT NULL,
    year INTEGER NOT NULL, -- Year for YTD calculations (e.g., 2025)
    month INTEGER NOT NULL, -- Current month (1-12)
    
    -- Accumulated salary data (Year-to-Date until previous month)
    accumulated_gross_salary_ytd NUMERIC(12, 2) NOT NULL DEFAULT 0.00, -- ∑(Y-K): Total gross salary YTD
    accumulated_net_salary_ytd NUMERIC(12, 2) NOT NULL DEFAULT 0.00, -- Net salary after deductions YTD
    accumulated_basic_salary_ytd NUMERIC(12, 2) NOT NULL DEFAULT 0.00, -- Basic salary component YTD
    accumulated_allowances_ytd NUMERIC(12, 2) NOT NULL DEFAULT 0.00, -- Total allowances YTD
    accumulated_overtime_ytd NUMERIC(12, 2) NOT NULL DEFAULT 0.00, -- Overtime payments YTD
    accumulated_bonus_ytd NUMERIC(12, 2) NOT NULL DEFAULT 0.00, -- Bonus payments YTD
    
    -- Accumulated statutory contributions (Year-to-Date)
    accumulated_epf_employee_ytd NUMERIC(10, 2) NOT NULL DEFAULT 0.00, -- K: Employee EPF contributions YTD
    accumulated_epf_employer_ytd NUMERIC(10, 2) NOT NULL DEFAULT 0.00, -- Employer EPF contributions YTD
    accumulated_socso_employee_ytd NUMERIC(10, 2) NOT NULL DEFAULT 0.00, -- Employee SOCSO contributions YTD
    accumulated_socso_employer_ytd NUMERIC(10, 2) NOT NULL DEFAULT 0.00, -- Employer SOCSO contributions YTD
    accumulated_eis_employee_ytd NUMERIC(10, 2) NOT NULL DEFAULT 0.00, -- Employee EIS contributions YTD
    accumulated_eis_employer_ytd NUMERIC(10, 2) NOT NULL DEFAULT 0.00, -- Employer EIS contributions YTD
    
    -- Accumulated tax data (Year-to-Date)
    accumulated_pcb_ytd NUMERIC(10, 2) NOT NULL DEFAULT 0.00, -- X: PCB tax deducted YTD
    accumulated_zakat_ytd NUMERIC(10, 2) NOT NULL DEFAULT 0.00, -- Z: Zakat/Fitrah/Levy YTD
    
    -- Accumulated reliefs and deductions (Year-to-Date)
    accumulated_tax_reliefs_ytd NUMERIC(10, 2) NOT NULL DEFAULT 0.00, -- ∑LP: Total approved tax reliefs YTD
    accumulated_other_deductions_ytd NUMERIC(10, 2) NOT NULL DEFAULT 0.00, -- Other deductions YTD
    accumulated_unpaid_leave_deduction_ytd NUMERIC(10, 2) NOT NULL DEFAULT 0.00, -- Unpaid leave deductions YTD
    
    -- Current month calculation context (for PCB calculation)
    current_month_gross_salary NUMERIC(10, 2) NULL, -- Current month gross salary
    current_month_epf_employee NUMERIC(10, 2) NULL, -- Current month EPF employee
    current_month_pcb_calculated NUMERIC(10, 2) NULL, -- Current month PCB calculated
    current_month_zakat NUMERIC(10, 2) NULL, -- Current month Zakat/Fitrah/Levy
    current_month_tax_reliefs NUMERIC(10, 2) NULL, -- LP1: Current month tax reliefs
    
    -- Tax relief context (annual maximums and eligibility)
    individual_relief NUMERIC(8, 2) NOT NULL DEFAULT 9000.00, -- D: Individual relief
    spouse_relief NUMERIC(8, 2) NOT NULL DEFAULT 0.00, -- S: Spouse relief
    child_relief_per_child NUMERIC(8, 2) NOT NULL DEFAULT 2000.00, -- Q: Child relief per child
    child_count INTEGER NOT NULL DEFAULT 0, -- C: Number of eligible children
    disabled_individual_relief NUMERIC(8, 2) NOT NULL DEFAULT 0.00, -- Du: Disabled individual relief
    disabled_spouse_relief NUMERIC(8, 2) NOT NULL DEFAULT 0.00, -- Su: Disabled spouse relief
    
    -- Employee tax context
    is_resident BOOLEAN NOT NULL DEFAULT true, -- Tax resident status
    is_individual_disabled BOOLEAN NOT NULL DEFAULT false, -- OKU status
    is_spouse_disabled BOOLEAN NOT NULL DEFAULT false, -- Spouse OKU status
    
    -- Record metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by TEXT NULL, -- Who created this record
    updated_by TEXT NULL, -- Who last updated this record
    
    -- Constraints
    CONSTRAINT payroll_ytd_accumulated_unique_employee_year_month 
        UNIQUE (employee_email, year, month),
    CONSTRAINT payroll_ytd_accumulated_valid_month 
        CHECK (month >= 1 AND month <= 12),
    CONSTRAINT payroll_ytd_accumulated_valid_year 
        CHECK (year >= 2020 AND year <= 2050),
    CONSTRAINT payroll_ytd_accumulated_positive_amounts 
        CHECK (
            accumulated_gross_salary_ytd >= 0 AND
            accumulated_epf_employee_ytd >= 0 AND
            accumulated_pcb_ytd >= 0 AND
            child_count >= 0
        )
) TABLESPACE pg_default;

-- Create indexes for efficient querying
CREATE INDEX idx_payroll_ytd_accumulated_employee_year 
    ON public.payroll_ytd_accumulated (employee_email, year);

CREATE INDEX idx_payroll_ytd_accumulated_year_month 
    ON public.payroll_ytd_accumulated (year, month);

CREATE INDEX idx_payroll_ytd_accumulated_created_at 
    ON public.payroll_ytd_accumulated (created_at);

-- Create trigger for updated_at timestamp
CREATE OR REPLACE FUNCTION update_payroll_ytd_accumulated_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_payroll_ytd_accumulated_updated_at
    BEFORE UPDATE ON public.payroll_ytd_accumulated
    FOR EACH ROW
    EXECUTE FUNCTION update_payroll_ytd_accumulated_updated_at();

-- Insert some sample data for testing (employee with accumulated data up to August 2025)
INSERT INTO public.payroll_ytd_accumulated (
    employee_email,
    year,
    month,
    accumulated_gross_salary_ytd,
    accumulated_net_salary_ytd,
    accumulated_epf_employee_ytd,
    accumulated_epf_employer_ytd,
    accumulated_socso_employee_ytd,
    accumulated_socso_employer_ytd,
    accumulated_eis_employee_ytd,
    accumulated_eis_employer_ytd,
    accumulated_pcb_ytd,
    accumulated_zakat_ytd,
    accumulated_tax_reliefs_ytd,
    individual_relief,
    spouse_relief,
    child_relief_per_child,
    child_count,
    is_resident,
    created_by
) VALUES 
-- August 2025 data for test employee
('aimanisfahan123@gmail.com', 2025, 8, 
 40000.00, -- 8 months * RM5000 gross
 32000.00, -- Net after deductions
 2200.00, -- 8 months * RM275 EPF employee (11% of RM2500 ceiling)
 2400.00, -- 8 months * RM300 EPF employer (12% of RM2500 ceiling) 
 200.00, -- 8 months * RM25 SOCSO employee
 700.00, -- 8 months * RM87.50 SOCSO employer
 80.00, -- 8 months * RM10 EIS employee
 80.00, -- 8 months * RM10 EIS employer
 2400.00, -- 8 months * RM300 PCB
 0.00, -- No zakat
 8000.00, -- Some tax reliefs claimed
 9000.00, -- Individual relief
 4000.00, -- Spouse relief
 2000.00, -- Child relief per child
 2, -- 2 children
 true, -- Malaysian resident
 'system'),

-- September 2025 data for test employee 
('aimanisfahan123@gmail.com', 2025, 9,
 45000.00, -- 9 months * RM5000 gross
 36000.00, -- Net after deductions
 2475.00, -- 9 months * RM275 EPF employee
 2700.00, -- 9 months * RM300 EPF employer
 225.00, -- 9 months * RM25 SOCSO employee
 787.50, -- 9 months * RM87.50 SOCSO employer
 90.00, -- 9 months * RM10 EIS employee
 90.00, -- 9 months * RM10 EIS employer
 2700.00, -- 9 months * RM300 PCB
 0.00, -- No zakat
 10000.00, -- Tax reliefs claimed
 9000.00, -- Individual relief
 4000.00, -- Spouse relief
 2000.00, -- Child relief per child
 2, -- 2 children
 true, -- Malaysian resident
 'system');

-- Enable Row Level Security (optional)
-- ALTER TABLE public.payroll_ytd_accumulated ENABLE ROW LEVEL SECURITY;

-- Create RLS policy for employee access (optional)
-- CREATE POLICY "Users can view their own YTD data" ON public.payroll_ytd_accumulated
--     FOR SELECT USING (auth.jwt() ->> 'email' = employee_email);

-- Create RLS policy for admin access (optional)  
-- CREATE POLICY "Admins can view all YTD data" ON public.payroll_ytd_accumulated
--     FOR ALL USING (auth.jwt() ->> 'role' = 'admin');

COMMENT ON TABLE public.payroll_ytd_accumulated IS 'Year-to-Date accumulated payroll data for automated PCB calculation and payroll processing';
COMMENT ON COLUMN public.payroll_ytd_accumulated.accumulated_gross_salary_ytd IS '∑(Y-K): Total gross salary accumulated from January to previous month';
COMMENT ON COLUMN public.payroll_ytd_accumulated.accumulated_epf_employee_ytd IS 'K: Employee EPF contributions accumulated (max RM4,000/year for tax relief)';
COMMENT ON COLUMN public.payroll_ytd_accumulated.accumulated_pcb_ytd IS 'X: PCB tax already deducted in previous months';
COMMENT ON COLUMN public.payroll_ytd_accumulated.accumulated_zakat_ytd IS 'Z: Zakat/Fitrah/Levy already paid in previous months';
COMMENT ON COLUMN public.payroll_ytd_accumulated.accumulated_tax_reliefs_ytd IS '∑LP: Total tax reliefs claimed in previous months';
