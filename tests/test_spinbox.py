from PyQt5.QtWidgets import QApplication
import sys

# Import the widget
from gui.employee_leave_tab import EmployeeLeaveTab

app = QApplication(sys.argv)
widget = EmployeeLeaveTab(user_email='test@example.com')

print('max:', widget.leave_duration_input.maximum())
print('initial value:', widget.leave_duration_input.value())

for v in [2, 10, 100, 365, 1000]:
    print('\n--- setting to', v)
    try:
        widget.leave_duration_input.setValue(v)
    except Exception as e:
        print('setValue exception:', e)
    print('spin value now:', widget.leave_duration_input.value())
    print('start:', widget.start_date.date().toString('yyyy-MM-dd'))
    print('end:  ', widget.end_date.date().toString('yyyy-MM-dd'))

print('\nDone')
app.quit()
