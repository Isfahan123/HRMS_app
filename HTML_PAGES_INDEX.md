# HTML Pages Index

This document provides an index of all HTML pages created for the HRMS web application, with descriptions and features.

## Overview

**Total Pages Created**: 12 HTML templates  
**Base Template**: 1 (base.html)  
**Employee Pages**: 5  
**Admin Pages**: 3  
**Authentication**: 1  
**Dashboard Pages**: 2

---

## Base Template

### base.html
**Purpose**: Base template with common layout structure  
**Location**: `templates/base.html`  
**Features**:
- HTML5 doctype and meta tags
- Common CSS and JavaScript includes
- Block structure for title and content
- Container wrapper for all pages

**Blocks Available**:
- `{% block title %}` - Page title
- `{% block extra_css %}` - Additional CSS
- `{% block content %}` - Main content
- `{% block extra_js %}` - Additional JavaScript

---

## Authentication Pages

### 1. Login Page
**File**: `templates/login.html`  
**Route**: `/login` (GET, POST)  
**Purpose**: User authentication  
**Original**: Converted from `gui/login_window.py`

**Features**:
- Username and password input fields
- AJAX form submission
- Error message display
- Responsive design
- Automatic redirect on success
- Account lockout message support

**Form Fields**:
- Username (text input)
- Password (password input)

**JavaScript Functions**:
- Form submission handler
- Error display
- Redirect logic

---

## Employee Dashboard Pages

### 2. Employee Dashboard
**File**: `templates/dashboard.html`  
**Route**: `/dashboard` (GET)  
**Purpose**: Main dashboard for employees  
**Original**: Converted from `gui/dashboard_window.py`

**Features**:
- Welcome header with user name
- Tab navigation (6 tabs)
- Summary cards on home tab
- Logout button
- Lazy loading of tab content

**Tabs**:
1. 🏠 **Home** - Summary view
2. 👤 **Profile** - Employee information
3. 📅 **Attendance** - Attendance records
4. 📬 **Leave Request** - Leave management
5. 💸 **Payroll** - Salary information
6. 🗂 **Engagements** - Training & trips

**Data Loaded**:
- Attendance summary
- Leave request summary
- Profile information (lazy loaded)

### 3. Employee Profile Tab
**File**: `templates/employee_profile.html`  
**Route**: Loaded via AJAX in dashboard  
**Purpose**: Display employee information  
**Original**: Converted from `gui/employee_profile_tab.py`

**Features**:
- Personal information section
- Employment details section
- Edit profile button
- Responsive grid layout

**Information Displayed**:
- Full Name, Email, Phone
- Employee ID, Department, Position
- Join Date, Status
- Employment Type, Salary, Manager

### 4. Employee Attendance Tab
**File**: `templates/employee_attendance.html`  
**Route**: Loaded via AJAX in dashboard  
**Purpose**: Attendance tracking and history  
**Original**: Converted from `gui/employee_attendance_tab.py`

**Features**:
- Check-in/Check-out buttons
- Today's status card
- Attendance history table
- Month filter
- Refresh button

**Components**:
- Action buttons (Check In, Check Out, Refresh)
- Status card showing today's times
- Attendance table with filters
- Monthly filtering

**Table Columns**:
- Date, Check In, Check Out, Hours, Status

### 5. Employee Leave Tab
**File**: `templates/employee_leave.html`  
**Route**: Loaded via AJAX in dashboard  
**Purpose**: Leave request management  
**Original**: Converted from `gui/employee_leave_tab.py`

**Features**:
- Leave balance cards (3 types)
- Leave request table
- New request modal
- Status filtering
- Request cancellation

**Leave Types**:
- Annual Leave
- Sick Leave
- Emergency Leave
- Unpaid Leave

**Modal Form**:
- Leave Type dropdown
- Start Date picker
- End Date picker
- Reason textarea
- Submit/Cancel buttons

**Table Columns**:
- Leave Type, Start Date, End Date, Days, Status, Reason, Actions

### 6. Employee Payroll Tab
**File**: `templates/employee_payroll.html`  
**Route**: Loaded via AJAX in dashboard  
**Purpose**: Payroll and salary information  
**Original**: Converted from `gui/employee_payroll_tab.py`

**Features**:
- Current salary card
- Payslip history table
- Year-to-date tax summary
- Year filter
- Download payslips

**Salary Information**:
- Basic Salary
- Allowances
- Total Gross

**Payslip Table**:
- Month, Year, Gross Salary, Deductions, Net Salary, Status, Download

**Tax Summary (YTD)**:
- Total Income
- EPF Contribution
- SOCSO Contribution
- EIS Contribution
- PCB Deducted

### 7. Employee Engagements Tab
**File**: `templates/employee_engagements.html`  
**Route**: Loaded via AJAX in dashboard  
**Purpose**: Training courses and overseas trips  
**Original**: Converted from `gui/employee_engagements_tab.py`

**Features**:
- Sub-tab navigation (Training, Trips)
- Statistics cards
- Training courses table
- Overseas trips table
- Request buttons

**Training Section**:
- Statistics (Completed, In Progress, Planned)
- Course table (Name, Provider, Dates, Status, Certificate)
- Request training button

**Trips Section**:
- Statistics (Total Trips, Countries Visited, Days Abroad)
- Trip table (Destination, Purpose, Dates, Duration, Status)
- Request trip button

---

## Admin Dashboard Pages

### 8. Admin Dashboard
**File**: `templates/admin_dashboard.html`  
**Route**: `/admin` (GET)  
**Purpose**: Main dashboard for administrators  
**Original**: Converted from `gui/admin_dashboard_window.py`

**Features**:
- Admin welcome header
- Tab navigation (10 tabs)
- System overview on home tab
- Summary cards
- Logout button

**Tabs**:
1. 🏠 **Home** - System overview
2. 👤 **Profile Management** - Employee CRUD
3. 📅 **Attendance Management** - Attendance oversight
4. 📬 **Leave Management** - Leave approvals
5. 💸 **Payroll Management** - Payroll processing
6. 💰 **Salary History** - Salary changes
7. 🎁 **Bonus Management** - Bonus allocation
8. 📚 **Training Courses** - Training management
9. ✈️ **Overseas Trips** - Trip management
10. 📊 **Tax Configuration** - Tax settings

**Summary Cards**:
- Total Employees
- Pending Leave Requests
- Today's Attendance
- Payroll Status

### 9. Admin Profile Management Tab
**File**: `templates/admin_profile.html`  
**Route**: Loaded via AJAX in admin dashboard  
**Purpose**: Employee management (CRUD operations)  
**Original**: Converted from `gui/admin_profile_tab.py`

**Features**:
- Add new employee button
- Search functionality
- Employee list table
- Edit/Delete actions
- Employee form modal

**Table Columns**:
- Employee ID, Full Name, Email, Department, Position, Status, Actions

**Employee Form Fields**:
- Full Name, Email, Phone
- Employee ID, Department, Position
- Join Date, Salary, Status, Role

**Actions**:
- Edit employee (opens modal)
- Delete employee (with confirmation)
- Search/filter employees

### 10. Admin Leave Management Tab
**File**: `templates/admin_leave.html`  
**Route**: Loaded via AJAX in admin dashboard  
**Purpose**: Review and approve/reject leave requests  
**Original**: Converted from `gui/admin_leave_tab.py`

**Features**:
- Summary cards (Pending, Approved, Rejected)
- Multiple filters (Status, Employee)
- Leave requests table
- Review modal
- Approve/Reject actions

**Summary Statistics**:
- Pending Requests count
- Approved This Month count
- Rejected This Month count

**Filters**:
- Status filter (All, Pending, Approved, Rejected)
- Employee filter (All, specific employee)

**Table Columns**:
- Employee, Leave Type, Start Date, End Date, Days, Reason, Status, Actions

**Review Modal**:
- Full leave request details
- Admin remarks field
- Approve/Reject/Cancel buttons

### 11. Admin Payroll Management Tab
**File**: `templates/admin_payroll.html`  
**Route**: Loaded via AJAX in admin dashboard  
**Purpose**: Process payroll and manage salaries  
**Original**: Converted from `gui/admin_payroll_tab.py`

**Features**:
- Process payroll button
- Generate payslips button
- Month/Year filters
- Summary statistics
- Detailed payroll table

**Summary Cards**:
- Total Employees
- Total Gross Salary
- Total Deductions
- Total Net Salary

**Action Buttons**:
- Process Payroll (for selected month)
- Generate Payslips (bulk generation)

**Table Columns**:
- Employee ID, Employee Name
- Basic Salary, Allowances, Bonuses, Gross Salary
- EPF, SOCSO, EIS, PCB
- Net Salary, Actions

**Payroll Details Modal**:
- Complete breakdown for one employee
- Download payslip button

---

## Page Dependencies

### CSS Dependencies
All pages use: `static/css/style.css`

### JavaScript Dependencies
- **All pages**: `static/js/main.js` (utility functions)
- **Dashboard pages**: `static/js/dashboard.js` (data loading)

### External Dependencies
- None (no external CSS/JS frameworks required)
- All styling is custom CSS
- All JavaScript is vanilla JS

---

## Common Components Across Pages

### Navigation Tabs
- Consistent tab interface
- Active state indication
- Click to switch views
- Lazy loading support

### Modal Dialogs
- Centered overlay
- Close button (×)
- Form submission
- Cancel button
- Backdrop click to close

### Data Tables
- Sortable columns
- Hover effects
- Alternating row colors
- Action buttons
- Responsive design

### Form Elements
- Consistent styling
- Validation support
- Error display
- Submit/Cancel actions

### Status Badges
- Color-coded by status
- Rounded design
- Used across multiple pages

### Summary Cards
- Gradient backgrounds
- Large numbers
- Icons/emojis
- Hover effects

---

## Responsive Breakpoints

All pages are responsive with breakpoints:
- **Desktop**: > 1024px (full features)
- **Tablet**: 768px - 1024px (adjusted layout)
- **Mobile**: < 768px (stacked layout)

**Mobile Optimizations**:
- Stacked navigation tabs
- Collapsible tables
- Touch-friendly buttons
- Simplified layouts

---

## Browser Compatibility

All pages tested and compatible with:
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ❌ Internet Explorer (not supported)

---

## Accessibility Features

- Semantic HTML5 elements
- ARIA labels where appropriate
- Keyboard navigation support
- Focus indicators
- Color contrast compliance
- Screen reader friendly

---

## Future Pages (To Be Created)

### Admin Pages
- [ ] admin_attendance.html - Attendance oversight and management
- [ ] admin_salary_history.html - Salary change history
- [ ] admin_bonus.html - Bonus allocation and management
- [ ] admin_training.html - Training course management
- [ ] admin_trips.html - Overseas trip management
- [ ] admin_tax_config.html - Tax configuration and settings

### Additional Components
- [ ] Calendar component for date selection
- [ ] Chart components for analytics
- [ ] Export functionality pages
- [ ] Settings/preferences page
- [ ] Help/documentation page
- [ ] User profile edit page

---

## Development Guidelines

### Adding New Pages

1. Create HTML file in `templates/`
2. Extend `base.html`
3. Add route in `app.py`
4. Style in `static/css/style.css`
5. Add JavaScript if needed
6. Test responsiveness
7. Update this index

### Naming Conventions

- **Files**: lowercase with underscores (`admin_leave.html`)
- **CSS Classes**: kebab-case (`.leave-summary`)
- **JavaScript Functions**: camelCase (`loadLeaveData()`)
- **IDs**: kebab-case (`#leave-modal`)

### Code Quality

- Valid HTML5
- W3C compliant
- Semantic markup
- Accessibility standards
- Mobile-first design
- Progressive enhancement

---

**Last Updated**: 2025-11-12  
**Total Pages**: 12  
**Status**: Core pages complete, additional admin pages pending
