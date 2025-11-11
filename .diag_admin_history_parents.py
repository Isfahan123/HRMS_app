from PyQt5.QtWidgets import QApplication
from gui.admin_dashboard_window import AdminDashboardWindow
import traceback

app = QApplication([])
try:
    class Stub:
        def setCurrentIndex(self, i):
            pass
    win = AdminDashboardWindow(Stub())
    print('AdminDashboardWindow created; tab count=', win.tab_widget.count())
    idx = win.tab_widget.indexOf(win.employee_history_tab)
    print('history tab index:', idx)
    tab_widget_obj = win.tab_widget.widget(idx) if idx != -1 else None
    print('tab_widget.widget(idx) is win.employee_history_tab?', tab_widget_obj is win.employee_history_tab)
    print('type tab_widget_obj:', type(tab_widget_obj))
    print('win.employee_history_tab.__dict__ keys:', sorted(list(win.employee_history_tab.__dict__.keys())))
    print('\nChecking parent and visible for key attributes:')
    for name in ['tabs','job_title_combo','record_table','name_label','header_label','avatar_label','submit_btn','choose_emp_btn']:
        a = getattr(win.employee_history_tab, name, None)
        if a is None:
            print(name, '=> MISSING')
            continue
        try:
            parent = a.parent()
            ptype = type(parent).__name__ if parent else None
        except Exception as e:
            ptype = f'parent_err: {e}'
        try:
            vis = a.isVisible()
        except Exception as e:
            vis = f'vis_err: {e}'
        print(f"{name}: parent={ptype}, visible={vis}")
    print('\nTab widget children:', len(tab_widget_obj.children()) if tab_widget_obj else 'N/A')
    print('EmployeeHistoryTab children:', len(win.employee_history_tab.children()))
except Exception:
    print('ERROR in diag')
    traceback.print_exc()
finally:
    try:
        app.quit()
    except Exception:
        pass
print('diag done')
