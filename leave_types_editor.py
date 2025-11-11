from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QCheckBox, QLineEdit, QSpinBox, QDoubleSpinBox, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal

try:
    from services.supabase_leave_types import list_leave_types, create_leave_type, update_leave_type, delete_leave_type, clear_cache
except Exception:
    # Provide minimal fallbacks; editor will show an error if imports fail
    def list_leave_types(*args, **kwargs):
        return []
    def create_leave_type(*args, **kwargs):
        raise RuntimeError('leave_types service unavailable')
    def update_leave_type(*args, **kwargs):
        raise RuntimeError('leave_types service unavailable')
    def delete_leave_type(*args, **kwargs):
        raise RuntimeError('leave_types service unavailable')
    def clear_cache(*args, **kwargs):
        pass


class LeaveTypesEditor(QWidget):
    """Admin editor for dynamic leave types.

    Columns:
     - Active (checkbox)
     - Code (text, unique)
     - Name (text)
     - Deduct From (combo: annual/sick/unpaid/none)
     - Requires Doc (checkbox)
     - Default Duration (days, 0.5 granularity)
     - Max Duration (days, 0.5 granularity)
     - Description (text)
    """

    types_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('LeaveTypesEditor')
        self._records = []  # last loaded
        self._init_ui()
        self.reload()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        header.addWidget(QLabel('🧩 Leave Types Configuration'))
        header.addStretch()
        self.refresh_btn = QPushButton('Refresh')
        self.refresh_btn.clicked.connect(self.reload)
        header.addWidget(self.refresh_btn)
        self.add_btn = QPushButton('Add New')
        self.add_btn.clicked.connect(self.add_row)
        header.addWidget(self.add_btn)
        self.save_btn = QPushButton('Save Changes')
        self.save_btn.clicked.connect(self.save_changes)
        header.addWidget(self.save_btn)
        layout.addLayout(header)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            'Active', 'Code', 'Name', 'Deduct From', 'Requires Doc', 'Default Duration', 'Max Duration', 'Description'
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # Hint row
        hint = QLabel('Tip: Code must be unique. Deduct From controls which balance reduces when this type is approved.')
        hint.setStyleSheet('color:#666;')
        layout.addWidget(hint)

    def reload(self):
        try:
            clear_cache()
            self._records = list_leave_types(active_only=False, force_refresh=True) or []
        except Exception as e:
            self._records = []
            QMessageBox.critical(self, 'Error', f'Failed to load leave types: {e}')
        self._populate()

    def _populate(self):
        self.table.setRowCount(len(self._records))
        for r, rec in enumerate(self._records):
            # Active
            chk_active = QCheckBox()
            chk_active.setChecked(bool(rec.get('is_active', True)))
            self.table.setCellWidget(r, 0, chk_active)

            # Code
            code_edit = QLineEdit(rec.get('code',''))
            code_edit.setPlaceholderText('unique-code')
            self.table.setCellWidget(r, 1, code_edit)

            # Name
            name_edit = QLineEdit(rec.get('name',''))
            name_edit.setPlaceholderText('Display Name')
            self.table.setCellWidget(r, 2, name_edit)

            # Deduct From
            deduct_combo = QComboBox()
            deduct_combo.addItems(['annual','sick','unpaid','none'])
            idx = deduct_combo.findText(rec.get('deduct_from','annual'))
            deduct_combo.setCurrentIndex(max(0, idx))
            self.table.setCellWidget(r, 3, deduct_combo)

            # Requires Doc
            chk_doc = QCheckBox()
            chk_doc.setChecked(bool(rec.get('requires_document', False)))
            self.table.setCellWidget(r, 4, chk_doc)

            # Default Duration
            def_spin = QDoubleSpinBox()
            def_spin.setDecimals(1)
            def_spin.setSingleStep(0.5)
            def_spin.setRange(0.0, 365.0)
            v = rec.get('default_duration'); def_spin.setValue(float(v) if v is not None else 0.0)
            self.table.setCellWidget(r, 5, def_spin)

            # Max Duration
            max_spin = QDoubleSpinBox()
            max_spin.setDecimals(1)
            max_spin.setSingleStep(0.5)
            max_spin.setRange(0.0, 365.0)
            mv = rec.get('max_duration'); max_spin.setValue(float(mv) if mv is not None else 0.0)
            self.table.setCellWidget(r, 6, max_spin)

            # Description
            desc_edit = QLineEdit(rec.get('description','') or '')
            self.table.setCellWidget(r, 7, desc_edit)

            # Store original code in item data for matching on save
            item = QTableWidgetItem('')
            item.setData(Qt.UserRole, rec.get('code'))
            self.table.setItem(r, 0, item)  # attach to first column item slot

    def add_row(self):
        r = self.table.rowCount()
        self.table.insertRow(r)
        # default widgets like in populate
        chk_active = QCheckBox(); chk_active.setChecked(True); self.table.setCellWidget(r, 0, chk_active)
        self.table.setCellWidget(r, 1, QLineEdit(''))  # code
        self.table.setCellWidget(r, 2, QLineEdit(''))  # name
        deduct_combo = QComboBox(); deduct_combo.addItems(['annual','sick','unpaid','none']); self.table.setCellWidget(r, 3, deduct_combo)
        chk_doc = QCheckBox(); chk_doc.setChecked(False); self.table.setCellWidget(r, 4, chk_doc)
        def_spin = QDoubleSpinBox(); def_spin.setDecimals(1); def_spin.setSingleStep(0.5); def_spin.setRange(0.0, 365.0); def_spin.setValue(0.0); self.table.setCellWidget(r, 5, def_spin)
        max_spin = QDoubleSpinBox(); max_spin.setDecimals(1); max_spin.setSingleStep(0.5); max_spin.setRange(0.0, 365.0); max_spin.setValue(0.0); self.table.setCellWidget(r, 6, max_spin)
        self.table.setCellWidget(r, 7, QLineEdit(''))  # description
        # mark new row original code as None
        item = QTableWidgetItem('')
        item.setData(Qt.UserRole, None)
        self.table.setItem(r, 0, item)

    def _row_to_payload(self, r: int) -> dict:
        payload = {}
        payload['is_active'] = self.table.cellWidget(r, 0).isChecked()
        payload['code'] = self.table.cellWidget(r, 1).text().strip()
        payload['name'] = self.table.cellWidget(r, 2).text().strip()
        payload['deduct_from'] = self.table.cellWidget(r, 3).currentText()
        payload['requires_document'] = self.table.cellWidget(r, 4).isChecked()
        payload['default_duration'] = float(self.table.cellWidget(r, 5).value()) or None
        payload['max_duration'] = float(self.table.cellWidget(r, 6).value()) or None
        payload['description'] = self.table.cellWidget(r, 7).text().strip() or None
        return payload

    def save_changes(self):
        created, updated, errors = 0, 0, []
        for r in range(self.table.rowCount()):
            orig_code = None
            it = self.table.item(r, 0)
            if it is not None:
                orig_code = it.data(Qt.UserRole)
            payload = self._row_to_payload(r)

            # basic validation
            if not payload['code']:
                errors.append(f'Row {r+1}: code is required')
                continue
            if not payload['name']:
                errors.append(f'Row {r+1}: name is required')
                continue

            try:
                if orig_code:  # update existing
                    if update_leave_type(orig_code, payload):
                        updated += 1
                    else:
                        errors.append(f'Row {r+1}: failed to update')
                else:  # create new
                    create_leave_type(payload)
                    created += 1
            except Exception as e:
                errors.append(f'Row {r+1} ({payload.get("code")}): {e}')

        msg = f'Saved. Created: {created}, Updated: {updated}.'
        if errors:
            msg += f"\nErrors (first 5):\n- " + "\n- ".join(errors[:5])
            QMessageBox.warning(self, 'Save completed with issues', msg)
        else:
            QMessageBox.information(self, 'Saved', msg)
        # Reload and notify listeners so other tabs can refresh their combos
        self.reload()
        try:
            self.types_changed.emit()
        except Exception:
            pass
