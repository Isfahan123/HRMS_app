from services.supabase_service import supabase

def fetch_engagement_with_employee(record_id):
    rec = supabase.table('engagements').select('*').eq('id', record_id).execute()
    if not rec or not rec.data:
        return None
    row = rec.data[0]
    emp = {}
    try:
        er = supabase.table('employees').select('full_name, department, job_title, email').eq('id', row['employee_id']).execute()
        emp = er.data[0] if er and er.data else {}
    except Exception:
        emp = {}
    out = dict(row)
    out.update(emp)
    return out


def insert_engagement(data: dict):
    import re
    payload = dict(data)
    attempts = 0
    max_attempts = max(3, len(payload)+1)
    while attempts < max_attempts:
        attempts += 1
        try:
            return supabase.table('engagements').insert(payload).execute()
        except Exception as e:
            # strip unknown columns for forward compatibility
            msg = ''
            try:
                msg = str(e.args[0]) if getattr(e, 'args', None) else str(e)
            except Exception:
                msg = str(e)
            m = re.search(r"Could (?:not )?find the '([^']+)' column|\'([^']+)\' column of", msg)
            missing = m.group(1) if m and m.group(1) else (m.group(2) if m else None)
            if missing and missing in payload:
                payload.pop(missing, None)
                continue
            if 'city_place_id' in msg and 'city_place_id' in payload:
                payload.pop('city_place_id', None)
                continue
            raise


def fetch_engagements(employee_id=None, filters=None):
    q = supabase.table('engagements').select('*')
    if employee_id:
        q = q.eq('employee_id', employee_id)
    if filters:
        for k, v in filters.items():
            q = q.eq(k, v)
    r = q.execute()
    return r.data


def update_engagement(record_id, data):
    return supabase.table('engagements').update(data).eq('id', record_id).execute()


def delete_engagement(record_id):
    return supabase.table('engagements').delete().eq('id', record_id).execute()
