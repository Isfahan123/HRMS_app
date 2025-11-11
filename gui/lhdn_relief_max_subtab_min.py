from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QGroupBox, QFormLayout, QDoubleSpinBox
from PyQt5.QtCore import Qt


def _ensure_hpb_inputs(admin) -> QWidget:
    """Create essential HPB input widgets on admin if missing and return a content widget.

    This defines the attributes expected by save/load methods in admin_payroll_tab:
    - B-codes: lhdn_b1_individual_relief, lhdn_b4_individual_disability, lhdn_b14_spouse_relief,
      lhdn_b15_disabled_spouse_relief, lhdn_b16_children_under_18, lhdn_b16_children_study_malaysia,
      lhdn_b16_children_higher_education, lhdn_b16_disabled_not_studying, lhdn_b16_disabled_studying,
      lhdn_b17_mandatory_epf, lhdn_b20_perkeso
    - Categories and caps used in save_potongan_max_configuration
    """
    def spin(name, minv, maxv, val):
        if not hasattr(admin, name):
            sb = QDoubleSpinBox()
            sb.setRange(float(minv), float(maxv))
            sb.setValue(float(val))
            sb.setSuffix(" RM")
            sb.setMinimumWidth(140)
            setattr(admin, name, sb)
        return getattr(admin, name)

    # B-codes group
    b_group = QGroupBox("B-codes (Reliefs Automatik)")
    b_form = QFormLayout()
    b_form.addRow("B1 Individu:", spin('lhdn_b1_individual_relief', 0, 15000, 9000))
    b_form.addRow("B4 Individu OKU:", spin('lhdn_b4_individual_disability', 0, 10000, 6000))
    b_form.addRow("B14 Pasangan:", spin('lhdn_b14_spouse_relief', 0, 10000, 4000))
    b_form.addRow("B15 Pasangan OKU:", spin('lhdn_b15_disabled_spouse_relief', 0, 10000, 5000))
    b_form.addRow("B16 Anak <18:", spin('lhdn_b16_children_under_18', 0, 5000, 2000))
    b_form.addRow("B16 Anak 18+ Matrik/MY:", spin('lhdn_b16_children_study_malaysia', 0, 5000, 2000))
    b_form.addRow("B16 Anak 18+ Diploma/Degree:", spin('lhdn_b16_children_higher_education', 0, 10000, 8000))
    b_form.addRow("B16 OKU tidak belajar:", spin('lhdn_b16_disabled_not_studying', 0, 10000, 6000))
    b_form.addRow("B16 OKU sedang belajar:", spin('lhdn_b16_disabled_studying', 0, 20000, 14000))
    b_form.addRow("B17 KWSP wajib:", spin('lhdn_b17_mandatory_epf', 0, 10000, 4000))
    b_form.addRow("B20 PERKESO:", spin('lhdn_b20_perkeso', 0, 500, 350))
    b_group.setLayout(b_form)

    # Parent/medical category
    med_group = QGroupBox("Perubatan Diri/Pasangan/Anak")
    med_form = QFormLayout()
    med_form.addRow("MAX CAP:", spin('medical_family_max_cap', 0, 20000, 10000))
    med_form.addRow("Penyakit serius:", spin('serious_disease_max', 0, 10000, 10000))
    med_form.addRow("Rawatan kesuburan:", spin('fertility_treatment_max', 0, 5000, 5000))
    med_form.addRow("Vaksin:", spin('vaccination_max', 0, 1000, 1000))
    med_form.addRow("Rawatan pergigian:", spin('dental_treatment_max', 0, 1000, 1000))
    med_form.addRow("Pemeriksaan kesihatan:", spin('health_checkup_max', 0, 1000, 1000))
    med_form.addRow("Anak kurang upaya pembelajaran:", spin('child_learning_disability_max', 0, 6000, 6000))
    med_group.setLayout(med_form)

    # Lifestyle basic
    life_basic = QGroupBox("Gaya Hidup Asas")
    lb_form = QFormLayout()
    lb_form.addRow("MAX CAP:", spin('lifestyle_basic_max_cap', 0, 3000, 2500))
    lb_form.addRow("Buku & majalah:", spin('lifestyle_books_max', 0, 2500, 2500))
    lb_form.addRow("Komputer/telefon:", spin('lifestyle_computer_max', 0, 2500, 2500))
    lb_form.addRow("Internet:", spin('lifestyle_internet_max', 0, 2500, 2500))
    lb_form.addRow("Kursus kemahiran:", spin('lifestyle_skills_max', 0, 2000, 2000))
    life_basic.setLayout(lb_form)

    # Lifestyle additional
    life_add = QGroupBox("Gaya Hidup Tambahan")
    la_form = QFormLayout()
    la_form.addRow("MAX CAP:", spin('lifestyle_additional_max_cap', 0, 2000, 1000))
    la_form.addRow("Peralatan sukan:", spin('sports_equipment_max', 0, 1000, 1000))
    la_form.addRow("Sewa fasiliti sukan:", spin('sports_facility_rent_max', 0, 1000, 1000))
    la_form.addRow("Fi pertandingan:", spin('competition_fees_max', 0, 1000, 1000))
    la_form.addRow("Yuran gym:", spin('gym_fees_max', 0, 1000, 1000))
    life_add.setLayout(la_form)

    # Other categories
    other = QGroupBox("Lain-lain")
    o_form = QFormLayout()
    o_form.addRow("Peralatan penyusuan:", spin('breastfeeding_equipment_max', 0, 1000, 1000))
    o_form.addRow("Yuran taska:", spin('childcare_fees_max', 0, 3000, 3000))
    o_form.addRow("Simpanan SSPN:", spin('sspn_savings_max', 0, 8000, 8000))
    o_form.addRow("Nafkah (alimony):", spin('alimony_max', 0, 10000, 0))
    # EPF + Life combined
    o_form.addRow("EPF+Insurans (combined):", spin('epf_insurance_combined_max', 0, 7000, 7000))
    o_form.addRow("Sub-had EPF (shared):", spin('epf_shared_subcap', 0, 7000, 4000))
    o_form.addRow("Sub-had Insurans Hayat:", spin('life_insurance_subcap', 0, 7000, 3000))
    # PRS & others
    o_form.addRow("PRS/Anuiti:", spin('prs_annuity_max', 0, 3000, 3000))
    o_form.addRow("Insurans Pendidikan/Perubatan:", spin('education_medical_insurance_max', 0, 8000, 3000))
    o_form.addRow("Pengecas EV:", spin('ev_charger_max', 0, 2500, 2500))
    # Housing loan interest caps
    o_form.addRow("Faedah rumah <500k:", spin('housing_loan_under_500k_max', 0, 10000, 10000))
    o_form.addRow("Faedah rumah 500k-750k:", spin('housing_loan_500k_750k_max', 0, 10000, 10000))
    other.setLayout(o_form)

    # Compose content
    content = QWidget()
    v = QVBoxLayout(content)
    v.addWidget(b_group)
    v.addWidget(med_group)
    v.addWidget(life_basic)
    v.addWidget(life_add)
    v.addWidget(other)
    v.addStretch()
    return content


def build_tax_relief_max_subtab(admin, subtab_widget):
    """Minimal 'Had Potongan Bulanan' subtab wiring Save/Load/Reset/Export to admin methods."""
    relief_tab = QWidget()
    layout = QVBoxLayout(relief_tab)

    header = QLabel("💼 Had Potongan Bulanan (HPB) — Konfigurasi Had & Sub-Had")
    header.setStyleSheet("QLabel { font-weight: bold; padding: 6px; }")
    layout.addWidget(header)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    content = getattr(admin, 'hpb_content_widget', None)
    if content is None:
        content = _ensure_hpb_inputs(admin)
        admin.hpb_content_widget = content
    scroll.setWidget(content)
    layout.addWidget(scroll)

    actions = QHBoxLayout()
    btn_reset = QPushButton("↺ Set Semula ke Had LHDN")
    btn_reset.clicked.connect(admin.reset_potongan_max_to_default)
    actions.addWidget(btn_reset)

    btn_save = QPushButton("💾 Simpan Konfigurasi Had")
    btn_save.clicked.connect(admin.save_potongan_max_configuration)
    actions.addWidget(btn_save)

    btn_load = QPushButton("↻ Muat Konfigurasi Had")
    btn_load.clicked.connect(admin.load_potongan_max_configuration)
    actions.addWidget(btn_load)

    btn_export = QPushButton("📤 Eksport Konfigurasi")
    btn_export.clicked.connect(admin.export_potongan_configuration)
    actions.addWidget(btn_export)

    actions.addStretch()
    layout.addLayout(actions)

    subtab_widget.addTab(relief_tab, "💼 Had Potongan Bulanan")
