from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QFormLayout,
    QScrollArea, QPushButton, QDoubleSpinBox, QSpinBox
)
from PyQt5.QtCore import Qt


def build_tax_rates_subtab(admin, subtab_widget):
    """Build the Tax Rates subtab and add it to subtab_widget.
    Uses helper methods on the admin instance (create_tax_bracket_input_group,
    toggle_tax_rates_editing, reset_tax_rates_to_default, save_tax_brackets_configuration,
    test_tax_rates_calculation).
    """
    try:
        rates_tab = QWidget()

        # Create scroll area for the subtab
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Main widget inside scroll area
        main_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Tax Rate Information Panel
        info_group = QGroupBox("Malaysian Personal Income Tax Rates (Assessment Year 2023, 2024 & 2025)")
        info_layout = QVBoxLayout()

        info_text = QLabel(
            """
<b>LHDN Progressive Tax System 2025:</b><br>
• <b>Tax Year:</b> Assessment Year 2025 (Income Year 2024)<br>
• <b>Progressive Rates:</b> 0% to 30% across multiple tax brackets<br>
• <b>Non-Resident Rate:</b> Flat 30% on total income<br><br>

<b>Reference:</b> <a href=\"https://www.hasil.gov.my/en/individual/individual-life-cycle/how-to-declare-income/tax-rate/\">HASIL Official Tax Rates</a>
            """
        )
        info_text.setWordWrap(True)
        info_text.setOpenExternalLinks(True)
        info_text.setStyleSheet(
            "QLabel { font-size: 11px; padding: 15px; background-color: #f0f8ff; border: 1px solid #ccc; border-radius: 5px; }"
        )
        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Tax Brackets Configuration
        brackets_group = QGroupBox("Tax Brackets Configuration")
        brackets_layout = QVBoxLayout()

        # Create a scroll area for tax brackets
        brackets_scroll = QScrollArea()
        brackets_scroll.setWidgetResizable(True)
        brackets_scroll.setMaximumHeight(400)

        # Widget to contain all tax bracket input groups
        brackets_container = QWidget()
        brackets_container_layout = QVBoxLayout()

        # Create tax bracket input groups
        admin.tax_bracket_inputs = []

        # Default LHDN tax brackets for initialization
        default_brackets = [
            {"from": 0, "to": 5000, "on_first": 0, "next": 0, "rate": 0, "tax_first": 0, "tax_next": 0},
            {"from": 5001, "to": 20000, "on_first": 5000, "next": 15000, "rate": 1, "tax_first": 0, "tax_next": 150},
            {"from": 20001, "to": 35000, "on_first": 20000, "next": 15000, "rate": 3, "tax_first": 150, "tax_next": 450},
            {"from": 35001, "to": 50000, "on_first": 35000, "next": 15000, "rate": 6, "tax_first": 600, "tax_next": 900},
            {"from": 50001, "to": 70000, "on_first": 50000, "next": 20000, "rate": 11, "tax_first": 1500, "tax_next": 2200},
            {"from": 70001, "to": 100000, "on_first": 70000, "next": 30000, "rate": 19, "tax_first": 3700, "tax_next": 5700},
            {"from": 100001, "to": 400000, "on_first": 100000, "next": 300000, "rate": 25, "tax_first": 9400, "tax_next": 75000},
            {"from": 400001, "to": 600000, "on_first": 400000, "next": 200000, "rate": 26, "tax_first": 84400, "tax_next": 52000},
            {"from": 600001, "to": 2000000, "on_first": 600000, "next": 1400000, "rate": 28, "tax_first": 136400, "tax_next": 392000},
            {"from": 2000001, "to": 999999999, "on_first": 2000000, "next": 0, "rate": 30, "tax_first": 528400, "tax_next": 0},
        ]

        for i, bracket in enumerate(default_brackets):
            bracket_group = admin.create_tax_bracket_input_group(i + 1, bracket)
            brackets_container_layout.addWidget(bracket_group)

        # Add button to add new bracket
        add_bracket_button = QPushButton("➕ Add Tax Bracket")
        add_bracket_button.clicked.connect(admin.add_new_tax_bracket)
        brackets_container_layout.addWidget(add_bracket_button)

        brackets_container.setLayout(brackets_container_layout)
        brackets_scroll.setWidget(brackets_container)
        brackets_layout.addWidget(brackets_scroll)

        # Special provisions
        special_group = QGroupBox("Special Tax Provisions")
        special_layout = QFormLayout()

        # Individual Tax Rebate
        admin.individual_tax_rebate = QDoubleSpinBox()
        admin.individual_tax_rebate.setRange(0.0, 10000.0)
        admin.individual_tax_rebate.setValue(400.0)
        admin.individual_tax_rebate.setSuffix(" RM")
        admin.individual_tax_rebate.setToolTip("Individual tax rebate amount (LHDN 2025: RM 400)")
        special_layout.addRow("Individual Tax Rebate:", admin.individual_tax_rebate)

        # Rebate threshold (annual chargeable income at/under which individual rebate applies)
        admin.rebate_threshold = QSpinBox()
        admin.rebate_threshold.setRange(0, 1000000)
        admin.rebate_threshold.setSingleStep(500)
        admin.rebate_threshold.setValue(35000)
        admin.rebate_threshold.setSuffix(" RM")
        admin.rebate_threshold.setToolTip("Annual chargeable income threshold to apply individual rebate (default RM 35,000)")
        special_layout.addRow("Rebate Threshold (Annual):", admin.rebate_threshold)

        # Non-resident rate
        admin.lhdn_non_resident_rate = QDoubleSpinBox()
        admin.lhdn_non_resident_rate.setRange(0.0, 100.0)
        admin.lhdn_non_resident_rate.setValue(30.0)
        admin.lhdn_non_resident_rate.setSuffix(" %")
        admin.lhdn_non_resident_rate.setToolTip("Flat tax rate for non-residents (LHDN 2025: 30%)")
        special_layout.addRow("Non-Resident Tax Rate:", admin.lhdn_non_resident_rate)

        special_group.setLayout(special_layout)
        brackets_layout.addWidget(special_group)

        brackets_group.setLayout(brackets_layout)
        layout.addWidget(brackets_group)

        # Action buttons for tax rates
        rates_buttons_layout = QHBoxLayout()

        edit_rates_button = QPushButton("🔧 Toggle Input Fields")
        edit_rates_button.clicked.connect(admin.toggle_tax_rates_editing)
        rates_buttons_layout.addWidget(edit_rates_button)

        reset_rates_button = QPushButton("↺ Reset to LHDN Default")
        reset_rates_button.clicked.connect(admin.reset_tax_rates_to_default)
        rates_buttons_layout.addWidget(reset_rates_button)

        save_brackets_button = QPushButton("💾 Save Tax Brackets")
        save_brackets_button.clicked.connect(admin.save_tax_brackets_configuration)
        rates_buttons_layout.addWidget(save_brackets_button)

        test_rates_button = QPushButton("🧮 Test Tax Calculation")
        test_rates_button.clicked.connect(admin.test_tax_rates_calculation)
        rates_buttons_layout.addWidget(test_rates_button)

        rates_buttons_layout.addStretch()
        layout.addLayout(rates_buttons_layout)

        # Set layout and add to scroll area
        main_widget.setLayout(layout)
        scroll_area.setWidget(main_widget)

        # Create the rates tab layout
        rates_tab_layout = QVBoxLayout()
        rates_tab_layout.setContentsMargins(0, 0, 0, 0)
        rates_tab_layout.addWidget(scroll_area)
        rates_tab.setLayout(rates_tab_layout)

        subtab_widget.addTab(rates_tab, "📊 Tax Rates")

    except Exception as e:
        # Defer UI error to admin Warning to keep consistent UX
        try:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(admin, "Error", f"Failed to create tax rates subtab: {e}")
        except Exception:
            # Last resort: print
            print(f"DEBUG: Error creating tax rates subtab: {e}")
