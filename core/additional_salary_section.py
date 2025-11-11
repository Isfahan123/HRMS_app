from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QFormLayout, QDoubleSpinBox, QHBoxLayout
# from .monthly_deductions_section import build_monthly_deductions_section  # deprecated

def build_additional_salary_section(dialog, parent_layout):
    """Mirror dialog.create_malaysian_additional_salary_section using dialog.fields."""
    additional_group = QGroupBox("🎁 SARAAN TAMBAHAN BULAN SEMASA - Additional Monthly Salary")
    additional_layout = QVBoxLayout()

    additional_grid = QHBoxLayout()
    additional_grid.setSpacing(20)

    # Column 1
    col1 = QFormLayout()
    dialog.fields["arrears"] = QDoubleSpinBox()
    dialog.fields["arrears"].setRange(0.0, 999999.99)
    dialog.fields["arrears"].setSuffix(" RM")
    col1.addRow("Tunggakan:", dialog.fields["arrears"])

    dialog.fields["commission"] = QDoubleSpinBox()
    dialog.fields["commission"].setRange(0.0, 999999.99)
    dialog.fields["commission"].setSuffix(" RM")
    col1.addRow("Komisen (tidak bulanan):", dialog.fields["commission"])

    # Column 2
    col2 = QFormLayout()
    dialog.fields["rewards"] = QDoubleSpinBox()
    dialog.fields["rewards"].setRange(0.0, 999999.99)
    dialog.fields["rewards"].setSuffix(" RM")
    col2.addRow("Ganjaran:", dialog.fields["rewards"])

    dialog.fields["compensation"] = QDoubleSpinBox()
    dialog.fields["compensation"].setRange(0.0, 999999.99)
    dialog.fields["compensation"].setSuffix(" RM")
    col2.addRow("Pampasan:", dialog.fields["compensation"])

    dialog.fields["director_fees"] = QDoubleSpinBox()
    dialog.fields["director_fees"].setRange(0.0, 999999.99)
    dialog.fields["director_fees"].setSuffix(" RM")
    col2.addRow("Yuran Pengarah:", dialog.fields["director_fees"])

    # Column 3
    col3 = QFormLayout()
    dialog.fields["tax_borne_by_employer"] = QDoubleSpinBox()
    dialog.fields["tax_borne_by_employer"].setRange(0.0, 999999.99)
    dialog.fields["tax_borne_by_employer"].setSuffix(" RM")
    col3.addRow("Cukai Ditanggung Majikan:", dialog.fields["tax_borne_by_employer"])

    dialog.fields["others_additional"] = QDoubleSpinBox()
    dialog.fields["others_additional"].setRange(0.0, 999999.99)
    dialog.fields["others_additional"].setSuffix(" RM")
    col3.addRow("Lain-lain:", dialog.fields["others_additional"])

    dialog.fields["epf_additional"] = QDoubleSpinBox()
    dialog.fields["epf_additional"].setRange(0.0, 4000.0)
    dialog.fields["epf_additional"].setSuffix(" RM")
    dialog.fields["epf_additional"].setToolTip("Compulsory EPF contribution from payroll (PCB calculation uses max RM4,000 only)")
    dialog.fields["epf_additional"].valueChanged.connect(dialog.validate_epf_insurance_limit)
    col3.addRow("KWSP Wajib (PCB: ≤ RM4,000):", dialog.fields["epf_additional"])

    additional_grid.addLayout(col1)
    additional_grid.addLayout(col2)
    additional_grid.addLayout(col3)

    additional_layout.addLayout(additional_grid)
    additional_group.setLayout(additional_layout)
    parent_layout.addWidget(additional_group)

    # Monthly deductions (Potongan Bulan Semasa) deprecated: moved to Admin TP1 reliefs; UI suppressed.
    # build_monthly_deductions_section(dialog, parent_layout)
