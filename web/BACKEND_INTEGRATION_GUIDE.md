# Backend Integration Guide for HTML Templates

This document outlines all the backend API endpoints and JavaScript functions that need to be implemented to make the HTML templates fully functional, matching the Python GUI capabilities.

## 🎯 Overview

The HTML templates have **100% UI parity** with the Python GUI (all forms, buttons, tabs, and fields are present). However, they need backend API integration to provide the same functionality.

---

## 📋 Required API Endpoints

### Authentication & Session Management

#### `POST /api/auth/login`
- **Purpose**: Authenticate user credentials
- **Request Body**: `{ email: string, password: string }`
- **Response**: `{ success: boolean, token: string, user: { email, role, full_name } }`
- **Used In**: `login.js`

#### `POST /api/auth/logout`
- **Purpose**: Clear user session
- **Response**: `{ success: boolean }`
- **Used In**: `admin_dashboard.js`, `dashboard.js`

---

### Employee Management (Admin)

#### `GET /api/employees`
- **Purpose**: Fetch all employees
- **Query Params**: `search`, `department`, `religion`
- **Response**: `{ success: boolean, data: Employee[] }`
- **Used In**: Admin Profiles tab
- **TODO**: Implement filtering by search, department, religion

#### `POST /api/employees`
- **Purpose**: Create new employee
- **Request Body**: `{ full_name, email, password, gender, dob, nric, nationality, citizenship, race, religion, marital_status, number_of_children, phone_number, address, city, state, zipcode, employee_id, department, position, role, employment_status, join_date, epf_number, socso_number, income_tax_number }`
- **Response**: `{ success: boolean, message: string, employee_id: string }`
- **Used In**: Admin Profiles tab - Add Employee Form
- **TODO**: Validate all 30+ form fields, hash password, insert into database

#### `PUT /api/employees/:id`
- **Purpose**: Update employee information
- **Request Body**: Employee fields to update
- **Response**: `{ success: boolean, message: string }`
- **Used In**: Admin Profiles tab - Edit Employee

#### `DELETE /api/employees/:id`
- **Purpose**: Delete employee
- **Response**: `{ success: boolean, message: string }`
- **Used In**: Admin Profiles tab

#### `GET /api/employees/export-csv`
- **Purpose**: Export employees to CSV
- **Query Params**: Current filters
- **Response**: CSV file download
- **Used In**: Admin Profiles tab - Export button
- **TODO**: Generate CSV with filtered employee data

---

### Attendance Management

#### `GET /api/attendance/all`
- **Purpose**: Get all attendance records (Admin)
- **Query Params**: `start_date`, `end_date`, `filter_field`, `search_text`
- **Response**: `{ success: boolean, data: AttendanceRecord[] }`
- **Used In**: Admin Attendance tab
- **TODO**: Implement date range and search filtering

#### `GET /api/attendance/my-history`
- **Purpose**: Get employee's own attendance history
- **Query Params**: `employee_email`
- **Response**: `{ success: boolean, data: AttendanceRecord[] }`
- **Used In**: Employee Attendance tab

#### `POST /api/attendance/clock-in`
- **Purpose**: Record clock-in time
- **Request Body**: `{ employee_email: string }`
- **Response**: `{ success: boolean, message: string, clock_in_time: timestamp }`
- **Used In**: Employee Attendance tab - Clock In button
- **TODO**: Validate clock-in limit, check if already clocked in today

#### `POST /api/attendance/clock-out`
- **Purpose**: Record clock-out time
- **Request Body**: `{ employee_email: string }`
- **Response**: `{ success: boolean, message: string, clock_out_time: timestamp }`
- **Used In**: Employee Attendance tab - Clock Out button
- **TODO**: Validate clock-out time, update today's record

#### `GET /api/attendance/settings`
- **Purpose**: Get working hours settings
- **Response**: `{ success: boolean, data: { work_start, work_end, clock_in_limit } }`
- **Used In**: Admin Attendance tab - Working Hours Settings

#### `PUT /api/attendance/settings`
- **Purpose**: Update working hours settings
- **Request Body**: `{ work_start: string, work_end: string, clock_in_limit: string }`
- **Response**: `{ success: boolean, message: string }`
- **Used In**: Admin Attendance tab - Save Working Hours button
- **TODO**: Validate time formats, update settings in database

#### `GET /api/attendance/export-csv`
- **Purpose**: Export attendance records to CSV
- **Query Params**: Date range and filters
- **Response**: CSV file download
- **Used In**: Admin Attendance tab - Export button

---

### Leave Management

#### `GET /api/leaves/pending` (Admin)
- **Purpose**: Get pending leave requests
- **Response**: `{ success: boolean, data: LeaveRequest[] }`
- **Used In**: Admin Leave tab - Pending subtab

#### `GET /api/leaves/history` (Admin)
- **Purpose**: Get approved/rejected leave history
- **Response**: `{ success: boolean, data: LeaveRequest[] }`
- **Used In**: Admin Leave tab - Approved/Rejected subtab

#### `GET /api/leaves/my-requests`
- **Purpose**: Get employee's leave requests
- **Query Params**: `employee_email`
- **Response**: `{ success: boolean, data: LeaveRequest[] }`
- **Used In**: Employee Leave tab - My Leave Requests subtab

#### `POST /api/leaves/submit`
- **Purpose**: Submit new leave request
- **Request Body**: `{ employee_email, leave_type, start_date, end_date, reason, days_count }`
- **Response**: `{ success: boolean, message: string, request_id: string }`
- **Used In**: Admin/Employee Leave tab - Submit Request subtab
- **TODO**: Validate dates, calculate days, check balance

#### `PUT /api/leaves/:id/approve`
- **Purpose**: Approve leave request
- **Request Body**: `{ approver_email: string, comments: string }`
- **Response**: `{ success: boolean, message: string }`
- **Used In**: Admin Leave tab - Pending subtab

#### `PUT /api/leaves/:id/reject`
- **Purpose**: Reject leave request
- **Request Body**: `{ approver_email: string, reason: string }`
- **Response**: `{ success: boolean, message: string }`
- **Used In**: Admin Leave tab - Pending subtab

#### `GET /api/leaves/balance/:employee_email`
- **Purpose**: Get leave balances
- **Response**: `{ success: boolean, data: { annual: number, sick: number, unpaid: number } }`
- **Used In**: Admin Leave tab - Balance subtabs

#### `GET /api/leaves/calendar`
- **Purpose**: Get calendar view of leaves
- **Query Params**: `year`, `month`
- **Response**: `{ success: boolean, data: CalendarEvent[] }`
- **Used In**: Admin Leave tab - Calendar subtab

---

### Payroll Management

#### `GET /api/payroll/history`
- **Purpose**: Get payroll history
- **Query Params**: `year`, `month`, `employee_id` (for admin)
- **Response**: `{ success: boolean, data: PayrollRecord[] }`
- **Used In**: Admin/Employee Payroll tab - Month subtabs
- **TODO**: Implement month filtering (All, Jan-Dec)

#### `POST /api/payroll/run`
- **Purpose**: Run payroll for a month
- **Request Body**: `{ year: number, month: number, employee_ids: string[] }`
- **Response**: `{ success: boolean, message: string, processed_count: number }`
- **Used In**: Admin Payroll tab - Payroll History subtab
- **TODO**: Calculate salaries, deductions, EPF, SOCSO, tax

#### `GET /api/payroll/skipped`
- **Purpose**: Get skipped payroll records
- **Response**: `{ success: boolean, data: SkippedPayroll[] }`
- **Used In**: Admin Payroll tab - Skipped Payroll subtab

#### `GET /api/payroll/contributions`
- **Purpose**: Get EPF/SOCSO contributions
- **Query Params**: `year`, `month`
- **Response**: `{ success: boolean, data: ContributionRecord[] }`
- **Used In**: Admin Payroll tab - View Contributions subtab

#### `GET /api/payroll/bonuses`
- **Purpose**: Get bonus records
- **Response**: `{ success: boolean, data: BonusRecord[] }`
- **Used In**: Admin Payroll tab - Bonuses subtab

#### `POST /api/payroll/bonuses`
- **Purpose**: Add bonus
- **Request Body**: `{ employee_id, bonus_type, amount, month, year }`
- **Response**: `{ success: boolean, message: string }`
- **Used In**: Admin Payroll tab - Bonuses subtab

#### `GET /api/payroll/variable-percentage`
- **Purpose**: Get variable percentage settings
- **Response**: `{ success: boolean, data: VariablePercentage[] }`
- **Used In**: Admin Payroll tab - Variable % subtab

#### `PUT /api/payroll/variable-percentage`
- **Purpose**: Update variable percentage
- **Request Body**: `{ employee_id, percentage: number }`
- **Response**: `{ success: boolean, message: string }`
- **Used In**: Admin Payroll tab - Variable % subtab

#### `GET /api/payroll/lhdn/tax-rates`
- **Purpose**: Get LHDN tax rates
- **Response**: `{ success: boolean, data: TaxRate[] }`
- **Used In**: Admin Payroll tab - LHDN Tax - Tax Rates subtab

#### `GET /api/payroll/lhdn/relief-max`
- **Purpose**: Get tax relief maximum values
- **Response**: `{ success: boolean, data: ReliefMax[] }`
- **Used In**: Admin Payroll tab - LHDN Tax - Relief Max subtab

#### `GET /api/payroll/lhdn/relief-overrides`
- **Purpose**: Get employee-specific relief overrides
- **Response**: `{ success: boolean, data: ReliefOverride[] }`
- **Used In**: Admin Payroll tab - LHDN Tax - Relief Overrides subtab

#### `GET /api/payroll/export-csv`
- **Purpose**: Export payroll to CSV
- **Query Params**: Year, month
- **Response**: CSV file download
- **Used In**: Admin Payroll tab

#### `GET /api/payroll/payslip/:id`
- **Purpose**: Get/download payslip
- **Response**: PDF file or payslip data
- **Used In**: Employee Payroll tab

---

### Salary History

#### `GET /api/salary-history/:employee_id`
- **Purpose**: Get salary change history
- **Response**: `{ success: boolean, data: SalaryHistoryRecord[] }`
- **Used In**: Admin Salary History tab

#### `POST /api/salary-history`
- **Purpose**: Add salary change record
- **Request Body**: `{ employee_id, old_salary, new_salary, effective_date, reason }`
- **Response**: `{ success: boolean, message: string }`
- **Used In**: Admin Salary History tab

---

### Activities/Engagements (Training & Trips)

#### `GET /api/engagements/all` (Admin)
- **Purpose**: Get all training/trip records
- **Response**: `{ success: boolean, data: Engagement[] }`
- **Used In**: Admin Activities tab - View All subtab

#### `GET /api/engagements/my-engagements`
- **Purpose**: Get employee's engagements
- **Query Params**: `employee_email`
- **Response**: `{ success: boolean, data: Engagement[] }`
- **Used In**: Employee Engagements tab - View My Engagements subtab

#### `POST /api/engagements/submit`
- **Purpose**: Submit training/trip request
- **Request Body**: `{ employee_email, engagement_type, title, description, start_date, end_date, cost }`
- **Response**: `{ success: boolean, message: string, engagement_id: string }`
- **Used In**: Admin/Employee Engagements tab - Submit subtab

---

### Employment History

#### `GET /api/employment-history/:employee_id`
- **Purpose**: Get employment history records
- **Response**: `{ success: boolean, data: EmploymentHistory[] }`
- **Used In**: Admin Employment History tab

#### `POST /api/employment-history`
- **Purpose**: Add employment history record
- **Request Body**: `{ employee_id, position, department, start_date, end_date, reason }`
- **Response**: `{ success: boolean, message: string }`
- **Used In**: Admin Employment History tab

---

### Profile Management

#### `GET /api/profile/:email`
- **Purpose**: Get detailed employee profile
- **Response**: `{ success: boolean, data: EmployeeProfile }`
- **Used In**: Employee Profile tab
- **TODO**: Return all 25+ profile fields

#### `PUT /api/profile/:email`
- **Purpose**: Update employee profile
- **Request Body**: Editable profile fields (10+ fields)
- **Response**: `{ success: boolean, message: string }`
- **Used In**: Employee Profile tab - Edit form
- **TODO**: Validate and update editable fields only

---

## 🔧 JavaScript Functions to Implement

### Admin Dashboard (`admin_dashboard.js`)

```javascript
// TODO: Implement these functions

// Employee Management
async function searchEmployees(searchText) {
    // Search employees by name, email, or employee ID
}

async function filterEmployeesByDepartment(department) {
    // Filter employees by selected department
}

async function filterEmployeesByReligion(religion) {
    // Filter employees by selected religion
}

async function clearEmployeeFilters() {
    // Reset all filters and reload full list
}

async function refreshEmployeeList() {
    // Reload employee list from API
}

async function exportEmployeesToCSV() {
    // Download filtered employee list as CSV
}

async function createEmployee(formData) {
    // Submit new employee form (30+ fields)
    // Validate all fields before submission
}

// Attendance Management
async function filterAttendanceByDateRange(startDate, endDate) {
    // Filter attendance records by date range
}

async function searchAttendance(filterField, searchText) {
    // Search attendance by email or date
}

async function saveWorkingHours(workStart, workEnd, clockInLimit) {
    // Save working hours settings to database
}

async function exportAttendanceToCSV() {
    // Download filtered attendance records as CSV
}

// Leave Management
async function loadPendingLeaves() {
    // Fetch and display pending leave requests
}

async function approveLeave(leaveId, comments) {
    // Approve leave request with comments
}

async function rejectLeave(leaveId, reason) {
    // Reject leave request with reason
}

async function loadLeaveBalance(employeeId) {
    // Fetch leave balance for employee
}

async function loadLeaveCalendar(year, month) {
    // Load calendar view of leaves
}

// Payroll Management
async function filterPayrollByMonth(month, year) {
    // Filter payroll records by selected month
}

async function runPayroll(year, month, employeeIds) {
    // Process payroll for selected employees and month
}

async function addBonus(employeeId, bonusData) {
    // Add bonus to employee
}

async function updateVariablePercentage(employeeId, percentage) {
    // Update variable percentage for employee
}

async function loadTaxRates() {
    // Load LHDN tax rate tables
}

async function loadReliefMax() {
    // Load tax relief maximum values
}

async function loadReliefOverrides() {
    // Load employee-specific relief overrides
}

// Calendar Navigation
function setupOpenCalendar() {
    // Navigate to Leave tab -> Calendar subtab
}
```

### Employee Dashboard (`dashboard.js`)

```javascript
// TODO: Implement these functions

// Profile Management
async function loadProfileData() {
    // Fetch and display all 25+ profile fields
}

async function updateProfile(formData) {
    // Submit profile edit form (10+ editable fields)
}

// Attendance
async function clockIn() {
    // Record clock-in time
    // Show success/error message
    // Check clock-in limit validation
}

async function clockOut() {
    // Record clock-out time
    // Show success/error message
}

async function loadMyAttendanceHistory() {
    // Fetch and display attendance history
}

// Leave Management
async function submitLeaveRequest(leaveData) {
    // Submit new leave request
    // Validate dates and check balance
}

async function loadMyLeaveRequests() {
    // Fetch and display leave request history
}

async function loadMyLeaveBalance() {
    // Fetch leave balance (annual, sick, unpaid)
}

// Payroll
async function filterMyPayrollByMonth(month, year) {
    // Filter payroll records by month
}

async function downloadPayslip(payslipId) {
    // Download payslip PDF
}

// Engagements
async function submitEngagement(engagementData) {
    // Submit training/trip request
}

async function loadMyEngagements() {
    // Fetch and display engagement history
}
```

---

## 📊 Data Models

### Employee
```javascript
{
    id: string,
    email: string,
    full_name: string,
    password_hash: string,
    role: 'admin' | 'employee',
    
    // Personal Information
    gender: string,
    date_of_birth: date,
    nric: string,
    nationality: string,
    citizenship: string,
    race: string,
    religion: string,
    marital_status: string,
    number_of_children: number,
    
    // Contact Information
    phone_number: string,
    address: string,
    city: string,
    state: string,
    zipcode: string,
    
    // Employment Information
    employee_id: string,
    department: string,
    position: string,
    employment_status: 'Active' | 'Inactive' | 'Terminated',
    join_date: date,
    
    // EPF/SOCSO
    epf_number: string,
    socso_number: string,
    income_tax_number: string,
    
    created_at: timestamp,
    updated_at: timestamp
}
```

### AttendanceRecord
```javascript
{
    id: string,
    employee_email: string,
    date: date,
    clock_in: timestamp,
    clock_out: timestamp,
    hours_worked: number,
    status: 'present' | 'late' | 'absent',
    created_at: timestamp
}
```

### LeaveRequest
```javascript
{
    id: string,
    employee_email: string,
    leave_type: 'annual' | 'sick' | 'emergency' | 'unpaid' | 'maternity' | 'paternity',
    start_date: date,
    end_date: date,
    days_count: number,
    reason: string,
    status: 'pending' | 'approved' | 'rejected',
    approver_email: string,
    approval_date: timestamp,
    comments: string,
    created_at: timestamp
}
```

### PayrollRecord
```javascript
{
    id: string,
    employee_email: string,
    year: number,
    month: number,
    basic_salary: number,
    bonus: number,
    variable_pay: number,
    gross_salary: number,
    epf_employee: number,
    epf_employer: number,
    socso_employee: number,
    socso_employer: number,
    tax_deduction: number,
    net_salary: number,
    payment_date: date,
    created_at: timestamp
}
```

---

## ✅ Implementation Checklist

### Phase 1: Authentication & Core
- [ ] Implement login/logout APIs
- [ ] Set up session management
- [ ] Create JWT token handling
- [ ] Implement role-based access control

### Phase 2: Employee Management
- [ ] Employee CRUD APIs
- [ ] Employee search and filtering
- [ ] Employee export to CSV
- [ ] Profile view and edit APIs

### Phase 3: Attendance
- [ ] Clock in/out functionality
- [ ] Attendance history APIs
- [ ] Working hours settings
- [ ] Attendance filtering and export

### Phase 4: Leave Management
- [ ] Leave request submission
- [ ] Leave approval/rejection
- [ ] Leave balance calculation
- [ ] Leave calendar view

### Phase 5: Payroll
- [ ] Payroll calculation engine
- [ ] Month-based payroll filtering
- [ ] Bonus management
- [ ] EPF/SOCSO/Tax calculations
- [ ] Payslip generation
- [ ] Export payroll to CSV

### Phase 6: Additional Features
- [ ] Salary history tracking
- [ ] Engagements (training/trips)
- [ ] Employment history
- [ ] Calendar/holidays management

### Phase 7: Polish
- [ ] Form validation on frontend
- [ ] Error handling and user feedback
- [ ] Loading states and spinners
- [ ] Data refresh mechanisms
- [ ] Export/download functionalities

---

## 🚀 Quick Start Guide

1. **Set up backend framework** (Flask, FastAPI, Express, Django, etc.)
2. **Create database schema** based on data models above
3. **Implement API endpoints** following the specifications
4. **Update JavaScript files** to call your API endpoints
5. **Test each feature** incrementally
6. **Deploy** to production

---

## 📝 Notes

- All API endpoints should return JSON responses
- Use proper HTTP status codes (200, 201, 400, 401, 404, 500)
- Implement proper error handling and validation
- Use authentication tokens for secure API access
- Add CORS headers if frontend and backend are on different domains
- Implement rate limiting for security
- Log all important operations for auditing

---

## 🎯 Current Status

### ✅ Completed (UI Layer)
- All HTML templates with complete structure
- All form fields (30+ employee fields, 25+ profile fields)
- All tabs and subtabs
- All buttons and controls
- Month-based navigation
- Search and filter UI elements
- Working hours settings UI

### ⏳ Pending (Backend Layer)
- API endpoint implementation
- Database schema creation
- Business logic (payroll calculations, leave balance, etc.)
- File upload/download handlers
- Data validation
- Authentication and authorization

---

**For questions or clarifications, refer to the Python GUI implementation in the `gui/` and `services/` directories.**
