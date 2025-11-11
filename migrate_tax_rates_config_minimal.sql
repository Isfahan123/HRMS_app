-- Migration: Slim tax_rates_config to minimal policy shape
-- Purpose: Move progressive brackets to progressive_tax_brackets and ceilings to statutory_limits_config.
-- Keeps only non_resident_rate and individual_tax_rebate in tax_rates_config.

begin;

-- Drop legacy columns we no longer use
alter table if exists public.tax_rates_config
    drop column if exists progressive_rates,
    drop column if exists epf_employee_rate,
    drop column if exists epf_employer_rate,
    drop column if exists socso_employee_rate,
    drop column if exists socso_employer_rate,
    drop column if exists eis_employee_rate,
    drop column if exists eis_employer_rate,
    drop column if exists epf_ceiling,
    drop column if exists socso_ceiling,
    drop column if exists eis_ceiling;

-- Ensure minimal columns exist
alter table if exists public.tax_rates_config
    add column if not exists non_resident_rate decimal(5,2) not null default 30.00,
    add column if not exists individual_tax_rebate decimal(10,2) not null default 400.00,
    add column if not exists is_active boolean not null default true,
    add column if not exists created_at timestamptz not null default now(),
    add column if not exists updated_at timestamptz not null default now();

-- Keep/ensure indexes
create index if not exists idx_tax_rates_config_name on public.tax_rates_config(config_name);
create index if not exists idx_tax_rates_active on public.tax_rates_config(is_active);

-- Seed/refresh default rows
insert into public.tax_rates_config (config_name, non_resident_rate, individual_tax_rebate, is_active)
values ('default', 30.00, 400.00, true)
on conflict (config_name) do update
set non_resident_rate = excluded.non_resident_rate,
    individual_tax_rebate = excluded.individual_tax_rebate,
    is_active = true,
    updated_at = now();

insert into public.tax_rates_config (config_name, non_resident_rate, individual_tax_rebate, is_active)
values ('current_admin_config', 30.00, 400.00, true)
on conflict (config_name) do nothing;

commit;
