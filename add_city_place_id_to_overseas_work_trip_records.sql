-- Migration: add city_place_id to overseas_work_trip_records
ALTER TABLE overseas_work_trip_records
ADD COLUMN IF NOT EXISTS city_place_id VARCHAR(255);

-- Note: run this against your Postgres/Supabase database to add the column used by the UI.
