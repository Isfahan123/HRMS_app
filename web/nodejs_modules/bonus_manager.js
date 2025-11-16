/**
 * Node.js alternative to Python's bonus_management_dialog.py
 * Provides bonus management utilities
 */

const { v4: uuidv4 } = require('crypto');

/**
 * Bonus types
 */
const BONUS_TYPES = {
    PERFORMANCE: 'Performance Bonus',
    ANNUAL: 'Annual Bonus',
    FESTIVE: 'Festive Bonus',
    PROJECT: 'Project Completion Bonus',
    ATTENDANCE: 'Perfect Attendance Bonus',
    OTHER: 'Other'
};

/**
 * Bonus status
 */
const BONUS_STATUS = {
    PENDING: 'pending',
    APPROVED: 'approved',
    PAID: 'paid',
    CANCELLED: 'cancelled'
};

/**
 * Create a new bonus record
 * @param {Object} bonusData - Bonus information
 * @returns {Object} - Formatted bonus record
 */
function createBonusRecord(bonusData) {
    const {
        employeeId,
        employeeName,
        bonusType,
        amount,
        description,
        payPeriod,
        approvedBy = null
    } = bonusData;
    
    // Validate required fields
    if (!employeeId || !amount || amount <= 0) {
        throw new Error('Invalid bonus data: employee ID and amount are required');
    }
    
    return {
        id: generateBonusId(),
        employee_id: employeeId,
        employee_name: employeeName,
        bonus_type: bonusType || BONUS_TYPES.OTHER,
        amount: parseFloat(amount),
        description: description || '',
        pay_period: payPeriod,
        status: BONUS_STATUS.PENDING,
        approved_by: approvedBy,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
    };
}

/**
 * Generate unique bonus ID
 * @returns {string} - Unique bonus ID
 */
function generateBonusId() {
    // Use crypto.randomUUID if available, otherwise use timestamp + random
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        return crypto.randomUUID();
    }
    return `bonus_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Calculate total bonus amount for employee
 * @param {Array<Object>} bonuses - Array of bonus records
 * @param {string} status - Filter by status (optional)
 * @returns {number} - Total bonus amount
 */
function calculateTotalBonus(bonuses, status = null) {
    return bonuses
        .filter(bonus => !status || bonus.status === status)
        .reduce((total, bonus) => total + parseFloat(bonus.amount || 0), 0);
}

/**
 * Validate bonus amount
 * @param {number} amount - Bonus amount
 * @param {number} basicSalary - Employee basic salary
 * @param {number} maxPercentage - Max percentage of basic salary (default 100%)
 * @returns {Object} - Validation result
 */
function validateBonusAmount(amount, basicSalary, maxPercentage = 100) {
    const errors = [];
    
    if (amount <= 0) {
        errors.push('Bonus amount must be greater than zero');
    }
    
    const maxAmount = (basicSalary * maxPercentage) / 100;
    if (amount > maxAmount) {
        errors.push(`Bonus amount cannot exceed ${maxPercentage}% of basic salary (RM ${maxAmount.toFixed(2)})`);
    }
    
    return {
        valid: errors.length === 0,
        errors,
        maxAmount
    };
}

/**
 * Format bonus record for display
 * @param {Object} bonus - Bonus record
 * @returns {Object} - Formatted bonus for display
 */
function formatBonusForDisplay(bonus) {
    return {
        id: bonus.id,
        employeeId: bonus.employee_id,
        employeeName: bonus.employee_name,
        type: bonus.bonus_type,
        amount: `RM ${parseFloat(bonus.amount).toFixed(2)}`,
        description: bonus.description,
        payPeriod: bonus.pay_period,
        status: bonus.status,
        statusBadge: getBonusStatusBadge(bonus.status),
        approvedBy: bonus.approved_by || '-',
        createdAt: new Date(bonus.created_at).toLocaleDateString('en-MY'),
        updatedAt: new Date(bonus.updated_at).toLocaleDateString('en-MY')
    };
}

/**
 * Get status badge HTML class
 * @param {string} status - Bonus status
 * @returns {string} - CSS class for badge
 */
function getBonusStatusBadge(status) {
    const badges = {
        [BONUS_STATUS.PENDING]: 'warning',
        [BONUS_STATUS.APPROVED]: 'success',
        [BONUS_STATUS.PAID]: 'info',
        [BONUS_STATUS.CANCELLED]: 'danger'
    };
    return badges[status] || 'secondary';
}

/**
 * Calculate variable percentage bonus
 * @param {number} basicSalary - Employee basic salary
 * @param {number} percentage - Bonus percentage
 * @returns {number} - Calculated bonus amount
 */
function calculateVariableBonus(basicSalary, percentage) {
    return Math.round((basicSalary * percentage / 100) * 100) / 100;
}

/**
 * Get bonus summary for period
 * @param {Array<Object>} bonuses - Array of bonus records
 * @param {string} payPeriod - Pay period filter (optional)
 * @returns {Object} - Bonus summary
 */
function getBonusSummary(bonuses, payPeriod = null) {
    const filteredBonuses = payPeriod 
        ? bonuses.filter(b => b.pay_period === payPeriod)
        : bonuses;
    
    const byStatus = {
        pending: filteredBonuses.filter(b => b.status === BONUS_STATUS.PENDING),
        approved: filteredBonuses.filter(b => b.status === BONUS_STATUS.APPROVED),
        paid: filteredBonuses.filter(b => b.status === BONUS_STATUS.PAID),
        cancelled: filteredBonuses.filter(b => b.status === BONUS_STATUS.CANCELLED)
    };
    
    return {
        total: filteredBonuses.length,
        totalAmount: calculateTotalBonus(filteredBonuses),
        byStatus: {
            pending: {
                count: byStatus.pending.length,
                amount: calculateTotalBonus(byStatus.pending)
            },
            approved: {
                count: byStatus.approved.length,
                amount: calculateTotalBonus(byStatus.approved)
            },
            paid: {
                count: byStatus.paid.length,
                amount: calculateTotalBonus(byStatus.paid)
            },
            cancelled: {
                count: byStatus.cancelled.length,
                amount: calculateTotalBonus(byStatus.cancelled)
            }
        }
    };
}

/**
 * Group bonuses by employee
 * @param {Array<Object>} bonuses - Array of bonus records
 * @returns {Object} - Bonuses grouped by employee ID
 */
function groupBonusesByEmployee(bonuses) {
    return bonuses.reduce((acc, bonus) => {
        const empId = bonus.employee_id;
        if (!acc[empId]) {
            acc[empId] = {
                employee_id: empId,
                employee_name: bonus.employee_name,
                bonuses: [],
                totalAmount: 0
            };
        }
        acc[empId].bonuses.push(bonus);
        acc[empId].totalAmount += parseFloat(bonus.amount || 0);
        return acc;
    }, {});
}

module.exports = {
    BONUS_TYPES,
    BONUS_STATUS,
    createBonusRecord,
    generateBonusId,
    calculateTotalBonus,
    validateBonusAmount,
    formatBonusForDisplay,
    getBonusStatusBadge,
    calculateVariableBonus,
    getBonusSummary,
    groupBonusesByEmployee
};
