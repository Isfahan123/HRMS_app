"""
Lightweight local cache for payroll settings to survive restarts when
remote persistence is unavailable or delayed (e.g., Supabase policies/latency).

Currently caches:
- calculation_method: 'fixed' | 'variable'
- active_variable_config: string

Stored at logs/payroll_settings_cache.json relative to repo root.
"""
from __future__ import annotations

import json
import os
from typing import Dict, Optional


def _cache_path() -> str:
    # Place cache at <repo-root>/logs/payroll_settings_cache.json
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(base_dir, 'logs')
    try:
        os.makedirs(logs_dir, exist_ok=True)
    except Exception:
        # If logs dir cannot be created, fallback to base_dir
        logs_dir = base_dir
    return os.path.join(logs_dir, 'payroll_settings_cache.json')


def load_cached_payroll_settings() -> Dict[str, str]:
    try:
        path = _cache_path()
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f) or {}
                method = str(data.get('calculation_method', 'fixed') or 'fixed').strip().lower()
                if method not in ('fixed', 'variable'):
                    method = 'fixed'
                active = str(data.get('active_variable_config', 'default') or 'default').strip()
                return {'calculation_method': method, 'active_variable_config': active}
    except Exception:
        pass
    return {'calculation_method': 'fixed', 'active_variable_config': 'default'}


def save_cached_payroll_settings(settings: Dict[str, str]) -> bool:
    try:
        path = _cache_path()
        data = {
            'calculation_method': str(settings.get('calculation_method', 'fixed') or 'fixed').strip().lower(),
            'active_variable_config': str(settings.get('active_variable_config', 'default') or 'default').strip(),
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False
