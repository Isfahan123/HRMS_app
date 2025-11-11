-- Migration: Add working_days column to leave_requests to persist computed working day duration
-- Safe to run multiple times (IF NOT EXISTS guard via DO block)

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='leave_requests' AND column_name='working_days'
    ) THEN
        ALTER TABLE leave_requests ADD COLUMN working_days NUMERIC(5,2);
        COMMENT ON COLUMN leave_requests.working_days IS 'Persisted working-day (holiday-aware) duration for the leave request; 0.5 for half-day leaves.';
    END IF;
END$$;

-- Optional backfill: compute working_days for already approved requests.
-- Uncomment and run separately if desired.
-- UPDATE leave_requests lr
-- SET working_days = CASE 
--     WHEN lr.is_half_day THEN 0.5
--     ELSE NULL  -- Intentionally left NULL for subsequent application-level backfill to avoid heavy recalculation in SQL
-- END
-- WHERE lr.working_days IS NULL;

-- Application-level backfill recommendation:
-- Iterate approved rows without working_days and call calculate_working_days(start_date,end_date,state) to fill.
