import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PyQt5.QtWidgets import QApplication

# Import widget classes
from gui.employee_leave_tab import EmployeeLeaveTab
from gui.admin_leave_tab import AdminLeaveTab
from gui.leave_management.submit_request import SubmitRequestWidget

app = QApplication([])

def check_employee():
    w = EmployeeLeaveTab(user_email='test@example.com')
    has_checkbox = hasattr(w, 'half_day_checkbox')
    has_period = hasattr(w, 'half_day_period')
    enabled_period = False
    try:
        enabled_period = w.half_day_period.isEnabled()
    except Exception:
        pass
    print('EmployeeLeaveTab: half_day_checkbox=', has_checkbox, 'half_day_period=', has_period, 'period_enabled=', enabled_period)
    w.deleteLater()

def check_admin():
    w = AdminLeaveTab()
    has_checkbox = hasattr(w, 'admin_half_day_checkbox')
    has_period = hasattr(w, 'admin_half_day_period')
    enabled_period = False
    try:
        enabled_period = w.admin_half_day_period.isEnabled()
    except Exception:
        pass
    print('AdminLeaveTab: admin_half_day_checkbox=', has_checkbox, 'admin_half_day_period=', has_period, 'period_enabled=', enabled_period)
    w.deleteLater()

def check_submit_widget():
    w = SubmitRequestWidget()
    has_checkbox = hasattr(w, 'half_day_checkbox')
    has_period = hasattr(w, 'half_day_period')
    enabled_period = False
    try:
        enabled_period = w.half_day_period.isEnabled()
    except Exception:
        pass
    print('SubmitRequestWidget: half_day_checkbox=', has_checkbox, 'half_day_period=', has_period, 'period_enabled=', enabled_period)
    w.deleteLater()

    # Now toggle to simulate user checking the half-day box and verify state changes
    w2 = SubmitRequestWidget()
    try:
        print('SubmitRequestWidget - before toggle: duration_enabled=', w2.duration_input.isEnabled(), 'end_enabled=', w2.end_date.isEnabled())
        w2.half_day_checkbox.setChecked(True)
        print('SubmitRequestWidget - after toggle ON: duration_enabled=', w2.duration_input.isEnabled(), 'end_enabled=', w2.end_date.isEnabled(), 'period_enabled=', w2.half_day_period.isEnabled())
        w2.half_day_checkbox.setChecked(False)
        print('SubmitRequestWidget - after toggle OFF: duration_enabled=', w2.duration_input.isEnabled(), 'end_enabled=', w2.end_date.isEnabled(), 'period_enabled=', w2.half_day_period.isEnabled())
    except Exception as e:
        print('SubmitRequestWidget - toggle simulation failed:', e)
    finally:
        w2.deleteLater()

if __name__ == '__main__':
    check_employee()
    check_admin()
    print('Done')
    app.quit()
