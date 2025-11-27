"""
EIS (Employment Insurance System / SIP) PDF file parser using pdfplumber.

This module provides functionality to parse EIS contribution rate tables
from PDF files published by PERKESO and upload them to the database.

EIS has a single category with contributions from both employer and employee.
"""
import re
from datetime import datetime
import pytz

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

KL_TZ = pytz.timezone('Asia/Kuala_Lumpur')


def parse_wage_range(wage_str):
    """
    Parse EIS wage range string into (min, max) values.
    
    Args:
        wage_str: String like "30.01 – 50.00" or "6,000.01 and above"
        
    Returns:
        tuple: (wage_min, wage_max) as floats
    """
    wage_str = str(wage_str).strip()
    
    # Handle "and above" / "ke atas" case
    if "and above" in wage_str.lower() or "ke atas" in wage_str.lower():
        parts = re.split(r'and above|ke atas', wage_str, flags=re.IGNORECASE)[0].strip()
        parts = parts.replace(",", "").replace("RM", "").replace("rm", "").strip()
        try:
            nums = re.findall(r'[\d.]+', parts)
            wage_min = float(nums[-1]) if nums else 0
        except (ValueError, IndexError):
            wage_min = 0
        return (wage_min, 999999.99)
    
    # Clean up the string
    wage_str = wage_str.replace(",", "").replace("RM", "").replace("rm", "")
    
    # Handle different separators: - – —
    for sep in [" - ", " – ", " — ", "-", "–", "—"]:
        if sep in wage_str:
            parts = wage_str.split(sep)
            if len(parts) == 2:
                try:
                    wage_min = float(parts[0].strip())
                    wage_max = float(parts[1].strip())
                    return (wage_min, wage_max)
                except ValueError:
                    continue
    
    # Try to extract two numbers from the string
    nums = re.findall(r'[\d.]+', wage_str)
    if len(nums) >= 2:
        return (float(nums[0]), float(nums[1]))
    elif len(nums) == 1:
        return (float(nums[0]), float(nums[0]))
    
    raise ValueError(f"Could not parse EIS wage range: {wage_str}")


def extract_eis_tables(pdf_path):
    """
    Extract EIS contribution tables from PDF.
    
    Args:
        pdf_path: Path to the EIS PDF file
        
    Returns:
        list: List of contribution records
    """
    if not PDFPLUMBER_AVAILABLE:
        raise ImportError("pdfplumber is required for EIS PDF parsing. Install with: pip install pdfplumber")
    
    results = []
    parsed_ranges = set()
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            
            if not tables:
                continue
            
            for table in tables:
                if len(table) < 2:
                    continue
                
                # Try to identify the table structure
                header_row = table[0] if table else []
                
                # Look for wage/contribution columns
                wage_col_idx = None
                employer_col_idx = None
                employee_col_idx = None
                total_col_idx = None
                
                for idx, col in enumerate(header_row):
                    col_lower = str(col).lower() if col else ""
                    if "wage" in col_lower or "gaji" in col_lower or "upah" in col_lower or "monthly" in col_lower:
                        wage_col_idx = idx
                    elif "employer" in col_lower or "majikan" in col_lower:
                        if "employee" not in col_lower and "pekerja" not in col_lower:
                            employer_col_idx = idx
                    elif "employee" in col_lower or "pekerja" in col_lower:
                        employee_col_idx = idx
                    elif "total" in col_lower or "jumlah" in col_lower:
                        total_col_idx = idx
                
                # If we couldn't identify columns by header, try positional
                if wage_col_idx is None and len(header_row) >= 4:
                    wage_col_idx = 0
                    employer_col_idx = 1
                    employee_col_idx = 2
                    total_col_idx = 3
                
                if wage_col_idx is None:
                    continue
                
                for row in table[1:]:
                    try:
                        if len(row) <= wage_col_idx:
                            continue
                        
                        wage_range = str(row[wage_col_idx] or "").strip()
                        if not wage_range or wage_range == "":
                            continue
                        
                        # Skip if it looks like a header row
                        if "wage" in wage_range.lower() or "gaji" in wage_range.lower():
                            continue
                        
                        try:
                            from_wage, to_wage = parse_wage_range(wage_range)
                        except ValueError:
                            continue
                        
                        # Skip duplicates
                        if (from_wage, to_wage) in parsed_ranges:
                            continue
                        parsed_ranges.add((from_wage, to_wage))
                        
                        # Extract contributions
                        employer = 0.0
                        employee = 0.0
                        total = 0.0
                        
                        if employer_col_idx is not None and len(row) > employer_col_idx:
                            try:
                                employer = float(str(row[employer_col_idx] or "0").replace(",", "").strip())
                            except ValueError:
                                pass
                        
                        if employee_col_idx is not None and len(row) > employee_col_idx:
                            try:
                                employee = float(str(row[employee_col_idx] or "0").replace(",", "").strip())
                            except ValueError:
                                pass
                        
                        if total_col_idx is not None and len(row) > total_col_idx:
                            try:
                                total = float(str(row[total_col_idx] or "0").replace(",", "").strip())
                            except ValueError:
                                total = employer + employee
                        else:
                            total = employer + employee
                        
                        results.append({
                            "contrib_type": "eis",
                            "category": "eis",  # EIS has single category
                            "from_wage": from_wage,
                            "to_wage": to_wage,
                            "employer_contribution": employer,
                            "employee_contribution": employee,
                            "total_contribution": total,
                            "created_at": datetime.now(KL_TZ).isoformat(),
                        })
                        
                    except Exception as e:
                        continue
    
    return results


def store_eis_tables(supabase, records):
    """
    Store parsed EIS tables in the database.
    
    Args:
        supabase: Supabase client instance
        records: List of EIS contribution records
    """
    if not records:
        return
    
    # Delete existing EIS records
    supabase.table("contribution_tables").delete().eq("contrib_type", "eis").execute()
    
    # Insert new records
    response = supabase.table("contribution_tables").insert(records).execute()
    print(f"DEBUG: Stored {len(records)} EIS rows")


def upload_and_parse_eis_pdf(pdf_path, supabase):
    """
    Upload and parse EIS PDF file to database.
    
    Args:
        pdf_path: Path to the EIS PDF file
        supabase: Supabase client instance
        
    Returns:
        dict: Result with success status and message
    """
    try:
        records = extract_eis_tables(pdf_path)
        
        if not records:
            return {
                "success": False,
                "message": "No EIS contribution data found in PDF. Please verify the PDF format."
            }
        
        store_eis_tables(supabase, records)
        
        return {
            "success": True,
            "message": f"EIS rates uploaded successfully. Parsed {len(records)} records."
        }
        
    except ImportError as e:
        return {
            "success": False,
            "message": str(e)
        }
    except Exception as e:
        print(f"DEBUG: Error parsing EIS PDF: {e}")
        return {
            "success": False,
            "message": f"Error parsing EIS PDF: {str(e)}"
        }
