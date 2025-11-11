from PyQt5.QtWidgets import QWidget, QVBoxLayout
from gui.admin_attendance_tab import AdminAttendanceTab as LegacyAdminAttendanceTab

class AdminAttendanceTab(QWidget):
    """Modular wrapper for legacy AdminAttendanceTab."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._legacy = LegacyAdminAttendanceTab(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._legacy)

    def set_user_email(self, email: str):
        if hasattr(self._legacy, 'set_user_email'):
            return self._legacy.set_user_email(email)
