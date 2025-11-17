# Leave Requests Fetch Fix Documentation

## Problem

The application was throwing the following error when trying to fetch leave requests:

```
Error fetching leave requests: {
  'code': 'PGRST200', 
  'details': "Searched for a foreign key relationship between 'leave_requests' and 'employees' in the schema 'public', but no matches were found.",
  'hint': "Perhaps you meant 'user_logins' instead of 'employees'.",
  'message': "Could not find a relationship between 'leave_requests' and 'employees' in the schema cache"
}
```

## Root Cause

The code was using PostgREST's join syntax:

```python
response = supabase.table("leave_requests").select("*, employees(full_name, email)")
```

This syntax requires a foreign key relationship between the `leave_requests` and `employees` tables to be defined in the database. While the `leave_requests` table has an `employee_id` column, the foreign key constraint linking it to `employees(id)` was either missing or not properly configured.

## Solution

Rather than requiring a database schema change, the fix implements application-level data merging:

### Before (Problematic Code)

```python
@app.get("/api/admin/leave-requests")
async def get_all_leave_requests():
    try:
        response = supabase.table("leave_requests").select("*, employees(full_name, email)").order("created_at", desc=True).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        print(f"Error fetching leave requests: {str(e)}")
        return {"success": False, "message": str(e)}
```

### After (Fixed Code)

```python
@app.get("/api/admin/leave-requests")
async def get_all_leave_requests():
    try:
        # Fetch leave requests without join
        response = supabase.table("leave_requests").select("*").order("created_at", desc=True).execute()
        
        if not response.data:
            return {"success": True, "data": []}
        
        leave_requests = response.data
        
        # Get unique employee emails
        employee_emails = list(set([lr.get("employee_email") for lr in leave_requests if lr.get("employee_email")]))
        
        # Fetch employee data separately
        employee_map = {}
        if employee_emails:
            employees_response = supabase.table("employees").select("email, full_name").in_("email", employee_emails).execute()
            if employees_response.data:
                employee_map = {emp["email"]: emp for emp in employees_response.data}
        
        # Merge employee data into leave requests
        for lr in leave_requests:
            employee_email = lr.get("employee_email")
            if employee_email and employee_email in employee_map:
                lr["employees"] = employee_map[employee_email]
            lr["email"] = employee_email
        
        return {"success": True, "data": leave_requests}
    except Exception as e:
        print(f"Error fetching leave requests: {str(e)}")
        return {"success": False, "message": str(e)}
```

## Key Benefits

1. **No Database Changes Required**: The fix works without modifying the database schema or adding foreign key constraints
2. **Performance Optimized**: Uses a single query to fetch all employee data (not N+1 queries)
3. **Backward Compatible**: The response format matches frontend expectations with the nested `employees` object
4. **Handles Edge Cases**: Gracefully handles empty results, missing emails, and employees not found
5. **Minimal Code Changes**: Only 2 functions modified in the entire codebase

## Frontend Compatibility

The frontend code expects this structure:

```javascript
request.employees?.full_name || request.email || '-'
```

The fix provides:
- `request.employees.full_name` - Employee's full name (if found)
- `request.email` - Employee's email as fallback

This ensures the frontend continues to work without any changes.

## Similar Fix Applied

The same pattern was also fixed in the bonuses endpoint:

```python
# Before
response = supabase.table("bonuses").select("*, employees(full_name, email)")

# After
response = supabase.table("bonuses").select("*")
```

Note: The bonuses table already has an `employee_name` field, so no additional merging was needed.

## Testing

To verify the fix works:

1. Start the web application: `python web_app.py`
2. Navigate to the admin dashboard
3. Click on "Leave Approval" tab
4. Verify leave requests load without errors
5. Verify employee names are displayed correctly

## Alternative Solutions Not Chosen

### Option 1: Add Foreign Key Constraint (Not Chosen)
```sql
ALTER TABLE public.leave_requests 
ADD CONSTRAINT fk_leave_requests_employee 
FOREIGN KEY (employee_id) REFERENCES public.employees(id) ON DELETE CASCADE;
```

**Why not chosen**: 
- Requires database schema changes
- May fail if data integrity issues exist
- Not a minimal change approach
- User may not have database admin access

### Option 2: Change Frontend Code (Not Chosen)
Update frontend to not expect nested `employees` object.

**Why not chosen**:
- Requires frontend code changes
- More extensive testing needed
- Not a minimal change approach

## Future Considerations

If you do want to add the foreign key relationship in the future for better data integrity:

1. Ensure all `leave_requests.employee_id` values exist in `employees.id`
2. Run the ALTER TABLE command from Option 1 above
3. The application will continue to work with the current code
4. You could optionally revert to using PostgREST join syntax, but it's not necessary

## Files Modified

- `web_app.py`:
  - `get_all_leave_requests()` (line 340)
  - `get_all_bonuses()` (line 546)

## Related Documentation

- [Supabase PostgREST Resource Embedding](https://postgrest.org/en/stable/api.html#resource-embedding)
- [Foreign Key Relationships in PostgreSQL](https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-FK)
