#!/usr/bin/env python3
"""
Test script for the PayrollInformationDialog with new column layout
"""

import sys
from PyQt5.QtWidgets import QApplication
from gui.payroll_dialog import PayrollInformationDialog

def test_payroll_dialog():
    app = QApplication(sys.argv)
    
    # Sample employee data for testing
    employee_data = {
        'id': 1,
        'name': 'Test Employee',
        'employee_id': 'EMP001',
        'email': 'test@example.com',
        'basic_salary': 5000.00,
        'income_tax_number': 'TAX123456',
        'epf_number': 'EPF789012',
        'socso_number': 'SOCSO345678'
    }
    
    # Create and show the dialog
    dialog = PayrollInformationDialog(employee_data=employee_data, is_admin=True)
    dialog.show()
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_payroll_dialog()
