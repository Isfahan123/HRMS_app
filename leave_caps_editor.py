from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableWidget,
    QTableWidgetItem, QPushButton, QSpinBox, QMessageBox
)
from PyQt5.QtCore import Qt

from services.leave_caps_service import (
    get_leave_caps,
    save_to_supabase,
    apply_policy_to_db,
)


class LeaveCapsEditor(QWidget):
    """Simple editor for global leave caps by years-of-service tiers."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('LeaveCapsEditor')
        self.data = get_leave_caps() or {}
        self.tiers = self.data.get('tiers', [])
        self.leave_types = self.data.get('leave_types', [])

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel('🛡️ Leave Caps by Years-of-Service')
        title.setAlignment(Qt.AlignLeft)
        layout.addWidget(title)

        # Tier selector
        row = QHBoxLayout()
        row.addWidget(QLabel('Tier:'))
        self.tier_selector = QComboBox()
        for t in self.tiers:
            self.tier_selector.addItem(t.get('label', t.get('id')), userData=t.get('id'))
        self.tier_selector.currentIndexChanged.connect(self._on_tier_changed)
        row.addWidget(self.tier_selector)
        row.addStretch()
        layout.addLayout(row)

        # Table of leave types -> caps
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['Leave Type', 'Cap (days)'])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # Actions — only Save (push to Supabase)
        actions = QHBoxLayout()
        self.save_btn = QPushButton('💾 Save to DB')
        self.save_btn.clicked.connect(self._on_save)
        actions.addWidget(self.save_btn)
        # Apply policy button
        self.apply_btn = QPushButton('⚙️ Apply policy to DB')
        self.apply_btn.clicked.connect(self._on_apply_policy)
        actions.addWidget(self.apply_btn)
        actions.addStretch()
        layout.addLayout(actions)

        # populate
        self._reload()

    def _reload(self):
        self.data = get_leave_caps() or {}
        self.tiers = self.data.get('tiers', [])
        self.leave_types = self.data.get('leave_types', [])
        # refresh selector
        current_id = self.tier_selector.currentData() if self.tier_selector.count() else None
        self.tier_selector.blockSignals(True)
        self.tier_selector.clear()
        for t in self.tiers:
            self.tier_selector.addItem(t.get('label', t.get('id')), userData=t.get('id'))
        self.tier_selector.blockSignals(False)

        # try to restore selected
        if current_id:
            idx = self.tier_selector.findData(current_id)
            if idx >= 0:
                self.tier_selector.setCurrentIndex(idx)

        self._populate_table_for_current_tier()

    def _on_tier_changed(self, _):
        self._populate_table_for_current_tier()

    def _populate_table_for_current_tier(self):
        tier_id = self.tier_selector.currentData()
        caps = (self.data.get('caps') or {}).get(tier_id, {})

        self.table.setRowCount(len(self.leave_types))
        for r, lt in enumerate(self.leave_types):
            self.table.setItem(r, 0, QTableWidgetItem(lt.capitalize()))
            spin = QSpinBox()
            spin.setRange(0, 365)
            spin.setValue(int(caps.get(lt, 0)))
            self.table.setCellWidget(r, 1, spin)

    def _on_save(self):
        tier_id = self.tier_selector.currentData()
        if not tier_id:
            QMessageBox.warning(self, 'No Tier', 'Please select a tier first.')
            return

        # gather values
        new_caps = self.data.get('caps', {}).copy()
        tier_caps = new_caps.get(tier_id, {}).copy()
        for r, lt in enumerate(self.leave_types):
            widget = self.table.cellWidget(r, 1)
            if hasattr(widget, 'value'):
                tier_caps[lt] = widget.value()
        new_caps[tier_id] = tier_caps
        self.data['caps'] = new_caps

        # Save directly to Supabase
        try:
            payload = self.data or get_leave_caps()
            ok = save_to_supabase(payload)
            if ok:
                # Optionally persist locally as backup
                try:
                    from services.leave_caps_service import save_leave_caps as _local_save
                    _local_save(payload)
                except Exception:
                    pass
                QMessageBox.information(self, 'Saved', 'Leave caps saved to database successfully.')
            else:
                QMessageBox.critical(self, 'Error', 'Failed to save to database. Check Supabase configuration and that tables exist.')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to save to DB: {e}')

    def _on_apply_policy(self):
        # First perform a dry-run and show a short summary
        try:
            summary = apply_policy_to_db(force=False, dry_run=True)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to run dry-run: {e}')
            return

        if summary.get('errors'):
            details = '\n'.join(summary.get('details', [])[:10])
            QMessageBox.warning(self, 'Dry-run completed with errors', f"Errors encountered:\n{details}")
            return

        msg = f"Dry-run: processed={summary.get('processed')}, created={summary.get('created')}, updated={summary.get('updated')}, skipped={summary.get('skipped')}\n\nProceed to apply changes to database?"
        resp = QMessageBox.question(self, 'Apply policy to DB', msg, QMessageBox.Yes | QMessageBox.No)
        if resp != QMessageBox.Yes:
            return

        # Ask if force overwrite
        resp2 = QMessageBox.question(self, 'Apply mode', 'Force overwrite existing entitlements? (Yes = force, No = only fill missing)', QMessageBox.Yes | QMessageBox.No)
        force_mode = (resp2 == QMessageBox.Yes)

        # perform actual apply
        try:
            real_summary = apply_policy_to_db(force=force_mode, dry_run=False)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to apply policy: {e}')
            return

        details = '\n'.join(real_summary.get('details', [])[:20])
        QMessageBox.information(self, 'Apply completed', f"Applied: processed={real_summary.get('processed')}, created={real_summary.get('created')}, updated={real_summary.get('updated')}, skipped={real_summary.get('skipped')}, errors={real_summary.get('errors')}\n\nDetails:\n{details}")

    # Note: Load/Sync handlers removed — Save now pushes directly to Supabase.
