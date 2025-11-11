# payslip_generator.py
import io
import requests
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from num2words import num2words

# --------------------------
# Company details
# --------------------------
LOGO_URL = "https://enigmatechnicalsolutions.com/wp-content/uploads/2024/07/cropped-enigma512px-300x300-1.png"
COMPANY_NAME = "ENIGMA TECHNICAL SOLUTIONS SDN BHD"
SSM_NO = "002628025-K"
COMPANY_ADDRESS_LINES = [
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
]

# --------------------------
# Helpers
# --------------------------
def download_logo_stream(url):
    """Try download logo and return ImageReader or None"""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        bio = io.BytesIO(resp.content)
        return ImageReader(bio)
    except Exception as e:
        print("Warning: logo download failed:", e)
        return None

def money(v):
    return f"{v:,.2f}"

def money_words(amount):
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

def calculate_pcb(gross_salary, epf_emp):
    """Simple PCB approximation: taxable = gross - epf_emp. Use bands approx."""
    taxable = max(0.0, gross_salary - epf_emp)
    if taxable < 3000:
        return 0.0
    if taxable < 5000:
        rate = 0.03
    elif taxable < 8000:
        rate = 0.07
    else:
        rate = 0.10
    return round(taxable * rate, 2)

def get_employee_payslip_data(employee_id, payroll_run_id):
    """Fetch employee and payslip data from database"""
    try:
        # Import supabase locally to avoid circular imports
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from services.supabase_service import supabase
        
        # Get employee data
        employee_response = supabase.table("employees").select("*").eq("id", employee_id).execute()
        if not employee_response.data:
            # print(f"DEBUG: No employee found for ID: {employee_id}")
            return None
        
        employee = employee_response.data[0]
        
        # Get payroll run data directly (since payroll run contains the calculation results)
        payroll_response = supabase.table("payroll_runs").select("*").eq("id", payroll_run_id).execute()
        if not payroll_response.data:
            # print(f"DEBUG: No payroll run found for ID: {payroll_run_id}")
            return None
            
        payroll_run = payroll_response.data[0]
        
        # Parse allowances
        allowances = payroll_run.get('allowances', {})
        if isinstance(allowances, str):
            import json
            allowances = json.loads(allowances)
            
        # Prepare earnings
        basic_salary = float(employee.get('basic_salary', 0))
        bonus_amount = float(payroll_run.get('bonus', 0))
        
        earning_current = [
            ("Basic Salary", basic_salary),
        ]
        
        # Add individual allowances
        if allowances:
            for allowance_type, amount in allowances.items():
                if amount and float(amount) > 0:
                    earning_current.append((f"{allowance_type.title()} Allowance", float(amount)))
        
        # Add bonuses if any
        if bonus_amount > 0:
            earning_current.append(("Bonus", bonus_amount))
            
        # Get statutory contributions from payroll run
        contributions = {
            'epf_employee': float(payroll_run.get('epf_employee', 0)),
            'epf_employer': float(payroll_run.get('epf_employer', 0)),
            'socso_employee': float(payroll_run.get('socso_employee', 0)),
            'socso_employer': float(payroll_run.get('socso_employer', 0)),
            # EIS enabled
            'eis_employee': float(payroll_run.get('eis_employee', 0)),
            'eis_employer': float(payroll_run.get('eis_employer', 0)),
            'pcb': float(payroll_run.get('pcb', 0))
        }
        
        # Get unpaid leave data from monthly_unpaid_leave table (before using it)
        unpaid_days = 0.0
        unpaid_deduction = 0.0
        
        try:
            # Parse payroll date to get year and month
            payroll_date = payroll_run.get('payroll_date', '')
            if payroll_date:
                date_obj = datetime.strptime(payroll_date, '%Y-%m-%d')
                payroll_year = date_obj.year
                payroll_month = date_obj.month
            else:
                payroll_year = datetime.now().year
                payroll_month = datetime.now().month
            
            # Get monthly unpaid leave data
            employee_id = employee.get('id', '')
            if employee_id:
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(__file__)))
                from services.supabase_service import get_monthly_unpaid_leave_deduction
                unpaid_leave_data = get_monthly_unpaid_leave_deduction(employee_id, payroll_year, payroll_month)
                unpaid_days = unpaid_leave_data.get('unpaid_days', 0.0)
                unpaid_deduction = unpaid_leave_data.get('total_deduction', 0.0)
        except Exception as e:
            print(f"Warning: Could not get unpaid leave data for payslip: {e}")
            unpaid_days = 0.0
            unpaid_deduction = 0.0
        
        # Prepare deductions (including optional contributions and unpaid leave)
        other_deductions_current = []
        
        # Add unpaid leave deduction first (Malaysian standard - show unpaid leave prominently)
        if unpaid_days > 0 and unpaid_deduction > 0:
            other_deductions_current.append((f'Unpaid Leave ({unpaid_days} days)', unpaid_deduction))
        
        # Add optional contributions to deductions
        sip_deduction = float(payroll_run.get('sip_deduction', 0))
        if sip_deduction > 0:
            other_deductions_current.append(('SIP', sip_deduction))
            
        additional_epf = float(payroll_run.get('additional_epf_deduction', 0))
        if additional_epf > 0:
            other_deductions_current.append(('Additional EPF', additional_epf))
            
        prs_deduction = float(payroll_run.get('prs_deduction', 0))
        if prs_deduction > 0:
            other_deductions_current.append(('PRS', prs_deduction))
            
        insurance_premium = float(payroll_run.get('insurance_premium', 0))
        if insurance_premium > 0:
            other_deductions_current.append(('Life Insurance', insurance_premium))
            
        medical_premium = float(payroll_run.get('medical_premium', 0))
        if medical_premium > 0:
            other_deductions_current.append(('Medical Insurance', medical_premium))
            
        other_deductions_amount = float(payroll_run.get('other_deductions', 0))
        if other_deductions_amount > 0:
            other_deductions_current.append(('Other Deductions', other_deductions_amount))
        
        # Get leave data (simplified)
        leave_data = {}
        
        # Parse payroll date (reuse date_obj from unpaid leave section above)
        try:
            if 'date_obj' not in locals():
                payroll_date = payroll_run.get('payroll_date', '')
                if payroll_date:
                    date_obj = datetime.strptime(payroll_date, '%Y-%m-%d')
                else:
                    date_obj = datetime.now()
            
            month = date_obj.strftime('%B')
            year = date_obj.year
            pay_date = date_obj.strftime('%d-%m-%Y')
        except:
            month = datetime.now().strftime('%B')
            year = datetime.now().year
            pay_date = datetime.now().strftime('%d-%m-%Y')
        
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
            # SOCSO/EIS snapshot columns
            ytd_socso = float(payroll_run.get('accumulated_socso_employee_ytd', 0.0) or 0.0)
            ytd_eis = float(payroll_run.get('accumulated_eis_employee_ytd', 0.0) or 0.0)

            # If snapshot columns are all zeros, fallback to payroll_ytd_accumulated table (as of prev month)
            def _fallback_from_ytd_table():
                nonlocal gross_ytd, ytd_epf_emp, ytd_pcb, ytd_socso, ytd_eis
                _pr_date = payroll_run.get('payroll_date', '')
                if not _pr_date:
                    return False
                _dt = datetime.strptime(_pr_date, '%Y-%m-%d')
                prev_month = 12 if _dt.month == 1 else (_dt.month - 1)
                prev_year = _dt.year - 1 if _dt.month == 1 else _dt.year
                emp_email = (employee.get('email') or '').lower()
                if not emp_email:
                    return False
                from services.supabase_service import supabase
                _ytd = (
                    supabase.table('payroll_ytd_accumulated')
                    .select('*')
                    .eq('employee_email', emp_email)
                    .eq('year', prev_year)
                    .eq('month', prev_month)
                    .execute()
                )
                if _ytd and _ytd.data:
                    _row = _ytd.data[0]
                    gross_ytd = float(_row.get('accumulated_gross_salary_ytd', 0.0) or 0.0)
                    ytd_epf_emp = float(_row.get('accumulated_epf_employee_ytd', 0.0) or 0.0)
                    ytd_pcb = float(_row.get('accumulated_pcb_ytd', 0.0) or 0.0)
                    ytd_socso = float(_row.get('accumulated_socso_employee_ytd', 0.0) or 0.0)
                    ytd_eis = float(_row.get('accumulated_eis_employee_ytd', 0.0) or 0.0)
                    return True
                return False

            def _fallback_from_payroll_runs():
                nonlocal gross_ytd, ytd_epf_emp, ytd_pcb, ytd_socso, ytd_eis
                _pr_date = payroll_run.get('payroll_date', '')
                if not _pr_date:
                    return False
                emp_uuid = employee.get('id')
                if not emp_uuid:
                    return False
                from services.supabase_service import supabase
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

            # If core YTDs are all zero, derive them from table or runs
            if gross_ytd == 0.0 and ytd_epf_emp == 0.0 and ytd_pcb == 0.0:
                if not _fallback_from_ytd_table():
                    _fallback_from_payroll_runs()

            # Independently ensure SOCSO/EIS YTD are filled even when core YTDs exist
            if ytd_socso == 0.0 or ytd_eis == 0.0:
                # Try YTD table first to pick up those columns, else compute from runs
                if not _fallback_from_ytd_table():
                    _fallback_from_payroll_runs()
        except Exception as _ytd_err:
            print(f"Warning: could not resolve YTD snapshot for payslip: {_ytd_err}")

        # Build YTD maps for the template
        # Distribute gross YTD into the first income row so the totals show correct YTD
        earning_ytd_map = {}
        if earning_current:
            first_label = earning_current[0][0]
            earning_ytd_map[first_label] = gross_ytd
            for lbl, _amt in earning_current[1:]:
                earning_ytd_map[lbl] = 0.0
        else:
            earning_ytd_map = {}

        ytd_deductions_map = {
            'epf_emp': ytd_epf_emp,
            'socso': ytd_socso,
            'pcb': ytd_pcb,
            'eis': ytd_eis,
        }

        # Format data for payslip generator
        # Prefer 'position' field; fallback to legacy 'job_title'
        emp_position = employee.get('position') or employee.get('job_title') or ''
        payslip_data = {
            "employee": {
                "name": employee.get('full_name', ''),
                "staff_no": employee.get('employee_id', ''),
                "ic": employee.get('ic_number', employee.get('nric', '')),
                "position": emp_position,
                "epf_no": employee.get('epf_number', ''),
                "socso_no": employee.get('socso_number', ''),
                "bank": employee.get('bank_name', ''),
                "acct": employee.get('bank_account', '')
            },
            "earning_current": earning_current,
            "earning_ytd": earning_ytd_map,
            "other_deductions_current": other_deductions_current,
            # We do not track per-line YTD for other deductions; default zeros will be used in the template
            "other_deductions_ytd": {},
            "statutory_contributions": contributions,
            "ytd": ytd_deductions_map,
            "leave": leave_data,
            "unpaid_leave": {
                "days": unpaid_days,
                "deduction": unpaid_deduction
            },
            "month": month,
            "year": year,
            "pay_date": pay_date
        }
        
        return payslip_data
        
    except Exception as e:
        # print(f"DEBUG: Error fetching payslip data: {e}")
        return None

# --------------------------
# Core generator (same as testing.py with minor modifications)
# --------------------------
def generate_payslip(data, output_path=None):
    """
    Generate payslip PDF using the template from testing.py
    """
    try:
        filename = output_path or f"Payslip_{data['employee']['staff_no']}_{data['month']}_{data['year']}.pdf"

        c = canvas.Canvas(filename, pagesize=A4)
        W, H = A4

        # Header: logo + company
        logo = download_logo_stream(LOGO_URL)
        logo_size = 28 * mm
        left_margin = 18 * mm
        top_y = H - 18 * mm

        text_x = left_margin
        if logo:
            c.drawImage(logo, left_margin, top_y - logo_size, width=logo_size, height=logo_size, mask='auto')
            text_x = left_margin + logo_size + 6 * mm

        c.setFont("Helvetica-Bold", 14)
        c.drawString(text_x, top_y - 4 * mm, COMPANY_NAME)
        c.setFont("Helvetica", 9)
        c.drawString(text_x, top_y - 10 * mm, f"SSM No: {SSM_NO}")
        for idx, line in enumerate(COMPANY_ADDRESS_LINES):
            c.drawString(text_x, top_y - (14 + idx * 6), line)

        # Payslip meta
        c.setFont("Helvetica-Bold", 7)
        c.drawRightString(W - 18*mm, top_y - 4*mm, f"Payslip for {data['month']} {data['year']}")
        c.setFont("Helvetica", 9)
        c.drawRightString(W - 18*mm, top_y - 11*mm, f"Date: {data.get('pay_date', datetime.now().strftime('%d-%m-%Y'))}")

        # Employee block (boxed)
        block_x = left_margin
        block_y = top_y - 44*mm
        box_w = W - 36*mm
        box_h = 20 * mm
        c.roundRect(block_x, block_y - box_h, box_w, box_h, 3*mm, stroke=1, fill=0)
        c.setFont("Helvetica-Bold", 10)
        emp = data['employee']
        c.drawString(block_x + 4*mm, block_y - 6*mm, f"NAME: {emp['name']}")
        c.drawString(block_x + 4*mm, block_y - 12*mm, f"STAFF NO: {emp['staff_no']}   NRIC: {emp.get('ic','-')}")
        # right side employee extras
        right_info_x = block_x + box_w - 70*mm
        c.drawRightString(right_info_x + 70*mm - 4*mm, block_y - 6*mm, f"Position: {emp.get('position','-')}")
        c.drawRightString(right_info_x + 70*mm - 4*mm, block_y - 12*mm, f"EPF No: {emp.get('epf_no','-')}   SOCSO: {emp.get('socso_no','-')}")

        # Income and Deductions tables (two columns with Current / YTD)
        table_x = left_margin
        table_y = block_y - box_h - 8*mm
        col_gap = 12*mm
        col1_w = (W - 2*left_margin - col_gap) / 2
        col2_w = col1_w

        # Left: Income
        c.setFont("Helvetica-Bold", 10)
        c.drawString(table_x, table_y, "INCOME")
        c.setFont("Helvetica", 9)
        income_x = table_x
        income_y = table_y - 6*mm
        row_h = 7*mm
        # header
        c.setFont("Helvetica-Bold", 9)
        c.drawString(income_x + 2*mm, income_y, "Description")
        c.drawRightString(income_x + col1_w - 22*mm, income_y, "Current")
        c.drawRightString(income_x + col1_w - 2*mm, income_y, "Y-T-D")
        c.setFont("Helvetica", 9)

        # Fill income rows
        y = income_y - row_h
        gross_current = 0.0
        gross_ytd = 0.0
        for lbl, amt in data['earning_current']:
            y_curr = float(amt)
            y_ytd = float(data['earning_ytd'].get(lbl, 0.0))
            c.drawString(income_x + 2*mm, y, lbl)
            c.drawRightString(income_x + col1_w - 22*mm, y, money(y_curr))
            c.drawRightString(income_x + col1_w - 2*mm, y, money(y_ytd))
            y -= row_h
            gross_current += y_curr
            gross_ytd += y_ytd

        # Gross totals
        c.setFont("Helvetica-Bold", 9)
        c.drawString(income_x + 2*mm, y - 2*mm, "Gross Total")
        c.drawRightString(income_x + col1_w - 22*mm, y - 2*mm, money(gross_current))
        c.drawRightString(income_x + col1_w - 2*mm, y - 2*mm, money(gross_ytd))
        c.setFont("Helvetica", 9)

        # Right: Deductions
        ded_x = table_x + col1_w + col_gap
        c.setFont("Helvetica-Bold", 10)
        c.drawString(ded_x, table_y, "DEDUCTION")
        c.setFont("Helvetica", 9)
        ded_y = income_y

        c.setFont("Helvetica-Bold", 9)
        c.drawString(ded_x + 2*mm, ded_y, "Description")
        c.drawRightString(ded_x + col2_w - 22*mm, ded_y, "Current")
        c.drawRightString(ded_x + col2_w - 2*mm, ded_y, "Y-T-D")
        c.setFont("Helvetica", 9)

        y2 = ded_y - row_h
        total_ded_current = 0.0
        total_ded_ytd = 0.0

        # Use actual calculated contributions
        contributions = data.get('statutory_contributions', {})
        epf_emp = contributions.get('epf_employee', 0.0)
        epf_er = contributions.get('epf_employer', 0.0)
        socso_emp = contributions.get('socso_employee', 0.0)
        socso_er = contributions.get('socso_employer', 0.0)
        eis_emp = contributions.get('eis_employee', 0.0)
        eis_er = contributions.get('eis_employer', 0.0)
        pcb = contributions.get('pcb', 0.0)

        # other deductions first
        for lbl, amt in data.get('other_deductions_current', []):
            ycur = float(amt)
            yytd = float(data.get('other_deductions_ytd', {}).get(lbl, 0.0))
            c.drawString(ded_x + 2*mm, y2, lbl)
            c.drawRightString(ded_x + col2_w - 22*mm, y2, money(ycur))
            c.drawRightString(ded_x + col2_w - 2*mm, y2, money(yytd))
            y2 -= row_h
            total_ded_current += ycur
            total_ded_ytd += yytd

        # EPF (Employee)
        c.drawString(ded_x + 2*mm, y2, "EPF (Employee)")
        c.drawRightString(ded_x + col2_w - 22*mm, y2, money(epf_emp))
        c.drawRightString(ded_x + col2_w - 2*mm, y2, money(data.get('ytd', {}).get('epf_emp', 0.0)))
        y2 -= row_h
        total_ded_current += epf_emp
        total_ded_ytd += data.get('ytd', {}).get('epf_emp', 0.0)

        # SOCSO
        c.drawString(ded_x + 2*mm, y2, "SOCSO")
        c.drawRightString(ded_x + col2_w - 22*mm, y2, money(socso_emp))
        c.drawRightString(ded_x + col2_w - 2*mm, y2, money(data.get('ytd', {}).get('socso', 0.0)))
        y2 -= row_h
        total_ded_current += socso_emp
        total_ded_ytd += data.get('ytd', {}).get('socso', 0.0)

        # PCB
        c.drawString(ded_x + 2*mm, y2, "PCB")
        c.drawRightString(ded_x + col2_w - 22*mm, y2, money(pcb))
        c.drawRightString(ded_x + col2_w - 2*mm, y2, money(data.get('ytd', {}).get('pcb', 0.0)))
        y2 -= row_h
        total_ded_current += pcb
        total_ded_ytd += data.get('ytd', {}).get('pcb', 0.0)

        # EIS
        c.drawString(ded_x + 2*mm, y2, "EIS")
        c.drawRightString(ded_x + col2_w - 22*mm, y2, money(eis_emp))
        c.drawRightString(ded_x + col2_w - 2*mm, y2, money(data.get('ytd', {}).get('eis', 0.0)))
        y2 -= row_h
        total_ded_current += eis_emp
        total_ded_ytd += data.get('ytd', {}).get('eis', 0.0)

        # Totals
        c.setFont("Helvetica-Bold", 9)
        c.drawString(ded_x + 2*mm, y2, "Total Deductions")
        c.drawRightString(ded_x + col2_w - 22*mm, y2, money(total_ded_current))
        c.drawRightString(ded_x + col2_w - 2*mm, y2, money(total_ded_ytd))
        y2 -= row_h

        # Employer contributions block (below tables)
        emp_cont_x = left_margin
        emp_cont_y = min(y - 8*mm, y2 - 8*mm) - 6*mm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(emp_cont_x, emp_cont_y, "Employer Contributions")
        c.setFont("Helvetica", 9)
        c.drawString(emp_cont_x + 4*mm, emp_cont_y - 6*mm, f"Employer EPF: RM {money(epf_er)}")
        c.drawString(emp_cont_x + 4*mm, emp_cont_y - 12*mm, f"Employer SOCSO: RM {money(socso_er)}")
        c.drawString(emp_cont_x + 4*mm, emp_cont_y - 18*mm, f"Employer EIS: RM {money(eis_er)}")

        # Totals / Net / End Month Pay (right side)
        gross = gross_current
        net = gross - total_ded_current
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(W - 18*mm, emp_cont_y, f"Gross Income : RM {money(gross)}")
        c.drawRightString(W - 18*mm, emp_cont_y - 7*mm, f"Total Deductions : RM {money(total_ded_current)}")
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(W - 18*mm, emp_cont_y - 16*mm, f"Net Income : RM {money(net)}")
        c.setFont("Helvetica", 9)
        c.drawRightString(W - 18*mm, emp_cont_y - 23*mm, f"End Month Pay : RM {money(net)}")

        # Net in words
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(emp_cont_x, emp_cont_y - 30*mm, f"In Words: {money_words(net)}")

        # Leave summary and unpaid leave details at bottom
        leave_y = 28*mm
        c.setFont("Helvetica", 8)
        leave_text = "  ".join([f"{k} Leave = {v[0]}, Balance = {v[1]}, YTD = {v[2]}" for k, v in data.get('leave', {}).items()])
        if leave_text.strip():
            c.drawString(left_margin, leave_y, leave_text)
            leave_y -= 4*mm

        # Unpaid leave information (Malaysian compliance)
        unpaid_leave_info = data.get('unpaid_leave', {})
        if unpaid_leave_info.get('days', 0) > 0:
            unpaid_text = f"Unpaid Leave: {unpaid_leave_info['days']} days (Deduction: RM {money(unpaid_leave_info['deduction'])})"
            c.setFont("Helvetica-Bold", 8)
            c.drawString(left_margin, leave_y, unpaid_text)
            c.setFont("Helvetica", 8)

        # Signature lines (Prepared by / Approved by / Employee)
        sig_y = 50*mm
        sig_x_start = left_margin
        sig_width = 40*mm
        gap = 20*mm

        # Prepared by
        c.line(sig_x_start, sig_y, sig_x_start + sig_width, sig_y)
        c.setFont("Helvetica", 8)
        c.drawString(sig_x_start, sig_y - 5*mm, "Prepared By (Name & Signature)")

        # Approved by
        app_x = sig_x_start + sig_width + gap
        c.line(app_x, sig_y, app_x + sig_width, sig_y)
        c.drawString(app_x, sig_y - 5*mm, "Approved By (Name & Signature)")

        # Employee acknowledgement
        emp_x = app_x + sig_width + gap
        c.line(emp_x, sig_y, emp_x + (sig_width + 12*mm), sig_y)
        c.drawString(emp_x, sig_y - 5*mm, "Employee (Acknowledgement & Signature)")

        # Footer
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.grey)
        c.drawCentredString(W/2, 12*mm, "This is a computer-generated payslip and does not require a signature.")
        c.setFillColor(colors.black)

        c.save()
        return filename

    except Exception:
        return None

def generate_payslip_for_employee(employee_id, payroll_run_id, output_path=None):
    """Generate payslip for a specific employee and payroll run"""
    try:
        # Get payslip data from database
        payslip_data = get_employee_payslip_data(employee_id, payroll_run_id)
        if not payslip_data:
            # print(f"DEBUG: No payslip data found for employee {employee_id}, payroll run {payroll_run_id}")
            return None
            
        # Generate the PDF
        return generate_payslip(payslip_data, output_path)
        
    except Exception as e:
        # print(f"DEBUG: Error generating payslip for employee: {e}")
        return None
