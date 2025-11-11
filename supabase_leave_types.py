"""Service layer for dynamic leave types configuration.

Provides cached CRUD helpers around the Supabase `leave_types` table.
Falls back gracefully if table is missing.
"""
from typing import List, Optional, Dict, Any
import time

try:
    from services.supabase_service import supabase
except Exception:  # Minimal stub for environments without Supabase
    supabase = None

_CACHE: Dict[str, Any] = {
    'timestamp': 0.0,
    'items': [],  # list of dicts
    'ttl': 30.0,  # seconds
}

_ALLOWED_COLUMNS = {
    'code','name','description','requires_document','deduct_from',
    'default_duration','max_duration','is_active','sort_order'
}


def _now() -> float:
    return time.time()


def _should_refresh() -> bool:
    return (_now() - _CACHE['timestamp']) > _CACHE.get('ttl', 30.0) or not _CACHE['items']


def list_leave_types(active_only: bool = True, force_refresh: bool = False) -> List[Dict[str, Any]]:
    """Return leave types (cached)."""
    if supabase is None:
        # Fallback defaults matching seed
        defaults = [
            {'code':'annual','name':'Annual Leave','deduct_from':'annual','requires_document': False},
            {'code':'sick','name':'Sick Leave','deduct_from':'sick','requires_document': True},
            {'code':'hospitalization','name':'Hospitalization','deduct_from':'sick','requires_document': True},
            {'code':'emergency','name':'Emergency Leave','deduct_from':'annual','requires_document': False},
            {'code':'unpaid','name':'Unpaid Leave','deduct_from':'unpaid','requires_document': False},
            {'code':'others','name':'Others','deduct_from':'annual','requires_document': False},
        ]
        return [d for d in defaults if (not active_only or d.get('is_active', True))]

    if force_refresh or _should_refresh():
        try:
            q = supabase.table('leave_types').select('*')
            if active_only:
                q = q.eq('is_active', True)
            res = q.order('sort_order', desc=False).execute()
            _CACHE['items'] = res.data or []
            _CACHE['timestamp'] = _now()
        except Exception:
            # preserve existing cache; if empty load defaults
            if not _CACHE['items']:
                return list_leave_types(active_only=active_only, force_refresh=False)  # recursion enters fallback
    items = _CACHE['items']
    return [it for it in items if (not active_only or it.get('is_active'))]


def get_leave_type(code: str) -> Optional[Dict[str, Any]]:
    code = (code or '').strip().lower()
    for lt in list_leave_types(active_only=False):
        if lt.get('code','').lower() == code:
            return lt
    return None


def create_leave_type(data: Dict[str, Any]) -> Dict[str, Any]:
    if supabase is None:
        raise RuntimeError('Supabase not configured')
    payload = {k: v for k, v in data.items() if k in _ALLOWED_COLUMNS}
    # Basic required fields
    if 'code' not in payload or 'name' not in payload:
        raise ValueError('code and name are required')
    # Attempt insert
    attempts = 0
    while attempts < 3:
        attempts += 1
        try:
            res = supabase.table('leave_types').insert(payload).execute()
            _CACHE['timestamp'] = 0  # invalidate
            return res.data[0] if res and res.data else payload
        except Exception as e:
            msg = str(e)
            # Unique violation or missing column fallback
            if 'unique' in msg.lower():
                raise
            # strip unknown column pattern
            import re
            m = re.search(r"'(.*?)' column", msg)
            if m:
                col = m.group(1)
                if col in payload:
                    payload.pop(col, None)
                    continue
            raise


def update_leave_type(code_or_id: str, data: Dict[str, Any]) -> bool:
    if supabase is None:
        raise RuntimeError('Supabase not configured')
    code_or_id = (code_or_id or '').strip()
    payload = {k: v for k, v in data.items() if k in _ALLOWED_COLUMNS}
    if not payload:
        return True
    try:
        # Try code first then id
        res = supabase.table('leave_types').update(payload).eq('code', code_or_id).execute()
        if not res.data:
            res = supabase.table('leave_types').update(payload).eq('id', code_or_id).execute()
        _CACHE['timestamp'] = 0
        return True
    except Exception:
        return False


def delete_leave_type(code_or_id: str) -> bool:
    if supabase is None:
        raise RuntimeError('Supabase not configured')
    code_or_id = (code_or_id or '').strip()
    try:
        res = supabase.table('leave_types').delete().eq('code', code_or_id).execute()
        if not res.data:
            res = supabase.table('leave_types').delete().eq('id', code_or_id).execute()
        _CACHE['timestamp'] = 0
        return True
    except Exception:
        return False


def toggle_active(code_or_id: str, active: bool) -> bool:
    return update_leave_type(code_or_id, {'is_active': active})


def bulk_upsert(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Upsert many records; returns summary."""
    created, updated, errors = 0, 0, []
    for item in items:
        try:
            code = item.get('code')
            existing = get_leave_type(code) if code else None
            if existing:
                ok = update_leave_type(code, item)
                updated += (1 if ok else 0)
            else:
                create_leave_type(item)
                created += 1
        except Exception as e:
            errors.append(f"{item.get('code')}: {e}")
    return {'created': created, 'updated': updated, 'errors': errors}


def clear_cache():
    _CACHE['timestamp'] = 0

if __name__ == '__main__':  # simple smoke
    print('Leave Types (active):', [lt.get('code') for lt in list_leave_types()])
