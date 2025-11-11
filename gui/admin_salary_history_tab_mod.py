from PyQt5.QtWidgets import QWidget, QVBoxLayout
from gui.admin_salary_history_tab import AdminSalaryHistoryTab as LegacyAdminSalaryHistoryTab

class AdminSalaryHistoryTab(QWidget):
    """Modular wrapper for legacy AdminSalaryHistoryTab."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._legacy = LegacyAdminSalaryHistoryTab()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._legacy)

    # Expose signals/slots through wrapper if needed
    @property
    def salary_updated(self):
        return getattr(self._legacy, 'salary_updated', None)
