# Calendar Replace Feature

## Overview
Added ability to replace existing holidays when importing Malaysia public holidays, allowing users to switch between states or update outdated holiday data.

## Date
2025-11-24

## Changes Made

### 1. New Service Function
**File**: `services/supabase_service.py:323`

```python
def delete_calendar_holidays_for_year(year: int, state: str = None) -> int:
    """
    Delete all calendar holidays for a specific year and optionally a state.
    Returns the number of holidays deleted.
    """
```

**Features:**
- Deletes holidays for a specific year
- Optional state filtering
- Returns count of deleted holidays
- Safe: Uses existing `delete_calendar_holiday_by_id()` function

### 2. Enhanced Import Endpoint
**File**: `web_app.py:2247`

**New parameter:** `replace: bool = False`

```python
@app.post("/api/holidays/import-malaysia")
async def import_malaysia_holidays(
    year: int, 
    state: Optional[str] = None, 
    replace: bool = False  # NEW
):
```

## Usage Examples

### Example 1: Import Without Replacement (Default)
**Request:**
```http
POST /api/holidays/import-malaysia?year=2025&state=Selangor
```

**Behavior:**
- Adds new holidays
- Skips duplicates
- Keeps existing holidays

**Response:**
```json
{
  "success": true,
  "message": "Imported 5 holidays, skipped 12 duplicates",
  "data": {
    "deleted": 0,
    "imported": 5,
    "skipped": 12,
    "errors": []
  }
}
```

### Example 2: Import With Replacement
**Request:**
```http
POST /api/holidays/import-malaysia?year=2025&state=Selangor&replace=true
```

**Behavior:**
1. Deletes all existing holidays for 2025 in Selangor
2. Imports fresh holiday data
3. Reports deleted and imported counts

**Response:**
```json
{
  "success": true,
  "message": "Replaced 15 existing holidays. Imported 17 new holidays, skipped 0 duplicates",
  "data": {
    "deleted": 15,
    "imported": 17,
    "skipped": 0,
    "errors": []
  }
}
```

### Example 3: Replace National Holidays
**Request:**
```http
POST /api/holidays/import-malaysia?year=2025&replace=true
```

**Behavior:**
- Deletes all national holidays for 2025
- Imports fresh national holiday data
- Does not affect state-specific holidays

### Example 4: Switch States
**Scenario:** User previously imported Johor holidays, now wants Selangor

**Step 1:** Delete old state
```http
POST /api/holidays/import-malaysia?year=2025&state=Johor&replace=true
```

**Step 2:** Import new state
```http
POST /api/holidays/import-malaysia?year=2025&state=Selangor&replace=false
```

Or in one call:
```http
POST /api/holidays/import-malaysia?year=2025&state=Selangor&replace=true
```

## Use Cases

### 1. Update Outdated Holidays
When holiday dates change or new holidays are announced:
```
replace=true
```

### 2. Switch Between States
When company relocates or user wants different state:
```
replace=true with new state parameter
```

### 3. Refresh Calendar Data
To ensure latest holiday information:
```
replace=true
```

### 4. Add New Holidays (Default)
Normal operation, doesn't affect existing data:
```
replace=false (or omit parameter)
```

## State Filtering Logic

When `state` parameter is provided:
- Deletes holidays where `state` matches OR `state IS NULL` (national)
- This ensures state-specific holidays are replaced along with national ones
- Holidays from other states remain untouched

When `state` is `None` or `'All Malaysia'`:
- Only deletes/updates national holidays
- State-specific holidays are not affected

## Backward Compatibility

✅ **Fully backward compatible**
- `replace=False` by default
- Existing API calls work unchanged
- No breaking changes to current behavior

## Response Format

The response now includes a `deleted` field:

```json
{
  "success": true,
  "message": "...",
  "data": {
    "deleted": 15,     // NEW: Number of holidays deleted (0 if replace=false)
    "imported": 17,    // Number of new holidays added
    "skipped": 0,      // Number of duplicate holidays skipped
    "errors": []       // Any errors during import
  }
}
```

## Technical Details

### Delete Function Implementation
```python
def delete_calendar_holidays_for_year(year: int, state: str = None) -> int:
    # 1. Find holidays matching year and state
    holidays_to_delete = find_calendar_holidays_for_year(year, state=state)
    
    # 2. Delete each holiday by ID
    for holiday in holidays_to_delete:
        delete_calendar_holiday_by_id(holiday['id'])
    
    # 3. Return count
    return deleted_count
```

### Import Flow With Replace
```python
# 1. Delete existing if replace=True
if replace:
    deleted_count = delete_calendar_holidays_for_year(year, state)

# 2. Fetch holiday data
holidays_set = get_holidays_for_year(year, state)

# 3. Import new holidays
for holiday in holidays_set:
    insert_calendar_holiday(...)
```

## Testing

### Manual Test
```bash
# 1. Import holidays
curl -X POST "http://localhost:8000/api/holidays/import-malaysia?year=2025&state=Selangor"

# 2. Replace with new data
curl -X POST "http://localhost:8000/api/holidays/import-malaysia?year=2025&state=Selangor&replace=true"

# 3. Verify deleted count in response
```

### Expected Behavior
- First call: Imports holidays
- Second call with `replace=true`: Deletes and re-imports
- Response shows `deleted` count matching first import count

## Error Handling

- If table doesn't exist: Returns 0 deleted
- If no holidays to delete: Returns 0 deleted
- If delete fails: Continues with remaining holidays
- All errors are logged and returned in `errors` array

## Security Considerations

✅ No SQL injection risk (uses parameterized queries)
✅ No authorization required (same as existing import)
✅ Limited to year range 1900-2100
✅ State parameter is sanitized

## Future Enhancements

Potential improvements:
1. Add confirmation prompt in UI for replace operation
2. Add undo/backup functionality
3. Add batch import for multiple years
4. Add audit log for deletions

## Related Files

- `services/supabase_service.py` - Backend logic
- `web_app.py` - API endpoint
- `core/holidays_service.py` - Holiday data source
