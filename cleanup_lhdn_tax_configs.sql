-- Clean up unused LHDN tax configuration table and update variable percentage structure
-- This script removes the lhdn_tax_configs table since it's no longer needed

-- 1. Drop LHDN tax configs table (no longer used)
DROP TABLE IF EXISTS public.lhdn_tax_configs CASCADE;

-- 2. Drop any related functions or triggers for LHDN tax configs
DROP FUNCTION IF EXISTS update_lhdn_tax_configs_updated_at() CASCADE;

-- 3. Display confirmation
SELECT 'LHDN tax configs table and related objects have been removed' AS status;

-- 4. Show remaining variable percentage configs table structure
\d public.variable_percentage_configs;

-- 5. Show current variable percentage configurations (if any)
SELECT 
    config_name,
    description,
    created_at,
    updated_at
FROM public.variable_percentage_configs
ORDER BY created_at;
