from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from gui.employee_history_tab import EmployeeHistoryTab

app = QApplication([])
w = EmployeeHistoryTab()
app.processEvents()

print('Main widget visible:', w.isVisible())
print('Tabs object:', repr(getattr(w,'tabs',None)))
try:
    print('Tabs count:', w.tabs.count())
    for i in range(w.tabs.count()):
        tab_w = w.tabs.widget(i)
        print(f' Tab {i} title={w.tabs.tabText(i)} widget_type={type(tab_w).__name__} children={len(tab_w.children())}')
except Exception as e:
    print('Tabs enumeration failed:', e)

print('\nTop-level children:')
for c in w.children():
    print(' -', type(c).__name__, 'objectName=', getattr(c,'objectName', lambda:None)())

print('\nAttributes and parent types:')
for name in ['job_title_combo','position_combo','department_combo','employment_type_combo','start_date_input','submit_btn','record_table','tabs','avatar_label','name_label','header_label','subtitle_label','choose_emp_btn','view_profile_btn','instruction_label']:
    attr = getattr(w, name, None)
    if attr is None:
        print(name, 'MISSING')
    else:
        parent = attr.parent()
        print(name, ' present; parent=', type(parent).__name__ if parent else None, '; visible=', attr.isVisible())

print('\nForm layout children (if any):')
try:
    # find a QFormLayout by scanning children
    from PyQt5.QtWidgets import QFormLayout
    form_layouts = [child for child in w.findChildren(QFormLayout)]
    print('found', len(form_layouts), 'QFormLayout(s)')
    for fl in form_layouts:
        print(' QFormLayout items:', fl.rowCount())
except Exception as e:
    print('form layout check failed:', e)

print('\nWidget tree dump:')

def dump(widget, indent=0):
    print(' ' * indent + f"{type(widget).__name__} (visible={widget.isVisible()})")
    for ch in widget.children():
        try:
            dump(ch, indent+2)
        except Exception:
            pass

dump(w)

print('\nDiag done')
app.quit()
