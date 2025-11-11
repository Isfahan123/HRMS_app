from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QMessageBox, QCalendarWidget, QListWidget, QCheckBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QTextCharFormat, QBrush, QColor
from datetime import date
from core.holidays_service import get_holidays_for_year
from services.supabase_service import (
    get_calendar_ui_prefs, upsert_calendar_ui_prefs,
    insert_calendar_holiday, find_calendar_holidays_for_year, find_calendar_holidays_by_date, delete_calendar_holiday_by_id
)
from services.supabase_service import update_calendar_holiday_by_id
from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QCheckBox
import subprocess
import sys

# Prefer centralized overrides helpers if available; otherwise provide a small
# JSON-backed fallback so the UI can work in offline/test environments and
# so editor/linters don't flag undefined names.
try:
    from core.holidays_service import add_override, remove_override
except Exception:
    import json, os

    _OVERRIDES_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'calendar_overrides.json'))

    def _ensure_overrides_file():
        d = os.path.dirname(_OVERRIDES_PATH)
        os.makedirs(d, exist_ok=True)
        if not os.path.exists(_OVERRIDES_PATH):
            try:
                with open(_OVERRIDES_PATH, 'w', encoding='utf-8') as fh:
                    json.dump([], fh)
            except Exception:
                pass

    def add_override(dt, reason):
        """Fallback: append an override record {date:ISO, reason} to local JSON file."""
        try:
            _ensure_overrides_file()
            with open(_OVERRIDES_PATH, 'r', encoding='utf-8') as fh:
                arr = json.load(fh) or []
        except Exception:
            arr = []
        try:
            rec = {'date': dt.isoformat() if hasattr(dt, 'isoformat') else str(dt), 'reason': reason}
            arr.append(rec)
            with open(_OVERRIDES_PATH, 'w', encoding='utf-8') as fh:
                json.dump(arr, fh, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def remove_override(dt):
        """Fallback: remove override(s) for the given date from local JSON file."""
        try:
            _ensure_overrides_file()
            with open(_OVERRIDES_PATH, 'r', encoding='utf-8') as fh:
                arr = json.load(fh) or []
        except Exception:
            return False
        try:
            iso = dt.isoformat() if hasattr(dt, 'isoformat') else str(dt)
            new = [r for r in arr if r.get('date') != iso]
            with open(_OVERRIDES_PATH, 'w', encoding='utf-8') as fh:
                json.dump(new, fh, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False


class CalendarTab(QWidget):
    """Month calendar view to inspect and manage holidays/overrides."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_year = date.today().year
        self.holidays = set()
        self.overrides = []
        self.init_ui()
        # Do not aggressively load holidays at import time; allow caller to create QApplication first.
        try:
            # Load saved prefs (global for now); apply to UI controls
            try:
                prefs = get_calendar_ui_prefs(None) or {}
                if prefs:
                    cy = prefs.get('year')
                    if cy:
                        self.current_year = int(cy)
                        self.year_combo.setCurrentText(str(cy))
                    st = prefs.get('state')
                    if st:
                        try:
                            self.state_combo.setCurrentText(st)
                        except Exception:
                            pass
                    show_nat = prefs.get('show_national')
                    if isinstance(show_nat, bool):
                        self.show_national_chk.setChecked(show_nat)
                    show_obs = prefs.get('show_observances')
                    if isinstance(show_obs, bool):
                        self.show_observances_chk.setChecked(show_obs)
            except Exception:
                pass
            # Ensure we pass the current state selection when initially loading so
            # saved prefs (state + show_national) are applied together.
            try:
                sel_state = self.state_combo.currentText()
                sel_state = None if (not sel_state or sel_state == 'All Malaysia') else sel_state
                self.load_year(self.current_year, state=sel_state)
            except Exception:
                self.load_year(self.current_year)
        except Exception:
            # Fail silently — Admin builders already catch initialization errors
            pass

    def init_ui(self):
        layout = QVBoxLayout()

        header = QHBoxLayout()
        header.addWidget(QLabel('Year:'))
        header.addWidget(QLabel('State:'))
        self.state_combo = QComboBox()
        states = ['All Malaysia', 'Johor', 'Kedah', 'Kelantan', 'Kuala Lumpur', 'Labuan', 'Malacca', 'Negeri Sembilan', 'Pahang', 'Penang', 'Perak', 'Perlis', 'Sabah', 'Sarawak', 'Selangor', 'Terengganu']
        for s in states:
            self.state_combo.addItem(s)
        self.state_combo.setCurrentText('All Malaysia')
        self.state_combo.currentTextChanged.connect(self.on_state_changed)
        header.addWidget(self.state_combo)
        self.year_combo = QComboBox()
        cy = date.today().year
        for y in range(cy - 3, cy + 4):
            self.year_combo.addItem(str(y))
        self.year_combo.setCurrentText(str(cy))
        self.year_combo.currentTextChanged.connect(self.on_year_changed)
        header.addWidget(self.year_combo)

        self.prev_month_btn = QPushButton('◀')
        self.next_month_btn = QPushButton('▶')
        self.prev_month_btn.clicked.connect(self.prev_month)
        self.next_month_btn.clicked.connect(self.next_month)
        header.addWidget(self.prev_month_btn)
        header.addWidget(self.next_month_btn)

        layout.addLayout(header)
        # Toggle controls for what to display
        toggles_row = QHBoxLayout()
        self.show_national_chk = QCheckBox('Show national holidays')
        self.show_national_chk.setChecked(True)
        self.show_observances_chk = QCheckBox('Show observances')
        self.show_observances_chk.setChecked(False)
        self.show_national_chk.stateChanged.connect(lambda _: self.load_year(self.current_year, state=self.state_combo.currentText()))
        self.show_observances_chk.stateChanged.connect(lambda _: self.load_year(self.current_year, state=self.state_combo.currentText()))
        # Save prefs when controls change
        self.year_combo.currentTextChanged.connect(self.save_prefs)
        self.state_combo.currentTextChanged.connect(self.save_prefs)
        self.show_national_chk.stateChanged.connect(lambda _: self.save_prefs())
        self.show_observances_chk.stateChanged.connect(lambda _: self.save_prefs())
        toggles_row.addWidget(self.show_national_chk)
        toggles_row.addWidget(self.show_observances_chk)
        layout.addLayout(toggles_row)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.selectionChanged.connect(self.on_selection_changed)
        # update holiday list when user navigates months
        try:
            self.calendar.currentPageChanged.connect(self.on_page_changed)
        except Exception:
            pass
        layout.addWidget(self.calendar)

        # Abbreviations legend (short code -> full name) shown below calendar
        # Build legend text from services.holidays_service.STATE_ABBREV
        try:
            from core.holidays_service import STATE_ABBREV
            # HTML legend with bold/colored abbreviations for readability
            parts_html = [f"<b><span style='color:#0B5394'>{v}</span></b>: {k}" for k, v in STATE_ABBREV.items()]
            legend_html = ' &nbsp; '.join(parts_html)
            # Plain text tooltip for the legend
            legend_tooltip = '\n'.join([f"{v}: {k}" for k, v in STATE_ABBREV.items()])
        except Exception:
            legend_html = ''
            legend_tooltip = ''
        self.abbrev_legend = QLabel(legend_html)
        self.abbrev_legend.setTextFormat(Qt.RichText)
        self.abbrev_legend.setToolTip(legend_tooltip)
        layout.addWidget(self.abbrev_legend)

        # Right below the calendar show a list of holidays for the visible month
        self.holiday_list = QListWidget()
        layout.addWidget(QLabel('Holidays in view:'))
        layout.addWidget(self.holiday_list)
        # action buttons for editing DB calendar_holidays
        action_row = QHBoxLayout()
        self.add_override_btn = QPushButton('Add Selected')
        self.add_override_btn.clicked.connect(self.add_override_dialog)
        action_row.addWidget(self.add_override_btn)

        self.edit_override_btn = QPushButton('Edit Selected')
        self.edit_override_btn.clicked.connect(self.edit_selected)
        action_row.addWidget(self.edit_override_btn)
        layout.addLayout(action_row)

        self.setLayout(layout)

    def load_year(self, year: int, state: str = None):
        try:
            self.current_year = int(year)
            # Collect holidays with optional names/sources to make mismatches visible
            details = {}

            # Use centralized holidays service (Calendarific + overrides)
            try:
                include_national = True
                include_observances = True
                try:
                    include_national = bool(self.show_national_chk.isChecked())
                    include_observances = bool(self.show_observances_chk.isChecked())
                except Exception:
                    pass
                res = get_holidays_for_year(self.current_year, state=None if (not state or state=='All Malaysia') else state, include_national=include_national, include_observances=include_observances)
                if isinstance(res, tuple) or isinstance(res, list):
                    hs, det = res
                else:
                    hs, det = res, {}
                # normalize hs to a set of date objects
                self.holidays = set(hs)
                # convert det keys (ISO strings) to date objects
                holiday_details = {}
                for k, v in (det or {}).items():
                    try:
                        dd = date.fromisoformat(k)
                        holiday_details[dd] = v
                    except Exception:
                        continue
                self.holiday_details = holiday_details
            except Exception:
                # fallback to no holidays
                self.holidays = set()
                self.holiday_details = {}
            # DB-managed overrides (admin-managed) -- optional; fetch but do not fall back to file overrides
            try:
                db_rows = find_calendar_holidays_for_year(self.current_year, state=None if self.state_combo.currentText()=='All Malaysia' else self.state_combo.currentText())
                self.overrides = []
                for r in db_rows:
                    try:
                        self.overrides.append({
                            'date': r.get('date'),
                            'reason': r.get('name'),
                            'id': r.get('id')
                        })
                    except Exception:
                        continue
            except Exception:
                self.overrides = []
            self.refresh_calendar()
            # ensure the holiday list matches the currently visible month
            self.update_holiday_list_for_visible_month()
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to load holidays for {year}: {e}')

    def refresh_calendar(self):
        # Clear formats
        fmt_default = QTextCharFormat()
        start = QDate(self.current_year, 1, 1)
        end = QDate(self.current_year, 12, 31)
        d = start
        while d <= end:
            self.calendar.setDateTextFormat(d, fmt_default)
            d = d.addDays(1)

        # Highlight public holidays and set per-date tooltips containing holiday names + legend
        from core.holidays_service import STATE_ABBREV
        rev_abbrev = {v: k for k, v in STATE_ABBREV.items()}
        for d in self.holidays:
            try:
                names = self.holiday_details.get(d, [])
                qd = QDate(d.year, d.month, d.day)
                fmt = QTextCharFormat()
                fmt.setBackground(QBrush(QColor('#FFDDDD')))
                # build plain-text tooltip: holiday names then legend of codes used on this date
                tooltip_lines = []
                if names:
                    tooltip_lines.append('Holidays:')
                    for nm in names:
                        tooltip_lines.append(f" - {nm}")
                # collect any codes inside brackets [CODE, ...]
                try:
                    import re
                    codes = set()
                    for nm in names:
                        m = re.search(r"\[(.*?)\]", nm)
                        if m:
                            parts = [p.strip() for p in m.group(1).split(',')]
                            for p in parts:
                                if p:
                                    codes.add(p)
                    if codes:
                        tooltip_lines.append('')
                        tooltip_lines.append('Legend:')
                        for c in sorted(codes):
                            full = rev_abbrev.get(c)
                            if full:
                                tooltip_lines.append(f" {c}: {full}")
                            else:
                                tooltip_lines.append(f" {c}")
                except Exception:
                    pass

                if tooltip_lines:
                    fmt.setToolTip('\n'.join(tooltip_lines))

                self.calendar.setDateTextFormat(qd, fmt)
            except Exception:
                continue

        # Highlight overrides differently (DB-managed) and add tooltip for override reason
        override_fmt_base = QTextCharFormat()
        override_fmt_base.setBackground(QBrush(QColor('#DDFFDD')))
        for ov in self.overrides:
            try:
                dd = date.fromisoformat(ov['date'])
                qd = QDate(dd.year, dd.month, dd.day)
                fmt = QTextCharFormat(override_fmt_base)
                reason = ov.get('reason') or ''
                if reason:
                    fmt.setToolTip(f"Override: {reason}")
                self.calendar.setDateTextFormat(qd, fmt)
            except Exception:
                continue

    def on_page_changed(self, year, month):
        # Called when user changes the month/year in the calendar
        try:
            self.update_holiday_list_for_visible_month()
        except Exception:
            pass

    def update_holiday_list_for_visible_month(self):
        # Populate the side list with holidays in the calendar's visible month
        try:
            vy = self.calendar.yearShown()
            vm = self.calendar.monthShown()
        except Exception:
            # fallback to current_year and selectedDate
            sel = self.calendar.selectedDate()
            vy, vm = sel.year(), sel.month()

        self.holiday_list.clear()
        displayed_dates = set()

        # Add standard holidays (from holidays_service details)
        for d in sorted(self.holidays):
            if d.year == vy and d.month == vm:
                names = self.holiday_details.get(d, [])
                if names:
                    item_text = f"{d.isoformat()} — {', '.join(names)}"
                    self.holiday_list.addItem(item_text)
                    displayed_dates.add(d.isoformat())
                    # Create tooltip mapping short codes -> full names for the item
                    try:
                        import re
                        from core.holidays_service import STATE_ABBREV
                        rev = {v: k for k, v in STATE_ABBREV.items()}
                        codes = set()
                        for nm in names:
                            m = re.search(r"\[(.*?)\]", nm)
                            if m:
                                parts = [p.strip() for p in m.group(1).split(',')]
                                for p in parts:
                                    if p:
                                        codes.add(p)
                        if codes:
                            lines = []
                            for c in sorted(codes):
                                full = rev.get(c, None)
                                if full:
                                    lines.append(f"{c}: {full}")
                                else:
                                    lines.append(f"{c}")
                            tip = '\n'.join(lines)
                            last = self.holiday_list.item(self.holiday_list.count() - 1)
                            if last is not None:
                                last.setToolTip(tip)
                    except Exception:
                        pass
                else:
                    self.holiday_list.addItem(d.isoformat())
                    displayed_dates.add(d.isoformat())

        # Include DB-managed overrides (admin-managed) in the side list as well
        try:
            for ov in self.overrides:
                try:
                    dd = date.fromisoformat(ov.get('date'))
                    if dd.year == vy and dd.month == vm:
                        iso = dd.isoformat()
                        # Avoid duplicate lines if same date already listed
                        if iso in displayed_dates:
                            continue
                        reason = ov.get('reason') or ov.get('name') or 'Override'
                        item_text = f"{iso} — Override: {reason}"
                        self.holiday_list.addItem(item_text)
                        displayed_dates.add(iso)
                except Exception:
                    continue
        except Exception:
            pass

    def on_year_changed(self, txt):
        try:
            self.load_year(int(txt))
            self.save_prefs()
        except Exception:
            pass

    def on_state_changed(self, txt):
        try:
            state = txt
            if state == 'All Malaysia':
                state = None
            self.load_year(self.current_year, state=state)
            self.save_prefs()
        except Exception:
            pass

    def save_prefs(self):
        try:
            prefs = {
                'year': int(self.year_combo.currentText()),
                'state': self.state_combo.currentText(),
                'show_national': bool(self.show_national_chk.isChecked()),
                'show_observances': bool(self.show_observances_chk.isChecked())
            }
            # Best-effort write; ignore result
            try:
                upsert_calendar_ui_prefs(prefs, None)
            except Exception:
                pass
        except Exception:
            pass

    def on_selection_changed(self):
        sel = self.calendar.selectedDate()
        # could show details in a status bar; for now, do nothing
        return

    def add_override_for_selected(self):
        sel = self.calendar.selectedDate()
        dt = date(sel.year(), sel.month(), sel.day())
        reason = 'manual override'
        try:
            # Insert into calendar_holidays as an admin-managed override (source='admin')
            # set state to None for global override; UI allows per-state selection later
            s = None if self.state_combo.currentText() == 'All Malaysia' else self.state_combo.currentText()
            ok = insert_calendar_holiday(dt.isoformat(), reason, state=s, is_national=False, is_observance=False, created_by=None)
            if not ok:
                # fallback to local override file
                add_override(dt, reason)
            else:
                try:
                    qd = QDate(dt.year, dt.month, dt.day)
                    self.calendar.setSelectedDate(qd)
                    self.calendar.showSelectedDate()
                except Exception:
                    pass
            self.load_year(self.current_year)
            QMessageBox.information(self, 'Added', f'Override added for {dt.isoformat()}')
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to add override: {e}')

    def add_override_dialog(self):
        """Show a dialog to manually add a holiday/override for the selected date."""
        sel = self.calendar.selectedDate()
        dt = date(sel.year(), sel.month(), sel.day())
        dlg = QDialog(self)
        dlg.setWindowTitle(f'Add Holiday for {dt.isoformat()}')
        form = QFormLayout(dlg)
        name_edit = QLineEdit('')
        state_edit = QLineEdit('')
        is_nat_chk = QCheckBox('Is national')
        is_obs_chk = QCheckBox('Is observance')
        form.addRow('Name:', name_edit)
        form.addRow('State (empty=All):', state_edit)
        form.addRow(is_nat_chk)
        form.addRow(is_obs_chk)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        form.addRow(buttons)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)

        if dlg.exec_() == QDialog.Accepted:
            name = name_edit.text().strip() or 'manual override'
            state = state_edit.text().strip() or None
            is_nat = bool(is_nat_chk.isChecked())
            is_obs = bool(is_obs_chk.isChecked())
            try:
                ok = insert_calendar_holiday(dt.isoformat(), name, state=state, is_national=is_nat, is_observance=is_obs, created_by=None)
                if ok:
                    try:
                        qd = QDate(dt.year, dt.month, dt.day)
                        self.calendar.setSelectedDate(qd)
                        self.calendar.showSelectedDate()
                    except Exception:
                        pass
                    QMessageBox.information(self, 'Added', f'Holiday added for {dt.isoformat()}')
                else:
                    QMessageBox.warning(self, 'Failed', 'Insert did not return success.')
            except Exception as e:
                QMessageBox.warning(self, 'Error', f'Failed to add holiday: {e}')
            try:
                self.load_year(self.current_year)
            except Exception:
                pass

    def remove_override_for_selected(self):
        sel = self.calendar.selectedDate()
        dt = date(sel.year(), sel.month(), sel.day())
        try:
            # Try to remove DB-managed rows for this date first
            try:
                rows = find_calendar_holidays_by_date(dt.isoformat(), state=None if self.state_combo.currentText()=='All Malaysia' else self.state_combo.currentText())
                removed = False
                for r in rows:
                    # Prefer deleting rows created by admin/source null; do not delete external Calendarific-imported rows unless they were marked 'admin'
                    try:
                        src = r.get('source')
                        rid = r.get('id')
                        if src in (None, 'admin'):
                            if delete_calendar_holiday_by_id(rid):
                                removed = True
                    except Exception:
                        continue
                if not removed:
                    # fallback to file-based removal
                    remove_override(dt)
            except Exception:
                # fallback to file-based removal
                remove_override(dt)
            self.load_year(self.current_year)
            QMessageBox.information(self, 'Removed', f'Override removed for {dt.isoformat()}')
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to remove override: {e}')

    def _get_selected_override_row(self):
        """Return the DB row dict for the selected date if available (first match), else None."""
        sel = self.calendar.selectedDate()
        dt = date(sel.year(), sel.month(), sel.day())
        try:
            rows = find_calendar_holidays_by_date(dt.isoformat(), state=None if self.state_combo.currentText()=='All Malaysia' else self.state_combo.currentText())
            if rows:
                return rows[0]
        except Exception:
            pass
        return None

    def edit_selected(self):
        row = self._get_selected_override_row()
        if not row:
            QMessageBox.information(self, 'Edit', 'No DB-managed override found for selected date to edit.')
            return
        # Build a simple edit dialog
        dlg = QDialog(self)
        dlg.setWindowTitle('Edit Holiday')
        form = QFormLayout(dlg)
        name_edit = QLineEdit(row.get('name') or '')
        state_edit = QLineEdit(row.get('state') or '')
        is_nat_chk = QCheckBox('Is national')
        is_nat_chk.setChecked(bool(row.get('is_national')))
        is_obs_chk = QCheckBox('Is observance')
        is_obs_chk.setChecked(bool(row.get('is_observance')))
        form.addRow('Name:', name_edit)
        form.addRow('State (empty=All):', state_edit)
        form.addRow(is_nat_chk)
        form.addRow(is_obs_chk)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        form.addRow(buttons)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        if dlg.exec_() == QDialog.Accepted:
            # collect fields and call updater
            new_name = name_edit.text().strip()
            new_state = state_edit.text().strip() or None
            new_fields = {
                'name': new_name,
                'state': new_state,
                'is_national': bool(is_nat_chk.isChecked()),
                'is_observance': bool(is_obs_chk.isChecked()),
                'updated_at': None
            }
            # remove None values to avoid accidental overwrites
            payload = {k: v for k, v in new_fields.items() if v is not None}
            try:
                if update_calendar_holiday_by_id(row.get('id'), payload):
                    QMessageBox.information(self, 'Updated', 'Holiday updated.')
                else:
                    QMessageBox.warning(self, 'Failed', 'Update did not succeed.')
            except Exception as e:
                QMessageBox.warning(self, 'Error', f'Failed to update holiday: {e}')
            self.load_year(self.current_year)

    def prev_month(self):
        cur = self.calendar.selectedDate()
        prev = cur.addMonths(-1)
        self.calendar.setSelectedDate(prev)
        self.calendar.showSelectedDate()

    def next_month(self):
        cur = self.calendar.selectedDate()
        nxt = cur.addMonths(1)
        self.calendar.setSelectedDate(nxt)
        self.calendar.showSelectedDate()

    def open_tkcalendar(self):
        QMessageBox.information(self, 'Unavailable', 'tkcalendar support has been removed from this build.')
