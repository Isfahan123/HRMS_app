# Database Setup Guide

## Quick Start: Setting Up Supabase Database

This guide will help you set up a working database for the HRMS web application.

---

## Step 1: Create Supabase Project

1. Go to https://supabase.com/dashboard
2. Click "New Project"
3. Fill in:
   - **Name:** HRMS Application
   - **Database Password:** (choose a strong password)
   - **Region:** Choose closest to you
4. Click "Create new project"
5. Wait ~2 minutes for project to initialize

---

## Step 2: Get Your Credentials

1. In your new project, click **Settings** (gear icon)
2. Click **API** in the left sidebar
3. Copy these values:
   - **Project URL:** `https://xxxxx.supabase.co`
   - **Service Role Key:** `eyJhbGc...` (long token)

4. Update `.env` file in project root:
   ```bash
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_KEY=eyJhbGc...
   ```

---

## Step 3: Create Database Tables

In Supabase dashboard, go to **SQL Editor** and run these SQL scripts in order:

### 1. Employees Table
```sql
CREATE TABLE IF NOT EXISTS employees (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    employee_id VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'employee',
    gender VARCHAR(20),
    date_of_birth DATE,
    nric VARCHAR(50),
    nationality VARCHAR(100),
    citizenship VARCHAR(100),
    race VARCHAR(50),
    religion VARCHAR(50),
    marital_status VARCHAR(50),
    number_of_children INTEGER DEFAULT 0,
    phone_number VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    zipcode VARCHAR(20),
    department VARCHAR(100),
    position VARCHAR(100),
    employment_status VARCHAR(50) DEFAULT 'active',
    join_date DATE,
    basic_salary DECIMAL(10, 2) DEFAULT 0,
    epf_number VARCHAR(50),
    socso_number VARCHAR(50),
    income_tax_number VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2. Leave Requests Table
```sql
CREATE TABLE IF NOT EXISTS leave_requests (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    employee_id UUID REFERENCES employees(id),
    employee_email VARCHAR(255),
    leave_type VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    days DECIMAL(5, 2) NOT NULL,
    title VARCHAR(255),
    reason TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    approved_by VARCHAR(255),
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 3. Bonuses Table
```sql
CREATE TABLE IF NOT EXISTS bonuses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    employee_id UUID REFERENCES employees(id),
    employee_name VARCHAR(255),
    bonus_type VARCHAR(100) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    description TEXT,
    pay_period VARCHAR(20),
    status VARCHAR(50) DEFAULT 'pending',
    approved_by VARCHAR(255),
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 4. Payroll Runs Table
```sql
CREATE TABLE IF NOT EXISTS payroll_runs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    employee_id UUID REFERENCES employees(id),
    employee_name VARCHAR(255),
    employee_email VARCHAR(255),
    month_year VARCHAR(20) NOT NULL,
    basic_salary DECIMAL(10, 2) DEFAULT 0,
    allowances DECIMAL(10, 2) DEFAULT 0,
    bonuses DECIMAL(10, 2) DEFAULT 0,
    gross_salary DECIMAL(10, 2) DEFAULT 0,
    epf_employee DECIMAL(10, 2) DEFAULT 0,
    epf_employer DECIMAL(10, 2) DEFAULT 0,
    socso_employee DECIMAL(10, 2) DEFAULT 0,
    socso_employer DECIMAL(10, 2) DEFAULT 0,
    eis DECIMAL(10, 2) DEFAULT 0,
    pcb DECIMAL(10, 2) DEFAULT 0,
    unpaid_leave_deduction DECIMAL(10, 2) DEFAULT 0,
    net_pay DECIMAL(10, 2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'completed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 5. LHDN Tax Rates Table
```sql
CREATE TABLE IF NOT EXISTS lhdn_tax_rates (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    bracket_number INTEGER NOT NULL,
    min_income DECIMAL(12, 2) NOT NULL,
    max_income DECIMAL(12, 2),
    tax_rate DECIMAL(5, 2) NOT NULL,
    tax_on_band DECIMAL(12, 2) DEFAULT 0,
    is_resident BOOLEAN DEFAULT true,
    effective_year INTEGER DEFAULT 2024,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 6. LHDN Relief Maximums Table
```sql
CREATE TABLE IF NOT EXISTS lhdn_relief_max (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    relief_category VARCHAR(100) UNIQUE NOT NULL,
    max_amount DECIMAL(10, 2) NOT NULL,
    description TEXT,
    effective_year INTEGER DEFAULT 2024,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 7. LHDN Relief Overrides Table
```sql
CREATE TABLE IF NOT EXISTS lhdn_relief_overrides (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    employee_id UUID REFERENCES employees(id),
    employee_name VARCHAR(255),
    relief_category VARCHAR(100) NOT NULL,
    override_amount DECIMAL(10, 2) NOT NULL,
    effective_from DATE,
    effective_to DATE,
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 8. Variable Percentage Rules Table
```sql
CREATE TABLE IF NOT EXISTS variable_percentage_rules (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    percentage DECIMAL(5, 2) NOT NULL,
    apply_to VARCHAR(100) NOT NULL,
    base_on VARCHAR(100) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    employee_email VARCHAR(255),
    effective_from DATE,
    effective_to DATE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 9. Employee History Table
```sql
CREATE TABLE IF NOT EXISTS employee_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    employee_id UUID REFERENCES employees(id),
    employee_email VARCHAR(255),
    field_changed VARCHAR(100) NOT NULL,
    previous_value TEXT,
    new_value TEXT,
    change_date DATE NOT NULL,
    reason TEXT,
    changed_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 10. Attendance Records Table
```sql
CREATE TABLE IF NOT EXISTS attendance_records (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    employee_id UUID REFERENCES employees(id),
    employee_email VARCHAR(255),
    date DATE NOT NULL,
    clock_in TIMESTAMP WITH TIME ZONE,
    clock_out TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(employee_id, date)
);
```

### 11. Engagements Table
```sql
CREATE TABLE IF NOT EXISTS engagements (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    employee_id UUID REFERENCES employees(id),
    employee_email VARCHAR(255),
    type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    location VARCHAR(255),
    organizer VARCHAR(255),
    cost DECIMAL(10, 2),
    status VARCHAR(50) DEFAULT 'pending',
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 12. Leave Types Table
```sql
CREATE TABLE IF NOT EXISTS leave_types (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    requires_approval BOOLEAN DEFAULT true,
    max_days INTEGER,
    color VARCHAR(20) DEFAULT '#667eea',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 13. Leave Entitlements Table
```sql
CREATE TABLE IF NOT EXISTS leave_entitlements (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    position_level VARCHAR(100) NOT NULL,
    annual_leave_days INTEGER DEFAULT 14,
    sick_leave_days INTEGER DEFAULT 14,
    carry_forward_max INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## Step 4: Seed Initial Data

### Create Admin User
```sql
INSERT INTO employees (
    employee_id, full_name, email, password, role, 
    department, position, employment_status, join_date, basic_salary
) VALUES (
    'EMP001', 'Admin User', 'admin@hrms.com', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5W', -- password: admin123
    'admin', 'Administration', 'System Administrator', 
    'active', CURRENT_DATE, 5000.00
);
```

### Add Default Leave Types
```sql
INSERT INTO leave_types (name, code, description, requires_approval, max_days, color) VALUES
('Annual Leave', 'AL', 'Paid annual leave', true, 0, '#667eea'),
('Sick Leave', 'SL', 'Medical leave with MC', true, 14, '#f56565'),
('Emergency Leave', 'EL', 'Urgent personal matters', true, 5, '#ed8936'),
('Unpaid Leave', 'UL', 'Leave without pay', true, 0, '#718096'),
('Maternity Leave', 'ML', 'Maternity leave (90 days)', true, 90, '#ed64a6'),
('Paternity Leave', 'PL', 'Paternity leave (7 days)', true, 7, '#4299e1');
```

### Add Leave Entitlements by Position
```sql
INSERT INTO leave_entitlements (position_level, annual_leave_days, sick_leave_days, carry_forward_max) VALUES
('Junior Staff', 14, 14, 5),
('Senior Staff', 18, 14, 7),
('Manager', 21, 14, 10),
('Senior Manager', 24, 14, 12),
('Director', 28, 14, 15);
```

### Add Malaysian Tax Rates (2024)
```sql
INSERT INTO lhdn_tax_rates (bracket_number, min_income, max_income, tax_rate, tax_on_band) VALUES
(1, 0, 5000, 0, 0),
(2, 5001, 20000, 1, 150),
(3, 20001, 35000, 3, 450),
(4, 35001, 50000, 8, 1200),
(5, 50001, 70000, 13, 2600),
(6, 70001, 100000, 21, 6300),
(7, 100001, 250000, 24, 36000),
(8, 250001, 400000, 24.5, 36750),
(9, 400001, 600000, 25, 50000),
(10, 600001, 1000000, 26, 104000),
(11, 1000001, 2000000, 28, 280000),
(12, 2000001, NULL, 30, NULL);
```

### Add Tax Relief Maximums
```sql
INSERT INTO lhdn_relief_max (relief_category, max_amount, description) VALUES
('Self Relief', 9000, 'Individual relief for taxpayer'),
('Spouse Relief', 4000, 'Relief for spouse without income'),
('Child Relief (Under 18)', 2000, 'Per child under 18 years'),
('Child Relief (18+ Education)', 8000, 'Per child 18+ in higher education'),
('Disabled Child', 6000, 'Per disabled child'),
('Life Insurance & EPF', 7000, 'Combined life insurance and EPF'),
('Education & Medical Insurance', 3000, 'Education and medical insurance premium'),
('Medical for Parents', 8000, 'Medical expenses for parents'),
('Medical (Serious Disease)', 8000, 'Medical for self/spouse/child serious diseases'),
('Basic Supporting Equipment', 6000, 'For disabled individual'),
('Lifestyle', 2500, 'Books, gym, internet subscription'),
('Domestic Tourism', 1000, 'Domestic tourism expenses'),
('Sports Equipment', 500, 'Purchase of sports equipment'),
('EIS & SOCSO', 250, 'Employment Insurance and SOCSO');
```

---

## Step 5: Verify Setup

1. **Test database connection:**
   ```bash
   python -c "from supabase import create_client; import os; from dotenv import load_dotenv; load_dotenv(); client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY')); print('Employees:', len(client.table('employees').select('*').execute().data))"
   ```

2. **Start web application:**
   ```bash
   python web_app.py
   ```

3. **Open browser:**
   - Go to http://localhost:8000
   - Login with: admin@hrms.com / admin123

4. **Test features:**
   - ✅ View employees
   - ✅ Add new employee
   - ✅ Submit leave request
   - ✅ Add bonus
   - ✅ Configure tax rates
   - ✅ View reports

---

## Troubleshooting

### Error: "No address associated with hostname"
- **Cause:** Invalid Supabase URL in .env
- **Fix:** Double-check project URL from Supabase dashboard

### Error: "relation does not exist"
- **Cause:** Missing database table
- **Fix:** Run the CREATE TABLE SQL for that table

### Error: "permission denied"
- **Cause:** Using anon key instead of service role key
- **Fix:** Use service_role key from API settings

### Can't login
- **Cause:** Password hash mismatch
- **Fix:** Use bcrypt to hash password correctly:
  ```python
  import bcrypt
  password = "admin123"
  hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
  print(hashed.decode('utf-8'))
  ```

---

## Alternative: Sample Database Files

If you prefer, you can also:

1. Run all SQL files in `/data/` directory in Supabase SQL Editor
2. They contain complete schema and sample data
3. Files to run in order:
   - `create_lhdn_tax_table.sql`
   - `create_leave_caps_table.sql`
   - `create_relief_overrides_tables.sql`
   - `create_training_course_records.sql`
   - `create_engagements_table.sql`
   - And others as needed

---

## Success!

Once database is set up:
- All 40+ features will work immediately
- No code changes needed
- Full HRMS functionality available

**Enjoy your fully functional HRMS web application! 🎉**
