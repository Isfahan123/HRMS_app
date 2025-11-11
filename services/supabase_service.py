from supabase import create_client, Client
from typing import Dict, Optional, List, Any
import os
from datetime import datetime
import json
import bcrypt
import uuid
import pytz
import io
import math
import mimetypes
import time
import random
import traceback
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import cm
from datetime import timedelta, date
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING

url: str = "https://wxaerkdmpxriveyknfov.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind4YWVya2RtcHhyaXZleWtuZm92Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Mzc2ODkxOSwiZXhwIjoyMDY5MzQ0OTE5fQ.Wsu46SgMRGkPe9HmtlVETktRD5kRP0o0zGzMB1BzPX8"
supabase: Client = create_client(url, key)
KL_TZ = pytz.timezone('Asia/Kuala_Lumpur')

# -----------------------------------------------------------------------------
# Windows-safe console output: avoid UnicodeEncodeError on emojis/special chars
# -----------------------------------------------------------------------------
_original_print = print

def _safe_print(*args, **kwargs):
    """Print wrapper that strips characters unsupported by the active console.

    This prevents crashes like 'charmap' codec can't encode character '\U0001f4c5'
    on Windows terminals that don't support emojis. If encoding fails, we reprint
    with non-encodable characters removed.
    """
    try:
        _original_print(*args, **kwargs)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, 'encoding', None) or 'utf-8'
        sanitized = []
        for a in args:
            s = str(a)
            try:
                s = s.encode(enc, errors='ignore').decode(enc, errors='ignore')
            except Exception:
                # Last resort: ASCII-only
                s = s.encode('ascii', errors='ignore').decode('ascii', errors='ignore')
            sanitized.append(s)
        _original_print(*sanitized, **kwargs)

# Shadow built-in print within this module to ensure all prints are safe
print = _safe_print

# Login lockout configuration (change as needed)
LOGIN_LOCK_THRESHOLD = int(os.environ.get('HRMS_LOGIN_LOCK_THRESHOLD', 5))
# Duration in minutes for an account to be locked after exceeding threshold
LOGIN_LOCK_DURATION_MINUTES = int(os.environ.get('HRMS_LOGIN_LOCK_DURATION_MINUTES', 15))

# Simple security event logger that appends JSON lines to logs/security.log
def _log_security_event(event_type: str, user_email: Optional[str] = None, user_id: Optional[str] = None,
                        employee_id: Optional[str] = None, client_ip: Optional[str] = None,
                        success: bool = False, details: Optional[Dict] = None,
                        error_message: Optional[str] = None, session_id: str = 'no_session') -> None:
    try:
        payload = {
            'timestamp': datetime.now(pytz.UTC).isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'user_email': user_email,
            'employee_id': employee_id,
            'client_ip': client_ip or '127.0.0.1',
            'success': bool(success),
            'details': details or {},
            'error_message': error_message,
            'session_id': session_id,
            'application': 'HRMS',
            'version': '2.0.0'
        }
        os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'logs'), exist_ok=True)
        log_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'security.log')
        # Normalize path and ensure forward slashes for Windows
        log_path = os.path.normpath(log_path)
        level = 'INFO' if success else 'WARNING'
        with open(log_path, 'a', encoding='utf-8') as fh:
            fh.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {level} - {json.dumps(payload, ensure_ascii=False)}\n")
    except Exception:
        # Never raise from logger
        pass


def _parse_timestamptz(val: Optional[str]) -> Optional[datetime]:
    if not val:
        return None
    try:
        # Try isoformat parsing first (Python 3.7+)
        return datetime.fromisoformat(val)
    except Exception:
        try:
            # Fallback: handle common Zulu tz
            if val.endswith('Z'):
                return datetime.fromisoformat(val.replace('Z', '+00:00'))
        except Exception:
            return None
    return None

def _parse_any_date(val: Optional[str]) -> Optional[datetime]:
    """Parse a variety of date string formats into a datetime (naive, local date at 00:00).

    Supported examples:
    - 'YYYY-MM-DD'
    - 'YYYY/MM/DD'
    - 'YYYY-MM'
    - 'YYYY/MM'
    - 'MM/YYYY'
    - 'MM-YYYY'
    - 'DD/MM/YYYY'
    - 'DD-MM-YYYY'
    Returns None if parsing fails.
    """
    if not val:
        return None
    s = str(val).strip()
    fmts = [
        '%Y-%m-%d', '%Y/%m/%d',
        '%d/%m/%Y', '%d-%m-%Y',
        '%Y-%m', '%Y/%m',
        '%m/%Y', '%m-%Y',
    ]
    for f in fmts:
        try:
            dt = datetime.strptime(s, f)
            # If format lacks day, default to 1st of month
            if f in ('%Y-%m', '%Y/%m', '%m/%Y', '%m-%Y'):
                # For %m/%Y and %m-%Y, datetime puts current day; ensure day=1 via re-parse
                parts = s.replace('-', '/').split('/')
                if f in ('%m/%Y', '%m-%Y'):
                    mm, yy = int(parts[0]), int(parts[1])
                    return datetime(yy, mm, 1)
                else:
                    yy, mm = int(parts[0]), int(parts[1])
                    return datetime(yy, mm, 1)
            return dt
        except Exception:
            continue
    return None

# -----------------------------------------------------------------------------
# Helpers for tax/relief derivations
# -----------------------------------------------------------------------------
def _derive_other_reliefs_current_from_monthly(monthly_deductions: Optional[Dict]) -> float:
    """Derive LP1 (other_reliefs_current) from monthly_deductions.

    Sums eligible relief-like fields and excludes rebate/non-relief entries.
    Excludes keys:
      - zakat_monthly (rebate handled elsewhere)
      - religious_travel_monthly (rebate-like)
      - other_deductions_amount (generic, not a tax relief)
    Unknown keys are best-effort treated as numeric relief if convertible.
    """
    try:
        if not isinstance(monthly_deductions, dict):
            return 0.0
        exclude_keys = {
            'zakat_monthly',
            'religious_travel_monthly',
            'other_deductions_amount',
            # Explicit taxable benefits (should not reduce PCB as reliefs)
            'mbb_amount',
            'ntk_amount',
        }
        total = 0.0
        for k, v in monthly_deductions.items():
            if k in exclude_keys:
                continue
            try:
                total += float(v or 0.0)
            except Exception:
                # Ignore non-numeric fields quietly
                continue
        return total
    except Exception:
        return 0.0

# -----------------------------------------------------------------------------
# Had Potongan Bulanan (HPB) configuration storage
# -----------------------------------------------------------------------------
def create_hpb_configs_table_sql() -> str:
    """Return SQL to create a table for Had Potongan Bulanan (HPB) UI configs.

    Stores arbitrary JSON (all inputs/caps) versioned by year and config_name.
    """
    return (
        """
        CREATE TABLE IF NOT EXISTS had_potongan_bulanan_configs (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            config_name TEXT NOT NULL,
            year INT NOT NULL,
            details JSONB NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE (config_name, year)
        );

        CREATE OR REPLACE FUNCTION update_hpb_configs_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS trigger_update_hpb_configs_updated_at ON had_potongan_bulanan_configs;
        CREATE TRIGGER trigger_update_hpb_configs_updated_at
        BEFORE UPDATE ON had_potongan_bulanan_configs
        FOR EACH ROW
        EXECUTE FUNCTION update_hpb_configs_updated_at();
        """
    )


def insert_calendar_holiday(date_str: str, name: str, state: str = None, is_national: bool = False, is_observance: bool = False, created_by: str = None) -> bool:
    """Insert a calendar_holidays row. Returns True on success."""
    try:
        if not _probe_table_exists('calendar_holidays'):
            # table missing; caller should run migration
            return False
        payload = {
            'date': date_str,
            'name': name,
            'state': state,
            'is_national': bool(is_national),
            'is_observance': bool(is_observance),
            'created_at': datetime.now(pytz.UTC).isoformat()
        }
        # Only include optional columns if they actually exist in the DB schema
        try:
            if created_by is not None and _probe_column_exists('calendar_holidays', 'created_by'):
                payload['created_by'] = created_by
        except Exception:
            # probe failed; conservative approach: do not include optional column
            pass
        res = supabase.table('calendar_holidays').insert(payload).execute()
        return bool(res and getattr(res, 'data', None))
    except Exception as e:
        print(f"DEBUG: insert_calendar_holiday error: {e}")
        return False


def find_calendar_holidays_for_year(year: int, state: str = None) -> List[Dict]:
    """Return list of calendar_holidays rows for the year; state filtering applied client-side (state can be None for nationwide/all)."""
    try:
        if not _probe_table_exists('calendar_holidays'):
            return []
        start = f"{int(year)}-01-01"
        end = f"{int(year)}-12-31"
        q = supabase.table('calendar_holidays').select('*').gte('date', start).lte('date', end)
        resp = q.execute()
        rows = resp.data if resp and getattr(resp, 'data', None) else []
        if state:
            out = []
            for r in rows:
                rs = r.get('state')
                if rs is None or str(rs).strip().lower() == str(state).strip().lower():
                    out.append(r)
            return out
        return rows
    except Exception as e:
        print(f"DEBUG: find_calendar_holidays_for_year error: {e}")
        return []


def find_calendar_holidays_by_date(date_str: str, state: str = None) -> List[Dict]:
    """Return list of calendar_holidays rows matching a specific date (YYYY-MM-DD)."""
    try:
        if not _probe_table_exists('calendar_holidays'):
            return []
        resp = supabase.table('calendar_holidays').select('*').eq('date', date_str).execute()
        rows = resp.data if resp and getattr(resp, 'data', None) else []
        if state:
            rows = [r for r in rows if (r.get('state') is None or str(r.get('state')).strip().lower() == state.strip().lower())]
        return rows
    except Exception as e:
        print(f"DEBUG: find_calendar_holidays_by_date error: {e}")
        return []


def delete_calendar_holiday_by_id(holiday_id: str) -> bool:
    try:
        if not _probe_table_exists('calendar_holidays'):
            return False
        res = supabase.table('calendar_holidays').delete().eq('id', holiday_id).execute()
        return bool(res and getattr(res, 'data', None))
    except Exception as e:
        print(f"DEBUG: delete_calendar_holiday_by_id error: {e}")
        return False


def update_calendar_holiday_by_id(holiday_id: str, fields: Dict) -> bool:
    """Update calendar_holidays row by id with provided fields. Returns True on success."""
    try:
        if not _probe_table_exists('calendar_holidays'):
            return False
        if not isinstance(fields, dict) or not fields:
            return False
        res = supabase.table('calendar_holidays').update(fields).eq('id', holiday_id).execute()
        return bool(res and getattr(res, 'data', None))
    except Exception as e:
        print(f"DEBUG: update_calendar_holiday_by_id error: {e}")
        return False

def upsert_hpb_config(config_name: str, year: int, details: Dict) -> bool:
    """Upsert a Had Potongan Bulanan configuration JSON for a given year."""
    try:
        if not _probe_table_exists('had_potongan_bulanan_configs'):
            # Table missing; caller can run create_hpb_configs_table_sql()
            return False
        payload = {
            'config_name': config_name or 'default',
            'year': int(year),
            'details': details or {},
            'updated_at': datetime.now(pytz.UTC).isoformat(),
        }
        existing = (
            supabase.table('had_potongan_bulanan_configs')
            .select('id')
            .eq('config_name', payload['config_name'])
            .eq('year', payload['year'])
            .execute()
        )
        if existing.data:
            res = (
                supabase.table('had_potongan_bulanan_configs')
                .update(payload)
                .eq('config_name', payload['config_name'])
                .eq('year', payload['year'])
                .execute()
            )
            return bool(res.data)
        else:
            payload['created_at'] = datetime.now(pytz.UTC).isoformat()
            res = supabase.table('had_potongan_bulanan_configs').insert(payload).execute()
            return bool(res.data)
    except Exception as e:
        print(f"DEBUG: Error upserting HPB config: {e}")
        return False

def get_hpb_config(config_name: str, year: int) -> Optional[Dict]:
    """Fetch a Had Potongan Bulanan configuration by name and year."""
    try:
        if not _probe_table_exists('had_potongan_bulanan_configs'):
            return None
        resp = (
            supabase.table('had_potongan_bulanan_configs')
            .select('details')
            .eq('config_name', config_name or 'default')
            .eq('year', int(year))
            .limit(1)
            .execute()
        )
        if resp.data:
            return resp.data[0].get('details')
        return None
    except Exception as e:
        print(f"DEBUG: Error fetching HPB config: {e}")
        return None

# -----------------------------------------------------------------------------
# TP1 monthly details (dedicated table)
# -----------------------------------------------------------------------------
def create_tp1_monthly_details_table_sql() -> str:
    """Return SQL to create a dedicated TP1 monthly details table for Potongan Bulan Semasa."""
    return (
        """
        CREATE TABLE IF NOT EXISTS tp1_monthly_details (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            employee_id UUID NOT NULL,
            year INT NOT NULL,
            month INT NOT NULL,
            -- Snapshot JSON of the full TP1 inputs for the month (UI values)
            details JSONB NOT NULL,
            -- Aggregates for convenience
            other_reliefs_monthly DECIMAL(12,2) DEFAULT 0.00,
            socso_eis_lp1_monthly DECIMAL(12,2) DEFAULT 0.00,
            zakat_monthly DECIMAL(12,2) DEFAULT 0.00,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE (employee_id, year, month)
        );

        CREATE OR REPLACE FUNCTION update_tp1_monthly_details_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS trigger_update_tp1_monthly_details_updated_at ON tp1_monthly_details;
        CREATE TRIGGER trigger_update_tp1_monthly_details_updated_at
        BEFORE UPDATE ON tp1_monthly_details
        FOR EACH ROW
        EXECUTE FUNCTION update_tp1_monthly_details_updated_at();
        """
    )


def create_leave_request_states_table_sql() -> str:
    """Return SQL to create a table to store one-or-more state/location selections for leave requests.

    This supports cases where a leave request should be evaluated against a particular
    state (for holiday/deduction rules). The table is intentionally separate so that
    historical leave_requests remain unchanged and we can support multi-location leaves.
    """
    return (
        """
        CREATE TABLE IF NOT EXISTS leave_request_states (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            leave_request_id UUID NOT NULL,
            state TEXT NOT NULL,
            -- Whether observances (astronomical/natural observances) were included when selecting holidays
            show_observances BOOLEAN DEFAULT FALSE NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_leave_request_states_leave_request_id ON leave_request_states(leave_request_id);
        """
    )

def upsert_tp1_monthly_details(employee_uuid: str, year: int, month: int, details: Dict, aggregates: Dict) -> bool:
    """Upsert TP1 monthly details row with full JSON snapshot and aggregates."""
    try:
        payload = {
            'employee_id': employee_uuid,
            'year': int(year),
            'month': int(month),
            'details': details or {},
            'other_reliefs_monthly': float(aggregates.get('other_reliefs_monthly', 0.0) or 0.0),
            'socso_eis_lp1_monthly': float(aggregates.get('socso_eis_lp1_monthly', 0.0) or 0.0),
            'zakat_monthly': float(aggregates.get('zakat_monthly', 0.0) or 0.0),
            'updated_at': datetime.now(pytz.UTC).isoformat(),
        }
        # If table missing, do nothing silently; user can run SQL via create_tp1_monthly_details_table_sql()
        if not _probe_table_exists('tp1_monthly_details'):
            return False
        existing = supabase.table('tp1_monthly_details').select('id').eq('employee_id', employee_uuid).eq('year', year).eq('month', month).execute()
        if existing.data:
            res = supabase.table('tp1_monthly_details').update(payload).eq('employee_id', employee_uuid).eq('year', year).eq('month', month).execute()
            return bool(res.data)
        else:
            payload['created_at'] = datetime.now(pytz.UTC).isoformat()
            res = supabase.table('tp1_monthly_details').insert(payload).execute()
            return bool(res.data)
    except Exception as e:
        print(f"DEBUG: Error upserting TP1 monthly details: {e}")
        return False


def user_logins_lockout_migration_sql() -> str:
    """Return SQL to add failed_attempts and locked_until columns to user_logins.

    This SQL is idempotent (uses IF NOT EXISTS) and intended to be run manually in
    Supabase SQL editor or via psql. The project also includes `sql/alter_user_logins_add_lockout.sql`.
    """
    return (
        """
        BEGIN;

        ALTER TABLE IF EXISTS public.user_logins
            ADD COLUMN IF NOT EXISTS failed_attempts INTEGER DEFAULT 0 NOT NULL;

        ALTER TABLE IF EXISTS public.user_logins
            ADD COLUMN IF NOT EXISTS locked_until TIMESTAMPTZ NULL;

        CREATE INDEX IF NOT EXISTS idx_user_logins_locked_until ON public.user_logins(locked_until);

        COMMIT;
        """
    )


def user_logins_has_lockout_columns() -> bool:
    """Return True if both `failed_attempts` and `locked_until` columns exist on user_logins.

    Uses the existing _probe_column_exists helper for safe, non-fatal probing.
    """
    try:
        return _probe_column_exists('user_logins', 'failed_attempts') and _probe_column_exists('user_logins', 'locked_until')
    except Exception as e:
        print(f"DEBUG: Error probing user_logins lockout columns: {e}")
        return False


def get_employee_history(employee_id: str, limit: int = 50, offset: int = 0) -> list:
    """Fetch employee history/activity rows for an employee.

    Returns a list of dicts (may be empty). This helper is tolerant to a missing
    `employee_history` table and will return an empty list if the table doesn't exist.
    """
    try:
        if not _probe_table_exists('employee_history'):
            return []
        # Primary attempt: exact match on employee_id (UUID expected).
        try:
            resp = (
                supabase.table('employee_history')
                .select('*')
                .eq('employee_id', employee_id)
                .order('created_at', desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )
        except Exception as inner_e:
            # Likely the provided identifier is not a UUID; fall back to a safe text-match
            # Use ilike to match substrings (this is tolerant and won't error on non-UUIDs)
            # First, try to resolve the identifier to the canonical employee UUID
            try:
                if _probe_table_exists('employees'):
                    # Try exact match on employee_id or email
                    emp = supabase.table('employees').select('id').eq('employee_id', employee_id).limit(1).execute()
                    if emp and getattr(emp, 'data', None):
                        resolved = emp.data[0].get('id')
                    else:
                        emp2 = supabase.table('employees').select('id').eq('email', employee_id).limit(1).execute()
                        resolved = emp2.data[0].get('id') if emp2 and getattr(emp2, 'data', None) else None
                    if resolved:
                        resp = (
                            supabase.table('employee_history')
                            .select('*')
                            .eq('employee_id', resolved)
                            .order('created_at', desc=True)
                            .limit(limit)
                            .offset(offset)
                            .execute()
                        )
                        if resp and getattr(resp, 'data', None):
                            return resp.data
            except Exception:
                # ignore and fall back to broader searches below
                pass

            try:
                resp = (
                    supabase.table('employee_history')
                    .select('*')
                    .ilike('employee_id', f"%{employee_id}%")
                    .order('created_at', desc=True)
                    .limit(limit)
                    .offset(offset)
                    .execute()
                )
            except Exception as e2:
                # Last-resort: try matching by company or notes content (very broad)
                try:
                    resp = (
                        supabase.table('employee_history')
                        .select('*')
                        .ilike('notes', f"%{employee_id}%")
                        .order('created_at', desc=True)
                        .limit(limit)
                        .offset(offset)
                        .execute()
                    )
                except Exception:
                    # Give up and re-raise the original inner exception for logging
                    raise inner_e

        if resp and getattr(resp, 'data', None):
            return resp.data
        return []
    except Exception as e:
        print(f"DEBUG: Error fetching employee history: {e}")
        return []

# ------------------------------
# Monthly deductions (Potongan Bulan Semasa)
# ------------------------------
def get_monthly_deductions(employee_id: str, year: int, month: int) -> Dict:
    """Fetch monthly deductions for an employee for a given year/month.
    Returns defaults when no record exists."""
    try:
        resp = (
            supabase.table('payroll_monthly_deductions')
            .select('*')
            .eq('employee_id', employee_id)
            .eq('year', year)
            .eq('month', month)
            .execute()
        )
        if resp.data:
            row = resp.data[0]
            return {
                'zakat_monthly': float(row.get('zakat_monthly', 0) or 0),
                'religious_travel_monthly': float(row.get('religious_travel_monthly', 0) or 0),
                'other_deductions_amount': float(row.get('other_deductions_amount', 0) or 0),
                'other_reliefs_monthly': float(row.get('other_reliefs_monthly', 0) or 0),
                'socso_eis_lp1_monthly': float(row.get('socso_eis_lp1_monthly', 0) or 0),
            }
        else:
            return {
                'zakat_monthly': 0.0,
                'religious_travel_monthly': 0.0,
                'other_deductions_amount': 0.0,
                'other_reliefs_monthly': 0.0,
                'socso_eis_lp1_monthly': 0.0,
            }
    except Exception as e:
        print(f"DEBUG: Error fetching monthly deductions: {e}")
        return {
            'zakat_monthly': 0.0,
            'religious_travel_monthly': 0.0,
            'other_deductions_amount': 0.0,
            'other_reliefs_monthly': 0.0,
            'socso_eis_lp1_monthly': 0.0,
        }

def upsert_monthly_deductions(employee_id: str, year: int, month: int, data: Dict) -> bool:
    """Create or update monthly deductions for an employee for a given year/month."""
    try:
        # Ensure required keys
        payload = {
            'employee_id': employee_id,
            'year': int(year),
            'month': int(month),
            'zakat_monthly': float(data.get('zakat_monthly', 0) or 0),
            'religious_travel_monthly': float(data.get('religious_travel_monthly', 0) or 0),
            'other_deductions_amount': float(data.get('other_deductions_amount', 0) or 0),
            'other_reliefs_monthly': float(data.get('other_reliefs_monthly', 0) or 0),
            'updated_at': datetime.now(pytz.UTC).isoformat(),
        }
        # Add optional SOCSO+EIS LP1 column only if present in schema
        try:
            if _probe_column_exists('payroll_monthly_deductions', 'socso_eis_lp1_monthly'):
                payload['socso_eis_lp1_monthly'] = float(data.get('socso_eis_lp1_monthly', 0) or 0)
        except Exception:
            pass

        existing = (
            supabase.table('payroll_monthly_deductions')
            .select('id')
            .eq('employee_id', employee_id)
            .eq('year', year)
            .eq('month', month)
            .execute()
        )
        if existing.data:
            res = (
                supabase.table('payroll_monthly_deductions')
                .update(payload)
                .eq('employee_id', employee_id)
                .eq('year', year)
                .eq('month', month)
                .execute()
            )
            return bool(res.data)
        else:
            payload['created_at'] = datetime.now(pytz.UTC).isoformat()
            res = supabase.table('payroll_monthly_deductions').insert(payload).execute()
            return bool(res.data)
    except Exception as e:
        print(f"DEBUG: Error upserting monthly deductions: {e}")
        return False

def upload_profile_picture(file_path: str, employee_id: str) -> Optional[str]:
    try:
        if not os.path.exists(file_path):
            print(f"DEBUG: File does not exist or is inaccessible: {file_path}")
            return None
        if not employee_id:
            print("DEBUG: Employee ID is empty")
            return None
        file_name = f"{employee_id}_{os.path.basename(file_path)}"
        subfolder = "profile_pictures"
        full_path = f"{subfolder}/{file_name}"
        print(f"DEBUG: Attempting to upload file: {full_path} to bucket employees.doc for employee_id: {employee_id}")
        
        response = supabase.table("employees").select("photo_url, email").eq("employee_id", employee_id).execute()
        if not response.data:
            print(f"DEBUG: No employee found for employee_id: {employee_id}")
            return None
        email = response.data[0].get("email")
        print(f"DEBUG: Found employee with email: {email}")
        
        if response.data[0].get("photo_url"):
            old_picture = response.data[0]["photo_url"]
            if old_picture and not old_picture.endswith("default_avatar.png"):
                try:
                    old_path = old_picture.replace(f"https://wxaerkdmpxriveyknfov.supabase.co/storage/v1/object/public/employees.doc/", "")
                    supabase.storage.from_("employees.doc").remove([old_path])
                    print(f"DEBUG: Deleted old profile picture: {old_path}")
                except Exception as e:
                    print(f"DEBUG: Non-critical error deleting old profile picture: {str(e)}")
        
        with open(file_path, "rb") as f:
            response = supabase.storage.from_("employees.doc").upload(
                path=full_path,
                file=f,
                file_options={"content-type": f"image/{os.path.splitext(file_path)[1].lstrip('.')}"}
            )
            print(f"DEBUG: Upload response: {response}")
        
        if hasattr(response, 'path') and response.path == full_path:
            public_url = supabase.storage.from_("employees.doc").get_public_url(full_path)
            print(f"DEBUG: Profile picture uploaded successfully, public URL: {public_url}")
            return public_url
        else:
            print(f"DEBUG: Profile picture upload failed for {full_path}. Response: {response}")
            return None
    except Exception as e:
        print(f"DEBUG: Error uploading profile picture: {str(e)}")
        return None

def login_user(email, password):
    """Authenticate a user with optional lockout behavior.

    Returns a dict: {"success": bool, "role": Optional[str], "locked_until": Optional[str]}.
    """
    try:
        email_norm = (email or '').lower()
        # request lockout-aware columns if present
        cols = "email, password, role"
        if user_logins_has_lockout_columns():
            cols = "email, password, role, failed_attempts, locked_until"

        response = supabase.table("user_logins").select(cols).eq("email", email_norm).execute()
        if not response.data:
            _log_security_event('login_failure', user_email=email_norm, success=False, error_message='Unknown email')
            return {"success": False, "role": None}

        user = response.data[0]

        # If lockout columns are present, check locked_until
        if 'locked_until' in user and user.get('locked_until'):
            lu = _parse_timestamptz(user.get('locked_until'))
            now_utc = datetime.now(pytz.UTC)
            if lu and lu > now_utc:
                # Account is locked
                _log_security_event('login_failure', user_email=email_norm, success=False,
                                    error_message=f'Account locked until {lu.isoformat()}',
                                    details={'locked_until': lu.isoformat()})
                return {"success": False, "role": None, "locked_until": lu.isoformat()}

        stored_password = user["password"].encode('utf-8')
        if bcrypt.checkpw(password.encode('utf-8'), stored_password):
            # Successful login; reset counters if columns exist
            try:
                if 'failed_attempts' in user or 'locked_until' in user:
                    supabase.table('user_logins').update({
                        'failed_attempts': 0,
                        'locked_until': None
                    }).eq('email', email_norm).execute()
            except Exception:
                pass
            _log_security_event('login_success', user_email=email_norm, success=True, details={'role': user.get('role')})
            return {"success": True, "role": user.get("role", "user"), "email": user.get("email")}
        else:
            # Failed password; increment failed_attempts and possibly lock
            try:
                if 'failed_attempts' in user:
                    cur = int(user.get('failed_attempts') or 0)
                    new = cur + 1
                    update_data = {'failed_attempts': new}
                    lock_set = False
                    if new >= LOGIN_LOCK_THRESHOLD:
                        lock_until = datetime.now(pytz.UTC) + timedelta(minutes=LOGIN_LOCK_DURATION_MINUTES)
                        update_data['locked_until'] = lock_until.isoformat()
                        lock_set = True
                    supabase.table('user_logins').update(update_data).eq('email', email_norm).execute()
                    if lock_set:
                        _log_security_event('login_failure', user_email=email_norm, success=False,
                                            error_message='Account locked due to repeated failures',
                                            details={'failed_attempts': new, 'locked_until': update_data.get('locked_until')})
                    else:
                        _log_security_event('login_failure', user_email=email_norm, success=False,
                                            error_message='Invalid credentials',
                                            details={'failed_attempts': new})
                else:
                    _log_security_event('login_failure', user_email=email_norm, success=False, error_message='Invalid credentials')
            except Exception as e:
                # Non-fatal: still return failure
                _log_security_event('login_failure', user_email=email_norm, success=False, error_message=f'Invalid credentials; update failed: {e}')
            return {"success": False, "role": None}
    except Exception as e:
        print(f"DEBUG: Error during login: {str(e)}")
        _log_security_event('login_failure', user_email=(email or '').lower(), success=False, error_message=str(e))
        return {"success": False, "role": None}

def login_user_by_username(username: str, password: str):
    """Authenticate a user by username with optional lockout behavior.

    Returns a dict: {"success": bool, "role": Optional[str], "locked_until": Optional[str], "email": Optional[str]}.
    """
    try:
        username_norm = (username or '').lower()
        cols = "username, email, password, role"
        if user_logins_has_lockout_columns():
            cols = "username, email, password, role, failed_attempts, locked_until"

        response = supabase.table("user_logins").select(cols).eq("username", username_norm).execute()
        if not response.data:
            _log_security_event('login_failure', user_email=username_norm, success=False, error_message='Unknown username')
            return {"success": False, "role": None}

        user = response.data[0]

        # Check lockout
        if 'locked_until' in user and user.get('locked_until'):
            lu = _parse_timestamptz(user.get('locked_until'))
            now_utc = datetime.now(pytz.UTC)
            if lu and lu > now_utc:
                _log_security_event('login_failure', user_email=username_norm, success=False,
                                    error_message=f'Account locked until {lu.isoformat()}',
                                    details={'locked_until': lu.isoformat()})
                return {"success": False, "role": None, "locked_until": lu.isoformat()}

        stored_password = user["password"].encode('utf-8')
        if bcrypt.checkpw(password.encode('utf-8'), stored_password):
            # Successful login; reset counters if present
            try:
                if 'failed_attempts' in user or 'locked_until' in user:
                    supabase.table('user_logins').update({
                        'failed_attempts': 0,
                        'locked_until': None
                    }).eq('username', username_norm).execute()
            except Exception:
                pass
            _log_security_event('login_success', user_email=username_norm, success=True, details={'role': user.get('role')})
            return {"success": True, "role": user.get("role", "user"), "email": user.get("email")}
        else:
            # Failed password; increment failed_attempts and possibly lock
            try:
                if 'failed_attempts' in user:
                    cur = int(user.get('failed_attempts') or 0)
                    new = cur + 1
                    update_data = {'failed_attempts': new}
                    lock_set = False
                    if new >= LOGIN_LOCK_THRESHOLD:
                        lock_until = datetime.now(pytz.UTC) + timedelta(minutes=LOGIN_LOCK_DURATION_MINUTES)
                        update_data['locked_until'] = lock_until.isoformat()
                        lock_set = True
                    supabase.table('user_logins').update(update_data).eq('username', username_norm).execute()
                    if lock_set:
                        _log_security_event('login_failure', user_email=username_norm, success=False,
                                            error_message='Account locked due to repeated failures',
                                            details={'failed_attempts': new, 'locked_until': update_data.get('locked_until')})
                    else:
                        _log_security_event('login_failure', user_email=username_norm, success=False,
                                            error_message='Invalid credentials',
                                            details={'failed_attempts': new})
                else:
                    _log_security_event('login_failure', user_email=username_norm, success=False, error_message='Invalid credentials')
            except Exception as e:
                _log_security_event('login_failure', user_email=username_norm, success=False, error_message=f'Invalid credentials; update failed: {e}')
            return {"success": False, "role": None}
    except Exception as e:
        print(f"DEBUG: Error during username login: {str(e)}")
        _log_security_event('login_failure', user_email=(username or '').lower(), success=False, error_message=str(e))
        return {"success": False, "role": None}

def insert_employee(data: dict, password: Optional[str] = None) -> dict:
    try:
        email = data.get("email")
        if not email:
            print("DEBUG: Email is missing")
            return {"success": False, "error": "Email is required"}

        response = supabase.table("user_logins").select("email").eq("email", email.lower()).execute()
        if response.data:
            print(f"DEBUG: Email already exists: {email.lower()}")
            return {"success": False, "error": "Email already exists"}
        # Optional username support
        username = (data.get("username") or "").strip().lower()
        if username:
            uname_resp = supabase.table("user_logins").select("username").eq("username", username).execute()
            if uname_resp.data:
                print(f"DEBUG: Username already exists: {username}")
                return {"success": False, "error": "Username already exists"}

        employee_data = data.copy()
        role = employee_data.pop("role", None)
        employee_data["created_at"] = datetime.now(KL_TZ).isoformat()
        employee_data["religion"] = employee_data.get("religion", "Other")

        employee_response = supabase.table("employees").insert(employee_data).execute()
        if not employee_response.data:
            print(f"DEBUG: Failed to insert employee: {employee_response}")
            return {"success": False, "error": "Failed to create employee record"}

        if password:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            login_data = {
                "email": email.lower(),
                "username": username or email.split('@')[0].lower(),
                "password": hashed_password,
                "role": role if role else "employee",
                "created_at": datetime.now(pytz.UTC).isoformat()
            }
            login_response = supabase.table("user_logins").insert(login_data).execute()
            if not login_response.data:
                print(f"DEBUG: Failed to insert user login: {login_response}")
                supabase.table("employees").delete().eq("employee_id", employee_data["employee_id"]).execute()
                return {"success": False, "error": "Failed to create user login"}

        print(f"DEBUG: Employee inserted for employee_id: {employee_data['employee_id']}")
        return {"success": True, "error": None}
    except Exception as e:
        print(f"DEBUG: Error inserting employee: {str(e)}")
        return {"success": False, "error": str(e)}

def update_employee(employee_id: str, data: dict) -> dict:
    try:
        employee_data = dict(data or {})
        # Strip auth/login-only fields that do not exist on employees
        for bad in ("username", "password", "role"):
            if bad in employee_data:
                employee_data.pop(bad, None)
        # Normalize empty-string fields to None to avoid storing empty strings in DB
        for _k in ("work_status", "payroll_status", "functional_group", "position"):
            if _k in employee_data and employee_data[_k] == "":
                employee_data[_k] = None
        employee_data["updated_at"] = datetime.now(pytz.UTC).isoformat()
        employee_data["religion"] = employee_data.get("religion", "Other")

        # Debug: Show what EPF/SOCSO and status data is being updated
        if 'epf_part' in employee_data:
            print(f"DEBUG: Updating epf_part to: {employee_data['epf_part']}")
        if 'socso_category' in employee_data:
            print(f"DEBUG: Updating socso_category to: {employee_data['socso_category']}")
        if 'work_status' in employee_data:
            print(f"DEBUG: Updating work_status to: {employee_data['work_status']}")
        if 'payroll_status' in employee_data:
            print(f"DEBUG: Updating payroll_status to: {employee_data['payroll_status']}")

        # Resilient update: remove unknown columns mentioned in PostgREST error and retry
        import re as _re
        attempts = 0
        max_attempts = max(3, len(employee_data) + 1)
        payload = dict(employee_data)
        response = None
        while attempts < max_attempts:
            attempts += 1
            try:
                response = supabase.table("employees").update(payload).eq("id", employee_id).execute()
                break
            except Exception as ue:
                msg = str(ue)
                m = _re.search(r"Could find the '([^']+)' column|Could not find the '([^']+)' column", msg)
                if not m:
                    m2 = _re.search(r"'([^']+)' column of 'employees' in the schema cache", msg)
                    missing = m2.group(1) if m2 else None
                else:
                    missing = m.group(1) or m.group(2)
                if missing and missing in payload:
                    print(f"DEBUG: Stripping unknown employees column during update: {missing}")
                    payload.pop(missing, None)
                    continue
                raise ue

        print(f"DEBUG: Update employee response for id {employee_id}: {getattr(response, 'data', None)}")
        if response and getattr(response, 'data', None):
            return {"success": True, "error": None}
        # Fallback: verify row exists (some PostgREST updates may return 204/no body)
        try:
            probe = supabase.table("employees").select("id").eq("id", employee_id).limit(1).execute()
            if probe and getattr(probe, 'data', None):
                return {"success": True, "error": None}
        except Exception:
            pass
        return {"success": False, "error": "Failed to update employee"}
    except Exception as e:
        print(f"DEBUG: Error updating employee: {str(e)}")
        return {"success": False, "error": str(e)}
    
def get_all_employees() -> list:
    try:
        result = supabase.table("employees").select("*").execute()
        return result.data
    except Exception as e:
        print(f"DEBUG: Error fetching employees: {str(e)}")
        return []


def get_calendar_ui_prefs(user_email: Optional[str] = None) -> dict:
    """Fetch calendar UI prefs for a given user_email. If no row for that user, return {}.

    If user_email is None, attempt to return the global prefs row (user_email IS NULL).
    This function is tolerant to missing table errors.
    """
    try:
        if not _probe_table_exists('calendar_ui_prefs'):
            return {}
        if user_email:
            resp = supabase.table('calendar_ui_prefs').select('prefs').eq('user_email', user_email).limit(1).execute()
            if resp.data:
                return resp.data[0].get('prefs') or {}
        # fallback to global
        resp = supabase.table('calendar_ui_prefs').select('prefs').is_('user_email', None).limit(1).execute()
        if resp.data:
            return resp.data[0].get('prefs') or {}
        return {}
    except Exception as e:
        print(f"DEBUG: Error fetching calendar UI prefs: {e}")
        return {}


def upsert_calendar_ui_prefs(prefs: dict, user_email: Optional[str] = None) -> bool:
    """Insert or update calendar UI prefs for a user or global (user_email=None).

    prefs will be stored as JSONB.
    """
    try:
        if not _probe_table_exists('calendar_ui_prefs'):
            return False
        # Try to find existing row
        if user_email:
            existing = supabase.table('calendar_ui_prefs').select('id').eq('user_email', user_email).limit(1).execute()
            payload = {'user_email': user_email, 'prefs': prefs, 'updated_at': datetime.now(pytz.UTC).isoformat()}
            if existing.data:
                res = supabase.table('calendar_ui_prefs').update(payload).eq('user_email', user_email).execute()
                return bool(res.data)
            else:
                res = supabase.table('calendar_ui_prefs').insert(payload).execute()
                return bool(res.data)
        else:
            existing = supabase.table('calendar_ui_prefs').select('id').is_('user_email', None).limit(1).execute()
            payload = {'user_email': None, 'prefs': prefs, 'updated_at': datetime.now(pytz.UTC).isoformat()}
            if existing.data:
                res = supabase.table('calendar_ui_prefs').update(payload).is_('user_email', None).execute()
                return bool(res.data)
            else:
                res = supabase.table('calendar_ui_prefs').insert(payload).execute()
                return bool(res.data)
    except Exception as e:
        print(f"DEBUG: Error upserting calendar UI prefs: {e}")
        return False

def submit_leave_request(
    employee_email: str,
    leave_type: str,
    start_date: str,
    end_date: str,
    title: str,
    document_url: Optional[str] = None,
    submitted_by_admin: Optional[str] = None,
    is_half_day: bool = False,
    half_day_period: Optional[str] = None,
    states: Optional[list] = None
) -> bool:
    try:
        data = {
            "employee_email": employee_email.lower(),
            "leave_type": leave_type,
            "start_date": start_date,
            "end_date": end_date,
            "title": title,
            "status": "pending",
            "document_url": document_url,
            "submitted_at": datetime.now(pytz.UTC).isoformat(),
            "is_half_day": is_half_day,
            "half_day_period": half_day_period
        }
        result = supabase.table("leave_requests").insert(data).execute()
        print(f"DEBUG: Submitted leave request for {employee_email}: {result.data}")
        
        if len(result.data) > 0:
            # Persist any associated states for the leave request if provided
            try:
                leave_row = result.data[0]
                leave_id = leave_row.get('id')
                if states and leave_id:
                    to_insert = []
                    for st in states:
                        if not st:
                            continue
                        to_insert.append({
                            'leave_request_id': leave_id,
                            'state': st.strip()
                        })
                    if to_insert:
                        supabase.table('leave_request_states').insert(to_insert).execute()
            except Exception as _sterr:
                print(f"DEBUG: Failed to persist leave_request states: {_sterr}")
            # Send email notifications
            try:
                from services.email_service import email_service
                
                # Get employee details for email
                employee_response = supabase.table("employees").select(
                    "full_name, employee_id, department"
                ).eq("email", employee_email.lower()).eq("status", "Active").execute()
                
                if employee_response.data:
                    employee_data = employee_response.data[0]
                    employee_data["email"] = employee_email
                    
                    leave_data = {
                        "leave_type": leave_type,
                        "start_date": start_date,
                        "end_date": end_date,
                        "title": title
                    }
                    
                    # Determine who to notify
                    if submitted_by_admin:
                        # Admin submitted on behalf of employee
                        # Notify admin and employee
                        email_service.send_admin_leave_request_notification(
                            submitted_by_admin, employee_data, leave_data, submitted_by_admin
                        )
                        # Also notify employee that leave was submitted for them
                        email_service.send_leave_status_notification(
                            employee_email, employee_data.get('full_name', 'Employee'), 
                            leave_data, "submitted", submitted_by_admin
                        )
                    else:
                        # Employee submitted their own request
                        # Notify admin/manager (using luminascea123@gmail.com as default manager)
                        manager_email = "luminascea123@gmail.com"  # This should be configurable
                        email_service.send_leave_request_notification(
                            manager_email, employee_data, leave_data
                        )
                        # Also send a confirmation to the employee that the request is submitted/pending
                        try:
                            email_service.send_leave_status_notification(
                                employee_email, employee_data.get('full_name', 'Employee'),
                                leave_data, "submitted", employee_email
                            )
                        except Exception:
                            pass
                        print(f"DEBUG: Leave request notification sent to manager: {manager_email}")
                
            except Exception as email_error:
                print(f"DEBUG: Error sending email notifications: {str(email_error)}")
                # Don't fail the request if email fails
        
        return len(result.data) > 0
    except Exception as e:
        print(f"DEBUG: Error submitting leave request: {str(e)}")
        return False

def fetch_user_leave_requests(employee_email: str) -> list:
    try:
        result = supabase.table("leave_requests").select("*").ilike("employee_email", employee_email.lower()).execute()
        return result.data
    except Exception as e:
        print(f"DEBUG: Error fetching leave requests: {str(e)}")
        return []

def update_leave_request_status(leave_id: str, status: str, admin_email: str) -> bool:
    try:
        if status not in ["pending", "approved", "rejected"]:
            print(f"DEBUG: Invalid leave status: {status}")
            return False
            
        # Get leave request details and current status first
        leave_request_response = supabase.table("leave_requests").select(
            "employee_email, leave_type, start_date, end_date, status, document_url, is_half_day, half_day_period"
        ).eq("id", leave_id).execute()
        
        if not leave_request_response.data:
            print(f"DEBUG: Leave request {leave_id} not found")
            return False
            
        leave_request = leave_request_response.data[0]
        previous_status = leave_request["status"]
        
        # Calculate working days for the leave period up-front so we can persist it when approving
        start_date = leave_request["start_date"]
        end_date = leave_request["end_date"]
        is_half_day = leave_request.get("is_half_day", False)

        # Retrieve any explicit state selection for the leave request
        try:
            state_rows = supabase.table('leave_request_states').select('state').eq('leave_request_id', leave_id).execute().data or []
            leave_state = state_rows[0]['state'] if state_rows else None
        except Exception:
            leave_state = None

        if is_half_day:
            leave_days = 0.5  # Half day leave
        else:
            print(f"DEBUG: update_leave_request_status will calculate working days for leave_id={leave_id}, state={leave_state}, start={start_date}, end={end_date}")
            leave_days = calculate_working_days(start_date, end_date, state=leave_state)
            print(f"DEBUG: update_leave_request_status calculated leave_days={leave_days} for leave_id={leave_id}")

        # Prepare base update payload
        data = {
            "status": status,
            "reviewed_by": admin_email.lower(),
            "reviewed_at": datetime.now(pytz.UTC).isoformat()
        }
        # Persist working_days only when moving into Approved; clear when moving out
        try:
            if previous_status != "approved" and status == "approved":
                data["working_days"] = leave_days
            elif previous_status == "approved" and status != "approved":
                # Keep audit minimal; remove approved-day when no longer approved
                data["working_days"] = None
        except Exception as _wd_err:
            print(f"DEBUG: Could not set working_days field (maybe column missing): {_wd_err}")

        result = supabase.table("leave_requests").update(data).eq("id", leave_id).execute()
        
        # Handle balance updates based on status change
        if len(result.data) > 0 and previous_status != status:
            try:
                # leave_days already computed above
                
                employee_email = leave_request["employee_email"]
                leave_type = leave_request["leave_type"]
                half_day_period = leave_request.get("half_day_period", "")
                
                period_info = f" ({half_day_period})" if is_half_day and half_day_period else ""
                print(f"DEBUG: Status change for {employee_email}: {previous_status} -> {status}, {leave_type}, {leave_days} days{period_info}")
                
                # Get employee_id for balance update
                employee_response = supabase.table("employees").select(
                    "employee_id"
                ).eq("email", employee_email).eq("status", "Active").execute()
                
                if employee_response.data:
                    employee_id = employee_response.data[0]["employee_id"]
                    year = datetime.now().year
                    
                    # Determine balance adjustment
                    adjustment = 0
                    if previous_status != "approved" and status == "approved":
                        # Newly approved - add to used days
                        adjustment = leave_days
                    elif previous_status == "approved" and status != "approved":
                        # Previously approved but now rejected/pending - subtract from used days
                        adjustment = -leave_days
                    
                    if adjustment != 0:
                        if leave_type.lower() == "annual":
                            # Update annual leave balance
                            balance_response = supabase.table("leave_balances").select(
                                "used_days"
                            ).eq("employee_id", employee_id).eq("year", year).execute()
                            
                            if balance_response.data:
                                current_used = balance_response.data[0]["used_days"]
                                new_used = max(0, current_used + adjustment)  # Don't go negative
                                
                                supabase.table("leave_balances").update({
                                    "used_days": new_used
                                }).eq("employee_id", employee_id).eq("year", year).execute()
                                
                                print(f"DEBUG: Updated annual leave balance: {current_used} -> {new_used} (adjustment: {adjustment})")
                        
                        elif leave_type.lower() == "sick":
                            # Check if sick leave has supporting document
                            document_url = leave_request.get("document_url")
                            has_document = document_url and document_url.strip()
                            
                            if has_document:
                                # Update sick leave balance (with document)
                                balance_response = supabase.table("sick_leave_balances").select(
                                    "used_sick_days"
                                ).eq("employee_id", employee_id).eq("year", year).execute()
                                
                                if balance_response.data:
                                    current_used = balance_response.data[0]["used_sick_days"]
                                    new_used = max(0, current_used + adjustment)  # Don't go negative
                                    
                                    supabase.table("sick_leave_balances").update({
                                        "used_sick_days": new_used
                                    }).eq("employee_id", employee_id).eq("year", year).execute()
                                    
                                    print(f"DEBUG: Updated sick leave balance (with document): {current_used} -> {new_used} (adjustment: {adjustment})")
                            else:
                                # No document - deduct from annual leave instead
                                balance_response = supabase.table("leave_balances").select(
                                    "used_days"
                                ).eq("employee_id", employee_id).eq("year", year).execute()
                                
                                if balance_response.data:
                                    current_used = balance_response.data[0]["used_days"]
                                    new_used = max(0, current_used + adjustment)  # Don't go negative
                                    
                                    supabase.table("leave_balances").update({
                                        "used_days": new_used
                                    }).eq("employee_id", employee_id).eq("year", year).execute()
                                    
                                    print(f"DEBUG: Updated annual leave balance (sick leave without document): {current_used} -> {new_used} (adjustment: {adjustment})")
                
            except Exception as balance_error:
                print(f"DEBUG: Error updating leave balance: {str(balance_error)}")
                # Don't fail the main operation if balance update fails
            # Update short-term work status in employees and employee_status table
            try:
                # Determine new short-term work status
                new_work_status = None
                if status == 'approved':
                    lt = (leave_type or '').lower()
                    if lt == 'sick':
                        new_work_status = 'On Sick Leave'
                    elif lt == 'unpaid':
                        new_work_status = 'On Unpaid Leave'
                    else:
                        new_work_status = 'On Leave'
                else:
                    # If leave is no longer approved, restore to On Duty
                    new_work_status = 'On Duty'

                # Persist to employees.work_status and upsert into employee_status (best-effort)
                try:
                    # Update employees row for short-term visibility
                    supabase.table('employees').update({'work_status': new_work_status}).eq('email', employee_email).execute()
                except Exception as _e:
                    print(f"DEBUG: Failed to update employees.work_status: {_e}")

                # Removed stray TP1 auto-load block (not relevant in leave status flow)

                try:
                    # upsert_employee_status is resilient to schema differences
                    from services.supabase_employee_history import upsert_employee_status
                    # Prefer using employee_id if available
                    if 'employee_id' not in locals() or not employee_id:
                        # attempt to fetch employee_id
                        er = supabase.table('employees').select('employee_id').eq('email', employee_email).limit(1).execute()
                        if er and getattr(er, 'data', None):
                            employee_id = er.data[0].get('employee_id')
                    if employee_id:
                        upsert_employee_status(employee_id, {
                            'work_status': new_work_status,
                            'last_changed_by': admin_email,
                            'last_changed_at': datetime.now(pytz.UTC).isoformat()
                        })
                except Exception as _e:
                    print(f"DEBUG: Failed to upsert employee_status: {_e}")
            except Exception as e:
                print(f"DEBUG: Error updating short-term work status: {e}")
            
            # Send email notification for status change
            try:
                from services.email_service import email_service
                
                # Get employee details for email
                employee_response = supabase.table("employees").select(
                    "full_name, employee_id, department"
                ).eq("email", employee_email).eq("status", "Active").execute()
                
                if employee_response.data:
                    employee_name = employee_response.data[0].get('full_name', 'Employee')
                    
                    leave_data = {
                        "leave_type": leave_request["leave_type"],
                        "start_date": leave_request["start_date"],
                        "end_date": leave_request["end_date"],
                        "title": leave_request.get("title", "N/A")
                    }
                    
                    # Send notification to employee about status change
                    email_service.send_leave_status_notification(
                        employee_email, employee_name, leave_data, status, admin_email
                    )
                    print(f"DEBUG: Leave status notification sent to employee: {employee_email}")
                
            except Exception as email_error:
                print(f"DEBUG: Error sending status change email: {str(email_error)}")
                # Don't fail the main operation if email fails
        
        print(f"DEBUG: Update leave request response for id {leave_id} by {admin_email}: {result.data}")
        return len(result.data) > 0
    except Exception as e:
        print(f"DEBUG: Error updating leave request status: {str(e)}")
        return False

def cancel_approved_leave_request(leave_id: str, admin_email: str, reason: str = "Cancelled by admin") -> bool:
    """Cancel an approved leave request and restore leave balance"""
    try:
        # Get leave request details first
        leave_request_response = supabase.table("leave_requests").select(
            "employee_email, leave_type, start_date, end_date, status, document_url, is_half_day, half_day_period"
        ).eq("id", leave_id).execute()
        
        if not leave_request_response.data:
            print(f"DEBUG: Leave request {leave_id} not found")
            return False
            
        leave_request = leave_request_response.data[0]
        
        # Only allow canceling approved requests
        if leave_request["status"] != "approved":
            print(f"DEBUG: Cannot cancel non-approved leave request. Current status: {leave_request['status']}")
            return False
        
        # Check if leave has already started (cannot cancel past/current leaves)
        start_date = datetime.strptime(leave_request["start_date"], "%Y-%m-%d").date()
        today = datetime.now().date()
        
        if start_date <= today:
            print(f"DEBUG: Cannot cancel leave that has already started or passed. Start date: {start_date}, Today: {today}")
            return False
        
        # Update leave request status to cancelled
        data = {
            "status": "cancelled",
            "reviewed_by": admin_email.lower(),
            "reviewed_at": datetime.now(pytz.UTC).isoformat(),
            "title": f"{leave_request.get('title', '')} [CANCELLED: {reason}]"
        }
        result = supabase.table("leave_requests").update(data).eq("id", leave_id).execute()
        
        if len(result.data) > 0:
            try:
                # Restore leave balance by reducing used days
                start_date_str = leave_request["start_date"]
                end_date_str = leave_request["end_date"]
                is_half_day = leave_request.get("is_half_day", False)
                
                if is_half_day:
                    leave_days = 0.5  # Half day leave
                else:
                    leave_days = calculate_working_days(start_date_str, end_date_str)
                
                employee_email = leave_request["employee_email"]
                leave_type = leave_request["leave_type"]
                half_day_period = leave_request.get("half_day_period", "")
                
                period_info = f" ({half_day_period})" if is_half_day and half_day_period else ""
                print(f"DEBUG: Cancelling {leave_type} leave for {employee_email}: {leave_days} days{period_info} to restore")
                
                # Get employee_id for balance update
                employee_response = supabase.table("employees").select(
                    "employee_id"
                ).eq("email", employee_email).eq("status", "Active").execute()
                
                if employee_response.data:
                    employee_id = employee_response.data[0]["employee_id"]
                    year = datetime.now().year
                    
                    if leave_type.lower() == "annual":
                        # Restore annual leave balance
                        balance_response = supabase.table("leave_balances").select(
                            "used_days"
                        ).eq("employee_id", employee_id).eq("year", year).execute()
                        
                        if balance_response.data:
                            current_used = balance_response.data[0]["used_days"]
                            new_used = max(0, current_used - leave_days)  # Restore days
                            
                            supabase.table("leave_balances").update({
                                "used_days": new_used
                            }).eq("employee_id", employee_id).eq("year", year).execute()
                            
                            print(f"DEBUG: Restored annual leave balance: {current_used} -> {new_used} (restored: {leave_days})")
                    
                    elif leave_type.lower() == "sick":
                        # Check if sick leave had supporting document
                        document_url = leave_request.get("document_url")
                        has_document = document_url and document_url.strip()
                        
                        if has_document:
                            # Restore sick leave balance (had document)
                            balance_response = supabase.table("sick_leave_balances").select(
                                "used_sick_days"
                            ).eq("employee_id", employee_id).eq("year", year).execute()
                            
                            if balance_response.data:
                                current_used = balance_response.data[0]["used_sick_days"]
                                new_used = max(0, current_used - leave_days)  # Restore days
                                
                                supabase.table("sick_leave_balances").update({
                                    "used_sick_days": new_used
                                }).eq("employee_id", employee_id).eq("year", year).execute()
                                
                                print(f"DEBUG: Restored sick leave balance (had document): {current_used} -> {new_used} (restored: {leave_days})")
                        else:
                            # No document - restore to annual leave instead
                            balance_response = supabase.table("leave_balances").select(
                                "used_days"
                            ).eq("employee_id", employee_id).eq("year", year).execute()
                            
                            if balance_response.data:
                                current_used = balance_response.data[0]["used_days"]
                                new_used = max(0, current_used - leave_days)  # Restore days
                                
                                supabase.table("leave_balances").update({
                                    "used_days": new_used
                                }).eq("employee_id", employee_id).eq("year", year).execute()
                                
                                print(f"DEBUG: Restored annual leave balance (sick leave without document): {current_used} -> {new_used} (restored: {leave_days})")
                
            except Exception as balance_error:
                print(f"DEBUG: Error restoring leave balance: {str(balance_error)}")
                # Don't fail the main operation if balance update fails
            
            # Send email notification about cancellation
            try:
                from services.email_service import email_service
                
                # Get employee details for email
                employee_response = supabase.table("employees").select(
                    "full_name, employee_id, department"
                ).eq("email", employee_email).eq("status", "Active").execute()
                
                if employee_response.data:
                    employee_name = employee_response.data[0].get('full_name', 'Employee')
                    
                    leave_data = {
                        "leave_type": leave_request["leave_type"],
                        "start_date": leave_request["start_date"],
                        "end_date": leave_request["end_date"],
                        "title": leave_request.get("title", ""),
                        "cancellation_reason": reason
                    }
                    
                    # Send notification to employee about cancellation
                    email_service.send_leave_status_notification(
                        employee_email, employee_name, leave_data, "cancelled", admin_email
                    )
                    print(f"DEBUG: Leave cancellation notification sent to employee: {employee_email}")
                
            except Exception as email_error:
                print(f"DEBUG: Error sending cancellation email: {str(email_error)}")
                # Don't fail the main operation if email fails
            # Ensure short-term work status is set back to On Duty for the employee
            try:
                supabase.table('employees').update({'work_status': 'On Duty'}).eq('email', employee_email).execute()
            except Exception as _e:
                print(f"DEBUG: Failed to update employees.work_status during cancellation: {_e}")

            try:
                from services.supabase_employee_history import upsert_employee_status
                # attempt to fetch employee_id
                er = supabase.table('employees').select('employee_id').eq('email', employee_email).limit(1).execute()
                if er and getattr(er, 'data', None):
                    emp_id = er.data[0].get('employee_id')
                    if emp_id:
                        upsert_employee_status(emp_id, {
                            'work_status': 'On Duty',
                            'last_changed_by': admin_email,
                            'last_changed_at': datetime.now(pytz.UTC).isoformat()
                        })
            except Exception as _e:
                print(f"DEBUG: Failed to upsert employee_status during cancellation: {_e}")
        
        print(f"DEBUG: Cancel leave request response for id {leave_id} by {admin_email}: {result.data}")
        return len(result.data) > 0
    except Exception as e:
        print(f"DEBUG: Error cancelling leave request: {str(e)}")
        return False

def get_all_leave_requests() -> list:
    try:
        result = supabase.table("leave_requests").select("*").execute()
        print(f"DEBUG: Fetched {len(result.data)} leave requests: {result.data}")
        return result.data
    except Exception as e:
        print(f"DEBUG: Error fetching all leave requests: {str(e)}")
        return []

def reconcile_employees_work_status_for_today(now_date: Optional[str] = None, admin_email: Optional[str] = None) -> Dict[str, Any]:
    """Best-effort reconciliation to ensure employees' short-term work_status reflects today's leave.

    Logic:
    - If an employee has an approved leave covering today, set work_status to:
        'On Sick Leave' (sick), 'On Unpaid Leave' (unpaid), otherwise 'On Leave'.
      If multiple overlaps, priority: Sick > Unpaid > Leave.
    - If an employee is currently marked as 'On Leave'/'On Sick Leave'/'On Unpaid Leave' but
      has no approved leave covering today, set work_status to 'On Duty'.

    Returns a dict with counts of updates performed.
    """
    try:
        today = None
        if isinstance(now_date, str) and now_date.strip():
            try:
                today = datetime.strptime(now_date.strip(), "%Y-%m-%d").date()
            except Exception:
                today = date.today()
        else:
            today = date.today()
        today_str = today.strftime("%Y-%m-%d")

        # 1) Fetch all approved leave that covers today
        try:
            lr = (
                supabase
                .table('leave_requests')
                .select('employee_email, leave_type, start_date, end_date, status')
                .eq('status', 'approved')
                .lte('start_date', today_str)
                .gte('end_date', today_str)
                .execute()
            )
            leave_rows = lr.data or []
        except Exception as e:
            print(f"DEBUG: reconcile: failed to query leave_requests: {e}")
            leave_rows = []

        # Build desired status per email with priority Sick > Unpaid > Leave
        priority = {'on sick leave': 3, 'on unpaid leave': 2, 'on leave': 1}
        desired_by_email: Dict[str, str] = {}
        for r in leave_rows:
            email = (r.get('employee_email') or '').lower()
            lt = (r.get('leave_type') or '').strip().lower()
            if not email:
                continue
            if lt == 'sick':
                ns = 'On Sick Leave'
            elif lt == 'unpaid':
                ns = 'On Unpaid Leave'
            else:
                ns = 'On Leave'
            prev = desired_by_email.get(email)
            if not prev or priority[ns.lower()] > priority[prev.lower()]:
                desired_by_email[email] = ns

        # 2) Fetch employees currently marked as any leave status
        leave_like_statuses = ['On Leave', 'On Sick Leave', 'On Unpaid Leave']
        try:
            emp_resp = (
                supabase
                .table('employees')
                .select('id, employee_id, email, work_status')
                .in_('work_status', leave_like_statuses)
                .execute()
            )
            leave_like_emps = emp_resp.data or []
        except Exception as e:
            print(f"DEBUG: reconcile: failed to query employees with leave-like status: {e}")
            leave_like_emps = []

        updated_to_leave = 0
        updated_to_duty = 0

        # 3) Ensure all active-leave employees reflect correct status
        active_emails = set(desired_by_email.keys())
        if active_emails:
            try:
                act_resp = (
                    supabase
                    .table('employees')
                    .select('id, employee_id, email, work_status')
                    .in_('email', list(active_emails))
                    .execute()
                )
                active_emps = act_resp.data or []
            except Exception as e:
                print(f"DEBUG: reconcile: failed to query active-leave employees: {e}")
                active_emps = []
            # Update mismatches
            for emp in active_emps:
                email = (emp.get('email') or '').lower()
                desired = desired_by_email.get(email)
                current = emp.get('work_status')
                if desired and desired != current:
                    try:
                        supabase.table('employees').update({'work_status': desired}).eq('id', emp.get('id')).execute()
                        updated_to_leave += 1
                    except Exception as _e:
                        print(f"DEBUG: reconcile: failed updating work_status to {desired} for {email}: {_e}")
                    # best-effort status snapshot
                    try:
                        from services.supabase_employee_history import upsert_employee_status
                        emp_code = emp.get('employee_id')
                        if emp_code:
                            upsert_employee_status(emp_code, {
                                'work_status': desired,
                                'last_changed_by': admin_email or 'system@startup',
                                'last_changed_at': datetime.now(pytz.UTC).isoformat()
                            })
                    except Exception as _e:
                        print(f"DEBUG: reconcile: failed upserting employee_status for {email}: {_e}")

        # 4) For employees currently marked as leave-like but with no active leave, set to On Duty
        active_emails_lower = set([e.lower() for e in active_emails])
        for emp in leave_like_emps:
            email = (emp.get('email') or '').lower()
            if email not in active_emails_lower:
                # Restore to On Duty
                try:
                    supabase.table('employees').update({'work_status': 'On Duty'}).eq('id', emp.get('id')).execute()
                    updated_to_duty += 1
                except Exception as _e:
                    print(f"DEBUG: reconcile: failed restoring On Duty for {email}: {_e}")
                # best-effort status snapshot
                try:
                    from services.supabase_employee_history import upsert_employee_status
                    emp_code = emp.get('employee_id')
                    if emp_code:
                        upsert_employee_status(emp_code, {
                            'work_status': 'On Duty',
                            'last_changed_by': admin_email or 'system@startup',
                            'last_changed_at': datetime.now(pytz.UTC).isoformat()
                        })
                except Exception as _e:
                    print(f"DEBUG: reconcile: failed snapshot to On Duty for {email}: {_e}")

        summary = {
            'date': today_str,
            'active_leave_employees': len(active_emails),
            'updated_to_leave': updated_to_leave,
            'updated_to_duty': updated_to_duty
        }
        print(f"DEBUG: reconcile_employees_work_status_for_today summary: {summary}")
        return summary
    except Exception as e:
        print(f"DEBUG: reconcile failed: {e}")
        return {'error': str(e)}

def upload_document_to_bucket(file_path: str, employee_email: str, is_leave_request: bool = False) -> Optional[str]:
    try:
        if not employee_email:
            print("DEBUG: Employee email is missing")
            return None
        if not os.path.exists(file_path):
            print(f"DEBUG: File does not exist or is inaccessible: {file_path}")
            return None
        file_extension = os.path.splitext(file_path)[1].lstrip('.')
        unique_suffix = str(uuid.uuid4())[:8]
        email_prefix = employee_email.split("@")[0]
        subfolder = "leave_requests" if is_leave_request else "documents"
        file_name = f"{subfolder}/{email_prefix}_{unique_suffix}.{file_extension}"

        # Determine content type using mimetypes
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            # Fallback to generic binary
            content_type = f"application/{file_extension}" if file_extension else "application/octet-stream"

        print(f"DEBUG: Attempting to upload document: {file_name} for {employee_email} (content-type: {content_type})")

        max_attempts = 5
        base_backoff = 0.5  # seconds
        last_exc = None
        for attempt in range(1, max_attempts + 1):
            try:
                with open(file_path, "rb") as f:
                    response = supabase.storage.from_("employees.doc").upload(
                        path=file_name,
                        file=f,
                        file_options={"content-type": content_type}
                    )

                print(f"DEBUG: Upload attempt {attempt} response: {response}")

                # Determine path from response (support different client versions)
                resp_path = None
                try:
                    resp_path = getattr(response, 'path', None)
                except Exception:
                    resp_path = None
                if not resp_path and isinstance(response, dict):
                    resp_path = response.get('path') or response.get('full_path') or response.get('fullPath')

                if resp_path == file_name or (isinstance(resp_path, str) and resp_path.endswith(file_name)):
                    public_url = supabase.storage.from_("employees.doc").get_public_url(file_name)
                    # Normalize URL: strip trailing '?' or empty query
                    if isinstance(public_url, str):
                        public_url = public_url.rstrip('?')
                    print(f"DEBUG: Document uploaded successfully: {file_name}, public URL: {public_url}")
                    return public_url

                # Unexpected response, treat as transient and retry
                print(f"DEBUG: Document upload returned unexpected response on attempt {attempt}: {response}")
                last_exc = Exception(f"Unexpected upload response: {response}")

            except Exception as e:
                last_exc = e
                tb = traceback.format_exc()
                print(f"DEBUG: Upload attempt {attempt} raised exception: {type(e).__name__}: {e}\n{tb}")

            # Exponential backoff with jitter before next attempt (unless last attempt)
            if attempt < max_attempts:
                backoff = base_backoff * (2 ** (attempt - 1))
                # add small jitter
                backoff = backoff + random.uniform(0, 0.4 * backoff)
                print(f"DEBUG: Waiting {backoff:.2f}s before retrying (attempt {attempt + 1}/{max_attempts})")
                time.sleep(backoff)

        # All attempts failed
        print(f"DEBUG: Document upload ultimately failed after {max_attempts} attempts. Last exception: {last_exc}")
        return None
    except Exception as e:
        print(f"DEBUG: Error uploading document: {str(e)}")
        return None

def delete_profile_picture(file_path: str) -> None:
    try:
        supabase.storage.from_("employees.doc").remove([file_path])
    except Exception as e:
        print(f"DEBUG: Error deleting profile picture: {str(e)}")

def get_all_attendance_records() -> list:
    try:
        result = supabase.table("attendance").select("*").execute()
        return result.data
    except Exception as e:
        print(f"DEBUG: Error fetching attendance records: {str(e)}")
        return []

def get_attendance_settings() -> dict:
    try:
        result = supabase.table("attendance_settings").select("*").limit(1).execute()
        return result.data[0] if result.data else {}
    except Exception as e:
        print(f"DEBUG: Error fetching attendance settings: {str(e)}")
        return {}

def update_attendance_settings(start_time: str, end_time: str, limit_time: str) -> bool:
    try:
        singleton_id = "00000000-0000-0000-0000-000000000001"
        data = {
            "id": singleton_id,
            "work_start": start_time,
            "work_end": end_time,
            "clock_in_limit": limit_time,
            "updated_at": datetime.now(pytz.UTC).isoformat()
        }
        # First try update
        result = supabase.table("attendance_settings").update(data).eq("id", singleton_id).execute()
        if not result.data:
            # Fallback to insert if no row was updated
            result = supabase.table("attendance_settings").insert(data).execute()
        return bool(result.data)
    except Exception as e:
        print(f"DEBUG: Error updating attendance settings: {str(e)}")
        return False

# ----------------------------
# Payroll calculation settings
# ----------------------------

def get_payroll_settings() -> Dict:
    """Retrieve global payroll calculation settings.

        Returns a dict with keys:
            - calculation_method: 'fixed' or 'variable'
            - active_variable_config: config name to use for variable mode (default 'default')
            - payroll_year_start_month: 1..12, for reporting/YTD windows (defaults to 1 = January)
    """
    try:
        resp = supabase.table('payroll_settings').select('*').limit(1).execute()
        row = (resp.data or [None])[0]
        if not row:
            # Fallback to local cache when table empty or not reachable
            try:
                from services.local_settings_cache import load_cached_payroll_settings
                return load_cached_payroll_settings()
            except Exception:
                return {'calculation_method': 'fixed', 'active_variable_config': 'default'}
        method = str(row.get('calculation_method') or 'fixed').strip().lower()
        if method not in ('fixed', 'variable'):
            method = 'fixed'
        active_cfg = row.get('active_variable_config') or 'default'
        try:
            pysm = int(row.get('payroll_year_start_month') or 1)
            if not (1 <= pysm <= 12):
                pysm = 1
        except Exception:
            pysm = 1
        return {'calculation_method': method, 'active_variable_config': active_cfg, 'payroll_year_start_month': pysm}
    except Exception as e:
        print(f"DEBUG: get_payroll_settings failed: {e}")
        try:
            from services.local_settings_cache import load_cached_payroll_settings
            data = load_cached_payroll_settings()
            if 'payroll_year_start_month' not in data:
                data['payroll_year_start_month'] = 1
            return data
        except Exception:
            return {'calculation_method': 'fixed', 'active_variable_config': 'default', 'payroll_year_start_month': 1}


def update_payroll_settings(calculation_method: Optional[str] = None,
                            active_variable_config: Optional[str] = None,
                            payroll_year_start_month: Optional[int] = None) -> bool:
    """Upsert the singleton payroll settings row.

    If table is empty, inserts the default id=1 row; otherwise updates.
    """
    try:
        payload: Dict[str, object] = {}
        if calculation_method:
            m = str(calculation_method).strip().lower()
            if m in ('fixed', 'variable'):
                payload['calculation_method'] = m
        if active_variable_config:
            payload['active_variable_config'] = str(active_variable_config).strip() or 'default'
        if payroll_year_start_month is not None:
            try:
                m = int(payroll_year_start_month)
                if 1 <= m <= 12:
                    payload['payroll_year_start_month'] = m
            except Exception:
                pass

        if not payload:
            return True

        # Ensure there's at least one row; use id=1 convention
        try:
            existing = supabase.table('payroll_settings').select('id').limit(1).execute()
            exists = bool(existing and existing.data)
        except Exception:
            exists = False

        if exists:
            res = supabase.table('payroll_settings').update(payload).neq('id', None).execute()
        else:
            base = {'id': 1, 'calculation_method': 'fixed', 'active_variable_config': 'default', 'payroll_year_start_month': 1}
            base.update(payload)
            res = supabase.table('payroll_settings').insert(base).execute()

        # Also persist locally for resilience across restarts even if DB write fails later
        try:
            from services.local_settings_cache import save_cached_payroll_settings
            # Merge with current to ensure both keys present
            current = get_payroll_settings()
            merged = dict(current)
            merged.update(payload)
            save_cached_payroll_settings(merged)
        except Exception:
            pass

        return True if res is not None else False
    except Exception as e:
        print(f"DEBUG: update_payroll_settings failed: {e}")
        # Best-effort: still cache locally so UI can reflect choice on next launch
        try:
            from services.local_settings_cache import save_cached_payroll_settings
            base = {'calculation_method': 'fixed', 'active_variable_config': 'default', 'payroll_year_start_month': 1}
            if calculation_method in ('fixed', 'variable'):
                base['calculation_method'] = calculation_method
            if active_variable_config:
                base['active_variable_config'] = str(active_variable_config).strip() or 'default'
            if payroll_year_start_month is not None:
                try:
                    m = int(payroll_year_start_month)
                    if 1 <= m <= 12:
                        base['payroll_year_start_month'] = m
                except Exception:
                    pass
            save_cached_payroll_settings(base)
        except Exception:
            pass
        return False

# ----------------------------
# Payroll YTD baseline helpers
# ----------------------------

def set_ytd_baseline(employee_email: str, year: int, month: int, accumulators: Dict[str, float]) -> bool:
    """Create or update a YTD baseline snapshot in payroll_ytd_accumulated for a given employee and (year, month).

    This is useful when starting payroll mid-year (e.g., start in Nov): seed the previous month (Oct)
    with accumulated values from Jan..Oct so PCB for Nov reflects the correct YTD context.
    """
    try:
        assert employee_email and isinstance(year, int) and isinstance(month, int)
        if not (1 <= month <= 12):
            raise ValueError('month must be 1..12')
        # Normalize payload to known column names
        cols_map = {
            'accumulated_gross_salary_ytd': 'accumulated_gross_salary_ytd',
            'accumulated_epf_employee_ytd': 'accumulated_epf_employee_ytd',
            'accumulated_pcb_ytd': 'accumulated_pcb_ytd',
            'accumulated_zakat_ytd': 'accumulated_zakat_ytd',
            'accumulated_tax_reliefs_ytd': 'accumulated_tax_reliefs_ytd',
            'accumulated_socso_employee_ytd': 'accumulated_socso_employee_ytd',
            'accumulated_eis_employee_ytd': 'accumulated_eis_employee_ytd',
        }
        payload = {'employee_email': employee_email.lower(), 'year': year, 'month': month}
        for k_in, k_out in cols_map.items():
            v = accumulators.get(k_in)
            if v is not None:
                try:
                    payload[k_out] = float(v)
                except Exception:
                    continue
        # Upsert on (employee_email, year, month)
        exists = supabase.table('payroll_ytd_accumulated').select('id').eq('employee_email', payload['employee_email']).eq('year', year).eq('month', month).limit(1).execute()
        if exists and getattr(exists, 'data', None):
            row_id = exists.data[0].get('id')
            res = supabase.table('payroll_ytd_accumulated').update({k: v for k, v in payload.items() if k not in ('employee_email', 'year', 'month')}).eq('id', row_id).execute()
            return bool(res)
        else:
            res = supabase.table('payroll_ytd_accumulated').insert(payload).execute()
            return bool(res)
    except Exception as e:
        print(f"DEBUG: set_ytd_baseline failed: {e}")
        return False


def get_current_calculation_method() -> str:
    """Convenience accessor returning 'fixed' or 'variable'."""
    try:
        s = get_payroll_settings()
        return s.get('calculation_method', 'fixed')
    except Exception:
        return 'fixed'

def record_clock_in(email: str) -> bool:
    try:
        today = datetime.now(pytz.UTC).strftime("%Y-%m-%d")
        existing = supabase.table("attendance").select("*").eq("email", email.lower()).eq("date", today).execute()
        if existing.data:
            print(f"DEBUG: Clock-in already recorded for {email} on {today}")
            return False
        data = {
            "email": email.lower(),
            "date": today,
            "clock_in": datetime.now(pytz.UTC).strftime("%H:%M:%S"),
            "created_at": datetime.now(pytz.UTC).isoformat()
        }
        result = supabase.table("attendance").insert(data).execute()
        print(f"DEBUG: Clock-in recorded for {email} at {data['clock_in']}")
        return len(result.data) > 0
    except Exception as e:
        print(f"DEBUG: Error recording clock-in: {str(e)}")
        return False

def record_clock_out(email: str) -> bool:
    try:
        today = datetime.now(pytz.UTC).strftime("%Y-%m-%d")
        existing = supabase.table("attendance").select("*").eq("email", email.lower()).eq("date", today).execute()
        if not existing.data:
            print(f"DEBUG: No clock-in record found for {email} on {today}")
            return False
        if existing.data[0].get("clock_out"):
            print(f"DEBUG: Clock-out already recorded for {email} on {today}")
            return False
        data = {
            "clock_out": datetime.now(pytz.UTC).strftime("%H:%M:%S")
        }
        result = supabase.table("attendance").update(data).eq("email", email.lower()).eq("date", today).execute()
        print(f"DEBUG: Clock-out recorded for {email} at {data['clock_out']}")
        return len(result.data) > 0
    except Exception as e:
        print(f"DEBUG: Error recording clock-out: {str(e)}")
        return False

def get_attendance_history(email: str) -> list:
    try:
        result = supabase.table("attendance").select("*").ilike("email", email.lower()).order("date", desc=True).execute()
        print(f"DEBUG: Fetched attendance history for {email}: {len(result.data)} records")
        return result.data
    except Exception as e:
        print(f"DEBUG: Error fetching attendance history: {str(e)}")
        return []
    
def add_employee_with_login(employee_data, password: str, role="employee"):
    try:
        # Ensure timestamps and normalize optional fields before insert
        try:
            employee_data = dict(employee_data)
        except Exception:
            employee_data = employee_data or {}
        employee_data.setdefault("created_at", datetime.now(pytz.UTC).isoformat())
        employee_data.setdefault("updated_at", datetime.now(pytz.UTC).isoformat())

        # Never try to insert auth-only fields into employees (they don't exist on that table)
        for bad_key in ("username", "password", "role"):
            if bad_key in employee_data:
                employee_data.pop(bad_key, None)

        # Normalize empty strings for optional fields
        for _k in ("work_status", "payroll_status", "functional_group", "position"):
            if _k in employee_data and employee_data[_k] == "":
                employee_data[_k] = None

        # Resilient insert into employees: strip unknown columns if PostgREST complains
        import re as _re
        payload = dict(employee_data)
        attempts = 0
        max_attempts = max(3, len(payload) + 1)
        employee_result = None
        while attempts < max_attempts:
            attempts += 1
            try:
                employee_result = supabase.table("employees").insert(payload).execute()
                break
            except Exception as ie:
                msg = str(ie)
                m = _re.search(r"Could find the '([^']+)' column|Could not find the '([^']+)' column", msg)
                if not m:
                    m2 = _re.search(r"'([^']+)' column of 'employees' in the schema cache", msg)
                    missing = m2.group(1) if m2 else None
                else:
                    missing = m.group(1) or m.group(2)
                if missing and missing in payload:
                    # Drop the unknown field and retry
                    payload.pop(missing, None)
                    continue
                # Not recoverable
                raise ie

        if not employee_result or not getattr(employee_result, 'data', None):
            # Best-effort read-back if API returned 204/no content
            try:
                probe = supabase.table("employees").select("id").eq("employee_id", employee_data.get("employee_id")).limit(1).execute()
                if probe and getattr(probe, 'data', None):
                    inserted_emp_id = probe.data[0].get('id')
                else:
                    print(f"DEBUG: Failed to insert employee: {getattr(employee_result, 'error', None)}")
                    return {"success": False, "error": "Failed to create employee record"}
            except Exception:
                print(f"DEBUG: Failed to insert employee: {getattr(employee_result, 'error', None)}")
                return {"success": False, "error": "Failed to create employee record"}
        else:
            inserted_emp_id = employee_result.data[0].get('id')

        # Insert into user_logins table
        # Ensure password provided; if not, generate a random fallback (never store None)
        import secrets, string
        if not password:
            # 12-char random alphanumeric + punctuation minus quotes/spaces
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*_-"
            password = ''.join(secrets.choice(alphabet) for _ in range(12))
            print("DEBUG: Generated fallback password for employee (was None/empty)")
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        username = (employee_data.get("username") or "").strip().lower()
        # Derive username from email if not provided
        email_val = (employee_data.get("email") or "").strip().lower()
        login_data = {
            "email": email_val,
            "username": username or (email_val.split('@')[0] if email_val else None),
            "password": hashed_password,
            "role": role,
            "created_at": datetime.now(pytz.UTC).isoformat()
        }
        # Strip None username to satisfy NOT NULL only if migration enforced it
        if not login_data["username"]:
            login_data.pop("username", None)

        login_result = supabase.table("user_logins").insert(login_data).execute()
        if not login_result or not getattr(login_result, 'data', None):
            print(f"DEBUG: Failed to insert user login: {getattr(login_result, 'error', None)}")
            # Rollback employee insertion
            try:
                supabase.table("employees").delete().eq("id", inserted_emp_id).execute()
            except Exception:
                pass
            return {"success": False, "error": "Failed to create user login"}

        print(f"DEBUG: Employee and login inserted successfully for employee_id: {employee_data.get('employee_id')}")
        return {"success": True, "employee_id": inserted_emp_id}
    except Exception as e:
        print(f"DEBUG: Error adding employee with login: {str(e)}")
        # Rollback employee insertion in case of an exception
        try:
            # Prefer rollback by UUID if available
            if 'inserted_emp_id' in locals() and inserted_emp_id:
                supabase.table("employees").delete().eq("id", inserted_emp_id).execute()
            elif "employee_id" in employee_data:
                supabase.table("employees").delete().eq("employee_id", employee_data["employee_id"]).execute()
        except Exception:
            pass
        return {"success": False, "error": str(e)}

def delete_employee(employee_id: str) -> dict:
    try:
        # Fetch employee to get email
        response = supabase.table("employees").select("email").eq("employee_id", employee_id).execute()
        if not response.data:
            print(f"DEBUG: No employee found for employee_id: {employee_id}")
            return {"success": False, "error": "Employee not found"}
        
        email = response.data[0]["email"]
        
        # Delete from employees table
        emp_response = supabase.table("employees").delete().eq("employee_id", employee_id).execute()
        if not emp_response.data:
            print(f"DEBUG: Failed to delete employee: {employee_id}")
            return {"success": False, "error": "Failed to delete employee"}
        
        # Delete from user_logins table
        login_response = supabase.table("user_logins").delete().eq("email", email.lower()).execute()
        print(f"DEBUG: Deleted user login for email: {email.lower()}")
        
        # Delete profile picture if exists
        photo_response = supabase.table("employees").select("photo_url").eq("employee_id", employee_id).execute()
        if photo_response.data and photo_response.data[0].get("photo_url"):
            photo_url = photo_response.data[0]["photo_url"]
            if not photo_url.endswith("default_avatar.png"):
                try:
                    photo_path = photo_url.replace(f"https://{url.split('//')[1]}/storage/v1/object/public/employees.doc/", "")
                    supabase.storage.from_("employees.doc").remove([photo_path])
                    print(f"DEBUG: Deleted profile picture: {photo_path}")
                except Exception as e:
                    print(f"DEBUG: Non-critical error deleting profile picture: {str(e)}")
        
        print(f"DEBUG: Employee deleted with employee_id: {employee_id}")
        return {"success": True, "error": None}
    except Exception as e:
        print(f"DEBUG: Error deleting employee: {str(e)}")
        return {"success": False, "error": str(e)}

def convert_utc_to_kl(utc_timestamp):
    if not utc_timestamp or utc_timestamp == "-":
        return utc_timestamp
    try:
        # If only time is given (e.g., "12:34:56"), combine with today's date
        if len(utc_timestamp) <= 8:
            t = datetime.strptime(utc_timestamp, "%H:%M:%S").time()
            # Use today's date with the time, assume UTC
            dt = datetime.combine(date.today(), t)
            dt = pytz.UTC.localize(dt)
        else:
            dt = datetime.fromisoformat(utc_timestamp.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt)   # ensure it's aware
        # Convert to Malaysia time
        dt_kl = dt.astimezone(KL_TZ)
        # Return formatted string to avoid strftime errors later
        return dt_kl.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"DEBUG: Error converting timestamp {utc_timestamp}: {str(e)}")
        return utc_timestamp

def fetch_employee_data(email: str) -> dict:
    try:
        response = supabase.table("employees").select("*").eq("email", email.lower()).execute()
        if not response.data:
            print(f"DEBUG: No employee found for email: {email.lower()}")
            return {}
        employee_data = response.data[0]
        # Convert timestamp fields to Asia/Kuala_Lumpur
        timestamp_fields = ["created_at", "updated_at"]
        for field in timestamp_fields:
            if field in employee_data and employee_data[field]:
                employee_data[field] = convert_utc_to_kl(employee_data[field])
        print(f"DEBUG: Fetched employee data for email: {email.lower()}")
        return employee_data
    except Exception as e:
        print(f"DEBUG: Error fetching employee data: {str(e)}")
        return {}

def update_user_role(email: str, role: str) -> dict:
    try:
        response = supabase.table("user_logins").update({"role": role}).eq("email", email.lower()).execute()
        if response.data:
            print(f"DEBUG: Role updated for {email} to {role}")
            return {"success": True}
        else:
            print(f"DEBUG: Failed to update role for {email}")
            return {"success": False, "error": "Failed to update role"}
    except Exception as e:
        print(f"DEBUG: Error updating role for {email}: {str(e)}")
        return {"success": False, "error": str(e)}

def update_user_login_credentials(email: str, username: Optional[str] = None, password: Optional[str] = None, role: Optional[str] = None) -> dict:
    """Update user_logins for a given email. Any of username/password/role may be provided.

    - Ensures username uniqueness across other accounts.
    - Hashes password if provided.
    - Returns {success: bool, error?: str}
    """
    try:
        update_data: Dict[str, Any] = {}
        email_l = (email or '').strip().lower()
        if not email_l:
            return {"success": False, "error": "Email required for login update"}

        if username is not None:
            uname = (username or '').strip().lower()
            if uname:
                # Check duplicate username owned by different email
                try:
                    chk = supabase.table('user_logins').select('email').eq('username', uname).limit(1).execute()
                    if chk and getattr(chk, 'data', None):
                        owner_email = (chk.data[0].get('email') or '').lower()
                        if owner_email and owner_email != email_l:
                            return {"success": False, "error": "Username already in use"}
                except Exception:
                    pass
                update_data['username'] = uname
        if password is not None:
            pw = (password or '').strip()
            if pw:
                hashed = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                update_data['password'] = hashed
        if role is not None:
            update_data['role'] = role

        if not update_data:
            return {"success": True}

        update_data['updated_at'] = datetime.now(pytz.UTC).isoformat()
        resp = supabase.table('user_logins').update(update_data).eq('email', email_l).execute()
        # Some PostgREST clients return no body; verify with a read
        if not resp or not getattr(resp, 'data', None):
            try:
                probe = supabase.table('user_logins').select('email').eq('email', email_l).limit(1).execute()
                if probe and getattr(probe, 'data', None):
                    return {"success": True}
            except Exception:
                pass
        return {"success": True} if resp and getattr(resp, 'data', None) else {"success": False, "error": "Failed to update user_logins"}
    except Exception as e:
        print(f"DEBUG: Error updating user login credentials: {e}")
        return {"success": False, "error": str(e)}

def fetch_user_role(email: str) -> str:
    try:
        response = supabase.table("user_logins").select("role").eq("email", email.lower()).execute()
        if response.data:
            return response.data[0].get("role", "employee")
        else:
            print(f"DEBUG: No role found for {email}")
            return "employee"
    except Exception as e:
        print(f"DEBUG: Error fetching role for {email}: {str(e)}")
        return "employee"
    
def calculate_pcb(gross_salary: float, epf_employee: float, relief: float) -> float:
    """
    Legacy PCB calculation function - now uses official LHDN formula
    This function is maintained for backward compatibility
    """
    try:
        # Prepare data for official LHDN calculation
        payroll_inputs = {
            'accumulated_gross_ytd': 0.0,
            'accumulated_epf_ytd': 0.0,
            'accumulated_pcb_ytd': 0.0,
            'accumulated_zakat_ytd': 0.0,
            'individual_relief': relief if relief > 0 else 9000.0,
            'spouse_relief': 0.0,
            'child_relief': 2000.0,
            'child_count': 0,
            'disabled_individual': 0.0,
            'disabled_spouse': 0.0,
            'other_reliefs_ytd': 0.0,
            'other_reliefs_current': 0.0,
            'current_month_zakat': 0.0
        }
        
        # Get current tax configuration
        tax_config = load_tax_rates_configuration() or get_default_tax_rates_config()
        
        # Use current month/year
        current_date = datetime.now(KL_TZ)
        month_year = f"{current_date.month:02d}/{current_date.year}"
        
        # Calculate using official LHDN formula
        return calculate_lhdn_pcb_official(
            payroll_inputs,
            gross_salary,
            epf_employee,
            tax_config,
            month_year
        )
        
    except Exception as e:
        print(f"DEBUG: Error in legacy PCB calculation, using fallback: {str(e)}")
        # Fallback to simplified calculation if official formula fails
        taxable_income = gross_salary - epf_employee - relief
        if taxable_income <= 0:
            return 0
        if taxable_income <= 5000:
            return taxable_income * 0.01
        elif taxable_income <= 20000:
            return (taxable_income - 5000) * 0.03 + 50
        elif taxable_income <= 35000:
            return (taxable_income - 20000) * 0.08 + 500
        else:
            return (taxable_income - 35000) * 0.13 + 1700

def generate_payslip_pdf(employee: Dict, payroll_data: Dict, payroll_date: str) -> bytes:
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("Payslip", styles['Title']))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"Employee: {employee['full_name']}", styles['Normal']))
        elements.append(Paragraph(f"Employee ID: {employee['employee_id']}", styles['Normal']))
        elements.append(Paragraph(f"Payroll Date: {payroll_date}", styles['Normal']))
        elements.append(Spacer(1, 0.5*cm))

        data = [
            ["Description", "Amount (RM)"],
            ["Basic Salary", f"{employee['basic_salary']:.2f}"],
        ]
        for allowance_type, amount in payroll_data.get("allowances", {}).items():
            data.append([allowance_type.replace("_", " ").title(), f"{amount:.2f}"])
        
        # Add unpaid leave deduction if present (Malaysian standard)
        unpaid_days = payroll_data.get("unpaid_days", 0)
        unpaid_deduction = payroll_data.get("unpaid_leave_deduction", 0)
        if unpaid_days > 0 and unpaid_deduction > 0:
            data.append([f"Unpaid Leave ({unpaid_days} days)", f"-{unpaid_deduction:.2f}"])
        
        data.extend([
            ["Gross Salary", f"{payroll_data['gross_salary']:.2f}"],
            ["EPF Employee", f"{payroll_data['epf_employee']:.2f}"],
            ["EPF Employer", f"{payroll_data['epf_employer']:.2f}"],
            ["SOCSO Employee", f"{payroll_data['socso_employee']:.2f}"],
            ["SOCSO Employer", f"{payroll_data['socso_employer']:.2f}"],
            ["EIS Employee", f"{payroll_data['eis_employee']:.2f}"],
            ["EIS Employer", f"{payroll_data['eis_employer']:.2f}"],
            ["PCB", f"{payroll_data['pcb']:.2f}"],
            ["Net Salary", f"{payroll_data['net_salary']:.2f}"]
        ])

        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)

        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()
        print(f"DEBUG: Payslip PDF generated for {employee['employee_id']}")
        return pdf_data
    except Exception as e:
        print(f"DEBUG: Error generating payslip PDF: {str(e)}")
        return b""

def upload_and_parse_contribution_file(file_path: str, source_type: str, category: str) -> bool:
    try:
        ext = os.path.splitext(file_path)[1].lower()
        data_to_insert = []
        
        # Special handling for EIS files
        if source_type.lower() == "eis" and ext in [".xlsx", ".xls"]:
            print("DEBUG: Processing EIS Excel file")
            from services.eis_excel_parser import parse_eis_excel
            eis_data = parse_eis_excel(file_path)
            
            if not eis_data:
                print("DEBUG: No EIS data extracted from file")
                return False
                
            # Delete existing EIS records
            supabase.table("contribution_tables").delete().eq("contrib_type", "eis").execute()
            
            # Insert new EIS records
            response = supabase.table("contribution_tables").insert(eis_data).execute()
            
            if response.data:
                print(f"DEBUG: Successfully uploaded {len(eis_data)} EIS records to database")
                return True
            else:
                print("DEBUG: Failed to upload EIS data to database")
                return False
        
        # Original handling for other contribution types
        if ext in [".csv"]:
            df = pd.read_csv(file_path)
            df.columns = [
                c.strip().lower()
                 .replace(" ", "_")
                 .replace("(", "")
                 .replace(")", "")
                 .replace("'", "")
                 .replace(",", "")
                for c in df.columns
            ]
            expected_cols = ["actual_monthly_wage_rm", "employers_contribution_first_category_rm",
                             "employees_contribution_first_category_rm", "total_contribution_first_category_rm",
                             "contribution_by_employer_only_second_category_rm"]
            for col in expected_cols:
                if col not in df.columns:
                    print(f"DEBUG: Missing expected column {col} in file {file_path}")
                    return False
            for _, row in df.iterrows():
                wage_range = str(row["actual_monthly_wage_rm"])
                # Handle "and above"
                if "and above" in wage_range:
                    wage_min = float(wage_range.split()[0])
                    wage_max = float('inf')
                else:
                    wage_min, wage_max = map(float, wage_range.replace('RM', '').replace('–', '-').split('-'))
                data = {
                    'contrib_type': source_type,  # Changed from source_type to contrib_type
                    'category': category,
                    'from_wage': wage_min,
                    'to_wage': wage_max,
                    'employee_contribution': float(row['employees_contribution_first_category_rm']),
                    'employer_contribution': float(row['employers_contribution_first_category_rm']),
                    'total_contribution': float(row['total_contribution_first_category_rm']),
                    'employer_only_contribution': float(row['contribution_by_employer_only_second_category_rm']),
                    'created_at': datetime.now(KL_TZ).isoformat(),
                    'updated_at': datetime.now(KL_TZ).isoformat()
                }
                data_to_insert.append(data)
        elif ext in [".xlsx", ".xls"]:
            contrib_data = parse_contribution_xlsx(file_path)
            for row in contrib_data:
                row['contrib_type'] = source_type   # <-- This is critical!
                row['category'] = category
                row['created_at'] = datetime.now(KL_TZ).isoformat()
                row['updated_at'] = datetime.now(KL_TZ).isoformat()
                row['from_wage'] = row['wage_min']   # <-- add this
                row['to_wage'] = row['wage_max']     # <-- add this
                # Optionally: del row['source_type'] if it exists
            data_to_insert = contrib_data
        else:
            print(f"DEBUG: Unsupported file type for {file_path}")
            return False

        # Use contrib_type instead of source_type for database operations
        supabase.table("contribution_tables").delete().eq("contrib_type", source_type).eq("category", category).execute()
        response = supabase.table("contribution_tables").insert(data_to_insert).execute()
        print(f"DEBUG: Successfully stored {len(data_to_insert)} rows for {source_type}, category {category}")
        return bool(response.data)
    except Exception as e:
        print(f"DEBUG: Error parsing/uploading contribution file {file_path}: {str(e)}")
        return False

def update_contribution_table(data: List[Dict], contrib_type: str) -> bool:
    try:
        supabase.table("contribution_tables").delete().eq("contrib_type", contrib_type).execute()
        for row in data:
            row["contrib_type"] = contrib_type
            row["created_at"] = datetime.now(KL_TZ).isoformat()
            # Ensure category is set, default to "default" if not provided
            if "category" not in row or row["category"] is None:
                row["category"] = "default"
        response = supabase.table("contribution_tables").insert(data).execute()
        print(f"DEBUG: Updated {contrib_type} contribution table with {len(data)} rows")
        return True if response.data else False
    except Exception as e:
        print(f"DEBUG: Error updating contribution table: {str(e)}")
        return False

def parse_contribution_xlsx(file_path):
    df = pd.read_excel(file_path)
    # Improved normalization: remove spaces, parentheses, apostrophes, commas
    df.columns = [
        c.strip().lower()
         .replace(" ", "_")
         .replace("(", "")
         .replace(")", "")
         .replace("'", "")
         .replace(",", "")
        for c in df.columns
    ]
    column_map = {
        "wage_range": ["actual_monthly_wage_rm", "wage_range"],
        "employer_contribution": ["employers_contribution_first_category_rm"],
        "employee_contribution": ["employees_contribution_first_category_rm"],
        "total_contribution": ["total_contribution_first_category_rm"],
        "employer_only_contribution": ["contribution_by_employer_only_second_category_rm"],
    }
    def find_column(possible_names):
        for name in possible_names:
            if name in df.columns:
                return name
        raise ValueError(f"Missing expected column. Tried: {possible_names}")
    wage_col = find_column(column_map["wage_range"])
    employer_col = find_column(column_map["employer_contribution"])
    employee_col = find_column(column_map["employee_contribution"])
    total_col = find_column(column_map["total_contribution"])
    employer_only_col = find_column(column_map["employer_only_contribution"])
    contrib_data = []
    for _, row in df.iterrows():
        wage_range = str(row[wage_col])
        if "and above" in wage_range:
            wage_min = float(wage_range.split()[0])
            wage_max = 999999.99  # or any suitably large value
        else:
            wage_min, wage_max = map(float, wage_range.replace('RM', '').replace('–', '-').split('-'))
        contrib_data.append({
            'wage_min': wage_min,
            'wage_max': wage_max,
            'employer_contribution': float(row[employer_col]),
            'employee_contribution': float(row[employee_col]),
            'total_contribution': float(row[total_col]),
            'employer_only_contribution': float(row[employer_only_col])
        })
    return contrib_data

def calculate_age(dob: str) -> int:
    try:
        dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
        today = datetime.now(KL_TZ).date()
        age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
        return age
    except Exception as e:
        print(f"DEBUG: Error calculating age: {str(e)}")
        return 0

def determine_epf_part(
    age: int,
    nationality: str,
    citizenship: str,
    is_intern: bool,
    is_electing: bool = False,
    election_date: Optional[str] = None
) -> Optional[str]:
    """
    Determine EPF contribution part based on official EPF schedule.
    
    Part A: Employees < 60 years - Malaysian citizens, PRs, Non-citizens elected before 1 Aug 1998
    Part B: Employees < 60 years - Non-citizens elected on/after 1 Aug 1998
    Part C: Employees ≥ 60 years - PRs, Non-citizens elected before 1 Aug 1998  
    Part D: Employees ≥ 60 years - Non-citizens elected on/after 1 Aug 1998
    Part E: Malaysian citizens ≥ 60 years
    """
    if is_intern:
        return None

    is_malaysian = nationality.lower() in ["malaysia", "malaysian"] and citizenship.lower() == "citizen"
    is_pr = citizenship.lower() == "permanent resident"
    is_non_citizen = citizenship.lower() == "non-citizen"

    # Determine election timing if available
    elected_pre_1998 = False
    if is_electing and election_date:
        try:
            cutoff_date = datetime(1998, 8, 1)
            election_dt = datetime.strptime(election_date, "%Y-%m-%d")
            elected_pre_1998 = election_dt < cutoff_date
        except Exception:
            # If election_date parsing fails, assume post-1998 for safety
            elected_pre_1998 = False
    
    # Apply EPF schedule logic
    if age < 60:  # Under 60 years
        if is_malaysian:  # (a) Malaysian citizens
            return "part_a"
        elif is_pr:  # (b) Non-Malaysian citizens who are permanent residents
            return "part_a"
        elif is_non_citizen and is_electing:
            # (c) Non-Malaysian citizens who elected to contribute
            if election_date and elected_pre_1998:
                return "part_a"  # Elected before 1 Aug 1998
            else:
                return "part_b"  # Elected on/after 1 Aug 1998 (or no date = assume post-1998)
        else:
            # Non-citizens who don't elect = no EPF
            return None
    else:  # 60 years and above
        if is_malaysian:
            return "part_e"  # Malaysian citizens ≥ 60 years
        elif is_pr:
            return "part_c"  # (b) Non-Malaysian citizens but permanent residents
        elif is_non_citizen and is_electing:
            # (c) Non-Malaysian citizens who elected to contribute
            if election_date and elected_pre_1998:
                return "part_c"  # Elected before 1 Aug 1998
            else:
                return "part_d"  # Elected on/after 1 Aug 1998 (or no date = assume post-1998)
        else:
            # Non-citizens who don't elect = no EPF
            return None
    
    return None

import math

def calculate_epf_over_20k(wage, part):
    if part == "part_a":
        emp = math.ceil(wage * 0.11)
        employer = math.ceil(wage * 0.12)
    elif part == "part_b":
        emp = math.ceil(wage * 0.11)
        employer = 5.00
    elif part == "part_c":
        emp = math.ceil(wage * 0.055)
        employer = math.ceil(wage * 0.06)
    elif part == "part_d":
        emp = math.ceil(wage * 0.055)
        employer = 5.00
    elif part == "part_e":
        emp = 0.00
        employer = math.ceil(wage * 0.04)
    else:
        emp = 0.0
        employer = 0.0
    return emp, employer

def calculate_epf_with_bonus(
    basic_salary: float,
    bonus_amount: float,
    part: str
) -> tuple[float, float]:
    """
    Calculate EPF contributions when bonus is included, applying special bonus rules.
    
    Special Bonus Rules (EPF Official Schedule):
    - Part A: If basic ≤ RM 5,000 and (basic + bonus) > RM 5,000 → Employer 13% of total
    - Part C: If basic ≤ RM 5,000 and (basic + bonus) > RM 5,000 → Employer 6.5% of total
    
    Args:
        basic_salary: Employee's basic monthly salary
        bonus_amount: Bonus amount for the month
        part: EPF part (part_a, part_b, part_c, part_d, part_e)
        
    Returns:
        tuple: (employee_contribution, employer_contribution)
    """
    total_wages = basic_salary + bonus_amount
    
    # Check if special bonus rules apply
    bonus_rule_applies = (
        basic_salary <= 5000.0 and
        total_wages > 5000.0 and
        part in ["part_a", "part_c"]
    )

    if bonus_rule_applies:
        # Attempt to read configured percentages from variable percentage config
        try:
            cfg = get_variable_percentage_config("default") or {}
        except Exception:
            cfg = {}

        # Helper to resolve rates with sensible fallbacks
        def _get_rate(keys, default):
            for k in keys:
                if k in cfg and cfg.get(k) is not None:
                    try:
                        return float(cfg.get(k))
                    except Exception:
                        continue
            return float(default)

        if part == "part_a":
            # Resolve employee and employer rates: prefer explicit Part A fields then stage defaults
            emp_rate = _get_rate(['epf_part_a_employee', 'epf_employee_rate_stage1'], 11.0)
            employer_rate = _get_rate(['epf_part_a_employer_bonus', 'epf_employer_rate_stage1'], 13.0)

        elif part == "part_c":
            emp_rate = _get_rate(['epf_part_c_employee', 'epf_employee_rate_stage2'], 5.5)
            employer_rate = _get_rate(['epf_part_c_employer_bonus', 'epf_employer_rate_stage2'], 6.5)

        else:
            return 0.0, 0.0

        # Apply configured rates to total wages
        emp = math.ceil(total_wages * (emp_rate / 100.0))
        employer = math.ceil(total_wages * (employer_rate / 100.0))
        return emp, employer

    # No special bonus rules apply, calculate normally
    return get_epf_contributions_for_wage(
        total_wages, part
    )

def get_epf_contributions_for_wage(wage: float, part: str) -> tuple[float, float]:
    """
    Calculate EPF contributions for a given wage and part, without bonus considerations.
    
    Args:
        wage: Total wage amount
        part: EPF part (part_a, part_b, part_c, part_d, part_e)
        
    Returns:
        tuple: (employee_contribution, employer_contribution)
    """
    if wage > 20000:
        return calculate_epf_over_20k(wage, part)

    # Use banded table lookup for wages ≤ RM 20,000
    query = supabase.table("contribution_tables") \
        .select("employee_contribution, employer_contribution, from_wage, to_wage") \
        .eq("contrib_type", "epf") \
        .eq("category", part) \
        .lte("from_wage", wage) \
        .gte("to_wage", wage) \
        .limit(1).execute()
        
    if query.data:
        contributions = query.data[0]
        return float(contributions["employee_contribution"]), float(contributions["employer_contribution"])
    else:
        # If no exact match, use highest band
        max_band = supabase.table("contribution_tables") \
            .select("employee_contribution, employer_contribution, from_wage, to_wage") \
            .eq("contrib_type", "epf") \
            .eq("category", part) \
            .order("to_wage", desc=True) \
            .limit(1).execute()
        if max_band.data:
            row = max_band.data[0]
            return float(row["employee_contribution"]), float(row["employer_contribution"])
        else:
            return 0.0, 0.0

def get_epf_contributions(
    wage: float,
    date_of_birth: str,
    nationality: str,
    is_intern: bool,
    citizenship: str,
    is_electing: bool = False,
    election_date: Optional[str] = None,
    basic_salary: Optional[float] = None,
    bonus_amount: Optional[float] = None
) -> tuple[float, float]:
    """
    Calculate EPF contributions with optional bonus handling.
    
    Args:
        wage: Total wage (basic + bonus if applicable)
        date_of_birth: Employee's date of birth (YYYY-MM-DD)
        nationality: Employee's nationality
        is_intern: Whether employee is an intern
        citizenship: Employee's citizenship status
        is_electing: Whether employee elected to contribute
        election_date: Date of EPF election (YYYY-MM-DD)
        basic_salary: Basic salary (required for bonus calculations)
        bonus_amount: Bonus amount (triggers special bonus rules)
        
    Returns:
        tuple: (employee_contribution, employer_contribution)
    """
    age = calculate_age(date_of_birth)
    part = determine_epf_part(
        age, nationality, citizenship, is_intern, is_electing, election_date
    )
    if not part:
        return 0.0, 0.0

    # If bonus is provided, use bonus calculation logic
    if bonus_amount is not None and bonus_amount > 0 and basic_salary is not None:
        return calculate_epf_with_bonus(basic_salary, bonus_amount, part)
    
    # Otherwise use standard calculation
    return get_epf_contributions_for_wage(wage, part)

def get_epf_contributions_standard(
    wage: float,
    date_of_birth: str,
    nationality: str,
    is_intern: bool,
    citizenship: str,
    is_electing: bool = False,
    election_date: Optional[str] = None
) -> tuple[float, float]:
    """
    Calculate standard EPF contributions without bonus considerations.
    This function maintains backward compatibility.
    """
    return get_epf_contributions(
        wage, date_of_birth, nationality, is_intern, citizenship, 
        is_electing, election_date
    )
    
def get_socso_contribution(wage, category="default"):
    """
    Returns (employee_contribution, employer_contribution, total_contribution) for a given wage.
    If wage exceeds the highest SOCSO band, the capped (max band) value is returned.
    Never raises; always returns floats (can be 0.0 if table is empty).
    """
    # Try to find the exact matching band
    response = supabase.table("contribution_tables") \
        .select("employee_contribution, employer_contribution, total_contribution, from_wage, to_wage") \
        .eq("contrib_type", "socso") \
        .eq("category", category) \
        .lte("from_wage", wage) \
        .gte("to_wage", wage) \
        .limit(1) \
        .execute()
    if response.data:
        row = response.data[0]
        return float(row["employee_contribution"]), float(row["employer_contribution"]), float(row["total_contribution"])
    else:
        # If out of range (wage > max), cap at the max band
        max_band = supabase.table("contribution_tables") \
            .select("employee_contribution, employer_contribution, total_contribution, from_wage, to_wage") \
            .eq("contrib_type", "socso") \
            .eq("category", category) \
            .order("to_wage", desc=True) \
            .limit(1) \
            .execute()
        if max_band.data:
            row = max_band.data[0]
            return float(row["employee_contribution"]), float(row["employer_contribution"]), float(row["total_contribution"])
        else:
            # Fallback: SOCSO table is empty or misconfigured
            return 0.0, 0.0, 0.0
        
def get_eis_contributions(wage: float, category: str = "eis") -> tuple[float, float, float]:
    """
    Get EIS contributions from contribution_tables for a given wage.
    Returns (employee_contribution, employer_contribution, total_contribution)
    """
    try:
        # Find the matching wage band in contribution_tables
        response = supabase.table("contribution_tables") \
            .select("employee_contribution, employer_contribution, total_contribution, from_wage, to_wage") \
            .eq("contrib_type", "eis") \
            .eq("category", category) \
            .lte("from_wage", wage) \
            .gte("to_wage", wage) \
            .limit(1) \
            .execute()
        
        if response.data:
            row = response.data[0]
            employee_contrib = float(row["employee_contribution"])
            employer_contrib = float(row["employer_contribution"])
            total_contrib = float(row["total_contribution"])
            print(f"DEBUG: EIS calculation for wage {wage}: Employee={employee_contrib}, Employer={employer_contrib}, Total={total_contrib}")
            return employee_contrib, employer_contrib, total_contrib
        else:
            # If wage is above the highest band, use the maximum band rate
            max_band = supabase.table("contribution_tables") \
                .select("employee_contribution, employer_contribution, total_contribution, from_wage, to_wage") \
                .eq("contrib_type", "eis") \
                .eq("category", category) \
                .order("to_wage", desc=True) \
                .limit(1) \
                .execute()
            
            if max_band.data:
                row = max_band.data[0]
                employee_contrib = float(row["employee_contribution"])
                employer_contrib = float(row["employer_contribution"])
                total_contrib = float(row["total_contribution"])
                print(f"DEBUG: EIS calculation (max band) for wage {wage}: Employee={employee_contrib}, Employer={employer_contrib}, Total={total_contrib}")
                return employee_contrib, employer_contrib, total_contrib
            else:
                print(f"DEBUG: No EIS data found for wage {wage}, category {category}")
                return 0.0, 0.0, 0.0
                
    except Exception as e:
        print(f"DEBUG: Error calculating EIS contributions: {str(e)}")
        return 0.0, 0.0, 0.0

def get_epf_contributions_from_table(wage: float, category: str) -> tuple[float, float, float]:
    """
    Get EPF contributions from contribution_tables for a given wage and category.
    Returns (employee_contribution, employer_contribution, total_contribution)
    
    Args:
        wage: The wage amount to calculate contributions for
        category: EPF part category (part_a, part_b, part_c, part_d, part_e)
    """
    try:
        print(f"DEBUG: EPF query for wage {wage}, category {category}")
        
        # First try: Standard query using numeric comparison
        response = supabase.table("contribution_tables") \
            .select("employee_contribution, employer_contribution, total_contribution, from_wage, to_wage") \
            .eq("contrib_type", "epf") \
            .eq("category", category) \
            .lte("from_wage", wage) \
            .gte("to_wage", wage) \
            .limit(1) \
            .execute()
        
        print(f"DEBUG: Initial query response: {response.data}")
        
        if response.data:
            row = response.data[0]
            employee_contrib = float(row["employee_contribution"])
            employer_contrib = float(row["employer_contribution"])
            total_contrib = float(row["total_contribution"])
            print(f"DEBUG: EPF found in table for wage {wage}: Employee={employee_contrib}, Employer={employer_contrib}, Total={total_contrib}")
            return employee_contrib, employer_contrib, total_contrib
        
        # Second try: Manual filtering in case of data type issues
        print(f"DEBUG: No match with standard query, trying manual filtering...")
        all_records = supabase.table("contribution_tables") \
            .select("employee_contribution, employer_contribution, total_contribution, from_wage, to_wage") \
            .eq("contrib_type", "epf") \
            .eq("category", category) \
            .execute()
        
        if all_records.data:
            print(f"DEBUG: Found {len(all_records.data)} EPF records, filtering for wage {wage}...")
            for record in all_records.data:
                try:
                    from_wage = float(record["from_wage"])
                    to_wage = float(record["to_wage"])
                    if from_wage <= wage <= to_wage:
                        employee_contrib = float(record["employee_contribution"])
                        employer_contrib = float(record["employer_contribution"])
                        total_contrib = float(record["total_contribution"])
                        print(f"DEBUG: EPF manual match found for wage {wage} in range {from_wage}-{to_wage}: Employee={employee_contrib}, Employer={employer_contrib}")
                        return employee_contrib, employer_contrib, total_contrib
                except (ValueError, TypeError) as e:
                    print(f"DEBUG: Data type issue with record: {record}, error: {e}")
                    continue
        
        # Third try: Check if wage exceeds maximum and use percentage
        print(f"DEBUG: No table match found, checking if wage exceeds maximum...")
        max_band = supabase.table("contribution_tables") \
            .select("from_wage, to_wage") \
            .eq("contrib_type", "epf") \
            .eq("category", category) \
            .order("to_wage", desc=True) \
            .limit(1) \
            .execute()
        
        if max_band.data:
            max_wage = float(max_band.data[0]["to_wage"])
            print(f"DEBUG: Maximum wage in EPF table: {max_wage}, current wage: {wage}")
            
            if wage > max_wage:
                print(f"DEBUG: Wage {wage} exceeds table maximum {max_wage}, using percentage calculation")
            else:
                print(f"DEBUG: Wage {wage} is within table range but no match found - possible data issue")
                print(f"DEBUG: Using percentage calculation as fallback")
        else:
            print(f"DEBUG: No EPF data found for category {category}")
        
        # Percentage calculation fallback
        if category in ["part_a", "part_b"]:
            # Active employees (under 60): 11% employee + 12% employer
            employee_contrib = round(wage * 0.11, 2)
            employer_contrib = round(wage * 0.12, 2)
        elif category == "part_e":
            # Malaysian citizens 60+: 0% employee + 4% employer
            employee_contrib = 0.0
            employer_contrib = round(wage * 0.04, 2)
        elif category in ["part_c", "part_d"]:
            # Non-citizens: rates depend on election status
            employee_contrib = 0.0
            employer_contrib = round(wage * 0.04, 2)
        else:
            employee_contrib = employer_contrib = 0.0
        
        total_contrib = employee_contrib + employer_contrib
        print(f"DEBUG: EPF percentage calculation for wage {wage}, category {category}: Employee={employee_contrib}, Employer={employer_contrib}, Total={total_contrib}")
        return employee_contrib, employer_contrib, total_contrib
                
    except Exception as e:
        print(f"DEBUG: Error calculating EPF contributions: {str(e)}")
        return 0.0, 0.0, 0.0

def get_socso_contributions_from_table(wage: float, category: str = "first_category") -> tuple[float, float, float]:
    """
    Get SOCSO contributions from contribution_tables for a given wage and category.
    Returns (employee_contribution, employer_contribution, total_contribution)
    
    Args:
        wage: The wage amount to calculate contributions for  
        category: SOCSO category (first_category, second_category)
    """
    try:
        # Find the matching wage band in contribution_tables
        response = supabase.table("contribution_tables") \
            .select("employee_contribution, employer_contribution, total_contribution, from_wage, to_wage") \
            .eq("contrib_type", "socso") \
            .eq("category", category) \
            .lte("from_wage", wage) \
            .gte("to_wage", wage) \
            .limit(1) \
            .execute()
        
        if response.data:
            row = response.data[0]
            employee_contrib = float(row["employee_contribution"])
            employer_contrib = float(row["employer_contribution"])
            total_contrib = float(row["total_contribution"])
            print(f"DEBUG: SOCSO calculation for wage {wage}, category {category}: Employee={employee_contrib}, Employer={employer_contrib}, Total={total_contrib}")
            return employee_contrib, employer_contrib, total_contrib
        else:
            # If wage is above the highest band, use the maximum band rate (SOCSO is capped)
            max_band = supabase.table("contribution_tables") \
                .select("employee_contribution, employer_contribution, total_contribution, from_wage, to_wage") \
                .eq("contrib_type", "socso") \
                .eq("category", category) \
                .order("to_wage", desc=True) \
                .limit(1) \
                .execute()
            
            if max_band.data:
                row = max_band.data[0]
                employee_contrib = float(row["employee_contribution"])
                employer_contrib = float(row["employer_contribution"])
                total_contrib = float(row["total_contribution"])
                print(f"DEBUG: SOCSO calculation (max band) for wage {wage}, category {category}: Employee={employee_contrib}, Employer={employer_contrib}, Total={total_contrib}")
                return employee_contrib, employer_contrib, total_contrib
            else:
                print(f"DEBUG: No SOCSO data found for wage {wage}, category {category}")
                return 0.0, 0.0, 0.0
                
    except Exception as e:
        print(f"DEBUG: Error calculating SOCSO contributions: {str(e)}")
        return 0.0, 0.0, 0.0

def update_expired_bonus_statuses():
    """
    Update all bonuses with status 'Active' to 'Expired' if their expiry date has passed.
    
    Returns:
        Number of bonuses updated
    """
    try:
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Find all active bonuses that have expired
        response = supabase.table("bonuses").select("id, expiry_date, bonus_type, amount").eq("status", "Active").lt("expiry_date", today).execute()
        
        if not response.data:
            return 0
        
        updated_count = 0
        for bonus in response.data:
            # Update each expired bonus status
            update_response = supabase.table("bonuses").update({"status": "Expired"}).eq("id", bonus["id"]).execute()
            if update_response.data:
                updated_count += 1
                print(f"DEBUG: Updated bonus ID {bonus['id']} ({bonus['bonus_type']}, RM {bonus['amount']}) to Expired status")
        
        print(f"DEBUG: Updated {updated_count} expired bonus statuses")
        return updated_count
        
    except Exception as e:
        print(f"DEBUG: Error updating expired bonus statuses: {e}")
        return 0

def get_active_bonuses_for_employee(employee_id: str, payroll_date: str) -> float:
    """
    Get total active bonus amount for an employee on a specific payroll date.
    
    Args:
        employee_id: Employee UUID
        payroll_date: Payroll date in YYYY-MM-DD format
        
    Returns:
        Total bonus amount for the employee
    """
    try:
        # Query active bonuses that are effective on the payroll date
        response = supabase.table("bonuses").select("amount, effective_date, expiry_date").eq("employee_id", employee_id).eq("status", "Active").execute()
        
        if not response.data:
            return 0.0
        
        total_bonus = 0.0
        for bonus in response.data:
            effective_date = bonus.get('effective_date')
            expiry_date = bonus.get('expiry_date')
            amount = bonus.get('amount', 0.0)
            
            # Check if bonus is valid for the payroll date
            is_effective = True
            if effective_date and effective_date > payroll_date:
                is_effective = False
            if expiry_date and expiry_date < payroll_date:
                is_effective = False
                
            if is_effective:
                total_bonus += float(amount)
                print(f"DEBUG: Added bonus RM {amount} for employee {employee_id}")
        
        print(f"DEBUG: Total bonus for employee {employee_id}: RM {total_bonus}")
        return total_bonus
        
    except Exception as e:
        print(f"DEBUG: Error getting bonuses for employee {employee_id}: {e}")
        return 0.0

def get_monthly_unpaid_leave_deduction(employee_id: str, year: int, month: int) -> Dict:
    """
    Get unpaid leave deduction from the monthly_unpaid_leave table for a specific month.
    This ensures unpaid leave is only calculated for the target month, not carried over.
    """
    # Add a small retry loop to handle transient network errors (e.g. WinError 10054 / connection reset)
    attempts = 3
    base_delay = 0.5
    for attempt in range(1, attempts + 1):
        try:
            print(f"🔍 Getting monthly unpaid leave for employee {employee_id}, {year}-{month:02d} (attempt {attempt}/{attempts})")

            # Query the monthly unpaid leave table for this specific employee and month
            response = supabase.table("monthly_unpaid_leave").select(
                "unpaid_days, deduction_amount, basic_salary, allowances"
            ).eq("employee_id", employee_id) \
             .eq("year", year) \
             .eq("month", month) \
             .execute()

            # If we get here, the query succeeded; break out of retry loop
            break

        except Exception as e:
            # Detect connection-reset-like errors heuristically and retry
            err_text = str(e)
            is_conn_reset = "10054" in err_text or "ConnectionResetError" in err_text or "reset by peer" in err_text.lower()
            print(f"❌ Error querying monthly_unpaid_leave (attempt {attempt}/{attempts}): {e}")
            if attempt < attempts and is_conn_reset:
                # Exponential backoff with jitter
                sleep_seconds = base_delay * (2 ** (attempt - 1)) + random.random() * 0.2
                print(f"⏳ Transient connection error detected, retrying in {sleep_seconds:.1f}s...")
                time.sleep(sleep_seconds)
                continue
            else:
                # Final failure: log and return safe defaults so payroll keeps running
                print("❌ All retries failed or non-transient error; returning zero unpaid leave as fallback.")
                return {
                    "unpaid_days": 0.0,
                    "total_deduction": 0.0,
                    "basic_salary_stored": 0.0,
                    "allowances_stored": 0.0
                }

    # At this point 'response' should be defined and successful
    try:
        if response.data and len(response.data) > 0:
            record = response.data[0]
            unpaid_days = float(record.get("unpaid_days", 0.0))
            deduction_amount = float(record.get("deduction_amount", 0.0))
            print(f"📊 Found monthly record: {unpaid_days} days, RM{deduction_amount:.2f} deduction")

            return {
                "unpaid_days": unpaid_days,
                "total_deduction": deduction_amount,
                "basic_salary_stored": float(record.get("basic_salary", 0.0)),
                "allowances_stored": float(record.get("allowances", 0.0))
            }
        else:
            print(f"📝 No monthly unpaid leave record found for {employee_id}, {year}-{month:02d}")
            return {
                "unpaid_days": 0.0,
                "total_deduction": 0.0,
                "basic_salary_stored": 0.0,
                "allowances_stored": 0.0
            }

    except Exception as e:
        print(f"❌ Error processing monthly unpaid leave response: {e}")
        return {
            "unpaid_days": 0.0,
            "total_deduction": 0.0,
            "basic_salary_stored": 0.0,
            "allowances_stored": 0.0
        }

def get_approved_unpaid_leave_for_period(employee_email: str, start_date: str, end_date: str) -> float:
    """
    DEPRECATED: Get the total unpaid leave days for an employee within a specific period.
    This function is kept for backward compatibility but should be replaced with monthly table lookup.
    Use get_monthly_unpaid_leave_deduction() for payroll calculations instead.
    """
    try:
        print(f"⚠️ DEPRECATED: Using old unpaid leave calculation for {employee_email}")
        print(f"DEBUG: Getting unpaid leave for {employee_email} from {start_date} to {end_date}")
        
        # Query approved unpaid leave requests that overlap with the payroll period
        response = supabase.table("leave_requests").select(
            "start_date, end_date, is_half_day, half_day_period"
        ).eq("employee_email", employee_email).eq("leave_type", "Unpaid").eq("status", "Approved").execute()
        
        if not response.data:
            print(f"DEBUG: No approved unpaid leave found for {employee_email}")
            return 0.0
        
        total_unpaid_days = 0.0
        payroll_start = datetime.strptime(start_date, "%Y-%m-%d").date()
        payroll_end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        for leave in response.data:
            leave_start = datetime.strptime(leave["start_date"], "%Y-%m-%d").date()
            leave_end = datetime.strptime(leave["end_date"], "%Y-%m-%d").date()
            
            # Check if leave period overlaps with payroll period
            overlap_start = max(payroll_start, leave_start)
            overlap_end = min(payroll_end, leave_end)
            
            if overlap_start <= overlap_end:
                # Calculate overlapping days using CALENDAR DAYS (including weekends/holidays)
                if leave.get("is_half_day", False):
                    # Half-day leave counts as 0.5 days
                    if overlap_start == overlap_end:  # Single day overlap for half-day
                        total_unpaid_days += 0.5
                        period_info = f" ({leave.get('half_day_period', 'unknown')} half-day)"
                        print(f"DEBUG: Added 0.5 unpaid calendar day for {employee_email} on {overlap_start}{period_info}")
                else:
                    # Full days - calculate CALENDAR days (not working days)
                    overlap_days = (overlap_end - overlap_start).days + 1  # +1 to include both start and end dates
                    total_unpaid_days += overlap_days
                    print(f"DEBUG: Added {overlap_days} unpaid calendar days for {employee_email} from {overlap_start} to {overlap_end}")
        
        print(f"DEBUG: Total unpaid leave calendar days for {employee_email}: {total_unpaid_days}")
        return total_unpaid_days
        
    except Exception as e:
        print(f"DEBUG: Error getting unpaid leave for {employee_email}: {e}")
        return 0.0

def calculate_unpaid_leave_deduction(basic_salary: float, total_allowances: float, unpaid_days: float, payroll_month: str) -> dict:
    """
    Calculate salary deduction for unpaid leave according to Malaysian Employment Act standards.
    Formula: Deduction = (Monthly Salary × Unpaid Days) ÷ Total Calendar Days in Month
    """
    try:
        if unpaid_days <= 0:
            return {
                "unpaid_days": 0.0,
                "calendar_days_in_month": 0,
                "daily_basic_rate": 0.0,
                "daily_allowance_rate": 0.0,
                "basic_salary_deduction": 0.0,
                "allowance_deduction": 0.0,
                "total_deduction": 0.0
            }
        
        # Get calendar days in the payroll month (Malaysian Employment Act standard)
        payroll_date = datetime.strptime(payroll_month, "%Y-%m-%d")
        if payroll_date.month == 12:
            next_month = payroll_date.replace(year=payroll_date.year + 1, month=1, day=1)
        else:
            next_month = payroll_date.replace(month=payroll_date.month + 1, day=1)
        
        calendar_days_in_month = (next_month - payroll_date.replace(day=1)).days
        
        # Calculate daily rates based on calendar days (Malaysian standard: salary ÷ calendar days)
        daily_basic_rate = basic_salary / calendar_days_in_month
        daily_allowance_rate = total_allowances / calendar_days_in_month
        
        # Calculate deductions (Malaysian standard: daily rate × unpaid days)
        basic_salary_deduction = daily_basic_rate * unpaid_days
        allowance_deduction = daily_allowance_rate * unpaid_days
        total_deduction = basic_salary_deduction + allowance_deduction
        
        print(f"DEBUG: Malaysian unpaid leave calculation:")
        print(f"  - Month: {payroll_month} ({calendar_days_in_month} calendar days)")
        print(f"  - Unpaid days: {unpaid_days}")
        print(f"  - Daily basic: RM {daily_basic_rate:.2f} (RM {basic_salary:.2f} ÷ {calendar_days_in_month})")
        print(f"  - Daily allowance: RM {daily_allowance_rate:.2f} (RM {total_allowances:.2f} ÷ {calendar_days_in_month})")
        print(f"  - Basic deduction: RM {basic_salary_deduction:.2f}")
        print(f"  - Allowance deduction: RM {allowance_deduction:.2f}")
        print(f"  - Total deduction: RM {total_deduction:.2f}")
        
        return {
            "unpaid_days": unpaid_days,
            "calendar_days_in_month": calendar_days_in_month,
            "daily_basic_rate": daily_basic_rate,
            "daily_allowance_rate": daily_allowance_rate,
            "basic_salary_deduction": basic_salary_deduction,
            "allowance_deduction": allowance_deduction,
            "total_deduction": total_deduction
        }
        
    except Exception as e:
        print(f"DEBUG: Error calculating Malaysian unpaid leave deduction: {e}")
        return {
            "unpaid_days": 0.0,
            "calendar_days_in_month": 0,
            "daily_basic_rate": 0.0,
            "daily_allowance_rate": 0.0,
            "basic_salary_deduction": 0.0,
            "allowance_deduction": 0.0,
            "total_deduction": 0.0
        }

# Monthly Unpaid Leave Management Functions (for Admin Unpaid Leave Tab)

def get_or_create_monthly_unpaid_leave(employee_id: str, employee_email: str, year: int, month: int) -> dict:
    """
    Get or create a monthly unpaid leave record for an employee.
    """
    try:
        print(f"🔍 Getting/creating monthly unpaid leave for employee {employee_id}, {year}-{month:02d}")
        
        # Check if record exists
        response = supabase.table("monthly_unpaid_leave").select("*") \
            .eq("employee_id", employee_id) \
            .eq("year", year) \
            .eq("month", month) \
            .execute()
        
        if response.data and len(response.data) > 0:
            record = response.data[0]
            print(f"📄 Found existing record: {record.get('unpaid_days', 0)} days")
            return record
        else:
            # Create new record with defaults (only essential columns to avoid schema mismatches)
            new_record = {
                "employee_id": employee_id,
                "employee_email": employee_email,
                "year": year,
                "month": month,
                "unpaid_days": 0.0,
                "basic_salary": 0.0,
                "allowances": 0.0,
                "deduction_amount": 0.0,
                "notes": "",
            }

            try:
                create_response = supabase.table("monthly_unpaid_leave").insert(new_record).execute()
            except Exception as e:
                # Fallback: if schema complains about unknown columns, drop optional fields and retry
                print(f"⚠️ Insert failed, retrying without optional fields: {e}")
                for k in ["created_by", "created_at", "updated_at", "updated_by"]:
                    new_record.pop(k, None)
                create_response = supabase.table("monthly_unpaid_leave").insert(new_record).execute()

            if create_response.data:
                print(f"✅ Created new monthly unpaid leave record")
                return create_response.data[0]
            else:
                print(f"❌ Failed to create new record")
                return new_record
                
    except Exception as e:
        print(f"❌ Error getting/creating monthly unpaid leave: {e}")
        return {
            "employee_id": employee_id,
            "employee_email": employee_email,
            "year": year,
            "month": month,
            "unpaid_days": 0.0,
            "basic_salary": 0.0,
            "allowances": 0.0,
            "deduction_amount": 0.0,
            "notes": ""
        }

def update_monthly_unpaid_leave(employee_id: str, year: int, month: int, unpaid_days: float, 
                              basic_salary: float, allowances: float, updated_by: str = "admin", 
                              notes: str = "") -> bool:
    """
    Update a monthly unpaid leave record with new values.
    """
    try:
        print(f"📝 Updating monthly unpaid leave for employee {employee_id}, {year}-{month:02d}")
        
        # Calculate deduction
        import calendar
        calendar_days = calendar.monthrange(year, month)[1]
        daily_basic = basic_salary / calendar_days
        daily_allowance = allowances / calendar_days
        total_deduction = (daily_basic + daily_allowance) * unpaid_days
        
        update_data = {
            "unpaid_days": unpaid_days,
            "basic_salary": basic_salary,
            "allowances": allowances,
            "deduction_amount": total_deduction,
            "updated_by": updated_by,
            "notes": notes,
            "updated_at": datetime.now().isoformat()
        }
        
        try:
            response = supabase.table("monthly_unpaid_leave").update(update_data) \
                .eq("employee_id", employee_id) \
                .eq("year", year) \
                .eq("month", month) \
                .execute()
        except Exception as e:
            print(f"⚠️ Update failed (possible missing columns), retrying without optional fields: {e}")
            for k in ["updated_by", "updated_at", "created_by", "created_at"]:
                update_data.pop(k, None)
            response = supabase.table("monthly_unpaid_leave").update(update_data) \
                .eq("employee_id", employee_id) \
                .eq("year", year) \
                .eq("month", month) \
                .execute()
        
        if response.data and len(response.data) > 0:
            print(f"✅ Updated monthly unpaid leave: {unpaid_days} days, RM{total_deduction:.2f} deduction")
            return True
        else:
            print(f"❌ Failed to update monthly unpaid leave record")
            return False
            
    except Exception as e:
        print(f"❌ Error updating monthly unpaid leave: {e}")
        return False

def sync_monthly_unpaid_leave_from_requests(employee_id: str, employee_email: str, year: int, month: int) -> bool:
    """
    Sync monthly unpaid leave data from approved leave requests.
    """
    try:
        print(f"🔄 Syncing unpaid leave from requests for employee {employee_id}, {year}-{month:02d}")
        
        # Get start and end dates for the month
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"
        
        # Query approved unpaid leave requests for this month
        # Be robust to case differences in leave_type/status
        response = (
            supabase
            .table("leave_requests")
            .select("start_date, end_date, is_half_day")
            .eq("employee_email", employee_email)
            .in_("leave_type", ["Unpaid", "unpaid"])  # tolerate case
            .in_("status", ["Approved", "approved"])  # tolerate case
            .gte("start_date", start_date)
            .lt("start_date", end_date)
            .execute()
        )
        
        total_unpaid_days = 0.0
        
        if response.data:
            for leave in response.data:
                leave_start = datetime.strptime(leave["start_date"], "%Y-%m-%d").date()
                leave_end = datetime.strptime(leave["end_date"], "%Y-%m-%d").date()
                
                if leave.get("is_half_day", False):
                    total_unpaid_days += 0.5
                    print(f"  📅 Half-day unpaid leave on {leave_start}")
                else:
                    days = (leave_end - leave_start).days + 1
                    total_unpaid_days += days
                    print(f"  📅 {days} days unpaid leave from {leave_start} to {leave_end}")
        
        print(f"📊 Total unpaid days from requests: {total_unpaid_days}")
        
        # Get employee salary information
        emp_response = supabase.table("employees").select("basic_salary, allowances") \
            .eq("id", employee_id).execute()
        
        if emp_response.data and len(emp_response.data) > 0:
            employee = emp_response.data[0]
            basic_salary = float(employee.get("basic_salary", 0))
            allowances_dict = employee.get("allowances") or {}
            total_allowances = sum(float(v) for v in allowances_dict.values() if v)
            
            # Update the monthly record
            return update_monthly_unpaid_leave(
                employee_id, year, month, total_unpaid_days,
                basic_salary, total_allowances, "sync_from_requests"
            )
        else:
            print(f"❌ Employee salary information not found")
            return False
            
    except Exception as e:
        print(f"❌ Error syncing monthly unpaid leave from requests: {e}")
        return False

def get_monthly_unpaid_leave_summary(employee_id: str, year: int) -> list:
    """
    Get monthly unpaid leave summary for an employee for the entire year.
    """
    try:
        print(f"📊 Getting annual unpaid leave summary for employee {employee_id}, year {year}")
        
        response = supabase.table("monthly_unpaid_leave").select("*") \
            .eq("employee_id", employee_id) \
            .eq("year", year) \
            .order("month") \
            .execute()
        
        if response.data:
            print(f"📄 Found {len(response.data)} monthly records")
            return response.data
        else:
            print(f"📝 No monthly records found for {employee_id} in {year}")
            return []
            
    except Exception as e:
        print(f"❌ Error getting monthly unpaid leave summary: {e}")
        return []

def reset_annual_unpaid_leave(year: int) -> bool:
    """
    Reset all unpaid leave data for a specific year to zero.
    """
    try:
        print(f"🗑️ Resetting all unpaid leave data for year {year}")
        
        reset_update = {
            "unpaid_days": 0.0,
            "deduction_amount": 0.0,
            "updated_by": "annual_reset",
            "updated_at": datetime.now().isoformat(),
        }
        try:
            response = supabase.table("monthly_unpaid_leave").update(reset_update) \
                .eq("year", year) \
                .execute()
        except Exception as e:
            print(f"⚠️ Annual reset update failed, retrying without optional fields: {e}")
            for k in ["updated_by", "updated_at"]:
                reset_update.pop(k, None)
            response = supabase.table("monthly_unpaid_leave").update(reset_update) \
                .eq("year", year) \
                .execute()
        
        if response.data:
            print(f"✅ Reset {len(response.data)} monthly records for year {year}")
            return True
        else:
            print(f"❌ No records found to reset for year {year}")
            return False
            
    except Exception as e:
        print(f"❌ Error resetting annual unpaid leave: {e}")
        return False

 

def run_payroll(payroll_date: str) -> bool:
    try:
        # Update expired bonus statuses before processing payroll
        print("DEBUG: Updating expired bonus statuses...")
        updated_count = update_expired_bonus_statuses()
        if updated_count > 0:
            print(f"DEBUG: Updated {updated_count} expired bonuses to 'Expired' status")
        
        employees = supabase.table("employees").select("*").execute().data
        print(f"DEBUG: Found {len(employees)} employees")
        
        # Debug: Check the first employee's ID format
        if employees:
            first_emp = employees[0]
            print(f"DEBUG: First employee ID: {first_emp.get('employee_id')} (type: {type(first_emp.get('employee_id'))})")
            print(f"DEBUG: First employee keys: {list(first_emp.keys())}")
        
        payroll_runs = []

        for employee in employees:
            # Skip employees with Inactive payroll status
            try:
                _ps = str(employee.get('payroll_status') or '').strip().lower()
                # Treat any value containing 'inactive' as inactive for safety (e.g., 'Inactive Payroll')
                if _ps and 'inactive' in _ps:
                    # Prefer logging with readable identifier
                    _emp_ident = employee.get('employee_id') or employee.get('email') or employee.get('full_name') or employee.get('id')
                    print(f"⏭️  Skipping payroll for {_emp_ident} due to payroll_status='{employee.get('payroll_status')}'")
                    # Persist skip record
                    try:
                        from datetime import datetime as _dt
                        supabase.table('payroll_run_skips').insert({
                            'employee_id': employee.get('id'),
                            'payroll_date': payroll_date,
                            'reason': f"payroll_status='{employee.get('payroll_status')}'",
                            'created_at': _dt.now().isoformat()
                        }).execute()
                    except Exception as _sk1:
                        print(f"DEBUG: Failed to persist skip (fixed run): {_sk1}")
                    continue
            except Exception:
                pass
            # Skip employees with non-active Employment Status (e.g., Inactive, Resigned, Terminated, Retired)
            try:
                _es = str(employee.get('status') or '').strip().lower()
                if _es in ('inactive', 'resigned', 'terminated', 'retired') or any(k in _es for k in ('inactive','resigned','terminated','retired')):
                    _emp_ident = employee.get('employee_id') or employee.get('email') or employee.get('full_name') or employee.get('id')
                    print(f"⏭️  Skipping payroll for {_emp_ident} due to employment status='{employee.get('status')}'")
                    # Persist skip record
                    try:
                        from datetime import datetime as _dt
                        supabase.table('payroll_run_skips').insert({
                            'employee_id': employee.get('id'),
                            'payroll_date': payroll_date,
                            'reason': f"employment status='{employee.get('status')}'",
                            'created_at': _dt.now().isoformat()
                        }).execute()
                    except Exception as _sk2:
                        print(f"DEBUG: Failed to persist skip (fixed run, status): {_sk2}")
                    continue
            except Exception:
                pass
            # Validate essential fields first
            # Use 'id' (UUID) not 'employee_id' (TEXT) for foreign key relationships
            employee_uuid = employee.get("id")
            employee_text_id = employee.get("employee_id") 
            
            if not employee_uuid:
                print(f"DEBUG: No UUID id found for employee: {employee}")
                continue
                
            print(f"DEBUG: Processing employee - UUID: {employee_uuid}, Text ID: {employee_text_id}")
                
            basic_salary = employee.get("basic_salary")
            if basic_salary is None:
                print(f"DEBUG: No basic_salary for employee {employee_text_id}, defaulting to 0")
                basic_salary = 0.0
            
            try:
                wage = float(basic_salary)
            except (ValueError, TypeError):
                print(f"DEBUG: Invalid basic_salary {basic_salary} for employee {employee_text_id}, defaulting to 0")
                wage = 0.0
                
            nationality = employee.get("nationality", "Malaysia")
            citizenship = employee.get("citizenship", "Citizen")
            date_of_birth = employee.get("date_of_birth", "1900-01-01")
            
            if date_of_birth is None:
                print(f"DEBUG: No date_of_birth for employee {employee_text_id}, defaulting to 1900-01-01")
                date_of_birth = "1900-01-01"
                
            age = calculate_age(date_of_birth)
            # Prefer 'position' as canonical seniority/role, fallback to 'job_title' for backwards compatibility
            emp_position = (employee.get('position') or employee.get('job_title') or '')
            is_intern = str(emp_position).lower() == "intern"
            # Validate allowances
            allowances = employee.get("allowances", {})
            if not isinstance(allowances, dict):
                print(f"DEBUG: Invalid allowances for employee {employee_text_id}, defaulting to empty dictionary")
                allowances = {}
            
            # Calculate total allowances with None handling
            total_allowances = 0.0
            for key, value in allowances.items():
                if value is not None:
                    try:
                        total_allowances += float(value)
                    except (ValueError, TypeError):
                        print(f"DEBUG: Invalid allowance value {value} for {key}, skipping")
            
            print(f"DEBUG: Employee {employee_text_id} - wage={wage}, total_allowances={total_allowances}")

            # Get active bonuses for this employee
            employee_bonus = get_active_bonuses_for_employee(employee_uuid, payroll_date)

            # Calculate unpaid leave deduction for the SPECIFIC payroll month ONLY
            # This ensures unpaid leave from September only affects September payroll
            payroll_dt = datetime.strptime(payroll_date, "%Y-%m-%d")
            payroll_year = payroll_dt.year
            payroll_month = payroll_dt.month
            
            print(f"📅 Processing payroll for {employee_text_id} - {payroll_year}-{payroll_month:02d}")
            
            # Use monthly table lookup instead of period-based calculation
            monthly_unpaid_leave = get_monthly_unpaid_leave_deduction(employee_uuid, payroll_year, payroll_month)
            unpaid_days = monthly_unpaid_leave["unpaid_days"]
            total_unpaid_deduction = monthly_unpaid_leave["total_deduction"]

            # Auto-sync fallback: if record missing/zero but approved requests exist, populate then re-fetch
            try:
                if float(unpaid_days or 0.0) == 0.0:
                    emp_email = (employee.get("email") or "").strip()
                    # Check if there are approved unpaid requests starting in this month
                    start_date = f"{payroll_year}-{payroll_month:02d}-01"
                    if payroll_month == 12:
                        end_date = f"{payroll_year + 1}-01-01"
                    else:
                        end_date = f"{payroll_year}-{(payroll_month + 1):02d}-01"
                    try:
                        lr = (
                            supabase
                            .table("leave_requests")
                            .select("id")
                            .eq("employee_email", emp_email)
                            .in_("leave_type", ["Unpaid", "unpaid"])  # case tolerant
                            .in_("status", ["Approved", "approved"])   # case tolerant
                            .gte("start_date", start_date)
                            .lt("start_date", end_date)
                            .execute()
                        )
                        has_unpaid = bool(getattr(lr, "data", []) )
                    except Exception as _qe:
                        print(f"DEBUG: Could not probe unpaid requests for autosync: {_qe}")
                        has_unpaid = False

                    if has_unpaid:
                        # Ensure monthly record exists, then sync from requests
                        try:
                            get_or_create_monthly_unpaid_leave(employee_uuid, emp_email, payroll_year, payroll_month)
                        except Exception as _gce:
                            print(f"DEBUG: get_or_create monthly unpaid failed: {_gce}")
                        try:
                            ok = sync_monthly_unpaid_leave_from_requests(employee_uuid, emp_email, payroll_year, payroll_month)
                            if ok:
                                # Re-fetch to use updated values
                                monthly_unpaid_leave = get_monthly_unpaid_leave_deduction(employee_uuid, payroll_year, payroll_month)
                                unpaid_days = monthly_unpaid_leave["unpaid_days"]
                                total_unpaid_deduction = monthly_unpaid_leave["total_deduction"]
                                print(f"🔄 Auto-synced monthly unpaid: {unpaid_days} days, RM{total_unpaid_deduction:.2f}")
                        except Exception as _se:
                            print(f"DEBUG: Autosync monthly unpaid failed: {_se}")
            except Exception as _aserr:
                print(f"DEBUG: Autosync block error: {_aserr}")
            
            # If no monthly record exists but we need to calculate from current salary
            if total_unpaid_deduction == 0.0 and unpaid_days > 0.0:
                print(f"🔄 Calculating deduction for {unpaid_days} days using current salary")
                unpaid_leave_deduction_info = calculate_unpaid_leave_deduction(wage, total_allowances, unpaid_days, payroll_date)
                total_unpaid_deduction = unpaid_leave_deduction_info["total_deduction"]
            
            # Apply unpaid leave deductions to salary components 
            # (This is just for display/calculation - actual deduction is total_unpaid_deduction)
            if total_unpaid_deduction > 0:
                print(f"💰 Applying RM{total_unpaid_deduction:.2f} unpaid leave deduction to {employee_text_id}")
            
            print(f"DEBUG: Employee {employee_text_id} - Original: Basic=RM{wage:.2f}, Allowances=RM{total_allowances:.2f}")
            print(f"DEBUG: Employee {employee_text_id} - Unpaid leave: {unpaid_days} days, Total deduction=RM{total_unpaid_deduction:.2f}")
            print(f"🎯 Month-specific unpaid leave: Only {payroll_year}-{payroll_month:02d} affects this payroll")

            # Load Potongan Bulan Semasa (monthly deductions) for the payroll month
            try:
                monthly_deductions = get_monthly_deductions(employee_uuid, payroll_year, payroll_month)
            except Exception as _md_err:
                print(f"DEBUG: Could not load monthly deductions for {employee_text_id}: {_md_err}")
                monthly_deductions = { 'zakat_monthly': 0.0, 'religious_travel_monthly': 0.0, 'other_deductions_amount': 0.0 }

            # Handle interns (SKIP all contributions and logs!)
            if is_intern:
                print(f"DEBUG: Processing intern {employee_text_id}")
                gross_salary = total_allowances + employee_bonus  # Use original allowances for interns (no basic salary)
                net_salary = gross_salary - total_unpaid_deduction  # Apply unpaid leave deduction
                payroll = {
                    "employee_id": employee_uuid,  # Use UUID for foreign key
                    "payroll_date": payroll_date,
                    "gross_salary": gross_salary,
                    "allowances": allowances,
                    "epf_employee": 0.0,
                    "epf_employer": 0.0,
                    "socso_employee": 0.0,
                    "socso_employer": 0.0,
                    "eis_employee": 0.0,
                    "eis_employer": 0.0,
                    "pcb": 0.0,
                    "net_salary": net_salary,
                    "bonus": employee_bonus,  # Use actual bonus amount
                    "sip_deduction": 0.0,
                    "additional_epf_deduction": 0.0,
                    "prs_deduction": 0.0,
                    "insurance_premium": 0.0,
                    "medical_premium": 0.0,
                    "other_deductions": 0.0,
                    "unpaid_leave_days": unpaid_days,
                    "unpaid_leave_deduction": total_unpaid_deduction,
                    "created_at": datetime.now(KL_TZ).isoformat()
                }
                payroll_runs.append(payroll)
                continue  # Skip statutory calculations for interns

            # 🇲🇾 MALAYSIAN PAYROLL CALCULATION SEQUENCE (EA 1955 + LHDN compliant)
            
            # Determine EPF part for this employee using new calculator
            try:
                from core.epf_socso_calculator import EPFSOCSCalculator
                calculator = EPFSOCSCalculator()
                
                # Get EPF eligibility
                epf_status = calculator.calculate_epf_socso_status(
                    birth_date=date_of_birth.strftime('%Y-%m-%d') if isinstance(date_of_birth, date) else date_of_birth,
                    nationality=nationality,
                    citizenship=citizenship
                )
                
                part = epf_status.get('epf_part')
                print(f"DEBUG: EPF part determined by calculator: {part}")
                
            except Exception as e:
                print(f"DEBUG: Error using EPF calculator, falling back to legacy: {e}")
                # Fallback to legacy function without missing fields
                part = determine_epf_part(
                    age,
                    nationality,
                    citizenship,
                    is_intern,
                    False,  # is_electing - no longer in database
                    None    # election_date - no longer in database
                )
            
            # Step 1: Calculate Gross Salary
            gross_salary = wage + total_allowances + employee_bonus
            print(f"🇲🇾 Step 1 - Gross Salary: RM{gross_salary:.2f} (Basic: RM{wage:.2f} + Allowances: RM{total_allowances:.2f} + Bonus: RM{employee_bonus:.2f})")
            
            # Step 2: Calculate EPF on GROSS SALARY (before unpaid leave deduction)
            if part:
                epf_employee, epf_employer, _ = get_epf_contributions_from_table(gross_salary, part)
                print(f"🇲🇾 Step 2 - EPF ({part}): Employee RM{epf_employee:.2f}, Employer RM{epf_employer:.2f} (on BASIC salary RM{gross_salary:.2f})")
            else:
                epf_employee, epf_employer = 0.0, 0.0
                print(f"🇲🇾 Step 2 - EPF: Skipped (no EPF eligibility)")

            # Step 3: Calculate SOCSO on GROSS SALARY (before unpaid leave deduction)
            if age < 60:
                socso_category = "first_category"  # Under 60: both schemes
                socso_employee, socso_employer, _ = get_socso_contributions_from_table(gross_salary, socso_category)
                print(f"🇲🇾 Step 3 - SOCSO ({socso_category}): Employee RM{socso_employee:.2f}, Employer RM{socso_employer:.2f}")
            else:
                socso_category = "second_category"  # 60+: employment injury only
                socso_employee, socso_employer, _ = get_socso_contributions_from_table(gross_salary, socso_category)
                print(f"🇲🇾 Step 3 - SOCSO ({socso_category}): Employee RM{socso_employee:.2f}, Employer RM{socso_employer:.2f}")

            # Step 4: Calculate EIS on GROSS SALARY (before unpaid leave deduction)
            eis_employee, eis_employer, _ = get_eis_contributions(gross_salary, "eis")
            print(f"🇲🇾 Step 4 - EIS: Employee RM{eis_employee:.2f}, Employer RM{eis_employer:.2f}")
            
            # Step 5: Calculate Taxable Income (gross salary minus EPF/SOCSO/EIS deductions)
            taxable_income = gross_salary - epf_employee - socso_employee - eis_employee
            print(f"🇲🇾 Step 5 - Taxable Income: RM{taxable_income:.2f} (After EPF/SOCSO/EIS deductions)")
            
            # Step 6: Calculate PCB using official LHDN formula
            # Load tax configuration first
            tax_config = load_tax_rates_configuration() or get_default_tax_rates_config()
            
            # Get YTD accumulated data for this employee from payroll_ytd_accumulated
            try:
                employee_email_for_ytd = (employee.get("email") or "").lower()
                ytd_row = None
                if employee_email_for_ytd:
                    # Use previous month’s YTD (up to last month) for current month PCB
                    _prev_month = 12 if payroll_dt.month == 1 else (payroll_dt.month - 1)
                    _prev_year = payroll_dt.year - 1 if payroll_dt.month == 1 else payroll_dt.year
                    _ytd = supabase.table("payroll_ytd_accumulated").select("*") \
                        .eq("employee_email", employee_email_for_ytd) \
                        .eq("year", _prev_year) \
                        .eq("month", _prev_month) \
                        .execute()
                    if _ytd and _ytd.data:
                        ytd_row = _ytd.data[0]
                if ytd_row:
                    ytd_data = {
                        'accumulated_gross': float(ytd_row.get('accumulated_gross_salary_ytd', 0.0) or 0.0),
                        'accumulated_epf': float(ytd_row.get('accumulated_epf_employee_ytd', 0.0) or 0.0),
                        'accumulated_pcb': float(ytd_row.get('accumulated_pcb_ytd', 0.0) or 0.0),
                        'accumulated_zakat': float(ytd_row.get('accumulated_zakat_ytd', 0.0) or 0.0),
                        'accumulated_other_reliefs': float(ytd_row.get('accumulated_tax_reliefs_ytd', 0.0) or 0.0),
                        'accumulated_socso': float(ytd_row.get('accumulated_socso_employee_ytd', 0.0) or 0.0),
                        'accumulated_eis': float(ytd_row.get('accumulated_eis_employee_ytd', 0.0) or 0.0),
                    }
                else:
                    # Fallback: reconstruct previous-month YTD from payroll_runs before payroll_dt
                    print("📝 No YTD row found; reconstructing from payroll_runs before current month")
                    try:
                        pr = (
                            supabase.table('payroll_runs')
                            .select('gross_salary, epf_employee, pcb, payroll_date, created_at')
                            .eq('employee_id', employee_uuid)
                            .execute()
                        )
                        _gross = _epf = _pcb = 0.0
                        # Deduplicate by month within the same year, picking the latest created_at per month strictly before payroll_dt
                        monthly_latest: dict = {}
                        dup_count = 0
                        if pr and pr.data:
                            for r in pr.data:
                                try:
                                    _pd = str(r.get('payroll_date') or '')
                                    _pdt = _parse_any_date(_pd)
                                    if not _pdt:
                                        continue
                                    # Restrict to current payroll year only and strictly before this payroll MONTH (exclude any rows within the same month)
                                    if _pdt.year != payroll_dt.year or _pdt.month >= payroll_dt.month:
                                        continue
                                    key = (_pdt.year, _pdt.month)
                                    prev = monthly_latest.get(key)
                                    # Choose the record with the latest created_at (fallback: keep the last seen)
                                    cur_created = _parse_any_date(str(r.get('created_at') or ''))
                                    if prev is None:
                                        monthly_latest[key] = (r, cur_created)
                                    else:
                                        dup_count += 1
                                        prev_created = prev[1]
                                        if not prev_created or (cur_created and cur_created > prev_created):
                                            monthly_latest[key] = (r, cur_created)
                                except Exception:
                                    continue
                        for (yy, mm), (r, _c) in monthly_latest.items():
                            _gross += float(r.get('gross_salary', 0) or 0)
                            _epf += float(r.get('epf_employee', 0) or 0)
                            _pcb += float(r.get('pcb', 0) or 0)
                        ytd_data = {
                            'accumulated_gross': _gross,
                            'accumulated_epf': _epf,
                            'accumulated_pcb': _pcb,
                            'accumulated_zakat': 0.0,
                            'accumulated_other_reliefs': 0.0,
                            'accumulated_socso': 0.0,
                            'accumulated_eis': 0.0,
                        }
                        print(f"DEBUG: Reconstructed previous-month YTD from payroll_runs as fallback for PCB inputs (months={len(monthly_latest)}, dups_skipped={dup_count})")
                    except Exception as _recon_err:
                        print(f"DEBUG: YTD reconstruction from payroll_runs failed: {_recon_err}; using zeros")
                        ytd_data = {
                            'accumulated_gross': 0.0,
                            'accumulated_epf': 0.0,
                            'accumulated_pcb': 0.0,
                            'accumulated_zakat': 0.0,
                            'accumulated_other_reliefs': 0.0,
                            'accumulated_socso': 0.0,
                            'accumulated_eis': 0.0,
                        }
            except Exception as _yr:
                print(f"DEBUG: Failed to load YTD from payroll_ytd_accumulated: {_yr}")
                # As a last resort, attempt reconstruction from payroll_runs
                try:
                    pr = (
                        supabase.table('payroll_runs')
                        .select('gross_salary, epf_employee, pcb, payroll_date, created_at')
                        .eq('employee_id', employee_uuid)
                        .execute()
                    )
                    _gross = _epf = _pcb = 0.0
                    monthly_latest: dict = {}
                    dup_count = 0
                    if pr and pr.data:
                        for r in pr.data:
                            try:
                                _pd = str(r.get('payroll_date') or '')
                                _pdt = _parse_any_date(_pd)
                                if not _pdt:
                                    continue
                                if _pdt.year != payroll_dt.year or _pdt.month >= payroll_dt.month:
                                    continue
                                key = (_pdt.year, _pdt.month)
                                prev = monthly_latest.get(key)
                                cur_created = _parse_any_date(str(r.get('created_at') or ''))
                                if prev is None:
                                    monthly_latest[key] = (r, cur_created)
                                else:
                                    dup_count += 1
                                    prev_created = prev[1]
                                    if not prev_created or (cur_created and cur_created > prev_created):
                                        monthly_latest[key] = (r, cur_created)
                            except Exception:
                                continue
                    for (yy, mm), (r, _c) in monthly_latest.items():
                        _gross += float(r.get('gross_salary', 0) or 0)
                        _epf += float(r.get('epf_employee', 0) or 0)
                        _pcb += float(r.get('pcb', 0) or 0)
                    ytd_data = {
                        'accumulated_gross': _gross,
                        'accumulated_epf': _epf,
                        'accumulated_pcb': _pcb,
                        'accumulated_zakat': 0.0,
                        'accumulated_other_reliefs': 0.0,
                        'accumulated_socso': 0.0,
                        'accumulated_eis': 0.0,
                    }
                    print(f"DEBUG: Reconstructed previous-month YTD from payroll_runs after YTD table error (months={len(monthly_latest)}, dups_skipped={dup_count})")
                except Exception as _last_err:
                    print(f"DEBUG: Final YTD reconstruction failed: {_last_err}; defaulting to zeros")
                    ytd_data = {
                        'accumulated_gross': 0.0,
                        'accumulated_epf': 0.0,
                        'accumulated_pcb': 0.0,
                        'accumulated_zakat': 0.0,
                        'accumulated_other_reliefs': 0.0,
                        'accumulated_socso': 0.0,
                        'accumulated_eis': 0.0,
                    }
            
            # TEST OVERRIDE (disabled by default): For November example with specific YTD data.
            # Enable only by setting HRMS_ENABLE_PCB_TEST_MODE=1 in environment.
            try:
                _enable_test = str(os.environ.get('HRMS_ENABLE_PCB_TEST_MODE', '0')).strip() == '1'
            except Exception:
                _enable_test = False
            if _enable_test and ((payroll_dt.month == 11 and abs(wage - 17000.0) < 0.01) or \
               (isinstance(tax_config, dict) and tax_config.get('test_mode', False))):
                print("TEST MODE ENABLED: Using simulated November YTD data")
                ytd_data = {
                    'accumulated_gross': 170000.0,   # 10 months × RM17,000
                    'accumulated_epf': 3333.3,       # 10 months × RM333.33 (limited)
                    'accumulated_pcb': 0.0,          # No previous PCB
                    'accumulated_zakat': 0.0,        # No zakat
                    'accumulated_other_reliefs': 0.0 # No other reliefs YTD
                }
            
            # Use monthly zakat from table (affects PCB calculation per LHDN formula)
            _current_month_zakat = 0.0
            try:
                _current_month_zakat = float(monthly_deductions.get('zakat_monthly', 0.0) or 0.0)
            except Exception:
                _current_month_zakat = 0.0

            # Compute SOCSO+EIS LP1 (B20) with RM350 annual cap (for PCB only)
            # Also reconstruct YTD LP1 (previous months) so P reflects elapsed LP1 like LHDN calculator.
            try:
                # Annual cap (try from tax config table if present; fallback RM350)
                try:
                    lhdn_cfg = get_lhdn_tax_config('default') or {}
                    # Prefer explicit B20 cap key; fall back to legacy or generic keys; else RM350
                    socso_eis_annual_cap = float(
                        lhdn_cfg.get('b20_socso_eis_annual_cap', lhdn_cfg.get('b20_socso_eis_max', lhdn_cfg.get('socso_eis_annual_cap', 350.0)))
                        or 350.0
                    )
                except Exception:
                    socso_eis_annual_cap = 350.0

                # YTD SOCSO+EIS already claimed (elapsed months only)
                ytd_lp1_claimed = 0.0
                try:
                    # Preferred source: tp1_monthly_details.socso_eis_lp1_monthly
                    if employee_uuid and _probe_table_exists('tp1_monthly_details') and _probe_column_exists('tp1_monthly_details', 'socso_eis_lp1_monthly'):
                        rows = (
                            supabase.table('tp1_monthly_details')
                            .select('year, month, socso_eis_lp1_monthly')
                            .eq('employee_id', employee_uuid)
                            .eq('year', payroll_dt.year)
                            .execute()
                        ).data or []
                        for r in rows:
                            try:
                                mm = int(r.get('month') or 0)
                                if 1 <= mm < payroll_dt.month:
                                    ytd_lp1_claimed += float(r.get('socso_eis_lp1_monthly', 0.0) or 0.0)
                            except Exception:
                                continue
                except Exception as _tp1y:
                    print(f"DEBUG: Failed to sum socso_eis_lp1_monthly (tp1_monthly_details): {_tp1y}")

                # Secondary source: payroll_monthly_deductions.socso_eis_lp1_monthly
                if ytd_lp1_claimed <= 0.0:
                    try:
                        if employee_uuid and _probe_table_exists('payroll_monthly_deductions') and _probe_column_exists('payroll_monthly_deductions', 'socso_eis_lp1_monthly'):
                            rows = (
                                supabase.table('payroll_monthly_deductions')
                                .select('year, month, socso_eis_lp1_monthly')
                                .eq('employee_id', employee_uuid)
                                .eq('year', payroll_dt.year)
                                .execute()
                            ).data or []
                            for r in rows:
                                try:
                                    mm = int(r.get('month') or 0)
                                    if 1 <= mm < payroll_dt.month:
                                        ytd_lp1_claimed += float(r.get('socso_eis_lp1_monthly', 0.0) or 0.0)
                                except Exception:
                                    continue
                    except Exception as _mdy:
                        print(f"DEBUG: Failed to sum socso_eis_lp1_monthly (payroll_monthly_deductions): {_mdy}")

                # Final fallback: infer from contributions in payroll_information (upper bound)
                if ytd_lp1_claimed <= 0.0:
                    try:
                        if id and _probe_table_exists('payroll_information'):
                            resp = (
                                supabase.table('payroll_information')
                                .select('employee_id, month_year, socso_employee, eis_employee')
                                .eq('employee_id', id)
                                .execute()
                            )
                            if resp.data:
                                for r in resp.data:
                                    try:
                                        mm_str, yy_str = str(r.get('month_year','')).split('/') if '/' in str(r.get('month_year','')) else (None,None)
                                        if mm_str and yy_str and int(yy_str) == payroll_dt.year and int(mm_str) < payroll_dt.month:
                                            ytd_lp1_claimed += float(r.get('socso_employee', 0.0) or 0.0) + float(r.get('eis_employee', 0.0) or 0.0)
                                    except Exception:
                                        continue
                    except Exception as _ytdse:
                        print(f"DEBUG: Could not compute YTD SOCSO+EIS for LP1 (fallback): {_ytdse}")

                # Extra safety fallback: infer from payroll_runs and take the maximum across sources
                try:
                    pr_prev = (
                        supabase.table('payroll_runs')
                        .select('socso_employee, eis_employee, payroll_date, created_at')
                        .eq('employee_id', employee_uuid)
                        .execute()
                    )
                    # Deduplicate by month in same year and sum socso+eis for months strictly before this month
                    monthly_latest_pr: dict = {}
                    if pr_prev and pr_prev.data:
                        for r in pr_prev.data:
                            try:
                                _pd = str(r.get('payroll_date') or '')
                                _pdt = _parse_any_date(_pd)
                                if not _pdt:
                                    continue
                                if _pdt.year != payroll_dt.year or _pdt.month >= payroll_dt.month:
                                    continue
                                key = (_pdt.year, _pdt.month)
                                prev = monthly_latest_pr.get(key)
                                cur_created = _parse_any_date(str(r.get('created_at') or ''))
                                if prev is None:
                                    monthly_latest_pr[key] = (r, cur_created)
                                else:
                                    prev_created = prev[1]
                                    if not prev_created or (cur_created and cur_created > prev_created):
                                        monthly_latest_pr[key] = (r, cur_created)
                            except Exception:
                                continue
                    fallback_sum = 0.0
                    for (_yy, _mm), (r, _c) in monthly_latest_pr.items():
                        fallback_sum += float(r.get('socso_employee', 0.0) or 0.0) + float(r.get('eis_employee', 0.0) or 0.0)
                    if fallback_sum > ytd_lp1_claimed:
                        ytd_lp1_claimed = fallback_sum
                except Exception as _pry:
                    print(f"DEBUG: Could not compute YTD SOCSO+EIS from payroll_runs: {_pry}")

                # Clamp YTD claimed to annual cap
                ytd_lp1_claimed = float(max(0.0, min(ytd_lp1_claimed, socso_eis_annual_cap)))

                # Current month eligible amount bounded by remaining cap
                current_socso_eis = float(socso_employee or 0.0) + float(eis_employee or 0.0)
                remaining_cap = max(0.0, float(socso_eis_annual_cap) - float(ytd_lp1_claimed))
                socso_eis_lp1_this_month = max(0.0, min(remaining_cap, current_socso_eis))

                # Do not persist SOCSO+EIS into monthly_deductions; only use it in LP1 for this month
                try:
                    print(f"🎯 B20 SOCSO+EIS LP1 this month: RM{socso_eis_lp1_this_month:.2f} (cap remaining RM{remaining_cap:.2f}, YTD claimed RM{ytd_lp1_claimed:.2f})")
                except Exception:
                    # Ignore console encoding issues; keep computed values
                    pass
            except Exception as _se_lp1_err:
                print(f"DEBUG: Error computing SOCSO+EIS LP1 (run_payroll): {_se_lp1_err}")

            # LP1 for PCB = base LP1 from monthly_deductions + SOCSO+EIS portion (this month)
            base_lp1_only = _derive_other_reliefs_current_from_monthly(monthly_deductions)
            _other_reliefs_current = round(float(base_lp1_only or 0.0) + float(socso_eis_lp1_this_month or 0.0), 2)

            # Fold YTD B20 into other_reliefs_ytd only when a prior YTD total isn't already present.
            # If payroll_ytd_accumulated.accumulated_tax_reliefs_ytd already includes B20 for prior months
            # (e.g., January ΣLP=TP1 cash + SOCSO/EIS), do not add it again here.
            other_reliefs_ytd_enhanced = float(ytd_data['accumulated_other_reliefs'] or 0.0)
            try:
                if other_reliefs_ytd_enhanced <= 0.0:
                    other_reliefs_ytd_enhanced = float(ytd_lp1_claimed or 0.0)
                # else keep existing ΣLP as-is (assumed already inclusive of B20), avoiding double-count
            except Exception:
                pass

            # Child count: prefer explicit child_count, else employees.number_of_children
            _emp_child_count = employee.get('child_count')
            if _emp_child_count in (None, '', 0):
                try:
                    _emp_child_count = int(employee.get('number_of_children', 0) or 0)
                except Exception:
                    _emp_child_count = 0

            # Spouse not working: default spouse relief and spouse rebate eligibility
            # Align with calculate_comprehensive_payroll behavior
            _spouse_relief_default = 4000.0
            try:
                _lhdn_cfg = get_lhdn_tax_config('default') or {}
                _spouse_relief_default = float(_lhdn_cfg.get('spouse_relief', 4000.0) or 4000.0)
            except Exception:
                _spouse_relief_default = 4000.0
            try:
                _ms = str(employee.get('marital_status', '') or '').strip().lower()
                _sw = employee.get('spouse_working')
                _sw_norm = None
                if isinstance(_sw, bool):
                    _sw_norm = _sw
                elif isinstance(_sw, str):
                    _s = _sw.strip().lower()
                    if _s in ('yes', 'y', 'true', '1'):
                        _sw_norm = True
                    elif _s in ('no', 'n', 'false', '0'):
                        _sw_norm = False
            except Exception:
                _ms, _sw_norm = '', None

            _spouse_relief_to_use = float(employee.get('spouse_relief', 0.0) or 0.0)
            _spouse_rebate_eligible = False
            if ('married' in _ms) and (_sw_norm is False):
                if _spouse_relief_to_use <= 0.0:
                    _spouse_relief_to_use = _spouse_relief_default
                _spouse_rebate_eligible = True

            # Determine OKU relief amounts for individual and spouse
            try:
                _lhdn_cfg2 = get_lhdn_tax_config('default') or {}
                _oku_self_amt = float(_lhdn_cfg2.get('b4_individual_disability_max', 6000.0) or 6000.0)
                # Align disabled spouse relief fallback to RM6,000 when config value missing
                _oku_spouse_amt = float(_lhdn_cfg2.get('b15_disabled_spouse_relief_max', 6000.0) or 6000.0)
            except Exception:
                _oku_self_amt, _oku_spouse_amt = 6000.0, 5000.0

            _oku_self_flag: Optional[bool] = None
            _oku_spouse_flag: Optional[bool] = None
            # Prefer payroll_configurations snapshot flags when available
            try:
                if employee_uuid and _probe_table_exists('payroll_configurations') and _probe_column_exists('payroll_configurations', 'tax_relief_data'):
                    _cfg = supabase.table('payroll_configurations').select('tax_relief_data').eq('employee_id', employee_uuid).limit(1).execute()
                    if _cfg and _cfg.data:
                        _snap = _cfg.data[0].get('tax_relief_data') or {}
                        if isinstance(_snap, dict):
                            if 'is_individual_disabled' in _snap:
                                _oku_self_flag = bool(_snap.get('is_individual_disabled'))
                            if 'is_spouse_disabled' in _snap:
                                _oku_spouse_flag = bool(_snap.get('is_spouse_disabled'))
            except Exception as _okuread:
                print(f"DEBUG: Unable to read OKU flags from payroll_configurations: {_okuread}")
            # Fallback to employee flags
            if _oku_self_flag is None:
                try:
                    _oku_self_flag = bool(employee.get('is_individual_disabled'))
                except Exception:
                    _oku_self_flag = False
            if _oku_spouse_flag is None:
                try:
                    _oku_spouse_flag = bool(employee.get('is_spouse_disabled'))
                except Exception:
                    _oku_spouse_flag = False

            _disabled_individual_amt = _oku_self_amt if _oku_self_flag else 0.0
            _disabled_spouse_amt = _oku_spouse_amt if _oku_spouse_flag else 0.0

            payroll_inputs_for_pcb = {
                'accumulated_gross_ytd': ytd_data['accumulated_gross'],
                'accumulated_epf_ytd': ytd_data['accumulated_epf'],
                'accumulated_pcb_ytd': ytd_data['accumulated_pcb'],
                'accumulated_zakat_ytd': ytd_data['accumulated_zakat'],
                'individual_relief': tax_config.get('individual_relief', 9000.0),
                'spouse_relief': _spouse_relief_to_use,
                'child_relief': tax_config.get('child_relief', 2000.0),
                'child_count': _emp_child_count,
                'disabled_individual': _disabled_individual_amt,
                'disabled_spouse': _disabled_spouse_amt,
                'other_reliefs_ytd': other_reliefs_ytd_enhanced,
                'other_reliefs_current': _other_reliefs_current,
                'current_month_zakat': _current_month_zakat,
                # Enable detailed PCB debug logs for this run
                'debug_pcb': True
            }
            if _spouse_rebate_eligible:
                payroll_inputs_for_pcb['spouse_rebate_eligible'] = True
            
            print(f"📊 YTD Data being used for PCB calculation:")
            print(f"  📈 Accumulated Gross: RM{ytd_data['accumulated_gross']:,.2f}")
            print(f"  💰 Accumulated EPF: RM{ytd_data['accumulated_epf']:,.2f}")
            print(f"  🏛️ Accumulated PCB: RM{ytd_data['accumulated_pcb']:,.2f}")
            print(f"  🎯 Other Reliefs Current: RM{payroll_inputs_for_pcb['other_reliefs_current']:,.2f}")
            
            # Calculate month/year for PCB calculation
            month_year = f"{payroll_dt.month:02d}/{payroll_dt.year}"
            
            # Use official LHDN PCB calculation — pass monthly gross, not taxable_income
            # Force-enable debug for PCB calc (disable by removing this line)
            tax_config['debug_pcb'] = True
            # Optional: debug input snapshot
            if tax_config.get('debug_pcb') or employee.get('debug_pcb'):
                _debug_dump_pcb_inputs(payroll_inputs_for_pcb, gross_salary, epf_employee, tax_config, month_year)

            pcb = calculate_lhdn_pcb_official(
                payroll_inputs_for_pcb,
                gross_salary,    # Monthly gross salary (Y1)
                epf_employee,    # Monthly EPF contribution (K1)
                tax_config,      # Tax configuration with rates and rebates
                month_year       # Current month/year
            )

            print(f"🇲🇾 Step 6 - PCB (LHDN Official): RM{pcb:.2f} (on monthly gross RM{gross_salary:.2f})")
            
            # Step 7: Apply Unpaid Leave Deduction (AFTER all statutory contributions calculated)
            salary_after_unpaid_leave = gross_salary - total_unpaid_deduction
            print(f"🇲🇾 Step 7 - After Unpaid Leave: RM{salary_after_unpaid_leave:.2f} (Unpaid deduction: RM{total_unpaid_deduction:.2f})")
            
            # Calculate additional deductions based on employee settings
            sip_deduction = 0.0
            if employee.get("sip_participation") == "Yes":
                sip_type = employee.get("sip_type", "None")
                sip_amount_rate = employee.get("sip_amount_rate", 0.0)
                if sip_amount_rate is not None:
                    try:
                        sip_amount_rate = float(sip_amount_rate)
                        if sip_type == "Fixed Amount":
                            sip_deduction = sip_amount_rate
                        elif sip_type == "Percentage":
                            sip_deduction = gross_salary * (sip_amount_rate / 100)
                    except (ValueError, TypeError):
                        print(f"DEBUG: Invalid sip_amount_rate for {employee_text_id}: {sip_amount_rate}")
            
            additional_epf_deduction = 0.0
            if employee.get("additional_epf_enabled") == "Yes":
                epf_amount = employee.get("additional_epf_amount", 0.0)
                if epf_amount is not None:
                    try:
                        additional_epf_deduction = float(epf_amount)
                    except (ValueError, TypeError):
                        print(f"DEBUG: Invalid additional_epf_amount for {employee_text_id}: {epf_amount}")
            
            prs_deduction = 0.0
            if employee.get("prs_participation") == "Yes":
                prs_amount = employee.get("prs_amount", 0.0)
                if prs_amount is not None:
                    try:
                        prs_deduction = float(prs_amount)
                    except (ValueError, TypeError):
                        print(f"DEBUG: Invalid prs_amount for {employee_text_id}: {prs_amount}")
            
            # Insurance and medical premiums
            try:
                insurance_premium = float(employee.get("insurance_premium", 0.0) or 0.0)
            except (ValueError, TypeError):
                print(f"DEBUG: Invalid insurance_premium for {employee_text_id}: {employee.get('insurance_premium')}")
                insurance_premium = 0.0
                
            try:
                medical_premium = float(employee.get("medical_premium", 0.0) or 0.0)
            except (ValueError, TypeError):
                print(f"DEBUG: Invalid medical_premium for {employee_text_id}: {employee.get('medical_premium')}")
                medical_premium = 0.0
                
            try:
                other_deductions = float(employee.get("other_deductions_amount", 0.0) or 0.0)
            except (ValueError, TypeError):
                print(f"DEBUG: Invalid other_deductions_amount for {employee_text_id}: {employee.get('other_deductions_amount')}")
                other_deductions = 0.0
            
            # Step 8: Calculate other deductions and final net salary
            # Net Salary = Gross Salary - Unpaid Leave - All Deductions
            # IMPORTANT: Only cash monthly deductions reduce net pay. Exclude LP1 fields used for PCB (other_reliefs_monthly, socso_eis_lp1_monthly).
            cash_md = 0.0
            try:
                if isinstance(monthly_deductions, dict):
                    cash_md = float(monthly_deductions.get('zakat_monthly', 0.0) or 0.0) \
                              + float(monthly_deductions.get('other_deductions_amount', 0.0) or 0.0)
            except Exception:
                cash_md = 0.0

            total_statutory_and_other_deductions = (
                epf_employee + socso_employee + eis_employee + pcb +
                sip_deduction + additional_epf_deduction + prs_deduction +
                insurance_premium + medical_premium + other_deductions +
                cash_md
            )
            net_salary = salary_after_unpaid_leave - total_statutory_and_other_deductions
            
            print(f"🇲🇾 Step 8 - Final Net Salary Calculation:")
            print(f"   Gross Salary: RM{gross_salary:.2f}")
            print(f"   Statutory Contributions on Basic Salary:")
            print(f"     - EPF Employee: RM{epf_employee:.2f}")
            print(f"     - SOCSO Employee: RM{socso_employee:.2f}")
            print(f"     - EIS Employee: RM{eis_employee:.2f}")
            print(f"     - PCB: RM{pcb:.2f}")
            print(f"   Unpaid Leave Deduction: RM{total_unpaid_deduction:.2f}")
            print(f"   Other Deductions: RM{sip_deduction + additional_epf_deduction + prs_deduction + insurance_premium + medical_premium + other_deductions:.2f}")
            try:
                print(f"   Monthly Deductions (cash to subtract): RM{cash_md:.2f} (zakat + other_deductions_amount). Excluded LP1 fields from net pay.")
            except Exception:
                pass
            print(f"   Final Net Salary: RM{net_salary:.2f}")

        # Persist monthly deductions row for this period (zakat + base LP1 only)
            try:
                md_payload = {
                    'zakat_monthly': float(_current_month_zakat or 0.0),
            'other_reliefs_monthly': float((monthly_deductions or {}).get('other_reliefs_monthly', 0.0) if isinstance(monthly_deductions, dict) else 0.0),
                }
                if isinstance(monthly_deductions, dict):
                    if 'religious_travel_monthly' in monthly_deductions:
                        md_payload['religious_travel_monthly'] = float(monthly_deductions.get('religious_travel_monthly') or 0.0)
                    if 'other_deductions_amount' in monthly_deductions:
                        md_payload['other_deductions_amount'] = float(monthly_deductions.get('other_deductions_amount') or 0.0)
                upsert_monthly_deductions(employee_uuid, payroll_year, payroll_month, md_payload)
            except Exception as _pmd:
                print(f"DEBUG: Upsert payroll_monthly_deductions (run_payroll) failed: {_pmd}")

            print(f"DEBUG: Payroll for {employee_text_id} - wage={wage}, epf_employee={epf_employee}, epf_employer={epf_employer}")

            # Derive previous-month YTD snapshot for SOCSO/EIS if table had no row
            try:
                if (ytd_data.get('accumulated_socso', 0.0) == 0.0 and ytd_data.get('accumulated_eis', 0.0) == 0.0):
                    # Sum prior payroll_runs strictly before this payroll_date (parse text dates robustly)
                    pr_sum = supabase.table('payroll_runs').select('socso_employee, eis_employee, payroll_date, created_at') \
                        .eq('employee_id', employee_uuid).execute()
                    if pr_sum and pr_sum.data:
                        _socso_ytd = 0.0
                        _eis_ytd = 0.0
                        monthly_latest_se: dict = {}
                        for r in pr_sum.data:
                            try:
                                _pd = str(r.get('payroll_date') or '')
                                _pdt = _parse_any_date(_pd)
                                if not _pdt:
                                    continue
                                if _pdt.year != payroll_dt.year or _pdt.month >= payroll_dt.month:
                                    continue
                                key = (_pdt.year, _pdt.month)
                                prev = monthly_latest_se.get(key)
                                cur_created = _parse_any_date(str(r.get('created_at') or ''))
                                if prev is None:
                                    monthly_latest_se[key] = (r, cur_created)
                                else:
                                    prev_created = prev[1]
                                    if not prev_created or (cur_created and cur_created > prev_created):
                                        monthly_latest_se[key] = (r, cur_created)
                            except Exception:
                                continue
                        for (yy, mm), (r, _c) in monthly_latest_se.items():
                            _socso_ytd += float(r.get('socso_employee', 0) or 0)
                            _eis_ytd += float(r.get('eis_employee', 0) or 0)
                        ytd_data['accumulated_socso'] = _socso_ytd
                        ytd_data['accumulated_eis'] = _eis_ytd
            except Exception as _sum_se:
                print(f"DEBUG: Fallback sum SOCSO/EIS YTD failed: {_sum_se}")

            # Cap snapshot metrics for auditing
            try:
                # EPF relief cap
                try:
                    relief_cfg = load_tax_relief_max_configuration() or {}
                    epf_cap = float(relief_cfg.get('epf_shared_subcap') or 4000.0)
                except Exception:
                    epf_cap = 4000.0
                epf_used_ytd = float(min(float(ytd_data.get('accumulated_epf', 0.0) or 0.0), epf_cap))
                epf_remaining = max(0.0, epf_cap - epf_used_ytd)
            except Exception:
                epf_cap, epf_used_ytd, epf_remaining = 4000.0, 0.0, 4000.0

            try:
                b20_cap = float(socso_eis_annual_cap or 350.0)
                b20_used_ytd = float(ytd_lp1_claimed or 0.0)
                b20_remaining = max(0.0, b20_cap - b20_used_ytd)
            except Exception:
                b20_cap, b20_used_ytd, b20_remaining = 350.0, 0.0, 350.0

            payroll = {
                "employee_id": employee_uuid,  # Use UUID for foreign key
                "payroll_date": payroll_date,
                "gross_salary": gross_salary,
                "allowances": allowances,
                "epf_employee": epf_employee,
                "epf_employer": epf_employer,
                "socso_employee": socso_employee,
                "socso_employer": socso_employer,
                "eis_employee": eis_employee,
                "eis_employer": eis_employer,
                "pcb": pcb,
                "net_salary": net_salary,
                "bonus": employee_bonus,  # Use actual bonus amount
                "sip_deduction": sip_deduction,
                "additional_epf_deduction": additional_epf_deduction,
                "prs_deduction": prs_deduction,
                "insurance_premium": insurance_premium,
                "medical_premium": medical_premium,
                "other_deductions": other_deductions,
                "unpaid_leave_days": unpaid_days,
                "unpaid_leave_deduction": total_unpaid_deduction,
                # YTD snapshot columns (as of previous month) for audit/payslip
                "ytd_as_of_year": (_prev_year if '_prev_year' in locals() else (payroll_year if payroll_month > 1 else payroll_year - 1)),
                "ytd_as_of_month": (_prev_month if '_prev_month' in locals() else (12 if payroll_month == 1 else payroll_month - 1)),
                "accumulated_gross_salary_ytd": float((ytd_data or {}).get('accumulated_gross', 0.0)) if 'ytd_data' in locals() else 0.0,
                "accumulated_net_salary_ytd": 0.0,
                "accumulated_basic_salary_ytd": 0.0,
                "accumulated_allowances_ytd": 0.0,
                "accumulated_overtime_ytd": 0.0,
                "accumulated_bonus_ytd": 0.0,
                "accumulated_epf_employee_ytd": float((ytd_data or {}).get('accumulated_epf', 0.0)) if 'ytd_data' in locals() else 0.0,
                "accumulated_socso_employee_ytd": float((ytd_data or {}).get('accumulated_socso', 0.0)) if 'ytd_data' in locals() else 0.0,
                "accumulated_eis_employee_ytd": float((ytd_data or {}).get('accumulated_eis', 0.0)) if 'ytd_data' in locals() else 0.0,
                "accumulated_pcb_ytd": float((ytd_data or {}).get('accumulated_pcb', 0.0)) if 'ytd_data' in locals() else 0.0,
                "accumulated_zakat_ytd": float((ytd_data or {}).get('accumulated_zakat', 0.0)) if 'ytd_data' in locals() else 0.0,
                "accumulated_tax_reliefs_ytd": float((ytd_data or {}).get('accumulated_other_reliefs', 0.0)) if 'ytd_data' in locals() else 0.0,
                "created_at": datetime.now(KL_TZ).isoformat()
            }
            # Conditionally include new cap snapshot columns only if present in DB
            try:
                if _probe_column_exists('payroll_runs', 'epf_relief_cap_annual'):
                    payroll.update({
                        "epf_relief_cap_annual": epf_cap,
                        "epf_relief_used_ytd": epf_used_ytd,
                        "epf_relief_remaining": epf_remaining,
                    })
                if _probe_column_exists('payroll_runs', 'socso_eis_lp1_cap_annual'):
                    payroll.update({
                        "socso_eis_lp1_cap_annual": b20_cap,
                        "socso_eis_lp1_claimed_ytd": b20_used_ytd,
                        "socso_eis_lp1_remaining": b20_remaining,
                    })
            except Exception:
                # If probe fails, skip adding optional columns to avoid insert errors
                pass
            payroll_runs.append(payroll)

        # Debug: Check what we're about to insert
        print(f"DEBUG: About to insert {len(payroll_runs)} payroll records")
        if payroll_runs:
            print(f"DEBUG: First payroll record employee_id: {payroll_runs[0].get('employee_id')} (type: {type(payroll_runs[0].get('employee_id'))})")
            print(f"DEBUG: First payroll record keys: {list(payroll_runs[0].keys())}")

        # Insert payroll data into the database
        try:
            response = supabase.table("payroll_runs").insert(payroll_runs).execute()
            if not response.data:
                print("DEBUG: Failed to insert payroll runs - no data returned")
                return False
        except Exception as insert_error:
            print(f"DEBUG: Error inserting payroll runs: {insert_error}")
            # If it's a UUID error, it might be a data type issue
            if "uuid" in str(insert_error).lower():
                print("DEBUG: UUID error detected - checking employee ID formats")
                for i, payroll in enumerate(payroll_runs):
                    print(f"DEBUG: Payroll {i}: employee_id={payroll.get('employee_id')} (type: {type(payroll.get('employee_id'))})")
            return False

        print(f"DEBUG: Payroll processed for {len(payroll_runs)} employees on {payroll_date}")

        # NEW: Upsert YTD accumulated data for current month so next month's PCB sees correct previous-month totals
        try:
            for pr in payroll_runs:
                try:
                    # Parse payroll date to get year/month
                    _pd = str(pr.get('payroll_date') or '')
                    _pdt = _parse_any_date(_pd)
                    if not _pdt:
                        continue
                    _year = int(_pdt.year)
                    _month = int(_pdt.month)

                    # Resolve employee email from UUID id
                    emp_email = None
                    try:
                        er = (
                            supabase.table('employees')
                            .select('email')
                            .eq('id', pr.get('employee_id'))
                            .limit(1)
                            .execute()
                        )
                        if er and getattr(er, 'data', None):
                            emp_email = (er.data[0].get('email') or '').lower()
                    except Exception:
                        emp_email = None
                    if not emp_email:
                        continue

                    # Previous-month snapshot carried on the payroll row
                    prev_gross = float(pr.get('accumulated_gross_salary_ytd', 0.0) or 0.0)
                    prev_epf = float(pr.get('accumulated_epf_employee_ytd', 0.0) or 0.0)
                    prev_pcb = float(pr.get('accumulated_pcb_ytd', 0.0) or 0.0)
                    prev_zakat = float(pr.get('accumulated_zakat_ytd', 0.0) or 0.0)
                    prev_socso = float(pr.get('accumulated_socso_employee_ytd', 0.0) or 0.0)
                    prev_eis = float(pr.get('accumulated_eis_employee_ytd', 0.0) or 0.0)

                    # Current month statutory and tax values
                    cur_gross = float(pr.get('gross_salary', 0.0) or 0.0)
                    cur_epf = float(pr.get('epf_employee', 0.0) or 0.0)
                    cur_pcb = float(pr.get('pcb', 0.0) or 0.0)
                    cur_socso = float(pr.get('socso_employee', 0.0) or 0.0)
                    cur_eis = float(pr.get('eis_employee', 0.0) or 0.0)

                    # Pull zakat for this month from payroll_monthly_deductions if available
                    cur_zakat = 0.0
                    try:
                        md = (
                            supabase.table('payroll_monthly_deductions')
                            .select('zakat_monthly')
                            .eq('employee_id', pr.get('employee_id'))
                            .eq('year', _year)
                            .eq('month', _month)
                            .limit(1)
                            .execute()
                        )
                        if md and getattr(md, 'data', None):
                            cur_zakat = float(md.data[0].get('zakat_monthly') or 0.0)
                    except Exception:
                        cur_zakat = 0.0

                    updated = {
                        'employee_email': emp_email,
                        'year': _year,
                        'month': _month,
                        # Accumulated up to and including current month
                        'accumulated_gross_salary_ytd': round(prev_gross + cur_gross, 2),
                        'accumulated_epf_employee_ytd': round(prev_epf + cur_epf, 2),
                        'accumulated_pcb_ytd': round(prev_pcb + cur_pcb, 2),
                        'accumulated_zakat_ytd': round(prev_zakat + cur_zakat, 2),
                        'accumulated_socso_employee_ytd': round(prev_socso + cur_socso, 2),
                        'accumulated_eis_employee_ytd': round(prev_eis + cur_eis, 2),
                        # Current month context for audit
                        'current_month_gross_salary': round(cur_gross, 2),
                        'current_month_epf_employee': round(cur_epf, 2),
                        'current_month_pcb_calculated': round(cur_pcb, 2),
                        'current_month_zakat': round(cur_zakat, 2),
                        'updated_at': datetime.now(pytz.UTC).isoformat(),
                    }

                    # Upsert: update if row exists, else insert
                    try:
                        exists = (
                            supabase.table('payroll_ytd_accumulated')
                            .select('id')
                            .eq('employee_email', emp_email)
                            .eq('year', _year)
                            .eq('month', _month)
                            .limit(1)
                            .execute()
                        )
                        if exists and getattr(exists, 'data', None):
                            supabase.table('payroll_ytd_accumulated').update(updated).eq('id', exists.data[0]['id']).execute()
                        else:
                            # Ensure created_at on insert
                            updated['created_at'] = datetime.now(pytz.UTC).isoformat()
                            supabase.table('payroll_ytd_accumulated').insert(updated).execute()
                    except Exception as _yup:
                        print(f"DEBUG: YTD upsert failed for {emp_email} {_year}/{_month}: {_yup}")
                except Exception as _per_emp:
                    print(f"DEBUG: Skipping YTD upsert for one payroll row due to error: {_per_emp}")
        except Exception as _yerr:
            print(f"DEBUG: Error while upserting YTD after payroll: {_yerr}")

        return True
    except Exception as e:
        print(f"DEBUG: Error running payroll: {str(e)}")
        return False
    
def update_statutory_rates(rates: Dict) -> bool:
    try:
        rates["updated_at"] = datetime.now(KL_TZ).isoformat()
        existing = supabase.table("statutory_rates").select("id").limit(1).execute().data
        if existing:
            response = supabase.table("statutory_rates").update(rates).eq("id", existing[0]["id"]).execute()
            print(f"DEBUG: Statutory rates updated for id {existing[0]['id']}")
        else:
            rates["id"] = str(uuid.uuid4())
            response = supabase.table("statutory_rates").insert(rates).execute()
            print("DEBUG: Statutory rates inserted")
        return True if response.data else False
    except Exception as e:
        print(f"DEBUG: Error updating statutory rates: {str(e)}")
        return False

def get_payroll_runs(email=None):
    try:
        print(f"DEBUG: Fetching payroll runs for email: {email}")
        query = supabase.table("payroll_runs").select("*")
        if email:
            # First check if user exists and get their role
            user = supabase.table("user_logins").select("role").eq("email", email.lower()).execute().data
            print(f"DEBUG: User data for {email}: {user}")
            if not user:
                print(f"DEBUG: No user found for {email}")
                return []
            
            # If not admin, filter by employee email
            if user[0]["role"] != "admin":
                employee = supabase.table("employees").select("id").eq("email", email.lower()).execute().data
                print(f"DEBUG: Employee data for {email}: {employee}")
                if employee:
                    query = query.eq("employee_id", employee[0]["id"])  # Use UUID 'id' field
                else:
                    print(f"DEBUG: No employee found for {email}")
                    return []
        # Order by payroll_date (YYYY-MM-DD text ordering works lexicographically) and created_at if present
        try:
            query = query.order('payroll_date', desc=True)
        except Exception:
            pass
        records = query.execute().data
        print(f"DEBUG: Fetched {len(records)} payroll records")
        
        # Add employee data to each record
        for record in records:
            # Get employee info using UUID 'id' field
            employee = supabase.table("employees").select("*").eq("id", record["employee_id"]).execute().data
            if employee:
                record["employee"] = employee[0]
            
            # Skip payslip lookup since the table might not exist
            record["payslip_url"] = ""
            
        return records
    except Exception as e:
        print(f"DEBUG: Error fetching payroll runs: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def upload_resume(file_path: str, employee_id: str) -> Optional[str]:
    try:
        if not os.path.exists(file_path):
            print(f"DEBUG: File does not exist: {file_path}")
            return None
        file_name = f"{employee_id}_resume.pdf"
        subfolder = "resumes"
        full_path = f"{subfolder}/{file_name}"
        response = supabase.table("employees").select("resume_url").eq("employee_id", employee_id).execute()
        if response.data and response.data[0].get("resume_url"):
            old_resume = response.data[0]["resume_url"]
            if old_resume:
                old_path = old_resume.replace(f"https://wxaerkdmpxriveyknfov.supabase.co/storage/v1/object/public/employees.doc/", "")
                supabase.storage.from_("employees.doc").remove([old_path])
                print(f"DEBUG: Deleted old resume: {old_path}")
        with open(file_path, "rb") as f:
            response = supabase.storage.from_("employees.doc").upload(
                path=full_path,
                file=f,
                file_options={"content-type": "application/pdf"}
            )
        if hasattr(response, 'path') and response.path == full_path:
            public_url = supabase.storage.from_("employees.doc").get_public_url(full_path)
            supabase.table("employees").update({"resume_url": public_url}).eq("employee_id", employee_id).execute()
            print(f"DEBUG: Resume uploaded successfully, public URL: {public_url}")
            return public_url
        else:
            print(f"DEBUG: Resume upload failed for {full_path}")
            return None
    except Exception as e:
        print(f"DEBUG: Error uploading resume: {str(e)}")
        return None


def get_individual_employee_leave_balance(employee_email, year=None):
    """Get individual employee leave balance from database"""
    try:
        if year is None:
            year = datetime.now().year
            
        print(f"DEBUG: Getting leave balance for {employee_email} (year: {year})")
        
        # Get employee_id for leave balance lookup
        employee_id = None
        employee_response = supabase.table("employees").select(
            "employee_id, date_joined, employment_type"
        ).eq("email", employee_email).eq("status", "Active").execute()
        
        if not employee_response.data:
            print(f"DEBUG: No active employee found for {employee_email}")
            return {"annual_entitlement": 0, "used_days": 0, "carried_forward": 0, "remaining_days": 0, "total_available": 0, "years_of_service": 0.0}
        
        employee = employee_response.data[0]
        employee_id = employee['employee_id']
        
        # Calculate base entitlement based on cumulative years of service
        years_of_service = 0.0
        base_entitlement = 14
        try:
            from core.employee_service import calculate_cumulative_service
            cum = calculate_cumulative_service(employee_id)
            if cum and cum.get('days', 0) > 0:
                years_of_service = cum.get('years', 0.0)
            else:
                # fallback to single date_joined field
                try:
                    date_joined = datetime.strptime(employee['date_joined'], '%Y-%m-%d').date()
                    years_of_service = (datetime.now().date() - date_joined).days / 365.25
                except Exception:
                    years_of_service = 0.0

            # Malaysian labor law: 8 days for < 2 years, 12 days for 2-5 years, 16+ days for 5+ years
            if years_of_service < 2:
                base_entitlement = 8
            elif years_of_service < 5:
                base_entitlement = 12
            else:
                base_entitlement = 16
        except Exception:
            base_entitlement = 14  # Default
            years_of_service = 0.0
        
        # Get actual leave balance from database
        balance_response = supabase.table("leave_balances").select(
            "annual_entitlement, used_days, carried_forward"
        ).eq("employee_id", employee_id).eq("year", year).execute()
        
        if balance_response.data:
            # Use database values
            balance_data = balance_response.data[0]
            annual_entitlement = balance_data.get('annual_entitlement', base_entitlement)
            used_days = balance_data.get('used_days', 0)
            carried_forward = balance_data.get('carried_forward', 0)
        else:
            # Create new balance record with calculated values
            annual_entitlement = base_entitlement
            used_days = 0
            carried_forward = 0
            
            # Insert the balance record
            try:
                supabase.table("leave_balances").insert({
                    "employee_id": employee_id,
                    "year": year,
                    "annual_entitlement": annual_entitlement,
                    "used_days": used_days,
                    "carried_forward": carried_forward
                }).execute()
                print(f"DEBUG: Created leave balance record for {employee_email} year {year}")
            except Exception as insert_error:
                print(f"DEBUG: Failed to create leave balance record: {insert_error}")
        
        remaining_days = annual_entitlement + carried_forward - used_days
        total_available = annual_entitlement + carried_forward
        
        return {
            "annual_entitlement": annual_entitlement,
            "used_days": used_days,
            "carried_forward": carried_forward,
            "remaining_days": max(0, remaining_days),
            "total_available": total_available,
            "years_of_service": years_of_service  # Add this for GUI display
        }
        
    except Exception as e:
        print(f"DEBUG: Error getting leave balance: {str(e)}")
        return {"annual_entitlement": 14, "used_days": 0, "carried_forward": 0, "remaining_days": 14, "total_available": 14, "years_of_service": 0.0}


def get_individual_employee_sick_leave_balance(employee_email, year=None):
    """Get individual employee sick leave balance from database"""
    try:
        if year is None:
            year = datetime.now().year
            
        print(f"DEBUG: Getting sick leave balance for {employee_email} (year: {year})")
        
        # Get employee_id for sick leave balance lookup
        employee_id = None
        employee_response = supabase.table("employees").select(
            "employee_id, date_joined, employment_type"
        ).eq("email", employee_email).eq("status", "Active").execute()
        
        if not employee_response.data:
            print(f"DEBUG: No active employee found for {employee_email}")
            return {
                "sick_days_entitlement": 0, "used_sick_days": 0, 
                "hospitalization_days_entitlement": 0, "used_hospitalization_days": 0
            }
        
        employee = employee_response.data[0]
        employee_id = employee['employee_id']
        
        # Calculate base entitlement based on cumulative years of service
        years_of_service = 0.0
        try:
            from core.employee_service import calculate_cumulative_service
            cum = calculate_cumulative_service(employee_id)
            if cum and cum.get('days', 0) > 0:
                years_of_service = cum.get('years', 0.0)
            else:
                try:
                    date_joined = datetime.strptime(employee['date_joined'], '%Y-%m-%d').date()
                    years_of_service = (datetime.now().date() - date_joined).days / 365.25
                except Exception:
                    years_of_service = 0.0

            # Malaysian labor law: Sick leave entitlement based on service years
            if years_of_service < 2:
                sick_entitlement = 14
                hosp_entitlement = 60
            elif years_of_service < 5:
                sick_entitlement = 18
                hosp_entitlement = 60
            else:
                sick_entitlement = 22
                hosp_entitlement = 60
        except Exception:
            sick_entitlement = 14  # Default
            hosp_entitlement = 60  # Default
            years_of_service = 0.0
        
        # Get actual sick leave balance from database
        balance_response = supabase.table("sick_leave_balances").select(
            "sick_days_entitlement, hospitalization_days_entitlement, used_sick_days, used_hospitalization_days"
        ).eq("employee_id", employee_id).eq("year", year).execute()
        
        if balance_response.data:
            # Use database values
            balance_data = balance_response.data[0]
            sick_days_entitlement = balance_data.get('sick_days_entitlement', sick_entitlement)
            hosp_days_entitlement = balance_data.get('hospitalization_days_entitlement', hosp_entitlement)
            used_sick_days = balance_data.get('used_sick_days', 0)
            used_hosp_days = balance_data.get('used_hospitalization_days', 0)
        else:
            # Create new balance record with calculated values
            sick_days_entitlement = sick_entitlement
            hosp_days_entitlement = hosp_entitlement
            used_sick_days = 0
            used_hosp_days = 0
            
            # Insert the balance record
            try:
                supabase.table("sick_leave_balances").insert({
                    "employee_id": employee_id,
                    "year": year,
                    "sick_days_entitlement": sick_days_entitlement,
                    "hospitalization_days_entitlement": hosp_days_entitlement,
                    "used_sick_days": used_sick_days,
                    "used_hospitalization_days": used_hosp_days
                }).execute()
                print(f"DEBUG: Created sick leave balance record for {employee_email} year {year}")
            except Exception as insert_error:
                print(f"DEBUG: Failed to create sick leave balance record: {insert_error}")
        
        return {
            "sick_days_entitlement": sick_days_entitlement,
            "used_sick_days": used_sick_days,
            "hospitalization_days_entitlement": hosp_days_entitlement,
            "used_hospitalization_days": used_hosp_days,
            "remaining_sick_days": max(0, sick_days_entitlement - used_sick_days),
            "remaining_hospitalization_days": max(0, hosp_days_entitlement - used_hosp_days),
            "years_of_service": years_of_service
        }
        
    except Exception as e:
        print(f"DEBUG: Error getting sick leave balance: {str(e)}")
        return {
            "sick_days_entitlement": 14, "used_sick_days": 0,
            "hospitalization_days_entitlement": 60, "used_hospitalization_days": 0,
            "remaining_sick_days": 14, "remaining_hospitalization_days": 60,
            "years_of_service": 0.0
        }


def calculate_working_days(start_date, end_date, state: Optional[str] = None, include_observances: Optional[bool] = None, include_national: Optional[bool] = None):
    """Calculate leave days between two dates using Malaysia calendar rules.

    Preferred approach:
    1. Use workalendar.Malaysia to check public holidays and weekend rules.
    2. If workalendar not available, fall back to the `holidays` package for Malaysia.
    3. Include an optional Hijri-converter check for Islamic holidays if needed.

    The function counts all calendar days between start_date and end_date (inclusive)
    except days that are public holidays or weekend days as determined by the calendar.
    """
    try:
        from datetime import datetime, timedelta
        # Normalize inputs
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        # Determine working days using the centralized holidays service (Calendarific + overrides)
        try:
            from core.holidays_service import get_holidays_for_year, canonical_state_name
            # We'll build a per-year holiday map first, then compute working days
            current = start_date
            # Determine include flags from saved calendar UI prefs if not explicitly provided
            try:
                if include_observances is None or include_national is None or state is None:
                    try:
                        prefs = get_calendar_ui_prefs(None) or {}
                        if include_observances is None:
                            include_observances = bool(prefs.get('show_observances', True))
                        if include_national is None:
                            include_national = bool(prefs.get('show_national', True))
                        # If caller didn't pass a state, try to default to saved calendar prefs
                        if state is None:
                            pref_state = prefs.get('state')
                            if pref_state and isinstance(pref_state, str):
                                ps = pref_state.strip()
                                if ps and ps.lower() != 'all malaysia':
                                    state = ps
                    except Exception:
                        # fallback defaults
                        if include_observances is None:
                            include_observances = True
                        if include_national is None:
                            include_national = True

                # request holidays for every year in the range; pass state and flags
                from datetime import timedelta
                years = set()
                current = start_date
                while current <= end_date:
                    years.add(current.year)
                    current += timedelta(days=1)

                # Normalize state label to canonical form for holiday/weekend logic
                try:
                    state = canonical_state_name(state)
                except Exception:
                    pass

                holidays_by_year = {}
                debug_holidays = os.getenv('HRMS_DEBUG_HOLIDAYS', '0') == '1'
                for y in years:
                    try:
                        hs, details = get_holidays_for_year(y, state=state, include_national=include_national, include_observances=include_observances)
                        holidays_by_year[y] = hs or set()
                        # Only print verbose holiday details when explicitly enabled
                        if debug_holidays:
                            print(f"DEBUG: holidays for year {y} (state={state}, include_national={include_national}, include_observances={include_observances}): count={len(holidays_by_year[y])}")
                            if len(holidays_by_year[y]) <= 50:
                                for d in sorted(list(holidays_by_year[y])):
                                    try:
                                        reason = details.get(d.isoformat(), '') if hasattr(d, 'isoformat') else details.get(str(d), '')
                                    except Exception:
                                        reason = ''
                                    print(f"DEBUG:  - {d} -> {reason}")
                    except Exception as _herr:
                        if debug_holidays:
                            print(f"DEBUG: Error fetching holidays for year {y}: {_herr}")
                        holidays_by_year[y] = set()
            except Exception:
                # If service fails, fallback to treating no holidays but keep structure
                holidays_by_year = {}

            # Compute working days (Mon-Fri excluding holidays) using holidays_by_year
            # Weekend mapping by state (Fri-Sat for Johor, Kedah, Kelantan, Terengganu; Sat-Sun otherwise)
            fri_sat_states = {"Johor", "Kedah", "Kelantan", "Terengganu"}
            weekend_days = {4, 5} if (state in fri_sat_states) else {5, 6}

            working_days = 0
            current = start_date
            while current <= end_date:
                try:
                    hs_for_year = holidays_by_year.get(current.year, set())
                    if (current.weekday() not in weekend_days) and (current not in hs_for_year):
                        working_days += 1
                except Exception:
                    # On unexpected errors, be conservative and count as working weekday
                    if current.weekday() not in weekend_days:
                        working_days += 1
                current += timedelta(days=1)
            if os.getenv('HRMS_DEBUG_HOLIDAYS', '0') == '1':
                print(f"DEBUG: holidays_service result: {working_days} working days between {start_date} and {end_date} (state={state}, include_national={include_national}, include_observances={include_observances})")
            return working_days
        except Exception:
            # Final fallback: count all calendar days inclusive
            total_days = (end_date - start_date).days + 1
            print(f"DEBUG: fallback calendar days (service missing): {total_days} between {start_date} and {end_date}")
            return total_days
    except Exception as e:
        print(f"DEBUG: Error calculating working days: {str(e)}")
        return 1

def get_employee_leave_balances(year):
    """Get all employee leave balances for a given year"""
    try:
        # Get all active employees
        employees_response = supabase.table("employees").select(
            "id, employee_id, email, full_name, department, employment_type, date_joined"
        ).eq("status", "Active").execute()
        
        if not employees_response.data:
            return []
        
        balances = []
        for employee in employees_response.data:
            try:
                # Get individual balance for this employee
                balance = get_individual_employee_leave_balance(employee['email'], year)
                if balance:
                    balance.update({
                        'id': employee['id'],
                        'employee_id': employee['employee_id'],
                        'email': employee['email'],
                        'full_name': employee['full_name'],
                        'department': employee['department'],
                        'employment_type': employee['employment_type']
                    })
                    balances.append(balance)
            except Exception as e:
                print(f"DEBUG: Error getting balance for {employee['email']}: {str(e)}")
                continue
        
        return balances
    except Exception as e:
        print(f"DEBUG: Error in get_employee_leave_balances: {str(e)}")
        return []

def update_employee_leave_balance(employee_id, year, adjustment_data=None, **kwargs):
    """Update employee leave balance.

    Backwards-compatible wrapper: callers may pass a single dict as the third
    argument (adjustment_data) or pass keyword args (e.g. annual_entitlement=...).
    """
    try:
        # Normalize adjustments into a dict
        if adjustment_data is None:
            adjustments = dict(kwargs or {})
        elif isinstance(adjustment_data, dict):
            # merge kwargs into adjustment_data if both provided
            adjustments = dict(adjustment_data)
            adjustments.update(kwargs or {})
        else:
            adjustments = {'value': adjustment_data}

        print(f"DEBUG: Update leave balance called for {employee_id}, year {year}")
        print(f"DEBUG: Adjustment data: {adjustments}")

        # Allow callers to pass either employee_id (UUID) or email
        emp_id = employee_id
        try:
            # heuristics: if the identifier looks like an email, resolve to employee_id
            if isinstance(emp_id, str) and '@' in emp_id and not emp_id.startswith('00000000'):
                resp = supabase.table('employees').select('employee_id').eq('email', emp_id).limit(1).execute()
                if not resp or not getattr(resp, 'data', None):
                    print(f"DEBUG: Employee not found for email {emp_id}")
                    return False
                emp_id = resp.data[0].get('employee_id')

        except Exception:
            pass

        if not emp_id:
            print("DEBUG: No employee_id resolved")
            return False

        # Build payload for leave_balances upsert/update. Only include known columns to avoid PGRST errors.
        payload = {}
        # integer fields we commonly support
        for fld in ['annual_entitlement', 'used_days', 'carried_forward']:
            if fld in adjustments:
                try:
                    payload[fld] = int(adjustments.get(fld) or 0)
                except Exception:
                    try:
                        payload[fld] = int(float(adjustments.get(fld) or 0))
                    except Exception:
                        payload[fld] = 0

        # optional audit fields
        if 'adjustment_notes' in adjustments:
            payload['adjustment_notes'] = adjustments.get('adjustment_notes')
        if 'adjusted_by' in adjustments:
            payload['adjusted_by'] = adjustments.get('adjusted_by')

        # timestamps
        try:
            payload['updated_at'] = datetime.now(KL_TZ).isoformat()
        except Exception:
            payload['updated_at'] = datetime.now().isoformat()

        # Check if leave_balances table exists
        if not _probe_table_exists('leave_balances'):
            print('DEBUG: leave_balances table not present; cannot persist adjustments')
            return False

        # Find existing balance for employee/year
        existing = supabase.table('leave_balances').select('*').eq('employee_id', emp_id).eq('year', int(year)).limit(1).execute()
        if existing and getattr(existing, 'data', None):
            rec = existing.data[0]
            try:
                # Merge with existing values where payload keys not provided
                to_update = dict(payload)
                # Only update columns that exist in DB schema to avoid errors
                # Try update
                res = supabase.table('leave_balances').update(to_update).eq('id', rec.get('id')).execute()
                return bool(res and getattr(res, 'data', None))
            except Exception as e:
                print(f"DEBUG: Error updating leave_balances row: {e}")
                return False
        else:
            # Create new leave_balances row
            try:
                insert_payload = {
                    'employee_id': emp_id,
                    'year': int(year),
                    'annual_entitlement': int(payload.get('annual_entitlement', 0)),
                    'used_days': int(payload.get('used_days', 0)),
                    'carried_forward': int(payload.get('carried_forward', 0)),
                    'created_at': datetime.now(KL_TZ).isoformat() if 'KL_TZ' in globals() else datetime.now().isoformat(),
                    'updated_at': payload.get('updated_at')
                }
                # include optional audit columns if present in payload
                if 'adjustment_notes' in payload:
                    insert_payload['adjustment_notes'] = payload.get('adjustment_notes')
                if 'adjusted_by' in payload:
                    insert_payload['adjusted_by'] = payload.get('adjusted_by')

                res = supabase.table('leave_balances').insert(insert_payload).execute()
                return bool(res and getattr(res, 'data', None))
            except Exception as e:
                print(f"DEBUG: Error inserting leave_balances row: {e}")
                return False

    except Exception as e:
        print(f"DEBUG: Error updating leave balance: {str(e)}")
        return False

def update_employee_sick_leave_balance(employee_id, year, adjustment_data=None, **kwargs):
    """Create or update an employee's sick/hospitalization leave balance.

    Accepts either a single dict (adjustment_data) or keyword arguments.
    Supported fields:
        - sick_days_entitlement (int)
        - hospitalization_days_entitlement (int)
        - used_sick_days (float; supports half-day .5 increments)
        - used_hospitalization_days (float)
        - adjustment_notes (str)
        - adjusted_by (str)

    Caller may pass employee_id (UUID) OR employee email; email will be resolved
    to employee_id for persistence.
    """
    try:
        # Normalize adjustments
        if adjustment_data is None:
            adjustments = dict(kwargs or {})
        elif isinstance(adjustment_data, dict):
            adjustments = dict(adjustment_data)
            adjustments.update(kwargs or {})
        else:
            adjustments = {'value': adjustment_data}

        print(f"DEBUG: Update sick leave balance called for {employee_id}, year {year}")
        print(f"DEBUG: Sick adjustment data: {adjustments}")

        emp_id = employee_id
        try:
            if isinstance(emp_id, str) and '@' in emp_id and not emp_id.startswith('00000000'):
                resp = supabase.table('employees').select('employee_id').eq('email', emp_id).limit(1).execute()
                if not resp or not getattr(resp, 'data', None):
                    print(f"DEBUG: Employee not found for email {emp_id}")
                    return False
                emp_id = resp.data[0].get('employee_id')
        except Exception as e:
            print(f"DEBUG: Email resolution failed (non-fatal): {e}")

        if not emp_id:
            print("DEBUG: No employee_id resolved (sick leave update)")
            return False

        if not _probe_table_exists('sick_leave_balances'):
            print('DEBUG: sick_leave_balances table missing; cannot update sick leave balance')
            return False

        # Build payload with safe casting
        payload = {}
        int_fields = ['sick_days_entitlement', 'hospitalization_days_entitlement']
        float_fields = ['used_sick_days', 'used_hospitalization_days']

        for fld in int_fields:
            if fld in adjustments:
                try:
                    payload[fld] = int(adjustments.get(fld) or 0)
                except Exception:
                    try:
                        payload[fld] = int(float(adjustments.get(fld) or 0))
                    except Exception:
                        payload[fld] = 0

        for fld in float_fields:
            if fld in adjustments:
                try:
                    val = adjustments.get(fld)
                    if val is None or val == '':
                        payload[fld] = 0.0
                    else:
                        payload[fld] = float(val)
                except Exception:
                    payload[fld] = 0.0

        # Optional audit fields
        if 'adjustment_notes' in adjustments:
            payload['adjustment_notes'] = adjustments.get('adjustment_notes')
        if 'adjusted_by' in adjustments:
            payload['adjusted_by'] = adjustments.get('adjusted_by')

        # Timestamp
        try:
            payload['updated_at'] = datetime.now(KL_TZ).isoformat()
        except Exception:
            payload['updated_at'] = datetime.now().isoformat()

        # Fetch existing record
        existing = supabase.table('sick_leave_balances').select('*').eq('employee_id', emp_id).eq('year', int(year)).limit(1).execute()
        if existing and getattr(existing, 'data', None):
            rec = existing.data[0]
            try:
                to_update = dict(payload)
                # Business rule: warn (log) if used > entitlement after change
                try:
                    if 'sick_days_entitlement' in to_update and float(rec.get('used_sick_days', 0)) > to_update['sick_days_entitlement']:
                        print(f"WARN: used_sick_days {rec.get('used_sick_days')} exceeds new sick_days_entitlement {to_update['sick_days_entitlement']}")
                    if 'hospitalization_days_entitlement' in to_update and float(rec.get('used_hospitalization_days', 0)) > to_update['hospitalization_days_entitlement']:
                        print(f"WARN: used_hospitalization_days {rec.get('used_hospitalization_days')} exceeds new hospitalization_days_entitlement {to_update['hospitalization_days_entitlement']}")
                except Exception:
                    pass
                res = supabase.table('sick_leave_balances').update(to_update).eq('id', rec.get('id')).execute()
                return bool(res and getattr(res, 'data', None))
            except Exception as e:
                print(f"DEBUG: Error updating sick_leave_balances row: {e}")
                return False
        else:
            # Insert new record
            try:
                insert_payload = {
                    'employee_id': emp_id,
                    'year': int(year),
                    'sick_days_entitlement': int(payload.get('sick_days_entitlement', 0)),
                    'hospitalization_days_entitlement': int(payload.get('hospitalization_days_entitlement', 0)),
                    'used_sick_days': float(payload.get('used_sick_days', 0.0)),
                    'used_hospitalization_days': float(payload.get('used_hospitalization_days', 0.0)),
                    'created_at': datetime.now(KL_TZ).isoformat() if 'KL_TZ' in globals() else datetime.now().isoformat(),
                    'updated_at': payload.get('updated_at')
                }
                if 'adjustment_notes' in payload:
                    insert_payload['adjustment_notes'] = payload.get('adjustment_notes')
                if 'adjusted_by' in payload:
                    insert_payload['adjusted_by'] = payload.get('adjusted_by')
                res = supabase.table('sick_leave_balances').insert(insert_payload).execute()
                return bool(res and getattr(res, 'data', None))
            except Exception as e:
                print(f"DEBUG: Error inserting sick_leave_balances row: {e}")
                return False
    except Exception as e:
        print(f"DEBUG: Unhandled error in update_employee_sick_leave_balance: {e}")
        return False

def get_employee_sick_leave_balances(year):
    """Get all employee sick leave balances for a given year"""
    try:
        # Get all active employees
        employees_response = supabase.table("employees").select(
            "id, employee_id, email, full_name, department, employment_type, date_joined"
        ).eq("status", "Active").execute()
        
        if not employees_response.data:
            return []
        
        balances = []
        for employee in employees_response.data:
            try:
                # Get individual sick leave balance for this employee
                balance = get_individual_employee_sick_leave_balance(employee['email'], year)
                if balance:
                    balance.update({
                        'id': employee['id'],
                        'employee_id': employee['employee_id'],
                        'email': employee['email'],
                        'full_name': employee['full_name'],
                        'department': employee['department'],
                        'employment_type': employee['employment_type']
                    })
                    balances.append(balance)
            except Exception as e:
                print(f"DEBUG: Error getting sick leave balance for {employee['email']}: {str(e)}")
                continue
        
        return balances
    except Exception as e:
        print(f"DEBUG: Error in get_employee_sick_leave_balances: {str(e)}")
        return []


def process_year_end_carry_forward(year: int, rules: Dict[str, Any]) -> bool:
    """Process year-end carry forward for all active employees according to rules.

    rules expects:
      - max_days: int (maximum days to carry)
      - expiry_months: int (months after which carried days expire)
      - applies_to: optional filter (e.g., 'Full-time')

    Returns True if processing attempted; False on unrecoverable errors.
    """
    try:
        # Validate rules
        max_days = int(rules.get('max_days', 10))
        expiry_months = int(rules.get('expiry_months', 6))

        if not _probe_table_exists('leave_balances'):
            print('DEBUG: leave_balances table missing; cannot process carry forward')
            return False

        # Fetch current year balances and active employees
        # We'll move remaining balance into carried_forward for next year (year+1)
        current_resp = supabase.table('leave_balances').select('id, employee_id, year, annual_entitlement, used_days, carried_forward').eq('year', int(year)).execute()
        balances = current_resp.data if current_resp and getattr(current_resp, 'data', None) else []

        for b in balances:
            try:
                emp_id = b.get('employee_id')
                annual = int(b.get('annual_entitlement') or 0)
                used = int(b.get('used_days') or 0)
                current_cf = int(b.get('carried_forward') or 0)

                remaining = max(0, annual + current_cf - used)
                to_carry = min(max_days, remaining)

                # Upsert into next year's record
                next_year = int(year) + 1
                existing_next = supabase.table('leave_balances').select('id, carried_forward, annual_entitlement, used_days').eq('employee_id', emp_id).eq('year', next_year).limit(1).execute()
                if existing_next and getattr(existing_next, 'data', None):
                    rec = existing_next.data[0]
                    new_cf = int(rec.get('carried_forward') or 0) + to_carry
                    try:
                        supabase.table('leave_balances').update({'carried_forward': new_cf, 'updated_at': datetime.now(KL_TZ).isoformat()}).eq('id', rec.get('id')).execute()
                    except Exception:
                        try:
                            supabase.table('leave_balances').update({'carried_forward': new_cf}).eq('id', rec.get('id')).execute()
                        except Exception as _u_e:
                            print(f"DEBUG: Failed to update carry-forward for {emp_id} next_year {next_year}: {_u_e}")
                            continue
                else:
                    # Create next year record with default entitlement if known, else 0
                    try:
                        # Derive next year entitlement by copying current annual_entitlement
                        supabase.table('leave_balances').insert({
                            'employee_id': emp_id,
                            'year': next_year,
                            'annual_entitlement': annual,
                            'used_days': 0,
                            'carried_forward': to_carry,
                            'created_at': datetime.now(KL_TZ).isoformat(),
                            'updated_at': datetime.now(KL_TZ).isoformat()
                        }).execute()
                    except Exception:
                        # Try without timestamps if columns missing
                        try:
                            supabase.table('leave_balances').insert({
                                'employee_id': emp_id,
                                'year': next_year,
                                'annual_entitlement': annual,
                                'used_days': 0,
                                'carried_forward': to_carry
                            }).execute()
                        except Exception as _inner_e:
                            # Log and continue with next record
                            print(f"DEBUG: Failed to insert carry-forward for {emp_id} next_year {next_year}: {_inner_e}")
                            continue

            except Exception as e:
                # Error while processing this employee's balance; log and continue
                try:
                    print(f"DEBUG: Error processing carry-forward for {b.get('employee_id')}: {e}")
                except Exception:
                    print(f"DEBUG: Error processing carry-forward: {e}")
                continue

        print('DEBUG: Year-end carry forward processing completed')
        return True
    except Exception as e:
        print(f"DEBUG: Error in process_year_end_carry_forward: {e}")
        return False


def set_carried_forward_for_all(next_year: int, days: int, applies_to: Optional[str] = None) -> bool:
    """Set carried_forward = days for all active employees for next_year.

    If `applies_to` is provided, it can be used to filter by employment_type (e.g., 'Full-time').
    Returns True on success.
    """
    try:
        if not _probe_table_exists('leave_balances'):
            print('DEBUG: leave_balances table missing; cannot set carried forward for all')
            return False

        # Build employee query (include is_intern flag so we can exclude interns cleanly)
        q = supabase.table('employees').select('employee_id, employment_type, is_intern').eq('status', 'Active')
        employees_resp = q.execute()
        employees = employees_resp.data if employees_resp and getattr(employees_resp, 'data', None) else []

        for emp in employees:
            try:
                emp_id = emp.get('employee_id') or emp.get('id')
                # Handle special 'exclude_interns' token explicitly
                if applies_to:
                    if str(applies_to).lower() == 'exclude_interns':
                        # If employee is marked as intern, skip
                        if emp.get('is_intern'):
                            continue
                    else:
                        et = emp.get('employment_type', '') or ''
                        if str(applies_to).lower() not in str(et).lower():
                            continue

                # Upsert next year's leave_balances row
                existing = supabase.table('leave_balances').select('id').eq('employee_id', emp_id).eq('year', int(next_year)).limit(1).execute()
                payload = {'carried_forward': int(days), 'updated_at': datetime.now(KL_TZ).isoformat()}
                if existing and getattr(existing, 'data', None):
                    rec = existing.data[0]
                    supabase.table('leave_balances').update(payload).eq('id', rec.get('id')).execute()
                else:
                    # Insert with minimal fields; set annual_entitlement to 0 if unknown
                    try:
                        supabase.table('leave_balances').insert({
                            'employee_id': emp_id,
                            'year': int(next_year),
                            'annual_entitlement': 0,
                            'used_days': 0,
                            'carried_forward': int(days),
                            'created_at': datetime.now(KL_TZ).isoformat(),
                            'updated_at': datetime.now(KL_TZ).isoformat()
                        }).execute()
                    except Exception:
                        supabase.table('leave_balances').insert({
                            'employee_id': emp_id,
                            'year': int(next_year),
                            'annual_entitlement': 0,
                            'used_days': 0,
                            'carried_forward': int(days)
                        }).execute()

            except Exception as e:
                print(f"DEBUG: Failed to set CF for employee {emp.get('employee_id')}: {e}")
                continue

        print(f"DEBUG: Set carried_forward={days} for all employees for {next_year}")
        return True

    except Exception as e:
        print(f"DEBUG: Error in set_carried_forward_for_all: {e}")
        return False


def get_leave_request_states(leave_request_id: str) -> list:
    """Return list of state strings associated with a leave_request_id."""
    try:
        if not _probe_table_exists('leave_request_states'):
            return []
        resp = supabase.table('leave_request_states').select('state').eq('leave_request_id', leave_request_id).execute()
        return [r.get('state') for r in (resp.data or [])]
    except Exception as e:
        print(f"DEBUG: Error fetching leave_request_states for {leave_request_id}: {e}")
        return []


def set_leave_request_states(leave_request_id: str, states: list) -> bool:
    """Replace existing states for a leave_request with the provided list."""
    try:
        if not _probe_table_exists('leave_request_states'):
            return False
        # Remove existing
        supabase.table('leave_request_states').delete().eq('leave_request_id', leave_request_id).execute()
        to_insert = []
        for st in (states or []):
            if st:
                to_insert.append({'leave_request_id': leave_request_id, 'state': st.strip()})
        if to_insert:
            supabase.table('leave_request_states').insert(to_insert).execute()
        return True
    except Exception as e:
        print(f"DEBUG: Error setting leave_request_states for {leave_request_id}: {e}")
        return False

def update_employee_sick_leave_balance(employee_id, year, adjustment_data):
    """Update employee sick leave balance - placeholder function"""
    try:
        print(f"DEBUG: Update sick leave balance called for {employee_id}, year {year}")
        print(f"DEBUG: Adjustment data: {adjustment_data}")
        # For now, return True as if update was successful
        # In future, this can be enhanced to use actual sick_leave_balances table
        return True
            
    except Exception as e:
        print(f"DEBUG: Error updating sick leave balance: {str(e)}")
        return False

# =============================================================================
# VARIABLE PERCENTAGE PAYROLL CONFIGURATION FUNCTIONS
# =============================================================================

def get_variable_percentage_config(config_name: str = "default") -> Optional[Dict]:
    """
    Retrieve variable percentage configuration from Supabase with enhanced SOCSO ACT support
    
    Expected table structure:
    - config_name (TEXT, PRIMARY KEY): Configuration identifier
    - epf_employee_rate_stage1 (DECIMAL): Employee EPF rate for under 60 (%)
    - epf_employer_rate_stage1 (DECIMAL): Employer EPF rate for under 60 (%)
    - epf_employee_rate_stage2 (DECIMAL): Employee EPF rate for 60-75 (%)
    - epf_employer_rate_stage2 (DECIMAL): Employer EPF rate for 60-75 (%)
    - socso_act4_employee_rate (DECIMAL): Employee SOCSO ACT 4 rate (under 60) (%)
    - socso_act4_employer_rate (DECIMAL): Employer SOCSO ACT 4 rate (under 60) (%)
    - socso_act800_employee_rate (DECIMAL): Employee SOCSO ACT 800 rate (under 60) (%)
    - socso_act800_employer_rate (DECIMAL): Employer SOCSO ACT 800 rate (under 60) (%)
    - eis_employee_rate (DECIMAL): Employee EIS rate (18-60 only) (%)
    - eis_employer_rate (DECIMAL): Employer EIS rate (18-60 only) (%)
    - pcb_rate (DECIMAL): PCB tax rate (%)
    - created_at (TIMESTAMP): Configuration creation timestamp
    - updated_at (TIMESTAMP): Last update timestamp
    - description (TEXT): Configuration description
    """
    try:
        print(f"DEBUG: Getting variable percentage config: {config_name}")
        
        # Try to get configuration from Supabase
        response = supabase.table("variable_percentage_configs").select("*").eq("config_name", config_name).execute()
        
        if response.data:
            config = response.data[0]
            print(f"DEBUG: Retrieved config from database: {config}")
            
            # Handle both old format (combined SOCSO) and new format (ACT 4/800)
            config_dict = {
                'config_name': config.get('config_name', config_name),
                'epf_employee_rate_stage1': float(config.get('epf_employee_rate_stage1', 11.0)),
                'epf_employer_rate_stage1': float(config.get('epf_employer_rate_stage1', 13.0)),
                'epf_employee_rate_stage2': float(config.get('epf_employee_rate_stage2', 0.0)),
                'epf_employer_rate_stage2': float(config.get('epf_employer_rate_stage2', 4.0)),
                'eis_employee_rate': float(config.get('eis_employee_rate', 0.2)),
                'eis_employer_rate': float(config.get('eis_employer_rate', 0.2)),
                'pcb_rate': float(config.get('pcb_rate', 0.0)),
                'description': config.get('description', 'Default PERKESO-compliant rates with SOCSO ACT categorization'),
                'created_at': config.get('created_at'),
                'updated_at': config.get('updated_at')
            }

            # Pass-through any EPF Part fields if present (round-trip UI inputs)
            try:
                for k, v in config.items():
                    if isinstance(k, str) and k.startswith('epf_part_'):
                        try:
                            config_dict[k] = float(v) if v is not None else 0.0
                        except Exception:
                            # Keep as-is if not numeric
                            config_dict[k] = v
            except Exception:
                pass
            
            # Check if enhanced SOCSO columns exist
            if 'socso_act4_employee_rate' in config:
                # New format with ACT categorization
                config_dict.update({
                    'socso_act4_employee_rate': float(config.get('socso_act4_employee_rate', 0.5)),
                    'socso_act4_employer_rate': float(config.get('socso_act4_employer_rate', 1.25)),
                    'socso_act800_employee_rate': float(config.get('socso_act800_employee_rate', 0.0)),
                    'socso_act800_employer_rate': float(config.get('socso_act800_employer_rate', 0.5)),
                })
                # Calculate combined SOCSO rates for backward compatibility
                config_dict['socso_employee_rate'] = config_dict['socso_act4_employee_rate'] + config_dict['socso_act800_employee_rate']
                config_dict['socso_employer_rate'] = config_dict['socso_act4_employer_rate'] + config_dict['socso_act800_employer_rate']
            else:
                # Old format - split combined SOCSO rates into ACT categories
                socso_employee_total = float(config.get('socso_employee_rate', 0.5))
                socso_employer_total = float(config.get('socso_employer_rate', 1.75))
                
                config_dict.update({
                    'socso_employee_rate': socso_employee_total,
                    'socso_employer_rate': socso_employer_total,
                    # Split SOCSO rates (ACT 4 typically gets more allocation)
                    'socso_act4_employee_rate': socso_employee_total,  # Employee usually only pays ACT 4
                    'socso_act4_employer_rate': socso_employer_total * 0.714,  # ~71.4% to ACT 4
                    'socso_act800_employee_rate': 0.0,  # Typically no employee contribution to ACT 800
                    'socso_act800_employer_rate': socso_employer_total * 0.286,  # ~28.6% to ACT 800
                })
            
            return config_dict
        else:
            print(f"DEBUG: No config found in database, returning PERKESO default rates")
            # Return PERKESO-compliant default rates based on official schedule
            return get_perkeso_default_rates()
            
    except Exception as e:
        print(f"DEBUG: Error getting variable percentage config: {str(e)}")
        # Return PERKESO default rates as fallback
        return get_perkeso_default_rates()

def save_variable_percentage_config(config_data: Dict) -> bool:
    """
    Save variable percentage configuration to Supabase with enhanced SOCSO ACT support
    """
    try:
        print(f"DEBUG: Saving variable percentage config: {config_data}")
        
        config_name = config_data.get('config_name', 'default')
        current_time = datetime.now(KL_TZ).isoformat()
        
        # Determine available schema (stage-based vs combined) and build payload accordingly
        def col_exists(col: str) -> bool:
            try:
                return _probe_column_exists('variable_percentage_configs', col)
            except Exception:
                return False

        has_stage_cols = all(col_exists(c) for c in [
            'epf_employee_rate_stage1', 'epf_employer_rate_stage1',
            'epf_employee_rate_stage2', 'epf_employer_rate_stage2'
        ])

        # Base payload
        db_data = {
            'config_name': config_name,
            'eis_employee_rate': float(config_data.get('eis_employee_rate', 0.2)),
            'eis_employer_rate': float(config_data.get('eis_employer_rate', 0.2)),
            'description': config_data.get('description', 'Custom configuration'),
            'updated_at': current_time
        }

        # Only include pcb_rate if explicitly provided and column exists
        if 'pcb_rate' in config_data and col_exists('pcb_rate'):
            try:
                db_data['pcb_rate'] = float(config_data.get('pcb_rate'))
            except Exception:
                pass

        if has_stage_cols:
            db_data.update({
                'epf_employee_rate_stage1': float(config_data.get('epf_employee_rate_stage1', 11.0)),
                'epf_employer_rate_stage1': float(config_data.get('epf_employer_rate_stage1', 13.0)),
                'epf_employee_rate_stage2': float(config_data.get('epf_employee_rate_stage2', 0.0)),
                'epf_employer_rate_stage2': float(config_data.get('epf_employer_rate_stage2', 4.0)),
            })
        else:
            # Fall back to combined EPF columns if stage columns not present
            db_data.update({
                'epf_employee_rate': float(config_data.get('epf_employee_rate_stage1', config_data.get('epf_employee_rate', 11.0))),
                'epf_employer_rate': float(config_data.get('epf_employer_rate_stage1', config_data.get('epf_employer_rate', 13.0))),
            })
        
        # Handle SOCSO rates - support both old and new format
        if 'socso_act4_employee_rate' in config_data and col_exists('socso_act4_employee_rate'):
            # New format with ACT categorization
            db_data.update({
                'socso_act4_employee_rate': float(config_data.get('socso_act4_employee_rate', 0.5)),
                'socso_act4_employer_rate': float(config_data.get('socso_act4_employer_rate', 1.25)),
                'socso_act800_employee_rate': float(config_data.get('socso_act800_employee_rate', 0.0)),
                'socso_act800_employer_rate': float(config_data.get('socso_act800_employer_rate', 0.5)),
            })
            # Calculate combined rates for backward compatibility
            db_data['socso_employee_rate'] = db_data['socso_act4_employee_rate'] + db_data['socso_act800_employee_rate']
            db_data['socso_employer_rate'] = db_data['socso_act4_employer_rate'] + db_data['socso_act800_employer_rate']
        else:
            # Old format - save combined rates and try to split into ACT categories
            socso_employee_total = float(config_data.get('socso_employee_rate', 0.5))
            socso_employer_total = float(config_data.get('socso_employer_rate', 1.75))
            
            db_data.update({
                'socso_employee_rate': socso_employee_total,
                'socso_employer_rate': socso_employer_total,
            })
            
            # Try to add ACT categorization only if those columns exist
            if all(col_exists(c) for c in ['socso_act4_employee_rate','socso_act4_employer_rate','socso_act800_employee_rate','socso_act800_employer_rate']):
                db_data.update({
                    'socso_act4_employee_rate': socso_employee_total,  # Employee usually only pays ACT 4
                    'socso_act4_employer_rate': socso_employer_total * 0.714,  # ~71.4% to ACT 4
                    'socso_act800_employee_rate': 0.0,  # Typically no employee contribution to ACT 800
                    'socso_act800_employer_rate': socso_employer_total * 0.286,  # ~28.6% to ACT 800
                })
        
        # Include EPF Part fields explicitly if provided and columns exist
        for k, v in list(config_data.items()):
            if isinstance(k, str) and k.startswith('epf_part_') and col_exists(k):
                try:
                    db_data[k] = float(v)
                except Exception:
                    pass

        # Check if configuration already exists
        existing = supabase.table("variable_percentage_configs").select("config_name").eq("config_name", config_name).execute()

        # Filter out any keys for columns that don't exist to avoid PGRST204
        filtered = {k: v for k, v in db_data.items() if col_exists(k)}
        if existing.data:
            # Update existing configuration
            response = supabase.table("variable_percentage_configs").update(filtered).eq("config_name", config_name).execute()
            print(f"DEBUG: Updated existing config: {response}")
        else:
            # Insert new configuration
            if col_exists('created_at'):
                filtered['created_at'] = current_time
            response = supabase.table("variable_percentage_configs").insert(filtered).execute()
            print(f"DEBUG: Inserted new config: {response}")
        
        print(f"DEBUG: Successfully saved variable percentage config: {config_name}")
        return True
        
    except Exception as e:
        print(f"DEBUG: Error saving variable percentage config: {str(e)}")
        return False

def get_all_variable_percentage_configs() -> List[Dict]:
    """
    Get all available variable percentage configurations
    """
    try:
        print("DEBUG: Getting all variable percentage configs")
        
        response = supabase.table("variable_percentage_configs").select("*").order("created_at", desc=True).execute()
        
        if response.data:
            configs = []
            for config in response.data:
                configs.append({
                    'config_name': config.get('config_name', 'Unknown'),
                    'epf_employee_rate_stage1': float(config.get('epf_employee_rate_stage1', 11.0)),
                    'epf_employer_rate_stage1': float(config.get('epf_employer_rate_stage1', 13.0)),
                    'epf_employee_rate_stage2': float(config.get('epf_employee_rate_stage2', 0.0)),
                    'epf_employer_rate_stage2': float(config.get('epf_employer_rate_stage2', 4.0)),
                    'socso_employee_rate': float(config.get('socso_employee_rate', 0.5)),
                    'socso_employer_rate': float(config.get('socso_employer_rate', 1.75)),
                    'eis_employee_rate': float(config.get('eis_employee_rate', 0.2)),
                    'eis_employer_rate': float(config.get('eis_employer_rate', 0.2)),
                    'pcb_rate': float(config.get('pcb_rate', 0.0)),
                    'description': config.get('description', ''),
                    'created_at': config.get('created_at'),
                    'updated_at': config.get('updated_at')
                })
            
            print(f"DEBUG: Retrieved {len(configs)} configurations")
            return configs
        else:
            print("DEBUG: No configurations found in database")
            return []
            
    except Exception as e:
        print(f"DEBUG: Error getting all variable percentage configs: {str(e)}")
        return []

def delete_variable_percentage_config(config_name: str) -> bool:
    """
    Delete a variable percentage configuration
    """
    try:
        print(f"DEBUG: Deleting variable percentage config: {config_name}")
        
        # Prevent deletion of default config
        if config_name.lower() == 'default':
            print("DEBUG: Cannot delete default configuration")
            return False
        
        response = supabase.table("variable_percentage_configs").delete().eq("config_name", config_name).execute()
        
        print(f"DEBUG: Successfully deleted config: {config_name}")
        return True
        
    except Exception as e:
        print(f"DEBUG: Error deleting variable percentage config: {str(e)}")
        return False

def get_perkeso_default_rates() -> Dict:
    """
    Get PERKESO-compliant default rates based on official PERKESO website
    - SOCSO: First Category (Under 60) vs Second Category (60+)
    - EIS: Single rate structure (0.2% each, capped at RM6,000)
    """
    return {
        'config_name': 'default',
        'epf_employee_rate_stage1': 11.0,  # Malaysian employee contribution (under 60)
        'epf_employer_rate_stage1': 13.0,  # Malaysian employer contribution for salary ≤ RM5,000 (under 60)
        'epf_employee_rate_stage2': 0.0,   # Voluntary contribution for 60+ (default 0%)
        'epf_employer_rate_stage2': 4.0,   # Reduced employer rate for 60+ employees
        # SOCSO - Two categories (official PERKESO structure)
        'socso_first_employee_rate': 0.5,    # First Category (Under 60) - Employee
        'socso_first_employer_rate': 1.75,   # First Category (Under 60) - Employer
        'socso_second_employee_rate': 0.0,   # Second Category (60+) - Employee
        'socso_second_employer_rate': 1.25,  # Second Category (60+) - Employer
        # EIS - Single rate structure (official PERKESO)
        'eis_employee_rate': 0.2,            # EIS Employee rate (capped at RM6,000)
        'eis_employer_rate': 0.2,            # EIS Employer rate (capped at RM6,000)
        'pcb_rate': 0.0,                     # PCB varies by salary bracket, default to 0
        'description': 'Official PERKESO rates: SOCSO (First/Second Category) and EIS (0.4% total)',
        'created_at': datetime.now(KL_TZ).isoformat(),
        'updated_at': datetime.now(KL_TZ).isoformat()
    }

def get_kwsp_default_rates() -> Dict:
    """
    Get KWSP-compliant default rates based on official Third Schedule with age stages
    These rates are for Malaysian employees with proper age-based differentiation
    """
    return {
        'config_name': 'default',
        'epf_employee_rate_stage1': 11.0,  # Malaysian employee contribution (under 60)
        'epf_employer_rate_stage1': 13.0,  # Malaysian employer contribution for salary ≤ RM5,000 (under 60)
        'epf_employee_rate_stage2': 0.0,   # Voluntary contribution for 60+ (default 0%)
        'epf_employer_rate_stage2': 4.0,   # Reduced employer rate for 60+ employees
        'socso_employee_rate': 0.5,        # SOCSO employee contribution (under 60 only)
        'socso_employer_rate': 1.75,       # SOCSO employer contribution (under 60 only)
        'eis_employee_rate': 0.2,          # EIS employee contribution (18-60 only)
        'eis_employer_rate': 0.2,          # EIS employer contribution (18-60 only)
        'pcb_rate': 0.0,                   # PCB varies by salary bracket, default to 0
        'description': 'KWSP-compliant default rates with age-based EPF stages',
        'created_at': datetime.now(KL_TZ).isoformat(),
        'updated_at': datetime.now(KL_TZ).isoformat()
    }

def create_variable_percentage_table() -> bool:
    """
    Create the variable_percentage_configs table if it doesn't exist
    This function provides the SQL for manual table creation
    """
    sql_command = """
    CREATE TABLE IF NOT EXISTS variable_percentage_configs (
        config_name TEXT PRIMARY KEY,
        epf_employee_rate DECIMAL(5,2) NOT NULL DEFAULT 11.0,
        epf_employer_rate DECIMAL(5,2) NOT NULL DEFAULT 13.0,
        socso_employee_rate DECIMAL(5,2) NOT NULL DEFAULT 0.5,
        socso_employer_rate DECIMAL(5,2) NOT NULL DEFAULT 1.75,
        eis_employee_rate DECIMAL(5,2) NOT NULL DEFAULT 0.2,
        eis_employer_rate DECIMAL(5,2) NOT NULL DEFAULT 0.2,
        pcb_rate DECIMAL(5,2) NOT NULL DEFAULT 0.0,
        description TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Insert default KWSP-compliant configuration
    INSERT INTO variable_percentage_configs (
        config_name, epf_employee_rate, epf_employer_rate,
        socso_employee_rate, socso_employer_rate,
        eis_employee_rate, eis_employer_rate, pcb_rate, description
    ) VALUES (
        'default', 11.0, 13.0, 0.5, 1.75, 0.2, 0.2, 0.0,
        'KWSP-compliant default rates for Malaysian employees (salary ≤ RM5,000)'
    ) ON CONFLICT (config_name) DO NOTHING;
    """
    
    print("DEBUG: SQL command to create variable_percentage_configs table:")
    print(sql_command)
    print("\nPlease execute this SQL command in your Supabase SQL editor to create the table.")
    return True

# LHDN Tax Configuration Management Functions
def create_lhdn_tax_configs_table():
    """Create the comprehensive LHDN tax configurations table structure with all B1-B21 relief maximums"""
    sql_command = """
    -- Create comprehensive LHDN tax configurations table
    CREATE TABLE IF NOT EXISTS lhdn_tax_configs (
        id SERIAL PRIMARY KEY,
        config_name VARCHAR(100) UNIQUE NOT NULL,
        description TEXT,
        
        -- B1 & B14-B16: Personal & Family Reliefs
        b1_personal_relief_max DECIMAL(10, 2) DEFAULT 15000.00,
        b14_spouse_relief_max DECIMAL(10, 2) DEFAULT 4000.00,
        b15_disabled_spouse_relief_max DECIMAL(10, 2) DEFAULT 5000.00,
        b16_children_under_18_per_child DECIMAL(10, 2) DEFAULT 2000.00,
        b16_children_tertiary_per_child DECIMAL(10, 2) DEFAULT 8000.00,
        b16_children_disabled_per_child DECIMAL(10, 2) DEFAULT 8000.00,
        
        -- B2-B8: Health & Medical Reliefs
        b2_parent_medical_max DECIMAL(10, 2) DEFAULT 8000.00,
        b3_basic_support_equipment_max DECIMAL(10, 2) DEFAULT 6000.00,
        b4_individual_disability_max DECIMAL(10, 2) DEFAULT 6000.00,
        b6_medical_expenses_max DECIMAL(10, 2) DEFAULT 10000.00,
        b7_medical_checkup_max DECIMAL(10, 2) DEFAULT 1000.00,
        b8_child_learning_disability_max DECIMAL(10, 2) DEFAULT 4000.00,
        
        -- B5, B12-B13: Education & Childcare Reliefs
        b5_education_fees_max DECIMAL(10, 2) DEFAULT 7000.00,
        b12_childcare_fees_max DECIMAL(10, 2) DEFAULT 3000.00,
        b13_sspn_max DECIMAL(10, 2) DEFAULT 8000.00,
        
        -- B9-B11, B21: Lifestyle & Other Reliefs
        b9_basic_lifestyle_max DECIMAL(10, 2) DEFAULT 2500.00,
        b10_additional_lifestyle_max DECIMAL(10, 2) DEFAULT 1000.00,
        b11_breastfeeding_equipment_max DECIMAL(10, 2) DEFAULT 1000.00,
        b21_ev_charging_max DECIMAL(10, 2) DEFAULT 2500.00,
        
        -- B17-B20: Investment & Insurance Reliefs
        b17_epf_life_insurance_max DECIMAL(10, 2) DEFAULT 7000.00,
        b18_prs_annuity_max DECIMAL(10, 2) DEFAULT 3000.00,
        b19_education_medical_insurance_max DECIMAL(10, 2) DEFAULT 3000.00,
        b20_socso_eis_max DECIMAL(10, 2) DEFAULT 350.00,
        
        -- Tax Rebates
        rebate_individual_amount DECIMAL(10, 2) DEFAULT 400.00,
        rebate_spouse_amount DECIMAL(10, 2) DEFAULT 400.00,
        rebate_zakat_max DECIMAL(10, 2) DEFAULT 20000.00,
        rebate_religious_travel_max DECIMAL(10, 2) DEFAULT 3000.00,
        
        -- Legacy fields for backward compatibility
        personal_relief DECIMAL(10, 2) DEFAULT 9000.00,
        spouse_relief DECIMAL(10, 2) DEFAULT 4000.00,
        child_relief DECIMAL(10, 2) DEFAULT 2000.00,
        disabled_child_relief DECIMAL(10, 2) DEFAULT 8000.00,
        epf_relief_enabled BOOLEAN DEFAULT true,
        epf_relief_max DECIMAL(10, 2) DEFAULT 6000.00,
        is_resident BOOLEAN DEFAULT true,
        
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Create update trigger for updated_at
    CREATE OR REPLACE FUNCTION update_lhdn_tax_configs_updated_at()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    
    DROP TRIGGER IF EXISTS trigger_update_lhdn_tax_configs_updated_at ON lhdn_tax_configs;
    CREATE TRIGGER trigger_update_lhdn_tax_configs_updated_at
    BEFORE UPDATE ON lhdn_tax_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_lhdn_tax_configs_updated_at();
    
    -- Insert default LHDN 2025 configuration with all B1-B21 relief maximums
    INSERT INTO lhdn_tax_configs (
        config_name, description,
        -- B1 & B14-B16: Personal & Family
        b1_personal_relief_max, b14_spouse_relief_max, b15_disabled_spouse_relief_max,
        b16_children_under_18_per_child, b16_children_tertiary_per_child, b16_children_disabled_per_child,
        -- B2-B8: Health & Medical
        b2_parent_medical_max, b3_basic_support_equipment_max, b4_individual_disability_max,
        b6_medical_expenses_max, b7_medical_checkup_max, b8_child_learning_disability_max,
        -- B5, B12-B13: Education & Childcare
        b5_education_fees_max, b12_childcare_fees_max, b13_sspn_max,
        -- B9-B11, B21: Lifestyle & Other
        b9_basic_lifestyle_max, b10_additional_lifestyle_max, b11_breastfeeding_equipment_max, b21_ev_charging_max,
        -- B17-B20: Investment & Insurance
        b17_epf_life_insurance_max, b18_prs_annuity_max, b19_education_medical_insurance_max, b20_socso_eis_max,
        -- Rebates
        rebate_individual_amount, rebate_spouse_amount, rebate_zakat_max, rebate_religious_travel_max,
        -- Legacy fields
        personal_relief, spouse_relief, child_relief, disabled_child_relief, epf_relief_enabled, epf_relief_max, is_resident
    ) VALUES (
        'default', 'Official LHDN 2025 tax reliefs B1-B21 with all maximum amounts per HASIL regulations',
        -- B1 & B14-B16: Personal & Family
        15000.00, 4000.00, 5000.00, 2000.00, 8000.00, 8000.00,
        -- B2-B8: Health & Medical  
        8000.00, 6000.00, 6000.00, 10000.00, 1000.00, 4000.00,
        -- B5, B12-B13: Education & Childcare
        7000.00, 3000.00, 8000.00,
        -- B9-B11, B21: Lifestyle & Other
        2500.00, 1000.00, 1000.00, 2500.00,
        -- B17-B20: Investment & Insurance
        7000.00, 3000.00, 3000.00, 350.00,
        -- Rebates
        400.00, 400.00, 20000.00, 3000.00,
        -- Legacy fields
        9000.00, 4000.00, 2000.00, 8000.00, true, 6000.00, true
    ) ON CONFLICT (config_name) DO UPDATE SET
        description = EXCLUDED.description,
        b1_personal_relief_max = EXCLUDED.b1_personal_relief_max,
        b14_spouse_relief_max = EXCLUDED.b14_spouse_relief_max,
        b15_disabled_spouse_relief_max = EXCLUDED.b15_disabled_spouse_relief_max,
        b16_children_under_18_per_child = EXCLUDED.b16_children_under_18_per_child,
        b16_children_tertiary_per_child = EXCLUDED.b16_children_tertiary_per_child,
        b16_children_disabled_per_child = EXCLUDED.b16_children_disabled_per_child,
        b2_parent_medical_max = EXCLUDED.b2_parent_medical_max,
        b3_basic_support_equipment_max = EXCLUDED.b3_basic_support_equipment_max,
        b4_individual_disability_max = EXCLUDED.b4_individual_disability_max,
        b6_medical_expenses_max = EXCLUDED.b6_medical_expenses_max,
        b7_medical_checkup_max = EXCLUDED.b7_medical_checkup_max,
        b8_child_learning_disability_max = EXCLUDED.b8_child_learning_disability_max,
        b5_education_fees_max = EXCLUDED.b5_education_fees_max,
        b12_childcare_fees_max = EXCLUDED.b12_childcare_fees_max,
        b13_sspn_max = EXCLUDED.b13_sspn_max,
        b9_basic_lifestyle_max = EXCLUDED.b9_basic_lifestyle_max,
        b10_additional_lifestyle_max = EXCLUDED.b10_additional_lifestyle_max,
        b11_breastfeeding_equipment_max = EXCLUDED.b11_breastfeeding_equipment_max,
        b21_ev_charging_max = EXCLUDED.b21_ev_charging_max,
        b17_epf_life_insurance_max = EXCLUDED.b17_epf_life_insurance_max,
        b18_prs_annuity_max = EXCLUDED.b18_prs_annuity_max,
        b19_education_medical_insurance_max = EXCLUDED.b19_education_medical_insurance_max,
        b20_socso_eis_max = EXCLUDED.b20_socso_eis_max,
        rebate_individual_amount = EXCLUDED.rebate_individual_amount,
        rebate_spouse_amount = EXCLUDED.rebate_spouse_amount,
        rebate_zakat_max = EXCLUDED.rebate_zakat_max,
        rebate_religious_travel_max = EXCLUDED.rebate_religious_travel_max,
        updated_at = NOW();
    """

    
    print("DEBUG: SQL command to create lhdn_tax_configs table:")
    print(sql_command)
    print("\nIMPORTANT: Please execute this SQL command in your Supabase SQL editor to create the LHDN tax table.")
    print("After running the SQL, restart the application to test the November PCB calculation.")
    
    # Try to create a basic version of the table by attempting to insert minimal data
    # This may fail but will provide better error information
    try:
        print("DEBUG: Attempting to create basic lhdn_tax_configs table structure...")
        
        # Try to insert minimal default data to see if we can create the table
        basic_config = {
            "config_name": "default",
            "description": "Basic LHDN tax configuration",
            "personal_relief": 9000.0,
            "spouse_relief": 4000.0,
            "child_relief": 2000.0
        }
        
        result = supabase.table("lhdn_tax_configs").insert(basic_config).execute()
        print("DEBUG: Basic lhdn_tax_configs table created successfully!")
        return True
        
    except Exception as insert_error:
        print(f"DEBUG: Could not create table via insert: {insert_error}")
        print("DEBUG: You must manually run the SQL above in Supabase SQL editor.")
        return False

def save_lhdn_tax_config(config: Dict) -> bool:
    """Save LHDN tax configuration to database"""
    try:
        print(f"DEBUG: Saving LHDN tax config: {config['config_name']}")
        
        response = supabase.table("lhdn_tax_configs").upsert({
            "config_name": config["config_name"],
            "description": config.get("description", ""),
            "personal_relief": config.get("personal_relief", 9000.0),
            "spouse_relief": config.get("spouse_relief", 4000.0),
            "child_relief": config.get("child_relief", 2000.0),
            "disabled_child_relief": config.get("disabled_child_relief", 8000.0),
            "epf_relief_enabled": config.get("epf_relief_enabled", True),
            "epf_relief_max": config.get("epf_relief_max", 6000.0),
            "is_resident": config.get("is_resident", True)
        }).execute()
        
        print(f"DEBUG: LHDN tax config saved successfully: {response.data}")
        return True
        
    except Exception as e:
        print(f"DEBUG: Error saving LHDN tax config: {e}")
        return False

def get_lhdn_tax_config(config_name: str) -> Optional[Dict]:
    """Get LHDN tax configuration by name"""
    try:
        print(f"DEBUG: Getting LHDN tax config: {config_name}")
        
        response = supabase.table("lhdn_tax_configs").select("*").eq("config_name", config_name).execute()
        
        if response.data:
            print(f"DEBUG: Found LHDN tax config: {response.data[0]}")
            return response.data[0]
        else:
            print(f"DEBUG: LHDN tax config not found: {config_name}")
            return None
            
    except Exception as e:
        print(f"DEBUG: Error getting LHDN tax config: {e}")
        return None

def get_all_lhdn_tax_configs() -> List[Dict]:
    """Get all LHDN tax configurations"""
    try:
        print("DEBUG: Getting all LHDN tax configs")
        
        response = supabase.table("lhdn_tax_configs").select("*").order("config_name").execute()
        
        print(f"DEBUG: Found {len(response.data)} LHDN tax configs")
        return response.data
        
    except Exception as e:
        print(f"DEBUG: Error getting all LHDN tax configs: {e}")
        
        # If table doesn't exist, try to create it with minimal structure
        if "does not exist" in str(e).lower():
            print("DEBUG: Table doesn't exist, attempting to create basic structure...")
            try:
                # Create basic default config to initialize the table
                default_config = {
                    "config_name": "default",
                    "description": "Basic LHDN tax configuration",
                    "personal_relief": 9000.0,
                    "spouse_relief": 4000.0,
                    "child_relief": 2000.0,
                    "disabled_child_relief": 8000.0,
                    "epf_relief_enabled": True,
                    "epf_relief_max": 6000.0,
                    "is_resident": True
                }
                
                # This will auto-create the table with these fields in Supabase
                result = supabase.table("lhdn_tax_configs").insert(default_config).execute()
                print("DEBUG: Created basic lhdn_tax_configs table with default config")
                return [default_config]
                
            except Exception as create_error:
                print(f"DEBUG: Could not auto-create table: {create_error}")
                print("DEBUG: Please manually create the lhdn_tax_configs table in Supabase")
                
        return []

def delete_lhdn_tax_config(config_name: str) -> bool:
    """Delete LHDN tax configuration"""
    try:
        print(f"DEBUG: Deleting LHDN tax config: {config_name}")
        
        if config_name == 'default':
            print("DEBUG: Cannot delete default LHDN tax configuration")
            return False
        
        response = supabase.table("lhdn_tax_configs").delete().eq("config_name", config_name).execute()
        
        print(f"DEBUG: LHDN tax config deleted successfully")
        return True
        
    except Exception as e:
        print(f"DEBUG: Error deleting LHDN tax config: {e}")
        return False

def get_lhdn_default_tax_config() -> Dict:
    """Get LHDN default tax configuration with official 2025 rates"""
    return {
        'config_name': 'default',
        'description': 'Official LHDN 2025 tax reliefs and progressive rates',
        'personal_relief': 9000.0,  # RM9,000 personal relief
        'spouse_relief': 4000.0,    # RM4,000 spouse relief
        'child_relief': 2000.0,     # RM2,000 per child
        'disabled_child_relief': 8000.0,  # RM8,000 per disabled child
        'epf_relief_enabled': True,  # Enable EPF relief
        'epf_relief_max': 6000.0,   # RM6,000 EPF relief limit
        'is_resident': True         # Default to resident status
    }

# =============================================================================
# TAX CONFIGURATION TABLES
# =============================================================================

def save_tax_rates_configuration(config_data: Dict) -> bool:
    """Save minimal tax policy (non-resident rate, individual rebate) to Supabase"""
    try:
        # Prepare data for tax_rates_config table
        tax_rates_data = {
            'config_name': config_data.get('config_name', 'default'),
            'non_resident_rate': config_data.get('non_resident_rate', 30.0),
            'individual_tax_rebate': config_data.get('individual_tax_rebate', 400.0),
            # Optional new field (2025+): threshold for applying individual rebate
            'rebate_threshold': config_data.get('rebate_threshold', 35000.0),
            'created_at': datetime.now(KL_TZ).isoformat(),
            'is_active': True
        }
        
        # Check if configuration already exists
        existing = supabase.table("tax_rates_config").select("id").eq("config_name", tax_rates_data['config_name']).execute()
        
        try:
            if existing.data:
                # Update existing configuration
                result = supabase.table("tax_rates_config").update(tax_rates_data).eq("config_name", tax_rates_data['config_name']).execute()
            else:
                # Insert new configuration
                result = supabase.table("tax_rates_config").insert(tax_rates_data).execute()
        except Exception as _col_err:
            # Backward compatibility: retry without rebate_threshold if column not present yet
            print(f"DEBUG: tax_rates_config missing rebate_threshold? Retrying without it: {_col_err}")
            tax_rates_fallback = dict(tax_rates_data)
            tax_rates_fallback.pop('rebate_threshold', None)
            if existing.data:
                result = supabase.table("tax_rates_config").update(tax_rates_fallback).eq("config_name", tax_rates_fallback['config_name']).execute()
            else:
                result = supabase.table("tax_rates_config").insert(tax_rates_fallback).execute()
            
        return len(result.data) > 0
        
    except Exception as e:
        print(f"DEBUG: Error saving tax rates configuration: {e}")
        return False

def load_tax_rates_configuration(config_name: str = 'default') -> Optional[Dict]:
    """Load minimal tax policy (non-resident rate, individual rebate)."""
    try:
        result = supabase.table("tax_rates_config").select("*").eq("config_name", config_name).eq("is_active", True).execute()
        
        if result.data:
            return result.data[0]
        else:
            # Return default configuration if none found
            return get_default_tax_rates_config()
            
    except Exception as e:
        print(f"DEBUG: Error loading tax rates configuration: {e}")
        return get_default_tax_rates_config()

def save_tax_relief_max_configuration(config_data: Dict) -> bool:
    """Save tax relief maximum amounts configuration to Supabase"""
    try:
        # Prepare data for tax_relief_max_config table
        relief_config_data = {
            'config_name': config_data.get('config_name', 'default'),
            'personal_relief_max': config_data.get('personal_relief_max', 9000.0),
            'spouse_relief_max': config_data.get('spouse_relief_max', 4000.0),
            'child_relief_max': config_data.get('child_relief_max', 2000.0),
            'disabled_child_relief_max': config_data.get('disabled_child_relief_max', 8000.0),
            'parent_medical_max': config_data.get('parent_medical_max', 8000.0),
            'medical_treatment_max': config_data.get('medical_treatment_max', 10000.0),
            'serious_disease_max': config_data.get('serious_disease_max', 10000.0),
            'fertility_treatment_max': config_data.get('fertility_treatment_max', 5000.0),
            'vaccination_max': config_data.get('vaccination_max', 1000.0),
            'dental_treatment_max': config_data.get('dental_treatment_max', 1000.0),
            'health_screening_max': config_data.get('health_screening_max', 500.0),
            'child_learning_disability_max': config_data.get('child_learning_disability_max', 3000.0),
            'education_max': config_data.get('education_max', 8000.0),
            'skills_course_max': config_data.get('skills_course_max', 1000.0),
            'lifestyle_max': config_data.get('lifestyle_max', 2500.0),
            'sports_equipment_max': config_data.get('sports_equipment_max', 300.0),
            'gym_membership_max': config_data.get('gym_membership_max', 300.0),
            'checkup_vaccine_upper_limit': config_data.get('checkup_vaccine_upper_limit', 1000.0),
            'life_insurance_upper_limit': config_data.get('life_insurance_upper_limit', 3000.0),
            'epf_shared_subcap': config_data.get('epf_shared_subcap', 4000.0),
            'combined_epf_insurance_limit': config_data.get('combined_epf_insurance_limit', 7000.0),
            'created_at': datetime.now(KL_TZ).isoformat(),
            'is_active': True
        }
        
        # Check if configuration already exists
        existing = supabase.table("tax_relief_max_config").select("id").eq("config_name", relief_config_data['config_name']).execute()
        
        if existing.data:
            # Update existing configuration
            result = supabase.table("tax_relief_max_config").update(relief_config_data).eq("config_name", relief_config_data['config_name']).execute()
        else:
            # Insert new configuration
            result = supabase.table("tax_relief_max_config").insert(relief_config_data).execute()
            
        return len(result.data) > 0
        
    except Exception as e:
        print(f"DEBUG: Error saving tax relief max configuration: {e}")
        return False

def load_tax_relief_max_configuration(config_name: str = 'default') -> Optional[Dict]:
    """Load tax relief maximum amounts configuration from Supabase"""
    try:
        result = supabase.table("tax_relief_max_config").select("*").eq("config_name", config_name).eq("is_active", True).execute()
        
        if result.data:
            return result.data[0]
        else:
            # Return default configuration if none found
            return get_default_tax_relief_max_config()
            
    except Exception as e:
        print(f"DEBUG: Error loading tax relief max configuration: {e}")
        return get_default_tax_relief_max_config()

# -----------------------------------------------------------------------------
# Statutory ceilings (EPF/SOCSO/EIS) configuration helpers
# -----------------------------------------------------------------------------
def load_statutory_limits_configuration(config_name: str = 'default') -> Optional[Dict]:
    """Load active statutory limits (EPF/SOCSO/EIS ceilings) from Supabase or defaults."""
    try:
        res = supabase.table('statutory_limits_config').select('*').eq('config_name', config_name).eq('is_active', True).limit(1).execute()
        if res and res.data:
            return res.data[0]
        # Fallback defaults
        return {
            'config_name': 'default',
            'epf_ceiling': 6000.0,
            'socso_ceiling': 6000.0,
            'eis_ceiling': 6000.0,
            'is_active': True,
        }
    except Exception as e:
        print(f"DEBUG: Error loading statutory limits config: {e}")
        return None


def save_statutory_limits_configuration(config_data: Dict) -> bool:
    """Upsert statutory limits configuration and mark it active.

    Expected keys: config_name, epf_ceiling, socso_ceiling, eis_ceiling, is_active
    """
    try:
        if not isinstance(config_data, dict):
            raise ValueError('config_data must be a dict')
        payload = {
            'config_name': config_data.get('config_name', 'default'),
            'epf_ceiling': float(config_data.get('epf_ceiling', 6000.0) or 6000.0),
            'socso_ceiling': float(config_data.get('socso_ceiling', 6000.0) or 6000.0),
            'eis_ceiling': float(config_data.get('eis_ceiling', 6000.0) or 6000.0),
            'is_active': bool(config_data.get('is_active', True)),
        }
        supabase.table('statutory_limits_config').upsert(payload, on_conflict='config_name').execute()
        return True
    except Exception as e:
        print(f"DEBUG: Error saving statutory limits config: {e}")
        return False

# =============================================================================
# PAYROLL DATA TABLES
# =============================================================================

def save_payroll_information(payroll_data: Dict) -> bool:
    """Save payroll information to Supabase"""
    try:
        # Prepare data for payroll_information table
        payroll_info = {
            'employee_id': payroll_data.get('employee_id'),
            'employee_email': payroll_data.get('employee_email'),
            'employee_name': payroll_data.get('employee_name'),
            'month_year': payroll_data.get('month_year'),
            'basic_salary': payroll_data.get('basic_salary', 0.0),
            'allowances': payroll_data.get('allowances', {}),
            'overtime_pay': payroll_data.get('overtime_pay', 0.0),
            'commission': payroll_data.get('commission', 0.0),
            'bonus': payroll_data.get('bonus', 0.0),
            'gross_income': payroll_data.get('gross_income', 0.0),
            'epf_employee': payroll_data.get('epf_employee', 0.0),
            'epf_employer': payroll_data.get('epf_employer', 0.0),
            'socso_employee': payroll_data.get('socso_employee', 0.0),
            'socso_employer': payroll_data.get('socso_employer', 0.0),
            'eis_employee': payroll_data.get('eis_employee', 0.0),
            'eis_employer': payroll_data.get('eis_employer', 0.0),
            'pcb_tax': payroll_data.get('pcb_tax', 0.0),
            'monthly_deductions': payroll_data.get('monthly_deductions', {}),
            'annual_tax_reliefs': payroll_data.get('annual_tax_reliefs', {}),
            'other_deductions': payroll_data.get('other_deductions', {}),
            'total_deductions': payroll_data.get('total_deductions', 0.0),
            'net_salary': payroll_data.get('net_salary', 0.0),
            'tax_resident_status': payroll_data.get('tax_resident_status', 'Resident'),
            'created_at': datetime.now(KL_TZ).isoformat(),
            'created_by': payroll_data.get('created_by', 'system')
        }
        
        # Check if payroll for this employee and month already exists
        existing = supabase.table("payroll_information").select("id").eq("employee_id", payroll_info['employee_id']).eq("month_year", payroll_info['month_year']).execute()
        
        if existing.data:
            # Update existing payroll record
            result = supabase.table("payroll_information").update(payroll_info).eq("employee_id", payroll_info['employee_id']).eq("month_year", payroll_info['month_year']).execute()
        else:
            # Insert new payroll record
            result = supabase.table("payroll_information").insert(payroll_info).execute()
            
        return len(result.data) > 0
        
    except Exception as e:
        print(f"DEBUG: Error saving payroll information: {e}")
        return False

def load_payroll_information(employee_id: str, month_year: str) -> Optional[Dict]:
    """Load payroll information for specific employee and month"""
    try:
        result = supabase.table("payroll_information").select("*").eq("employee_id", employee_id).eq("month_year", month_year).execute()
        
        if result.data:
            return result.data[0]
        else:
            return None
            
    except Exception as e:
        print(f"DEBUG: Error loading payroll information: {e}")
        return None

def get_employee_payroll_history(employee_id: str) -> List[Dict]:
    """Get payroll history for an employee"""
    try:
        result = supabase.table("payroll_information").select("*").eq("employee_id", employee_id).order("month_year", desc=True).execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        print(f"DEBUG: Error loading payroll history: {e}")
        return []

def get_all_payroll_records(month_year: str = None) -> List[Dict]:
    """Get all payroll records, optionally filtered by month/year"""
    try:
        query = supabase.table("payroll_information").select("*")
        
        if month_year:
            query = query.eq("month_year", month_year)
            
        result = query.order("created_at", desc=True).execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        print(f"DEBUG: Error loading payroll records: {e}")
        return []

# =============================================================================
# PAYSLIP GENERATION AND MANAGEMENT
# =============================================================================

def generate_payslip_pdf(payroll_data: Dict, output_path: str = None) -> Optional[str]:
    """Generate payslip PDF from payroll data"""
    try:
        if not output_path:
            # Generate filename based on employee and date
            employee_id = payroll_data.get('employee_id', 'unknown')
            month_year = payroll_data.get('month_year', 'unknown')
            output_path = f"Payslip_{employee_id}_{month_year.replace('/', '_')}.pdf"
        
        # Create PDF document
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Company header
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.darkblue,
            alignment=1  # Center
        )
        
        story.append(Paragraph("PAYSLIP", title_style))
        story.append(Spacer(1, 0.5*cm))
        
        # Employee information
        employee_info = [
            ['Employee ID:', payroll_data.get('employee_id', '')],
            ['Employee Name:', payroll_data.get('employee_name', '')],
            ['Month/Year:', payroll_data.get('month_year', '')],
            ['Tax Status:', payroll_data.get('tax_resident_status', 'Resident')]
        ]
        
        employee_table = Table(employee_info, colWidths=[4*cm, 8*cm])
        employee_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(employee_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Income details
        income_data = [
            ['INCOME', 'AMOUNT (RM)'],
            ['Basic Salary', f"{payroll_data.get('basic_salary', 0.0):,.2f}"],
            ['Overtime Pay', f"{payroll_data.get('overtime_pay', 0.0):,.2f}"],
            ['Commission', f"{payroll_data.get('commission', 0.0):,.2f}"],
            ['Bonus', f"{payroll_data.get('bonus', 0.0):,.2f}"],
            ['GROSS INCOME', f"{payroll_data.get('gross_income', 0.0):,.2f}"]
        ]
        
        # Add allowances if any
        allowances = payroll_data.get('allowances', {})
        if allowances:
            for allowance_name, amount in allowances.items():
                if amount > 0:
                    income_data.insert(-1, [allowance_name.replace('_', ' ').title(), f"{amount:,.2f}"])
        
        income_table = Table(income_data, colWidths=[8*cm, 4*cm])
        income_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(income_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Deductions details
        deductions_data = [
            ['DEDUCTIONS', 'AMOUNT (RM)'],
            ['EPF Employee', f"{payroll_data.get('epf_employee', 0.0):,.2f}"],
            ['SOCSO Employee', f"{payroll_data.get('socso_employee', 0.0):,.2f}"],
            ['EIS Employee', f"{payroll_data.get('eis_employee', 0.0):,.2f}"],
            ['PCB Tax', f"{payroll_data.get('pcb_tax', 0.0):,.2f}"]
        ]
        
        # Add monthly deductions
        monthly_deductions = payroll_data.get('monthly_deductions', {})
        if monthly_deductions:
            for deduction_name, amount in monthly_deductions.items():
                if amount > 0:
                    deductions_data.append([deduction_name.replace('_', ' ').title(), f"{amount:,.2f}"])
        
        # Add other deductions
        other_deductions = payroll_data.get('other_deductions', {})
        if other_deductions:
            for deduction_name, amount in other_deductions.items():
                if amount > 0:
                    deductions_data.append([deduction_name.replace('_', ' ').title(), f"{amount:,.2f}"])
        
        deductions_data.append(['TOTAL DEDUCTIONS', f"{payroll_data.get('total_deductions', 0.0):,.2f}"])
        
        deductions_table = Table(deductions_data, colWidths=[8*cm, 4*cm])
        deductions_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightpink),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(deductions_table)
        story.append(Spacer(1, 0.5*cm))
        
        # YTD Accumulated (as of previous month)
        try:
            ytd = payroll_data.get('ytd_accumulated') or {}
            if ytd:
                ytd_title = ParagraphStyle(
                    'YTDTitle', parent=styles['Heading2'], fontSize=12, textColor=colors.darkblue
                )
                story.append(Paragraph("YTD Accumulated (as of previous month)", ytd_title))
                story.append(Spacer(1, 0.2*cm))
                ytd_rows = [
                    ['Period', f"{int(ytd.get('as_of_month', 0)):02d}/{ytd.get('as_of_year', '')}"],
                    ['Gross (YTD)', f"{float(ytd.get('gross', 0.0)):,.2f}"],
                    ['EPF Employee (YTD)', f"{float(ytd.get('epf_employee', 0.0)):,.2f}"],
                    ['PCB (YTD)', f"{float(ytd.get('pcb', 0.0)):,.2f}"],
                    ['Zakat (YTD)', f"{float(ytd.get('zakat', 0.0)):,.2f}"],
                    ['Other Reliefs LP1 (YTD)', f"{float(ytd.get('other_reliefs', 0.0)):,.2f}"],
                ]
                ytd_table = Table(ytd_rows, colWidths=[8*cm, 4*cm])
                ytd_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(ytd_table)
                story.append(Spacer(1, 0.5*cm))
        except Exception as _ytd_pdf:
            print(f"DEBUG: Skipped YTD section in PDF: {_ytd_pdf}")

        # Net salary
        net_salary_data = [
            ['NET SALARY', f"RM {payroll_data.get('net_salary', 0.0):,.2f}"]
        ]
        
        net_salary_table = Table(net_salary_data, colWidths=[8*cm, 4*cm])
        net_salary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 2, colors.black)
        ]))
        
        story.append(net_salary_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Footer
        footer_text = f"Generated on: {datetime.now(KL_TZ).strftime('%d/%m/%Y %H:%M:%S')} (Malaysia Time)"
        story.append(Paragraph(footer_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        return output_path
        
    except Exception as e:
        print(f"DEBUG: Error generating payslip PDF: {e}")
        return None

def get_default_tax_rates_config() -> Dict:
    """Default tax policy fallback."""
    return {
        'config_name': 'default',
        'non_resident_rate': 30.0,
    'individual_tax_rebate': 400.0,
    'spouse_tax_rebate': 400.0,
    'rebate_threshold': 35000.0,
    }

def get_default_tax_relief_max_config() -> Dict:
    """Get default tax relief maximum amounts configuration"""
    return {
        'config_name': 'default',
        'personal_relief_max': 9000.0,
        'spouse_relief_max': 4000.0,
        'child_relief_max': 2000.0,
        'disabled_child_relief_max': 8000.0,
        'parent_medical_max': 8000.0,
        'medical_treatment_max': 10000.0,
        'serious_disease_max': 10000.0,
        'fertility_treatment_max': 5000.0,
        'vaccination_max': 1000.0,
        'dental_treatment_max': 1000.0,
        'health_screening_max': 500.0,
        'child_learning_disability_max': 3000.0,
        'education_max': 8000.0,
        'skills_course_max': 1000.0,
        'lifestyle_max': 2500.0,
        'sports_equipment_max': 300.0,
        'gym_membership_max': 300.0,
        'checkup_vaccine_upper_limit': 1000.0,
        'life_insurance_upper_limit': 3000.0,
        'epf_shared_subcap': 4000.0,
        'combined_epf_insurance_limit': 7000.0
    }

# =============================================================================
# OFFICIAL LHDN PCB CALCULATION FUNCTIONS
# =============================================================================

def _round_to_nearest_0_05(amount: float) -> float:
    """Round amount to the nearest 0.05 following sen rules (half-up).
    0.01/0.02 -> .00; 0.03/0.04 -> .05; 0.06/0.07 -> .05; 0.08/0.09 -> .10
    Safeguard: quantize to 2 d.p. first to avoid float artifacts affecting 0.05 steps.
    """
    try:
        d = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        # scale by 20 (1 / 0.05), round to nearest integer, scale back
        scaled = d * Decimal('20')
        return float(scaled.to_integral_value(rounding=ROUND_HALF_UP) / Decimal('20'))
    except Exception:
        return round(amount, 2)

def _round_up_to_0_05(amount: float) -> float:
    """Round amount UP to the next multiple of 0.05 (ceiling to 5 sen).
    Example: 2,676.31 -> 2,676.35; 2,676.30 stays 2,676.30.
    Safeguard: quantize to 2 d.p. first to avoid float artifacts (e.g., 0.35 -> 0.40).
    """
    try:
        d = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        # Multiply by 20 (1/0.05), ceiling to integer, divide back
        scaled = d * Decimal('20')
        return float(scaled.to_integral_value(rounding=ROUND_CEILING) / Decimal('20'))
    except Exception:
        import math as _m
        return (_m.ceil(round(float(amount), 2) * 20) / 20.0)

def _get_pcb_formula_options(tax_config: Dict, payroll_inputs: Dict) -> Dict[str, object]:
    """Return configurable PCB formula options with safe defaults.
    Options (read from env first, then tax_config, then defaults):
      - rounding_mode: 'ceiling_0_05' or 'nearest_0_05' (default: ceiling_0_05)
      - divisor_mode: 'n_plus_1' or 'n' (default: n_plus_1)
      - include_lp1_in_annual: bool (default: True)
    """
    try:
        env_round = os.getenv('HRMS_PCB_ROUNDING_MODE', '').strip().lower()
        env_divisor = os.getenv('HRMS_PCB_DIVISOR_MODE', '').strip().lower()
        env_lp1 = os.getenv('HRMS_PCB_INCLUDE_LP1_IN_ANNUAL', '').strip().lower()

        cfg_round = (tax_config or {}).get('rounding_mode') if isinstance(tax_config, dict) else None
        cfg_divisor = (tax_config or {}).get('divisor_mode') if isinstance(tax_config, dict) else None
        cfg_lp1 = (tax_config or {}).get('include_lp1_in_annual') if isinstance(tax_config, dict) else None

        rounding_mode = (env_round or cfg_round or 'ceiling_0_05')
        if rounding_mode not in ('ceiling_0_05', 'nearest_0_05'):
            rounding_mode = 'ceiling_0_05'

        divisor_mode = (env_divisor or cfg_divisor or 'n_plus_1')
        if divisor_mode not in ('n_plus_1', 'n'):
            divisor_mode = 'n_plus_1'

        if isinstance(cfg_lp1, bool):
            include_lp1_in_annual = cfg_lp1
        elif env_lp1 in ('true', '1', 'yes'):
            include_lp1_in_annual = True
        elif env_lp1 in ('false', '0', 'no'):
            include_lp1_in_annual = False
        else:
            include_lp1_in_annual = True

        return {
            'rounding_mode': rounding_mode,
            'divisor_mode': divisor_mode,
            'include_lp1_in_annual': include_lp1_in_annual,
        }
    except Exception:
        return {
            'rounding_mode': 'ceiling_0_05',
            'divisor_mode': 'n_plus_1',
            'include_lp1_in_annual': True,
        }

def calculate_lhdn_pcb_official(payroll_inputs: Dict, gross_monthly: float, epf_monthly: float, tax_config: Dict, month_year: str) -> float:
    """
    Calculate PCB using official LHDN formula:
    PCB = [((P-M) × R + B - (Z + X)) / (n+1)] - Zakat/Fi/Levi Bulan Semasa
    
    Where:
    P = Annual taxable income excluding bonus
    M = First amount of taxable income bracket
    R = Tax rate percentage  
    B = Tax amount on M after individual and spouse rebate
    Z = Accumulated Zakat/Fitrah/Levy paid (excluding current month)
    X = Accumulated PCB paid in previous months
    n = Remaining working months in year
    """
    try:
        # Extract payroll period
        # Month/year parsing (MM/YYYY)
        try:
            current_month = int(str(month_year).split('/')[-2] if '/' in str(month_year) else str(month_year))
        except Exception:
            from datetime import datetime as _dt
            current_month = _dt.now(KL_TZ).month

        # Helper to coerce to float safely
        def _f(v, d=0.0):
            try:
                return float(v)
            except Exception:
                return float(d)

        # Accumulated inputs (YTD)
        accumulated_gross = _f(payroll_inputs.get('accumulated_gross_ytd', 0.0))
        accumulated_epf = _f(payroll_inputs.get('accumulated_epf_ytd', 0.0))
        accumulated_pcb = _f(payroll_inputs.get('accumulated_pcb_ytd', 0.0))  # X
        accumulated_zakat = _f(payroll_inputs.get('accumulated_zakat_ytd', 0.0))  # Z

        # Current month data
        Y1 = _f(gross_monthly)
        K1 = _f(epf_monthly)

        # Remaining months calculation
        n = 12 - current_month  # Baki bulan bekerja dalam setahun
        n_plus_1 = n + 1        # Termasuk bulan semasa

        # Load configurable formula options
        formula_opts = _get_pcb_formula_options(tax_config, payroll_inputs)

        # Estimate future months (assume steady state)
        Y2 = Y1
        # EPF cap for PCB (K)
        # Priority: explicit tax_config['pcb_epf_annual_cap'] -> tax_relief_max_config['epf_shared_subcap'] -> default 4000
        pcb_epf_cap = _f(tax_config.get('pcb_epf_annual_cap') or 0.0, 0.0)
        if pcb_epf_cap <= 0.0:
            try:
                relief_cfg = load_tax_relief_max_configuration() or {}
                pcb_epf_cap = _f(relief_cfg.get('epf_shared_subcap') or 4000.0, 4000.0)
            except Exception:
                pcb_epf_cap = 4000.0
        # Remaining EPF relief after accumulated and current month contributions
        remaining_epf_relief = max(0.0, pcb_epf_cap - (accumulated_epf + K1))
        # Distribute remaining relief across remaining months, but not exceeding K1 per month
        K2 = min(K1, (remaining_epf_relief / n) if n > 0 else 0.0)

        # Tax reliefs (D, S, Du, Su, Q×C, LP)
        individual_relief = _f(payroll_inputs.get('individual_relief', 9000.0))  # D
        spouse_relief = _f(payroll_inputs.get('spouse_relief', 0.0))             # S
        disabled_individual = _f(payroll_inputs.get('disabled_individual', 0.0)) # Du
        disabled_spouse = _f(payroll_inputs.get('disabled_spouse', 0.0))         # Su
        child_relief = _f(payroll_inputs.get('child_relief', 0.0))               # Q
        try:
            child_count = int(payroll_inputs.get('child_count', 0) or 0)
        except Exception:
            child_count = 0
        other_reliefs_ytd = _f(payroll_inputs.get('other_reliefs_ytd', 0.0))     # ∑LP
        other_reliefs_current = _f(payroll_inputs.get('other_reliefs_current', 0.0))  # LP1

        # Annualized components
        future_gross = Y2 * n if n > 0 else 0.0
        future_epf = K2 * n if n > 0 else 0.0
        annual_gross = accumulated_gross + Y1 + future_gross
        annual_epf_paid = accumulated_epf + K1 + future_epf
        # Apply PCB-specific EPF cap (K limited annually)
        epf_relief_capped = min(annual_epf_paid, pcb_epf_cap)

        # Total annual reliefs
        # Optionally include LP1 (current month other reliefs) into annual reliefs P
        lp1_component = other_reliefs_current if formula_opts.get('include_lp1_in_annual', True) else 0.0
        total_reliefs_annual = (
            individual_relief + spouse_relief + disabled_individual + disabled_spouse +
            (child_relief * child_count) + other_reliefs_ytd + lp1_component + epf_relief_capped
        )

        # Annual chargeable income (P)
        P = max(0.0, annual_gross - total_reliefs_annual)

        # Compute annual tax using bracket details
        M, R, B = get_tax_bracket_details(P, {}, tax_config)
        annual_tax = ((P - M) * R + B) if P > M else B

        # Apply rebates (individual and optionally spouse) if within threshold
        rebate_threshold = _f(tax_config.get('rebate_threshold') or 35000.0, 35000.0)
        individual_rebate = _f(tax_config.get('individual_tax_rebate') or 400.0, 400.0)
        spouse_rebate = _f(tax_config.get('spouse_tax_rebate') or 400.0, 400.0)
        spouse_rebate_eligible = bool(payroll_inputs.get('spouse_rebate_eligible') or tax_config.get('spouse_rebate_eligible', False))
        if P <= rebate_threshold:
            total_rebate = individual_rebate + (spouse_rebate if spouse_rebate_eligible else 0.0)
            annual_tax = max(0.0, annual_tax - total_rebate)

        # Current month zakat
        current_zakat = _f(payroll_inputs.get('current_month_zakat', 0.0))

        # PCB per official divisor (n+1)
        # Divisor mode: n_plus_1 (official) or n (configurable)
        divisor = max(1, (n_plus_1 if formula_opts.get('divisor_mode') == 'n_plus_1' else n))
        pcb_gross = ((annual_tax - accumulated_zakat - accumulated_pcb) / divisor) if annual_tax > 0 else 0.0
        pcb_net = pcb_gross - current_zakat
        pcb_final = max(0.0, pcb_net)

        # Optional debug dump
        debug_pcb = bool((tax_config.get('debug_pcb') if isinstance(tax_config, dict) else False) or payroll_inputs.get('debug_pcb'))
        if debug_pcb:
            try:
                print(
                    "DEBUG PCB => "
                    f"month={current_month}, n={n}, divisor={divisor}; "
                    f"Y1={Y1:.2f}, K1={K1:.2f}, Y2={Y2:.2f}, K2={K2:.2f}; "
                    f"annual_gross={annual_gross:.2f}, epf_relief_capped={epf_relief_capped:.2f}; "
                    f"reliefs_total={total_reliefs_annual:.2f}, P={P:.2f}; "
                    f"M={M:.2f}, R={R:.3f}, B={B:.2f}, annual_tax={annual_tax:.2f}; "
                    f"Z={accumulated_zakat:.2f}, X={accumulated_pcb:.2f}, current_zakat={current_zakat:.2f}; "
                    f"pcb={pcb_final:.2f}"
                )
            except Exception:
                pass
        # Rounding mode: ceiling to 0.05 (default) or nearest 0.05
        if formula_opts.get('rounding_mode') == 'nearest_0_05':
            pcb_rounded = _round_to_nearest_0_05(pcb_final)
        else:
            pcb_rounded = _round_up_to_0_05(pcb_final)
        if debug_pcb:
            try:
                print(
                    f"DEBUG PCB Rounding => raw={pcb_final:.2f} rounded_0.05={pcb_rounded:.2f} "
                    f"[opts: rounding={formula_opts.get('rounding_mode')}, divisor={formula_opts.get('divisor_mode')}, include_lp1={formula_opts.get('include_lp1_in_annual')}]"
                )
            except Exception:
                pass
        return pcb_rounded
    except Exception as e:
        print(f"DEBUG: Error in LHDN PCB calculation: {e}")
        return 0.0

def _debug_dump_pcb_inputs(payroll_inputs: Dict, gross_monthly: float, epf_monthly: float, tax_config: Dict, month_year: str) -> None:
    """Print a structured summary of PCB inputs and config to help diagnose mismatches."""
    try:
        # Parse month and compute n
        try:
            cm = int(str(month_year).split('/')[0])
        except Exception:
            cm = 1
        n = 12 - cm
        # Read brackets count from DB
        cfg_name = tax_config.get('config_name', 'default') if isinstance(tax_config, dict) else 'default'
        rows = _load_progressive_tax_brackets(cfg_name) or []
        brackets_count = len(rows)
        print("DEBUG: PCB INPUTS BEGIN ———")
        print(f"  period={month_year} parsed_month={cm} n={n} divisor={n+1}")
        print(f"  gross_monthly(Y1)={gross_monthly:.2f} epf_monthly(K1)={epf_monthly:.2f}")
        print(f"  accumulated_gross_ytd={float(payroll_inputs.get('accumulated_gross_ytd',0)):.2f}")
        print(f"  accumulated_epf_ytd={float(payroll_inputs.get('accumulated_epf_ytd',0)):.2f}")
        print(f"  accumulated_pcb_ytd(X)={float(payroll_inputs.get('accumulated_pcb_ytd',0)):.2f}")
        print(f"  accumulated_zakat_ytd(Z)={float(payroll_inputs.get('accumulated_zakat_ytd',0)):.2f}")
        print(f"  individual_relief(D)={float(payroll_inputs.get('individual_relief',0)):.2f}")
        print(f"  spouse_relief(S)={float(payroll_inputs.get('spouse_relief',0)):.2f}")
        print(f"  disabled_individual(Du)={float(payroll_inputs.get('disabled_individual',0)):.2f}")
        print(f"  disabled_spouse(Su)={float(payroll_inputs.get('disabled_spouse',0)):.2f}")
        print(f"  child_relief(Q)={float(payroll_inputs.get('child_relief',0)):.2f} child_count(C)={int(payroll_inputs.get('child_count',0) or 0)}")
        print(f"  other_reliefs_ytd(ΣLP)={float(payroll_inputs.get('other_reliefs_ytd',0)):.2f}")
        print(f"  other_reliefs_current(LP1)={float(payroll_inputs.get('other_reliefs_current',0)):.2f}")
        print(f"  current_month_zakat={float(payroll_inputs.get('current_month_zakat',0)):.2f}")
        # Tax config summary
        pcb_epf_cap = tax_config.get('pcb_epf_annual_cap')
        print("  tax_config:")
        print(f"    config_name={cfg_name} rebate_threshold={tax_config.get('rebate_threshold', 35000.0)}")
        print(f"    individual_tax_rebate={tax_config.get('individual_tax_rebate', 400.0)} spouse_tax_rebate={tax_config.get('spouse_tax_rebate', 400.0)}")
        print(f"    spouse_rebate_eligible={bool(tax_config.get('spouse_rebate_eligible', False) or payroll_inputs.get('spouse_rebate_eligible', False))}")
        print(f"    pcb_epf_annual_cap={pcb_epf_cap} (fallback to tax_relief_max_config.epf_shared_subcap if None)")
        print(f"    progressive_tax_brackets rows={brackets_count} (DB)")
        print("DEBUG: PCB INPUTS END ———")
    except Exception as e:
        print(f"DEBUG: Failed to dump PCB inputs: {e}")

def calculate_pcb_additional_remuneration(
    payroll_inputs: Dict,
    gross_monthly: float,
    epf_monthly: float,
    tax_config: Dict,
    month_year: str,
    additional_gross: float,
    additional_epf: float,
) -> Dict[str, float]:
    """Compute PCB for a month that includes saraan tambahan (additional remuneration)
    following LHDN two-step method.

    Returns a dict with:
      - pcb_A_raw: Monthly PCB(A) before rounding and zakat deduction
      - pcb_A_rounded: Monthly PCB(A) rounded per config
      - CS_annual_tax: Annual tax CS with Yt/Kt included (after rebates)
      - pcb_C_raw: Additional PCB(C) before rounding
      - pcb_C_rounded: Additional PCB(C) rounded per config
      - pcb_total_raw: pcb_A_raw - current_month_zakat + pcb_C_raw
      - pcb_total_rounded: pcb_A_rounded - current_month_zakat + pcb_C_rounded

    Notes:
    - pcb_A uses K2 computed without Kt (standard monthly flow).
    - CS recomputes K2 with Kt included in the remaining EPF relief, as per worksheet.
    - Rounding uses the same configurable mode as monthly PCB.
    """
    try:
        # Helper to coerce float safely
        def _f(v, d=0.0):
            try:
                return float(v)
            except Exception:
                return float(d)

        # Parse current month and n
        try:
            cm = int(str(month_year).split('/')[0])
        except Exception:
            from datetime import datetime as _dt
            cm = _dt.now(KL_TZ).month
        n = 12 - int(cm)
        n_plus_1 = n + 1

        # Read formula options
        opts = _get_pcb_formula_options(tax_config, payroll_inputs)

        # Extract YTD and relief inputs
        accumulated_gross = _f(payroll_inputs.get('accumulated_gross_ytd', 0.0))
        accumulated_epf = _f(payroll_inputs.get('accumulated_epf_ytd', 0.0))
        accumulated_pcb = _f(payroll_inputs.get('accumulated_pcb_ytd', 0.0))  # X
        accumulated_zakat = _f(payroll_inputs.get('accumulated_zakat_ytd', 0.0))  # Z

        individual_relief = _f(payroll_inputs.get('individual_relief', 9000.0))
        spouse_relief = _f(payroll_inputs.get('spouse_relief', 0.0))
        disabled_individual = _f(payroll_inputs.get('disabled_individual', 0.0))
        disabled_spouse = _f(payroll_inputs.get('disabled_spouse', 0.0))
        child_relief = _f(payroll_inputs.get('child_relief', 0.0))
        try:
            child_count = int(payroll_inputs.get('child_count', 0) or 0)
        except Exception:
            child_count = 0
        other_reliefs_ytd = _f(payroll_inputs.get('other_reliefs_ytd', 0.0))
        other_reliefs_current = _f(payroll_inputs.get('other_reliefs_current', 0.0))
        current_zakat = _f(payroll_inputs.get('current_month_zakat', 0.0))

        # EPF annual cap used for PCB (default to tax_relief_max_config.epf_shared_subcap or 4,000)
        pcb_epf_cap = _f(tax_config.get('pcb_epf_annual_cap') or 0.0, 0.0)
        if pcb_epf_cap <= 0.0:
            try:
                relief_cfg = load_tax_relief_max_configuration() or {}
                pcb_epf_cap = _f(relief_cfg.get('epf_shared_subcap') or 4000.0, 4000.0)
            except Exception:
                pcb_epf_cap = 4000.0

        # A) Standard monthly PCB without considering Yt/Kt (uses existing helper, which applies rounding and subtracts current zakat)
        # We'll recompute the raw A (before zakat) by adding current zakat back afterwards for clarity
        # Note: calculate_lhdn_pcb_official returns a rounded amount with zakat already deducted.
        # To get A-rounded, call with current_zakat=0 temporarily, then subtract outside.
        pcb_inputs_for_A = dict(payroll_inputs)
        pcb_inputs_for_A['debug_pcb'] = False
        # neutralize zakat to isolate A
        saved_cz = pcb_inputs_for_A.get('current_month_zakat', 0.0)
        pcb_inputs_for_A['current_month_zakat'] = 0.0
        pcb_A_rounded = calculate_lhdn_pcb_official(
            pcb_inputs_for_A,
            gross_monthly,
            epf_monthly,
            tax_config,
            month_year,
        )
        # Recreate raw by reversing rounding to nearest cent is not deterministic; instead, recompute raw via formula path
        # Build monthly (A) annual tax using the same logic as calculate_lhdn_pcb_official without Z and X
        Y1 = _f(gross_monthly)
        K1 = _f(epf_monthly)
        Y2 = Y1
        # K2 for A (without Kt)
        remaining_epf_relief_A = max(0.0, pcb_epf_cap - (accumulated_epf + K1))
        K2_A = min(K1, (remaining_epf_relief_A / n) if n > 0 else 0.0)
        future_gross_A = Y2 * n if n > 0 else 0.0
        future_epf_A = K2_A * n if n > 0 else 0.0
        annual_gross_A = accumulated_gross + Y1 + future_gross_A
        annual_epf_paid_A = accumulated_epf + K1 + future_epf_A
        epf_relief_capped_A = min(annual_epf_paid_A, pcb_epf_cap)
        lp1_component = other_reliefs_current if opts.get('include_lp1_in_annual', True) else 0.0
        total_reliefs_A = (
            individual_relief + spouse_relief + disabled_individual + disabled_spouse +
            (child_relief * child_count) + other_reliefs_ytd + lp1_component + epf_relief_capped_A
        )
        P_A = max(0.0, annual_gross_A - total_reliefs_A)
        M_A, R_A, B_A = get_tax_bracket_details(P_A, {}, tax_config)
        annual_tax_A = ((P_A - M_A) * R_A + B_A) if P_A > M_A else B_A
        # Apply rebates if within threshold
        rebate_threshold = _f(tax_config.get('rebate_threshold') or 35000.0, 35000.0)
        individual_rebate = _f(tax_config.get('individual_tax_rebate') or 400.0, 400.0)
        spouse_rebate = _f(tax_config.get('spouse_tax_rebate') or 400.0, 400.0)
        spouse_rebate_eligible = bool(payroll_inputs.get('spouse_rebate_eligible') or tax_config.get('spouse_rebate_eligible', False))
        if P_A <= rebate_threshold:
            annual_tax_A = max(0.0, annual_tax_A - (individual_rebate + (spouse_rebate if spouse_rebate_eligible else 0.0)))
        divisor = max(1, (n_plus_1 if opts.get('divisor_mode') == 'n_plus_1' else n))
        pcb_A_raw = (annual_tax_A - 0.0 - 0.0) / divisor  # exclude Z and X for monthly PCB(A)

        # B) CS with Yt/Kt included (recompute K2 with Kt in remaining relief)
        Yt = _f(additional_gross, 0.0)
        Kt = _f(additional_epf, 0.0)
        remaining_epf_relief_CS = max(0.0, pcb_epf_cap - (accumulated_epf + K1 + Kt))
        K2_CS = min(K1, (remaining_epf_relief_CS / n) if n > 0 else 0.0)
        future_gross_CS = Y2 * n if n > 0 else 0.0
        future_epf_CS = K2_CS * n if n > 0 else 0.0
        annual_gross_CS = accumulated_gross + Y1 + Yt + future_gross_CS
        annual_epf_paid_CS = accumulated_epf + K1 + Kt + future_epf_CS
        epf_relief_capped_CS = min(annual_epf_paid_CS, pcb_epf_cap)
        total_reliefs_CS = (
            individual_relief + spouse_relief + disabled_individual + disabled_spouse +
            (child_relief * child_count) + other_reliefs_ytd + lp1_component + epf_relief_capped_CS
        )
        P_CS = max(0.0, annual_gross_CS - total_reliefs_CS)
        M_CS, R_CS, B_CS = get_tax_bracket_details(P_CS, {}, tax_config)
        CS_annual_tax = ((P_CS - M_CS) * R_CS + B_CS) if P_CS > M_CS else B_CS
        if P_CS <= rebate_threshold:
            CS_annual_tax = max(0.0, CS_annual_tax - (individual_rebate + (spouse_rebate if spouse_rebate_eligible else 0.0)))

        # C) Additional PCB(C) = CS - [PCB(B) + Zakat terkumpul], where PCB(B) = X + A*(n+1)
        pcb_B_projected_raw = accumulated_pcb + (pcb_A_raw * n_plus_1)
        pcb_C_raw = CS_annual_tax - (pcb_B_projected_raw + accumulated_zakat)

        # Round components per config
        if opts.get('rounding_mode') == 'nearest_0_05':
            pcb_A_final = _round_to_nearest_0_05(pcb_A_raw)
            pcb_C_final = _round_to_nearest_0_05(pcb_C_raw)
        else:
            pcb_A_final = _round_up_to_0_05(pcb_A_raw)
            pcb_C_final = _round_up_to_0_05(pcb_C_raw)

        total_raw = max(0.0, pcb_A_raw - current_zakat + pcb_C_raw)
        total_rounded = max(0.0, pcb_A_final - current_zakat + pcb_C_final)

        return {
            'pcb_A_raw': round(pcb_A_raw, 2),
            'pcb_A_rounded': round(pcb_A_final, 2),
            'CS_annual_tax': round(CS_annual_tax, 2),
            'pcb_C_raw': round(pcb_C_raw, 2),
            'pcb_C_rounded': round(pcb_C_final, 2),
            'pcb_total_raw': round(total_raw, 2),
            'pcb_total_rounded': round(total_rounded, 2),
            'n': float(n),
            'n_plus_1': float(n_plus_1),
            'K2_monthly': round(K2_A, 2),
            'K2_with_YtKt': round(K2_CS, 2),
            'P_monthly': round(P_A, 2),
            'P_with_YtKt': round(P_CS, 2),
        }
    except Exception as e:
        print(f"DEBUG: Error in additional remuneration PCB calculation: {e}")
        return {
            'pcb_A_raw': 0.0,
            'pcb_A_rounded': 0.0,
            'CS_annual_tax': 0.0,
            'pcb_C_raw': 0.0,
            'pcb_C_rounded': 0.0,
            'pcb_total_raw': 0.0,
            'pcb_total_rounded': 0.0,
            'n': 0.0,
            'n_plus_1': 0.0,
            'K2_monthly': 0.0,
            'K2_with_YtKt': 0.0,
            'P_monthly': 0.0,
            'P_with_YtKt': 0.0,
        }

def _load_progressive_tax_brackets(config_name: str = 'default') -> Optional[List[Dict]]:
    """Load progressive tax brackets from DB; returns list of dicts with lower_bound, upper_bound, rate."""
    try:
        res = supabase.table('progressive_tax_brackets') \
            .select('lower_bound, upper_bound, rate') \
            .eq('config_name', config_name) \
            .order('lower_bound', desc=False) \
            .execute()
        if res and res.data:
            return res.data
        return None
    except Exception as e:
        print(f"DEBUG: Could not load progressive tax brackets: {e}")
        return None


def save_progressive_tax_brackets(brackets: List[Dict], config_name: str = 'default') -> bool:
    """Persist progressive tax brackets to DB, replacing existing rows for config_name.
    Expected bracket dict keys: from, to, rate (percent or fraction handled), optional order.
    """
    try:
        # Normalize and validate
        normalized: List[Dict] = []
        for idx, b in enumerate(brackets, start=1):
            lb = float(b.get('from', 0.0) or 0.0)
            ub = b.get('to')
            if ub is None or float(ub) <= 0:
                ub_val = None  # open-ended
            else:
                ub_val = float(ub)
            rate_val = float(b.get('rate', 0.0) or 0.0)
            # Accept 0-100 or 0-1 scale
            rate = rate_val/100.0 if rate_val > 1.0 else rate_val
            normalized.append({
                'config_name': config_name,
                'bracket_order': int(b.get('order', idx)),
                'lower_bound': lb,
                'upper_bound': ub_val,
                'rate': rate,
                # UI helper fields
                'on_first_amount': float(b.get('on_first', 0.0) or 0.0),
                'next_amount': float(b.get('next', 0.0) or 0.0),
                'tax_first_amount': float(b.get('tax_first', 0.0) or 0.0),
                'tax_next_amount': float(b.get('tax_next', 0.0) or 0.0),
            })

        # Transaction: delete existing then upsert new
        # Some Supabase setups may not expose 'id'; delete by config_name only
        supabase.table('progressive_tax_brackets').delete().eq('config_name', config_name).execute()
        if normalized:
            # Insert in batches to be safe
            batch_size = 100
            for i in range(0, len(normalized), batch_size):
                supabase.table('progressive_tax_brackets').insert(normalized[i:i+batch_size]).execute()
        return True
    except Exception as e:
        print(f"DEBUG: Error saving progressive tax brackets: {e}")
        return False


def load_progressive_tax_brackets(config_name: str = 'default') -> List[Dict]:
    """Public loader for UI: returns list of {'from','to','rate','order'} sorted by order."""
    rows = _load_progressive_tax_brackets(config_name) or []
    result: List[Dict] = []
    for i, r in enumerate(rows, start=1):
        lb = float(r.get('lower_bound', 0.0) or 0.0)
        ub = r.get('upper_bound')
        rate = float(r.get('rate', 0.0) or 0.0)
        result.append({
            'from': lb,
            'to': ub if ub is not None else 0.0,
            'rate': rate*100.0,
            'order': i,
            # UI helper fields
            'on_first': float(r.get('on_first_amount', 0.0) or 0.0),
            'next': float(r.get('next_amount', 0.0) or 0.0),
            'tax_first': float(r.get('tax_first_amount', 0.0) or 0.0),
            'tax_next': float(r.get('tax_next_amount', 0.0) or 0.0),
        })
    return result


def get_tax_bracket_details(annual_income: float, progressive_rates: Dict, tax_config: Dict) -> tuple:
    """
    Compute bracket details M, R, B for a given annual income.
    Prefers DB-backed progressive_tax_brackets; falls back to hard-coded 2025 brackets.
    Returns M (lower bound), R (marginal rate), B (cumulative tax at lower bound).
    """
    try:
        # Try DB-backed brackets first
        cfg_name = tax_config.get('config_name', 'default') if isinstance(tax_config, dict) else 'default'
        brackets_db = _load_progressive_tax_brackets(cfg_name)
        brackets: List[tuple] = []
        if brackets_db:
            # Convert to a list of (upper, rate) while preserving order; ensure last upper is inf if null
            cumulative_bounds: List[tuple] = []
            for row in brackets_db:
                lb = float(row.get('lower_bound', 0.0) or 0.0)
                ub_val = row.get('upper_bound')
                ub = float(ub_val) if ub_val is not None else float('inf')
                rate_val = float(row.get('rate', 0.0) or 0.0)
                # DB may store percentage (e.g., 25 for 25%). Normalize to fraction if > 1.0
                rate = rate_val/100.0 if rate_val > 1.0 else rate_val
                cumulative_bounds.append((lb, ub, rate))
            # We keep only (upper, rate) for tax accumulation helper
            brackets = [(ub, rate) for (_lb, ub, rate) in cumulative_bounds]
        else:
            print("DEBUG: Using fallback progressive tax brackets (DB returned none)")
            # Fallback to a bracket schedule consistent with Jadual PCB baseline
            # Ensures for M=100,000: R=25% and B=9,400 (as per example provided)
            brackets = [
                (5000, 0.00),     # 0 - 5,000 @ 0%
                (20000, 0.01),    # 5,001 - 20,000 @ 1%  (tax on band: 150)
                (35000, 0.03),    # 20,001 - 35,000 @ 3% (tax on band: 450) cumulative: 600
                (50000, 0.06),    # 35,001 - 50,000 @ 6% (tax on band: 900) cumulative: 1,500
                (70000, 0.11),    # 50,001 - 70,000 @ 11% (tax on band: 2,200) cumulative: 3,700
                (100000, 0.19),   # 70,001 - 100,000 @ 19% (tax on band: 5,700) cumulative: 9,400
                (400000, 0.25),   # 100,001 - 400,000 @ 25%
                (600000, 0.26),   # 400,001 - 600,000 @ 26%
                (2000000, 0.28),  # 600,001 - 2,000,000 @ 28%
                (float('inf'), 0.30)
            ]

        # Helper to compute cumulative tax up to a given amount using brackets
        def cumulative_tax_up_to(amount: float) -> float:
            total = 0.0
            prev_upper = 0.0
            for upper, rate in brackets:
                if amount <= prev_upper:
                    break
                taxable = min(amount, upper) - prev_upper
                if taxable > 0:
                    total += taxable * rate
                prev_upper = upper
                if upper == float('inf'):
                    break
            return total

        prev_upper = 0.0
        for upper, rate in brackets:
            if annual_income <= upper:
                M = prev_upper
                R = rate
                B = cumulative_tax_up_to(M)
                return M, R, B
            prev_upper = upper

        # Fallback (shouldn't happen)
        return 2000000.0, 0.30, cumulative_tax_up_to(2000000.0)

    except Exception as e:
        print(f"DEBUG: Error getting tax bracket details: {e}")
        return 0.0, 0.0, 0.0


# -----------------------------------------------------------------------------
# EPF variable-percentage helper (shared by service and GUI)
# -----------------------------------------------------------------------------
def compute_variable_epf_for_part(
    part: Optional[str],
    gross_income: float,
    age: int,
    limits_cfg: Optional[Dict] = None,
    cfg: Optional[Dict] = None,
) -> Dict:
    """Compute EPF employee/employer (variable %) for a given EPF Part and income.

    Inputs:
      - part: 'part_a'|'part_b'|'part_c'|'part_d'|'part_e' (case-insensitive) or None
      - gross_income: monthly wage base before EPF
      - age: integer age (for stage fallback when part is unknown)
      - limits_cfg: {'epf_ceiling': float} (optional)
      - cfg: variable % config dict with keys like epf_part_a_employee, epf_part_e_employer_over20k, etc.

    Behavior:
      - If gross_income > 20,000: EPF base is full gross (no EPF cap)
      - Else: apply epf_ceiling if positive; otherwise use gross
      - Part A/B (<60): defaults employee 11%, employer 13% (12% if gross>5k and not overridden)
      - Part C/D/E (>=60): defaults employee 0%, employer 4% (with part-specific overrides)
      - Supports special over-20k and fixed-employer fields when present in cfg

    Returns dict:
      { 'employee': float, 'employer': float, 'base': float,
        'employee_rate': float, 'employer_rate': float,
        'over20k': bool, 'part_used': str, 'source': 'variable-percent' }
    """
    try:
        part_norm = (str(part).strip().lower() if part else None)
        limits_cfg = limits_cfg or {}
        cfg = cfg or {}

        def _cfg_float(keys, default):
            for k in (keys if isinstance(keys, (list, tuple)) else [keys]):
                if k in cfg and cfg.get(k) is not None:
                    try:
                        return float(cfg.get(k))
                    except Exception:
                        continue
            return float(default)

        over20k_income = float(gross_income or 0.0) > 20000.0
        try:
            epf_cap_val = float(limits_cfg.get('epf_ceiling', 0.0) or 0.0)
        except Exception:
            epf_cap_val = 0.0
        if over20k_income:
            base = float(gross_income or 0.0)
        else:
            base = float(gross_income or 0.0) if epf_cap_val <= 0.0 else min(float(gross_income or 0.0), epf_cap_val)

        # Optional hybrid mode: mirror official table for wages ≤ RM20,000 to ensure parity
        # Default enabled (True) to match user expectation that variable closely mirrors fixed
        try:
            mirror_table = bool(cfg.get('mirror_table_upto_20k', True))
        except Exception:
            mirror_table = True
        if not over20k_income and mirror_table:
            try:
                # Use existing table helper to get exact EPF amounts for the EPF Part
                from_wage = float(gross_income or 0.0)
                if not part_norm:
                    # Fallback by stage (age) when part is unavailable
                    part_norm = 'part_e' if int(age or 0) >= 60 else 'part_a'
                emp_amt, empr_amt, _ = get_epf_contributions_from_table(from_wage, part_norm)
                # Derive effective rates for transparency
                eff_emp_rate = (emp_amt / base * 100.0) if base > 0 else 0.0
                eff_empr_rate = (empr_amt / base * 100.0) if base > 0 else 0.0
                return {
                    'employee': round(float(emp_amt), 2),
                    'employer': round(float(empr_amt), 2),
                    'base': round(base, 2),
                    'employee_rate': float(eff_emp_rate),
                    'employer_rate': float(eff_empr_rate),
                    'over20k': False,
                    'part_used': part_norm,
                    'source': 'table-mirror',
                }
            except Exception as _tbl_mirror_err:
                # Fall back to percentage path below if table mirror fails
                try:
                    print(f"DEBUG: Table-mirror EPF failed, falling back to percentage: {_tbl_mirror_err}")
                except Exception:
                    pass

        emp = 0.0
        empr = 0.0
        emp_rate_used = 0.0
        empr_rate_used = 0.0

        # Part-specific handling
        if part_norm in ('part_a', 'part_b', 'part_c', 'part_d', 'part_e'):
            if part_norm == 'part_a':
                emp_rate = _cfg_float(['epf_part_a_employee', 'epf_employee_rate_stage1'], 11.0)
                default_empr_stage1 = 13.0 if float(gross_income or 0.0) <= 5000.0 else 12.0
                empr_rate = _cfg_float(['epf_part_a_employer', 'epf_employer_rate_stage1'], default_empr_stage1)
                if over20k_income:
                    emp_rate = _cfg_float('epf_part_a_employee_over20k', emp_rate)
                    empr_rate = _cfg_float('epf_part_a_employer_over20k', empr_rate)
                emp = base * (emp_rate / 100.0)
                empr = base * (empr_rate / 100.0)
                emp_rate_used, empr_rate_used = emp_rate, empr_rate
            elif part_norm == 'part_b':
                emp_rate = _cfg_float(['epf_part_b_employee', 'epf_employee_rate_stage1'], 11.0)
                default_empr_stage1 = 13.0 if float(gross_income or 0.0) <= 5000.0 else 12.0
                empr_rate = _cfg_float(['epf_part_b_employer', 'epf_employer_rate_stage1'], default_empr_stage1)
                if over20k_income:
                    emp_rate = _cfg_float('epf_part_b_employee_over20k', emp_rate)
                    empr_fixed = cfg.get('epf_part_b_employer_over20k_fixed')
                    if empr_fixed is not None:
                        try:
                            empr = float(empr_fixed)
                        except Exception:
                            empr = 0.0
                if empr == 0.0:
                    empr = base * (empr_rate / 100.0)
                emp = base * (emp_rate / 100.0)
                emp_rate_used, empr_rate_used = emp_rate, (empr / base * 100.0 if base > 0 else 0.0)
            elif part_norm == 'part_c':
                # Official schedule uses 5.5% employee and 6% employer for Part C over-20k.
                # Defaults can be overridden via config to match business policy.
                emp_rate = _cfg_float(['epf_part_c_employee', 'epf_employee_rate_stage2'], 0.0)
                empr_rate = _cfg_float(['epf_part_c_employer', 'epf_employer_rate_stage2'], 4.0)
                if over20k_income:
                    emp_rate = _cfg_float('epf_part_c_employee_over20k', emp_rate)
                    empr_rate = _cfg_float('epf_part_c_employer_over20k', empr_rate)
                emp = base * (emp_rate / 100.0)
                empr = base * (empr_rate / 100.0)
                emp_rate_used, empr_rate_used = emp_rate, empr_rate
            elif part_norm == 'part_d':
                # Official schedule uses 5.5% employee and fixed RM5 employer for Part D over-20k.
                emp_rate = _cfg_float(['epf_part_d_employee', 'epf_employee_rate_stage2'], 0.0)
                empr_rate = _cfg_float(['epf_part_d_employer', 'epf_employer_rate_stage2'], 4.0)
                if over20k_income:
                    emp_rate = _cfg_float('epf_part_d_employee_over20k', emp_rate)
                    empr_fixed = cfg.get('epf_part_d_employer_over20k_fixed')
                    if empr_fixed is not None:
                        try:
                            empr = float(empr_fixed)
                        except Exception:
                            empr = 0.0
                if empr == 0.0:
                    empr = base * (empr_rate / 100.0)
                emp = base * (emp_rate / 100.0)
                emp_rate_used, empr_rate_used = emp_rate, (empr / base * 100.0 if base > 0 else 0.0)
            elif part_norm == 'part_e':
                emp_rate = _cfg_float(['epf_part_e_employee', 'epf_employee_rate_stage2'], 0.0)
                empr_rate = _cfg_float(['epf_part_e_employer', 'epf_employer_rate_stage2'], 4.0)
                if over20k_income:
                    emp_rate = _cfg_float('epf_part_e_employee_over20k', emp_rate)
                    empr_rate = _cfg_float('epf_part_e_employer_over20k', empr_rate)
                emp = base * (emp_rate / 100.0)
                empr = base * (empr_rate / 100.0)
                emp_rate_used, empr_rate_used = emp_rate, empr_rate
        else:
            # Fallback by stage (age)
            if int(age or 0) >= 60:
                emp_rate = _cfg_float(['epf_employee_rate_stage2', 'epf_part_e_employee'], 0.0)
                empr_rate = _cfg_float(['epf_employer_rate_stage2', 'epf_part_e_employer'], 4.0)
            else:
                emp_rate = _cfg_float(['epf_employee_rate_stage1', 'epf_part_a_employee'], 11.0)
                default_empr_stage1 = 13.0 if float(gross_income or 0.0) <= 5000.0 else 12.0
                empr_rate = _cfg_float(['epf_employer_rate_stage1', 'epf_part_a_employer'], default_empr_stage1)
            emp = base * (emp_rate / 100.0)
            empr = base * (empr_rate / 100.0)
            emp_rate_used, empr_rate_used = emp_rate, empr_rate

        # For >RM20k, official schedule rounds each contribution to the next ringgit.
        if over20k_income:
            try:
                import math
                emp = float(math.ceil(emp))
                empr = float(math.ceil(empr)) if not (part_norm in ('part_b','part_d') and cfg.get(f'{part_norm}_employer_over20k_fixed') is not None) else empr
            except Exception:
                pass

        return {
            'employee': round(emp, 2),
            'employer': round(empr, 2),
            'base': round(base, 2),
            'employee_rate': float(emp_rate_used),
            'employer_rate': float(empr_rate_used),
            'over20k': bool(over20k_income),
            'part_used': part_norm or ('stage2' if int(age or 0) >= 60 else 'stage1'),
            'source': 'variable-percent',
        }
    except Exception as _err:
        print(f"DEBUG: compute_variable_epf_for_part failed: {_err}")
        return {
            'employee': 0.0,
            'employer': 0.0,
            'base': float(gross_income or 0.0),
            'employee_rate': 0.0,
            'employer_rate': 0.0,
            'over20k': float(gross_income or 0.0) > 20000.0,
            'part_used': part_norm or 'unknown',
            'source': 'variable-percent',
        }


# -----------------------------------------------------------------------------
# Schema verification helpers for tax-related tables
# -----------------------------------------------------------------------------
def _probe_column_exists(table: str, column: str) -> bool:
    """Return True if selecting the column succeeds; False if column likely missing."""
    try:
        # Limit to 1 row to minimize load; selection will fail if column doesn't exist
        supabase.table(table).select(column).limit(1).execute()
        return True
    except Exception as e:
        print(f"DEBUG: Column probe failed {table}.{column}: {e}")
        return False

def _probe_table_exists(table: str) -> bool:
    """Return True if selecting a known column succeeds, False otherwise."""
    try:
        supabase.table(table).select('*').limit(1).execute()
        return True
    except Exception as e:
        print(f"DEBUG: Table probe failed {table}: {e}")
        return False


def verify_tax_schema() -> Dict:
    """Verify the presence of expected columns for tax-related tables in Supabase.

    Returns a dict per table with status, missing required columns, and optional missing columns.
    """
    report: Dict[str, Dict] = {}

    def check(table: str, required: List[str], optional: List[str]) -> Dict:
        missing = [c for c in required if not _probe_column_exists(table, c)]
        opt_missing = [c for c in optional if not _probe_column_exists(table, c)]
        status = 'ok' if not missing else 'missing'
        return {'status': status, 'missing': missing, 'optional_missing': opt_missing}

    # progressive_tax_brackets
    report['progressive_tax_brackets'] = check(
        'progressive_tax_brackets',
        required=['config_name', 'lower_bound', 'upper_bound', 'rate'],
        optional=['bracket_order', 'on_first_amount', 'next_amount', 'tax_first_amount', 'tax_next_amount']
    )

    # tax_rates_config (minimal policy)
    report['tax_rates_config'] = check(
        'tax_rates_config',
        required=['config_name', 'is_active', 'non_resident_rate', 'individual_tax_rebate'],
        optional=['rebate_threshold']
    )

    # tax_relief_max_config
    relief_required = [
        'config_name', 'is_active', 'created_at',
        'personal_relief_max', 'spouse_relief_max', 'child_relief_max',
        'disabled_child_relief_max', 'parent_medical_max', 'medical_treatment_max',
        'serious_disease_max', 'fertility_treatment_max', 'vaccination_max',
        'dental_treatment_max', 'health_screening_max', 'child_learning_disability_max',
        'education_max', 'skills_course_max', 'lifestyle_max', 'sports_equipment_max',
        'gym_membership_max', 'checkup_vaccine_upper_limit', 'life_insurance_upper_limit',
        'epf_shared_subcap', 'combined_epf_insurance_limit'
    ]
    report['tax_relief_max_config'] = check('tax_relief_max_config', relief_required, optional=[])

    # statutory_limits_config
    report['statutory_limits_config'] = check(
        'statutory_limits_config',
        required=['config_name', 'is_active', 'epf_ceiling', 'socso_ceiling', 'eis_ceiling'],
        optional=[]
    )

    # variable_percentage_configs (support old vs new formats)
    # We'll consider either combined or ACT-split as acceptable
    var_required_any = [
        ['config_name', 'epf_employee_rate', 'epf_employer_rate', 'socso_employee_rate', 'socso_employer_rate', 'eis_employee_rate', 'eis_employer_rate'],
        ['config_name', 'epf_employee_rate_stage1', 'epf_employer_rate_stage1', 'epf_employee_rate_stage2', 'epf_employer_rate_stage2', 'eis_employee_rate', 'eis_employer_rate']
    ]
    var_optional = ['pcb_rate', 'description', 'created_at', 'updated_at', 'socso_act4_employee_rate', 'socso_act4_employer_rate', 'socso_act800_employee_rate', 'socso_act800_employer_rate']
    # Determine which required set is satisfied
    set_statuses = []
    for req_set in var_required_any:
        missing = [c for c in req_set if not _probe_column_exists('variable_percentage_configs', c)]
        set_statuses.append((req_set, missing))
    # Pick the best
    best = min(set_statuses, key=lambda t: len(t[1])) if set_statuses else ([], [])
    var_missing = best[1]
    var_opt_missing = [c for c in var_optional if not _probe_column_exists('variable_percentage_configs', c)]
    report['variable_percentage_configs'] = {
        'status': 'ok' if len(var_missing) == 0 else 'missing',
        'missing': var_missing,
        'optional_missing': var_opt_missing,
        'accepted_required_set': best[0]
    }

    # payroll_monthly_deductions (LP1 source)
    report['payroll_monthly_deductions'] = check(
        'payroll_monthly_deductions',
        required=['employee_id', 'year', 'month'],
    optional=['zakat_monthly', 'religious_travel_monthly', 'other_deductions_amount', 'other_reliefs_monthly', 'socso_eis_lp1_monthly']
    )

    # relief overrides tables (admin UI)
    report['relief_item_overrides'] = check(
        'relief_item_overrides',
        required=['item_key'],
        optional=['cap', 'pcb_only', 'cycle_years']
    )
    report['relief_group_overrides'] = check(
        'relief_group_overrides',
        required=['group_id'],
        optional=['cap']
    )

    return report


def print_tax_schema_report() -> None:
    """Pretty-print the verification report to stdout."""
    rep = verify_tax_schema()
    print("\nTax schema verification:")
    for table, info in rep.items():
        status = info.get('status')
        missing = info.get('missing', [])
        opt = info.get('optional_missing', [])
        extra = info.get('accepted_required_set', [])
        print(f"- {table}: {status}")
        if extra:
            print(f"  accepted_required_set: {extra}")
        if missing:
            print(f"  missing: {missing}")
        if opt:
            print(f"  optional_missing: {opt}")


# -----------------------------------------------------------------------------
# Debug helpers for LP1 / monthly deductions visibility
# -----------------------------------------------------------------------------
def debug_print_monthly_deductions(employee_id: str, year: int, month: int) -> Dict:
    """Fetch and print monthly deductions row, returning the dict for inspection."""
    md = get_monthly_deductions(employee_id, year, month)
    try:
        print(f"Monthly deductions for {employee_id} {month:02d}/{year}: {md}")
    except Exception:
        pass
    return md


def debug_show_lp1_snapshot(employee_id: str, year: int, month: int) -> Dict:
    """Show how LP1 (other_reliefs_current) is derived from monthly_deductions."""
    md = get_monthly_deductions(employee_id, year, month)
    lp1 = _derive_other_reliefs_current_from_monthly(md)
    details = {
        'employee_id': employee_id,
        'year': year,
        'month': month,
        'monthly_deductions': md,
        'computed_LP1': round(lp1, 2),
    }
    try:
        print("LP1 snapshot: ")
        print(details)
    except Exception:
        pass
    return details


# -----------------------------------------------------------------------------
# Employee statutory classification (EPF Part, SOCSO category, EIS eligibility)
# -----------------------------------------------------------------------------
def classify_employee_statutory_fields(employee_row: Dict, overwrite: bool = False, persist: bool = True) -> Dict:
    """Classify a single employee into EPF Part, SOCSO category, and EIS eligibility.

    Inputs:
      - employee_row: dict representing a row from employees table. Should contain at least:
          id, employee_id, full_name, date_of_birth, nationality, citizenship
          optionally: epf_part (existing), socso_category (existing)
      - overwrite: if True, will overwrite existing epf_part/socso_category; if False, only fill missing
      - persist: if True, writes updates back to employees table

    Returns a dict with keys:
      { 'id', 'employee_id', 'full_name', 'age', 'epf_part_old', 'epf_part_new',
        'socso_category_old', 'socso_category_new', 'eis_eligible', 'updated': bool }
    """
    result: Dict[str, Any] = {}
    try:
        if not isinstance(employee_row, dict):
            return {'updated': False, 'error': 'invalid_row'}
        emp_id = employee_row.get('employee_id')
        emp_uuid = employee_row.get('id')
        full_name = employee_row.get('full_name') or employee_row.get('name') or ''

        # Normalize inputs for eligibility calculator
        data_for_calc = {
            'date_of_birth': employee_row.get('date_of_birth') or employee_row.get('dob') or '',
            'nationality': employee_row.get('nationality') or '',
            'citizenship': employee_row.get('citizenship') or '',
            'basic_salary': employee_row.get('basic_salary') or 0.0,
        }
        from core.epf_socso_calculator import calculate_epf_socso_eligibility, EPFSOCSCalculator
        status = calculate_epf_socso_eligibility(data_for_calc)

        # If employee already has an explicit EPF part, prefer keeping it unless overwrite=True
        epf_part_old = employee_row.get('epf_part')
        epf_part_new = status.get('epf_part')
        if epf_part_old and not overwrite:
            epf_part_new = epf_part_old

        # SOCSO category from calculator is already aligned to employees.socso_category values
        socso_old = employee_row.get('socso_category')
        socso_new = status.get('socso_category') or socso_old or 'Exempt'
        if socso_old and not overwrite:
            socso_new = socso_old

        eis_eligible = bool(status.get('eis_eligible', False))

        result = {
            'id': emp_uuid,
            'employee_id': emp_id,
            'full_name': full_name,
            'age': status.get('employee_age'),
            'epf_part_old': epf_part_old,
            'epf_part_new': epf_part_new,
            'socso_category_old': socso_old,
            'socso_category_new': socso_new,
            'eis_eligible': eis_eligible,
            'updated': False,
        }

        # Prepare DB payload with column existence checks
        if persist and emp_uuid:
            payload = {}
            def col_exists(col: str) -> bool:
                return _probe_column_exists('employees', col)

            if epf_part_new != epf_part_old and col_exists('epf_part'):
                payload['epf_part'] = epf_part_new
            if socso_new != socso_old and col_exists('socso_category'):
                payload['socso_category'] = socso_new
            # Only persist EIS eligibility if column exists (not guaranteed in current schema)
            if col_exists('eis_eligible'):
                payload['eis_eligible'] = eis_eligible

            if payload:
                try:
                    supabase.table('employees').update(payload).eq('id', emp_uuid).execute()
                    result['updated'] = True
                except Exception as _up:
                    print(f"DEBUG: Failed to persist classification for {emp_id}: {_up}")
                    result['updated'] = False
        return result
    except Exception as e:
        print(f"DEBUG: classify_employee_statutory_fields error: {e}")
        result['updated'] = False
        result['error'] = str(e)
        return result


def classify_all_employees_statutory(overwrite: bool = False, persist: bool = True, batch_size: int = 500) -> Dict:
    """Classify all employees and optionally persist updates.

    Scans the employees table in batches and applies EPF/SOCSO/EIS classification.
    Returns a summary dict with counts per EPF Part and SOCSO category and update stats.
    """
    summary = {
        'processed': 0,
        'updated': 0,
        'epf_parts': {},
        'socso_categories': {},
        'errors': 0,
        'samples': [],
    }
    try:
        # Count total rows (best-effort)
        try:
            total = supabase.table('employees').select('id', count='exact').execute().count or 0
        except Exception:
            total = 0

        start = 0
        while True:
            try:
                # Fetch a batch (id + minimal fields)
                rows = (
                    supabase
                    .table('employees')
                    .select('id, employee_id, full_name, date_of_birth, nationality, citizenship, basic_salary, epf_part, socso_category')
                    .range(start, start + batch_size - 1)
                    .execute()
                )
                data = getattr(rows, 'data', None) or []
            except Exception as _qerr:
                print(f"DEBUG: Failed to fetch employees batch starting at {start}: {_qerr}")
                break

            if not data:
                break

            for row in data:
                res = classify_employee_statutory_fields(row, overwrite=overwrite, persist=persist)
                summary['processed'] += 1
                if res.get('updated'):
                    summary['updated'] += 1
                ep = res.get('epf_part_new') or 'None'
                summary['epf_parts'][ep] = summary['epf_parts'].get(ep, 0) + 1
                sc = res.get('socso_category_new') or 'Exempt'
                summary['socso_categories'][sc] = summary['socso_categories'].get(sc, 0) + 1
                if len(summary['samples']) < 10:
                    summary['samples'].append({
                        'employee_id': res.get('employee_id'),
                        'full_name': res.get('full_name'),
                        'epf_part': res.get('epf_part_new'),
                        'socso_category': res.get('socso_category_new'),
                        'eis_eligible': res.get('eis_eligible'),
                        'updated': res.get('updated'),
                    })

            start += batch_size

        try:
            summary['total'] = total or summary['processed']
        except Exception:
            summary['total'] = summary['processed']
        return summary
    except Exception as e:
        print(f"DEBUG: classify_all_employees_statutory error: {e}")
        summary['error'] = str(e)
        return summary


def calculate_comprehensive_payroll(employee_data: Dict, payroll_inputs: Dict, month_year: str) -> Dict:
    """Calculate comprehensive payroll including all deductions, taxes, and reliefs."""
    try:
        # Load configs
        tax_rates_config = load_tax_rates_configuration() or {}
        tax_relief_config = load_tax_relief_max_configuration() or {}
        limits_cfg = load_statutory_limits_configuration('default') or {
            'epf_ceiling': 6000.0, 'socso_ceiling': 6000.0, 'eis_ceiling': 6000.0
        }

        # Extract basics
        employee_id = employee_data.get('employee_id', '')
        employee_uuid = employee_data.get('id')
        # Resolve employee UUID from employee_id code if necessary for DB lookups
        if not employee_uuid and employee_id:
            try:
                r = supabase.table('employees').select('id').eq('employee_id', employee_id).limit(1).execute()
                if r and getattr(r, 'data', None):
                    employee_uuid = r.data[0].get('id') or employee_uuid
            except Exception as _eid_resolve_err:
                print(f"DEBUG: Could not resolve employees.id from employee_id code: {_eid_resolve_err}")
        employee_name = employee_data.get('full_name', '')
        employee_email = employee_data.get('email', '')
        # Determine tax resident status priority order:
        # 1. Explicit value passed in payroll_inputs
        # 2. Employee record field 'tax_resident_status' (string, e.g. "Resident" / "Non-Resident")
        # 3. Boolean employee field 'is_resident' (True -> Resident, False -> Non-Resident)
        # 4. Default to 'Resident'
        tax_resident_status = payroll_inputs.get('tax_resident_status')
        if not tax_resident_status:
            emp_ts = employee_data.get('tax_resident_status')
            if isinstance(emp_ts, str) and emp_ts.strip():
                tax_resident_status = emp_ts.strip().title()
            else:
                is_res_bool = employee_data.get('is_resident')
                if isinstance(is_res_bool, bool):
                    tax_resident_status = 'Resident' if is_res_bool else 'Non-Resident'
        if not tax_resident_status:
            tax_resident_status = 'Resident'
        payroll_inputs['tax_resident_status'] = tax_resident_status  # ensure downstream consistency

        # Period
        try:
            mm, yy = month_year.split('/')
            period_month, period_year = int(mm), int(yy)
        except Exception:
            now_dt = datetime.now(KL_TZ)
            period_month, period_year = now_dt.month, now_dt.year

        # Gross income
        basic_salary = payroll_inputs.get('basic_salary', 0.0)
        allowances = payroll_inputs.get('allowances', {})
        overtime_pay = payroll_inputs.get('overtime_pay', 0.0)
        commission = payroll_inputs.get('commission', 0.0)
        bonus = payroll_inputs.get('bonus', 0.0)
        total_allowances = sum(allowances.values()) if allowances else 0.0
        gross_income = basic_salary + total_allowances + overtime_pay + commission + bonus

        # Statutory ceilings
        epf_ceiling = float(limits_cfg.get('epf_ceiling', 6000.0) or 6000.0)
        socso_ceiling = float(limits_cfg.get('socso_ceiling', 6000.0) or 6000.0)
        eis_ceiling = float(limits_cfg.get('eis_ceiling', 6000.0) or 6000.0)

        # Contributions via table or variable % based on setting
        epf_rate_source = 'table-based'
        try:
            settings = get_payroll_settings()
        except Exception:
            settings = {'calculation_method': 'fixed', 'active_variable_config': 'default'}

        method = str(settings.get('calculation_method', 'fixed') or 'fixed').strip().lower()

        # EPF part via calculator (used for both modes)
        part = None
        try:
            from core.epf_socso_calculator import EPFSOCSCalculator
            calculator = EPFSOCSCalculator()
            dob = employee_data.get('date_of_birth', '1900-01-01')
            nationality = employee_data.get('nationality', 'Malaysia')
            citizenship = employee_data.get('citizenship', 'Citizen')
            status = calculator.calculate_epf_socso_status(
                birth_date=dob if isinstance(dob, str) else dob.strftime('%Y-%m-%d'),
                nationality=nationality,
                citizenship=citizenship,
            )
            part = status.get('epf_part')
        except Exception:
            part = None

        # SOCSO age-based category (robust DOB parsing with fallbacks)
        try:
            from datetime import date as _date
            def _calc_age_from_str(ds: str) -> int:
                try:
                    from datetime import datetime as _dt
                    # Try common formats
                    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'):
                        try:
                            d = _dt.strptime(ds, fmt).date()
                            break
                        except Exception:
                            d = None
                    if d is None:
                        return 0
                    today = _date.today()
                    return today.year - d.year - ((today.month, today.day) < (d.month, d.day))
                except Exception:
                    return 0

            def _calc_age_flexible(e: Dict) -> int:
                # Priority list of possible DOB fields
                candidates = [
                    e.get('date_of_birth'), e.get('dob'), e.get('birth_date'),
                    e.get('birthdate'), e.get('birthday')
                ]
                for c in candidates:
                    if not c:
                        continue
                    if hasattr(c, 'strftime'):
                        try:
                            return _calc_age_from_str(c.strftime('%Y-%m-%d'))
                        except Exception:
                            pass
                    elif isinstance(c, str) and c.strip():
                        a = _calc_age_from_str(c.strip())
                        if a > 0:
                            return a
                # Try parsing Malaysian NRIC (YYMMDD-...)
                try:
                    ic = e.get('ic_number') or e.get('nric')
                    if isinstance(ic, str) and len(ic) >= 6:
                        yy = int(ic[0:2]); mm = int(ic[2:4]); dd = int(ic[4:6])
                        from datetime import date as _d
                        today = _date.today()
                        century = 1900 if (yy > (today.year % 100)) else 2000
                        birth = _d(century + yy, mm, dd)
                        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
                except Exception:
                    pass
                return 0

            age = _calc_age_flexible(employee_data)
        except Exception:
            age = 0
        socso_is_first = (age < 60)

        if method == 'variable':
            epf_rate_source = 'variable-percent'
            # Load active variable % config
            try:
                cfg_name = settings.get('active_variable_config') or 'default'
                cfg = get_variable_percentage_config(cfg_name) or {}
            except Exception:
                cfg = {}

            # Local helper to read percentage rates from variable config safely
            def _cfg_float(key: str, default: float) -> float:
                try:
                    if isinstance(cfg, dict) and key in cfg and cfg.get(key) is not None:
                        return float(cfg.get(key))
                    return float(default)
                except Exception:
                    return float(default)

            # Compute EPF via shared helper
            try:
                epf_dec = compute_variable_epf_for_part(part, gross_income, age, limits_cfg, cfg)
                epf_employee = float(epf_dec.get('employee', 0.0) or 0.0)
                epf_employer = float(epf_dec.get('employer', 0.0) or 0.0)
                wage_base_epf = float(epf_dec.get('base', gross_income) or gross_income)
                try:
                    print(
                        f"DEBUG EPF: part={epf_dec.get('part_used')} age={age} gross={gross_income:.2f} base={wage_base_epf:.2f} "
                        f"emp_rate={epf_dec.get('employee_rate')}% empr_rate={epf_dec.get('employer_rate')}% "
                        f"emp={epf_employee:.2f} empr={epf_employer:.2f}"
                    )
                except Exception:
                    pass
            except Exception as _epfvar:
                print(f"DEBUG: Variable EPF calc failed, defaulting to 0: {_epfvar}")
                epf_employee = epf_employer = 0.0

            wage_base_socso = min(gross_income, socso_ceiling)
            wage_base_eis = min(gross_income, eis_ceiling)

            # SOCSO
            try:
                if socso_is_first:
                    se = _cfg_float('socso_first_employee_rate', 0.5)
                    sr = _cfg_float('socso_first_employer_rate', 1.75)
                else:
                    se = _cfg_float('socso_second_employee_rate', 0.0)
                    sr = _cfg_float('socso_second_employer_rate', 1.25)
                socso_employee = wage_base_socso * (se / 100.0)
                socso_employer = wage_base_socso * (sr / 100.0)
            except Exception as _soc:
                print(f"DEBUG: Variable SOCSO calc failed: {_soc}")
                socso_employee = socso_employer = 0.0

            # EIS (eligible if 18-60, but we approximate using age<60 check only)
            try:
                eis_emp_rate = _cfg_float('eis_employee_rate', 0.2)
                eis_empr_rate = _cfg_float('eis_employer_rate', 0.2)
                if age >= 60:
                    eis_employee = 0.0
                    eis_employer = 0.0
                else:
                    eis_employee = wage_base_eis * (eis_emp_rate / 100.0)
                    eis_employer = wage_base_eis * (eis_empr_rate / 100.0)
            except Exception as _eis:
                print(f"DEBUG: Variable EIS calc failed: {_eis}")
                eis_employee = eis_employer = 0.0
        else:
            # Fixed/table method
            try:
                if part:
                    epf_employee, epf_employer, _ = get_epf_contributions_from_table(gross_income, part)
                else:
                    epf_employee, epf_employer = 0.0, 0.0
                socso_category = 'first_category' if socso_is_first else 'second_category'
                socso_employee, socso_employer, _ = get_socso_contributions_from_table(gross_income, socso_category)
                eis_employee, eis_employer, _ = get_eis_contributions(gross_income, 'eis')
            except Exception as _tbl:
                print(f"DEBUG: Fallback percentage calc due to error: {_tbl}")
                epf_rate_source = 'fallback-zeros'
                epf_employee = epf_employer = socso_employee = socso_employer = eis_employee = eis_employer = 0.0

        taxable_income = gross_income - epf_employee - socso_employee - eis_employee

        # YTD enrichment
        try:
            if employee_email and tax_resident_status == 'Resident':
                # Use previous month’s YTD (up to last month) for current month PCB
                _prev_month = 12 if period_month == 1 else (period_month - 1)
                _prev_year = period_year - 1 if period_month == 1 else period_year
                ytd_resp = supabase.table('payroll_ytd_accumulated').select('*') \
                    .eq('employee_email', employee_email) \
                    .eq('year', _prev_year) \
                    .eq('month', _prev_month) \
                    .execute()
                if ytd_resp.data:
                    ytd_row = ytd_resp.data[0]
                    payroll_inputs['accumulated_gross_ytd'] = float(ytd_row.get('accumulated_gross_salary_ytd', 0.0))
                    payroll_inputs['accumulated_epf_ytd'] = float(ytd_row.get('accumulated_epf_employee_ytd', 0.0))
                    payroll_inputs['accumulated_pcb_ytd'] = float(ytd_row.get('accumulated_pcb_ytd', 0.0))
                    payroll_inputs['accumulated_zakat_ytd'] = float(ytd_row.get('accumulated_zakat_ytd', 0.0))
                    payroll_inputs['other_reliefs_ytd'] = float(ytd_row.get('accumulated_tax_reliefs_ytd', 0.0))
                    payroll_inputs['individual_relief'] = float(ytd_row.get('individual_relief', 9000.0))
                    payroll_inputs['spouse_relief'] = float(ytd_row.get('spouse_relief', 0.0))
                    payroll_inputs['child_relief'] = float(ytd_row.get('child_relief_per_child', 2000.0))
                    payroll_inputs['child_count'] = int(ytd_row.get('child_count', 0) or 0)
                    payroll_inputs['disabled_individual'] = float(ytd_row.get('disabled_individual_relief', 0.0))
                    payroll_inputs['disabled_spouse'] = float(ytd_row.get('disabled_spouse_relief', 0.0))
                else:
                    # Fallback: reconstruct previous-month YTD by summing prior payroll_runs when accumulation table is empty
                    try:
                        cur_ref = datetime(period_year, period_month, 1)
                        gross_ytd = 0.0
                        epf_ytd = 0.0
                        pcb_ytd = 0.0
                        zakat_ytd = 0.0
                        # Pull minimal fields to sum — adapt to available identifier column
                        selector_cols = 'gross_salary, epf_employee, pcb, payroll_date'
                        identifier_filter = None
                        if employee_email and _probe_column_exists('payroll_runs', 'employee_email'):
                            selector_cols += ', employee_email'
                            identifier_filter = ('employee_email', employee_email)
                        elif employee_uuid and _probe_column_exists('payroll_runs', 'employee_id'):
                            selector_cols += ', employee_id'
                            identifier_filter = ('employee_id', employee_uuid)
                        else:
                            # Try generic 'email' column as last resort
                            if employee_email and _probe_column_exists('payroll_runs', 'email'):
                                selector_cols += ', email'
                                identifier_filter = ('email', employee_email)

                        q = supabase.table('payroll_runs').select(selector_cols)
                        if identifier_filter:
                            q = q.eq(identifier_filter[0], identifier_filter[1])
                        pr = q.execute()
                        rows = pr.data or []
                        for r in rows:
                            try:
                                dt = _parse_any_date(r.get('payroll_date'))
                                if dt and dt < cur_ref:
                                    gross_ytd += float(r.get('gross_salary', 0.0) or 0.0)
                                    epf_ytd += float(r.get('epf_employee', 0.0) or 0.0)
                                    pcb_ytd += float(r.get('pcb', 0.0) or 0.0)
                            except Exception:
                                continue
                        payroll_inputs.setdefault('accumulated_gross_ytd', gross_ytd)
                        payroll_inputs.setdefault('accumulated_epf_ytd', epf_ytd)
                        payroll_inputs.setdefault('accumulated_pcb_ytd', pcb_ytd)
                        payroll_inputs.setdefault('accumulated_zakat_ytd', zakat_ytd)
                        # other_reliefs_ytd defaults to 0.0 here; per-item reliefs are persisted via dedicated tables
                        if gross_ytd > 0.0 or epf_ytd > 0.0 or pcb_ytd > 0.0:
                            print("DEBUG: Reconstructed previous-month YTD from payroll_runs as fallback for PCB inputs")
                    except Exception as _recon_err:
                        print(f"DEBUG: Failed to reconstruct YTD from payroll_runs: {_recon_err}")
        except Exception as _ytd_err:
            print(f"DEBUG: YTD enrichment skipped due to error: {_ytd_err}")

    # Monthly deductions for current zakat
        monthly_deductions = payroll_inputs.get('monthly_deductions')
        if tax_resident_status == 'Resident' and not monthly_deductions and employee_uuid:
            try:
                monthly_deductions = get_monthly_deductions(employee_uuid, period_year, period_month)
                payroll_inputs['monthly_deductions'] = monthly_deductions
            except Exception as _md_err:
                print(f"DEBUG: Could not load monthly deductions: {_md_err}")

        try:
            current_month_zakat = 0.0
            if tax_resident_status == 'Resident' and isinstance(monthly_deductions, dict):
                current_month_zakat = float(monthly_deductions.get('zakat_monthly', 0.0) or 0.0)
            payroll_inputs['current_month_zakat'] = current_month_zakat
        except Exception as _cz:
            print(f"DEBUG: Could not set current month zakat: {_cz}")

        # Derive child_count from payroll_configurations children data when still missing/zero
        try:
            def _to_list(val):
                if isinstance(val, list):
                    return val
                if isinstance(val, str):
                    import json as _json
                    try:
                        dec = _json.loads(val)
                        return dec if isinstance(dec, list) else []
                    except Exception:
                        return []
                return []

            _cc = payroll_inputs.get('child_count')
            try:
                _cc = int(_cc or 0)
            except Exception:
                _cc = 0
            if tax_resident_status == 'Resident' and _cc <= 0 and employee_uuid:
                try:
                    cfg = supabase.table('payroll_configurations').select('individual_children, children_data') \
                        .eq('employee_id', employee_uuid).limit(1).execute()
                    row = (cfg.data or [None])[0]
                    if row:
                        lst = []
                        lst += _to_list(row.get('individual_children'))
                        if not lst:
                            lst = _to_list(row.get('children_data'))
                        if lst:
                            full_claim = 0
                            for ch in lst:
                                try:
                                    share = str(ch.get('custody_percentage', '') or '').strip().lower()
                                    if share.startswith('100'):  # "100% (Full claim)"
                                        full_claim += 1
                                except Exception:
                                    continue
                            if full_claim > 0:
                                payroll_inputs['child_count'] = int(full_claim)
                except Exception as _cfgc:
                    print(f"DEBUG: Could not derive child_count from payroll_configurations: {_cfgc}")
        except Exception as _dch:
            print(f"DEBUG: Derive child_count block failed: {_dch}")

        # Spouse not working: default spouse relief and spouse rebate eligibility
        try:
            ms = str(employee_data.get('marital_status', '') or '').strip().lower()
            sw = employee_data.get('spouse_working')
            # Normalize spouse_working to boolean True/False when possible
            sw_norm = None
            if isinstance(sw, bool):
                sw_norm = sw
            elif isinstance(sw, str):
                _s = sw.strip().lower()
                if _s in ('yes', 'y', 'true', '1'): sw_norm = True
                elif _s in ('no', 'n', 'false', '0'): sw_norm = False
            # Apply only if married and spouse not working
            if 'married' in ms and sw_norm is False:
                try:
                    default_spouse_relief = float((tax_relief_config or {}).get('spouse_relief', 4000.0) or 4000.0)
                except Exception:
                    default_spouse_relief = 4000.0
                # Only set if not already provided by YTD or explicit inputs
                if float(payroll_inputs.get('spouse_relief', 0.0) or 0.0) <= 0.0:
                    payroll_inputs['spouse_relief'] = default_spouse_relief
                # Mark spouse rebate as eligible (PCB will apply within rebate threshold)
                if 'spouse_rebate_eligible' not in payroll_inputs:
                    payroll_inputs['spouse_rebate_eligible'] = True
        except Exception as _spr:
            print(f"DEBUG: Spouse-not-working default relief failed: {_spr}")

        # OKU mapping (Disabled self/spouse): infer flags and apply configured relief amounts when not already set
        try:
            # Load configured amounts from LHDN config (fallbacks: self=6000, spouse=5000)
            try:
                _lhdn_cfg = get_lhdn_tax_config('default') or {}
                _disabled_self_amt = float(_lhdn_cfg.get('b4_individual_disability_max', 6000.0) or 6000.0)
                # Align disabled spouse relief to RM6,000 when config table is missing
                _disabled_spouse_amt = float(_lhdn_cfg.get('b15_disabled_spouse_relief_max', 6000.0) or 6000.0)
            except Exception:
                _disabled_self_amt = 6000.0
                _disabled_spouse_amt = 6000.0

            # Detect flags priority: payroll_configurations.tax_relief_data -> employee_data flags
            oku_self: Optional[bool] = None
            oku_spouse: Optional[bool] = None
            if employee_uuid:
                try:
                    _cfg = supabase.table('payroll_configurations').select('tax_relief_data').eq('employee_id', employee_uuid).limit(1).execute()
                    if _cfg and _cfg.data:
                        _snap = _cfg.data[0].get('tax_relief_data') or {}
                        if isinstance(_snap, dict):
                            if 'is_individual_disabled' in _snap:
                                oku_self = bool(_snap.get('is_individual_disabled'))
                            if 'is_spouse_disabled' in _snap:
                                oku_spouse = bool(_snap.get('is_spouse_disabled'))
                except Exception as _cfgerr:
                    print(f"DEBUG: Could not read payroll_configurations.tax_relief_data for OKU flags: {_cfgerr}")
            # Fallback to employee_data flags if still None
            if oku_self is None:
                try:
                    oku_self = bool(employee_data.get('is_individual_disabled'))
                except Exception:
                    oku_self = False
            if oku_spouse is None:
                try:
                    oku_spouse = bool(employee_data.get('is_spouse_disabled'))
                except Exception:
                    oku_spouse = False

            # Apply numeric reliefs only if currently zero or missing
            try:
                cur_self_relief = float(payroll_inputs.get('disabled_individual', 0.0) or 0.0)
            except Exception:
                cur_self_relief = 0.0
            try:
                cur_spouse_relief = float(payroll_inputs.get('disabled_spouse', 0.0) or 0.0)
            except Exception:
                cur_spouse_relief = 0.0

            if oku_self and cur_self_relief <= 0.0:
                payroll_inputs['disabled_individual'] = _disabled_self_amt
            if oku_spouse and cur_spouse_relief <= 0.0:
                payroll_inputs['disabled_spouse'] = _disabled_spouse_amt
        except Exception as _oku:
            print(f"DEBUG: OKU mapping failed: {_oku}")

        # Compute SOCSO+EIS LP1 (B20) with RM350 annual cap and include in LP1 pipeline
        socso_eis_lp1_this_month = 0.0
        try:
            # Determine annual cap from LHDN config if available; fallback RM350
            try:
                _lhdn_cfg2 = get_lhdn_tax_config('default') or {}
                # Prefer explicit B20 cap key; fall back to a generic key if present; else 350.0
                socso_eis_annual_cap = float(
                    _lhdn_cfg2.get('b20_socso_eis_annual_cap', _lhdn_cfg2.get('socso_eis_annual_cap', 350.0))
                    or 350.0
                )
            except Exception:
                socso_eis_annual_cap = 350.0
            # Sum YTD SOCSO+EIS LP1 previously CLAIMED (preferred sources), else fallback to contributions
            ytd_socso_eis_claimed = 0.0
            try:
                if employee_uuid and _probe_table_exists('tp1_monthly_details') and _probe_column_exists('tp1_monthly_details', 'socso_eis_lp1_monthly'):
                    rows = (
                        supabase.table('tp1_monthly_details')
                        .select('year, month, socso_eis_lp1_monthly')
                        .eq('employee_id', employee_uuid)
                        .eq('year', period_year)
                        .execute()
                    ).data or []
                    for r in rows:
                        try:
                            mm = int(r.get('month') or 0)
                            if 1 <= mm < period_month:
                                ytd_socso_eis_claimed += float(r.get('socso_eis_lp1_monthly', 0.0) or 0.0)
                        except Exception:
                            continue
            except Exception as _tp1ytd:
                print(f"DEBUG: Failed to sum socso_eis_lp1_monthly from tp1_monthly_details: {_tp1ytd}")

            # Secondary source: payroll_monthly_deductions.socso_eis_lp1_monthly if present
            if ytd_socso_eis_claimed <= 0.0:
                try:
                    if employee_uuid and _probe_table_exists('payroll_monthly_deductions') and _probe_column_exists('payroll_monthly_deductions', 'socso_eis_lp1_monthly'):
                        rows = (
                            supabase.table('payroll_monthly_deductions')
                            .select('year, month, socso_eis_lp1_monthly')
                            .eq('employee_id', employee_uuid)
                            .eq('year', period_year)
                            .execute()
                        ).data or []
                        for r in rows:
                            try:
                                mm = int(r.get('month') or 0)
                                if 1 <= mm < period_month:
                                    ytd_socso_eis_claimed += float(r.get('socso_eis_lp1_monthly', 0.0) or 0.0)
                            except Exception:
                                continue
                except Exception as _mdytd:
                    print(f"DEBUG: Failed to sum socso_eis_lp1_monthly from payroll_monthly_deductions: {_mdytd}")

            # Final fallback: infer from contributions in payroll_information (less precise but safe upper bound)
            if ytd_socso_eis_claimed <= 0.0:
                try:
                    if employee_id and _probe_table_exists('payroll_information'):
                        resp = (
                            supabase.table('payroll_information')
                            .select('employee_id, month_year, socso_employee, eis_employee')
                            .eq('employee_id', employee_id)
                            .execute()
                        )
                        if resp.data:
                            for r in resp.data:
                                try:
                                    mm_str, yy_str = str(r.get('month_year','')).split('/') if '/' in str(r.get('month_year','')) else (None,None)
                                    if mm_str and yy_str and int(yy_str) == period_year and int(mm_str) < period_month:
                                        ytd_socso_eis_claimed += float(r.get('socso_employee', 0.0) or 0.0) + float(r.get('eis_employee', 0.0) or 0.0)
                                except Exception:
                                    continue
                except Exception as _ytdse:
                    print(f"DEBUG: Could not compute YTD SOCSO+EIS for LP1 (fallback): {_ytdse}")

            # Inject elapsed months' B20 into other_reliefs_ytd only when we don't already have a YTD total
            # from the accumulation table. This avoids double-counting B20 when January (or prior months)
            # have already been saved and accumulated_tax_reliefs_ytd includes LP1 values.
            try:
                _existing_or_ytd = float(payroll_inputs.get('other_reliefs_ytd', 0.0) or 0.0)
                # Clamp YTD claims to annual cap
                _ytd_b20_capped = max(0.0, min(ytd_socso_eis_claimed, socso_eis_annual_cap))
                if _existing_or_ytd <= 0.0:
                    payroll_inputs['other_reliefs_ytd'] = round(_ytd_b20_capped, 2)
                else:
                    # YTD already present (likely from payroll_ytd_accumulated) — do not add B20 again
                    payroll_inputs['other_reliefs_ytd'] = round(_existing_or_ytd, 2)
            except Exception as _inytd:
                print(f"DEBUG: Could not fold B20 YTD into other_reliefs_ytd: {_inytd}")

            # Current month amount that could be claimed
            current_socso_eis = float(socso_employee or 0.0) + float(eis_employee or 0.0)
            remaining_cap = max(0.0, socso_eis_annual_cap - ytd_socso_eis_claimed)
            socso_eis_lp1_this_month = min(current_socso_eis, remaining_cap)

            # Do NOT persist SOCSO+EIS LP1 into monthly_deductions to avoid double counting.
            # We'll compute LP1 for PCB as: base other_reliefs_monthly + socso_eis_lp1_this_month.
            try:
                print(f"🎯 B20 SOCSO+EIS LP1 this month: RM{socso_eis_lp1_this_month:.2f} (cap remaining RM{remaining_cap:.2f})")
            except Exception:
                pass
        except Exception as _se_lp1_err:
            print(f"DEBUG: Error computing SOCSO+EIS LP1: {_se_lp1_err}")
            socso_eis_lp1_this_month = 0.0

        # LP1 for PCB: derive from detailed TP1 claims if provided; else fallback to monthly_deductions.
        # Then add SOCSO+EIS portion (pcb-only) to obtain PCB LP1. Persist only base (non-pcb-only) part.
        try:
            tp1_claims = payroll_inputs.get('tp1_relief_claims')  # expected dict of internal keys
            # If not provided by caller, try to load saved claims for this employee/period
            if (not isinstance(tp1_claims, dict) or not tp1_claims) and employee_uuid:
                try:
                    if _probe_table_exists('tp1_monthly_details'):
                        _q = supabase.table('tp1_monthly_details').select('details') \
                            .eq('employee_id', employee_uuid).eq('year', period_year).eq('month', period_month).limit(1).execute()
                        _rows = getattr(_q, 'data', None) or []
                        if _rows and isinstance(_rows[0].get('details'), dict):
                            tp1_claims = _rows[0]['details']
                            payroll_inputs['tp1_relief_claims'] = tp1_claims
                            try:
                                print(f"DEBUG: Loaded TP1 claims from DB for {period_month:02d}/{period_year} (items={len(tp1_claims)})")
                            except Exception:
                                pass
                except Exception as _tp1db_err:
                    print(f"DEBUG: Could not load TP1 claims from DB: {_tp1db_err}")
            original_tp1_claims = dict(tp1_claims) if isinstance(tp1_claims, dict) else None
            ytd_rows = []
            # YTD & cycle adjustment (if table exists and claims provided)
            if isinstance(tp1_claims, dict) and tp1_claims and employee_uuid:
                try:
                    if _probe_table_exists('relief_ytd_accumulated'):
                        ytd_rows = supabase.table('relief_ytd_accumulated').select('item_key, claimed_ytd, last_claim_year').eq('employee_id', employee_uuid).eq('year', period_year).execute().data or []
                        from core.tax_relief_catalog import adjust_claims_for_ytd_and_cycles
                        adjusted = adjust_claims_for_ytd_and_cycles(tp1_claims, ytd_rows, period_year)
                        payroll_inputs['tp1_relief_claims_adjusted'] = adjusted
                        tp1_claims = adjusted
                except Exception as _adj_err:
                    print(f"DEBUG: YTD/cycle adjust failed (comprehensive payroll), proceeding without: {_adj_err}")
            base_lp1 = 0.0
            per_item_applied = {}
            comp = {}
            total_lp1_pcb = None  # includes pcb_only items from TP1 claims if any
            if isinstance(tp1_claims, dict) and tp1_claims:
                try:
                    from core.tax_relief_catalog import (
                        compute_lp1_totals,
                        compute_applied_and_ytd_updates,
                        load_relief_overrides_from_db,
                        load_relief_group_overrides_from_db,
                        get_effective_items
                    )
                    try:
                        _relief_overrides = load_relief_overrides_from_db(supabase)
                    except Exception:
                        _relief_overrides = {}
                    try:
                        _group_overrides = load_relief_group_overrides_from_db(supabase)
                    except Exception:
                        _group_overrides = {}
                    _catalog = get_effective_items(_relief_overrides)
                    comp = compute_lp1_totals(tp1_claims, items_catalog=_catalog, group_overrides=_group_overrides)
                    # Base (cash) portion excludes pcb_only (e.g., SOCSO/EIS)
                    base_lp1 = float(comp.get('total_lp1_cash', 0.0) or 0.0)
                    total_lp1_pcb = float(comp.get('total_lp1_pcb', 0.0) or 0.0)
                    per_item_applied = comp.get('per_item', {})
                    try:
                        print(f"DEBUG: TP1 detailed LP1 derived base={base_lp1:.2f} (cash), pcb_total={total_lp1_pcb:.2f}")
                    except Exception:
                        pass
                except Exception as _tp1calc:
                    print(f"DEBUG: TP1 compute_lp1_totals failed, fallback to monthly_deductions: {_tp1calc}")
                    base_lp1 = _derive_other_reliefs_current_from_monthly(monthly_deductions)
            else:
                # Backward compatibility
                explicit_base_lp1 = payroll_inputs.get('other_reliefs_current', None)
                if explicit_base_lp1 is not None:
                    base_lp1 = float(explicit_base_lp1 or 0.0)
                else:
                    base_lp1 = _derive_other_reliefs_current_from_monthly(monthly_deductions)

            # Compose LP1 for PCB:
            # - Use total_lp1_pcb (includes any items marked PCB? in overrides) when available
            # - Add SOCSO+EIS pcb-only portion if it's not already present in TP1 claims
            contains_socso_claim = isinstance(tp1_claims, dict) and 'socso_eis_lp1' in tp1_claims
            if total_lp1_pcb is not None:
                lp1_for_pcb = float(total_lp1_pcb)
                if not contains_socso_claim:
                    lp1_for_pcb += float(socso_eis_lp1_this_month or 0.0)
            else:
                lp1_for_pcb = float(base_lp1 or 0.0) + float(socso_eis_lp1_this_month or 0.0)
            payroll_inputs['other_reliefs_current'] = lp1_for_pcb
            payroll_inputs['lp1_base_cash'] = base_lp1
            if per_item_applied:
                payroll_inputs['tp1_items_applied'] = per_item_applied

            # Persist base LP1 + zakat only
            if employee_uuid:
                md_payload = {
                    'zakat_monthly': float(payroll_inputs.get('current_month_zakat', 0.0) or 0.0),
                    'other_reliefs_monthly': float(base_lp1 or 0.0),
                }
                if isinstance(monthly_deductions, dict):
                    if 'religious_travel_monthly' in monthly_deductions:
                        md_payload['religious_travel_monthly'] = float(monthly_deductions.get('religious_travel_monthly') or 0.0)
                    if 'other_deductions_amount' in monthly_deductions:
                        md_payload['other_deductions_amount'] = float(monthly_deductions.get('other_deductions_amount') or 0.0)
                try:
                    upsert_monthly_deductions(employee_uuid, period_year, period_month, md_payload)
                except Exception as _lp1_up:
                    print(f"DEBUG: Failed to upsert monthly deductions (LP1/zakat): {_lp1_up}")

                # Optional TP1 details table: store snapshot + base + socso/eis component
                try:
                    details_snapshot = original_tp1_claims if original_tp1_claims is not None else (monthly_deductions if isinstance(monthly_deductions, dict) else {})
                    meta_extra = {
                        'other_reliefs_monthly': float(base_lp1 or 0.0),
                        'socso_eis_lp1_monthly': float(socso_eis_lp1_this_month or 0.0),
                        'zakat_monthly': float(md_payload['zakat_monthly'] or 0.0),
                    }
                    if total_lp1_pcb is not None:
                        meta_extra['lp1_total_for_pcb'] = float(lp1_for_pcb)
                    if payroll_inputs.get('tp1_relief_claims_adjusted'):
                        meta_extra['tp1_relief_claims_adjusted'] = payroll_inputs['tp1_relief_claims_adjusted']
                    if per_item_applied:
                        meta_extra['tp1_items_applied'] = per_item_applied
                    upsert_tp1_monthly_details(
                        employee_uuid,
                        period_year,
                        period_month,
                        details_snapshot,
                        meta_extra
                    )
                except Exception as _tp1:
                    print(f"DEBUG: TP1 monthly details upsert skipped/failed: {_tp1}")

                # Persist YTD relief accumulation (per-item) if we have applied items & table exists
                try:
                    if per_item_applied and _probe_table_exists('relief_ytd_accumulated'):
                        from core.tax_relief_catalog import compute_applied_and_ytd_updates
                        ytd_updates = compute_applied_and_ytd_updates(per_item_applied, ytd_rows, period_year)
                        if ytd_updates:
                            # Upsert each item (assuming RPC or upsert available)
                            for row in ytd_updates:
                                payload = {
                                    'employee_id': employee_uuid,
                                    'year': period_year,
                                    'item_key': row['item_key'],
                                    'claimed_ytd': row['claimed_ytd'],
                                    'last_claim_year': row.get('last_claim_year'),
                                }
                                try:
                                    # Use composite unique key to perform a true upsert instead of hitting the PK (id)
                                    # This avoids duplicate key errors on (employee_id, year, item_key)
                                    supabase.table('relief_ytd_accumulated').upsert(
                                        payload,
                                        on_conflict="employee_id,year,item_key",
                                    ).execute()
                                except Exception as _yu:
                                    print(f"DEBUG: Upsert relief_ytd_accumulated failed for {payload.get('item_key')}: {_yu}")
                except Exception as _ytdp:
                    print(f"DEBUG: Relief YTD persistence skipped/failed: {_ytdp}")
        except Exception as _lp1_err:
            print(f"DEBUG: Could not derive LP1 (detailed TP1 path): {_lp1_err}")

        # Optional: enable detailed PCB debug logs via environment variable
        try:
            if str(os.environ.get('HRMS_PCB_DEBUG', '0')).strip() == '1':
                payroll_inputs['debug_pcb'] = True
        except Exception:
            pass

        # PCB
        if tax_resident_status == 'Resident':
            pcb_tax = calculate_lhdn_pcb_official(
                payroll_inputs,
                gross_income,
                epf_employee,
                tax_rates_config,
                month_year,
            )
        else:
            non_resident_rate = tax_rates_config.get('non_resident_rate', 30.0) / 100.0
            pcb_tax = taxable_income * non_resident_rate

        # Other deductions
        other_deductions = payroll_inputs.get('other_deductions', {})
        total_other_deductions = sum(other_deductions.values()) if other_deductions else 0.0
        total_monthly_deductions = 0.0
        if tax_resident_status == 'Resident':
            monthly_deductions = payroll_inputs.get('monthly_deductions', monthly_deductions or {})
            total_monthly_deductions = sum(monthly_deductions.values()) if monthly_deductions else 0.0

        # Only include cash monthly deductions in net salary (exclude LP1 fields like other_reliefs_monthly, socso_eis_lp1_monthly)
        cash_md = 0.0
        try:
            md = payroll_inputs.get('monthly_deductions', {}) if tax_resident_status == 'Resident' else {}
            if isinstance(md, dict):
                cash_md = float(md.get('zakat_monthly', 0.0) or 0.0) + float(md.get('other_deductions_amount', 0.0) or 0.0)
        except Exception:
            cash_md = 0.0
        total_deductions = epf_employee + socso_employee + eis_employee + pcb_tax + total_other_deductions + cash_md
        if tax_resident_status == 'Resident':
            try:
                print(f"   Monthly Deductions (cash to subtract): RM{cash_md:.2f} (zakat + other_deductions_amount). Excluded LP1 fields from net pay.")
            except Exception:
                pass
        net_salary = gross_income - total_deductions

        # Build a YTD snapshot (as of previous month) from inputs we enriched earlier
        try:
            _mm = int(str(month_year).split('/')[0]) if isinstance(month_year, str) and '/' in month_year else 0
            _yy = int(str(month_year).split('/')[1]) if isinstance(month_year, str) and '/' in month_year else 0
        except Exception:
            from datetime import date as _date
            _today = _date.today()
            _mm, _yy = _today.month, _today.year
        _prev_m = 12 if _mm == 1 else max(1, _mm - 1)
        _prev_y = _yy - 1 if _mm == 1 else _yy
        ytd_snapshot = {
            'as_of_year': _prev_y,
            'as_of_month': _prev_m,
            'gross': float(payroll_inputs.get('accumulated_gross_ytd', 0.0) or 0.0),
            'epf_employee': float(payroll_inputs.get('accumulated_epf_ytd', 0.0) or 0.0),
            'pcb': float(payroll_inputs.get('accumulated_pcb_ytd', 0.0) or 0.0),
            'zakat': float(payroll_inputs.get('accumulated_zakat_ytd', 0.0) or 0.0),
            'other_reliefs': float(payroll_inputs.get('other_reliefs_ytd', payroll_inputs.get('other_reliefs_ytd', 0.0)) or 0.0),
        }

        payroll_data = {
            'employee_id': employee_id,
            'employee_email': employee_email,
            'employee_name': employee_name,
            'month_year': month_year,
            'basic_salary': basic_salary,
            'allowances': allowances,
            'overtime_pay': overtime_pay,
            'commission': commission,
            'bonus': bonus,
            'gross_income': gross_income,
            'epf_employee': epf_employee,
            'epf_employer': epf_employer,
            'socso_employee': socso_employee,
            'socso_employer': socso_employer,
            'eis_employee': eis_employee,
            'eis_employer': eis_employer,
            'pcb_tax': pcb_tax,
            'monthly_deductions': monthly_deductions if tax_resident_status == 'Resident' else {},
            'annual_tax_reliefs': payroll_inputs.get('annual_tax_reliefs', {}) if tax_resident_status == 'Resident' else {},
            'other_deductions': other_deductions,
            'total_deductions': total_deductions,
            'net_salary': net_salary,
            'tax_resident_status': tax_resident_status,
            'ytd_accumulated': ytd_snapshot,
            'calculation_details': {
                'tax_rates_config_used': tax_rates_config.get('config_name', 'default'),
                'tax_relief_config_used': tax_relief_config.get('config_name', 'default'),
                'epf_ceiling_applied': epf_ceiling,
                'socso_ceiling_applied': socso_ceiling,
                'eis_ceiling_applied': eis_ceiling,
                'epf_rate_source': epf_rate_source,
                'pcb_method': 'lhdn_official' if tax_resident_status == 'Resident' else 'non_resident_flat',
                'annual_taxable_income': taxable_income * 12 if tax_resident_status == 'Resident' else 0,
                'annual_tax_calculated': pcb_tax * 12 if tax_resident_status == 'Resident' else pcb_tax * 12,
                'ytd_source': 'payroll_ytd_accumulated' if employee_email else 'none',
            },
        }

        return payroll_data
    except Exception as e:
        print(f"DEBUG: Error calculating comprehensive payroll: {e}")
        return {}

def calculate_progressive_tax(annual_income: float, tax_brackets: Dict) -> float:
    """Calculate progressive tax based on Malaysia's tax brackets"""
    try:
        total_tax = 0.0
        remaining_income = annual_income
        
        # Define standard Malaysian tax brackets if not provided
        if not tax_brackets:
            tax_brackets = {
                '0-5000': 0.0,
                '5001-20000': 1.0,
                '20001-35000': 3.0,
                '35001-50000': 8.0,
                '50001-70000': 14.0,
                '70001-100000': 21.0,
                '100001-400000': 24.0,
                '400001-600000': 24.5,
                '600001-2000000': 25.0,
                '2000001+': 30.0
            }
        
        # Process each tax bracket
        brackets = [
            (5000, 0.0),      # RM0 - RM5,000
            (15000, 1.0),     # RM5,001 - RM20,000
            (15000, 3.0),     # RM20,001 - RM35,000
            (15000, 8.0),     # RM35,001 - RM50,000
            (20000, 14.0),    # RM50,001 - RM70,000
            (30000, 21.0),    # RM70,001 - RM100,000
            (300000, 24.0),   # RM100,001 - RM400,000
            (200000, 24.5),   # RM400,001 - RM600,000
            (1400000, 25.0),  # RM600,001 - RM2,000,000
            (float('inf'), 30.0)  # RM2,000,001+
        ]
        
        for bracket_size, rate in brackets:
            if remaining_income <= 0:
                break
                
            taxable_in_bracket = min(remaining_income, bracket_size)
            tax_for_bracket = taxable_in_bracket * (rate / 100)
            total_tax += tax_for_bracket
            remaining_income -= taxable_in_bracket
        
        return total_tax
        
    except Exception as e:
        print(f"DEBUG: Error calculating progressive tax: {e}")
        return 0.0

def process_payroll_and_generate_payslip(employee_data: Dict, payroll_inputs: Dict, month_year: str, generate_pdf: bool = True) -> Dict:
    """Complete payroll processing: calculate, save to database, and generate payslip"""
    try:
        # Respect payroll_status gating: do not process if employee is marked inactive for payroll
        try:
            ps = str((employee_data or {}).get('payroll_status') or '').strip().lower()
            if ps and 'inactive' in ps:
                ident = (employee_data or {}).get('employee_id') or (employee_data or {}).get('email') or (employee_data or {}).get('full_name')
                msg = f"Payroll is inactive for employee {ident}. Set Payroll Status to 'Active Payroll' to enable processing."
                print(f"⏭️  {msg}")
                # Persist skip record with month_year mapped to first day of month
                try:
                    _my = str(month_year)
                    if '/' in _my:
                        mm = int(_my.split('/')[0]); yy = int(_my.split('/')[1])
                        _date = f"{yy}-{mm:02d}-01"
                    else:
                        _date = _my  # if already a date-like string
                    from datetime import datetime as _dt
                    supabase.table('payroll_run_skips').insert({
                        'employee_id': (employee_data or {}).get('id'),
                        'payroll_date': _date,
                        'reason': f"payroll_status='{(employee_data or {}).get('payroll_status')}'",
                        'created_at': _dt.now().isoformat()
                    }).execute()
                except Exception as _sk3:
                    print(f"DEBUG: Failed to persist skip (single run): {_sk3}")
                return {'success': False, 'error': msg, 'skipped': True}
        except Exception:
            pass
        # Respect Employment Status gating: skip for Inactive/Resigned/Terminated/Retired
        try:
            es = str((employee_data or {}).get('status') or '').strip().lower()
            if es in ('inactive', 'resigned', 'terminated', 'retired') or any(k in es for k in ('inactive','resigned','terminated','retired')):
                ident = (employee_data or {}).get('employee_id') or (employee_data or {}).get('email') or (employee_data or {}).get('full_name')
                msg = f"Employment status '{(employee_data or {}).get('status')}' blocks payroll for {ident}. Set Status to 'Active' to enable processing."
                print(f"⏭️  {msg}")
                # Persist skip record with month_year mapped to first day of month
                try:
                    _my = str(month_year)
                    if '/' in _my:
                        mm = int(_my.split('/')[0]); yy = int(_my.split('/')[1])
                        _date = f"{yy}-{mm:02d}-01"
                    else:
                        _date = _my
                    from datetime import datetime as _dt
                    supabase.table('payroll_run_skips').insert({
                        'employee_id': (employee_data or {}).get('id'),
                        'payroll_date': _date,
                        'reason': f"employment status='{(employee_data or {}).get('status')}'",
                        'created_at': _dt.now().isoformat()
                    }).execute()
                except Exception as _sk4:
                    print(f"DEBUG: Failed to persist skip (single run, status): {_sk4}")
                return {'success': False, 'error': msg, 'skipped': True}
        except Exception:
            pass
        # Calculate comprehensive payroll
        payroll_data = calculate_comprehensive_payroll(employee_data, payroll_inputs, month_year)
        
        if not payroll_data:
            return {'success': False, 'error': 'Failed to calculate payroll'}
        
        # Save to database
        save_success = save_payroll_information(payroll_data)
        
        if not save_success:
            return {'success': False, 'error': 'Failed to save payroll to database'}
        
        result = {'success': True, 'payroll_data': payroll_data}

        # After saving payroll, update YTD accumulation table for next runs
        try:
            _email = payroll_data.get('employee_email') or (employee_data or {}).get('email')
            if _email and isinstance(month_year, str) and '/' in month_year:
                _mm = int(month_year.split('/')[0])
                _yy = int(month_year.split('/')[1])
                _ = update_ytd_after_payroll(_email, _yy, _mm, payroll_data, payroll_inputs)
        except Exception as _ytd_upd_err:
            # Non-fatal: payroll already saved; log and continue
            print(f"DEBUG: Skipped YTD update due to error: {_ytd_upd_err}")
        
        # Generate payslip PDF if requested
        if generate_pdf:
            pdf_path = generate_payslip_pdf(payroll_data)
            if pdf_path:
                result['payslip_pdf'] = pdf_path
            else:
                result['pdf_warning'] = 'Payroll saved but PDF generation failed'
        
        return result
        
    except Exception as e:
        print(f"DEBUG: Error processing payroll: {e}")
        return {'success': False, 'error': str(e)}


def update_ytd_after_payroll(employee_email: str, year: int, month: int, payroll_data: Dict, payroll_inputs: Optional[Dict] = None) -> bool:
    """
    Update YTD accumulated values for the given employee/year/month after a successful payroll.
    This sets the current month's YTD row to (previous month YTD + current month amounts),
    so re-running the same payroll month remains idempotent.
    """
    try:
        # Fetch previous month YTD (treat as zeros if not found)
        prev_month = 12 if month == 1 else (month - 1)
        prev_year = year - 1 if month == 1 else year

        prev_resp = supabase.table("payroll_ytd_accumulated").select("*") \
            .eq("employee_email", employee_email) \
            .eq("year", prev_year) \
            .eq("month", prev_month) \
            .execute()

        prev_row = prev_resp.data[0] if prev_resp and prev_resp.data else {}

        def _prev(col: str) -> float:
            try:
                return float(prev_row.get(col, 0.0) or 0.0)
            except Exception:
                return 0.0

        # Current month metrics from saved payroll_data
        allowances_dict = payroll_data.get('allowances') or {}
        allowances_total = 0.0
        try:
            allowances_total = float(sum(float(v or 0.0) for v in allowances_dict.values()))
        except Exception:
            allowances_total = 0.0

        gross_income = float(payroll_data.get('gross_income', 0.0) or 0.0)
        net_salary = float(payroll_data.get('net_salary', 0.0) or 0.0)
        basic_salary = float(payroll_data.get('basic_salary', 0.0) or 0.0)
        overtime_pay = float(payroll_data.get('overtime_pay', 0.0) or 0.0)
        bonus = float(payroll_data.get('bonus', 0.0) or 0.0)

        epf_emp = float(payroll_data.get('epf_employee', 0.0) or 0.0)
        epf_empr = float(payroll_data.get('epf_employer', 0.0) or 0.0)
        socso_emp = float(payroll_data.get('socso_employee', 0.0) or 0.0)
        socso_empr = float(payroll_data.get('socso_employer', 0.0) or 0.0)
        eis_emp = float(payroll_data.get('eis_employee', 0.0) or 0.0)
        eis_empr = float(payroll_data.get('eis_employer', 0.0) or 0.0)
        pcb_tax = float(payroll_data.get('pcb_tax', 0.0) or 0.0)

        # Current month zakat and other reliefs (if provided in inputs)
        current_month_zakat = 0.0
        other_reliefs_current = 0.0
        try:
            if isinstance(payroll_inputs, dict):
                current_month_zakat = float(payroll_inputs.get('current_month_zakat', 0.0) or 0.0)
                other_reliefs_current = float(payroll_inputs.get('other_reliefs_current', 0.0) or 0.0)
        except Exception:
            pass

        # Other deductions current month (optional aggregate)
        other_deductions_total = 0.0
        try:
            _od = payroll_data.get('other_deductions') or {}
            other_deductions_total = float(sum(float(v or 0.0) for v in _od.values()))
        except Exception:
            other_deductions_total = 0.0

        new_values = {
            'accumulated_gross_salary_ytd': _prev('accumulated_gross_salary_ytd') + gross_income,
            'accumulated_net_salary_ytd': _prev('accumulated_net_salary_ytd') + net_salary,
            'accumulated_basic_salary_ytd': _prev('accumulated_basic_salary_ytd') + basic_salary,
            'accumulated_allowances_ytd': _prev('accumulated_allowances_ytd') + allowances_total,
            'accumulated_overtime_ytd': _prev('accumulated_overtime_ytd') + overtime_pay,
            'accumulated_bonus_ytd': _prev('accumulated_bonus_ytd') + bonus,

            'accumulated_epf_employee_ytd': _prev('accumulated_epf_employee_ytd') + epf_emp,
            'accumulated_epf_employer_ytd': _prev('accumulated_epf_employer_ytd') + epf_empr,
            'accumulated_socso_employee_ytd': _prev('accumulated_socso_employee_ytd') + socso_emp,
            'accumulated_socso_employer_ytd': _prev('accumulated_socso_employer_ytd') + socso_empr,
            'accumulated_eis_employee_ytd': _prev('accumulated_eis_employee_ytd') + eis_emp,
            'accumulated_eis_employer_ytd': _prev('accumulated_eis_employer_ytd') + eis_empr,

            'accumulated_pcb_ytd': _prev('accumulated_pcb_ytd') + pcb_tax,
            'accumulated_zakat_ytd': _prev('accumulated_zakat_ytd') + current_month_zakat,
            'accumulated_tax_reliefs_ytd': _prev('accumulated_tax_reliefs_ytd') + other_reliefs_current,
            'accumulated_other_deductions_ytd': _prev('accumulated_other_deductions_ytd') + other_deductions_total,
        }

        # Build relief settings if provided (kept stable for the year)
        if isinstance(payroll_inputs, dict):
            relief_fields = {
                'individual_relief': payroll_inputs.get('individual_relief'),
                'spouse_relief': payroll_inputs.get('spouse_relief'),
                'child_relief_per_child': payroll_inputs.get('child_relief'),
                'child_count': payroll_inputs.get('child_count'),
                'disabled_individual_relief': payroll_inputs.get('disabled_individual'),
                'disabled_spouse_relief': payroll_inputs.get('disabled_spouse'),
            }
            for k, v in relief_fields.items():
                if v is not None:
                    new_values[k] = v

        # Ensure current month row exists, then set it to previous+current
        cur_resp = supabase.table("payroll_ytd_accumulated").select("id").eq("employee_email", employee_email).eq("year", year).eq("month", month).execute()
        if cur_resp and cur_resp.data:
            upd = supabase.table("payroll_ytd_accumulated").update(new_values) \
                .eq("employee_email", employee_email) \
                .eq("year", year) \
                .eq("month", month) \
                .execute()
            return bool(upd and upd.data)
        else:
            ins_payload = { 'employee_email': employee_email, 'year': year, 'month': month }
            ins_payload.update(new_values)
            ins = supabase.table("payroll_ytd_accumulated").insert(ins_payload).execute()
            return bool(ins and ins.data)

    except Exception as e:
        print(f"DEBUG: Error updating YTD accumulation: {e}")
        return False

def login_user_by_username(username: str, password: str):
    """Authenticate a user by username with optional lockout behavior.

    Returns a dict: {"success": bool, "role": Optional[str], "locked_until": Optional[str], "email": Optional[str]}.
    """
    try:
        username_norm = (username or '').lower()
        cols = "username, email, password, role"
        if user_logins_has_lockout_columns():
            cols = "username, email, password, role, failed_attempts, locked_until"

        response = supabase.table("user_logins").select(cols).eq("username", username_norm).execute()
        if not response.data:
            _log_security_event('login_failure', user_email=username_norm, success=False, error_message='Unknown username')
            return {"success": False, "role": None}

        user = response.data[0]

        # Check lockout
        if 'locked_until' in user and user.get('locked_until'):
            lu = _parse_timestamptz(user.get('locked_until'))
            now_utc = datetime.now(pytz.UTC)
            if lu and lu > now_utc:
                _log_security_event('login_failure', user_email=username_norm, success=False,
                                    error_message=f'Account locked until {lu.isoformat()}',
                                    details={'locked_until': lu.isoformat()})
                return {"success": False, "role": None, "locked_until": lu.isoformat()}

        stored_password = user["password"].encode('utf-8')
        if bcrypt.checkpw(password.encode('utf-8'), stored_password):
            # Successful login; reset counters if present
            try:
                if 'failed_attempts' in user or 'locked_until' in user:
                    supabase.table('user_logins').update({
                        'failed_attempts': 0,
                        'locked_until': None
                    }).eq('username', username_norm).execute()
            except Exception:
                pass
            _log_security_event('login_success', user_email=username_norm, success=True, details={'role': user.get('role')})
            return {"success": True, "role": user.get("role", "user"), "email": user.get("email")}
        else:
            # Failed password; increment failed_attempts and possibly lock
            try:
                if 'failed_attempts' in user:
                    cur = int(user.get('failed_attempts') or 0)
                    new = cur + 1
                    update_data = {'failed_attempts': new}
                    lock_set = False
                    if new >= LOGIN_LOCK_THRESHOLD:
                        lock_until = datetime.now(pytz.UTC) + timedelta(minutes=LOGIN_LOCK_DURATION_MINUTES)
                        update_data['locked_until'] = lock_until.isoformat()
                        lock_set = True
                    supabase.table('user_logins').update(update_data).eq('username', username_norm).execute()
                    if lock_set:
                        _log_security_event('login_failure', user_email=username_norm, success=False,
                                            error_message='Account locked due to repeated failures',
                                            details={'failed_attempts': new, 'locked_until': update_data.get('locked_until')})
                    else:
                        _log_security_event('login_failure', user_email=username_norm, success=False,
                                            error_message='Invalid credentials',
                                            details={'failed_attempts': new})
                else:
                    _log_security_event('login_failure', user_email=username_norm, success=False, error_message='Invalid credentials')
            except Exception as e:
                _log_security_event('login_failure', user_email=username_norm, success=False, error_message=f'Invalid credentials; update failed: {e}')
            return {"success": False, "role": None}
    except Exception as e:
        print(f"DEBUG: Error during username login: {str(e)}")
        _log_security_event('login_failure', user_email=(username or '').lower(), success=False, error_message=str(e))
        return {"success": False, "role": None}

