# Employment History and Payroll History Issues Analysis

**Date:** November 24, 2025

---

## Issues Reported

1. **Employment History (Admin Dashboard)**: Employee and Company columns are empty
2. **Employment History**: Python GUI doesn't have Company column (but HTML does)
3. **Payroll History (Employee Dashboard)**: Basic salary, gross salary, deduction, and net pay columns are empty
4. **Payroll History**: Status showing "pending" instead of "completed"
5. **Payroll History**: Missing payslip download button

---

## Issue 1: Employment History - Empty Employee & Company Columns

### Root Cause

**API Issue:** `/api/admin/employee-history` endpoint (line 1339 in web_app.py)

```python
response = supabase.table("employee_history").select("*").order("start_date", desc=True).limit(200).execute()
```

This query does NOT join with the `employees` table to get employee names. The table only has `employee_id` and `employee_email`, but the JavaScript expects `employee_name`.

### Current JavaScript (lines 2957-2958):
```javascript
html += `<td style="padding: 10px;">${record.employee_name || record.employees?.full_name || record.employee_email || '-'}</td>`;
html += `<td style="padding: 10px;"><strong>${record.company || '-'}</strong></td>`;
```

### Why It's Empty

1. **Employee Column**: `employee_name` field doesn't exist in employee_history table - needs JOIN
2. **Company Column**: `company` field exists but may not have data in database

### Fix Required

Update API to JOIN employees table:

```python
response = supabase.table("employee_history")
    .select("*, employees(full_name, email)")
    .order("start_date", desc=True)
    .limit(200)
    .execute()
```

Then process to flatten:
```python
for record in response.data:
    if 'employees' in record and record['employees']:
        record['employee_name'] = record['employees']['full_name']
```

---

## Issue 2: Python GUI vs HTML - Company Column

### Python GUI Implementation

**File:** `gui/admin_employee_history_tab.py` (needs verification)

The Python GUI likely has:
- Employee selection
- Job title
- Position
- Start/End dates
- Employment type
- Notes

**Company field**: May or may not exist depending on implementation

### HTML Implementation

**Columns:**
1. Employee
2. **Company** ← This column exists
3. Job Title
4. Position
5. Department
6. Type
7. Period
8. Actions

### Analysis

The HTML version has **Company** column which is a valid addition. This is not necessarily wrong - it's an enhancement to track which company/organization the employment history refers to (previous employers, etc.).

**Recommendation**: Keep the Company column - it's useful data. This is an enhancement over Python GUI.

---

## Issue 3 & 4: Payroll History - Empty Columns & Wrong Status

### Root Cause

**API Issue:** `/api/payroll/{employee_id}` endpoint (line 247-258)

Calls `get_employee_payroll_history()` function which queries `payroll_information` table:

```python
result = supabase.table("payroll_information")
    .select("*")
    .eq("employee_id", employee_id)
    .order("month_year", desc=True)
    .execute()
```

### JavaScript Display (lines 215-231 in dashboard.js):

```javascript
function buildPayrollTable(records) {
    let html = '<table><thead><tr>';
    html += '<th>Month</th><th>Basic Salary</th><th>Net Pay</th><th>Status</th><th>Actions</th>';
    html += '</tr></thead><tbody>';
    
    records.forEach(record => {
        html += '<tr>';
        html += `<td>${record.month_year || '-'}</td>`;
        html += `<td>${formatCurrency(record.basic_salary)}</td>`;  // ← May be empty
        html += `<td>${formatCurrency(record.net_pay)}</td>`;       // ← May be empty
        html += `<td>${record.status || '-'}</td>`;                 // ← Shows 'pending'
        html += `<td><button class="btn-primary" onclick="downloadPayslip('${record.id}', '${record.month_year}')">Download PDF</button></td>`;
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    return html;
}
```

### Why Columns Are Empty

**Possible reasons:**

1. **Database schema issue**: `payroll_information` table may not have `basic_salary` and `net_pay` columns
2. **Wrong table**: Should query `payroll_runs` instead of `payroll_information`
3. **Column names mismatch**: Fields might be named differently in database

### Fix Required

**Option 1: Query the correct table**
```python
result = supabase.table("payroll_runs")
    .select("*")
    .eq("employee_id", employee_id)
    .order("month_year", desc=True)
    .execute()
```

**Option 2: Fix the query to get all needed fields**

Check which table has the payroll data and ensure it includes:
- `month_year`
- `basic_salary` (or `base_salary`)
- `gross_salary`
- `total_deductions`
- `net_pay`
- `status`

### Status Showing "Pending"

If `status` field shows "pending", it means:
1. Payroll runs were created but not completed
2. Status field needs to be updated after payroll processing
3. Should show "completed" after successful run

---

## Issue 5: Missing Payslip Download Button

### Analysis

**Good News:** The button EXISTS in the code!

```javascript
html += `<td><button class="btn-primary" onclick="downloadPayslip('${record.id}', '${record.month_year}')">Download PDF</button></td>`;
```

### Why It May Not Be Visible

1. **Table not rendering**: If columns are empty, table might not display properly
2. **CSS issue**: Button might be hidden or not styled
3. **Function missing**: `downloadPayslip()` function needs to be defined

### Check downloadPayslip Function

Looking at line 545-583 in dashboard.js, the function exists:

```javascript
// Global function for payslip download
async function downloadPayslip(payrollRunId, monthYear) {
    try {
        // Get employee ID
        const employeeResponse = await fetch(`/api/employee/${userEmail}`);
        const employeeData = await employeeResponse.json();
        
        if (!employeeData.success || !employeeData.data) {
            alert('Failed to get employee information');
            return;
        }
        
        const employeeId = employeeData.data.id;
        
        // Download payslip PDF
        const response = await fetch(`/api/payroll/payslip/${employeeId}/${payrollRunId}`);
        // ... rest of download logic
    }
}
```

**The function exists and should work!**

### Likely Issue

The button is probably rendering, but:
1. If the table has empty columns, the display looks broken
2. The function uses `record.id` but field might be `record.payroll_run_id` or different

---

## Python GUI Comparison

### Employment History (Python)

Likely has these fields:
- Employee selection
- Job title
- Position/Level
- Start date
- End date
- Employment type
- Department
- Notes

**Company field**: Needs verification if Python GUI has this

### Payroll History (Python)

Python GUI likely shows:
- Month/Year
- Basic salary
- Gross salary
- EPF employee
- EPF employer
- SOCSO employee
- SOCSO employer
- EIS
- PCB (tax)
- Total deductions
- Net pay
- Status
- Payslip generation button

---

## Recommended Fixes

### Fix 1: Employment History API (web_app.py line 1339)

```python
@app.get("/api/admin/employee-history")
async def get_employee_history():
    """
    Get complete employment/re-employment history (previous jobs, companies, positions)
    """
    try:
        # Join with employees table to get names
        response = supabase.table("employee_history")\
            .select("*, employees(full_name, email)")\
            .order("start_date", desc=True)\
            .limit(200)\
            .execute()
        
        if not response.data:
            return {"success": True, "data": []}
        
        # Flatten the employee data
        records = []
        for record in response.data:
            if 'employees' in record and record['employees']:
                record['employee_name'] = record['employees']['full_name']
                # Remove nested object
                del record['employees']
            records.append(record)
        
        return {"success": True, "data": records}
    except Exception as e:
        print(f"Error getting employee history: {str(e)}")
        return {"success": False, "message": str(e)}
```

### Fix 2: Payroll History Query (services/supabase_service.py line 6500)

```python
def get_employee_payroll_history(employee_id: str) -> List[Dict]:
    """Get payroll history for an employee"""
    try:
        # Query payroll_runs table instead of payroll_information
        result = supabase.table("payroll_runs")\
            .select("*")\
            .eq("employee_id", employee_id)\
            .order("month_year", desc=True)\
            .execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        print(f"DEBUG: Error loading payroll history: {e}")
        return []
```

Or if using payroll_information, ensure all fields are present:
```python
def get_employee_payroll_history(employee_id: str) -> List[Dict]:
    """Get payroll history for an employee"""
    try:
        result = supabase.table("payroll_information")\
            .select("id, employee_id, month_year, base_salary, gross_salary, total_deductions, net_pay, status, created_at")\
            .eq("employee_id", employee_id)\
            .order("month_year", desc=True)\
            .execute()
        
        # Map field names if different
        records = []
        for record in result.data or []:
            records.append({
                'id': record.get('id'),
                'employee_id': record.get('employee_id'),
                'month_year': record.get('month_year'),
                'basic_salary': record.get('base_salary') or record.get('basic_salary'),
                'gross_salary': record.get('gross_salary'),
                'total_deductions': record.get('total_deductions'),
                'net_pay': record.get('net_pay'),
                'status': record.get('status', 'completed'),  # Default to completed
                'created_at': record.get('created_at')
            })
        
        return records
        
    except Exception as e:
        print(f"DEBUG: Error loading payroll history: {e}")
        return []
```

### Fix 3: Update Payroll Table Display (dashboard.js)

Add more columns to match Python GUI:

```javascript
function buildPayrollTable(records) {
    let html = '<table><thead><tr>';
    html += '<th>Month</th>';
    html += '<th>Basic Salary</th>';
    html += '<th>Gross Salary</th>';
    html += '<th>Deductions</th>';
    html += '<th>Net Pay</th>';
    html += '<th>Status</th>';
    html += '<th>Actions</th>';
    html += '</tr></thead><tbody>';
    
    records.forEach(record => {
        html += '<tr>';
        html += `<td>${record.month_year || '-'}</td>`;
        html += `<td>${formatCurrency(record.basic_salary || record.base_salary)}</td>`;
        html += `<td>${formatCurrency(record.gross_salary)}</td>`;
        html += `<td>${formatCurrency(record.total_deductions)}</td>`;
        html += `<td><strong>${formatCurrency(record.net_pay)}</strong></td>`;
        
        // Status badge
        const statusClass = record.status === 'completed' ? 'success' : 'pending';
        html += `<td><span class="badge ${statusClass}">${record.status || 'completed'}</span></td>`;
        
        // Actions - Download payslip
        html += '<td>';
        html += `<button class="btn-primary btn-sm" onclick="downloadPayslip('${record.id}', '${record.month_year}')">`;
        html += '📄 Download Payslip</button>';
        html += '</td>';
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    return html;
}
```

---

## Summary

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| **Employment History - Empty Employee** | API doesn't JOIN employees table | Add JOIN in API |
| **Employment History - Empty Company** | Database may not have data | Data issue, not code |
| **Employment History - Company Column** | HTML has extra column vs Python | Keep it - it's useful |
| **Payroll - Empty Columns** | Wrong table or missing fields | Query correct table with all fields |
| **Payroll - Wrong Status** | Data or default value issue | Set proper status |
| **Payroll - Missing Button** | Button exists but table broken | Fix will make it visible |

---

## Testing Checklist

After fixes:
- [ ] Employment history shows employee names
- [ ] Employment history shows company names (if data exists)
- [ ] Payroll history shows basic salary
- [ ] Payroll history shows gross salary
- [ ] Payroll history shows deductions
- [ ] Payroll history shows net pay
- [ ] Payroll history shows correct status
- [ ] Payslip download button is visible
- [ ] Payslip download works

---

**Analysis Date:** November 24, 2025  
**Files to Fix:**
1. `web_app.py` - Line 1339 (employee history API)
2. `services/supabase_service.py` - Line 6500 (payroll history query)
3. `web/static/js/dashboard.js` - Line 215 (payroll table display - optional enhancement)
