import sys
import os
import pytest
from PyQt5.QtWidgets import QApplication

# Ensure project root is on sys.path when tests run
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Ensure QApplication exists for widget creation
app = QApplication.instance() or QApplication(sys.argv)

from gui.admin_dashboard_window import AdminDashboardWindow


def test_history_tab_receives_employee_and_enables_forms():
    window = AdminDashboardWindow(None)
    # Simulate an employee dict as returned by Supabase
    employee = {'id': '00000000-0000-0000-0000-000000000001', 'full_name': 'Test Employee'}

    # Ensure initial state: no employee selected
    hist_tab = window.employee_history_tab
    assert 'No employee selected' in hist_tab.header_label.text()
    assert not hist_tab.job_title_combo.isEnabled()

    # Simulate profile tab emitting employee_selected
    window.on_profile_employee_selected(employee)

    # After emitting, the header should be updated and form enabled
    assert 'Test Employee' in hist_tab.header_label.text()
    assert hist_tab.job_title_combo.isEnabled()
    assert hist_tab.submit_btn.isEnabled()

    # Clean up
    window.close()
