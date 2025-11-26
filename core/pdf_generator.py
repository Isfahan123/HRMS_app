"""
PDF generation utilities using fpdf2 (pure Python).

This module provides PDF generation functionality using fpdf2, which is a pure
Python library that works on cPanel/shared hosting without requiring C compilation.

This version replicates the same format as the desktop GUI payslip generator
(gui/payslip_generator.py) but using fpdf2 instead of reportlab.
"""
import io
import json
import os
import tempfile
import traceback
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime

# Constants for PDF layout
LABEL_MAX_LENGTH = 25  # Maximum characters for table labels before truncation

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

try:
    from num2words import num2words
    NUM2WORDS_AVAILABLE = True
except ImportError:
    NUM2WORDS_AVAILABLE = False

# --------------------------
# Company details (same as gui/payslip_generator.py)
# --------------------------
LOGO_URL = "https://enigmatechnicalsolutions.com/wp-content/uploads/2024/07/cropped-enigma512px-300x300-1.png"
COMPANY_NAME = "ENIGMA TECHNICAL SOLUTIONS SDN BHD"
SSM_NO = "002628025-K"
COMPANY_ADDRESS_LINES = [
    "56 & 57, Persiaran Venice Sutera 1, Desa Manjung Raya",
    "32200 Lumut, Perak, Malaysia",
    "Tel: +60-3-4131 9114 | Email: info@enigmatechnical.com"
]

# --------------------------
# Helpers
# --------------------------
def download_logo_bytes(url):
    """Try download logo and return bytes or None"""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        print("Warning: logo download failed:", e)
        return None

def money(v):
    """Format money with comma separators and 2 decimal places"""
    return f"{v:,.2f}"

def money_words(amount):
    """Convert amount to words (e.g., 'One Thousand Two Hundred Ringgit Fifty Sen Only')"""
    if not NUM2WORDS_AVAILABLE:
        return f"RM {money(amount)}"
    
    whole = int(amount)
    cents = int(round((amount - whole) * 100))
    w = num2words(whole, to='cardinal', lang='en').title()
    if cents:
        c = num2words(cents, to='cardinal', lang='en').title()
        return f"{w} Ringgit {c} Sen Only"
    else:
        return f"{w} Ringgit Only"

def _parse_any_date(val):
    """Best-effort parse of common date formats to a datetime object.
    Supports: YYYY-MM-DD, YYYY/MM/DD, DD/MM/YYYY, DD-MM-YYYY, YYYY-MM, YYYY/MM, MM/YYYY, MM-YYYY.
    Returns None on failure.
    """
    try:
        if not val:
            return None
        from datetime import datetime as _dt
        s = str(val).strip()
        fmts = [
            '%Y-%m-%d', '%Y/%m/%d',
            '%d/%m/%Y', '%d-%m-%Y',
            '%Y-%m', '%Y/%m',
            '%m/%Y', '%m-%Y',
        ]
        for f in fmts:
            try:
                dt = _dt.strptime(s, f)
                if f in ('%Y-%m', '%Y/%m', '%m/%Y', '%m-%Y'):
                    parts = s.replace('-', '/').split('/')
                    if f in ('%m/%Y', '%m-%Y'):
                        mm, yy = int(parts[0]), int(parts[1])
                        return _dt(yy, mm, 1)
                    else:
                        yy, mm = int(parts[0]), int(parts[1])
                        return _dt(yy, mm, 1)
                return dt
            except Exception:
                continue
        return None
    except Exception:
        return None


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
    reportlab which requires C libraries. It replicates the same format as
    gui/payslip_generator.py for consistent output between desktop and web.
    
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
        
        # Resolve YTD snapshot (as of previous month)
        gross_ytd = 0.0
        ytd_epf_emp = 0.0
        ytd_socso = 0.0
        ytd_pcb = 0.0
        ytd_eis = 0.0
        try:
            # Preferred: use snapshot columns on payroll_runs if present
            gross_ytd = float(payroll_run.get('accumulated_gross_salary_ytd', 0.0) or 0.0)
            ytd_epf_emp = float(payroll_run.get('accumulated_epf_employee_ytd', 0.0) or 0.0)
            ytd_pcb = float(payroll_run.get('accumulated_pcb_ytd', 0.0) or 0.0)
            ytd_socso = float(payroll_run.get('accumulated_socso_employee_ytd', 0.0) or 0.0)
            ytd_eis = float(payroll_run.get('accumulated_eis_employee_ytd', 0.0) or 0.0)

            # Fallback to calculating from payroll runs if snapshot columns are empty
            def _fallback_from_payroll_runs():
                nonlocal gross_ytd, ytd_epf_emp, ytd_pcb, ytd_socso, ytd_eis
                _pr_date = payroll_run.get('payroll_date', '')
                if not _pr_date:
                    return False
                emp_uuid = employee.get('id')
                if not emp_uuid:
                    return False
                pr = (
                    supabase.table('payroll_runs')
                    .select('gross_salary, epf_employee, pcb, socso_employee, eis_employee, payroll_date')
                    .eq('employee_id', emp_uuid)
                    .execute()
                )
                if pr and pr.data:
                    try:
                        _ref = _parse_any_date(_pr_date)
                    except Exception:
                        _ref = None
                    _rows = []
                    for r in pr.data:
                        try:
                            _dtp = _parse_any_date(r.get('payroll_date'))
                            if _ref and _dtp and _dtp < _ref:
                                _rows.append(r)
                        except Exception:
                            continue
                    if _rows:
                        gross_ytd = sum(float(r.get('gross_salary', 0) or 0) for r in _rows)
                        ytd_epf_emp = sum(float(r.get('epf_employee', 0) or 0) for r in _rows)
                        ytd_pcb = sum(float(r.get('pcb', 0) or 0) for r in _rows)
                        ytd_socso = sum(float(r.get('socso_employee', 0) or 0) for r in _rows)
                        ytd_eis = sum(float(r.get('eis_employee', 0) or 0) for r in _rows)
                        return True
                return False

            # If core YTDs are all zero, derive them from runs
            if gross_ytd == 0.0 and ytd_epf_emp == 0.0 and ytd_pcb == 0.0:
                _fallback_from_payroll_runs()
        except Exception as _ytd_err:
            print(f"Warning: could not resolve YTD snapshot for payslip: {_ytd_err}")
        
        # Generate output path if not provided
        if not output_path:
            employee_display_id = employee.get('employee_id', employee_id)
            output_path = f"Payslip_{employee_display_id}_{month}_{year}.pdf"
        
        # =========================================================
        # Generate PDF using fpdf2 - Replicate old reportlab format
        # =========================================================
        pdf = FPDF('P', 'mm', 'A4')
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Page dimensions (A4 = 210 x 297 mm)
        W = 210
        left_margin = 18
        right_margin = 18
        usable_width = W - left_margin - right_margin
        
        # Try to download and add logo
        logo_bytes = download_logo_bytes(LOGO_URL)
        logo_size = 28  # mm
        
        # Starting position
        top_y = 18
        text_x = left_margin
        
        if logo_bytes:
            tmp_path = None
            try:
                # Save logo to temp file for fpdf2
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                    tmp.write(logo_bytes)
                    tmp_path = tmp.name
                
                pdf.image(tmp_path, left_margin, top_y, logo_size, logo_size)
                text_x = left_margin + logo_size + 6
            except Exception as e:
                print(f"Warning: Could not add logo to PDF: {e}")
            finally:
                # Clean up temp file
                if tmp_path:
                    try:
                        os.unlink(tmp_path)
                    except (OSError, FileNotFoundError):
                        pass
        
        # Company name and details (right of logo)
        pdf.set_xy(text_x, top_y)
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 6, COMPANY_NAME, ln=True)
        
        pdf.set_xy(text_x, top_y + 7)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(0, 5, f"SSM No: {SSM_NO}", ln=True)
        
        # Company address lines
        y_pos = top_y + 13
        for line in COMPANY_ADDRESS_LINES:
            if line.strip():
                pdf.set_xy(text_x, y_pos)
                pdf.cell(0, 4, line, ln=True)
                y_pos += 4
        
        # Payslip meta (right side)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_xy(W - right_margin - 60, top_y)
        pdf.cell(60, 5, f"Payslip for {month} {year}", align='R')
        
        pdf.set_font('Helvetica', '', 9)
        pdf.set_xy(W - right_margin - 60, top_y + 7)
        pdf.cell(60, 5, f"Date: {pay_date}", align='R')
        
        # Employee block (boxed section)
        block_y = top_y + logo_size + 14
        box_h = 20
        
        pdf.set_draw_color(0, 0, 0)
        pdf.set_line_width(0.3)
        pdf.rect(left_margin, block_y, usable_width, box_h)
        
        emp_position = employee.get('position') or employee.get('job_title') or '-'
        emp_name = employee.get('full_name', '')
        emp_staff_no = employee.get('employee_id', '')
        emp_ic = employee.get('ic_number', employee.get('nric', '-'))
        emp_epf_no = employee.get('epf_number', '-')
        emp_socso_no = employee.get('socso_number', '-')
        
        # Employee info - left side
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_xy(left_margin + 4, block_y + 4)
        pdf.cell(0, 5, f"NAME: {emp_name}")
        
        pdf.set_xy(left_margin + 4, block_y + 10)
        pdf.cell(0, 5, f"STAFF NO: {emp_staff_no}   NRIC: {emp_ic}")
        
        # Employee info - right side
        pdf.set_xy(left_margin + usable_width - 74, block_y + 4)
        pdf.cell(70, 5, f"Position: {emp_position}", align='R')
        
        pdf.set_xy(left_margin + usable_width - 74, block_y + 10)
        pdf.cell(70, 5, f"EPF No: {emp_epf_no}   SOCSO: {emp_socso_no}", align='R')
        
        # =========================================================
        # Income and Deductions tables (two columns with Current/YTD)
        # =========================================================
        table_y = block_y + box_h + 8
        col_gap = 12
        col1_w = (usable_width - col_gap) / 2
        col2_w = col1_w
        row_h = 6
        
        # Build income items
        earning_current = [("Basic Salary", basic_salary)]
        if allowances:
            for allowance_type, amount in allowances.items():
                if amount and float(amount) > 0:
                    earning_current.append((f"{allowance_type.title()} Allowance", float(amount)))
        if bonus > 0:
            earning_current.append(("Bonus", bonus))
        
        # Build YTD map (put all YTD on first item for simplicity)
        earning_ytd_map = {}
        if earning_current:
            first_label = earning_current[0][0]
            earning_ytd_map[first_label] = gross_ytd
            for lbl, _amt in earning_current[1:]:
                earning_ytd_map[lbl] = 0.0
        
        # Left column: INCOME
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_xy(left_margin, table_y)
        pdf.cell(col1_w, 6, "INCOME", ln=True)
        
        # Income header row
        income_y = table_y + 7
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_xy(left_margin, income_y)
        pdf.cell(col1_w * 0.5, 5, "Description")
        pdf.cell(col1_w * 0.25, 5, "Current", align='R')
        pdf.cell(col1_w * 0.25, 5, "Y-T-D", align='R')
        
        # Income data rows
        pdf.set_font('Helvetica', '', 9)
        y = income_y + row_h
        gross_current = 0.0
        gross_ytd_total = 0.0
        
        for lbl, amt in earning_current:
            y_curr = float(amt)
            y_ytd = float(earning_ytd_map.get(lbl, 0.0))
            
            pdf.set_xy(left_margin, y)
            pdf.cell(col1_w * 0.5, 5, lbl[:LABEL_MAX_LENGTH])  # Truncate long labels
            pdf.cell(col1_w * 0.25, 5, money(y_curr), align='R')
            pdf.cell(col1_w * 0.25, 5, money(y_ytd), align='R')
            
            y += row_h
            gross_current += y_curr
            gross_ytd_total += y_ytd
        
        # Gross totals row
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_xy(left_margin, y)
        pdf.cell(col1_w * 0.5, 5, "Gross Total")
        pdf.cell(col1_w * 0.25, 5, money(gross_current), align='R')
        pdf.cell(col1_w * 0.25, 5, money(gross_ytd_total), align='R')
        income_end_y = y + row_h
        
        # Right column: DEDUCTION
        ded_x = left_margin + col1_w + col_gap
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_xy(ded_x, table_y)
        pdf.cell(col2_w, 6, "DEDUCTION", ln=True)
        
        # Deduction header row
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_xy(ded_x, income_y)
        pdf.cell(col2_w * 0.5, 5, "Description")
        pdf.cell(col2_w * 0.25, 5, "Current", align='R')
        pdf.cell(col2_w * 0.25, 5, "Y-T-D", align='R')
        
        # Deduction data rows
        pdf.set_font('Helvetica', '', 9)
        y2 = income_y + row_h
        total_ded_current = 0.0
        total_ded_ytd = 0.0
        
        # Build deduction items with YTD
        deduction_items = []
        
        # Other deductions first (unpaid leave, etc.)
        if unpaid_days > 0 and unpaid_deduction > 0:
            deduction_items.append((f'Unpaid Leave ({unpaid_days} days)', unpaid_deduction, 0.0))
        
        # Add other optional deductions from payroll run
        other_deduction_keys = ['sip_deduction', 'additional_epf_deduction', 'prs_deduction', 
                        'insurance_premium', 'medical_premium', 'other_deductions']
        for ded_key in other_deduction_keys:
            ded_amount = float(payroll_run.get(ded_key, 0))
            if ded_amount > 0:
                ded_name = ded_key.replace('_deduction', '').replace('_', ' ').title()
                deduction_items.append((ded_name, ded_amount, 0.0))
        
        # Statutory deductions with YTD
        deduction_items.append(("EPF (Employee)", epf_employee, ytd_epf_emp))
        deduction_items.append(("SOCSO", socso_employee, ytd_socso))
        deduction_items.append(("PCB", pcb, ytd_pcb))
        deduction_items.append(("EIS", eis_employee, ytd_eis))
        
        for lbl, ycur, yytd in deduction_items:
            pdf.set_xy(ded_x, y2)
            pdf.cell(col2_w * 0.5, 5, lbl[:LABEL_MAX_LENGTH])
            pdf.cell(col2_w * 0.25, 5, money(ycur), align='R')
            pdf.cell(col2_w * 0.25, 5, money(yytd), align='R')
            
            y2 += row_h
            total_ded_current += ycur
            total_ded_ytd += yytd
        
        # Total deductions row
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_xy(ded_x, y2)
        pdf.cell(col2_w * 0.5, 5, "Total Deductions")
        pdf.cell(col2_w * 0.25, 5, money(total_ded_current), align='R')
        pdf.cell(col2_w * 0.25, 5, money(total_ded_ytd), align='R')
        ded_end_y = y2 + row_h
        
        # =========================================================
        # Employer contributions block
        # =========================================================
        emp_cont_y = max(income_end_y, ded_end_y) + 8
        
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_xy(left_margin, emp_cont_y)
        pdf.cell(0, 5, "Employer Contributions")
        
        pdf.set_font('Helvetica', '', 9)
        pdf.set_xy(left_margin + 4, emp_cont_y + 6)
        pdf.cell(0, 5, f"Employer EPF: RM {money(epf_employer)}")
        
        pdf.set_xy(left_margin + 4, emp_cont_y + 11)
        pdf.cell(0, 5, f"Employer SOCSO: RM {money(socso_employer)}")
        
        pdf.set_xy(left_margin + 4, emp_cont_y + 16)
        pdf.cell(0, 5, f"Employer EIS: RM {money(eis_employer)}")
        
        # =========================================================
        # Totals / Net / End Month Pay (right side)
        # =========================================================
        net = gross_current - total_ded_current
        
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_xy(W - right_margin - 70, emp_cont_y)
        pdf.cell(70, 5, f"Gross Income : RM {money(gross_current)}", align='R')
        
        pdf.set_xy(W - right_margin - 70, emp_cont_y + 6)
        pdf.cell(70, 5, f"Total Deductions : RM {money(total_ded_current)}", align='R')
        
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_xy(W - right_margin - 70, emp_cont_y + 14)
        pdf.cell(70, 5, f"Net Income : RM {money(net)}", align='R')
        
        pdf.set_font('Helvetica', '', 9)
        pdf.set_xy(W - right_margin - 70, emp_cont_y + 21)
        pdf.cell(70, 5, f"End Month Pay : RM {money(net)}", align='R')
        
        # =========================================================
        # Net in words
        # =========================================================
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_xy(left_margin, emp_cont_y + 28)
        pdf.cell(0, 5, f"In Words: {money_words(net)}")
        
        # =========================================================
        # Unpaid leave information (if any)
        # =========================================================
        if unpaid_days > 0:
            pdf.set_font('Helvetica', 'B', 8)
            pdf.set_xy(left_margin, emp_cont_y + 35)
            pdf.cell(0, 5, f"Unpaid Leave: {unpaid_days} days (Deduction: RM {money(unpaid_deduction)})")
        
        # =========================================================
        # Signature lines
        # =========================================================
        sig_y = 250  # Fixed position near bottom
        sig_width = 40
        gap = 20
        
        pdf.set_draw_color(0, 0, 0)
        pdf.set_line_width(0.2)
        
        # Prepared by
        pdf.line(left_margin, sig_y, left_margin + sig_width, sig_y)
        pdf.set_font('Helvetica', '', 8)
        pdf.set_xy(left_margin, sig_y + 1)
        pdf.cell(sig_width, 5, "Prepared By (Name & Signature)")
        
        # Approved by
        app_x = left_margin + sig_width + gap
        pdf.line(app_x, sig_y, app_x + sig_width, sig_y)
        pdf.set_xy(app_x, sig_y + 1)
        pdf.cell(sig_width, 5, "Approved By (Name & Signature)")
        
        # Employee acknowledgement
        emp_x = app_x + sig_width + gap
        emp_sig_width = sig_width + 12
        pdf.line(emp_x, sig_y, emp_x + emp_sig_width, sig_y)
        pdf.set_xy(emp_x, sig_y + 1)
        pdf.cell(emp_sig_width, 5, "Employee (Acknowledgement & Signature)")
        
        # =========================================================
        # Footer
        # =========================================================
        pdf.set_font('Helvetica', '', 7)
        pdf.set_text_color(128, 128, 128)
        pdf.set_xy(0, 280)
        pdf.cell(W, 5, "This is a computer-generated payslip and does not require a signature.", align='C')
        pdf.set_text_color(0, 0, 0)
        
        # Save PDF
        pdf.output(output_path)
        return output_path
        
    except Exception as e:
        print(f"DEBUG: Error generating payslip for employee: {e}")
        traceback.print_exc()
        return None
