-- =============================================================================
-- UPDATE SCRIPT FOR ADDING INDIVIDUAL TAX REBATE TO EXISTING TABLES
-- =============================================================================

-- Add individual_tax_rebate column to existing tax_rates_config table
-- This script is safe to run multiple times (will only add column if it doesn't exist)

DO $$ 
BEGIN 
    -- Check if column exists and add it if it doesn't
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'tax_rates_config' 
        AND column_name = 'individual_tax_rebate'
    ) THEN
        ALTER TABLE tax_rates_config 
        ADD COLUMN individual_tax_rebate DECIMAL(10,2) NOT NULL DEFAULT 400.00;
        
        -- Add comment to the column
        COMMENT ON COLUMN tax_rates_config.individual_tax_rebate IS 'Individual tax rebate amount (LHDN 2025: RM 400)';
        
        RAISE NOTICE 'Column individual_tax_rebate added to tax_rates_config table';
    ELSE
        RAISE NOTICE 'Column individual_tax_rebate already exists in tax_rates_config table';
    END IF;
END $$;

-- Update existing default configuration with individual tax rebate
UPDATE tax_rates_config 
SET individual_tax_rebate = 400.00,
    updated_at = NOW()
WHERE config_name = 'default';

-- Create a backup of existing configurations before update
-- This is for safety in case we need to rollback
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
    eis_ceiling,
    is_active
) 
SELECT 
    config_name || '_backup_' || to_char(NOW(), 'YYYY_MM_DD_HH24_MI'),
    progressive_rates,
    non_resident_rate,
    COALESCE(individual_tax_rebate, 400.00),
    epf_employee_rate,
    epf_employer_rate,
    socso_employee_rate,
    socso_employer_rate,
    eis_employee_rate,
    eis_employer_rate,
    epf_ceiling,
    socso_ceiling,
    eis_ceiling,
    FALSE  -- Mark backup as inactive
FROM tax_rates_config 
WHERE config_name = 'default'
ON CONFLICT (config_name) DO NOTHING;

-- Verify the update
SELECT 
    config_name,
    individual_tax_rebate,
    updated_at
FROM tax_rates_config 
WHERE config_name = 'default' OR config_name LIKE '%backup%'
ORDER BY updated_at DESC;

-- Success message
DO $$ 
BEGIN 
    RAISE NOTICE 'Individual tax rebate successfully added to tax_rates_config table';
    RAISE NOTICE 'Default configuration updated with RM 400 individual tax rebate';
    RAISE NOTICE 'Backup configuration created for safety';
END $$;
