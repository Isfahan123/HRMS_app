-- Expanded training_course_records table (idempotent)
-- Use IF NOT EXISTS so this migration can be run multiple times safely.
ALTER TABLE training_course_records
	ADD COLUMN IF NOT EXISTS course_title VARCHAR(200),
	ADD COLUMN IF NOT EXISTS provider VARCHAR(200),
	ADD COLUMN IF NOT EXISTS country VARCHAR(100),
	ADD COLUMN IF NOT EXISTS city VARCHAR(100),
	ADD COLUMN IF NOT EXISTS start_date DATE,
	ADD COLUMN IF NOT EXISTS end_date DATE,
	ADD COLUMN IF NOT EXISTS duration INT,
	ADD COLUMN IF NOT EXISTS objectives TEXT,
	ADD COLUMN IF NOT EXISTS certification VARCHAR(200),
	ADD COLUMN IF NOT EXISTS skills TEXT,
	ADD COLUMN IF NOT EXISTS course_fees DECIMAL(12,2),
	ADD COLUMN IF NOT EXISTS travel_accommodation DECIMAL(12,2),
	ADD COLUMN IF NOT EXISTS daily_allowance DECIMAL(12,2),
	ADD COLUMN IF NOT EXISTS nominated_by VARCHAR(100),
	ADD COLUMN IF NOT EXISTS approval_date DATE,
	ADD COLUMN IF NOT EXISTS feedback TEXT,
	ADD COLUMN IF NOT EXISTS supervisor_evaluation TEXT,
	ADD COLUMN IF NOT EXISTS attachments TEXT;

-- Note: adjust types / add NOT NULL/default constraints as required by your application.
-- If you need to set default values for existing rows, run UPDATE statements after this migration.
