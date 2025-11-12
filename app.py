# app.py - Flask Web Application for HRMS
import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_file
from functools import wraps
from datetime import datetime, timedelta
import secrets

# Import existing services
from services.supabase_service import (
    login_user_by_username,
    reconcile_employees_work_status_for_today
)
from services.supabase_employee import fetch_employee_list, fetch_employee_details
from services import supabase_leave_types

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

# Decorator for login required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator for admin required
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if not session.get('is_admin', False):
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Redirect to login or dashboard based on session"""
    if 'user_id' in session:
        if session.get('is_admin', False):
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        try:
            # Authenticate user
            result = login_user_by_username(username, password)
            
            if result and result.get('success'):
                # Set session variables
                session.permanent = True
                session['username'] = username
                session['email'] = result.get('email', username)
                session['role'] = result.get('role', 'employee')
                session['is_admin'] = result.get('role') == 'admin'
                
                # Fetch employee details using email
                try:
                    employees = fetch_employee_list()
                    # Find matching employee by email
                    for emp_uuid, emp_id, emp_name in employees:
                        emp_details = fetch_employee_details(emp_uuid if emp_uuid else emp_id)
                        if emp_details.get('email', '').lower() == result.get('email', '').lower():
                            session['user_id'] = emp_uuid if emp_uuid else emp_id
                            session['employee_name'] = emp_name or username
                            break
                    else:
                        # Fallback if no employee found
                        session['user_id'] = result.get('email')
                        session['employee_name'] = username
                except Exception as e:
                    print(f"Error fetching employee details: {e}")
                    session['user_id'] = result.get('email')
                    session['employee_name'] = username
                
                # Reconcile work status on login
                try:
                    reconcile_employees_work_status_for_today()
                except Exception as e:
                    print(f"Work status reconcile warning: {e}")
                
                flash(f'Welcome, {session.get("employee_name", username)}!', 'success')
                
                # Redirect based on role
                if session['is_admin']:
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('dashboard'))
            elif result.get('locked_until'):
                flash(f'Account is locked until {result.get("locked_until")}. Please try again later.', 'danger')
            else:
                flash('Invalid username or password.', 'danger')
        except Exception as e:
            print(f"Login error: {e}")
            flash('An error occurred during login. Please try again.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}!', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Employee dashboard"""
    try:
        # Fetch employee details
        employee = fetch_employee_details(session['user_id']) if session.get('user_id') else {}
        return render_template('dashboard.html', 
                             employee=employee,
                             username=session.get('employee_name', session['username']))
    except Exception as e:
        print(f"Dashboard error: {e}")
        flash('Error loading dashboard.', 'danger')
        return redirect(url_for('login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    try:
        return render_template('admin_dashboard.html',
                             username=session.get('employee_name', session['username']))
    except Exception as e:
        print(f"Admin dashboard error: {e}")
        flash('Error loading admin dashboard.', 'danger')
        return redirect(url_for('login'))

# API endpoints for AJAX requests
@app.route('/api/profile')
@login_required
def api_profile():
    """Get current user profile"""
    try:
        employee = fetch_employee_details(session['user_id']) if session.get('user_id') else {}
        return jsonify({'success': True, 'employee': employee})
    except Exception as e:
        print(f"API profile error: {e}")  # Log for debugging
        return jsonify({'success': False, 'error': 'Failed to load profile'}), 500

@app.route('/api/employees')
@admin_required
def api_employees():
    """Get all employees (admin only)"""
    try:
        employees_list = fetch_employee_list()
        employees = []
        for emp_uuid, emp_id, emp_name in employees_list:
            emp_details = fetch_employee_details(emp_uuid if emp_uuid else emp_id)
            employees.append({
                'id': emp_uuid if emp_uuid else emp_id,
                'employee_id': emp_id,
                'name': emp_name or emp_details.get('full_name', '--'),
                'email': emp_details.get('email', '--'),
                'department': emp_details.get('department', '--'),
                'position': emp_details.get('job_title', '--')
            })
        return jsonify({'success': True, 'employees': employees})
    except Exception as e:
        print(f"API employees error: {e}")  # Log for debugging
        return jsonify({'success': False, 'error': 'Failed to load employees'}), 500

@app.route('/api/leave/types')
@login_required
def api_leave_types():
    """Get leave types"""
    try:
        leave_types = supabase_leave_types.list_leave_types()
        return jsonify({'success': True, 'leave_types': leave_types})
    except Exception as e:
        print(f"API leave types error: {e}")  # Log for debugging
        return jsonify({'success': False, 'error': 'Failed to load leave types'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', 
                         error_code=404, 
                         error_message='Page not found'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('error.html', 
                         error_code=500, 
                         error_message='Internal server error'), 500

if __name__ == '__main__':
    # Development server
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    port = int(os.getenv('FLASK_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
