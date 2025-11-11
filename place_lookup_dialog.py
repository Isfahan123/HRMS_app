from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListWidget, QPushButton, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt
from services.geoapify_service import search_places


class PlaceLookupDialog(QDialog):
    def __init__(self, parent=None, initial_query=''):
        super().__init__(parent)
        self.setWindowTitle('Find Place')
        self.setModal(True)
        self.resize(480, 320)

        self.layout = QVBoxLayout(self)

        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText('Type school or institution name and press Enter')
        self.search_edit.setText(initial_query or '')
        self.layout.addWidget(self.search_edit)

        self.results = QListWidget(self)
        self.layout.addWidget(self.results)

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton('OK')
        self.cancel_btn = QPushButton('Cancel')
        btn_layout.addStretch()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        self.layout.addLayout(btn_layout)

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.search_edit.returnPressed.connect(self._do_search)

        # initial search if provided
        if initial_query:
            self._do_search()

    def _do_search(self):
        q = self.search_edit.text().strip()
        self.results.clear()
        if not q:
            return
        try:
            items = search_places(q, limit=8)
            for it in items:
                # display name + formatted address
                name = it.get('name') or ''
                formatted = it.get('formatted') or ''
                label = f"{name} — {formatted}" if formatted else name
                self.results.addItem(label)
            # store raw items for selection
            self._last_items = items
        except Exception as e:
            self.results.addItem(f'Error: {e}')
            self._last_items = []

    def selected(self):
        idx = self.results.currentRow()
        if idx is None or idx < 0:
            return None
        return self._last_items[idx] if hasattr(self, '_last_items') and idx < len(self._last_items) else None
