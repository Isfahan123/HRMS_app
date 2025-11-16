/**
 * Node.js alternative to Python's payslip_generator.py
 * Generates PDF payslips using PDFKit
 */

const PDFDocument = require('pdfkit');
const fs = require('fs');
const axios = require('axios');

// Company details
const LOGO_URL = "https://enigmatechnicalsolutions.com/wp-content/uploads/2024/07/cropped-enigma512px-300x300-1.png";
const COMPANY_NAME = "ENIGMA TECHNICAL SOLUTIONS SDN BHD";
const SSM_NO = "002628025-K";
const COMPANY_ADDRESS_LINES = [
    "",
    "",
    "",
    "",
    "",
    "",
    "56 & 57, Persiaran Venice Sutera 1, Desa Manjung Raya",
    "",
    "32200 Lumut, Perak, Malaysia",
    "",
    "Tel: +60-3-4131 9114 | Email: info@enigmatechnical.com"
];

/**
 * Format number as money
 */
function formatMoney(value) {
    return parseFloat(value).toLocaleString('en-MY', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

/**
 * Convert number to words (Ringgit)
 */
function numberToWords(amount) {
    const ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine'];
    const tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'];
    const teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen'];
    
    function convertLessThanThousand(num) {
        if (num === 0) return '';
        
        let result = '';
        
        if (num >= 100) {
            result += ones[Math.floor(num / 100)] + ' Hundred ';
            num %= 100;
        }
        
        if (num >= 20) {
            result += tens[Math.floor(num / 10)] + ' ';
            num %= 10;
        } else if (num >= 10) {
            result += teens[num - 10] + ' ';
            return result;
        }
        
        if (num > 0) {
            result += ones[num] + ' ';
        }
        
        return result;
    }
    
    let whole = Math.floor(amount);
    const cents = Math.round((amount - whole) * 100);
    
    if (whole === 0 && cents === 0) {
        return 'Zero Ringgit Only';
    }
    
    let result = '';
    
    if (whole >= 1000000) {
        result += convertLessThanThousand(Math.floor(whole / 1000000)) + 'Million ';
        whole %= 1000000;
    }
    
    if (whole >= 1000) {
        result += convertLessThanThousand(Math.floor(whole / 1000)) + 'Thousand ';
        whole %= 1000;
    }
    
    result += convertLessThanThousand(whole);
    result += 'Ringgit';
    
    if (cents > 0) {
        result += ' ' + convertLessThanThousand(cents) + 'Sen';
    }
    
    return result.trim() + ' Only';
}

/**
 * Calculate PCB (estimated)
 */
function calculatePCB(grossSalary, epfEmp) {
    const taxable = Math.max(0, grossSalary - epfEmp);
    
    if (taxable < 3000) return 0;
    if (taxable < 5000) return Math.round(taxable * 0.03 * 100) / 100;
    if (taxable < 8000) return Math.round(taxable * 0.07 * 100) / 100;
    return Math.round(taxable * 0.10 * 100) / 100;
}

/**
 * Download company logo
 */
async function downloadLogo(url) {
    try {
        const response = await axios.get(url, { responseType: 'arraybuffer' });
        return Buffer.from(response.data);
    } catch (error) {
        console.warn('Warning: logo download failed:', error.message);
        return null;
    }
}

/**
 * Generate payslip PDF
 * @param {Object} data - Employee and payroll data
 * @param {string} outputPath - Output file path
 * @returns {Promise<string>} - Path to generated PDF
 */
async function generatePayslip(data, outputPath) {
    return new Promise(async (resolve, reject) => {
        try {
            // Create a document
            const doc = new PDFDocument({ size: 'A4', margin: 50 });
            
            // Pipe to file or memory
            const stream = fs.createWriteStream(outputPath);
            doc.pipe(stream);
            
            // Try to download and add logo
            const logoBuffer = await downloadLogo(LOGO_URL);
            if (logoBuffer) {
                try {
                    doc.image(logoBuffer, 50, 45, { width: 60 });
                } catch (e) {
                    console.warn('Could not add logo:', e.message);
                }
            }
            
            // Company header
            doc.fontSize(16).font('Helvetica-Bold')
               .text(COMPANY_NAME, 120, 50, { width: 400 });
            doc.fontSize(8).font('Helvetica')
               .text(`(${SSM_NO})`, 120, 70);
            
            // Company address
            let y = 80;
            COMPANY_ADDRESS_LINES.forEach(line => {
                if (line.trim()) {
                    doc.fontSize(8).text(line, 120, y);
                }
                y += 10;
            });
            
            // Title
            doc.fontSize(18).font('Helvetica-Bold')
               .text('PAYSLIP', 50, 200, { align: 'center', width: 500 });
            
            // Employee information
            y = 240;
            doc.fontSize(10).font('Helvetica');
            doc.text(`Employee Name: ${data.employee_name || '-'}`, 50, y);
            doc.text(`Employee ID: ${data.employee_id || '-'}`, 350, y);
            y += 20;
            doc.text(`Department: ${data.department || '-'}`, 50, y);
            doc.text(`Position: ${data.position || '-'}`, 350, y);
            y += 20;
            doc.text(`Pay Period: ${data.pay_period || '-'}`, 50, y);
            doc.text(`Pay Date: ${data.pay_date || '-'}`, 350, y);
            
            // Line separator
            y += 30;
            doc.moveTo(50, y).lineTo(550, y).stroke();
            
            // Earnings section
            y += 20;
            doc.fontSize(12).font('Helvetica-Bold').text('EARNINGS', 50, y);
            y += 20;
            
            doc.fontSize(10).font('Helvetica');
            const basicSalary = parseFloat(data.basic_salary || 0);
            const allowances = parseFloat(data.allowances || 0);
            const bonuses = parseFloat(data.bonuses || 0);
            const grossSalary = basicSalary + allowances + bonuses;
            
            doc.text('Basic Salary', 50, y);
            doc.text(`RM ${formatMoney(basicSalary)}`, 400, y, { align: 'right', width: 150 });
            y += 15;
            
            if (allowances > 0) {
                doc.text('Allowances', 50, y);
                doc.text(`RM ${formatMoney(allowances)}`, 400, y, { align: 'right', width: 150 });
                y += 15;
            }
            
            if (bonuses > 0) {
                doc.text('Bonuses', 50, y);
                doc.text(`RM ${formatMoney(bonuses)}`, 400, y, { align: 'right', width: 150 });
                y += 15;
            }
            
            y += 5;
            doc.moveTo(50, y).lineTo(550, y).stroke();
            y += 15;
            
            doc.font('Helvetica-Bold').text('Gross Salary', 50, y);
            doc.text(`RM ${formatMoney(grossSalary)}`, 400, y, { align: 'right', width: 150 });
            
            // Deductions section
            y += 30;
            doc.fontSize(12).text('DEDUCTIONS', 50, y);
            y += 20;
            
            doc.fontSize(10).font('Helvetica');
            const epfEmp = parseFloat(data.epf_employee || 0);
            const socsoEmp = parseFloat(data.socso_employee || 0);
            const eis = parseFloat(data.eis || 0);
            const pcb = parseFloat(data.pcb || calculatePCB(grossSalary, epfEmp));
            const unpaidLeave = parseFloat(data.unpaid_leave_deduction || 0);
            const totalDeductions = epfEmp + socsoEmp + eis + pcb + unpaidLeave;
            
            doc.text('EPF (Employee)', 50, y);
            doc.text(`RM ${formatMoney(epfEmp)}`, 400, y, { align: 'right', width: 150 });
            y += 15;
            
            doc.text('SOCSO (Employee)', 50, y);
            doc.text(`RM ${formatMoney(socsoEmp)}`, 400, y, { align: 'right', width: 150 });
            y += 15;
            
            doc.text('EIS', 50, y);
            doc.text(`RM ${formatMoney(eis)}`, 400, y, { align: 'right', width: 150 });
            y += 15;
            
            doc.text('PCB (Tax)', 50, y);
            doc.text(`RM ${formatMoney(pcb)}`, 400, y, { align: 'right', width: 150 });
            y += 15;
            
            if (unpaidLeave > 0) {
                doc.text('Unpaid Leave', 50, y);
                doc.text(`RM ${formatMoney(unpaidLeave)}`, 400, y, { align: 'right', width: 150 });
                y += 15;
            }
            
            y += 5;
            doc.moveTo(50, y).lineTo(550, y).stroke();
            y += 15;
            
            doc.font('Helvetica-Bold').text('Total Deductions', 50, y);
            doc.text(`RM ${formatMoney(totalDeductions)}`, 400, y, { align: 'right', width: 150 });
            
            // Net pay
            y += 30;
            const netPay = grossSalary - totalDeductions;
            doc.fontSize(14).text('NET PAY', 50, y);
            doc.text(`RM ${formatMoney(netPay)}`, 400, y, { align: 'right', width: 150 });
            
            // Amount in words
            y += 25;
            doc.fontSize(9).font('Helvetica-Oblique')
               .text(`(${numberToWords(netPay)})`, 50, y, { width: 500 });
            
            // Footer
            y += 40;
            doc.fontSize(8).font('Helvetica')
               .text('This is a computer-generated payslip and does not require a signature.', 50, y, {
                   align: 'center',
                   width: 500
               });
            
            // Finalize PDF
            doc.end();
            
            stream.on('finish', () => {
                resolve(outputPath);
            });
            
            stream.on('error', (error) => {
                reject(error);
            });
            
        } catch (error) {
            reject(error);
        }
    });
}

/**
 * Generate payslip for employee
 * @param {Object} employeeData - Employee data from database
 * @param {Object} payrollData - Payroll run data
 * @param {string} outputPath - Output file path
 * @returns {Promise<string>} - Path to generated PDF
 */
async function generatePayslipForEmployee(employeeData, payrollData, outputPath) {
    const data = {
        employee_name: employeeData.full_name,
        employee_id: employeeData.employee_id,
        department: employeeData.department,
        position: employeeData.position,
        pay_period: payrollData.pay_period,
        pay_date: payrollData.pay_date,
        basic_salary: payrollData.basic_salary,
        allowances: payrollData.allowances,
        bonuses: payrollData.bonuses,
        epf_employee: payrollData.epf_employee,
        socso_employee: payrollData.socso_employee,
        eis: payrollData.eis,
        pcb: payrollData.pcb,
        unpaid_leave_deduction: payrollData.unpaid_leave_deduction
    };
    
    return generatePayslip(data, outputPath);
}

module.exports = {
    generatePayslip,
    generatePayslipForEmployee,
    formatMoney,
    numberToWords,
    calculatePCB
};
