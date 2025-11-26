"""
PDF generation utilities using fpdf2 (pure Python).

This module provides PDF generation functionality using fpdf2, which is a pure
Python library that works on cPanel/shared hosting without requiring C compilation.

For desktop environments where reportlab is available, the gui/payslip_generator.py
can be used instead for more advanced formatting.
"""
import io
import json
import traceback
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


def generate_payslip_for_employee(employee_id: str, payroll_run_id: str, output_path: str = None) -> Optional[str]:
    """
    Generate payslip PDF for a specific employee and payroll run using fpdf2.
    
    This is a web-compatible version that uses fpdf2 (pure Python) instead of 
    reportlab which requires C libraries. It mirrors the interface of
    gui/payslip_generator.py for seamless replacement in web environments.
    
    Args:
        employee_id: UUID of the employee
        payroll_run_id: UUID of the payroll run
        output_path: Optional output file path. Auto-generated if not provided.
        
    Returns:
        Path to generated PDF file, or None on error
    """
    if not FPDF_AVAILABLE:
        print("DEBUG: fpdf2 not available for PDF generation")
        return None
    
    try:
        # Import supabase service (relative import within the package)
        from services.supabase_service import supabase, get_monthly_unpaid_leave_deduction
        
        # Get employee data
        employee_response = supabase.table("employees").select("*").eq("id", employee_id).execute()
        if not employee_response.data:
            print(f"DEBUG: No employee found for ID: {employee_id}")
            return None
        
        employee = employee_response.data[0]
        
        # Get payroll run data
        payroll_response = supabase.table("payroll_runs").select("*").eq("id", payroll_run_id).execute()
        if not payroll_response.data:
            print(f"DEBUG: No payroll run found for ID: {payroll_run_id}")
            return None
            
        payroll_run = payroll_response.data[0]
        
        # Parse payroll date
        payroll_date = payroll_run.get('payroll_date', '')
        if payroll_date:
            try:
                date_obj = datetime.strptime(payroll_date, '%Y-%m-%d')
                month = date_obj.strftime('%B')
                year = date_obj.year
                payroll_year = date_obj.year
                payroll_month = date_obj.month
                pay_date = date_obj.strftime('%d-%m-%Y')
            except ValueError:
                month = datetime.now().strftime('%B')
                year = datetime.now().year
                payroll_year = datetime.now().year
                payroll_month = datetime.now().month
                pay_date = datetime.now().strftime('%d-%m-%Y')
        else:
            month = datetime.now().strftime('%B')
            year = datetime.now().year
            payroll_year = datetime.now().year
            payroll_month = datetime.now().month
            pay_date = datetime.now().strftime('%d-%m-%Y')
        
        # Parse allowances
        allowances = payroll_run.get('allowances', {})
        if isinstance(allowances, str):
            allowances = json.loads(allowances) if allowances else {}
        
        # Get unpaid leave data
        unpaid_days = 0.0
        unpaid_deduction = 0.0
        try:
            unpaid_leave_data = get_monthly_unpaid_leave_deduction(employee_id, payroll_year, payroll_month)
            unpaid_days = unpaid_leave_data.get('unpaid_days', 0.0)
            unpaid_deduction = unpaid_leave_data.get('total_deduction', 0.0)
        except Exception as e:
            print(f"DEBUG: Could not get unpaid leave data: {e}")
        
        # Get contributions from payroll run
        epf_employee = float(payroll_run.get('epf_employee', 0))
        epf_employer = float(payroll_run.get('epf_employer', 0))
        socso_employee = float(payroll_run.get('socso_employee', 0))
        socso_employer = float(payroll_run.get('socso_employer', 0))
        eis_employee = float(payroll_run.get('eis_employee', 0))
        eis_employer = float(payroll_run.get('eis_employer', 0))
        pcb = float(payroll_run.get('pcb', 0))
        gross_salary = float(payroll_run.get('gross_salary', 0))
        net_salary = float(payroll_run.get('net_salary', 0))
        basic_salary = float(employee.get('basic_salary', 0))
        bonus = float(payroll_run.get('bonus', 0))
        
        # Generate output path if not provided
        if not output_path:
            employee_display_id = employee.get('employee_id', employee_id)
            output_path = f"Payslip_{employee_display_id}_{month}_{year}.pdf"
        
        # Generate PDF using fpdf2
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Title
        pdf.set_font('Helvetica', 'B', 18)
        pdf.set_text_color(0, 0, 139)  # Dark blue
        pdf.cell(0, 12, 'PAYSLIP', ln=True, align='C')
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 6, f"For {month} {year}", ln=True, align='C')
        pdf.ln(5)
        
        # Employee information section
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 8, 'Employee Information', ln=True)
        
        pdf.set_font('Helvetica', '', 10)
        emp_position = employee.get('position') or employee.get('job_title') or ''
        info_rows = [
            ('Employee ID:', employee.get('employee_id', '')),
            ('Employee Name:', employee.get('full_name', '')),
            ('Position:', emp_position),
            ('IC Number:', employee.get('ic_number', employee.get('nric', ''))),
            ('EPF Number:', employee.get('epf_number', '')),
            ('Bank:', f"{employee.get('bank_name', '')} - {employee.get('bank_account', '')}"),
            ('Pay Date:', pay_date),
        ]
        
        for label, value in info_rows:
            if value:  # Only show non-empty values
                pdf.set_fill_color(211, 211, 211)
                pdf.cell(50, 7, label, 1, 0, 'L', True)
                pdf.cell(120, 7, str(value), 1, 1, 'L')
        
        pdf.ln(5)
        
        # Income section
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_fill_color(0, 0, 139)  # Dark blue
        pdf.set_text_color(255, 255, 255)
        pdf.cell(100, 10, 'INCOME', 1, 0, 'C', True)
        pdf.cell(70, 10, 'AMOUNT (RM)', 1, 1, 'C', True)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', '', 10)
        
        # Income items
        income_items = [('Basic Salary', basic_salary)]
        
        # Add allowances
        if allowances:
            for name, amount in allowances.items():
                if amount and float(amount) > 0:
                    income_items.append((f"{name.replace('_', ' ').title()} Allowance", float(amount)))
        
        # Add bonus if any
        if bonus > 0:
            income_items.append(('Bonus', bonus))
        
        for desc, amount in income_items:
            if float(amount) > 0:
                pdf.cell(100, 8, desc, 1, 0, 'L')
                pdf.cell(70, 8, f"{float(amount):,.2f}", 1, 1, 'R')
        
        # Gross income total
        pdf.set_fill_color(173, 216, 230)  # Light blue
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(100, 8, 'GROSS INCOME', 1, 0, 'L', True)
        pdf.cell(70, 8, f"{gross_salary:,.2f}", 1, 1, 'R', True)
        
        pdf.ln(5)
        
        # Deductions section
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_fill_color(139, 0, 0)  # Dark red
        pdf.set_text_color(255, 255, 255)
        pdf.cell(100, 10, 'DEDUCTIONS', 1, 0, 'C', True)
        pdf.cell(70, 10, 'AMOUNT (RM)', 1, 1, 'C', True)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', '', 10)
        
        deduction_items = []
        
        # Add unpaid leave deduction first
        if unpaid_days > 0 and unpaid_deduction > 0:
            deduction_items.append((f'Unpaid Leave ({unpaid_days} days)', unpaid_deduction))
        
        # Standard deductions
        if epf_employee > 0:
            deduction_items.append(('EPF (Employee)', epf_employee))
        if socso_employee > 0:
            deduction_items.append(('SOCSO', socso_employee))
        if eis_employee > 0:
            deduction_items.append(('EIS', eis_employee))
        if pcb > 0:
            deduction_items.append(('PCB Tax', pcb))
        
        # Add other deductions from payroll run and update total_deductions
        other_deduction_keys = ['sip_deduction', 'additional_epf_deduction', 'prs_deduction', 
                        'insurance_premium', 'medical_premium', 'other_deductions']
        for ded_key in other_deduction_keys:
            ded_amount = float(payroll_run.get(ded_key, 0))
            if ded_amount > 0:
                ded_name = ded_key.replace('_deduction', '').replace('_', ' ').title()
                deduction_items.append((ded_name, ded_amount))
        
        # Calculate total deductions from all items displayed
        total_deductions = sum(amount for _, amount in deduction_items)
        
        for desc, amount in deduction_items:
            if float(amount) > 0:
                pdf.cell(100, 8, desc, 1, 0, 'L')
                pdf.cell(70, 8, f"{float(amount):,.2f}", 1, 1, 'R')
        
        # Total deductions
        pdf.set_fill_color(255, 182, 193)  # Light pink
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(100, 8, 'TOTAL DEDUCTIONS', 1, 0, 'L', True)
        pdf.cell(70, 8, f"{total_deductions:,.2f}", 1, 1, 'R', True)
        
        pdf.ln(5)
        
        # Employer contributions section
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_fill_color(70, 130, 180)  # Steel blue
        pdf.set_text_color(255, 255, 255)
        pdf.cell(100, 10, 'EMPLOYER CONTRIBUTIONS', 1, 0, 'C', True)
        pdf.cell(70, 10, 'AMOUNT (RM)', 1, 1, 'C', True)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', '', 10)
        
        employer_items = []
        if epf_employer > 0:
            employer_items.append(('EPF (Employer)', epf_employer))
        if socso_employer > 0:
            employer_items.append(('SOCSO (Employer)', socso_employer))
        if eis_employer > 0:
            employer_items.append(('EIS (Employer)', eis_employer))
        
        for desc, amount in employer_items:
            pdf.cell(100, 8, desc, 1, 0, 'L')
            pdf.cell(70, 8, f"{float(amount):,.2f}", 1, 1, 'R')
        
        pdf.ln(5)
        
        # Net salary
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_fill_color(0, 100, 0)  # Dark green
        pdf.set_text_color(255, 255, 255)
        pdf.cell(100, 12, 'NET SALARY', 1, 0, 'C', True)
        pdf.cell(70, 12, f"RM {net_salary:,.2f}", 1, 1, 'C', True)
        
        pdf.ln(5)
        
        # Footer
        pdf.set_text_color(128, 128, 128)
        pdf.set_font('Helvetica', 'I', 8)
        pdf.cell(0, 6, 'This is a computer-generated payslip and does not require a signature.', ln=True, align='C')
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, f"Generated on: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} (Malaysia Time)", ln=True)
        
        pdf.output(output_path)
        return output_path
        
    except Exception as e:
        print(f"DEBUG: Error generating payslip for employee: {e}")
        traceback.print_exc()
        return None
