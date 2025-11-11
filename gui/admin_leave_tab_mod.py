from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from typing import Optional

# Reuse existing, already-separated widgets
from gui.pending_requests import PendingLeaveRequestsWidget
from gui.history import LeaveHistoryWidget
from gui.annual_balance import AnnualBalanceWidget
from gui.sick_balance import SickBalanceWidget
from gui.submit_request import SubmitRequestWidget
try:
    from gui.calendar_tab import CalendarTab
except Exception as e:
    CalendarTab = None
    print(f"DEBUG: AdminLeaveTab - failed to import CalendarTab: {e}")

# New leave caps editor
try:
    from gui.leave_caps_editor import LeaveCapsEditor
except Exception as e:
    LeaveCapsEditor = None
    print(f"DEBUG: AdminLeaveTab - failed to import LeaveCapsEditor: {e}")

# Combined policy editor (types + caps)
try:
    from gui.leave_policy_editor import LeavePolicyEditor
except Exception as e:
    LeavePolicyEditor = None
    print(f"DEBUG: AdminLeaveTab - failed to import LeavePolicyEditor: {e}")

# Unpaid leave specialized tab
try:
    from gui.admin_unpaid_leave_tab import AdminUnpaidLeaveTab
except Exception:
    AdminUnpaidLeaveTab = None

class AdminLeaveTab(QWidget):
    """Modular Admin Leave Tab composed from smaller widgets.
    Tabs:
      - Pending (PendingLeaveRequestsWidget)
      - Approved/Rejected (LeaveHistoryWidget)
      - Submit Leave Request (SubmitRequestWidget)
      - Annual Leave Balance (AnnualBalanceWidget)
      - Sick Leave Balance (SickBalanceWidget)
      - Unpaid Leave (AdminUnpaidLeaveTab, if available)
    """
    def __init__(self, parent: Optional[QWidget] = None, admin_email: Optional[str] = None) -> None:
        super().__init__(parent)
        self.current_admin_email = admin_email or "admin@example.com"
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Pending
        self.pending_widget = PendingLeaveRequestsWidget(self, admin_email=self.current_admin_email)
        self.tab_widget.addTab(self.pending_widget, "Pending")

        # Approved/Rejected (History)
        self.history_widget = LeaveHistoryWidget(self)
        self.tab_widget.addTab(self.history_widget, "Approved/Rejected")

        # Submit Leave Request (Admin)
        self.submit_widget = SubmitRequestWidget(self, admin_email=self.current_admin_email)
        self.tab_widget.addTab(self.submit_widget, "Submit Leave Request")

        # Annual Leave Balance
        self.annual_balance_widget = AnnualBalanceWidget(self)
        self.tab_widget.addTab(self.annual_balance_widget, "Annual Leave Balance")

        # Sick Leave Balance
        self.sick_balance_widget = SickBalanceWidget(self)
        self.tab_widget.addTab(self.sick_balance_widget, "Sick Leave Balance")

        # Unpaid Leave (optional)
        if AdminUnpaidLeaveTab is not None:
            try:
                self.unpaid_leave_widget = AdminUnpaidLeaveTab()
                self.tab_widget.addTab(self.unpaid_leave_widget, "\U0001F4CA Unpaid Leave")
            except Exception:
                pass

        # Calendar / Holidays management tab (optional)
        if CalendarTab is not None:
            try:
                self.calendar_widget = CalendarTab(self)
                self.tab_widget.addTab(self.calendar_widget, "Calendar / Holidays")
                print('DEBUG: Calendar / Holidays tab added to AdminLeaveTab')
            except Exception as e:
                print(f"DEBUG: AdminLeaveTab - failed to initialize CalendarTab instance: {e}")
        else:
            # Create a disabled placeholder tab so the UI still shows a Calendar tab
            try:
                placeholder = QWidget()
                self.tab_widget.addTab(placeholder, "Calendar / Holidays (Unavailable)")
            except Exception:
                pass

        # Leave Policy (combined Types + Caps)
        if LeavePolicyEditor is not None:
            try:
                self.leave_policy_widget = LeavePolicyEditor(self)
                self.tab_widget.addTab(self.leave_policy_widget, "Leave Policy")
                # Hook signals to keep submit widget in sync
                try:
                    self.leave_policy_widget.types_changed.connect(self._on_leave_types_changed)
                except Exception:
                    pass
            except Exception as e:
                print(f"DEBUG: AdminLeaveTab - failed to initialize LeavePolicyEditor: {e}")

        # Lightweight cross-tab refresh hooks
        try:
            # When a request is approved/rejected, refresh history and balances
            if hasattr(self.pending_widget, 'request_updated'):
                self.pending_widget.request_updated.connect(self._on_requests_changed)
            # When admin submits a request, refresh pending/history too
            if hasattr(self.submit_widget, 'request_submitted'):
                self.submit_widget.request_submitted.connect(self._on_requests_changed)
        except Exception:
            pass

    def _on_requests_changed(self, *_):
        try:
            if hasattr(self.history_widget, 'refresh_data'):
                self.history_widget.refresh_data()
            if hasattr(self.pending_widget, 'load_requests'):
                self.pending_widget.load_requests()
        except Exception:
            pass

    def set_admin_email(self, admin_email):
        """Update the admin email for all components"""
        self.current_admin_email = admin_email or "admin@example.com"
        if hasattr(self.pending_widget, 'admin_email'):
            self.pending_widget.admin_email = self.current_admin_email
        if hasattr(self.submit_widget, 'admin_email'):
            self.submit_widget.admin_email = self.current_admin_email

    def _on_leave_types_changed(self, *_):
        try:
            if hasattr(self.submit_widget, '_populate_leave_types_dynamic'):
                # Ask submit widget to re-fetch active leave types and refresh UI
                self.submit_widget._populate_leave_types_dynamic()
        except Exception:
            pass
