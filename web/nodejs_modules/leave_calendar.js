/**
 * Node.js alternative to Python's leave_calendar.py
 * Provides calendar utilities for leave management
 */

const { format, isWeekend, parseISO, eachDayOfInterval } = require('date-fns');

/**
 * Check if a date is a weekend (Saturday or Sunday)
 * @param {Date|string} date - Date to check
 * @returns {boolean} - True if weekend
 */
function isWeekendDay(date) {
    const d = typeof date === 'string' ? parseISO(date) : date;
    return isWeekend(d);
}

/**
 * Check if a date should deduct leave
 * Returns true for working days, false for weekends/holidays
 * @param {Date|string} checkDate - Date to check
 * @param {Array<string>} holidays - Array of holiday dates (YYYY-MM-DD)
 * @returns {boolean} - True if date should be deducted
 */
function isLeaveDeductible(checkDate, holidays = []) {
    const date = typeof checkDate === 'string' ? parseISO(checkDate) : checkDate;
    const dateStr = format(date, 'yyyy-MM-dd');
    
    // Weekends are not deductible
    if (isWeekendDay(date)) {
        return false;
    }
    
    // Holidays are not deductible
    if (holidays.includes(dateStr)) {
        return false;
    }
    
    return true;
}

/**
 * Count working days between two dates
 * @param {Date|string} startDate - Start date
 * @param {Date|string} endDate - End date
 * @param {Array<string>} holidays - Array of holiday dates (YYYY-MM-DD)
 * @returns {number} - Number of working days
 */
function countWorkingDays(startDate, endDate, holidays = []) {
    const start = typeof startDate === 'string' ? parseISO(startDate) : startDate;
    const end = typeof endDate === 'string' ? parseISO(endDate) : endDate;
    
    const days = eachDayOfInterval({ start, end });
    
    return days.filter(day => isLeaveDeductible(day, holidays)).length;
}

/**
 * Get all dates in a leave period
 * @param {Date|string} startDate - Start date
 * @param {Date|string} endDate - End date
 * @returns {Array<string>} - Array of date strings (YYYY-MM-DD)
 */
function getLeavePeriodDates(startDate, endDate) {
    const start = typeof startDate === 'string' ? parseISO(startDate) : startDate;
    const end = typeof endDate === 'string' ? parseISO(endDate) : endDate;
    
    const days = eachDayOfInterval({ start, end });
    return days.map(day => format(day, 'yyyy-MM-dd'));
}

/**
 * Calculate leave balance
 * @param {number} totalLeave - Total leave entitlement
 * @param {number} usedLeave - Already used leave
 * @param {number} pendingLeave - Pending leave requests
 * @returns {Object} - Balance information
 */
function calculateLeaveBalance(totalLeave, usedLeave, pendingLeave) {
    const available = totalLeave - usedLeave - pendingLeave;
    const remaining = totalLeave - usedLeave;
    
    return {
        total: totalLeave,
        used: usedLeave,
        pending: pendingLeave,
        available: Math.max(0, available),
        remaining: Math.max(0, remaining)
    };
}

/**
 * Validate leave request dates
 * @param {Date|string} startDate - Start date
 * @param {Date|string} endDate - End date
 * @returns {Object} - Validation result
 */
function validateLeaveRequest(startDate, endDate) {
    const start = typeof startDate === 'string' ? parseISO(startDate) : startDate;
    const end = typeof endDate === 'string' ? parseISO(endDate) : endDate;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const errors = [];
    
    if (start > end) {
        errors.push('Start date must be before or equal to end date');
    }
    
    if (start < today) {
        errors.push('Cannot request leave for past dates');
    }
    
    return {
        valid: errors.length === 0,
        errors
    };
}

/**
 * Get calendar data for a month
 * @param {number} year - Year
 * @param {number} month - Month (1-12)
 * @param {Array<Object>} leaveRequests - Leave requests for the month
 * @param {Array<string>} holidays - Holiday dates
 * @returns {Object} - Calendar data
 */
function getMonthCalendar(year, month, leaveRequests = [], holidays = []) {
    const firstDay = new Date(year, month - 1, 1);
    const lastDay = new Date(year, month, 0);
    
    const weeks = [];
    let currentWeek = [];
    
    // Fill in the days before the first day of month
    const startDayOfWeek = firstDay.getDay(); // 0 = Sunday
    for (let i = 0; i < startDayOfWeek; i++) {
        currentWeek.push(null);
    }
    
    // Fill in all days of the month
    for (let day = 1; day <= lastDay.getDate(); day++) {
        const date = new Date(year, month - 1, day);
        const dateStr = format(date, 'yyyy-MM-dd');
        
        const dayData = {
            date: dateStr,
            day: day,
            isWeekend: isWeekendDay(date),
            isHoliday: holidays.includes(dateStr),
            leaveRequests: leaveRequests.filter(req => {
                const reqStart = parseISO(req.start_date);
                const reqEnd = parseISO(req.end_date);
                return date >= reqStart && date <= reqEnd;
            })
        };
        
        currentWeek.push(dayData);
        
        // Start new week on Sunday
        if (date.getDay() === 6) {
            weeks.push(currentWeek);
            currentWeek = [];
        }
    }
    
    // Fill in remaining days
    if (currentWeek.length > 0) {
        while (currentWeek.length < 7) {
            currentWeek.push(null);
        }
        weeks.push(currentWeek);
    }
    
    return {
        year,
        month,
        monthName: format(firstDay, 'MMMM'),
        weeks
    };
}

module.exports = {
    isWeekendDay,
    isLeaveDeductible,
    countWorkingDays,
    getLeavePeriodDates,
    calculateLeaveBalance,
    validateLeaveRequest,
    getMonthCalendar
};
