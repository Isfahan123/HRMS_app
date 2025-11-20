-- SQL migration to create employee_history table
-- This table serves dual purposes:
-- 1. Employment history (previous jobs) - uses start_date, end_date, company, position
-- 2. Salary change history - uses effective_date, change_type, change_amount, change_percentage
-- Fields: id, employee_id, company, position, start_date, end_date, notes, attachments, city_place_id, admin_notes, created_at, updated_at

CREATE TABLE IF NOT EXISTS employee_history (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id uuid NOT NULL,
    employee_email varchar(255),
    company text,
    -- UI fields surfaced in Employee History tab
    -- These are added to persist the form's job/department/group choices
    job_title text,
    position text,
    department text,
    functional_group text,
    employment_type text,
    start_date date,
    end_date date,
    notes text,
    attachments jsonb,
    city_place_id text,
    admin_notes text,
    -- Fields for salary change tracking
    effective_date date,
    change_date date,
    field_changed varchar(100),
    previous_value text,
    new_value text,
    reason text,
    changed_by varchar(255),
    change_type varchar(100),
    change_amount decimal(12, 2),
    change_percentage decimal(5, 2),
    employee_name varchar(255),
    created_by varchar(255),
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_employee_history_employee_id ON employee_history (employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_history_effective_date ON employee_history (effective_date);
CREATE INDEX IF NOT EXISTS idx_employee_history_email_effective ON employee_history (employee_email, effective_date DESC);
