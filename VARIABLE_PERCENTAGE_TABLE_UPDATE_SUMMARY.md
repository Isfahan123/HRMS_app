# Variable Percentage Configuration Table Update Summary

## Overview
The `variable_percentage_configs` table has been updated to match the current implementation in the `admin_payroll_tab.py` file. The previous simple structure has been replaced with a comprehensive structure that supports all EPF Parts A-E, SOCSO categories, and EIS rates.

## Changes Made

### 1. **Removed Simple Structure**
**Old table structure:**
```sql
epf_employee_rate DECIMAL(5,2) NOT NULL DEFAULT 11.0,
epf_employer_rate DECIMAL(5,2) NOT NULL DEFAULT 13.0,
socso_employee_rate DECIMAL(5,2) NOT NULL DEFAULT 0.5,
socso_employer_rate DECIMAL(5,2) NOT NULL DEFAULT 1.75,
eis_employee_rate DECIMAL(5,2) NOT NULL DEFAULT 0.2,
eis_employer_rate DECIMAL(5,2) NOT NULL DEFAULT 0.2,
pcb_rate DECIMAL(5,2) NOT NULL DEFAULT 0.0,  -- Removed (PCB UI was removed)
```

### 2. **Added Comprehensive EPF Structure**
**New EPF structure supports all 5 official KWSP Parts:**

- **Part A**: Malaysian + PRs + Non-citizens (before 1 Aug 1998) - Under 60
- **Part B**: Non-citizens (on/after 1 Aug 1998) - Under 60
- **Part C**: PRs + Non-citizens (before 1 Aug 1998) - 60 and above
- **Part D**: Non-citizens (on/after 1 Aug 1998) - 60 and above
- **Part E**: Malaysian Citizens - 60 and above

Each part includes:
- Basic rates for table lookup
- Rates for wages exceeding RM20,000
- Special rules (bonus rules, fixed amounts)

### 3. **Enhanced SOCSO Structure**
**SOCSO now supports two categories:**
- **First Category**: Under 60 years (Employment Injury + Invalidity Schemes)
- **Second Category**: 60+ years (Employment Injury Scheme only)

### 4. **Maintained EIS Structure**
- Single rate structure for employees and employers
- Applies to ages 18-60 with salary cap of RM6,000

## Database Columns

### EPF Part A (Malaysian + PRs + Non-citizens before 1998, Under 60)
- `epf_part_a_employee` - Employee rate (%)
- `epf_part_a_employer` - Employer rate (%)
- `epf_part_a_employee_over20k` - Employee rate for wages >RM20k (%)
- `epf_part_a_employer_over20k` - Employer rate for wages >RM20k (%)
- `epf_part_a_employer_bonus` - Employer bonus rule rate (%)

### EPF Part B (Non-citizens after 1998, Under 60)
- `epf_part_b_employee` - Employee rate (%)
- `epf_part_b_employer` - Employer rate (%)
- `epf_part_b_employee_over20k` - Employee rate for wages >RM20k (%)
- `epf_part_b_employer_over20k_fixed` - Employer fixed amount for wages >RM20k (RM)

### EPF Part C (PRs + Non-citizens before 1998, 60+)
- `epf_part_c_employee` - Employee rate (%)
- `epf_part_c_employer_fixed` - Employer fixed amount (RM)
- `epf_part_c_employee_over20k` - Employee rate for wages >RM20k (%)
- `epf_part_c_employer_over20k` - Employer rate for wages >RM20k (%)
- `epf_part_c_employer_bonus` - Employer bonus rule rate (%)

### EPF Part D (Non-citizens after 1998, 60+)
- `epf_part_d_employee` - Employee rate (%)
- `epf_part_d_employer` - Employer rate (%)
- `epf_part_d_employee_over20k` - Employee rate for wages >RM20k (%)
- `epf_part_d_employer_over20k_fixed` - Employer fixed amount for wages >RM20k (RM)

### EPF Part E (Malaysian Citizens, 60+)
- `epf_part_e_employee` - Employee rate (%) [voluntary]
- `epf_part_e_employer` - Employer rate (%)
- `epf_part_e_employee_over20k` - Employee rate for wages >RM20k (%) [voluntary]
- `epf_part_e_employer_over20k` - Employer rate for wages >RM20k (%)

### SOCSO Categories
- `socso_first_employee_rate` - First Category employee rate (%) [Under 60]
- `socso_first_employer_rate` - First Category employer rate (%) [Under 60]
- `socso_second_employee_rate` - Second Category employee rate (%) [60+]
- `socso_second_employer_rate` - Second Category employer rate (%) [60+]

### EIS Rates
- `eis_employee_rate` - Employee rate (%) [Ages 18-60]
- `eis_employer_rate` - Employer rate (%) [Ages 18-60]

### Metadata
- `config_name` - Primary key
- `description` - Optional configuration description
- `created_at` - Timestamp
- `updated_at` - Timestamp (auto-updated)

## Default Configuration
The table includes a default configuration with official PERKESO/KWSP rates:

```sql
INSERT INTO variable_percentage_configs VALUES (
    'default',
    'PERKESO-compliant default rates with comprehensive Malaysian statutory contributions (KWSP Parts A-E)',
    -- EPF Part A: 11.0, 12.0, 11.0, 12.0, 13.0
    -- EPF Part B: 11.0, 4.0, 11.0, 5.0
    -- EPF Part C: 5.5, 5.0, 5.5, 6.0, 6.5
    -- EPF Part D: 5.5, 4.0, 5.5, 5.0
    -- EPF Part E: 0.0, 4.0, 0.0, 4.0
    -- SOCSO: 0.5, 1.75, 0.0, 1.25
    -- EIS: 0.2, 0.2
);
```

## Removed Components
1. **PCB Rate** - `pcb_rate` column removed since PCB UI components were removed
2. **LHDN Tax Configs** - `lhdn_tax_configs` table can be dropped (separate cleanup script provided)

## Scripts Provided
1. **`update_variable_percentage_configs_table.sql`** - Main update script
2. **`cleanup_lhdn_tax_configs.sql`** - Optional cleanup for LHDN table

## UI Alignment
The table structure now perfectly matches the variable percentage input fields in `admin_payroll_tab.py`:
- All EPF Parts A-E with their respective input controls
- SOCSO First/Second Category rates
- EIS employee/employer rates
- No longer includes removed PCB/salary limits/configuration management components

## Migration Notes
- The old simple structure is completely replaced
- All existing data in the old table will be lost
- A new default configuration is automatically created
- The application no longer uses configuration save/load functionality (UI removed)
- Variable percentage rates are now direct input only (no database persistence from UI)

This structure provides comprehensive support for Malaysian statutory contribution calculations while removing unnecessary complexity from removed UI components.
