"""DEPRECATED: Former Potongan Bulan Semasa (monthly deduction max-cap) admin subtab.

All per-item relief capture and statutory caps are now enforced internally via the TP1
relief dialog and calculation engine. This file is intentionally minimal to satisfy
any lingering imports until the admin tab code is fully purged of references. It can
be deleted outright once `admin_payroll_tab.py` no longer calls `build_tax_relief_max_subtab`.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

__all__ = ["build_tax_relief_max_subtab"]

def build_tax_relief_max_subtab(admin, subtab_widget):  # pragma: no cover - trivial stub
    """Attach a single deprecation notice tab (safe placeholder)."""
    if subtab_widget is None:  # defensive
        return
    tab = QWidget()
    layout = QVBoxLayout(tab)
    msg = QLabel(
        "<b>Potongan Bulan Semasa UI Removed.</b><br>"
        "Use TP1 Relief dialog for all claims. Max caps now internal."
    )
    msg.setWordWrap(True)
    msg.setAlignment(Qt.AlignTop)
    layout.addWidget(msg)
    subtab_widget.addTab(tab, "💼 Had Potongan Bulanan")
