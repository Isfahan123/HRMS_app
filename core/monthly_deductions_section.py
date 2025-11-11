from PyQt5.QtWidgets import (
  QGroupBox,
  QVBoxLayout,
  QLabel,
  QFormLayout,
  QHBoxLayout,
  QDoubleSpinBox,
  QWidget,
)


def build_monthly_deductions_section(dialog, parent_layout):
  """Create Malaysian monthly deductions section - mirrors original dialog implementation."""
  dialog.deductions_group = QGroupBox("✂️ POTONGAN BULAN SEMASA - Monthly Deductions (with sub-caps)")
  deductions_layout = QVBoxLayout()

  columns_widget = QWidget()
  columns_layout = QHBoxLayout(columns_widget)
  columns_layout.setSpacing(15)

  # LEFT COLUMN - Categories 1-5
  left_column = QWidget()
  left_layout = QVBoxLayout(left_column)

  # 1. Parent medical (admin MAX CAP)
  parent_medical_max = dialog.admin_max_caps.get('parent_medical_max', 8000.0)
  parent_medical_group = QGroupBox(f"1. Perbelanjaan untuk ibu bapa / datuk nenek (≤ RM{parent_medical_max:,.0f} setahun)")
  parent_medical_form = QFormLayout()

  dialog.fields["parent_medical_treatment"] = QDoubleSpinBox()
  treatment_max = dialog.admin_max_caps.get('parent_medical_treatment_max', 8000.0)
  dialog.fields["parent_medical_treatment"].setRange(0.0, treatment_max)
  dialog.fields["parent_medical_treatment"].setSuffix(" RM")
  dialog.fields["parent_medical_treatment"].setToolTip(f"LHDN default: RM8,000, Admin MAX CAP: RM{treatment_max:,.0f}")
  parent_medical_form.addRow("a) Rawatan perubatan/keperluan khas/penjagaan:", dialog.fields["parent_medical_treatment"])

  dialog.fields["parent_dental"] = QDoubleSpinBox()
  dental_max = dialog.admin_max_caps.get('parent_dental_max', 8000.0)
  dialog.fields["parent_dental"].setRange(0.0, dental_max)
  dialog.fields["parent_dental"].setSuffix(" RM")
  dialog.fields["parent_dental"].setToolTip(f"LHDN default: RM8,000, Admin MAX CAP: RM{dental_max:,.0f}")
  parent_medical_form.addRow("b) Rawatan pergigian:", dialog.fields["parent_dental"])

  dialog.fields["parent_checkup_vaccine"] = QDoubleSpinBox()
  checkup_max = dialog.admin_max_caps.get('parent_checkup_vaccine_max', 1000.0)
  dialog.fields["parent_checkup_vaccine"].setRange(0.0, checkup_max)
  dialog.fields["parent_checkup_vaccine"].setSuffix(" RM")
  dialog.fields["parent_checkup_vaccine"].setToolTip(f"LHDN default: RM1,000, Admin MAX CAP: RM{checkup_max:,.0f}")
  parent_medical_form.addRow("c) Pemeriksaan penuh + vaksin (≤ RM1,000):", dialog.fields["parent_checkup_vaccine"])

  parent_medical_group.setLayout(parent_medical_form)
  left_layout.addWidget(parent_medical_group)

  # 2. Basic support equipment
  support_max = dialog.admin_max_caps.get('basic_support_equipment_max', 6000.0)
  support_group = QGroupBox(f"2. Peralatan sokongan asas (≤ RM{support_max:,.0f})")
  support_form = QFormLayout()
  dialog.fields["basic_support_equipment"] = QDoubleSpinBox()
  dialog.fields["basic_support_equipment"].setRange(0.0, support_max)
  dialog.fields["basic_support_equipment"].setSuffix(" RM")
  dialog.fields["basic_support_equipment"].setToolTip(f"LHDN default: RM6,000, Admin MAX CAP: RM{support_max:,.0f}")
  support_form.addRow("Peralatan sokongan asas:", dialog.fields["basic_support_equipment"])
  support_group.setLayout(support_form)
  left_layout.addWidget(support_group)

  # 3. Education
  education_group = QGroupBox("3. Yuran pengajian sendiri (uses admin MAX CAP)")
  education_form = QFormLayout()

  dialog.fields["education_non_masters"] = QDoubleSpinBox()
  education_non_masters_max = dialog.admin_max_caps.get('education_non_masters_max', 7000.0)
  dialog.fields["education_non_masters"].setRange(0.0, education_non_masters_max)
  dialog.fields["education_non_masters"].setSuffix(" RM")
  dialog.fields["education_non_masters"].setToolTip(f"LHDN default: RM7,000, Admin MAX CAP: RM{education_non_masters_max:,.0f}")
  education_form.addRow("a) Selain Sarjana/PhD (bidang tertentu):", dialog.fields["education_non_masters"])

  dialog.fields["education_masters_phd"] = QDoubleSpinBox()
  education_masters_phd_max = dialog.admin_max_caps.get('education_masters_phd_max', 7000.0)
  dialog.fields["education_masters_phd"].setRange(0.0, education_masters_phd_max)
  dialog.fields["education_masters_phd"].setSuffix(" RM")
  dialog.fields["education_masters_phd"].setToolTip(f"LHDN default: RM7,000, Admin MAX CAP: RM{education_masters_phd_max:,.0f}")
  education_form.addRow("b) Sarjana/PhD (semua bidang):", dialog.fields["education_masters_phd"])

  dialog.fields["skills_course"] = QDoubleSpinBox()
  skills_course_max = dialog.admin_max_caps.get('skills_course_max', 2000.0)
  dialog.fields["skills_course"].setRange(0.0, skills_course_max)
  dialog.fields["skills_course"].setSuffix(" RM")
  dialog.fields["skills_course"].setToolTip(f"LHDN default: RM2,000, Admin MAX CAP: RM{skills_course_max:,.0f}")
  education_form.addRow("c) Kursus kemahiran/diri (≤ RM2,000):", dialog.fields["skills_course"])

  education_group.setLayout(education_form)
  left_layout.addWidget(education_group)

  # 4. Medical family
  medical_group = QGroupBox("4. Perubatan diri/pasangan/anak (uses admin MAX CAP)")
  medical_form = QFormLayout()

  dialog.fields["serious_disease"] = QDoubleSpinBox()
  serious_disease_max = dialog.admin_max_caps.get('serious_disease_max', 10000.0)
  dialog.fields["serious_disease"].setRange(0.0, serious_disease_max)
  dialog.fields["serious_disease"].setSuffix(" RM")
  medical_form.addRow("a) Penyakit serius:", dialog.fields["serious_disease"])

  dialog.fields["fertility_treatment"] = QDoubleSpinBox()
  dialog.fields["fertility_treatment"].setRange(0.0, 1000.0)
  dialog.fields["fertility_treatment"].setSuffix(" RM")
  medical_form.addRow("b) Rawatan kesuburan:", dialog.fields["fertility_treatment"])

  dialog.fields["vaccination"] = QDoubleSpinBox()
  dialog.fields["vaccination"].setRange(0.0, 1000.0)
  dialog.fields["vaccination"].setSuffix(" RM")
  medical_form.addRow("c) Pemvaksinan (≤ RM1,000):", dialog.fields["vaccination"])

  dialog.fields["dental_treatment"] = QDoubleSpinBox()
  dialog.fields["dental_treatment"].setRange(0.0, 1000.0)
  dialog.fields["dental_treatment"].setSuffix(" RM")
  medical_form.addRow("d) Pemeriksaan & rawatan pergigian (≤ RM1,000):", dialog.fields["dental_treatment"])

  dialog.fields["health_checkup"] = QDoubleSpinBox()
  dialog.fields["health_checkup"].setRange(0.0, 1000.0)
  dialog.fields["health_checkup"].setSuffix(" RM")
  medical_form.addRow("e) Pemeriksaan penuh/COVID-19/mental health (≤ RM1,000):", dialog.fields["health_checkup"])

  dialog.fields["child_learning_disability"] = QDoubleSpinBox()
  dialog.fields["child_learning_disability"].setRange(0.0, 6000.0)
  dialog.fields["child_learning_disability"].setSuffix(" RM")
  medical_form.addRow("f) Anak kurang upaya pembelajaran <18 (≤ RM6,000):", dialog.fields["child_learning_disability"])

  medical_group.setLayout(medical_form)
  left_layout.addWidget(medical_group)

  # 5. Lifestyle basic
  lifestyle_basic_group = QGroupBox("5. Gaya hidup asas (≤ RM2,500)")
  lifestyle_basic_form = QFormLayout()
  dialog.fields["lifestyle_books"] = QDoubleSpinBox()
  dialog.fields["lifestyle_books"].setRange(0.0, 2500.0)
  dialog.fields["lifestyle_books"].setSuffix(" RM")
  lifestyle_basic_form.addRow("a) Buku/majalah/surat khabar:", dialog.fields["lifestyle_books"])

  dialog.fields["lifestyle_computer"] = QDoubleSpinBox()
  dialog.fields["lifestyle_computer"].setRange(0.0, 2500.0)
  dialog.fields["lifestyle_computer"].setSuffix(" RM")
  lifestyle_basic_form.addRow("b) Komputer/telefon/tablet:", dialog.fields["lifestyle_computer"])

  dialog.fields["lifestyle_internet"] = QDoubleSpinBox()
  dialog.fields["lifestyle_internet"].setRange(0.0, 2500.0)
  dialog.fields["lifestyle_internet"].setSuffix(" RM")
  lifestyle_basic_form.addRow("c) Internet (nama sendiri):", dialog.fields["lifestyle_internet"])

  dialog.fields["lifestyle_skills"] = QDoubleSpinBox()
  dialog.fields["lifestyle_skills"].setRange(0.0, 2500.0)
  dialog.fields["lifestyle_skills"].setSuffix(" RM")
  lifestyle_basic_form.addRow("d) Kursus kemahiran:", dialog.fields["lifestyle_skills"])

  lifestyle_basic_group.setLayout(lifestyle_basic_form)
  left_layout.addWidget(lifestyle_basic_group)

  columns_layout.addWidget(left_column)

  # RIGHT COLUMN - Categories 6-16
  right_column = QWidget()
  right_layout = QVBoxLayout(right_column)

  lifestyle_additional_group = QGroupBox("6. Gaya hidup tambahan (≤ RM1,000)")
  lifestyle_additional_form = QFormLayout()
  dialog.fields["sports_equipment"] = QDoubleSpinBox()
  dialog.fields["sports_equipment"].setRange(0.0, 1000.0)
  dialog.fields["sports_equipment"].setSuffix(" RM")
  lifestyle_additional_form.addRow("a) Peralatan sukan:", dialog.fields["sports_equipment"])

  dialog.fields["sports_facility_rent"] = QDoubleSpinBox()
  dialog.fields["sports_facility_rent"].setRange(0.0, 1000.0)
  dialog.fields["sports_facility_rent"].setSuffix(" RM")
  lifestyle_additional_form.addRow("b) Sewa/fi fasiliti sukan:", dialog.fields["sports_facility_rent"])

  dialog.fields["competition_fees"] = QDoubleSpinBox()
  dialog.fields["competition_fees"].setRange(0.0, 1000.0)
  dialog.fields["competition_fees"].setSuffix(" RM")
  lifestyle_additional_form.addRow("c) Fi pertandingan diluluskan:", dialog.fields["competition_fees"])

  dialog.fields["gym_fees"] = QDoubleSpinBox()
  dialog.fields["gym_fees"].setRange(0.0, 1000.0)
  dialog.fields["gym_fees"].setSuffix(" RM")
  lifestyle_additional_form.addRow("d) Yuran gym/latihan sukan:", dialog.fields["gym_fees"])

  lifestyle_additional_group.setLayout(lifestyle_additional_form)
  right_layout.addWidget(lifestyle_additional_group)

  # Remaining deductions groups (7-18)
  dialog.breastfeeding_group = QGroupBox("7. Peralatan penyusuan ibu (≤ RM1,000, sekali setiap 2 tahun)")
  breastfeeding_form = QFormLayout()
  dialog.fields["breastfeeding_equipment"] = QDoubleSpinBox()
  dialog.fields["breastfeeding_equipment"].setRange(0.0, 1000.0)
  dialog.fields["breastfeeding_equipment"].setSuffix(" RM")
  breastfeeding_form.addRow("Peralatan penyusuan:", dialog.fields["breastfeeding_equipment"])
  dialog.breastfeeding_group.setLayout(breastfeeding_form)
  right_layout.addWidget(dialog.breastfeeding_group)

  dialog.childcare_group = QGroupBox("8. Yuran taska/tadika anak ≤ 6 tahun (≤ RM3,000)")
  childcare_form = QFormLayout()
  dialog.fields["childcare_fees"] = QDoubleSpinBox()
  dialog.fields["childcare_fees"].setRange(0.0, 3000.0)
  dialog.fields["childcare_fees"].setSuffix(" RM")
  childcare_form.addRow("Yuran taska/tadika:", dialog.fields["childcare_fees"])
  dialog.childcare_group.setLayout(childcare_form)
  right_layout.addWidget(dialog.childcare_group)

  dialog.sspn_group = QGroupBox("9. SSPN (tabungan bersih) (≤ RM8,000)")
  sspn_form = QFormLayout()
  dialog.fields["sspn_savings"] = QDoubleSpinBox()
  dialog.fields["sspn_savings"].setRange(0.0, 8000.0)
  dialog.fields["sspn_savings"].setSuffix(" RM")
  sspn_form.addRow("SSPN tabungan bersih:", dialog.fields["sspn_savings"])
  dialog.sspn_group.setLayout(sspn_form)
  right_layout.addWidget(dialog.sspn_group)

  dialog.alimony_group = QGroupBox("10. Alimoni kepada bekas isteri (≤ RM4,000)")
  alimony_form = QFormLayout()
  dialog.fields["alimony"] = QDoubleSpinBox()
  dialog.fields["alimony"].setRange(0.0, 4000.0)
  dialog.fields["alimony"].setSuffix(" RM")
  alimony_form.addRow("Alimoni:", dialog.fields["alimony"])
  dialog.alimony_group.setLayout(alimony_form)
  right_layout.addWidget(dialog.alimony_group)

  dialog.epf_insurance_group = QGroupBox("11. KWSP + Insuran Nyawa (COMBINED MAX: RM7,000)")
  epf_insurance_form = QFormLayout()

  law_note = QLabel("🏛️ <b>LHDN Law:</b> Total KWSP (compulsory + voluntary) + Life Insurance ≤ RM7,000 COMBINED")
  law_note.setStyleSheet("color: #d32f2f; font-weight: bold; font-size: 11px; margin-bottom: 10px; padding: 5px; background: #fff3e0; border-left: 3px solid #ff9800;")
  epf_insurance_form.addRow(law_note)

  pcb_note = QLabel("📊 <b>PCB Split:</b> Calculator shows separate fields but law treats as ONE bucket with shared EPF subcap")
  pcb_note.setStyleSheet("color: #1976d2; font-weight: bold; font-size: 10px; margin-bottom: 5px;")
  epf_insurance_form.addRow(pcb_note)

  shared_epf_note = QLabel("🔗 <b>Shared EPF Limit:</b> Mandatory + Voluntary EPF share RM4,000 subcap (total)")
  shared_epf_note.setStyleSheet("color: #4caf50; font-weight: bold; font-size: 10px; margin-bottom: 8px;")
  epf_insurance_form.addRow(shared_epf_note)

  dialog.fields["epf_voluntary"] = QDoubleSpinBox()
  dialog.fields["epf_voluntary"].setRange(0.0, 4000.0)
  dialog.fields["epf_voluntary"].setSuffix(" RM")
  dialog.fields["epf_voluntary"].setToolTip("Voluntary EPF contributions (shares RM4,000 subcap with mandatory EPF)")
  epf_insurance_form.addRow("a) KWSP sukarela (shares EPF limit):", dialog.fields["epf_voluntary"])

  dialog.fields["life_insurance"] = QDoubleSpinBox()
  dialog.fields["life_insurance"].setRange(0.0, 3000.0)
  dialog.fields["life_insurance"].setSuffix(" RM")
  dialog.fields["life_insurance"].setToolTip("Life insurance premium relief (independent RM3,000 subcap)")
  epf_insurance_form.addRow("b) Insuran nyawa (independent ≤ RM3,000):", dialog.fields["life_insurance"])

  dialog.fields["epf_voluntary"].valueChanged.connect(dialog.validate_epf_insurance_limit)
  dialog.fields["life_insurance"].valueChanged.connect(dialog.validate_epf_insurance_limit)

  dialog.epf_insurance_group.setLayout(epf_insurance_form)
  right_layout.addWidget(dialog.epf_insurance_group)

  dialog.prs_group = QGroupBox("12. PRS / Anuiti tertangguh (≤ RM3,000)")
  prs_form = QFormLayout()
  dialog.fields["prs_annuity"] = QDoubleSpinBox()
  dialog.fields["prs_annuity"].setRange(0.0, 3000.0)
  dialog.fields["prs_annuity"].setSuffix(" RM")
  prs_form.addRow("PRS/Anuiti:", dialog.fields["prs_annuity"])
  dialog.prs_group.setLayout(prs_form)
  right_layout.addWidget(dialog.prs_group)

  dialog.education_medical_insurance_group = QGroupBox("13. Insurans pendidikan & perubatan (≤ RM4,000)")
  education_medical_insurance_form = QFormLayout()
  dialog.fields["education_medical_insurance"] = QDoubleSpinBox()
  dialog.fields["education_medical_insurance"].setRange(0.0, 4000.0)
  dialog.fields["education_medical_insurance"].setSuffix(" RM")
  education_medical_insurance_form.addRow("Insurans pendidikan & perubatan:", dialog.fields["education_medical_insurance"])
  dialog.education_medical_insurance_group.setLayout(education_medical_insurance_form)
  right_layout.addWidget(dialog.education_medical_insurance_group)

  dialog.ev_group = QGroupBox("14. EV charger / compost machine (≤ RM2,500 sekali 3 tahun)")
  ev_form = QFormLayout()
  dialog.fields["ev_charger"] = QDoubleSpinBox()
  dialog.fields["ev_charger"].setRange(0.0, 2500.0)
  dialog.fields["ev_charger"].setSuffix(" RM")
  ev_form.addRow("EV charger/compost machine:", dialog.fields["ev_charger"])
  dialog.ev_group.setLayout(ev_form)
  right_layout.addWidget(dialog.ev_group)

  dialog.housing_group = QGroupBox("15. Faedah pinjaman rumah pertama")
  housing_form = QFormLayout()
  dialog.fields["housing_loan_under_500k"] = QDoubleSpinBox()
  dialog.fields["housing_loan_under_500k"].setRange(0.0, 7000.0)
  dialog.fields["housing_loan_under_500k"].setSuffix(" RM")
  housing_form.addRow("a) Harga ≤ RM500k (≤ RM7,000):", dialog.fields["housing_loan_under_500k"])

  dialog.fields["housing_loan_500k_750k"] = QDoubleSpinBox()
  dialog.fields["housing_loan_500k_750k"].setRange(0.0, 5000.0)
  dialog.fields["housing_loan_500k_750k"].setSuffix(" RM")
  housing_form.addRow("b) Harga RM500k-750k (≤ RM5,000):", dialog.fields["housing_loan_500k_750k"])
  dialog.housing_group.setLayout(housing_form)
  right_layout.addWidget(dialog.housing_group)

  dialog.mbb_group = QGroupBox("17. Manfaat Berupa Barangan (MBB) - Taxable Benefits")
  dialog.mbb_group.setStyleSheet("QGroupBox { background-color: #fff3e0; border: 2px solid #ff9800; }")
  mbb_form = QFormLayout()
  dialog.fields["mbb_amount"] = QDoubleSpinBox()
  dialog.fields["mbb_amount"].setRange(0.0, 999999.0)
  dialog.fields["mbb_amount"].setSuffix(" RM")
  dialog.fields["mbb_amount"].setToolTip("Manfaat Berupa Barangan (kereta syarikat, handphone, dll)")
  mbb_form.addRow("MBB Amount:", dialog.fields["mbb_amount"])
  dialog.mbb_group.setLayout(mbb_form)
  right_layout.addWidget(dialog.mbb_group)

  ntk_group = QGroupBox("18. Nilai Tempat Kediaman (NTK) - Accommodation Value")
  ntk_group.setStyleSheet("QGroupBox { background-color: #fff3e0; border: 2px solid #ff9800; }")
  ntk_form = QFormLayout()
  dialog.fields["ntk_amount"] = QDoubleSpinBox()
  dialog.fields["ntk_amount"].setRange(0.0, 999999.0)
  dialog.fields["ntk_amount"].setSuffix(" RM")
  dialog.fields["ntk_amount"].setToolTip("Nilai Tempat Kediaman (rumah/flat syarikat)")
  ntk_form.addRow("NTK Amount:", dialog.fields["ntk_amount"])
  ntk_group.setLayout(ntk_form)
  right_layout.addWidget(ntk_group)

  columns_layout.addWidget(right_column)

  # Add columns to main deductions layout
  deductions_layout.addWidget(columns_widget)

  # Rebates group
  rebate_monthly_group = QGroupBox("REBAT BULAN SEMASA - Maklumat Rebat")
  rebate_monthly_form = QFormLayout()
  rebate_info_label = QLabel("🏛️ <b>REBAT KHUSUS - Tolak Terus dari PCB:</b>")
  rebate_info_label.setStyleSheet("color: #7b1fa2; font-weight: bold; font-size: 11px;")
  rebate_monthly_form.addRow(rebate_info_label)

  dialog.fields["zakat_monthly"] = QDoubleSpinBox()
  dialog.fields["zakat_monthly"].setRange(0.0, 50000.0)
  dialog.fields["zakat_monthly"].setSuffix(" RM")
  dialog.fields["zakat_monthly"].setToolTip("Zakat/fitrah amount (deducted directly from PCB)")
  rebate_monthly_form.addRow("i. Zakat atau Fitrah:", dialog.fields["zakat_monthly"])

  dialog.fields["religious_travel_monthly"] = QDoubleSpinBox()
  dialog.fields["religious_travel_monthly"].setRange(0.0, 20000.0)
  dialog.fields["religious_travel_monthly"].setSuffix(" RM")
  dialog.fields["religious_travel_monthly"].setToolTip("Religious travel levy (2 times per lifetime)")
  rebate_monthly_form.addRow("ii. Levi pelepasan umrah/agama:", dialog.fields["religious_travel_monthly"])

  rebate_monthly_group.setLayout(rebate_monthly_form)
  deductions_layout.addWidget(rebate_monthly_group)

  dialog.deductions_group.setLayout(deductions_layout)
  parent_layout.addWidget(dialog.deductions_group)
