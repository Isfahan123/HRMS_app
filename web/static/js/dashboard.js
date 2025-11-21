// Dashboard JavaScript logic
// Handles employee dashboard functionality and API calls

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
    // Check if user is logged in
    const userEmail = sessionStorage.getItem('userEmail');
    const userRole = sessionStorage.getItem('userRole');
    
    if (!userEmail) {
        // Redirect to login if not authenticated
        window.location.href = '/';
        return;
    }
    
    // Initialize dashboard
    initializeDashboard();
    setupTabs();
    setupLogout();
    setupLeaveRequestForm();
    setupProfileEdit();
    setupPayslipDownload();
    
    async function initializeDashboard() {
        try {
            // Fetch employee data
            const employeeResponse = await fetch(`/api/employee/${userEmail}`);
            const employeeData = await employeeResponse.json();
            
            if (employeeData.success) {
                const employee = employeeData.data;
                
                // Update welcome message
                document.getElementById('welcomeMessage').textContent = 
                    `Welcome, ${employee.full_name || employee.email}`;
                
                // Update profile tab - Basic Information
                document.getElementById('profileName').textContent = employee.full_name || '-';
                document.getElementById('profileEmail').textContent = employee.email || '-';
                document.getElementById('profileEmployeeID').textContent = employee.employee_id || '-';
                document.getElementById('profileGender').textContent = employee.gender || '-';
                document.getElementById('profileDOB').textContent = employee.date_of_birth || '-';
                document.getElementById('profileNRIC').textContent = employee.nric || '-';
                document.getElementById('profileNationality').textContent = employee.nationality || '-';
                document.getElementById('profileCitizenship').textContent = employee.citizenship || '-';
                document.getElementById('profileRace').textContent = employee.race || '-';
                document.getElementById('profileReligion').textContent = employee.religion || '-';
                document.getElementById('profileMaritalStatus').textContent = employee.marital_status || '-';
                document.getElementById('profileChildren').textContent = employee.number_of_children || '-';
                
                // Contact Information
                document.getElementById('profilePhone').textContent = employee.phone_number || '-';
                document.getElementById('profileAddress').textContent = employee.address || '-';
                document.getElementById('profileCity').textContent = employee.city || '-';
                document.getElementById('profileState').textContent = employee.state || '-';
                document.getElementById('profileZipcode').textContent = employee.zipcode || '-';
                
                // Employment Information
                document.getElementById('profileDepartment').textContent = employee.department || '-';
                document.getElementById('profilePosition').textContent = employee.position || '-';
                document.getElementById('profileStatus').textContent = employee.employment_status || '-';
                document.getElementById('profileJoinDate').textContent = employee.join_date || '-';
                
                // EPF/SOCSO Information
                document.getElementById('profileEPFNumber').textContent = employee.epf_number || '-';
                document.getElementById('profileSOCSONumber').textContent = employee.socso_number || '-';
                document.getElementById('profileTaxNumber').textContent = employee.income_tax_number || '-';
            }
            
            // Load attendance data
            loadAttendanceData();
            
            // Load leave requests
            loadLeaveRequests();
            
            // Load payroll data
            loadPayrollData();
            
            // Load engagements data
            loadEngagementsData();
            
        } catch (error) {
            console.error('Error initializing dashboard:', error);
        }
    }
    
    async function loadAttendanceData() {
        try {
            const response = await fetch(`/api/attendance/${userEmail}`);
            const data = await response.json();
            
            if (data.success && data.data && data.data.length > 0) {
                const recentRecords = data.data.slice(0, 5);
                const summary = `${recentRecords.length} recent record(s)`;
                document.getElementById('attendanceSummary').textContent = summary;
                
                // Build attendance table
                const tableHtml = buildAttendanceTable(data.data);
                document.getElementById('attendanceTable').innerHTML = tableHtml;
            } else {
                document.getElementById('attendanceSummary').textContent = 'No attendance records';
                document.getElementById('attendanceTable').innerHTML = '<p>No attendance records found.</p>';
            }
        } catch (error) {
            console.error('Error loading attendance:', error);
            document.getElementById('attendanceSummary').textContent = 'Error loading attendance';
            document.getElementById('attendanceTable').innerHTML = '<p>Error loading attendance data.</p>';
        }
    }
    
    async function loadLeaveRequests() {
        try {
            const response = await fetch(`/api/leave-requests/${userEmail}`);
            const data = await response.json();
            
            if (data.success && data.data && data.data.length > 0) {
                const pendingRequests = data.data.filter(req => req.status === 'pending');
                const summary = `${pendingRequests.length} pending request(s), ${data.data.length} total`;
                document.getElementById('leaveSummary').textContent = summary;
                
                // Build leave requests table
                const tableHtml = buildLeaveRequestsTable(data.data);
                document.getElementById('leaveRequests').innerHTML = tableHtml;
            } else {
                document.getElementById('leaveSummary').textContent = 'No leave requests';
                document.getElementById('leaveRequests').innerHTML = '<p>No leave requests found.</p>';
            }
        } catch (error) {
            console.error('Error loading leave requests:', error);
            document.getElementById('leaveSummary').textContent = 'Error loading requests';
            document.getElementById('leaveRequests').innerHTML = '<p>Error loading leave requests.</p>';
        }
    }
    
    function buildAttendanceTable(records) {
        let html = '<table><thead><tr>';
        html += '<th>Date</th><th>Check In</th><th>Check Out</th><th>Status</th>';
        html += '</tr></thead><tbody>';
        
        records.forEach(record => {
            html += '<tr>';
            html += `<td>${record.date || '-'}</td>`;
            html += `<td>${record.check_in_time || '-'}</td>`;
            html += `<td>${record.check_out_time || '-'}</td>`;
            html += `<td>${record.status || '-'}</td>`;
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        return html;
    }
    
    function buildLeaveRequestsTable(requests) {
        let html = '<table><thead><tr>';
        html += '<th>Start Date</th><th>End Date</th><th>Type</th><th>Status</th>';
        html += '</tr></thead><tbody>';
        
        requests.forEach(request => {
            html += '<tr>';
            html += `<td>${request.start_date || '-'}</td>`;
            html += `<td>${request.end_date || '-'}</td>`;
            html += `<td>${request.leave_type || '-'}</td>`;
            html += `<td>${request.status || '-'}</td>`;
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        return html;
    }
    
    async function loadPayrollData() {
        try {
            const response = await fetch(`/api/payroll/${userEmail}`);
            const data = await response.json();
            
            const container = document.getElementById('employeePayrollTable');
            if (!container) return;
            
            if (data.success && data.data && data.data.length > 0) {
                const tableHtml = buildPayrollTable(data.data);
                container.innerHTML = tableHtml;
            } else {
                container.innerHTML = '<p>No payroll records found.</p>';
            }
        } catch (error) {
            console.error('Error loading payroll:', error);
            const container = document.getElementById('employeePayrollTable');
            if (container) container.innerHTML = '<p>Error loading payroll data.</p>';
        }
    }
    
    function buildPayrollTable(records) {
        let html = '<table><thead><tr>';
        html += '<th>Month</th><th>Basic Salary</th><th>Net Pay</th><th>Status</th><th>Actions</th>';
        html += '</tr></thead><tbody>';
        
        records.forEach(record => {
            html += '<tr>';
            html += `<td>${record.month_year || '-'}</td>`;
            html += `<td>${formatCurrency(record.basic_salary)}</td>`;
            html += `<td>${formatCurrency(record.net_pay)}</td>`;
            html += `<td>${record.status || '-'}</td>`;
            html += `<td><button class="btn-primary" onclick="downloadPayslip('${record.id}', '${record.month_year}')">Download PDF</button></td>`;
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        return html;
    }
    
    async function loadEngagementsData() {
        try {
            const response = await fetch(`/api/engagements/${userEmail}`);
            const data = await response.json();
            
            const container = document.getElementById('myEngagementsTable');
            if (!container) return;
            
            if (data.success && data.data) {
                let html = '';
                
                // Training courses
                if (data.data.training && data.data.training.length > 0) {
                    html += '<h3>Training Courses</h3>';
                    html += buildTrainingTable(data.data.training);
                } else {
                    html += '<h3>Training Courses</h3><p>No training courses found.</p>';
                }
                
                // Overseas trips
                if (data.data.trips && data.data.trips.length > 0) {
                    html += '<h3>Overseas Work Trips</h3>';
                    html += buildTripsTable(data.data.trips);
                } else {
                    html += '<h3>Overseas Work Trips</h3><p>No overseas trips found.</p>';
                }
                
                container.innerHTML = html;
            } else {
                container.innerHTML = '<p>No engagement records found.</p>';
            }
        } catch (error) {
            console.error('Error loading engagements:', error);
            const container = document.getElementById('myEngagementsTable');
            if (container) container.innerHTML = '<p>Error loading engagement data.</p>';
        }
    }
    
    function buildTrainingTable(records) {
        let html = '<table><thead><tr>';
        html += '<th>Course Name</th><th>Start Date</th><th>End Date</th><th>Status</th>';
        html += '</tr></thead><tbody>';
        
        records.forEach(record => {
            html += '<tr>';
            html += `<td>${record.course_name || '-'}</td>`;
            html += `<td>${record.start_date || '-'}</td>`;
            html += `<td>${record.end_date || '-'}</td>`;
            html += `<td>${record.status || '-'}</td>`;
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        return html;
    }
    
    function buildTripsTable(records) {
        let html = '<table><thead><tr>';
        html += '<th>Destination</th><th>Start Date</th><th>End Date</th><th>Purpose</th>';
        html += '</tr></thead><tbody>';
        
        records.forEach(record => {
            html += '<tr>';
            html += `<td>${record.destination || '-'}</td>`;
            html += `<td>${record.start_date || '-'}</td>`;
            html += `<td>${record.end_date || '-'}</td>`;
            html += `<td>${record.purpose || '-'}</td>`;
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        return html;
    }
    
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
                
                // Get parent tab to scope subtab switching
                const parentContainer = this.closest('.tab-pane');
                if (!parentContainer) return;
                
                // If this is a month tab (for payroll history)
                if (monthValue) {
                    // Handle month tab switching
                    const monthButtons = parentContainer.querySelectorAll('[data-month]');
                    monthButtons.forEach(btn => btn.classList.remove('active'));
                    this.classList.add('active');
                    
                    // Filter payroll table by month
                    filterEmployeePayrollByMonth(monthValue);
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
        
        // Setup year filter for employee payroll
        const yearFilter = document.getElementById('employeePayrollYearFilter');
        if (yearFilter) {
            yearFilter.addEventListener('change', function() {
                filterEmployeePayrollByMonth(document.querySelector('[data-month].active')?.getAttribute('data-month') || 'all');
            });
        }
    }
    
    function filterEmployeePayrollByMonth(month) {
        // This function will filter the payroll table based on selected month
        console.log('Filtering employee payroll by month:', month);
        
        const table = document.getElementById('employeePayrollTable');
        if (!table) return;
        
        const year = document.getElementById('employeePayrollYearFilter')?.value;
        
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
    
    function setupLeaveRequestForm() {
        const form = document.getElementById('leaveRequestForm');
        const messageDiv = document.getElementById('leaveFormMessage');
        
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = {
                employee_email: userEmail,
                leave_type: document.getElementById('leaveType').value,
                start_date: document.getElementById('startDate').value,
                end_date: document.getElementById('endDate').value,
                title: document.getElementById('leaveTitle').value,
                is_half_day: document.getElementById('isHalfDay').checked
            };
            
            try {
                const response = await fetch('/api/leave-requests/submit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });
                
                const data = await response.json();
                
                messageDiv.style.display = 'block';
                if (data.success) {
                    messageDiv.className = 'success-message';
                    messageDiv.textContent = data.message;
                    form.reset();
                    // Reload leave requests
                    loadLeaveRequests();
                } else {
                    messageDiv.className = 'error-message';
                    messageDiv.textContent = data.message;
                }
            } catch (error) {
                messageDiv.style.display = 'block';
                messageDiv.className = 'error-message';
                messageDiv.textContent = 'Error submitting leave request';
                console.error('Error:', error);
            }
        });
    }
    
    function setupProfileEdit() {
        const editBtn = document.getElementById('editProfileBtn');
        const cancelBtn = document.getElementById('cancelEditBtn');
        const profileView = document.getElementById('profileView');
        const profileForm = document.getElementById('profileEditForm');
        const messageDiv = document.getElementById('profileEditMessage');
        
        editBtn.addEventListener('click', function() {
            // Populate form with current values
            document.getElementById('editFullName').value = document.getElementById('profileName').textContent;
            document.getElementById('editPhone').value = document.getElementById('profilePhone').textContent !== '-' ? document.getElementById('profilePhone').textContent : '';
            document.getElementById('editAddress').value = document.getElementById('profileAddress').textContent !== '-' ? document.getElementById('profileAddress').textContent : '';
            
            profileView.style.display = 'none';
            profileForm.style.display = 'block';
        });
        
        cancelBtn.addEventListener('click', function() {
            profileView.style.display = 'block';
            profileForm.style.display = 'none';
            messageDiv.style.display = 'none';
        });
        
        profileForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = {
                full_name: document.getElementById('editFullName').value,
                phone_number: document.getElementById('editPhone').value,
                address: document.getElementById('editAddress').value
            };
            
            try {
                const response = await fetch(`/api/employee/${userEmail}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });
                
                const data = await response.json();
                
                messageDiv.style.display = 'block';
                if (data.success) {
                    messageDiv.className = 'success-message';
                    messageDiv.textContent = data.message;
                    
                    // Update profile display
                    document.getElementById('profileName').textContent = formData.full_name;
                    document.getElementById('profilePhone').textContent = formData.phone_number || '-';
                    document.getElementById('profileAddress').textContent = formData.address || '-';
                    
                    // Switch back to view mode after a delay
                    setTimeout(() => {
                        profileView.style.display = 'block';
                        profileForm.style.display = 'none';
                        messageDiv.style.display = 'none';
                    }, 2000);
                } else {
                    messageDiv.className = 'error-message';
                    messageDiv.textContent = data.message;
                }
            } catch (error) {
                messageDiv.style.display = 'block';
                messageDiv.className = 'error-message';
                messageDiv.textContent = 'Error updating profile';
                console.error('Error:', error);
            }
        });
    }
    
    function setupPayslipDownload() {
        // Payslip download will be attached to payroll table rows
        // We'll add download buttons dynamically when building the payroll table
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
    
    // Global function for payslip download
    window.downloadPayslip = async function(payrollRunId, monthYear) {
        try {
            // Get employee ID from profile data
            const employeeResponse = await fetch(`/api/employee/${userEmail}`);
            const employeeData = await employeeResponse.json();
            
            if (!employeeData.success || !employeeData.data) {
                alert('Failed to get employee information');
                return;
            }
            
            const employeeId = employeeData.data.id;
            
            // Download payslip PDF
            const response = await fetch(`/api/payroll/payslip/${employeeId}/${payrollRunId}`);
            if (response.ok) {
                const blob = await response.blob();
                const filename = `payslip_${monthYear.replace(/[\/\s]/g, '_')}.pdf`;
                
                // Create download link
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                const errorData = await response.json();
                alert(`Failed to download payslip: ${errorData.detail || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error downloading payslip:', error);
            alert('Error downloading payslip: ' + error.message);
        }
    };
});
