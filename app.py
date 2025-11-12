"""
Flask web application for HRMS
Replaces the PyQt5 desktop application with a web-based interface
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import os
from datetime import datetime, date
from dotenv import load_dotenv
from services.supabase_service import (
    login_user_by_username,
    supabase,
    get_attendance_history,
    fetch_user_leave_requests,
    get_all_employees,
    insert_employee,
    update_employee,
    get_all_leave_requests,
    update_leave_request_status,
    submit_leave_request,
    get_all_attendance_records,
    get_employee_history,
    get_hpb_config,
    upsert_hpb_config
)
from services.supabase_employee import fetch_employee_list, fetch_employee_details
from services.supabase_engagements import fetch_engagements
from services.supabase_training_overseas import (
    fetch_training_course_records,
    fetch_overseas_work_trip_records,
    insert_training_course_record,
    insert_overseas_work_trip_record,
    update_training_course_record,
    update_overseas_work_trip_record
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session or session.get('role') != 'admin':
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Landing page or redirect to dashboard if logged in"""
    if 'user_email' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip().lower()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Please enter both username and password'}), 400
        
        result = login_user_by_username(username, password)
        
        if result and result.get('locked_until'):
            return jsonify({
                'success': False,
                'message': f"Account is locked until {result['locked_until']}. Please try again later."
            }), 403
        
        if result and result.get('role'):
            session['user_email'] = result.get('email', '').lower()
            session['role'] = result['role'].lower()
            session['full_name'] = result.get('full_name', '')
            
            redirect_url = url_for('admin_dashboard') if session['role'] == 'admin' else url_for('dashboard')
            return jsonify({'success': True, 'redirect': redirect_url})
        
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Employee dashboard"""
    return render_template('dashboard.html', user_email=session['user_email'], full_name=session.get('full_name', ''))

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    return render_template('admin_dashboard.html', user_email=session['user_email'], full_name=session.get('full_name', ''))

# API routes for data
@app.route('/api/attendance')
@login_required
def api_attendance():
    """Get attendance history for current user"""
    try:
        history = get_attendance_history(session['user_email'])
        return jsonify({'success': True, 'data': history})
    except Exception as e:
        # Log error for debugging but don't expose stack trace to user
        app.logger.error(f"Error fetching attendance: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch attendance data'}), 500

@app.route('/api/leave-requests')
@login_required
def api_leave_requests():
    """Get leave requests for current user"""
    try:
        requests_data = fetch_user_leave_requests(session['user_email'])
        return jsonify({'success': True, 'data': requests_data})
    except Exception as e:
        # Log error for debugging but don't expose stack trace to user
        app.logger.error(f"Error fetching leave requests: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch leave requests'}), 500

@app.route('/api/profile')
@login_required
def api_profile():
    """Get employee profile for current user"""
    try:
        # Fetch employee details using email
        result = supabase.table('employees').select('*').eq('email', session['user_email']).limit(1).execute()
        if result.data:
            return jsonify({'success': True, 'data': result.data[0]})
        return jsonify({'success': False, 'message': 'Profile not found'}), 404
    except Exception as e:
        app.logger.error(f"Error fetching profile: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch profile'}), 500

@app.route('/api/leave-requests/submit', methods=['POST'])
@login_required
def api_submit_leave_request():
    """Submit a new leave request"""
    try:
        data = request.get_json()
        result = submit_leave_request(
            employee_email=session['user_email'],
            leave_type=data.get('leave_type'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            reason=data.get('reason')
        )
        if result:
            return jsonify({'success': True, 'message': 'Leave request submitted successfully'})
        return jsonify({'success': False, 'message': 'Failed to submit leave request'}), 400
    except Exception as e:
        app.logger.error(f"Error submitting leave request: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to submit leave request'}), 500

@app.route('/api/payroll')
@login_required
def api_payroll():
    """Get payroll information for current user"""
    try:
        # Fetch payroll records for the user
        result = supabase.table('payroll').select('*').eq('employee_email', session['user_email']).order('year', desc=True).order('month', desc=True).limit(12).execute()
        return jsonify({'success': True, 'data': result.data})
    except Exception as e:
        app.logger.error(f"Error fetching payroll: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch payroll data'}), 500

@app.route('/api/training')
@login_required
def api_training():
    """Get training courses for current user"""
    try:
        # Get employee ID first
        emp_result = supabase.table('employees').select('id').eq('email', session['user_email']).limit(1).execute()
        if emp_result.data:
            employee_id = emp_result.data[0]['id']
            courses = fetch_training_course_records(employee_id=employee_id)
            return jsonify({'success': True, 'data': courses})
        return jsonify({'success': True, 'data': []})
    except Exception as e:
        app.logger.error(f"Error fetching training: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch training data'}), 500

@app.route('/api/trips')
@login_required
def api_trips():
    """Get overseas trips for current user"""
    try:
        # Get employee ID first
        emp_result = supabase.table('employees').select('id').eq('email', session['user_email']).limit(1).execute()
        if emp_result.data:
            employee_id = emp_result.data[0]['id']
            trips = fetch_overseas_work_trip_records(employee_id=employee_id)
            return jsonify({'success': True, 'data': trips})
        return jsonify({'success': True, 'data': []})
    except Exception as e:
        app.logger.error(f"Error fetching trips: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch trips data'}), 500

# Admin API endpoints
@app.route('/api/admin/employees')
@admin_required
def api_admin_employees():
    """Get all employees (admin only)"""
    try:
        employees = get_all_employees()
        return jsonify({'success': True, 'data': employees})
    except Exception as e:
        app.logger.error(f"Error fetching employees: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch employees'}), 500

@app.route('/api/admin/employees/add', methods=['POST'])
@admin_required
def api_admin_add_employee():
    """Add a new employee (admin only)"""
    try:
        data = request.get_json()
        password = data.pop('password', None)
        result = insert_employee(data, password)
        return jsonify({'success': True, 'message': 'Employee added successfully', 'data': result})
    except Exception as e:
        app.logger.error(f"Error adding employee: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to add employee'}), 500

@app.route('/api/admin/employees/<employee_id>', methods=['PUT'])
@admin_required
def api_admin_update_employee(employee_id):
    """Update an employee (admin only)"""
    try:
        data = request.get_json()
        result = update_employee(employee_id, data)
        return jsonify({'success': True, 'message': 'Employee updated successfully', 'data': result})
    except Exception as e:
        app.logger.error(f"Error updating employee: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to update employee'}), 500

@app.route('/api/admin/leave-requests')
@admin_required
def api_admin_leave_requests():
    """Get all leave requests (admin only)"""
    try:
        requests_data = get_all_leave_requests()
        return jsonify({'success': True, 'data': requests_data})
    except Exception as e:
        app.logger.error(f"Error fetching leave requests: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch leave requests'}), 500

@app.route('/api/admin/leave-requests/<leave_id>/approve', methods=['POST'])
@admin_required
def api_admin_approve_leave(leave_id):
    """Approve a leave request (admin only)"""
    try:
        result = update_leave_request_status(leave_id, 'approved', session['user_email'])
        if result:
            return jsonify({'success': True, 'message': 'Leave request approved'})
        return jsonify({'success': False, 'message': 'Failed to approve leave request'}), 400
    except Exception as e:
        app.logger.error(f"Error approving leave: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to approve leave request'}), 500

@app.route('/api/admin/leave-requests/<leave_id>/reject', methods=['POST'])
@admin_required
def api_admin_reject_leave(leave_id):
    """Reject a leave request (admin only)"""
    try:
        result = update_leave_request_status(leave_id, 'rejected', session['user_email'])
        if result:
            return jsonify({'success': True, 'message': 'Leave request rejected'})
        return jsonify({'success': False, 'message': 'Failed to reject leave request'}), 400
    except Exception as e:
        app.logger.error(f"Error rejecting leave: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to reject leave request'}), 500

@app.route('/api/admin/attendance')
@admin_required
def api_admin_attendance():
    """Get all attendance records (admin only)"""
    try:
        records = get_all_attendance_records()
        return jsonify({'success': True, 'data': records})
    except Exception as e:
        app.logger.error(f"Error fetching attendance: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch attendance records'}), 500

@app.route('/api/admin/salary-history/<employee_id>')
@admin_required
def api_admin_salary_history(employee_id):
    """Get salary history for an employee (admin only)"""
    try:
        history = get_employee_history(employee_id)
        return jsonify({'success': True, 'data': history})
    except Exception as e:
        app.logger.error(f"Error fetching salary history: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch salary history'}), 500

@app.route('/api/admin/bonus', methods=['GET'])
@admin_required
def api_admin_bonus():
    """Get all bonus records (admin only)"""
    try:
        result = supabase.table('bonus').select('*').order('created_at', desc=True).execute()
        return jsonify({'success': True, 'data': result.data})
    except Exception as e:
        app.logger.error(f"Error fetching bonus records: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch bonus records'}), 500

@app.route('/api/admin/bonus/add', methods=['POST'])
@admin_required
def api_admin_add_bonus():
    """Add a new bonus (admin only)"""
    try:
        data = request.get_json()
        data['created_by'] = session['user_email']
        data['created_at'] = datetime.now().isoformat()
        result = supabase.table('bonus').insert(data).execute()
        return jsonify({'success': True, 'message': 'Bonus added successfully', 'data': result.data})
    except Exception as e:
        app.logger.error(f"Error adding bonus: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to add bonus'}), 500

@app.route('/api/admin/training', methods=['GET'])
@admin_required
def api_admin_training():
    """Get all training courses (admin only)"""
    try:
        courses = fetch_training_course_records()
        return jsonify({'success': True, 'data': courses})
    except Exception as e:
        app.logger.error(f"Error fetching training: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch training courses'}), 500

@app.route('/api/admin/training/add', methods=['POST'])
@admin_required
def api_admin_add_training():
    """Add a new training course (admin only)"""
    try:
        data = request.get_json()
        result = insert_training_course_record(data)
        return jsonify({'success': True, 'message': 'Training course added successfully', 'data': result.data})
    except Exception as e:
        app.logger.error(f"Error adding training: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to add training course'}), 500

@app.route('/api/admin/trips', methods=['GET'])
@admin_required
def api_admin_trips():
    """Get all overseas trips (admin only)"""
    try:
        trips = fetch_overseas_work_trip_records()
        return jsonify({'success': True, 'data': trips})
    except Exception as e:
        app.logger.error(f"Error fetching trips: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch trips'}), 500

@app.route('/api/admin/trips/add', methods=['POST'])
@admin_required
def api_admin_add_trip():
    """Add a new overseas trip (admin only)"""
    try:
        data = request.get_json()
        result = insert_overseas_work_trip_record(data)
        return jsonify({'success': True, 'message': 'Trip added successfully', 'data': result.data})
    except Exception as e:
        app.logger.error(f"Error adding trip: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to add trip'}), 500

@app.route('/api/admin/tax-config/<int:year>')
@admin_required
def api_admin_tax_config(year):
    """Get tax configuration for a specific year (admin only)"""
    try:
        config = get_hpb_config('tax_rates', year)
        return jsonify({'success': True, 'data': config})
    except Exception as e:
        app.logger.error(f"Error fetching tax config: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to fetch tax configuration'}), 500

@app.route('/api/admin/tax-config/<int:year>', methods=['PUT'])
@admin_required
def api_admin_update_tax_config(year):
    """Update tax configuration for a specific year (admin only)"""
    try:
        data = request.get_json()
        result = upsert_hpb_config('tax_rates', year, data)
        if result:
            return jsonify({'success': True, 'message': 'Tax configuration updated successfully'})
        return jsonify({'success': False, 'message': 'Failed to update tax configuration'}), 400
    except Exception as e:
        app.logger.error(f"Error updating tax config: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to update tax configuration'}), 500

if __name__ == '__main__':
    # Only enable debug mode in development, not production
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
