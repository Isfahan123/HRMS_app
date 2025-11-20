# Verification Steps for Salary History Fix

## Pre-Migration Check
Before applying the migration, you should see these errors:
```
Error getting salary history: {'code': '42703', 'details': None, 'hint': None, 'message': 'column employee_history.effective_date does not exist'}
```

## Migration Steps

### 1. Run the Migration SQL
Execute the migration file in your Supabase SQL Editor:
```sql
-- Copy and paste the contents of:
data/migrate_add_effective_date_to_employee_history.sql
```

### 2. Verify the Migration
Check that the columns were added successfully:
```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'employee_history' 
  AND table_schema = 'public'
ORDER BY column_name;
```

You should see these new columns:
- `effective_date` (date)
- `change_type` (varchar)
- `change_amount` (decimal)
- `change_percentage` (decimal)
- `employee_name` (varchar)
- `created_by` (varchar)

## Post-Migration Verification

### Option 1: Using the Web Interface
1. Start the web application:
   ```bash
   python web_app.py
   # or
   uvicorn web_app:app --reload
   ```

2. Navigate to `http://localhost:8000/admin-dashboard`

3. Test the Salary History functionality:
   - View salary history records (should load without errors)
   - Create a new salary change record
   - Export salary history to CSV
   - Edit an existing salary record
   - Delete a salary record

4. Check the browser console and server logs - there should be no errors related to `effective_date`

### Option 2: Using the API Test Script
```bash
python test_api_endpoints.py
```

Look for the line:
```
GET /api/admin/salary-history - View salary history
```

It should show:
- Status: ✅ Working
- Status Code: 200
- No errors about missing columns

### Option 3: Using cURL
```bash
# Test GET endpoint
curl http://localhost:8000/api/admin/salary-history

# Expected response (no errors):
{"success": true, "data": [...]}
```

```bash
# Test POST endpoint
curl -X POST http://localhost:8000/api/admin/salary-history \
  -H "Content-Type: application/json" \
  -d '{
    "employee_email": "test@example.com",
    "previous_salary": "5000",
    "new_salary": "5500",
    "effective_date": "2025-01-01",
    "change_type": "salary_adjustment",
    "reason": "Annual increment"
  }'

# Expected response:
{"success": true, "message": "Salary change recorded successfully", "data": {...}}
```

## Expected Outcomes

### Before Fix ❌
```
Error getting salary history: {'code': '42703', ...}
GET /api/admin/salary-history - FAILED
```

### After Fix ✅
```
GET /api/admin/salary-history - SUCCESS
{
  "success": true,
  "data": [
    {
      "id": "...",
      "employee_email": "...",
      "effective_date": "2025-01-01",
      "change_type": "salary_adjustment",
      "previous_value": "5000",
      "new_value": "5500",
      "change_amount": 500,
      "change_percentage": 10.0,
      "reason": "Annual increment",
      ...
    }
  ]
}
```

## Rollback (if needed)
If you need to rollback the changes:
```sql
-- Remove the added columns
ALTER TABLE public.employee_history
  DROP COLUMN IF EXISTS effective_date,
  DROP COLUMN IF EXISTS change_type,
  DROP COLUMN IF EXISTS change_amount,
  DROP COLUMN IF EXISTS change_percentage,
  DROP COLUMN IF EXISTS employee_name,
  DROP COLUMN IF EXISTS created_by;

-- Remove the indexes
DROP INDEX IF EXISTS idx_employee_history_effective_date;
DROP INDEX IF EXISTS idx_employee_history_email_effective;
```

**Note:** Only rollback if there's a critical issue. The added columns are designed to be backward compatible.

## Troubleshooting

### Issue: Migration fails with "column already exists"
**Solution:** This is fine! It means the column already exists. The migration uses `ADD COLUMN IF NOT EXISTS` so it's safe to run multiple times.

### Issue: Still seeing the error after migration
**Solution:**
1. Verify the migration was applied: Check `information_schema.columns` as shown above
2. Restart your application to clear any cached schema information
3. Check you're connected to the correct database (staging vs production)

### Issue: Data not appearing in salary history
**Solution:**
1. Check if the `employee_history` table has any records: `SELECT COUNT(*) FROM employee_history WHERE change_type IN ('salary_adjustment', 'promotion', 'increment');`
2. The endpoint filters for specific change types - make sure records have appropriate `change_type` values
3. Check that `effective_date` is populated for salary history records

## Support
If you continue to experience issues:
1. Check the application logs for detailed error messages
2. Verify your Supabase connection settings
3. Ensure the migration was applied to the correct schema/database
4. Create a GitHub issue with the error details
