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
        
        tabButtons.forEach(button => {
            button.addEventListener('click', function() {
                const tabName = this.getAttribute('data-tab');
                
                // Remove active class from all buttons and panes
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabPanes.forEach(pane => pane.classList.remove('active'));
                
                // Add active class to clicked button and corresponding pane
                this.classList.add('active');
                document.getElementById(tabName + 'Tab').classList.add('active');
            });
        });
    }
    
    function setupLogout() {
        document.getElementById('logoutBtn').addEventListener('click', function() {
            // Clear session storage
            sessionStorage.clear();
            
            // Redirect to login
            window.location.href = '/';
        });
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
});
