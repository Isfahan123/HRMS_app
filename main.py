# main.py
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QStackedWidget, QDesktopWidget, QWidget, QVBoxLayout, QLabel, QProgressBar, QMainWindow
)
from PyQt5.QtCore import QSettings, Qt, QCoreApplication
import time
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QSizePolicy
from gui.login_window import LoginWindow
from gui.dashboard_window import DashboardWindow
from gui.admin_dashboard_window import AdminDashboardWindow
try:
    # Best-effort import; if unavailable, app continues without startup reconcile
    from services.supabase_service import reconcile_employees_work_status_for_today
except Exception:
    reconcile_employees_work_status_for_today = None

class MainApp(QMainWindow):
    def __init__(self, progress_callback=None):
        # print("DEBUG: Starting MainApp.__init__")
        try:
            super().__init__()
            # Ensure this widget is a normal top-level window with standard
            # decorations so the user can resize it by dragging edges.
            try:
                # Prefer setWindowFlag where available to add the Window flag
                self.setWindowFlag(Qt.Window, True)
                # Show minimize/maximize buttons where supported
                self.setWindowFlag(Qt.WindowMinMaxButtonsHint, True)
            except Exception:
                # Fallback: ensure Window flag is present in windowFlags()
                try:
                    self.setWindowFlags(self.windowFlags() | Qt.Window)
                except Exception:
                    pass
            # print("DEBUG: QStackedWidget initialized")
            self.setWindowTitle("HRMS - Human Resources Management System")
            # Create an internal QStackedWidget that will be the central widget of the QMainWindow
            self._stack = QStackedWidget()
            self.setCentralWidget(self._stack)
            # Set a reasonable initial size and minimum size
            self.resize(900, 600)
            self.setMinimumSize(400, 300)
            # Center the window
            self.center_window()
            # print("DEBUG: Window properties set")
            
            # Using default PyQt5 styling

            # Track progress callback (call with integer 0..100)
            self._progress_cb = progress_callback

            def prog(p, msg=None):
                try:
                    if callable(self._progress_cb):
                        self._progress_cb(int(p), msg or '')
                except Exception:
                    pass

            # print("DEBUG: Initializing LoginWindow")
            # Keep passing self to child pages for compatibility; pages will be added to internal stack
            self.login_page = LoginWindow(self)
            prog(10, 'Login UI ready')

            # print("DEBUG: Initializing DashboardWindow")
            try:
                self.dashboard_page = DashboardWindow(self)
                prog(40, 'Dashboard ready')
            except Exception as e:
                print(f"DEBUG: Error initializing DashboardWindow: {str(e)}")
                self.dashboard_page = None

            # print("DEBUG: Initializing AdminDashboardWindow")
            try:
                self.admin_dashboard_page = AdminDashboardWindow(self)
                print("DEBUG: AdminDashboardWindow initialized successfully")
                prog(70, 'Admin dashboard ready')
            except Exception as e:
                print(f"DEBUG: Error initializing AdminDashboardWindow: {str(e)}")
                self.admin_dashboard_page = None
            # print("DEBUG: All pages initialized")

            # print("DEBUG: Adding widgets to stack")          
            # Add pages to the internal stack via compatibility wrapper
            self.addWidget(self.login_page)
            prog(85, 'Pages added')
            if self.dashboard_page:
                self.addWidget(self.dashboard_page)
            if self.admin_dashboard_page:
                self.addWidget(self.admin_dashboard_page)
            prog(95, 'Finalizing')
            # print("DEBUG: Widgets added")
        
            print("DEBUG: Setting current index to 0")
            self.setCurrentIndex(0)
            prog(100, 'Ready')
            print("DEBUG: MainApp initialization complete")
        except Exception as e:
            print(f"DEBUG: Error in MainApp.__init__: {str(e)}")
            raise

    def center_window(self):
        # Get the geometry of the screen
        screen_geometry = QDesktopWidget().availableGeometry()
        window_geometry = self.frameGeometry()
        # Calculate the center point
        center_point = screen_geometry.center()
        # Move the window to the center
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())  

    # Compatibility wrapper methods so external code that expects a QStackedWidget
    # API on MainApp continues to work.
    def addWidget(self, widget):
        return self._stack.addWidget(widget)

    def setCurrentIndex(self, index: int):
        return self._stack.setCurrentIndex(index)

    def currentIndex(self):
        return self._stack.currentIndex()

    def indexOf(self, widget):
        """Compatibility wrapper for QStackedWidget.indexOf"""
        try:
            return self._stack.indexOf(widget)
        except Exception:
            return -1

if __name__ == "__main__":
    print("DEBUG: Starting application")
    try:
        app = QApplication(sys.argv)
        print("DEBUG: QApplication created")
        # Create a simple splash widget with a progress bar
        class SplashWidget(QWidget):
            def __init__(self):
                super().__init__()
                self.setWindowFlags(Qt.SplashScreen | Qt.WindowStaysOnTopHint)
                self.resize(420, 220)
                layout = QVBoxLayout(self)
                title = QLabel('HRMS - Loading')
                title_font = QFont(); title_font.setPointSize(14); title_font.setBold(True)
                title.setFont(title_font)
                title.setAlignment(Qt.AlignCenter)
                layout.addWidget(title)
                self.progress = QProgressBar(self)
                self.progress.setRange(0, 100)
                self.progress.setValue(0)
                self.progress.setTextVisible(True)
                self.progress.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                layout.addWidget(self.progress)
                self.status = QLabel('Starting...')
                self.status.setAlignment(Qt.AlignCenter)
                layout.addWidget(self.status)

            def set_progress(self, value, message=''):
                try:
                    self.progress.setValue(int(value))
                    if message:
                        self.status.setText(message)
                except Exception:
                    pass

            def animate_to(self, target, message='', duration_ms=400):
                """Smoothly animate the progress bar from current value to target over duration_ms."""
                try:
                    start = int(self.progress.value())
                    target = int(max(0, min(100, target)))
                    if target <= start:
                        # immediate set for non-increasing values
                        self.set_progress(target, message)
                        return
                    # number of steps (~25ms per step)
                    step_ms = 25
                    steps = max(1, int(duration_ms / step_ms))
                    delta = (target - start) / steps
                    for i in range(steps):
                        val = start + delta * (i + 1)
                        self.progress.setValue(int(val))
                        if message:
                            self.status.setText(message)
                        QCoreApplication.processEvents()
                        time.sleep(step_ms / 1000.0)
                    # ensure exact target
                    self.progress.setValue(target)
                    if message:
                        self.status.setText(message)
                    QCoreApplication.processEvents()
                except Exception:
                    try:
                        self.set_progress(target, message)
                    except Exception:
                        pass

        splash = SplashWidget()
        splash.show()
        app.processEvents()

        # progress callback to update splash
        def progress_cb(pct, msg=''):
            try:
                # animate progress for a smooth experience
                try:
                    splash.animate_to(pct, msg, duration_ms=300)
                except Exception:
                    splash.set_progress(pct, msg)
                QCoreApplication.processEvents()
            except Exception:
                pass

        # Optional: Run a best-effort reconcile of employee work status before UI initializes
        try:
            if callable(reconcile_employees_work_status_for_today):
                splash.set_progress(5, 'Reconciling work status…')
                rec = reconcile_employees_work_status_for_today()
                print(f"DEBUG: Startup reconcile result: {rec}")
        except Exception as _e:
            print(f"DEBUG: Startup reconcile failed: {_e}")

        # Create main app with stacked widget approach and pass progress callback
        main_app = MainApp(progress_callback=progress_cb)

        # finalize
        try:
            splash.set_progress(100, 'Ready')
        except Exception:
            pass

        main_app.show()
        splash.close()

        sys.exit(app.exec_())
    except Exception as e:
        print(f"DEBUG: Fatal error in main.py: {str(e)}")