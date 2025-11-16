# Placeholder Implementation Checklist

This document lists all "coming soon..." placeholders and missing functionality in the web interface that need to be implemented.

## Current Status Summary

**Total Placeholders Found:** 9 sections with "coming soon..." text

### Priority Levels
- 🔴 **HIGH** - Core functionality, frequently used
- 🟡 **MEDIUM** - Important but less critical
- 🟢 **LOW** - Nice to have, less frequently used

---

## Admin Dashboard Placeholders

### 1. Payroll Tab - Skipped Payroll Subtab
**Location:** `web/templates/admin_dashboard.html` (Line 603)

**Current State:**
```html
<div id="payrollSkippedSubtab" class="subtab-content">
    <h3>Skipped Payroll</h3>
    <p>Skipped payroll records coming soon...</p>
</div>
```

**What Needs Implementation:**
- Display table of employees with skipped payroll records
- Show reason for skipping (unpaid leave, on hold, etc.)
- Filter by month/year
- Option to include in next payroll run
- Export to CSV

**Desktop GUI Reference:** `gui/admin_payroll_tab.py` - has skipped payroll tracking

**Priority:** 🟡 MEDIUM

**Backend API Needed:**
- `GET /api/admin/payroll/skipped` - List skipped records
- `POST /api/admin/payroll/skipped/{id}/include` - Include in next run

---

### 2. Payroll Tab - View Contributions Subtab
**Location:** `web/templates/admin_dashboard.html` (Line 609)

**Current State:**
```html
<div id="payrollContributionsSubtab" class="subtab-content">
    <h3>View Contributions</h3>
    <p>EPF, SOCSO, and EIS contributions coming soon...</p>
</div>
```

**What Needs Implementation:**
- Detailed EPF contributions breakdown (employee + employer)
- SOCSO contributions details
- EIS contributions details
- Filter by employee, month, year
- Show citizen vs non-citizen rates
- Export detailed contribution report
- **Upload PDF functionality for EPF/SOCSO/EIS rate tables** (mentioned by user)

**Desktop GUI Reference:** `gui/admin_payroll_tab.py` (Lines 362-371) - Has PDF upload buttons:
```python
epf_upload_button = QPushButton("Upload EPF Rate PDF")
socso_upload_button = QPushButton("Upload SOCSO Rate PDF")
eis_upload_button = QPushButton("Upload EIS Rate PDF")
```

**Priority:** 🔴 HIGH (User specifically mentioned this)

**Backend API Needed:**
- `GET /api/admin/contributions?month=&year=&employee_id=` - Get contribution details
- `POST /api/admin/contributions/upload-rates` - Upload PDF with rate tables
- `GET /api/admin/contributions/rates` - Get current rates

**Implementation Notes:**
- Need file upload component
- PDF parsing functionality already exists in `services/epf_pdf_parser.py`
- Should integrate with existing `upload_and_parse_epf_pdf` function

---

### 3. Payroll Tab - Variable % Subtab
**Location:** `web/templates/admin_dashboard.html` (Line 621)

**Current State:**
```html
<div id="payrollVariableSubtab" class="subtab-content">
    <h3>📊 Variable %</h3>
    <p>Variable percentage configuration coming soon...</p>
</div>
```

**What Needs Implementation:**
- Configure variable percentage bonuses
- Set percentage per employee or department
- Monthly/quarterly/annual variable pay settings
- Performance-based percentage calculations
- History of variable percentage changes

**Desktop GUI Reference:** `gui/admin_payroll_tab.py` - has variable percentage logic

**Priority:** 🔴 HIGH (User specifically mentioned this)

**Backend API Needed:**
- `GET /api/admin/variable-percentage` - Get all configurations
- `POST /api/admin/variable-percentage` - Create new config
- `PUT /api/admin/variable-percentage/{id}` - Update config
- `DELETE /api/admin/variable-percentage/{id}` - Delete config

---

### 4. Salary History Tab
**Location:** `web/templates/admin_dashboard.html` (Line 738)

**Current State:**
```html
<div id="salaryHistoryTab" class="tab-pane">
    <h2>📈 Salary History</h2>
    <p>Salary history management coming soon...</p>
</div>
```

**What Needs Implementation:**
- View salary history for all employees
- Track salary changes over time
- Show effective dates
- Filter by employee, date range
- Add/edit salary history records
- Export salary history report
- Visualize salary trends (charts)

**Desktop GUI Reference:** `gui/admin_salary_history_tab.py`

**Priority:** 🟡 MEDIUM

**Backend API Needed:**
- `GET /api/admin/salary-history?employee_id=` - Get salary history
- `POST /api/admin/salary-history` - Add salary change record
- `PUT /api/admin/salary-history/{id}` - Update record

---

### 5. Engagements Tab - Submit Subtab
**Location:** `web/templates/admin_dashboard.html` (Line 754)

**Current State:**
```html
<div id="engagementsSubmitSubtab" class="subtab-content active">
    <h3>Submit New Engagement</h3>
    <p>Submit training, courses, trips, or work assignments coming soon...</p>
</div>
```

**What Needs Implementation:**
- Form to submit new training/course
- Form to submit overseas work trips
- Employee selection (multiple employees)
- Date range selection
- Location/venue input
- Cost/budget tracking
- Approval workflow

**Desktop GUI Reference:** 
- `gui/employee_training_course_tab.py`
- `gui/employee_overseas_work_trip_tab.py`

**Priority:** 🟡 MEDIUM

**Backend API Needed:**
- `POST /api/admin/engagements/training` - Submit training
- `POST /api/admin/engagements/trip` - Submit trip
- Existing: `/api/engagements/{employee_id}` for viewing

---

### 6. Engagements Tab - View All Subtab
**Location:** `web/templates/admin_dashboard.html` (Line 760)

**Current State:**
```html
<div id="engagementsViewSubtab" class="subtab-content">
    <h3>All Engagements</h3>
    <p>View all training, courses, trips, and work assignments coming soon...</p>
</div>
```

**What Needs Implementation:**
- List all engagements across all employees
- Filter by type (training, trip, course)
- Filter by date range
- Filter by employee
- Sort by various fields
- Export to CSV
- View details modal

**Desktop GUI Reference:** Same as above

**Priority:** 🟡 MEDIUM

**Backend API Needed:**
- `GET /api/admin/engagements/all?type=&from_date=&to_date=` - Get all engagements

---

### 7. Employment History Tab
**Location:** `web/templates/admin_dashboard.html` (Line 846)

**Current State:**
```html
<div id="employeeHistoryTab" class="tab-pane">
    <h2>🧾 Employment History</h2>
    <p>Employment history management coming soon...</p>
</div>
```

**What Needs Implementation:**
- View employment history for all employees
- Track position changes, transfers
- Department changes history
- Status changes (Active, Terminated, etc.)
- Filter by employee
- Timeline view of changes
- Export employment history

**Desktop GUI Reference:** `gui/employee_history_tab.py`, `gui/employee_history_dialog.py`

**Priority:** 🟢 LOW

**Backend API Needed:**
- `GET /api/admin/employment-history?employee_id=` - Get history
- `POST /api/admin/employment-history` - Add history record

---

## Employee Dashboard Placeholders

### 8. Engagements Tab - Submit Subtab (Employee)
**Location:** `web/templates/dashboard.html` (Line 321)

**Current State:**
```html
<div id="engagementsSubmitSubtab" class="subtab-content active">
    <h3>Submit New Engagement</h3>
    <p>Submit training, courses, trips, or work assignments coming soon...</p>
</div>
```

**What Needs Implementation:**
- Employee can request training
- Employee can request to attend course
- Employee can log work trips
- Submit for approval
- Attach documents/certificates

**Desktop GUI Reference:** `gui/employee_training_course_tab.py`

**Priority:** 🟡 MEDIUM

**Backend API Needed:**
- `POST /api/employee/engagements/request` - Submit request

---

### 9. Engagements Tab - View My Engagements (Employee)
**Location:** `web/templates/dashboard.html` (Line 327)

**Current State:**
```html
<div id="engagementsViewSubtab" class="subtab-content">
    <h3>My Engagements</h3>
    <p>View your training, courses, trips, and work assignments coming soon...</p>
</div>
```

**What Needs Implementation:**
- View personal engagement history
- Filter by type and date
- See approval status
- Download certificates
- Export personal training record

**Desktop GUI Reference:** `gui/employee_training_course_tab.py`

**Priority:** 🟡 MEDIUM

**Backend API Needed:**
- Already exists: `GET /api/engagements/{employee_id}`

---

## Additional Missing Features (Not Placeholder Text, But Missing Functionality)

### 10. Edit Employee Functionality
**Location:** Admin Dashboard - Employees Tab

**Current State:**
- Employee table shows data but has NO edit buttons
- Function `buildEmployeeTable` in `admin_dashboard.js` (Line 64) doesn't include action buttons

**What Needs Implementation:**
- Add "Edit" button to each row in employee table
- Create employee edit modal/form
- Update employee information
- Save changes to database

**Desktop GUI Reference:** `gui/employee_profile_dialog.py` - Full edit dialog

**Priority:** 🔴 HIGH (User specifically mentioned this)

**Backend API Needed:**
- `PUT /api/admin/employees/{id}` - Update employee
- May already exist, need to verify

**Implementation Plan:**
1. Modify `buildEmployeeTable()` to add action column with edit button
2. Create modal form similar to "Add Employee" form
3. Pre-populate form with existing employee data
4. Connect to update API endpoint

---

### 11. Leave Types Configuration (Partially Implemented)
**Location:** Admin Dashboard - Leave Tab - Configuration Subtab

**Current State:**
- UI exists with tables and forms (Lines 436-525)
- JavaScript functions referenced: `closeLeaveTypeModal()`, `addLeaveTypeBtn`, etc.
- But functionality may not be fully wired up

**What Needs Verification:**
- Check if `leave_config.js` has complete implementation
- Verify CRUD operations work
- Test form submissions

**Desktop GUI Reference:** `gui/leave_types_editor.py`, `gui/leave_caps_editor.py`

**Priority:** 🟡 MEDIUM

---

### 12. LHDN Tax Configuration (Partially Implemented)
**Location:** Admin Dashboard - Payroll Tab - LHDN Tax Subtab

**Current State:**
- UI exists with full forms and tables (Lines 625-726)
- JavaScript functions: `addTaxBracket()`, `editAllReliefs()`, `addReliefOverride()`
- `lhdn_config.js` file exists with tax rate data

**What Needs Verification:**
- Check if backend APIs are connected
- Verify data saves to database
- Test all CRUD operations

**Desktop GUI Reference:** `gui/lhdn_tax_config_tab.py`

**Priority:** 🟡 MEDIUM (UI exists, may just need backend hookup)

---

## Implementation Priority Order

### Immediate Priority (🔴 HIGH)
1. **Edit Employee** - Most basic admin function
2. **View Contributions** with **PDF Upload for Rates** - User specifically mentioned
3. **Variable Percentage Configuration** - User specifically mentioned

### Next Priority (🟡 MEDIUM)
4. Skipped Payroll management
5. Salary History tracking
6. Engagements (Training/Trips) submission and viewing
7. Verify LHDN Tax Configuration backend
8. Verify Leave Types Configuration backend

### Lower Priority (🟢 LOW)
9. Employment History tracking

---

## Notes for Implementation

1. **Existing Backend Functions**: Many backend functions already exist in `services/supabase_service.py`. Check before creating new ones.

2. **Desktop GUI Reference**: All desktop features are in `gui/` directory. Use as reference for:
   - Field requirements
   - Validation rules
   - Business logic
   - API calls

3. **Reusable Components**: Consider creating:
   - Employee selector component (used in multiple places)
   - Date range picker component
   - File upload component (for PDFs)
   - Data table component with sorting/filtering

4. **API Endpoints**: Check `web_app.py` for existing endpoints before adding new ones.

5. **JavaScript Files**: 
   - Some functionality may be partially implemented in JS files
   - Check before marking as completely missing

6. **Testing**: Each implemented feature should be tested:
   - Form validation
   - API integration
   - Error handling
   - Success feedback to user

---

## User's Specific Requests

From user comment: "@copilot first of all, i want you to check all this 'coming soon' or placeholder html that needed to be added"

User wants:
1. ✅ List of all placeholders - PROVIDED ABOVE
2. Edit employee functionality - **MISSING**
3. Fixed percentage (contribution rates) - **MISSING** 
4. Variable percentage - **MISSING**
5. Upload PDF for EPF, SOCSO, EIS fixed rates - **MISSING**

---

## Next Steps

1. Prioritize based on user's specific mentions:
   - Edit Employee
   - Contributions view with PDF upload
   - Variable percentage

2. For each feature:
   - Design the UI/form
   - Identify backend API needs
   - Implement frontend
   - Connect to backend
   - Test thoroughly

3. Remove "coming soon..." text only after feature is fully implemented and tested.
