-- Creates the admin override tables for TP1 reliefs. Run this in Supabase SQL editor.

create table if not exists public.relief_item_overrides (
  item_key text primary key,
  cap numeric,
  pcb_only boolean,
  cycle_years integer,
  updated_at timestamptz default now(),
  created_at timestamptz default now()
);

create or replace function public.update_relief_item_overrides_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_update_relief_item_overrides on public.relief_item_overrides;
create trigger trg_update_relief_item_overrides
before update on public.relief_item_overrides
for each row execute function public.update_relief_item_overrides_updated_at();

-- Group overrides table for group-level caps
create table if not exists public.relief_group_overrides (
  group_id text primary key,
  cap numeric not null,
  updated_at timestamptz default now(),
  created_at timestamptz default now()
);

create or replace function public.update_relief_group_overrides_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_update_relief_group_overrides on public.relief_group_overrides;
create trigger trg_update_relief_group_overrides
before update on public.relief_group_overrides
for each row execute function public.update_relief_group_overrides_updated_at();

-- Employee-specific relief overrides table (for web interface)
-- This table stores per-employee custom relief amounts (different from item-level overrides)
create table if not exists public.lhdn_relief_overrides (
  id uuid default gen_random_uuid() primary key,
  employee_id uuid references public.employees(id) on delete cascade,
  employee_name varchar(255),
  employee_email varchar(255),
  relief_category varchar(100) not null,
  override_amount decimal(10, 2) not null,
  effective_from date,
  effective_to date,
  reason text,
  created_at timestamptz default now()
);

create index if not exists idx_relief_overrides_employee on public.lhdn_relief_overrides(employee_id);
create index if not exists idx_relief_overrides_category on public.lhdn_relief_overrides(relief_category);

-- Optional: enable RLS and grant policies according to your security model.
-- alter table public.relief_item_overrides enable row level security;
-- alter table public.relief_group_overrides enable row level security;
-- alter table public.lhdn_relief_overrides enable row level security;
-- create policy "admin can manage relief overrides" on public.relief_item_overrides using (true) with check (true);
-- create policy "admin can manage group overrides" on public.relief_group_overrides using (true) with check (true);
-- create policy "admin can manage employee relief overrides" on public.lhdn_relief_overrides using (true) with check (true);
