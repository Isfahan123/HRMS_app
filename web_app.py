"""
Web application entry point for HRMS
This provides a web-based interface using HTML/JavaScript with Python backend
"""
from flask import Flask, request, jsonify, render_template, send_file, Response, make_response
from typing import Optional, List, Dict, Any
import os
import csv
import io
import re
import json
import requests
import logging
import sys
from datetime import datetime

# Add gui directory to path for payslip_generator import (done at module level for efficiency)
_gui_path = os.path.join(os.path.dirname(__file__), 'gui')
if _gui_path not in sys.path:
    sys.path.insert(0, _gui_path)

# Import configuration
from config import config

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
    get_variable_percentage_config,
    get_attendance_settings,
    update_attendance_settings,
    calculate_working_days
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
    insert_employee_history_record,
    update_employee_history_record,
    delete_employee_history_record
)
from core.employee_service import calculate_cumulative_service

# Create Flask app
app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), "web", "templates"),
            static_folder=os.path.join(os.path.dirname(__file__), "web", "static"))

# Setup templates and static files
# Ensure directories exist
templates_dir = os.path.join(os.path.dirname(__file__), "web", "templates")
static_dir = os.path.join(os.path.dirname(__file__), "web", "static")
os.makedirs(templates_dir, exist_ok=True)
os.makedirs(static_dir, exist_ok=True)
os.makedirs(os.path.join(static_dir, "css"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "js"), exist_ok=True)

def get_template_context(**kwargs):
    """Get template context with config values"""
    return config.get_template_context(request=request, **kwargs)


# Helper functions
def normalize_payroll_date(payroll_date: str) -> Optional[str]:
    """
    Normalize payroll date to YYYY-MM-DD format.
    Accepts YYYY-MM (month input) or YYYY-MM-DD formats.
    Returns the first day of the month (day 01) for YYYY-MM format.
    Returns None if the date is invalid.
    """
    # Try YYYY-MM format first (from HTML month input)
    try:
        parsed = datetime.strptime(payroll_date, "%Y-%m")
        return parsed.strftime("%Y-%m-%d")
    except ValueError:
        pass
    
    # Try YYYY-MM-DD format
    try:
        datetime.strptime(payroll_date, "%Y-%m-%d")
        return payroll_date
    except ValueError:
        return None

# Routes
@app.route("/")
def root():
    """Serve the login page"""
    context = get_template_context(page_title="Login - HRMS")
    return render_template("login.html", **context)

@app.route("/dashboard")
def dashboard():
    """Serve the dashboard page"""
    context = get_template_context(page_title="Employee Dashboard - HRMS")
    return render_template("dashboard.html", **context)

@app.route("/admin-dashboard")
def admin_dashboard():
    """Serve the admin dashboard page"""
    context = get_template_context(page_title="Admin Dashboard - HRMS")
    return render_template("admin_dashboard.html", **context)

@app.route("/demo")
def demo_dashboard():
    """Serve the demo dashboard page (for testing UI without auth)"""
    context = get_template_context(page_title="Demo Dashboard - HRMS")
    return render_template("demo_dashboard.html", **context)

@app.route("/admin-preview")
def admin_preview():
    """Serve the full admin dashboard for preview (no auth required)"""
    context = get_template_context(page_title="Admin Preview - HRMS")
    return render_template("admin_dashboard.html", **context)

@app.route("/test-subtabs")
def test_subtabs():
    """Test page to verify subtabs fix"""
    context = get_template_context(page_title="Test Subtabs - HRMS")
    return render_template("test_subtabs.html", **context)

@app.route("/ux-demo")
def ux_demo():
    """UX components demonstration page"""
    context = get_template_context(page_title="UX Demo - HRMS")
    return render_template("ux_demo.html", **context)

@app.route("/table-test")
def table_test():
    """Table mobile scrolling test page"""
    context = get_template_context(page_title="Table Test - HRMS")
    return render_template("table_test.html", **context)

@app.route("/WEB_INTERFACE_GUIDE.md")
def serve_guide():
    """Serve the web interface guide"""
    import os
    guide_path = os.path.join(os.path.dirname(__file__), "WEB_INTERFACE_GUIDE.md")
    if os.path.exists(guide_path):
        with open(guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({"content": content, "format": "markdown"})
    return jsonify({"error": "Guide not found"})

# API Endpoints
@app.route("/api/login", methods=["POST"])
def api_login():
    """
    Handle user login
    Reuses existing login_user_by_username function from services
    """
    try:
        login_data = request.get_json()
        username = login_data.get("username", "").strip().lower()
        password = login_data.get("password", "")
        
        if not username or not password:
            return jsonify({
                "success": False,
                "message": "Please enter both username and password"
            })
        
        result = login_user_by_username(username, password)
        
        # Check if account is locked
        if result and result.get("locked_until"):
            locked_until = result.get("locked_until")
            try:
                display_locked = convert_utc_to_kl(locked_until)
            except Exception:
                display_locked = locked_until
            
            return jsonify({
                "success": False,
                "message": f"Account is locked until {display_locked} (Malaysia Time)",
                "locked_until": display_locked
            })
        
        # Check if login successful
        if result and result.get("role"):
            return jsonify({
                "success": True,
                "message": "Login successful",
                "role": result["role"].lower(),
                "email": result.get("email", "").lower()
            })
        else:
            return jsonify({
                "success": False,
                "message": "Invalid username or password"
            })
            
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An error occurred during login"
        })


@app.route("/api/employee/<email>")
def get_employee_data(email):
    """
    Get employee data by email
    """
    try:
        response = supabase.table("employees").select("*").eq("email", email.lower()).execute()
        if response.data and len(response.data) > 0:
            return jsonify({"success": True, "data": response.data[0]})
        else:
            return jsonify({"success": False, "message": "Employee not found"})
    except Exception as e:
        print(f"Error fetching employee: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/attendance/<email>")
def get_attendance(email):
    """
    Get attendance history for employee
    Reuses existing get_attendance_history function
    """
    try:
        attendance_data = get_attendance_history(email)
        return jsonify({"success": True, "data": attendance_data})
    except Exception as e:
        print(f"Error fetching attendance: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/leave-requests/<email>")
def get_leave_requests(email):
    """
    Get leave requests for employee
    Reuses existing fetch_user_leave_requests function
    """
    try:
        leave_requests = fetch_user_leave_requests(email)
        return jsonify({"success": True, "data": leave_requests})
    except Exception as e:
        print(f"Error fetching leave requests: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/leave-balance/<email>")
def get_leave_balance(email):
    """
    Get leave balance for a specific employee by email
    Returns both annual and sick leave balances
    """
    try:
        from services.supabase_service import get_individual_employee_leave_balance, get_individual_employee_sick_leave_balance
        
        current_year = datetime.now().year
        
        # Get annual leave balance
        annual_balance = get_individual_employee_leave_balance(email, current_year)
        # Get sick leave balance
        sick_balance = get_individual_employee_sick_leave_balance(email, current_year)
        
        return {
            "success": True,
            "balances": {
                "annual": annual_balance.get('remaining_days', 0),
                "sick": sick_balance.get('remaining_sick_days', 0)
            }
        }
    except Exception as e:
        print(f"Error getting leave balance: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/employees")
def list_employees():
    """
    List all employees (admin only - add authentication later)
    """
    try:
        response = supabase.table("employees").select("*").execute()
        return jsonify({"success": True, "data": response.data})
    except Exception as e:
        print(f"Error listing employees: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/payroll/<employee_id>")
def get_payroll_history(employee_id):
    """
    Get payroll history for employee
    Reuses existing get_employee_payroll_history function
    """
    try:
        payroll_data = get_employee_payroll_history(employee_id)
        return jsonify({"success": True, "data": payroll_data})
    except Exception as e:
        print(f"Error fetching payroll: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/engagements/<employee_id>")
def get_engagements(employee_id):
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
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/engagements", methods=["POST"])
def create_engagement():
    """
    Create a new engagement (training/course/trip) record
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['type', 'title', 'start_date', 'end_date']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"success": False, "message": f"Missing required field: <field>"})
        
        # Look up employee_id from employee_email if not provided
        if not data.get('employee_id'):
            employee_email = data.get('employee_email')
            if not employee_email:
                return jsonify({"success": False, "message": "Missing required field: employee_email or employee_id"})
            
            # Fetch employee UUID from email
            emp_response = supabase.table("employees").select("id").eq("email", employee_email.lower()).execute()
            if not emp_response.data:
                return jsonify({"success": False, "message": f"Employee not found with email: <employee_email>"})
            
            data['employee_id'] = emp_response.data[0]['id']
        
        # Add timestamps and default status
        data['created_at'] = datetime.utcnow().isoformat()
        if 'status' not in data:
            data['status'] = 'pending'  # For employee submissions
        
        # Determine which table to insert into based on type and map fields accordingly
        if data['type'] in ['training', 'course']:
            table_name = "training_course_records"
            # Map common fields to table-specific required fields
            # training_course_records requires: course_name (NOT NULL), course_date (NOT NULL)
            if 'course_name' not in data or not data['course_name']:
                data['course_name'] = data.get('title', 'Training/Course')
            if 'course_date' not in data or not data['course_date']:
                data['course_date'] = data.get('start_date')
        elif data['type'] == 'overseas_trip':
            table_name = "overseas_work_trip_records"
            # Map common fields to table-specific required fields
            # overseas_work_trip_records requires: location (NOT NULL), trip_date (NOT NULL)
            if 'trip_date' not in data or not data['trip_date']:
                data['trip_date'] = data.get('start_date')
            if 'location' not in data or not data['location']:
                # Build location from city, state, country or use title/description
                location_parts = []
                if data.get('city'):
                    location_parts.append(data['city'])
                if data.get('state'):
                    location_parts.append(data['state'])
                if data.get('country'):
                    location_parts.append(data['country'])
                if location_parts:
                    data['location'] = ', '.join(location_parts)
                else:
                    data['location'] = data.get('title') or data.get('description') or 'Overseas Trip'
        else:
            table_name = "engagements"
        
        response = supabase.table(table_name).insert(data).execute()
        
        if response.data:
            return jsonify({"success": True, "message": "Engagement submitted successfully", "data": response.data[0]})
        else:
            return jsonify({"success": False, "message": "Failed to submit engagement"})
    except Exception as e:
        print(f"Error creating engagement: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/engagements/all")
def get_all_engagements():
    """
    Get all engagements across all employees (admin only)
    """
    try:
        all_data = []
        
        # Fetch from all engagement tables
        try:
            training_response = supabase.table("training_course_records").select("*").order("created_at", desc=True).limit(100).execute()
            if training_response.data:
                for record in training_response.data:
                    record['type'] = 'training'
                    all_data.append(record)
        except:
            pass
        
        try:
            trips_response = supabase.table("overseas_work_trip_records").select("*").order("created_at", desc=True).limit(100).execute()
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
        
        return jsonify({"success": True, "data": all_data})
    except Exception as e:
        print(f"Error getting all engagements: {str(e)}")
        return jsonify({"success": False, "message": str(e), "data": []})

@app.route("/api/admin/engagements/<engagement_id>", methods=["PUT"])
def update_engagement_record(engagement_id):
    """
    Update an engagement record (admin only)
    """
    try:
        data = request.get_json()
        
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
                return jsonify({"success": True, "message": "Engagement updated successfully", "data": response.data[0]})
            success = True
        except Exception as e:
            error_msg = str(e)
        
        # Try training_courses table
        try:
            response = supabase.table("training_course_records").update(data).eq("id", engagement_id).execute()
            if response.data:
                return jsonify({"success": True, "message": "Training course updated successfully", "data": response.data[0]})
            success = True
        except Exception as e:
            error_msg = str(e)
        
        # Try overseas_trips table
        try:
            response = supabase.table("overseas_work_trip_records").update(data).eq("id", engagement_id).execute()
            if response.data:
                return jsonify({"success": True, "message": "Overseas trip updated successfully", "data": response.data[0]})
            success = True
        except Exception as e:
            error_msg = str(e)
        
        if not success:
            return jsonify({"success": False, "message": f"Failed to update engagement: <error_msg>"})
        
        return jsonify({"success": True, "message": "Engagement updated successfully"})
    except Exception as e:
        print(f"Error updating engagement: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/engagements/<engagement_id>", methods=["DELETE"])
def delete_engagement_record(engagement_id):
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
                return jsonify({"success": True, "message": "Engagement deleted successfully"})
            deleted = True
        except Exception as e:
            error_msg = str(e)
        
        # Try training_courses table
        try:
            response = supabase.table("training_course_records").delete().eq("id", engagement_id).execute()
            if response.data:
                return jsonify({"success": True, "message": "Training course deleted successfully"})
            deleted = True
        except Exception as e:
            error_msg = str(e)
        
        # Try overseas_trips table
        try:
            response = supabase.table("overseas_work_trip_records").delete().eq("id", engagement_id).execute()
            if response.data:
                return jsonify({"success": True, "message": "Overseas trip deleted successfully"})
            deleted = True
        except Exception as e:
            error_msg = str(e)
        
        if not deleted:
            return jsonify({"success": False, "message": f"Failed to delete engagement: <error_msg>"})
        
        return jsonify({"success": True, "message": "Engagement deleted successfully"})
    except Exception as e:
        print(f"Error deleting engagement: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/attendance")
def get_all_attendance():
    """
    Get all attendance records (admin only)
    """
    try:
        attendance_data = get_all_attendance_records()
        return jsonify({"success": True, "data": attendance_data})
    except Exception as e:
        print(f"Error fetching all attendance: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/attendance-settings")
def get_attendance_settings_api():
    """
    Get attendance/working hours settings
    """
    try:
        settings = get_attendance_settings()
        return jsonify({"success": True, "data": settings})
    except Exception as e:
        print(f"Error fetching attendance settings: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/attendance-settings", methods=["POST"])
def update_attendance_settings_api():
    """
    Update attendance/working hours settings
    """
    try:
        data = request.get_json()
        start_time = data.get("work_start", "09:00")
        end_time = data.get("work_end", "18:00")
        limit_time = data.get("clock_in_limit", "09:30")
        
        success = update_attendance_settings(start_time, end_time, limit_time)
        
        if success:
            return jsonify({"success": True, "message": "Working hours updated successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to update working hours"})
    except Exception as e:
        print(f"Error updating attendance settings: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/leave-requests")
def get_all_leave_requests():
    """
    Get all leave requests for admin approval
    """
    try:
        # Fetch leave requests without join to avoid foreign key relationship requirement
        response = supabase.table("leave_requests").select("*").order("created_at", desc=True).execute()
        
        if not response.data:
            return jsonify({"success": True, "data": []})
        
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
        
        return jsonify({"success": True, "data": leave_requests})
    except Exception as e:
        print(f"Error fetching leave requests: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/leave-requests/<leave_id>/approve", methods=["POST"])
def approve_leave_request(leave_id):
    """
    Approve a leave request
    """
    try:
        # Get admin email from session (for now using a placeholder)
        admin_email = "admin@hrms.com"
        success = update_leave_request_status(leave_id, "approved", admin_email)
        if success:
            return jsonify({"success": True, "message": "Leave request approved"})
        else:
            return jsonify({"success": False, "message": "Failed to approve leave request"})
    except Exception as e:
        print(f"Error approving leave: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/leave-requests/<leave_id>/reject", methods=["POST"])
def reject_leave_request(leave_id):
    """
    Reject a leave request
    """
    try:
        # Get admin email from session (for now using a placeholder)
        admin_email = "admin@hrms.com"
        success = update_leave_request_status(leave_id, "rejected", admin_email)
        if success:
            return jsonify({"success": True, "message": "Leave request rejected"})
        else:
            return jsonify({"success": False, "message": "Failed to reject leave request"})
    except Exception as e:
        print(f"Error rejecting leave: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/leave-requests/submit", methods=["POST"])
def submit_new_leave_request():
    """
    Submit a new leave request
    """
    try:
        data = request.get_json()
        employee_email = data.get("employee_email")
        leave_type = data.get("leave_type")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        title = data.get("title", "Leave Request")
        is_half_day = data.get("is_half_day", False)
        half_day_period = data.get("half_day_period")
        
        if not all([employee_email, leave_type, start_date, end_date]):
            return jsonify({"success": False, "message": "Missing required fields"})
        
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
            return jsonify({"success": True, "message": "Leave request submitted successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to submit leave request"})
    except Exception as e:
        print(f"Error submitting leave request: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/working-days")
def get_working_days():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    state = request.args.get("state")
    """
    Calculate working days between two dates, excluding weekends and holidays.
    Uses the same calculation logic as the leave request approval.
    
    Query Parameters:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        state: Optional Malaysian state for state-specific holidays
    """
    try:
        if not start_date or not end_date:
            return jsonify({"success": False, "message": "start_date and end_date are required"})
        
        # Use the centralized calculate_working_days function
        working_days = calculate_working_days(start_date, end_date, state=state)
        
        return {
            "success": True,
            "working_days": working_days,
            "start_date": start_date,
            "end_date": end_date,
            "state": state
        }
    except Exception as e:
        print(f"Error calculating working days: {str(e)}")
        return jsonify({"success": False, "message": str(e), "working_days": 1})

@app.route("/api/employee/<email>", methods=["PUT"])
def update_employee_profile(email):
    """
    Update employee profile information
    """
    try:
        data = request.get_json()
        
        # Get employee_id first
        emp_response = supabase.table("employees").select("id").eq("email", email.lower()).execute()
        if not emp_response.data or len(emp_response.data) == 0:
            return jsonify({"success": False, "message": "Employee not found"})
        
        employee_id = emp_response.data[0]["id"]
        
        # Update employee
        result = update_employee(employee_id, data)
        
        if result:
            return jsonify({"success": True, "message": "Profile updated successfully", "data": result})
        else:
            return jsonify({"success": False, "message": "Failed to update profile"})
    except Exception as e:
        print(f"Error updating employee: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/employees", methods=["POST"])
def create_new_employee():
    """
    Create a new employee (admin only)
    """
    try:
        data = request.get_json()
        password = data.pop("password", None)
        
        result = insert_employee(data, password)
        
        if result and result.get("success"):
            return jsonify({"success": True, "message": "Employee created successfully", "data": result, "employee_id": data.get("employee_id")})
        else:
            error_message = result.get("error") if result else "Failed to create employee"
            return jsonify({"success": False, "message": error_message})
    except Exception as e:
        print(f"Error creating employee: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/employees/<employee_id>", methods=["PUT"])
def update_employee_admin(employee_id):
    """
    Update employee information (admin only)
    """
    try:
        data = request.get_json()
        
        result = update_employee(employee_id, data)
        
        if result:
            return jsonify({"success": True, "message": "Employee updated successfully", "data": result})
        else:
            return jsonify({"success": False, "message": "Failed to update employee"})
    except Exception as e:
        print(f"Error updating employee: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/employees/<employee_id>", methods=["DELETE"])
def delete_employee_endpoint(employee_id):
    """
    Delete an employee (admin only)
    """
    try:
        result = delete_employee(employee_id)
        
        if result.get("success"):
            return jsonify({"success": True, "message": "Employee deleted successfully"})
        else:
            return jsonify({"success": False, "message": result.get("error", "Failed to delete employee")})
    except Exception as e:
        print(f"Error deleting employee: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/payroll-runs")
def get_all_payroll_runs():
    """
    Get all payroll runs (admin only)
    """
    try:
        payroll_runs = get_payroll_runs()
        return jsonify({"success": True, "data": payroll_runs})
    except Exception as e:
        print(f"Error fetching payroll runs: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/payroll/run", methods=["POST"])
def run_payroll_processing():
    """
    Run payroll for a specific month/year (admin only)
    """
    try:
        data = request.get_json()
        payroll_date = data.get("payroll_date")  # Format: YYYY-MM from month input
        
        if not payroll_date:
            return jsonify({"success": False, "message": "Payroll date is required"})
        
        # Convert YYYY-MM to YYYY-MM-DD format
        # The run_payroll function expects YYYY-MM-DD format
        # Payroll is run on the first day of the month (day 01) for the given month
        payroll_date = normalize_payroll_date(payroll_date)
        if payroll_date is None:
            return jsonify({"success": False, "message": "Invalid date format. Use YYYY-MM or YYYY-MM-DD"})
        
        success = run_payroll(payroll_date)
        
        if success:
            return jsonify({"success": True, "message": f"Payroll processed successfully for <payroll_date>"})
        else:
            return jsonify({"success": False, "message": "Failed to process payroll"})
    except Exception as e:
        print(f"Error running payroll: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/bonuses")
def get_all_bonuses():
    """
    Get all bonus records (admin only)
    """
    try:
        # Fetch bonuses without join - bonuses table already has employee_name field
        response = supabase.table("bonuses").select("*").order("created_at", desc=True).execute()
        return jsonify({"success": True, "data": response.data})
    except Exception as e:
        print(f"Error fetching bonuses: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/bonuses", methods=["POST"])
def create_bonus():
    """
    Create a new bonus record (admin only)
    """
    try:
        data = request.get_json()
        
        response = supabase.table("bonuses").insert(data).execute()
        
        if response.data:
            return jsonify({"success": True, "message": "Bonus created successfully", "data": response.data})
        else:
            return jsonify({"success": False, "message": "Failed to create bonus"})
    except Exception as e:
        print(f"Error creating bonus: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/bonuses/<bonus_id>", methods=["PUT"])
def update_bonus(bonus_id):
    """
    Update a bonus record (admin only)
    """
    try:
        data = request.get_json()
        
        response = supabase.table("bonuses").update(data).eq("id", bonus_id).execute()
        
        if response.data:
            return jsonify({"success": True, "message": "Bonus updated successfully", "data": response.data})
        else:
            return jsonify({"success": False, "message": "Failed to update bonus"})
    except Exception as e:
        print(f"Error updating bonus: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/bonuses/<bonus_id>", methods=["DELETE"])
def delete_bonus(bonus_id):
    """
    Delete a bonus record (admin only)
    """
    try:
        response = supabase.table("bonuses").delete().eq("id", bonus_id).execute()
        
        if response.data:
            return jsonify({"success": True, "message": "Bonus deleted successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to delete bonus"})
    except Exception as e:
        print(f"Error deleting bonus: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

def _safe_to_float(value):
    """
    Safely convert a value to float, handling dicts, numbers, and None.
    
    Args:
        value: Can be None, a number, a string, or a dictionary
        
    Returns:
        float: Converted value or 0.0 on failure
        
    Examples:
        - _safe_to_float(None) -> 0.0
        - _safe_to_float(100) -> 100.0
        - _safe_to_float("150") -> 150.0
        - _safe_to_float({"transport": 100, "housing": 200}) -> 300.0
        - _safe_to_float({}) -> 0.0
    """
    if value is None:
        return 0.0
    if isinstance(value, dict):
        # Sum all numeric values in the dictionary
        total = 0.0
        for key, v in value.items():
            if v is not None:
                try:
                    total += float(v)
                except (ValueError, TypeError):
                    logging.warning(f"Could not convert dictionary value for key '<key>': {v!r}")
        return total
    try:
        return float(value)
    except (ValueError, TypeError):
        logging.warning(f"Could not convert value to float: {value!r}")
        return 0.0

@app.route("/api/payroll/payslip/<employee_id>/<payroll_run_id>")
def generate_payslip(employee_id: str, payroll_run_id: str):
    """
    Generate and download payslip PDF for an employee
    Uses fpdf2-based PDF generator (pure Python, web-compatible)
    """
    try:
        import tempfile
        
        from core.pdf_generator import generate_payslip_for_employee as generate_pdf
        
        # Get employee data for filename
        employee_response = supabase.table("employees").select("employee_id, full_name").eq("id", employee_id).execute()
        if not employee_response.data:
            return jsonify({"success": False, "message": f"Employee with ID '<employee_id>' not found in database"}), 404
        
        employee = employee_response.data[0]
        
        # Get payroll run data for filename
        payroll_response = supabase.table("payroll_runs").select("month_year").eq("id", payroll_run_id).execute()
        if not payroll_response.data:
            return jsonify({"success": False, "message": f"Payroll run with ID '<payroll_run_id>' not found in database"}), 404
        
        payroll = payroll_response.data[0]
        
        # Create temp directory for output
        temp_dir = tempfile.gettempdir()
        month_year = payroll.get('month_year') or 'unknown'
        employee_display_id = employee.get('employee_id') or employee_id
        output_filename = f"payslip_<employee_display_id>_{month_year.replace('/', '_')}.pdf"
        output_path = os.path.join(temp_dir, output_filename)
        
        # Generate payslip using Python-based generator (same as desktop GUI)
        result_path = generate_pdf(employee_id, payroll_run_id, output_path)
        
        if not result_path or not os.path.exists(result_path):
            raise HTTPException(
                status_code=500, 
                detail=f"Payslip PDF generation failed for employee '{employee.get('full_name', employee_id)}' and payroll period '{payroll.get('month_year', 'unknown')}'. Ensure the employee has payroll data for this period."
            )
        
        # Return the PDF file
        return FileResponse(
            result_path,
            media_type="application/pdf",
            filename=output_filename,
            headers={"Content-Disposition": f"attachment; filename=<output_filename>"}
        )
    except Exception as e:
        print(f"Error generating payslip: {str(e)}")
        return jsonify({"success": False, "message": f"Unexpected error generating payslip: {str(e)}"}), 500

@app.route("/api/admin/leave-balances")
def get_leave_balances():
    """
    Get annual leave balances for all employees
    """
    try:
        from services.supabase_service import get_employee_leave_balances
        current_year = datetime.now().year
        balances = get_employee_leave_balances(current_year)
        return jsonify({"success": True, "data": balances})
    except Exception as e:
        print(f"Error getting leave balances: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/sick-leave-balances")
def get_sick_leave_balances():
    """
    Get sick leave balances for all employees
    """
    try:
        # Query employees and their sick leave balances with department info
        from services.supabase_service import get_individual_employee_sick_leave_balance
        
        current_year = datetime.now().year
        response = supabase.table("employees").select("id, employee_id, full_name, email, department").execute()
        
        if not response.data:
            return jsonify({"success": True, "data": []})
        
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
        
        return jsonify({"success": True, "data": balances})
    except Exception as e:
        print(f"Error getting sick leave balances: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/leave-balances/<employee_email>", methods=["PUT"])
def update_leave_balance(employee_email):
    """
    Update an employee's leave balance
    """
    try:
        from services.supabase_service import update_employee_leave_balance
        data = request.get_json()
        
        year = data.get('year', datetime.now().year)
        employee_email_decoded = employee_email.replace('%40', '@')
        
        # Get employee_id from email
        emp_response = supabase.table("employees").select("employee_id").eq("email", employee_email_decoded).execute()
        if not emp_response.data:
            return jsonify({"success": False, "message": "Employee not found"})
        
        employee_id = emp_response.data[0]['employee_id']
        
        # Update balance
        result = update_employee_leave_balance(employee_id, year, data)
        
        return jsonify({"success": True, "message": "Leave balance updated successfully"})
    except Exception as e:
        print(f"Error updating leave balance: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/leave-balances/carry-forward", methods=["POST"])
def process_carry_forward():
    """
    Process year-end carry forward for all employees
    """
    try:
        from services.supabase_service import process_year_end_carry_forward
        data = request.get_json()
        
        year = data.get('year', datetime.now().year)
        rules = data.get('rules', {})
        
        result = process_year_end_carry_forward(year, rules)
        
        return jsonify({"success": result, "message": "Carry forward processed successfully" if result else "Failed to process carry forward"})
    except Exception as e:
        print(f"Error processing carry forward: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/leave-balances/set-carry-forward-all", methods=["POST"])
def set_carry_forward_all():
    """
    Set carried forward days for all employees
    """
    try:
        from services.supabase_service import set_carried_forward_for_all
        data = request.get_json()
        
        current_year = data.get('current_year', datetime.now().year)
        next_year = data.get('next_year', current_year + 1)
        days = data.get('days', 0)
        applies_to = data.get('applies_to', 'all')
        
        result = set_carried_forward_for_all(current_year, next_year, days, applies_to)
        
        return jsonify({"success": result, "message": f"Set <days> carried forward days for all employees" if result else "Failed to set carried forward"})
    except Exception as e:
        print(f"Error setting carry forward for all: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/unpaid-leave-summary")
def get_unpaid_leave_summary():
    """
    Get unpaid leave summary for all employees
    """
    try:
        from services.supabase_service import get_monthly_unpaid_leave_summary
        current_year = datetime.now().year
        
        # Get all employees
        response = supabase.table("employees").select("id, employee_id, full_name, email").execute()
        
        if not response.data:
            return jsonify({"success": True, "data": []})
        
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
        
        return jsonify({"success": True, "data": summaries})
    except Exception as e:
        print(f"Error getting unpaid leave summary: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/payroll-contributions")
def get_payroll_contributions():
    """
    Get EPF, SOCSO, EIS contributions summary
    """
    try:
        # Get all payroll runs
        response = supabase.table("payroll_runs").select("*").order("created_at", desc=True).limit(100).execute()
        
        if not response.data:
            return jsonify({"success": True, "data": []})
        
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
        
        return jsonify({"success": True, "data": contributions})
    except Exception as e:
        print(f"Error getting contributions: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/contributions/upload-rates", methods=["POST"])
def upload_contribution_rates():
    contribution_type = request.form.get("contribution_type") or request.args.get("contribution_type")
    """
    Upload PDF containing EPF/SOCSO/EIS contribution rate tables
    """
    try:
        # Validate contribution type
        if contribution_type not in ['epf', 'socso', 'eis']:
            return jsonify({"success": False, "message": "Invalid contribution type. Must be epf, socso, or eis"})
        
        # Validate file type
        if not file.filename.endswith('.pdf'):
            return jsonify({"success": False, "message": "Only PDF files are supported"})
        
        # Save the uploaded file temporarily
        import tempfile
        import shutil
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file.read())
            tmp_path = tmp_file.name
        
        try:
            # For EPF, use the dedicated parser
            if contribution_type == 'epf':
                try:
                    from core.epf_pdf_parser import upload_and_parse_epf_pdf
                    upload_and_parse_epf_pdf(tmp_path, supabase)
                    return jsonify({"success": True, "message": "EPF rates uploaded and parsed successfully"})
                except ImportError as e:
                    return jsonify({"success": False, "message": f"EPF parser not available: {str(e)}. Install pdfplumber."})
                except Exception as e:
                    return jsonify({"success": False, "message": f"Error parsing EPF PDF: {str(e)}"})
            
            # For SOCSO, use the dedicated parser
            elif contribution_type == 'socso':
                try:
                    from core.socso_pdf_parser import upload_and_parse_socso_pdf
                    result = upload_and_parse_socso_pdf(tmp_path, supabase)
                    return result
                except ImportError as e:
                    return jsonify({"success": False, "message": f"SOCSO parser not available: {str(e)}. Install pdfplumber."})
                except Exception as e:
                    return jsonify({"success": False, "message": f"Error parsing SOCSO PDF: {str(e)}"})
            
            # For EIS, use the dedicated parser
            elif contribution_type == 'eis':
                try:
                    from core.eis_pdf_parser import upload_and_parse_eis_pdf
                    result = upload_and_parse_eis_pdf(tmp_path, supabase)
                    return result
                except ImportError as e:
                    return jsonify({"success": False, "message": f"EIS parser not available: {str(e)}. Install pdfplumber."})
                except Exception as e:
                    return jsonify({"success": False, "message": f"Error parsing EIS PDF: {str(e)}"})
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            
    except Exception as e:
        print(f"Error uploading contribution rates: {str(e)}")
        return jsonify({"success": False, "message": f"Error uploading file: {str(e)}"})

# Variable Percentage API Endpoints
@app.route("/api/admin/variable-percentage")
def get_variable_percentage_rules():
    """
    Get all variable percentage configurations (same table as Python GUI)
    """
    try:
        response = supabase.table("variable_percentage_configs").select("*").order("created_at", desc=True).execute()
        return jsonify({"success": True, "data": response.data or []})
    except Exception as e:
        print(f"Error getting variable percentage configs: {str(e)}")
        return jsonify({"success": False, "message": str(e), "data": []})

@app.route("/api/admin/variable-percentage", methods=["POST"])
def create_variable_percentage_rule():
    """
    Create a new variable percentage configuration
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'type', 'percentage', 'apply_to', 'base_on', 'frequency', 'status']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"success": False, "message": f"Missing required field: <field>"})
        
        # Validate percentage
        try:
            percentage = float(data['percentage'])
            if percentage < 0 or percentage > 100:
                return jsonify({"success": False, "message": "Percentage must be between 0 and 100"})
        except ValueError:
            return jsonify({"success": False, "message": "Invalid percentage value"})
        
        # Add timestamp
        data['created_at'] = datetime.utcnow().isoformat()
        
        response = supabase.table("variable_percentage_configs").insert(data).execute()
        
        if response.data:
            return jsonify({"success": True, "message": "Variable percentage config created successfully", "data": response.data[0]})
        else:
            return jsonify({"success": False, "message": "Failed to create config"})
    except Exception as e:
        print(f"Error creating variable percentage config: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/variable-percentage/<rule_id>", methods=["PUT"])
def update_variable_percentage_rule(rule_id):
    """
    Update an existing variable percentage configuration
    """
    try:
        data = request.get_json()
        
        # Remove fields that shouldn't be updated
        data.pop('id', None)
        data.pop('created_at', None)
        
        # Add updated timestamp
        data['updated_at'] = datetime.utcnow().isoformat()
        
        response = supabase.table("variable_percentage_configs").update(data).eq("id", rule_id).execute()
        
        if response.data:
            return jsonify({"success": True, "message": "Config updated successfully", "data": response.data[0]})
        else:
            return jsonify({"success": False, "message": "Failed to update config"})
    except Exception as e:
        print(f"Error updating variable percentage config: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/variable-percentage/<rule_id>", methods=["DELETE"])
def delete_variable_percentage_rule(rule_id):
    """
    Delete a variable percentage configuration
    """
    try:
        response = supabase.table("variable_percentage_configs").delete().eq("id", rule_id).execute()
        
        if response.data:
            return jsonify({"success": True, "message": "Config deleted successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to delete config"})
    except Exception as e:
        print(f"Error deleting variable percentage config: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

# Skipped Payroll API Endpoint
@app.route("/api/admin/skipped-payroll")
def get_skipped_payroll():
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
                return jsonify({"success": True, "data": skipped_records})
        except Exception as e:
            print(f"Info: payroll_run_skips table query failed, trying payroll_runs: {str(e)}")
        
        # Fallback to querying payroll_runs with skip flag
        response = supabase.table("payroll_runs").select("*").eq("status", "skipped").order("created_at", desc=True).limit(100).execute()
        
        if not response.data:
            # If no skipped records found, return empty array
            return jsonify({"success": True, "data": []})
        
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
        
        return jsonify({"success": True, "data": skipped_records})
    except Exception as e:
        print(f"Error getting skipped payroll: {str(e)}")
        return jsonify({"success": False, "message": str(e), "data": []})

@app.route("/api/admin/skipped-payroll/<record_id>/include", methods=["POST"])
def include_skipped_in_next_payroll(record_id):
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
            return jsonify({"success": True, "message": "Record marked for inclusion in next payroll"})
        else:
            return jsonify({"success": False, "message": "Failed to update record"})
    except Exception as e:
        print(f"Error including skipped payroll: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/salary-history")
def get_salary_history():
    """
    Get salary change history for employees
    Uses salary_history table (same as Python GUI) with effective_date column
    """
    try:
        # Query salary history from salary_history table (same table as Python GUI uses)
        response = supabase.table("salary_history").select("*").order("effective_date", desc=True).limit(100).execute()
        
        if not response.data:
            return jsonify({"success": True, "data": []})
        
        salary_changes = response.data
        
        # Get unique employee IDs
        employee_ids = list(set([sc.get("employee_id") for sc in salary_changes if sc.get("employee_id")]))
        
        # Fetch employee data for all relevant employees
        employee_map = {}
        if employee_ids:
            employees_response = supabase.table("employees").select("id, email, full_name").in_("id", employee_ids).execute()
            if employees_response.data:
                employee_map = {emp["id"]: emp for emp in employees_response.data}
        
        # Enrich salary changes with employee names and emails
        for record in salary_changes:
            employee_id = record.get("employee_id")
            if employee_id and employee_id in employee_map:
                record["employee_name"] = employee_map[employee_id].get("full_name", "")
                record["employee_email"] = employee_map[employee_id].get("email", "")
            else:
                record["employee_name"] = ""
                record["employee_email"] = ""
        
        return jsonify({"success": True, "data": salary_changes})
    except Exception as e:
        print(f"Error getting salary history: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/salary-history", methods=["POST"])
def create_salary_change():
    """
    Record a salary change for an employee
    """
    try:
        data = request.get_json()
        
        # Look up employee_id from employee_email if not provided
        if not data.get('employee_id'):
            employee_email = data.get('employee_email')
            if not employee_email:
                return jsonify({"success": False, "message": "Missing required field: employee_email or employee_id"})
            
            # Fetch employee UUID from email
            emp_response = supabase.table("employees").select("id").eq("email", employee_email.lower()).execute()
            if not emp_response.data:
                return jsonify({"success": False, "message": f"Employee not found with email: <employee_email>"})
            
            data['employee_id'] = emp_response.data[0]['id']
        
        # Validate required fields - using fields that match Python GUI's salary_history table
        required_fields = ['employee_id', 'previous_salary', 'new_salary', 'effective_date']
        for field in required_fields:
            if field not in data or data[field] == '':
                return jsonify({"success": False, "message": f"Missing required field: <field>"})
        
        # Validate salary values
        try:
            prev_salary = float(data['previous_salary'])
            new_salary = float(data['new_salary'])
            if prev_salary < 0 or new_salary < 0:
                return jsonify({"success": False, "message": "Salary values must be positive"})
        except ValueError:
            return jsonify({"success": False, "message": "Invalid salary values"})
        
        # Calculate change amount and percentage
        change_amount = new_salary - prev_salary
        # Handle edge case: if previous salary is 0, use None to indicate undefined percentage
        if prev_salary > 0:
            change_percentage = (change_amount / prev_salary * 100)
        elif new_salary > 0:
            change_percentage = None  # Represents infinite/undefined percentage (new hire with no previous salary)
        else:
            change_percentage = 0  # Both zero, no change
        
        # Create salary history record matching Python GUI structure
        history_record = {
            "employee_id": data['employee_id'],
            "effective_date": data['effective_date'],
            "previous_salary": prev_salary,
            "new_salary": new_salary,
            "change_amount": change_amount,
            "change_percentage": change_percentage,
            "reason": data.get('reason', data.get('change_type', '')),
            "notes": data.get('notes', ''),
            "created_by": "admin",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Insert into salary_history table (same as Python GUI)
        response = supabase.table("salary_history").insert(history_record).execute()
        
        if response.data:
            return jsonify({"success": True, "message": "Salary change recorded successfully", "data": response.data[0]})
        else:
            return jsonify({"success": False, "message": "Failed to record salary change"})
    except Exception as e:
        print(f"Error creating salary change: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/employee-history")
def get_employee_history():
    """
    Get complete employment/re-employment history (previous jobs, companies, positions)
    """
    try:
        # Query employee_history without join to avoid foreign key relationship requirement
        response = supabase.table("employee_history").select("*").order("start_date", desc=True).limit(200).execute()
        
        if not response.data:
            return jsonify({"success": True, "data": []})
        
        records = response.data
        
        # Get unique employee emails and IDs
        employee_emails = list(set([rec.get("employee_email") for rec in records if rec.get("employee_email")]))
        employee_ids = list(set([rec.get("employee_id") for rec in records if rec.get("employee_id")]))
        
        # Fetch employee data for all relevant employees by email
        employee_map_by_email = {}
        if employee_emails:
            employees_response = supabase.table("employees").select("id, email, full_name").in_("email", employee_emails).execute()
            if employees_response.data:
                employee_map_by_email = {emp["email"]: emp for emp in employees_response.data}
        
        # Fetch employee data for all relevant employees by ID (for records that don't have email)
        employee_map_by_id = {}
        if employee_ids:
            employees_response = supabase.table("employees").select("id, email, full_name").in_("id", employee_ids).execute()
            if employees_response.data:
                employee_map_by_id = {emp["id"]: emp for emp in employees_response.data}
        
        # Enrich records with employee names
        for record in records:
            employee_email = record.get("employee_email")
            employee_id = record.get("employee_id")
            
            # First try to look up by email
            if employee_email and employee_email in employee_map_by_email:
                record["employee_name"] = employee_map_by_email[employee_email].get("full_name", "")
            # Then try to look up by ID
            elif employee_id and employee_id in employee_map_by_id:
                emp = employee_map_by_id[employee_id]
                record["employee_name"] = emp.get("full_name", "")
                # Also fill in the email if missing
                if not employee_email and emp.get("email"):
                    record["employee_email"] = emp.get("email")
            else:
                record["employee_name"] = ""
        
        return jsonify({"success": True, "data": records})
    except Exception as e:
        print(f"Error getting employee history: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/employee-history", methods=["POST"])
def create_employment_history():
    """
    Record employment / re-employment history (internal job changes and previous employment)
    """
    try:
        data = request.get_json()
        
        # Validate required fields - company is now optional for internal history
        required_fields = ['employee_email', 'job_title', 'start_date']
        for field in required_fields:
            if field not in data or data[field] == '':
                return jsonify({"success": False, "message": f"Missing required field: <field>"})
        
        # Get employee_id from email
        employee_response = supabase.table("employees").select("id").eq("email", data['employee_email']).execute()
        if not employee_response.data:
            return jsonify({"success": False, "message": "Employee not found"})
        
        employee_id = employee_response.data[0]['id']
        
        # Create employment history record with all fields from Python GUI
        # Note: employee_email is not stored in employee_history table, only employee_id
        history_record = {
            "employee_id": employee_id,
            "company": data.get('company', ''),  # Optional: empty for internal history
            "job_title": data['job_title'],
            "position": data.get('position', ''),
            "department": data.get('department', ''),
            "status": data.get('status', ''),
            "functional_group": data.get('functional_group', ''),
            "employment_type": data.get('employment_type', ''),
            "work_status": data.get('work_status', ''),
            "payroll_status": data.get('payroll_status', ''),
            "start_date": data['start_date'],
            "end_date": data.get('end_date') or None,  # None means currently employed (convert empty string to None)
            "notes": data.get('notes', ''),
        }
        
        # Use resilient insert function that handles schema mismatches
        response = insert_employee_history_record(history_record)
        
        if response and hasattr(response, 'data') and response.data:
            # Sync payroll_status and status to the employees table so run_payroll respects it
            payroll_status = data.get('payroll_status', '')
            employment_status = data.get('status', '')
            employee_update = {}
            
            if payroll_status:
                employee_update['payroll_status'] = payroll_status
            if employment_status:
                employee_update['status'] = employment_status
            
            if employee_update:
                try:
                    supabase.table("employees").update(employee_update).eq("id", employee_id).execute()
                except Exception as sync_err:
                    print(f"Warning: Failed to sync status to employees table: <sync_err>")
            
            return jsonify({"success": True, "message": "Employment history recorded successfully", "data": response.data[0]})
        else:
            return jsonify({"success": False, "message": "Failed to record employment history"})
    except Exception as e:
        print(f"Error creating employment history: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/employee-history/<record_id>", methods=["PUT"])
def update_employment_history(record_id):
    """
    Update an employee history record (admin only)
    """
    try:
        data = request.get_json()
        
        # Store employee_id before removing read-only fields
        employee_id = data.get('employee_id')
        
        # Remove read-only fields
        data.pop('id', None)
        data.pop('created_at', None)
        
        # Convert empty string end_date to None (for optional date field)
        if 'end_date' in data and data['end_date'] == '':
            data['end_date'] = None
        
        # Update the record using the service
        response = update_employee_history_record(record_id, data)
        
        if response and response.data:
            # Sync payroll_status and status to the employees table so run_payroll respects it
            payroll_status = data.get('payroll_status', '')
            employment_status = data.get('status', '')
            employee_update = {}
            
            if payroll_status:
                employee_update['payroll_status'] = payroll_status
            if employment_status:
                employee_update['status'] = employment_status
            
            if employee_update and employee_id:
                try:
                    supabase.table("employees").update(employee_update).eq("id", employee_id).execute()
                except Exception as sync_err:
                    print(f"Warning: Failed to sync status to employees table: <sync_err>")
            
            return jsonify({"success": True, "message": "Employee history record updated successfully", "data": response.data[0] if response.data else None})
        else:
            return jsonify({"success": False, "message": "Failed to update employee history record"})
    except Exception as e:
        print(f"Error updating employee history: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/employee-history/<record_id>", methods=["DELETE"])
def delete_employment_history(record_id):
    """
    Delete an employee history record (admin only)
    """
    try:
        response = delete_employee_history_record(record_id)
        
        if response:
            return jsonify({"success": True, "message": "Employee history record deleted successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to delete employee history record"})
    except Exception as e:
        print(f"Error deleting employee history: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/payroll-info/<employee_id>")
def get_payroll_info(employee_id):
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
        
        # Parse JSON fields
        allowances = {}
        if employee_data.get("allowances"):
            try:
                allowances = json.loads(employee_data["allowances"]) if isinstance(employee_data["allowances"], str) else employee_data["allowances"]
            except:
                pass
        
        benefits = {}
        if employee_data.get("benefits"):
            try:
                benefits = json.loads(employee_data["benefits"]) if isinstance(employee_data["benefits"], str) else employee_data["benefits"]
            except:
                pass
        
        children = []
        if employee_data.get("children_tax_relief"):
            try:
                children = json.loads(employee_data["children_tax_relief"]) if isinstance(employee_data["children_tax_relief"], str) else employee_data["children_tax_relief"]
            except:
                pass
        
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
            "tax_resident_status": employee_data.get("tax_resident_status", "Resident"),
            "is_individual_disabled": employee_data.get("is_individual_disabled", False),
            "is_spouse_disabled": employee_data.get("is_spouse_disabled", False),
            # Allowances
            "meal_allowance": allowances.get("meal", 0),
            "transport_allowance": allowances.get("transport", 0),
            "medical_allowance": allowances.get("medical", 0),
            "phone_allowance": allowances.get("phone", 0),
            "other_allowance": allowances.get("other", 0),
            # Benefits
            "sip_participation": benefits.get("sip_participation", "No"),
            "sip_type": benefits.get("sip_type", "None"),
            "sip_amount_rate": benefits.get("sip_amount_rate", 0),
            "additional_epf_enabled": benefits.get("additional_epf_enabled", "No"),
            "additional_epf_amount": benefits.get("additional_epf_amount", 0),
            "prs_participation": benefits.get("prs_participation", "No"),
            "prs_amount": benefits.get("prs_amount", 0),
            # Children
            "children": children,
            **deductions_data  # Include all deductions data
        }
        
        return jsonify({"success": True, "data": result})
    except Exception as e:
        print(f"Error getting payroll info: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

def _safe_update_employees(employee_id: str, payload: dict):
    """
    Resilient update for employees table: if PostgREST reports missing columns (PGRST204),
    strip them from payload and retry.
    """
    attempt = dict(payload)
    # Known optional fields that may not exist in all schemas
    fallback_fields = ['income_tax_number', 'epf_number', 'socso_number', 'tax_resident_status', 
                       'allowances', 'bank_name', 'bank_account', 'basic_salary',
                       'is_individual_disabled', 'is_spouse_disabled', 'benefits', 'children_tax_relief']
    # Allow extra iterations beyond fallback_fields count for fields not in fallback list
    max_retries = len(fallback_fields) + 2
    for _ in range(max_retries):
        if not attempt:
            return None  # Nothing to update
        try:
            return supabase.table("employees").update(attempt).eq("id", employee_id).execute()
        except Exception as e:
            msg = str(e)
            if 'PGRST204' not in msg:
                raise
            # Try to extract missing column name
            m = re.search(r"Could not find the '([^']+)' column of 'employees'", msg)
            missing = m.group(1) if m else None
            if missing and missing in attempt:
                attempt.pop(missing, None)
                continue
            # Fallback: remove one optional field at a time
            removed = False
            for k in list(attempt.keys()):
                if k in fallback_fields:
                    attempt.pop(k, None)
                    removed = True
                    break
            if removed:
                continue
            raise
    return None

@app.route("/api/admin/payroll-info", methods=["POST"])
def save_payroll_info():
    """
    Save payroll information (monthly deductions, tax info, etc.) for an employee
    """
    # Fields that should be saved to the employees table (not monthly deductions)
    EMPLOYEE_TABLE_FIELDS = ["tax_number", "epf_number", "socso_number", "bank_name", "bank_account", "basic_salary",
                             "tax_resident_status", "is_individual_disabled", "is_spouse_disabled",
                             "meal_allowance", "transport_allowance", "medical_allowance", "phone_allowance", "other_allowance",
                             "sip_participation", "sip_type", "sip_amount_rate",
                             "additional_epf_enabled", "additional_epf_amount",
                             "prs_participation", "prs_amount", "children"]
    # Fields that should not be saved to monthly deductions
    EXCLUDED_FROM_DEDUCTIONS = ["employee_id", "year", "month"] + EMPLOYEE_TABLE_FIELDS
    
    try:
        data = request.get_json()
        
        employee_id = data.get("employee_id")
        if not employee_id:
            return jsonify({"success": False, "message": "Missing employee_id"})
        
        year = data.get("year", datetime.now().year)
        month = data.get("month", datetime.now().month)
        
        # Update employee basic info (bank, tax numbers, allowances, etc.)
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
        if "tax_resident_status" in data:
            employee_updates["tax_resident_status"] = data["tax_resident_status"]
        if "is_individual_disabled" in data:
            employee_updates["is_individual_disabled"] = data["is_individual_disabled"]
        if "is_spouse_disabled" in data:
            employee_updates["is_spouse_disabled"] = data["is_spouse_disabled"]
        
        # Save allowances as JSON string
        allowances = {}
        if "meal_allowance" in data:
            allowances["meal"] = data["meal_allowance"]
        if "transport_allowance" in data:
            allowances["transport"] = data["transport_allowance"]
        if "medical_allowance" in data:
            allowances["medical"] = data["medical_allowance"]
        if "phone_allowance" in data:
            allowances["phone"] = data["phone_allowance"]
        if "other_allowance" in data:
            allowances["other"] = data["other_allowance"]
        if allowances:
            employee_updates["allowances"] = json.dumps(allowances)
        
        # Save benefits as JSON string
        benefits = {}
        if "sip_participation" in data:
            benefits["sip_participation"] = data["sip_participation"]
        if "sip_type" in data:
            benefits["sip_type"] = data["sip_type"]
        if "sip_amount_rate" in data:
            benefits["sip_amount_rate"] = data["sip_amount_rate"]
        if "additional_epf_enabled" in data:
            benefits["additional_epf_enabled"] = data["additional_epf_enabled"]
        if "additional_epf_amount" in data:
            benefits["additional_epf_amount"] = data["additional_epf_amount"]
        if "prs_participation" in data:
            benefits["prs_participation"] = data["prs_participation"]
        if "prs_amount" in data:
            benefits["prs_amount"] = data["prs_amount"]
        if benefits:
            employee_updates["benefits"] = json.dumps(benefits)
        
        # Save children data as JSON string
        if "children" in data:
            employee_updates["children_tax_relief"] = json.dumps(data["children"])
        
        if employee_updates:
            _safe_update_employees(employee_id, employee_updates)
        
        # Save monthly deductions data (excluding employee table fields)
        deductions_data = {k: v for k, v in data.items() if k not in EXCLUDED_FROM_DEDUCTIONS}
        
        success = upsert_monthly_deductions(employee_id, year, month, deductions_data)
        
        if success:
            return jsonify({"success": True, "message": "Payroll information saved successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to save payroll information"})
    except Exception as e:
        print(f"Error saving payroll info: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/tp1-reliefs/<employee_id>/<year>/<month>")
def get_tp1_reliefs(employee_id: str, year: int, month: int):
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
        
        return jsonify({"success": True, "data": tp1_data})
    except Exception as e:
        print(f"Error getting TP1 relief data: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/tp1-reliefs", methods=["POST"])
def save_tp1_reliefs():
    """
    Save TP1 tax relief data for an employee for a specific month
    """
    try:
        data = request.get_json()
        
        employee_id = data.get("employee_id")
        if not employee_id:
            return jsonify({"success": False, "message": "Missing employee_id"})
        
        year = data.get("year", datetime.now().year)
        month = data.get("month", datetime.now().month)
        relief_data = data.get("relief_data", {})
        
        # Save TP1 relief data to monthly deductions
        success = upsert_monthly_deductions(employee_id, year, month, relief_data)
        
        if success:
            return jsonify({"success": True, "message": "TP1 relief data saved successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to save TP1 relief data"})
    except Exception as e:
        print(f"Error saving TP1 relief data: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/salary-history/<record_id>", methods=["PUT"])
def update_salary_history(record_id):
    """
    Update a salary history record (admin only)
    Uses salary_history table (same as Python GUI)
    """
    try:
        data = request.get_json()
        
        # Remove read-only fields
        data.pop('id', None)
        data.pop('created_at', None)
        
        # Build update data with proper field names for salary_history table
        update_data = {}
        
        if 'previous_salary' in data:
            update_data['previous_salary'] = float(data['previous_salary'])
        if 'new_salary' in data:
            update_data['new_salary'] = float(data['new_salary'])
        if 'effective_date' in data:
            update_data['effective_date'] = data['effective_date']
        if 'reason' in data:
            update_data['reason'] = data['reason']
        if 'notes' in data:
            update_data['notes'] = data['notes']
        
        # Recalculate change amount and percentage if salary values are present
        if 'previous_salary' in update_data and 'new_salary' in update_data:
            prev_salary = update_data['previous_salary']
            new_salary = update_data['new_salary']
            
            update_data['change_amount'] = new_salary - prev_salary
            # Handle edge case: if previous salary is 0, use None to indicate undefined percentage
            if prev_salary > 0:
                update_data['change_percentage'] = ((new_salary - prev_salary) / prev_salary * 100)
            elif new_salary > 0:
                update_data['change_percentage'] = None  # Represents infinite/undefined percentage
            else:
                update_data['change_percentage'] = 0  # Both zero, no change
        
        # Update the record in salary_history table
        response = supabase.table("salary_history").update(update_data).eq("id", record_id).execute()
        
        if response and response.data:
            return jsonify({"success": True, "message": "Salary history record updated successfully", "data": response.data[0] if response.data else None})
        else:
            return jsonify({"success": False, "message": "Failed to update salary history record"})
    except Exception as e:
        print(f"Error updating salary history: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/salary-history/<record_id>", methods=["DELETE"])
def delete_salary_history(record_id):
    """
    Delete a salary history record (admin only)
    Uses salary_history table (same as Python GUI)
    """
    try:
        response = supabase.table("salary_history").delete().eq("id", record_id).execute()
        
        if response:
            return jsonify({"success": True, "message": "Salary history record deleted successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to delete salary history record"})
    except Exception as e:
        print(f"Error deleting salary history: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

# ====================
# LHDN Tax Configuration Endpoints
# ====================

@app.route("/api/admin/lhdn/tax-rates")
def get_tax_rates():
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
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/lhdn/tax-rates", methods=["POST"])
def create_tax_rate():
    data = request.get_json()
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
            return jsonify({"success": True, "message": "Tax rate saved successfully", "data": response.data[0]})
        else:
            return jsonify({"success": False, "message": "Failed to save tax rate"})
    except Exception as e:
        print(f"Error saving tax rate: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/lhdn/tax-rates/<rate_id>", methods=["DELETE"])
def delete_tax_rate(rate_id: int):
    """Delete a tax rate bracket"""
    try:
        response = supabase.table("lhdn_tax_rates").delete().eq("id", rate_id).execute()
        
        if response.data:
            return jsonify({"success": True, "message": "Tax rate deleted successfully"})
        else:
            return jsonify({"success": False, "message": "Tax rate not found"})
    except Exception as e:
        print(f"Error deleting tax rate: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/lhdn/relief-max")
def get_relief_maximums():
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
            return jsonify({"success": True, "data": relief_array})
        else:
            return jsonify({"success": True, "data": []})
    except Exception as e:
        print(f"Error fetching relief maximums: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/lhdn/relief-max", methods=["POST"])
def update_relief_maximum():
    data = request.get_json()
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
            return jsonify({"success": True, "message": "Relief maximum updated successfully", "data": response.data[0]})
        else:
            return jsonify({"success": False, "message": "Failed to update relief maximum"})
    except Exception as e:
        print(f"Error updating relief maximum: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/lhdn/relief-item-overrides")
def get_relief_item_overrides():
    """Get relief item overrides (cap, pcb_only, cycle_years) - matches Python GUI"""
    try:
        response = supabase.table("relief_item_overrides").select("*").execute()
        
        # Return data in format matching database structure
        overrides = []
        if response.data:
            for item in response.data:
                overrides.append({
                    "item_key": item.get("item_key"),
                    "cap": item.get("cap"),
                    "pcb_only": item.get("pcb_only"),
                    "cycle_years": item.get("cycle_years"),
                    "updated_at": item.get("updated_at"),
                    "created_at": item.get("created_at")
                })
        
        return jsonify({"success": True, "data": overrides})
    except Exception as e:
        print(f"Error fetching relief item overrides: {str(e)}")
        return jsonify({"success": True, "data": []})

@app.route("/api/admin/lhdn/relief-group-overrides")
def get_relief_group_overrides():
    """Get relief group cap overrides - matches Python GUI"""
    try:
        response = supabase.table("relief_group_overrides").select("*").execute()
        
        overrides = []
        if response.data:
            for item in response.data:
                overrides.append({
                    "group_id": item.get("group_id"),
                    "cap": item.get("cap"),
                    "updated_at": item.get("updated_at"),
                    "created_at": item.get("created_at")
                })
        
        return jsonify({"success": True, "data": overrides})
    except Exception as e:
        print(f"Error fetching relief group overrides: {str(e)}")
        return jsonify({"success": True, "data": []})

@app.route("/api/admin/lhdn/relief-item-overrides", methods=["POST"])
def upsert_relief_item_override():
    data = request.get_json()
    """Create or update relief item override (upsert) - matches Python GUI"""
    try:
        item_key = data.get("item_key")
        if not item_key:
            return jsonify({"success": False, "message": "item_key is required"})
        
        override = {"item_key": item_key}
        
        # Only include fields that are provided (not None)
        if data.get("cap") is not None:
            override["cap"] = float(data["cap"])
        if data.get("pcb_only") is not None:
            override["pcb_only"] = bool(data["pcb_only"])
        if data.get("cycle_years") is not None:
            override["cycle_years"] = int(data["cycle_years"])
        
        # Upsert (insert or update if exists)
        response = supabase.table("relief_item_overrides").upsert(override).execute()
        
        if response.data:
            return jsonify({"success": True, "message": "Relief item override saved", "data": response.data[0]})
        else:
            return jsonify({"success": False, "message": "Failed to save relief item override"})
    except Exception as e:
        print(f"Error saving relief item override: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/lhdn/relief-group-overrides", methods=["POST"])
def upsert_relief_group_override():
    data = request.get_json()
    """Create or update relief group override (upsert) - matches Python GUI"""
    try:
        group_id = data.get("group_id")
        cap = data.get("cap")
        
        if not group_id:
            return jsonify({"success": False, "message": "group_id is required"})
        if cap is None:
            return jsonify({"success": False, "message": "cap is required"})
        
        override = {
            "group_id": group_id,
            "cap": float(cap)
        }
        
        # Upsert (insert or update if exists)
        response = supabase.table("relief_group_overrides").upsert(override).execute()
        
        if response.data:
            return jsonify({"success": True, "message": "Relief group override saved", "data": response.data[0]})
        else:
            return jsonify({"success": False, "message": "Failed to save relief group override"})
    except Exception as e:
        print(f"Error saving relief group override: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/lhdn/relief-item-overrides/<item_key>", methods=["DELETE"])
def delete_relief_item_override(item_key):
    """Delete relief item override - matches Python GUI"""
    try:
        response = supabase.table("relief_item_overrides").delete().eq("item_key", item_key).execute()
        
        if response.data:
            return jsonify({"success": True, "message": "Relief item override deleted"})
        else:
            return jsonify({"success": False, "message": "Relief item override not found"})
    except Exception as e:
        print(f"Error deleting relief item override: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/lhdn/relief-group-overrides/<group_id>", methods=["DELETE"])
def delete_relief_group_override(group_id):
    """Delete relief group override - matches Python GUI"""
    try:
        response = supabase.table("relief_group_overrides").delete().eq("group_id", group_id).execute()
        
        if response.data:
            return jsonify({"success": True, "message": "Relief group override deleted"})
        else:
            return jsonify({"success": False, "message": "Relief group override not found"})
    except Exception as e:
        print(f"Error deleting relief group override: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

# ====================
# Leave Configuration Endpoints
# ====================

@app.route("/api/admin/leave-types")
def get_leave_types():
    """Get all leave types"""
    try:
        response = supabase.table("leave_types").select("*").execute()
        
        if response.data:
            return jsonify({"success": True, "data": response.data})
        else:
            return jsonify({"success": True, "data": []})
    except Exception as e:
        print(f"Error fetching leave types: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/leave-types", methods=["POST"])
def create_leave_type():
    data = request.get_json()
    """Create a new leave type"""
    try:
        leave_type = {
            "name": data["name"],
            "code": data["code"],
            "color": data.get("color", "#3498db"),
            "description": data.get("description", ""),
            "requires_approval": data.get("requires_approval", True),
            "is_paid": data.get("is_paid", True),
            "is_active": data.get("is_active", True),
            "deduct_from": data.get("deduct_from", "none"),
            "requires_document": data.get("requires_document", False),
            "default_duration": data.get("default_duration", 1.0),
            "max_duration": data.get("max_duration", 14.0),
            "created_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table("leave_types").insert(leave_type).execute()
        
        if response.data:
            return jsonify({"success": True, "message": "Leave type created successfully", "data": response.data[0]})
        else:
            return jsonify({"success": False, "message": "Failed to create leave type"})
    except Exception as e:
        print(f"Error creating leave type: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/leave-types/<type_id>", methods=["PUT"])
def update_leave_type(type_id: str, data: Dict[str, Any]):
    """Update a leave type by ID (numeric) or code (string)"""
    try:
        leave_type = {
            "name": data.get("name"),
            "code": data.get("code"),
            "color": data.get("color"),
            "description": data.get("description"),
            "requires_approval": data.get("requires_approval"),
            "is_paid": data.get("is_paid"),
            "is_active": data.get("is_active"),
            "deduct_from": data.get("deduct_from"),
            "requires_document": data.get("requires_document"),
            "default_duration": data.get("default_duration"),
            "max_duration": data.get("max_duration"),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Remove None values
        leave_type = {k: v for k, v in leave_type.items() if v is not None}
        
        # Determine lookup method: if type_id is numeric, use ID; otherwise use code
        if type_id.isdigit():
            # Numeric ID - update by ID only
            response = supabase.table("leave_types").update(leave_type).eq("id", int(type_id)).execute()
        else:
            # String code - update by code only
            response = supabase.table("leave_types").update(leave_type).eq("code", type_id).execute()
        
        if response and response.data:
            return jsonify({"success": True, "message": "Leave type updated successfully", "data": response.data[0]})
        else:
            return jsonify({"success": False, "message": "Leave type not found"})
    except Exception as e:
        print(f"Error updating leave type: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/leave-types/<type_id>", methods=["DELETE"])
def delete_leave_type(type_id):
    """Delete a leave type by ID (numeric) or code (string)"""
    try:
        # Determine lookup method: if type_id is numeric, use ID; otherwise use code
        if type_id.isdigit():
            # Numeric ID - delete by ID only
            response = supabase.table("leave_types").delete().eq("id", int(type_id)).execute()
        else:
            # String code - delete by code only
            response = supabase.table("leave_types").delete().eq("code", type_id).execute()
        
        if response and response.data:
            return jsonify({"success": True, "message": "Leave type deleted successfully"})
        else:
            return jsonify({"success": False, "message": "Leave type not found"})
    except Exception as e:
        print(f"Error deleting leave type: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

# Default multiplier for max accumulation calculation (3x the entitlement days)
DEFAULT_MAX_ACCUMULATION_MULTIPLIER = 3

@app.route("/api/admin/leave-entitlements")
def get_leave_entitlements():
    """Get leave entitlements/caps - returns per leave-type per tier format"""
    try:
        # Get tiers and caps from the actual database structure
        tiers_response = supabase.table("leave_caps_tiers").select("*").execute()
        caps_response = supabase.table("leave_caps").select("*").execute()
        
        # Get leave types for name lookup
        leave_types_response = supabase.table("leave_types").select("*").execute()
        leave_type_names = {}
        if leave_types_response.data:
            for lt in leave_types_response.data:
                leave_type_names[lt.get("code", "").lower()] = lt.get("name", lt.get("code", ""))
        
        # Create tier lookup for labels
        tier_labels = {}
        tier_id_to_label = {}
        if tiers_response.data:
            for tier in tiers_response.data:
                tier_id = tier.get("id")
                tier_labels[tier_id] = tier.get("label", f"{tier.get('min_years', 0)}-{tier.get('max_years', 99)} years")
                tier_id_to_label[tier_id] = tier_labels[tier_id]
        
        # Transform to expected format: one entry per leave_type per tier
        entitlements = []
        entry_id = 1
        
        if caps_response.data:
            for cap in caps_response.data:
                tier_id = cap.get("tier_id")
                leave_type_code = cap.get("leave_type", "").lower()
                cap_value = cap.get("cap", 0) or 0
                
                # Get leave type name from database or capitalize code
                leave_type_name = leave_type_names.get(leave_type_code, leave_type_code.capitalize() + " Leave")
                
                # Get tier label
                tier_label = tier_id_to_label.get(tier_id, tier_id)
                
                entitlements.append({
                    "id": entry_id,
                    "leave_type_code": leave_type_code,
                    "leave_type_name": leave_type_name,
                    "employee_tier": tier_id,
                    "tier_label": tier_label,
                    "days_entitlement": cap_value,
                    "max_accumulation": cap.get("max_accumulation") or cap_value * DEFAULT_MAX_ACCUMULATION_MULTIPLIER
                })
                entry_id += 1
        
        return jsonify({"success": True, "data": entitlements})
    except Exception as e:
        print(f"Error fetching leave entitlements: {str(e)}")
        return jsonify({"success": False, "message": str(e), "data": []})

@app.route("/api/admin/leave-entitlements", methods=["POST"])
def create_leave_entitlement():
    data = request.get_json()
    """Create a leave entitlement rule in leave_caps table"""
    try:
        leave_type_code = data.get("leave_type_code")
        tier_id = data.get("employee_tier")
        days_entitlement = data.get("days_entitlement", 0)
        
        if not leave_type_code or not tier_id:
            return jsonify({"success": False, "message": "leave_type_code and employee_tier are required"})
        
        # Check if this combination already exists
        existing = supabase.table("leave_caps").select("*").eq("tier_id", tier_id).eq("leave_type", leave_type_code).execute()
        
        if existing.data and len(existing.data) > 0:
            # Update existing record
            response = supabase.table("leave_caps").update({
                "cap": days_entitlement
            }).eq("tier_id", tier_id).eq("leave_type", leave_type_code).execute()
            
            if response.data:
                return jsonify({"success": True, "message": "Leave entitlement updated successfully", "data": response.data[0]})
        else:
            # Insert new record
            response = supabase.table("leave_caps").insert({
                "tier_id": tier_id,
                "leave_type": leave_type_code,
                "cap": days_entitlement
            }).execute()
            
            if response.data:
                return jsonify({"success": True, "message": "Leave entitlement created successfully", "data": response.data[0]})
        
        return jsonify({"success": False, "message": "Failed to create/update leave entitlement"})
    except Exception as e:
        print(f"Error creating leave entitlement: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/leave-entitlements/<entitlement_id>", methods=["PUT"])
def update_leave_entitlement(entitlement_id: int, data: Dict[str, Any]):
    """Update a leave entitlement rule in leave_caps table"""
    try:
        leave_type_code = data.get("leave_type_code")
        tier_id = data.get("employee_tier")
        days_entitlement = data.get("days_entitlement")
        
        if leave_type_code and tier_id:
            # Update by tier_id and leave_type combination
            response = supabase.table("leave_caps").update({
                "cap": days_entitlement
            }).eq("tier_id", tier_id).eq("leave_type", leave_type_code).execute()
            
            if response.data:
                return jsonify({"success": True, "message": "Leave entitlement updated successfully", "data": response.data[0]})
            else:
                return jsonify({"success": False, "message": "Leave entitlement not found"})
        else:
            return jsonify({"success": False, "message": "leave_type_code and employee_tier are required for update"})
    except Exception as e:
        print(f"Error updating leave entitlement: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/leave-entitlements/<entitlement_id>", methods=["DELETE"])
def delete_leave_entitlement(entitlement_id):
    """Delete a leave entitlement rule from leave_caps table"""
    try:
        leave_type_code = request.args.get("leave_type_code")
        employee_tier = request.args.get("employee_tier")
        if leave_type_code and employee_tier:
            # Delete by tier_id and leave_type
            response = supabase.table("leave_caps").delete().eq("tier_id", employee_tier).eq("leave_type", leave_type_code).execute()
        else:
            # Fallback: try to delete by record id if available
            response = supabase.table("leave_caps").delete().eq("id", entitlement_id).execute()
        
        if response.data:
            return jsonify({"success": True, "message": "Leave entitlement deleted successfully"})
        else:
            return jsonify({"success": False, "message": "Leave entitlement not found"})
    except Exception as e:
        print(f"Error deleting leave entitlement: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/leave-tiers")
def get_leave_tiers():
    """Get leave entitlement tiers (years of service)"""
    try:
        response = supabase.table("leave_caps_tiers").select("*").order("min_years", desc=False).execute()
        
        if response.data:
            tiers = []
            for tier in response.data:
                tiers.append({
                    "id": tier.get("id"),
                    "label": tier.get("label"),
                    "min_years": tier.get("min_years", 0),
                    "max_years": tier.get("max_years", 99)
                })
            return jsonify({"success": True, "data": tiers})
        else:
            # Return default tiers if none exist
            return jsonify({"success": True, "data": [
                {"id": "lt2", "label": "< 2 years", "min_years": 0, "max_years": 1.99},
                {"id": "2to5", "label": "2 - 5 years", "min_years": 2, "max_years": 5},
                {"id": "gt5", "label": "> 5 years", "min_years": 5.01, "max_years": 100}
            ]})
    except Exception as e:
        print(f"Error fetching leave tiers: {str(e)}")
        return jsonify({"success": False, "message": str(e), "data": []})

# ====================
# Leave Policies Endpoints
# ====================

@app.route("/api/admin/leave-policies")
def get_leave_policies():
    """Get company leave policies"""
    try:
        from services.supabase_service import get_company_leave_policies
        policies = get_company_leave_policies()
        return jsonify({"success": True, "data": policies})
    except Exception as e:
        print(f"Error getting leave policies: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/leave-policies", methods=["POST"])
def update_leave_policies():
    """Update company leave policies"""
    try:
        from services.supabase_service import update_company_leave_policy
        data = request.get_json()
        
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
            return jsonify({"success": True, "message": "Leave policies updated successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to update some policies"})
    except Exception as e:
        print(f"Error updating leave policies: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

# ====================
# Calendar & Holidays Endpoints
# ====================

@app.route("/api/holidays")
def get_holidays():
    """Get public holidays"""
    try:
        # Get current year
        current_year = datetime.now().year
        
        response = supabase.table("calendar_holidays").select("*").gte("date", f"<current_year>-01-01").lte("date", f"{current_year+1}-12-31").order("date").execute()
        
        if response.data:
            return jsonify({"success": True, "data": response.data})
        else:
            return jsonify({"success": True, "data": []})
    except Exception as e:
        print(f"Error fetching holidays: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/leave-calendar/<employee_id>")
def get_leave_calendar(employee_id):
    """Get leave calendar for an employee"""
    try:
        if not year:
            year = datetime.now().year
        
        # Fetch leave requests for the year
        response = supabase.table("leave_requests").select("*").eq("employee_id", employee_id).gte("start_date", f"<year>-01-01").lte("end_date", f"<year>-12-31").execute()
        
        # Fetch holidays
        holidays_response = supabase.table("calendar_holidays").select("*").gte("date", f"<year>-01-01").lte("date", f"<year>-12-31").execute()
        
        return {
            "success": True,
            "data": {
                "leave_requests": response.data if response.data else [],
                "holidays": holidays_response.data if holidays_response.data else []
            }
        }
    except Exception as e:
        print(f"Error fetching leave calendar: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/holidays", methods=["POST"])
def create_holiday():
    holiday = request.get_json()
    """Create a new holiday"""
    try:
        response = supabase.table("calendar_holidays").insert(holiday).execute()
        
        if response.data:
            return jsonify({"success": True, "data": response.data[0], "message": "Holiday created successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to create holiday"})
    except Exception as e:
        print(f"Error creating holiday: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/holidays/<holiday_id>", methods=["PUT"])
def update_holiday(holiday_id: int, holiday: dict):
    """Update an existing holiday"""
    try:
        response = supabase.table("calendar_holidays").update(holiday).eq("id", holiday_id).execute()
        
        if response.data:
            return jsonify({"success": True, "data": response.data[0], "message": "Holiday updated successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to update holiday"})
    except Exception as e:
        print(f"Error updating holiday: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/holidays/<holiday_id>", methods=["DELETE"])
def delete_holiday(holiday_id: int):
    """Delete a holiday"""
    try:
        response = supabase.table("calendar_holidays").delete().eq("id", holiday_id).execute()
        
        if response.data:
            return jsonify({"success": True, "message": "Holiday deleted successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to delete holiday"})
    except Exception as e:
        print(f"Error deleting holiday: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/holidays/import-malaysia", methods=["POST"])
def import_malaysia_holidays():
    year = request.args.get("year", type=int)
    state = request.args.get("state")
    replace = request.args.get("replace", "false").lower() == "true"
    """
    Auto-import Malaysia public holidays for a specific year
    
    Args:
        year: Year to import holidays for (1900-2100)
        state: Optional state filter (e.g., 'Selangor', 'Johor'). None for national holidays.
        replace: If True, delete existing holidays for this year/state before importing
    """
    try:
        # Validate year parameter
        if year < 1900 or year > 2100:
            return {
                "success": False,
                "message": "Year must be between 1900 and 2100"
            }
        
        from core.holidays_service import get_holidays_for_year
        from services.supabase_service import insert_calendar_holiday, find_calendar_holidays_for_year, delete_calendar_holidays_for_year
        
        # Normalize state parameter
        normalized_state = None if (not state or state == 'All Malaysia') else state
        
        # If replace=True, delete existing holidays for this year/state
        deleted_count = 0
        if replace:
            deleted_count = delete_calendar_holidays_for_year(year, state=normalized_state)
        
        # Get holidays from python-holidays library
        holidays_set, holiday_details = get_holidays_for_year(
            year, 
            state=normalized_state,
            include_national=True,
            include_observances=True
        )
        
        # Fetch existing holidays for this year upfront (avoid N+1 query pattern)
        # Note: If replace=True, this will be empty since we just deleted them
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
                    errors.append(f"Failed to import <name> on <date_str>")
            except Exception as e:
                errors.append(f"Failed to import <name> on <date_str>: {str(e)}")
        
        # Build message based on whether replacement occurred
        if replace and deleted_count > 0:
            message = f"Replaced <deleted_count> existing holidays. Imported <imported_count> new holidays, skipped <skipped_count> duplicates"
        elif replace and deleted_count == 0:
            message = f"No existing holidays to replace. Imported <imported_count> holidays, skipped <skipped_count> duplicates"
        else:
            message = f"Imported <imported_count> holidays, skipped <skipped_count> duplicates"
        
        return {
            "success": True,
            "message": message,
            "data": {
                "deleted": deleted_count if replace else 0,
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
        return jsonify({"success": False, "message": str(e)})

# Helper function to generate CSV from data
def generate_csv(headers: List[str], rows: List[List[Any]]):
    """Generate a CSV file from headers and rows"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = f"attachment; filename=export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return response

# CSV Export Endpoints
@app.route("/api/admin/skipped-payroll/export/csv")
def export_skipped_payroll_csv():
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
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/admin/contributions/export/csv")
def export_contributions_csv():
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
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/admin/salary-history/export/csv")
def export_salary_history_csv():
    """Export salary history to CSV"""
    try:
        # Get salary history data from salary_history table (same as Python GUI)
        response = supabase.table("salary_history").select("*").order("effective_date", desc=True).limit(1000).execute()
        
        if not response.data:
            headers = ["Effective Date", "Employee ID", "Employee Name", "Previous Salary", "New Salary", "Change Amount", "Change Percentage", "Reason", "Notes"]
            return generate_csv(headers, [])
        
        salary_changes = response.data
        
        # Get unique employee IDs for name lookup
        employee_ids = list(set([sc.get("employee_id") for sc in salary_changes if sc.get("employee_id")]))
        employee_map = {}
        if employee_ids:
            employees_response = supabase.table("employees").select("id, full_name").in_("id", employee_ids).execute()
            if employees_response.data:
                employee_map = {emp["id"]: emp.get("full_name", "") for emp in employees_response.data}
        
        headers = ["Effective Date", "Employee ID", "Employee Name", "Previous Salary", "New Salary", "Change Amount", "Change Percentage", "Reason", "Notes"]
        rows = []
        for record in salary_changes:
            prev_salary = float(record.get('previous_salary', 0) or 0)
            new_salary = float(record.get('new_salary', 0) or 0)
            change_amount = float(record.get('change_amount', 0) or 0)
            change_percent = float(record.get('change_percentage', 0) or 0)
            employee_id = record.get('employee_id', '')
            employee_name = employee_map.get(employee_id, '')
            
            rows.append([
                record.get('effective_date', ''),
                employee_id,
                employee_name,
                f"{prev_salary:.2f}",
                f"{new_salary:.2f}",
                f"{change_amount:.2f}",
                f"{change_percent:.2f}%",
                record.get('reason', ''),
                record.get('notes', '')
            ])
        
        return generate_csv(headers, rows)
    except Exception as e:
        print(f"Error exporting salary history: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/admin/engagements/export/csv")
def export_engagements_csv():
    """Export engagements to CSV"""
    try:
        all_data = []
        
        # Fetch from all engagement tables
        try:
            training_response = supabase.table("training_course_records").select("*").order("created_at", desc=True).limit(1000).execute()
            if training_response.data:
                for record in training_response.data:
                    record['type'] = 'training'
                    all_data.append(record)
        except:
            pass
        
        try:
            trips_response = supabase.table("overseas_work_trip_records").select("*").order("created_at", desc=True).limit(1000).execute()
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
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/admin/employee-history/export/csv")
def export_employee_history_csv():
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
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/admin/attendance/export/csv")
def export_attendance_csv():
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
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/admin/leave-requests/export/csv")
def export_leave_requests_csv():
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
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/admin/payroll/export/csv")
def export_payroll_runs_csv():
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
        return jsonify({"success": False, "message": str(e)}), 500

# ============================================================================
# File Upload Endpoints
# ============================================================================

@app.route("/api/employees/<employee_id>/profile-picture", methods=["POST"])
def upload_employee_profile_picture(employee_id: str):
    """Upload profile picture for an employee"""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            return jsonify({"success": False, "message": "Only image files are allowed"})
        
        # Validate file size (5MB limit)
        file = request.files.get("file")
        if not file:
            return jsonify({"success": False, "message": "No file provided"})
        contents = file.read()
        if len(contents) > 5 * 1024 * 1024:
            return jsonify({"success": False, "message": "File size must be less than 5MB"})
        
        # Save temporarily
        import tempfile
        temp_dir = tempfile.gettempdir()
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"profile_<employee_id>_{file.filename}")
        
        with open(temp_path, "wb") as f:
            f.write(contents)
        
        # Upload to Supabase storage
        photo_url = upload_profile_picture(temp_path, employee_id)
        
        # Clean up temp file
        try:
            os.remove(temp_path)
        except (OSError, FileNotFoundError) as e:
            print(f"Warning: Could not remove temp file: <e>")
        
        if photo_url:
            return {
                "success": True, 
                "message": "Profile picture uploaded successfully",
                "photo_url": photo_url
            }
        else:
            return jsonify({"success": False, "message": "Failed to upload profile picture"})
    
    except Exception as e:
        print(f"Error uploading profile picture: {str(e)}")
        return jsonify({"success": False, "message": f"Error uploading file: {str(e)}"})

@app.route("/api/employees/<employee_id>/resume", methods=["POST"])
def upload_employee_resume(employee_id: str):
    """Upload resume/CV for an employee"""
    try:
        # Validate file type
        allowed_types = ['application/pdf', 'application/msword', 
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        if not file.content_type or file.content_type not in allowed_types:
            return jsonify({"success": False, "message": "Only PDF, DOC, and DOCX files are allowed"})
        
        # Validate file size (10MB limit)
        file = request.files.get("file")
        if not file:
            return jsonify({"success": False, "message": "No file provided"})
        contents = file.read()
        if len(contents) > 10 * 1024 * 1024:
            return jsonify({"success": False, "message": "File size must be less than 10MB"})
        
        # Save temporarily
        import tempfile
        temp_dir = tempfile.gettempdir()
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"resume_<employee_id>_{file.filename}")
        
        with open(temp_path, "wb") as f:
            f.write(contents)
        
        # Upload to Supabase storage
        resume_url = upload_resume(temp_path, employee_id)
        
        # Clean up temp file
        try:
            os.remove(temp_path)
        except (OSError, FileNotFoundError) as e:
            print(f"Warning: Could not remove temp file: <e>")
        
        if resume_url:
            return {
                "success": True, 
                "message": "Resume uploaded successfully",
                "resume_url": resume_url
            }
        else:
            return jsonify({"success": False, "message": "Failed to upload resume"})
    
    except Exception as e:
        print(f"Error uploading resume: {str(e)}")
        return jsonify({"success": False, "message": f"Error uploading file: {str(e)}"})

# ============================================================================
# Payroll Settings Endpoints
# ============================================================================

@app.route("/api/admin/payroll/settings")
def get_payroll_settings_api():
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

@app.route("/api/admin/payroll/settings", methods=["POST"])
def update_payroll_settings_api():
    settings = request.get_json()
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
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/variable-config/<config_name>")
def get_variable_config_api(config_name):
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
                "message": f"Configuration '<config_name>' not found"
            }
    except Exception as e:
        print(f"Error getting variable config: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }

# ============================================================================
# TP1 Relief Claims Endpoints
# ============================================================================

@app.route("/api/admin/tp1-reliefs/<employee_id>")
def get_tp1_relief_claims(employee_id):
    """
    Get TP1 relief claims for an employee from the tp1_monthly_details table.
    
    Args:
        employee_id: Employee UUID
        year: Optional year filter (defaults to current year)
        month: Optional month filter (1-12). If not provided, returns all months for the year.
    
    Returns:
        List of TP1 relief claim records with details JSON and aggregates
    """
    try:
        year = request.args.get("year", type=int)
        month = request.args.get("month", type=int)
        
        if year is None:
            year = datetime.now().year
        
        # Build query
        query = supabase.table("tp1_monthly_details").select("*").eq("employee_id", employee_id).eq("year", year)
        
        if month is not None:
            query = query.eq("month", month)
        
        query = query.order("month", desc=False)
        response = query.execute()
        
        if response.data:
            # Transform data for frontend consumption
            reliefs = []
            for record in response.data:
                reliefs.append({
                    "id": record.get("id"),
                    "employee_id": record.get("employee_id"),
                    "year": record.get("year"),
                    "month": record.get("month"),
                    "details": record.get("details", {}),
                    "other_reliefs_monthly": float(record.get("other_reliefs_monthly", 0) or 0),
                    "socso_eis_lp1_monthly": float(record.get("socso_eis_lp1_monthly", 0) or 0),
                    "zakat_monthly": float(record.get("zakat_monthly", 0) or 0),
                    "created_at": record.get("created_at"),
                    "updated_at": record.get("updated_at")
                })
            return jsonify({"success": True, "data": reliefs})
        else:
            return jsonify({"success": True, "data": []})
    except Exception as e:
        print(f"Error fetching TP1 reliefs: {str(e)}")
        return jsonify({"success": False, "message": str(e), "data": []})

@app.route("/api/admin/tp1-reliefs", methods=["POST"])
def create_tp1_relief():
    relief_data = request.get_json()
    """
    Create or update TP1 relief claims for an employee.
    Uses the upsert_tp1_monthly_details function from supabase_service.
    
    Args:
        relief_data: Dictionary containing:
            - employee_id: Employee UUID (required)
            - year: Year (required, e.g., 2024)
            - month: Month (required, 1-12)
            - details: Dictionary of relief claim details (required)
            - other_reliefs_monthly: Optional aggregate for other reliefs
            - socso_eis_lp1_monthly: Optional aggregate for SOCSO/EIS LP1
            - zakat_monthly: Optional aggregate for zakat
    
    Returns:
        Success status and message
    """
    try:
        from services.supabase_service import upsert_tp1_monthly_details
        
        employee_id = relief_data.get("employee_id")
        year = relief_data.get("year")
        month = relief_data.get("month")
        details = relief_data.get("details", {})
        
        # Validate required fields
        if not employee_id:
            return jsonify({"success": False, "message": "employee_id is required"})
        if year is None:
            return jsonify({"success": False, "message": "year is required"})
        if month is None:
            return jsonify({"success": False, "message": "month is required"})
        
        # Validate month range
        if not (1 <= int(month) <= 12):
            return jsonify({"success": False, "message": "month must be between 1 and 12"})
        
        # Build aggregates dictionary
        aggregates = {
            "other_reliefs_monthly": relief_data.get("other_reliefs_monthly", 0),
            "socso_eis_lp1_monthly": relief_data.get("socso_eis_lp1_monthly", 0),
            "zakat_monthly": relief_data.get("zakat_monthly", 0)
        }
        
        # Call the service function to upsert
        success = upsert_tp1_monthly_details(
            employee_uuid=employee_id,
            year=int(year),
            month=int(month),
            details=details,
            aggregates=aggregates
        )
        
        if success:
            return jsonify({"success": True, "message": "TP1 relief claims saved successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to save TP1 relief claims. The tp1_monthly_details table may not exist."})
    except Exception as e:
        print(f"Error saving TP1 relief: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route("/api/admin/tp1-reliefs/<relief_id>", methods=["DELETE"])
def delete_tp1_relief(relief_id):
    """
    Delete a TP1 relief claim record by ID.
    
    Args:
        relief_id: UUID of the TP1 relief record to delete
    
    Returns:
        Success status and message
    """
    try:
        response = supabase.table("tp1_monthly_details").delete().eq("id", relief_id).execute()
        
        if response.data:
            return jsonify({"success": True, "message": "TP1 relief claim deleted successfully"})
        else:
            return jsonify({"success": False, "message": "TP1 relief claim not found"})
    except Exception as e:
        print(f"Error deleting TP1 relief: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

# ============================================================================
# Bulk Operations Endpoints
# ============================================================================

@app.route("/api/admin/employees/generate-pdfs", methods=["POST"])
def generate_all_employee_pdfs():
    """
    Generate payslip PDFs for multiple employees and return as a ZIP file.
    
    Request body:
        - payroll_run_id: UUID of a payroll run (optional). If provided, extracts month_year from it.
        - month_year: Month/year string like "01/2024" (optional, used if payroll_run_id not provided)
        - employee_ids: Optional list of employee UUIDs. If not provided, generates for all employees with payroll runs for the period.
    
    Returns:
        ZIP file containing all generated payslip PDFs
    """
    import tempfile
    import zipfile
    import shutil
    
    temp_dir = None
    try:
        from core.pdf_generator import generate_payslip_for_employee as generate_pdf
        
        data = request.get_json()
        payroll_run_id = data.get("payroll_run_id")
        month_year = data.get("month_year")
        employee_ids = data.get("employee_ids", [])
        
        # Determine month_year from payroll_run_id if provided
        if payroll_run_id:
            payroll_response = supabase.table("payroll_runs").select("month_year, payroll_date, employee_id").eq("id", payroll_run_id).execute()
            if not payroll_response.data:
                return jsonify({"success": False, "message": "Payroll run not found"})
            payroll_info = payroll_response.data[0]
            month_year = payroll_info.get("month_year")
            # If no employee_ids provided, use the one from this payroll run
            if not employee_ids:
                employee_ids = [payroll_info.get("employee_id")]
        
        if not month_year:
            return jsonify({"success": False, "message": "Either payroll_run_id or month_year is required"})
        
        # If no specific employee_ids provided, get all employees with payroll runs for this month/year
        if not employee_ids:
            runs_response = supabase.table("payroll_runs").select("id, employee_id").eq("month_year", month_year).execute()
            if runs_response.data:
                employee_ids = list(set([run.get("employee_id") for run in runs_response.data if run.get("employee_id")]))
            if not employee_ids:
                return jsonify({"success": False, "message": f"No payroll runs found for <month_year>"})
        
        # Get payroll run IDs for each employee in this period
        employee_payroll_map = {}
        runs = supabase.table("payroll_runs").select("id, employee_id").eq("month_year", month_year).in_("employee_id", employee_ids).execute()
        if runs.data:
            for run in runs.data:
                employee_payroll_map[run.get("employee_id")] = run.get("id")
        
        month_year_safe = month_year.replace("/", "_") if month_year else "unknown"
        
        # Create temporary directory for PDFs
        temp_dir = tempfile.mkdtemp(prefix="payslips_")
        generated_files = []
        errors = []
        
        for employee_id in employee_ids:
            try:
                # Get the payroll run ID for this employee
                run_id = employee_payroll_map.get(employee_id)
                if not run_id:
                    errors.append(f"No payroll run found for employee <employee_id> in <month_year>")
                    continue
                
                # Get employee info for filename
                emp_response = supabase.table("employees").select("employee_id, full_name").eq("id", employee_id).execute()
                if not emp_response.data:
                    errors.append(f"Employee <employee_id> not found")
                    continue
                
                emp = emp_response.data[0]
                emp_display_id = emp.get("employee_id", employee_id)
                emp_name = emp.get("full_name", "Unknown").replace(" ", "_").replace("/", "-")
                
                # Generate filename
                filename = f"payslip_<emp_display_id>_<emp_name>_<month_year_safe>.pdf"
                output_path = os.path.join(temp_dir, filename)
                
                # Generate the PDF
                result_path = generate_pdf(employee_id, run_id, output_path)
                
                if result_path and os.path.exists(result_path):
                    generated_files.append((filename, result_path))
                else:
                    errors.append(f"Failed to generate PDF for {emp.get('full_name', employee_id)}")
            except Exception as e:
                errors.append(f"Error generating PDF for <employee_id>: {str(e)}")
        
        if not generated_files:
            # Clean up temp directory on failure
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            return {
                "success": False, 
                "message": "No PDFs were generated",
                "errors": errors
            }
        
        # Create ZIP file
        zip_filename = f"payslips_<month_year_safe>.zip"
        zip_path = os.path.join(temp_dir, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filename, filepath in generated_files:
                zipf.write(filepath, filename)
        
        # Clean up individual PDF files (keep only the ZIP)
        for _, filepath in generated_files:
            try:
                os.remove(filepath)
            except (OSError, FileNotFoundError):
                pass
        
        # Return the ZIP file
        # Note: FastAPI's FileResponse handles the file, but temp directory cleanup 
        # is left to the OS temp file cleanup mechanism for simplicity
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=zip_filename,
            headers={"Content-Disposition": f"attachment; filename=<zip_filename>"}
        )
        
    except Exception as e:
        # Clean up temp directory on error
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"Error generating bulk PDFs: {str(e)}")
        return jsonify({"success": False, "message": f"Error generating PDFs: {str(e)}"})

# ============================================================================
# Location Autocomplete Endpoint
# ============================================================================

@app.route("/api/location/autocomplete")
def location_autocomplete(query: str, country: Optional[str] = None):
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
            return jsonify({"success": True, "data": []})
        
        # Geoapify API configuration - use same key as Python GUI
        GEOAPIFY_API_KEY = os.environ.get('GEOAPIFY_KEY')
        if not GEOAPIFY_API_KEY:
            # Fallback to the key from places_autocomplete.py (same as Python GUI)
            try:
                from gui.places_autocomplete import GEOAPIFY_API_KEY as GUI_KEY
                GEOAPIFY_API_KEY = GUI_KEY
            except ImportError:
                GEOAPIFY_API_KEY = None
        
        if not GEOAPIFY_API_KEY:
            return {
                "success": False,
                "message": "Location service not configured.",
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
        
        return jsonify({"success": True, "data": results})
        
    except requests.exceptions.RequestException as e:
        print(f"Error calling Geoapify API: {str(e)}")
        return jsonify({"success": False, "message": f"Location service error: {str(e)}", "data": []})
    except Exception as e:
        print(f"Error in location autocomplete: {str(e)}")
        return jsonify({"success": False, "message": str(e), "data": []})

@app.route("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    print("Starting HRMS Web Application...")
    print("Access the application at: http://localhost:8000")
    app.run(host="0.0.0.0", port=8000, debug=True)
