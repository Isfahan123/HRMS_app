# Fiscal Payroll Year (Start From Any Month)

You can run payroll starting from any month (e.g., Nov 2025 → Oct 2026) while preserving official PCB taxation rules that are based on the calendar year.

Key points:
- PCB (tax) is always calculated on the calendar year per LHDN. This does not change.
- To start mid‑year (e.g., first payroll in Nov), seed a YTD baseline up to October so November PCB is correct.
- For reports/UI, you can set the start month for a "payroll year" window without changing tax behavior.

## 1) Configure the Payroll Year Start Month

Run the SQL migration:

```sql
-- migrate_add_payroll_year_start_month.sql
ALTER TABLE IF EXISTS public.payroll_settings
ADD COLUMN IF NOT EXISTS payroll_year_start_month integer NOT NULL DEFAULT 1;
ALTER TABLE public.payroll_settings
ADD CONSTRAINT IF NOT EXISTS chk_payroll_settings_year_start_month
  CHECK (payroll_year_start_month >= 1 AND payroll_year_start_month <= 12);
```

Then set it via code (example):

```python
from services.supabase_service import update_payroll_settings
update_payroll_settings(payroll_year_start_month=11)  # 11 = November
```

This setting controls reporting windows you may build (e.g., Nov→Oct). PCB remains calendar‑year.

## 2) Seed YTD Baselines For Mid‑Year Starts (Required for correct PCB)

When you begin in November 2025, insert a snapshot row for October 2025 into `payroll_ytd_accumulated` for each employee with totals from Jan→Oct.

Use the helper:

```python
from services.supabase_service import set_ytd_baseline

ok = set_ytd_baseline(
    employee_email='employee@example.com',
    year=2025,
    month=10,  # previous month
    accumulators={
        'accumulated_gross_salary_ytd': 123456.78,
        'accumulated_epf_employee_ytd': 8901.23,
        'accumulated_pcb_ytd': 4567.89,
        'accumulated_zakat_ytd': 0.0,
        'accumulated_tax_reliefs_ytd': 2000.0,
        'accumulated_socso_employee_ytd': 300.0,
        'accumulated_eis_employee_ytd': 50.0,
    }
)
print('Baseline OK?', ok)
```

The payroll engine already reads the previous month’s YTD for PCB. By inserting this baseline, the first live month (November) has the correct YTD context.

## 3) No Schema Change Needed For Baselines

`payroll_ytd_accumulated` already stores YTD per (employee_email, year, month). You only need to insert the baseline rows. No extra columns are required.

## 4) Notes & Best Practices
- PCB, EPF relief caps, and other statutory rules remain calendar‑year. Do not alter these to a custom fiscal year.
- If you prefer a CSV import for baselines, add a small script to read a CSV and call `set_ytd_baseline` per row.
- For UI YTD displays (e.g., Admin Payroll), you may sum a rolling 12‑month window from `payroll_year_start_month` for a fiscal view while keeping PCB as is.
