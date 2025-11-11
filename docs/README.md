# HRMS_app

Human Resources Management System - A comprehensive HRMS application built with PyQt5 and Supabase.

## Repository Structure

This repository is organized into logical directories for improved maintainability:

- **`/core`** - Core business logic, calculators, and utilities (31 files)
- **`/gui`** - User interface components, windows, dialogs, and tabs (67 files)
- **`/services`** - External service integrations (Supabase, APIs) (9 files)
- **`/data`** - Configuration files, SQL schemas, and migrations (56 files)
- **`/docs`** - Documentation and guides (16 files)
- **`/tests`** - Test files and diagnostic tools (125 files)
- **`/scripts`** - Build and utility scripts (6 files)
- **`/examples`** - Sample data and exports (11 files)

For detailed information about the repository structure, see [REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md).

## Getting Started

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for installation and setup instructions.

## Documentation

- [Setup Guide](SETUP_GUIDE.md) - Installation and configuration
- [Repository Structure](REPOSITORY_STRUCTURE.md) - Detailed directory organization
- [Integration Summary](INTEGRATION_SUMMARY.md) - Integration overview
- [PCB Implementation](LHDN_PCB_IMPLEMENTATION.md) - Tax calculation details

## Running the Application

### Windows
```batch
scripts\start_hrms.bat
```

Or using PowerShell:
```powershell
scripts\start_hrms.ps1
```

### Python Direct
```bash
python main.py
```

## Key Features

- Employee management and profiles
- Leave request and approval system
- Payroll processing with Malaysian tax calculations
- Attendance tracking
- Holiday calendar management
- Bonus management
- Training and overseas work trip tracking
- PDF payslip generation

## Technology Stack

- **Frontend**: PyQt5
- **Backend**: Python 3.x
- **Database**: Supabase (PostgreSQL)
- **PDF Generation**: ReportLab
- **Authentication**: bcrypt