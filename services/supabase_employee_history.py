from services.supabase_service import supabase, KL_TZ
from datetime import datetime


# Employee history (work/re-employment history) functions
def insert_employee_history_record(data):
    # resilient insert: if new columns are present in client but not in DB, strip them and retry
    import re
    payload = dict(data)
    attempts = 0
    max_attempts = max(3, len(payload) + 1)
    while attempts < max_attempts:
        attempts += 1
        try:
            # attach created_at/updated_at timestamps if not present
            try:
                now = datetime.now(KL_TZ).isoformat()
                payload.setdefault('created_at', now)
                payload.setdefault('updated_at', now)
            except Exception:
                pass
            return supabase.table('employee_history').insert(payload).execute()
        except Exception as e:
            msg = str(e)
            m = re.search(r"Could find the '([^']+)' column|Could not find the '([^']+)' column", msg)
            if not m:
                m2 = re.search(r"'([^']+)' column of '[^']+' in the schema cache", msg)
                missing = m2.group(1) if m2 else None
            else:
                missing = m.group(1) or m.group(2)
            if missing and missing in payload:
                payload.pop(missing, None)
                continue
            # nothing recoverable
            raise


def fetch_employee_history_records(employee_id=None, filters=None):
    q = supabase.table('employee_history').select('*')
    if employee_id:
        q = q.eq('employee_id', employee_id)
    if filters:
        for k, v in filters.items():
            if isinstance(v, str) and '%' in v:
                q = q.ilike(k, v)
            else:
                q = q.eq(k, v)
    resp = q.execute()
    return resp.data if resp and hasattr(resp, 'data') else []


def update_employee_history_record(record_id, data):
    # set updated_at timestamp
    try:
        from services.supabase_service import KL_TZ
        data = dict(data or {})
        data['updated_at'] = datetime.now(KL_TZ).isoformat()
    except Exception:
        pass
    resp = supabase.table('employee_history').update(data).eq('id', record_id).execute()
    return resp


def delete_employee_history_record(record_id):
    resp = supabase.table('employee_history').delete().eq('id', record_id).execute()
    return resp


# Employee status functions
def fetch_employee_status(employee_id):
    resp = supabase.table('employee_status').select('*').eq('employee_id', employee_id).execute()
    if resp and getattr(resp, 'data', None):
        return resp.data[0]
    return None


def upsert_employee_status(employee_id, data):
    # resilient upsert: try update then insert; if DB complains about missing columns
    # strip unknown keys and retry, similar to how history insert is resilient.
    import re
    payload = dict(data or {})
    payload['employee_id'] = employee_id
    attempts = 0
    max_attempts = max(3, len(payload) + 1)
    while attempts < max_attempts:
        attempts += 1
        try:
            # try update first
            try:
                update_resp = supabase.table('employee_status').update(payload).eq('employee_id', employee_id).execute()
                # If server returned representation, pass it through
                if update_resp and getattr(update_resp, 'data', None):
                    return update_resp
            except Exception as ue:
                msg = str(ue)
                # PostgREST may return 204 (no content), which some clients surface as JSON parse errors
                if 'JSON could not be generated' in msg or 'JSONDecodeError' in msg or 'code: 404' in msg:
                    try:
                        # Verify via a read that the row exists (treat as success if so)
                        chk = supabase.table('employee_status').select('employee_id').eq('employee_id', employee_id).limit(1).execute()
                        if chk and getattr(chk, 'data', None):
                            return chk
                    except Exception:
                        # fall through to insert path
                        pass
                else:
                    # handle below as a generic failure (e.g., missing column parsing)
                    raise ue
            # otherwise, try insert
            try:
                insert_resp = supabase.table('employee_status').insert(payload).execute()
                return insert_resp
            except Exception as ie:
                msg2 = str(ie)
                if 'JSON could not be generated' in msg2 or 'JSONDecodeError' in msg2 or 'code: 404' in msg2:
                    # Verify insert by selecting
                    try:
                        chk2 = supabase.table('employee_status').select('employee_id').eq('employee_id', employee_id).limit(1).execute()
                        if chk2 and getattr(chk2, 'data', None):
                            return chk2
                    except Exception:
                        pass
                # re-raise so we can attempt missing-column cleanup
                raise ie
        except Exception as e:
            msg = str(e)
            # attempt to parse missing column name from common supabase/postgres error messages
            m = re.search(r"Could find the '([^']+)' column|Could not find the '([^']+)' column", msg)
            if not m:
                m2 = re.search(r"'([^']+)' column of '[^']+' in the schema cache", msg)
                missing = m2.group(1) if m2 else None
            else:
                missing = m.group(1) or m.group(2)
            if missing and missing in payload:
                # drop the offending field and retry
                payload.pop(missing, None)
                continue
            # nothing recoverable, re-raise
            raise
