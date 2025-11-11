-- Created: 29-Sep-2025
-- SQL: create employees table with additional history column (date_leave). `date_re_joined` removed per request.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS public.employees (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  full_name text NOT NULL,
  gender text NULL,
  date_of_birth date NULL,
  nationality text NULL,
  marital_status text NULL,
  email text NULL DEFAULT 'aimanisfahan123@gmail.com'::text,
  phone_number text NULL,
  address text NULL,
  city text NULL,
  state text NULL,
  zipcode text NULL,
  highest_qualification text NULL,
  institution text NULL,
  graduation_year integer NULL,
  employee_id text NOT NULL,
  job_title text NOT NULL,
  department text NOT NULL,
  employment_type text NULL,
  date_joined date NOT NULL,
  date_leave date NULL,
  status text NULL DEFAULT 'Active'::text,
  basic_salary numeric NULL DEFAULT 0.0,
  bank_account text NULL,
  epf_number text NULL,
  socso_number text NULL,
  emergency_name text NULL,
  emergency_relation text NULL,
  emergency_phone text NULL,
  photo_url text NULL,
  resume_url text NULL,
  created_at timestamp with time zone NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp with time zone NULL,
  allowances jsonb NULL DEFAULT '{}'::jsonb,
  citizenship text NULL,
  religion text NULL,
  number_of_children integer NULL DEFAULT 0,
  spouse_working boolean NULL DEFAULT false,
  nric character varying(20) NULL,
  bank_name text NULL,
  race character varying NULL,
  sip_participation text NULL DEFAULT 'No'::text,
  sip_type text NULL DEFAULT 'None'::text,
  sip_amount_rate numeric(10,2) NULL DEFAULT 0.0,
  additional_epf_enabled text NULL DEFAULT 'No'::text,
  additional_epf_amount numeric(10,2) NULL DEFAULT 0.0,
  prs_participation text NULL DEFAULT 'No'::text,
  prs_provider text NULL DEFAULT 'None'::text,
  prs_amount numeric(10,2) NULL DEFAULT 0.0,
  life_insurance_type text NULL DEFAULT 'No'::text,
  insurance_premium numeric(10,2) NULL DEFAULT 0.0,
  medical_insurance_type text NULL DEFAULT 'No'::text,
  medical_premium numeric(10,2) NULL DEFAULT 0.0,
  other_deductions_amount numeric(10,2) NULL DEFAULT 0.0,
  other_deduction_type text NULL,
  residency_status text NULL,
  tax_resident_status character varying(20) NULL DEFAULT 'Resident'::character varying,
  days_in_malaysia_current_year integer NULL,
  tax_form_type character varying(10) NULL DEFAULT 'BE'::character varying,
  epf_participation character varying(20) NULL DEFAULT 'Mandatory'::character varying,
  socso_category character varying(20) NULL DEFAULT 'Category1'::character varying,
  socso_participation character varying(20) NULL DEFAULT 'Mandatory'::character varying,
  sip_amount numeric(10,2) NULL DEFAULT 0.00,
  life_insurance_premium numeric(10,2) NULL DEFAULT 0.00,
  medical_insurance_premium numeric(10,2) NULL DEFAULT 0.00,
  epf_part text NULL,
  role text NULL,
  CONSTRAINT employees_pkey PRIMARY KEY (id),
  CONSTRAINT employees_email_key UNIQUE (email),
  CONSTRAINT employees_employee_id_key UNIQUE (employee_id),
  CONSTRAINT check_sip_amount CHECK ((sip_amount >= 0.00)),
  CONSTRAINT check_socso_category CHECK (
    ((socso_category)::text = ANY ((ARRAY['Category1'::character varying,'Category2'::character varying,'Category3'::character varying,'Category4'::character varying,'Exempt'::character varying])::text[]))
  ),
  CONSTRAINT check_socso_participation CHECK (
    ((socso_participation)::text = ANY ((ARRAY['Mandatory'::character varying,'Voluntary'::character varying,'Exempt'::character varying])::text[]))
  ),
  CONSTRAINT check_tax_form_type CHECK (
    ((tax_form_type)::text = ANY ((ARRAY['BE'::character varying,'B'::character varying,'BT'::character varying,'M'::character varying])::text[]))
  ),
  CONSTRAINT check_tax_resident_status CHECK (
    ((tax_resident_status)::text = ANY ((ARRAY['Resident'::character varying,'Non-Resident'::character varying])::text[]))
  ),
  CONSTRAINT chk_additional_epf_amount_positive CHECK ((additional_epf_amount >= (0)::numeric)),
  CONSTRAINT chk_additional_epf_enabled CHECK ( (additional_epf_enabled = ANY (ARRAY['Yes'::text,'No'::text])) ),
  CONSTRAINT chk_employee_insurance_premium_positive CHECK ((insurance_premium >= (0)::numeric)),
  CONSTRAINT chk_employee_medical_premium_positive CHECK ((medical_premium >= (0)::numeric)),
  CONSTRAINT chk_employee_other_deductions_positive CHECK ((other_deductions_amount >= (0)::numeric)),
  CONSTRAINT chk_life_insurance_type CHECK (
    (life_insurance_type = ANY (ARRAY['No'::text,'Company Scheme'::text,'Personal'::text]))
  ),
  CONSTRAINT chk_medical_insurance_type CHECK (
    (medical_insurance_type = ANY (ARRAY['No'::text,'Company Scheme'::text,'Personal'::text]))
  ),
  CONSTRAINT chk_prs_amount_positive CHECK ((prs_amount >= (0)::numeric)),
  CONSTRAINT chk_prs_participation CHECK ( (prs_participation = ANY (ARRAY['Yes'::text,'No'::text])) ),
  CONSTRAINT chk_sip_amount_rate_positive CHECK ((sip_amount_rate >= (0)::numeric)),
  CONSTRAINT chk_sip_participation CHECK ( (sip_participation = ANY (ARRAY['Yes'::text,'No'::text])) ),
  CONSTRAINT chk_sip_type CHECK ( (sip_type = ANY (ARRAY['None'::text,'Fixed Amount'::text,'Percentage'::text])) ),
  CONSTRAINT employees_employment_type_check CHECK ( (employment_type = ANY (ARRAY['Full-time'::text,'Part-time'::text,'Contract'::text])) ),
  CONSTRAINT employees_gender_check CHECK ( (gender = ANY (ARRAY['Male'::text,'Female'::text,'Other'::text])) ),
  CONSTRAINT employees_residency_status_check CHECK ( (residency_status = ANY (ARRAY['Resident'::text,'Non-Resident'::text])) ),
  CONSTRAINT check_additional_epf_amount CHECK ((additional_epf_amount >= 0.00)),
  CONSTRAINT employees_status_check CHECK ( (status = ANY (ARRAY['Active'::text,'Inactive'::text,'Resigned'::text,'Terminated'::text])) ),
  CONSTRAINT check_epf_participation CHECK (
    ((epf_participation)::text = ANY ((ARRAY['Mandatory'::character varying,'Voluntary'::character varying,'Exempt'::character varying])::text[]))
  ),
  CONSTRAINT check_prs_amount CHECK ((prs_amount >= 0.00))
) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_employees_sip_participation ON public.employees USING btree (sip_participation) TABLESPACE pg_default
WHERE (sip_participation = 'Yes'::text);

CREATE INDEX IF NOT EXISTS idx_employees_prs_participation ON public.employees USING btree (prs_participation) TABLESPACE pg_default
WHERE (prs_participation = 'Yes'::text);

-- trigger creation (assumes lowercase_email function exists in the DB)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger t
    JOIN pg_class c ON t.tgrelid = c.oid
    WHERE c.relname = 'employees' AND t.tgname = 'lowercase_email_trigger'
  ) THEN
    EXECUTE $$
      CREATE TRIGGER lowercase_email_trigger
      BEFORE INSERT OR UPDATE ON employees
      FOR EACH ROW
      EXECUTE FUNCTION lowercase_email();
    $$;
  END IF;
END$$;

-- Notes: added date_leave and date_re_joined to support employee history tracking.
