# HRMS Node.js Modules

This directory contains Node.js alternatives to Python GUI functionality that hasn't been implemented in the HTML/JavaScript web interface yet.

## Overview

The HRMS application originally had Python/Flask GUI components using PyQt5. This module provides Node.js/JavaScript equivalents for features that need to be available in the web version but couldn't be directly implemented in HTML/JavaScript.

## Modules

### 1. Payslip Generator (`payslip_generator.js`)

**Purpose**: Generate PDF payslips programmatically

**Python Equivalent**: `gui/payslip_generator.py`

**Features**:
- Generate PDF payslips with company branding
- Calculate deductions (EPF, SOCSO, EIS, PCB)
- Format currency and convert amounts to words
- Download and embed company logo
- Professional payslip layout matching Malaysian standards

**Usage**:
```javascript
const { generatePayslip } = require('./payslip_generator');

const payslipData = {
    employee_name: 'John Doe',
    employee_id: 'EMP001',
    department: 'Engineering',
    position: 'Software Engineer',
    pay_period: '2024-11',
    pay_date: '2024-11-30',
    basic_salary: 5000.00,
    allowances: 500.00,
    bonuses: 1000.00,
    epf_employee: 550.00,
    socso_employee: 39.25,
    eis: 7.90,
    pcb: 200.00,
    unpaid_leave_deduction: 0.00
};

await generatePayslip(payslipData, 'payslip_nov_2024.pdf');
```

### 2. Leave Calendar (`leave_calendar.js`)

**Purpose**: Calendar utilities for leave management

**Python Equivalent**: `gui/leave_calendar.py`

**Features**:
- Check if dates are weekends or holidays
- Calculate working days between dates
- Validate leave requests
- Calculate leave balance
- Generate monthly calendar data for visualization

**Usage**:
```javascript
const { isLeaveDeductible, countWorkingDays } = require('./leave_calendar');

// Check if a date should deduct leave
const isDeductible = isLeaveDeductible('2024-12-25', ['2024-12-25']); // false (holiday)

// Count working days
const workingDays = countWorkingDays('2024-11-01', '2024-11-30', holidays);
console.log(`Working days: ${workingDays}`);
```

### 3. Bonus Manager (`bonus_manager.js`)

**Purpose**: Bonus management utilities

**Python Equivalent**: `gui/bonus_management_dialog.py`

**Features**:
- Create and validate bonus records
- Calculate total bonuses
- Group bonuses by employee
- Generate bonus summaries
- Format bonus data for display

**Usage**:
```javascript
const { createBonusRecord, calculateTotalBonus } = require('./bonus_manager');

// Create a new bonus
const bonus = createBonusRecord({
    employeeId: 'EMP001',
    employeeName: 'John Doe',
    bonusType: 'Performance Bonus',
    amount: 1000.00,
    description: 'Q4 Performance Bonus',
    payPeriod: '2024-12'
});

// Calculate total bonuses
const total = calculateTotalBonus(bonuses, 'approved');
```

## Web Integration

### Frontend Components

The following JavaScript files in `/web/static/js/` use these modules:

1. **calendar.js**: Visual calendar component for leave management
   - Interactive monthly calendar view
   - Display leave requests and holidays
   - Navigate between months
   - Count working days for leave requests

2. **bonus.js**: Bonus management interface
   - Add/edit/delete bonuses
   - Approve bonus requests
   - View bonus summaries
   - Employee bonus history

### API Integration

Backend API endpoints in `web_app.py` should be created to:

1. **Payslip Generation**:
   - `POST /api/payroll/generate-payslip` - Generate payslip PDF
   - `GET /api/payroll/payslip/{id}` - Download payslip

2. **Leave Calendar**:
   - `GET /api/calendar/holidays` - Get holiday list
   - `GET /api/calendar/month/{year}/{month}` - Get month calendar data
   - `POST /api/leave/calculate-days` - Calculate working days

3. **Bonus Management**:
   - `GET /api/admin/bonuses` - List all bonuses
   - `POST /api/admin/bonuses` - Create new bonus
   - `PUT /api/admin/bonuses/{id}` - Update bonus
   - `DELETE /api/admin/bonuses/{id}` - Delete bonus
   - `POST /api/admin/bonuses/{id}/approve` - Approve bonus

## Installation

Install the required Node.js dependencies:

```bash
cd web/nodejs_modules
npm install
```

This will install:
- `pdfkit`: PDF generation
- `axios`: HTTP client for downloading resources
- `date-fns`: Date manipulation utilities

## Development

### Testing Modules

You can test individual modules:

```bash
# Test payslip generator
node -e "const p = require('./payslip_generator'); console.log(p.formatMoney(1234.56));"

# Test calendar utilities
node -e "const c = require('./leave_calendar'); console.log(c.isWeekendDay(new Date()));"

# Test bonus manager
node -e "const b = require('./bonus_manager'); console.log(b.BONUS_TYPES);"
```

### Running the Main Module

```bash
node index.js
```

This will display available modules and usage examples.

## Migration from Python GUI

### Comparison

| Feature | Python (PyQt5) | Node.js/JavaScript |
|---------|----------------|-------------------|
| Payslip PDF | reportlab | pdfkit |
| Date handling | datetime | date-fns |
| UI Framework | PyQt5 widgets | HTML/CSS/JS |
| Calendar | QCalendarWidget | Custom calendar.js |
| File handling | Python file I/O | Node.js fs module |

### Benefits of Node.js Version

1. **Web Compatible**: Can run in browser or server-side
2. **Cross-Platform**: Works on any system with Node.js
3. **Modern Stack**: Uses modern JavaScript features
4. **No Desktop Dependency**: Doesn't require PyQt5 installation
5. **Easy Deployment**: Can be deployed to web servers

### Differences

1. **PDF Generation**:
   - Python uses `reportlab` (more features)
   - Node.js uses `pdfkit` (simpler, sufficient for payslips)

2. **Date Handling**:
   - Python uses `datetime` module
   - Node.js uses `date-fns` library

3. **UI**:
   - Python uses desktop widgets (QCalendarWidget, QTableWidget)
   - Node.js uses HTML/CSS with JavaScript for interactivity

## Future Enhancements

- [ ] Add unit tests for all modules
- [ ] Add TypeScript type definitions
- [ ] Create React/Vue components for calendar
- [ ] Add PDF template customization
- [ ] Support multiple languages
- [ ] Add email functionality for payslips
- [ ] Create REST API server wrapper
- [ ] Add database integration helpers
- [ ] Generate Excel reports

## Troubleshooting

### PDFKit Installation Issues

If you encounter issues installing pdfkit:

```bash
# Clear npm cache
npm cache clean --force

# Install with legacy peer deps
npm install --legacy-peer-deps
```

### Date Format Issues

The modules use ISO date format (YYYY-MM-DD). Ensure dates are in this format:

```javascript
// Good
const date = '2024-11-16';

// Bad
const date = '16/11/2024'; // Will not work
```

### Module Not Found

Make sure you're in the correct directory:

```bash
cd /path/to/HRMS_app/web/nodejs_modules
node your_script.js
```

## License

MIT License - Same as parent HRMS project

## Contributing

When adding new modules:

1. Create a new `.js` file in this directory
2. Export functions using `module.exports`
3. Add documentation in this README
4. Create corresponding frontend components in `/web/static/js/`
5. Add API endpoints in `web_app.py`
6. Update `index.js` to export the new module

## Support

For issues or questions:
- Check the main HRMS documentation
- Review Python GUI equivalents in `/gui/` directory
- Consult the web application guide in `docs/WEB_APPLICATION_GUIDE.md`
