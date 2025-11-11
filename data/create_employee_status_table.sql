-- Migration: create employee_status table
-- Created: 2025-09-29

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS public.employee_status (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  employee_id text NOT NULL,
  status text NOT NULL,
  effective_date date NULL,
  notes text NULL,
  updated_at timestamp with time zone NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_employee_status_employee_id ON public.employee_status(employee_id);

-- Example: trigger to update updated_at could be added if desired
