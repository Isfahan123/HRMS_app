# HRMS Web Application - API Documentation

Complete API reference for all backend endpoints in the Flask web application.

## Table of Contents
- [Authentication](#authentication)
- [Employee API Endpoints](#employee-api-endpoints)
- [Admin API Endpoints](#admin-api-endpoints)
- [Error Handling](#error-handling)
- [Examples](#examples)

---

## Authentication

All API endpoints (except `/login`) require authentication via Flask sessions.

### Login
```
POST /login
Content-Type: application/json

Request Body:
{
  "username": "john.doe",
  "password": "password123"
}

Success Response (200):
{
  "success": true,
  "redirect": "/dashboard" or "/admin"
}

Error Response (401):
{
  "success": false,
  "message": "Invalid username or password"
}
```

### Logout
```
GET /logout
```
Clears session and redirects to login page.

---

## Employee API Endpoints

All employee endpoints require authentication (`@login_required`).

### 1. Get Employee Profile
```
GET /api/profile

Success Response (200):
{
  "success": true,
  "data": {
    "id": "uuid",
    "employee_id": "EMP001",
    "full_name": "John Doe",
    "email": "john.doe@company.com",
    "department": "Engineering",
    "job_title": "Software Engineer",
    "phone_number": "+60123456789",
    "hire_date": "2023-01-15",
    "basic_salary": 5000.00,
    ...
  }
}
```

### 2. Get Attendance History
```
GET /api/attendance

Success Response (200):
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "date": "2024-11-11",
      "check_in": "09:00:00",
      "check_out": "18:00:00",
      "status": "present",
      "hours_worked": 8.0
    },
    ...
  ]
}
```

### 3. Get Leave Requests
```
GET /api/leave-requests

Success Response (200):
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "leave_type": "annual",
      "start_date": "2024-12-20",
      "end_date": "2024-12-22",
      "days": 3,
      "status": "pending",
      "reason": "Family vacation",
      "submitted_at": "2024-11-10T10:30:00Z"
    },
    ...
  ]
}
```

### 4. Submit Leave Request
```
POST /api/leave-requests/submit
Content-Type: application/json

Request Body:
{
  "leave_type": "annual",
  "start_date": "2024-12-20",
  "end_date": "2024-12-22",
  "reason": "Family vacation"
}

Success Response (200):
{
  "success": true,
  "message": "Leave request submitted successfully"
}
```

### 5. Get Payroll Information
```
GET /api/payroll

Success Response (200):
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "year": 2024,
      "month": 11,
      "basic_salary": 5000.00,
      "allowances": 500.00,
      "deductions": 300.00,
      "net_salary": 5200.00,
      "epf_employee": 550.00,
      "epf_employer": 600.00,
      "socso": 50.00,
      "eis": 10.00,
      "tax": 200.00,
      "paid_at": "2024-11-25T00:00:00Z"
    },
    ...
  ]
}
```

### 6. Get Training Courses
```
GET /api/training

Success Response (200):
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "course_name": "Python Advanced Programming",
      "provider": "Tech Academy",
      "start_date": "2024-11-01",
      "end_date": "2024-11-30",
      "duration_days": 30,
      "status": "in_progress",
      "certificate_received": false
    },
    ...
  ]
}
```

### 7. Get Overseas Trips
```
GET /api/trips

Success Response (200):
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "destination": "Singapore",
      "purpose": "Client meeting",
      "start_date": "2024-12-01",
      "end_date": "2024-12-05",
      "duration_days": 5,
      "status": "approved",
      "flight_cost": 500.00,
      "accommodation_cost": 1000.00,
      "meal_allowance": 250.00,
      "total_cost": 1750.00
    },
    ...
  ]
}
```

---

## Admin API Endpoints

All admin endpoints require admin role (`@admin_required`).

### 1. List All Employees
```
GET /api/admin/employees

Success Response (200):
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "employee_id": "EMP001",
      "full_name": "John Doe",
      "email": "john.doe@company.com",
      "department": "Engineering",
      "job_title": "Software Engineer",
      "hire_date": "2023-01-15",
      "work_status": "active"
    },
    ...
  ]
}
```

### 2. Add New Employee
```
POST /api/admin/employees/add
Content-Type: application/json

Request Body:
{
  "employee_id": "EMP999",
  "full_name": "Jane Smith",
  "email": "jane.smith@company.com",
  "department": "HR",
  "job_title": "HR Manager",
  "phone_number": "+60123456789",
  "hire_date": "2024-11-15",
  "basic_salary": 6000.00,
  "password": "initial_password"
}

Success Response (200):
{
  "success": true,
  "message": "Employee added successfully",
  "data": { ... }
}
```

### 3. Update Employee
```
PUT /api/admin/employees/<employee_id>
Content-Type: application/json

Request Body:
{
  "department": "Engineering",
  "job_title": "Senior Engineer",
  "basic_salary": 7000.00
}

Success Response (200):
{
  "success": true,
  "message": "Employee updated successfully",
  "data": { ... }
}
```

### 4. List All Leave Requests
```
GET /api/admin/leave-requests

Success Response (200):
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "employee_name": "John Doe",
      "employee_email": "john.doe@company.com",
      "leave_type": "annual",
      "start_date": "2024-12-20",
      "end_date": "2024-12-22",
      "days": 3,
      "status": "pending",
      "reason": "Family vacation",
      "submitted_at": "2024-11-10T10:30:00Z"
    },
    ...
  ]
}
```

### 5. Approve Leave Request
```
POST /api/admin/leave-requests/<leave_id>/approve

Success Response (200):
{
  "success": true,
  "message": "Leave request approved"
}
```

### 6. Reject Leave Request
```
POST /api/admin/leave-requests/<leave_id>/reject

Success Response (200):
{
  "success": true,
  "message": "Leave request rejected"
}
```

### 7. List All Attendance Records
```
GET /api/admin/attendance

Success Response (200):
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "employee_email": "john.doe@company.com",
      "date": "2024-11-11",
      "check_in": "09:00:00",
      "check_out": "18:00:00",
      "status": "present",
      "hours_worked": 8.0
    },
    ...
  ]
}
```

### 8. Get Salary History
```
GET /api/admin/salary-history/<employee_id>

Success Response (200):
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "employee_id": "EMP001",
      "change_date": "2024-01-01",
      "old_salary": 5000.00,
      "new_salary": 5500.00,
      "change_type": "increment",
      "change_percentage": 10.0,
      "reason": "Annual increment",
      "approved_by": "admin@company.com"
    },
    ...
  ]
}
```

### 9. List Bonuses
```
GET /api/admin/bonus

Success Response (200):
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "employee_id": "EMP001",
      "employee_name": "John Doe",
      "bonus_type": "performance",
      "amount": 2000.00,
      "description": "Q4 2024 performance bonus",
      "status": "approved",
      "created_at": "2024-11-10T10:00:00Z"
    },
    ...
  ]
}
```

### 10. Add Bonus
```
POST /api/admin/bonus/add
Content-Type: application/json

Request Body:
{
  "employee_id": "EMP001",
  "bonus_type": "performance",
  "amount": 2000.00,
  "description": "Q4 2024 performance bonus",
  "status": "approved"
}

Success Response (200):
{
  "success": true,
  "message": "Bonus added successfully",
  "data": { ... }
}
```

### 11. List Training Courses
```
GET /api/admin/training

Success Response (200):
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "employee_id": "EMP001",
      "employee_name": "John Doe",
      "course_name": "Python Advanced Programming",
      "provider": "Tech Academy",
      "start_date": "2024-11-01",
      "end_date": "2024-11-30",
      "duration_days": 30,
      "status": "in_progress",
      "cost": 1500.00
    },
    ...
  ]
}
```

### 12. Add Training Course
```
POST /api/admin/training/add
Content-Type: application/json

Request Body:
{
  "employee_id": "EMP001",
  "course_name": "AWS Certification",
  "provider": "Amazon",
  "start_date": "2024-12-01",
  "end_date": "2024-12-31",
  "duration_days": 31,
  "cost": 2000.00,
  "status": "planned"
}

Success Response (200):
{
  "success": true,
  "message": "Training course added successfully",
  "data": { ... }
}
```

### 13. List Overseas Trips
```
GET /api/admin/trips

Success Response (200):
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "employee_id": "EMP001",
      "employee_name": "John Doe",
      "destination": "Singapore",
      "purpose": "Client meeting",
      "start_date": "2024-12-01",
      "end_date": "2024-12-05",
      "duration_days": 5,
      "status": "approved",
      "total_cost": 1750.00
    },
    ...
  ]
}
```

### 14. Add Overseas Trip
```
POST /api/admin/trips/add
Content-Type: application/json

Request Body:
{
  "employee_id": "EMP001",
  "destination": "Singapore",
  "purpose": "Client meeting",
  "start_date": "2024-12-01",
  "end_date": "2024-12-05",
  "flight_cost": 500.00,
  "accommodation_cost": 1000.00,
  "meal_allowance": 250.00,
  "status": "pending"
}

Success Response (200):
{
  "success": true,
  "message": "Trip added successfully",
  "data": { ... }
}
```

### 15. Get Tax Configuration
```
GET /api/admin/tax-config/<year>

Example: GET /api/admin/tax-config/2024

Success Response (200):
{
  "success": true,
  "data": {
    "year": 2024,
    "tax_brackets": [
      { "max_income": 5000, "rate": 0.0 },
      { "max_income": 20000, "rate": 0.01 },
      { "max_income": 35000, "rate": 0.03 },
      ...
    ],
    "relief_maximums": {
      "self": 9000,
      "spouse": 4000,
      "children": 2000,
      "epf": 4000,
      "insurance": 3000,
      "medical": 8000
    },
    "statutory_rates": {
      "epf_employee": 0.11,
      "epf_employer": 0.13,
      "socso_employee": 0.005,
      "socso_employer": 0.0175,
      "eis": 0.002
    }
  }
}
```

### 16. Update Tax Configuration
```
PUT /api/admin/tax-config/<year>
Content-Type: application/json

Request Body:
{
  "tax_brackets": [ ... ],
  "relief_maximums": { ... },
  "statutory_rates": { ... }
}

Success Response (200):
{
  "success": true,
  "message": "Tax configuration updated successfully"
}
```

---

## Error Handling

All endpoints follow a consistent error response format:

### Error Response Format
```json
{
  "success": false,
  "message": "Human-readable error message"
}
```

### Common HTTP Status Codes
- `200` - Success
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (not logged in)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error

### Error Examples

**Not Authenticated:**
```
Status: 401 Unauthorized
{
  "success": false,
  "message": "Authentication required"
}
```

**Insufficient Permissions:**
```
Status: 403 Forbidden
{
  "success": false,
  "message": "Admin access required"
}
```

**Server Error:**
```
Status: 500 Internal Server Error
{
  "success": false,
  "message": "Failed to fetch data"
}
```

---

## Examples

### JavaScript (Fetch API)

**Get Profile:**
```javascript
fetch('/api/profile')
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      console.log('Profile:', data.data);
    } else {
      console.error('Error:', data.message);
    }
  });
```

**Submit Leave Request:**
```javascript
fetch('/api/leave-requests/submit', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    leave_type: 'annual',
    start_date: '2024-12-20',
    end_date: '2024-12-22',
    reason: 'Family vacation'
  })
})
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      alert(data.message);
    } else {
      alert('Error: ' + data.message);
    }
  });
```

**Admin: Approve Leave:**
```javascript
fetch('/api/admin/leave-requests/12345/approve', {
  method: 'POST'
})
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      alert('Leave approved!');
    } else {
      alert('Error: ' + data.message);
    }
  });
```

### cURL Examples

**Get Profile:**
```bash
curl -X GET http://localhost:5000/api/profile \
  -H "Cookie: session=your_session_cookie"
```

**Submit Leave Request:**
```bash
curl -X POST http://localhost:5000/api/leave-requests/submit \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your_session_cookie" \
  -d '{
    "leave_type": "annual",
    "start_date": "2024-12-20",
    "end_date": "2024-12-22",
    "reason": "Family vacation"
  }'
```

**Admin: List Employees:**
```bash
curl -X GET http://localhost:5000/api/admin/employees \
  -H "Cookie: session=your_admin_session_cookie"
```

---

## Notes

1. **Authentication**: All API requests must include the Flask session cookie obtained after successful login.

2. **CORS**: If accessing the API from a different domain, you'll need to configure CORS in Flask.

3. **Rate Limiting**: Consider implementing rate limiting in production to prevent abuse.

4. **CSRF Protection**: For production, add CSRF protection using Flask-WTF or similar.

5. **HTTPS**: Always use HTTPS in production to protect session cookies and sensitive data.

6. **Error Logging**: All server errors are logged to `app.logger` for debugging. Check application logs for details.

---

## Support

For questions or issues:
- See `README_WEB.md` for application overview
- See `QUICKSTART.md` for setup instructions
- See `CONVERSION_SUMMARY.md` for technical details

---

**Version**: 2.0.0  
**Last Updated**: 2025-11-12  
**Status**: Complete
