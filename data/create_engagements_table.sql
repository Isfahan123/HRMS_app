-- Unified engagements table for Training/Course and Overseas Trip/Work
create table if not exists public.engagements (
  id uuid primary key default gen_random_uuid(),
  employee_id uuid not null references public.employees (id) on delete cascade,
  type text not null check (type in ('training','course','trip','work_assignment')),
  -- Training/Course
  title text,
  provider text,
  certification text,
  skills text,
  -- Trip/Work
  country text,
  city text,
  city_place_id text,
  purpose text,
  flight_details text,
  accommodation_details text,
  -- Common
  description text,
  start_date date,
  end_date date,
  duration integer,
  course_fees numeric,
  travel_costs numeric,
  daily_allowance numeric,
  total_cost numeric,
  approved_by text,
  approval_date date,
  attachment_url text,
  admin_notes text,
  created_at timestamptz default now()
);

create index if not exists idx_engagements_employee on public.engagements (employee_id);
create index if not exists idx_engagements_start_date on public.engagements (start_date);
