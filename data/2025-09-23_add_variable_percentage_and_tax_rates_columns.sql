-- Migration helper: add missing columns for variable_percentage_configs and tax_rates_config
-- Run these statements in your Supabase SQL editor if columns are missing.

-- variable_percentage_configs: support both combined and stage-based EPF, SOCSO, and optional ACT split
alter table if exists variable_percentage_configs
    add column if not exists epf_employee_rate numeric,
    add column if not exists epf_employer_rate numeric,
    add column if not exists epf_employee_rate_stage1 numeric,
    add column if not exists epf_employer_rate_stage1 numeric,
    add column if not exists epf_employee_rate_stage2 numeric,
    add column if not exists epf_employer_rate_stage2 numeric,
    add column if not exists socso_employee_rate numeric,
    add column if not exists socso_employer_rate numeric,
    add column if not exists socso_act4_employee_rate numeric,
    add column if not exists socso_act4_employer_rate numeric,
    add column if not exists socso_act800_employee_rate numeric,
    add column if not exists socso_act800_employer_rate numeric,
    add column if not exists eis_employee_rate numeric,
    add column if not exists eis_employer_rate numeric,
    add column if not exists pcb_rate numeric,
    add column if not exists description text,
    add column if not exists created_at timestamp with time zone default now(),
    add column if not exists updated_at timestamp with time zone default now();

-- tax_rates_config: ensure proper columns for minimal policy
alter table if exists tax_rates_config
    add column if not exists individual_tax_rebate numeric,
    add column if not exists rebate_threshold numeric,
    add column if not exists is_active boolean default true;
