"""Tax Relief Catalog (TP1 2025 Structure)

Defines structured metadata for Malaysian Potongan Bulan Semasa / TP1 relief items.
No DB writes here; pure constants + helper utilities to be consumed by UI/service layer.

Design goals:
- Single source of truth: code maps each line & sub-line to an internal key.
- Encodes annual caps, group caps, subcaps, and multi-year cycle constraints.
- Provides lightweight helper to aggregate a month submission (dict of raw amounts) into:
  (validated_totals, per_item_applied, per_group_remaining)
- Keeps SOCSO/EIS (item 14) flagged as pcb_only so it never reduces cash net pay.

NOTE: Monetary caps reflect TP1 2025 description provided. Adjust if official changes occur.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Iterable

# -----------------------------
# Data Structures
# -----------------------------
@dataclass(frozen=True)
class ReliefItem:
    code: str                  # e.g. '1a'
    key: str                   # internal key e.g. 'parent_medical_care'
    description: str
    cap: Optional[float] = None          # Individual item cap (subcap) if distinct
    group: Optional[str] = None          # Parent group identifier
    group_cap: Optional[float] = None    # Mirror of group's cap for quick reference
    pcb_only: bool = False               # True if only for PCB (e.g., SOCSO/EIS)
    cycle_years: Optional[int] = None    # Multi-year cycle (e.g., breastfeeding=2, ev=3)
    notes: str = ''

@dataclass(frozen=True)
class ReliefGroup:
    id: str
    description: str
    cap: Optional[float] = None
    # For nested groups that share an umbrella (e.g. group 1, 3, 4, 5, 6)

# -----------------------------
# Group Definitions
# -----------------------------
RELIEF_GROUPS: Dict[str, ReliefGroup] = {
    'G1_PARENT': ReliefGroup('G1_PARENT', 'Parent / grandparent expenses (a+b+c)', 8000.0),
    'G3_SELF_EDU': ReliefGroup('G3_SELF_EDU', 'Self education fees (a+b+c)', 7000.0),
    'G4_MEDICAL': ReliefGroup('G4_MEDICAL', 'Medical expenses (a..f)', 10000.0),
    'G5_LIFESTYLE': ReliefGroup('G5_LIFESTYLE', 'Lifestyle (a..d)', 2500.0),
    'G6_SPORTS': ReliefGroup('G6_SPORTS', 'Additional lifestyle sports (a..d)', 1000.0),
    'G11_EPF_LIFE': ReliefGroup('G11_EPF_LIFE', 'EPF + Life Insurance combined', 7000.0),
}

# -----------------------------
# Item Definitions
# -----------------------------
ITEMS: List[ReliefItem] = [
    # 1 Parent / Grandparent
    ReliefItem('1a', 'parent_medical_care', 'Rawatan perubatan/keperluan/penjagaan ibu bapa/datok nenek', group='G1_PARENT', group_cap=8000.0),
    ReliefItem('1b', 'parent_dental', 'Rawatan pergigian ibu bapa/datok nenek', group='G1_PARENT', group_cap=8000.0),
    ReliefItem('1c', 'parent_full_exam_vaccine', 'Pemeriksaan penuh & vaksin (subcap RM1,000)', cap=1000.0, group='G1_PARENT', group_cap=8000.0),

    # 2 Support equipment
    ReliefItem('2', 'support_equipment_disabled', 'Peralatan sokongan asas', cap=6000.0),

    # 3 Self education
    ReliefItem('3a', 'self_edu_non_pg_professional', 'Yuran bidang profesional bukan Sarjana/PhD', group='G3_SELF_EDU', group_cap=7000.0),
    ReliefItem('3b', 'self_edu_masters_phd', 'Yuran Sarjana/PhD', group='G3_SELF_EDU', group_cap=7000.0),
    ReliefItem('3c', 'self_edu_skill_upgrading', 'Kursus peningkatan kemahiran (subcap RM2,000)', cap=2000.0, group='G3_SELF_EDU', group_cap=7000.0),

    # 4 Medical umbrella
    ReliefItem('4a', 'medical_serious_disease', 'Penyakit serius self/spouse/child', group='G4_MEDICAL', group_cap=10000.0),
    ReliefItem('4b', 'medical_fertility', 'Rawatan kesuburan', group='G4_MEDICAL', group_cap=10000.0),
    ReliefItem('4c', 'medical_vaccination', 'Pemvaksinan (subcap RM1,000)', cap=1000.0, group='G4_MEDICAL', group_cap=10000.0),
    ReliefItem('4d', 'medical_dental', 'Pemeriksaan & rawatan pergigian (subcap RM1,000)', cap=1000.0, group='G4_MEDICAL', group_cap=10000.0),
    ReliefItem('4e', 'medical_check_covid_mental_devices', 'Check-up/COVID/Mental/peralatan (subcap RM1,000)', cap=1000.0, group='G4_MEDICAL', group_cap=10000.0),
    ReliefItem('4f', 'medical_learning_disability_child', 'Intervensi anak kurang upaya pembelajaran (subcap RM6,000)', cap=6000.0, group='G4_MEDICAL', group_cap=10000.0),

    # 5 Lifestyle base
    ReliefItem('5a', 'lifestyle_publications', 'Buku/jurnal/majalah', group='G5_LIFESTYLE', group_cap=2500.0),
    ReliefItem('5b', 'lifestyle_devices', 'Peranti (PC/telefon/tablet)', group='G5_LIFESTYLE', group_cap=2500.0),
    ReliefItem('5c', 'lifestyle_internet', 'Langganan internet', group='G5_LIFESTYLE', group_cap=2500.0),
    ReliefItem('5d', 'lifestyle_skill_course', 'Yuran kursus peningkatan kemahiran', group='G5_LIFESTYLE', group_cap=2500.0),

    # 6 Lifestyle sports
    ReliefItem('6a', 'sports_equipment', 'Peralatan sukan', group='G6_SPORTS', group_cap=1000.0),
    ReliefItem('6b', 'sports_facility_fees', 'Fi fasiliti sukan', group='G6_SPORTS', group_cap=1000.0),
    ReliefItem('6c', 'sports_event_registration', 'Fi pendaftaran pertandingan sukan', group='G6_SPORTS', group_cap=1000.0),
    ReliefItem('6d', 'sports_gym_membership', 'Yuran keahlian gim / latihan', group='G6_SPORTS', group_cap=1000.0),

    # 7 Breastfeeding (biennial)
    ReliefItem('7', 'breastfeeding_equipment', 'Peralatan penyusuan (sekali setiap 2 tahun)', cap=1000.0, cycle_years=2),

    # 8 Childcare
    ReliefItem('8', 'childcare_fees', 'Yuran tadika/asuhan (≤6 tahun)', cap=3000.0),

    # 9 SSPN
    ReliefItem('9', 'sspn_net_savings', 'Tabungan bersih SSPN', cap=8000.0),

    # 10 Alimony
    ReliefItem('10', 'alimony_ex_wife', 'Bayaran alimoni bekas isteri', cap=4000.0),

    # 11 EPF + Life combined (subcaps)
    ReliefItem('11a', 'epf_total_including_voluntary', 'KWSP (wajib + sukarela) subcap', cap=4000.0, group='G11_EPF_LIFE', group_cap=7000.0),
    ReliefItem('11b', 'life_insurance', 'Insurans nyawa subcap', cap=3000.0, group='G11_EPF_LIFE', group_cap=7000.0),

    # 12 PRS / Annuity
    ReliefItem('12', 'prs_deferred_annuity', 'PRS & anuiti tertangguh', cap=3000.0),

    # 13 Education & medical insurance
    ReliefItem('13', 'education_medical_insurance', 'Insurans pendidikan & perubatan', cap=4000.0),

    # 14 SOCSO/EIS (PCB only)
    ReliefItem('14', 'socso_eis_lp1', 'Caruman PERKESO + EIS (PCB sahaja)', cap=350.0, pcb_only=True),

    # 15 EV Charger / Compost (3-year cycle)
    ReliefItem('15', 'ev_charger_compost', 'EV charger / mesin kompos (3 tahun sekali)', cap=2500.0, cycle_years=3),

    # 16 Home loan interest (two tiers)
    ReliefItem('16a', 'home_loan_interest_tier1', 'Faedah pinjaman rumah ≤500k', cap=7000.0),
    ReliefItem('16b', 'home_loan_interest_tier2', 'Faedah pinjaman rumah 500k–750k', cap=5000.0),
]

# Indexes for quick lookups
ITEM_BY_KEY: Dict[str, ReliefItem] = {i.key: i for i in ITEMS}
ITEM_BY_CODE: Dict[str, ReliefItem] = {i.code: i for i in ITEMS}
GROUP_TO_ITEMS: Dict[str, List[str]] = {}
for it in ITEMS:
    if it.group:
        GROUP_TO_ITEMS.setdefault(it.group, []).append(it.key)

# -----------------------------
# Helper Functions
# -----------------------------

def apply_relief_caps(raw_claims: Dict[str, float], groups: Dict[str, 'ReliefGroup'] = None) -> Tuple[float, Dict[str, float], Dict[str, float]]:
    """Apply per-item subcaps and (optionally overridden) group caps.

    Args:
        raw_claims: mapping item_key -> amount
        groups: optional mapping of group_id -> ReliefGroup (allows dynamic cap overrides). If None, uses global RELIEF_GROUPS.

    Returns:
        (total_for_LP1, per_item_applied, group_usage)

    Notes:
        - Multi-year cycle enforcement is external.
        - PCB-only items are included; caller can filter for cash.
        - Proportional trimming occurs when a group's subtotal exceeds its cap.
    """
    groups = groups or RELIEF_GROUPS
    # First, clip by item caps
    per_item_applied: Dict[str, float] = {}
    for key, amount in raw_claims.items():
        item = ITEM_BY_KEY.get(key)
        if not item:
            continue
        amt = float(amount or 0.0)
        if item.cap is not None:
            amt = min(amt, item.cap)
        per_item_applied[key] = max(0.0, amt)

    # Then enforce group caps
    group_usage: Dict[str, float] = {}
    for group_id, members in GROUP_TO_ITEMS.items():
        cap = groups.get(group_id).cap if group_id in groups else None
        if cap is None:
            # No cap; skip
            continue
        subtotal = sum(per_item_applied.get(m, 0.0) for m in members)
        if subtotal <= cap + 1e-9:
            group_usage[group_id] = subtotal
            continue
        # Need proportional trim (simple approach)
        if subtotal <= 0:
            group_usage[group_id] = 0.0
            continue
        ratio = cap / subtotal
        new_subtotal = 0.0
        for m in members:
            original = per_item_applied.get(m, 0.0)
            trimmed = round(original * ratio, 2)
            per_item_applied[m] = trimmed
            new_subtotal += trimmed
        group_usage[group_id] = round(new_subtotal, 2)

    # Combined EPF + Life explicit enforcement (defensive if not already covered)
    if 'G11_EPF_LIFE' in groups:
        epf_life_members = GROUP_TO_ITEMS.get('G11_EPF_LIFE', [])
        cap = groups['G11_EPF_LIFE'].cap or 0.0
        subtotal = sum(per_item_applied.get(m, 0.0) for m in epf_life_members)
        if subtotal > cap and subtotal > 0:
            ratio = cap / subtotal
            for m in epf_life_members:
                per_item_applied[m] = round(per_item_applied.get(m, 0.0) * ratio, 2)

    total_lp1 = round(sum(v for k, v in per_item_applied.items()), 2)
    return total_lp1, per_item_applied, group_usage


def filter_pcb_only(per_item: Dict[str, float]) -> Dict[str, float]:
    """Return dict excluding pcb_only items (for cash deduction exclusion)."""
    out = {}
    for k, v in per_item.items():
        item = ITEM_BY_KEY.get(k)
        if item and item.pcb_only:
            continue
        out[k] = v
    return out

def compute_lp1_totals(raw_claims: Dict[str, float], items_catalog: Dict[str, ReliefItem] = None, group_overrides: Dict[str, float] = None) -> Dict[str, Any]:
    """High-level helper returning structured LP1 totals.
    raw_claims: mapping item_key -> amount for this month.
    items_catalog: optional override mapping (item_key -> ReliefItem). If provided, it is used
                   for pcb_only filtering and metadata lookup (caps already enforced externally
                   if caller used apply_relief_caps variant). Backwards compatible: when None,
                   uses global ITEM_BY_KEY.

    Returns dict with keys:
      total_lp1_pcb: total including pcb_only items (for PCB calculation)
      total_lp1_cash: total excluding pcb_only items (if ever needed separately)
      per_item: applied amounts after caps
      per_item_cash: applied amounts excluding pcb_only items
      group_usage: usage per capped group
    """
    eff_groups = RELIEF_GROUPS
    if group_overrides:
        eff_groups = get_effective_groups(group_overrides)
    total_lp1, per_item_applied, group_usage = apply_relief_caps(raw_claims or {}, groups=eff_groups)
    catalog = items_catalog or ITEM_BY_KEY
    # Filter pcb_only using provided catalog (fallback global)
    per_item_cash: Dict[str, float] = {}
    for k, v in per_item_applied.items():
        it = catalog.get(k)
        if it and it.pcb_only:
            continue
        per_item_cash[k] = v
    total_cash = round(sum(per_item_cash.values()), 2)
    return {
        'total_lp1_pcb': total_lp1,
        'total_lp1_cash': total_cash,
        'per_item': per_item_applied,
        'per_item_cash': per_item_cash,
        'group_usage': group_usage,
    }

# --------------------------------------------------
# Override / dynamic configuration helpers
# --------------------------------------------------
def apply_item_overrides(overrides: Dict[str, Dict[str, Any]]) -> Dict[str, ReliefItem]:
    """Return a new ITEM_BY_KEY-like catalog with field overrides applied.

    overrides format:
        {
          'item_key': { 'cap': 5000.0, 'pcb_only': False, 'cycle_years': 2 }
        }
    Only provided keys are updated; unspecified attributes retain existing values.
    Safe to call with empty dict.
    """
    if not overrides:
        return ITEM_BY_KEY
    new_catalog: Dict[str, ReliefItem] = {}
    for key, base in ITEM_BY_KEY.items():
        ov = overrides.get(key)
        if not ov:
            new_catalog[key] = base
            continue
        # Build a mutable dict of fields from dataclass
        data = {
            'code': base.code,
            'key': base.key,
            'description': base.description,
            'cap': ov.get('cap', base.cap),
            'group': base.group,
            'group_cap': base.group_cap,
            'pcb_only': ov.get('pcb_only', base.pcb_only),
            'cycle_years': ov.get('cycle_years', base.cycle_years),
            'notes': ov.get('notes', base.notes),
        }
        new_catalog[key] = ReliefItem(**data)
    return new_catalog

def get_effective_items(overrides: Optional[Dict[str, Dict[str, Any]]]) -> Dict[str, ReliefItem]:
    """Convenience wrapper returning a catalog with overrides applied (or global if None)."""
    return apply_item_overrides(overrides) if overrides else ITEM_BY_KEY

def load_relief_overrides_from_db(supabase_client) -> Dict[str, Dict[str, Any]]:
    """Attempt to load relief overrides from DB (graceful fallback to empty dict).

    Expected table shape (example): relief_item_overrides
      columns: item_key TEXT PK, cap NUMERIC, pcb_only BOOLEAN, cycle_years INT
    Any missing column or table returns empty dict.
    """
    try:
        resp = supabase_client.table('relief_item_overrides').select('*').execute()
        rows = getattr(resp, 'data', None) or []
        out: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            key = r.get('item_key')
            if not key or key not in ITEM_BY_KEY:
                continue
            entry: Dict[str, Any] = {}
            if 'cap' in r and r.get('cap') is not None:
                try:
                    entry['cap'] = float(r.get('cap'))
                except Exception:
                    pass
            if 'pcb_only' in r and r.get('pcb_only') is not None:
                entry['pcb_only'] = bool(r.get('pcb_only'))
            if 'cycle_years' in r and r.get('cycle_years') is not None:
                try:
                    entry['cycle_years'] = int(r.get('cycle_years'))
                except Exception:
                    pass
            if entry:
                out[key] = entry
        return out
    except Exception:
        return {}

def load_relief_group_overrides_from_db(supabase_client) -> Dict[str, float]:
    """Load group cap overrides. Expected table: relief_group_overrides(group_id TEXT PK, cap NUMERIC)."""
    try:
        resp = supabase_client.table('relief_group_overrides').select('*').execute()
        rows = getattr(resp, 'data', None) or []
        out: Dict[str, float] = {}
        for r in rows:
            gid = r.get('group_id')
            if gid and gid in RELIEF_GROUPS and r.get('cap') is not None:
                try:
                    out[gid] = float(r.get('cap'))
                except Exception:
                    continue
        return out
    except Exception:
        return {}

def get_effective_groups(group_overrides: Dict[str, float] = None) -> Dict[str, ReliefGroup]:
    """Return mapping of group_id -> ReliefGroup with overridden cap values applied."""
    if not group_overrides:
        return RELIEF_GROUPS
    eff: Dict[str, ReliefGroup] = {}
    for gid, grp in RELIEF_GROUPS.items():
        new_cap = group_overrides.get(gid, grp.cap)
        eff[gid] = ReliefGroup(grp.id, grp.description, new_cap)
    return eff

# -----------------------------
# YTD / Cycle Enforcement Helpers (optional integration)
# -----------------------------

def create_relief_ytd_table_sql() -> str:
    """SQL DDL for a YTD relief tracking table (idempotent)."""
    return (
        """
        CREATE TABLE IF NOT EXISTS relief_ytd_accumulated (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            employee_id UUID NOT NULL,
            year INT NOT NULL,
            item_key TEXT NOT NULL,
            claimed_ytd DECIMAL(12,2) DEFAULT 0.00,
            last_claim_year INT,
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE (employee_id, year, item_key)
        );

        CREATE OR REPLACE FUNCTION update_relief_ytd_accumulated_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS trg_update_relief_ytd_accumulated ON relief_ytd_accumulated;
        CREATE TRIGGER trg_update_relief_ytd_accumulated
        BEFORE UPDATE ON relief_ytd_accumulated
        FOR EACH ROW
        EXECUTE FUNCTION update_relief_ytd_accumulated_updated_at();
        """
    )

def adjust_claims_for_ytd_and_cycles(raw_claims: Dict[str, float], ytd_rows: List[Dict], current_year: int) -> Dict[str, float]:
    """Reduce raw_claims based on YTD already claimed and multi-year cycle rules.
    ytd_rows: rows from relief_ytd_accumulated for employee (could include prior years for cycle check).
    Logic:
      - For items with annual cap: remaining = item.cap - claimed_ytd (clip >=0); claimed portion limited.
      - For groups we rely on core apply_relief_caps after this reduction.
      - Multi-year cycle: if cycle_years=2 and last_claim_year == current_year-1 deny; if 3-year cycle ensure gap.
    """
    adjusted = dict(raw_claims or {})
    # Index YTD by item_key for quick lookup
    ytd_map = {}
    for r in ytd_rows or []:
        try:
            ytd_map[r.get('item_key')] = {
                'claimed_ytd': float(r.get('claimed_ytd', 0.0) or 0.0),
                'last_claim_year': r.get('last_claim_year')
            }
        except Exception:
            continue
    for key, amount in list(adjusted.items()):
        item = ITEM_BY_KEY.get(key)
        if not item:
            continue
        meta = ytd_map.get(key, {'claimed_ytd': 0.0, 'last_claim_year': None})
        already = meta['claimed_ytd']
        # Annual cap enforcement at item level
        if item.cap is not None:
            remaining = max(0.0, item.cap - already)
            if remaining <= 0:
                adjusted[key] = 0.0
                continue
            if amount > remaining:
                adjusted[key] = remaining
        # Multi-year cycle enforcement
        if item.cycle_years:
            last_year = meta.get('last_claim_year')
            if last_year is not None and (current_year - int(last_year)) < item.cycle_years:
                # Not yet eligible this year
                adjusted[key] = 0.0
    return adjusted

def compute_applied_and_ytd_updates(applied_items: Dict[str, float], ytd_rows: List[Dict], current_year: int) -> List[Dict]:
    """Given final applied per_item amounts, produce list of row dicts to upsert with new YTD totals & cycle year update if >0."""
    ytd_index = {r.get('item_key'): r for r in (ytd_rows or [])}
    updates: List[Dict] = []
    for key, amt in applied_items.items():
        if amt <= 0:
            continue
        base = ytd_index.get(key)
        prev_claimed = 0.0
        if base:
            try:
                prev_claimed = float(base.get('claimed_ytd', 0.0) or 0.0)
            except Exception:
                prev_claimed = 0.0
        new_total = round(prev_claimed + amt, 2)
        item = ITEM_BY_KEY.get(key)
        updates.append({
            'item_key': key,
            'claimed_ytd': new_total,
            'last_claim_year': current_year if (item and item.cycle_years) else (base.get('last_claim_year') if base else None)
        })
    return updates

__all__ = [
    'ReliefItem', 'ReliefGroup', 'RELIEF_GROUPS', 'ITEMS', 'ITEM_BY_KEY', 'ITEM_BY_CODE', 'GROUP_TO_ITEMS',
    'apply_relief_caps', 'filter_pcb_only'
]

__all__.append('compute_lp1_totals')
__all__ += [
    'create_relief_ytd_table_sql',
    'adjust_claims_for_ytd_and_cycles',
    'compute_applied_and_ytd_updates',
    'apply_item_overrides',
    'get_effective_items',
    'load_relief_overrides_from_db',
    'load_relief_group_overrides_from_db',
    'get_effective_groups'
]
