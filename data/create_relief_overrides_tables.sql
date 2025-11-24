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

-- Optional: enable RLS and grant policies according to your security model.
-- alter table public.relief_item_overrides enable row level security;
-- alter table public.relief_group_overrides enable row level security;
-- create policy "admin can manage relief overrides" on public.relief_item_overrides using (true) with check (true);
-- create policy "admin can manage group overrides" on public.relief_group_overrides using (true) with check (true);
