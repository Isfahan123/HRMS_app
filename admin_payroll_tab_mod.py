from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSignal
from gui.admin_payroll_tab import AdminPayrollTab as LegacyAdminPayrollTab

class AdminPayrollTab(QWidget):
    """Modular wrapper for legacy AdminPayrollTab."""
    # Mirror the legacy signal so external dialogs can connect reliably
    max_cap_changed = pyqtSignal(str, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._legacy = LegacyAdminPayrollTab(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._legacy)

        # If legacy has the signal, bridge it
        if hasattr(self._legacy, 'max_cap_changed'):
            try:
                self._legacy.max_cap_changed.connect(self.max_cap_changed.emit)
            except Exception:
                pass

    def set_user_email(self, email: str):
        if hasattr(self._legacy, 'set_user_email'):
            return self._legacy.set_user_email(email)

    def __getattr__(self, name):
        # Fallback: proxy attribute access to the legacy instance
        # Prevent recursion for special attributes
        if name in ('_legacy', 'max_cap_changed'):
            raise AttributeError
        return getattr(self._legacy, name)
