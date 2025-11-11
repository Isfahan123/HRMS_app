import pandas as pd
import re
from datetime import datetime
import pytz

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
        df = pd.read_excel(file_path)
        
        # Expected columns in EIS file
        expected_columns = [
            'Actual Monthly Wage (RM)',
            "Employer's Contribution (RM)",
            "Employee's Contribution (RM)",
            'Total Contribution (RM)'
        ]
        
        # Validate columns
        for col in expected_columns:
            if col not in df.columns:
                raise ValueError(f"Missing expected column: {col}")
        
        eis_data = []
        
        for _, row in df.iterrows():
            try:
                wage_range = str(row['Actual Monthly Wage (RM)']).strip()
                
                # Parse wage range
                if "and above" in wage_range.lower():
                    # Handle "6000.01 and above" case
                    from_wage = float(wage_range.split()[0])
                    to_wage = 999999.99  # Use large number for "and above"
                else:
                    # Handle "0.00 - 30.00" format
                    wage_range = wage_range.replace('RM', '').strip()
                    if ' - ' in wage_range:
                        from_str, to_str = wage_range.split(' - ')
                        from_wage = float(from_str.strip())
                        to_wage = float(to_str.strip())
                    else:
                        print(f"DEBUG: Could not parse wage range: {wage_range}")
                        continue
                
                # Extract contribution amounts
                employer_contribution = float(row["Employer's Contribution (RM)"])
                employee_contribution = float(row["Employee's Contribution (RM)"])
                total_contribution = float(row['Total Contribution (RM)'])
                
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
                print(f"DEBUG: Error parsing EIS row {row.to_dict()}: {e}")
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
