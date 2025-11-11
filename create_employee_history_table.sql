-- SQL migration to create employee_history table
-- Fields: id, employee_id, company, position, start_date, end_date, notes, attachments, city_place_id, admin_notes, created_at, updated_at

CREATE TABLE IF NOT EXISTS employee_history (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id uuid NOT NULL,
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
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_employee_history_employee_id ON employee_history (employee_id);
