from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel
from .lhdn_tax_rates_subtab import build_tax_rates_subtab
from .lhdn_relief_max_subtab_min import build_tax_relief_max_subtab
from .relief_overrides_subtab import build_relief_overrides_subtab  # NEW: ensure overrides tab added

# This module hosts LHDN Tax Config tab builders. Functions are thin wrappers
# that create the container/tab structure and delegate subtab content back
# into the AdminPayrollTab instance to keep UI and state unchanged.

def add_lhdn_tax_config_tab(admin, tab_widget):
    """Create the top-level LHDN Tax tab with its subtabs and add to tab_widget.

    Sets admin.lhdn_subtab_widget and admin.tax_relief_subtab_index for
    resident/non-resident visibility toggling elsewhere in the class.
    """
    # Create the top-level LHDN tab container
    lhdn_tab = QWidget()
    lhdn_layout = QVBoxLayout(lhdn_tab)

    # Optional header/description (kept minimal to avoid changing UX)
    header = QLabel("🏛️ LHDN Tax Configuration")
    header.setObjectName("lhdnHeaderLabel")
    header.setStyleSheet("QLabel#lhdnHeaderLabel { font-weight: bold; padding: 4px; }")
    lhdn_layout.addWidget(header)

    # Subtabs container
    subtab_widget = QTabWidget()
    lhdn_layout.addWidget(subtab_widget)

    # Expose the subtab widget on the admin instance for later control
    admin.lhdn_subtab_widget = subtab_widget

    # Add subtabs in order: Tax Rates, Relief Max, Config
    # 1) Tax Rates
    build_tax_rates_subtab(admin, subtab_widget)

    # 2) Tax Relief Max — capture index for resident toggle logic
    count_before = subtab_widget.count()
    build_tax_relief_max_subtab(admin, subtab_widget)
    # Relief tab will be appended as last; index is count_before (after append it's at count_before)
    # If any unexpected behavior, fall back to last index
    relief_index = count_before if subtab_widget.count() > count_before else subtab_widget.count() - 1
    if relief_index < 0:
        relief_index = 0
    admin.tax_relief_subtab_index = relief_index

    # 3) Relief Overrides (caps / pcb-only / cycle edits) – appended after stubbed max-cap tab
    try:
        build_relief_overrides_subtab(admin, subtab_widget)
    except Exception as e:
        # Non-fatal; leave visible in logs for troubleshooting
        print(f"DEBUG: Failed to build Relief Overrides subtab (lhdn_tax_config_tab): {e}")

    # Configuration subtab removed per request

    # Finally add top-level tab
    tab_widget.addTab(lhdn_tab, "🏛️ LHDN Tax")

def add_tax_rates_subtab(admin, subtab_widget):
    # Backward-compat wrapper in case other code calls this
    return build_tax_rates_subtab(admin, subtab_widget)

def add_tax_relief_max_subtab(admin, subtab_widget):
    return build_tax_relief_max_subtab(admin, subtab_widget)

# Configuration subtab intentionally removed
