import pycountry
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QPoint

class CountryDropdown(QWidget):
    countrySelected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_edit = QLineEdit()
        self.list_widget = QListWidget()
        # Make the list a popup but avoid activating it so the line edit keeps keyboard focus
        self.list_widget.setWindowFlags(self.list_widget.windowFlags() | Qt.Popup | Qt.FramelessWindowHint)
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        self.list_widget.setAttribute(Qt.WA_ShowWithoutActivating)
        # Forward keypresses from the popup back to the line edit so typing continues
        self.list_widget.installEventFilter(self)
        self.list_widget.hide()
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.line_edit)
        self.setLayout(layout)
        self.countries = sorted([c.name for c in pycountry.countries])
        self.line_edit.textEdited.connect(self._on_text_edited)
        self.list_widget.itemClicked.connect(self._on_item_clicked)

    def _on_text_edited(self, _):
        text = self.line_edit.text().strip().lower()
        self.list_widget.clear()
        if not text:
            self.list_widget.hide()
            return
        matches = [c for c in self.countries if text in c.lower()]
        for country in matches[:20]:
            item = QListWidgetItem(country)
            self.list_widget.addItem(item)
        if matches:
            self.position_popup()
            self.list_widget.show()
        else:
            self.list_widget.hide()

    def position_popup(self):
        global_pos = self.line_edit.mapToGlobal(self.line_edit.rect().bottomLeft())
        self.list_widget.move(global_pos)
        # Keep the popup from covering the input and use a sensible width
        target_width = max(self.line_edit.width(), 280)
        self.list_widget.resize(target_width, min(200, 20 * self.list_widget.count() + 4))

    def eventFilter(self, obj, event):
        # Forward ordinary key events from the popup to the line edit so typing continues
        if obj is self.list_widget and event.type() == QEvent.KeyPress:
            key = event.key()
            if key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Escape, Qt.Key_Tab):
                return False
            QApplication.sendEvent(self.line_edit, event)
            return True
        return super().eventFilter(obj, event)
        self.list_widget.resize(self.line_edit.width()*2, 180)

    def _on_item_clicked(self, item):
        country = item.text()
        self.line_edit.setText(country)
        self.list_widget.hide()
        self.countrySelected.emit(country)

    def text(self):
        return self.line_edit.text()

    def setText(self, value: str):
        self.line_edit.setText(value)

    def clear(self):
        self.line_edit.clear()
        self.list_widget.hide()
