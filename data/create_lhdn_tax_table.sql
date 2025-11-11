-- Create the LHDN tax configurations table in Supabase
-- Run this SQL in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS lhdn_tax_configs (
    id SERIAL PRIMARY KEY,
    config_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    
    -- Legacy fields for backward compatibility
    personal_relief DECIMAL(10, 2) DEFAULT 9000.00,
    spouse_relief DECIMAL(10, 2) DEFAULT 4000.00,
    child_relief DECIMAL(10, 2) DEFAULT 2000.00,
    disabled_child_relief DECIMAL(10, 2) DEFAULT 8000.00,
    epf_relief_enabled BOOLEAN DEFAULT true,
    epf_relief_max DECIMAL(10, 2) DEFAULT 6000.00,
    is_resident BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default LHDN 2025 configuration
INSERT INTO lhdn_tax_configs (
    config_name, description, personal_relief, spouse_relief, child_relief, 
    disabled_child_relief, epf_relief_enabled, epf_relief_max, is_resident
) VALUES (
    'default', 'Official LHDN 2025 tax reliefs with standard amounts per HASIL regulations',
    9000.00, 4000.00, 2000.00, 8000.00, true, 6000.00, true
) ON CONFLICT (config_name) DO UPDATE SET
    description = EXCLUDED.description,
    personal_relief = EXCLUDED.personal_relief,
    spouse_relief = EXCLUDED.spouse_relief,
    child_relief = EXCLUDED.child_relief,
    disabled_child_relief = EXCLUDED.disabled_child_relief,
    epf_relief_enabled = EXCLUDED.epf_relief_enabled,
    epf_relief_max = EXCLUDED.epf_relief_max,
    is_resident = EXCLUDED.is_resident,
    updated_at = NOW();
