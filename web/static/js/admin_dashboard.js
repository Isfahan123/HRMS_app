// Admin Dashboard JavaScript logic
// Handles admin dashboard functionality and API calls

// Helper function to format currency values safely
function formatCurrency(value) {
    if (value === null || value === undefined || value === '') {
        return '-';
    }
    const numValue = parseFloat(value);
    if (isNaN(numValue)) {
        return '-';
    }
    return `RM ${numValue.toFixed(2)}`;
}

// Helper function to format numeric values safely
function formatNumber(value, decimals = 2) {
    if (value === null || value === undefined || value === '') {
        return '-';
    }
    const numValue = parseFloat(value);
    if (isNaN(numValue)) {
        return '-';
    }
    return numValue.toFixed(decimals);
}

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
    setupTableSorting();
    setupAttendanceSettings();
    
    async function initializeAdminDashboard() {
        try {
            // Load employee list
            loadEmployeeList();
            
            // Load attendance records
            loadAllAttendance();
            
            // Load leave requests for approval
            loadLeaveRequests();
            
            // Load approved/rejected leave requests
            loadApprovedRejectedLeaveRequests();
            
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
                cachedEmployees = data.data; // Cache for sorting
                const tableHtml = buildEmployeeTable(data.data);
                document.getElementById('employeeTable').innerHTML = tableHtml;
            } else {
                cachedEmployees = [];
                document.getElementById('employeeTable').innerHTML = '<p>No employees found.</p>';
            }
        } catch (error) {
            console.error('Error loading employees:', error);
            cachedEmployees = [];
            document.getElementById('employeeTable').innerHTML = '<p>Error loading employee data.</p>';
        }
    }
    
    function buildEmployeeTable(employees) {
        let html = '<table class="employee-table"><thead><tr>';
        html += '<th style="width: 80px;">👤 Profile</th>';
        html += '<th class="sortable" data-sort="name">📝 Name <span class="sort-indicator">↕</span></th>';
        html += '<th style="width: 120px;">🆔 Employee ID</th>';
        html += '<th class="sortable" data-sort="email">📧 Email <span class="sort-indicator">↕</span></th>';
        html += '<th>🏢 Department</th>';
        html += '<th>💼 Job Title</th>';
        html += '<th style="width: 100px;">📊 Status</th>';
        html += '<th style="width: 120px;">🏷️ Work Status</th>';
        html += '<th style="width: 100px;">🕌 Religion</th>';
        html += '<th style="width: 100px;">📄 Resume</th>';
        html += '<th style="width: 150px;">⚙️ Actions</th>';
        html += '</tr></thead><tbody>';
        
        employees.forEach(employee => {
            html += '<tr>';
            
            // Profile Picture - use photo_url (actual DB column name)
            const profilePicUrl = employee.photo_url || '/static/images/default_avatar.svg';
            html += `<td><img src="${profilePicUrl}" alt="Profile" class="profile-pic-small" onerror="this.src='/static/images/default_avatar.svg'" /></td>`;
            
            // Name
            html += `<td><strong>${employee.full_name || '-'}</strong></td>`;
            
            // Employee ID
            html += `<td>${employee.employee_id || '-'}</td>`;
            
            // Email
            html += `<td>${employee.email || '-'}</td>`;
            
            // Department
            html += `<td>${employee.department || '-'}</td>`;
            
            // Job Title
            html += `<td>${employee.job_title || '-'}</td>`;
            
            // Status - use status (actual DB column name)
            html += `<td>${employee.status || '-'}</td>`;
            
            // Work Status - Note: This column doesn't exist in DB, will show '-'
            html += `<td>${employee.work_status || '-'}</td>`;
            
            // Religion
            html += `<td>${employee.religion || '-'}</td>`;
            
            // Resume
            if (employee.resume_url) {
                html += `<td>
                    <button class="btn-secondary btn-xs" onclick="window.open('${employee.resume_url}', '_blank')" title="View Resume">👁️</button>
                    <button class="btn-secondary btn-xs" onclick="downloadResume('${employee.resume_url}', '${employee.full_name}')" title="Download Resume">⬇️</button>
                </td>`;
            } else {
                html += `<td>-</td>`;
            }
            
            // Actions
            html += `<td>
                <button class="btn-secondary btn-sm" onclick="openEditEmployeeModal('${employee.id || employee.email}')" title="Edit Employee">✏️ Edit</button>
                <button class="btn-secondary btn-sm" onclick="openPayrollInfoModal('${employee.id || employee.email}')" title="Payroll Info">📋</button>
                <button class="btn-danger btn-sm" onclick="deleteEmployee('${employee.id || employee.email}', '${employee.full_name}')" title="Delete Employee">🗑️ Delete</button>
            </td>`;
            
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        return html;
    }
    
    // Helper function to download resume
    function downloadResume(url, employeeName) {
        if (!url) return;
        
        // Get file extension from URL
        const urlParts = url.split('.');
        const extension = urlParts.length > 1 ? urlParts[urlParts.length - 1].split('?')[0] : 'pdf';
        
        // Create a temporary link element
        const link = document.createElement('a');
        link.href = url;
        link.download = `${employeeName}_resume.${extension}`;
        link.target = '_blank';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    // Helper function to delete employee
    async function deleteEmployee(employeeId, employeeName) {
        if (!confirm(`Are you sure you want to delete employee "${employeeName}"? This action cannot be undone.`)) {
            return;
        }
        
        try {
            const response = await fetch(`/api/employees/${employeeId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert(`Employee "${employeeName}" has been deleted successfully.`);
                loadEmployeeList(); // Reload the employee list
            } else {
                alert(`Failed to delete employee: ${data.message || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error deleting employee:', error);
            alert('Error deleting employee. Please try again.');
        }
    }
    
    // Table sorting functionality
    let currentSort = { column: null, direction: 'asc' };
    let cachedEmployees = [];
    
    function setupTableSorting() {
        // Add click handlers to sortable headers
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('sortable') || e.target.closest('.sortable')) {
                const header = e.target.classList.contains('sortable') ? e.target : e.target.closest('.sortable');
                const sortColumn = header.getAttribute('data-sort');
                sortEmployeeTable(sortColumn);
            }
        });
    }
    
    function sortEmployeeTable(column) {
        // Toggle direction if same column, else default to ascending
        if (currentSort.column === column) {
            currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            currentSort.column = column;
            currentSort.direction = 'asc';
        }
        
        // Sort the cached employees array
        const sortedEmployees = [...cachedEmployees].sort((a, b) => {
            let aVal = '';
            let bVal = '';
            
            if (column === 'name') {
                aVal = (a.full_name || '').toLowerCase();
                bVal = (b.full_name || '').toLowerCase();
            } else if (column === 'email') {
                aVal = (a.email || '').toLowerCase();
                bVal = (b.email || '').toLowerCase();
            }
            
            if (currentSort.direction === 'asc') {
                return aVal.localeCompare(bVal);
            } else {
                return bVal.localeCompare(aVal);
            }
        });
        
        // Rebuild and display the sorted table
        const tableHtml = buildEmployeeTable(sortedEmployees);
        document.getElementById('employeeTable').innerHTML = tableHtml;
        
        // Update sort indicators
        updateSortIndicators();
    }
    
    function updateSortIndicators() {
        // Reset all indicators
        document.querySelectorAll('.sort-indicator').forEach(indicator => {
            indicator.textContent = '↕';
        });
        
        // Update current sorted column indicator
        if (currentSort.column) {
            const header = document.querySelector(`[data-sort="${currentSort.column}"]`);
            if (header) {
                const indicator = header.querySelector('.sort-indicator');
                if (indicator) {
                    indicator.textContent = currentSort.direction === 'asc' ? '↑' : '↓';
                }
            }
        }
    }
    
    // Setup attendance settings save/load
    function setupAttendanceSettings() {
        // Load current settings when page loads
        loadAttendanceSettings();
        
        // Handle save button click
        const saveBtn = document.getElementById('saveWorkingHoursBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', saveAttendanceSettings);
        }
    }
    
    async function loadAttendanceSettings() {
        try {
            const response = await fetch('/api/admin/attendance-settings');
            const data = await response.json();
            
            if (data.success && data.data) {
                const settings = data.data;
                
                // Populate form fields
                const clockIn = document.getElementById('clockInTime');
                const clockOut = document.getElementById('clockOutTime');
                const clockInLimit = document.getElementById('clockInLimit');
                
                if (clockIn && settings.work_start) clockIn.value = settings.work_start;
                if (clockOut && settings.work_end) clockOut.value = settings.work_end;
                if (clockInLimit && settings.clock_in_limit) clockInLimit.value = settings.clock_in_limit;
            }
        } catch (error) {
            console.error('Error loading attendance settings:', error);
        }
    }
    
    async function saveAttendanceSettings() {
        const clockIn = document.getElementById('clockInTime');
        const clockOut = document.getElementById('clockOutTime');
        const clockInLimit = document.getElementById('clockInLimit');
        const messageDiv = document.getElementById('workingHoursMessage');
        
        if (!clockIn || !clockOut || !clockInLimit) {
            console.error('Attendance settings form elements not found');
            return;
        }
        
        try {
            const response = await fetch('/api/admin/attendance-settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    work_start: clockIn.value,
                    work_end: clockOut.value,
                    clock_in_limit: clockInLimit.value
                })
            });
            
            const data = await response.json();
            
            if (messageDiv) {
                if (data.success) {
                    messageDiv.style.display = 'block';
                    messageDiv.className = 'success-message';
                    messageDiv.textContent = '✅ Working hours saved successfully!';
                } else {
                    messageDiv.style.display = 'block';
                    messageDiv.className = 'error-message';
                    messageDiv.textContent = '❌ ' + (data.message || 'Failed to save working hours');
                }
                
                // Hide message after 3 seconds
                setTimeout(() => {
                    messageDiv.style.display = 'none';
                }, 3000);
            }
        } catch (error) {
            console.error('Error saving attendance settings:', error);
            if (messageDiv) {
                messageDiv.style.display = 'block';
                messageDiv.className = 'error-message';
                messageDiv.textContent = '❌ Error saving working hours';
                setTimeout(() => {
                    messageDiv.style.display = 'none';
                }, 3000);
            }
        }
    }
    
    async function loadAllAttendance() {
        try {
            const response = await fetch('/api/admin/attendance');
            const data = await response.json();
            
            const container = document.getElementById('allAttendanceTable');
            if (!container) return;
            
            if (data.success && data.data && data.data.length > 0) {
                const tableHtml = buildAttendanceTable(data.data);
                container.innerHTML = tableHtml;
            } else {
                container.innerHTML = '<p>No attendance records found.</p>';
            }
        } catch (error) {
            console.error('Error loading attendance:', error);
            const container = document.getElementById('allAttendanceTable');
            if (container) container.innerHTML = '<p>Error loading attendance data.</p>';
        }
    }
    
    function buildAttendanceTable(records) {
        let html = '<table><thead><tr>';
        html += '<th>Employee</th><th>Date</th><th>Check In</th><th>Check Out</th><th>Status</th>';
        html += '</tr></thead><tbody>';
        
        records.forEach(record => {
            html += '<tr>';
            // Use consistent fallback logic for employee display
            const employeeName = record.full_name || record.employee_name || record.email || '-';
            html += `<td>${employeeName}</td>`;
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
            
            const container = document.getElementById('pendingLeaveRequestsTable');
            if (!container) return;
            
            if (data.success && data.data && data.data.length > 0) {
                // Filter to show ONLY pending requests
                const pendingRequests = data.data.filter(r => r.status === 'pending');
                
                if (pendingRequests.length > 0) {
                    const tableHtml = buildLeaveRequestsTable(pendingRequests);
                    container.innerHTML = tableHtml;
                } else {
                    container.innerHTML = '<p>No pending leave requests found.</p>';
                }
            } else {
                container.innerHTML = '<p>No leave requests found.</p>';
            }
        } catch (error) {
            console.error('Error loading leave requests:', error);
            const container = document.getElementById('pendingLeaveRequestsTable');
            if (container) container.innerHTML = '<p>Error loading leave requests.</p>';
        }
    }
    
    function buildLeaveRequestsTable(requests) {
        let html = '<table><thead><tr>';
        html += '<th>Employee</th><th>Type</th><th>Start Date</th><th>End Date</th><th>Status</th><th>Actions</th>';
        html += '</tr></thead><tbody>';
        
        requests.forEach(request => {
            html += '<tr>';
            // Use consistent fallback logic: nested object, then employee_email, then email, then dash
            const employeeName = request.employees?.full_name || request.employee_email || request.email || '-';
            html += `<td>${employeeName}</td>`;
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
    
    // Load approved/rejected leave requests
    async function loadApprovedRejectedLeaveRequests(statusFilter = '', typeFilter = '', employeeFilter = '', startDateFilter = '', endDateFilter = '') {
        try {
            const response = await fetch('/api/admin/leave-requests');
            const data = await response.json();
            
            const container = document.getElementById('approvedRejectedLeaveRequestsTable');
            if (!container) return;
            
            if (data.success && data.data && data.data.length > 0) {
                // Filter for non-pending requests
                let filteredRequests = data.data.filter(r => r.status !== 'pending');
                
                // Apply status filter if specified
                if (statusFilter) {
                    filteredRequests = filteredRequests.filter(r => r.status === statusFilter);
                }
                
                // Apply leave type filter if specified
                if (typeFilter) {
                    filteredRequests = filteredRequests.filter(r => 
                        (r.leave_type || '').toLowerCase() === typeFilter.toLowerCase()
                    );
                }
                
                // Apply employee filter if specified
                if (employeeFilter) {
                    const searchTerm = employeeFilter.toLowerCase();
                    filteredRequests = filteredRequests.filter(r => {
                        const employeeName = (r.employees?.full_name || r.employee_email || r.email || '').toLowerCase();
                        return employeeName.includes(searchTerm);
                    });
                }
                
                // Apply date range filter if specified
                if (startDateFilter) {
                    filteredRequests = filteredRequests.filter(r => 
                        r.start_date && r.start_date >= startDateFilter
                    );
                }
                if (endDateFilter) {
                    filteredRequests = filteredRequests.filter(r => 
                        r.end_date && r.end_date <= endDateFilter
                    );
                }
                
                if (filteredRequests.length === 0) {
                    container.innerHTML = '<p>No approved/rejected leave requests found matching the filters.</p>';
                    return;
                }
                
                let html = '<table><thead><tr>';
                html += '<th>Employee</th><th>Type</th><th>Start Date</th><th>End Date</th><th>Days</th><th>Status</th><th>Reviewed By</th><th>Reviewed At</th>';
                html += '</tr></thead><tbody>';
                
                filteredRequests.forEach(request => {
                    const statusColor = request.status === 'approved' ? 'green' : 
                                       request.status === 'rejected' ? 'red' : '#666';
                    html += '<tr>';
                    // Use consistent fallback logic: nested object, then employee_email, then email, then dash
                    const employeeName = request.employees?.full_name || request.employee_email || request.email || '-';
                    html += `<td>${employeeName}</td>`;
                    html += `<td>${request.leave_type || '-'}</td>`;
                    html += `<td>${request.start_date || '-'}</td>`;
                    html += `<td>${request.end_date || '-'}</td>`;
                    html += `<td>${request.total_days || '-'}</td>`;
                    html += `<td style="color: ${statusColor}; font-weight: bold;">${(request.status || '').toUpperCase()}</td>`;
                    html += `<td>${request.reviewed_by || '-'}</td>`;
                    html += `<td>${request.reviewed_at ? new Date(request.reviewed_at).toLocaleDateString() : '-'}</td>`;
                    html += '</tr>';
                });
                
                html += '</tbody></table>';
                html += `<p style="margin-top: 10px; color: #666;">Showing ${filteredRequests.length} leave request(s)</p>`;
                container.innerHTML = html;
            } else {
                container.innerHTML = '<p>No leave requests found.</p>';
            }
        } catch (error) {
            console.error('Error loading approved/rejected leave requests:', error);
            const container = document.getElementById('approvedRejectedLeaveRequestsTable');
            if (container) container.innerHTML = '<p>Error loading leave requests.</p>';
        }
    }
    
    // Wire up filter buttons for approved/rejected leave requests
    const filterLeaveBtn = document.getElementById('filterLeaveBtn');
    if (filterLeaveBtn) {
        filterLeaveBtn.addEventListener('click', () => {
            const statusFilter = document.getElementById('leaveStatusFilter')?.value || '';
            const typeFilter = document.getElementById('leaveTypeFilter')?.value || '';
            const employeeFilter = document.getElementById('leaveEmployeeFilter')?.value || '';
            const startDateFilter = document.getElementById('leaveStartDateFilter')?.value || '';
            const endDateFilter = document.getElementById('leaveEndDateFilter')?.value || '';
            loadApprovedRejectedLeaveRequests(statusFilter, typeFilter, employeeFilter, startDateFilter, endDateFilter);
        });
    }
    
    const clearLeaveFilterBtn = document.getElementById('clearLeaveFilterBtn');
    if (clearLeaveFilterBtn) {
        clearLeaveFilterBtn.addEventListener('click', () => {
            document.getElementById('leaveStatusFilter').value = '';
            if (document.getElementById('leaveTypeFilter')) document.getElementById('leaveTypeFilter').value = '';
            if (document.getElementById('leaveEmployeeFilter')) document.getElementById('leaveEmployeeFilter').value = '';
            if (document.getElementById('leaveStartDateFilter')) document.getElementById('leaveStartDateFilter').value = '';
            if (document.getElementById('leaveEndDateFilter')) document.getElementById('leaveEndDateFilter').value = '';
            loadApprovedRejectedLeaveRequests();
        });
    }
    
    // Store payroll runs globally for filtering
    let allPayrollRuns = [];
    
    async function loadPayrollRuns() {
        try {
            const response = await fetch('/api/admin/payroll-runs');
            const data = await response.json();
            
            const container = document.getElementById('payrollRunsTable');
            if (!container) return;
            
            if (data.success && data.data && data.data.length > 0) {
                allPayrollRuns = data.data; // Store for filtering
                const tableHtml = buildPayrollRunsTable(data.data);
                container.innerHTML = tableHtml;
            } else {
                allPayrollRuns = [];
                container.innerHTML = '<p>No payroll runs found.</p>';
            }
        } catch (error) {
            console.error('Error loading payroll runs:', error);
            allPayrollRuns = [];
            const container = document.getElementById('payrollRunsTable');
            if (container) container.innerHTML = '<p>Error loading payroll data.</p>';
        }
    }
    
    function buildPayrollRunsTable(runs) {
        // Helper function to format allowances with breakdown
        const formatAllowances = (allowances) => {
            if (!allowances || typeof allowances !== 'object') return 'None';
            
            const allowancesList = [];
            let total = 0;
            
            for (const [key, value] of Object.entries(allowances)) {
                if (value && value !== 0) {
                    try {
                        const amount = parseFloat(value);
                        const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                        allowancesList.push(`${label}: RM ${amount.toFixed(2)}`);
                        total += amount;
                    } catch (e) {
                        // Skip invalid values
                    }
                }
            }
            
            if (allowancesList.length > 0) {
                return allowancesList.join(', ') + ` | Total: RM ${total.toFixed(2)}`;
            }
            return 'None';
        };
        
        // Helper function to format days (handle half-days)
        const formatDays = (value) => {
            if (!value || value === 0) return '0';
            const days = parseFloat(value);
            return days === Math.floor(days) ? Math.floor(days).toString() : days.toFixed(1);
        };
        
        let html = '<div style="overflow-x: auto;"><table style="width: 100%; border-collapse: collapse; font-size: 13px;"><thead><tr style="background: #667eea; color: white;">';
        // 20 columns matching Python GUI
        html += '<th style="padding: 8px; text-align: left; min-width: 120px;">Employee Name</th>';
        html += '<th style="padding: 8px; text-align: left; min-width: 90px;">Payroll Date</th>';
        html += '<th style="padding: 8px; text-align: right; min-width: 90px;">Gross Salary</th>';
        html += '<th style="padding: 8px; text-align: left; min-width: 150px;">Allowances</th>';
        html += '<th style="padding: 8px; text-align: right; min-width: 70px;">Unpaid Days</th>';
        html += '<th style="padding: 8px; text-align: right; min-width: 90px;">Unpaid Deduction</th>';
        html += '<th style="padding: 8px; text-align: right; min-width: 85px;">EPF Employee</th>';
        html += '<th style="padding: 8px; text-align: right; min-width: 85px;">EPF Employer</th>';
        html += '<th style="padding: 8px; text-align: right; min-width: 90px;">SOCSO Employee</th>';
        html += '<th style="padding: 8px; text-align: right; min-width: 90px;">SOCSO Employer</th>';
        html += '<th style="padding: 8px; text-align: right; min-width: 85px;">EIS Employee</th>';
        html += '<th style="padding: 8px; text-align: right; min-width: 85px;">EIS Employer</th>';
        html += '<th style="padding: 8px; text-align: right; min-width: 70px;">PCB</th>';
        html += '<th style="padding: 8px; text-align: right; min-width: 70px;">SIP</th>';
        html += '<th style="padding: 8px; text-align: right; min-width: 95px;">Additional EPF</th>';
        html += '<th style="padding: 8px; text-align: right; min-width: 70px;">PRS</th>';
        html += '<th style="padding: 8px; text-align: right; min-width: 75px;">Insurance</th>';
        html += '<th style="padding: 8px; text-align: right; min-width: 100px;">Other Deductions</th>';
        html += '<th style="padding: 8px; text-align: right; min-width: 90px;">Net Salary</th>';
        html += '<th style="padding: 8px; text-align: center; min-width: 80px;">Actions</th>';
        html += '</tr></thead><tbody>';
        
        runs.forEach(run => {
            html += '<tr style="border-bottom: 1px solid #eee;">';
            
            // Employee Name
            const employeeName = run.employee_name || run.employee?.full_name || run.employee_email || '-';
            html += `<td style="padding: 8px;">${employeeName}</td>`;
            
            // Payroll Date
            html += `<td style="padding: 8px;">${run.payroll_date || run.month_year || '-'}</td>`;
            
            // Gross Salary
            html += `<td style="padding: 8px; text-align: right;">${formatCurrency(run.gross_salary)}</td>`;
            
            // Allowances (with breakdown)
            const allowancesText = formatAllowances(run.allowances);
            html += `<td style="padding: 8px;"><small>${allowancesText}</small></td>`;
            
            // Unpaid Days
            html += `<td style="padding: 8px; text-align: right;">${formatDays(run.unpaid_leave_days)}</td>`;
            
            // Unpaid Deduction
            html += `<td style="padding: 8px; text-align: right;">${formatCurrency(run.unpaid_leave_deduction)}</td>`;
            
            // EPF Employee
            html += `<td style="padding: 8px; text-align: right;">${formatCurrency(run.epf_employee)}</td>`;
            
            // EPF Employer
            html += `<td style="padding: 8px; text-align: right;">${formatCurrency(run.epf_employer)}</td>`;
            
            // SOCSO Employee
            html += `<td style="padding: 8px; text-align: right;">${formatCurrency(run.socso_employee)}</td>`;
            
            // SOCSO Employer
            html += `<td style="padding: 8px; text-align: right;">${formatCurrency(run.socso_employer)}</td>`;
            
            // EIS Employee
            html += `<td style="padding: 8px; text-align: right;">${formatCurrency(run.eis_employee)}</td>`;
            
            // EIS Employer
            html += `<td style="padding: 8px; text-align: right;">${formatCurrency(run.eis_employer)}</td>`;
            
            // PCB (with fallback to legacy fields)
            const pcb = run.pcb || run.pcb_tax || run.pcb_amount;
            html += `<td style="padding: 8px; text-align: right;">${formatCurrency(pcb)}</td>`;
            
            // SIP
            html += `<td style="padding: 8px; text-align: right;">${formatCurrency(run.sip_deduction)}</td>`;
            
            // Additional EPF
            html += `<td style="padding: 8px; text-align: right;">${formatCurrency(run.additional_epf_deduction)}</td>`;
            
            // PRS
            html += `<td style="padding: 8px; text-align: right;">${formatCurrency(run.prs_deduction)}</td>`;
            
            // Insurance
            html += `<td style="padding: 8px; text-align: right;">${formatCurrency(run.insurance_premium)}</td>`;
            
            // Other Deductions
            html += `<td style="padding: 8px; text-align: right;">${formatCurrency(run.other_deductions)}</td>`;
            
            // Net Salary
            html += `<td style="padding: 8px; text-align: right;"><strong style="color: #059669;">${formatCurrency(run.net_salary)}</strong></td>`;
            
            // Actions column with download payslip button
            html += '<td style="padding: 8px; text-align: center;">';
            const employeeId = run.employee_id || run.employee?.id;
            const payrollRunId = run.id;
            if (employeeId && payrollRunId) {
                html += `<button onclick="downloadPayslip('${employeeId}', '${payrollRunId}')" class="btn-sm btn-secondary" title="Download Payslip PDF" style="font-size: 11px;">📄 Generate</button>`;
            } else {
                html += '<span style="color: #999;">N/A</span>';
            }
            html += '</td>';
            
            html += '</tr>';
        });
        
        html += '</tbody></table></div>';
        html += `<p style="margin-top: 15px; color: #666; font-size: 14px;">Showing ${runs.length} payroll record(s)</p>`;
        return html;
    }
    
    // Global function for downloading payslip
    window.downloadPayslip = async function(employeeId, payrollRunId) {
        try {
            // Show loading state
            console.log(`Downloading payslip for employee ${employeeId}, payroll run ${payrollRunId}`);
            
            // Fetch the payslip PDF
            const response = await fetch(`/api/payroll/payslip/${employeeId}/${payrollRunId}`);
            
            if (!response.ok) {
                // Try to parse error as JSON, fallback to text
                let errorMessage = 'Failed to generate payslip';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorMessage;
                } catch (e) {
                    // If not JSON, try to get text
                    const errorText = await response.text();
                    errorMessage = errorText || errorMessage;
                }
                throw new Error(errorMessage);
            }
            
            // Get the blob data
            const blob = await response.blob();
            
            // Create a download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `payslip_${employeeId}_${payrollRunId}.pdf`;
            document.body.appendChild(a);
            a.click();
            
            // Cleanup
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            console.log('Payslip downloaded successfully');
        } catch (error) {
            console.error('Error downloading payslip:', error);
            alert('Error downloading payslip: ' + error.message);
        }
    };
    
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
    
    // Employee History Edit/Delete Functions - defined early for onclick handlers
    window.editEmployeeHistory = async function(recordId) {
        try {
            const response = await fetch('/api/admin/employee-history');
            const data = await response.json();
            
            if (data.success && data.data) {
                const record = data.data.find(r => r.id === recordId);
                if (!record) {
                    alert('Record not found');
                    return;
                }
                
                // Load employee selector first
                await loadEmployeeHistorySelector();
                
                // Populate the edit modal with record data
                document.getElementById('editEmpHistoryRecordId').value = recordId;
                document.getElementById('editEmpHistoryEmployeeSelect').value = record.employee_email || '';
                document.getElementById('editEmpHistoryCompany').value = record.company || '';
                document.getElementById('editEmpHistoryJobTitle').value = record.job_title || '';
                document.getElementById('editEmpHistoryPosition').value = record.position || '';
                document.getElementById('editEmpHistoryDepartment').value = record.department || '';
                document.getElementById('editEmpHistoryFunctionalGroup').value = record.functional_group || '';
                document.getElementById('editEmpHistoryStatus').value = record.status || '';
                document.getElementById('editEmpHistoryEmploymentType').value = record.employment_type || '';
                document.getElementById('editEmpHistoryWorkStatus').value = record.work_status || '';
                document.getElementById('editEmpHistoryPayrollStatus').value = record.payroll_status || '';
                document.getElementById('editEmpHistoryStartDate').value = record.start_date || '';
                document.getElementById('editEmpHistoryEndDate').value = record.end_date || '';
                document.getElementById('editEmpHistoryNotes').value = record.notes || '';
                
                // Clear any previous messages
                document.getElementById('editEmploymentHistoryMessage').style.display = 'none';
                
                // Show the modal
                document.getElementById('editEmploymentHistoryModal').style.display = 'block';
            }
        } catch (error) {
            console.error('Error loading employee history for edit:', error);
            alert('Error loading employee history record');
        }
    };
    
    window.deleteEmployeeHistory = async function(recordId) {
        if (!confirm('Are you sure you want to delete this employee history record? This action cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/admin/employee-history/${recordId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            if (result.success) {
                alert('Employee history deleted successfully!');
                loadEmployeeHistory();
            } else {
                alert('Failed to delete employee history: ' + result.message);
            }
        } catch (error) {
            console.error('Error deleting employee history:', error);
            alert('Error deleting employee history');
        }
    };
    
    // Additional global functions for onclick handlers - defined early to prevent ReferenceErrors
    window.openEditEmployeeModal = async function(employeeId) {
        try {
            console.log('Opening edit modal for employee:', employeeId);
            
            // Fetch employee data
            const response = await fetch(`/api/employees`);
            const data = await response.json();
            
            if (data.success && data.data) {
                // Find the employee by ID or email
                const employee = data.data.find(emp => emp.id === employeeId || emp.email === employeeId);
                
                if (!employee) {
                    alert('Employee not found');
                    return;
                }
                
                // Populate the form
                document.getElementById('editEmpId').value = employee.id || employee.email;
                document.getElementById('editEmpName').value = employee.full_name || '';
                document.getElementById('editEmpEmail').value = employee.email || '';
                document.getElementById('editEmpEmployeeID').value = employee.employee_id || '';
                // Personal Information
                document.getElementById('editEmpGender').value = employee.gender || '';
                document.getElementById('editEmpDOB').value = employee.date_of_birth || '';
                document.getElementById('editEmpNRIC').value = employee.nric || '';
                document.getElementById('editEmpNationality').value = employee.nationality || '';
                document.getElementById('editEmpCitizenship').value = employee.citizenship || '';
                document.getElementById('editEmpRace').value = employee.race || '';
                document.getElementById('editEmpReligion').value = employee.religion || '';
                document.getElementById('editEmpMaritalStatus').value = employee.marital_status || '';
                document.getElementById('editEmpChildren').value = employee.number_of_children || '0';
                document.getElementById('editEmpSpouseWorking').value = employee.spouse_working || '';
                // Contact Information
                document.getElementById('editEmpUsername').value = employee.username || '';
                document.getElementById('editEmpPhone').value = employee.phone_number || '';
                document.getElementById('editEmpAddress').value = employee.address || '';
                document.getElementById('editEmpCity').value = employee.city || '';
                document.getElementById('editEmpState').value = employee.state || '';
                document.getElementById('editEmpZipcode').value = employee.zipcode || '';
                // Employment Information
                document.getElementById('editEmpDepartment').value = employee.department || '';
                document.getElementById('editEmpJobTitle').value = employee.job_title || '';
                document.getElementById('editEmpPosition').value = employee.position || '';
                document.getElementById('editEmpFunctionalGroup').value = employee.functional_group || '';
                document.getElementById('editEmpEmploymentType').value = employee.employment_type || 'Full-time';
                document.getElementById('editEmpRole').value = employee.role || 'employee';
                document.getElementById('editEmpStatus').value = employee.employment_status || 'Active';
                document.getElementById('editEmpWorkStatus').value = employee.work_status || 'On Duty';
                document.getElementById('editEmpPayrollStatus').value = employee.payroll_status || 'Active Payroll';
                document.getElementById('editEmpJoinDate').value = employee.join_date || '';
                // EPF/SOCSO Information
                document.getElementById('editEmpEPFNumber').value = employee.epf_number || '';
                document.getElementById('editEmpSOCSONumber').value = employee.socso_number || '';
                document.getElementById('editEmpIncomeTaxNumber').value = employee.income_tax_number || '';
                // Emergency Contact
                document.getElementById('editEmpContactName').value = employee.emergency_name || '';
                document.getElementById('editEmpRelation').value = employee.emergency_relation || '';
                document.getElementById('editEmpEmergencyPhone').value = employee.emergency_phone || '';
                // Primary Education
                document.getElementById('editEmpPrimarySchool').value = employee.primary_school_name || '';
                document.getElementById('editEmpPrimaryLocation').value = employee.primary_location || '';
                document.getElementById('editEmpPrimaryType').value = employee.primary_type || '';
                document.getElementById('editEmpPrimaryYearStarted').value = employee.primary_year_started || '';
                document.getElementById('editEmpPrimaryYearCompleted').value = employee.primary_year_completed || '';
                // Secondary Education
                document.getElementById('editEmpSecondarySchool').value = employee.secondary_school_name || '';
                document.getElementById('editEmpSecondaryLocation').value = employee.secondary_location || '';
                document.getElementById('editEmpSecondaryType').value = employee.secondary_type || '';
                document.getElementById('editEmpSecondaryYearStarted').value = employee.secondary_year_started || '';
                document.getElementById('editEmpSecondaryYearCompleted').value = employee.secondary_year_completed || '';
                document.getElementById('editEmpSecondaryQualification').value = employee.secondary_qualification || '';
                document.getElementById('editEmpSecondaryStream').value = employee.secondary_stream || '';
                document.getElementById('editEmpSecondaryGrades').value = employee.secondary_grades || '';
                // Tertiary Education
                document.getElementById('editEmpTertiaryInstitution').value = employee.tertiary_institution || '';
                document.getElementById('editEmpTertiaryLocation').value = employee.tertiary_location || '';
                document.getElementById('editEmpTertiaryLevel').value = employee.tertiary_level || '';
                document.getElementById('editEmpTertiaryType').value = employee.tertiary_institution_type || '';
                document.getElementById('editEmpTertiaryField').value = employee.tertiary_field || '';
                document.getElementById('editEmpTertiaryMajor').value = employee.tertiary_major || '';
                document.getElementById('editEmpTertiaryYearStarted').value = employee.tertiary_year_started || '';
                document.getElementById('editEmpTertiaryYearCompleted').value = employee.tertiary_year_completed || '';
                document.getElementById('editEmpTertiaryStatus').value = employee.tertiary_status || '';
                document.getElementById('editEmpTertiaryCGPA').value = employee.tertiary_cgpa || '';
                
                // Show the modal
                document.getElementById('editEmployeeModal').style.display = 'block';
            }
        } catch (error) {
            console.error('Error loading employee data:', error);
            alert('Error loading employee data');
        }
    };
    
    window.editBonus = async function(bonusId) {
        // Delegate to bonusManager if available
        if (typeof bonusManager !== 'undefined' && bonusManager) {
            bonusManager.editBonus(bonusId);
        } else {
            alert('Bonus manager not loaded. Please refresh the page.');
        }
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
    
    window.editSalaryHistory = async function(recordId) {
        try {
            const response = await fetch('/api/admin/salary-history');
            const data = await response.json();
            
            if (data.success && data.data) {
                // Convert recordId to string for comparison (handles both UUID and numeric IDs)
                const recordIdStr = String(recordId);
                const record = data.data.find(r => String(r.id) === recordIdStr);
                if (!record) {
                    alert('Record not found');
                    return;
                }
                
                const newEffectiveDate = prompt('Effective Date (YYYY-MM-DD):', record.effective_date || '');
                if (newEffectiveDate === null) return; // User cancelled
                
                const newPrevSalary = prompt('Previous Salary:', parseFloat(record.previous_salary) || 0);
                if (newPrevSalary === null) return;
                
                const newNewSalary = prompt('New Salary:', parseFloat(record.new_salary) || 0);
                if (newNewSalary === null) return;
                
                const newReason = prompt('Reason:', record.reason || '');
                if (newReason === null) return;
                
                const updateData = {
                    effective_date: newEffectiveDate,
                    previous_salary: newPrevSalary,
                    new_salary: newNewSalary,
                    reason: newReason
                };
                
                const updateResponse = await fetch(`/api/admin/salary-history/${recordId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updateData)
                });
                
                const result = await updateResponse.json();
                if (result.success) {
                    alert('Salary history updated successfully!');
                    loadSalaryHistory();
                } else {
                    alert('Failed to update salary history: ' + result.message);
                }
            }
        } catch (error) {
            console.error('Error editing salary history:', error);
            alert('Error editing salary history');
        }
    };
    
    window.deleteSalaryHistory = async function(recordId) {
        if (!confirm('Are you sure you want to delete this salary history record? This action cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/admin/salary-history/${recordId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            if (result.success) {
                alert('Salary history deleted successfully!');
                loadSalaryHistory();
            } else {
                alert('Failed to delete salary history: ' + result.message);
            }
        } catch (error) {
            console.error('Error deleting salary history:', error);
            alert('Error deleting salary history');
        }
    };
    
    window.editEngagement = async function(engagementId) {
        try {
            const response = await fetch('/api/admin/engagements/all');
            const data = await response.json();
            
            if (data.success && data.data) {
                const record = data.data.find(r => r.id === engagementId);
                if (!record) {
                    alert('Engagement not found');
                    return;
                }
                
                const newTitle = prompt('Title:', record.title || '');
                if (newTitle === null) return; // User cancelled
                
                const newStartDate = prompt('Start Date (YYYY-MM-DD):', record.start_date || '');
                if (newStartDate === null) return;
                
                const newEndDate = prompt('End Date (YYYY-MM-DD):', record.end_date || '');
                if (newEndDate === null) return;
                
                const newLocation = prompt('Location:', record.location || '');
                if (newLocation === null) return;
                
                const newStatus = prompt('Status (pending/approved/completed/cancelled):', record.status || '');
                if (newStatus === null) return;
                
                const updateData = {
                    title: newTitle,
                    start_date: newStartDate,
                    end_date: newEndDate,
                    location: newLocation,
                    status: newStatus
                };
                
                const updateResponse = await fetch(`/api/admin/engagements/${engagementId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updateData)
                });
                
                const result = await updateResponse.json();
                if (result.success) {
                    alert('Engagement updated successfully!');
                    loadAllEngagements();
                } else {
                    alert('Failed to update engagement: ' + result.message);
                }
            }
        } catch (error) {
            console.error('Error editing engagement:', error);
            alert('Error editing engagement');
        }
    };
    
    window.deleteEngagement = async function(engagementId) {
        if (!confirm('Are you sure you want to delete this engagement? This action cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/admin/engagements/${engagementId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            if (result.success) {
                alert('Engagement deleted successfully!');
                loadAllEngagements();
            } else {
                alert('Failed to delete engagement: ' + result.message);
            }
        } catch (error) {
            console.error('Error deleting engagement:', error);
            alert('Error deleting engagement');
        }
    };
    
    // Old edit and delete functions removed - replaced with EPF/SOCSO/EIS configuration system
    
    window.includeInNextPayroll = async function(recordId) {
        if (!confirm('Mark this employee to be included in the next payroll run?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/admin/skipped-payroll/${recordId}/include`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert('✅ ' + result.message);
                loadSkippedPayroll();
            } else {
                alert('❌ ' + result.message);
            }
        } catch (error) {
            console.error('Error including in next payroll:', error);
            alert('❌ Error updating record');
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
                    
                    // Load data when specific tabs are activated
                    if (tabName === 'employeeHistory') {
                        console.log('🔄 Reloading employment history data...');
                        loadEmployeeHistory();
                    } else if (tabName === 'salaryHistory') {
                        console.log('🔄 Loading salary history...');
                        loadSalaryHistory();
                    } else if (tabName === 'payroll') {
                        console.log('🔄 Loading payroll runs...');
                        loadPayrollRuns();
                    }
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
                
                // If this is a month tab (for payroll history)
                if (monthValue) {
                    // Handle month tab switching
                    const parentContainer = this.closest('.tab-pane');
                    if (!parentContainer) {
                        console.error('❌ Parent container not found for subtab');
                        return;
                    }
                    const monthButtons = parentContainer.querySelectorAll('[data-month]');
                    monthButtons.forEach(btn => btn.classList.remove('active'));
                    this.classList.add('active');
                    
                    console.log('✅ Month filter activated:', monthValue);
                    
                    // Filter payroll table by month
                    filterPayrollByMonth(monthValue);
                    return;
                }
                
                // Regular subtab switching - find the immediate parent subtabs container
                const subtabsContainer = this.closest('.subtabs');
                if (!subtabsContainer) {
                    console.error('❌ Subtabs container not found for subtab button');
                    return;
                }
                
                // Find the parent that contains both the buttons and content
                // This could be either a .tab-pane or a .subtab-content (for nested subtabs)
                let contentParent = subtabsContainer.parentElement;
                
                // Remove active class from sibling buttons in the same subtabs container
                const siblingButtons = subtabsContainer.querySelectorAll('.subtab-button');
                siblingButtons.forEach(btn => btn.classList.remove('active'));
                
                // Remove active class from sibling content divs at the same level
                const siblingContents = contentParent.querySelectorAll(':scope > .subtab-content');
                siblingContents.forEach(content => content.classList.remove('active'));
                
                // Add active class to clicked button and corresponding content
                this.classList.add('active');
                const subtabContent = document.getElementById(subtabName + 'Subtab');
                if (subtabContent) {
                    subtabContent.classList.add('active');
                }
                
                // Load data when specific subtabs are activated
                if (subtabName === 'leavePending') {
                    console.log('🔄 Loading pending leave requests...');
                    loadLeaveRequests();
                } else if (subtabName === 'leaveApprovedRejected') {
                    console.log('🔄 Loading approved/rejected leave requests...');
                    loadApprovedRejectedLeaveRequests();
                } else if (subtabName === 'leaveAnnualBalance') {
                    console.log('🔄 Loading annual leave balances...');
                    loadLeaveBalances();
                } else if (subtabName === 'leaveSickBalance') {
                    console.log('🔄 Loading sick leave balances...');
                    loadSickLeaveBalances();
                } else if (subtabName === 'leaveUnpaid') {
                    console.log('🔄 Loading unpaid leave summary...');
                    loadUnpaidLeaveSummary();
                } else if (subtabName === 'payrollBonuses') {
                    console.log('🔄 Loading bonuses...');
                    loadBonuses();
                } else if (subtabName === 'payrollVariable') {
                    console.log('🔄 Loading variable percentage rules...');
                    loadVariablePercentageRules();
                } else if (subtabName === 'payrollLHDN') {
                    console.log('🔄 Loading LHDN Tax configuration...');
                    // Load tax rates by default when LHDN tab is opened
                    if (typeof loadTaxRatesFromAPI === 'function') {
                        loadTaxRatesFromAPI();
                    }
                    if (typeof loadReliefMaximumsFromAPI === 'function') {
                        loadReliefMaximumsFromAPI();
                    }
                    if (typeof loadReliefOverridesFromAPI === 'function') {
                        loadReliefOverridesFromAPI();
                    }
                } else if (subtabName === 'engagementsView') {
                    console.log('🔄 Loading engagements...');
                    // Load all engagements
                    if (typeof loadAllEngagements === 'function') {
                        loadAllEngagements();
                    }
                } else if (subtabName === 'lhdnTaxRates') {
                    console.log('🔄 Loading LHDN tax rates...');
                    if (typeof loadTaxRatesFromAPI === 'function') {
                        loadTaxRatesFromAPI();
                    }
                } else if (subtabName === 'lhdnReliefMax') {
                    console.log('🔄 Loading tax relief maximums...');
                    if (typeof loadReliefMaximumsFromAPI === 'function') {
                        loadReliefMaximumsFromAPI();
                    }
                } else if (subtabName === 'lhdnReliefOverrides') {
                    console.log('🔄 Loading relief overrides...');
                    if (typeof loadReliefOverridesFromAPI === 'function') {
                        loadReliefOverridesFromAPI();
                    }
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
        const container = document.getElementById('payrollRunsTable');
        if (!container) return;
        
        if (allPayrollRuns.length === 0) {
            container.innerHTML = '<p>No payroll runs found.</p>';
            return;
        }
        
        const year = document.getElementById('adminPayrollYearFilter')?.value;
        
        // Filter payroll runs by month and year
        let filteredRuns = allPayrollRuns;
        
        // Filter by month (if not "all")
        if (month && month !== 'all') {
            filteredRuns = filteredRuns.filter(run => {
                // Extract month from payroll_date or month_year
                const dateStr = run.month_year || run.payroll_date || '';
                if (!dateStr) return false;
                
                // Try to parse the date and extract month
                try {
                    // Handle formats like "2024-01", "2024-01-15", "January 2024", etc.
                    let runMonth;
                    
                    if (dateStr.includes('-')) {
                        // Format: "2024-01" or "2024-01-15"
                        const parts = dateStr.split('-');
                        runMonth = parseInt(parts[1], 10);
                    } else if (dateStr.match(/^\d{4}$/)) {
                        // Year only, no month
                        return false;
                    } else {
                        // Try to parse as date
                        const date = new Date(dateStr);
                        if (!isNaN(date.getTime())) {
                            runMonth = date.getMonth() + 1; // getMonth() returns 0-11
                        } else {
                            return false;
                        }
                    }
                    
                    return runMonth === parseInt(month, 10);
                } catch (e) {
                    console.warn('Unable to parse date:', dateStr);
                    return false;
                }
            });
        }
        
        // Filter by year (if selected)
        if (year) {
            filteredRuns = filteredRuns.filter(run => {
                const dateStr = run.month_year || run.payroll_date || '';
                return dateStr.includes(year);
            });
        }
        
        // Display filtered results
        if (filteredRuns.length > 0) {
            const tableHtml = buildPayrollRunsTable(filteredRuns);
            container.innerHTML = tableHtml;
        } else {
            const monthName = month === 'all' ? 'all months' : 
                             ['', 'January', 'February', 'March', 'April', 'May', 'June',
                              'July', 'August', 'September', 'October', 'November', 'December'][parseInt(month)] || `month ${month}`;
            container.innerHTML = `<p>No payroll runs found for ${monthName}${year ? ' ' + year : ''}.</p>`;
        }
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
                password: document.getElementById('newEmpPassword').value,
                // Personal Information
                gender: document.getElementById('newEmpGender').value,
                date_of_birth: document.getElementById('newEmpDOB').value,
                nric: document.getElementById('newEmpNRIC').value,
                nationality: document.getElementById('newEmpNationality').value,
                citizenship: document.getElementById('newEmpCitizenship').value,
                race: document.getElementById('newEmpRace').value,
                religion: document.getElementById('newEmpReligion').value,
                marital_status: document.getElementById('newEmpMaritalStatus').value,
                number_of_children: document.getElementById('newEmpChildren').value,
                spouse_working: document.getElementById('newEmpSpouseWorking').value,
                // Contact Information
                username: document.getElementById('newEmpUsername').value,
                phone_number: document.getElementById('newEmpPhone').value,
                address: document.getElementById('newEmpAddress').value,
                city: document.getElementById('newEmpCity').value,
                state: document.getElementById('newEmpState').value,
                zipcode: document.getElementById('newEmpZipcode').value,
                // Employment Information
                employee_id: document.getElementById('newEmpEmployeeID').value,
                department: document.getElementById('newEmpDepartment').value,
                job_title: document.getElementById('newEmpJobTitle').value,
                position: document.getElementById('newEmpPosition').value,
                functional_group: document.getElementById('newEmpFunctionalGroup').value,
                employment_type: document.getElementById('newEmpEmploymentType').value,
                role: document.getElementById('newEmpRole').value,
                employment_status: document.getElementById('newEmpStatus').value,
                work_status: document.getElementById('newEmpWorkStatus').value,
                payroll_status: document.getElementById('newEmpPayrollStatus').value,
                join_date: document.getElementById('newEmpJoinDate').value,
                // EPF/SOCSO Information
                epf_number: document.getElementById('newEmpEPFNumber').value,
                socso_number: document.getElementById('newEmpSOCSONumber').value,
                income_tax_number: document.getElementById('newEmpIncomeTaxNumber').value,
                // Emergency Contact
                emergency_name: document.getElementById('newEmpContactName').value,
                emergency_relation: document.getElementById('newEmpRelation').value,
                emergency_phone: document.getElementById('newEmpEmergencyPhone').value,
                // Primary Education
                primary_school_name: document.getElementById('newEmpPrimarySchool').value,
                primary_location: document.getElementById('newEmpPrimaryLocation').value,
                primary_type: document.getElementById('newEmpPrimaryType').value,
                primary_year_started: document.getElementById('newEmpPrimaryYearStarted').value,
                primary_year_completed: document.getElementById('newEmpPrimaryYearCompleted').value,
                // Secondary Education
                secondary_school_name: document.getElementById('newEmpSecondarySchool').value,
                secondary_location: document.getElementById('newEmpSecondaryLocation').value,
                secondary_type: document.getElementById('newEmpSecondaryType').value,
                secondary_year_started: document.getElementById('newEmpSecondaryYearStarted').value,
                secondary_year_completed: document.getElementById('newEmpSecondaryYearCompleted').value,
                secondary_qualification: document.getElementById('newEmpSecondaryQualification').value,
                secondary_stream: document.getElementById('newEmpSecondaryStream').value,
                secondary_grades: document.getElementById('newEmpSecondaryGrades').value,
                // Tertiary Education
                tertiary_institution: document.getElementById('newEmpTertiaryInstitution').value,
                tertiary_location: document.getElementById('newEmpTertiaryLocation').value,
                tertiary_level: document.getElementById('newEmpTertiaryLevel').value,
                tertiary_institution_type: document.getElementById('newEmpTertiaryType').value,
                tertiary_field: document.getElementById('newEmpTertiaryField').value,
                tertiary_major: document.getElementById('newEmpTertiaryMajor').value,
                tertiary_year_started: document.getElementById('newEmpTertiaryYearStarted').value,
                tertiary_year_completed: document.getElementById('newEmpTertiaryYearCompleted').value,
                tertiary_status: document.getElementById('newEmpTertiaryStatus').value,
                tertiary_cgpa: document.getElementById('newEmpTertiaryCGPA').value
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
                    
                    // Upload files if employee was created successfully
                    const employeeId = data.employee_id || formData.employee_id;
                    if (employeeId) {
                        // Upload profile picture if selected
                        const profilePicInput = document.getElementById('newEmpProfilePic');
                        if (profilePicInput && profilePicInput.files.length > 0) {
                            await uploadEmployeeFile(employeeId, profilePicInput.files[0], 'profile-picture');
                        }
                        
                        // Upload resume if selected
                        const resumeInput = document.getElementById('newEmpResume');
                        if (resumeInput && resumeInput.files.length > 0) {
                            await uploadEmployeeFile(employeeId, resumeInput.files[0], 'resume');
                        }
                    }
                    
                    newEmployeeForm.reset();
                    clearProfilePicPreview('new');
                    clearResume('new');
                    
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
                // Get current calculation method
                const calculationMethod = document.getElementById('fixedRateBtn').classList.contains('active') ? 'fixed' : 'variable';
                
                const response = await fetch('/api/admin/payroll/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        payroll_date: payrollDate,
                        calculation_method: calculationMethod
                    })
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
        
        // Refresh payroll button
        const refreshPayrollBtn = document.getElementById('refreshPayrollBtn');
        if (refreshPayrollBtn) {
            refreshPayrollBtn.addEventListener('click', function() {
                loadPayrollRuns();
                messageDiv.style.display = 'block';
                messageDiv.className = 'success-message';
                messageDiv.textContent = 'Payroll history refreshed';
            });
        }
        
        // TP1 Reliefs button
        const tp1ReliefsBtn = document.getElementById('tp1ReliefsBtn');
        if (tp1ReliefsBtn) {
            tp1ReliefsBtn.addEventListener('click', function() {
                // Show info message using the payroll message div
                messageDiv.style.display = 'block';
                messageDiv.className = 'info-message';
                messageDiv.style.backgroundColor = '#e3f2fd';
                messageDiv.style.color = '#1976d2';
                messageDiv.style.border = '1px solid #90caf9';
                messageDiv.textContent = 'ℹ️ TP1 Relief Claims: This feature allows entering per-item TP1 relief claims for selected employees. Backend API implementation is pending.';
                
                // Auto-hide after 5 seconds
                setTimeout(() => {
                    messageDiv.style.display = 'none';
                }, 5000);
            });
        }
        
        // Calculation method toggle buttons
        const fixedRateBtn = document.getElementById('fixedRateBtn');
        const variablePercentBtn = document.getElementById('variablePercentBtn');
        const methodStatusLabel = document.getElementById('methodStatusLabel');
        
        if (fixedRateBtn && variablePercentBtn) {
            fixedRateBtn.addEventListener('click', async function() {
                if (!this.classList.contains('active')) {
                    fixedRateBtn.classList.add('active');
                    variablePercentBtn.classList.remove('active');
                    methodStatusLabel.textContent = '🔢 Current: Fixed Rate Calculation';
                    methodStatusLabel.style.color = 'green';
                    
                    // Persist preference to backend (gracefully handle if endpoint doesn't exist yet)
                    try {
                        await fetch('/api/admin/payroll/settings', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ calculation_method: 'fixed' })
                        });
                        console.log('Switched to Fixed Rate calculation method');
                    } catch (error) {
                        console.log('Note: Calculation method preference not persisted (API pending)');
                    }
                }
            });
            
            variablePercentBtn.addEventListener('click', async function() {
                if (!this.classList.contains('active')) {
                    variablePercentBtn.classList.add('active');
                    fixedRateBtn.classList.remove('active');
                    methodStatusLabel.textContent = '📊 Current: Variable Percentage Calculation';
                    methodStatusLabel.style.color = 'blue';
                    
                    // Persist preference to backend (gracefully handle if endpoint doesn't exist yet)
                    try {
                        await fetch('/api/admin/payroll/settings', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ calculation_method: 'variable' })
                        });
                        console.log('Switched to Variable Percentage calculation method');
                    } catch (error) {
                        console.log('Note: Calculation method preference not persisted (API pending)');
                    }
                }
            });
        }
    }
    
    async function loadBonuses() {
        try {
            const response = await fetch('/api/admin/bonuses');
            const data = await response.json();
            
            const tbody = document.getElementById('bonusTableBody');
            if (!tbody) return;
            
            if (data.success && data.data && data.data.length > 0) {
                const rowsHtml = buildBonusesTableRows(data.data);
                tbody.innerHTML = rowsHtml;
            } else {
                tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 20px;">No bonus records found.</td></tr>';
            }
        } catch (error) {
            console.error('Error loading bonuses:', error);
            const tbody = document.getElementById('bonusTableBody');
            if (tbody) tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 20px;">Error loading bonus data.</td></tr>';
        }
    }
    
    function buildBonusesTableRows(bonuses) {
        let html = '';
        
        bonuses.forEach(bonus => {
            html += '<tr>';
            html += `<td style="padding: 12px;">${bonus.employees?.full_name || bonus.employee_id || '-'}</td>`;
            html += `<td style="padding: 12px;">${bonus.bonus_type || '-'}</td>`;
            html += `<td style="padding: 12px; text-align: right;">${formatCurrency(bonus.amount)}</td>`;
            html += `<td style="padding: 12px;">${bonus.description || '-'}</td>`;
            html += `<td style="padding: 12px;">${bonus.pay_period || '-'}</td>`;
            html += `<td style="padding: 12px; text-align: center;">${bonus.status || '-'}</td>`;
            html += `<td style="padding: 12px;">${bonus.approved_by || '-'}</td>`;
            html += '<td style="padding: 12px; text-align: center;">';
            html += `<button class="btn-approve" onclick="editBonus('${bonus.id}')">Edit</button> `;
            html += `<button class="btn-reject" onclick="deleteBonus('${bonus.id}')">Delete</button>`;
            html += '</td>';
            html += '</tr>';
        });
        
        return html;
    }
    
    function setupBonusManagement() {
        const addBtn = document.getElementById('addBonusBtn');
        const cancelBtn = document.getElementById('cancelAddBonusBtn');
        const addForm = document.getElementById('addBonusForm');
        const newBonusForm = document.getElementById('newBonusForm');
        const messageDiv = document.getElementById('addBonusMessage');
        
        // Only setup event listeners if the elements exist
        if (addBtn) {
            addBtn.addEventListener('click', function() {
                if (addForm) {
                    addForm.style.display = 'block';
                    addBtn.style.display = 'none';
                }
            });
        }
        
        if (cancelBtn && addForm && newBonusForm && messageDiv) {
            cancelBtn.addEventListener('click', function() {
                addForm.style.display = 'none';
                if (addBtn) addBtn.style.display = 'inline-block';
                newBonusForm.reset();
                messageDiv.style.display = 'none';
            });
        }
        
        if (newBonusForm) {
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
                    
                    if (messageDiv) {
                        messageDiv.style.display = 'block';
                        if (data.success) {
                            messageDiv.className = 'success-message';
                            messageDiv.textContent = data.message;
                            newBonusForm.reset();
                            
                            // Reload bonus list
                            loadBonuses();
                            
                            // Hide form after a delay
                            setTimeout(() => {
                                if (addForm) addForm.style.display = 'none';
                                if (addBtn) addBtn.style.display = 'inline-block';
                                messageDiv.style.display = 'none';
                            }, 2000);
                        } else {
                            messageDiv.className = 'error-message';
                            messageDiv.textContent = data.message;
                        }
                    }
                } catch (error) {
                    if (messageDiv) {
                        messageDiv.style.display = 'block';
                        messageDiv.className = 'error-message';
                        messageDiv.textContent = 'Error creating bonus';
                    }
                    console.error('Error:', error);
                }
            });
        }
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
        
        // Download All PDFs button
        const downloadAllPDFsBtn = document.getElementById('downloadAllPDFsBtn');
        if (downloadAllPDFsBtn) {
            downloadAllPDFsBtn.addEventListener('click', async () => {
                alert('📥 Download All PDFs Feature\n\nThis feature will generate comprehensive PDF profiles for all employees.\n\nStatus: Coming Soon\nRequires: Backend PDF generation service\n\nPlease use individual employee view/edit for now.');
                // TODO: Implement PDF generation for all employees
                // This would call: POST /api/admin/employees/generate-pdfs
                // Backend would need to implement PDF generation using reportlab or similar
            });
        }
        
        // Print All Profiles button
        const printAllProfilesBtn = document.getElementById('printAllProfilesBtn');
        if (printAllProfilesBtn) {
            printAllProfilesBtn.addEventListener('click', () => {
                if (!confirm('Print all employee profiles?')) {
                    return;
                }
                
                // Store current display state
                const currentTab = document.querySelector('.tab-pane.active');
                
                // Show employee table for printing
                const employeeTab = document.getElementById('employeesTab');
                if (employeeTab) {
                    // Add print class to trigger print styles
                    document.body.classList.add('printing');
                    window.print();
                    document.body.classList.remove('printing');
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
    
    // Load leave balances
    let annualLeaveBalancesData = []; // Store for filtering
    
    async function loadLeaveBalances() {
        try {
            // Populate year selector if not already done
            const yearSelector = document.getElementById('annualLeaveYearSelector');
            if (yearSelector && yearSelector.options.length === 0) {
                const currentYear = new Date().getFullYear();
                for (let year = currentYear - 2; year <= currentYear + 2; year++) {
                    const option = document.createElement('option');
                    option.value = year;
                    option.textContent = year;
                    if (year === currentYear) option.selected = true;
                    yearSelector.appendChild(option);
                }
            }
            
            const year = yearSelector ? yearSelector.value : new Date().getFullYear();
            const response = await fetch(`/api/admin/leave-balances?year=${year}`);
            const data = await response.json();
            
            const tbody = document.getElementById('annualLeaveBalanceTable');
            if (!tbody) return;
            
            annualLeaveBalancesData = data.success && data.data ? data.data : [];
            applyAnnualLeaveFilters();
            
        } catch (error) {
            console.error('Error loading leave balances:', error);
            const tbody = document.getElementById('annualLeaveBalanceTable');
            if (tbody) tbody.innerHTML = '<p>Error loading leave balances.</p>';
        }
    }
    
    function applyAnnualLeaveFilters() {
        const filterText = document.getElementById('annualLeaveEmployeeFilter')?.value.toLowerCase() || '';
        
        // Filter data
        const filteredData = annualLeaveBalancesData.filter(balance => {
            const searchText = `${balance.full_name || ''} ${balance.email || ''} ${balance.department || ''}`.toLowerCase();
            return searchText.includes(filterText);
        });
        
        displayAnnualLeaveBalances(filteredData);
    }
    
    function displayAnnualLeaveBalances(data) {
        const tbody = document.getElementById('annualLeaveBalanceTable');
        if (!tbody) return;
        
        if (data.length > 0) {
                let html = '<table style="width: 100%; border-collapse: collapse; font-size: 14px;"><thead><tr style="background: #667eea; color: white;">';
                html += '<th style="padding: 10px; text-align: left;">Employee Email</th>';
                html += '<th style="padding: 10px; text-align: left;">Employee Name</th>';
                html += '<th style="padding: 10px; text-align: left;">Department</th>';
                html += '<th style="padding: 10px; text-align: center;">Employment Type</th>';
                html += '<th style="padding: 10px; text-align: center;">Years of Service</th>';
                html += '<th style="padding: 10px; text-align: center;">Annual<br>Entitlement</th>';
                html += '<th style="padding: 10px; text-align: center;">Used This<br>Year</th>';
                html += '<th style="padding: 10px; text-align: center;">Remaining<br>Balance</th>';
                html += '<th style="padding: 10px; text-align: center;">Carried<br>Forward</th>';
                html += '<th style="padding: 10px; text-align: center;">Total<br>Available</th>';
                html += '<th style="padding: 10px; text-align: center;">Actions</th>';
                html += '</tr></thead><tbody>';
                
                data.forEach(balance => {
                    // Calculate values with fallbacks
                    const annualEntitlement = balance.annual_entitlement || balance.total_leave || 14;
                    const usedDays = balance.used_days || balance.used_leave || 0;
                    const carriedForward = balance.carried_forward || 0;
                    const totalAvailable = balance.total_available || (annualEntitlement + carriedForward);
                    const remainingBalance = balance.remaining_days || balance.remaining_leave || (totalAvailable - usedDays);
                    const yearsOfService = balance.years_of_service !== undefined ? balance.years_of_service.toFixed(1) : '-';
                    
                    // Color coding for low balances
                    let rowStyle = '';
                    if (remainingBalance <= 0) {
                        rowStyle = 'background: #fee; ';
                    } else if (remainingBalance < 3) {
                        rowStyle = 'background: #fffbeb; ';
                    }
                    
                    html += `<tr style="border-bottom: 1px solid #eee; ${rowStyle}">`;
                    html += `<td style="padding: 10px;">${balance.email || '-'}</td>`;
                    html += `<td style="padding: 10px;"><strong>${balance.full_name || '-'}</strong></td>`;
                    html += `<td style="padding: 10px;">${balance.department || '-'}</td>`;
                    html += `<td style="padding: 10px; text-align: center;">${balance.employment_type || '-'}</td>`;
                    html += `<td style="padding: 10px; text-align: center;">${yearsOfService}</td>`;
                    html += `<td style="padding: 10px; text-align: center;">${annualEntitlement}</td>`;
                    html += `<td style="padding: 10px; text-align: center;">${usedDays}</td>`;
                    html += `<td style="padding: 10px; text-align: center;"><strong style="color: ${remainingBalance <= 0 ? '#dc2626' : remainingBalance < 3 ? '#d97706' : '#059669'};">${remainingBalance}</strong></td>`;
                    html += `<td style="padding: 10px; text-align: center;">${carriedForward}</td>`;
                    html += `<td style="padding: 10px; text-align: center;">${totalAvailable}</td>`;
                    html += `<td style="padding: 10px; text-align: center;"><button class="btn-secondary" style="padding: 5px 10px; font-size: 12px;" onclick="adjustLeaveBalance('${balance.email}')">Adjust</button></td>`;
                    html += '</tr>';
                });
                
                html += '</tbody></table>';
                html += `<p style="margin-top: 15px; color: #666; font-size: 14px;">Showing ${data.length} employee(s)</p>`;
                tbody.innerHTML = html;
            } else {
                tbody.innerHTML = '<p>No leave balance data available.</p>';
            }
    }
    
    // Adjust Leave Balance Functions
    window.adjustLeaveBalance = function(email) {
        // Find the balance data for this employee
        const balance = annualLeaveBalancesData.find(b => b.email === email);
        if (!balance) {
            alert('Employee data not found');
            return;
        }
        
        // Populate form
        document.getElementById('adjustEmployeeEmail').value = email;
        document.getElementById('adjustEmployeeName').textContent = `${balance.full_name} (${email})`;
        document.getElementById('adjustAnnualEntitlement').value = balance.annual_entitlement || balance.total_leave || 14;
        document.getElementById('adjustUsedDays').value = balance.used_days || balance.used_leave || 0;
        document.getElementById('adjustCarriedForward').value = balance.carried_forward || 0;
        
        // Show modal
        document.getElementById('adjustLeaveBalanceModal').style.display = 'block';
    };
    
    window.closeAdjustLeaveBalanceModal = function() {
        document.getElementById('adjustLeaveBalanceModal').style.display = 'none';
    };
    
    // Handle adjust form submission
    const adjustLeaveBalanceForm = document.getElementById('adjustLeaveBalanceForm');
    if (adjustLeaveBalanceForm) {
        adjustLeaveBalanceForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const email = document.getElementById('adjustEmployeeEmail').value;
            const yearSelector = document.getElementById('annualLeaveYearSelector');
            const year = yearSelector ? yearSelector.value : new Date().getFullYear();
            
            const data = {
                year: parseInt(year),
                annual_entitlement: parseFloat(document.getElementById('adjustAnnualEntitlement').value),
                used_days: parseFloat(document.getElementById('adjustUsedDays').value),
                carried_forward: parseFloat(document.getElementById('adjustCarriedForward').value)
            };
            
            try {
                const response = await fetch(`/api/admin/leave-balances/${encodeURIComponent(email)}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('Leave balance updated successfully');
                    closeAdjustLeaveBalanceModal();
                    loadLeaveBalances();
                } else {
                    alert('Error: ' + (result.message || 'Failed to update leave balance'));
                }
            } catch (error) {
                console.error('Error updating leave balance:', error);
                alert('Error updating leave balance');
            }
        });
    }
    
    // Set Carry Forward for All Functions
    window.openSetCarryForwardAllModal = function() {
        document.getElementById('setCarryForwardAllModal').style.display = 'block';
    };
    
    window.closeSetCarryForwardAllModal = function() {
        document.getElementById('setCarryForwardAllModal').style.display = 'none';
    };
    
    const setCarryForwardAllForm = document.getElementById('setCarryForwardAllForm');
    if (setCarryForwardAllForm) {
        setCarryForwardAllForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const days = parseInt(document.getElementById('carryForwardDays').value);
            const appliesTo = document.getElementById('carryForwardAppliesTo').value;
            const yearSelector = document.getElementById('annualLeaveYearSelector');
            const currentYear = yearSelector ? parseInt(yearSelector.value) : new Date().getFullYear();
            
            if (!confirm(`Set ${days} carried forward days for all employees for year ${currentYear + 1}?`)) {
                return;
            }
            
            try {
                const response = await fetch('/api/admin/leave-balances/set-carry-forward-all', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        current_year: currentYear,
                        next_year: currentYear + 1,
                        days: days,
                        applies_to: appliesTo
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert(result.message || 'Carried forward set successfully for all employees');
                    closeSetCarryForwardAllModal();
                    loadLeaveBalances();
                } else {
                    alert('Error: ' + (result.message || 'Failed to set carry forward'));
                }
            } catch (error) {
                console.error('Error setting carry forward:', error);
                alert('Error setting carry forward for all');
            }
        });
    }
    
    // Process Carry Forward Functions
    window.openProcessCarryForwardModal = function() {
        document.getElementById('processCarryForwardModal').style.display = 'block';
    };
    
    window.closeProcessCarryForwardModal = function() {
        document.getElementById('processCarryForwardModal').style.display = 'none';
    };
    
    window.confirmProcessCarryForward = async function() {
        const maxDays = parseInt(document.getElementById('carryForwardMaxDays').value);
        const yearSelector = document.getElementById('annualLeaveYearSelector');
        const year = yearSelector ? parseInt(yearSelector.value) : new Date().getFullYear();
        
        if (!confirm(`Process year-end carry forward for all employees from ${year} to ${year + 1}?\n\nMaximum carry forward: ${maxDays} days`)) {
            return;
        }
        
        try {
            const response = await fetch('/api/admin/leave-balances/carry-forward', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    year: year,
                    rules: {
                        max_carry_forward: maxDays
                    }
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert(result.message || 'Carry forward processed successfully');
                closeProcessCarryForwardModal();
                loadLeaveBalances();
            } else {
                alert('Error: ' + (result.message || 'Failed to process carry forward'));
            }
        } catch (error) {
            console.error('Error processing carry forward:', error);
            alert('Error processing carry forward');
        }
    };
    
    let sickLeaveBalancesData = []; // Store for filtering
    
    async function loadSickLeaveBalances() {
        try {
            // Populate year selector if not already done
            const yearSelector = document.getElementById('sickLeaveYearSelector');
            if (yearSelector && yearSelector.options.length === 0) {
                const currentYear = new Date().getFullYear();
                for (let year = currentYear - 2; year <= currentYear + 2; year++) {
                    const option = document.createElement('option');
                    option.value = year;
                    option.textContent = year;
                    if (year === currentYear) option.selected = true;
                    yearSelector.appendChild(option);
                }
            }
            
            const year = yearSelector ? yearSelector.value : new Date().getFullYear();
            const response = await fetch(`/api/admin/sick-leave-balances?year=${year}`);
            const data = await response.json();
            
            sickLeaveBalancesData = data.success && data.data ? data.data : [];
            applySickLeaveFilters();
            
        } catch (error) {
            console.error('Error loading sick leave balances:', error);
            const tbody = document.getElementById('sickLeaveBalanceTable');
            if (tbody) tbody.innerHTML = '<p style="color: red;">Error loading sick leave balances.</p>';
        }
    }
    
    function applySickLeaveFilters() {
        const filterText = document.getElementById('sickLeaveEmployeeFilter')?.value.toLowerCase() || '';
        
        // Filter data
        const filteredData = sickLeaveBalancesData.filter(balance => {
            const searchText = `${balance.full_name || ''} ${balance.email || ''} ${balance.department || ''}`.toLowerCase();
            return searchText.includes(filterText);
        });
        
        displaySickLeaveBalances(filteredData);
    }
    
    function displaySickLeaveBalances(data) {
        const tbody = document.getElementById('sickLeaveBalanceTable');
        if (!tbody) return;
        
        if (data.length === 0) {
            tbody.innerHTML = '<p>No sick leave balance data found.</p>';
            return;
        }
        
        let html = '<table style="width: 100%; border-collapse: collapse; font-size: 14px;"><thead><tr style="background: #667eea; color: white;">';
        html += '<th style="padding: 10px; text-align: left;">Email</th>';
        html += '<th style="padding: 10px; text-align: left;">Name</th>';
        html += '<th style="padding: 10px; text-align: left;">Department</th>';
        html += '<th style="padding: 10px; text-align: center;">Years of Service</th>';
        html += '<th style="padding: 10px; text-align: center;">Sick Days<br>Entitlement</th>';
        html += '<th style="padding: 10px; text-align: center;">Used Sick<br>Days</th>';
        html += '<th style="padding: 10px; text-align: center;">Remaining<br>Sick Days</th>';
        html += '<th style="padding: 10px; text-align: center;">Hospitalization<br>Entitlement</th>';
        html += '<th style="padding: 10px; text-align: center;">Used<br>Hospitalization</th>';
        html += '<th style="padding: 10px; text-align: center;">Remaining<br>Hospitalization</th>';
        html += '<th style="padding: 10px; text-align: center;">Actions</th>';
        html += '</tr></thead><tbody>';
        
        data.forEach(balance => {
            const remainingSick = (balance.sick_days_entitlement || 14) - (balance.used_sick_days || 0);
            const remainingHosp = (balance.hospitalization_days_entitlement || 60) - (balance.used_hospitalization_days || 0);
            
            // Color coding for low balances
            let sickRowStyle = '';
            if (remainingSick <= 0) {
                sickRowStyle = 'background: #fee; '; // Red for zero/negative
            } else if (remainingSick < 3) {
                sickRowStyle = 'background: #fffbeb; '; // Yellow for low
            }
            
            html += `<tr style="border-bottom: 1px solid #eee; ${sickRowStyle}">`;
            html += `<td style="padding: 10px;">${balance.email || '-'}</td>`;
            html += `<td style="padding: 10px;"><strong>${balance.full_name || '-'}</strong></td>`;
            html += `<td style="padding: 10px;">${balance.department || '-'}</td>`;
            html += `<td style="padding: 10px; text-align: center;">${balance.years_of_service_display || balance.years_of_service?.toFixed(1) || '-'}</td>`;
            html += `<td style="padding: 10px; text-align: center;">${balance.sick_days_entitlement || 14}</td>`;
            html += `<td style="padding: 10px; text-align: center;">${balance.used_sick_days || 0}</td>`;
            html += `<td style="padding: 10px; text-align: center;"><strong style="color: ${remainingSick <= 0 ? '#dc2626' : remainingSick < 3 ? '#d97706' : '#059669'};">${remainingSick}</strong></td>`;
            html += `<td style="padding: 10px; text-align: center;">${balance.hospitalization_days_entitlement || 60}</td>`;
            html += `<td style="padding: 10px; text-align: center;">${balance.used_hospitalization_days || 0}</td>`;
            html += `<td style="padding: 10px; text-align: center;"><strong>${remainingHosp}</strong></td>`;
            html += `<td style="padding: 10px; text-align: center;"><button class="btn-secondary" style="padding: 5px 10px; font-size: 12px;" onclick="viewSickLeaveDetails('${balance.email}')">View Details</button></td>`;
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        tbody.innerHTML = html;
    }
    
    window.viewSickLeaveDetails = async function(email) {
        alert(`Detailed view for ${email} will be implemented in future update.\n\nFeatures:\n- View/edit sick leave balances\n- Manual adjustments\n- Leave history`);
    }
    
    function showEmploymentActInfo() {
        const message = `📖 Employment Act 1955 - Sick Leave Provisions\n\n` +
            `Section 60F: Sick Leave Entitlement\n\n` +
            `An employee is entitled to paid sick leave if:\n` +
            `1. Hospitalization - Number of days hospitalized, up to 60 days per year\n` +
            `2. Outpatient treatment:\n` +
            `   • 14 days per year (for employees with < 2 years of service)\n` +
            `   • 18 days per year (for employees with 2-5 years of service)\n` +
            `   • 22 days per year (for employees with > 5 years of service)\n\n` +
            `Note: Sick leave entitlement includes hospitalization leave.\n\n` +
            `Requirements:\n` +
            `• Medical certificate required for more than 2 consecutive days\n` +
            `• Certificate must be from registered medical practitioner\n` +
            `• Certification for hospitalization leave is mandatory`;
        alert(message);
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
    
    // Contributions Management Functions
    window.loadContributions = async function() {
        try {
            const response = await fetch('/api/admin/payroll-contributions');
            const data = await response.json();
            
            const tableContainer = document.getElementById('contributionsTable');
            if (!tableContainer) return;
            
            if (data.success && data.data && data.data.length > 0) {
                // Apply filters
                const monthFilter = document.getElementById('contribMonthFilter')?.value || '';
                const employeeFilter = document.getElementById('contribEmployeeFilter')?.value.toLowerCase() || '';
                const citizenFilter = document.getElementById('contribCitizenFilter')?.value || '';
                
                let filteredData = data.data;
                
                if (monthFilter) {
                    const [year, month] = monthFilter.split('-');
                    const filterMonthYear = `${month}/${year}`;
                    filteredData = filteredData.filter(c => c.month_year === filterMonthYear);
                }
                
                if (employeeFilter) {
                    filteredData = filteredData.filter(c => 
                        (c.employee_name || '').toLowerCase().includes(employeeFilter)
                    );
                }
                
                if (filteredData.length === 0) {
                    tableContainer.innerHTML = '<p style="color: #666;">No contributions found matching the filters.</p>';
                    return;
                }
                
                let html = '<table style="width: 100%; border-collapse: collapse; margin-top: 10px;"><thead><tr style="background: #667eea; color: white;">';
                html += '<th style="padding: 10px;">Employee</th>';
                html += '<th style="padding: 10px;">Period</th>';
                html += '<th style="padding: 10px; text-align: right;">EPF (Ee)</th>';
                html += '<th style="padding: 10px; text-align: right;">EPF (Er)</th>';
                html += '<th style="padding: 10px; text-align: right;">SOCSO (Ee)</th>';
                html += '<th style="padding: 10px; text-align: right;">SOCSO (Er)</th>';
                html += '<th style="padding: 10px; text-align: right;">EIS (Ee)</th>';
                html += '<th style="padding: 10px; text-align: right;">EIS (Er)</th>';
                html += '<th style="padding: 10px; text-align: right;">PCB</th>';
                html += '<th style="padding: 10px; text-align: right;">Total (Ee)</th>';
                html += '<th style="padding: 10px; text-align: right;">Total (Er)</th>';
                html += '</tr></thead><tbody>';
                
                let totalEpfEe = 0, totalEpfEr = 0, totalSocsoEe = 0, totalSocsoEr = 0, totalEisEe = 0, totalEisEr = 0, totalPcb = 0;
                
                filteredData.forEach(contrib => {
                    const epfEe = parseFloat(contrib.epf_employee) || 0;
                    const epfEr = parseFloat(contrib.epf_employer) || 0;
                    const socsoEe = parseFloat(contrib.socso_employee) || 0;
                    const socsoEr = parseFloat(contrib.socso_employer) || 0;
                    const eisEe = parseFloat(contrib.eis) || 0;
                    const eisEr = parseFloat(contrib.eis_employer) || 0;
                    const pcb = parseFloat(contrib.pcb) || 0;
                    const totalEe = epfEe + socsoEe + eisEe;
                    const totalEr = epfEr + socsoEr + eisEr;
                    
                    totalEpfEe += epfEe;
                    totalEpfEr += epfEr;
                    totalSocsoEe += socsoEe;
                    totalSocsoEr += socsoEr;
                    totalEisEe += eisEe;
                    totalEisEr += eisEr;
                    totalPcb += pcb;
                    
                    html += '<tr style="border-bottom: 1px solid #eee;">';
                    html += `<td style="padding: 10px;">${contrib.employee_name || '-'}</td>`;
                    html += `<td style="padding: 10px;">${contrib.month_year || '-'}</td>`;
                    html += `<td style="padding: 10px; text-align: right;">RM ${epfEe.toFixed(2)}</td>`;
                    html += `<td style="padding: 10px; text-align: right;">RM ${epfEr.toFixed(2)}</td>`;
                    html += `<td style="padding: 10px; text-align: right;">RM ${socsoEe.toFixed(2)}</td>`;
                    html += `<td style="padding: 10px; text-align: right;">RM ${socsoEr.toFixed(2)}</td>`;
                    html += `<td style="padding: 10px; text-align: right;">RM ${eisEe.toFixed(2)}</td>`;
                    html += `<td style="padding: 10px; text-align: right;">RM ${eisEr.toFixed(2)}</td>`;
                    html += `<td style="padding: 10px; text-align: right;">RM ${pcb.toFixed(2)}</td>`;
                    html += `<td style="padding: 10px; text-align: right;"><strong>RM ${totalEe.toFixed(2)}</strong></td>`;
                    html += `<td style="padding: 10px; text-align: right;"><strong>RM ${totalEr.toFixed(2)}</strong></td>`;
                    html += '</tr>';
                });
                
                // Add totals row
                html += '<tr style="background: #f0f0f0; font-weight: bold;">';
                html += '<td style="padding: 10px;" colspan="2">TOTAL</td>';
                html += `<td style="padding: 10px; text-align: right;">RM ${totalEpfEe.toFixed(2)}</td>`;
                html += `<td style="padding: 10px; text-align: right;">RM ${totalEpfEr.toFixed(2)}</td>`;
                html += `<td style="padding: 10px; text-align: right;">RM ${totalSocsoEe.toFixed(2)}</td>`;
                html += `<td style="padding: 10px; text-align: right;">RM ${totalSocsoEr.toFixed(2)}</td>`;
                html += `<td style="padding: 10px; text-align: right;">RM ${totalEisEe.toFixed(2)}</td>`;
                html += `<td style="padding: 10px; text-align: right;">RM ${totalEisEr.toFixed(2)}</td>`;
                html += `<td style="padding: 10px; text-align: right;">RM ${totalPcb.toFixed(2)}</td>`;
                html += `<td style="padding: 10px; text-align: right;">RM ${(totalEpfEe + totalSocsoEe + totalEisEe).toFixed(2)}</td>`;
                html += `<td style="padding: 10px; text-align: right;">RM ${(totalEpfEr + totalSocsoEr + totalEisEr).toFixed(2)}</td>`;
                html += '</tr>';
                
                html += '</tbody></table>';
                html += `<p style="margin-top: 15px; color: #666; font-size: 14px;">Showing ${filteredData.length} contribution record(s)</p>`;
                tableContainer.innerHTML = html;
            } else {
                tableContainer.innerHTML = '<p style="color: #666;">No contribution data available. Run payroll first.</p>';
            }
        } catch (error) {
            console.error('Error loading contributions:', error);
            const tableContainer = document.getElementById('contributionsTable');
            if (tableContainer) tableContainer.innerHTML = '<p style="color: #f44336;">Error loading contributions data.</p>';
        }
    };
    
    window.uploadRatePDF = async function(contributionType) {
        const fileInput = document.getElementById(`${contributionType}RateFile`);
        const messageDiv = document.getElementById('uploadRateMessage');
        
        if (!fileInput.files || fileInput.files.length === 0) {
            messageDiv.style.display = 'block';
            messageDiv.className = 'error-message';
            messageDiv.style.background = '#ffebee';
            messageDiv.style.color = '#c62828';
            messageDiv.textContent = 'Please select a PDF file first';
            return;
        }
        
        const file = fileInput.files[0];
        
        if (!file.name.endsWith('.pdf')) {
            messageDiv.style.display = 'block';
            messageDiv.className = 'error-message';
            messageDiv.style.background = '#ffebee';
            messageDiv.style.color = '#c62828';
            messageDiv.textContent = 'Only PDF files are supported';
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('contribution_type', contributionType);
        
        try {
            messageDiv.style.display = 'block';
            messageDiv.style.background = '#e3f2fd';
            messageDiv.style.color = '#1976d2';
            messageDiv.textContent = `Uploading ${contributionType.toUpperCase()} rate table...`;
            
            const response = await fetch(`/api/admin/contributions/upload-rates?contribution_type=${contributionType}`, {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                messageDiv.style.background = '#e8f5e9';
                messageDiv.style.color = '#2e7d32';
                messageDiv.textContent = `✅ ${result.message}`;
                if (result.note) {
                    messageDiv.textContent += ` Note: ${result.note}`;
                }
                fileInput.value = ''; // Clear the file input
            } else {
                messageDiv.style.background = '#ffebee';
                messageDiv.style.color = '#c62828';
                messageDiv.textContent = `❌ ${result.message}`;
            }
        } catch (error) {
            console.error('Error uploading rate PDF:', error);
            messageDiv.style.display = 'block';
            messageDiv.style.background = '#ffebee';
            messageDiv.style.color = '#c62828';
            messageDiv.textContent = `❌ Error uploading file: ${error.message}`;
        }
    };
    
    window.exportContributionsCSV = async function() {
        try {
            const response = await fetch('/api/admin/contributions/export/csv');
            if (response.ok) {
                const blob = await response.blob();
                downloadBlob(blob, `contributions_${new Date().toISOString().split('T')[0]}.csv`);
            } else {
                alert('Failed to export contributions data');
            }
        } catch (error) {
            console.error('Error exporting contributions:', error);
            alert('Error exporting contributions data');
        }
    };
    
    // Salary History Management Functions
    window.showAddSalaryChangeForm = function() {
        document.getElementById('addSalaryChangeForm').style.display = 'block';
    };
    
    window.hideAddSalaryChangeForm = function() {
        document.getElementById('addSalaryChangeForm').style.display = 'none';
        document.getElementById('newSalaryChangeForm').reset();
        document.getElementById('addSalaryChangeMessage').style.display = 'none';
    };
    
    async function loadSalaryHistory() {
        try {
            const response = await fetch('/api/admin/salary-history');
            const data = await response.json();
            
            const tableContainer = document.getElementById('salaryHistoryTable');
            if (!tableContainer) return;
            
            if (data.success && data.data && data.data.length > 0) {
                // Apply filters
                const employeeFilter = document.getElementById('salaryHistoryEmployeeFilter')?.value.toLowerCase() || '';
                const typeFilter = document.getElementById('salaryHistoryTypeFilter')?.value || '';
                const yearFilter = document.getElementById('salaryHistoryYearFilter')?.value || '';
                
                let filteredData = data.data;
                
                if (employeeFilter) {
                    filteredData = filteredData.filter(r => 
                        ((r.employee_name || '').toLowerCase().includes(employeeFilter)) ||
                        ((r.employee_email || '').toLowerCase().includes(employeeFilter))
                    );
                }
                
                if (typeFilter) {
                    filteredData = filteredData.filter(r => r.change_type === typeFilter);
                }
                
                if (yearFilter) {
                    filteredData = filteredData.filter(r => {
                        const date = r.effective_date || '';
                        return date.startsWith(yearFilter);
                    });
                }
                
                if (filteredData.length === 0) {
                    let message = '<p style="color: #666;">No salary history records found';
                    if (employeeFilter) {
                        message += ' for the selected employee';
                    }
                    message += '.</p>';
                    if (employeeFilter) {
                        message += '<p style="color: #999; font-size: 14px; margin-top: 10px;">This employee has no salary change history yet. You can add salary changes using the form on the left.</p>';
                    }
                    tableContainer.innerHTML = message;
                    return;
                }
                
                let html = '<table style="width: 100%; border-collapse: collapse; margin-top: 10px;"><thead><tr style="background: #667eea; color: white;">';
                html += '<th style="padding: 10px;">Effective Date</th>';
                html += '<th style="padding: 10px;">Employee</th>';
                html += '<th style="padding: 10px;">Change Type</th>';
                html += '<th style="padding: 10px;">Previous Salary</th>';
                html += '<th style="padding: 10px;">New Salary</th>';
                html += '<th style="padding: 10px;">Change</th>';
                html += '<th style="padding: 10px;">Reason</th>';
                html += '<th style="padding: 10px;">Actions</th>';
                html += '</tr></thead><tbody>';
                
                filteredData.forEach(record => {
                    // Parse salary values, defaulting to 0 for calculation purposes
                    // Database stores: previous_salary, new_salary (not previous_value, new_value)
                    const prevSalary = parseFloat(record.previous_salary) || 0;
                    const newSalary = parseFloat(record.new_salary) || 0;
                    const change = newSalary - prevSalary;
                    const changePercent = prevSalary > 0 ? (change / prevSalary * 100) : 0;
                    const changeColor = change >= 0 ? '#2e7d32' : '#c62828';
                    
                    html += '<tr style="border-bottom: 1px solid #eee;">';
                    html += `<td style="padding: 10px;">${record.effective_date || '-'}</td>`;
                    // Prefer showing name over email for better readability, with consistent fallback chain
                    const employeeName = record.employee_name || record.employee_email || record.employee?.full_name || '-';
                    html += `<td style="padding: 10px;">${employeeName}</td>`;
                    // Database stores change type in 'reason' field
                    html += `<td style="padding: 10px;"><span style="background: #e3f2fd; padding: 4px 8px; border-radius: 4px; color: #1976d2; font-size: 12px;">${record.reason || record.change_type || '-'}</span></td>`;
                    html += `<td style="padding: 10px;">${formatCurrency(record.previous_salary)}</td>`;
                    html += `<td style="padding: 10px;"><strong>${formatCurrency(record.new_salary)}</strong></td>`;
                    // Only show change if both values exist
                    if (record.previous_salary && record.new_salary) {
                        html += `<td style="padding: 10px; color: ${changeColor};"><strong>${change >= 0 ? '+' : ''}RM ${change.toFixed(2)} (${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(1)}%)</strong></td>`;
                    } else {
                        html += `<td style="padding: 10px;">-</td>`;
                    }
                    html += `<td style="padding: 10px;"><small>${record.notes || record.reason || '-'}</small></td>`;
                    html += '<td style="padding: 10px;">';
                    html += `<button class="btn-secondary btn-sm" onclick="editSalaryHistory('${record.id}')" style="margin-right: 5px;">✏️ Edit</button>`;
                    html += `<button class="btn-reject btn-sm" onclick="deleteSalaryHistory('${record.id}')">🗑️ Delete</button>`;
                    html += '</td>';
                    html += '</tr>';
                });
                
                html += '</tbody></table>';
                let summaryText = `<p style="margin-top: 15px; color: #666; font-size: 14px;">Showing ${filteredData.length} salary change record(s)`;
                if (employeeFilter) {
                    summaryText += ` for selected employee`;
                }
                summaryText += '</p>';
                html += summaryText;
                tableContainer.innerHTML = html;
            } else {
                tableContainer.innerHTML = '<p style="color: #666;">No salary history records found. Record salary changes using the "Record Salary Change" button above.</p>';
            }
        } catch (error) {
            console.error('Error loading salary history:', error);
            const tableContainer = document.getElementById('salaryHistoryTable');
            if (tableContainer) tableContainer.innerHTML = '<p style="color: #f44336;">Error loading salary history data.</p>';
        }
    }
    
    // Handle new salary change form submission
    const newSalaryChangeForm = document.getElementById('newSalaryChangeForm');
    if (newSalaryChangeForm) {
        newSalaryChangeForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(newSalaryChangeForm);
            const data = {};
            
            for (let [key, value] of formData.entries()) {
                data[key] = value;
            }
            
            try {
                const response = await fetch('/api/admin/salary-history', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                const messageDiv = document.getElementById('addSalaryChangeMessage');
                messageDiv.style.display = 'block';
                
                if (result.success) {
                    messageDiv.className = 'success-message';
                    messageDiv.textContent = '✅ Salary change recorded successfully!';
                    
                    setTimeout(() => {
                        hideAddSalaryChangeForm();
                        loadSalaryHistory();
                    }, 1500);
                } else {
                    messageDiv.className = 'error-message';
                    messageDiv.textContent = result.message || 'Failed to record salary change';
                }
            } catch (error) {
                console.error('Error recording salary change:', error);
                const messageDiv = document.getElementById('addSalaryChangeMessage');
                messageDiv.style.display = 'block';
                messageDiv.className = 'error-message';
                messageDiv.textContent = 'Error recording salary change';
            }
        });
    }
    
    window.exportSalaryHistoryCSV = async function() {
        try {
            const response = await fetch('/api/admin/salary-history/export/csv');
            if (response.ok) {
                const blob = await response.blob();
                downloadBlob(blob, `salary_history_${new Date().toISOString().split('T')[0]}.csv`);
            } else {
                alert('Failed to export salary history');
            }
        } catch (error) {
            console.error('Error exporting salary history:', error);
            alert('Error exporting salary history');
        }
    };
    
    // Load employees into the salary history employee selector
    async function loadSalaryHistoryEmployeeSelector() {
        try {
            const response = await fetch('/api/employees');
            const data = await response.json();
            
            const selector = document.getElementById('salaryHistoryEmployeeSelect');
            if (!selector) return;
            
            if (data.success && data.data && data.data.length > 0) {
                selector.innerHTML = '<option value="">Select Employee</option>';
                data.data.forEach(emp => {
                    const option = document.createElement('option');
                    option.value = emp.email;
                    option.textContent = `${emp.full_name || emp.email} - ${emp.department || 'N/A'}`;
                    option.dataset.salary = emp.basic_salary || 0;
                    selector.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading employees for salary history:', error);
        }
    }
    
    // Update current salary display when employee is selected
    if (document.getElementById('salaryHistoryEmployeeSelect')) {
        document.getElementById('salaryHistoryEmployeeSelect').addEventListener('change', function(e) {
            const selectedOption = this.options[this.selectedIndex];
            const salary = selectedOption.dataset.salary || 0;
            const selectedEmail = selectedOption.value;
            const employeeName = selectedOption.textContent;
            
            const salaryDisplay = document.getElementById('currentSalaryDisplay');
            if (salaryDisplay) {
                salaryDisplay.textContent = `RM ${parseFloat(salary).toFixed(2)}`;
            }
            
            // Auto-fill the employee email in the form
            const emailInput = document.getElementById('salaryChangeEmployee');
            if (emailInput) {
                emailInput.value = selectedEmail;
            }
            
            // Auto-fill previous salary
            const prevSalaryInput = document.getElementById('salaryChangePrevious');
            if (prevSalaryInput) {
                prevSalaryInput.value = parseFloat(salary).toFixed(2);
            }
            
            // Show/update employee status indicator
            const statusDiv = document.getElementById('salaryHistoryEmployeeStatus');
            const statusName = document.getElementById('salaryHistoryEmployeeName');
            
            // Filter the table to show only this employee's salary history
            if (selectedEmail) {
                const employeeFilterInput = document.getElementById('salaryHistoryEmployeeFilter');
                if (employeeFilterInput) {
                    employeeFilterInput.value = selectedEmail;
                }
                
                // Show status indicator
                if (statusDiv && statusName) {
                    statusName.textContent = employeeName;
                    statusDiv.style.display = 'block';
                }
                
                loadSalaryHistory();
            } else {
                // Clear the filter when "Select Employee" is chosen
                const employeeFilterInput = document.getElementById('salaryHistoryEmployeeFilter');
                if (employeeFilterInput) {
                    employeeFilterInput.value = '';
                }
                // Reset salary display
                if (salaryDisplay) {
                    salaryDisplay.textContent = 'RM 0.00';
                }
                
                // Hide status indicator
                if (statusDiv) {
                    statusDiv.style.display = 'none';
                }
                
                loadSalaryHistory();
            }
        });
    }
    
    // Update Current Salary function - updates employee's basic salary in their profile
    window.updateCurrentSalary = async function() {
        const employeeEmail = document.getElementById('salaryChangeEmployee')?.value;
        const newSalary = document.getElementById('salaryChangeNew')?.value;
        
        if (!employeeEmail || !newSalary) {
            alert('Please fill in Employee Email and New Salary fields');
            return;
        }
        
        if (!confirm(`Update ${employeeEmail}'s current basic salary to RM ${parseFloat(newSalary).toFixed(2)}?\n\nThis will update their employee profile.`)) {
            return;
        }
        
        try {
            // Find the employee ID
            const empResponse = await fetch('/api/employees');
            const empData = await empResponse.json();
            
            if (!empData.success || !empData.data) {
                alert('Failed to fetch employee data');
                return;
            }
            
            const employee = empData.data.find(emp => emp.email === employeeEmail);
            if (!employee) {
                alert('Employee not found');
                return;
            }
            
            // Update the employee's basic salary
            const updateResponse = await fetch(`/api/admin/employees/${employee.id || employee.email}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    basic_salary: parseFloat(newSalary)
                })
            });
            
            const result = await updateResponse.json();
            
            if (result.success) {
                alert('✅ Current salary updated successfully!');
                
                // Refresh the employee selector
                loadSalaryHistoryEmployeeSelector();
                
                // Update the display
                const salaryDisplay = document.getElementById('currentSalaryDisplay');
                if (salaryDisplay) {
                    salaryDisplay.textContent = `RM ${parseFloat(newSalary).toFixed(2)}`;
                }
                
                const lastUpdatedDisplay = document.getElementById('lastUpdatedDisplay');
                if (lastUpdatedDisplay) {
                    lastUpdatedDisplay.textContent = new Date().toLocaleDateString();
                }
            } else {
                alert('Failed to update current salary: ' + (result.message || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error updating current salary:', error);
            alert('Error updating current salary: ' + error.message);
        }
    };
    
    // Engagements Management Functions (Admin)
    // Load employees into the engagement form employee selector
    async function loadEngagementEmployeeSelector() {
        try {
            const response = await fetch('/api/employees');
            const data = await response.json();
            
            const selector = document.getElementById('adminEngEmployeeEmail');
            
            if (selector && data.success && data.data && data.data.length > 0) {
                selector.innerHTML = '<option value="">Select Employee</option>';
                data.data.forEach(emp => {
                    const option = document.createElement('option');
                    option.value = emp.email;
                    option.textContent = `${emp.full_name || emp.email} - ${emp.department || 'N/A'}`;
                    selector.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading employees for engagement form:', error);
        }
    }
    
    // Load employees when page loads
    if (document.getElementById('adminEngEmployeeEmail')) {
        loadEngagementEmployeeSelector();
    }
    
    const adminEngagementForm = document.getElementById('adminEngagementForm');
    if (adminEngagementForm) {
        adminEngagementForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(adminEngagementForm);
            const data = {};
            
            for (let [key, value] of formData.entries()) {
                data[key] = value;
            }
            
            try {
                const response = await fetch('/api/engagements', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                const messageDiv = document.getElementById('adminEngagementMessage');
                messageDiv.style.display = 'block';
                
                if (result.success) {
                    messageDiv.className = 'success-message';
                    messageDiv.textContent = '✅ Engagement submitted successfully!';
                    adminEngagementForm.reset();
                    
                    setTimeout(() => {
                        messageDiv.style.display = 'none';
                    }, 3000);
                } else {
                    messageDiv.className = 'error-message';
                    messageDiv.textContent = result.message || 'Failed to submit engagement';
                }
            } catch (error) {
                console.error('Error submitting engagement:', error);
                const messageDiv = document.getElementById('adminEngagementMessage');
                messageDiv.style.display = 'block';
                messageDiv.className = 'error-message';
                messageDiv.textContent = 'Error submitting engagement';
            }
        });
    }
    
    window.loadAllEngagements = async function() {
        try {
            const response = await fetch('/api/admin/engagements/all');
            const data = await response.json();
            
            const tableContainer = document.getElementById('allEngagementsTable');
            if (!tableContainer) return;
            
            if (data.success && data.data && data.data.length > 0) {
                // Apply filters
                const typeFilter = document.getElementById('engTypeFilter')?.value || '';
                const employeeFilter = document.getElementById('engEmployeeFilter')?.value.toLowerCase() || '';
                const statusFilter = document.getElementById('engStatusFilter')?.value || '';
                
                let filteredData = data.data;
                
                if (typeFilter) {
                    filteredData = filteredData.filter(r => r.type === typeFilter);
                }
                
                if (employeeFilter) {
                    filteredData = filteredData.filter(r => 
                        ((r.employee_email || '').toLowerCase().includes(employeeFilter)) ||
                        ((r.employee_name || '').toLowerCase().includes(employeeFilter))
                    );
                }
                
                if (statusFilter) {
                    filteredData = filteredData.filter(r => r.status === statusFilter);
                }
                
                if (filteredData.length === 0) {
                    tableContainer.innerHTML = '<p style="color: #666;">No engagements found matching the filters.</p>';
                    return;
                }
                
                let html = '<table style="width: 100%; border-collapse: collapse; margin-top: 10px;"><thead><tr style="background: #667eea; color: white;">';
                html += '<th style="padding: 10px;">Type</th>';
                html += '<th style="padding: 10px;">Title</th>';
                html += '<th style="padding: 10px;">Employee</th>';
                html += '<th style="padding: 10px;">Start Date</th>';
                html += '<th style="padding: 10px;">End Date</th>';
                html += '<th style="padding: 10px;">Location</th>';
                html += '<th style="padding: 10px;">Cost</th>';
                html += '<th style="padding: 10px;">Status</th>';
                html += '<th style="padding: 10px;">Actions</th>';
                html += '</tr></thead><tbody>';
                
                filteredData.forEach(record => {
                    const statusColors = {
                        'approved': '#2e7d32',
                        'completed': '#1976d2',
                        'pending': '#f57c00',
                        'cancelled': '#c62828'
                    };
                    const statusColor = statusColors[record.status] || '#666';
                    
                    html += '<tr style="border-bottom: 1px solid #eee;">';
                    html += `<td style="padding: 10px;"><span style="background: #e3f2fd; padding: 4px 8px; border-radius: 4px; font-size: 12px;">${record.type || '-'}</span></td>`;
                    html += `<td style="padding: 10px;"><strong>${record.title || '-'}</strong></td>`;
                    // Show employee name first, fall back to email if name not available
                    html += `<td style="padding: 10px;">${record.employee_name || record.employees?.full_name || record.employee_email || '-'}</td>`;
                    html += `<td style="padding: 10px;">${record.start_date || '-'}</td>`;
                    html += `<td style="padding: 10px;">${record.end_date || '-'}</td>`;
                    html += `<td style="padding: 10px;">${record.location || '-'}</td>`;
                    html += `<td style="padding: 10px;">${formatCurrency(record.cost)}</td>`;
                    html += `<td style="padding: 10px;"><span style="color: ${statusColor}; font-weight: bold;">${record.status || '-'}</span></td>`;
                    html += '<td style="padding: 10px;">';
                    html += `<button class="btn-secondary btn-sm" onclick="editEngagement('${record.id}')" style="margin-right: 5px;">✏️ Edit</button>`;
                    html += `<button class="btn-reject btn-sm" onclick="deleteEngagement('${record.id}')">🗑️ Delete</button>`;
                    html += '</td>';
                    html += '</tr>';
                });
                
                html += '</tbody></table>';
                html += `<p style="margin-top: 15px; color: #666; font-size: 14px;">Showing ${filteredData.length} engagement(s)</p>`;
                tableContainer.innerHTML = html;
            } else {
                tableContainer.innerHTML = '<p style="color: #666;">No engagements found. Submit engagements using the form above.</p>';
            }
        } catch (error) {
            console.error('Error loading engagements:', error);
            const tableContainer = document.getElementById('allEngagementsTable');
            if (tableContainer) tableContainer.innerHTML = '<p style="color: #f44336;">Error loading engagements data.</p>';
        }
    };
    
    window.exportEngagementsCSV = async function() {
        try {
            const response = await fetch('/api/admin/engagements/export/csv');
            if (response.ok) {
                const blob = await response.blob();
                downloadBlob(blob, `engagements_${new Date().toISOString().split('T')[0]}.csv`);
            } else {
                alert('Failed to export engagements');
            }
        } catch (error) {
            console.error('Error exporting engagements:', error);
            alert('Error exporting engagements');
        }
    };
    
    // Employment History Management Functions
    window.showAddEmploymentHistoryForm = function() {
        loadEmployeeHistorySelector();
        document.getElementById('addEmploymentHistoryForm').style.display = 'block';
    };
    
    window.hideAddEmploymentHistoryForm = function() {
        document.getElementById('addEmploymentHistoryForm').style.display = 'none';
        document.getElementById('newEmploymentHistoryForm').reset();
        document.getElementById('addEmploymentHistoryMessage').style.display = 'none';
    };
    
    // Load employees into the employment history employee selector
    async function loadEmployeeHistorySelector() {
        try {
            const response = await fetch('/api/employees');
            const data = await response.json();
            
            const selectors = [
                document.getElementById('empHistoryEmployeeSelect'),
                document.getElementById('editEmpHistoryEmployeeSelect'),
                document.getElementById('empHistoryEmployeeQuickSelect')
            ];
            
            if (data.success && data.data && data.data.length > 0) {
                // Store employees data for pre-fill functionality
                window.employeeHistoryData = data.data;
                
                selectors.forEach(selector => {
                    if (!selector) return;
                    // Different default text for the quick select
                    if (selector.id === 'empHistoryEmployeeQuickSelect') {
                        selector.innerHTML = '<option value="">All Employees</option>';
                    } else {
                        selector.innerHTML = '<option value="">Select Employee</option>';
                    }
                    data.data.forEach(emp => {
                        const option = document.createElement('option');
                        option.value = emp.email;
                        option.textContent = `${emp.full_name || emp.email} - ${emp.department || 'N/A'}`;
                        selector.appendChild(option);
                    });
                });
            }
        } catch (error) {
            console.error('Error loading employees for employment history:', error);
        }
    }
    
    // Pre-fill employment history form when an employee is selected
    const empHistoryEmployeeSelect = document.getElementById('empHistoryEmployeeSelect');
    if (empHistoryEmployeeSelect) {
        empHistoryEmployeeSelect.addEventListener('change', async function() {
            const selectedEmail = this.value;
            if (!selectedEmail) {
                // Clear pre-filled fields when no employee is selected
                document.getElementById('empHistoryDepartment').value = '';
                document.getElementById('empHistoryPosition').value = '';
                document.getElementById('empHistoryJobTitle').value = '';
                return;
            }
            
            // Find the employee in the cached data
            const employee = (window.employeeHistoryData || []).find(emp => emp.email === selectedEmail);
            if (employee) {
                // Pre-fill fields with employee's current data
                const departmentField = document.getElementById('empHistoryDepartment');
                const positionField = document.getElementById('empHistoryPosition');
                const jobTitleField = document.getElementById('empHistoryJobTitle');
                
                if (departmentField && employee.department) {
                    departmentField.value = employee.department;
                }
                if (positionField && employee.position) {
                    positionField.value = employee.position;
                }
                if (jobTitleField && employee.position) {
                    jobTitleField.value = employee.position; // Often same as position
                }
            }
        });
    }
    
    // Add event listener for quick employee selection in employment history
    if (document.getElementById('empHistoryEmployeeQuickSelect')) {
        document.getElementById('empHistoryEmployeeQuickSelect').addEventListener('change', function(e) {
            const selectedEmail = this.value;
            
            // Update the text filter to match the selected employee
            const employeeFilterInput = document.getElementById('empHistoryEmployeeFilter');
            if (employeeFilterInput) {
                employeeFilterInput.value = selectedEmail;
            }
            
            // Reload the table with the filter applied
            loadEmployeeHistory();
        });
    }
    
    async function loadEmployeeHistory() {
        try {
            const response = await fetch('/api/admin/employee-history');
            const data = await response.json();
            
            const tableContainer = document.getElementById('employeeHistoryTable');
            if (!tableContainer) return;
            
            if (data.success && data.data && data.data.length > 0) {
                // Apply filters
                const employeeFilter = document.getElementById('empHistoryEmployeeFilter')?.value.toLowerCase() || '';
                const companyFilter = document.getElementById('empHistoryCompanyFilter')?.value.toLowerCase() || '';
                const yearFilter = document.getElementById('empHistoryYearFilter')?.value || '';
                
                let filteredData = data.data;
                
                if (employeeFilter) {
                    filteredData = filteredData.filter(r => 
                        ((r.employee_name || '').toLowerCase().includes(employeeFilter)) ||
                        ((r.employee_email || '').toLowerCase().includes(employeeFilter))
                    );
                }
                
                if (companyFilter) {
                    filteredData = filteredData.filter(r => 
                        ((r.company || '').toLowerCase().includes(companyFilter))
                    );
                }
                
                if (yearFilter) {
                    filteredData = filteredData.filter(r => {
                        const startDate = r.start_date || '';
                        const endDate = r.end_date || '';
                        return startDate.startsWith(yearFilter) || endDate.startsWith(yearFilter);
                    });
                }
                
                if (filteredData.length === 0) {
                    tableContainer.innerHTML = '<p style="color: #666;">No employment history records found matching the filters.</p>';
                    return;
                }
                
                let html = '<table style="width: 100%; border-collapse: collapse; margin-top: 10px;"><thead><tr style="background: #667eea; color: white;">';
                html += '<th style="padding: 10px;">Employee</th>';
                html += '<th style="padding: 10px;">Company</th>';
                html += '<th style="padding: 10px;">Job Title</th>';
                html += '<th style="padding: 10px;">Position</th>';
                html += '<th style="padding: 10px;">Department</th>';
                html += '<th style="padding: 10px;">Status</th>';
                html += '<th style="padding: 10px;">Functional Group</th>';
                html += '<th style="padding: 10px;">Type</th>';
                html += '<th style="padding: 10px;">Work Status</th>';
                html += '<th style="padding: 10px;">Payroll Status</th>';
                html += '<th style="padding: 10px;">Period</th>';
                html += '<th style="padding: 10px;">Notes</th>';
                html += '<th style="padding: 10px;">Actions</th>';
                html += '</tr></thead><tbody>';
                
                filteredData.forEach(record => {
                    html += '<tr style="border-bottom: 1px solid #eee;">';
                    // Show employee name first, fall back to email if name not available
                    html += `<td style="padding: 10px;">${record.employee_name || record.employees?.full_name || record.employee_email || '-'}</td>`;
                    // Company: show 'Internal' badge if empty, otherwise show company name
                    const companyDisplay = record.company ? `<strong>${record.company}</strong>` : '<span style="background: #4caf5020; padding: 4px 8px; border-radius: 4px; color: #4caf50; font-size: 12px;">Internal</span>';
                    html += `<td style="padding: 10px;">${companyDisplay}</td>`;
                    html += `<td style="padding: 10px;">${record.job_title || '-'}</td>`;
                    html += `<td style="padding: 10px;">${record.position || '-'}</td>`;
                    html += `<td style="padding: 10px;">${record.department || '-'}</td>`;
                    // Status with color coding
                    const status = record.status || '-';
                    let statusColor = '#667eea';
                    if (status.toLowerCase() === 'active') statusColor = '#4caf50';
                    else if (status.toLowerCase() === 'inactive') statusColor = '#ff9800';
                    else if (status.toLowerCase() === 'resigned' || status.toLowerCase() === 'terminated') statusColor = '#f44336';
                    html += `<td style="padding: 10px;"><span style="background: ${statusColor}20; padding: 4px 8px; border-radius: 4px; color: ${statusColor}; font-size: 12px;">${status}</span></td>`;
                    html += `<td style="padding: 10px;">${record.functional_group || '-'}</td>`;
                    html += `<td style="padding: 10px;"><span style="background: #667eea20; padding: 4px 8px; border-radius: 4px; color: #667eea; font-size: 12px;">${record.employment_type || '-'}</span></td>`;
                    html += `<td style="padding: 10px;">${record.work_status || '-'}</td>`;
                    html += `<td style="padding: 10px;">${record.payroll_status || '-'}</td>`;
                    
                    const startDate = record.start_date || '-';
                    const endDate = record.end_date || 'Present';
                    html += `<td style="padding: 10px;"><small>${startDate} to ${endDate}</small></td>`;
                    html += `<td style="padding: 10px;"><small>${record.notes || '-'}</small></td>`;
                    
                    html += '<td style="padding: 10px;">';
                    html += `<button class="btn-secondary btn-sm" onclick="editEmployeeHistory('${record.id}')" style="margin-right: 5px;">✏️ Edit</button>`;
                    html += `<button class="btn-reject btn-sm" onclick="deleteEmployeeHistory('${record.id}')">🗑️ Delete</button>`;
                    html += '</td>';
                    html += '</tr>';
                });
                
                html += '</tbody></table>';
                html += `<p style="margin-top: 15px; color: #666; font-size: 14px;">Showing ${filteredData.length} employment history record(s)</p>`;
                tableContainer.innerHTML = html;
            } else {
                tableContainer.innerHTML = '<p style="color: #666;">No employment history records found. Add employment history using the "Add Employment History" button above.</p>';
            }
        } catch (error) {
            console.error('Error loading employee history:', error);
            const tableContainer = document.getElementById('employeeHistoryTable');
            if (tableContainer) tableContainer.innerHTML = '<p style="color: #f44336;">Error loading employment history data.</p>';
        }
    }
    
    // Handle new employment history form submission
    const newEmploymentHistoryForm = document.getElementById('newEmploymentHistoryForm');
    if (newEmploymentHistoryForm) {
        newEmploymentHistoryForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(newEmploymentHistoryForm);
            const data = {};
            
            for (let [key, value] of formData.entries()) {
                if (value) data[key] = value; // Only include non-empty values
            }
            
            try {
                const response = await fetch('/api/admin/employee-history', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                const messageDiv = document.getElementById('addEmploymentHistoryMessage');
                messageDiv.style.display = 'block';
                
                if (result.success) {
                    messageDiv.className = 'success-message';
                    messageDiv.textContent = '✅ Employment history recorded successfully!';
                    
                    setTimeout(() => {
                        hideAddEmploymentHistoryForm();
                        loadEmployeeHistory();
                    }, 1500);
                } else {
                    messageDiv.className = 'error-message';
                    messageDiv.textContent = result.message || 'Failed to record employment history';
                }
            } catch (error) {
                console.error('Error recording employment history:', error);
                const messageDiv = document.getElementById('addEmploymentHistoryMessage');
                messageDiv.style.display = 'block';
                messageDiv.className = 'error-message';
                messageDiv.textContent = 'Error recording employment history';
            }
        });
    }
    
    window.exportEmployeeHistoryCSV = async function() {
        try {
            const response = await fetch('/api/admin/employee-history/export/csv');
            if (response.ok) {
                const blob = await response.blob();
                downloadBlob(blob, `employee_history_${new Date().toISOString().split('T')[0]}.csv`);
            } else {
                alert('Failed to export employee history');
            }
        } catch (error) {
            console.error('Error exporting employee history:', error);
            alert('Error exporting employee history');
        }
    };
    
    window.closeEditEmployeeModal = function() {
        document.getElementById('editEmployeeModal').style.display = 'none';
        document.getElementById('editEmployeeMessage').style.display = 'none';
    };
    
    // Handle edit employee form submission
    const editEmployeeForm = document.getElementById('editEmployeeForm');
    if (editEmployeeForm) {
        editEmployeeForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const employeeId = document.getElementById('editEmpId').value;
            const formData = new FormData(editEmployeeForm);
            const data = {};
            
            // Convert FormData to object
            for (let [key, value] of formData.entries()) {
                if (key !== 'employee_id_display') { // Skip the display-only field
                    data[key] = value;
                }
            }
            
            try {
                const response = await fetch(`/api/admin/employees/${employeeId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                const messageDiv = document.getElementById('editEmployeeMessage');
                messageDiv.style.display = 'block';
                
                if (result.success) {
                    messageDiv.className = 'success-message';
                    messageDiv.textContent = 'Employee updated successfully!';
                    
                    // Upload files if employee was updated successfully
                    if (employeeId) {
                        // Upload profile picture if selected
                        const profilePicInput = document.getElementById('editEmpProfilePic');
                        if (profilePicInput && profilePicInput.files.length > 0) {
                            await uploadEmployeeFile(employeeId, profilePicInput.files[0], 'profile-picture');
                        }
                        
                        // Upload resume if selected
                        const resumeInput = document.getElementById('editEmpResume');
                        if (resumeInput && resumeInput.files.length > 0) {
                            await uploadEmployeeFile(employeeId, resumeInput.files[0], 'resume');
                        }
                    }
                    
                    // Refresh the employee list
                    setTimeout(() => {
                        closeEditEmployeeModal();
                        loadEmployeeList();
                    }, 1500);
                } else {
                    messageDiv.className = 'error-message';
                    messageDiv.textContent = result.message || 'Failed to update employee';
                }
            } catch (error) {
                console.error('Error updating employee:', error);
                const messageDiv = document.getElementById('editEmployeeMessage');
                messageDiv.style.display = 'block';
                messageDiv.className = 'error-message';
                messageDiv.textContent = 'Error updating employee';
            }
        });
    }
    
    // Variable Percentage Management Functions
    // Old variable percentage functions removed - replaced with EPF/SOCSO/EIS configuration
    
    async function loadVariablePercentageRules() {
        // This function now loads EPF/SOCSO/EIS configuration instead of bonus rules
        // Load the default or active configuration from the server
        try {
            const configName = document.getElementById('varConfigName')?.value || 'default';
            const response = await fetch(`/api/admin/variable-config/${configName}`);
            
            // Check if endpoint exists
            if (response.status === 404) {
                console.log('⚠️ Variable config API endpoint not yet implemented, using default values');
                return;
            }
            
            const data = await response.json();
            
            if (data.success && data.config) {
                const config = data.config;
                
                // Load EPF Part A values with null checks
                const epfPartAEmployee = document.getElementById('epfPartAEmployee');
                const epfPartAEmployer = document.getElementById('epfPartAEmployer');
                const epfPartAEmployeeOver20k = document.getElementById('epfPartAEmployeeOver20k');
                const epfPartAEmployerOver20k = document.getElementById('epfPartAEmployerOver20k');
                const epfPartAEmployerBonus = document.getElementById('epfPartAEmployerBonus');
                
                if (epfPartAEmployee) epfPartAEmployee.value = config.epf_part_a_employee || 11.0;
                if (epfPartAEmployer) epfPartAEmployer.value = config.epf_part_a_employer || 12.0;
                if (epfPartAEmployeeOver20k) epfPartAEmployeeOver20k.value = config.epf_part_a_employee_over20k || 11.0;
                if (epfPartAEmployerOver20k) epfPartAEmployerOver20k.value = config.epf_part_a_employer_over20k || 12.0;
                if (epfPartAEmployerBonus) epfPartAEmployerBonus.value = config.epf_part_a_employer_bonus || 13.0;
                
                // Load EPF Part B values with null checks
                const epfPartBEmployee = document.getElementById('epfPartBEmployee');
                const epfPartBEmployer = document.getElementById('epfPartBEmployer');
                const epfPartBEmployeeOver20k = document.getElementById('epfPartBEmployeeOver20k');
                const epfPartBEmployerOver20k = document.getElementById('epfPartBEmployerOver20k');
                
                if (epfPartBEmployee) epfPartBEmployee.value = config.epf_part_b_employee || 0.0;
                if (epfPartBEmployer) epfPartBEmployer.value = config.epf_part_b_employer || 13.0;
                if (epfPartBEmployeeOver20k) epfPartBEmployeeOver20k.value = config.epf_part_b_employee_over20k || 0.0;
                if (epfPartBEmployerOver20k) epfPartBEmployerOver20k.value = config.epf_part_b_employer_over20k || 13.0;
                
                // Load EPF Part C values with null checks
                const epfPartCEmployee = document.getElementById('epfPartCEmployee');
                const epfPartCEmployerFixed = document.getElementById('epfPartCEmployerFixed');
                const epfPartCEmployeeOver20k = document.getElementById('epfPartCEmployeeOver20k');
                const epfPartCEmployerOver20k = document.getElementById('epfPartCEmployerOver20k');
                const epfPartCEmployerBonus = document.getElementById('epfPartCEmployerBonus');
                
                if (epfPartCEmployee) epfPartCEmployee.value = config.epf_part_c_employee || 0.0;
                if (epfPartCEmployerFixed) epfPartCEmployerFixed.value = config.epf_part_c_employer_fixed || 5.0;
                if (epfPartCEmployeeOver20k) epfPartCEmployeeOver20k.value = config.epf_part_c_employee_over20k || 0.0;
                if (epfPartCEmployerOver20k) epfPartCEmployerOver20k.value = config.epf_part_c_employer_over20k || 6.0;
                if (epfPartCEmployerBonus) epfPartCEmployerBonus.value = config.epf_part_c_employer_bonus || 6.5;
                
                // Load EPF Part D values with null checks
                const epfPartDEmployee = document.getElementById('epfPartDEmployee');
                const epfPartDEmployer = document.getElementById('epfPartDEmployer');
                const epfPartDEmployeeOver20k = document.getElementById('epfPartDEmployeeOver20k');
                const epfPartDEmployerOver20kFixed = document.getElementById('epfPartDEmployerOver20kFixed');
                
                if (epfPartDEmployee) epfPartDEmployee.value = config.epf_part_d_employee || 0.0;
                if (epfPartDEmployer) epfPartDEmployer.value = config.epf_part_d_employer || 4.0;
                if (epfPartDEmployeeOver20k) epfPartDEmployeeOver20k.value = config.epf_part_d_employee_over20k || 0.0;
                if (epfPartDEmployerOver20kFixed) epfPartDEmployerOver20kFixed.value = config.epf_part_d_employer_over20k_fixed || 5.0;
                
                // Load EPF Part E values with null checks
                const epfPartEEmployee = document.getElementById('epfPartEEmployee');
                const epfPartEEmployer = document.getElementById('epfPartEEmployer');
                const epfPartEEmployeeOver20k = document.getElementById('epfPartEEmployeeOver20k');
                const epfPartEEmployerOver20kFixed = document.getElementById('epfPartEEmployerOver20kFixed');
                
                if (epfPartEEmployee) epfPartEEmployee.value = config.epf_part_e_employee || 0.0;
                if (epfPartEEmployer) epfPartEEmployer.value = config.epf_part_e_employer || 4.0;
                if (epfPartEEmployeeOver20k) epfPartEEmployeeOver20k.value = config.epf_part_e_employee_over20k || 0.0;
                if (epfPartEEmployerOver20kFixed) epfPartEEmployerOver20kFixed.value = config.epf_part_e_employer_over20k_fixed || 5.0;
                
                // Load SOCSO values with null checks
                const socsoFirstEmployee = document.getElementById('socsoFirstEmployee');
                const socsoFirstEmployer = document.getElementById('socsoFirstEmployer');
                const socsoSecondEmployee = document.getElementById('socsoSecondEmployee');
                const socsoSecondEmployer = document.getElementById('socsoSecondEmployer');
                
                if (socsoFirstEmployee) socsoFirstEmployee.value = config.socso_first_employee || 0.5;
                if (socsoFirstEmployer) socsoFirstEmployer.value = config.socso_first_employer || 1.75;
                if (socsoSecondEmployee) socsoSecondEmployee.value = config.socso_second_employee || 0.0;
                if (socsoSecondEmployer) socsoSecondEmployer.value = config.socso_second_employer || 1.25;
                
                // Load EIS values with null checks
                const eisEmployee = document.getElementById('eisEmployee');
                const eisEmployer = document.getElementById('eisEmployer');
                
                if (eisEmployee) eisEmployee.value = config.eis_employee || 0.2;
                if (eisEmployer) eisEmployer.value = config.eis_employer || 0.2;
                
                console.log('✅ Loaded variable percentage configuration:', configName);
            } else {
                console.log('⚠️ No configuration found, using defaults');
                // Load default values (already set in HTML)
            }
        } catch (error) {
            console.error('Error loading variable percentage configuration:', error);
            console.log('⚠️ Using default values from HTML');
        }
    }
    
    // Save variable percentage configuration
    window.saveVariableConfig = async function() {
        try {
            const configName = document.getElementById('varConfigName')?.value || 'default';
            
            // Helper function to safely get and parse float values
            const safeParseFloat = (elementId, defaultValue) => {
                const element = document.getElementById(elementId);
                if (!element || !element.value) return defaultValue;
                const value = parseFloat(element.value);
                return isNaN(value) ? defaultValue : value;
            };
            
            const config = {
                config_name: configName,
                // EPF Part A
                epf_part_a_employee: safeParseFloat('epfPartAEmployee', 11.0),
                epf_part_a_employer: safeParseFloat('epfPartAEmployer', 12.0),
                epf_part_a_employee_over20k: safeParseFloat('epfPartAEmployeeOver20k', 11.0),
                epf_part_a_employer_over20k: safeParseFloat('epfPartAEmployerOver20k', 12.0),
                epf_part_a_employer_bonus: safeParseFloat('epfPartAEmployerBonus', 13.0),
                // EPF Part B
                epf_part_b_employee: safeParseFloat('epfPartBEmployee', 0.0),
                epf_part_b_employer: safeParseFloat('epfPartBEmployer', 13.0),
                epf_part_b_employee_over20k: safeParseFloat('epfPartBEmployeeOver20k', 0.0),
                epf_part_b_employer_over20k: safeParseFloat('epfPartBEmployerOver20k', 13.0),
                // EPF Part C
                epf_part_c_employee: safeParseFloat('epfPartCEmployee', 0.0),
                epf_part_c_employer_fixed: safeParseFloat('epfPartCEmployerFixed', 5.0),
                epf_part_c_employee_over20k: safeParseFloat('epfPartCEmployeeOver20k', 0.0),
                epf_part_c_employer_over20k: safeParseFloat('epfPartCEmployerOver20k', 6.0),
                epf_part_c_employer_bonus: safeParseFloat('epfPartCEmployerBonus', 6.5),
                // EPF Part D
                epf_part_d_employee: safeParseFloat('epfPartDEmployee', 0.0),
                epf_part_d_employer: safeParseFloat('epfPartDEmployer', 4.0),
                epf_part_d_employee_over20k: safeParseFloat('epfPartDEmployeeOver20k', 0.0),
                epf_part_d_employer_over20k_fixed: safeParseFloat('epfPartDEmployerOver20kFixed', 5.0),
                // EPF Part E
                epf_part_e_employee: safeParseFloat('epfPartEEmployee', 0.0),
                epf_part_e_employer: safeParseFloat('epfPartEEmployer', 4.0),
                epf_part_e_employee_over20k: safeParseFloat('epfPartEEmployeeOver20k', 0.0),
                epf_part_e_employer_over20k_fixed: safeParseFloat('epfPartEEmployerOver20kFixed', 5.0),
                // SOCSO
                socso_first_employee: safeParseFloat('socsoFirstEmployee', 0.5),
                socso_first_employer: safeParseFloat('socsoFirstEmployer', 1.75),
                socso_second_employee: safeParseFloat('socsoSecondEmployee', 0.0),
                socso_second_employer: safeParseFloat('socsoSecondEmployer', 1.25),
                // EIS
                eis_employee: safeParseFloat('eisEmployee', 0.2),
                eis_employer: safeParseFloat('eisEmployer', 0.2)
            };
            
            const response = await fetch('/api/admin/variable-config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(config)
            });
            
            // Check if endpoint exists
            if (response.status === 404) {
                alert('⚠️ Save functionality requires backend API implementation.\n\nConfiguration changes are currently stored locally in the browser only.\n\nAPI endpoint needed: POST /api/admin/variable-config');
                console.warn('Variable config save API endpoint not yet implemented');
                return;
            }
            
            const result = await response.json();
            
            if (result.success) {
                alert(`✅ Configuration "${configName}" saved successfully!`);
                const displayElement = document.getElementById('configNameDisplay');
                if (displayElement) displayElement.textContent = configName;
            } else {
                alert(`❌ Failed to save configuration: ${result.message || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error saving variable configuration:', error);
            alert('❌ Error saving configuration');
        }
    };
    
    // Load variable percentage configuration
    window.loadVariableConfig = async function() {
        const configName = prompt('Enter configuration name to load:', 'default');
        if (configName) {
            document.getElementById('varConfigName').value = configName;
            document.getElementById('configNameDisplay').textContent = configName;
            await loadVariablePercentageRules();
        }
    };
    
    // Update config name display when typing
    const varConfigNameInput = document.getElementById('varConfigName');
    if (varConfigNameInput) {
        varConfigNameInput.addEventListener('input', function() {
            document.getElementById('configNameDisplay').textContent = this.value || 'default';
        });
    }

    
    // Skipped Payroll Management Functions
    window.loadSkippedPayroll = async function() {
        try {
            const response = await fetch('/api/admin/skipped-payroll');
            const data = await response.json();
            
            const tableContainer = document.getElementById('skippedPayrollTable');
            if (!tableContainer) return;
            
            if (data.success && data.data && data.data.length > 0) {
                // Apply filters
                const monthFilter = document.getElementById('skippedMonthFilter')?.value || '';
                const employeeFilter = document.getElementById('skippedEmployeeFilter')?.value.toLowerCase() || '';
                const reasonFilter = document.getElementById('skippedReasonFilter')?.value || '';
                
                let filteredData = data.data;
                
                if (monthFilter) {
                    const [year, month] = monthFilter.split('-');
                    const filterMonthYear = `${month}/${year}`;
                    filteredData = filteredData.filter(r => r.month_year === filterMonthYear);
                }
                
                if (employeeFilter) {
                    filteredData = filteredData.filter(r => 
                        (r.employee_name || '').toLowerCase().includes(employeeFilter)
                    );
                }
                
                if (reasonFilter) {
                    filteredData = filteredData.filter(r => r.reason === reasonFilter);
                }
                
                if (filteredData.length === 0) {
                    tableContainer.innerHTML = '<p style="color: #666;">No skipped payroll records found matching the filters.</p>';
                    return;
                }
                
                let html = '<table style="width: 100%; border-collapse: collapse; margin-top: 10px;"><thead><tr style="background: #667eea; color: white;">';
                html += '<th style="padding: 10px;">Employee</th>';
                html += '<th style="padding: 10px;">Email</th>';
                html += '<th style="padding: 10px;">Period</th>';
                html += '<th style="padding: 10px;">Reason</th>';
                html += '<th style="padding: 10px;">Skipped Date</th>';
                html += '<th style="padding: 10px;">Notes</th>';
                html += '<th style="padding: 10px;">Actions</th>';
                html += '</tr></thead><tbody>';
                
                filteredData.forEach(record => {
                    html += '<tr style="border-bottom: 1px solid #eee;">';
                    html += `<td style="padding: 10px;">${record.employee_name || '-'}</td>`;
                    html += `<td style="padding: 10px;">${record.employee_email || '-'}</td>`;
                    html += `<td style="padding: 10px;">${record.month_year || '-'}</td>`;
                    html += `<td style="padding: 10px;"><span style="background: #ffebee; padding: 4px 8px; border-radius: 4px; color: #c62828; font-size: 12px;">${record.reason || 'Not specified'}</span></td>`;
                    html += `<td style="padding: 10px;">${record.skipped_date ? new Date(record.skipped_date).toLocaleDateString() : '-'}</td>`;
                    html += `<td style="padding: 10px;"><small>${record.notes || '-'}</small></td>`;
                    html += `<td style="padding: 10px;">`;
                    if (record.can_include) {
                        html += `<button class="btn-primary btn-sm" onclick="includeInNextPayroll('${record.id}')">Include in Next Run</button>`;
                    } else {
                        html += `<span style="color: #666; font-size: 12px;">Already included</span>`;
                    }
                    html += `</td>`;
                    html += '</tr>';
                });
                
                html += '</tbody></table>';
                html += `<p style="margin-top: 15px; color: #666; font-size: 14px;">Showing ${filteredData.length} skipped record(s)</p>`;
                tableContainer.innerHTML = html;
            } else {
                tableContainer.innerHTML = '<p style="color: #666;">No skipped payroll records found. Employees who are skipped during payroll runs will appear here.</p>';
            }
        } catch (error) {
            console.error('Error loading skipped payroll:', error);
            const tableContainer = document.getElementById('skippedPayrollTable');
            if (tableContainer) tableContainer.innerHTML = '<p style="color: #f44336;">Error loading skipped payroll data.</p>';
        }
    };
    
    window.exportSkippedPayrollCSV = async function() {
        try {
            const response = await fetch('/api/admin/skipped-payroll/export/csv');
            if (response.ok) {
                const blob = await response.blob();
                downloadBlob(blob, `skipped_payroll_${new Date().toISOString().split('T')[0]}.csv`);
            } else {
                alert('Failed to export skipped payroll');
            }
        } catch (error) {
            console.error('Error exporting skipped payroll:', error);
            alert('Error exporting skipped payroll');
        }
    };
    
    // Load employees into various form dropdowns
    async function loadFormEmployeeSelectors() {
        try {
            const response = await fetch('/api/employees');
            const data = await response.json();
            
            if (data.success && data.data && data.data.length > 0) {
                // Admin Leave Request form
                const leaveSelector = document.getElementById('adminLeaveEmployeeId');
                if (leaveSelector) {
                    leaveSelector.innerHTML = '<option value="">Select Employee</option>';
                    data.data.forEach(emp => {
                        const option = document.createElement('option');
                        option.value = emp.email; // Use email as value instead of employee_id
                        option.textContent = `${emp.full_name || emp.email} - ${emp.department || 'N/A'}`;
                        leaveSelector.appendChild(option);
                    });
                }
                
                // Variable Percentage form
                const varPctSelector = document.getElementById('varPctEmployee');
                if (varPctSelector) {
                    varPctSelector.innerHTML = '<option value="">Select Employee</option>';
                    data.data.forEach(emp => {
                        const option = document.createElement('option');
                        option.value = emp.email;
                        option.textContent = `${emp.full_name || emp.email} - ${emp.department || 'N/A'}`;
                        varPctSelector.appendChild(option);
                    });
                }
                
                // Salary Change form
                const salaryChangeSelector = document.getElementById('salaryChangeEmployee');
                if (salaryChangeSelector) {
                    salaryChangeSelector.innerHTML = '<option value="">Select Employee</option>';
                    data.data.forEach(emp => {
                        const option = document.createElement('option');
                        option.value = emp.email;
                        option.textContent = `${emp.full_name || emp.email} - ${emp.department || 'N/A'}`;
                        salaryChangeSelector.appendChild(option);
                    });
                }
            }
        } catch (error) {
            console.error('Error loading employees for form selectors:', error);
        }
    }
    
    // Load employees when page loads
    if (document.getElementById('adminLeaveEmployeeId') || 
        document.getElementById('varPctEmployee') || 
        document.getElementById('salaryChangeEmployee')) {
        loadFormEmployeeSelectors();
    }
    
    // Admin Leave Request Form Handler
    const adminLeaveRequestForm = document.getElementById('adminLeaveRequestForm');
    if (adminLeaveRequestForm) {
        adminLeaveRequestForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(adminLeaveRequestForm);
            const employeeEmail = formData.get('employee_id'); // Now contains email directly from dropdown
            
            try {
                // Build leave request data
                const isHalfDay = formData.get('is_half_day') === 'on';
                const leaveData = {
                    employee_email: employeeEmail,
                    leave_type: formData.get('leave_type'),
                    start_date: formData.get('start_date'),
                    end_date: formData.get('end_date'),
                    title: formData.get('title') || 'Admin submitted leave',
                    is_half_day: isHalfDay,
                    half_day_period: isHalfDay ? formData.get('half_day_period') : null
                };
                
                // Submit leave request
                const response = await fetch('/api/leave-requests/submit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(leaveData)
                });
                
                const result = await response.json();
                const messageDiv = document.getElementById('adminLeaveFormMessage');
                messageDiv.style.display = 'block';
                
                if (result.success) {
                    messageDiv.className = 'success-message';
                    messageDiv.textContent = '✅ Leave request submitted successfully!';
                    adminLeaveRequestForm.reset();
                    
                    // Reload leave requests
                    setTimeout(() => {
                        messageDiv.style.display = 'none';
                        loadLeaveRequests();
                        loadApprovedRejectedLeaveRequests();
                    }, 2000);
                } else {
                    messageDiv.className = 'error-message';
                    messageDiv.textContent = result.message || 'Failed to submit leave request';
                }
            } catch (error) {
                console.error('Error submitting admin leave request:', error);
                const messageDiv = document.getElementById('adminLeaveFormMessage');
                messageDiv.style.display = 'block';
                messageDiv.className = 'error-message';
                messageDiv.textContent = 'Error submitting leave request: ' + error.message;
            }
        });
        
        // Handle leave balance loading when employee is selected
        const employeeSelect = document.getElementById('adminLeaveEmployeeId');
        const refreshBalanceBtn = document.getElementById('adminRefreshBalance');
        
        async function loadEmployeeLeaveBalance() {
            const employeeEmail = employeeSelect.value;
            if (!employeeEmail) {
                document.getElementById('adminAnnualBalance').textContent = 'Select an employee to view balance';
                document.getElementById('adminSickBalance').textContent = 'Select an employee to view balance';
                return;
            }
            
            try {
                const response = await fetch(`/api/leave-balance/${encodeURIComponent(employeeEmail)}`);
                const data = await response.json();
                
                if (data.success) {
                    const annualBalance = data.balances.annual || 0;
                    const sickBalance = data.balances.sick || 0;
                    document.getElementById('adminAnnualBalance').textContent = `${annualBalance} days remaining`;
                    document.getElementById('adminSickBalance').textContent = `${sickBalance} days remaining`;
                } else {
                    document.getElementById('adminAnnualBalance').textContent = 'Error loading balance';
                    document.getElementById('adminSickBalance').textContent = 'Error loading balance';
                }
            } catch (error) {
                console.error('Error loading leave balance:', error);
                document.getElementById('adminAnnualBalance').textContent = 'Error loading balance';
                document.getElementById('adminSickBalance').textContent = 'Error loading balance';
            }
        }
        
        if (employeeSelect) {
            employeeSelect.addEventListener('change', loadEmployeeLeaveBalance);
        }
        
        if (refreshBalanceBtn) {
            refreshBalanceBtn.addEventListener('click', loadEmployeeLeaveBalance);
        }
        
        // Handle sick leave type selection to show info
        const leaveTypeSelect = document.getElementById('adminLeaveType');
        const sickLeaveInfo = document.getElementById('adminSickLeaveInfo');
        
        if (leaveTypeSelect && sickLeaveInfo) {
            leaveTypeSelect.addEventListener('change', function() {
                const selectedType = this.value.toLowerCase();
                if (selectedType === 'sick' || selectedType === 'hospitalization') {
                    sickLeaveInfo.style.display = 'block';
                } else {
                    sickLeaveInfo.style.display = 'none';
                }
            });
        }
        
        // Handle half-day period visibility and duration input
        const halfDayCheckbox = document.getElementById('adminLeaveHalfDay');
        const halfDayPeriod = document.getElementById('adminHalfDayPeriod');
        const durationInput = document.getElementById('adminLeaveDuration');
        const endDateInput = document.getElementById('adminLeaveEndDate');
        
        if (halfDayCheckbox && halfDayPeriod && durationInput) {
            halfDayCheckbox.addEventListener('change', function() {
                if (this.checked) {
                    // Half-day selected: enable 0.5 step for fractional days (e.g., 0.5, 1.5, 2.5)
                    durationInput.min = 0.5;
                    durationInput.step = 0.5;
                    // If current value is whole number, keep it; otherwise allow fractional
                    updateWorkingDaysDisplay();
                } else {
                    // Full day selected: only allow whole days
                    durationInput.min = 1;
                    durationInput.step = 1;
                    // Round up to nearest whole day if currently fractional
                    const currentVal = parseFloat(durationInput.value);
                    if (currentVal % 1 !== 0) {
                        durationInput.value = Math.ceil(currentVal);
                    }
                    if (parseFloat(durationInput.value) < 1) {
                        durationInput.value = 1;
                    }
                    updateWorkingDaysDisplay();
                }
            });
        }
        
        // Handle document upload
        const uploadBtn = document.getElementById('adminUploadDocument');
        const removeBtn = document.getElementById('adminRemoveDocument');
        const fileInput = document.getElementById('adminDocumentInput');
        const docName = document.getElementById('adminDocumentName');
        
        if (uploadBtn && fileInput) {
            uploadBtn.addEventListener('click', function() {
                fileInput.click();
            });
            
            fileInput.addEventListener('change', function() {
                if (this.files && this.files[0]) {
                    docName.textContent = this.files[0].name;
                    removeBtn.style.display = 'inline-block';
                }
            });
        }
        
        if (removeBtn && fileInput) {
            removeBtn.addEventListener('click', function() {
                fileInput.value = '';
                docName.textContent = '';
                this.style.display = 'none';
            });
        }
        
        // Calculate working days between dates
        function calculateWorkingDays(startDate, endDate, excludeWeekends = true) {
            if (!startDate || !endDate) return 0;
            
            const start = new Date(startDate);
            const end = new Date(endDate);
            
            if (end < start) return 0;
            
            let days = 0;
            const current = new Date(start);
            
            while (current <= end) {
                const dayOfWeek = current.getDay();
                if (!excludeWeekends || (dayOfWeek !== 0 && dayOfWeek !== 6)) {
                    days++;
                }
                current.setDate(current.getDate() + 1);
            }
            
            return days;
        }
        
        // Update working days display with API call for accurate calculation
        async function updateWorkingDaysDisplay() {
            const startDate = document.getElementById('adminLeaveStartDate').value;
            const endDate = document.getElementById('adminLeaveEndDate').value;
            const display = document.getElementById('adminWorkingDaysDisplay');
            const halfDay = document.getElementById('adminLeaveHalfDay');
            const stateSelect = document.getElementById('adminLeaveState');
            const durationInput = document.getElementById('adminLeaveDuration');
            
            if (!startDate || !endDate) {
                display.textContent = 'Working days: - (excludes weekends & holidays)';
                return;
            }
            
            display.style.color = '#555';
            display.textContent = 'Calculating working days...';
            
            // Call API to get accurate working days calculation (includes holidays)
            try {
                const state = stateSelect ? stateSelect.value : '';
                const params = new URLSearchParams({
                    start_date: startDate,
                    end_date: endDate
                });
                if (state && state !== 'All Malaysia') {
                    params.append('state', state);
                }
                
                const response = await fetch(`/api/working-days?${params.toString()}`);
                const data = await response.json();
                
                if (data.success) {
                    // Check if half-day is selected and show duration input value for fractional days
                    const currentDuration = durationInput ? parseFloat(durationInput.value) : data.working_days;
                    const isHalfDayEnabled = halfDay && halfDay.checked;
                    
                    if (isHalfDayEnabled && currentDuration % 1 !== 0) {
                        display.textContent = `Working days: ${currentDuration} (includes half-day, excludes weekends & holidays)`;
                    } else {
                        display.textContent = `Working days: ${data.working_days} (excludes weekends & holidays)`;
                    }
                } else {
                    // Fallback to local calculation
                    const days = calculateWorkingDays(startDate, endDate);
                    display.textContent = `Working days: ${days} (estimate, weekends excluded)`;
                }
            } catch (error) {
                console.error('Error fetching working days:', error);
                // Fallback to local calculation
                const days = calculateWorkingDays(startDate, endDate);
                display.textContent = `Working days: ${days} (estimate, weekends excluded)`;
            }
        }
        
        // Update dates when duration changes
        const durationField = document.getElementById('adminLeaveDuration');
        if (durationField) {
            durationField.addEventListener('change', function() {
                const duration = parseFloat(this.value);
                const startDate = document.getElementById('adminLeaveStartDate');
                const endDate = document.getElementById('adminLeaveEndDate');
                
                if (startDate.value) {
                    const start = new Date(startDate.value);
                    
                    // Handle fractional days (e.g., 0.5, 1.5)
                    if (duration === 0.5 || (duration % 1 === 0.5)) {
                        // For half-day or half-day increments, end date should be same as start
                        // or we calculate the whole days and the last day is half
                        const wholeDays = Math.floor(duration);
                        let workingDaysAdded = 0;
                        const current = new Date(start);
                        
                        // Add whole working days
                        while (workingDaysAdded < wholeDays) {
                            const dayOfWeek = current.getDay();
                            if (dayOfWeek !== 0 && dayOfWeek !== 6) {
                                workingDaysAdded++;
                            }
                            if (workingDaysAdded < wholeDays) {
                                current.setDate(current.getDate() + 1);
                            }
                        }
                        
                        endDate.value = current.toISOString().split('T')[0];
                    } else {
                        // For whole days, calculate normally
                        let workingDaysAdded = 0;
                        const current = new Date(start);
                        const targetDays = Math.round(duration);
                        
                        while (workingDaysAdded < targetDays) {
                            const dayOfWeek = current.getDay();
                            if (dayOfWeek !== 0 && dayOfWeek !== 6) {
                                workingDaysAdded++;
                            }
                            if (workingDaysAdded < targetDays) {
                                current.setDate(current.getDate() + 1);
                            }
                        }
                        
                        endDate.value = current.toISOString().split('T')[0];
                    }
                    
                    updateWorkingDaysDisplay();
                }
            });
        }
        
        // Update working days when dates change
        const startDateField = document.getElementById('adminLeaveStartDate');
        const endDateField = document.getElementById('adminLeaveEndDate');
        const stateField = document.getElementById('adminLeaveState');
        
        if (startDateField) {
            startDateField.addEventListener('change', updateWorkingDaysDisplay);
        }
        
        if (endDateField) {
            endDateField.addEventListener('change', updateWorkingDaysDisplay);
        }
        
        // Also update when state changes (affects holiday calculation)
        if (stateField) {
            stateField.addEventListener('change', updateWorkingDaysDisplay);
        }
        
        // Initialize with current dates
        if (startDateField && endDateField) {
            const today = new Date().toISOString().split('T')[0];
            if (!startDateField.value) startDateField.value = today;
            if (!endDateField.value) endDateField.value = today;
            updateWorkingDaysDisplay();
        }
    }
    
    window.closeEditEmploymentHistoryModal = function() {
        document.getElementById('editEmploymentHistoryModal').style.display = 'none';
        document.getElementById('editEmploymentHistoryForm').reset();
        document.getElementById('editEmploymentHistoryMessage').style.display = 'none';
    };
    
    // Handle edit employment history form submission
    const editEmploymentHistoryForm = document.getElementById('editEmploymentHistoryForm');
    if (editEmploymentHistoryForm) {
        editEmploymentHistoryForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const recordId = document.getElementById('editEmpHistoryRecordId').value;
            const formData = new FormData(editEmploymentHistoryForm);
            const data = {};
            
            for (let [key, value] of formData.entries()) {
                // Convert empty date fields to null so database accepts them
                if (key === 'end_date' && !value) {
                    data[key] = null;
                } else {
                    data[key] = value;
                }
            }
            
            try {
                const response = await fetch(`/api/admin/employee-history/${recordId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                const messageDiv = document.getElementById('editEmploymentHistoryMessage');
                messageDiv.style.display = 'block';
                
                if (result.success) {
                    messageDiv.className = 'success-message';
                    messageDiv.textContent = '✅ Employment history updated successfully!';
                    
                    setTimeout(() => {
                        closeEditEmploymentHistoryModal();
                        loadEmployeeHistory();
                    }, 1500);
                } else {
                    messageDiv.className = 'error-message';
                    messageDiv.textContent = result.message || 'Failed to update employment history';
                }
            } catch (error) {
                console.error('Error updating employee history:', error);
                const messageDiv = document.getElementById('editEmploymentHistoryMessage');
                messageDiv.style.display = 'block';
                messageDiv.className = 'error-message';
                messageDiv.textContent = 'Error updating employment history';
            }
        });
    }
    
    // Export additional functions for onclick handlers
    window.loadSalaryHistory = loadSalaryHistory;
    window.loadEmployeeHistory = loadEmployeeHistory;
    
    // Event listeners for Sick Leave Balance controls
    const sickLeaveEmployeeFilter = document.getElementById('sickLeaveEmployeeFilter');
    if (sickLeaveEmployeeFilter) {
        sickLeaveEmployeeFilter.addEventListener('input', applySickLeaveFilters);
    }
    
    const sickLeaveYearSelector = document.getElementById('sickLeaveYearSelector');
    if (sickLeaveYearSelector) {
        sickLeaveYearSelector.addEventListener('change', loadSickLeaveBalances);
    }
    
    const refreshSickLeaveBtn = document.getElementById('refreshSickLeaveBtn');
    if (refreshSickLeaveBtn) {
        refreshSickLeaveBtn.addEventListener('click', loadSickLeaveBalances);
    }
    
    const employmentActInfoBtn = document.getElementById('employmentActInfoBtn');
    if (employmentActInfoBtn) {
        employmentActInfoBtn.addEventListener('click', showEmploymentActInfo);
    }
    
    // Setup annual leave balance event listeners
    const annualLeaveEmployeeFilter = document.getElementById('annualLeaveEmployeeFilter');
    if (annualLeaveEmployeeFilter) {
        annualLeaveEmployeeFilter.addEventListener('input', applyAnnualLeaveFilters);
    }
    
    const annualLeaveYearSelector = document.getElementById('annualLeaveYearSelector');
    if (annualLeaveYearSelector) {
        annualLeaveYearSelector.addEventListener('change', loadLeaveBalances);
    }
    
    const refreshAnnualLeaveBtn = document.getElementById('refreshAnnualLeaveBtn');
    if (refreshAnnualLeaveBtn) {
        refreshAnnualLeaveBtn.addEventListener('click', loadLeaveBalances);
    }
    
    // Setup carry forward buttons
    const processCarryForwardBtn = document.getElementById('processCarryForwardBtn');
    if (processCarryForwardBtn) {
        processCarryForwardBtn.addEventListener('click', openProcessCarryForwardModal);
    }
    
    const setCarryForwardAllBtn = document.getElementById('setCarryForwardAllBtn');
    if (setCarryForwardAllBtn) {
        setCarryForwardAllBtn.addEventListener('click', openSetCarryForwardAllModal);
    }
    
    // Load all new data on init
    loadLeaveBalances();
    loadSickLeaveBalances();
    loadUnpaidLeaveSummary();
    loadSkippedPayroll();
    loadContributions();
    loadSalaryHistory();
    loadSalaryHistoryEmployeeSelector();
    loadEmployeeHistory();
    loadVariablePercentageRules();
    
    // Setup file upload handlers
    setupFileUploadHandlers();
});

// File upload handling functions (defined globally)
function setupFileUploadHandlers() {
    // Profile picture preview for new employee
    const newProfilePicInput = document.getElementById('newEmpProfilePic');
    if (newProfilePicInput) {
        newProfilePicInput.addEventListener('change', function(e) {
            handleProfilePicChange(e, 'new');
        });
    }
    
    // Resume upload for new employee
    const newResumeInput = document.getElementById('newEmpResume');
    if (newResumeInput) {
        newResumeInput.addEventListener('change', function(e) {
            handleResumeChange(e, 'new');
        });
    }
    
    // Profile picture preview for edit employee
    const editProfilePicInput = document.getElementById('editEmpProfilePic');
    if (editProfilePicInput) {
        editProfilePicInput.addEventListener('change', function(e) {
            handleProfilePicChange(e, 'edit');
        });
    }
    
    // Resume upload for edit employee
    const editResumeInput = document.getElementById('editEmpResume');
    if (editResumeInput) {
        editResumeInput.addEventListener('change', function(e) {
            handleResumeChange(e, 'edit');
        });
    }
}

function handleProfilePicChange(event, formType) {
    const file = event.target.files[0];
    if (file) {
        // Validate file type
        if (!file.type.startsWith('image/')) {
            alert('Please select an image file.');
            event.target.value = '';
            return;
        }
        
        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            alert('Profile picture must be less than 5MB.');
            event.target.value = '';
            return;
        }
        
        // Show preview
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById(`${formType}EmpProfilePicPreview`);
            if (preview) {
                preview.src = e.target.result;
            }
        };
        reader.readAsDataURL(file);
        
        // Update file name display
        const nameDiv = document.getElementById(`${formType}EmpProfilePicName`);
        if (nameDiv) {
            nameDiv.textContent = file.name;
        }
    }
}

function handleResumeChange(event, formType) {
    const file = event.target.files[0];
    if (file) {
        // Validate file type
        const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        if (!allowedTypes.includes(file.type)) {
            alert('Please select a PDF or Word document.');
            event.target.value = '';
            return;
        }
        
        // Validate file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            alert('Resume must be less than 10MB.');
            event.target.value = '';
            return;
        }
        
        // Update file name display
        const nameDiv = document.getElementById(`${formType}EmpResumeName`);
        if (nameDiv) {
            nameDiv.textContent = file.name;
        }
    }
}

function clearProfilePicPreview(formType) {
    const input = document.getElementById(`${formType}EmpProfilePic`);
    const preview = document.getElementById(`${formType}EmpProfilePicPreview`);
    const nameDiv = document.getElementById(`${formType}EmpProfilePicName`);
    
    if (input) input.value = '';
    if (preview) preview.src = '/static/images/default_avatar.svg';
    if (nameDiv) nameDiv.textContent = 'No file selected';
}

function clearResume(formType) {
    const input = document.getElementById(`${formType}EmpResume`);
    const nameDiv = document.getElementById(`${formType}EmpResumeName`);
    
    if (input) input.value = '';
    if (nameDiv) nameDiv.textContent = 'No file selected';
}

async function uploadEmployeeFile(employeeId, file, fileType) {
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`/api/employees/${employeeId}/${fileType}`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log(`${fileType} uploaded successfully:`, data);
        } else {
            console.error(`Error uploading ${fileType}:`, data.message);
        }
        
        return data;
    } catch (error) {
        console.error(`Error uploading ${fileType}:`, error);
        return { success: false, message: error.message };
    }
}
