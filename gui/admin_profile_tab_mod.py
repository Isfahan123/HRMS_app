from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSignal
from gui.admin_profile_tab import AdminProfileTab as LegacyAdminProfileTab

class AdminProfileTab(QWidget):
    """
    Modular wrapper for the legacy AdminProfileTab so we can migrate
    sub-sections incrementally without breaking imports.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._legacy = LegacyAdminProfileTab(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._legacy)

        # Forward legacy signals so callers can connect to this wrapper
        try:
            if hasattr(self._legacy, 'employee_selected'):
                # create a local signal attribute and forward emits
                self.employee_selected = self._legacy.employee_selected
        except Exception:
            pass

    # Passthrough helpers used elsewhere (signals/slots)
    def refresh_employee_dialogs(self, employee_id: str):
        if hasattr(self._legacy, 'refresh_employee_dialogs'):
            return self._legacy.refresh_employee_dialogs(employee_id)

    def set_user_email(self, email: str):
        if hasattr(self._legacy, 'set_user_email'):
            return self._legacy.set_user_email(email)
