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
import requests
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
    run_payroll,
    delete_employee,
    upload_profile_picture,
    upload_resume,
    get_payroll_settings,
    update_payroll_settings,
    get_monthly_deductions,
    upsert_monthly_deductions,
    get_variable_percentage_config
)
from services.supabase_engagements import (
    fetch_engagements, 
    update_engagement, 
    delete_engagement
)
from services.supabase_training_overseas import (
    fetch_training_course_records,
    fetch_overseas_work_trip_records
)
from services.supabase_employee_history import (
    update_employee_history_record,
    delete_employee_history_record
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

@app.get("/ux-demo", response_class=HTMLResponse)
async def ux_demo(request: Request):
    """UX components demonstration page"""
    return templates.TemplateResponse("ux_demo.html", {"request": request})

@app.get("/table-test", response_class=HTMLResponse)
async def table_test(request: Request):
    """Table mobile scrolling test page"""
    return templates.TemplateResponse("table_test.html", {"request": request})

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

@app.put("/api/admin/engagements/{engagement_id}")
async def update_engagement_record(engagement_id: str, request: Request):
    """
    Update an engagement record (admin only)
    """
    try:
        data = await request.json()
        
        # Remove read-only fields that shouldn't be updated
        data.pop('id', None)
        data.pop('created_at', None)
        
        # Try to update in all possible tables
        success = False
        error_msg = None
        
        # Try engagements table first
        try:
            response = supabase.table("engagements").update(data).eq("id", engagement_id).execute()
            if response.data:
                return {"success": True, "message": "Engagement updated successfully", "data": response.data[0]}
            success = True
        except Exception as e:
            error_msg = str(e)
        
        # Try training_courses table
        try:
            response = supabase.table("training_courses").update(data).eq("id", engagement_id).execute()
            if response.data:
                return {"success": True, "message": "Training course updated successfully", "data": response.data[0]}
            success = True
        except Exception as e:
            error_msg = str(e)
        
        # Try overseas_trips table
        try:
            response = supabase.table("overseas_trips").update(data).eq("id", engagement_id).execute()
            if response.data:
                return {"success": True, "message": "Overseas trip updated successfully", "data": response.data[0]}
            success = True
        except Exception as e:
            error_msg = str(e)
        
        if not success:
            return {"success": False, "message": f"Failed to update engagement: {error_msg}"}
        
        return {"success": True, "message": "Engagement updated successfully"}
    except Exception as e:
        print(f"Error updating engagement: {str(e)}")
        return {"success": False, "message": str(e)}

@app.delete("/api/admin/engagements/{engagement_id}")
async def delete_engagement_record(engagement_id: str):
    """
    Delete an engagement record (admin only)
    """
    try:
        # Try to delete from all possible tables
        deleted = False
        error_msg = None
        
        # Try engagements table first
        try:
            response = supabase.table("engagements").delete().eq("id", engagement_id).execute()
            if response.data:
                return {"success": True, "message": "Engagement deleted successfully"}
            deleted = True
        except Exception as e:
            error_msg = str(e)
        
        # Try training_courses table
        try:
            response = supabase.table("training_courses").delete().eq("id", engagement_id).execute()
            if response.data:
                return {"success": True, "message": "Training course deleted successfully"}
            deleted = True
        except Exception as e:
            error_msg = str(e)
        
        # Try overseas_trips table
        try:
            response = supabase.table("overseas_trips").delete().eq("id", engagement_id).execute()
            if response.data:
                return {"success": True, "message": "Overseas trip deleted successfully"}
            deleted = True
        except Exception as e:
            error_msg = str(e)
        
        if not deleted:
            return {"success": False, "message": f"Failed to delete engagement: {error_msg}"}
        
        return {"success": True, "message": "Engagement deleted successfully"}
    except Exception as e:
        print(f"Error deleting engagement: {str(e)}")
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

@app.delete("/api/employees/{employee_id}")
async def delete_employee_endpoint(employee_id: str):
    """
    Delete an employee (admin only)
    """
    try:
        result = delete_employee(employee_id)
        
        if result.get("success"):
            return {"success": True, "message": "Employee deleted successfully"}
        else:
            return {"success": False, "message": result.get("error", "Failed to delete employee")}
    except Exception as e:
        print(f"Error deleting employee: {str(e)}")
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
        # Query employees and their sick leave balances with department info
        from services.supabase_service import get_individual_employee_sick_leave_balance
        
        current_year = datetime.now().year
        response = supabase.table("employees").select("id, employee_id, full_name, email, department").execute()
        
        if not response.data:
            return {"success": True, "data": []}
        
        balances = []
        for employee in response.data:
            # Get sick leave balance from service function
            balance = get_individual_employee_sick_leave_balance(employee['email'], current_year)
            
            # Map to frontend expected field names (keep all fields from service)
            balances.append({
                "employee_id": employee['employee_id'],
                "full_name": employee['full_name'],
                "email": employee['email'],
                "department": employee.get('department', ''),
                # Sick leave fields (use correct field names from service)
                "sick_days_entitlement": balance.get('sick_days_entitlement', 14),
                "used_sick_days": balance.get('used_sick_days', 0),
                "remaining_sick_days": balance.get('remaining_sick_days', 14),
                # Hospitalization fields
                "hospitalization_days_entitlement": balance.get('hospitalization_days_entitlement', 60),
                "used_hospitalization_days": balance.get('used_hospitalization_days', 0),
                "remaining_hospitalization_days": balance.get('remaining_hospitalization_days', 60),
                # Additional info
                "years_of_service": balance.get('years_of_service', 0.0),
                "years_of_service_display": f"{balance.get('years_of_service', 0.0):.1f}"
            })
        
        return {"success": True, "data": balances}
    except Exception as e:
        print(f"Error getting sick leave balances: {str(e)}")
        return {"success": False, "message": str(e)}

@app.put("/api/admin/leave-balances/{employee_email}")
async def update_leave_balance(employee_email: str, request: Request):
    """
    Update an employee's leave balance
    """
    try:
        from services.supabase_service import update_employee_leave_balance
        data = await request.json()
        
        year = data.get('year', datetime.now().year)
        employee_email_decoded = employee_email.replace('%40', '@')
        
        # Get employee_id from email
        emp_response = supabase.table("employees").select("employee_id").eq("email", employee_email_decoded).execute()
        if not emp_response.data:
            return {"success": False, "message": "Employee not found"}
        
        employee_id = emp_response.data[0]['employee_id']
        
        # Update balance
        result = update_employee_leave_balance(employee_id, year, data)
        
        return {"success": True, "message": "Leave balance updated successfully"}
    except Exception as e:
        print(f"Error updating leave balance: {str(e)}")
        return {"success": False, "message": str(e)}

@app.post("/api/admin/leave-balances/carry-forward")
async def process_carry_forward(request: Request):
    """
    Process year-end carry forward for all employees
    """
    try:
        from services.supabase_service import process_year_end_carry_forward
        data = await request.json()
        
        year = data.get('year', datetime.now().year)
        rules = data.get('rules', {})
        
        result = process_year_end_carry_forward(year, rules)
        
        return {"success": result, "message": "Carry forward processed successfully" if result else "Failed to process carry forward"}
    except Exception as e:
        print(f"Error processing carry forward: {str(e)}")
        return {"success": False, "message": str(e)}

@app.post("/api/admin/leave-balances/set-carry-forward-all")
async def set_carry_forward_all(request: Request):
    """
    Set carried forward days for all employees
    """
    try:
        from services.supabase_service import set_carried_forward_for_all
        data = await request.json()
        
        current_year = data.get('current_year', datetime.now().year)
        next_year = data.get('next_year', current_year + 1)
        days = data.get('days', 0)
        applies_to = data.get('applies_to', 'all')
        
        result = set_carried_forward_for_all(current_year, next_year, days, applies_to)
        
        return {"success": result, "message": f"Set {days} carried forward days for all employees" if result else "Failed to set carried forward"}
    except Exception as e:
        print(f"Error setting carry forward for all: {str(e)}")
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
            eis_employee = float(run.get('eis_employee', 0) or run.get('eis', 0))
            eis_employer = float(run.get('eis_employer', 0))
            contributions.append({
                "employee_name": run.get('employee_name', ''),
                "month_year": run.get('month_year', ''),
                "epf_employee": float(run.get('epf_employee', 0)),
                "epf_employer": float(run.get('epf_employer', 0)),
                "socso_employee": float(run.get('socso_employee', 0)),
                "socso_employer": float(run.get('socso_employer', 0)),
                "eis": eis_employee,  # Use correct field name: eis_employee
                "eis_employer": eis_employer,  # Also include employer contribution
                "pcb": float(run.get('pcb', 0)),
                "total_employee": float(run.get('epf_employee', 0)) + float(run.get('socso_employee', 0)) + eis_employee,
                "total_employer": float(run.get('epf_employer', 0)) + float(run.get('socso_employer', 0)) + eis_employer
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
        # Try to query from payroll_run_skips table first (correct table used by GUI)
        try:
            # Query without join to avoid foreign key relationship requirement
            response = supabase.table("payroll_run_skips").select("*").order("created_at", desc=True).limit(200).execute()
            
            if response.data:
                # Get unique employee IDs
                employee_ids = list(set([rec.get("employee_id") for rec in response.data if rec.get("employee_id")]))
                
                # Fetch employee data for all relevant employees
                employee_map = {}
                if employee_ids:
                    employees_response = supabase.table("employees").select("id, full_name, email").in_("id", employee_ids).execute()
                    if employees_response.data:
                        employee_map = {emp["id"]: emp for emp in employees_response.data}
                
                skipped_records = []
                for record in response.data:
                    employee_id = record.get('employee_id', '')
                    employee = employee_map.get(employee_id, {})
                    
                    skipped_records.append({
                        "id": record.get('id'),
                        "employee_name": employee.get('full_name', ''),
                        "employee_email": employee.get('email', ''),
                        "employee_id": employee_id,
                        "month_year": record.get('payroll_date', ''),
                        "reason": record.get('reason', 'Not specified'),
                        "skipped_date": record.get('created_at', ''),
                        "notes": record.get('notes', ''),
                        "can_include": True
                    })
                return {"success": True, "data": skipped_records}
        except Exception as e:
            print(f"Info: payroll_run_skips table query failed, trying payroll_runs: {str(e)}")
        
        # Fallback to querying payroll_runs with skip flag
        response = supabase.table("payroll_runs").select("*").eq("status", "skipped").order("created_at", desc=True).limit(100).execute()
        
        if not response.data:
            # If no skipped records found, return empty array
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
        # Query salary history from employee_history table without join to avoid foreign key relationship requirement
        response = supabase.table("employee_history").select("*").order("effective_date", desc=True).limit(100).execute()
        
        if not response.data:
            return {"success": True, "data": []}
        
        # Filter for salary-related changes
        salary_changes = [
            record for record in response.data 
            if record.get('change_type') in ['salary_adjustment', 'promotion', 'increment']
        ]
        
        if not salary_changes:
            return {"success": True, "data": []}
        
        # Get unique employee emails
        employee_emails = list(set([sc.get("employee_email") for sc in salary_changes if sc.get("employee_email")]))
        
        # Fetch employee data for all relevant employees
        employee_map = {}
        if employee_emails:
            employees_response = supabase.table("employees").select("email, full_name").in_("email", employee_emails).execute()
            if employees_response.data:
                employee_map = {emp["email"]: emp for emp in employees_response.data}
        
        # Enrich salary changes with employee names
        for record in salary_changes:
            employee_email = record.get("employee_email")
            if employee_email and employee_email in employee_map:
                record["employee_name"] = employee_map[employee_email].get("full_name", "")
            else:
                record["employee_name"] = ""
        
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
    Get complete employment/re-employment history (previous jobs, companies, positions)
    """
    try:
        # Query employee_history without join to avoid foreign key relationship requirement
        response = supabase.table("employee_history").select("*").order("start_date", desc=True).limit(200).execute()
        
        if not response.data:
            return {"success": True, "data": []}
        
        records = response.data
        
        # Get unique employee emails
        employee_emails = list(set([rec.get("employee_email") for rec in records if rec.get("employee_email")]))
        
        # Fetch employee data for all relevant employees
        employee_map = {}
        if employee_emails:
            employees_response = supabase.table("employees").select("email, full_name").in_("email", employee_emails).execute()
            if employees_response.data:
                employee_map = {emp["email"]: emp for emp in employees_response.data}
        
        # Enrich records with employee names
        for record in records:
            employee_email = record.get("employee_email")
            if employee_email and employee_email in employee_map:
                record["employee_name"] = employee_map[employee_email].get("full_name", "")
            else:
                record["employee_name"] = ""
        
        return {"success": True, "data": records}
    except Exception as e:
        print(f"Error getting employee history: {str(e)}")
        return {"success": False, "message": str(e)}

@app.post("/api/admin/employee-history")
async def create_employment_history(request: Request):
    """
    Record employment / re-employment history (previous jobs, companies, positions)
    """
    try:
        data = await request.json()
        
        # Validate required fields
        required_fields = ['employee_email', 'company', 'job_title', 'start_date']
        for field in required_fields:
            if field not in data or data[field] == '':
                return {"success": False, "message": f"Missing required field: {field}"}
        
        # Get employee_id from email
        employee_response = supabase.table("employees").select("id").eq("email", data['employee_email']).execute()
        if not employee_response.data or len(employee_response.data) == 0:
            return {"success": False, "message": "Employee not found"}
        
        employee_id = employee_response.data[0]['id']
        
        # Create employment history record
        history_record = {
            "employee_id": employee_id,
            "employee_email": data['employee_email'],
            "company": data['company'],
            "job_title": data['job_title'],
            "position": data.get('position', ''),
            "department": data.get('department', ''),
            "employment_type": data.get('employment_type', ''),
            "start_date": data['start_date'],
            "end_date": data.get('end_date', None),  # None means currently employed
            "notes": data.get('notes', ''),
            "created_at": datetime.utcnow().isoformat(),
        }
        
        response = supabase.table("employee_history").insert(history_record).execute()
        
        if response.data:
            return {"success": True, "message": "Employment history recorded successfully", "data": response.data[0]}
        else:
            return {"success": False, "message": "Failed to record employment history"}
    except Exception as e:
        print(f"Error creating employment history: {str(e)}")
        return {"success": False, "message": str(e)}

@app.put("/api/admin/employee-history/{record_id}")
async def update_employment_history(record_id: str, request: Request):
    """
    Update an employee history record (admin only)
    """
    try:
        data = await request.json()
        
        # Remove read-only fields
        data.pop('id', None)
        data.pop('created_at', None)
        
        # Update the record using the service
        response = update_employee_history_record(record_id, data)
        
        if response and response.data:
            return {"success": True, "message": "Employee history record updated successfully", "data": response.data[0] if response.data else None}
        else:
            return {"success": False, "message": "Failed to update employee history record"}
    except Exception as e:
        print(f"Error updating employee history: {str(e)}")
        return {"success": False, "message": str(e)}

@app.delete("/api/admin/employee-history/{record_id}")
async def delete_employment_history(record_id: str):
    """
    Delete an employee history record (admin only)
    """
    try:
        response = delete_employee_history_record(record_id)
        
        if response:
            return {"success": True, "message": "Employee history record deleted successfully"}
        else:
            return {"success": False, "message": "Failed to delete employee history record"}
    except Exception as e:
        print(f"Error deleting employee history: {str(e)}")
        return {"success": False, "message": str(e)}

@app.get("/api/admin/payroll-info/{employee_id}")
async def get_payroll_info(employee_id: str):
    """
    Get payroll information (monthly deductions, tax info, etc.) for an employee
    """
    try:
        # Get current year and month
        now = datetime.now()
        year = now.year
        month = now.month
        
        # Get monthly deductions data
        deductions_data = get_monthly_deductions(employee_id, year, month)
        
        # Get employee basic info for defaults
        employee_response = supabase.table("employees").select("*").eq("id", employee_id).execute()
        employee_data = employee_response.data[0] if employee_response.data and len(employee_response.data) > 0 else {}
        
        # Merge employee data with deductions data
        result = {
            "employee_id": employee_id,
            "year": year,
            "month": month,
            "tax_number": employee_data.get("income_tax_number", ""),
            "epf_number": employee_data.get("epf_number", ""),
            "socso_number": employee_data.get("socso_number", ""),
            "bank_name": employee_data.get("bank_name", ""),
            "bank_account": employee_data.get("bank_account", ""),
            "basic_salary": employee_data.get("basic_salary", 0.0),
            **deductions_data  # Include all deductions data
        }
        
        return {"success": True, "data": result}
    except Exception as e:
        print(f"Error getting payroll info: {str(e)}")
        return {"success": False, "message": str(e)}

@app.post("/api/admin/payroll-info")
async def save_payroll_info(request: Request):
    """
    Save payroll information (monthly deductions, tax info, etc.) for an employee
    """
    # Fields that should be saved to the employees table (not monthly deductions)
    EMPLOYEE_TABLE_FIELDS = ["tax_number", "epf_number", "socso_number", "bank_name", "bank_account", "basic_salary"]
    # Fields that should not be saved to monthly deductions
    EXCLUDED_FROM_DEDUCTIONS = ["employee_id", "year", "month"] + EMPLOYEE_TABLE_FIELDS
    
    try:
        data = await request.json()
        
        employee_id = data.get("employee_id")
        if not employee_id:
            return {"success": False, "message": "Missing employee_id"}
        
        year = data.get("year", datetime.now().year)
        month = data.get("month", datetime.now().month)
        
        # Update employee basic info (bank, tax numbers)
        employee_updates = {}
        if "tax_number" in data:
            employee_updates["income_tax_number"] = data["tax_number"]
        if "epf_number" in data:
            employee_updates["epf_number"] = data["epf_number"]
        if "socso_number" in data:
            employee_updates["socso_number"] = data["socso_number"]
        if "bank_name" in data:
            employee_updates["bank_name"] = data["bank_name"]
        if "bank_account" in data:
            employee_updates["bank_account"] = data["bank_account"]
        if "basic_salary" in data:
            employee_updates["basic_salary"] = data["basic_salary"]
        
        if employee_updates:
            supabase.table("employees").update(employee_updates).eq("id", employee_id).execute()
        
        # Save monthly deductions data (excluding employee table fields)
        deductions_data = {k: v for k, v in data.items() if k not in EXCLUDED_FROM_DEDUCTIONS}
        
        success = upsert_monthly_deductions(employee_id, year, month, deductions_data)
        
        if success:
            return {"success": True, "message": "Payroll information saved successfully"}
        else:
            return {"success": False, "message": "Failed to save payroll information"}
    except Exception as e:
        print(f"Error saving payroll info: {str(e)}")
        return {"success": False, "message": str(e)}

@app.get("/api/admin/tp1-reliefs/{employee_id}/{year}/{month}")
async def get_tp1_reliefs(employee_id: str, year: int, month: int):
    """
    Get TP1 tax relief data for an employee for a specific month
    """
    # TP1 relief item key prefixes (must match JavaScript TP1_ITEMS keys)
    TP1_RELIEF_PREFIXES = [
        'parent_', 'medical_', 'lifestyle_', 'sports_', 'support_', 
        'self_edu_', 'breastfeeding_', 'childcare_', 'sspn_', 'alimony_', 
        'epf_voluntary', 'life_insurance_', 'education_medical_insurance',
        'prs_', 'socso_eis_', 'domestic_tourism', 'ev_charging_'
    ]
    
    try:
        # Get monthly deductions which includes TP1 relief data
        deductions_data = get_monthly_deductions(employee_id, year, month)
        
        # Extract TP1 relief items by checking if key starts with any relief prefix
        tp1_data = {
            k: v for k, v in deductions_data.items() 
            if any(k.startswith(prefix) or k == prefix for prefix in TP1_RELIEF_PREFIXES)
        }
        
        return {"success": True, "data": tp1_data}
    except Exception as e:
        print(f"Error getting TP1 relief data: {str(e)}")
        return {"success": False, "message": str(e)}

@app.post("/api/admin/tp1-reliefs")
async def save_tp1_reliefs(request: Request):
    """
    Save TP1 tax relief data for an employee for a specific month
    """
    try:
        data = await request.json()
        
        employee_id = data.get("employee_id")
        if not employee_id:
            return {"success": False, "message": "Missing employee_id"}
        
        year = data.get("year", datetime.now().year)
        month = data.get("month", datetime.now().month)
        relief_data = data.get("relief_data", {})
        
        # Save TP1 relief data to monthly deductions
        success = upsert_monthly_deductions(employee_id, year, month, relief_data)
        
        if success:
            return {"success": True, "message": "TP1 relief data saved successfully"}
        else:
            return {"success": False, "message": "Failed to save TP1 relief data"}
    except Exception as e:
        print(f"Error saving TP1 relief data: {str(e)}")
        return {"success": False, "message": str(e)}

@app.put("/api/admin/salary-history/{record_id}")
async def update_salary_history(record_id: str, request: Request):
    """
    Update a salary history record (admin only)
    Salary history is stored in employee_history table
    """
    try:
        data = await request.json()
        
        # Remove read-only fields
        data.pop('id', None)
        data.pop('created_at', None)
        
        # If updating salary values, recalculate change amount and percentage
        if 'previous_salary' in data and 'new_salary' in data:
            try:
                prev_salary = float(data.get('previous_salary', data.get('previous_value', 0)))
                new_salary = float(data.get('new_salary', data.get('new_value', 0)))
                
                change_amount = new_salary - prev_salary
                change_percentage = (change_amount / prev_salary * 100) if prev_salary > 0 else 0
                
                data['previous_value'] = str(prev_salary)
                data['new_value'] = str(new_salary)
                data['change_amount'] = change_amount
                data['change_percentage'] = change_percentage
            except (ValueError, TypeError):
                pass
        
        # Update the record using the service
        response = update_employee_history_record(record_id, data)
        
        if response and response.data:
            return {"success": True, "message": "Salary history record updated successfully", "data": response.data[0] if response.data else None}
        else:
            return {"success": False, "message": "Failed to update salary history record"}
    except Exception as e:
        print(f"Error updating salary history: {str(e)}")
        return {"success": False, "message": str(e)}

@app.delete("/api/admin/salary-history/{record_id}")
async def delete_salary_history(record_id: str):
    """
    Delete a salary history record (admin only)
    Salary history is stored in employee_history table
    """
    try:
        response = delete_employee_history_record(record_id)
        
        if response:
            return {"success": True, "message": "Salary history record deleted successfully"}
        else:
            return {"success": False, "message": "Failed to delete salary history record"}
    except Exception as e:
        print(f"Error deleting salary history: {str(e)}")
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
# Leave Policies Endpoints
# ====================

@app.get("/api/admin/leave-policies")
async def get_leave_policies():
    """Get company leave policies"""
    try:
        from services.supabase_service import get_company_leave_policies
        policies = get_company_leave_policies()
        return {"success": True, "data": policies}
    except Exception as e:
        print(f"Error getting leave policies: {str(e)}")
        return {"success": False, "message": str(e)}

@app.post("/api/admin/leave-policies")
async def update_leave_policies(request: Request):
    """Update company leave policies"""
    try:
        from services.supabase_service import update_company_leave_policy
        data = await request.json()
        
        # Update each policy
        admin_email = "admin"  # Could be extracted from session
        success = True
        
        for policy_name, policy_value in data.items():
            # Convert to string for storage
            value_str = str(policy_value)
            if not update_company_leave_policy(policy_name, value_str, admin_email):
                success = False
                break
        
        if success:
            return {"success": True, "message": "Leave policies updated successfully"}
        else:
            return {"success": False, "message": "Failed to update some policies"}
    except Exception as e:
        print(f"Error updating leave policies: {str(e)}")
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

@app.post("/api/holidays/import-malaysia")
async def import_malaysia_holidays(year: int, state: Optional[str] = None):
    """Auto-import Malaysia public holidays for a specific year"""
    try:
        # Validate year parameter
        if year < 1900 or year > 2100:
            return {
                "success": False,
                "message": "Year must be between 1900 and 2100"
            }
        
        from core.holidays_service import get_holidays_for_year
        from services.supabase_service import insert_calendar_holiday, find_calendar_holidays_for_year
        
        # Normalize state parameter
        normalized_state = None if (not state or state == 'All Malaysia') else state
        
        # Get holidays from python-holidays library
        holidays_set, holiday_details = get_holidays_for_year(
            year, 
            state=normalized_state,
            include_national=True,
            include_observances=True
        )
        
        # Fetch existing holidays for this year upfront (avoid N+1 query pattern)
        existing_holidays = find_calendar_holidays_for_year(year, state=normalized_state)
        existing_dates = {h.get('date') for h in existing_holidays if h.get('date')}
        
        imported_count = 0
        skipped_count = 0
        errors = []
        
        for holiday_date in holidays_set:
            date_str = holiday_date.isoformat()
            
            # Check if holiday already exists (in-memory check)
            if date_str in existing_dates:
                skipped_count += 1
                continue
            
            # Get holiday name from details
            holiday_names = holiday_details.get(date_str, [])
            
            # Use first name or create a generic name
            if holiday_names:
                # Extract just the holiday name (remove provider prefix)
                name = holiday_names[0]
                if ':' in name:
                    name = name.split(':', 1)[1].strip()
                # Remove location brackets for cleaner display
                if '[' in name:
                    name = name.split('[')[0].strip()
            else:
                name = "Public Holiday"
            
            # Determine if national or state-specific
            is_national = (normalized_state is None)
            is_observance = False  # Can be enhanced to detect observances
            
            # Insert new holiday using existing service function
            try:
                success = insert_calendar_holiday(
                    date_str=date_str,
                    name=name,
                    state=normalized_state,
                    is_national=is_national,
                    is_observance=is_observance
                )
                if success:
                    imported_count += 1
                    existing_dates.add(date_str)  # Update cache
                else:
                    errors.append(f"Failed to import {name} on {date_str}")
            except Exception as e:
                errors.append(f"Failed to import {name} on {date_str}: {str(e)}")
        
        return {
            "success": True,
            "message": f"Imported {imported_count} holidays, skipped {skipped_count} duplicates",
            "data": {
                "imported": imported_count,
                "skipped": skipped_count,
                "errors": errors
            }
        }
    except ImportError:
        return {
            "success": False,
            "message": "Holiday library not available. Please install 'holidays' package: pip install holidays"
        }
    except Exception as e:
        print(f"Error importing Malaysia holidays: {str(e)}")
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
        # Try to get data from payroll_run_skips table first
        try:
            # Query without join to avoid foreign key relationship requirement
            response = supabase.table("payroll_run_skips").select("*").order("created_at", desc=True).limit(1000).execute()
            
            if response.data:
                # Get unique employee IDs
                employee_ids = list(set([rec.get("employee_id") for rec in response.data if rec.get("employee_id")]))
                
                # Fetch employee data for all relevant employees
                employee_map = {}
                if employee_ids:
                    employees_response = supabase.table("employees").select("id, full_name, email").in_("id", employee_ids).execute()
                    if employees_response.data:
                        employee_map = {emp["id"]: emp for emp in employees_response.data}
                
                headers = ["ID", "Employee Name", "Employee Email", "Employee ID", "Payroll Date", "Reason", "Skipped Date"]
                rows = []
                for record in response.data:
                    employee_id = record.get('employee_id', '')
                    employee = employee_map.get(employee_id, {})
                    
                    rows.append([
                        record.get('id', ''),
                        employee.get('full_name', ''),
                        employee.get('email', ''),
                        employee_id,
                        record.get('payroll_date', ''),
                        record.get('reason', 'Not specified'),
                        record.get('created_at', '')
                    ])
                return generate_csv(headers, rows)
        except Exception as e:
            print(f"Info: payroll_run_skips export failed, trying payroll_runs: {str(e)}")
        
        # Fallback to payroll_runs table
        response = supabase.table("payroll_runs").select("*").eq("status", "skipped").order("created_at", desc=True).limit(1000).execute()
        
        if not response.data:
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
    """Export employment/re-employment history to CSV"""
    try:
        # Get employee history data
        response = supabase.table("employee_history").select("*").order("start_date", desc=True).limit(1000).execute()
        
        if not response.data:
            headers = ["Employee Email", "Company", "Job Title", "Position", "Department", "Employment Type", "Start Date", "End Date", "Notes", "Created At"]
            return generate_csv(headers, [])
        
        headers = ["Employee Email", "Company", "Job Title", "Position", "Department", "Employment Type", "Start Date", "End Date", "Notes", "Created At"]
        rows = []
        for record in response.data:
            rows.append([
                record.get('employee_email', ''),
                record.get('company', ''),
                record.get('job_title', ''),
                record.get('position', ''),
                record.get('department', ''),
                record.get('employment_type', ''),
                record.get('start_date', ''),
                record.get('end_date', ''),
                record.get('notes', ''),
                record.get('created_at', '')
            ])
        
        return generate_csv(headers, rows)
    except Exception as e:
        print(f"Error exporting employee history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/attendance/export/csv")
async def export_attendance_csv():
    """Export attendance records to CSV"""
    try:
        # Get attendance data
        attendance_data = get_all_attendance_records()
        
        if not attendance_data:
            headers = ["ID", "Employee Email", "Date", "Clock In", "Clock Out", "Status", "Notes", "Created At"]
            return generate_csv(headers, [])
        
        headers = ["ID", "Employee Email", "Date", "Clock In", "Clock Out", "Status", "Notes", "Created At"]
        rows = []
        for record in attendance_data:
            rows.append([
                record.get('id', ''),
                record.get('employee_email', ''),
                record.get('date', ''),
                record.get('clock_in', ''),
                record.get('clock_out', ''),
                record.get('status', ''),
                record.get('notes', ''),
                record.get('created_at', '')
            ])
        
        return generate_csv(headers, rows)
    except Exception as e:
        print(f"Error exporting attendance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/leave-requests/export/csv")
async def export_leave_requests_csv():
    """Export leave requests to CSV"""
    try:
        # Fetch leave requests
        response = supabase.table("leave_requests").select("*").order("created_at", desc=True).execute()
        
        if not response.data:
            headers = ["ID", "Employee Email", "Employee Name", "Leave Type", "Start Date", "End Date", "Days", "Status", "Title", "Description", "Created At", "Reviewed At", "Reviewed By"]
            return generate_csv(headers, [])
        
        leave_requests = response.data
        
        # Get unique employee emails for enrichment
        employee_emails = list(set([lr.get("employee_email") for lr in leave_requests if lr.get("employee_email")]))
        
        # Fetch employee data
        employee_map = {}
        if employee_emails:
            employees_response = supabase.table("employees").select("email, full_name").in_("email", employee_emails).execute()
            if employees_response.data:
                employee_map = {emp["email"]: emp.get("full_name", "") for emp in employees_response.data}
        
        headers = ["ID", "Employee Email", "Employee Name", "Leave Type", "Start Date", "End Date", "Days", "Status", "Title", "Description", "Created At", "Reviewed At", "Reviewed By"]
        rows = []
        for record in leave_requests:
            employee_email = record.get('employee_email', '')
            employee_name = employee_map.get(employee_email, '')
            
            rows.append([
                record.get('id', ''),
                employee_email,
                employee_name,
                record.get('leave_type', ''),
                record.get('start_date', ''),
                record.get('end_date', ''),
                record.get('total_days', ''),
                record.get('status', ''),
                record.get('title', ''),
                record.get('description', ''),
                record.get('created_at', ''),
                record.get('reviewed_at', ''),
                record.get('reviewed_by', '')
            ])
        
        return generate_csv(headers, rows)
    except Exception as e:
        print(f"Error exporting leave requests: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/payroll/export/csv")
async def export_payroll_runs_csv():
    """Export payroll runs to CSV"""
    try:
        # Get payroll runs
        payroll_runs = get_payroll_runs()
        
        if not payroll_runs:
            headers = ["ID", "Employee Email", "Employee Name", "Month/Year", "Basic Salary", "Allowances", "Deductions", "EPF Employee", "EPF Employer", "SOCSO Employee", "SOCSO Employer", "EIS", "PCB", "Net Salary", "Created At"]
            return generate_csv(headers, [])
        
        headers = ["ID", "Employee Email", "Employee Name", "Month/Year", "Basic Salary", "Allowances", "Deductions", "EPF Employee", "EPF Employer", "SOCSO Employee", "SOCSO Employer", "EIS", "PCB", "Net Salary", "Created At"]
        rows = []
        for record in payroll_runs:
            rows.append([
                record.get('id', ''),
                record.get('employee_email', ''),
                record.get('employee_name', ''),
                record.get('month_year', ''),
                f"{float(record.get('basic_salary', 0)):.2f}",
                f"{float(record.get('allowances', 0)):.2f}",
                f"{float(record.get('deductions', 0)):.2f}",
                f"{float(record.get('epf_employee', 0)):.2f}",
                f"{float(record.get('epf_employer', 0)):.2f}",
                f"{float(record.get('socso_employee', 0)):.2f}",
                f"{float(record.get('socso_employer', 0)):.2f}",
                f"{float(record.get('eis', 0)):.2f}",
                f"{float(record.get('pcb', 0)):.2f}",
                f"{float(record.get('net_salary', 0)):.2f}",
                record.get('created_at', '')
            ])
        
        return generate_csv(headers, rows)
    except Exception as e:
        print(f"Error exporting payroll runs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# File Upload Endpoints
# ============================================================================

@app.post("/api/employees/{employee_id}/profile-picture")
async def upload_employee_profile_picture(employee_id: str, file: UploadFile = File(...)):
    """Upload profile picture for an employee"""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            return {"success": False, "message": "Only image files are allowed"}
        
        # Validate file size (5MB limit)
        contents = await file.read()
        if len(contents) > 5 * 1024 * 1024:
            return {"success": False, "message": "File size must be less than 5MB"}
        
        # Save temporarily
        import tempfile
        temp_dir = tempfile.gettempdir()
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"profile_{employee_id}_{file.filename}")
        
        with open(temp_path, "wb") as f:
            f.write(contents)
        
        # Upload to Supabase storage
        photo_url = upload_profile_picture(temp_path, employee_id)
        
        # Clean up temp file
        try:
            os.remove(temp_path)
        except (OSError, FileNotFoundError) as e:
            print(f"Warning: Could not remove temp file: {e}")
        
        if photo_url:
            return {
                "success": True, 
                "message": "Profile picture uploaded successfully",
                "photo_url": photo_url
            }
        else:
            return {"success": False, "message": "Failed to upload profile picture"}
    
    except Exception as e:
        print(f"Error uploading profile picture: {str(e)}")
        return {"success": False, "message": f"Error uploading file: {str(e)}"}

@app.post("/api/employees/{employee_id}/resume")
async def upload_employee_resume(employee_id: str, file: UploadFile = File(...)):
    """Upload resume/CV for an employee"""
    try:
        # Validate file type
        allowed_types = ['application/pdf', 'application/msword', 
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        if not file.content_type or file.content_type not in allowed_types:
            return {"success": False, "message": "Only PDF, DOC, and DOCX files are allowed"}
        
        # Validate file size (10MB limit)
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            return {"success": False, "message": "File size must be less than 10MB"}
        
        # Save temporarily
        import tempfile
        temp_dir = tempfile.gettempdir()
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"resume_{employee_id}_{file.filename}")
        
        with open(temp_path, "wb") as f:
            f.write(contents)
        
        # Upload to Supabase storage
        resume_url = upload_resume(temp_path, employee_id)
        
        # Clean up temp file
        try:
            os.remove(temp_path)
        except (OSError, FileNotFoundError) as e:
            print(f"Warning: Could not remove temp file: {e}")
        
        if resume_url:
            return {
                "success": True, 
                "message": "Resume uploaded successfully",
                "resume_url": resume_url
            }
        else:
            return {"success": False, "message": "Failed to upload resume"}
    
    except Exception as e:
        print(f"Error uploading resume: {str(e)}")
        return {"success": False, "message": f"Error uploading file: {str(e)}"}

# ============================================================================
# Payroll Settings Endpoints
# ============================================================================

@app.get("/api/admin/payroll/settings")
async def get_payroll_settings_api():
    """Get current payroll settings (calculation method preference)"""
    try:
        settings = get_payroll_settings()
        return {
            "success": True,
            "data": settings
        }
    except Exception as e:
        print(f"Error getting payroll settings: {str(e)}")
        return {
            "success": False, 
            "message": str(e),
            "data": {"calculation_method": "fixed"}
        }

@app.post("/api/admin/payroll/settings")
async def update_payroll_settings_api(settings: Dict[str, Any]):
    """Update payroll settings (calculation method preference)"""
    try:
        calculation_method = settings.get('calculation_method')
        
        if calculation_method and calculation_method not in ['fixed', 'variable']:
            return {
                "success": False,
                "message": "calculation_method must be 'fixed' or 'variable'"
            }
        
        # Update settings
        success = update_payroll_settings(
            calculation_method=calculation_method,
            active_variable_config=settings.get('active_variable_config')
        )
        
        if success:
            return {
                "success": True,
                "message": "Payroll settings updated successfully"
            }
        else:
            return {
                "success": False,
                "message": "Failed to update payroll settings"
            }
    
    except Exception as e:
        print(f"Error updating payroll settings: {str(e)}")
        return {"success": False, "message": str(e)}

@app.get("/api/admin/variable-config/{config_name}")
async def get_variable_config_api(config_name: str):
    """Get variable percentage configuration (EPF/SOCSO/EIS rates)"""
    try:
        config = get_variable_percentage_config(config_name)
        
        if config:
            return {
                "success": True,
                "config": config
            }
        else:
            return {
                "success": False,
                "message": f"Configuration '{config_name}' not found"
            }
    except Exception as e:
        print(f"Error getting variable config: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }

# ============================================================================
# TP1 Relief Claims Endpoints (Placeholder for future implementation)
# ============================================================================

@app.get("/api/admin/tp1-reliefs/{employee_id}")
async def get_tp1_reliefs(employee_id: str, year: Optional[int] = None, month: Optional[int] = None):
    """Get TP1 relief claims for an employee (placeholder)"""
    return {
        "success": False,
        "message": "TP1 relief claims API is not yet implemented. This endpoint is reserved for future use.",
        "data": []
    }

@app.post("/api/admin/tp1-reliefs")
async def create_tp1_relief(relief_data: Dict[str, Any]):
    """Create/update TP1 relief claims (placeholder)"""
    return {
        "success": False,
        "message": "TP1 relief claims API is not yet implemented. This endpoint is reserved for future use."
    }

# ============================================================================
# Bulk Operations Endpoints
# ============================================================================

@app.post("/api/admin/employees/generate-pdfs")
async def generate_all_employee_pdfs():
    """Generate PDFs for all employees and return as ZIP (placeholder)"""
    return {
        "success": False,
        "message": "Bulk PDF generation is not yet implemented. This feature requires PDF generation library integration."
    }

# ============================================================================
# Location Autocomplete Endpoint
# ============================================================================

@app.get("/api/location/autocomplete")
async def location_autocomplete(query: str, country: Optional[str] = None):
    """
    Location autocomplete using Geoapify API
    
    Args:
        query: Search query (minimum 3 characters)
        country: Optional 2-letter country code (e.g., 'MY' for Malaysia)
    
    Returns:
        List of location suggestions with description and place_id
    """
    try:
        # Validate query length
        if not query or len(query.strip()) < 3:
            return {"success": True, "data": []}
        
        # Geoapify API configuration
        GEOAPIFY_API_KEY = os.environ.get('GEOAPIFY_KEY')
        if not GEOAPIFY_API_KEY:
            return {
                "success": False,
                "message": "Location service not configured. Please set GEOAPIFY_KEY environment variable.",
                "data": []
            }
        
        AUTOCOMPLETE_URL = "https://api.geoapify.com/v1/geocode/autocomplete"
        
        # Build request parameters
        params = {
            "text": query.strip(),
            "apiKey": GEOAPIFY_API_KEY,
            "type": "city",
            "limit": 7,
        }
        
        # Add country filter if specified
        if country:
            params["filter"] = f"countrycode:{country.lower()}"
        
        # Make request to Geoapify API
        response = requests.get(AUTOCOMPLETE_URL, params=params, timeout=6)
        response.raise_for_status()
        data = response.json()
        
        # Parse results
        features = data.get("features", [])
        results = []
        
        for feature in features:
            props = feature.get("properties", {})
            
            # Build description from city, state, country
            desc_parts = [
                props.get("city") or props.get("name"),
                props.get("state"),
                props.get("country")
            ]
            description = ", ".join([p for p in desc_parts if p])
            
            results.append({
                "description": description,
                "place_id": str(props.get("place_id", "")),
                "city": props.get("city") or props.get("name"),
                "state": props.get("state"),
                "country": props.get("country"),
                "formatted": props.get("formatted")
            })
        
        return {"success": True, "data": results}
        
    except requests.exceptions.RequestException as e:
        print(f"Error calling Geoapify API: {str(e)}")
        return {"success": False, "message": f"Location service error: {str(e)}", "data": []}
    except Exception as e:
        print(f"Error in location autocomplete: {str(e)}")
        return {"success": False, "message": str(e), "data": []}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    print("Starting HRMS Web Application...")
    print("Access the application at: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
