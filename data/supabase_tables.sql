-- =============================================================================
-- SUPABASE TABLE CREATION SCRIPT FOR HRMS TAX AND PAYROLL SYSTEM
-- =============================================================================

-- 1. Tax Rates Configuration Table
CREATE TABLE IF NOT EXISTS tax_rates_config (
    id SERIAL PRIMARY KEY,
    config_name VARCHAR(100) NOT NULL UNIQUE,
    progressive_rates JSONB NOT NULL DEFAULT '{}',
    non_resident_rate DECIMAL(5,2) NOT NULL DEFAULT 30.00,
    individual_tax_rebate DECIMAL(10,2) NOT NULL DEFAULT 400.00,
    epf_employee_rate DECIMAL(5,2) NOT NULL DEFAULT 11.00,
    epf_employer_rate DECIMAL(5,2) NOT NULL DEFAULT 12.00,
    socso_employee_rate DECIMAL(5,2) NOT NULL DEFAULT 0.50,
    socso_employer_rate DECIMAL(5,2) NOT NULL DEFAULT 1.75,
    eis_employee_rate DECIMAL(5,2) NOT NULL DEFAULT 0.20,
    eis_employer_rate DECIMAL(5,2) NOT NULL DEFAULT 0.20,
    epf_ceiling DECIMAL(10,2) NOT NULL DEFAULT 6000.00,
    socso_ceiling DECIMAL(10,2) NOT NULL DEFAULT 6000.00,
    eis_ceiling DECIMAL(10,2) NOT NULL DEFAULT 6000.00,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_tax_rates_config_name ON tax_rates_config(config_name);
CREATE INDEX IF NOT EXISTS idx_tax_rates_active ON tax_rates_config(is_active);

-- 2. Tax Relief Maximum Configuration Table
CREATE TABLE IF NOT EXISTS tax_relief_max_config (
    id SERIAL PRIMARY KEY,
    config_name VARCHAR(100) NOT NULL UNIQUE,
    personal_relief_max DECIMAL(10,2) NOT NULL DEFAULT 9000.00,
    spouse_relief_max DECIMAL(10,2) NOT NULL DEFAULT 4000.00,
    child_relief_max DECIMAL(10,2) NOT NULL DEFAULT 2000.00,
    disabled_child_relief_max DECIMAL(10,2) NOT NULL DEFAULT 8000.00,
    parent_medical_max DECIMAL(10,2) NOT NULL DEFAULT 8000.00,
    medical_treatment_max DECIMAL(10,2) NOT NULL DEFAULT 10000.00,
    serious_disease_max DECIMAL(10,2) NOT NULL DEFAULT 10000.00,
    fertility_treatment_max DECIMAL(10,2) NOT NULL DEFAULT 5000.00,
    vaccination_max DECIMAL(10,2) NOT NULL DEFAULT 1000.00,
    dental_treatment_max DECIMAL(10,2) NOT NULL DEFAULT 1000.00,
    health_screening_max DECIMAL(10,2) NOT NULL DEFAULT 500.00,
    child_learning_disability_max DECIMAL(10,2) NOT NULL DEFAULT 3000.00,
    education_max DECIMAL(10,2) NOT NULL DEFAULT 8000.00,
    skills_course_max DECIMAL(10,2) NOT NULL DEFAULT 1000.00,
    lifestyle_max DECIMAL(10,2) NOT NULL DEFAULT 2500.00,
    sports_equipment_max DECIMAL(10,2) NOT NULL DEFAULT 300.00,
    gym_membership_max DECIMAL(10,2) NOT NULL DEFAULT 300.00,
    checkup_vaccine_upper_limit DECIMAL(10,2) NOT NULL DEFAULT 1000.00,
    life_insurance_upper_limit DECIMAL(10,2) NOT NULL DEFAULT 3000.00,
    epf_shared_subcap DECIMAL(10,2) NOT NULL DEFAULT 4000.00,
    combined_epf_insurance_limit DECIMAL(10,2) NOT NULL DEFAULT 7000.00,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_tax_relief_config_name ON tax_relief_max_config(config_name);
CREATE INDEX IF NOT EXISTS idx_tax_relief_active ON tax_relief_max_config(is_active);

-- 3. Comprehensive Payroll Information Table
CREATE TABLE IF NOT EXISTS payroll_information (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) NOT NULL,
    employee_email VARCHAR(255) NOT NULL,
    employee_name VARCHAR(255) NOT NULL,
    month_year VARCHAR(10) NOT NULL, -- Format: MM/YYYY
    basic_salary DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    allowances JSONB DEFAULT '{}',
    overtime_pay DECIMAL(12,2) DEFAULT 0.00,
    commission DECIMAL(12,2) DEFAULT 0.00,
    bonus DECIMAL(12,2) DEFAULT 0.00,
    gross_income DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    
    -- Statutory Deductions
    epf_employee DECIMAL(12,2) DEFAULT 0.00,
    epf_employer DECIMAL(12,2) DEFAULT 0.00,
    socso_employee DECIMAL(12,2) DEFAULT 0.00,
    socso_employer DECIMAL(12,2) DEFAULT 0.00,
    eis_employee DECIMAL(12,2) DEFAULT 0.00,
    eis_employer DECIMAL(12,2) DEFAULT 0.00,
    pcb_tax DECIMAL(12,2) DEFAULT 0.00,
    
    -- Tax Relief and Deductions
    monthly_deductions JSONB DEFAULT '{}',
    annual_tax_reliefs JSONB DEFAULT '{}',
    other_deductions JSONB DEFAULT '{}',
    total_deductions DECIMAL(12,2) DEFAULT 0.00,
    net_salary DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    
    -- Tax Status
    tax_resident_status VARCHAR(20) DEFAULT 'Resident',
    
    -- Calculation Details
    calculation_details JSONB DEFAULT '{}',
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(255) DEFAULT 'system',
    
    -- Constraints
    UNIQUE(employee_id, month_year)
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_payroll_employee_id ON payroll_information(employee_id);
CREATE INDEX IF NOT EXISTS idx_payroll_month_year ON payroll_information(month_year);
CREATE INDEX IF NOT EXISTS idx_payroll_employee_month ON payroll_information(employee_id, month_year);
CREATE INDEX IF NOT EXISTS idx_payroll_created_at ON payroll_information(created_at);
CREATE INDEX IF NOT EXISTS idx_payroll_tax_status ON payroll_information(tax_resident_status);

-- 4. Payslip Generation History Table
CREATE TABLE IF NOT EXISTS payslip_history (
    id SERIAL PRIMARY KEY,
    payroll_id INTEGER REFERENCES payroll_information(id) ON DELETE CASCADE,
    employee_id VARCHAR(50) NOT NULL,
    month_year VARCHAR(10) NOT NULL,
    pdf_filename VARCHAR(255),
    pdf_path VARCHAR(500),
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    generated_by VARCHAR(255) DEFAULT 'system',
    file_size_bytes INTEGER,
    checksum VARCHAR(64) -- For file integrity verification
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_payslip_payroll_id ON payslip_history(payroll_id);
CREATE INDEX IF NOT EXISTS idx_payslip_employee_id ON payslip_history(employee_id);
CREATE INDEX IF NOT EXISTS idx_payslip_month_year ON payslip_history(month_year);

-- =============================================================================
-- INSERT DEFAULT CONFIGURATIONS
-- =============================================================================

-- Insert default tax rates configuration
INSERT INTO tax_rates_config (
    config_name,
    progressive_rates,
    non_resident_rate,
    individual_tax_rebate,
    epf_employee_rate,
    epf_employer_rate,
    socso_employee_rate,
    socso_employer_rate,
    eis_employee_rate,
    eis_employer_rate,
    epf_ceiling,
    socso_ceiling,
    eis_ceiling
) VALUES (
    'default',
    '{
        "0-5000": 0.0,
        "5001-20000": 1.0,
        "20001-35000": 3.0,
        "35001-50000": 8.0,
        "50001-70000": 14.0,
        "70001-100000": 21.0,
        "100001-400000": 24.0,
        "400001-600000": 24.5,
        "600001-2000000": 25.0,
        "2000001+": 30.0
    }',
    30.00,
    400.00,
    11.00,
    12.00,
    0.50,
    1.75,
    0.20,
    0.20,
    6000.00,
    6000.00,
    6000.00
) ON CONFLICT (config_name) DO UPDATE SET
    progressive_rates = EXCLUDED.progressive_rates,
    individual_tax_rebate = EXCLUDED.individual_tax_rebate,
    updated_at = NOW();

-- Insert default tax relief maximum configuration
INSERT INTO tax_relief_max_config (
    config_name,
    personal_relief_max,
    spouse_relief_max,
    child_relief_max,
    disabled_child_relief_max,
    parent_medical_max,
    medical_treatment_max,
    serious_disease_max,
    fertility_treatment_max,
    vaccination_max,
    dental_treatment_max,
    health_screening_max,
    child_learning_disability_max,
    education_max,
    skills_course_max,
    lifestyle_max,
    sports_equipment_max,
    gym_membership_max,
    checkup_vaccine_upper_limit,
    life_insurance_upper_limit,
    epf_shared_subcap,
    combined_epf_insurance_limit
) VALUES (
    'default',
    9000.00,
    4000.00,
    2000.00,
    8000.00,
    8000.00,
    10000.00,
    10000.00,
    5000.00,
    1000.00,
    1000.00,
    500.00,
    3000.00,
    8000.00,
    1000.00,
    2500.00,
    300.00,
    300.00,
    1000.00,
    3000.00,
    4000.00,
    7000.00
) ON CONFLICT (config_name) DO UPDATE SET
    updated_at = NOW();

-- =============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =============================================================================

-- Enable RLS on all tables
ALTER TABLE tax_rates_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_relief_max_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE payroll_information ENABLE ROW LEVEL SECURITY;
ALTER TABLE payslip_history ENABLE ROW LEVEL SECURITY;

-- Create policies for authenticated users
CREATE POLICY "Allow authenticated users to read tax_rates_config" ON tax_rates_config
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated users to modify tax_rates_config" ON tax_rates_config
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated users to read tax_relief_max_config" ON tax_relief_max_config
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated users to modify tax_relief_max_config" ON tax_relief_max_config
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated users to read payroll_information" ON payroll_information
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated users to modify payroll_information" ON payroll_information
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated users to read payslip_history" ON payslip_history
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Allow authenticated users to modify payslip_history" ON payslip_history
    FOR ALL USING (auth.role() = 'authenticated');

-- =============================================================================
-- FUNCTIONS AND TRIGGERS
-- =============================================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_tax_rates_config_updated_at BEFORE UPDATE ON tax_rates_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tax_relief_max_config_updated_at BEFORE UPDATE ON tax_relief_max_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_payroll_information_updated_at BEFORE UPDATE ON payroll_information
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE tax_rates_config IS 'Stores tax rates configuration including progressive rates, EPF/SOCSO/EIS rates and ceilings';
COMMENT ON TABLE tax_relief_max_config IS 'Stores maximum amounts for various tax relief categories as per LHDN guidelines';
COMMENT ON TABLE payroll_information IS 'Comprehensive payroll records including all income, deductions, and tax calculations';
COMMENT ON TABLE payslip_history IS 'Tracks generated payslip PDFs for audit and retrieval purposes';

COMMENT ON COLUMN payroll_information.monthly_deductions IS 'JSONB field storing monthly deductions (potongan bulan semasa)';
COMMENT ON COLUMN payroll_information.annual_tax_reliefs IS 'JSONB field storing annual tax relief amounts';
COMMENT ON COLUMN payroll_information.calculation_details IS 'JSONB field storing calculation metadata and configuration used';
