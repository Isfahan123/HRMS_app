# Table Name Mismatches - FOUND THE REAL ISSUE!

## The Problem

You're absolutely right! The tables DO exist in your database, but the web_app.py code is looking for the WRONG table names.

## Table Name Mismatches

| Code Queries For | Actual Table Name | Status |
|------------------|-------------------|---------|
| `lhdn_tax_rates` | `progressive_tax_brackets` | ❌ MISMATCH |
| `lhdn_relief_max` | `tax_relief_max_config` | ❌ MISMATCH |
| `lhdn_relief_overrides` | May exist or needs creation | ⚠️ CHECK |
| `public_holidays` | `calendar_holidays` | ❌ MISMATCH |
| `leave_entitlements` | `leave_caps` + `leave_caps_tiers` | ❌ MISMATCH |
| `variable_percentage_rules` | Likely correct | ✅ OK |
| `employee_history` | Likely correct | ✅ OK |

## Detailed Fixes Needed

### 1. Tax Rates (Line ~1125 in web_app.py)

**Current Code:**
```python
response = supabase.table("lhdn_tax_rates").select("*").order("income_from").execute()
```

**Should Be:**
```python
response = supabase.table("progressive_tax_brackets").select("*").eq("config_name", "default").order("bracket_order").execute()
```

**Table Structure:**
- `progressive_tax_brackets` has: `bracket_order`, `lower_bound`, `upper_bound`, `rate`
- Not: `income_from`, `income_to`, `rate_percent`

### 2. Tax Relief Maximums (Line ~1205 in web_app.py)

**Current Code:**
```python
response = supabase.table("lhdn_relief_max").select("*").execute()
```

**Should Be:**
```python
response = supabase.table("tax_relief_max_config").select("*").eq("config_name", "default").execute()
```

**Table Structure:**
- `tax_relief_max_config` has columns like:
  - `personal_relief_max`
  - `spouse_relief_max`
  - `child_relief_max`
  - `parent_medical_max`
  - `lifestyle_max`
  - etc. (20+ relief categories as columns)

### 3. Public Holidays (Line ~1487 in web_app.py)

**Current Code:**
```python
response = supabase.table("public_holidays").select("*")...execute()
```

**Should Be:**
```python
response = supabase.table("calendar_holidays").select("*")...execute()
```

**Table Structure:**
- `calendar_holidays` has: `date`, `name`, `state`, `is_national`, `is_observance`

### 4. Leave Entitlements (Line ~1406 in web_app.py)

**Current Code:**
```python
response = supabase.table("leave_entitlements").select("*").execute()
```

**Should Be:**
```python
# Need to join two tables
tiers_response = supabase.table("leave_caps_tiers").select("*").execute()
caps_response = supabase.table("leave_caps").select("*").execute()
# Then combine the data
```

**Table Structure:**
- `leave_caps_tiers` has: `id`, `label`, `min_years`, `max_years`
- `leave_caps` has: `tier_id`, `leave_type`, `cap`

### 5. Relief Overrides (Line ~1251 in web_app.py)

**Current Code:**
```python
response = supabase.table("lhdn_relief_overrides").select("*").execute()
```

**May Need:**
- Check if `relief_item_overrides` table exists (from create_relief_overrides_tables.sql)
- Or create new table matching the expected schema

## Why This Happened

The web_app.py was written to use simplified table names, but the actual database uses the original Python desktop app's table structure which has:
- More descriptive names
- Different schemas
- Split tables (like leave_caps split into two tables)

## Solution Approach

Two options:

### Option A: Fix the Code (Recommended)
Update web_app.py to use the correct existing table names and adapt queries to match the actual schema.

### Option B: Create Alias Views
Create database views with the names the code expects:
```sql
CREATE VIEW lhdn_tax_rates AS SELECT ... FROM progressive_tax_brackets;
CREATE VIEW lhdn_relief_max AS SELECT ... FROM tax_relief_max_config;
CREATE VIEW public_holidays AS SELECT ... FROM calendar_holidays;
```

## Next Steps

I'll fix the web_app.py to use the correct table names and adapt the data transformations to match the actual database schema.
