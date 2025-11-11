from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QCheckBox, QLineEdit, QSpinBox, QDoubleSpinBox, QMessageBox, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal

# Import existing services
try:
    from services.leave_caps_service import get_leave_caps, save_to_supabase as save_caps_to_db
except Exception:
    def get_leave_caps():
        return {}
    def save_caps_to_db(data):
        return False

try:
    from services.supabase_leave_types import list_leave_types, create_leave_type, update_leave_type, delete_leave_type, clear_cache as clear_types_cache
except Exception:
    def list_leave_types(*a, **k): return []
    def create_leave_type(*a, **k): raise RuntimeError('leave_types unavailable')
    def update_leave_type(*a, **k): return False
    def delete_leave_type(*a, **k): return False
    def clear_types_cache(): pass

class LeavePolicyEditor(QWidget):
    """Combined editor for Leave Types & Leave Caps in a single tab.

    Left pane: Leave Types configuration (CRUD, activation, metadata).
    Right pane: Caps per years-of-service tiers referencing leave type codes.

    Emits signals when types or caps are changed so other widgets can refresh combos/balances.
    """
    types_changed = pyqtSignal()
    caps_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('LeavePolicyEditor')
        self._types = []
        self._caps_data = get_leave_caps() or {}
        self._tiers = self._caps_data.get('tiers', [])
        self._caps = self._caps_data.get('caps', {})
        self._init_ui()
        self.reload_all()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        header.addWidget(QLabel('🛠️ Leave Policy Configuration'))
        header.addStretch()
        self.refresh_all_btn = QPushButton('Refresh All')
        self.refresh_all_btn.clicked.connect(self.reload_all)
        header.addWidget(self.refresh_all_btn)
        layout.addLayout(header)

        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # LEFT: Leave Types
        left = QWidget(); left_layout = QVBoxLayout(left)
        lt_header = QHBoxLayout()
        lt_header.addWidget(QLabel('🧩 Leave Types'))
        lt_header.addStretch()
        self.types_add_btn = QPushButton('Add Type')
        self.types_add_btn.clicked.connect(self.add_type_row)
        lt_header.addWidget(self.types_add_btn)
        self.types_save_btn = QPushButton('Save Types')
        self.types_save_btn.clicked.connect(self.save_types)
        lt_header.addWidget(self.types_save_btn)
        self.types_delete_btn = QPushButton('Delete Selected')
        self.types_delete_btn.setToolTip('Delete highlighted leave type(s)')
        self.types_delete_btn.clicked.connect(self.delete_selected_types)
        lt_header.addWidget(self.types_delete_btn)
        left_layout.addLayout(lt_header)

        self.types_table = QTableWidget()
        self.types_table.setColumnCount(9)
        self.types_table.setHorizontalHeaderLabels([
            'Active','Code','Name','Deduct From','Requires Doc','Default Dur','Max Dur','Description','Actions'
        ])
        self.types_table.horizontalHeader().setStretchLastSection(True)
        left_layout.addWidget(self.types_table)

        # RIGHT: Leave Caps
        right = QWidget(); right_layout = QVBoxLayout(right)
        lc_header = QHBoxLayout()
        lc_header.addWidget(QLabel('📊 Leave Caps (Years-of-Service Tiers)'))
        lc_header.addStretch()
        self.caps_tier_combo = QComboBox(); self.caps_tier_combo.currentIndexChanged.connect(self._populate_caps_table)
        lc_header.addWidget(QLabel('Tier:'))
        lc_header.addWidget(self.caps_tier_combo)
        self.caps_save_btn = QPushButton('Save Caps')
        self.caps_save_btn.clicked.connect(self.save_caps)
        lc_header.addWidget(self.caps_save_btn)
        right_layout.addLayout(lc_header)

        self.caps_table = QTableWidget()
        self.caps_table.setColumnCount(3)
        self.caps_table.setHorizontalHeaderLabels(['Leave Type Code','Cap (days)','Actions'])
        self.caps_table.horizontalHeader().setStretchLastSection(True)
        right_layout.addWidget(self.caps_table)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0,2)
        splitter.setStretchFactor(1,1)

        # Footer hint
        hint = QLabel('Hint: Caps reference leave type codes. Edit types on left; assign per-tier caps on right.')
        hint.setStyleSheet('color:#666;')
        layout.addWidget(hint)

    # ---- RELOAD ----
    def reload_all(self):
        self.reload_types()
        self.reload_caps()

    def reload_types(self):
        try:
            clear_types_cache()
            self._types = list_leave_types(active_only=False, force_refresh=True) or []
        except Exception:
            self._types = []
        self._populate_types_table()
        try:
            self.types_changed.emit()
        except Exception:
            pass

    def reload_caps(self):
        self._caps_data = get_leave_caps() or {}
        self._tiers = self._caps_data.get('tiers', [])
        self._caps = self._caps_data.get('caps', {})
        self.caps_tier_combo.blockSignals(True)
        self.caps_tier_combo.clear()
        for t in self._tiers:
            self.caps_tier_combo.addItem(t.get('label', t.get('id')), userData=t.get('id'))
        self.caps_tier_combo.blockSignals(False)
        self._populate_caps_table()
        try:
            self.caps_changed.emit()
        except Exception:
            pass

    # ---- TYPES TABLE ----
    def _populate_types_table(self):
        self.types_table.setRowCount(len(self._types))
        for r, rec in enumerate(self._types):
            # Active
            chk = QCheckBox(); chk.setChecked(bool(rec.get('is_active', True)))
            self.types_table.setCellWidget(r,0,chk)
            # Code
            code = QLineEdit(rec.get('code',''))
            self.types_table.setCellWidget(r,1,code)
            # Name
            name = QLineEdit(rec.get('name',''))
            self.types_table.setCellWidget(r,2,name)
            # Deduct From
            ded = QComboBox(); ded.addItems(['annual','sick','unpaid','none'])
            idx = ded.findText(rec.get('deduct_from','annual'))
            ded.setCurrentIndex(max(0,idx))
            self.types_table.setCellWidget(r,3,ded)
            # Requires Doc
            req = QCheckBox(); req.setChecked(bool(rec.get('requires_document', False)))
            self.types_table.setCellWidget(r,4,req)
            # Default Duration
            def_spin = QDoubleSpinBox(); def_spin.setDecimals(1); def_spin.setSingleStep(0.5); def_spin.setRange(0.0,365.0)
            v = rec.get('default_duration'); def_spin.setValue(float(v) if v is not None else 0.0)
            self.types_table.setCellWidget(r,5,def_spin)
            # Max Duration
            max_spin = QDoubleSpinBox(); max_spin.setDecimals(1); max_spin.setSingleStep(0.5); max_spin.setRange(0.0,365.0)
            mv = rec.get('max_duration'); max_spin.setValue(float(mv) if mv is not None else 0.0)
            self.types_table.setCellWidget(r,6,max_spin)
            # Description
            desc = QLineEdit(rec.get('description','') or '')
            self.types_table.setCellWidget(r,7,desc)
            # Store original code
            item = QTableWidgetItem(''); item.setData(Qt.UserRole, rec.get('code')); self.types_table.setItem(r,0,item)
            # Actions
            btn = QPushButton('Save')
            btn.clicked.connect(lambda _=False, row=r: self.save_type_row(row))
            self.types_table.setCellWidget(r,8,btn)

    def add_type_row(self):
        r = self.types_table.rowCount()
        self.types_table.insertRow(r)
        self.types_table.setCellWidget(r,0,QCheckBox()); self.types_table.cellWidget(r,0).setChecked(True)
        self.types_table.setCellWidget(r,1,QLineEdit(''))
        self.types_table.setCellWidget(r,2,QLineEdit(''))
        ded = QComboBox(); ded.addItems(['annual','sick','unpaid','none']); self.types_table.setCellWidget(r,3,ded)
        self.types_table.setCellWidget(r,4,QCheckBox())
        ds = QDoubleSpinBox(); ds.setDecimals(1); ds.setSingleStep(0.5); ds.setRange(0.0,365.0); ds.setValue(0.0); self.types_table.setCellWidget(r,5,ds)
        ms = QDoubleSpinBox(); ms.setDecimals(1); ms.setSingleStep(0.5); ms.setRange(0.0,365.0); ms.setValue(0.0); self.types_table.setCellWidget(r,6,ms)
        self.types_table.setCellWidget(r,7,QLineEdit(''))
        # Actions
        btn = QPushButton('Save')
        btn.clicked.connect(lambda _=False, row=r: self.save_type_row(row))
        self.types_table.setCellWidget(r,8,btn)
        item = QTableWidgetItem(''); item.setData(Qt.UserRole, None); self.types_table.setItem(r,0,item)

    def _row_to_type_payload(self, r:int) -> dict:
        return {
            'is_active': self.types_table.cellWidget(r,0).isChecked(),
            'code': self.types_table.cellWidget(r,1).text().strip(),
            'name': self.types_table.cellWidget(r,2).text().strip(),
            'deduct_from': self.types_table.cellWidget(r,3).currentText(),
            'requires_document': self.types_table.cellWidget(r,4).isChecked(),
            'default_duration': float(self.types_table.cellWidget(r,5).value()) or None,
            'max_duration': float(self.types_table.cellWidget(r,6).value()) or None,
            'description': self.types_table.cellWidget(r,7).text().strip() or None,
        }

    def save_types(self):
        created, updated, errors = 0,0,[]
        for r in range(self.types_table.rowCount()):
            orig_code = self.types_table.item(r,0).data(Qt.UserRole) if self.types_table.item(r,0) else None
            payload = self._row_to_type_payload(r)
            if not payload['code']:
                errors.append(f'Row {r+1}: code required'); continue
            if not payload['name']:
                errors.append(f'Row {r+1}: name required'); continue
            try:
                if orig_code:
                    if update_leave_type(orig_code, payload):
                        updated += 1
                    else:
                        errors.append(f'Row {r+1}: update failed')
                else:
                    create_leave_type(payload); created += 1
            except Exception as e:
                errors.append(f"Row {r+1} ({payload.get('code')}): {e}")
        msg = f'Types saved. Created: {created}, Updated: {updated}'
        if errors:
            msg += '\nErrors (first 5):\n- ' + '\n- '.join(errors[:5])
            QMessageBox.warning(self,'Types Save Issues', msg)
        else:
            QMessageBox.information(self,'Types Saved', msg)
        self.reload_types()

    def save_type_row(self, r: int):
        """Save only the specified type row (create or update)."""
        try:
            orig_code = self.types_table.item(r,0).data(Qt.UserRole) if self.types_table.item(r,0) else None
            payload = self._row_to_type_payload(r)
            if not payload['code']:
                QMessageBox.warning(self,'Validation','Code is required for this row.')
                return
            if not payload['name']:
                QMessageBox.warning(self,'Validation','Name is required for this row.')
                return
            if orig_code:
                ok = update_leave_type(orig_code, payload)
                if not ok:
                    QMessageBox.warning(self,'Update Failed', f"Failed to update type '{orig_code}'.")
                    return
                QMessageBox.information(self,'Updated', f"Type '{payload['code']}' updated.")
            else:
                create_leave_type(payload)
                QMessageBox.information(self,'Created', f"Type '{payload['code']}' created.")
        except Exception as e:
            QMessageBox.critical(self,'Error', f'Failed to save row: {e}')
            return
        # Refresh and try to keep focus on this code
        code_now = payload.get('code')
        self.reload_types()
        try:
            # Find row with code_now and select it
            for row in range(self.types_table.rowCount()):
                w = self.types_table.cellWidget(row,1)
                if hasattr(w,'text') and w.text().strip() == code_now:
                    self.types_table.selectRow(row)
                    break
        except Exception:
            pass

    def delete_selected_types(self):
        rows = sorted({idx.row() for idx in self.types_table.selectedIndexes()}, reverse=True)
        if not rows:
            QMessageBox.information(self,'No Selection','Select one or more rows to delete.')
            return
        codes = []
        for r in rows:
            item = self.types_table.item(r,0)
            code = item.data(Qt.UserRole) if item else None
            if code:
                codes.append(code)
        if not codes:
            QMessageBox.warning(self,'Cannot Delete','Only existing (saved) types can be deleted.')
            return
        # Confirmation
        msg = 'Delete the following leave types?\n- ' + '\n- '.join(codes)
        resp = QMessageBox.question(self,'Confirm Deletion', msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        deleted, errors = 0, []
        for code in codes:
            try:
                if delete_leave_type(code):
                    deleted += 1
                    # Remove code from caps structure if present
                    try:
                        for tier_id, tier_caps in (self._caps or {}).items():
                            if code in tier_caps:
                                tier_caps.pop(code, None)
                        # Persist caps cleanup
                        save_caps_to_db(self._caps_data)
                    except Exception:
                        pass
                else:
                    errors.append(code)
            except Exception as e:
                errors.append(f"{code}: {e}")
        summary = f'Deleted: {deleted}'
        if errors:
            summary += '\nErrors: ' + ', '.join(errors)
            QMessageBox.warning(self,'Deletion Completed with Issues', summary)
        else:
            QMessageBox.information(self,'Deletion Completed', summary)
        self.reload_all()

    # ---- CAPS TABLE ----
    def _populate_caps_table(self):
        tier_id = self.caps_tier_combo.currentData()
        codes = [t.get('code') for t in self._types] or []
        tier_caps = (self._caps or {}).get(tier_id, {}) if tier_id else {}
        self.caps_table.setRowCount(len(codes))
        for r, code in enumerate(codes):
            self.caps_table.setItem(r,0,QTableWidgetItem(code))
            spin = QSpinBox(); spin.setRange(0,365); spin.setValue(int(tier_caps.get(code,0)))
            self.caps_table.setCellWidget(r,1,spin)
            btn = QPushButton('Save')
            btn.clicked.connect(lambda _=False, row=r: self.save_cap_row(row))
            self.caps_table.setCellWidget(r,2,btn)

    def save_caps(self):
        tier_id = self.caps_tier_combo.currentData()
        if not tier_id:
            QMessageBox.warning(self,'No Tier','Select a tier first.'); return
        tier_caps = {}
        for r in range(self.caps_table.rowCount()):
            code = self.caps_table.item(r,0).text()
            spin = self.caps_table.cellWidget(r,1)
            if hasattr(spin,'value'):
                tier_caps[code] = spin.value()
        new_caps = self._caps.copy(); new_caps[tier_id] = tier_caps
        self._caps_data['caps'] = new_caps
        ok = False
        try:
            ok = save_caps_to_db(self._caps_data)
        except Exception as e:
            QMessageBox.critical(self,'Save Failed', f'Failed to save caps: {e}')
            return
        if ok:
            QMessageBox.information(self,'Caps Saved','Leave caps saved to database.')
            self.reload_caps()
        else:
            QMessageBox.critical(self,'Error','Failed to save caps to database.')

    def save_cap_row(self, r: int):
        """Save only the cap value for the code in this row and current tier."""
        tier_id = self.caps_tier_combo.currentData()
        if not tier_id:
            QMessageBox.warning(self,'No Tier','Select a tier first.'); return
        try:
            code_item = self.caps_table.item(r,0)
            code = code_item.text() if code_item else None
            spin = self.caps_table.cellWidget(r,1)
            if not code or not hasattr(spin,'value'):
                QMessageBox.warning(self,'Invalid Row','Cannot determine leave type or cap value for this row.')
                return
            # Update only this code's cap in current tier
            new_caps = (self._caps.copy()) if isinstance(self._caps, dict) else {}
            tier_caps = dict(new_caps.get(tier_id, {}))
            tier_caps[code] = int(spin.value())
            new_caps[tier_id] = tier_caps
            self._caps_data['caps'] = new_caps
            ok = save_caps_to_db(self._caps_data)
            if ok:
                QMessageBox.information(self,'Cap Saved', f"Saved cap for '{code}' in tier '{tier_id}'.")
                self.reload_caps()
                # Try reselect same row
                try:
                    self.caps_table.selectRow(r)
                except Exception:
                    pass
            else:
                QMessageBox.critical(self,'Error','Failed to save cap to database.')
        except Exception as e:
            QMessageBox.critical(self,'Error', f'Failed to save cap row: {e}')

if __name__ == '__main__':
    print('LeavePolicyEditor smoke: types=', [t.get('code') for t in list_leave_types(active_only=False)][:5])
