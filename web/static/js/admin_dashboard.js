// Admin Dashboard JavaScript logic
// Handles admin dashboard functionality and API calls

document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in as admin
    const userEmail = sessionStorage.getItem('userEmail');
    const userRole = sessionStorage.getItem('userRole');
    
    if (!userEmail || userRole !== 'admin') {
        // Redirect to login if not authenticated as admin
        window.location.href = '/';
        return;
    }
    
    // Initialize admin dashboard
    initializeAdminDashboard();
    setupTabs();
    setupLogout();
    setupOpenCalendar();
    setupEmployeeManagement();
    setupPayrollProcessing();
    setupBonusManagement();
    setupExportHandlers();
    
    async function initializeAdminDashboard() {
        try {
            // Load employee list
            loadEmployeeList();
            
            // Load attendance records
            loadAllAttendance();
            
            // Load leave requests for approval
            loadLeaveRequests();
            
            // Load payroll runs
            loadPayrollRuns();
            
            // Load bonuses
            loadBonuses();
            
        } catch (error) {
            console.error('Error initializing admin dashboard:', error);
        }
    }
    
    async function loadEmployeeList() {
        try {
            const response = await fetch('/api/employees');
            const data = await response.json();
            
            if (data.success && data.data && data.data.length > 0) {
                const tableHtml = buildEmployeeTable(data.data);
                document.getElementById('employeeTable').innerHTML = tableHtml;
            } else {
                document.getElementById('employeeTable').innerHTML = '<p>No employees found.</p>';
            }
        } catch (error) {
            console.error('Error loading employees:', error);
            document.getElementById('employeeTable').innerHTML = '<p>Error loading employee data.</p>';
        }
    }
    
    function buildEmployeeTable(employees) {
        let html = '<table><thead><tr>';
        html += '<th>Name</th><th>Email</th><th>Department</th><th>Position</th><th>Status</th>';
        html += '</tr></thead><tbody>';
        
        employees.forEach(employee => {
            html += '<tr>';
            html += `<td>${employee.full_name || '-'}</td>`;
            html += `<td>${employee.email || '-'}</td>`;
            html += `<td>${employee.department || '-'}</td>`;
            html += `<td>${employee.position || '-'}</td>`;
            html += `<td>${employee.employment_status || '-'}</td>`;
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        return html;
    }
    
    async function loadAllAttendance() {
        try {
            const response = await fetch('/api/admin/attendance');
            const data = await response.json();
            
            if (data.success && data.data && data.data.length > 0) {
                const tableHtml = buildAttendanceTable(data.data);
                document.getElementById('attendanceTab').innerHTML = '<h2>Attendance Management</h2>' + tableHtml;
            } else {
                document.getElementById('attendanceTab').innerHTML = '<h2>Attendance Management</h2><p>No attendance records found.</p>';
            }
        } catch (error) {
            console.error('Error loading attendance:', error);
            document.getElementById('attendanceTab').innerHTML = '<h2>Attendance Management</h2><p>Error loading attendance data.</p>';
        }
    }
    
    function buildAttendanceTable(records) {
        let html = '<table><thead><tr>';
        html += '<th>Employee</th><th>Date</th><th>Check In</th><th>Check Out</th><th>Status</th>';
        html += '</tr></thead><tbody>';
        
        records.forEach(record => {
            html += '<tr>';
            html += `<td>${record.email || '-'}</td>`;
            html += `<td>${record.date || '-'}</td>`;
            html += `<td>${record.check_in_time || '-'}</td>`;
            html += `<td>${record.check_out_time || '-'}</td>`;
            html += `<td>${record.status || '-'}</td>`;
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        return html;
    }
    
    async function loadLeaveRequests() {
        try {
            const response = await fetch('/api/admin/leave-requests');
            const data = await response.json();
            
            if (data.success && data.data && data.data.length > 0) {
                const tableHtml = buildLeaveRequestsTable(data.data);
                document.getElementById('leaveTab').innerHTML = '<h2>Leave Approval</h2>' + tableHtml;
            } else {
                document.getElementById('leaveTab').innerHTML = '<h2>Leave Approval</h2><p>No leave requests found.</p>';
            }
        } catch (error) {
            console.error('Error loading leave requests:', error);
            document.getElementById('leaveTab').innerHTML = '<h2>Leave Approval</h2><p>Error loading leave requests.</p>';
        }
    }
    
    function buildLeaveRequestsTable(requests) {
        let html = '<table><thead><tr>';
        html += '<th>Employee</th><th>Type</th><th>Start Date</th><th>End Date</th><th>Status</th><th>Actions</th>';
        html += '</tr></thead><tbody>';
        
        requests.forEach(request => {
            html += '<tr>';
            html += `<td>${request.employees?.full_name || request.email || '-'}</td>`;
            html += `<td>${request.leave_type || '-'}</td>`;
            html += `<td>${request.start_date || '-'}</td>`;
            html += `<td>${request.end_date || '-'}</td>`;
            html += `<td>${request.status || '-'}</td>`;
            html += '<td>';
            if (request.status === 'pending') {
                html += `<button class="btn-approve" onclick="approveLeave('${request.id}')">Approve</button> `;
                html += `<button class="btn-reject" onclick="rejectLeave('${request.id}')">Reject</button>`;
            } else {
                html += '-';
            }
            html += '</td>';
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        return html;
    }
    
    async function loadPayrollRuns() {
        try {
            const response = await fetch('/api/admin/payroll-runs');
            const data = await response.json();
            
            if (data.success && data.data && data.data.length > 0) {
                const tableHtml = buildPayrollRunsTable(data.data);
                document.getElementById('payrollTab').innerHTML = '<h2>Payroll Processing</h2>' + tableHtml;
            } else {
                document.getElementById('payrollTab').innerHTML = '<h2>Payroll Processing</h2><p>No payroll runs found.</p>';
            }
        } catch (error) {
            console.error('Error loading payroll runs:', error);
            document.getElementById('payrollTab').innerHTML = '<h2>Payroll Processing</h2><p>Error loading payroll data.</p>';
        }
    }
    
    function buildPayrollRunsTable(runs) {
        let html = '<table><thead><tr>';
        html += '<th>Employee</th><th>Month</th><th>Basic Salary</th><th>Net Pay</th><th>Status</th>';
        html += '</tr></thead><tbody>';
        
        runs.forEach(run => {
            html += '<tr>';
            html += `<td>${run.employee_email || '-'}</td>`;
            html += `<td>${run.month_year || '-'}</td>`;
            html += `<td>RM ${parseFloat(run.basic_salary || 0).toFixed(2)}</td>`;
            html += `<td>RM ${parseFloat(run.net_pay || 0).toFixed(2)}</td>`;
            html += `<td>${run.status || '-'}</td>`;
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        return html;
    }
    
    // Global functions for leave approval
    window.approveLeave = async function(leaveId) {
        try {
            const response = await fetch(`/api/admin/leave-requests/${leaveId}/approve`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                alert('Leave request approved successfully');
                loadLeaveRequests(); // Reload the table
            } else {
                alert('Failed to approve leave request: ' + data.message);
            }
        } catch (error) {
            console.error('Error approving leave:', error);
            alert('Error approving leave request');
        }
    };
    
    window.rejectLeave = async function(leaveId) {
        try {
            const response = await fetch(`/api/admin/leave-requests/${leaveId}/reject`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                alert('Leave request rejected successfully');
                loadLeaveRequests(); // Reload the table
            } else {
                alert('Failed to reject leave request: ' + data.message);
            }
        } catch (error) {
            console.error('Error rejecting leave:', error);
            alert('Error rejecting leave request');
        }
    };
    
    function setupTabs() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabPanes = document.querySelectorAll('.tab-pane');
        
        console.log('🔧 Setting up tabs:', tabButtons.length, 'tab buttons found');
        console.log('🔧 Tab panes:', tabPanes.length, 'panes found');
        
        tabButtons.forEach(button => {
            button.addEventListener('click', function() {
                const tabName = this.getAttribute('data-tab');
                console.log('✅ Tab clicked:', tabName);
                
                // Remove active class from all buttons and panes
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabPanes.forEach(pane => pane.classList.remove('active'));
                
                // Add active class to clicked button and corresponding pane
                this.classList.add('active');
                const targetPane = document.getElementById(tabName + 'Tab');
                if (targetPane) {
                    targetPane.classList.add('active');
                    console.log('✅ Activated tab pane:', tabName + 'Tab');
                } else {
                    console.error('❌ Tab pane not found:', tabName + 'Tab');
                }
            });
        });
        
        // Setup subtabs
        setupSubtabs();
    }
    
    function setupSubtabs() {
        const subtabButtons = document.querySelectorAll('.subtab-button');
        
        console.log('🔧 Setting up subtabs:', subtabButtons.length, 'subtab buttons found');
        
        subtabButtons.forEach(button => {
            button.addEventListener('click', function() {
                const subtabName = this.getAttribute('data-subtab');
                const monthValue = this.getAttribute('data-month');
                
                console.log('✅ Subtab clicked:', subtabName || 'Month: ' + monthValue);
                
                // Get parent tab to scope subtab switching
                const parentContainer = this.closest('.tab-pane');
                if (!parentContainer) {
                    console.error('❌ Parent container not found for subtab');
                    return;
                }
                
                // If this is a month tab (for payroll history)
                if (monthValue) {
                    // Handle month tab switching
                    const monthButtons = parentContainer.querySelectorAll('[data-month]');
                    monthButtons.forEach(btn => btn.classList.remove('active'));
                    this.classList.add('active');
                    
                    console.log('✅ Month filter activated:', monthValue);
                    
                    // Filter payroll table by month
                    filterPayrollByMonth(monthValue);
                    return;
                }
                
                // Regular subtab switching
                const containerSubtabButtons = parentContainer.querySelectorAll('.subtab-button:not([data-month])');
                const containerSubtabContents = parentContainer.querySelectorAll('.subtab-content');
                
                containerSubtabButtons.forEach(btn => btn.classList.remove('active'));
                containerSubtabContents.forEach(content => content.classList.remove('active'));
                
                // Add active class to clicked button and corresponding content
                this.classList.add('active');
                const subtabContent = document.getElementById(subtabName + 'Subtab');
                if (subtabContent) {
                    subtabContent.classList.add('active');
                }
            });
        });
        
        // Setup year filter for admin payroll
        const yearFilter = document.getElementById('adminPayrollYearFilter');
        if (yearFilter) {
            yearFilter.addEventListener('change', function() {
                filterPayrollByMonth(document.querySelector('[data-month].active')?.getAttribute('data-month') || 'all');
            });
        }
    }
    
    function filterPayrollByMonth(month) {
        // This function will filter the payroll table based on selected month
        // Implementation depends on how payroll data is structured
        console.log('Filtering payroll by month:', month);
        
        const table = document.getElementById('payrollRunsTable');
        if (!table) return;
        
        const year = document.getElementById('adminPayrollYearFilter')?.value;
        
        // For now, just log - actual filtering would be done when loading data
        console.log('Filter by year:', year, 'month:', month);
    }
    
    function setupLogout() {
        document.getElementById('logoutBtn').addEventListener('click', function() {
            // Clear session storage
            sessionStorage.clear();
            
            // Redirect to login
            window.location.href = '/';
        });
    }
    
    function setupOpenCalendar() {
        const calendarBtn = document.getElementById('openCalendarBtn');
        if (calendarBtn) {
            calendarBtn.addEventListener('click', function() {
                // Switch to Leave tab and then to Calendar subtab
                const leaveTabButton = document.querySelector('[data-tab="leave"]');
                if (leaveTabButton) {
                    leaveTabButton.click();
                    
                    // Wait a bit for tab to switch, then click calendar subtab
                    setTimeout(() => {
                        const calendarSubtab = document.querySelector('[data-subtab="leaveCalendar"]');
                        if (calendarSubtab) {
                            calendarSubtab.click();
                        }
                    }, 100);
                }
            });
        }
    }
    
    function setupEmployeeManagement() {
        const addBtn = document.getElementById('addEmployeeBtn');
        const cancelBtn = document.getElementById('cancelAddEmployeeBtn');
        const addForm = document.getElementById('addEmployeeForm');
        const newEmployeeForm = document.getElementById('newEmployeeForm');
        const messageDiv = document.getElementById('addEmployeeMessage');
        
        addBtn.addEventListener('click', function() {
            addForm.style.display = 'block';
            addBtn.style.display = 'none';
        });
        
        cancelBtn.addEventListener('click', function() {
            addForm.style.display = 'none';
            addBtn.style.display = 'inline-block';
            newEmployeeForm.reset();
            messageDiv.style.display = 'none';
        });
        
        newEmployeeForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = {
                full_name: document.getElementById('newEmpName').value,
                email: document.getElementById('newEmpEmail').value,
                department: document.getElementById('newEmpDepartment').value,
                position: document.getElementById('newEmpPosition').value,
                password: document.getElementById('newEmpPassword').value,
                role: document.getElementById('newEmpRole').value,
                employment_status: 'active'
            };
            
            try {
                const response = await fetch('/api/admin/employees', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });
                
                const data = await response.json();
                
                messageDiv.style.display = 'block';
                if (data.success) {
                    messageDiv.className = 'success-message';
                    messageDiv.textContent = data.message;
                    newEmployeeForm.reset();
                    
                    // Reload employee list
                    loadEmployeeList();
                    
                    // Hide form after a delay
                    setTimeout(() => {
                        addForm.style.display = 'none';
                        addBtn.style.display = 'inline-block';
                        messageDiv.style.display = 'none';
                    }, 2000);
                } else {
                    messageDiv.className = 'error-message';
                    messageDiv.textContent = data.message;
                }
            } catch (error) {
                messageDiv.style.display = 'block';
                messageDiv.className = 'error-message';
                messageDiv.textContent = 'Error creating employee';
                console.error('Error:', error);
            }
        });
    }
    
    function setupPayrollProcessing() {
        const payrollForm = document.getElementById('runPayrollForm');
        const messageDiv = document.getElementById('payrollMessage');
        
        payrollForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const payrollDate = document.getElementById('payrollMonth').value;
            
            if (!payrollDate) {
                messageDiv.style.display = 'block';
                messageDiv.className = 'error-message';
                messageDiv.textContent = 'Please select a month';
                return;
            }
            
            // Show loading message
            messageDiv.style.display = 'block';
            messageDiv.className = 'success-message';
            messageDiv.textContent = 'Processing payroll... This may take a few minutes.';
            
            try {
                const response = await fetch('/api/admin/payroll/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ payroll_date: payrollDate })
                });
                
                const data = await response.json();
                
                messageDiv.style.display = 'block';
                if (data.success) {
                    messageDiv.className = 'success-message';
                    messageDiv.textContent = data.message;
                    
                    // Reload payroll runs
                    loadPayrollRuns();
                } else {
                    messageDiv.className = 'error-message';
                    messageDiv.textContent = data.message;
                }
            } catch (error) {
                messageDiv.style.display = 'block';
                messageDiv.className = 'error-message';
                messageDiv.textContent = 'Error processing payroll';
                console.error('Error:', error);
            }
        });
    }
    
    async function loadBonuses() {
        try {
            const response = await fetch('/api/admin/bonuses');
            const data = await response.json();
            
            if (data.success && data.data && data.data.length > 0) {
                const tableHtml = buildBonusesTable(data.data);
                document.getElementById('bonusTable').innerHTML = tableHtml;
            } else {
                document.getElementById('bonusTable').innerHTML = '<p>No bonus records found.</p>';
            }
        } catch (error) {
            console.error('Error loading bonuses:', error);
            document.getElementById('bonusTable').innerHTML = '<p>Error loading bonus data.</p>';
        }
    }
    
    function buildBonusesTable(bonuses) {
        let html = '<table><thead><tr>';
        html += '<th>Employee</th><th>Type</th><th>Amount</th><th>Effective Date</th><th>Expiry Date</th><th>Status</th><th>Actions</th>';
        html += '</tr></thead><tbody>';
        
        bonuses.forEach(bonus => {
            html += '<tr>';
            html += `<td>${bonus.employees?.full_name || bonus.employee_id}</td>`;
            html += `<td>${bonus.bonus_type || '-'}</td>`;
            html += `<td>RM ${parseFloat(bonus.amount || 0).toFixed(2)}</td>`;
            html += `<td>${bonus.effective_date || '-'}</td>`;
            html += `<td>${bonus.expiry_date || '-'}</td>`;
            html += `<td>${bonus.status || '-'}</td>`;
            html += '<td>';
            html += `<button class="btn-approve" onclick="editBonus('${bonus.id}')">Edit</button> `;
            html += `<button class="btn-reject" onclick="deleteBonus('${bonus.id}')">Delete</button>`;
            html += '</td>';
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        return html;
    }
    
    function setupBonusManagement() {
        const addBtn = document.getElementById('addBonusBtn');
        const cancelBtn = document.getElementById('cancelAddBonusBtn');
        const addForm = document.getElementById('addBonusForm');
        const newBonusForm = document.getElementById('newBonusForm');
        const messageDiv = document.getElementById('addBonusMessage');
        
        addBtn.addEventListener('click', function() {
            addForm.style.display = 'block';
            addBtn.style.display = 'none';
        });
        
        cancelBtn.addEventListener('click', function() {
            addForm.style.display = 'none';
            addBtn.style.display = 'inline-block';
            newBonusForm.reset();
            messageDiv.style.display = 'none';
        });
        
        newBonusForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = {
                employee_id: document.getElementById('bonusEmployeeId').value,
                bonus_type: document.getElementById('bonusType').value,
                amount: parseFloat(document.getElementById('bonusAmount').value),
                status: document.getElementById('bonusStatus').value,
                effective_date: document.getElementById('bonusEffectiveDate').value,
                expiry_date: document.getElementById('bonusExpiryDate').value,
                remarks: document.getElementById('bonusRemarks').value
            };
            
            try {
                const response = await fetch('/api/admin/bonuses', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });
                
                const data = await response.json();
                
                messageDiv.style.display = 'block';
                if (data.success) {
                    messageDiv.className = 'success-message';
                    messageDiv.textContent = data.message;
                    newBonusForm.reset();
                    
                    // Reload bonus list
                    loadBonuses();
                    
                    // Hide form after a delay
                    setTimeout(() => {
                        addForm.style.display = 'none';
                        addBtn.style.display = 'inline-block';
                        messageDiv.style.display = 'none';
                    }, 2000);
                } else {
                    messageDiv.className = 'error-message';
                    messageDiv.textContent = data.message;
                }
            } catch (error) {
                messageDiv.style.display = 'block';
                messageDiv.className = 'error-message';
                messageDiv.textContent = 'Error creating bonus';
                console.error('Error:', error);
            }
        });
    }
    
    function setupExportHandlers() {
        // Export attendance to CSV
        const exportAttendanceBtn = document.getElementById('exportAttendanceCSVBtn');
        if (exportAttendanceBtn) {
            exportAttendanceBtn.addEventListener('click', async () => {
                try {
                    const response = await fetch('/api/admin/attendance/export/csv');
                    if (response.ok) {
                        const blob = await response.blob();
                        downloadBlob(blob, `attendance_${new Date().toISOString().split('T')[0]}.csv`);
                    } else {
                        alert('Failed to export attendance data');
                    }
                } catch (error) {
                    console.error('Error exporting attendance:', error);
                    alert('Error exporting attendance data');
                }
            });
        }
        
        // Export leave requests to CSV
        const exportLeaveRequestsBtn = document.getElementById('exportLeaveRequestsCSVBtn');
        if (exportLeaveRequestsBtn) {
            exportLeaveRequestsBtn.addEventListener('click', async () => {
                try {
                    const response = await fetch('/api/admin/leave-requests/export/csv');
                    if (response.ok) {
                        const blob = await response.blob();
                        downloadBlob(blob, `leave_requests_${new Date().toISOString().split('T')[0]}.csv`);
                    } else {
                        alert('Failed to export leave requests');
                    }
                } catch (error) {
                    console.error('Error exporting leave requests:', error);
                    alert('Error exporting leave requests');
                }
            });
        }
        
        // Export payroll runs to CSV
        const exportPayrollBtn = document.getElementById('exportPayrollCSVBtn');
        if (exportPayrollBtn) {
            exportPayrollBtn.addEventListener('click', async () => {
                try {
                    const response = await fetch('/api/admin/payroll/export/csv');
                    if (response.ok) {
                        const blob = await response.blob();
                        downloadBlob(blob, `payroll_runs_${new Date().toISOString().split('T')[0]}.csv`);
                    } else {
                        alert('Failed to export payroll data');
                    }
                } catch (error) {
                    console.error('Error exporting payroll:', error);
                    alert('Error exporting payroll data');
                }
            });
        }
    }
    
    // Helper function to download blob as file
    function downloadBlob(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }
    
    // Global functions for bonus actions
    window.editBonus = async function(bonusId) {
        alert('Edit functionality: Bonus ID ' + bonusId + '. Full edit dialog will be implemented in next iteration.');
    };
    
    window.deleteBonus = async function(bonusId) {
        if (!confirm('Are you sure you want to delete this bonus?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/admin/bonuses/${bonusId}`, {
                method: 'DELETE'
            });
            const data = await response.json();
            
            if (data.success) {
                alert('Bonus deleted successfully');
                loadBonuses(); // Reload the table
            } else {
                alert('Failed to delete bonus: ' + data.message);
            }
        } catch (error) {
            console.error('Error deleting bonus:', error);
            alert('Error deleting bonus');
        }
    };
    
    // Load leave balances
    async function loadLeaveBalances() {
        try {
            const response = await fetch('/api/admin/leave-balances');
            const data = await response.json();
            
            const tbody = document.getElementById('annualLeaveBalanceTable');
            if (!tbody) return;
            
            if (data.success && data.data && data.data.length > 0) {
                let html = '<table style="width: 100%; border-collapse: collapse;"><thead><tr style="background: #667eea; color: white;">';
                html += '<th style="padding: 10px;">Employee ID</th>';
                html += '<th style="padding: 10px;">Name</th>';
                html += '<th style="padding: 10px; text-align: center;">Total Entitled</th>';
                html += '<th style="padding: 10px; text-align: center;">Used</th>';
                html += '<th style="padding: 10px; text-align: center;">Pending</th>';
                html += '<th style="padding: 10px; text-align: center;">Remaining</th>';
                html += '</tr></thead><tbody>';
                
                data.data.forEach(balance => {
                    html += '<tr style="border-bottom: 1px solid #eee;">';
                    html += `<td style="padding: 10px;">${balance.employee_id || '-'}</td>`;
                    html += `<td style="padding: 10px;">${balance.full_name || '-'}</td>`;
                    html += `<td style="padding: 10px; text-align: center;">${balance.total_leave || 0}</td>`;
                    html += `<td style="padding: 10px; text-align: center;">${balance.used_leave || 0}</td>`;
                    html += `<td style="padding: 10px; text-align: center;">${balance.pending_leave || 0}</td>`;
                    html += `<td style="padding: 10px; text-align: center;"><strong>${balance.remaining_leave || 0}</strong></td>`;
                    html += '</tr>';
                });
                
                html += '</tbody></table>';
                tbody.innerHTML = html;
            } else {
                tbody.innerHTML = '<p>No leave balance data available.</p>';
            }
        } catch (error) {
            console.error('Error loading leave balances:', error);
            const tbody = document.getElementById('annualLeaveBalanceTable');
            if (tbody) tbody.innerHTML = '<p>Error loading leave balances.</p>';
        }
    }
    
    async function loadSickLeaveBalances() {
        try {
            const response = await fetch('/api/admin/sick-leave-balances');
            const data = await response.json();
            
            const tbody = document.getElementById('sickLeaveBalanceTable');
            if (!tbody) return;
            
            if (data.success && data.data && data.data.length > 0) {
                let html = '<table style="width: 100%; border-collapse: collapse;"><thead><tr style="background: #667eea; color: white;">';
                html += '<th style="padding: 10px;">Employee ID</th>';
                html += '<th style="padding: 10px;">Name</th>';
                html += '<th style="padding: 10px; text-align: center;">Total Sick Leave</th>';
                html += '<th style="padding: 10px; text-align: center;">Used</th>';
                html += '<th style="padding: 10px; text-align: center;">Remaining</th>';
                html += '</tr></thead><tbody>';
                
                data.data.forEach(balance => {
                    html += '<tr style="border-bottom: 1px solid #eee;">';
                    html += `<td style="padding: 10px;">${balance.employee_id || '-'}</td>`;
                    html += `<td style="padding: 10px;">${balance.full_name || '-'}</td>`;
                    html += `<td style="padding: 10px; text-align: center;">${balance.total_sick_leave || 14}</td>`;
                    html += `<td style="padding: 10px; text-align: center;">${balance.used_sick_leave || 0}</td>`;
                    html += `<td style="padding: 10px; text-align: center;"><strong>${balance.remaining_sick_leave || 14}</strong></td>`;
                    html += '</tr>';
                });
                
                html += '</tbody></table>';
                tbody.innerHTML = html;
            } else {
                tbody.innerHTML = '<p>No sick leave balance data available.</p>';
            }
        } catch (error) {
            console.error('Error loading sick leave balances:', error);
            const tbody = document.getElementById('sickLeaveBalanceTable');
            if (tbody) tbody.innerHTML = '<p>Error loading sick leave balances.</p>';
        }
    }
    
    async function loadUnpaidLeaveSummary() {
        try {
            const response = await fetch('/api/admin/unpaid-leave-summary');
            const data = await response.json();
            
            const tbody = document.getElementById('unpaidLeaveTable');
            if (!tbody) return;
            
            if (data.success && data.data && data.data.length > 0) {
                let html = '<table style="width: 100%; border-collapse: collapse;"><thead><tr style="background: #667eea; color: white;">';
                html += '<th style="padding: 10px;">Employee ID</th>';
                html += '<th style="padding: 10px;">Name</th>';
                html += '<th style="padding: 10px; text-align: center;">Total Unpaid Days (Year)</th>';
                html += '<th style="padding: 10px;">Monthly Breakdown</th>';
                html += '</tr></thead><tbody>';
                
                data.data.forEach(summary => {
                    html += '<tr style="border-bottom: 1px solid #eee;">';
                    html += `<td style="padding: 10px;">${summary.employee_id || '-'}</td>`;
                    html += `<td style="padding: 10px;">${summary.full_name || '-'}</td>`;
                    html += `<td style="padding: 10px; text-align: center;"><strong>${summary.total_unpaid_days || 0}</strong></td>`;
                    
                    // Monthly breakdown
                    let breakdown = '';
                    if (summary.monthly_breakdown && summary.monthly_breakdown.length > 0) {
                        const months = summary.monthly_breakdown.filter(m => m.unpaid_days > 0);
                        breakdown = months.map(m => `${m.month}/${m.year}: ${m.unpaid_days} days`).join(', ');
                    }
                    html += `<td style="padding: 10px;"><small>${breakdown || 'None'}</small></td>`;
                    html += '</tr>';
                });
                
                html += '</tbody></table>';
                tbody.innerHTML = html;
            } else {
                tbody.innerHTML = '<p>No unpaid leave data available.</p>';
            }
        } catch (error) {
            console.error('Error loading unpaid leave summary:', error);
            const tbody = document.getElementById('unpaidLeaveTable');
            if (tbody) tbody.innerHTML = '<p>Error loading unpaid leave data.</p>';
        }
    }
    
    async function loadPayrollContributions() {
        try {
            const response = await fetch('/api/admin/payroll-contributions');
            const data = await response.json();
            
            const container = document.getElementById('payrollContributionsSubtab');
            if (!container) return;
            
            if (data.success && data.data && data.data.length > 0) {
                let html = '<h3>View Contributions</h3>';
                html += '<p style="color: #666; margin-bottom: 15px;">EPF, SOCSO, and EIS contributions summary</p>';
                html += '<table style="width: 100%; border-collapse: collapse;"><thead><tr style="background: #667eea; color: white;">';
                html += '<th style="padding: 10px;">Employee</th>';
                html += '<th style="padding: 10px;">Period</th>';
                html += '<th style="padding: 10px; text-align: right;">EPF (Employee)</th>';
                html += '<th style="padding: 10px; text-align: right;">EPF (Employer)</th>';
                html += '<th style="padding: 10px; text-align: right;">SOCSO (Employee)</th>';
                html += '<th style="padding: 10px; text-align: right;">SOCSO (Employer)</th>';
                html += '<th style="padding: 10px; text-align: right;">EIS</th>';
                html += '<th style="padding: 10px; text-align: right;">PCB</th>';
                html += '</tr></thead><tbody>';
                
                data.data.forEach(contrib => {
                    html += '<tr style="border-bottom: 1px solid #eee;">';
                    html += `<td style="padding: 10px;">${contrib.employee_name || '-'}</td>`;
                    html += `<td style="padding: 10px;">${contrib.month_year || '-'}</td>`;
                    html += `<td style="padding: 10px; text-align: right;">RM ${contrib.epf_employee.toFixed(2)}</td>`;
                    html += `<td style="padding: 10px; text-align: right;">RM ${contrib.epf_employer.toFixed(2)}</td>`;
                    html += `<td style="padding: 10px; text-align: right;">RM ${contrib.socso_employee.toFixed(2)}</td>`;
                    html += `<td style="padding: 10px; text-align: right;">RM ${contrib.socso_employer.toFixed(2)}</td>`;
                    html += `<td style="padding: 10px; text-align: right;">RM ${contrib.eis.toFixed(2)}</td>`;
                    html += `<td style="padding: 10px; text-align: right;">RM ${contrib.pcb.toFixed(2)}</td>`;
                    html += '</tr>';
                });
                
                html += '</tbody></table>';
                container.innerHTML = html;
            } else {
                container.innerHTML = '<h3>View Contributions</h3><p>No contribution data available.</p>';
            }
        } catch (error) {
            console.error('Error loading contributions:', error);
            const container = document.getElementById('payrollContributionsSubtab');
            if (container) container.innerHTML = '<h3>View Contributions</h3><p>Error loading contributions.</p>';
        }
    }
    
    async function loadSalaryHistory() {
        try {
            const response = await fetch('/api/admin/salary-history');
            const data = await response.json();
            
            const container = document.getElementById('salaryHistoryTab');
            if (!container) return;
            
            if (data.success && data.data && data.data.length > 0) {
                let html = '<h2>📈 Salary History</h2>';
                html += '<p style="color: #666; margin-bottom: 15px;">Track salary changes, promotions, and increments</p>';
                html += '<table style="width: 100%; border-collapse: collapse;"><thead><tr style="background: #667eea; color: white;">';
                html += '<th style="padding: 10px;">Date</th>';
                html += '<th style="padding: 10px;">Employee</th>';
                html += '<th style="padding: 10px;">Change Type</th>';
                html += '<th style="padding: 10px;">Previous</th>';
                html += '<th style="padding: 10px;">New</th>';
                html += '<th style="padding: 10px;">Reason</th>';
                html += '</tr></thead><tbody>';
                
                data.data.forEach(record => {
                    html += '<tr style="border-bottom: 1px solid #eee;">';
                    html += `<td style="padding: 10px;">${record.effective_date || '-'}</td>`;
                    html += `<td style="padding: 10px;">${record.employee_name || '-'}</td>`;
                    html += `<td style="padding: 10px;">${record.change_type || '-'}</td>`;
                    html += `<td style="padding: 10px;">${record.previous_value || '-'}</td>`;
                    html += `<td style="padding: 10px;"><strong>${record.new_value || '-'}</strong></td>`;
                    html += `<td style="padding: 10px;">${record.reason || '-'}</td>`;
                    html += '</tr>';
                });
                
                html += '</tbody></table>';
                container.innerHTML = html;
            } else {
                container.innerHTML = '<h2>📈 Salary History</h2><p>No salary history records found.</p>';
            }
        } catch (error) {
            console.error('Error loading salary history:', error);
            const container = document.getElementById('salaryHistoryTab');
            if (container) container.innerHTML = '<h2>📈 Salary History</h2><p>Error loading salary history.</p>';
        }
    }
    
    async function loadEmployeeHistory() {
        try {
            const response = await fetch('/api/admin/employee-history');
            const data = await response.json();
            
            const container = document.getElementById('employeeHistoryTab');
            if (!container) return;
            
            if (data.success && data.data && data.data.length > 0) {
                let html = '<h2>🧾 Employment History</h2>';
                html += '<p style="color: #666; margin-bottom: 15px;">Complete history of employee changes</p>';
                html += '<table style="width: 100%; border-collapse: collapse;"><thead><tr style="background: #667eea; color: white;">';
                html += '<th style="padding: 10px;">Date</th>';
                html += '<th style="padding: 10px;">Employee</th>';
                html += '<th style="padding: 10px;">Change Type</th>';
                html += '<th style="padding: 10px;">Field</th>';
                html += '<th style="padding: 10px;">Previous</th>';
                html += '<th style="padding: 10px;">New</th>';
                html += '<th style="padding: 10px;">Reason</th>';
                html += '</tr></thead><tbody>';
                
                data.data.forEach(record => {
                    html += '<tr style="border-bottom: 1px solid #eee;">';
                    html += `<td style="padding: 10px;">${record.effective_date || '-'}</td>`;
                    html += `<td style="padding: 10px;">${record.employee_name || '-'}</td>`;
                    html += `<td style="padding: 10px;">${record.change_type || '-'}</td>`;
                    html += `<td style="padding: 10px;">${record.field_changed || '-'}</td>`;
                    html += `<td style="padding: 10px;">${record.previous_value || '-'}</td>`;
                    html += `<td style="padding: 10px;"><strong>${record.new_value || '-'}</strong></td>`;
                    html += `<td style="padding: 10px;"><small>${record.reason || '-'}</small></td>`;
                    html += '</tr>';
                });
                
                html += '</tbody></table>';
                container.innerHTML = html;
            } else {
                container.innerHTML = '<h2>🧾 Employment History</h2><p>No employment history records found.</p>';
            }
        } catch (error) {
            console.error('Error loading employee history:', error);
            const container = document.getElementById('employeeHistoryTab');
            if (container) container.innerHTML = '<h2>🧾 Employment History</h2><p>Error loading employment history.</p>';
        }
    }
    
    // Load all new data on init
    loadLeaveBalances();
    loadSickLeaveBalances();
    loadUnpaidLeaveSummary();
    loadPayrollContributions();
    loadSalaryHistory();
    loadEmployeeHistory();
});
