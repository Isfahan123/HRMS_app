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
    convert_utc_to_kl
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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    print("Starting HRMS Web Application...")
    print("Access the application at: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
