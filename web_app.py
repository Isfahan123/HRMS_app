"""
Web application entry point for HRMS
This provides a web-based interface using HTML/JavaScript with Python backend
"""
from fastapi import FastAPI, HTTPException, Request, Depends, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import csv
import io
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

@app.get("/admin-preview", response_class=HTMLResponse)
async def admin_preview(request: Request):
    """Serve the full admin dashboard for preview (no auth required)"""
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

@app.get("/test-subtabs", response_class=HTMLResponse)
async def test_subtabs(request: Request):
    """Test page to verify subtabs fix"""
    return templates.TemplateResponse("test_subtabs.html", {"request": request})

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

@app.post("/api/engagements")
async def create_engagement(request: Request):
    """
    Create a new engagement (training/course/trip) record
    """
    try:
        data = await request.json()
        
        # Validate required fields
        required_fields = ['type', 'title', 'start_date', 'end_date']
        for field in required_fields:
            if field not in data or not data[field]:
                return {"success": False, "message": f"Missing required field: {field}"}
        
        # Add timestamps and default status
        data['created_at'] = datetime.utcnow().isoformat()
        if 'status' not in data:
            data['status'] = 'pending'  # For employee submissions
        
        # Determine which table to insert into based on type
        if data['type'] in ['training', 'course']:
            table_name = "training_courses"
        elif data['type'] == 'overseas_trip':
            table_name = "overseas_trips"
        else:
            table_name = "engagements"
        
        response = supabase.table(table_name).insert(data).execute()
        
        if response.data:
            return {"success": True, "message": "Engagement submitted successfully", "data": response.data[0]}
        else:
            return {"success": False, "message": "Failed to submit engagement"}
    except Exception as e:
        print(f"Error creating engagement: {str(e)}")
        return {"success": False, "message": str(e)}

@app.get("/api/admin/engagements/all")
async def get_all_engagements():
    """
    Get all engagements across all employees (admin only)
    """
    try:
        all_data = []
        
        # Fetch from all engagement tables
        try:
            training_response = supabase.table("training_courses").select("*").order("created_at", desc=True).limit(100).execute()
            if training_response.data:
                for record in training_response.data:
                    record['type'] = 'training'
                    all_data.append(record)
        except:
            pass
        
        try:
            trips_response = supabase.table("overseas_trips").select("*").order("created_at", desc=True).limit(100).execute()
            if trips_response.data:
                for record in trips_response.data:
                    record['type'] = 'overseas_trip'
                    all_data.append(record)
        except:
            pass
        
        try:
            eng_response = supabase.table("engagements").select("*").order("created_at", desc=True).limit(100).execute()
            if eng_response.data:
                all_data.extend(eng_response.data)
        except:
            pass
        
        # Sort by date
        all_data.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return {"success": True, "data": all_data}
    except Exception as e:
        print(f"Error getting all engagements: {str(e)}")
        return {"success": False, "message": str(e), "data": []}

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
        # Fetch leave requests without join to avoid foreign key relationship requirement
        response = supabase.table("leave_requests").select("*").order("created_at", desc=True).execute()
        
        if not response.data:
            return {"success": True, "data": []}
        
        # Enrich leave requests with employee names
        leave_requests = response.data
        
        # Get unique employee emails
        employee_emails = list(set([lr.get("employee_email") for lr in leave_requests if lr.get("employee_email")]))
        
        # Fetch employee data for all relevant employees
        employee_map = {}
        if employee_emails:
            employees_response = supabase.table("employees").select("email, full_name").in_("email", employee_emails).execute()
            if employees_response.data:
                employee_map = {emp["email"]: emp for emp in employees_response.data}
        
        # Merge employee data into leave requests
        for lr in leave_requests:
            employee_email = lr.get("employee_email")
            if employee_email and employee_email in employee_map:
                # Add nested employees object to match frontend expectations
                lr["employees"] = employee_map[employee_email]
            # Also set email field as fallback for frontend
            lr["email"] = employee_email
        
        return {"success": True, "data": leave_requests}
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
        # Fetch bonuses without join - bonuses table already has employee_name field
        response = supabase.table("bonuses").select("*").order("created_at", desc=True).execute()
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

# Skipped Payroll API Endpoint
@app.get("/api/admin/skipped-payroll")
async def get_skipped_payroll():
    """
    Get skipped payroll records
    """
    try:
        # Query skipped payroll from payroll_skipped table or payroll_runs with skip flag
        # For now, we'll create mock data structure since table might not exist yet
        response = supabase.table("payroll_runs").select("*").eq("status", "skipped").order("created_at", desc=True).limit(100).execute()
        
        if not response.data:
            # If no skipped records in payroll_runs, return empty array
            return {"success": True, "data": []}
        
        skipped_records = []
        for record in response.data:
            skipped_records.append({
                "id": record.get('id'),
                "employee_name": record.get('employee_name', ''),
                "employee_email": record.get('employee_email', ''),
                "month_year": record.get('month_year', ''),
                "reason": record.get('skip_reason', 'Not specified'),
                "skipped_date": record.get('created_at', ''),
                "notes": record.get('notes', ''),
                "can_include": record.get('can_include_next', True)
            })
        
        return {"success": True, "data": skipped_records}
    except Exception as e:
        print(f"Error getting skipped payroll: {str(e)}")
        return {"success": False, "message": str(e), "data": []}

@app.post("/api/admin/skipped-payroll/{record_id}/include")
async def include_skipped_in_next_payroll(record_id: str):
    """
    Mark a skipped payroll record to be included in next run
    """
    try:
        # Update the record to mark it for inclusion in next payroll
        data = {
            "can_include_next": True,
            "status": "pending_inclusion",
            "updated_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table("payroll_runs").update(data).eq("id", record_id).execute()
        
        if response.data:
            return {"success": True, "message": "Record marked for inclusion in next payroll"}
        else:
            return {"success": False, "message": "Failed to update record"}
    except Exception as e:
        print(f"Error including skipped payroll: {str(e)}")
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

@app.post("/api/admin/salary-history")
async def create_salary_change(request: Request):
    """
    Record a salary change for an employee
    """
    try:
        data = await request.json()
        
        # Validate required fields
        required_fields = ['employee_email', 'previous_salary', 'new_salary', 'effective_date', 'change_type']
        for field in required_fields:
            if field not in data or data[field] == '':
                return {"success": False, "message": f"Missing required field: {field}"}
        
        # Validate salary values
        try:
            prev_salary = float(data['previous_salary'])
            new_salary = float(data['new_salary'])
            if prev_salary < 0 or new_salary < 0:
                return {"success": False, "message": "Salary values must be positive"}
        except ValueError:
            return {"success": False, "message": "Invalid salary values"}
        
        # Calculate change amount and percentage
        change_amount = new_salary - prev_salary
        change_percentage = (change_amount / prev_salary * 100) if prev_salary > 0 else 0
        
        # Create salary history record
        history_record = {
            "employee_email": data['employee_email'],
            "change_type": data['change_type'],
            "field_changed": "salary",
            "previous_value": str(prev_salary),
            "new_value": str(new_salary),
            "effective_date": data['effective_date'],
            "reason": data.get('reason', f"Salary changed from RM {prev_salary:.2f} to RM {new_salary:.2f} ({change_percentage:+.1f}%)"),
            "change_amount": change_amount,
            "change_percentage": change_percentage,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "admin"
        }
        
        response = supabase.table("employee_history").insert(history_record).execute()
        
        if response.data:
            return {"success": True, "message": "Salary change recorded successfully", "data": response.data[0]}
        else:
            return {"success": False, "message": "Failed to record salary change"}
    except Exception as e:
        print(f"Error creating salary change: {str(e)}")
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

@app.post("/api/admin/employee-history")
async def create_employment_change(request: Request):
    """
    Record an employment change (promotion, transfer, status change, etc.)
    """
    try:
        data = await request.json()
        
        # Validate required fields
        required_fields = ['employee_email', 'change_type', 'field_changed', 'effective_date', 'previous_value', 'new_value']
        for field in required_fields:
            if field not in data or data[field] == '':
                return {"success": False, "message": f"Missing required field: {field}"}
        
        # Create employment history record
        history_record = {
            "employee_email": data['employee_email'],
            "change_type": data['change_type'],
            "field_changed": data['field_changed'],
            "previous_value": data['previous_value'],
            "new_value": data['new_value'],
            "effective_date": data['effective_date'],
            "reason": data.get('reason', f"{data['field_changed']} changed from {data['previous_value']} to {data['new_value']}"),
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "admin"
        }
        
        response = supabase.table("employee_history").insert(history_record).execute()
        
        if response.data:
            return {"success": True, "message": "Employment change recorded successfully", "data": response.data[0]}
        else:
            return {"success": False, "message": "Failed to record employment change"}
    except Exception as e:
        print(f"Error creating employment change: {str(e)}")
        return {"success": False, "message": str(e)}

# ====================
# LHDN Tax Configuration Endpoints
# ====================

@app.get("/api/admin/lhdn/tax-rates")
async def get_tax_rates():
    """Get LHDN tax rates for residents and non-residents"""
    try:
        # Fetch tax rates from progressive_tax_brackets table
        response = supabase.table("progressive_tax_brackets").select("*").eq("config_name", "default").order("bracket_order").execute()
        
        # Organize by residency type
        resident_rates = []
        non_resident_rates = []
        
        if response.data:
            for rate in response.data:
                rate_data = {
                    "id": rate.get("id"),
                    "income_from": float(rate.get("lower_bound", 0)),
                    "income_to": float(rate.get("upper_bound")) if rate.get("upper_bound") is not None else None,
                    "rate_percent": float(rate.get("rate", 0)) * 100,  # Convert decimal to percentage
                    "tax_on_band": float(rate.get("tax_first_amount", 0)),
                    "year": 2024,
                    "bracket_order": rate.get("bracket_order")
                }
                
                # All progressive_tax_brackets are for residents
                resident_rates.append(rate_data)
        
        return {
            "success": True,
            "data": {
                "resident": resident_rates,
                "non_resident": non_resident_rates
            }
        }
    except Exception as e:
        print(f"Error fetching tax rates: {str(e)}")
        return {"success": False, "message": str(e)}

@app.post("/api/admin/lhdn/tax-rates")
async def create_tax_rate(data: Dict[str, Any]):
    """Create or update a tax rate bracket"""
    try:
        tax_rate = {
            "residency_type": data.get("residency_type", "resident"),
            "income_from": data["income_from"],
            "income_to": data["income_to"],
            "rate_percent": data["rate_percent"],
            "tax_on_band": data.get("tax_on_band", 0),
            "year": data.get("year", 2024),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Check if updating existing rate
        if data.get("id"):
            response = supabase.table("lhdn_tax_rates").update(tax_rate).eq("id", data["id"]).execute()
        else:
            tax_rate["created_at"] = datetime.utcnow().isoformat()
            response = supabase.table("lhdn_tax_rates").insert(tax_rate).execute()
        
        if response.data:
            return {"success": True, "message": "Tax rate saved successfully", "data": response.data[0]}
        else:
            return {"success": False, "message": "Failed to save tax rate"}
    except Exception as e:
        print(f"Error saving tax rate: {str(e)}")
        return {"success": False, "message": str(e)}

@app.delete("/api/admin/lhdn/tax-rates/{rate_id}")
async def delete_tax_rate(rate_id: int):
    """Delete a tax rate bracket"""
    try:
        response = supabase.table("lhdn_tax_rates").delete().eq("id", rate_id).execute()
        
        if response.data:
            return {"success": True, "message": "Tax rate deleted successfully"}
        else:
            return {"success": False, "message": "Tax rate not found"}
    except Exception as e:
        print(f"Error deleting tax rate: {str(e)}")
        return {"success": False, "message": str(e)}

@app.get("/api/admin/lhdn/relief-max")
async def get_relief_maximums():
    """Get tax relief maximum amounts"""
    try:
        response = supabase.table("tax_relief_max_config").select("*").eq("config_name", "default").execute()
        
        if response.data and len(response.data) > 0:
            # Transform the column-based structure to array format for frontend
            config = response.data[0]
            relief_array = [
                {"relief_code": "self", "relief_name": "Self Relief", "max_amount": config.get("personal_relief_max", 9000)},
                {"relief_code": "spouse", "relief_name": "Spouse Relief", "max_amount": config.get("spouse_relief_max", 4000)},
                {"relief_code": "child", "relief_name": "Child Relief (Under 18)", "max_amount": config.get("child_relief_max", 2000)},
                {"relief_code": "disabled_child", "relief_name": "Disabled Child", "max_amount": config.get("disabled_child_relief_max", 8000)},
                {"relief_code": "parent_medical", "relief_name": "Medical for Parents", "max_amount": config.get("parent_medical_max", 8000)},
                {"relief_code": "serious_disease", "relief_name": "Medical (Serious Disease)", "max_amount": config.get("serious_disease_max", 10000)},
                {"relief_code": "education", "relief_name": "Education", "max_amount": config.get("education_max", 8000)},
                {"relief_code": "lifestyle", "relief_name": "Lifestyle", "max_amount": config.get("lifestyle_max", 2500)},
                {"relief_code": "sports", "relief_name": "Sports Equipment", "max_amount": config.get("sports_equipment_max", 300)},
                {"relief_code": "epf_insurance", "relief_name": "Life Insurance & EPF", "max_amount": config.get("combined_epf_insurance_limit", 7000)},
            ]
            return {"success": True, "data": relief_array}
        else:
            return {"success": True, "data": []}
    except Exception as e:
        print(f"Error fetching relief maximums: {str(e)}")
        return {"success": False, "message": str(e)}

@app.post("/api/admin/lhdn/relief-max")
async def update_relief_maximum(data: Dict[str, Any]):
    """Update a tax relief maximum amount"""
    try:
        relief_data = {
            "relief_code": data["relief_code"],
            "relief_name": data["relief_name"],
            "max_amount": data["max_amount"],
            "description": data.get("description", ""),
            "year": data.get("year", 2024),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Check if relief exists
        existing = supabase.table("lhdn_relief_max").select("*").eq("relief_code", data["relief_code"]).eq("year", data.get("year", 2024)).execute()
        
        if existing.data:
            # Update existing
            response = supabase.table("lhdn_relief_max").update(relief_data).eq("id", existing.data[0]["id"]).execute()
        else:
            # Create new
            relief_data["created_at"] = datetime.utcnow().isoformat()
            response = supabase.table("lhdn_relief_max").insert(relief_data).execute()
        
        if response.data:
            return {"success": True, "message": "Relief maximum updated successfully", "data": response.data[0]}
        else:
            return {"success": False, "message": "Failed to update relief maximum"}
    except Exception as e:
        print(f"Error updating relief maximum: {str(e)}")
        return {"success": False, "message": str(e)}

@app.get("/api/admin/lhdn/relief-overrides")
async def get_relief_overrides():
    """Get employee-specific relief overrides"""
    try:
        # Try to query relief_item_overrides table (actual table name)
        # If it doesn't exist or has different structure, return empty array
        response = supabase.table("relief_item_overrides").select("*").execute()
        
        # Transform to expected format
        overrides = []
        if response.data:
            for item in response.data:
                overrides.append({
                    "id": item.get("item_key"),
                    "relief_code": item.get("item_key"),
                    "cap": item.get("cap"),
                    "pcb_only": item.get("pcb_only"),
                    "cycle_years": item.get("cycle_years")
                })
        
        return {"success": True, "data": overrides}
    except Exception as e:
        print(f"Error fetching relief overrides: {str(e)}")
        # Return empty array instead of error to prevent UI from breaking
        return {"success": True, "data": []}

@app.post("/api/admin/lhdn/relief-overrides")
async def create_relief_override(data: Dict[str, Any]):
    """Create an employee-specific relief override"""
    try:
        override = {
            "employee_id": data["employee_id"],
            "relief_code": data["relief_code"],
            "override_amount": data["override_amount"],
            "effective_period": data.get("effective_period", "2024"),
            "reason": data.get("reason", ""),
            "created_at": datetime.utcnow().isoformat(),
            "created_by": "admin"
        }
        
        response = supabase.table("lhdn_relief_overrides").insert(override).execute()
        
        if response.data:
            return {"success": True, "message": "Relief override created successfully", "data": response.data[0]}
        else:
            return {"success": False, "message": "Failed to create relief override"}
    except Exception as e:
        print(f"Error creating relief override: {str(e)}")
        return {"success": False, "message": str(e)}

@app.put("/api/admin/lhdn/relief-overrides/{override_id}")
async def update_relief_override(override_id: int, data: Dict[str, Any]):
    """Update an employee-specific relief override"""
    try:
        override = {
            "override_amount": data["override_amount"],
            "effective_period": data.get("effective_period"),
            "reason": data.get("reason", ""),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table("lhdn_relief_overrides").update(override).eq("id", override_id).execute()
        
        if response.data:
            return {"success": True, "message": "Relief override updated successfully", "data": response.data[0]}
        else:
            return {"success": False, "message": "Relief override not found"}
    except Exception as e:
        print(f"Error updating relief override: {str(e)}")
        return {"success": False, "message": str(e)}

@app.delete("/api/admin/lhdn/relief-overrides/{override_id}")
async def delete_relief_override(override_id: int):
    """Delete an employee-specific relief override"""
    try:
        response = supabase.table("lhdn_relief_overrides").delete().eq("id", override_id).execute()
        
        if response.data:
            return {"success": True, "message": "Relief override deleted successfully"}
        else:
            return {"success": False, "message": "Relief override not found"}
    except Exception as e:
        print(f"Error deleting relief override: {str(e)}")
        return {"success": False, "message": str(e)}

# ====================
# Leave Configuration Endpoints
# ====================

@app.get("/api/admin/leave-types")
async def get_leave_types():
    """Get all leave types"""
    try:
        response = supabase.table("leave_types").select("*").execute()
        
        if response.data:
            return {"success": True, "data": response.data}
        else:
            return {"success": True, "data": []}
    except Exception as e:
        print(f"Error fetching leave types: {str(e)}")
        return {"success": False, "message": str(e)}

@app.post("/api/admin/leave-types")
async def create_leave_type(data: Dict[str, Any]):
    """Create a new leave type"""
    try:
        leave_type = {
            "name": data["name"],
            "code": data["code"],
            "color": data.get("color", "#3498db"),
            "description": data.get("description", ""),
            "requires_approval": data.get("requires_approval", True),
            "is_paid": data.get("is_paid", True),
            "created_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table("leave_types").insert(leave_type).execute()
        
        if response.data:
            return {"success": True, "message": "Leave type created successfully", "data": response.data[0]}
        else:
            return {"success": False, "message": "Failed to create leave type"}
    except Exception as e:
        print(f"Error creating leave type: {str(e)}")
        return {"success": False, "message": str(e)}

@app.put("/api/admin/leave-types/{type_id}")
async def update_leave_type(type_id: int, data: Dict[str, Any]):
    """Update a leave type"""
    try:
        leave_type = {
            "name": data.get("name"),
            "color": data.get("color"),
            "description": data.get("description"),
            "requires_approval": data.get("requires_approval"),
            "is_paid": data.get("is_paid"),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Remove None values
        leave_type = {k: v for k, v in leave_type.items() if v is not None}
        
        response = supabase.table("leave_types").update(leave_type).eq("id", type_id).execute()
        
        if response.data:
            return {"success": True, "message": "Leave type updated successfully", "data": response.data[0]}
        else:
            return {"success": False, "message": "Leave type not found"}
    except Exception as e:
        print(f"Error updating leave type: {str(e)}")
        return {"success": False, "message": str(e)}

@app.delete("/api/admin/leave-types/{type_id}")
async def delete_leave_type(type_id: int):
    """Delete a leave type"""
    try:
        response = supabase.table("leave_types").delete().eq("id", type_id).execute()
        
        if response.data:
            return {"success": True, "message": "Leave type deleted successfully"}
        else:
            return {"success": False, "message": "Leave type not found"}
    except Exception as e:
        print(f"Error deleting leave type: {str(e)}")
        return {"success": False, "message": str(e)}

@app.get("/api/admin/leave-entitlements")
async def get_leave_entitlements():
    """Get leave entitlements/caps"""
    try:
        # Get tiers and caps from the actual database structure
        tiers_response = supabase.table("leave_caps_tiers").select("*").execute()
        caps_response = supabase.table("leave_caps").select("*").execute()
        
        # Transform to expected format
        entitlements = []
        if tiers_response.data:
            for tier in tiers_response.data:
                tier_caps = [cap for cap in caps_response.data if cap.get("tier_id") == tier.get("id")]
                
                # Create entitlement entry for this tier
                entitlement = {
                    "id": tier.get("id"),
                    "position_level": tier.get("label"),
                    "min_years": tier.get("min_years", 0),
                    "max_years": tier.get("max_years", 9999),
                    "annual_leave_days": 0,
                    "sick_leave_days": 0,
                    "carry_forward_max": 0
                }
                
                # Extract specific leave types from caps
                for cap in tier_caps:
                    leave_type = cap.get("leave_type", "").lower()
                    cap_value = cap.get("cap", 0)
                    
                    if "annual" in leave_type:
                        entitlement["annual_leave_days"] = cap_value
                    elif "sick" in leave_type:
                        entitlement["sick_leave_days"] = cap_value
                    elif "carry" in leave_type or "forward" in leave_type:
                        entitlement["carry_forward_max"] = cap_value
                
                entitlements.append(entitlement)
        
        return {"success": True, "data": entitlements}
    except Exception as e:
        print(f"Error fetching leave entitlements: {str(e)}")
        return {"success": False, "message": str(e)}

@app.post("/api/admin/leave-entitlements")
async def create_leave_entitlement(data: Dict[str, Any]):
    """Create a leave entitlement rule"""
    try:
        entitlement = {
            "leave_type_id": data["leave_type_id"],
            "employee_level": data.get("employee_level", "all"),
            "annual_days": data["annual_days"],
            "carry_forward_days": data.get("carry_forward_days", 0),
            "effective_year": data.get("effective_year", 2024),
            "created_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table("leave_entitlements").insert(entitlement).execute()
        
        if response.data:
            return {"success": True, "message": "Leave entitlement created successfully", "data": response.data[0]}
        else:
            return {"success": False, "message": "Failed to create leave entitlement"}
    except Exception as e:
        print(f"Error creating leave entitlement: {str(e)}")
        return {"success": False, "message": str(e)}

@app.put("/api/admin/leave-entitlements/{entitlement_id}")
async def update_leave_entitlement(entitlement_id: int, data: Dict[str, Any]):
    """Update a leave entitlement rule"""
    try:
        entitlement = {
            "annual_days": data.get("annual_days"),
            "carry_forward_days": data.get("carry_forward_days"),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Remove None values
        entitlement = {k: v for k, v in entitlement.items() if v is not None}
        
        response = supabase.table("leave_entitlements").update(entitlement).eq("id", entitlement_id).execute()
        
        if response.data:
            return {"success": True, "message": "Leave entitlement updated successfully", "data": response.data[0]}
        else:
            return {"success": False, "message": "Leave entitlement not found"}
    except Exception as e:
        print(f"Error updating leave entitlement: {str(e)}")
        return {"success": False, "message": str(e)}

@app.delete("/api/admin/leave-entitlements/{entitlement_id}")
async def delete_leave_entitlement(entitlement_id: int):
    """Delete a leave entitlement rule"""
    try:
        response = supabase.table("leave_entitlements").delete().eq("id", entitlement_id).execute()
        
        if response.data:
            return {"success": True, "message": "Leave entitlement deleted successfully"}
        else:
            return {"success": False, "message": "Leave entitlement not found"}
    except Exception as e:
        print(f"Error deleting leave entitlement: {str(e)}")
        return {"success": False, "message": str(e)}

# ====================
# Calendar & Holidays Endpoints
# ====================

@app.get("/api/holidays")
async def get_holidays():
    """Get public holidays"""
    try:
        # Get current year
        current_year = datetime.now().year
        
        response = supabase.table("calendar_holidays").select("*").gte("date", f"{current_year}-01-01").lte("date", f"{current_year+1}-12-31").order("date").execute()
        
        if response.data:
            return {"success": True, "data": response.data}
        else:
            return {"success": True, "data": []}
    except Exception as e:
        print(f"Error fetching holidays: {str(e)}")
        return {"success": False, "message": str(e)}

@app.get("/api/leave-calendar/{employee_id}")
async def get_leave_calendar(employee_id: str, year: Optional[int] = None):
    """Get leave calendar for an employee"""
    try:
        if not year:
            year = datetime.now().year
        
        # Fetch leave requests for the year
        response = supabase.table("leave_requests").select("*").eq("employee_id", employee_id).gte("start_date", f"{year}-01-01").lte("end_date", f"{year}-12-31").execute()
        
        # Fetch holidays
        holidays_response = supabase.table("calendar_holidays").select("*").gte("date", f"{year}-01-01").lte("date", f"{year}-12-31").execute()
        
        return {
            "success": True,
            "data": {
                "leave_requests": response.data if response.data else [],
                "holidays": holidays_response.data if holidays_response.data else []
            }
        }
    except Exception as e:
        print(f"Error fetching leave calendar: {str(e)}")
        return {"success": False, "message": str(e)}

@app.post("/api/holidays")
async def create_holiday(holiday: dict):
    """Create a new holiday"""
    try:
        response = supabase.table("calendar_holidays").insert(holiday).execute()
        
        if response.data:
            return {"success": True, "data": response.data[0], "message": "Holiday created successfully"}
        else:
            return {"success": False, "message": "Failed to create holiday"}
    except Exception as e:
        print(f"Error creating holiday: {str(e)}")
        return {"success": False, "message": str(e)}

@app.put("/api/holidays/{holiday_id}")
async def update_holiday(holiday_id: int, holiday: dict):
    """Update an existing holiday"""
    try:
        response = supabase.table("calendar_holidays").update(holiday).eq("id", holiday_id).execute()
        
        if response.data:
            return {"success": True, "data": response.data[0], "message": "Holiday updated successfully"}
        else:
            return {"success": False, "message": "Failed to update holiday"}
    except Exception as e:
        print(f"Error updating holiday: {str(e)}")
        return {"success": False, "message": str(e)}

@app.delete("/api/holidays/{holiday_id}")
async def delete_holiday(holiday_id: int):
    """Delete a holiday"""
    try:
        response = supabase.table("calendar_holidays").delete().eq("id", holiday_id).execute()
        
        if response.data:
            return {"success": True, "message": "Holiday deleted successfully"}
        else:
            return {"success": False, "message": "Failed to delete holiday"}
    except Exception as e:
        print(f"Error deleting holiday: {str(e)}")
        return {"success": False, "message": str(e)}

# Helper function to generate CSV from data
def generate_csv(headers: List[str], rows: List[List[Any]]) -> StreamingResponse:
    """Generate a CSV file from headers and rows"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

# CSV Export Endpoints
@app.get("/api/admin/skipped-payroll/export/csv")
async def export_skipped_payroll_csv():
    """Export skipped payroll records to CSV"""
    try:
        # Get skipped payroll data
        response = supabase.table("payroll_runs").select("*").eq("status", "skipped").order("created_at", desc=True).limit(1000).execute()
        
        if not response.data:
            # Return empty CSV with headers
            headers = ["ID", "Employee Name", "Employee Email", "Month/Year", "Reason", "Skipped Date", "Notes"]
            return generate_csv(headers, [])
        
        headers = ["ID", "Employee Name", "Employee Email", "Month/Year", "Reason", "Skipped Date", "Notes"]
        rows = []
        for record in response.data:
            rows.append([
                record.get('id', ''),
                record.get('employee_name', ''),
                record.get('employee_email', ''),
                record.get('month_year', ''),
                record.get('skip_reason', 'Not specified'),
                record.get('created_at', ''),
                record.get('notes', '')
            ])
        
        return generate_csv(headers, rows)
    except Exception as e:
        print(f"Error exporting skipped payroll: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/contributions/export/csv")
async def export_contributions_csv():
    """Export payroll contributions to CSV"""
    try:
        # Get payroll contributions data
        response = supabase.table("payroll_runs").select("*").order("created_at", desc=True).limit(1000).execute()
        
        if not response.data:
            headers = ["Employee Name", "Month/Year", "EPF Employee", "EPF Employer", "SOCSO Employee", "SOCSO Employer", "EIS", "PCB", "Total Employee", "Total Employer"]
            return generate_csv(headers, [])
        
        headers = ["Employee Name", "Month/Year", "EPF Employee", "EPF Employer", "SOCSO Employee", "SOCSO Employer", "EIS", "PCB", "Total Employee", "Total Employer"]
        rows = []
        for run in response.data:
            epf_employee = float(run.get('epf_employee', 0))
            epf_employer = float(run.get('epf_employer', 0))
            socso_employee = float(run.get('socso_employee', 0))
            socso_employer = float(run.get('socso_employer', 0))
            eis = float(run.get('eis', 0))
            pcb = float(run.get('pcb', 0))
            
            rows.append([
                run.get('employee_name', ''),
                run.get('month_year', ''),
                f"{epf_employee:.2f}",
                f"{epf_employer:.2f}",
                f"{socso_employee:.2f}",
                f"{socso_employer:.2f}",
                f"{eis:.2f}",
                f"{pcb:.2f}",
                f"{epf_employee + socso_employee + eis:.2f}",
                f"{epf_employer + socso_employer:.2f}"
            ])
        
        return generate_csv(headers, rows)
    except Exception as e:
        print(f"Error exporting contributions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/salary-history/export/csv")
async def export_salary_history_csv():
    """Export salary history to CSV"""
    try:
        # Get salary history data
        response = supabase.table("employee_history").select("*").order("effective_date", desc=True).limit(1000).execute()
        
        if not response.data:
            headers = ["Effective Date", "Employee Email", "Employee Name", "Change Type", "Previous Salary", "New Salary", "Change Amount", "Change Percentage", "Reason"]
            return generate_csv(headers, [])
        
        # Filter for salary-related changes
        salary_changes = [
            record for record in response.data 
            if record.get('change_type') in ['salary_adjustment', 'promotion', 'increment']
        ]
        
        headers = ["Effective Date", "Employee Email", "Employee Name", "Change Type", "Previous Salary", "New Salary", "Change Amount", "Change Percentage", "Reason"]
        rows = []
        for record in salary_changes:
            prev_salary = float(record.get('previous_value', 0))
            new_salary = float(record.get('new_value', 0))
            change = new_salary - prev_salary
            change_percent = (change / prev_salary * 100) if prev_salary > 0 else 0
            
            rows.append([
                record.get('effective_date', ''),
                record.get('employee_email', ''),
                record.get('employee_name', ''),
                record.get('change_type', ''),
                f"{prev_salary:.2f}",
                f"{new_salary:.2f}",
                f"{change:.2f}",
                f"{change_percent:.2f}%",
                record.get('reason', '')
            ])
        
        return generate_csv(headers, rows)
    except Exception as e:
        print(f"Error exporting salary history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/engagements/export/csv")
async def export_engagements_csv():
    """Export engagements to CSV"""
    try:
        all_data = []
        
        # Fetch from all engagement tables
        try:
            training_response = supabase.table("training_courses").select("*").order("created_at", desc=True).limit(1000).execute()
            if training_response.data:
                for record in training_response.data:
                    record['type'] = 'training'
                    all_data.append(record)
        except:
            pass
        
        try:
            trips_response = supabase.table("overseas_trips").select("*").order("created_at", desc=True).limit(1000).execute()
            if trips_response.data:
                for record in trips_response.data:
                    record['type'] = 'overseas_trip'
                    all_data.append(record)
        except:
            pass
        
        try:
            eng_response = supabase.table("engagements").select("*").order("created_at", desc=True).limit(1000).execute()
            if eng_response.data:
                all_data.extend(eng_response.data)
        except:
            pass
        
        # Sort by date
        all_data.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        headers = ["Type", "Employee Email", "Title", "Start Date", "End Date", "Location", "Organizer", "Cost", "Status", "Description", "Created At"]
        rows = []
        for record in all_data:
            rows.append([
                record.get('type', 'engagement'),
                record.get('employee_email', ''),
                record.get('title', ''),
                record.get('start_date', ''),
                record.get('end_date', ''),
                record.get('location', ''),
                record.get('organizer', ''),
                f"{float(record.get('cost', 0)):.2f}" if record.get('cost') else '0.00',
                record.get('status', ''),
                record.get('description', ''),
                record.get('created_at', '')
            ])
        
        return generate_csv(headers, rows)
    except Exception as e:
        print(f"Error exporting engagements: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/employee-history/export/csv")
async def export_employee_history_csv():
    """Export employee history to CSV"""
    try:
        # Get employee history data
        response = supabase.table("employee_history").select("*").order("effective_date", desc=True).limit(1000).execute()
        
        if not response.data:
            headers = ["Effective Date", "Employee Email", "Employee Name", "Change Type", "Field Changed", "Previous Value", "New Value", "Reason", "Created At"]
            return generate_csv(headers, [])
        
        headers = ["Effective Date", "Employee Email", "Employee Name", "Change Type", "Field Changed", "Previous Value", "New Value", "Reason", "Created At"]
        rows = []
        for record in response.data:
            rows.append([
                record.get('effective_date', ''),
                record.get('employee_email', ''),
                record.get('employee_name', ''),
                record.get('change_type', ''),
                record.get('field_changed', ''),
                record.get('previous_value', ''),
                record.get('new_value', ''),
                record.get('reason', ''),
                record.get('created_at', '')
            ])
        
        return generate_csv(headers, rows)
    except Exception as e:
        print(f"Error exporting employee history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    print("Starting HRMS Web Application...")
    print("Access the application at: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
