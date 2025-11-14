"""
Web application entry point for HRMS
This provides a web-based interface using HTML/JavaScript with Python backend
"""
from fastapi import FastAPI, HTTPException, Request, Depends, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import io
import csv
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
    upload_document_to_bucket
)
from services.supabase_engagements import fetch_engagements
from services.supabase_training_overseas import (
    fetch_training_course_records,
    fetch_overseas_work_trip_records
)
from core.employee_service import calculate_cumulative_service
from gui.payslip_generator import generate_payslip_for_employee

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

# ====================
# Export Endpoints
# ====================

@app.get("/api/employee/payslip/download/{payroll_run_id}")
async def download_payslip(payroll_run_id: int):
    """Generate and download PDF payslip"""
    try:
        # Import payslip generator
        from gui.payslip_generator import get_employee_payslip_data, generate_payslip_pdf
        
        # Get payslip data
        payslip_data = get_employee_payslip_data(None, payroll_run_id)
        if not payslip_data:
            raise HTTPException(status_code=404, detail="Payslip not found")
        
        # Generate PDF
        pdf_buffer = generate_payslip_pdf(payslip_data)
        
        # Return PDF as downloadable file
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=payslip_{payroll_run_id}.pdf"
            }
        )
    except Exception as e:
        print(f"Error generating payslip: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/attendance/csv")
async def export_attendance_csv():
    """Export all attendance records as CSV"""
    try:
        from services.supabase_service import supabase
        
        # Fetch all attendance records with employee details
        response = supabase.table("attendance").select("*, employees(name, email)").execute()
        
        if not response.data:
            return {"success": False, "message": "No attendance records found"}
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(["Employee Name", "Email", "Date", "Time In", "Time Out", "Status"])
        
        # Write data
        for record in response.data:
            employee = record.get("employees", {})
            writer.writerow([
                employee.get("name", ""),
                employee.get("email", ""),
                record.get("date", ""),
                record.get("time_in", ""),
                record.get("time_out", ""),
                record.get("status", "")
            ])
        
        # Return CSV as downloadable file
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=attendance_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )
    except Exception as e:
        print(f"Error exporting attendance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/leave-requests/csv")
async def export_leave_requests_csv():
    """Export all leave requests as CSV"""
    try:
        from services.supabase_service import supabase
        
        # Fetch all leave requests with employee details
        response = supabase.table("leave_requests").select("*, employees(name, email)").execute()
        
        if not response.data:
            return {"success": False, "message": "No leave requests found"}
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(["Employee Name", "Email", "Leave Type", "Start Date", "End Date", "Days", "Status", "Reason"])
        
        # Write data
        for record in response.data:
            employee = record.get("employees", {})
            writer.writerow([
                employee.get("name", ""),
                employee.get("email", ""),
                record.get("leave_type", ""),
                record.get("start_date", ""),
                record.get("end_date", ""),
                record.get("days_requested", ""),
                record.get("status", ""),
                record.get("reason", "")
            ])
        
        # Return CSV as downloadable file
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=leave_requests_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )
    except Exception as e:
        print(f"Error exporting leave requests: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/payroll/csv")
async def export_payroll_csv():
    """Export all payroll runs as CSV"""
    try:
        from services.supabase_service import supabase
        
        # Fetch all payroll runs with employee details
        response = supabase.table("payroll_runs").select("*, employees(name, email)").execute()
        
        if not response.data:
            return {"success": False, "message": "No payroll runs found"}
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            "Employee Name", "Email", "Month", "Year", "Basic Salary",
            "Gross Salary", "EPF Employee", "EPF Employer", "SOCSO Employee",
            "SOCSO Employer", "EIS Employee", "EIS Employer", "PCB", "Net Pay"
        ])
        
        # Write data
        for record in response.data:
            employee = record.get("employees", {})
            writer.writerow([
                employee.get("name", ""),
                employee.get("email", ""),
                record.get("month", ""),
                record.get("year", ""),
                record.get("basic_salary", 0),
                record.get("gross_salary", 0),
                record.get("epf_employee", 0),
                record.get("epf_employer", 0),
                record.get("socso_employee", 0),
                record.get("socso_employer", 0),
                record.get("eis_employee", 0),
                record.get("eis_employer", 0),
                record.get("pcb", 0),
                record.get("net_pay", 0)
            ])
        
        # Return CSV as downloadable file
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=payroll_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )
    except Exception as e:
        print(f"Error exporting payroll: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ====================
# File Upload Endpoints
# ====================

@app.post("/api/upload/document")
async def upload_document(
    file: UploadFile = File(...),
    employee_id: int = Form(...),
    document_type: str = Form(...)
):
    """Upload document to Supabase storage"""
    try:
        from services.supabase_service import supabase
        
        # Read file content
        file_content = await file.read()
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{employee_id}_{document_type}_{timestamp}_{file.filename}"
        
        # Upload to Supabase storage
        bucket_name = "employee-documents"
        response = supabase.storage.from_(bucket_name).upload(
            filename,
            file_content,
            {
                "content-type": file.content_type
            }
        )
        
        # Get public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(filename)
        
        # Save document record to database
        doc_record = {
            "employee_id": employee_id,
            "document_type": document_type,
            "filename": file.filename,
            "storage_path": filename,
            "file_url": public_url,
            "uploaded_at": datetime.now().isoformat()
        }
        
        supabase.table("employee_documents").insert(doc_record).execute()
        
        return {
            "success": True,
            "filename": filename,
            "url": public_url
        }
    except Exception as e:
        print(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/employee/documents/{employee_id}")
async def get_employee_documents(employee_id: int):
    """Get all documents for an employee"""
    try:
        from services.supabase_service import supabase
        
        response = supabase.table("employee_documents")\
            .select("*")\
            .eq("employee_id", employee_id)\
            .order("uploaded_at", desc=True)\
            .execute()
        
        return {"success": True, "documents": response.data}
    except Exception as e:
        print(f"Error fetching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/document/{document_id}")
async def delete_document(document_id: int):
    """Delete a document"""
    try:
        from services.supabase_service import supabase
        
        # Get document record
        response = supabase.table("employee_documents")\
            .select("*")\
            .eq("id", document_id)\
            .single()\
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete from storage
        storage_path = response.data["storage_path"]
        bucket_name = "employee-documents"
        supabase.storage.from_(bucket_name).remove([storage_path])
        
        # Delete database record
        supabase.table("employee_documents").delete().eq("id", document_id).execute()
        
        return {"success": True, "message": "Document deleted"}
    except Exception as e:
        print(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ====================
# Search & Filter Endpoints
# ====================

@app.get("/api/admin/attendance/filter")
async def filter_attendance(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    employee_email: Optional[str] = None,
    status: Optional[str] = None
):
    """Filter attendance records by date range, employee, and status"""
    try:
        from services.supabase_service import supabase
        
        query = supabase.table("attendance").select("*, employees(name, email, employee_id)")
        
        if start_date:
            query = query.gte("date", start_date)
        if end_date:
            query = query.lte("date", end_date)
        if status:
            query = query.eq("status", status)
        
        response = query.order("date", desc=True).execute()
        
        # Filter by employee email if provided
        if employee_email:
            response.data = [r for r in response.data if r.get("employees", {}).get("email") == employee_email]
        
        return {"success": True, "attendance": response.data}
    except Exception as e:
        print(f"Error filtering attendance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/leave-requests/filter")
async def filter_leave_requests(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    employee_email: Optional[str] = None,
    status: Optional[str] = None,
    leave_type: Optional[str] = None
):
    """Filter leave requests by date range, employee, status, and leave type"""
    try:
        from services.supabase_service import supabase
        
        query = supabase.table("leave_requests").select("*, employees(name, email, employee_id)")
        
        if start_date:
            query = query.gte("start_date", start_date)
        if end_date:
            query = query.lte("end_date", end_date)
        if status:
            query = query.eq("status", status)
        if leave_type:
            query = query.eq("leave_type", leave_type)
        
        response = query.order("start_date", desc=True).execute()
        
        # Filter by employee email if provided
        if employee_email:
            response.data = [r for r in response.data if r.get("employees", {}).get("email") == employee_email]
        
        return {"success": True, "leave_requests": response.data}
    except Exception as e:
        print(f"Error filtering leave requests: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/payroll-runs/filter")
async def filter_payroll_runs(
    month: Optional[int] = None,
    year: Optional[int] = None,
    employee_email: Optional[str] = None
):
    """Filter payroll runs by month, year, and employee"""
    try:
        from services.supabase_service import supabase
        
        query = supabase.table("payroll_runs").select("*, employees(name, email, employee_id)")
        
        if month:
            query = query.eq("month", month)
        if year:
            query = query.eq("year", year)
        
        response = query.order("year", desc=True).order("month", desc=True).execute()
        
        # Filter by employee email if provided
        if employee_email:
            response.data = [r for r in response.data if r.get("employees", {}).get("email") == employee_email]
        
        return {"success": True, "payroll_runs": response.data}
    except Exception as e:
        print(f"Error filtering payroll runs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PDF PAYSLIP DOWNLOAD
# ============================================================================
@app.get("/api/employee/payslip/download/{payroll_run_id}")
async def download_payslip(payroll_run_id: int):
    """Generate and download PDF payslip for a payroll run"""
    try:
        # Get payroll run details
        payroll_response = supabase.table("payroll_runs").select("*, employees(*)").eq("id", payroll_run_id).single().execute()
        if not payroll_response.data:
            raise HTTPException(status_code=404, detail="Payroll run not found")
        
        payroll_data = payroll_response.data
        employee_id = payroll_data.get("employee_id")
        
        # Generate payslip PDF in memory
        pdf_buffer = io.BytesIO()
        generate_payslip_for_employee(employee_id, payroll_run_id, output_path=pdf_buffer)
        pdf_buffer.seek(0)
        
        # Return as downloadable file
        employee_name = payroll_data.get("employees", {}).get("name", "Employee").replace(" ", "_")
        month = payroll_data.get("month")
        year = payroll_data.get("year")
        filename = f"Payslip_{employee_name}_{year}_{month:02d}.pdf"
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        print(f"Error generating payslip: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# CSV EXPORT ENDPOINTS
# ============================================================================
@app.get("/api/admin/export/attendance")
async def export_attendance_csv(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    employee_email: Optional[str] = None
):
    """Export attendance records to CSV"""
    try:
        query = supabase.table("attendance").select("*, employees(name, email, employee_id)")
        
        if start_date:
            query = query.gte("date", start_date)
        if end_date:
            query = query.lte("date", end_date)
        
        response = query.order("date", desc=True).execute()
        data = response.data
        
        # Filter by employee if needed
        if employee_email:
            data = [r for r in data if r.get("employees", {}).get("email") == employee_email]
        
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date", "Employee Name", "Email", "Check In", "Check Out", "Work Hours", "Status"])
        
        for record in data:
            emp = record.get("employees", {})
            writer.writerow([
                record.get("date", ""),
                emp.get("name", ""),
                emp.get("email", ""),
                record.get("check_in_time", ""),
                record.get("check_out_time", ""),
                record.get("work_hours", 0),
                record.get("status", "")
            ])
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=attendance_export.csv"}
        )
    except Exception as e:
        print(f"Error exporting attendance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/export/leave-requests")
async def export_leave_requests_csv(
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Export leave requests to CSV"""
    try:
        query = supabase.table("leave_requests").select("*, employees(name, email, employee_id), leave_types(name)")
        
        if status:
            query = query.eq("status", status)
        if start_date:
            query = query.gte("start_date", start_date)
        if end_date:
            query = query.lte("end_date", end_date)
        
        response = query.order("start_date", desc=True).execute()
        data = response.data
        
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Employee Name", "Email", "Leave Type", "Start Date", "End Date", "Days", "Half Day", "Reason", "Status"])
        
        for record in data:
            emp = record.get("employees", {})
            leave_type = record.get("leave_types", {})
            writer.writerow([
                emp.get("name", ""),
                emp.get("email", ""),
                leave_type.get("name", ""),
                record.get("start_date", ""),
                record.get("end_date", ""),
                record.get("days_requested", 0),
                "Yes" if record.get("is_half_day") else "No",
                record.get("reason", ""),
                record.get("status", "")
            ])
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=leave_requests_export.csv"}
        )
    except Exception as e:
        print(f"Error exporting leave requests: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/export/payroll")
async def export_payroll_csv(
    month: Optional[int] = None,
    year: Optional[int] = None
):
    """Export payroll runs to CSV"""
    try:
        query = supabase.table("payroll_runs").select("*, employees(name, email, employee_id)")
        
        if month:
            query = query.eq("month", month)
        if year:
            query = query.eq("year", year)
        
        response = query.order("year", desc=True).order("month", desc=True).execute()
        data = response.data
        
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Employee Name", "Email", "Month", "Year", "Basic Salary", "Gross Salary", "EPF Employee", "EPF Employer", "SOCSO Employee", "SOCSO Employer", "PCB/Tax", "Net Pay", "Status"])
        
        for record in data:
            emp = record.get("employees", {})
            writer.writerow([
                emp.get("name", ""),
                emp.get("email", ""),
                record.get("month", ""),
                record.get("year", ""),
                record.get("basic_salary", 0),
                record.get("gross_salary", 0),
                record.get("epf_employee", 0),
                record.get("epf_employer", 0),
                record.get("socso_employee", 0),
                record.get("socso_employer", 0),
                record.get("pcb_tax", 0),
                record.get("net_salary", 0),
                record.get("status", "")
            ])
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=payroll_export.csv"}
        )
    except Exception as e:
        print(f"Error exporting payroll: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# FILE UPLOAD ENDPOINTS
# ============================================================================
@app.post("/api/upload/document")
async def upload_document(
    file: UploadFile = File(...),
    employee_email: str = Form(...),
    is_leave_request: bool = Form(False)
):
    """Upload document (for training, trips, leave requests, etc.)"""
    try:
        # Save file temporarily
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Upload to Supabase Storage
        public_url = upload_document_to_bucket(temp_path, employee_email, is_leave_request)
        
        # Clean up temp file
        os.remove(temp_path)
        
        if public_url:
            return {"success": True, "url": public_url, "filename": file.filename}
        else:
            raise HTTPException(status_code=500, detail="Failed to upload document")
    except Exception as e:
        print(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# CONFIGURATION UI ENDPOINTS
# ============================================================================
@app.get("/api/config/leave-types")
async def get_leave_types():
    """Get all leave types configuration"""
    try:
        response = supabase.table("leave_types").select("*").execute()
        return {"success": True, "leave_types": response.data}
    except Exception as e:
        print(f"Error fetching leave types: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config/leave-types")
async def create_leave_type(
    name: str = Form(...),
    days_per_year: float = Form(...),
    description: Optional[str] = Form(None)
):
    """Create new leave type"""
    try:
        response = supabase.table("leave_types").insert({
            "name": name,
            "days_per_year": days_per_year,
            "description": description
        }).execute()
        return {"success": True, "leave_type": response.data[0]}
    except Exception as e:
        print(f"Error creating leave type: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/config/leave-types/{leave_type_id}")
async def update_leave_type(
    leave_type_id: int,
    name: str = Form(...),
    days_per_year: float = Form(...),
    description: Optional[str] = Form(None)
):
    """Update leave type"""
    try:
        response = supabase.table("leave_types").update({
            "name": name,
            "days_per_year": days_per_year,
            "description": description
        }).eq("id", leave_type_id).execute()
        return {"success": True, "leave_type": response.data[0]}
    except Exception as e:
        print(f"Error updating leave type: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/config/leave-types/{leave_type_id}")
async def delete_leave_type(leave_type_id: int):
    """Delete leave type"""
    try:
        response = supabase.table("leave_types").delete().eq("id", leave_type_id).execute()
        return {"success": True}
    except Exception as e:
        print(f"Error deleting leave type: {str(e)}")
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
