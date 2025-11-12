"""
Flask web application for HRMS
Replaces the PyQt5 desktop application with a web-based interface
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import os
from dotenv import load_dotenv
from services.supabase_service import (
    login_user_by_username, 
    supabase,
    get_attendance_history,
    fetch_user_leave_requests
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
    """Redirect to login or dashboard"""
    if 'user_email' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

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
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/leave-requests')
@login_required
def api_leave_requests():
    """Get leave requests for current user"""
    try:
        requests_data = fetch_user_leave_requests(session['user_email'])
        return jsonify({'success': True, 'data': requests_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
