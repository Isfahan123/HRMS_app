# Quick test for EmployeeLeaveTab.update_dates_from_duration
# Creates a minimal QApplication, instantiates the widget, sets a start date
# and a duration, then calls the update and prints the resulting start/end.
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QDate
import os

# Ensure project root is on sys.path so package imports work when running this
# script from the tools/ folder.
proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
	sys.path.insert(0, proj_root)

# Import the target widget
from gui.employee_leave_tab import EmployeeLeaveTab

app = QApplication.instance() or QApplication(sys.argv)
widget = EmployeeLeaveTab(user_email='test@example.com')

tests = [
	('All Malaysia', 'All Malaysia'),
	('Johor via UI label', 'JOHORE'),
	('Penang via UI label', 'PULAU PINANG'),
	('Sarawak via UI label', 'SARAWAK'),
]

for label, ui_value in tests:
	print('\n---')
	print('Test:', label, 'UI value:', ui_value)
	# Set state selector if available
	try:
		idx = widget.state_combo.findText(ui_value)
		if idx != -1:
			widget.state_combo.setCurrentIndex(idx)
		else:
			# If not found, set editable text if combo is editable, else just leave it
			try:
				widget.state_combo.setEditText(ui_value)
			except Exception:
				pass
	except Exception:
		pass

	# Set the start date and duration and call update
	widget.start_date.setDate(QDate(2025, 10, 1))
	widget.leave_duration_input.setValue(3)
	widget.update_dates_from_duration(3)

	start_str = widget.start_date.date().toString('yyyy-MM-dd')
	end_str = widget.end_date.date().toString('yyyy-MM-dd')
	print('Computed start:', start_str)
	print('Computed end:  ', end_str)

# Also print holidays around the date for verification
from services.holidays_service import get_holidays_for_year
holidays, details = get_holidays_for_year(2025, None)
print('Total holidays 2025:', len(holidays))
# print any holidays in Oct 2025
oct_holidays = sorted(d for d in holidays if d.month == 10)
print('October holidays:', [d.isoformat() for d in oct_holidays])

# Exit explicitly
sys.exit(0)
