-- ============================================================================
-- HRMS Database Setup - Missing Tables Creation Script
-- ============================================================================
-- This script creates all the tables that are showing as missing in your logs
-- Run this in your Supabase SQL Editor
-- ============================================================================

-- 1. LHDN Tax Rates Table
-- Used by: /api/admin/lhdn/tax-rates
CREATE TABLE IF NOT EXISTS public.lhdn_tax_rates (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    bracket_number INTEGER NOT NULL,
    min_income DECIMAL(12, 2) NOT NULL,
    max_income DECIMAL(12, 2),
    tax_rate DECIMAL(5, 2) NOT NULL,
    tax_on_band DECIMAL(12, 2) DEFAULT 0,
    is_resident BOOLEAN DEFAULT true,
    effective_year INTEGER DEFAULT 2024,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(bracket_number, is_resident, effective_year)
);

-- Insert Malaysian 2024 tax brackets (Resident)
INSERT INTO public.lhdn_tax_rates (bracket_number, min_income, max_income, tax_rate, tax_on_band, is_resident, effective_year) VALUES
(1, 0, 5000, 0, 0, true, 2024),
(2, 5001, 20000, 1, 150, true, 2024),
(3, 20001, 35000, 3, 450, true, 2024),
(4, 35001, 50000, 8, 1200, true, 2024),
(5, 50001, 70000, 13, 2600, true, 2024),
(6, 70001, 100000, 21, 6300, true, 2024),
(7, 100001, 250000, 24, 36000, true, 2024),
(8, 250001, 400000, 24.5, 36750, true, 2024),
(9, 400001, 600000, 25, 50000, true, 2024),
(10, 600001, 1000000, 26, 104000, true, 2024),
(11, 1000001, 2000000, 28, 280000, true, 2024),
(12, 2000001, NULL, 30, NULL, true, 2024)
ON CONFLICT (bracket_number, is_resident, effective_year) DO NOTHING;

-- Insert Non-Resident tax (flat 30%)
INSERT INTO public.lhdn_tax_rates (bracket_number, min_income, max_income, tax_rate, tax_on_band, is_resident, effective_year) VALUES
(1, 0, NULL, 30, NULL, false, 2024)
ON CONFLICT (bracket_number, is_resident, effective_year) DO NOTHING;

-- ============================================================================

-- 2. LHDN Relief Maximums Table
-- Used by: /api/admin/lhdn/relief-max
CREATE TABLE IF NOT EXISTS public.lhdn_relief_max (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    relief_category VARCHAR(100) UNIQUE NOT NULL,
    max_amount DECIMAL(10, 2) NOT NULL,
    description TEXT,
    effective_year INTEGER DEFAULT 2024,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert Malaysian 2024 relief maximums
INSERT INTO public.lhdn_relief_max (relief_category, max_amount, description, effective_year) VALUES
('Self Relief', 9000, 'Individual relief for taxpayer', 2024),
('Spouse Relief', 4000, 'Relief for spouse without income', 2024),
('Child Relief (Under 18)', 2000, 'Per child under 18 years', 2024),
('Child Relief (18+ Education)', 8000, 'Per child 18+ in higher education', 2024),
('Disabled Child', 6000, 'Per disabled child', 2024),
('Life Insurance & EPF', 7000, 'Combined life insurance and EPF', 2024),
('Education & Medical Insurance', 3000, 'Education and medical insurance premium', 2024),
('Medical for Parents', 8000, 'Medical expenses for parents', 2024),
('Medical (Serious Disease)', 8000, 'Medical for self/spouse/child serious diseases', 2024),
('Basic Supporting Equipment', 6000, 'For disabled individual', 2024),
('Lifestyle', 2500, 'Books, gym, internet subscription', 2024),
('Domestic Tourism', 1000, 'Domestic tourism expenses', 2024),
('Sports Equipment', 500, 'Purchase of sports equipment', 2024),
('EIS & SOCSO', 250, 'Employment Insurance and SOCSO', 2024)
ON CONFLICT (relief_category) DO UPDATE SET
    max_amount = EXCLUDED.max_amount,
    description = EXCLUDED.description,
    effective_year = EXCLUDED.effective_year;

-- ============================================================================

-- 3. LHDN Relief Overrides Table
-- Used by: /api/admin/lhdn/relief-overrides
CREATE TABLE IF NOT EXISTS public.lhdn_relief_overrides (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    employee_id UUID REFERENCES public.employees(id) ON DELETE CASCADE,
    employee_name VARCHAR(255),
    employee_email VARCHAR(255),
    relief_category VARCHAR(100) NOT NULL,
    override_amount DECIMAL(10, 2) NOT NULL,
    effective_from DATE,
    effective_to DATE,
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_relief_overrides_employee ON public.lhdn_relief_overrides(employee_id);
CREATE INDEX IF NOT EXISTS idx_relief_overrides_category ON public.lhdn_relief_overrides(relief_category);

-- ============================================================================

-- 4. Leave Entitlements Table
-- Used by: /api/admin/leave-entitlements
CREATE TABLE IF NOT EXISTS public.leave_entitlements (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    position_level VARCHAR(100) NOT NULL,
    annual_leave_days INTEGER DEFAULT 14,
    sick_leave_days INTEGER DEFAULT 14,
    carry_forward_max INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default entitlements by position
INSERT INTO public.leave_entitlements (position_level, annual_leave_days, sick_leave_days, carry_forward_max) VALUES
('Junior Staff', 14, 14, 5),
('Senior Staff', 18, 14, 7),
('Manager', 21, 14, 10),
('Senior Manager', 24, 14, 12),
('Director', 28, 14, 15),
('Executive', 30, 14, 20)
ON CONFLICT DO NOTHING;

-- ============================================================================

-- 5. Public Holidays Table
-- Used by: /api/holidays
CREATE TABLE IF NOT EXISTS public.public_holidays (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    state VARCHAR(100),
    is_federal BOOLEAN DEFAULT true,
    year INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(name, date, state)
);

CREATE INDEX IF NOT EXISTS idx_holidays_date ON public.public_holidays(date);
CREATE INDEX IF NOT EXISTS idx_holidays_year ON public.public_holidays(year);
CREATE INDEX IF NOT EXISTS idx_holidays_state ON public.public_holidays(state);

-- Insert common Malaysian federal holidays for 2024
INSERT INTO public.public_holidays (name, date, state, is_federal, year) VALUES
('New Year''s Day', '2024-01-01', NULL, true, 2024),
('Federal Territory Day', '2024-02-01', 'Federal Territory', false, 2024),
('Chinese New Year', '2024-02-10', NULL, true, 2024),
('Chinese New Year', '2024-02-11', NULL, true, 2024),
('Hari Raya Aidilfitri', '2024-04-10', NULL, true, 2024),
('Hari Raya Aidilfitri', '2024-04-11', NULL, true, 2024),
('Labour Day', '2024-05-01', NULL, true, 2024),
('Wesak Day', '2024-05-22', NULL, true, 2024),
('Agong''s Birthday', '2024-06-03', NULL, true, 2024),
('Hari Raya Aidiladha', '2024-06-17', NULL, true, 2024),
('Awal Muharram', '2024-07-07', NULL, true, 2024),
('National Day', '2024-08-31', NULL, true, 2024),
('Malaysia Day', '2024-09-16', NULL, true, 2024),
('Prophet Muhammad''s Birthday', '2024-09-16', NULL, true, 2024),
('Deepavali', '2024-11-01', NULL, true, 2024),
('Christmas Day', '2024-12-25', NULL, true, 2024)
ON CONFLICT (name, date, state) DO NOTHING;

-- Insert 2025 holidays
INSERT INTO public.public_holidays (name, date, state, is_federal, year) VALUES
('New Year''s Day', '2025-01-01', NULL, true, 2025),
('Federal Territory Day', '2025-02-01', 'Federal Territory', false, 2025),
('Chinese New Year', '2025-01-29', NULL, true, 2025),
('Chinese New Year', '2025-01-30', NULL, true, 2025),
('Hari Raya Aidilfitri', '2025-03-31', NULL, true, 2025),
('Hari Raya Aidilfitri', '2025-04-01', NULL, true, 2025),
('Labour Day', '2025-05-01', NULL, true, 2025),
('Wesak Day', '2025-05-12', NULL, true, 2025),
('Agong''s Birthday', '2025-06-02', NULL, true, 2025),
('Hari Raya Aidiladha', '2025-06-07', NULL, true, 2025),
('Awal Muharram', '2025-06-26', NULL, true, 2025),
('National Day', '2025-08-31', NULL, true, 2025),
('Malaysia Day', '2025-09-16', NULL, true, 2025),
('Prophet Muhammad''s Birthday', '2025-09-05', NULL, true, 2025),
('Deepavali', '2025-10-20', NULL, true, 2025),
('Christmas Day', '2025-12-25', NULL, true, 2025)
ON CONFLICT (name, date, state) DO NOTHING;

-- ============================================================================

-- 6. Fix Foreign Key Relationship for Leave Requests
-- The error mentioned: "Could not find a relationship between 'leave_requests' and 'employees'"
-- This adds the proper foreign key constraint if it doesn't exist

-- First, check if leave_requests table exists and has employee_id column
DO $$ 
BEGIN
    -- Add employee_id column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'leave_requests' 
        AND column_name = 'employee_id'
    ) THEN
        ALTER TABLE public.leave_requests ADD COLUMN employee_id UUID;
    END IF;

    -- Add foreign key constraint if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_schema = 'public' 
        AND table_name = 'leave_requests' 
        AND constraint_name = 'fk_leave_requests_employee'
    ) THEN
        ALTER TABLE public.leave_requests 
        ADD CONSTRAINT fk_leave_requests_employee 
        FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_leave_requests_employee ON public.leave_requests(employee_id);

-- ============================================================================

-- 7. Variable Percentage Rules Table (if not exists)
-- Used by: /api/admin/variable-percentage
CREATE TABLE IF NOT EXISTS public.variable_percentage_rules (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    percentage DECIMAL(5, 2) NOT NULL,
    apply_to VARCHAR(100) NOT NULL,
    base_on VARCHAR(100) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    employee_email VARCHAR(255),
    effective_from DATE,
    effective_to DATE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_var_pct_rules_status ON public.variable_percentage_rules(status);
CREATE INDEX IF NOT EXISTS idx_var_pct_rules_employee ON public.variable_percentage_rules(employee_email);

-- ============================================================================

-- 8. Employee History Table (if not exists)
-- Used by: /api/admin/employee-history
CREATE TABLE IF NOT EXISTS public.employee_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    employee_id UUID REFERENCES public.employees(id) ON DELETE CASCADE,
    employee_email VARCHAR(255),
    field_changed VARCHAR(100) NOT NULL,
    previous_value TEXT,
    new_value TEXT,
    change_date DATE NOT NULL,
    reason TEXT,
    changed_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_employee_history_employee ON public.employee_history(employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_history_date ON public.employee_history(change_date);

-- ============================================================================

-- Verify all tables were created successfully
DO $$
DECLARE
    table_list text[] := ARRAY[
        'lhdn_tax_rates',
        'lhdn_relief_max',
        'lhdn_relief_overrides',
        'leave_entitlements',
        'public_holidays',
        'variable_percentage_rules',
        'employee_history'
    ];
    tbl text;
    missing_tables text := '';
BEGIN
    FOREACH tbl IN ARRAY table_list
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = tbl
        ) THEN
            missing_tables := missing_tables || tbl || ', ';
        END IF;
    END LOOP;
    
    IF missing_tables != '' THEN
        RAISE NOTICE 'WARNING: The following tables were not created: %', missing_tables;
    ELSE
        RAISE NOTICE 'SUCCESS: All required tables have been created!';
    END IF;
END $$;

-- ============================================================================
-- END OF SCRIPT
-- ============================================================================
