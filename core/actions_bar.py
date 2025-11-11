from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton

class ProfileActionsBar(QWidget):
    """Reusable actions bar for Admin Profile tab."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(12)

        self.add_btn = QPushButton("➕ Add New Employee")
        self.add_btn.setProperty("class", "primary")
        layout.addWidget(self.add_btn)

        self.download_all_btn = QPushButton("📥 Download All PDFs")
        layout.addWidget(self.download_all_btn)

        self.print_all_btn = QPushButton("🖨️ Print All Profiles")
        layout.addWidget(self.print_all_btn)

        layout.addStretch()
