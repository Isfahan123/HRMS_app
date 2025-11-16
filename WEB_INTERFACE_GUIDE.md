# HRMS Web Interface - User Guide

## 🚀 Getting Started

### Important: How to Access the Web Interface

**✅ CORRECT Way:**
```bash
# 1. Start the web server
python start_web.py

# 2. Open your browser and navigate to:
http://localhost:8000
```

**❌ WRONG Way:**
- Do NOT open the HTML files directly by double-clicking them
- Do NOT use file:// URLs (file:///path/to/dashboard.html)
- This will cause CSS and JavaScript to not load properly!

## 📱 Understanding the Dashboard Interface

### Tab Navigation

When you first log in, you'll see the dashboard with multiple tabs at the top:

**For Employees:**
- 🏠 Home - Summary view
- 👤 Profile - Your personal information
- 📅 Attendance - Clock in/out and view history
- 📬 Leave Request - Submit and view leave requests
- 💸 Payroll - View payslips and payroll history
- 🗂 Engagements - Training and trips

**For Admins:**
- 👥 Profiles - Manage all employees
- 📋 Attendance - View all attendance records
- 📅 Leaves - Approve/reject leave requests
- 💸 Payroll - **Run payroll** and manage payroll settings
- 💰 Bonuses - Manage employee bonuses
- 📈 Salary History - View salary changes
- 📚 Activities - Training and trip management
- 🧾 Employment History - Track employee history

### How to Navigate

1. **Click on a tab** to view its content
   - Only ONE tab is visible at a time
   - The active tab has a purple/gradient background
   - Other tabs are white/gray

2. **Within each tab, look for subtabs**
   - Many tabs have subtabs for different functions
   - Subtabs appear as smaller buttons below the main tab title
   - Example: Payroll tab has subtabs for History, Contributions, Tax Config, etc.

3. **Subtabs within subtabs**
   - Some sections have multiple levels
   - Example: LHDN Tax Config has Tax Rates, Relief Max, Overrides subtabs

## 💸 Payroll Tab - Complete Guide

### Admin Payroll Functions

When you click on the **💸 Payroll** tab, you'll see these subtabs:

1. **Payroll History** (Default view)
   - **Run Payroll form** - Select month and run payroll
   - Month filters (Jan, Feb, Mar, etc.) to view specific months
   - Export to CSV button
   - Table showing all payroll runs

2. **Skipped Payroll**
   - View records of skipped payroll

3. **View Contributions**
   - EPF, SOCSO, and EIS contribution details

4. **💰 Bonuses**
   - Manage bonuses (also accessible from Bonus tab)

5. **📊 Variable %**
   - Variable percentage configuration

6. **🏛️ LHDN Tax**
   - **Tax Rates** - Configure resident/non-resident tax brackets
   - **Tax Relief Max** - Set maximum relief amounts
   - **Relief Overrides** - Employee-specific overrides

### Where is "Run Payroll"?

**Location:** Payroll Tab → Payroll History Subtab → Top of page

**Steps to access:**
1. Click on "💸 Payroll" tab
2. Make sure "Payroll History" subtab is selected (it's active by default)
3. You'll see the "Run Payroll" form at the top
4. Select a month and click "Run Payroll" button

## 📅 Leave Management

### Admin Leave Functions

When you click on the **📅 Leaves** tab, you'll see these subtabs:

1. **Pending** - Approve/reject pending leave requests
2. **Approved/Rejected** - View processed requests
3. **Submit Leave Request** - Submit leave for employees
4. **Annual Leave Balance** - View all employees' annual leave
5. **Sick Leave Balance** - View sick leave balances
6. **📊 Unpaid Leave** - Track unpaid leave
7. **Calendar / Holidays** - Visual calendar view
8. **⚙️ Configuration** - Configure leave types and entitlements

### Employee Leave Functions

**Subtabs:**
1. **Submit Leave Request** - Submit new leave request
2. **My Leave Requests** - View your submitted requests
3. **📅 Calendar View** - See your leave on a calendar

## 🔍 Troubleshooting

### Problem: "I don't see any subtabs"

**Solution:**
1. Make sure you've clicked on the main tab first
2. Subtabs only appear INSIDE the active tab
3. Check if JavaScript is enabled in your browser
4. Verify you're accessing via http://localhost:8000, not file://

### Problem: "Everything looks unstyled"

**Solution:**
1. You're probably opening the HTML file directly
2. You MUST run the web server: `python start_web.py`
3. Then access via http://localhost:8000

### Problem: "Buttons don't work"

**Solution:**
1. Check browser console for JavaScript errors (F12 key)
2. Make sure you're logged in (check sessionStorage)
3. Verify web server is running
4. Try refreshing the page (Ctrl+R or Cmd+R)

### Problem: "Some features say 'coming soon'"

**Solution:**
- Some advanced features are still in development
- Core features (Run Payroll, Leave Management, Attendance) are fully functional
- Check MISSING_FEATURES_ANALYSIS.md for feature status

## 🎯 Quick Reference

### Running Payroll (Admin)
1. Log in as admin
2. Click "💸 Payroll" tab
3. Ensure "Payroll History" subtab is active
4. Find "Run Payroll" form at top
5. Select month
6. Click "Run Payroll" button

### Approving Leave (Admin)
1. Log in as admin
2. Click "📅 Leaves" tab
3. Click "Pending" subtab
4. Review requests
5. Click Approve/Reject buttons

### Submitting Leave (Employee)
1. Log in
2. Click "📬 Leave Request" tab
3. Click "Submit Leave Request" subtab
4. Fill out the form
5. Click "Submit Leave Request" button

### Editing Profile (Employee)
1. Log in
2. Click "👤 Profile" tab
3. Click "Edit Profile" button
4. Update information
5. Click "Save Changes"

## 📞 Need Help?

1. Check this guide first
2. Review QUICKSTART_WEB.md for setup instructions
3. Check MISSING_FEATURES_ANALYSIS.md for feature availability
4. Look for error messages in browser console (F12)

## 🎨 Visual Guide

### Tab Structure Example:

```
[👥 Profiles] [📋 Attendance] [📅 Leaves] [💸 Payroll*] [💰 Bonuses]
                                            ↓
        [Payroll History*] [Skipped] [Contributions] [💰 Bonuses] [📊 Variable %] [🏛️ LHDN Tax]
                ↓
        🔹 Run Payroll Form
        🔹 Payroll Runs Table
           ↓
           [All*] [Jan] [Feb] [Mar] [Apr] [May] [Jun] [Jul] [Aug] [Sep] [Oct] [Nov] [Dec]
```

*Active/visible sections

## ✅ Checklist: Is Everything Working?

- [ ] Can you see the login page when accessing http://localhost:8000?
- [ ] Can you log in with valid credentials?
- [ ] Can you see the main dashboard tabs at the top?
- [ ] Can you click on different tabs to switch views?
- [ ] Can you see subtabs within each tab?
- [ ] Can you see the "Run Payroll" form in Payroll → Payroll History?
- [ ] Can you see forms, tables, and buttons (not just "coming soon" text)?

If you answered "No" to any question, refer to the Troubleshooting section above.

---

**Remember:** The web interface is fully functional and mirrors most desktop app features. Make sure you're accessing it correctly through the web server!
