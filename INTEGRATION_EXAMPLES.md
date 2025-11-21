# Integration Examples - Using New GUI Components

## Quick Start Guide

This document shows practical examples of how to integrate the new GUI components into existing HRMS code.

---

## 1. Employee Selector Integration

### Example A: Bonus Form

**Current Code (using dropdown):**
```html
<select id="bonusEmployeeId" required>
    <option value="">Select Employee</option>
    <!-- Loaded dynamically -->
</select>
```

**Enhanced Code (using Employee Selector):**
```html
<div style="display: flex; gap: 10px; align-items: center;">
    <input type="hidden" id="bonusEmployeeId" required>
    <input type="text" id="bonusEmployeeName" readonly 
           style="flex: 1; padding: 8px;" 
           placeholder="Click to select employee">
    <button type="button" class="btn-secondary" 
            onclick="openEmployeeSelectorForBonus()">
        🔍 Select Employee
    </button>
</div>

<script>
function openEmployeeSelectorForBonus() {
    employeeSelector.open((employee) => {
        document.getElementById('bonusEmployeeId').value = employee.id;
        document.getElementById('bonusEmployeeName').value = employee.full_name;
    });
}
</script>
```

### Example B: Engagement/Training Assignment

```javascript
// In admin_dashboard.js or engagements section
function selectEmployeeForEngagement() {
    employeeSelector.open((employee) => {
        // Populate form fields
        document.getElementById('engagementEmployeeId').value = employee.id;
        document.getElementById('engagementEmployeeName').value = employee.full_name;
        document.getElementById('engagementDepartment').value = employee.department;
        
        // Show success notification
        showInfo(`Selected: ${employee.full_name} (${employee.department})`);
    });
}
```

### Example C: Multiple Employee Selection

For forms that need to assign something to multiple employees:

```html
<div id="selectedEmployeesList"></div>
<button onclick="addAnotherEmployee()" class="btn-secondary">
    ➕ Add Employee
</button>

<script>
const selectedEmployees = [];

function addAnotherEmployee() {
    employeeSelector.open((employee) => {
        // Check if already added
        if (selectedEmployees.find(e => e.id === employee.id)) {
            showWarning('Employee already added!');
            return;
        }
        
        // Add to list
        selectedEmployees.push(employee);
        updateSelectedEmployeesList();
        showSuccess(`Added ${employee.full_name}`);
    });
}

function updateSelectedEmployeesList() {
    const listDiv = document.getElementById('selectedEmployeesList');
    listDiv.innerHTML = selectedEmployees.map((emp, index) => `
        <div style="display: flex; justify-content: space-between; align-items: center; 
                    padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px;">
            <div>
                <strong>${emp.full_name}</strong>
                <br>
                <small>${emp.email} - ${emp.department}</small>
            </div>
            <button onclick="removeEmployee(${index})" class="btn-danger">Remove</button>
        </div>
    `).join('');
}

function removeEmployee(index) {
    const emp = selectedEmployees[index];
    showConfirm(`Remove ${emp.full_name}?`, () => {
        selectedEmployees.splice(index, 1);
        updateSelectedEmployeesList();
        showSuccess('Employee removed');
    });
}
</script>
```

---

## 2. Export Utility Integration

### Example A: Export Employee Table

**Add to Employees Tab:**
```html
<!-- In admin_dashboard.html, Employees tab -->
<div style="display: flex; gap: 10px; margin-bottom: 20px;">
    <button id="addEmployeeBtn" class="btn-primary">Add New Employee</button>
    <button onclick="exportEmployees()" class="btn-secondary">
        📤 Export Employees
    </button>
</div>

<script>
async function exportEmployees() {
    try {
        // Show loading notification
        const loadingId = showLoading('Preparing export...');
        
        // Fetch employee data
        const response = await fetch('/api/admin/employees');
        const employees = await response.json();
        
        // Dismiss loading
        notificationSystem.dismiss(loadingId);
        
        // Show export modal with format options
        exportUtility.showExportModal(employees, 'employees', {
            columns: ['full_name', 'email', 'department', 'position', 'date_joined', 'salary']
        });
    } catch (error) {
        showError('Failed to export employees: ' + error.message);
    }
}
</script>
```

### Example B: Export Payroll with Custom Formatting

```javascript
async function exportPayrollWithFormatting() {
    try {
        const response = await fetch('/api/admin/payroll/runs');
        const payrollData = await response.json();
        
        // Define custom template with formatters
        const template = {
            employee_name: { 
                label: 'Employee Name' 
            },
            employee_id: { 
                label: 'Employee ID' 
            },
            basic_salary: { 
                label: 'Basic Salary (RM)', 
                format: (val) => exportUtility.formatCurrency(val) 
            },
            epf_employee: { 
                label: 'EPF Employee (RM)', 
                format: (val) => exportUtility.formatCurrency(val) 
            },
            epf_employer: { 
                label: 'EPF Employer (RM)', 
                format: (val) => exportUtility.formatCurrency(val) 
            },
            net_pay: { 
                label: 'Net Pay (RM)', 
                format: (val) => exportUtility.formatCurrency(val) 
            },
            payroll_date: { 
                label: 'Payroll Date', 
                format: (val) => exportUtility.formatDate(val) 
            }
        };
        
        exportUtility.exportWithTemplate(payrollData, template, 'payroll_report.csv');
        showSuccess('Payroll exported successfully!');
    } catch (error) {
        showError('Export failed: ' + error.message);
    }
}
```

### Example C: Quick Table Export

For any existing table, add this button:

```html
<button onclick="exportUtility.exportTableToCSV('employeeTable', 'employees.csv')" 
        class="btn-secondary">
    📤 Quick Export
</button>
```

---

## 3. Notification System Integration

### Example A: Replace Alert in Form Submission

**Old Code:**
```javascript
async function saveEmployee(data) {
    try {
        const response = await fetch('/api/admin/employees', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            alert('Employee saved successfully!');  // ❌ Old way
            location.reload();
        } else {
            alert('Failed to save employee');  // ❌ Old way
        }
    } catch (error) {
        alert('Error: ' + error.message);  // ❌ Old way
    }
}
```

**New Code:**
```javascript
async function saveEmployee(data) {
    const loadingId = showLoading('Saving employee...'); // ✅ Show loading
    
    try {
        const response = await fetch('/api/admin/employees', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        notificationSystem.dismiss(loadingId); // Dismiss loading
        
        if (response.ok) {
            showSuccess('Employee saved successfully!');  // ✅ New way
            setTimeout(() => location.reload(), 1000); // Give time to see notification
        } else {
            const error = await response.json();
            showError('Failed to save: ' + (error.message || 'Unknown error'));  // ✅ New way
        }
    } catch (error) {
        notificationSystem.dismiss(loadingId);
        showError('Network error: ' + error.message);  // ✅ New way
    }
}
```

### Example B: Replace Confirm in Delete Action

**Old Code:**
```javascript
function deleteEmployee(id, name) {
    if (confirm(`Delete employee ${name}?`)) {  // ❌ Old way
        // Perform delete
        fetch(`/api/admin/employees/${id}`, { method: 'DELETE' })
            .then(() => {
                alert('Deleted successfully');
                loadEmployees();
            });
    }
}
```

**New Code:**
```javascript
function deleteEmployee(id, name) {
    showConfirm(
        `Are you sure you want to delete employee ${name}? This action cannot be undone.`,
        async () => {  // ✅ Confirm callback
            const loadingId = showLoading('Deleting employee...');
            
            try {
                const response = await fetch(`/api/admin/employees/${id}`, { 
                    method: 'DELETE' 
                });
                
                notificationSystem.dismiss(loadingId);
                
                if (response.ok) {
                    showSuccess(`${name} deleted successfully`);
                    loadEmployees();
                } else {
                    showError('Failed to delete employee');
                }
            } catch (error) {
                notificationSystem.dismiss(loadingId);
                showError('Delete failed: ' + error.message);
            }
        },
        () => {  // ✅ Cancel callback (optional)
            showInfo('Delete cancelled');
        }
    );
}
```

### Example C: Form Validation with Warnings

```javascript
function validatePayrollForm() {
    const month = document.getElementById('payrollMonth').value;
    const skipUnpaidLeave = document.getElementById('skipUnpaidLeave').checked;
    
    if (!month) {
        showError('Please select a payroll month');
        return false;
    }
    
    if (!skipUnpaidLeave) {
        showWarning('Employees with unpaid leave will be included in this payroll run');
    }
    
    showInfo('Validating payroll data...');
    return true;
}

async function runPayroll() {
    if (!validatePayrollForm()) {
        return;
    }
    
    showConfirm(
        'Run payroll for selected month? This will generate pay slips for all active employees.',
        async () => {
            const loadingId = showLoading('Running payroll... This may take a minute.');
            
            try {
                const response = await fetch('/api/admin/payroll/run', {
                    method: 'POST',
                    body: JSON.stringify({ month: document.getElementById('payrollMonth').value })
                });
                
                notificationSystem.dismiss(loadingId);
                
                if (response.ok) {
                    const result = await response.json();
                    showSuccess(`Payroll completed! Processed ${result.employee_count} employees.`);
                    loadPayrollHistory();
                } else {
                    showError('Payroll run failed. Please try again.');
                }
            } catch (error) {
                notificationSystem.dismiss(loadingId);
                showError('Error running payroll: ' + error.message);
            }
        }
    );
}
```

---

## 4. Combined Examples

### Example: Complete CRUD Operations with All Components

```javascript
// ============================================
// BONUS MANAGEMENT WITH ALL NEW COMPONENTS
// ============================================

// 1. CREATE - Add Bonus
function showAddBonusForm() {
    document.getElementById('bonusForm').reset();
    document.getElementById('bonusModal').style.display = 'block';
}

function selectEmployeeForBonus() {
    employeeSelector.open((employee) => {
        document.getElementById('bonusEmployeeId').value = employee.id;
        document.getElementById('bonusEmployeeName').value = employee.full_name;
        showInfo(`Selected: ${employee.full_name}`);
    });
}

async function saveBonus(formData) {
    const loadingId = showLoading('Saving bonus...');
    
    try {
        const response = await fetch('/api/admin/bonuses', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        notificationSystem.dismiss(loadingId);
        
        if (response.ok) {
            showSuccess('Bonus saved successfully!');
            document.getElementById('bonusModal').style.display = 'none';
            loadBonuses();
        } else {
            showError('Failed to save bonus');
        }
    } catch (error) {
        notificationSystem.dismiss(loadingId);
        showError('Error: ' + error.message);
    }
}

// 2. READ - List Bonuses
async function loadBonuses() {
    try {
        const response = await fetch('/api/admin/bonuses');
        const bonuses = await response.json();
        renderBonusTable(bonuses);
    } catch (error) {
        showError('Failed to load bonuses: ' + error.message);
    }
}

// 3. UPDATE - Edit Bonus
function editBonus(bonusId) {
    // Load bonus data and show form
    showInfo('Loading bonus details...');
}

// 4. DELETE - Remove Bonus
function deleteBonus(bonusId, employeeName) {
    showConfirm(
        `Delete bonus for ${employeeName}?`,
        async () => {
            const loadingId = showLoading('Deleting bonus...');
            
            try {
                const response = await fetch(`/api/admin/bonuses/${bonusId}`, {
                    method: 'DELETE'
                });
                
                notificationSystem.dismiss(loadingId);
                
                if (response.ok) {
                    showSuccess('Bonus deleted successfully');
                    loadBonuses();
                } else {
                    showError('Failed to delete bonus');
                }
            } catch (error) {
                notificationSystem.dismiss(loadingId);
                showError('Error: ' + error.message);
            }
        }
    );
}

// 5. EXPORT - Download Bonuses
async function exportBonuses() {
    try {
        const loadingId = showLoading('Preparing export...');
        
        const response = await fetch('/api/admin/bonuses');
        const bonuses = await response.json();
        
        notificationSystem.dismiss(loadingId);
        
        // Custom template for bonus export
        const template = {
            employee_name: { label: 'Employee Name' },
            bonus_type: { label: 'Bonus Type' },
            amount: { 
                label: 'Amount (RM)', 
                format: (val) => exportUtility.formatCurrency(val) 
            },
            effective_date: { 
                label: 'Effective Date', 
                format: (val) => exportUtility.formatDate(val) 
            },
            status: { label: 'Status' }
        };
        
        exportUtility.exportWithTemplate(bonuses, template, 'bonuses_report.csv');
        showSuccess('Bonuses exported successfully!');
    } catch (error) {
        showError('Export failed: ' + error.message);
    }
}
```

---

## 5. Bulk Operations Example

```javascript
// Example: Bulk bonus assignment
const selectedEmployeesForBonus = [];

function showBulkBonusForm() {
    selectedEmployeesForBonus.length = 0;
    document.getElementById('bulkBonusModal').style.display = 'block';
    updateBulkEmployeeList();
}

function addEmployeeToBulkBonus() {
    employeeSelector.open((employee) => {
        if (selectedEmployeesForBonus.find(e => e.id === employee.id)) {
            showWarning('Employee already added!');
            return;
        }
        
        selectedEmployeesForBonus.push(employee);
        updateBulkEmployeeList();
        showInfo(`Added: ${employee.full_name}`);
    });
}

function updateBulkEmployeeList() {
    const list = document.getElementById('bulkEmployeeList');
    list.innerHTML = selectedEmployeesForBonus.map((emp, idx) => `
        <div style="padding: 8px; margin: 4px 0; background: #f5f5f5; border-radius: 4px;
                    display: flex; justify-content: space-between; align-items: center;">
            <span>${emp.full_name} - ${emp.department}</span>
            <button onclick="removeFromBulk(${idx})" class="btn-danger btn-sm">×</button>
        </div>
    `).join('');
    
    document.getElementById('bulkCount').textContent = selectedEmployeesForBonus.length;
}

function removeFromBulk(index) {
    const emp = selectedEmployeesForBonus[index];
    selectedEmployeesForBonus.splice(index, 1);
    updateBulkEmployeeList();
    showInfo(`Removed: ${emp.full_name}`);
}

async function saveBulkBonus() {
    if (selectedEmployeesForBonus.length === 0) {
        showWarning('Please add at least one employee');
        return;
    }
    
    const bonusAmount = document.getElementById('bulkBonusAmount').value;
    const bonusType = document.getElementById('bulkBonusType').value;
    
    if (!bonusAmount) {
        showError('Please enter bonus amount');
        return;
    }
    
    showConfirm(
        `Assign ${bonusAmount} RM bonus to ${selectedEmployeesForBonus.length} employee(s)?`,
        async () => {
            const loadingId = showLoading(`Processing bonuses for ${selectedEmployeesForBonus.length} employees...`);
            let successCount = 0;
            let failCount = 0;
            
            for (const emp of selectedEmployeesForBonus) {
                try {
                    await fetch('/api/admin/bonuses', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            employee_id: emp.id,
                            amount: bonusAmount,
                            type: bonusType
                        })
                    });
                    successCount++;
                } catch (error) {
                    failCount++;
                }
            }
            
            notificationSystem.dismiss(loadingId);
            
            if (failCount === 0) {
                showSuccess(`Successfully assigned bonuses to all ${successCount} employees!`);
            } else {
                showWarning(`Assigned ${successCount} bonuses, ${failCount} failed.`);
            }
            
            document.getElementById('bulkBonusModal').style.display = 'none';
            loadBonuses();
        }
    );
}
```

---

## Testing Checklist

After implementing these integrations:

- [ ] Employee selector works on all forms
- [ ] Export buttons appear on all tables
- [ ] All alerts replaced with notifications
- [ ] All confirms replaced with custom dialogs
- [ ] Loading indicators show during async operations
- [ ] Success messages appear after actions
- [ ] Error messages show when operations fail
- [ ] Mobile responsiveness verified
- [ ] Cross-browser compatibility tested

---

## Tips for Best Practices

1. **Always use loading notifications for async operations**
   ```javascript
   const loadingId = showLoading('Processing...');
   // ... do work ...
   notificationSystem.dismiss(loadingId);
   ```

2. **Provide feedback for all user actions**
   ```javascript
   showSuccess('Action completed');
   showError('Action failed');
   showInfo('Action in progress');
   showWarning('Please confirm');
   ```

3. **Use employee selector for better UX**
   - Instead of long dropdowns
   - Especially when > 20 employees

4. **Standardize exports across all tables**
   - Use consistent file naming
   - Apply proper formatting
   - Include all relevant columns

5. **Test on mobile devices**
   - Notifications should be readable
   - Employee selector should be usable
   - Export should work on mobile

---

**Need Help?**
- Check `NEW_GUI_COMPONENTS.md` for complete API reference
- Review console for errors
- Test components individually first
- Gradually migrate existing code

**Status:** Ready for implementation  
**Difficulty:** Easy to Medium  
**Impact:** High - Better UX across entire application
