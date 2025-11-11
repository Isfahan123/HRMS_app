"""
Simple service to load organization structure data from data/org_structure.json.
Provides helper functions for the UI to query departments, positions, and titles.
"""
import json
import os
from typing import List, Dict, Optional

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'org_structure.json')

def _load() -> Dict:
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

_cache: Optional[Dict] = None

def _get_cache() -> Dict:
    global _cache
    if _cache is None:
        _cache = _load()
    return _cache


def list_position_hierarchy() -> List[str]:
    return _get_cache().get('positions_hierarchy', [])


def list_departments() -> List[str]:
    return list(_get_cache().get('departments', {}).keys())


def get_department_units(dept_name: str) -> List[str]:
    return _get_cache().get('departments', {}).get(dept_name, [])


def list_job_title_groups() -> List[str]:
    return list(_get_cache().get('job_titles', {}).keys())


def get_titles_for_group(group: str) -> List[str]:
    return _get_cache().get('job_titles', {}).get(group, [])
