"""
Web application entry point for HRMS
This provides a web-based interface using HTML/JavaScript with Python backend
"""
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
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
    update_employee
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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    print("Starting HRMS Web Application...")
    print("Access the application at: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
