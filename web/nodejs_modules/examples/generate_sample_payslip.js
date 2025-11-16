#!/usr/bin/env node
/**
 * Example: Generate a sample payslip
 * 
 * Usage: node examples/generate_sample_payslip.js
 */

const path = require('path');
const fs = require('fs');
const { generatePayslip } = require('../payslip_generator');

// Ensure tmp directory exists
const tmpDir = path.join(__dirname, '../../../tmp');
if (!fs.existsSync(tmpDir)) {
    fs.mkdirSync(tmpDir, { recursive: true });
}

// Sample payslip data
const sampleData = {
    employee_name: 'John Doe',
    employee_id: 'EMP001',
    department: 'Engineering',
    position: 'Senior Software Engineer',
    pay_period: 'November 2024',
    pay_date: '2024-11-30',
    basic_salary: 6000.00,
    allowances: 800.00,
    bonuses: 1500.00,
    epf_employee: 660.00,
    socso_employee: 39.25,
    eis: 7.90,
    pcb: 378.00,
    unpaid_leave_deduction: 0.00
};

const outputPath = path.join(tmpDir, 'sample_payslip.pdf');

console.log('Generating sample payslip...');
console.log('Employee:', sampleData.employee_name);
console.log('Period:', sampleData.pay_period);

generatePayslip(sampleData, outputPath)
    .then(() => {
        console.log('\n✅ Payslip generated successfully!');
        console.log('📄 Output:', outputPath);
        const gross = sampleData.basic_salary + sampleData.allowances + sampleData.bonuses;
        const deductions = sampleData.epf_employee + sampleData.socso_employee + sampleData.eis + sampleData.pcb;
        console.log('  NET PAY: RM', (gross - deductions).toFixed(2));
    })
    .catch((error) => {
        console.error('\n❌ Error:', error.message);
        process.exit(1);
    });
