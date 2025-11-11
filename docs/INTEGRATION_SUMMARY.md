# HRMS TAX SYSTEM - COMPLETE DATABASE INTEGRATION

## Overview
This document outlines the complete integration of tax configurations and payroll processing with Supabase database for the HRMS application.

## New Database Tables Created

### 1. tax_rates_config
**Purpose**: Store tax rates and statutory contribution configurations
**Key Fields**:
- `progressive_rates` (JSONB): Malaysia's progressive tax brackets
- `non_resident_rate`: Flat tax rate for non-residents (30%)
- `epf_employee_rate`, `epf_employer_rate`: EPF contribution rates
- `socso_employee_rate`, `socso_employer_rate`: SOCSO contribution rates
- `eis_employee_rate`, `eis_employer_rate`: EIS contribution rates
- `epf_ceiling`, `socso_ceiling`, `eis_ceiling`: Maximum salary ceilings

### 2. tax_relief_max_config
**Purpose**: Store maximum amounts for tax relief categories
**Key Fields**:
- All LHDN-compliant maximum amounts for each relief category
- Special sub-cap limits and upper limits
- Combined limits (e.g., EPF + Insurance = RM7,000)

### 3. payroll_information
**Purpose**: Comprehensive payroll records for all employees
**Key Fields**:
- Employee identification and basic salary information
- Income components (allowances, overtime, commission, bonus)
- Statutory deductions (EPF, SOCSO, EIS, PCB)
- Monthly deductions (potongan bulan semasa) - stored as JSONB
- Annual tax reliefs - stored as JSONB
- Other deductions and final net salary
- Tax resident status and calculation metadata

### 4. payslip_history
**Purpose**: Track generated payslip PDFs for audit purposes
**Key Fields**:
- References to payroll records
- PDF file information and paths
- Generation timestamps and user tracking

## New Supabase Service Functions

### Tax Configuration Functions
```python
save_tax_rates_configuration(config_data: Dict) -> bool
load_tax_rates_configuration(config_name: str = 'default') -> Optional[Dict]
save_tax_relief_max_configuration(config_data: Dict) -> bool
load_tax_relief_max_configuration(config_name: str = 'default') -> Optional[Dict]
```

### Payroll Processing Functions
```python
calculate_comprehensive_payroll(employee_data: Dict, payroll_inputs: Dict, month_year: str) -> Dict
process_payroll_and_generate_payslip(employee_data: Dict, payroll_inputs: Dict, month_year: str, generate_pdf: bool = True) -> Dict
save_payroll_information(payroll_data: Dict) -> bool
load_payroll_information(employee_id: str, month_year: str) -> Optional[Dict]
get_employee_payroll_history(employee_id: str) -> List[Dict]
```

### Payslip Generation
```python
generate_payslip_pdf(payroll_data: Dict, output_path: str = None) -> Optional[str]
```

## Integration Points

### Admin Payroll Tab Integration
**File**: `integration/database_integration.py`

**Functions Added**:
- `save_tax_rates_to_db()`: Save current admin tax rates to database
- `save_tax_relief_max_to_db()`: Save current admin tax relief maximums
- `load_configurations_from_db()`: Load saved configurations from database

**Features**:
- Extracts current admin panel settings
- Saves to database with versioning
- Loads saved configurations back to admin controls

### Payroll Dialog Integration
**File**: `integration/database_integration.py`

**Functions Added**:
- `save_payroll_to_db()`: Process complete payroll calculation and save
- `load_payroll_from_db()`: Load existing payroll data for editing

**Features**:
- Extracts all payroll inputs from dialog fields
- Processes comprehensive payroll calculation
- Saves to database and generates payslip PDF
- Loads existing payroll data for modifications

## Complete Payroll Processing Flow

### 1. Tax Configuration Setup (Admin)
```
Admin Panel → Set Tax Rates & Relief Maximums → Save to Database
```

### 2. Employee Payroll Processing
```
Payroll Dialog → Enter Employee Data → Calculate Payroll → Save to Database → Generate Payslip
```

### 3. Calculation Process
```
Basic Income + Allowances + Overtime + Commission + Bonus = Gross Income
↓
Gross Income - EPF - SOCSO - EIS = Taxable Income
↓
Apply Tax Reliefs (Residents) / Flat Rate (Non-Residents) = PCB Tax
↓
Gross Income - All Deductions = Net Salary
```

## Non-Resident Tax Compliance

### UI Restrictions
- **Payroll Dialog**: Monthly deductions and tax relief sections hidden for non-residents
- **Admin Panel**: Tax relief configuration sections hidden for non-residents

### Calculation Logic
- **Residents**: Progressive tax rates with full relief eligibility
- **Non-Residents**: 30% flat tax rate, no relief eligibility (except EPF contributions)

## Database Security

### Row Level Security (RLS)
- All tables have RLS enabled
- Policies restrict access to authenticated users only
- Audit trails with timestamps and user tracking

### Data Integrity
- Foreign key constraints between related tables
- JSON schema validation for complex fields
- Automatic timestamp updates with triggers

## PDF Payslip Generation

### Features
- Professional payslip layout with company branding
- Detailed income and deduction breakdowns
- Tax status indication
- Timestamp and generation metadata
- File storage with audit trail

### Integration
- Automatic generation during payroll processing
- Storage path tracking in database
- Retrieval system for historical payslips

## Usage Instructions

### Setting Up Tables
1. Execute `supabase_tables.sql` in Supabase SQL editor
2. Verify all tables are created with proper indexes and policies
3. Confirm default configurations are inserted

### Admin Configuration
1. Open Admin Payroll Tab
2. Configure tax rates and relief maximums
3. Click "Save Tax Rates to DB" and "Save Tax Relief Max to DB"
4. Configurations are now stored and will be used for all payroll calculations

### Processing Payroll
1. Open Payroll Dialog for an employee
2. Enter all salary and deduction information
3. Select appropriate tax resident status
4. Click "Process & Save Payroll"
5. Payroll is calculated, saved to database, and payslip is generated

### Loading Existing Data
1. Use "Load Configurations from DB" in admin panel to restore settings
2. Use "Load Existing Payroll" in payroll dialog to edit previous entries

## Error Handling

### Database Operations
- All functions include comprehensive error handling
- User-friendly error messages via QMessageBox
- Debug logging for troubleshooting
- Graceful fallbacks to default configurations

### Calculation Validation
- Input validation for all monetary values
- LHDN compliance checks for relief limits
- Cross-validation of tax calculations
- Automatic recalculation on data changes

## Maintenance and Updates

### Configuration Updates
- Admin can update tax rates and relief maximums anytime
- Changes apply to new payroll calculations immediately
- Historical data remains unchanged for audit purposes

### System Monitoring
- All database operations are logged
- Payslip generation history is tracked
- User actions are audited with timestamps

## Technical Notes

### Performance Optimizations
- Database indexes on frequently queried fields
- JSON field optimization for complex data
- Efficient SQL queries with proper joins
- Caching of frequently accessed configurations

### Scalability Considerations
- Table partitioning capability for large datasets
- Configurable data retention policies
- Backup and restore procedures
- Performance monitoring capabilities

This implementation provides a complete, LHDN-compliant payroll system with robust database integration, comprehensive tax handling, and professional payslip generation capabilities.
