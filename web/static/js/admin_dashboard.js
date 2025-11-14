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
});
