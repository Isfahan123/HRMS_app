"""
SOCSO (PERKESO) PDF file parser using pdfplumber.

This module provides functionality to parse SOCSO contribution rate tables
from PDF files published by PERKESO and upload them to the database.

SOCSO has two categories:
- First Category: For employees eligible for invalidity and employment injury benefits
- Second Category: For employees aged 60 and above, eligible for employment injury benefits only
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

# Headers to identify SOCSO categories in PDF
CATEGORY_HEADERS = {
    "first_category": re.compile(r"FIRST\s*CATEGORY|KATEGORI\s*PERTAMA|JADUAL\s*PERTAMA", re.IGNORECASE),
    "second_category": re.compile(r"SECOND\s*CATEGORY|KATEGORI\s*KEDUA|JADUAL\s*KEDUA", re.IGNORECASE),
}


def find_category_pages(pdf):
    """
    Find pages containing SOCSO category headers.
    
    Args:
        pdf: pdfplumber PDF object
        
    Returns:
        dict: Mapping of category name to page index
    """
    category_pages = {}
    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        for category, regex in CATEGORY_HEADERS.items():
            if regex.search(text):
                if category not in category_pages:
                    category_pages[category] = i
    return category_pages


def parse_wage_range(wage_str):
    """
    Parse SOCSO wage range string into (min, max) values.
    
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
            # Get the last number in the string
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
    
    raise ValueError(f"Could not parse SOCSO wage range: {wage_str}")


def extract_socso_tables(pdf_path):
    """
    Extract SOCSO contribution tables from PDF.
    
    Args:
        pdf_path: Path to the SOCSO PDF file
        
    Returns:
        dict: Mapping of category to list of contribution records
    """
    if not PDFPLUMBER_AVAILABLE:
        raise ImportError("pdfplumber is required for SOCSO PDF parsing. Install with: pip install pdfplumber")
    
    results = {k: [] for k in CATEGORY_HEADERS}
    
    with pdfplumber.open(pdf_path) as pdf:
        category_pages = find_category_pages(pdf)
        
        # If no category headers found, try to parse all pages as first category
        if not category_pages:
            category_pages = {"first_category": 0}
        
        for category, header_page_index in category_pages.items():
            page_index = header_page_index
            parsed_ranges = set()
            
            while page_index < len(pdf.pages):
                page = pdf.pages[page_index]
                tables = page.extract_tables()
                
                if not tables:
                    break
                
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
                        if "wage" in col_lower or "gaji" in col_lower or "upah" in col_lower:
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
                            
                            results[category].append({
                                "contrib_type": "socso",
                                "category": category,
                                "from_wage": from_wage,
                                "to_wage": to_wage,
                                "employer_contribution": employer,
                                "employee_contribution": employee,
                                "total_contribution": total,
                                "created_at": datetime.now(KL_TZ).isoformat(),
                            })
                            
                        except Exception as e:
                            continue
                
                page_index += 1
                
                # Stop if we hit a new category header on the next page
                if page_index < len(pdf.pages):
                    next_text = pdf.pages[page_index].extract_text() or ""
                    for other_cat, regex in CATEGORY_HEADERS.items():
                        if other_cat != category and regex.search(next_text):
                            break
    
    return results


def store_socso_tables(supabase, tables_dict):
    """
    Store parsed SOCSO tables in the database.
    
    Args:
        supabase: Supabase client instance
        tables_dict: Dictionary mapping category to list of records
    """
    for category, rows in tables_dict.items():
        if not rows:
            continue
        
        # Delete existing records for this category
        supabase.table("contribution_tables").delete().eq("contrib_type", "socso").eq("category", category).execute()
        
        # Insert new records
        response = supabase.table("contribution_tables").insert(rows).execute()
        print(f"DEBUG: Stored {len(rows)} SOCSO {category} rows")


def upload_and_parse_socso_pdf(pdf_path, supabase):
    """
    Upload and parse SOCSO PDF file to database.
    
    Args:
        pdf_path: Path to the SOCSO PDF file
        supabase: Supabase client instance
        
    Returns:
        dict: Result with success status and message
    """
    try:
        tables_dict = extract_socso_tables(pdf_path)
        
        total_records = sum(len(rows) for rows in tables_dict.values())
        if total_records == 0:
            return {
                "success": False,
                "message": "No SOCSO contribution data found in PDF. Please verify the PDF format."
            }
        
        store_socso_tables(supabase, tables_dict)
        
        return {
            "success": True,
            "message": f"SOCSO rates uploaded successfully. Parsed {total_records} records.",
            "details": {cat: len(rows) for cat, rows in tables_dict.items() if rows}
        }
        
    except ImportError as e:
        return {
            "success": False,
            "message": str(e)
        }
    except Exception as e:
        print(f"DEBUG: Error parsing SOCSO PDF: {e}")
        return {
            "success": False,
            "message": f"Error parsing SOCSO PDF: {str(e)}"
        }
