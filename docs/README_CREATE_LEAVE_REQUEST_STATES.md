How to apply: create_leave_request_states.sql

1. Open the Supabase web console > SQL Editor, paste the contents of
   `create_leave_request_states.sql` and run it.

OR, using psql (replace placeholders):

   psql "postgresql://<user>:<password>@<host>:5432/<db>" -f create_leave_request_states.sql

Notes:
- The function `create_leave_request_states_table_sql()` exists in `services/supabase_service.py` and returns the same SQL if you prefer generating from code.
- After running the migration, leave request submissions that include `states` will be persisted.
