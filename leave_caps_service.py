import json
import os
from typing import Dict, Any

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'leave_caps.json')


def _load_raw() -> Dict[str, Any]:
    try:
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def get_leave_caps() -> Dict[str, Any]:
    """Return the full leave caps structure."""
    return _load_raw()


def save_leave_caps(payload: Dict[str, Any]) -> bool:
    """Save the leave caps JSON payload to disk. Returns True on success."""
    try:
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
        with open(DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)
        return True
    except Exception:
        return False


def get_tiers() -> list:
    data = _load_raw()
    return data.get('tiers', [])


def get_leave_types() -> list:
    data = _load_raw()
    return data.get('leave_types', [])


def get_caps_by_tier(tier_id: str) -> Dict[str, Any]:
    data = _load_raw()
    return data.get('caps', {}).get(tier_id, {})


def _tiers_sorted():
    data = _load_raw()
    tiers = data.get('tiers', [])
    # sort by min_years
    try:
        return sorted(tiers, key=lambda t: float(t.get('min_years', 0)))
    except Exception:
        return tiers


def get_caps_for_years(years_of_service: float) -> Dict[str, Any]:
    """Return caps dict for given years of service (falls back to best-match tier)."""
    tiers = _tiers_sorted()
    for t in tiers:
        try:
            min_y = float(t.get('min_years', 0))
            max_y = float(t.get('max_years', 9999))
            if min_y <= years_of_service <= max_y:
                tier_id = t.get('id')
                return get_caps_by_tier(tier_id)
        except Exception:
            continue
    # fallback to first tier caps or empty
    data = _load_raw()
    caps = data.get('caps', {})
    if caps:
        # return first available
        return next(iter(caps.values()))
    return {}


def load_from_supabase() -> Dict[str, Any]:
    """Attempt to read leave caps from Supabase tables. Falls back to JSON if unavailable.
    Expected tables:
      - leave_caps_tiers (id, label, min_years, max_years)
      - leave_caps (tier_id, leave_type, cap)
    """
    try:
        from services.supabase_service import supabase
    except Exception:
        return _load_raw()

    try:
        tiers_resp = supabase.table('leave_caps_tiers').select('*').execute()
        caps_resp = supabase.table('leave_caps').select('*').execute()
        data = {'tiers': [], 'leave_types': [], 'caps': {}}

        if tiers_resp.data:
            for t in tiers_resp.data:
                data['tiers'].append({
                    'id': t.get('id'),
                    'label': t.get('label'),
                    'min_years': t.get('min_years'),
                    'max_years': t.get('max_years')
                })

        if caps_resp.data:
            leave_types = set()
            for c in caps_resp.data:
                tier_id = c.get('tier_id')
                lt = c.get('leave_type')
                val = c.get('cap')
                leave_types.add(lt)
                data['caps'].setdefault(tier_id, {})[lt] = val
            data['leave_types'] = sorted(list(leave_types))

        # if empty, fallback to file
        if not data['tiers'] and not data['caps']:
            return _load_raw()
        return data
    except Exception:
        return _load_raw()


def save_to_supabase(payload: Dict[str, Any]) -> bool:
    """Persist tiers and caps to Supabase. This will upsert tiers and caps. Returns True on success or False.
    Note: Requires `services.supabase_service.supabase` to be configured and the tables to exist.
    """
    try:
        from services.supabase_service import supabase
    except Exception:
        # Supabase client unavailable
        return False

    try:
        # upsert tiers
        tiers = payload.get('tiers', [])
        for t in tiers:
            supabase.table('leave_caps_tiers').upsert({
                'id': t.get('id'),
                'label': t.get('label'),
                'min_years': t.get('min_years'),
                'max_years': t.get('max_years')
            }).execute()

        # upsert caps: delete existing caps for tier and re-insert for simplicity
        caps = payload.get('caps', {})
        for tier_id, caps_map in caps.items():
            # delete existing
            supabase.table('leave_caps').delete().eq('tier_id', tier_id).execute()
            for lt, val in caps_map.items():
                supabase.table('leave_caps').insert({
                    'tier_id': tier_id,
                    'leave_type': lt,
                    'cap': int(val) if val is not None else 0
                }).execute()

        return True
    except Exception as e:
        print(f"DEBUG: save_to_supabase error: {e}")
        return False


# Backwards compatibility aliases (some modules may try the older names)
def load_from_db():
    return load_from_supabase()


def save_to_db(payload: Dict[str, Any]):
    return save_to_supabase(payload)


def apply_policy_to_db(force: bool = False, year: int = None, dry_run: bool = True) -> Dict[str, Any]:
    """Apply current leave caps policy to all active employees in DB.

    Parameters:
      - force: if True, overwrite existing entitlements; if False, only fill missing (None) or zero values
      - year: target year for balances (defaults to current year)
      - dry_run: if True, do not perform DB writes; return a summary of actions that would be taken

    Returns a summary dict: {processed: int, updated: int, created: int, skipped: int, details: [..]}
    """
    import math
    from datetime import datetime

    summary = {
        'processed': 0,
        'updated': 0,
        'created': 0,
        'skipped': 0,
        'errors': 0,
        'details': []
    }

    if year is None:
        year = datetime.now().year

    # load policy
    policy = _load_raw()
    if not policy:
        # try db load
        policy = load_from_supabase()

    # safe-get function
    def _caps_for_years(yos):
        try:
            return get_caps_for_years(float(yos))
        except Exception:
            return get_caps_for_years(0.0)

    try:
        from services.supabase_service import supabase
    except Exception:
        # Supabase not available; return what a dry-run would be (no writes possible)
        summary['details'].append('Supabase client not available; cannot connect to DB')
        summary['errors'] += 1
        return summary

    try:
        # fetch active employees
        resp = supabase.table('employees').select('id, employee_id, email, date_joined, status').eq('status', 'Active').execute()
        employees = resp.data or []

        for emp in employees:
            summary['processed'] += 1
            emp_id = emp.get('employee_id') or emp.get('id')
            email = emp.get('email')

            # compute years of service
            yos = 0.0
            try:
                dj = emp.get('date_joined')
                if dj:
                    from datetime import datetime as _dt
                    dj_date = _dt.strptime(dj, '%Y-%m-%d').date()
                    yos = (datetime.now().date() - dj_date).days / 365.25
            except Exception:
                yos = 0.0

            caps = _caps_for_years(yos)

            # prepare intended values
            intended_annual = int(caps.get('annual', 0)) if caps.get('annual') is not None else 0
            intended_sick = int(caps.get('sick', 0)) if caps.get('sick') is not None else 0
            intended_hosp = int(caps.get('hospitalization', 0)) if caps.get('hospitalization') is not None else 0

            # check existing leave_balances
            lb_resp = supabase.table('leave_balances').select('id, annual_entitlement, used_days, carried_forward').eq('employee_id', emp_id).eq('year', year).execute()
            if lb_resp.data:
                rec = lb_resp.data[0]
                current_ent = rec.get('annual_entitlement')
                do_update = False
                if force:
                    do_update = True
                else:
                    if current_ent in (None, 0):
                        do_update = True

                if do_update:
                    summary['details'].append(f"UPDATE leave_balances {emp_id}: {current_ent} -> {intended_annual}")
                    if not dry_run:
                        try:
                            supabase.table('leave_balances').update({'annual_entitlement': intended_annual}).eq('id', rec.get('id')).execute()
                            summary['updated'] += 1
                        except Exception as e:
                            summary['errors'] += 1
                            summary['details'].append(f"ERROR updating leave_balances {emp_id}: {e}")
                    else:
                        summary['updated'] += 1
                else:
                    summary['skipped'] += 1
            else:
                # create record
                summary['details'].append(f"CREATE leave_balances {emp_id}: annual_entitlement={intended_annual}")
                if not dry_run:
                    try:
                        supabase.table('leave_balances').insert({
                            'employee_id': emp_id,
                            'year': year,
                            'annual_entitlement': intended_annual,
                            'used_days': 0,
                            'carried_forward': 0
                        }).execute()
                        summary['created'] += 1
                    except Exception as e:
                        summary['errors'] += 1
                        summary['details'].append(f"ERROR creating leave_balances {emp_id}: {e}")
                else:
                    summary['created'] += 1

            # sick leave balances
            sl_resp = supabase.table('sick_leave_balances').select('id, sick_days_entitlement, hospitalization_days_entitlement, used_sick_days, used_hospitalization_days').eq('employee_id', emp_id).eq('year', year).execute()
            if sl_resp.data:
                rec = sl_resp.data[0]
                current_sick = rec.get('sick_days_entitlement')
                current_hosp = rec.get('hospitalization_days_entitlement')
                do_update = False
                if force:
                    do_update = True
                else:
                    if (current_sick in (None, 0)) or (current_hosp in (None, 0)):
                        do_update = True

                if do_update:
                    summary['details'].append(f"UPDATE sick_leave_balances {emp_id}: sick {current_sick}->{intended_sick}, hosp {current_hosp}->{intended_hosp}")
                    if not dry_run:
                        try:
                            supabase.table('sick_leave_balances').update({
                                'sick_days_entitlement': intended_sick,
                                'hospitalization_days_entitlement': intended_hosp
                            }).eq('id', rec.get('id')).execute()
                            summary['updated'] += 1
                        except Exception as e:
                            summary['errors'] += 1
                            summary['details'].append(f"ERROR updating sick_leave_balances {emp_id}: {e}")
                    else:
                        summary['updated'] += 1
                else:
                    summary['skipped'] += 1
            else:
                summary['details'].append(f"CREATE sick_leave_balances {emp_id}: sick={intended_sick}, hosp={intended_hosp}")
                if not dry_run:
                    try:
                        supabase.table('sick_leave_balances').insert({
                            'employee_id': emp_id,
                            'year': year,
                            'sick_days_entitlement': intended_sick,
                            'hospitalization_days_entitlement': intended_hosp,
                            'used_sick_days': 0,
                            'used_hospitalization_days': 0
                        }).execute()
                        summary['created'] += 1
                    except Exception as e:
                        summary['errors'] += 1
                        summary['details'].append(f"ERROR creating sick_leave_balances {emp_id}: {e}")
                else:
                    summary['created'] += 1

        return summary

    except Exception as e:
        summary['errors'] += 1
        summary['details'].append(f"ERROR during apply_policy_to_db: {e}")
        return summary

