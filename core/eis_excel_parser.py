"""
EIS Excel file parser using openpyxl (pure Python, no pandas/numpy).

This module provides functionality to parse EIS contribution rate tables
from Excel files and upload them to the database.
"""
from datetime import datetime
import pytz
from core.file_parsers import read_excel_as_dicts, parse_wage_range

KL_TZ = pytz.timezone('Asia/Kuala_Lumpur')


def parse_eis_excel(file_path):
    """
    Parse EIS rate chart Excel file and extract contribution data
    
    Args:
        file_path (str): Path to the EIS Excel file
        
    Returns:
        list: List of dictionaries containing EIS contribution data
    """
    try:
        rows = read_excel_as_dicts(file_path)
        
        if not rows:
            print("DEBUG: No data found in EIS Excel file")
            return []
        
        # Expected columns in EIS file (normalized)
        expected_columns = [
            'actual_monthly_wage_rm',
            "employers_contribution_rm",
            "employees_contribution_rm",
            'total_contribution_rm'
        ]
        
        # Get actual column names
        columns = list(rows[0].keys()) if rows else []
        
        # Validate columns - try to find matching columns
        def find_col(partial_matches):
            for col in columns:
                for match in partial_matches:
                    if match in col:
                        return col
            return None
        
        wage_col = find_col(['actual_monthly_wage', 'wage'])
        employer_col = find_col(['employers_contribution', 'employer'])
        employee_col = find_col(['employees_contribution', 'employee'])
        total_col = find_col(['total_contribution', 'total'])
        
        if not all([wage_col, employer_col, employee_col, total_col]):
            missing = []
            if not wage_col: missing.append('wage')
            if not employer_col: missing.append('employer contribution')
            if not employee_col: missing.append('employee contribution')
            if not total_col: missing.append('total contribution')
            raise ValueError(f"Missing expected columns: {', '.join(missing)}")
        
        eis_data = []
        
        for row in rows:
            try:
                wage_range = str(row.get(wage_col, '')).strip()
                
                if not wage_range:
                    continue
                
                # Parse wage range using shared utility
                try:
                    from_wage, to_wage = parse_wage_range(wage_range)
                except ValueError as e:
                    print(f"DEBUG: Could not parse wage range: {wage_range}: {e}")
                    continue
                
                # Extract contribution amounts
                employer_contribution = float(row.get(employer_col, 0) or 0)
                employee_contribution = float(row.get(employee_col, 0) or 0)
                total_contribution = float(row.get(total_col, 0) or 0)
                
                # Create data record
                eis_record = {
                    "contrib_type": "eis",
                    "category": "eis",  # EIS has single category
                    "from_wage": from_wage,
                    "to_wage": to_wage,
                    "employer_contribution": employer_contribution,
                    "employee_contribution": employee_contribution,
                    "total_contribution": total_contribution,
                    "created_at": datetime.now(KL_TZ).isoformat(),
                }
                
                eis_data.append(eis_record)
                
            except (ValueError, IndexError) as e:
                print(f"DEBUG: Error parsing EIS row: {e}")
                continue
        
        print(f"DEBUG: Successfully parsed {len(eis_data)} EIS records")
        return eis_data
        
    except Exception as e:
        print(f"DEBUG: Error parsing EIS Excel file {file_path}: {e}")
        return []


def upload_and_parse_eis_excel(file_path, supabase):
    """
    Upload and parse EIS Excel file to database
    
    Args:
        file_path (str): Path to the EIS Excel file
        supabase: Supabase client instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Parse EIS data
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
        
    except Exception as e:
        print(f"DEBUG: Error uploading EIS Excel file: {e}")
        return False
