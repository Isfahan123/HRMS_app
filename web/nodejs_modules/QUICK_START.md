# Quick Start Guide - Node.js Modules

## Installation

```bash
cd web/nodejs_modules
npm install
```

## Testing the Modules

### 1. Test All Modules

```bash
node index.js
```

### 2. Generate Sample Payslip

```bash
node examples/generate_sample_payslip.js
```

Output: `/tmp/sample_payslip.pdf`

### 3. Test Individual Functions

**Payslip Generator:**
```bash
node -e "
const p = require('./payslip_generator');
console.log('Money:', p.formatMoney(1234.56));
console.log('Words:', p.numberToWords(1234.56));
console.log('PCB:', p.calculatePCB(6000, 600));
"
```

**Calendar:**
```bash
node -e "
const c = require('./leave_calendar');
console.log('Weekend:', c.isWeekendDay(new Date('2024-11-16')));
console.log('Working days:', c.countWorkingDays('2024-11-01', '2024-11-30', []));
"
```

**Bonus Manager:**
```bash
node -e "
const b = require('./bonus_manager');
const bonus = b.createBonusRecord({
    employeeId: 'EMP001',
    employeeName: 'John Doe',
    amount: 1000
});
console.log(bonus);
"
```

## Usage in Your Code

### Generate Payslip

```javascript
const { generatePayslip } = require('./web/nodejs_modules/payslip_generator');

const data = {
    employee_name: 'John Doe',
    employee_id: 'EMP001',
    basic_salary: 5000.00,
    // ... more fields
};

await generatePayslip(data, 'output.pdf');
```

### Calendar Operations

```javascript
const { countWorkingDays, isLeaveDeductible } = require('./web/nodejs_modules/leave_calendar');

const holidays = ['2024-12-25', '2024-01-01'];
const days = countWorkingDays('2024-11-01', '2024-11-30', holidays);
console.log(`Working days: ${days}`);
```

### Bonus Management

```javascript
const { createBonusRecord, calculateTotalBonus } = require('./web/nodejs_modules/bonus_manager');

const bonus = createBonusRecord({
    employeeId: 'EMP001',
    employeeName: 'John Doe',
    amount: 1000,
    bonusType: 'Performance Bonus'
});

console.log('Bonus created:', bonus.id);
```

## Integration with Python

### Call from Python (subprocess)

```python
import subprocess
import json

# Prepare data
data = {
    "employee_name": "John Doe",
    "basic_salary": 5000,
    # ... more fields
}

# Write to temp file
with open('/tmp/payslip_data.json', 'w') as f:
    json.dump(data, f)

# Call Node.js
script = """
const { generatePayslip } = require('./web/nodejs_modules/payslip_generator');
const fs = require('fs');
const data = JSON.parse(fs.readFileSync('/tmp/payslip_data.json'));
generatePayslip(data, '/tmp/output.pdf').then(() => console.log('Done'));
"""

subprocess.run(['node', '-e', script], check=True)
```

## Frontend Integration

### Calendar Component

```html
<div id="leaveCalendar"></div>
<script src="/static/js/calendar.js"></script>
<script>
    const calendar = new LeaveCalendar('leaveCalendar');
    calendar.init();
</script>
```

### Bonus Management Component

```html
<div id="bonusManagement"></div>
<script src="/static/js/bonus.js"></script>
<script>
    const bonusManager = new BonusManager();
    bonusManager.init();
</script>
```

## Troubleshooting

### Module not found

Make sure you're in the correct directory:
```bash
cd /path/to/HRMS_app
node web/nodejs_modules/index.js
```

### PDF generation fails

Check output directory exists:
```bash
mkdir -p /tmp
```

### Date format errors

Always use ISO format (YYYY-MM-DD):
```javascript
const date = '2024-11-16'; // Good
const date = '16/11/2024'; // Bad
```

## Documentation

- **Module README**: `web/nodejs_modules/README.md`
- **Implementation Guide**: `docs/NODEJS_ALTERNATIVES_GUIDE.md`
- **Task Summary**: `IMPLEMENTATION_SUMMARY.md`

## Support

For issues:
1. Check the documentation above
2. Review Python equivalents in `/gui/` directory
3. Check `docs/WEB_APPLICATION_GUIDE.md`
