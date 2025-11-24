# Deployment Checklist

## After Pulling Code Updates

When you pull new code changes, especially bug fixes, follow these steps to ensure the changes take effect:

### 1. Pull Latest Changes
```bash
git pull origin <branch-name>
```

### 2. Clear Python Bytecode Cache
Python caches compiled bytecode (.pyc files) which can cause old code to run even after updates.

```bash
# Remove all __pycache__ directories
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null

# Or more thorough cleanup
find . -type f -name "*.pyc" -delete
find . -type d -name __pycache__ -delete
```

### 3. Restart Application Server

#### For Development (uvicorn/FastAPI)
```bash
# Stop the current server (Ctrl+C)
# Then restart
python -m uvicorn web_app:app --host 0.0.0.0 --port 8000 --reload
```

#### For Production (with systemd)
```bash
sudo systemctl restart hrms
```

#### For cPanel/Passenger
- Touch the tmp/restart.txt file to trigger restart
```bash
touch tmp/restart.txt
```

### 4. Verify the Fix

#### Check Python Version in Memory
```python
import sys
print(sys.path)  # Check if the right paths are being used
```

#### Test the Endpoint
```bash
curl http://localhost:8000/api/admin/attendance
```

### 5. Check Logs
Monitor application logs for any errors:
```bash
tail -f /path/to/logs/app.log
```

## Common Issues

### Issue: Old Code Still Running
**Symptoms**: Error messages reference old code patterns
**Solution**: 
1. Verify you pulled the latest commit
2. Clear all Python cache
3. Restart the server completely (not just reload)

### Issue: Import Errors
**Symptoms**: `ModuleNotFoundError` or `ImportError`
**Solution**:
```bash
pip install -r requirements.txt
```

### Issue: Database Connection
**Symptoms**: PGRST errors or connection timeouts
**Solution**: Verify Supabase credentials in .env file

## For This PR Specifically

The fixes in this PR eliminate foreign key join dependencies in these functions:
- `get_all_attendance_records()` - services/supabase_service.py:1802
- `get_salary_history()` - web_app.py:1272
- `get_employee_history()` - web_app.py:1368
- `get_skipped_payroll()` - web_app.py:1200
- `export_skipped_payroll_csv()` - web_app.py:2361
- `load_skipped_payrolls()` - gui/admin_payroll_tab.py:1245

If you see PGRST200 errors about foreign key relationships after deploying, it means:
1. The code hasn't been deployed yet (pull + restart needed)
2. Old bytecode is cached (clear __pycache__)
3. Wrong version of file is being executed (check sys.path)

## Verification Commands

```bash
# Check current git commit
git log -1 --oneline

# Verify specific function has the fix
grep -A5 "def get_all_attendance_records" services/supabase_service.py | grep select

# Should see: select("*")
# Should NOT see: select("*, employees(")
```
