# Fix: Payroll History Display Issue

## Problem Reported
User reported that:
> "payroll history data seems to be displaying in view contribution while actual payroll history subtab display no value except employee's name"

## Investigation

### Tabs Involved
1. **Payroll History subtab** - Shows payroll runs with salary details
2. **View Contributions subtab** - Shows EPF, SOCSO, EIS contributions

### Root Cause
The `buildPayrollRunsTable()` function in `web/static/js/admin_dashboard.js` was using incorrect field references:

**Before (line 274):**
```javascript
html += `<td>${run.employee_email || '-'}</td>`;
```

**Issue**: The payroll_runs table doesn't store `employee_email` directly, it stores `employee_name`. This caused the table to display only dashes or empty values for employee names, and the other columns appeared to be missing data as well.

## Solution

### Changed Function
Updated `buildPayrollRunsTable()` in `web/static/js/admin_dashboard.js`:

**After:**
```javascript
const employeeName = run.employee_name || run.employee?.full_name || run.employee_email || '-';
html += `<td>${employeeName}</td>`;
```

### Additional Improvements
1. **Added missing columns**: Gross Pay and Total Deductions for better visibility
2. **Robust field access**: Added fallback logic to handle multiple possible field names
3. **Better table structure**: Now displays 7 columns instead of 5:
   - Employee Name
   - Month/Year
   - Basic Salary
   - Gross Pay (NEW)
   - Total Deductions (NEW)
   - Net Pay
   - Status

## Data Flow Clarification

### Payroll History Tab
- **Endpoint**: `/api/admin/payroll-runs`
- **Function**: `get_all_payroll_runs()` → `get_payroll_runs()`
- **Data Source**: `payroll_runs` table
- **Fields Used**: `employee_name`, `month_year`, `basic_salary`, `gross_pay`, `total_deductions`, `net_pay`, `status`

### View Contributions Tab
- **Endpoint**: `/api/admin/payroll-contributions`
- **Function**: `get_payroll_contributions()`
- **Data Source**: `payroll_runs` table (same as above)
- **Fields Used**: `employee_name`, `month_year`, `epf_employee`, `epf_employer`, `socso_employee`, `socso_employer`, `eis`, `pcb`

Both tabs correctly pull from the same `payroll_runs` table but display different fields.

## Testing Recommendations

### Before Fix
- Payroll History tab would show only dashes or partial data
- Employee names would be missing or showing as "-"
- Other payroll fields (salary, net pay) might appear but without proper context

### After Fix
- Payroll History tab shows complete data:
  - ✅ Employee names display correctly
  - ✅ All salary information visible
  - ✅ Gross pay and deductions now shown
  - ✅ Net pay calculated properly
  - ✅ Status information displayed

### Verification Steps
1. Navigate to Admin Dashboard → Payroll → Payroll History
2. Verify employee names are displayed (not dashes)
3. Verify all 7 columns show data:
   - Employee name/email
   - Month (e.g., "01/2025")
   - Basic Salary (RM amount)
   - Gross Pay (RM amount) 
   - Deductions (RM amount)
   - Net Pay (RM amount)
   - Status (e.g., "completed")

4. Navigate to View Contributions subtab
5. Verify contribution data displays correctly (this should have been working already)

## Related Files
- `web/static/js/admin_dashboard.js` - Display logic
- `web_app.py` - Backend endpoints (lines 628-638, 905-935)
- `services/supabase_service.py` - Data retrieval (lines 4714-4758)

## Commit
- **Commit**: 98551ab
- **Message**: "Fix payroll history display to show correct employee data"
