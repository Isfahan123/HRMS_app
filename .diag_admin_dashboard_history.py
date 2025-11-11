from PyQt5.QtWidgets import QApplication
from gui.admin_dashboard_window import AdminDashboardWindow
import traceback

app = QApplication([])
win = None
try:
    # stacked_widget stub
    class Stub:
        def setCurrentIndex(self, i):
            pass
    win = AdminDashboardWindow(Stub())
    print('AdminDashboardWindow created')
    print('tab count:', win.tab_widget.count())
    idx = win.tab_widget.indexOf(win.employee_history_tab)
    print('history tab index:', idx)
    if idx != -1:
        print('current tab text:', win.tab_widget.tabText(idx))
        hist_w = win.employee_history_tab
        print('history widget children count:', len(hist_w.children()))
        print('has record_table:', hasattr(hist_w,'record_table'))
        try:
            print('record_table visible:', hist_w.record_table.isVisible())
        except Exception:
            pass
except Exception:
    print('ERROR instantiating AdminDashboardWindow')
    traceback.print_exc()
finally:
    try:
        app.quit()
    except Exception:
        pass
print('diag done')
