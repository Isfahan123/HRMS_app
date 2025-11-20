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
        html += '<th>Name</th><th>Email</th><th>Department</th><th>Position</th><th>Status</th><th>Actions</th>';
        html += '</tr></thead><tbody>';
        
        employees.forEach(employee => {
            html += '<tr>';
            html += `<td>${employee.full_name || '-'}</td>`;
            html += `<td>${employee.email || '-'}</td>`;
            html += `<td>${employee.department || '-'}</td>`;
            html += `<td>${employee.position || '-'}</td>`;
            html += `<td>${employee.employment_status || '-'}</td>`;
            html += `<td><button class="btn-secondary btn-sm" onclick="openEditEmployeeModal('${employee.id || employee.email}')">✏️ Edit</button></td>`;
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        return html;
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
            
            const container = document.getElementById('pendingLeaveRequestsTable');
            if (!container) return;
            
            if (data.success && data.data && data.data.length > 0) {
                const tableHtml = buildLeaveRequestsTable(data.data);
                container.innerHTML = tableHtml;
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
    
    // Load approved/rejected leave requests
    async function loadApprovedRejectedLeaveRequests(statusFilter = '') {
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
                
                if (filteredRequests.length === 0) {
                    container.innerHTML = '<p>No approved/rejected leave requests found.</p>';
                    return;
                }
                
                let html = '<table><thead><tr>';
                html += '<th>Employee</th><th>Type</th><th>Start Date</th><th>End Date</th><th>Days</th><th>Status</th><th>Reviewed By</th><th>Reviewed At</th>';
                html += '</tr></thead><tbody>';
                
                filteredRequests.forEach(request => {
                    const statusColor = request.status === 'approved' ? 'green' : 
                                       request.status === 'rejected' ? 'red' : '#666';
                    html += '<tr>';
                    html += `<td>${request.employees?.full_name || request.employee_email || '-'}</td>`;
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
            loadApprovedRejectedLeaveRequests(statusFilter);
        });
    }
    
    const clearLeaveFilterBtn = document.getElementById('clearLeaveFilterBtn');
    if (clearLeaveFilterBtn) {
        clearLeaveFilterBtn.addEventListener('click', () => {
            document.getElementById('leaveStatusFilter').value = '';
            loadApprovedRejectedLeaveRequests();
        });
    }
    
    async function loadPayrollRuns() {
        try {
            const response = await fetch('/api/admin/payroll-runs');
            const data = await response.json();
            
            const container = document.getElementById('payrollRunsTable');
            if (!container) return;
            
            if (data.success && data.data && data.data.length > 0) {
                const tableHtml = buildPayrollRunsTable(data.data);
                container.innerHTML = tableHtml;
            } else {
                container.innerHTML = '<p>No payroll runs found.</p>';
            }
        } catch (error) {
            console.error('Error loading payroll runs:', error);
            const container = document.getElementById('payrollRunsTable');
            if (container) container.innerHTML = '<p>Error loading payroll data.</p>';
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
                    
                    // Load data when specific tabs are activated
                    if (tabName === 'employeeHistory') {
                        console.log('🔄 Reloading employment history data...');
                        loadEmployeeHistory();
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
            html += `<td style="padding: 12px;">${bonus.employees?.full_name || bonus.employee_id}</td>`;
            html += `<td style="padding: 12px;">${bonus.bonus_type || '-'}</td>`;
            html += `<td style="padding: 12px; text-align: right;">RM ${parseFloat(bonus.amount || 0).toFixed(2)}</td>`;
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
                html += '<th style="padding: 10px; text-align: right;">EIS</th>';
                html += '<th style="padding: 10px; text-align: right;">PCB</th>';
                html += '<th style="padding: 10px; text-align: right;">Total (Ee)</th>';
                html += '<th style="padding: 10px; text-align: right;">Total (Er)</th>';
                html += '</tr></thead><tbody>';
                
                let totalEpfEe = 0, totalEpfEr = 0, totalSocsoEe = 0, totalSocsoEr = 0, totalEis = 0, totalPcb = 0;
                
                filteredData.forEach(contrib => {
                    const epfEe = parseFloat(contrib.epf_employee) || 0;
                    const epfEr = parseFloat(contrib.epf_employer) || 0;
                    const socsoEe = parseFloat(contrib.socso_employee) || 0;
                    const socsoEr = parseFloat(contrib.socso_employer) || 0;
                    const eis = parseFloat(contrib.eis) || 0;
                    const pcb = parseFloat(contrib.pcb) || 0;
                    const totalEe = epfEe + socsoEe + eis;
                    const totalEr = epfEr + socsoEr;
                    
                    totalEpfEe += epfEe;
                    totalEpfEr += epfEr;
                    totalSocsoEe += socsoEe;
                    totalSocsoEr += socsoEr;
                    totalEis += eis;
                    totalPcb += pcb;
                    
                    html += '<tr style="border-bottom: 1px solid #eee;">';
                    html += `<td style="padding: 10px;">${contrib.employee_name || '-'}</td>`;
                    html += `<td style="padding: 10px;">${contrib.month_year || '-'}</td>`;
                    html += `<td style="padding: 10px; text-align: right;">RM ${epfEe.toFixed(2)}</td>`;
                    html += `<td style="padding: 10px; text-align: right;">RM ${epfEr.toFixed(2)}</td>`;
                    html += `<td style="padding: 10px; text-align: right;">RM ${socsoEe.toFixed(2)}</td>`;
                    html += `<td style="padding: 10px; text-align: right;">RM ${socsoEr.toFixed(2)}</td>`;
                    html += `<td style="padding: 10px; text-align: right;">RM ${eis.toFixed(2)}</td>`;
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
                html += `<td style="padding: 10px; text-align: right;">RM ${totalEis.toFixed(2)}</td>`;
                html += `<td style="padding: 10px; text-align: right;">RM ${totalPcb.toFixed(2)}</td>`;
                html += `<td style="padding: 10px; text-align: right;">RM ${(totalEpfEe + totalSocsoEe + totalEis).toFixed(2)}</td>`;
                html += `<td style="padding: 10px; text-align: right;">RM ${(totalEpfEr + totalSocsoEr).toFixed(2)}</td>`;
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
                    tableContainer.innerHTML = '<p style="color: #666;">No salary history records found matching the filters.</p>';
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
                html += '</tr></thead><tbody>';
                
                filteredData.forEach(record => {
                    const prevSalary = parseFloat(record.previous_value) || 0;
                    const newSalary = parseFloat(record.new_value) || 0;
                    const change = newSalary - prevSalary;
                    const changePercent = prevSalary > 0 ? (change / prevSalary * 100) : 0;
                    const changeColor = change >= 0 ? '#2e7d32' : '#c62828';
                    
                    html += '<tr style="border-bottom: 1px solid #eee;">';
                    html += `<td style="padding: 10px;">${record.effective_date || '-'}</td>`;
                    html += `<td style="padding: 10px;">${record.employee_email || record.employee_name || '-'}</td>`;
                    html += `<td style="padding: 10px;"><span style="background: #e3f2fd; padding: 4px 8px; border-radius: 4px; color: #1976d2; font-size: 12px;">${record.change_type || '-'}</span></td>`;
                    html += `<td style="padding: 10px;">RM ${prevSalary.toFixed(2)}</td>`;
                    html += `<td style="padding: 10px;"><strong>RM ${newSalary.toFixed(2)}</strong></td>`;
                    html += `<td style="padding: 10px; color: ${changeColor};"><strong>${change >= 0 ? '+' : ''}RM ${change.toFixed(2)} (${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(1)}%)</strong></td>`;
                    html += `<td style="padding: 10px;"><small>${record.reason || '-'}</small></td>`;
                    html += '</tr>';
                });
                
                html += '</tbody></table>';
                html += `<p style="margin-top: 15px; color: #666; font-size: 14px;">Showing ${filteredData.length} salary change record(s)</p>`;
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
            
            const salaryDisplay = document.getElementById('currentSalaryDisplay');
            if (salaryDisplay) {
                salaryDisplay.textContent = `RM ${parseFloat(salary).toFixed(2)}`;
            }
            
            // Auto-fill the employee email in the form
            const emailInput = document.getElementById('salaryChangeEmployee');
            if (emailInput) {
                emailInput.value = selectedOption.value;
            }
            
            // Auto-fill previous salary
            const prevSalaryInput = document.getElementById('salaryChangePrevious');
            if (prevSalaryInput) {
                prevSalaryInput.value = parseFloat(salary).toFixed(2);
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
                    html += `<td style="padding: 10px;">${record.employee_email || record.employee_name || '-'}</td>`;
                    html += `<td style="padding: 10px;">${record.start_date || '-'}</td>`;
                    html += `<td style="padding: 10px;">${record.end_date || '-'}</td>`;
                    html += `<td style="padding: 10px;">${record.location || '-'}</td>`;
                    html += `<td style="padding: 10px;">${record.cost ? 'RM ' + parseFloat(record.cost).toFixed(2) : '-'}</td>`;
                    html += `<td style="padding: 10px;"><span style="color: ${statusColor}; font-weight: bold;">${record.status || '-'}</span></td>`;
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
                document.getElementById('editEmpHistoryEmployeeSelect')
            ];
            
            if (data.success && data.data && data.data.length > 0) {
                selectors.forEach(selector => {
                    if (!selector) return;
                    selector.innerHTML = '<option value="">Select Employee</option>';
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
                html += '<th style="padding: 10px;">Type</th>';
                html += '<th style="padding: 10px;">Period</th>';
                html += '<th style="padding: 10px;">Actions</th>';
                html += '</tr></thead><tbody>';
                
                filteredData.forEach(record => {
                    html += '<tr style="border-bottom: 1px solid #eee;">';
                    html += `<td style="padding: 10px;">${record.employee_email || record.employee_name || '-'}</td>`;
                    html += `<td style="padding: 10px;"><strong>${record.company || '-'}</strong></td>`;
                    html += `<td style="padding: 10px;">${record.job_title || '-'}</td>`;
                    html += `<td style="padding: 10px;">${record.position || '-'}</td>`;
                    html += `<td style="padding: 10px;">${record.department || '-'}</td>`;
                    html += `<td style="padding: 10px;"><span style="background: #667eea20; padding: 4px 8px; border-radius: 4px; color: #667eea; font-size: 12px;">${record.employment_type || '-'}</span></td>`;
                    
                    const startDate = record.start_date || '-';
                    const endDate = record.end_date || 'Present';
                    html += `<td style="padding: 10px;"><small>${startDate} to ${endDate}</small></td>`;
                    
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
    
    // Edit Employee Functions
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
                document.getElementById('editEmpGender').value = employee.gender || '';
                document.getElementById('editEmpDOB').value = employee.date_of_birth || '';
                document.getElementById('editEmpNRIC').value = employee.nric || '';
                document.getElementById('editEmpNationality').value = employee.nationality || '';
                document.getElementById('editEmpCitizenship').value = employee.citizenship || '';
                document.getElementById('editEmpRace').value = employee.race || '';
                document.getElementById('editEmpReligion').value = employee.religion || '';
                document.getElementById('editEmpMaritalStatus').value = employee.marital_status || '';
                document.getElementById('editEmpChildren').value = employee.number_of_children || '0';
                document.getElementById('editEmpPhone').value = employee.phone_number || '';
                document.getElementById('editEmpAddress').value = employee.address || '';
                document.getElementById('editEmpCity').value = employee.city || '';
                document.getElementById('editEmpState').value = employee.state || '';
                document.getElementById('editEmpZipcode').value = employee.zipcode || '';
                document.getElementById('editEmpDepartment').value = employee.department || '';
                document.getElementById('editEmpPosition').value = employee.position || '';
                document.getElementById('editEmpRole').value = employee.role || 'employee';
                document.getElementById('editEmpStatus').value = employee.employment_status || 'Active';
                document.getElementById('editEmpJoinDate').value = employee.join_date || '';
                document.getElementById('editEmpEPFNumber').value = employee.epf_number || '';
                document.getElementById('editEmpSOCSONumber').value = employee.socso_number || '';
                document.getElementById('editEmpIncomeTaxNumber').value = employee.income_tax_number || '';
                
                // Show the modal
                document.getElementById('editEmployeeModal').style.display = 'block';
            }
        } catch (error) {
            console.error('Error loading employee data:', error);
            alert('Error loading employee data');
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
    window.showAddVariablePercentageForm = function() {
        document.getElementById('addVariablePercentageForm').style.display = 'block';
    };
    
    window.hideAddVariablePercentageForm = function() {
        document.getElementById('addVariablePercentageForm').style.display = 'none';
        const form = document.getElementById('newVariablePercentageForm');
        form.reset();
        document.getElementById('addVariablePercentageMessage').style.display = 'none';
        
        // Reset edit mode
        form.removeAttribute('data-rule-id');
        form.removeAttribute('data-edit-mode');
        
        // Reset form title and button
        const formTitle = document.querySelector('#addVariablePercentageForm h4');
        if (formTitle) formTitle.textContent = 'Add Variable Percentage Rule';
        
        const submitBtn = document.querySelector('#newVariablePercentageForm button[type="submit"]');
        if (submitBtn) submitBtn.textContent = 'Create Rule';
        
        // Hide conditional fields
        document.getElementById('varPctDepartmentGroup').style.display = 'none';
        document.getElementById('varPctEmployeeGroup').style.display = 'none';
    };
    
    window.toggleEmployeeSelection = function() {
        const applyTo = document.getElementById('varPctApplyTo').value;
        const deptGroup = document.getElementById('varPctDepartmentGroup');
        const empGroup = document.getElementById('varPctEmployeeGroup');
        
        if (applyTo === 'department') {
            deptGroup.style.display = 'block';
            empGroup.style.display = 'none';
        } else if (applyTo === 'individual') {
            deptGroup.style.display = 'none';
            empGroup.style.display = 'block';
        } else {
            deptGroup.style.display = 'none';
            empGroup.style.display = 'none';
        }
    };
    
    async function loadVariablePercentageRules() {
        try {
            const response = await fetch('/api/admin/variable-percentage');
            const data = await response.json();
            
            const container = document.getElementById('variablePercentageRulesTable');
            if (!container) return;
            
            if (data.success && data.data && data.data.length > 0) {
                let html = '<h4 style="margin-top: 20px; margin-bottom: 15px;">Active Variable Percentage Rules</h4>';
                html += '<table style="width: 100%; border-collapse: collapse;"><thead><tr style="background: #667eea; color: white;">';
                html += '<th style="padding: 10px;">Rule Name</th>';
                html += '<th style="padding: 10px;">Type</th>';
                html += '<th style="padding: 10px;">Percentage</th>';
                html += '<th style="padding: 10px;">Apply To</th>';
                html += '<th style="padding: 10px;">Base On</th>';
                html += '<th style="padding: 10px;">Frequency</th>';
                html += '<th style="padding: 10px;">Status</th>';
                html += '<th style="padding: 10px;">Actions</th>';
                html += '</tr></thead><tbody>';
                
                data.data.forEach(rule => {
                    const statusClass = rule.status === 'active' ? 'color: #2e7d32;' : 'color: #f57c00;';
                    const applyToText = rule.apply_to === 'all' ? 'All Employees' : 
                                      rule.apply_to === 'department' ? `Dept: ${rule.department || '-'}` :
                                      rule.apply_to === 'individual' ? `Emp: ${rule.employee_email || '-'}` : '-';
                    
                    html += '<tr style="border-bottom: 1px solid #eee;">';
                    html += `<td style="padding: 10px;"><strong>${rule.name || '-'}</strong></td>`;
                    html += `<td style="padding: 10px;">${rule.type || '-'}</td>`;
                    html += `<td style="padding: 10px;"><strong>${rule.percentage}%</strong></td>`;
                    html += `<td style="padding: 10px;">${applyToText}</td>`;
                    html += `<td style="padding: 10px;">${(rule.base_on || '').replace('_', ' ') || '-'}</td>`;
                    html += `<td style="padding: 10px;">${rule.frequency || '-'}</td>`;
                    html += `<td style="padding: 10px; ${statusClass}"><strong>${rule.status || '-'}</strong></td>`;
                    html += `<td style="padding: 10px;">`;
                    html += `<button class="btn-secondary btn-sm" onclick="editVariablePercentageRule('${rule.id}')">✏️ Edit</button> `;
                    html += `<button class="btn-secondary btn-sm" onclick="deleteVariablePercentageRule('${rule.id}')">🗑️ Delete</button>`;
                    html += `</td>`;
                    html += '</tr>';
                });
                
                html += '</tbody></table>';
                html += `<p style="margin-top: 10px; color: #666; font-size: 14px;">${data.data.length} rule(s) configured</p>`;
                container.innerHTML = html;
            } else {
                container.innerHTML = '<p style="color: #666;">No variable percentage rules configured yet. Click "Add Variable Percentage Rule" to create one.</p>';
            }
        } catch (error) {
            console.error('Error loading variable percentage rules:', error);
            const container = document.getElementById('variablePercentageRulesTable');
            if (container) container.innerHTML = '<p style="color: #f44336;">Error loading rules.</p>';
        }
    }
    
    // Handle new variable percentage form submission
    const newVariablePercentageForm = document.getElementById('newVariablePercentageForm');
    if (newVariablePercentageForm) {
        newVariablePercentageForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(newVariablePercentageForm);
            const data = {};
            
            for (let [key, value] of formData.entries()) {
                data[key] = value;
            }
            
            // Check if we're in edit mode
            const isEditMode = this.getAttribute('data-edit-mode') === 'true';
            const ruleId = this.getAttribute('data-rule-id');
            
            try {
                const url = isEditMode ? `/api/admin/variable-percentage/${ruleId}` : '/api/admin/variable-percentage';
                const method = isEditMode ? 'PUT' : 'POST';
                
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                const messageDiv = document.getElementById('addVariablePercentageMessage');
                messageDiv.style.display = 'block';
                
                if (result.success) {
                    messageDiv.className = 'success-message';
                    messageDiv.textContent = isEditMode ? '✅ Variable percentage rule updated successfully!' : '✅ Variable percentage rule created successfully!';
                    
                    setTimeout(() => {
                        hideAddVariablePercentageForm();
                        loadVariablePercentageRules();
                    }, 1500);
                } else {
                    messageDiv.className = 'error-message';
                    messageDiv.textContent = result.message || (isEditMode ? 'Failed to update rule' : 'Failed to create rule');
                }
            } catch (error) {
                console.error('Error saving variable percentage rule:', error);
                const messageDiv = document.getElementById('addVariablePercentageMessage');
                messageDiv.style.display = 'block';
                messageDiv.className = 'error-message';
                messageDiv.textContent = 'Error saving rule';
            }
        });
    }
    
    window.editVariablePercentageRule = async function(ruleId) {
        try {
            // Fetch all rules
            const response = await fetch('/api/admin/variable-percentage');
            const data = await response.json();
            
            if (!data.success || !data.data) {
                alert('Error loading rule data');
                return;
            }
            
            // Find the specific rule
            const rule = data.data.find(r => r.id === ruleId);
            if (!rule) {
                alert('Rule not found');
                return;
            }
            
            // Show the form
            showAddVariablePercentageForm();
            
            // Pre-populate the form with existing rule data
            document.getElementById('varPctName').value = rule.name || '';
            document.getElementById('varPctType').value = rule.type || '';
            document.getElementById('varPctPercentage').value = rule.percentage || '';
            document.getElementById('varPctApplyTo').value = rule.apply_to || '';
            toggleEmployeeSelection(); // Show/hide department/employee fields
            document.getElementById('varPctDepartment').value = rule.department || '';
            document.getElementById('varPctEmployee').value = rule.employee_email || '';
            document.getElementById('varPctBaseOn').value = rule.base_on || '';
            document.getElementById('varPctFrequency').value = rule.frequency || '';
            document.getElementById('varPctStatus').value = rule.status || '';
            document.getElementById('varPctStartDate').value = rule.start_date || '';
            document.getElementById('varPctEndDate').value = rule.end_date || '';
            document.getElementById('varPctDescription').value = rule.description || '';
            
            // Change form title to indicate edit mode
            const formTitle = document.querySelector('#addVariablePercentageForm h4');
            if (formTitle) formTitle.textContent = 'Edit Variable Percentage Rule';
            
            // Change button text
            const submitBtn = document.querySelector('#newVariablePercentageForm button[type="submit"]');
            if (submitBtn) submitBtn.textContent = 'Update Rule';
            
            // Store the rule ID for update
            const form = document.getElementById('newVariablePercentageForm');
            form.setAttribute('data-rule-id', ruleId);
            form.setAttribute('data-edit-mode', 'true');
            
        } catch (error) {
            console.error('Error loading rule for edit:', error);
            alert('Error loading rule data');
        }
    };
    
    window.deleteVariablePercentageRule = async function(ruleId) {
        if (!confirm('Are you sure you want to delete this variable percentage rule?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/admin/variable-percentage/${ruleId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert('✅ Rule deleted successfully');
                loadVariablePercentageRules();
            } else {
                alert(`❌ ${result.message}`);
            }
        } catch (error) {
            console.error('Error deleting variable percentage rule:', error);
            alert('❌ Error deleting rule');
        }
    };
    
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
    
    // Admin Leave Request Form Handler
    const adminLeaveRequestForm = document.getElementById('adminLeaveRequestForm');
    if (adminLeaveRequestForm) {
        adminLeaveRequestForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(adminLeaveRequestForm);
            const employeeId = formData.get('employee_id');
            
            // Need to convert employee_id to email - fetch employee data
            try {
                const employeesResponse = await fetch('/api/employees');
                const employeesData = await employeesResponse.json();
                
                if (!employeesData.success || !employeesData.data) {
                    throw new Error('Failed to load employee data');
                }
                
                // Find employee by ID
                const employee = employeesData.data.find(emp => 
                    emp.employee_id === employeeId || emp.email === employeeId
                );
                
                if (!employee) {
                    const messageDiv = document.getElementById('adminLeaveFormMessage');
                    messageDiv.style.display = 'block';
                    messageDiv.className = 'error-message';
                    messageDiv.textContent = `Employee with ID "${employeeId}" not found. Please use employee email or valid ID.`;
                    return;
                }
                
                // Build leave request data
                const leaveData = {
                    employee_email: employee.email,
                    leave_type: formData.get('leave_type'),
                    start_date: formData.get('start_date'),
                    end_date: formData.get('end_date'),
                    title: formData.get('title') || 'Admin submitted leave',
                    is_half_day: formData.get('is_half_day') === 'on',
                    half_day_period: formData.get('is_half_day') === 'on' ? 'morning' : null
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
    }
    
    // Salary History Edit/Delete Functions
    window.editSalaryHistory = async function(recordId) {
        try {
            const response = await fetch('/api/admin/salary-history');
            const data = await response.json();
            
            if (data.success && data.data) {
                const record = data.data.find(r => r.id === recordId);
                if (!record) {
                    alert('Record not found');
                    return;
                }
                
                const newEffectiveDate = prompt('Effective Date (YYYY-MM-DD):', record.effective_date || '');
                if (newEffectiveDate === null) return; // User cancelled
                
                const newPrevSalary = prompt('Previous Salary:', parseFloat(record.previous_value) || 0);
                if (newPrevSalary === null) return;
                
                const newNewSalary = prompt('New Salary:', parseFloat(record.new_value) || 0);
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
    
    // Engagement Edit/Delete Functions
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
    
    // Employee History Edit/Delete Functions
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
                data[key] = value;
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
    
    // Export additional functions for onclick handlers
    window.loadSalaryHistory = loadSalaryHistory;
    window.loadEmployeeHistory = loadEmployeeHistory;
    
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
});
