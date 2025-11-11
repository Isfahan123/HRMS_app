"""TP1 Relief Overrides Subtab

Provides an admin UI for editing per-item relief overrides (cap, pcb_only, cycle_years).
Changes are persisted to the `relief_item_overrides` table and loaded at runtime
via `load_relief_overrides_from_db` when payroll calculations execute.

Design principles:
- Show default catalog values alongside override values.
- Blank override cells = inherit catalog default (row removed if previously existed).
- Only upsert fields that are changed (NULL for cleared values).
- Defensive: if Supabase missing table, show warning banner but keep UI usable (read-only).
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QMessageBox, QAbstractItemView, QHeaderView, QCheckBox, QSpinBox, QLineEdit,
    QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor
from services.tax_relief_catalog import (
    ITEMS, ITEM_BY_KEY, load_relief_overrides_from_db,
    RELIEF_GROUPS, load_relief_group_overrides_from_db, get_effective_groups
)
from services.supabase_service import supabase, _probe_table_exists

OVERRIDES_TABLE = 'relief_item_overrides'

"""Relief Overrides Subtab (clean)

Single definitive implementation replacing duplicated broken content.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton,
    QLabel, QMessageBox, QAbstractItemView, QHeaderView, QCheckBox, QLineEdit,
    QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor
from services.tax_relief_catalog import (
    ITEMS, ITEM_BY_KEY, RELIEF_GROUPS,
    load_relief_overrides_from_db, load_relief_group_overrides_from_db
)
from services.supabase_service import supabase

OVERRIDES_TABLE = 'relief_item_overrides'


class ReliefOverridesSubtab(QWidget):
    def __init__(self, parent_admin):
        super().__init__()
        self.admin = parent_admin
        self.setObjectName('ReliefOverridesSubtab')
        self.overrides_cache = {}
        self.group_overrides_cache = {}
        self.group_caps = self._build_group_caps_index()
        # Map group_id -> row index in group_table for quick lookup (rebuilt each populate)
        self.group_row_index = {}
        self._build_ui()
        self.reload_overrides()

    def _build_group_caps_index(self):
        from services.tax_relief_catalog import GROUP_TO_ITEMS
        return {gid: {"cap": grp.cap, "members": GROUP_TO_ITEMS.get(gid, [])}
                for gid, grp in RELIEF_GROUPS.items()}

    def _build_ui(self):
        layout = QVBoxLayout(self)
        # Header / legend
        head = QLabel('<b>TP1 Relief Overrides</b> — per-item & group caps. Blank = inherit.')
        head.setWordWrap(True)
        layout.addWidget(head)
        legend = QLabel("<span style='font-size:11px;'>Legend: <span style='background:#d0f5d0;padding:2px 4px;'>Higher</span> <span style='background:#ffe9b3;padding:2px 4px;'>Lower</span> <span style='background:#e0e0e0;padding:2px 4px;'>Inherit</span> <span style='background:#ffd0d0;padding:2px 4px;'>Invalid</span> <span style='background:#d0e8ff;padding:2px 4px;'>PCB Only</span></span>")
        layout.addWidget(legend)
        # Filter + overridden toggle
        filt = QHBoxLayout()
        self.filter_edit = QLineEdit(); self.filter_edit.setPlaceholderText('Filter (code/key/desc)')
        self.filter_edit.textChanged.connect(self.apply_filter)
        self.cb_overridden_only = QCheckBox('Only Overridden')
        self.cb_overridden_only.stateChanged.connect(self.apply_filter)
        filt.addWidget(QLabel('Filter:'))
        filt.addWidget(self.filter_edit)
        filt.addWidget(self.cb_overridden_only)
        filt.addStretch()
        layout.addLayout(filt)
        # Status
        self.status_label = QLabel('')
        self.status_label.setStyleSheet('color:#555;font-size:11px')
        layout.addWidget(self.status_label)
        # Scrollable content area for tables
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        content = QWidget(); content_layout = QVBoxLayout(content)

        # Group table (enlarged)
        self.group_table = QTableWidget()
        self.group_table.setColumnCount(5)
        self.group_table.setHorizontalHeaderLabels(['Group ID','Description','Default Cap','Override Cap','Effective Cap'])
        self.group_table.verticalHeader().setVisible(False)
        self.group_table.setAlternatingRowColors(True)
        bigger_font_css = 'font-size:13px;'
        self.group_table.setStyleSheet(f"QTableWidget {{{bigger_font_css}}} QLineEdit {{ font-size:13px; padding:3px 6px; }}")
        header_g = self.group_table.horizontalHeader()
        header_g.setSectionResizeMode(QHeaderView.Interactive)
        header_g.setSectionResizeMode(1, QHeaderView.Stretch)
        header_g.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.group_table.setColumnWidth(0,140)
        self.group_table.setColumnWidth(2,140)
        self.group_table.setColumnWidth(3,170)
        self.group_table.setColumnWidth(4,160)
        self.group_table.verticalHeader().setDefaultSectionSize(34)
        self.group_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # Ensure group table shows a comfortable height
        self.group_table.setMinimumHeight(220)
        content_layout.addWidget(QLabel('<b>Group Caps</b>'))
        content_layout.addWidget(self.group_table)
        # Item table
        self.table = QTableWidget(); self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(['Code','Item Key','Description','Default Cap','Override Cap','Effective Cap','PCB Only?','Default Cycle','Override Cycle'])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.AllEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        # Larger font and inputs for readability
        self.table.setStyleSheet(f"QTableWidget {{{bigger_font_css}}} QLineEdit {{ font-size:13px; padding:3px 6px; }}")
        widths = [70,130,360,110,120,120,90,110,120]
        for i,w in enumerate(widths):
            self.table.setColumnWidth(i,w)
        # Slightly taller rows for easier scanning
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        # Let the item table expand and be scrollable, and ensure a larger minimum height
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setMinimumHeight(600)
        content_layout.addWidget(self.table)

        # Finalize scroll area
        scroll.setWidget(content)
        layout.addWidget(scroll)
        # Buttons
        btns = QHBoxLayout()
        self.btn_save=QPushButton('💾 Save Changes')
        self.btn_reload=QPushButton('↻ Reload')
        self.btn_clear=QPushButton('🧹 Clear Selected Override')
        self.btn_reset_all=QPushButton('♻ Reset All Overrides')
        for b in (self.btn_save,self.btn_reload,self.btn_clear,self.btn_reset_all):
            btns.addWidget(b)
        btns.addStretch()
        layout.addLayout(btns)
        self.btn_save.clicked.connect(self.save_changes)
        self.btn_reload.clicked.connect(self.reload_overrides)
        self.btn_clear.clicked.connect(self.clear_selected_override)
        self.btn_reset_all.clicked.connect(self.reset_all_overrides)

    def apply_filter(self):
        txt=self.filter_edit.text().strip().lower()
        overridden_only = self.cb_overridden_only.isChecked()
        # Filter item table
        for r in range(self.table.rowCount()):
            vals=[self.table.item(r,c).text().lower() if self.table.item(r,c) else '' for c in (0,1,2)]
            matches = all(t in ' '.join(vals) for t in txt.split()) if txt else True
            if matches and overridden_only:
                matches = self._row_has_override(r)
            self.table.setRowHidden(r, not matches)
        # Filter group table
        for gr in range(self.group_table.rowCount()):
            gid_item = self.group_table.item(gr,0)
            desc_item = self.group_table.item(gr,1)
            def_cap_item = self.group_table.item(gr,2)
            texts = []
            for itm in (gid_item, desc_item, def_cap_item):
                if itm: texts.append(itm.text().lower())
            gmatch = all(t in ' '.join(texts) for t in txt.split()) if txt else True
            if gmatch and overridden_only:
                cap_edit = self.group_table.cellWidget(gr,3)
                raw = cap_edit.text().strip() if cap_edit else ''
                gmatch = bool(raw)  # any text in override cap means overridden
            self.group_table.setRowHidden(gr, not gmatch)

    def _row_has_override(self, row:int)->bool:
        """Return True if any override field differs from inherited (cap, pcb, cycle)."""
        key = self.table.item(row,1).text()
        existing = self.overrides_cache.get(key, {})
        # Quick path: existing override row in cache
        if existing:
            return True
        # Otherwise inspect current widgets for new unsaved changes
        cap_edit=self.table.cellWidget(row,4); raw_cap=cap_edit.text().strip() if cap_edit else ''
        pcb_cb=self.table.cellWidget(row,6); pcb_state=pcb_cb.checkState() if pcb_cb else Qt.PartiallyChecked
        cycle_edit=self.table.cellWidget(row,8); raw_cycle=cycle_edit.text().strip() if cycle_edit else ''
        if raw_cap:
            try: float(raw_cap); return True
            except ValueError: return True  # treat invalid as changed
        if pcb_state!=Qt.PartiallyChecked:
            return True
        if raw_cycle:
            return True
        return False

    def reload_overrides(self):
        try:
            self.overrides_cache=load_relief_overrides_from_db(supabase) or {}
            self.group_overrides_cache=load_relief_group_overrides_from_db(supabase) or {}
            self.populate_group_table(); self.populate_table()
            missing = []
            if not _probe_table_exists('relief_item_overrides'):
                missing.append('relief_item_overrides')
            if not _probe_table_exists('relief_group_overrides'):
                missing.append('relief_group_overrides')
            if missing:
                self.status_label.setText(
                    '⚠ Missing tables: ' + ', '.join(missing) +
                    ' — run sql/create_relief_overrides_tables.sql in Supabase SQL editor.'
                )
            else:
                self.status_label.setText(f'Loaded {len(self.overrides_cache)} item overrides, {len(self.group_overrides_cache)} group overrides.')
        except Exception as e:
            self.overrides_cache={}; self.group_overrides_cache={}
            self.populate_group_table(); self.populate_table()
            self.status_label.setText(f'⚠ Unable to load overrides: {e}')
        self.group_caps=self._build_group_caps_index()
        for gid,cap in self.group_overrides_cache.items():
            if gid in self.group_caps: self.group_caps[gid]['cap']=cap

    def populate_group_table(self):
        self.group_table.setRowCount(len(RELIEF_GROUPS))
        self.group_row_index = {}
        for r,(gid,grp) in enumerate(RELIEF_GROUPS.items()):
            self.group_row_index[gid] = r
            ov=self.group_overrides_cache.get(gid)
            id_item=QTableWidgetItem(gid); id_item.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled); self.group_table.setItem(r,0,id_item)
            desc_item=QTableWidgetItem(grp.description); desc_item.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled); self.group_table.setItem(r,1,desc_item)
            def_item=QTableWidgetItem('' if grp.cap is None else f'{grp.cap:.0f}'); def_item.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled); self.group_table.setItem(r,2,def_item)
            cap_edit=QLineEdit(self); cap_edit.setPlaceholderText('(inherit)')
            if ov is not None: cap_edit.setText(f'{ov:.0f}')
            # When group cap text changes, update effective cap cell and re-style affected item rows live
            cap_edit.textChanged.connect(lambda _v,gid=gid,row=r: self._on_group_cap_changed(gid, row))
            self.group_table.setCellWidget(r,3,cap_edit)
            eff_item=QTableWidgetItem(); eff_item.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled); self.group_table.setItem(r,4,eff_item)
            self._update_group_effective_cap_row(r)

    def _update_group_effective_cap_row(self,row:int):
        def_item=self.group_table.item(row,2); eff_item=self.group_table.item(row,4); cap_edit=self.group_table.cellWidget(row,3)
        default_txt=def_item.text() if def_item else ''; raw=cap_edit.text().strip() if cap_edit else ''
        if raw:
            try: eff_item.setText(f'{float(raw):.0f}')
            except ValueError: eff_item.setText('✖')
        else: eff_item.setText(default_txt)
        inherit=QBrush(QColor('#e0e0e0')); higher=QBrush(QColor('#d0f5d0')); lower=QBrush(QColor('#ffe9b3')); invalid=QBrush(QColor('#ffd0d0'))
        brush=inherit
        if raw:
            try:
                v=float(raw)
                if default_txt:
                    d=float(default_txt); brush=higher if v>d else lower if v<d else inherit
                else: brush=higher
            except ValueError: brush=invalid
        eff_item.setBackground(brush)

    def populate_table(self):
        self.table.setRowCount(len(ITEMS))
        for r,item in enumerate(ITEMS):
            ov=self.overrides_cache.get(item.key,{})
            code_item=QTableWidgetItem(item.code); code_item.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled); self.table.setItem(r,0,code_item)
            key_item=QTableWidgetItem(item.key); key_item.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled); self.table.setItem(r,1,key_item)
            desc_item=QTableWidgetItem(item.description); desc_item.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled); self.table.setItem(r,2,desc_item)
            def_cap_txt='' if item.cap is None else f'{item.cap:.0f}'
            def_cap_item=QTableWidgetItem(def_cap_txt); def_cap_item.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled); self.table.setItem(r,3,def_cap_item)
            cap_edit=QLineEdit(self); cap_edit.setPlaceholderText('(inherit)')
            if ov.get('cap') is not None: cap_edit.setText(f"{ov['cap']:.0f}")
            cap_edit.textChanged.connect(lambda _v,row=r: self._update_effective_cap_row(row))
            self.table.setCellWidget(r,4,cap_edit)
            eff_item=QTableWidgetItem(); eff_item.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled); self.table.setItem(r,5,eff_item)
            pcb_cb=QCheckBox(self); pcb_cb.setTristate(True)
            if ov.get('pcb_only') is None: pcb_cb.setCheckState(Qt.PartiallyChecked)
            else: pcb_cb.setCheckState(Qt.Checked if ov.get('pcb_only') else Qt.Unchecked)
            pcb_cb.stateChanged.connect(lambda _s,row=r: self._style_row(row))
            self.table.setCellWidget(r,6,pcb_cb)
            def_cycle_txt='' if item.cycle_years is None else str(item.cycle_years)
            def_cycle_item=QTableWidgetItem(def_cycle_txt); def_cycle_item.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled); self.table.setItem(r,7,def_cycle_item)
            cycle_edit=QLineEdit(self); cycle_edit.setPlaceholderText('(inherit)')
            if ov.get('cycle_years') is not None: cycle_edit.setText(str(int(ov['cycle_years'])))
            cycle_edit.textChanged.connect(lambda _v,row=r: self._update_effective_cap_row(row))
            self.table.setCellWidget(r,8,cycle_edit)
            self._update_effective_cap_row(r)
        self.apply_filter()

    def _update_effective_cap_row(self,row:int):
        default_txt=self.table.item(row,3).text() or ''
        cap_edit=self.table.cellWidget(row,4); eff_item=self.table.item(row,5)
        raw=cap_edit.text().strip() if cap_edit else ''
        if raw:
            try: eff_item.setText(f'{float(raw):.0f}')
            except ValueError: eff_item.setText('✖')
        else: eff_item.setText(default_txt)
        self._style_row(row)

    def _style_row(self,row:int):
        default_txt=self.table.item(row,3).text() or ''
        default_cap=float(default_txt) if default_txt else None
        cap_edit=self.table.cellWidget(row,4); eff_item=self.table.item(row,5)
        raw=cap_edit.text().strip() if cap_edit else ''
        inherit=QBrush(QColor('#e0e0e0')); higher=QBrush(QColor('#d0f5d0')); lower=QBrush(QColor('#ffe9b3')); invalid=QBrush(QColor('#ffd0d0')); pcb=QBrush(QColor('#d0e8ff'))
        brush=inherit
        if raw:
            try:
                v=float(raw)
                if default_cap is not None:
                    if v>default_cap: brush=higher
                    elif v<default_cap: brush=lower
                else: brush=higher
            except ValueError: brush=invalid
        eff_item.setBackground(brush)
        pcb_cb=self.table.cellWidget(row,6)
        if pcb_cb and pcb_cb.checkState()==Qt.Checked and brush!=invalid:
            base=brush.color(); pcb_c=pcb.color(); mix=QColor((base.red()+pcb_c.red())//2,(base.green()+pcb_c.green())//2,(base.blue()+pcb_c.blue())//2)
            eff_item.setBackground(QBrush(mix))
            tip=eff_item.toolTip() or ''
            eff_item.setToolTip((tip+'\n' if tip else '')+'PCB-only override will not reduce cash total')
        warn=self._group_cap_violation(row)
        if warn:
            tip=eff_item.toolTip() or ''
            eff_item.setToolTip((tip+'\n' if tip else '')+warn)

    def _group_cap_violation(self,row:int):
        key=self.table.item(row,1).text(); meta=ITEM_BY_KEY.get(key)
        if not meta or not meta.group: return None
        # Determine current (possibly unsaved) group cap
        gcap_status = self._current_group_cap(meta.group)
        if gcap_status == 'invalid':
            return 'Group cap invalid'
        gcap = gcap_status  # numeric or None
        cap_edit=self.table.cellWidget(row,4); raw=cap_edit.text().strip() if cap_edit else ''
        if not raw: return None
        try:
            val=float(raw)
        except ValueError:
            return 'Invalid numeric cap'
        if gcap is not None and val>gcap:
            return f'Override exceeds group cap {gcap:.0f}'
        return None

    # --- Live group cap support helpers ---
    def _on_group_cap_changed(self, gid:str, row:int):
        """Update group row visuals then refresh any item rows belonging to this group for live validation."""
        self._update_group_effective_cap_row(row)
        self._refresh_items_for_group(gid)

    def _refresh_items_for_group(self, gid:str):
        # Iterate item table, re-style rows matching group
        for r in range(self.table.rowCount()):
            key_item = self.table.item(r,1)
            if not key_item: continue
            meta = ITEM_BY_KEY.get(key_item.text())
            if meta and meta.group == gid:
                self._style_row(r)

    def _current_group_cap(self, gid:str):
        """Return current effective group cap considering unsaved edits.
        Returns numeric cap, None (inherit/no cap), or 'invalid' if the edit box has invalid number.
        """
        # Row lookup
        row = self.group_row_index.get(gid)
        grp = RELIEF_GROUPS.get(gid)
        base_default = grp.cap if grp else None
        if row is None:
            return base_default
        cap_edit = self.group_table.cellWidget(row,3)
        raw = cap_edit.text().strip() if cap_edit else ''
        if not raw:
            return base_default
        try:
            return float(raw)
        except ValueError:
            return 'invalid'

    def save_changes(self):
        errs=[]
        for r in range(self.group_table.rowCount()):
            raw=self.group_table.cellWidget(r,3).text().strip() if self.group_table.cellWidget(r,3) else ''
            if raw:
                try:
                    v=float(raw)
                    if v<0: errs.append(f'Group row {r+1}: cap cannot be negative')
                except ValueError:
                    errs.append(f'Group row {r+1}: invalid numeric cap')
        for r in range(self.table.rowCount()):
            warn=self._group_cap_violation(r)
            if warn: errs.append(f'Row {r+1}: {warn}')
        if errs:
            QMessageBox.warning(self,'Validation Failed','Cannot save due to:\n'+"\n".join(errs[:10]))
            return
        group_upsert=[]; group_delete=[]
        for r in range(self.group_table.rowCount()):
            gid=self.group_table.item(r,0).text(); raw=self.group_table.cellWidget(r,3).text().strip() if self.group_table.cellWidget(r,3) else ''
            if not raw:
                if gid in self.group_overrides_cache: group_delete.append(gid)
                continue
            try: v=float(raw)
            except ValueError: continue
            if self.group_overrides_cache.get(gid)!=v:
                group_upsert.append({'group_id':gid,'cap':v})
        item_upsert=[]; item_delete=[]
        for r in range(self.table.rowCount()):
            if self.table.isRowHidden(r): continue
            key=self.table.item(r,1).text(); cap_edit=self.table.cellWidget(r,4); pcb_cb=self.table.cellWidget(r,6); cycle_edit=self.table.cellWidget(r,8)
            raw_cap=cap_edit.text().strip() if cap_edit else ''
            cap_val=None
            if raw_cap:
                try: cap_val=float(raw_cap)
                except ValueError:
                    QMessageBox.warning(self,'Invalid Cap',f'Row {r+1}: Cap must be numeric.'); return
            pcb_state=pcb_cb.checkState() if pcb_cb else Qt.PartiallyChecked
            pcb_val=None if pcb_state==Qt.PartiallyChecked else (pcb_state==Qt.Checked)
            raw_cycle=cycle_edit.text().strip() if cycle_edit else ''
            cycle_val=None
            if raw_cycle:
                if not raw_cycle.isdigit() or int(raw_cycle)<=0:
                    QMessageBox.warning(self,'Invalid Cycle',f'Row {r+1}: Cycle must be positive integer.'); return
                cycle_val=int(raw_cycle)
            existing=self.overrides_cache.get(key,{})
            changed=(existing.get('cap')!=cap_val or existing.get('pcb_only')!=pcb_val or existing.get('cycle_years')!=cycle_val)
            if not changed: continue
            if cap_val is None and pcb_val is None and cycle_val is None and existing:
                item_delete.append(key); continue
            payload={'item_key':key}
            if cap_val is not None: payload['cap']=cap_val
            if pcb_val is not None: payload['pcb_only']=pcb_val
            if cycle_val is not None: payload['cycle_years']=cycle_val
            item_upsert.append(payload)
        try:
            affected=0
            if group_upsert:
                supabase.table('relief_group_overrides').upsert(group_upsert).execute(); affected+=len(group_upsert)
            if group_delete:
                for gid in group_delete:
                    supabase.table('relief_group_overrides').delete().eq('group_id',gid).execute(); affected+=1
            if item_upsert:
                supabase.table(OVERRIDES_TABLE).upsert(item_upsert).execute(); affected+=len(item_upsert)
            if item_delete:
                for k in item_delete:
                    supabase.table(OVERRIDES_TABLE).delete().eq('item_key',k).execute(); affected+=1
            if affected > 0:
                self.status_label.setText(f'Saved changes. {affected} rows affected.');
                # Optional visual confirmation popup
                try:
                    QMessageBox.information(self, 'Saved', f'Saved changes. {affected} row(s) affected.')
                except Exception:
                    pass
            else:
                self.status_label.setText('No changes to save.');
                try:
                    QMessageBox.information(self, 'No changes', 'No changes detected to save.')
                except Exception:
                    pass
            self.reload_overrides()
        except Exception as e:
            msg = str(e)
            if '404' in msg or 'Not Found' in msg:
                msg += '\n\nHint: create missing tables by running sql/create_relief_overrides_tables.sql in Supabase.'
            QMessageBox.warning(self,'Save Failed',f'Failed to save overrides: {msg}')

    def clear_selected_override(self):
        r=self.table.currentRow()
        if r<0: return
        key=self.table.item(r,1).text()
        if key in self.overrides_cache:
            try:
                supabase.table(OVERRIDES_TABLE).delete().eq('item_key',key).execute(); self.status_label.setText(f'Cleared override for {key}'); self.reload_overrides()
            except Exception as e:
                QMessageBox.warning(self,'Delete Failed',f'Failed to delete override: {e}')
        else:
            self.table.cellWidget(r,4).clear(); pcb_cb=self.table.cellWidget(r,6); pcb_cb.setCheckState(Qt.PartiallyChecked)
            self.table.cellWidget(r,8).clear(); self.status_label.setText(f'No existing override for {key}; cleared inputs only.')

    def reset_all_overrides(self):
        if QMessageBox.question(self,'Confirm Reset','Delete ALL override rows (item + group)?',QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes: return
        try:
            supabase.table(OVERRIDES_TABLE).delete().neq('item_key','___dummy___').execute()
            try: supabase.table('relief_group_overrides').delete().neq('group_id','___dummy___').execute()
            except Exception: pass
            self.status_label.setText('All item & group overrides cleared.'); self.reload_overrides()
        except Exception as e:
            QMessageBox.warning(self,'Reset Failed',f'Failed to reset overrides: {e}')


def build_relief_overrides_subtab(admin, subtab_widget):
    tab = ReliefOverridesSubtab(admin)
    subtab_widget.addTab(tab,'🛠 Relief Overrides')
