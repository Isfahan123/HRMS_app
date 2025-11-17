/**
 * Leave Calendar Component for Web Interface
 * Provides visual calendar for leave management
 */

class LeaveCalendar {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.currentYear = new Date().getFullYear();
        this.currentMonth = new Date().getMonth() + 1;
        this.leaveRequests = [];
        this.holidays = [];
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
                // Extract just the dates from the holiday data
                this.holidays = data.data.map(h => h.date);
                this.holidayDetails = data.data; // Store full details for tooltip
            } else {
                // Fall back to sample data
                this.holidays = [
                    '2024-01-01', // New Year
                    '2024-02-10', // Chinese New Year
                    '2024-05-01', // Labour Day
                    '2024-08-31', // Merdeka Day
                    '2024-12-25'  // Christmas
                ];
            }
        } catch (error) {
            console.error('Error loading holidays:', error);
            // Fall back to sample data on error
            this.holidays = [
                '2024-01-01', '2024-02-10', '2024-05-01',
                '2024-08-31', '2024-12-25'
            ];
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
                content += '<div class="day-label">Holiday</div>';
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
}

// Global instance
let leaveCalendar;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Check if calendar container exists
    const calendarContainer = document.getElementById('leaveCalendar');
    if (calendarContainer) {
        leaveCalendar = new LeaveCalendar('leaveCalendar');
        leaveCalendar.init();
    }
});
