/**
 * Leave Calendar Component for Web Interface
 * Provides visual calendar for leave management with holiday CRUD
 */

class LeaveCalendar {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.currentYear = new Date().getFullYear();
        this.currentMonth = new Date().getMonth() + 1;
        this.leaveRequests = [];
        this.holidays = [];
        this.holidayDetails = []; // Full holiday data with names
    }

    /**
     * Initialize the calendar
     */
    async init() {
        await this.loadHolidays();
        await this.loadLeaveRequests();
        this.render();
    }

    /**
     * Load holidays from API
     */
    async loadHolidays() {
        try {
            const response = await fetch('/api/holidays');
            const data = await response.json();
            
            if (data.success && data.data) {
                // Store full holiday details for management
                this.holidayDetails = data.data;
                // Extract just the dates for quick lookup
                this.holidays = data.data.map(h => h.date);
            } else {
                // Fall back to sample data
                this.holidayDetails = [
                    {id: 1, date: '2024-01-01', name: 'New Year\'s Day', type: 'national'},
                    {id: 2, date: '2024-02-10', name: 'Chinese New Year', type: 'national'},
                    {id: 3, date: '2024-05-01', name: 'Labour Day', type: 'national'},
                    {id: 4, date: '2024-08-31', name: 'Merdeka Day', type: 'national'},
                    {id: 5, date: '2024-12-25', name: 'Christmas Day', type: 'national'}
                ];
                this.holidays = this.holidayDetails.map(h => h.date);
            }
        } catch (error) {
            console.error('Error loading holidays:', error);
            // Fall back to sample data on error
            this.holidayDetails = [
                {id: 1, date: '2024-01-01', name: 'New Year\'s Day', type: 'national'},
                {id: 2, date: '2024-05-01', name: 'Labour Day', type: 'national'}
            ];
            this.holidays = this.holidayDetails.map(h => h.date);
        }
    }

    /**
     * Load leave requests from API
     */
    async loadLeaveRequests() {
        try {
            const userEmail = sessionStorage.getItem('userEmail');
            if (!userEmail) {
                // For admin view, fetch all leave requests
                const response = await fetch('/api/admin/leave-requests');
                const data = await response.json();
                
                if (data.success) {
                    this.leaveRequests = data.data || [];
                }
                return;
            }

            const response = await fetch(`/api/leave-requests/${userEmail}`);
            const data = await response.json();
            
            if (data.success) {
                this.leaveRequests = data.data || [];
            }
        } catch (error) {
            console.error('Error loading leave requests:', error);
        }
    }

    /**
     * Check if a date is a weekend
     */
    isWeekend(date) {
        const day = date.getDay();
        return day === 0 || day === 6; // Sunday or Saturday
    }

    /**
     * Check if a date is a holiday
     */
    isHoliday(dateStr) {
        return this.holidays.includes(dateStr);
    }

    /**
     * Format date as YYYY-MM-DD
     */
    formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    /**
     * Get leave requests for a specific date
     */
    getLeavesForDate(dateStr) {
        return this.leaveRequests.filter(leave => {
            const start = new Date(leave.start_date);
            const end = new Date(leave.end_date);
            const date = new Date(dateStr);
            return date >= start && date <= end;
        });
    }

    /**
     * Navigate to previous month
     */
    previousMonth() {
        this.currentMonth--;
        if (this.currentMonth < 1) {
            this.currentMonth = 12;
            this.currentYear--;
        }
        this.render();
    }

    /**
     * Navigate to next month
     */
    nextMonth() {
        this.currentMonth++;
        if (this.currentMonth > 12) {
            this.currentMonth = 1;
            this.currentYear++;
        }
        this.render();
    }

    /**
     * Go to today's month
     */
    goToToday() {
        const today = new Date();
        this.currentYear = today.getFullYear();
        this.currentMonth = today.getMonth() + 1;
        this.render();
    }

    /**
     * Render the calendar
     */
    render() {
        if (!this.container) return;

        const monthNames = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ];

        const firstDay = new Date(this.currentYear, this.currentMonth - 1, 1);
        const lastDay = new Date(this.currentYear, this.currentMonth, 0);
        const today = new Date();
        const todayStr = this.formatDate(today);

        let html = `
            <div class="calendar-header">
                <button onclick="leaveCalendar.previousMonth()" class="btn-secondary">◀ Previous</button>
                <h3>${monthNames[this.currentMonth - 1]} ${this.currentYear}</h3>
                <button onclick="leaveCalendar.nextMonth()" class="btn-secondary">Next ▶</button>
                <button onclick="leaveCalendar.goToToday()" class="btn-secondary">Today</button>
                <button onclick="leaveCalendar.showAddHolidayModal()" class="btn-primary" style="margin-left: 20px;">➕ Add Holiday</button>
                <button onclick="leaveCalendar.showHolidayListModal()" class="btn-secondary">📋 Manage Holidays</button>
                <button onclick="leaveCalendar.showImportMalaysiaHolidaysModal()" class="btn-secondary btn-import-holidays">🇲🇾 Import Malaysia Holidays</button>
            </div>
            <table class="calendar-table">
                <thead>
                    <tr>
                        <th>Sun</th>
                        <th>Mon</th>
                        <th>Tue</th>
                        <th>Wed</th>
                        <th>Thu</th>
                        <th>Fri</th>
                        <th>Sat</th>
                    </tr>
                </thead>
                <tbody>
        `;

        // Add empty cells before first day
        const startDayOfWeek = firstDay.getDay();
        let currentWeek = '<tr>';
        
        for (let i = 0; i < startDayOfWeek; i++) {
            currentWeek += '<td class="calendar-day empty"></td>';
        }

        // Add all days of the month
        for (let day = 1; day <= lastDay.getDate(); day++) {
            const date = new Date(this.currentYear, this.currentMonth - 1, day);
            const dateStr = this.formatDate(date);
            const dayOfWeek = date.getDay();
            
            let classes = ['calendar-day'];
            let content = `<div class="day-number">${day}</div>`;
            
            // Check if today
            if (dateStr === todayStr) {
                classes.push('today');
            }
            
            // Check if weekend
            if (this.isWeekend(date)) {
                classes.push('weekend');
            }
            
            // Check if holiday
            if (this.isHoliday(dateStr)) {
                classes.push('holiday');
                const holidayInfo = this.getHolidayForDate(dateStr);
                const holidayName = holidayInfo ? holidayInfo.name : 'Holiday';
                content += `<div class="day-label" title="${holidayName}">🏖️ ${holidayName}</div>`;
            }
            
            // Check for leave requests
            const leaves = this.getLeavesForDate(dateStr);
            if (leaves.length > 0) {
                classes.push('has-leave');
                leaves.forEach(leave => {
                    const statusClass = leave.status || 'pending';
                    content += `<div class="leave-indicator ${statusClass}" title="${leave.leave_type} - ${leave.status}">${leave.leave_type}</div>`;
                });
            }
            
            currentWeek += `<td class="${classes.join(' ')}">${content}</td>`;
            
            // Start new row on Sunday
            if (dayOfWeek === 6) {
                currentWeek += '</tr>';
                html += currentWeek;
                currentWeek = '<tr>';
            }
        }

        // Fill remaining cells
        const endDayOfWeek = lastDay.getDay();
        for (let i = endDayOfWeek + 1; i < 7; i++) {
            currentWeek += '<td class="calendar-day empty"></td>';
        }
        currentWeek += '</tr>';
        html += currentWeek;

        html += `
                </tbody>
            </table>
            <div class="calendar-legend">
                <div class="legend-item">
                    <span class="legend-color today"></span> Today
                </div>
                <div class="legend-item">
                    <span class="legend-color weekend"></span> Weekend
                </div>
                <div class="legend-item">
                    <span class="legend-color holiday"></span> Holiday
                </div>
                <div class="legend-item">
                    <span class="legend-color approved"></span> Approved Leave
                </div>
                <div class="legend-item">
                    <span class="legend-color pending"></span> Pending Leave
                </div>
            </div>
        `;

        this.container.innerHTML = html;
    }

    /**
     * Count working days between two dates
     */
    countWorkingDays(startDate, endDate) {
        let count = 0;
        const start = new Date(startDate);
        const end = new Date(endDate);
        
        for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
            const dateStr = this.formatDate(d);
            if (!this.isWeekend(d) && !this.isHoliday(dateStr)) {
                count++;
            }
        }
        
        return count;
    }

    /**
     * Show add holiday modal
     */
    showAddHolidayModal() {
        document.getElementById('holidayModalTitle').textContent = '➕ Add Holiday';
        document.getElementById('holidayId').value = '';
        document.getElementById('holidayDate').value = '';
        document.getElementById('holidayName').value = '';
        document.getElementById('holidayType').value = 'national';
        document.getElementById('holidayState').value = '';
        document.getElementById('holidayObservance').checked = false;
        document.getElementById('holidayModal').style.display = 'block';
    }

    /**
     * Show edit holiday modal
     */
    showEditHolidayModal(holidayId) {
        const holiday = this.holidayDetails.find(h => h.id === holidayId);
        if (!holiday) return;

        document.getElementById('holidayModalTitle').textContent = '✏️ Edit Holiday';
        document.getElementById('holidayId').value = holiday.id;
        document.getElementById('holidayDate').value = holiday.date;
        document.getElementById('holidayName').value = holiday.name || '';
        document.getElementById('holidayType').value = holiday.type || 'national';
        document.getElementById('holidayState').value = holiday.state || '';
        document.getElementById('holidayObservance').checked = holiday.is_observance || false;
        document.getElementById('holidayModal').style.display = 'block';
    }

    /**
     * Close holiday modal
     */
    closeHolidayModal() {
        document.getElementById('holidayModal').style.display = 'none';
    }

    /**
     * Save holiday (add or update)
     */
    async saveHoliday() {
        const holidayId = document.getElementById('holidayId').value;
        const date = document.getElementById('holidayDate').value;
        const name = document.getElementById('holidayName').value;
        const type = document.getElementById('holidayType').value;
        const state = document.getElementById('holidayState').value;
        const isObservance = document.getElementById('holidayObservance').checked;

        if (!date || !name) {
            alert('❌ Please fill in all required fields (Date and Name)');
            return;
        }

        const holidayData = {
            date: date,
            name: name,
            type: type,
            state: state || null,
            is_observance: isObservance
        };

        try {
            let response;
            if (holidayId) {
                // Update existing holiday
                response = await fetch(`/api/holidays/${holidayId}`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(holidayData)
                });
            } else {
                // Create new holiday
                response = await fetch('/api/holidays', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(holidayData)
                });
            }

            const data = await response.json();
            
            if (data.success) {
                alert(`✅ Holiday ${holidayId ? 'updated' : 'added'} successfully!`);
                this.closeHolidayModal();
                await this.loadHolidays();
                this.render();
            } else {
                alert(`❌ Error: ${data.message || 'Failed to save holiday'}`);
            }
        } catch (error) {
            console.error('Error saving holiday:', error);
            alert('❌ Error saving holiday. Please try again.');
        }
    }

    /**
     * Delete holiday
     */
    async deleteHoliday(holidayId) {
        if (!confirm('🗑️ Are you sure you want to delete this holiday?')) {
            return;
        }

        try {
            const response = await fetch(`/api/holidays/${holidayId}`, {
                method: 'DELETE'
            });

            const data = await response.json();
            
            if (data.success) {
                alert('✅ Holiday deleted successfully!');
                await this.loadHolidays();
                this.render();
                // Close holiday list modal if open
                const listModal = document.getElementById('holidayListModal');
                if (listModal && listModal.style.display === 'block') {
                    this.showHolidayListModal(); // Refresh the list
                }
            } else {
                alert(`❌ Error: ${data.message || 'Failed to delete holiday'}`);
            }
        } catch (error) {
            console.error('Error deleting holiday:', error);
            alert('❌ Error deleting holiday. Please try again.');
        }
    }

    /**
     * Show holiday list modal
     */
    showHolidayListModal() {
        const modal = document.getElementById('holidayListModal');
        const tbody = modal.querySelector('tbody');
        
        // Sort holidays by date
        const sortedHolidays = [...this.holidayDetails].sort((a, b) => 
            new Date(a.date) - new Date(b.date)
        );

        // Generate table rows
        let rows = '';
        sortedHolidays.forEach(holiday => {
            const dateObj = new Date(holiday.date);
            const formattedDate = dateObj.toLocaleDateString('en-MY', {
                year: 'numeric', month: 'short', day: 'numeric'
            });
            const typeBadge = holiday.type === 'national' ? '🇲🇾 National' : 
                             holiday.type === 'state' ? '📍 State' : 
                             '📅 ' + (holiday.type || 'Other');
            const observanceBadge = holiday.is_observance ? '👁️ Observance' : '';
            const stateName = holiday.state ? `(${holiday.state})` : '';

            rows += `
                <tr>
                    <td>${formattedDate}</td>
                    <td><strong>${holiday.name}</strong></td>
                    <td>${typeBadge} ${stateName}</td>
                    <td>${observanceBadge}</td>
                    <td>
                        <button onclick="leaveCalendar.showEditHolidayModal(${holiday.id})" class="btn-sm" style="background: #667eea; color: white; margin-right: 5px;">✏️ Edit</button>
                        <button onclick="leaveCalendar.deleteHoliday(${holiday.id})" class="btn-sm" style="background: #dc3545; color: white;">🗑️ Delete</button>
                    </td>
                </tr>
            `;
        });

        tbody.innerHTML = rows || '<tr><td colspan="5" style="text-align: center; color: #666;">No holidays found</td></tr>';
        modal.style.display = 'block';
    }

    /**
     * Close holiday list modal
     */
    closeHolidayListModal() {
        document.getElementById('holidayListModal').style.display = 'none';
    }

    /**
     * Get holiday details for a specific date
     */
    getHolidayForDate(dateStr) {
        return this.holidayDetails.find(h => h.date === dateStr);
    }

    /**
     * Show import Malaysia holidays modal
     */
    showImportMalaysiaHolidaysModal() {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.style.display = 'block';
        
        const states = [
            'All Malaysia',
            'Johor', 'Kedah', 'Kelantan', 'Kuala Lumpur',
            'Labuan', 'Malacca', 'Negeri Sembilan', 'Pahang',
            'Penang', 'Perak', 'Perlis', 'Putrajaya',
            'Sabah', 'Sarawak', 'Selangor', 'Terengganu'
        ];
        
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 500px;">
                <span class="close" onclick="this.parentElement.parentElement.remove()">&times;</span>
                <h2>🇲🇾 Import Malaysia Public Holidays</h2>
                <p style="color: #666; margin-bottom: 20px;">
                    Automatically import official Malaysia public holidays from the python-holidays library.
                    Existing holidays will not be duplicated.
                </p>
                <form id="importMalaysiaHolidaysForm" style="text-align: left;">
                    <div class="form-group">
                        <label for="importYear">Year:</label>
                        <input type="number" id="importYear" min="2020" max="2030" value="${this.currentYear}" required style="width: 100%; padding: 8px;">
                    </div>
                    <div class="form-group">
                        <label for="importState">State/Region:</label>
                        <select id="importState" style="width: 100%; padding: 8px;">
                            ${states.map(state => `<option value="${state}">${state}</option>`).join('')}
                        </select>
                        <small style="color: #666; display: block; margin-top: 5px;">
                            Select "All Malaysia" for national holidays only, or choose a specific state to include state-specific holidays.
                        </small>
                    </div>
                    <div style="margin-top: 20px; display: flex; gap: 10px;">
                        <button type="submit" class="btn-primary">Import Holidays</button>
                        <button type="button" class="btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
                    </div>
                    <div id="importMessage" style="margin-top: 15px; display: none;"></div>
                </form>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Handle form submission
        document.getElementById('importMalaysiaHolidaysForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const year = parseInt(document.getElementById('importYear').value);
            const state = document.getElementById('importState').value;
            const messageDiv = document.getElementById('importMessage');
            
            try {
                messageDiv.style.display = 'block';
                messageDiv.className = 'info-message';
                messageDiv.textContent = 'Importing holidays...';
                
                const response = await fetch(`/api/holidays/import-malaysia?year=${year}&state=${encodeURIComponent(state)}`, {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    messageDiv.className = 'success-message';
                    messageDiv.textContent = data.message;
                    
                    // Reload holidays and re-render calendar
                    await this.loadHolidays();
                    this.render();
                    
                    // Close modal after 2 seconds
                    setTimeout(() => {
                        modal.remove();
                    }, 2000);
                } else {
                    messageDiv.className = 'error-message';
                    messageDiv.textContent = data.message || 'Failed to import holidays';
                }
            } catch (error) {
                messageDiv.style.display = 'block';
                messageDiv.className = 'error-message';
                messageDiv.textContent = 'Error importing holidays: ' + error.message;
                console.error('Error:', error);
            }
        });
    }
}

// Global instance
let leaveCalendar;

// Initialize leave calendar
function initLeaveCalendar() {
    const calendarContainer = document.getElementById('leaveCalendar');
    if (calendarContainer) {
        console.log('Initializing Leave Calendar...');
        leaveCalendar = new LeaveCalendar('leaveCalendar');
        leaveCalendar.init();
    } else {
        console.warn('Calendar container not found, scheduling retry...');
        setTimeout(initLeaveCalendar, 100);
    }
}

// Initialize immediately since script loads at bottom of page
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLeaveCalendar);
} else {
    // DOM already loaded
    initLeaveCalendar();
}
