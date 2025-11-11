from services.supabase_service import supabase

def fetch_employee_list():
    """
    Return a list of tuples: (id, employee_id, full_name).
    This keeps the UUID available to UI code so it can send the correct
    `employee_id` (UUID) to other tables that expect a UUID foreign key.
    """
    try:
        resp = supabase.table('employees').select('id, employee_id, full_name').execute()
        if resp.data:
            return [(r.get('id'), r.get('employee_id'), r.get('full_name')) for r in resp.data]
    except Exception:
        # Fallback: try older column shape
        try:
            resp2 = supabase.table('employees').select('employee_id, full_name').execute()
            if resp2.data:
                return [(None, r.get('employee_id'), r.get('full_name')) for r in resp2.data]
        except Exception:
            pass
    return []


def fetch_employee_details(employee_token: str):
    """
    Return a dict of employee details. Accepts either the UUID `id` or the employee code `employee_id`.
    """
    try:
        # Avoid importing uuid at top-level to keep imports light
        import uuid as _uuid
        # If token is a UUID, query by id, otherwise query by employee_id
        try:
            _uuid.UUID(str(employee_token))
            resp = supabase.table('employees').select('id, employee_id, full_name, department, job_title, email').eq('id', str(employee_token)).limit(1).execute()
        except Exception:
            resp = supabase.table('employees').select('id, employee_id, full_name, department, job_title, email').eq('employee_id', employee_token).limit(1).execute()
        return resp.data[0] if resp.data else {}
    except Exception:
        return {}
