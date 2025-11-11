-- Progressive tax brackets normalized table (replaces JSON progressive_rates)
-- Stores bracket ranges and rates per configuration.

create table if not exists public.progressive_tax_brackets (
    id bigserial primary key,
    config_name text not null default 'default',
    bracket_order smallint not null,
    lower_bound numeric(14,2) not null,        -- inclusive lower bound (RM)
    upper_bound numeric(14,2),                 -- inclusive upper bound; null means infinity
    rate numeric(6,5) not null,                -- decimal fraction, e.g., 0.14 for 14%
    -- Optional UI helper fields (not required for PCB):
    on_first_amount numeric(14,2),             -- UI: "On First" amount for display only
    next_amount numeric(14,2),                 -- UI: "Next" band width for display only
    tax_first_amount numeric(14,2),            -- UI: Tax on first portion (RM)
    tax_next_amount numeric(14,2),             -- UI: Tax on next portion (RM)
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create unique index if not exists idx_progressive_tax_brackets_cfg_order
    on public.progressive_tax_brackets (config_name, bracket_order);

create index if not exists idx_progressive_tax_brackets_bounds
    on public.progressive_tax_brackets (config_name, lower_bound, upper_bound);

create trigger trg_progressive_tax_brackets_updated_at
    before update on public.progressive_tax_brackets
    for each row execute procedure public.set_current_timestamp_updated_at();

-- Seed default 2025 brackets (idempotent upsert by config_name + bracket_order)
insert into public.progressive_tax_brackets (config_name, bracket_order, lower_bound, upper_bound, rate)
values
  ('default', 1, 0,        5000,      0.00),
  ('default', 2, 5000,     20000,     0.01),
  ('default', 3, 20000,    35000,     0.03),
  ('default', 4, 35000,    50000,     0.08),
  ('default', 5, 50000,    70000,     0.14),
  ('default', 6, 70000,    100000,    0.21),
  ('default', 7, 100000,   400000,    0.24),
  ('default', 8, 400000,   600000,    0.245),
  ('default', 9, 600000,   2000000,   0.25),
  ('default',10, 2000000,  null,       0.30)
on conflict (config_name, bracket_order) do update
set lower_bound = excluded.lower_bound,
    upper_bound = excluded.upper_bound,
    rate        = excluded.rate,
    updated_at  = now();
