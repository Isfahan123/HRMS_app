-- Update variable_percentage_configs table structure to match current admin_payroll_tab implementation
-- Remove old simple structure and replace with comprehensive EPF Parts A-E + SOCSO + EIS structure

-- Drop the existing table if it exists
DROP TABLE IF EXISTS public.variable_percentage_configs;

-- Create updated variable_percentage_configs table with comprehensive structure
CREATE TABLE public.variable_percentage_configs (
    -- Primary identifier
    config_name TEXT NOT NULL,
    
    -- EPF rates - Part A: Malaysian + PRs + Non-citizens (before 1 Aug 1998) - Under 60
    epf_part_a_employee NUMERIC(5, 2) NOT NULL DEFAULT 11.0,
    epf_part_a_employer NUMERIC(5, 2) NOT NULL DEFAULT 12.0,
    epf_part_a_employee_over20k NUMERIC(5, 2) NOT NULL DEFAULT 11.0,
    epf_part_a_employer_over20k NUMERIC(5, 2) NOT NULL DEFAULT 12.0,
    epf_part_a_employer_bonus NUMERIC(5, 2) NOT NULL DEFAULT 13.0,
    
    -- EPF rates - Part B: Non-citizens (on/after 1 Aug 1998) - Under 60
    epf_part_b_employee NUMERIC(5, 2) NOT NULL DEFAULT 11.0,
    epf_part_b_employer NUMERIC(5, 2) NOT NULL DEFAULT 4.0,
    epf_part_b_employee_over20k NUMERIC(5, 2) NOT NULL DEFAULT 11.0,
    epf_part_b_employer_over20k_fixed NUMERIC(5, 2) NOT NULL DEFAULT 5.0,
    
    -- EPF rates - Part C: PRs + Non-citizens (before 1 Aug 1998) - 60 and above
    epf_part_c_employee NUMERIC(5, 2) NOT NULL DEFAULT 5.5,
    epf_part_c_employer_fixed NUMERIC(5, 2) NOT NULL DEFAULT 5.0,
    epf_part_c_employee_over20k NUMERIC(5, 2) NOT NULL DEFAULT 5.5,
    epf_part_c_employer_over20k NUMERIC(5, 2) NOT NULL DEFAULT 6.0,
    epf_part_c_employer_bonus NUMERIC(5, 2) NOT NULL DEFAULT 6.5,
    
    -- EPF rates - Part D: Non-citizens (on/after 1 Aug 1998) - 60 and above
    epf_part_d_employee NUMERIC(5, 2) NOT NULL DEFAULT 5.5,
    epf_part_d_employer NUMERIC(5, 2) NOT NULL DEFAULT 4.0,
    epf_part_d_employee_over20k NUMERIC(5, 2) NOT NULL DEFAULT 5.5,
    epf_part_d_employer_over20k_fixed NUMERIC(5, 2) NOT NULL DEFAULT 5.0,
    
    -- EPF rates - Part E: Malaysian Citizens - 60 and above
    epf_part_e_employee NUMERIC(5, 2) NOT NULL DEFAULT 0.0,
    epf_part_e_employer NUMERIC(5, 2) NOT NULL DEFAULT 4.0,
    epf_part_e_employee_over20k NUMERIC(5, 2) NOT NULL DEFAULT 0.0,
    epf_part_e_employer_over20k NUMERIC(5, 2) NOT NULL DEFAULT 4.0,
    
    -- SOCSO rates (two categories)
    socso_first_employee_rate NUMERIC(5, 2) NOT NULL DEFAULT 0.5,
    socso_first_employer_rate NUMERIC(5, 2) NOT NULL DEFAULT 1.75,
    socso_second_employee_rate NUMERIC(5, 2) NOT NULL DEFAULT 0.0,
    socso_second_employer_rate NUMERIC(5, 2) NOT NULL DEFAULT 1.25,
    
    -- EIS rates (single rate structure)
    eis_employee_rate NUMERIC(5, 2) NOT NULL DEFAULT 0.2,
    eis_employer_rate NUMERIC(5, 2) NOT NULL DEFAULT 0.2,
    
    -- Configuration metadata
    description TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
    
    CONSTRAINT variable_percentage_configs_pkey PRIMARY KEY (config_name)
) TABLESPACE pg_default;

-- Create trigger for updated_at timestamp
CREATE OR REPLACE FUNCTION update_variable_percentage_configs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_variable_percentage_configs_updated_at
    BEFORE UPDATE ON public.variable_percentage_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_variable_percentage_configs_updated_at();

-- Insert default configuration with official PERKESO/KWSP rates
INSERT INTO public.variable_percentage_configs (
    config_name,
    description,
    -- EPF Part A defaults
    epf_part_a_employee,
    epf_part_a_employer,
    epf_part_a_employee_over20k,
    epf_part_a_employer_over20k,
    epf_part_a_employer_bonus,
    -- EPF Part B defaults
    epf_part_b_employee,
    epf_part_b_employer,
    epf_part_b_employee_over20k,
    epf_part_b_employer_over20k_fixed,
    -- EPF Part C defaults
    epf_part_c_employee,
    epf_part_c_employer_fixed,
    epf_part_c_employee_over20k,
    epf_part_c_employer_over20k,
    epf_part_c_employer_bonus,
    -- EPF Part D defaults
    epf_part_d_employee,
    epf_part_d_employer,
    epf_part_d_employee_over20k,
    epf_part_d_employer_over20k_fixed,
    -- EPF Part E defaults
    epf_part_e_employee,
    epf_part_e_employer,
    epf_part_e_employee_over20k,
    epf_part_e_employer_over20k,
    -- SOCSO defaults
    socso_first_employee_rate,
    socso_first_employer_rate,
    socso_second_employee_rate,
    socso_second_employer_rate,
    -- EIS defaults
    eis_employee_rate,
    eis_employer_rate
) VALUES (
    'default',
    'PERKESO-compliant default rates with comprehensive Malaysian statutory contributions (KWSP Parts A-E)',
    -- EPF Part A: Malaysian + PRs + Non-citizens (before 1 Aug 1998) - Under 60
    11.0, 12.0, 11.0, 12.0, 13.0,
    -- EPF Part B: Non-citizens (on/after 1 Aug 1998) - Under 60  
    11.0, 4.0, 11.0, 5.0,
    -- EPF Part C: PRs + Non-citizens (before 1 Aug 1998) - 60 and above
    5.5, 5.0, 5.5, 6.0, 6.5,
    -- EPF Part D: Non-citizens (on/after 1 Aug 1998) - 60 and above
    5.5, 4.0, 5.5, 5.0,
    -- EPF Part E: Malaysian Citizens - 60 and above
    0.0, 4.0, 0.0, 4.0,
    -- SOCSO: First Category (Under 60) and Second Category (60+)
    0.5, 1.75, 0.0, 1.25,
    -- EIS: Employment Insurance System (18-60 years)
    0.2, 0.2
);

-- Add comments to table and columns for documentation
COMMENT ON TABLE public.variable_percentage_configs IS 'Variable percentage configuration for payroll calculations with comprehensive EPF Parts A-E, SOCSO categories, and EIS rates';

-- EPF Part A comments
COMMENT ON COLUMN public.variable_percentage_configs.epf_part_a_employee IS 'EPF Part A employee rate (%) - Malaysian + PRs + Non-citizens (before 1 Aug 1998) - Under 60';
COMMENT ON COLUMN public.variable_percentage_configs.epf_part_a_employer IS 'EPF Part A employer rate (%) - Malaysian + PRs + Non-citizens (before 1 Aug 1998) - Under 60';
COMMENT ON COLUMN public.variable_percentage_configs.epf_part_a_employee_over20k IS 'EPF Part A employee rate (%) for wages exceeding RM20,000';
COMMENT ON COLUMN public.variable_percentage_configs.epf_part_a_employer_over20k IS 'EPF Part A employer rate (%) for wages exceeding RM20,000';
COMMENT ON COLUMN public.variable_percentage_configs.epf_part_a_employer_bonus IS 'EPF Part A employer bonus rule rate (%) for wages ≤RM5k + bonus >RM5k';

-- EPF Part B comments
COMMENT ON COLUMN public.variable_percentage_configs.epf_part_b_employee IS 'EPF Part B employee rate (%) - Non-citizens (on/after 1 Aug 1998) - Under 60';
COMMENT ON COLUMN public.variable_percentage_configs.epf_part_b_employer IS 'EPF Part B employer rate (%) - Non-citizens (on/after 1 Aug 1998) - Under 60';
COMMENT ON COLUMN public.variable_percentage_configs.epf_part_b_employee_over20k IS 'EPF Part B employee rate (%) for wages exceeding RM20,000';
COMMENT ON COLUMN public.variable_percentage_configs.epf_part_b_employer_over20k_fixed IS 'EPF Part B employer fixed amount (RM) for wages exceeding RM20,000';

-- EPF Part C comments
COMMENT ON COLUMN public.variable_percentage_configs.epf_part_c_employee IS 'EPF Part C employee rate (%) - PRs + Non-citizens (before 1 Aug 1998) - 60 and above';
COMMENT ON COLUMN public.variable_percentage_configs.epf_part_c_employer_fixed IS 'EPF Part C employer fixed amount (RM) for table lookup';
COMMENT ON COLUMN public.variable_percentage_configs.epf_part_c_employee_over20k IS 'EPF Part C employee rate (%) for wages exceeding RM20,000';
COMMENT ON COLUMN public.variable_percentage_configs.epf_part_c_employer_over20k IS 'EPF Part C employer rate (%) for wages exceeding RM20,000';
COMMENT ON COLUMN public.variable_percentage_configs.epf_part_c_employer_bonus IS 'EPF Part C employer bonus rule rate (%) for wages ≤RM5k + bonus >RM5k';

-- EPF Part D comments
COMMENT ON COLUMN public.variable_percentage_configs.epf_part_d_employee IS 'EPF Part D employee rate (%) - Non-citizens (on/after 1 Aug 1998) - 60 and above';
COMMENT ON COLUMN public.variable_percentage_configs.epf_part_d_employer IS 'EPF Part D employer rate (%) - Non-citizens (on/after 1 Aug 1998) - 60 and above';
COMMENT ON COLUMN public.variable_percentage_configs.epf_part_d_employee_over20k IS 'EPF Part D employee rate (%) for wages exceeding RM20,000';
COMMENT ON COLUMN public.variable_percentage_configs.epf_part_d_employer_over20k_fixed IS 'EPF Part D employer fixed amount (RM) for wages exceeding RM20,000';

-- EPF Part E comments
COMMENT ON COLUMN public.variable_percentage_configs.epf_part_e_employee IS 'EPF Part E employee rate (%) - Malaysian Citizens - 60 and above (voluntary)';
COMMENT ON COLUMN public.variable_percentage_configs.epf_part_e_employer IS 'EPF Part E employer rate (%) - Malaysian Citizens - 60 and above';
COMMENT ON COLUMN public.variable_percentage_configs.epf_part_e_employee_over20k IS 'EPF Part E employee rate (%) for wages exceeding RM20,000 (voluntary)';
COMMENT ON COLUMN public.variable_percentage_configs.epf_part_e_employer_over20k IS 'EPF Part E employer rate (%) for wages exceeding RM20,000';

-- SOCSO comments
COMMENT ON COLUMN public.variable_percentage_configs.socso_first_employee_rate IS 'SOCSO First Category employee rate (%) - Under 60 years (Employment Injury + Invalidity)';
COMMENT ON COLUMN public.variable_percentage_configs.socso_first_employer_rate IS 'SOCSO First Category employer rate (%) - Under 60 years (Employment Injury + Invalidity)';
COMMENT ON COLUMN public.variable_percentage_configs.socso_second_employee_rate IS 'SOCSO Second Category employee rate (%) - 60+ years (Employment Injury only)';
COMMENT ON COLUMN public.variable_percentage_configs.socso_second_employer_rate IS 'SOCSO Second Category employer rate (%) - 60+ years (Employment Injury only)';

-- EIS comments
COMMENT ON COLUMN public.variable_percentage_configs.eis_employee_rate IS 'EIS employee rate (%) - Employment Insurance System (18-60 years, max RM6,000)';
COMMENT ON COLUMN public.variable_percentage_configs.eis_employer_rate IS 'EIS employer rate (%) - Employment Insurance System (18-60 years, max RM6,000)';

-- Metadata comments
COMMENT ON COLUMN public.variable_percentage_configs.config_name IS 'Unique configuration name identifier';
COMMENT ON COLUMN public.variable_percentage_configs.description IS 'Optional description of the configuration';
COMMENT ON COLUMN public.variable_percentage_configs.created_at IS 'Timestamp when configuration was created';
COMMENT ON COLUMN public.variable_percentage_configs.updated_at IS 'Timestamp when configuration was last updated';

-- Create indexes for performance
CREATE INDEX idx_variable_percentage_configs_created_at ON public.variable_percentage_configs(created_at);
CREATE INDEX idx_variable_percentage_configs_updated_at ON public.variable_percentage_configs(updated_at);

-- Grant permissions (adjust as needed for your application)
-- GRANT ALL PRIVILEGES ON public.variable_percentage_configs TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE variable_percentage_configs_id_seq TO your_app_user;

-- Display final table structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default,
    ordinal_position
FROM information_schema.columns 
WHERE table_name = 'variable_percentage_configs' 
    AND table_schema = 'public'
ORDER BY ordinal_position;
