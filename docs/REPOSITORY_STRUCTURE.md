# Repository Structure

This document describes the organization of the HRMS application repository after restructuring for improved maintainability and clarity.

## Directory Overview

```
HRMS_app/
├── main.py                 # Application entry point
├── main.spec              # PyInstaller spec file
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore patterns
│
├── core/                 # Core business logic (31 files)
├── gui/                  # User interface components (67 files)
├── services/             # External service integrations (9 files)
├── data/                 # Configuration and schema files (56 files)
├── docs/                 # Documentation (16 files)
├── tests/                # Tests and diagnostic tools (125 files)
├── scripts/              # Build and utility scripts (6 files)
└── examples/             # Sample data and exports (11 files)
```

## Directory Details

### `/core` - Core Business Logic (31 files)

Contains the core business logic, calculations, and utility functions that are independent of UI and database implementations.

**Key modules:**
- **Calculators:**
  - `epf_socso_calculator.py` - EPF and SOCSO calculations
  - `malaysian_pcb_calculator.py` - Malaysian PCB tax calculations
  - `tax_relief_catalog.py` - Tax relief catalog and computations

- **Services:**
  - `employee_service.py` - Employee-related business logic
  - `holidays_service.py` - Holiday management and calculations
  - `leave_caps_service.py` - Leave capacity management
  - `email_service.py` - Email sending functionality
  - `calendarific_service.py` - Calendar API integration

- **Data Access:**
  - `database_integration.py` - Database integration utilities
  - `ytd_service_functions.py` - Year-to-date calculations
  - `job_title_mapping_loader.py` - Job title data loader

- **Other utilities:**
  - Various audit, calculation, and data processing scripts

### `/gui` - User Interface (67 files)

Contains all PyQt5 user interface components including windows, dialogs, tabs, and widgets.

**Main Windows:**
- `login_window.py` - User login interface
- `dashboard_window.py` - Employee dashboard
- `admin_dashboard_window.py` - Administrator dashboard

**Admin Tabs:**
- `admin_attendance_tab.py` - Attendance management
- `admin_bonus_tab.py` - Bonus management
- `admin_leave_tab.py` - Leave approval and management
- `admin_payroll_tab.py` - Payroll processing
- `admin_profile_tab.py` - Employee profile management
- `admin_salary_history_tab.py` - Salary history
- Various `_mod` versions for modular implementations

**Employee Tabs:**
- `employee_leave_tab.py` - Employee leave requests
- `employee_payroll_tab.py` - Payroll information
- `employee_profile_tab.py` - Profile editing
- `employee_attendance_tab.py` - Attendance tracking
- `employee_history_tab.py` - Employment history

**Dialogs & Widgets:**
- `employee_profile_dialog.py` - Profile editing dialog
- `employee_selector_dialog.py` - Employee selection
- `payroll_dialog.py` - Payroll processing dialog
- `bonus_management_dialog.py` - Bonus management
- `place_lookup_dialog.py` - Location lookup
- Various autocomplete and input widgets

**Specialized Components:**
- `calendar_tab.py` - Calendar management
- `payslip_generator.py` - Payslip PDF generation
- `leave_calendar.py` - Leave calendar view
- LHDN tax configuration tabs and subtabs

### `/services` - External Integrations (9 files)

Contains modules that integrate with external services, primarily Supabase database and organization structure.

**Supabase Integration:**
- `supabase_service.py` - Main Supabase client and utilities
- `supabase_employee.py` - Employee data access
- `supabase_employee_history.py` - Employee history records
- `supabase_engagements.py` - Employee engagements
- `supabase_leave_types.py` - Leave type management
- `supabase_training_overseas.py` - Training and overseas work trips

**Other Services:**
- `org_structure_service.py` - Organization structure data
- `local_settings_cache.py` - Local settings caching

### `/data` - Data Files (56 files)

Contains configuration files, database schemas, and migration scripts.

**SQL Files (47 files):**
- Schema creation scripts (`create_*.sql`)
- Migration scripts (`migrate_*.sql`, `2025-*.sql`)
- Table alteration scripts (`add_*.sql`, `alter_*.sql`, `update_*.sql`)

**JSON Configuration (9 files):**
- `org_structure.json` - Organization hierarchy
- `org_structure_detailed.json` - Detailed organization data
- `leave_caps.json` - Leave capacity configurations
- `job_title_mapping.json` - Job title to department/position mapping
- `department_functional_group_template.json` - Department templates
- `employee_history.json` - Employee history data
- `employee_status.json` - Employee status definitions
- `holiday_overrides.json` - Holiday calendar overrides
- `schema_report.json` - Schema documentation

### `/docs` - Documentation (16 files)

Contains all project documentation, setup guides, and technical summaries.

**Main Documentation:**
- `README.md` - Project overview
- `SETUP_GUIDE.md` - Setup instructions
- `REPOSITORY_STRUCTURE.md` - This file

**Technical Documentation:**
- `INTEGRATION_SUMMARY.md` - Integration overview
- `FISCAL_PAYROLL_YEAR.md` - Fiscal year handling
- `LHDN_PCB_IMPLEMENTATION.md` - PCB tax implementation
- `PCB_UPDATE_SUMMARY.md` - PCB updates summary
- `VARIABLE_PERCENTAGE_TABLE_UPDATE_SUMMARY.md` - Variable percentage updates

**Feature Documentation:**
- `HOW_TO_SEE_REALTIME_CHANGES.md` - Real-time updates
- `MAX_CAP_SYNCHRONIZATION_SOLUTION.md` - Max cap sync
- `COMPLETE_MAX_CAP_SYNC_SOLUTION.md` - Complete sync solution
- `REAL_TIME_MAX_CAP_SYNC.md` - Real-time max cap sync
- `INDIVIDUAL_TAX_REBATE_UPDATE.md` - Tax rebate updates
- Various other technical summaries

### `/tests` - Tests & Diagnostics (125 files)

Contains test files, debugging scripts, validation tools, and diagnostic utilities.

**Test Files (test_*.py):**
- `test_employee_leave_tab.py` - Leave tab tests
- `test_login_lockout.py` - Login security tests
- `test_pcb_debug.py` - PCB calculation tests
- `test_tax_bracket_ordering.py` - Tax bracket tests
- `test_working_days.py` - Working days calculation tests
- And 17 more test files

**Diagnostic & Debug Scripts:**
- `debug_*.py` - Various debugging tools
- `smoke_*.py` - Smoke test scripts
- `diag_*.py` - Diagnostic utilities
- `check_*.py` - Validation scripts
- `verify_*.py` - Verification tools

**Run & Utility Scripts:**
- `run_*.py` - Execution scripts for specific scenarios
- `compare_*.py` - Comparison utilities
- `fetch_*.py` - Data fetching scripts
- `inspect_*.py` - Inspection tools
- `sync_*.py` - Synchronization utilities

### `/scripts` - Build & Utility Scripts (6 files)

Contains scripts for building, running, and managing the application.

**Startup Scripts:**
- `start_hrms.bat` - Windows batch file to start HRMS
- `start_hrms.ps1` - PowerShell script to start HRMS

**Data Management:**
- `import_malaysia_holidays.ps1` - Holiday data import script

**Build Configuration:**
- `composer.json` - PHP Composer configuration
- `composer.lock` - PHP dependency lock file
- `hrms_app.code-workspace` - VS Code workspace configuration

### `/examples` - Sample Data (11 files)

Contains example data, sample outputs, and reference implementations.

**Sample Payslips (8 PDF files):**
- `Payslip_*.pdf` - Various sample payslip PDFs for testing and reference

**Export Scripts:**
- `export_malaysia_holidays_php.php` - PHP holiday export script
- `holiday.php` - Holiday processing PHP script
- `print_file_with_lines.py` - File printing utility

## Import Conventions

The restructured repository uses the following import conventions:

### From Core Modules
```python
from core.employee_service import calculate_cumulative_service
from core.holidays_service import get_holidays_for_year
from core.epf_socso_calculator import EPFSOCSCalculator
from core.tax_relief_catalog import ITEMS as TP1_ITEMS
```

### From GUI Modules
```python
from gui.login_window import LoginWindow
from gui.dashboard_window import DashboardWindow
from gui.employee_leave_tab import EmployeeLeaveTab
```

### From Service Modules
```python
from services.supabase_service import supabase
from services.supabase_employee import fetch_employee_list
from services.org_structure_service import list_departments
```

### Data File Access
Data files in `/data` are accessed using relative paths:
```python
import os
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'leave_caps.json')
```

## Benefits of This Structure

1. **Clear Separation of Concerns**: Business logic, UI, and data access are clearly separated
2. **Easier Navigation**: Related files are grouped together
3. **Better Maintainability**: Changes to one area don't affect others
4. **Simplified Testing**: Test files are isolated and easy to find
5. **Cleaner Root**: Main application files remain in root for easy access
6. **Documentation Organization**: All docs in one place for easy reference

## Migration Notes

- All imports have been updated to use the new package structure
- Data file paths have been updated from `database/` to `data/`
- The application entry point (`main.py`) remains in the root directory
- All Python modules compile successfully with no syntax errors
