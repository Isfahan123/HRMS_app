-- Expanded overseas_work_trip_records table
ALTER TABLE overseas_work_trip_records
ADD COLUMN country VARCHAR(100),
ADD COLUMN city VARCHAR(100),
ADD COLUMN start_date DATE,
ADD COLUMN end_date DATE,
ADD COLUMN duration INT,
ADD COLUMN flight_details TEXT,
ADD COLUMN accommodation_details TEXT,
ADD COLUMN daily_allowance DECIMAL(12,2),
ADD COLUMN travel_costs DECIMAL(12,2),
ADD COLUMN total_claim DECIMAL(12,2),
ADD COLUMN approved_by VARCHAR(100),
ADD COLUMN approval_date DATE,
ADD COLUMN attachments TEXT;
-- You may need to adjust types and add NOT NULL/defaults as needed.
