-- Migration: Add detailed education fields to employees table
-- Date: 2025-09-30
-- Adds primary, secondary and tertiary education related columns

BEGIN;

ALTER TABLE employees
    ADD COLUMN primary_school_name TEXT,
    ADD COLUMN primary_location TEXT,
    ADD COLUMN primary_year_started VARCHAR(10),
    ADD COLUMN primary_year_completed VARCHAR(10),
    ADD COLUMN primary_type VARCHAR(64),

    ADD COLUMN secondary_school_name TEXT,
    ADD COLUMN secondary_location TEXT,
    ADD COLUMN secondary_year_started VARCHAR(10),
    ADD COLUMN secondary_year_completed VARCHAR(10),
    ADD COLUMN secondary_qualification VARCHAR(128),
    ADD COLUMN secondary_stream VARCHAR(64),
    ADD COLUMN secondary_grades TEXT,
    ADD COLUMN secondary_type VARCHAR(64),

    ADD COLUMN tertiary_institution TEXT,
    ADD COLUMN tertiary_location TEXT,
    ADD COLUMN tertiary_institution_type VARCHAR(64),
    ADD COLUMN tertiary_level VARCHAR(64),
    ADD COLUMN tertiary_field VARCHAR(128),
    ADD COLUMN tertiary_major VARCHAR(128),
    ADD COLUMN tertiary_year_started VARCHAR(10),
    ADD COLUMN tertiary_year_completed VARCHAR(10),
    ADD COLUMN tertiary_status VARCHAR(32),
    ADD COLUMN tertiary_cgpa VARCHAR(32);

COMMIT;
