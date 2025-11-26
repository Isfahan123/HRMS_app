"""
PDF generation utilities using fpdf2 (pure Python).

This module provides PDF generation functionality using fpdf2, which is a pure
Python library that works on cPanel/shared hosting without requiring C compilation.

For desktop environments where reportlab is available, the gui/payslip_generator.py
can be used instead for more advanced formatting.
"""
import io
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False


def generate_payslip_pdf_fpdf(employee: Dict, payroll_data: Dict, payroll_date: str) -> bytes:
    """
    Generate a simple payslip PDF using fpdf2.
    
    Args:
        employee: Dictionary with employee details (full_name, employee_id, basic_salary)
        payroll_data: Dictionary with payroll calculations
        payroll_date: Payroll date string
        
    Returns:
        PDF content as bytes, or empty bytes on error
    """
    if not FPDF_AVAILABLE:
        print("DEBUG: fpdf2 not available for PDF generation")
        return b""
    
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Title
        pdf.set_font('Helvetica', 'B', 18)
        pdf.cell(0, 10, 'PAYSLIP', ln=True, align='C')
        pdf.ln(5)
        
        # Employee info
        pdf.set_font('Helvetica', '', 11)
        pdf.cell(0, 8, f"Employee: {employee.get('full_name', 'N/A')}", ln=True)
        pdf.cell(0, 8, f"Employee ID: {employee.get('employee_id', 'N/A')}", ln=True)
        pdf.cell(0, 8, f"Payroll Date: {payroll_date}", ln=True)
        pdf.ln(5)
        
        # Table header
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_fill_color(128, 128, 128)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(100, 10, 'Description', 1, 0, 'C', True)
        pdf.cell(70, 10, 'Amount (RM)', 1, 1, 'C', True)
        
        # Reset colors for data rows
        pdf.set_text_color(0, 0, 0)
        pdf.set_fill_color(245, 245, 220)  # Beige
        pdf.set_font('Helvetica', '', 10)
        
        # Data rows
        rows = [
            ("Basic Salary", f"{float(employee.get('basic_salary', 0)):.2f}"),
        ]
        
        # Add allowances
        for allowance_type, amount in payroll_data.get("allowances", {}).items():
            rows.append((allowance_type.replace("_", " ").title(), f"{float(amount):.2f}"))
        
        # Add unpaid leave if applicable
        unpaid_days = payroll_data.get("unpaid_days", 0)
        unpaid_deduction = payroll_data.get("unpaid_leave_deduction", 0)
        if unpaid_days > 0 and unpaid_deduction > 0:
            rows.append((f"Unpaid Leave ({unpaid_days} days)", f"-{float(unpaid_deduction):.2f}"))
        
        # Add standard payroll items
        rows.extend([
            ("Gross Salary", f"{float(payroll_data.get('gross_salary', 0)):.2f}"),
            ("EPF Employee", f"{float(payroll_data.get('epf_employee', 0)):.2f}"),
            ("EPF Employer", f"{float(payroll_data.get('epf_employer', 0)):.2f}"),
            ("SOCSO Employee", f"{float(payroll_data.get('socso_employee', 0)):.2f}"),
            ("SOCSO Employer", f"{float(payroll_data.get('socso_employer', 0)):.2f}"),
            ("EIS Employee", f"{float(payroll_data.get('eis_employee', 0)):.2f}"),
            ("EIS Employer", f"{float(payroll_data.get('eis_employer', 0)):.2f}"),
            ("PCB", f"{float(payroll_data.get('pcb', 0)):.2f}"),
            ("Net Salary", f"{float(payroll_data.get('net_salary', 0)):.2f}"),
        ])
        
        # Render rows
        fill = False
        for desc, amount in rows:
            pdf.cell(100, 8, desc, 1, 0, 'L', fill)
            pdf.cell(70, 8, amount, 1, 1, 'R', fill)
            fill = not fill
        
        pdf.ln(5)
        
        # Footer
        pdf.set_font('Helvetica', 'I', 8)
        pdf.cell(0, 8, f"Generated on: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
        
        return pdf.output()
        
    except Exception as e:
        print(f"DEBUG: Error generating payslip PDF with fpdf2: {e}")
        return b""


def generate_payslip_pdf_to_file(payroll_data: Dict, output_path: str = None) -> Optional[str]:
    """
    Generate a payslip PDF file from comprehensive payroll data.
    
    Args:
        payroll_data: Dictionary with full payroll calculation results
        output_path: Optional output file path. Auto-generated if not provided.
        
    Returns:
        Path to generated PDF file, or None on error
    """
    if not FPDF_AVAILABLE:
        print("DEBUG: fpdf2 not available for PDF generation")
        return None
    
    try:
        if not output_path:
            employee_id = payroll_data.get('employee_id', 'unknown')
            month_year = payroll_data.get('month_year', 'unknown')
            output_path = f"Payslip_{employee_id}_{month_year.replace('/', '_')}.pdf"
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Title
        pdf.set_font('Helvetica', 'B', 18)
        pdf.set_text_color(0, 0, 139)  # Dark blue
        pdf.cell(0, 12, 'PAYSLIP', ln=True, align='C')
        pdf.ln(5)
        
        # Employee information section
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, 'Employee Information', ln=True)
        
        pdf.set_font('Helvetica', '', 10)
        info_rows = [
            ('Employee ID:', payroll_data.get('employee_id', '')),
            ('Employee Name:', payroll_data.get('employee_name', '')),
            ('Month/Year:', payroll_data.get('month_year', '')),
            ('Tax Status:', payroll_data.get('tax_resident_status', 'Resident')),
        ]
        
        for label, value in info_rows:
            pdf.set_fill_color(211, 211, 211)
            pdf.cell(50, 8, label, 1, 0, 'L', True)
            pdf.cell(120, 8, str(value), 1, 1, 'L')
        
        pdf.ln(5)
        
        # Income section
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_fill_color(0, 0, 139)  # Dark blue
        pdf.set_text_color(255, 255, 255)
        pdf.cell(100, 10, 'INCOME', 1, 0, 'C', True)
        pdf.cell(70, 10, 'AMOUNT (RM)', 1, 1, 'C', True)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', '', 10)
        
        income_items = [
            ('Basic Salary', payroll_data.get('basic_salary', 0)),
            ('Overtime Pay', payroll_data.get('overtime_pay', 0)),
            ('Commission', payroll_data.get('commission', 0)),
            ('Bonus', payroll_data.get('bonus', 0)),
        ]
        
        # Add allowances
        allowances = payroll_data.get('allowances', {})
        if allowances:
            for name, amount in allowances.items():
                if amount > 0:
                    income_items.append((name.replace('_', ' ').title(), amount))
        
        for desc, amount in income_items:
            if float(amount) > 0:
                pdf.cell(100, 8, desc, 1, 0, 'L')
                pdf.cell(70, 8, f"{float(amount):,.2f}", 1, 1, 'R')
        
        # Gross income total
        pdf.set_fill_color(173, 216, 230)  # Light blue
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(100, 8, 'GROSS INCOME', 1, 0, 'L', True)
        pdf.cell(70, 8, f"{float(payroll_data.get('gross_income', 0)):,.2f}", 1, 1, 'R', True)
        
        pdf.ln(5)
        
        # Deductions section
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_fill_color(139, 0, 0)  # Dark red
        pdf.set_text_color(255, 255, 255)
        pdf.cell(100, 10, 'DEDUCTIONS', 1, 0, 'C', True)
        pdf.cell(70, 10, 'AMOUNT (RM)', 1, 1, 'C', True)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', '', 10)
        
        deduction_items = [
            ('EPF Employee', payroll_data.get('epf_employee', 0)),
            ('SOCSO Employee', payroll_data.get('socso_employee', 0)),
            ('EIS Employee', payroll_data.get('eis_employee', 0)),
            ('PCB Tax', payroll_data.get('pcb_tax', 0)),
        ]
        
        # Add monthly deductions
        monthly_deductions = payroll_data.get('monthly_deductions', {})
        if monthly_deductions:
            for name, amount in monthly_deductions.items():
                if float(amount or 0) > 0:
                    deduction_items.append((name.replace('_', ' ').title(), amount))
        
        # Add other deductions
        other_deductions = payroll_data.get('other_deductions', {})
        if other_deductions:
            for name, amount in other_deductions.items():
                if float(amount or 0) > 0:
                    deduction_items.append((name.replace('_', ' ').title(), amount))
        
        for desc, amount in deduction_items:
            if float(amount or 0) > 0:
                pdf.cell(100, 8, desc, 1, 0, 'L')
                pdf.cell(70, 8, f"{float(amount):,.2f}", 1, 1, 'R')
        
        # Total deductions
        pdf.set_fill_color(255, 182, 193)  # Light pink
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(100, 8, 'TOTAL DEDUCTIONS', 1, 0, 'L', True)
        pdf.cell(70, 8, f"{float(payroll_data.get('total_deductions', 0)):,.2f}", 1, 1, 'R', True)
        
        pdf.ln(5)
        
        # Net salary
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_fill_color(0, 100, 0)  # Dark green
        pdf.set_text_color(255, 255, 255)
        pdf.cell(100, 12, 'NET SALARY', 1, 0, 'C', True)
        pdf.cell(70, 12, f"RM {float(payroll_data.get('net_salary', 0)):,.2f}", 1, 1, 'C', True)
        
        pdf.ln(5)
        
        # Footer
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(0, 8, f"Generated on: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} (Malaysia Time)", ln=True)
        
        pdf.output(output_path)
        return output_path
        
    except Exception as e:
        print(f"DEBUG: Error generating payslip PDF: {e}")
        return None
