# Payroll History Table - Python GUI vs HTML GUI Comparison

**Date:** 2025-11-24  
**Status:** ✅ **COMPLETE - Full Column Parity Achieved**

---

## Summary

The HTML GUI payroll history table has been updated to match the Python GUI's detailed 20-column structure, showing complete payroll breakdown including statutory contributions and all deductions.

---

## Column Comparison

### Before (HTML GUI - 8 columns)

| # | Column | Description |
|---|--------|-------------|
| 1 | Employee | Employee name |
| 2 | Month | Payroll date |
| 3 | Basic Salary | Base salary |
| 4 | Gross Pay | Total gross |
| 5 | Deductions | **Total deductions only** |
| 6 | Net Pay | Final take-home |
| 7 | Status | Completed/Pending |
| 8 | Actions | Download payslip |

**Issue:** No breakdown of statutory contributions (EPF, SOCSO, EIS) or individual deductions (PCB, SIP, PRS, etc.)

---

### After (HTML GUI - 20 columns) ✅

Matching Python GUI exactly:

| # | Column | Description | Field Name |
|---|--------|-------------|------------|
| 1 | Employee Name | Full employee name | `employee_name` |
| 2 | Payroll Date | YYYY-MM-DD format | `payroll_date` |
| 3 | Gross Salary | Total gross before deductions | `gross_salary` |
| 4 | Allowances | Detailed breakdown with total | `allowances` (JSON) |
| 5 | Unpaid Days | Days of unpaid leave | `unpaid_leave_days` |
| 6 | Unpaid Deduction | Deduction for unpaid leave | `unpaid_leave_deduction` |
| 7 | EPF Employee | Employee EPF contribution | `epf_employee` |
| 8 | EPF Employer | Employer EPF contribution | `epf_employer` |
| 9 | SOCSO Employee | Employee SOCSO contribution | `socso_employee` |
| 10 | SOCSO Employer | Employer SOCSO contribution | `socso_employer` |
| 11 | EIS Employee | Employee EIS contribution | `eis_employee` |
| 12 | EIS Employer | Employer EIS contribution | `eis_employer` |
| 13 | PCB | Monthly tax deduction | `pcb` / `pcb_tax` |
| 14 | SIP | Salary in lieu of notice | `sip_deduction` |
| 15 | Additional EPF | Voluntary EPF contribution | `additional_epf_deduction` |
| 16 | PRS | Private Retirement Scheme | `prs_deduction` |
| 17 | Insurance | Insurance premium deduction | `insurance_premium` |
| 18 | Other Deductions | Miscellaneous deductions | `other_deductions` |
| 19 | Net Salary | Final take-home pay | `net_salary` |
| 20 | Actions | Generate/download payslip | Button |

---

## Implementation Details

### JavaScript Changes (`web/static/js/admin_dashboard.js`)

**Function Updated:** `buildPayrollRunsTable(runs)`

**Key Features:**

1. **Allowances Breakdown**
   ```javascript
   const formatAllowances = (allowances) => {
       // Parses JSON allowances object
       // Shows: "Transport: RM 200.00, Housing: RM 500.00 | Total: RM 700.00"
   }
   ```

2. **Days Formatting**
   ```javascript
   const formatDays = (value) => {
       // Handles half-days: 1.5 displays as "1.5"
       // Whole days: 5.0 displays as "5"
   }
   ```

3. **PCB Fallback**
   ```javascript
   const pcb = run.pcb || run.pcb_tax || run.pcb_amount;
   // Supports multiple field names for backward compatibility
   ```

4. **Responsive Table**
   ```html
   <div style="overflow-x: auto;">
       <table style="width: 100%; min-width: 1800px;">
   ```
   - Horizontal scroll for small screens
   - Minimum column widths ensure readability

---

## Display Examples

### Allowances Column

**Format:** Detailed breakdown with total

```
Transport: RM 200.00, Housing: RM 500.00, Meal: RM 150.00 | Total: RM 850.00
```

If no allowances:
```
None
```

### Unpaid Days Column

**Format:** Supports half-days

```
0        → "0"
1.0      → "1"
1.5      → "1.5"
5.0      → "5"
```

### Statutory Contributions

**EPF/SOCSO/EIS Columns:** Show individual employee and employer portions

```
EPF Employee:   RM 275.00
EPF Employer:   RM 300.00
SOCSO Employee: RM 12.50
SOCSO Employer: RM 43.75
EIS Employee:   RM 5.00
EIS Employer:   RM 5.00
```

This allows for transparent verification of statutory contribution calculations.

---

## Benefits of Detailed View

### 1. **Transparency**
- Employees can verify all deductions
- Administrators can audit payroll calculations
- Clear breakdown of where money goes

### 2. **Compliance**
- Shows statutory contributions (EPF, SOCSO, EIS) separately
- Displays PCB (monthly tax) clearly
- Tracks voluntary deductions (Additional EPF, PRS)

### 3. **Debugging**
- Easy to spot calculation errors
- Can verify contribution rates
- Allowances breakdown shows component amounts

### 4. **Reconciliation**
- Matches official payslip format
- All components visible for cross-checking
- Supports audit trails

---

## Technical Notes

### Table Styling

```javascript
// Smaller font for readability
font-size: 13px

// Minimum column widths
min-width: 70px to 150px (varies by column)

// Horizontal scroll container
<div style="overflow-x: auto;">
```

### Data Handling

**Allowances:** Parsed from JSON, formatted with labels
**Currency:** All values formatted with `formatCurrency()` helper
**Null/Undefined:** Handled gracefully, displays "RM 0.00"

---

## Comparison Result

| Aspect | Python GUI | HTML (Before) | HTML (After) | Status |
|--------|-----------|---------------|--------------|--------|
| **Column Count** | 20 columns | 8 columns | 20 columns | ✅ Match |
| **Statutory Breakdown** | EPF/SOCSO/EIS separate | Total only | EPF/SOCSO/EIS separate | ✅ Match |
| **Allowances Detail** | Itemized with total | Not shown | Itemized with total | ✅ Match |
| **Unpaid Leave** | Days + Deduction | Not shown | Days + Deduction | ✅ Match |
| **Other Deductions** | 5 separate columns | Total only | 5 separate columns | ✅ Match |
| **Actions** | Generate Payslip | Download Payslip | Generate Payslip | ✅ Match |

---

## Conclusion

✅ **100% Column Parity Achieved**

The HTML GUI payroll history table now displays the exact same 20 columns as the Python GUI, with:
- Complete statutory contribution breakdown (EPF, SOCSO, EIS)
- Detailed allowances with itemization
- Unpaid leave tracking (days + deduction)
- Individual deduction columns (PCB, SIP, Additional EPF, PRS, Insurance, Other)
- Full transparency and audit capability

The implementation matches the Python GUI's Malaysian payroll structure, following the correct sequence:
1. Gross Salary + Allowances
2. Unpaid Leave Deduction
3. Statutory Contributions (EPF, SOCSO, EIS)
4. PCB Tax
5. Other Deductions
6. Net Salary

---

**Updated:** 2025-11-24  
**Commit:** 145dd59  
**Status:** Complete - Ready for production use
