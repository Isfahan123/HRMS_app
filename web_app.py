"""
Web application entry point for HRMS
This provides a web-based interface using HTML/JavaScript with Python backend
"""
from fastapi import FastAPI, HTTPException, Request, Depends, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
from datetime import datetime

# Import existing services and business logic
from services.supabase_service import (
    login_user_by_username, 
    supabase, 
    get_attendance_history, 
    fetch_user_leave_requests,
    convert_utc_to_kl,
    get_employee_payroll_history,
    get_all_attendance_records,
    update_leave_request_status,
    get_payroll_runs,
    submit_leave_request,
    insert_employee,
    update_employee,
    run_payroll
)
from services.supabase_engagements import fetch_engagements
from services.supabase_training_overseas import (
    fetch_training_course_records,
    fetch_overseas_work_trip_records
)
from core.employee_service import calculate_cumulative_service

app = FastAPI(title="HRMS Web Application")

# Setup templates and static files
templates_dir = os.path.join(os.path.dirname(__file__), "web", "templates")
static_dir = os.path.join(os.path.dirname(__file__), "web", "static")

# Create directories if they don't exist
os.makedirs(templates_dir, exist_ok=True)
os.makedirs(static_dir, exist_ok=True)
os.makedirs(os.path.join(static_dir, "css"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "js"), exist_ok=True)

templates = Jinja2Templates(directory=templates_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Pydantic models for request/response
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    role: Optional[str] = None
    email: Optional[str] = None
    locked_until: Optional[str] = None

class EmployeeData(BaseModel):
    email: str
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None

# Routes
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve the dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/admin-dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Serve the admin dashboard page"""
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

@app.get("/demo", response_class=HTMLResponse)
async def demo_dashboard(request: Request):
    """Serve the demo dashboard page (for testing UI without auth)"""
    return templates.TemplateResponse("demo_dashboard.html", {"request": request})

@app.get("/WEB_INTERFACE_GUIDE.md")
async def serve_guide():
    """Serve the web interface guide"""
    import os
    guide_path = os.path.join(os.path.dirname(__file__), "WEB_INTERFACE_GUIDE.md")
    if os.path.exists(guide_path):
        with open(guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"content": content, "format": "markdown"}
    return {"error": "Guide not found"}

# API Endpoints
@app.post("/api/login", response_model=LoginResponse)
async def api_login(login_data: LoginRequest):
    """
    Handle user login
    Reuses existing login_user_by_username function from services
    """
    try:
        username = login_data.username.strip().lower()
        password = login_data.password
        
        if not username or not password:
            return LoginResponse(
                success=False,
                message="Please enter both username and password"
            )
        
        result = login_user_by_username(username, password)
        
        # Check if account is locked
        if result and result.get("locked_until"):
            locked_until = result.get("locked_until")
            try:
                display_locked = convert_utc_to_kl(locked_until)
            except Exception:
                display_locked = locked_until
            
            return LoginResponse(
                success=False,
                message=f"Account is locked until {display_locked} (Malaysia Time)",
                locked_until=display_locked
            )
        
        # Check if login successful
        if result and result.get("role"):
            return LoginResponse(
                success=True,
                message="Login successful",
                role=result["role"].lower(),
                email=result.get("email", "").lower()
            )
        else:
            return LoginResponse(
                success=False,
                message="Invalid username or password"
            )
            
    except Exception as e:
        print(f"Login error: {str(e)}")
        return LoginResponse(
            success=False,
            message="An error occurred during login"
        )

@app.get("/api/employee/{email}")
async def get_employee_data(email: str):
    """
    Get employee data by email
    """
    try:
        response = supabase.table("employees").select("*").eq("email", email.lower()).execute()
        if response.data and len(response.data) > 0:
            return {"success": True, "data": response.data[0]}
        else:
            return {"success": False, "message": "Employee not found"}
    except Exception as e:
        print(f"Error fetching employee: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/attendance/{email}")
async def get_attendance(email: str):
    """
    Get attendance history for employee
    Reuses existing get_attendance_history function
    """
    try:
        attendance_data = get_attendance_history(email)
        return {"success": True, "data": attendance_data}
    except Exception as e:
        print(f"Error fetching attendance: {str(e)}")
        return {"success": False, "message": str(e)}

@app.get("/api/leave-requests/{email}")
async def get_leave_requests(email: str):
    """
    Get leave requests for employee
    Reuses existing fetch_user_leave_requests function
    """
    try:
        leave_requests = fetch_user_leave_requests(email)
        return {"success": True, "data": leave_requests}
    except Exception as e:
        print(f"Error fetching leave requests: {str(e)}")
        return {"success": False, "message": str(e)}

@app.get("/api/employees")
async def list_employees():
    """
    List all employees (admin only - add authentication later)
    """
    try:
        response = supabase.table("employees").select("*").execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        print(f"Error listing employees: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/payroll/{employee_id}")
async def get_payroll_history(employee_id: str):
    """
    Get payroll history for employee
    Reuses existing get_employee_payroll_history function
    """
    try:
        payroll_data = get_employee_payroll_history(employee_id)
        return {"success": True, "data": payroll_data}
    except Exception as e:
        print(f"Error fetching payroll: {str(e)}")
        return {"success": False, "message": str(e)}

@app.get("/api/engagements/{employee_id}")
async def get_engagements(employee_id: str):
    """
    Get engagements (training & trips) for employee
    """
    try:
        # Fetch engagements
        engagements = fetch_engagements(employee_id=employee_id)
        
        # Fetch training courses
        training = fetch_training_course_records(employee_id=employee_id)
        
        # Fetch overseas trips
        trips = fetch_overseas_work_trip_records(employee_id=employee_id)
        
        return {
            "success": True, 
            "data": {
                "engagements": engagements or [],
                "training": training or [],
                "trips": trips or []
            }
        }
    except Exception as e:
        print(f"Error fetching engagements: {str(e)}")
        return {"success": False, "message": str(e)}

@app.get("/api/admin/attendance")
async def get_all_attendance():
    """
    Get all attendance records (admin only)
    """
    try:
        attendance_data = get_all_attendance_records()
        return {"success": True, "data": attendance_data}
    except Exception as e:
        print(f"Error fetching all attendance: {str(e)}")
        return {"success": False, "message": str(e)}

@app.get("/api/admin/leave-requests")
async def get_all_leave_requests():
    """
    Get all leave requests for admin approval
    """
    try:
        response = supabase.table("leave_requests").select("*, employees(full_name, email)").order("created_at", desc=True).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        print(f"Error fetching leave requests: {str(e)}")
        return {"success": False, "message": str(e)}

@app.post("/api/admin/leave-requests/{leave_id}/approve")
async def approve_leave_request(leave_id: str):
    """
    Approve a leave request
    """
    try:
        # Get admin email from session (for now using a placeholder)
        admin_email = "admin@hrms.com"
        success = update_leave_request_status(leave_id, "approved", admin_email)
        if success:
            return {"success": True, "message": "Leave request approved"}
        else:
            return {"success": False, "message": "Failed to approve leave request"}
    except Exception as e:
        print(f"Error approving leave: {str(e)}")
        return {"success": False, "message": str(e)}

@app.post("/api/admin/leave-requests/{leave_id}/reject")
async def reject_leave_request(leave_id: str):
    """
    Reject a leave request
    """
    try:
        # Get admin email from session (for now using a placeholder)
        admin_email = "admin@hrms.com"
        success = update_leave_request_status(leave_id, "rejected", admin_email)
        if success:
            return {"success": True, "message": "Leave request rejected"}
        else:
            return {"success": False, "message": "Failed to reject leave request"}
    except Exception as e:
        print(f"Error rejecting leave: {str(e)}")
        return {"success": False, "message": str(e)}

@app.post("/api/leave-requests/submit")
async def submit_new_leave_request(request: Request):
    """
    Submit a new leave request
    """
    try:
        data = await request.json()
        employee_email = data.get("employee_email")
        leave_type = data.get("leave_type")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        title = data.get("title", "Leave Request")
        is_half_day = data.get("is_half_day", False)
        half_day_period = data.get("half_day_period")
        
        if not all([employee_email, leave_type, start_date, end_date]):
            return {"success": False, "message": "Missing required fields"}
        
        success = submit_leave_request(
            employee_email=employee_email,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            title=title,
            is_half_day=is_half_day,
            half_day_period=half_day_period
        )
        
        if success:
            return {"success": True, "message": "Leave request submitted successfully"}
        else:
            return {"success": False, "message": "Failed to submit leave request"}
    except Exception as e:
        print(f"Error submitting leave request: {str(e)}")
        return {"success": False, "message": str(e)}

@app.put("/api/employee/{email}")
async def update_employee_profile(email: str, request: Request):
    """
    Update employee profile information
    """
    try:
        data = await request.json()
        
        # Get employee_id first
        emp_response = supabase.table("employees").select("id").eq("email", email.lower()).execute()
        if not emp_response.data or len(emp_response.data) == 0:
            return {"success": False, "message": "Employee not found"}
        
        employee_id = emp_response.data[0]["id"]
        
        # Update employee
        result = update_employee(employee_id, data)
        
        if result:
            return {"success": True, "message": "Profile updated successfully", "data": result}
        else:
            return {"success": False, "message": "Failed to update profile"}
    except Exception as e:
        print(f"Error updating employee: {str(e)}")
        return {"success": False, "message": str(e)}

@app.post("/api/admin/employees")
async def create_new_employee(request: Request):
    """
    Create a new employee (admin only)
    """
    try:
        data = await request.json()
        password = data.pop("password", None)
        
        result = insert_employee(data, password)
        
        if result:
            return {"success": True, "message": "Employee created successfully", "data": result}
        else:
            return {"success": False, "message": "Failed to create employee"}
    except Exception as e:
        print(f"Error creating employee: {str(e)}")
        return {"success": False, "message": str(e)}

@app.put("/api/admin/employees/{employee_id}")
async def update_employee_admin(employee_id: str, request: Request):
    """
    Update employee information (admin only)
    """
    try:
        data = await request.json()
        
        result = update_employee(employee_id, data)
        
        if result:
            return {"success": True, "message": "Employee updated successfully", "data": result}
        else:
            return {"success": False, "message": "Failed to update employee"}
    except Exception as e:
        print(f"Error updating employee: {str(e)}")
        return {"success": False, "message": str(e)}

@app.get("/api/admin/payroll-runs")
async def get_all_payroll_runs():
    """
    Get all payroll runs (admin only)
    """
    try:
        payroll_runs = get_payroll_runs()
        return {"success": True, "data": payroll_runs}
    except Exception as e:
        print(f"Error fetching payroll runs: {str(e)}")
        return {"success": False, "message": str(e)}

@app.post("/api/admin/payroll/run")
async def run_payroll_processing(request: Request):
    """
    Run payroll for a specific month/year (admin only)
    """
    try:
        data = await request.json()
        payroll_date = data.get("payroll_date")  # Format: YYYY-MM
        
        if not payroll_date:
            return {"success": False, "message": "Payroll date is required"}
        
        success = run_payroll(payroll_date)
        
        if success:
            return {"success": True, "message": f"Payroll processed successfully for {payroll_date}"}
        else:
            return {"success": False, "message": "Failed to process payroll"}
    except Exception as e:
        print(f"Error running payroll: {str(e)}")
        return {"success": False, "message": str(e)}

@app.get("/api/admin/bonuses")
async def get_all_bonuses():
    """
    Get all bonus records (admin only)
    """
    try:
        response = supabase.table("bonuses").select("*, employees(full_name, email)").order("created_at", desc=True).execute()
        return {"success": True, "data": response.data}
    except Exception as e:
        print(f"Error fetching bonuses: {str(e)}")
        return {"success": False, "message": str(e)}

@app.post("/api/admin/bonuses")
async def create_bonus(request: Request):
    """
    Create a new bonus record (admin only)
    """
    try:
        data = await request.json()
        
        response = supabase.table("bonuses").insert(data).execute()
        
        if response.data:
            return {"success": True, "message": "Bonus created successfully", "data": response.data}
        else:
            return {"success": False, "message": "Failed to create bonus"}
    except Exception as e:
        print(f"Error creating bonus: {str(e)}")
        return {"success": False, "message": str(e)}

@app.put("/api/admin/bonuses/{bonus_id}")
async def update_bonus(bonus_id: str, request: Request):
    """
    Update a bonus record (admin only)
    """
    try:
        data = await request.json()
        
        response = supabase.table("bonuses").update(data).eq("id", bonus_id).execute()
        
        if response.data:
            return {"success": True, "message": "Bonus updated successfully", "data": response.data}
        else:
            return {"success": False, "message": "Failed to update bonus"}
    except Exception as e:
        print(f"Error updating bonus: {str(e)}")
        return {"success": False, "message": str(e)}

@app.delete("/api/admin/bonuses/{bonus_id}")
async def delete_bonus(bonus_id: str):
    """
    Delete a bonus record (admin only)
    """
    try:
        response = supabase.table("bonuses").delete().eq("id", bonus_id).execute()
        
        if response.data:
            return {"success": True, "message": "Bonus deleted successfully"}
        else:
            return {"success": False, "message": "Failed to delete bonus"}
    except Exception as e:
        print(f"Error deleting bonus: {str(e)}")
        return {"success": False, "message": str(e)}

@app.get("/api/payroll/payslip/{employee_id}/{payroll_run_id}")
async def generate_payslip(employee_id: str, payroll_run_id: str):
    """
    Generate and download payslip PDF for an employee
    Uses Node.js payslip generator module
    """
    try:
        import subprocess
        import json
        import tempfile
        from fastapi.responses import FileResponse
        
        # Get employee data
        employee_response = supabase.table("employees").select("*").eq("id", employee_id).execute()
        if not employee_response.data:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        employee = employee_response.data[0]
        
        # Get payroll run data
        payroll_response = supabase.table("payroll_runs").select("*").eq("id", payroll_run_id).execute()
        if not payroll_response.data:
            raise HTTPException(status_code=404, detail="Payroll run not found")
        
        payroll = payroll_response.data[0]
        
        # Prepare payslip data
        payslip_data = {
            "employee_name": employee.get("full_name", ""),
            "employee_id": employee.get("employee_id", ""),
            "department": employee.get("department", ""),
            "position": employee.get("position", ""),
            "pay_period": payroll.get("month_year", ""),
            "pay_date": payroll.get("created_at", "")[:10] if payroll.get("created_at") else "",
            "basic_salary": float(payroll.get("basic_salary", 0)),
            "allowances": float(payroll.get("allowances", 0)),
            "bonuses": float(payroll.get("bonuses", 0)),
            "epf_employee": float(payroll.get("epf_employee", 0)),
            "socso_employee": float(payroll.get("socso_employee", 0)),
            "eis": float(payroll.get("eis", 0)),
            "pcb": float(payroll.get("pcb", 0)),
            "unpaid_leave_deduction": float(payroll.get("unpaid_leave_deduction", 0))
        }
        
        # Create temp directory for output
        temp_dir = tempfile.gettempdir()
        output_filename = f"payslip_{employee.get('employee_id', employee_id)}_{payroll.get('month_year', 'unknown').replace('/', '_')}.pdf"
        output_path = os.path.join(temp_dir, output_filename)
        
        # Write data to temp JSON file
        data_file = os.path.join(temp_dir, f"payslip_data_{employee_id}.json")
        with open(data_file, 'w') as f:
            json.dump(payslip_data, f)
        
        # Call Node.js to generate PDF
        node_script = f"""
const {{ generatePayslip }} = require('./web/nodejs_modules/payslip_generator');
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('{data_file}', 'utf8'));
generatePayslip(data, '{output_path}')
    .then(() => {{ console.log('PDF generated'); process.exit(0); }})
    .catch(err => {{ console.error('Error:', err); process.exit(1); }});
"""
        
        # Run the Node.js script
        result = subprocess.run(
            ['node', '-e', node_script],
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Clean up temp data file
        try:
            os.remove(data_file)
        except:
            pass
        
        if result.returncode != 0:
            print(f"Node.js error: {result.stderr}")
            raise HTTPException(status_code=500, detail=f"Failed to generate payslip: {result.stderr}")
        
        # Check if PDF was created
        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="Payslip PDF was not generated")
        
        # Return the PDF file
        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename=output_filename,
            headers={"Content-Disposition": f"attachment; filename={output_filename}"}
        )
        
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Payslip generation timed out")
    except Exception as e:
        print(f"Error generating payslip: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/leave-balances")
async def get_leave_balances():
    """
    Get annual leave balances for all employees
    """
    try:
        from services.supabase_service import get_employee_leave_balances
        current_year = datetime.now().year
        balances = get_employee_leave_balances(current_year)
        return {"success": True, "data": balances}
    except Exception as e:
        print(f"Error getting leave balances: {str(e)}")
        return {"success": False, "message": str(e)}

@app.get("/api/admin/sick-leave-balances")
async def get_sick_leave_balances():
    """
    Get sick leave balances for all employees
    """
    try:
        # Query employees and their sick leave balances
        current_year = datetime.now().year
        response = supabase.table("employees").select("id, employee_id, full_name, email").execute()
        
        if not response.data:
            return {"success": True, "data": []}
        
        balances = []
        for employee in response.data:
            from services.supabase_service import get_individual_employee_sick_leave_balance
            balance = get_individual_employee_sick_leave_balance(employee['email'], current_year)
            balances.append({
                "employee_id": employee['employee_id'],
                "full_name": employee['full_name'],
                "email": employee['email'],
                "total_sick_leave": balance.get('total_sick_leave', 14),
                "used_sick_leave": balance.get('used_sick_leave', 0),
                "remaining_sick_leave": balance.get('remaining_sick_leave', 14)
            })
        
        return {"success": True, "data": balances}
    except Exception as e:
        print(f"Error getting sick leave balances: {str(e)}")
        return {"success": False, "message": str(e)}

@app.get("/api/admin/unpaid-leave-summary")
async def get_unpaid_leave_summary():
    """
    Get unpaid leave summary for all employees
    """
    try:
        from services.supabase_service import get_monthly_unpaid_leave_summary
        current_year = datetime.now().year
        
        # Get all employees
        response = supabase.table("employees").select("id, employee_id, full_name, email").execute()
        
        if not response.data:
            return {"success": True, "data": []}
        
        summaries = []
        for employee in response.data:
            summary = get_monthly_unpaid_leave_summary(employee['id'], current_year)
            total_unpaid = sum([month.get('unpaid_days', 0) for month in summary])
            summaries.append({
                "employee_id": employee['employee_id'],
                "full_name": employee['full_name'],
                "email": employee['email'],
                "total_unpaid_days": total_unpaid,
                "monthly_breakdown": summary
            })
        
        return {"success": True, "data": summaries}
    except Exception as e:
        print(f"Error getting unpaid leave summary: {str(e)}")
        return {"success": False, "message": str(e)}

@app.get("/api/admin/payroll-contributions")
async def get_payroll_contributions():
    """
    Get EPF, SOCSO, EIS contributions summary
    """
    try:
        # Get all payroll runs
        response = supabase.table("payroll_runs").select("*").order("created_at", desc=True).limit(100).execute()
        
        if not response.data:
            return {"success": True, "data": []}
        
        contributions = []
        for run in response.data:
            contributions.append({
                "employee_name": run.get('employee_name', ''),
                "month_year": run.get('month_year', ''),
                "epf_employee": float(run.get('epf_employee', 0)),
                "epf_employer": float(run.get('epf_employer', 0)),
                "socso_employee": float(run.get('socso_employee', 0)),
                "socso_employer": float(run.get('socso_employer', 0)),
                "eis": float(run.get('eis', 0)),
                "pcb": float(run.get('pcb', 0)),
                "total_employee": float(run.get('epf_employee', 0)) + float(run.get('socso_employee', 0)) + float(run.get('eis', 0)),
                "total_employer": float(run.get('epf_employer', 0)) + float(run.get('socso_employer', 0))
            })
        
        return {"success": True, "data": contributions}
    except Exception as e:
        print(f"Error getting contributions: {str(e)}")
        return {"success": False, "message": str(e)}

@app.post("/api/admin/contributions/upload-rates")
async def upload_contribution_rates(contribution_type: str, file: UploadFile = File(...)):
    """
    Upload PDF containing EPF/SOCSO/EIS contribution rate tables
    """
    try:
        # Validate contribution type
        if contribution_type not in ['epf', 'socso', 'eis']:
            return {"success": False, "message": "Invalid contribution type. Must be epf, socso, or eis"}
        
        # Validate file type
        if not file.filename.endswith('.pdf'):
            return {"success": False, "message": "Only PDF files are supported"}
        
        # Save the uploaded file temporarily
        import tempfile
        import shutil
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name
        
        try:
            # For EPF, use the dedicated parser if available
            if contribution_type == 'epf':
                try:
                    from services.epf_pdf_parser import upload_and_parse_epf_pdf
                    upload_and_parse_epf_pdf(tmp_path, supabase)
                    return {"success": True, "message": f"EPF rates uploaded and parsed successfully"}
                except ImportError:
                    # Fall back to generic parsing
                    pass
            
            # Generic PDF parsing for SOCSO/EIS or EPF fallback
            # For now, just acknowledge the upload
            # TODO: Implement PDF parsing for SOCSO and EIS
            return {
                "success": True, 
                "message": f"{contribution_type.upper()} rate table uploaded successfully. Parsing functionality will be implemented soon.",
                "note": "Manual rate verification recommended until parsing is fully implemented"
            }
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            
    except Exception as e:
        print(f"Error uploading contribution rates: {str(e)}")
        return {"success": False, "message": f"Error uploading file: {str(e)}"}

# Variable Percentage API Endpoints
@app.get("/api/admin/variable-percentage")
async def get_variable_percentage_rules():
    """
    Get all variable percentage rules
    """
    try:
        response = supabase.table("variable_percentage_rules").select("*").order("created_at", desc=True).execute()
        return {"success": True, "data": response.data or []}
    except Exception as e:
        print(f"Error getting variable percentage rules: {str(e)}")
        return {"success": False, "message": str(e), "data": []}

@app.post("/api/admin/variable-percentage")
async def create_variable_percentage_rule(request: Request):
    """
    Create a new variable percentage rule
    """
    try:
        data = await request.json()
        
        # Validate required fields
        required_fields = ['name', 'type', 'percentage', 'apply_to', 'base_on', 'frequency', 'status']
        for field in required_fields:
            if field not in data or not data[field]:
                return {"success": False, "message": f"Missing required field: {field}"}
        
        # Validate percentage
        try:
            percentage = float(data['percentage'])
            if percentage < 0 or percentage > 100:
                return {"success": False, "message": "Percentage must be between 0 and 100"}
        except ValueError:
            return {"success": False, "message": "Invalid percentage value"}
        
        # Add timestamp
        data['created_at'] = datetime.utcnow().isoformat()
        
        response = supabase.table("variable_percentage_rules").insert(data).execute()
        
        if response.data:
            return {"success": True, "message": "Variable percentage rule created successfully", "data": response.data[0]}
        else:
            return {"success": False, "message": "Failed to create rule"}
    except Exception as e:
        print(f"Error creating variable percentage rule: {str(e)}")
        return {"success": False, "message": str(e)}

@app.put("/api/admin/variable-percentage/{rule_id}")
async def update_variable_percentage_rule(rule_id: str, request: Request):
    """
    Update an existing variable percentage rule
    """
    try:
        data = await request.json()
        
        # Remove fields that shouldn't be updated
        data.pop('id', None)
        data.pop('created_at', None)
        
        # Add updated timestamp
        data['updated_at'] = datetime.utcnow().isoformat()
        
        response = supabase.table("variable_percentage_rules").update(data).eq("id", rule_id).execute()
        
        if response.data:
            return {"success": True, "message": "Rule updated successfully", "data": response.data[0]}
        else:
            return {"success": False, "message": "Failed to update rule"}
    except Exception as e:
        print(f"Error updating variable percentage rule: {str(e)}")
        return {"success": False, "message": str(e)}

@app.delete("/api/admin/variable-percentage/{rule_id}")
async def delete_variable_percentage_rule(rule_id: str):
    """
    Delete a variable percentage rule
    """
    try:
        response = supabase.table("variable_percentage_rules").delete().eq("id", rule_id).execute()
        
        if response.data:
            return {"success": True, "message": "Rule deleted successfully"}
        else:
            return {"success": False, "message": "Failed to delete rule"}
    except Exception as e:
        print(f"Error deleting variable percentage rule: {str(e)}")
        return {"success": False, "message": str(e)}

@app.get("/api/admin/salary-history")
async def get_salary_history():
    """
    Get salary change history for employees
    """
    try:
        # Query salary history from employee_history table
        response = supabase.table("employee_history").select("*").order("effective_date", desc=True).limit(100).execute()
        
        if not response.data:
            return {"success": True, "data": []}
        
        # Filter for salary-related changes
        salary_changes = [
            record for record in response.data 
            if record.get('change_type') in ['salary_adjustment', 'promotion', 'increment']
        ]
        
        return {"success": True, "data": salary_changes}
    except Exception as e:
        print(f"Error getting salary history: {str(e)}")
        return {"success": False, "message": str(e)}

@app.get("/api/admin/employee-history")
async def get_employee_history():
    """
    Get complete employee history (all changes)
    """
    try:
        response = supabase.table("employee_history").select("*").order("effective_date", desc=True).limit(200).execute()
        
        if not response.data:
            return {"success": True, "data": []}
        
        return {"success": True, "data": response.data}
    except Exception as e:
        print(f"Error getting employee history: {str(e)}")
        return {"success": False, "message": str(e)}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    print("Starting HRMS Web Application...")
    print("Access the application at: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
