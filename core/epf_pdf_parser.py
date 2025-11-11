import pdfplumber
import re
from datetime import datetime
import pytz

KL_TZ = pytz.timezone('Asia/Kuala_Lumpur')

PART_HEADERS = {
    "part_a": re.compile(r"PART\s*A\b", re.IGNORECASE),
    "part_b": re.compile(r"PART\s*B\b", re.IGNORECASE),
    "part_c": re.compile(r"PART\s*C\b", re.IGNORECASE),
    "part_d": re.compile(r"PART\s*D\b", re.IGNORECASE),
    "part_e": re.compile(r"PART\s*E\b", re.IGNORECASE),
}

def find_part_pages(pdf):
    part_pages = {}
    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        for part, regex in PART_HEADERS.items():
            if regex.search(text):
                part_pages[part] = i
                # print(f"DEBUG: Found header for {part} on page {i + 1}")
    return part_pages

def extract_tables_from_pdf(pdf_path):
    results = {k: [] for k in PART_HEADERS}  # Initialize results for each part
    with pdfplumber.open(pdf_path) as pdf:
        part_pages = find_part_pages(pdf)  # Find header pages for each part
        for part, header_page_index in part_pages.items():
            page_index = header_page_index
            parsed_ranges = set()  # Initialize a set to track parsed ranges for this part
            while page_index < len(pdf.pages):  # Process all pages starting from the header page
                page = pdf.pages[page_index]
                tables = page.extract_tables()
                if not tables:
                    # print(f"DEBUG: No tables found on page {page_index + 1} for {part}")
                    break  # Stop processing if no tables are found on this page
                for table in tables:
                    # print(f"DEBUG: Extracted table for {part} on page {page_index + 1}: {table}")
                    if len(table) < 3:
                        # print(f"DEBUG: Skipping table with insufficient rows: {table}")
                        continue
                    header_row = table[0]
                    if header_row != ["Amount of Wages (RM)", "Employer Contribution (RM)", "Employee Contribution (RM)", "Total Contribution (RM)"]:
                        # print(f"DEBUG: Skipping table with unexpected header: {header_row}")
                        continue
                    for row in table[1:]:
                        try:
                            # Clean and parse the wage range
                            wage_range = row[0].replace(",", "").strip()
                            if "–" in wage_range:
                                from_wage, to_wage = map(float, wage_range.split("–"))
                                if (from_wage, to_wage) in parsed_ranges:
                                    # print(f"DEBUG: Duplicate range found: {from_wage} - {to_wage}")
                                    continue
                                parsed_ranges.add((from_wage, to_wage))
                            else:
                                raise ValueError(f"Invalid wage range format: {wage_range}")

                            # Parse contributions
                            employer = float(row[1].replace(",", "").strip())
                            employee = float(row[2].replace(",", "").strip())
                            total = float(row[3].replace(",", "").strip())

                            # Append parsed data
                            results[part].append({
                                "contrib_type": "epf",
                                "category": part,
                                "from_wage": from_wage,
                                "to_wage": to_wage,
                                "employer_contribution": employer,
                                "employee_contribution": employee,
                                "total_contribution": total,
                                "created_at": datetime.now(KL_TZ).isoformat(),
                            })
                        except Exception as e:
                            # print(f"DEBUG: Failed to parse row for {part}: {row} ({e})")
                            pass
                page_index += 1  # Move to the next page
    return results

def store_epf_tables(supabase, tables_dict):
    for part, rows in tables_dict.items():
        if not rows:
            # print(f"DEBUG: No rows found for {part}")
            continue
        supabase.table("contribution_tables").delete().eq("contrib_type", "epf").eq("category", part).execute()
        response = supabase.table("contribution_tables").insert(rows).execute()
        # print(f"DEBUG: Stored {len(rows)} rows for {part}: {response.data}")
        
def upload_and_parse_epf_pdf(pdf_path, supabase):
    tables_dict = extract_tables_from_pdf(pdf_path)
    store_epf_tables(supabase, tables_dict)
    # print("DEBUG: EPF PDF parsed and stored for all parts.")