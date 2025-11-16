/**
 * HRMS Node.js Modules - Main Entry Point
 * 
 * This module provides Node.js alternatives for Python GUI functionality
 * that hasn't been implemented in the HTML/JavaScript web interface yet.
 */

const payslipGenerator = require('./payslip_generator');
const leaveCalendar = require('./leave_calendar');
const bonusManager = require('./bonus_manager');

module.exports = {
    // Payslip generation
    payslip: payslipGenerator,
    
    // Leave calendar utilities
    calendar: leaveCalendar,
    
    // Bonus management
    bonus: bonusManager
};

// Example usage documentation
if (require.main === module) {
    console.log('HRMS Node.js Modules');
    console.log('====================');
    console.log('');
    console.log('Available modules:');
    console.log('1. Payslip Generator - Generate PDF payslips');
    console.log('2. Leave Calendar - Calendar utilities for leave management');
    console.log('3. Bonus Manager - Bonus management utilities');
    console.log('');
    console.log('Usage:');
    console.log('  const hrms = require("./web/nodejs_modules");');
    console.log('  await hrms.payslip.generatePayslip(data, outputPath);');
    console.log('  const workingDays = hrms.calendar.countWorkingDays(start, end);');
    console.log('  const bonus = hrms.bonus.createBonusRecord(bonusData);');
    console.log('');
    console.log('For detailed documentation, see individual module files.');
}
