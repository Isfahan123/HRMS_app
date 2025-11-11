import sys
from PyQt5.QtWidgets import QApplication, QPushButton

def main():
    app = QApplication([])
    try:
        from gui.admin_dashboard_window import AdminDashboardWindow
        w = AdminDashboardWindow(None)
        btns = w.findChildren(QPushButton)
        labels = [b.text() for b in btns]
        print('BUTTONS:', labels)
        print('HAS_OPEN_CALENDAR:', any('Open Calendar' == t or 'Calendar / Holidays' == t or 'Open Calendar' in t for t in labels))
        # cleanup
        w.deleteLater()
    except Exception as e:
        print('ERROR:', e)
    finally:
        app.quit()

if __name__ == '__main__':
    main()
