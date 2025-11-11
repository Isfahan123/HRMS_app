from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from gui.employee_history_tab import EmployeeHistoryTab

app = QApplication([])
w = EmployeeHistoryTab()
# show briefly to allow any layout computations
w.show()
app.processEvents()

def dump_state(widget):
    print('== Widget state for EmployeeHistoryTab ==')
    print('visible:', widget.isVisible())
    print('size:', widget.size())
    print('layout:', type(widget.layout()).__name__ if widget.layout() else None)
    try:
        print('layout count:', widget.layout().count())
    except Exception:
        print('layout count: ?')
    # important sub-widgets
    for name in ['job_title_combo','position_combo','department_combo','employment_type_combo','start_date_input','submit_btn','record_table','tabs','avatar_label','name_label']:
        attr = getattr(widget, name, None)
        print(f"{name}:", 'present' if attr is not None else 'MISSING', end='')
        if attr is not None:
            try:
                print(', visible=', attr.isVisible(), ', parent=', type(attr.parent()).__name__ if attr.parent() else None)
            except Exception:
                print()
        else:
            print()

# dump layout children names
try:
    print('\nLayout children:')
    for i in range(w.layout().count()):
        item = w.layout().itemAt(i)
        print(' -', type(item).__name__, getattr(item, '__class__', ''))
except Exception as e:
    print('failed to enumerate layout children:', e)

# dump tabs
try:
    print('\nTabs count:', w.tabs.count())
    for i in range(w.tabs.count()):
        print(' Tab', i, 'title=', w.tabs.tabText(i))
except Exception:
    pass

# dump form layout if accessible
try:
    # find job title combo's parent layout
    jt = w.job_title_combo
    parent = jt.parent()
    print('\njob_title_combo parent:', type(parent).__name__)
except Exception:
    pass

# exit
QTimer.singleShot(100, app.quit)
app.exec_()
print('diag done')
