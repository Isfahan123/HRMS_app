from PyQt5.QtWidgets import QWidget, QLineEdit, QListWidget, QVBoxLayout, QListWidgetItem, QApplication
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint, QEvent
from services.places_autocomplete import autocomplete_cities, new_session_token

class CityAutocompleteWidget(QWidget):
    citySelected = pyqtSignal(str, str)  # (description, place_id)

    def __init__(self, parent=None, country_restriction: str | None = None):
        super().__init__(parent)
        self.country_restriction = country_restriction
        self.session_token = new_session_token()
        self.line_edit = QLineEdit()
        self.list_widget = QListWidget()
    # Make the list a lightweight popup but avoid activating it (so the line edit keeps focus)
        self.list_widget.setWindowFlags(self.list_widget.windowFlags() | Qt.Popup | Qt.FramelessWindowHint)
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        # Show without activating keeps keyboard focus on the line edit so typing continues
        self.list_widget.setAttribute(Qt.WA_ShowWithoutActivating)
        # Install an event filter so we can forward normal keypresses back to the line edit
        self.list_widget.installEventFilter(self)
        self.list_widget.hide()
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.line_edit)
        self.setLayout(layout)
        self.debounce_timer = QTimer(self)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.perform_lookup)
        self.line_edit.textEdited.connect(self._on_text_edited)
        self.list_widget.itemClicked.connect(self._on_item_clicked)

    def _on_text_edited(self, _):
        text = self.line_edit.text().strip()
        if len(text) < 3:
            self.list_widget.hide()
            return
        self.debounce_timer.start(300)

    def perform_lookup(self):
        query = self.line_edit.text().strip()
        if len(query) < 3:
            return
        results = autocomplete_cities(query, self.session_token, self.country_restriction)
        self.list_widget.clear()
        if not results:
            self.list_widget.hide()
            return
        for res in results:
            item = QListWidgetItem(res["description"])
            item.setData(Qt.UserRole, res["place_id"])
            self.list_widget.addItem(item)
        self.position_popup()
        self.list_widget.show()

    def position_popup(self):
        if not self.list_widget.isVisible():
            # approximate position just below the widget
            global_pos = self.line_edit.mapToGlobal(QPoint(0, self.line_edit.height()))
            self.list_widget.move(global_pos)
        # Make the popup a sensible width so it doesn't cover the input; allow wider suggestions but not huge
        target_width = max(self.line_edit.width(), 280)
        self.list_widget.resize(target_width, 180)

    def eventFilter(self, obj, event):
        # Forward ordinary text key events to the line edit so the user can continue typing
        if obj is self.list_widget and event.type() == QEvent.KeyPress:
            key = event.key()
            # Let arrow keys, enter/escape be handled by the list widget for navigation/selection
            if key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Escape, Qt.Key_Tab):
                return False
            # Forward other keypresses to the line edit
            QApplication.sendEvent(self.line_edit, event)
            return True
        return super().eventFilter(obj, event)

    def _on_item_clicked(self, item: QListWidgetItem):
        desc = item.text()
        place_id = item.data(Qt.UserRole)
        self.line_edit.setText(desc)
        self.list_widget.hide()
        self.citySelected.emit(desc, place_id)

    def text(self):
        return self.line_edit.text()

    def setText(self, value: str):
        self.line_edit.setText(value)

    def clear(self):
        self.line_edit.clear()
        self.list_widget.hide()
