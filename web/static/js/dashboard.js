// Dashboard JavaScript logic
// Handles employee dashboard functionality and API calls

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
                
                // Update profile tab
                document.getElementById('profileName').textContent = employee.full_name || '-';
                document.getElementById('profileEmail').textContent = employee.email || '-';
                document.getElementById('profileDepartment').textContent = employee.department || '-';
                document.getElementById('profilePosition').textContent = employee.position || '-';
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
            
            if (data.success && data.data && data.data.length > 0) {
                const tableHtml = buildPayrollTable(data.data);
                document.getElementById('payrollTab').innerHTML = '<h2>Payroll Information</h2>' + tableHtml;
            } else {
                document.getElementById('payrollTab').innerHTML = '<h2>Payroll Information</h2><p>No payroll records found.</p>';
            }
        } catch (error) {
            console.error('Error loading payroll:', error);
            document.getElementById('payrollTab').innerHTML = '<h2>Payroll Information</h2><p>Error loading payroll data.</p>';
        }
    }
    
    function buildPayrollTable(records) {
        let html = '<table><thead><tr>';
        html += '<th>Month</th><th>Basic Salary</th><th>Net Pay</th><th>Status</th>';
        html += '</tr></thead><tbody>';
        
        records.forEach(record => {
            html += '<tr>';
            html += `<td>${record.month_year || '-'}</td>`;
            html += `<td>RM ${parseFloat(record.basic_salary || 0).toFixed(2)}</td>`;
            html += `<td>RM ${parseFloat(record.net_pay || 0).toFixed(2)}</td>`;
            html += `<td>${record.status || '-'}</td>`;
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        return html;
    }
    
    async function loadEngagementsData() {
        try {
            const response = await fetch(`/api/engagements/${userEmail}`);
            const data = await response.json();
            
            if (data.success && data.data) {
                let html = '<h2>Training & Trips</h2>';
                
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
                
                document.getElementById('engagementsTab').innerHTML = html;
            } else {
                document.getElementById('engagementsTab').innerHTML = '<h2>Training & Trips</h2><p>No engagement records found.</p>';
            }
        } catch (error) {
            console.error('Error loading engagements:', error);
            document.getElementById('engagementsTab').innerHTML = '<h2>Training & Trips</h2><p>Error loading engagement data.</p>';
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
