# Fix for Employee History Errors: Missing Column Issues

## Problem
Multiple endpoints were failing with column not found errors:

1. **Salary History endpoint** (`/api/admin/salary-history`):
```
Error getting salary history: {'code': '42703', 'details': None, 'hint': None, 'message': 'column employee_history.effective_date does not exist'}
```

2. **Employee History endpoint** (`/api/admin/employee-history`):
Potential error with `start_date` column ordering.

## Root Cause
The `employee_history` table is used for two purposes:
1. **Employment history** (previous jobs, companies) - uses `start_date`, `end_date`, `company`, `position`
2. **Salary change history** - uses `effective_date`, `change_type`, `change_amount`

The application code was trying to query both types of records, but the database schema was missing columns for both purposes. The CREATE_MISSING_TABLES.sql only had fields for generic change tracking, missing:
- Employment history specific columns (`start_date`, `end_date`, `company`, `position`, etc.)
- Salary tracking specific columns (`effective_date`, `change_amount`, `change_percentage`)

## Solution
Added all missing columns to the `employee_history` table to support both employment history and salary change tracking.

### New Columns Added for Employment History:
- `company` - Company/employer name
- `job_title` - Job title at that company
- `position` - Position held
- `department` - Department worked in
- `functional_group` - Functional group/division
- `employment_type` - Type of employment (full-time, contract, etc.)
- `start_date` - Start date of employment period
- `end_date` - End date of employment period
- `notes` - Additional notes
- `attachments` - Document attachments (JSONB)
- `city_place_id` - Location identifier
- `admin_notes` - Administrative notes
- `updated_at` - Last update timestamp

### New Columns Added for Salary Change Tracking:
- `effective_date` - Date when the salary change becomes effective
- `change_type` - Type of change (e.g., 'salary_adjustment', 'promotion', 'increment')
- `change_amount` - Amount of salary change
- `change_percentage` - Percentage of salary change
- `employee_name` - Employee name for easier reporting
- `created_by` - User who created the record

## Migration Instructions

### Option 1: Run the Migration SQL (Recommended)
Execute this SQL script in your Supabase SQL Editor:
```bash
data/migrate_add_effective_date_to_employee_history.sql
```

This will add the missing columns without affecting existing data.

### Option 2: Recreate from Scratch (Only for new installations)
If you're setting up a fresh database, you can run:
```bash
CREATE_MISSING_TABLES.sql
```
or
```bash
data/create_employee_history_table.sql
```

Both files have been updated to include the new columns.

## Files Modified
1. `CREATE_MISSING_TABLES.sql` - Updated employee_history table schema
2. `data/create_employee_history_table.sql` - Updated to include salary history columns
3. `data/migrate_add_effective_date_to_employee_history.sql` - New migration file (ADD THIS FILE)

## Affected Endpoints
The following endpoints now work correctly:

**Salary History:**
- `GET /api/admin/salary-history` - Get salary change history (orders by `effective_date`)
- `POST /api/admin/salary-history` - Create salary change record
- `PUT /api/admin/salary-history/{record_id}` - Update salary change record
- `DELETE /api/admin/salary-history/{record_id}` - Delete salary change record
- `GET /api/admin/salary-history/export/csv` - Export salary history to CSV

**Employment History:**
- `GET /api/admin/employee-history` - Get employment history (orders by `start_date`)
- `POST /api/admin/employee-history` - Create employment history record
- `PUT /api/admin/employee-history/{record_id}` - Update employment history record
- `DELETE /api/admin/employee-history/{record_id}` - Delete employment history record
- `GET /api/admin/employee-history/export/csv` - Export employment history to CSV

## Testing
After running the migration:
1. Navigate to the Admin Dashboard in the web interface
2. Click on any salary-related functionality
3. Verify that no errors appear in the console
4. Try creating, viewing, and exporting salary history records

## Notes
- The `employee_history` table now supports both employment history and salary change tracking
- Existing records are not affected
- All new salary change records will use the `effective_date` field
- Employment history records continue to use `start_date` and `end_date`
