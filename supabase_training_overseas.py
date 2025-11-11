# Fetch training course records with employee info
def fetch_training_course_with_employee(record_id):
    record_resp = supabase.table("training_course_records").select("*").eq("id", record_id).execute()
    if not record_resp.data:
        return None
    record = record_resp.data[0]
    # Use job_title (not position) as the canonical role/title field
    emp_resp = supabase.table("employees").select("full_name, department, job_title, email").eq("employee_id", record["employee_id"]).execute()
    employee = emp_resp.data[0] if emp_resp.data else {}
    return {**record, **employee}

# Fetch overseas work trip records with employee info
def fetch_overseas_work_trip_with_employee(record_id):
    record_resp = supabase.table("overseas_work_trip_records").select("*").eq("id", record_id).execute()
    if not record_resp.data:
        return None
    record = record_resp.data[0]
    # Use job_title (not position) as the canonical role/title field
    emp_resp = supabase.table("employees").select("full_name, department, job_title, email").eq("employee_id", record["employee_id"]).execute()
    employee = emp_resp.data[0] if emp_resp.data else {}
    return {**record, **employee}
from services.supabase_service import supabase

# Training/Course

def insert_training_course_record(data):
    # Accepts all expanded fields, including attachments as comma-separated URLs
    # Resilient insert: if PostgREST reports missing columns (PGRST204), strip them and retry.
    import re
    max_attempts = max(3, len(data) + 1)
    attempts = 0
    payload = dict(data)
    while attempts < max_attempts:
        attempts += 1
        try:
            response = supabase.table("training_course_records").insert(payload).execute()
            return response
        except Exception as e:
            # try to parse missing column name from the PostgREST message and remove it
            msg = ''
            try:
                if hasattr(e, 'args') and e.args:
                    msg = str(e.args[0])
                else:
                    msg = str(e)
            except Exception:
                msg = str(e)
            m = re.search(r"Could find the '([^']+)' column|Could not find the '([^']+)' column", msg)
            if not m:
                m2 = re.search(r"'([^']+)' column of '[^']+' in the schema cache", msg)
                missing_col = m2.group(1) if m2 else None
            else:
                missing_col = m.group(1) or m.group(2)
            if missing_col and missing_col in payload:
                payload.pop(missing_col, None)
                continue
            # special-case older messages referencing city_place_id
            if ('city_place_id' in msg) and 'city_place_id' in payload:
                payload.pop('city_place_id', None)
                continue
            # nothing to recover; re-raise
            raise

def fetch_training_course_records(employee_id=None, filters=None):
    query = supabase.table("training_course_records").select("*")
    if employee_id:
        query = query.eq("employee_id", employee_id)
    if filters:
        for key, value in filters.items():
            if isinstance(value, str) and '%' in value:
                query = query.ilike(key, value)
            else:
                query = query.eq(key, value)
    response = query.execute()
    return response.data

def update_training_course_record(record_id, data):
    # Accepts all expanded fields, including attachments
    response = supabase.table("training_course_records").update(data).eq("id", record_id).execute()
    return response

def delete_training_course_record(record_id):
    response = supabase.table("training_course_records").delete().eq("id", record_id).execute()
    return response

# Overseas Work/Trip

def insert_overseas_work_trip_record(data):
    # Accepts all expanded fields, including attachments as comma-separated URLs
    # We'll attempt the insert and, on PGRST204 (missing column) errors,
    # strip the missing column from the payload and retry. This supports
    # staged deployments where the client sends newer fields than the DB.
    import re
    max_attempts = max(3, len(data) + 1)
    attempts = 0
    payload = dict(data)
    last_exc = None
    while attempts < max_attempts:
        attempts += 1
        try:
            response = supabase.table("overseas_work_trip_records").insert(payload).execute()
            return response
        except Exception as e:
            last_exc = e
            # Try to extract missing column name from PostgREST error message
            msg = ''
            try:
                if hasattr(e, 'args') and e.args:
                    msg = str(e.args[0])
                else:
                    msg = str(e)
            except Exception:
                msg = str(e)
            m = re.search(r"Could find the '([^']+)' column|Could not find the '([^']+)' column", msg)
            if not m:
                # Some versions of PostgREST include code PGRST204 but different phrasing
                m2 = re.search(r"'([^']+)' column of '[^']+' in the schema cache", msg)
                if m2:
                    missing_col = m2.group(1)
                else:
                    missing_col = None
            else:
                missing_col = m.group(1) or m.group(2)
            if missing_col and missing_col in payload:
                # Remove the missing key and retry
                payload.pop(missing_col, None)
                continue
            # As a special-case, handle older error messages for specific known columns
            if ('city_place_id' in msg) and 'city_place_id' in payload:
                payload.pop('city_place_id', None)
                continue
            # Nothing we can recover from programmatically; re-raise
            raise

def fetch_overseas_work_trip_records(employee_id=None, filters=None):
    query = supabase.table("overseas_work_trip_records").select("*")
    if employee_id:
        query = query.eq("employee_id", employee_id)
    if filters:
        for key, value in filters.items():
            if isinstance(value, str) and '%' in value:
                query = query.ilike(key, value)
            else:
                query = query.eq(key, value)
    response = query.execute()
    return response.data

def update_overseas_work_trip_record(record_id, data):
    # Accepts all expanded fields, including attachments
    response = supabase.table("overseas_work_trip_records").update(data).eq("id", record_id).execute()
    return response

def delete_overseas_work_trip_record(record_id):
    response = supabase.table("overseas_work_trip_records").delete().eq("id", record_id).execute()
    return response
