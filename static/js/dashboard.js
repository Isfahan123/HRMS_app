/**
 * Dashboard JavaScript - Handles employee dashboard functionality
 */

// Load data for different tabs
async function loadProfileData() {
    try {
        const response = await fetch('/api/profile');
        const data = await response.json();
        
        if (data.success && data.data) {
            const profile = data.data;
            document.getElementById('profile-name').textContent = profile.full_name || '-';
            document.getElementById('profile-email').textContent = profile.email || '-';
            document.getElementById('profile-phone').textContent = profile.phone || '-';
            document.getElementById('profile-employee-id').textContent = profile.employee_id || '-';
            document.getElementById('profile-department').textContent = profile.department || '-';
            document.getElementById('profile-position').textContent = profile.position || '-';
            document.getElementById('profile-join-date').textContent = 
                window.hrmsUtils.formatDate(profile.join_date) || '-';
            document.getElementById('profile-status').textContent = profile.status || '-';
            document.getElementById('profile-employment-type').textContent = profile.employment_type || '-';
            document.getElementById('profile-salary').textContent = 
                profile.salary ? `RM ${parseFloat(profile.salary).toFixed(2)}` : '-';
            document.getElementById('profile-manager').textContent = profile.manager_name || '-';
        }
    } catch (error) {
        console.error('Error loading profile:', error);
        window.hrmsUtils.showNotification('Failed to load profile data', 'error');
    }
}

async function loadAttendanceData() {
    try {
        const response = await fetch('/api/attendance');
        const data = await response.json();
        
        if (data.success && data.data) {
            const tbody = document.getElementById('attendance-tbody');
            tbody.innerHTML = '';
            
            if (data.data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">No attendance records found</td></tr>';
                return;
            }
            
            data.data.forEach(record => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${window.hrmsUtils.formatDate(record.date)}</td>
                    <td>${window.hrmsUtils.formatTime(record.check_in)}</td>
                    <td>${window.hrmsUtils.formatTime(record.check_out)}</td>
                    <td>${record.hours || '-'}</td>
                    <td><span class="status-badge status-${record.status}">${record.status}</span></td>
                `;
                tbody.appendChild(row);
            });
            
            // Update today's status if available
            const today = data.data[0];
            if (today && today.date === new Date().toISOString().split('T')[0]) {
                document.getElementById('today-checkin').textContent = 
                    window.hrmsUtils.formatTime(today.check_in);
                document.getElementById('today-checkout').textContent = 
                    window.hrmsUtils.formatTime(today.check_out);
                document.getElementById('today-hours').textContent = today.hours || '-';
            }
        }
    } catch (error) {
        console.error('Error loading attendance:', error);
        window.hrmsUtils.showNotification('Failed to load attendance data', 'error');
    }
}

async function loadLeaveData() {
    try {
        const response = await fetch('/api/leave-requests');
        const data = await response.json();
        
        if (data.success && data.data) {
            const tbody = document.getElementById('leave-tbody');
            tbody.innerHTML = '';
            
            if (data.data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align: center;">No leave requests found</td></tr>';
                return;
            }
            
            data.data.forEach(request => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${request.leave_type}</td>
                    <td>${window.hrmsUtils.formatDate(request.start_date)}</td>
                    <td>${window.hrmsUtils.formatDate(request.end_date)}</td>
                    <td>${request.days}</td>
                    <td><span class="status-badge status-${request.status}">${request.status}</span></td>
                    <td>${request.reason || '-'}</td>
                    <td>
                        <button class="btn-view" onclick="viewLeaveDetails(${request.id})">View</button>
                        ${request.status === 'pending' ? 
                            `<button class="btn-delete" onclick="cancelLeaveRequest(${request.id})">Cancel</button>` : ''}
                    </td>
                `;
                tbody.appendChild(row);
            });
        }
        
        // Load leave balance
        const balanceResponse = await fetch('/api/leave-balance');
        const balanceData = await balanceResponse.json();
        if (balanceData.success && balanceData.data) {
            document.getElementById('annual-balance').textContent = balanceData.data.annual || 0;
            document.getElementById('sick-balance').textContent = balanceData.data.sick || 0;
            document.getElementById('emergency-balance').textContent = balanceData.data.emergency || 0;
        }
    } catch (error) {
        console.error('Error loading leave data:', error);
        window.hrmsUtils.showNotification('Failed to load leave data', 'error');
    }
}

async function loadPayrollData() {
    try {
        const response = await fetch('/api/payroll');
        const data = await response.json();
        
        if (data.success && data.data) {
            document.getElementById('basic-salary').textContent = 
                `RM ${parseFloat(data.data.basic_salary || 0).toFixed(2)}`;
            document.getElementById('allowances').textContent = 
                `RM ${parseFloat(data.data.allowances || 0).toFixed(2)}`;
            document.getElementById('total-gross').textContent = 
                `RM ${parseFloat(data.data.gross_salary || 0).toFixed(2)}`;
            
            // Load payslip history
            const payslips = data.data.payslips || [];
            const tbody = document.getElementById('payslip-tbody');
            tbody.innerHTML = '';
            
            if (payslips.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align: center;">No payslips found</td></tr>';
                return;
            }
            
            payslips.forEach(payslip => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${payslip.month}</td>
                    <td>${payslip.year}</td>
                    <td>RM ${parseFloat(payslip.gross_salary).toFixed(2)}</td>
                    <td>RM ${parseFloat(payslip.deductions).toFixed(2)}</td>
                    <td>RM ${parseFloat(payslip.net_salary).toFixed(2)}</td>
                    <td><span class="status-badge status-${payslip.status}">${payslip.status}</span></td>
                    <td><button class="btn-download" onclick="downloadPayslip(${payslip.id})">Download</button></td>
                `;
                tbody.appendChild(row);
            });
            
            // Load YTD summary
            if (data.data.ytd) {
                document.getElementById('ytd-income').textContent = 
                    `RM ${parseFloat(data.data.ytd.income || 0).toFixed(2)}`;
                document.getElementById('ytd-epf').textContent = 
                    `RM ${parseFloat(data.data.ytd.epf || 0).toFixed(2)}`;
                document.getElementById('ytd-socso').textContent = 
                    `RM ${parseFloat(data.data.ytd.socso || 0).toFixed(2)}`;
                document.getElementById('ytd-eis').textContent = 
                    `RM ${parseFloat(data.data.ytd.eis || 0).toFixed(2)}`;
                document.getElementById('ytd-pcb').textContent = 
                    `RM ${parseFloat(data.data.ytd.pcb || 0).toFixed(2)}`;
            }
        }
    } catch (error) {
        console.error('Error loading payroll data:', error);
        window.hrmsUtils.showNotification('Failed to load payroll data', 'error');
    }
}

async function loadEngagementsData() {
    try {
        // Load training courses
        const trainingResponse = await fetch('/api/training');
        const trainingData = await trainingResponse.json();
        
        if (trainingData.success && trainingData.data) {
            const tbody = document.getElementById('training-tbody');
            tbody.innerHTML = '';
            
            if (trainingData.data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">No training courses found</td></tr>';
            } else {
                trainingData.data.forEach(course => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${course.course_name}</td>
                        <td>${course.provider}</td>
                        <td>${window.hrmsUtils.formatDate(course.start_date)}</td>
                        <td>${window.hrmsUtils.formatDate(course.end_date)}</td>
                        <td><span class="status-badge status-${course.status}">${course.status}</span></td>
                        <td>${course.certificate ? '<a href="#">Download</a>' : '-'}</td>
                    `;
                    tbody.appendChild(row);
                });
            }
            
            // Update training stats
            const stats = trainingData.data.reduce((acc, course) => {
                acc[course.status] = (acc[course.status] || 0) + 1;
                return acc;
            }, {});
            document.getElementById('completed-training').textContent = stats.completed || 0;
            document.getElementById('inprogress-training').textContent = stats['in-progress'] || 0;
            document.getElementById('planned-training').textContent = stats.planned || 0;
        }
        
        // Load overseas trips
        const tripsResponse = await fetch('/api/trips');
        const tripsData = await tripsResponse.json();
        
        if (tripsData.success && tripsData.data) {
            const tbody = document.getElementById('trips-tbody');
            tbody.innerHTML = '';
            
            if (tripsData.data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">No trips found</td></tr>';
            } else {
                tripsData.data.forEach(trip => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${trip.destination}</td>
                        <td>${trip.purpose}</td>
                        <td>${window.hrmsUtils.formatDate(trip.start_date)}</td>
                        <td>${window.hrmsUtils.formatDate(trip.end_date)}</td>
                        <td>${trip.duration} days</td>
                        <td><span class="status-badge status-${trip.status}">${trip.status}</span></td>
                    `;
                    tbody.appendChild(row);
                });
            }
            
            // Update trip stats
            document.getElementById('total-trips').textContent = tripsData.data.length;
            const countries = new Set(tripsData.data.map(t => t.country));
            document.getElementById('countries-visited').textContent = countries.size;
            const totalDays = tripsData.data.reduce((sum, t) => sum + (t.duration || 0), 0);
            document.getElementById('days-abroad').textContent = totalDays;
        }
    } catch (error) {
        console.error('Error loading engagements data:', error);
        window.hrmsUtils.showNotification('Failed to load engagements data', 'error');
    }
}

// Check in/out functions
async function checkIn() {
    try {
        const response = await fetch('/api/attendance/check-in', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        
        if (data.success) {
            window.hrmsUtils.showNotification('Checked in successfully!', 'success');
            loadAttendanceData();
        } else {
            window.hrmsUtils.showNotification(data.message || 'Check-in failed', 'error');
        }
    } catch (error) {
        console.error('Error checking in:', error);
        window.hrmsUtils.showNotification('Check-in failed', 'error');
    }
}

async function checkOut() {
    try {
        const response = await fetch('/api/attendance/check-out', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        
        if (data.success) {
            window.hrmsUtils.showNotification('Checked out successfully!', 'success');
            loadAttendanceData();
        } else {
            window.hrmsUtils.showNotification(data.message || 'Check-out failed', 'error');
        }
    } catch (error) {
        console.error('Error checking out:', error);
        window.hrmsUtils.showNotification('Check-out failed', 'error');
    }
}

// Submit leave request
async function submitLeaveRequest(event) {
    event.preventDefault();
    
    const formData = {
        leave_type: document.getElementById('leave-type').value,
        start_date: document.getElementById('start-date').value,
        end_date: document.getElementById('end-date').value,
        reason: document.getElementById('leave-reason').value
    };
    
    try {
        const response = await fetch('/api/leave-request', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        const data = await response.json();
        
        if (data.success) {
            window.hrmsUtils.showNotification('Leave request submitted successfully!', 'success');
            document.getElementById('leave-modal').style.display = 'none';
            document.getElementById('leave-request-form').reset();
            loadLeaveData();
        } else {
            window.hrmsUtils.showNotification(data.message || 'Submission failed', 'error');
        }
    } catch (error) {
        console.error('Error submitting leave request:', error);
        window.hrmsUtils.showNotification('Submission failed', 'error');
    }
}

// Download payslip
async function downloadPayslip(payslipId) {
    try {
        window.location.href = `/api/payroll/payslip/${payslipId}/download`;
    } catch (error) {
        console.error('Error downloading payslip:', error);
        window.hrmsUtils.showNotification('Download failed', 'error');
    }
}

// Initialize event listeners when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Attach event listeners for attendance buttons if they exist
    const checkInBtn = document.getElementById('check-in-btn');
    const checkOutBtn = document.getElementById('check-out-btn');
    
    if (checkInBtn) checkInBtn.addEventListener('click', checkIn);
    if (checkOutBtn) checkOutBtn.addEventListener('click', checkOut);
    
    // Attach leave form submission handler
    const leaveForm = document.getElementById('leave-request-form');
    if (leaveForm) leaveForm.addEventListener('submit', submitLeaveRequest);
});
