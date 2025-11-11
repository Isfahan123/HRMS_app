-- Adds EPF Part A–E fields so the table can "follow the input" exactly
-- Safe to run multiple times due to IF NOT EXISTS guards

ALTER TABLE public.variable_percentage_configs
  ADD COLUMN IF NOT EXISTS epf_part_a_employee NUMERIC,
  ADD COLUMN IF NOT EXISTS epf_part_a_employer NUMERIC,
  ADD COLUMN IF NOT EXISTS epf_part_a_employee_over20k NUMERIC,
  ADD COLUMN IF NOT EXISTS epf_part_a_employer_over20k NUMERIC,
  ADD COLUMN IF NOT EXISTS epf_part_a_employer_bonus NUMERIC,
  ADD COLUMN IF NOT EXISTS epf_part_b_employee NUMERIC,
  ADD COLUMN IF NOT EXISTS epf_part_b_employer NUMERIC,
  ADD COLUMN IF NOT EXISTS epf_part_b_employee_over20k NUMERIC,
  ADD COLUMN IF NOT EXISTS epf_part_b_employer_over20k_fixed NUMERIC,
  ADD COLUMN IF NOT EXISTS epf_part_c_employee NUMERIC,
  ADD COLUMN IF NOT EXISTS epf_part_c_employer_fixed NUMERIC,
  ADD COLUMN IF NOT EXISTS epf_part_c_employee_over20k NUMERIC,
  ADD COLUMN IF NOT EXISTS epf_part_c_employer_over20k NUMERIC,
  ADD COLUMN IF NOT EXISTS epf_part_c_employer_bonus NUMERIC,
  ADD COLUMN IF NOT EXISTS epf_part_d_employee NUMERIC,
  ADD COLUMN IF NOT EXISTS epf_part_d_employer NUMERIC,
  ADD COLUMN IF NOT EXISTS epf_part_d_employee_over20k NUMERIC,
  ADD COLUMN IF NOT EXISTS epf_part_d_employer_over20k_fixed NUMERIC,
  ADD COLUMN IF NOT EXISTS epf_part_e_employee NUMERIC,
  ADD COLUMN IF NOT EXISTS epf_part_e_employer NUMERIC,
  ADD COLUMN IF NOT EXISTS epf_part_e_employee_over20k NUMERIC,
  ADD COLUMN IF NOT EXISTS epf_part_e_employer_over20k NUMERIC;
