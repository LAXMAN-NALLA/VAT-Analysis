from fastapi import FastAPI, HTTPException, Header, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json
from fastapi.middleware.cors import CORSMiddleware
from processor import calculate_vat_amount, calculate_total_with_vat, validate_vat_calculation, get_vat_rate_by_category, calculate_vat_payable, get_user_company_details
from collections import defaultdict
from datetime import datetime
# import boto3  # COMMENTED OUT - S3 integration disabled for now
from processor import log_user_event
from processor import normalize_amount
# import os  # COMMENTED OUT - Not needed without S3
# from dotenv import load_dotenv  # COMMENTED OUT - Not needed without S3

# Load environment variables
# load_dotenv()  # COMMENTED OUT - Not needed without S3

# Initialize FastAPI
app = FastAPI()

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow React frontend (replace with actual domain for production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== IN-MEMORY STORAGE (Replaces S3) ====================
# Simple in-memory storage dictionaries
# TODO: Replace with S3 or database in production

# Store user VAT analysis data: {user_id: {year: {invoice_data}}}
user_vat_data = defaultdict(dict)

# Store company details: {user_id: {company_name, company_vat, updated_at}}
user_company_details = {}

# Store PDF count: {user_id: count}
user_pdf_count = defaultdict(int)

# ==================== COMMENTED OUT - S3 Integration (for future use) ====================
# # S3 Client
# s3_client = boto3.client('s3')
# bucket_name = os.getenv('S3_BUCKET_NAME', 'vat-analysis-new')

def try_parse_date(date_str):
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%d-%m-%y", "%d/%m/%y", "%d.%m.%y", "%d %B %Y", "%d %b %Y", "%b %d, %Y", "%B %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except:
            continue
    return None

def get_quarter_from_month(month):
    """Convert month to quarter"""
    month_to_quarter = {
        'Jan': 'Q1', 'Feb': 'Q1', 'Mar': 'Q1',
        'Apr': 'Q2', 'May': 'Q2', 'Jun': 'Q2',
        'Jul': 'Q3', 'Aug': 'Q3', 'Sep': 'Q3',
        'Oct': 'Q4', 'Nov': 'Q4', 'Dec': 'Q4'
    }
    return month_to_quarter.get(month, 'Unknown')

def get_quarter_name(quarter):
    """Get full quarter name"""
    quarter_names = {
        'Q1': 'Quarter 1 (Jan-Mar)',
        'Q2': 'Quarter 2 (Apr-Jun)', 
        'Q3': 'Quarter 3 (Jul-Sep)',
        'Q4': 'Quarter 4 (Oct-Dec)'
    }
    return quarter_names.get(quarter, quarter)

# ==================== REMOVED ENDPOINTS ====================
# The following endpoints were removed as they are no longer needed:
# - /user-info - User info can be derived from data
# - /upload - PDF upload not needed (using JSON via /process-invoices)
# - /trigger - VAT analysis trigger not needed (processing happens in /process-invoices)

# ==================== PYDANTIC MODELS FOR API DOCS ====================

class RegisterEntry(BaseModel):
    """Register entry model for invoice data"""
    Date: str = Field(..., description="Invoice date (YYYY-MM-DD or DD-MM-YYYY)")
    Type: str = Field(..., description="Transaction type: Purchase, Sales, or Unclassified")
    VAT_percent: Optional[float] = Field(None, alias="VAT %", description="VAT percentage")
    Currency: Optional[str] = Field(None, description="Currency code")
    VAT_Amount: Optional[float] = Field(None, description="VAT amount")
    Description: str = Field(..., description="Transaction description")
    Nett_Amount: Optional[float] = Field(None, description="Net amount before VAT")
    Vendor_Name: Optional[str] = Field(None, description="Vendor/supplier name")
    Gross_Amount: Optional[float] = Field(None, description="Gross amount including VAT")
    VAT_Category: Optional[str] = Field(None, description="VAT category (e.g., Reverse Charge, Zero Rated)")
    Customer_Name: Optional[str] = Field(None, description="Customer/client name")
    Invoice_Number: str = Field(..., alias="Invoice Number", description="Invoice number")
    VAT_Amount_EUR: Optional[float] = Field(None, alias="VAT Amount (EUR)", description="VAT amount in EUR")
    Nett_Amount_EUR: Optional[float] = Field(None, alias="Nett Amount (EUR)", description="Net amount in EUR")
    Gross_Amount_EUR: Optional[float] = Field(None, alias="Gross Amount (EUR)", description="Gross amount in EUR")
    Full_Extraction_Data: Optional[Dict[str, Any]] = Field(None, description="Full extraction data with additional details")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "Date": "2025-07-28",
                "Type": "Purchase",
                "VAT %": 0,
                "Currency": "EUR",
                "VAT Amount": 0,
                "Description": "Service description",
                "Nett Amount": 440,
                "Vendor Name": "Vendor Name",
                "Gross Amount": 440,
                "VAT Category": "Reverse Charge",
                "Customer Name": "Customer Name",
                "Invoice Number": "INV-001",
                "VAT Amount (EUR)": 0,
                "Nett Amount (EUR)": 440,
                "Gross Amount (EUR)": 440
            }
        }

class InvoiceResult(BaseModel):
    """Invoice result model"""
    status: str = Field(..., description="Status: success or error")
    file_name: Optional[str] = Field(None, description="Original filename")
    register_entry: Optional[RegisterEntry] = Field(None, description="Invoice register entry")
    error: Optional[str] = Field(None, description="Error message if status is error")

class InvoiceProcessingRequest(BaseModel):
    """Request model for processing invoices"""
    status: str = Field(..., description="Overall status")
    results: List[InvoiceResult] = Field(..., description="Array of invoice results")
    summary: Optional[Dict[str, Any]] = Field(None, description="Summary information")
    eur_converted_summary: Optional[Dict[str, Any]] = Field(None, description="EUR converted summary")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "results": [
                    {
                        "status": "success",
                        "file_name": "invoice.pdf",
                        "register_entry": {
                            "Date": "2025-07-28",
                            "Type": "Purchase",
                            "VAT %": 0,
                            "Currency": "EUR",
                            "VAT Amount": 0,
                            "Description": "Service description",
                            "Nett Amount": 440,
                            "Vendor Name": "Vendor Name",
                            "Gross Amount": 440,
                            "VAT Category": "Reverse Charge",
                            "Customer Name": "Customer Name",
                            "Invoice Number": "INV-001",
                            "VAT Amount (EUR)": 0,
                            "Nett Amount (EUR)": 440,
                            "Gross Amount (EUR)": 440
                        }
                    }
                ]
            }
        }

# ==================== HELPER FUNCTION FOR MULTIPLE JSON PARSING ====================

def parse_multiple_json_objects(text):
    """
    Parse multiple JSON objects from concatenated text
    Handles: {...}{...}{...} format
    """
    objects = []
    text = text.strip()
    
    if not text:
        return objects
    
    # Try to find JSON object boundaries
    depth = 0
    start = -1
    in_string = False
    escape_next = False
    
    for i, char in enumerate(text):
        if escape_next:
            escape_next = False
            continue
        
        if char == '\\':
            escape_next = True
            continue
        
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
        
        if not in_string:
            if char == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0 and start >= 0:
                    # Found complete JSON object
                    json_str = text[start:i+1]
                    try:
                        obj = json.loads(json_str)
                        objects.append(obj)
                    except json.JSONDecodeError:
                        pass
                    start = -1
    
    return objects

# ==================== NEW SIMPLE APPROACH: DIRECT JSON ARRAY ====================

@app.post("/process-invoices", response_model=Dict[str, Any])
async def process_invoices_simple(
    user_id: str = Header(..., alias="X-User-ID"),
    invoices: List[Dict[str, Any]] = Body(..., description="Array of analyzed invoice data. Each invoice should have: date, type, net_amount, vat_amount, vat_category, etc.")
):
    """
    Store analyzed invoice data directly (UPDATED APPROACH - Uses provided NL VAT codes)
    
    **Input Format:**
    JSON array of analyzed invoices with Dutch VAT category codes:
    ```json
    [
      {
        "date": "2025-09-25",
        "type": "Purchase",
        "net_amount": 4357.46,
        "vat_amount": null,
        "vat_percentage": "0",
        "description": "SEPTEMBER SALES",
        "vendor_name": "PAE Business Ltd",
        "file_name": "Invoice_26411.pdf",
        "VAT Category (NL) Code": "4a",
        "VAT Category (NL) Description": "Purchases of goods from EU countries"
      },
      ...
    ]
    ```
    
    **New Required Fields:**
    - `VAT Category (NL) Code`: Dutch VAT return category code (e.g., "1a", "1b", "1c", "2a", "3a", "3b", "4a", "4b", "5b")
    - `VAT Category (NL) Description`: Human-readable description of the VAT category
    
    **Backward Compatibility:**
    If NL codes are not provided, the system will attempt to map from old `vat_category` field.
    
    **Required Header:**
    - `X-User-ID`: Your user identifier
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing X-User-ID header")
    
    if not invoices or not isinstance(invoices, list):
        raise HTTPException(status_code=400, detail="Expected a JSON array of invoices")
    
    try:
        processed_count = 0
        skipped_count = 0
        error_count = 0
        updated_years = set()
        
        # Load existing data
        if user_id not in user_vat_data:
            user_vat_data[user_id] = {}
        
        # Process each invoice
        for invoice_item in invoices:
            try:
                # Helper function to get value with multiple field name variations
                def get_field_value(*field_names, default=None):
                    for field_name in field_names:
                        value = invoice_item.get(field_name)
                        if value is not None and value != "":
                            # Handle NaN values from Excel/CSV exports
                            if isinstance(value, float) and (value != value):  # NaN check
                                return default
                            return value
                    return default
                
                # Extract basic info - handle multiple field name formats
                date_str = get_field_value("date", "Date", default="")
                invoice_type = str(get_field_value("type", "Type", default="")).lower()
                file_name = get_field_value("file_name", "File Name", "file_name", default="")
                
                # Extract year from date
                year = "unknown"
                if date_str:
                    try:
                        # Try common date formats
                        for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%m-%d-%Y", "%m/%d/%Y"]:
                            try:
                                dt = datetime.strptime(str(date_str).strip(), fmt)
                                year = str(dt.year)
                                break
                            except ValueError:
                                continue
                    except Exception:
                        pass
                
                # Check for duplicate by file_name and invoice_number
                if year not in user_vat_data[user_id]:
                    user_vat_data[user_id][year] = {"invoices": []}
                
                # Extract invoice number for duplicate checking
                # Try to get actual invoice number from input, fallback to file_name if not provided
                input_invoice_number = get_field_value("invoice_number", "invoice_no", "Invoice Number", "Invoice No")
                file_name_base = file_name.replace(".pdf", "")
                
                # Check if already exists (by file_name/source_file OR invoice_number)
                existing_invoices = user_vat_data[user_id][year].get("invoices", [])
                is_duplicate = any(
                    # Check by file name (always check this)
                    inv.get("source_file") == file_name or inv.get("file_name") == file_name or
                    # Check by invoice number (if provided and different from file_name)
                    # This catches cases where same invoice is uploaded with different file names
                    (input_invoice_number and 
                     input_invoice_number != file_name_base and 
                     inv.get("invoice_no") == input_invoice_number)
                    for inv in existing_invoices
                )
                
                if is_duplicate:
                    skipped_count += 1
                    continue
                
                # Map transaction type
                transaction_type = "sale" if invoice_type in ["sales", "sale"] else "purchase"
                
                # Get VAT category code and description - NEW APPROACH: Use provided NL codes directly
                vat_category_code = get_field_value(
                    "VAT Category (NL) Code", 
                    "vat_category_nl_code", 
                    "vat_category_code",
                    "VAT Category Code",
                    default=""
                )
                vat_category_description = get_field_value(
                    "VAT Category (NL) Description",
                    "vat_category_nl_description",
                    "vat_category_description", 
                    "VAT Category Description",
                    default=""
                )
                
                # Fallback: If NL code not provided, try to map from old format (backward compatibility)
                if not vat_category_code:
                    vat_category_str = get_field_value("vat_category", "VAT Category", default="")
                    vat_percentage_raw = get_field_value("vat_percentage", "VAT %", "VAT Percentage", default="0")
                    # Clean VAT percentage (remove % symbol if present)
                    if isinstance(vat_percentage_raw, str):
                        vat_percentage = vat_percentage_raw.replace("%", "").strip()
                    else:
                        vat_percentage = str(vat_percentage_raw)
                    # Get country for country-based classification
                    country = get_field_value("country", "Country", default="")
                    vat_category_code = map_vat_category_simple(vat_category_str, transaction_type, vat_percentage, country)
                    # If still no description, use the old category string
                    if not vat_category_description:
                        vat_category_description = vat_category_str
                
                # Get VAT percentage for display
                vat_percentage_raw = get_field_value("vat_percentage", "VAT %", "VAT Percentage", default="0")
                if isinstance(vat_percentage_raw, str):
                    vat_percentage = vat_percentage_raw.replace("%", "").strip()
                else:
                    vat_percentage = str(vat_percentage_raw)
                
                # Extract amounts - handle multiple field name formats and NaN values
                net_amount_raw = get_field_value("net_amount", "Net Amount", default=0)
                vat_amount_raw = get_field_value("vat_amount", "VAT Amount", default=None)
                gross_amount_raw = get_field_value("gross_amount", "Gross Amount", default=0)
                
                # Normalize amounts (handle NaN)
                net_amount = normalize_amount(net_amount_raw)
                # Handle NaN for VAT amount - if NaN or None, set to 0
                if vat_amount_raw is None or (isinstance(vat_amount_raw, float) and (vat_amount_raw != vat_amount_raw)):  # NaN check
                    vat_amount = 0.0
                else:
                    vat_amount = normalize_amount(vat_amount_raw)
                gross_amount = normalize_amount(gross_amount_raw)
                
                # Extract vendor/customer name - handle both field name formats
                # For purchases: use vendor_name (the supplier)
                # For sales: use customer_name (the buyer)
                if transaction_type == "purchase":
                    # Try multiple field name variations for vendor
                    invoice_to = (
                        get_field_value("vendor_name", "Vendor Name", "vendor", default="")
                    )
                else:  # sale
                    # Try multiple field name variations for customer
                    invoice_to = (
                        get_field_value("customer_name", "Customer Name", "customer", default="")
                    )
                
                # Build invoice structure
                invoice = {
                    "invoice_no": input_invoice_number or file_name.replace(".pdf", ""),
                    "date": date_str,
                    "invoice_to": invoice_to,
                    "country": get_field_value("country", "Country", default=""),
                    "vat_no": get_field_value("vendor_vat_id", "Vendor VAT ID") if transaction_type == "purchase" else get_field_value("customer_vat_id", "Customer VAT ID", default=""),
                    "transactions": [{
                        "description": get_field_value("description", "Description", default=""),
                        "amount_pre_vat": net_amount,
                        "vat_percentage": f"{vat_percentage}%",
                        "vat_category": vat_category_code,
                        "vat_category_description": vat_category_description
                    }],
                    "subtotal": net_amount,
                    "vat_amount": vat_amount,
                    "total_amount": gross_amount,
                    "transaction_type": transaction_type,
                    "source_file": file_name
                }
                
                # Add to storage
                user_vat_data[user_id][year]["invoices"].append(invoice)
                updated_years.add(year)
                processed_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"Error processing invoice: {e}")
                continue
        
        return {
            "status": "success",
            "message": f"Processed {processed_count} invoices, skipped {skipped_count}, errors: {error_count}",
            "details": {
                "processed": processed_count,
                "skipped": skipped_count,
                "errors": error_count,
                "updated_years": list(updated_years)
            },
            "total_invoices_received": len(invoices)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing invoices: {str(e)}")

# Jurisdiction Constants
DOMESTIC_COUNTRY = "NL"

# List of EU Countries (excluding NL)
EU_COUNTRIES = [
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", 
    "HU", "IE", "IT", "LV", "LT", "LU", "MT", "PL", "PT", "RO", "SK", "SI", 
    "ES", "SE"
]
# Note: GB (United Kingdom) is NON-EU.

def map_vat_category_simple(vat_category_str, transaction_type, vat_percentage, country=""):
    """
    Multi-Field VAT Category Mapping Logic with Country-Based Classification
    
    Priority Order:
    1. Check Category (vat_category string)
    2. Check Type (Sales or Purchase)
    3. Check Rate (vat_percentage) - CRUCIAL for "Standard VAT" to resolve 21% vs 9%
    4. Check Country (for 0% transactions) - NEW: Distinguishes EU/Non-EU/NL
    
    This follows the exact logic table:
    - "Standard VAT" + Sales + 21% → 1a
    - "Standard VAT" + Sales + 9% → 1b
    - "Standard VAT" + Purchase + Any% → 5b
    - "Reduced Rate" + Sales → 1b
    - "Reduced Rate" + Purchase → 5b
    - "Zero Rated" + Sales + 0% + NL → 1e
    - "Zero Rated" + Sales + 0% + EU → 3b
    - "Zero Rated" + Sales + 0% + Non-EU → 3a
    - "Zero Rated" + Purchase + 0% + EU → 4b
    - "Zero Rated" + Purchase + 0% + Non-EU → 4a
    - "EU Goods" + Sales → 3a
    - "EU Goods" + Purchase → 4a
    - "EU Services" + Sales → 3b
    - "EU Services" + Purchase → 4b
    - "Reverse Charge" + Purchase → 2a
    - "Import" + Purchase → 4c
    """
    # Normalize inputs
    category = str(vat_category_str).strip() if vat_category_str else ""
    category_lower = category.lower()
    tx_type = str(transaction_type).strip().lower()
    country_upper = str(country).strip().upper() if country else ""
    
    # Parse percentage (handle string "21" or "21%" to float 21.0)
    percentage_str = str(vat_percentage).replace("%", "").strip()
    try:
        percentage = float(percentage_str)
    except (ValueError, TypeError):
        percentage = 0.0
    
    # --- LOGIC FOR STANDARD / REDUCED RATES (Priority: Check Percentage) ---
    if "standard vat" in category_lower or "standard rate" in category_lower:
        if tx_type == "sale" or tx_type == "sales":
            if percentage == 21:
                return "1a"  # Standard rate sales (21%)
            elif percentage == 9:
                return "1b"  # Reduced rate labeled as standard (9%)
            else:
                # Default to 1a if percentage doesn't match
                return "1a"
        elif tx_type == "purchase":
            return "5b"  # Domestic input VAT (any percentage)
    
    if "reduced rate" in category_lower or "reduced" in category_lower:
        if tx_type == "sale" or tx_type == "sales":
            return "1b"  # Reduced rate sales (9%)
        elif tx_type == "purchase":
            return "5b"  # Alternative label for domestic input VAT
    
    # --- LOGIC FOR ZERO RATED / EU (WITH COUNTRY-BASED CLASSIFICATION) ---
    if "zero rated" in category_lower or "zero-rated" in category_lower:
        if tx_type == "sale" or tx_type == "sales":
            # For Sales with 0% VAT, check country to determine correct code
            if percentage == 0:
                if country_upper == DOMESTIC_COUNTRY:
                    return "1e"  # Domestic 0% / Exempt (NL customer)
                elif country_upper in EU_COUNTRIES:
                    return "3b"  # Intra-Community Supply (EU customer)
                elif country_upper and country_upper not in EU_COUNTRIES:
                    return "3a"  # Export to Non-EU (Non-EU customer)
                else:
                    # No country info - default to 1c (general zero-rated)
                    return "1c"  # General Exports / Zero Rated sales
            else:
                return "1c"  # Non-zero percentage with zero-rated category (shouldn't happen, but fallback)
        elif tx_type == "purchase":
            # For Purchases with 0% VAT, check country to determine correct code
            if percentage == 0:
                if country_upper in EU_COUNTRIES:
                    return "4b"  # Services/Goods from EU
                elif country_upper and country_upper not in EU_COUNTRIES:
                    return "4a"  # Services/Goods from Non-EU
                else:
                    # No country info - default to 4a (assumes EU Goods Purchase)
                    return "4a"  # Assumes EU Goods Purchase
            else:
                return "4a"  # Non-zero percentage with zero-rated category (shouldn't happen, but fallback)
    
    if "eu goods" in category_lower:
        if tx_type == "sale" or tx_type == "sales":
            return "3a"  # Specific EU Supply
        elif tx_type == "purchase":
            return "4a"  # Same code as Zero Rated Purchase
    
    if "eu services" in category_lower:
        if tx_type == "sale" or tx_type == "sales":
            return "3b"  # EU Service Supply
        elif tx_type == "purchase":
            return "4b"  # EU Service Purchase
    
    # Handle generic "EU" category
    if "eu" in category_lower and "goods" not in category_lower and "services" not in category_lower:
        if tx_type == "sale" or tx_type == "sales":
            return "3a"  # Default to goods for EU sales
        elif tx_type == "purchase":
            return "4a"  # Default to goods for EU purchases
    
    # --- LOGIC FOR OTHERS ---
    if ("reverse charge" in category_lower or "reverse-charge" in category_lower) and tx_type == "purchase":
        return "2a"  # Reverse Charge Mechanism
    
    if "import" in category_lower and tx_type == "purchase":
        return "4c"  # Non-EU Import
    
    # --- FALLBACK LOGIC (if category not recognized) ---
    # Default based on transaction type, VAT percentage, and country
    if tx_type == "sale" or tx_type == "sales":
        if percentage == 21:
            return "1a"
        elif percentage == 9:
            return "1b"
        elif percentage == 0:
            # For 0% sales, check country in fallback too
            if country_upper == DOMESTIC_COUNTRY:
                return "1e"  # Domestic 0% / Exempt
            elif country_upper in EU_COUNTRIES:
                return "3b"  # Intra-Community Supply
            elif country_upper and country_upper not in EU_COUNTRIES:
                return "3a"  # Export to Non-EU
            else:
                return "1c"  # Default zero-rated sales
        else:
            return "1a"  # Default to standard rate
    elif tx_type == "purchase":
        if percentage == 0:
            # For 0% purchases, check country in fallback too
            if country_upper in EU_COUNTRIES:
                return "4b"  # Services/Goods from EU
            elif country_upper and country_upper not in EU_COUNTRIES:
                return "4a"  # Services/Goods from Non-EU
            else:
                return "2a"  # Default to reverse charge for zero-rated purchases (no country info)
        else:
            return "5b"  # Default to domestic input VAT
    
    # Final fallback
    return "5b"  # Default to domestic input VAT

# ==================== HELPER FUNCTIONS ====================

def parse_multiple_json_objects(text):
    """
    Parse multiple JSON objects from concatenated text
    Handles: {...}{...}{...} format
    """
    objects = []
    text = text.strip()
    
    if not text:
        return objects
    
    # Try to find JSON object boundaries
    depth = 0
    start = -1
    in_string = False
    escape_next = False
    
    for i, char in enumerate(text):
        if escape_next:
            escape_next = False
            continue
        
        if char == '\\':
            escape_next = True
            continue
        
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
        
        if not in_string:
            if char == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0 and start >= 0:
                    # Found complete JSON object
                    json_str = text[start:i+1]
                    try:
                        obj = json.loads(json_str)
                        objects.append(obj)
                    except json.JSONDecodeError:
                        pass
                    start = -1
    
    return objects

# ==================== REMOVED ENDPOINTS ====================
# The following endpoints were removed as they are redundant:
# - /vat-summary - Redundant (use /vat-report-quarterly, /vat-report-monthly, or /vat-report-yearly instead)
# - /transactions - Redundant (transactions are included in all report endpoints)


# ==================== COMPANY DETAILS ROUTE ====================

@app.post("/company-details")
async def update_company_details(
    user_id: str = Header(..., alias="X-User-ID"),
    company_name: str = Header(..., alias="X-Company-Name"),
    company_vat: str = Header(..., alias="X-Company-VAT")
):
    """Update company details for a user"""
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing X-User-ID header")
    if not company_name:
        raise HTTPException(status_code=400, detail="Missing X-Company-Name header")
    if not company_vat:
        raise HTTPException(status_code=400, detail="Missing X-Company-VAT header")

    # In-memory storage
    user_company_details[user_id] = {
        "company_name": company_name,
        "company_vat": company_vat,
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }
    
    # ==================== COMMENTED OUT - S3 Integration ====================
    # # Store company details in S3
    # company_data = {
    #     "user_id": user_id,
    #     "company_name": company_name,
    #     "company_vat": company_vat,
    #     "updated_at": datetime.utcnow().isoformat() + "Z"
    # }
    # 
    # company_key = f"users/{user_id}/company_details.json"
    # s3_client.put_object(
    #     Bucket=bucket_name,
    #     Key=company_key,
    #     Body=json.dumps(company_data, indent=2),
    #     ContentType='application/json'
    # )
    
    log_user_event(user_id, "Company Details Updated", {
        "company_name": company_name,
        "company_vat": company_vat
    })
    
    return {
        "message": "Company details updated successfully",
        "company_name": company_name,
        "company_vat": company_vat
    }

@app.get("/company-details")
async def get_company_details(user_id: str = Header(..., alias="X-User-ID")):
    """Get company details for a user"""
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing X-User-ID header")

    # In-memory storage
    company_data = user_company_details.get(user_id)
    if company_data:
        return {
            "company_name": company_data.get("company_name"),
            "company_vat": company_data.get("company_vat"),
            "updated_at": company_data.get("updated_at")
        }
    else:
        return {
            "company_name": None,
            "company_vat": None,
            "updated_at": None,
            "message": "No company details found. Please set company details first."
        }
    
    # ==================== COMMENTED OUT - S3 Integration ====================
    # company_key = f"users/{user_id}/company_details.json"
    # try:
    #     obj = s3_client.get_object(Bucket=bucket_name, Key=company_key)
    #     company_data = json.loads(obj['Body'].read().decode('utf-8'))
    #     return {
    #         "company_name": company_data.get("company_name"),
    #         "company_vat": company_data.get("company_vat"),
    #         "updated_at": company_data.get("updated_at")
    #     }
    # except s3_client.exceptions.NoSuchKey:
    #     return {
    #         "company_name": None,
    #         "company_vat": None,
    #         "updated_at": None,
    #         "message": "No company details found. Please set company details first."
    #     }


# ==================== REMOVED ENDPOINT ====================
# /vat-quarterly - Removed as redundant (use /vat-report-quarterly instead)


# ===============================

# ==================== VAT CALCULATION ENDPOINT ====================

@app.post("/calculate-vat")
async def calculate_vat_endpoint(
    user_id: str = Header(..., alias="X-User-ID"),
    pre_vat_amount: float = None,
    vat_percentage: str = None,
    vat_category: str = None
):
    """Calculate VAT amount and total for given inputs"""
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing X-User-ID header")
    
    if pre_vat_amount is None or vat_percentage is None:
        raise HTTPException(status_code=400, detail="pre_vat_amount and vat_percentage are required")
    
    # Use VAT category rate if provided, otherwise use vat_percentage
    if vat_category:
        vat_rate = get_vat_rate_by_category(vat_category)
        vat_percentage = f"{vat_rate}%"
    
    # Calculate VAT amount
    vat_amount = calculate_vat_amount(pre_vat_amount, vat_percentage)
    total_with_vat = calculate_total_with_vat(pre_vat_amount, vat_amount)
    
    return {
        "pre_vat_amount": pre_vat_amount,
        "vat_percentage": vat_percentage,
        "vat_category": vat_category,
        "calculated_vat_amount": vat_amount,
        "total_with_vat": total_with_vat,
        "vat_rate_used": vat_rate if vat_category else float(vat_percentage.replace("%", ""))
    }

@app.post("/validate-vat")
async def validate_vat_endpoint(
    user_id: str = Header(..., alias="X-User-ID"),
    pre_vat_amount: float = None,
    vat_percentage: str = None,
    extracted_vat_amount: float = None,
    vat_category: str = None
):
    """Validate if extracted VAT amount matches calculated amount"""
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing X-User-ID header")
    
    if pre_vat_amount is None or vat_percentage is None or extracted_vat_amount is None:
        raise HTTPException(status_code=400, detail="pre_vat_amount, vat_percentage, and extracted_vat_amount are required")
    
    # Use VAT category rate if provided
    if vat_category:
        vat_rate = get_vat_rate_by_category(vat_category)
        vat_percentage = f"{vat_rate}%"
    
    # Calculate expected VAT amount
    calculated_vat = calculate_vat_amount(pre_vat_amount, vat_percentage)
    
    # Validate the amounts
    is_valid = validate_vat_calculation(extracted_vat_amount, calculated_vat)
    difference = abs(extracted_vat_amount - calculated_vat)
    
    return {
        "pre_vat_amount": pre_vat_amount,
        "vat_percentage": vat_percentage,
        "extracted_vat_amount": extracted_vat_amount,
        "calculated_vat_amount": calculated_vat,
        "is_valid": is_valid,
        "difference": round(difference, 2),
        "vat_category": vat_category
    }

@app.get("/vat-payable")
async def get_vat_payable(user_id: str = Header(..., alias="X-User-ID"), year: str = ""):
    """Calculate net VAT payable (VAT collected - VAT paid)"""
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing X-User-ID header")
    
    if not year:
        year = str(datetime.now().year)
    
    # In-memory storage
    try:
        data = user_vat_data.get(user_id, {}).get(year, {"invoices": []})
        if not isinstance(data, dict) or "invoices" not in data:
            data = {"invoices": []}
    except:
        return {
            "vat_collected": 0,
            "vat_paid": 0,
            "vat_payable": 0,
            "year": year
        }
    
    # ==================== COMMENTED OUT - S3 Integration ====================
    # json_key = f"users/{user_id}/results/VATanalysis_{year}.json"
    # try:
    #     obj = s3_client.get_object(Bucket=bucket_name, Key=json_key)
    #     data = json.loads(obj['Body'].read().decode('utf-8'))
    # except s3_client.exceptions.NoSuchKey:
    #     return {
    #         "vat_collected": 0,
    #         "vat_paid": 0,
    #         "vat_payable": 0,
    #         "year": year
    #     }
    
    vat_collected = 0.0
    vat_paid = 0.0
    
    for invoice in data.get("invoices", []):
        vat_amount = normalize_amount(invoice.get("vat_amount", "0"))
        
        # Determine if this is VAT collected (sales) or VAT paid (purchases)
        transaction_type = invoice.get("transaction_type", "sale")
        
        if transaction_type == "sale":
            vat_collected += vat_amount
        else:
            vat_paid += vat_amount
    
    vat_payable = calculate_vat_payable(vat_collected, vat_paid)
    
    return {
        "year": year,
        "vat_collected": round(vat_collected, 2),
        "vat_paid": round(vat_paid, 2),
        "vat_payable": vat_payable,
        "status": "refund_due" if vat_payable < 0 else "payment_due" if vat_payable > 0 else "balanced"
    }

# ==================== SIMPLIFIED VAT REPORTS ====================

@app.get("/vat-report-quarterly")
async def get_vat_report_quarterly(user_id: str = Header(..., alias="X-User-ID"), year: str = "", quarter: str = ""):
    """Get simplified quarterly VAT report in the requested format"""
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing X-User-ID header")

    if not year:
        year = str(datetime.now().year)
    
    if not quarter:
        current_month = datetime.now().month
        if current_month <= 3:
            quarter = "Q1"
        elif current_month <= 6:
            quarter = "Q2"
        elif current_month <= 9:
            quarter = "Q3"
        else:
            quarter = "Q4"
    else:
        # Normalize quarter to uppercase (handle q1, Q1, etc.)
        quarter = quarter.upper()

    # In-memory storage
    try:
        data = user_vat_data.get(user_id, {}).get(year, {"invoices": []})
        if not isinstance(data, dict) or "invoices" not in data:
            data = {"invoices": []}
    except:
        return {
            "report_type": "vat_tax_return",
            "period": f"{quarter} {year}",
            "generated_at": datetime.now().isoformat(),
            "categories": {},
            "vat_calculation": {"vat_collected": 0, "vat_deductible": 0, "vat_payable": 0},
        }
    
    # ==================== COMMENTED OUT - S3 Integration ====================
    # json_key = f"users/{user_id}/results/VATanalysis_{year}.json"
    # try:
    #     obj = s3_client.get_object(Bucket=bucket_name, Key=json_key)
    #     data = json.loads(obj['Body'].read().decode('utf-8'))
    # except s3_client.exceptions.NoSuchKey:
    #     return {
    #         "report_type": "vat_tax_return",
    #         "period": f"{quarter} {year}",
    #         "generated_at": datetime.now().isoformat(),
    #         "categories": {},
    #         "vat_calculation": {"vat_collected": 0, "vat_deductible": 0, "vat_payable": 0},
    #     }

    # Get company details (pass in-memory storage)
    company_details = get_user_company_details(user_id, storage_dict=user_company_details)
    if company_details is None:
        company_details = {}
    
    # Filter transactions by quarter
    quarter_months = {
        "Q1": ["Jan", "Feb", "Mar"],
        "Q2": ["Apr", "May", "Jun"], 
        "Q3": ["Jul", "Aug", "Sep"],
        "Q4": ["Oct", "Nov", "Dec"]
    }
    
    target_months = quarter_months.get(quarter, [])
    
    # Categorize transactions
    categories = {
        "1a": {"name": "Sales Taxed at the Standard Rate (21%)", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "1b": {"name": "Sales Taxed at the Reduced Rate (9%)", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "1c": {"name": "Sales Taxed at 0% (EU and Export)", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "1e": {"name": "Exempt / out-of-scope supplies", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "2a": {"name": "Reverse-Charge Supplies", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "3a": {"name": "Supplies of Goods to EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "3b": {"name": "Supplies of Services to EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "3c": {"name": "Intra-EU B2C goods (distance/installation sales)", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "4a": {"name": "Purchases of Goods from EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "4b": {"name": "Purchases of Services from EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "4c": {"name": "Purchases of Goods from Non-EU Countries (Imports)", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "5a": {"name": "Domestic purchases with Dutch VAT", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "5b": {"name": "Input VAT on Domestic Purchases", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}}
    }
    
    vat_collected = 0.0
    vat_deductible = 0.0
    
    for invoice in data.get("invoices", []):
        dt = try_parse_date(invoice.get("date", ""))
        if not dt: continue
        
        month = dt.strftime("%b")
        if month not in target_months: continue
        
        invoice_no = invoice.get("invoice_no", "")
        date = invoice.get("date", "")
        transaction_type = invoice.get("transaction_type", "sale")
        
        # Get invoice-level VAT amount (handle both string and numeric)
        invoice_vat_total = normalize_amount(invoice.get("vat_amount", 0))
        invoice_net_total = normalize_amount(invoice.get("subtotal", invoice.get("total_amount", 0)))
        
        # Process transactions
        transactions_list = invoice.get("transactions", [])
        if not transactions_list:
            # If no transactions, create one from invoice-level data
            transactions_list = [{
                "description": invoice.get("invoice_to", "N/A"),
                "amount_pre_vat": invoice_net_total,
                "vat_percentage": "0%",
                "vat_category": ""
            }]
        
        # Distribute VAT proportionally if multiple transactions
        total_net = sum(normalize_amount(tx.get("amount_pre_vat", 0)) for tx in transactions_list)
        
        # If total_net is 0 but invoice has amount (positive or negative), use invoice amount for single transaction
        if total_net == 0 and invoice_net_total != 0 and len(transactions_list) == 1:
            total_net = invoice_net_total
        
        for tx in transactions_list:
            vat_category = tx.get("vat_category", "")
            description = tx.get("description", "")
            tx_amount = normalize_amount(tx.get("amount_pre_vat", 0))
            
            # CRITICAL FIX: Handle both positive and negative amounts (credit notes)
            # Credit notes have negative amounts and must be preserved for correct VAT calculation
            if tx_amount != 0:  # Use != 0 to handle both positive and negative
                amount_pre_vat = tx_amount
            elif invoice_net_total != 0:  # Use != 0 to handle both positive and negative
                # Use invoice amount - distribute if multiple transactions
                if len(transactions_list) == 1:
                    amount_pre_vat = invoice_net_total
                    # Update total_net for VAT calculation (preserve sign)
                    if total_net == 0:
                        total_net = invoice_net_total
                else:
                    # Multiple transactions - distribute invoice total proportionally (preserve sign)
                    if total_net == 0:
                        total_net = invoice_net_total
                    amount_pre_vat = invoice_net_total / len(transactions_list)
            else:
                amount_pre_vat = 0.0
            
            vat_percentage_str = tx.get("vat_percentage", "0")
            vat_percentage = float(vat_percentage_str.replace("%", "")) if isinstance(vat_percentage_str, str) else float(vat_percentage_str)
            
            # Handle VAT calculation for both positive and negative amounts (credit notes)
            # Credit notes have negative VAT that must be subtracted
            if invoice_vat_total != 0 and total_net != 0:
                # Distribute VAT proportionally (preserve sign for credit notes)
                vat_amount = round((amount_pre_vat / total_net) * invoice_vat_total, 2)
            elif invoice_vat_total != 0 and total_net == 0 and amount_pre_vat != 0:
                # If total_net is 0 but we have amount_pre_vat, use it directly (preserve sign)
                vat_amount = invoice_vat_total
            elif vat_percentage != 0:
                # Calculate from percentage (preserve sign - negative amount * positive % = negative VAT)
                vat_amount = round(amount_pre_vat * vat_percentage / 100, 2)
            else:
                vat_amount = 0.0
            
            # Get vendor/customer name from invoice
            invoice_to = invoice.get("invoice_to", "")
            
            transaction = {
                "date": date,
                "invoice_no": invoice_no,
                "description": description,
                "net_amount": round(amount_pre_vat, 2),
                "vat_percentage": vat_percentage,
                "vat_amount": vat_amount,
                "vat_category": vat_category,
                "vat_category_description": tx.get("vat_category_description", "")
            }
            
            # Add vendor_name for purchases, customer_name for sales (only if not empty)
            if transaction_type == "purchase" and invoice_to:
                transaction["vendor_name"] = invoice_to
            elif transaction_type == "sale" and invoice_to:
                transaction["customer_name"] = invoice_to
            
            if vat_category in categories:
                categories[vat_category]["transactions"].append(transaction)
                categories[vat_category]["totals"]["net"] += amount_pre_vat
                categories[vat_category]["totals"]["vat"] += vat_amount
                
                if transaction_type == "sale":
                    vat_collected += vat_amount
                else:
                    vat_deductible += vat_amount
    
    vat_payable = vat_collected - vat_deductible
    
    # Round all totals in categories
    for cat_code, cat_data in categories.items():
        cat_data["totals"]["net"] = round(cat_data["totals"]["net"], 2)
        cat_data["totals"]["vat"] = round(cat_data["totals"]["vat"], 2)
    
    return {
        "report_type": "vat_tax_return",
        "period": f"{quarter} {year}",
        "generated_at": datetime.now().isoformat(),
        "company_info": {
            "company_name": company_details.get("company_name", "N/A") if company_details else "N/A",
            "company_vat": company_details.get("company_vat", "N/A") if company_details else "N/A",
            "reporting_period": f"{quarter} {year}"
        },
        "categories": categories,
        "vat_calculation": {
            "vat_collected": round(vat_collected, 2),
            "vat_deductible": round(vat_deductible, 2),
            "vat_payable": round(vat_payable, 2)
        }
    }

@app.get("/vat-report-yearly")
async def get_vat_report_yearly(user_id: str = Header(..., alias="X-User-ID"), year: str = ""):
    """Get simplified yearly VAT report in the requested format"""
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing X-User-ID header")

    if not year:
        year = str(datetime.now().year)

    # In-memory storage
    try:
        data = user_vat_data.get(user_id, {}).get(year, {"invoices": []})
        if not isinstance(data, dict) or "invoices" not in data:
            data = {"invoices": []}
    except:
        return {
            "report_type": "vat_tax_return",
            "period": year,
            "generated_at": datetime.now().isoformat(),
            "categories": {},
            "vat_calculation": {"vat_collected": 0, "vat_deductible": 0, "vat_payable": 0},
        }
    
    # ==================== COMMENTED OUT - S3 Integration ====================
    # json_key = f"users/{user_id}/results/VATanalysis_{year}.json"
    # try:
    #     obj = s3_client.get_object(Bucket=bucket_name, Key=json_key)
    #     data = json.loads(obj['Body'].read().decode('utf-8'))
    # except s3_client.exceptions.NoSuchKey:
    #     return {
    #         "report_type": "vat_tax_return",
    #         "period": year,
    #         "generated_at": datetime.now().isoformat(),
    #         "categories": {},
    #         "vat_calculation": {"vat_collected": 0, "vat_deductible": 0, "vat_payable": 0},
    #     }

    # Get company details (pass in-memory storage)
    company_details = get_user_company_details(user_id, storage_dict=user_company_details)
    if company_details is None:
        company_details = {}
    
    # Categorize transactions
    categories = {
        "1a": {"name": "Sales Taxed at the Standard Rate (21%)", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "1b": {"name": "Sales Taxed at the Reduced Rate (9%)", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "1c": {"name": "Sales Taxed at 0% (EU and Export)", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "1e": {"name": "Exempt / out-of-scope supplies", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "2a": {"name": "Reverse-Charge Supplies", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "3a": {"name": "Supplies of Goods to EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "3b": {"name": "Supplies of Services to EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "3c": {"name": "Intra-EU B2C goods (distance/installation sales)", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "4a": {"name": "Purchases of Goods from EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "4b": {"name": "Purchases of Services from EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "4c": {"name": "Purchases of Goods from Non-EU Countries (Imports)", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "5a": {"name": "Domestic purchases with Dutch VAT", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "5b": {"name": "Input VAT on Domestic Purchases", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}}
    }
    
    # Quarterly breakdown
    quarterly_breakdown = {
        "Q1": {"period": f"Q1 {year} (Jan-Mar)", "vat_collected": 0.0, "vat_deductible": 0.0, "vat_payable": 0.0},
        "Q2": {"period": f"Q2 {year} (Apr-Jun)", "vat_collected": 0.0, "vat_deductible": 0.0, "vat_payable": 0.0},
        "Q3": {"period": f"Q3 {year} (Jul-Sep)", "vat_collected": 0.0, "vat_deductible": 0.0, "vat_payable": 0.0},
        "Q4": {"period": f"Q4 {year} (Oct-Dec)", "vat_collected": 0.0, "vat_deductible": 0.0, "vat_payable": 0.0}
    }
    
    vat_collected = 0.0
    vat_deductible = 0.0
    
    for invoice in data.get("invoices", []):
        dt = try_parse_date(invoice.get("date", ""))
        if not dt: continue
        
        month = dt.strftime("%b")
        quarter = get_quarter_from_month(month)
        invoice_no = invoice.get("invoice_no", "")
        date = invoice.get("date", "")
        transaction_type = invoice.get("transaction_type", "sale")
        
        # Get invoice-level VAT amount (handle both string and numeric)
        invoice_vat_total = normalize_amount(invoice.get("vat_amount", 0))
        invoice_net_total = normalize_amount(invoice.get("subtotal", invoice.get("total_amount", 0)))
        
        # Process transactions
        transactions_list = invoice.get("transactions", [])
        if not transactions_list:
            # If no transactions, create one from invoice-level data
            transactions_list = [{
                "description": invoice.get("invoice_to", "N/A"),
                "amount_pre_vat": invoice_net_total,
                "vat_percentage": "0%",
                "vat_category": ""
            }]
        
        # Distribute VAT proportionally if multiple transactions
        total_net = sum(normalize_amount(tx.get("amount_pre_vat", 0)) for tx in transactions_list)
        
        # If total_net is 0 but invoice has amount (positive or negative), use invoice amount for single transaction
        if total_net == 0 and invoice_net_total != 0 and len(transactions_list) == 1:
            total_net = invoice_net_total
        
        for tx in transactions_list:
            vat_category = tx.get("vat_category", "")
            description = tx.get("description", "")
            tx_amount = normalize_amount(tx.get("amount_pre_vat", 0))
            
            # CRITICAL FIX: Handle both positive and negative amounts (credit notes)
            # Credit notes have negative amounts and must be preserved for correct VAT calculation
            if tx_amount != 0:  # Use != 0 to handle both positive and negative
                amount_pre_vat = tx_amount
            elif invoice_net_total != 0:  # Use != 0 to handle both positive and negative
                # Use invoice amount - distribute if multiple transactions
                if len(transactions_list) == 1:
                    amount_pre_vat = invoice_net_total
                    # Update total_net for VAT calculation (preserve sign)
                    if total_net == 0:
                        total_net = invoice_net_total
                else:
                    # Multiple transactions - distribute invoice total proportionally (preserve sign)
                    if total_net == 0:
                        total_net = invoice_net_total
                    amount_pre_vat = invoice_net_total / len(transactions_list)
            else:
                amount_pre_vat = 0.0
            
            vat_percentage_str = tx.get("vat_percentage", "0")
            vat_percentage = float(vat_percentage_str.replace("%", "")) if isinstance(vat_percentage_str, str) else float(vat_percentage_str)
            
            # Handle VAT calculation for both positive and negative amounts (credit notes)
            # Credit notes have negative VAT that must be subtracted
            if invoice_vat_total != 0 and total_net != 0:
                # Distribute VAT proportionally (preserve sign for credit notes)
                vat_amount = round((amount_pre_vat / total_net) * invoice_vat_total, 2)
            elif invoice_vat_total != 0 and total_net == 0 and amount_pre_vat != 0:
                # If total_net is 0 but we have amount_pre_vat, use it directly (preserve sign)
                vat_amount = invoice_vat_total
            elif vat_percentage != 0:
                # Calculate from percentage (preserve sign - negative amount * positive % = negative VAT)
                vat_amount = round(amount_pre_vat * vat_percentage / 100, 2)
            else:
                vat_amount = 0.0
            
            # Get vendor/customer name from invoice
            invoice_to = invoice.get("invoice_to", "")
            
            transaction = {
                "date": date,
                "invoice_no": invoice_no,
                "description": description,
                "net_amount": round(amount_pre_vat, 2),
                "vat_percentage": vat_percentage,
                "vat_amount": vat_amount
            }
            
            # Add vendor_name for purchases, customer_name for sales (only if not empty)
            if transaction_type == "purchase" and invoice_to:
                transaction["vendor_name"] = invoice_to
            elif transaction_type == "sale" and invoice_to:
                transaction["customer_name"] = invoice_to
            
            if vat_category in categories:
                categories[vat_category]["transactions"].append(transaction)
                categories[vat_category]["totals"]["net"] += amount_pre_vat
                categories[vat_category]["totals"]["vat"] += vat_amount
                
                if transaction_type == "sale":
                    vat_collected += vat_amount
                    quarterly_breakdown[quarter]["vat_collected"] += vat_amount
                else:
                    vat_deductible += vat_amount
                    quarterly_breakdown[quarter]["vat_deductible"] += vat_amount
    
    # Calculate quarterly VAT payable
    for quarter in quarterly_breakdown:
        q_vat_collected = quarterly_breakdown[quarter]["vat_collected"]
        q_vat_deductible = quarterly_breakdown[quarter]["vat_deductible"]
        quarterly_breakdown[quarter]["vat_payable"] = round(q_vat_collected - q_vat_deductible, 2)
        quarterly_breakdown[quarter]["vat_collected"] = round(quarterly_breakdown[quarter]["vat_collected"], 2)
        quarterly_breakdown[quarter]["vat_deductible"] = round(quarterly_breakdown[quarter]["vat_deductible"], 2)
    
    vat_payable = vat_collected - vat_deductible
    
    # Round all totals in categories
    for cat_code, cat_data in categories.items():
        cat_data["totals"]["net"] = round(cat_data["totals"]["net"], 2)
        cat_data["totals"]["vat"] = round(cat_data["totals"]["vat"], 2)
    
    return {
        "report_type": "vat_tax_return",
        "period": year,
        "generated_at": datetime.now().isoformat(),
        "company_info": {
            "company_name": company_details.get("company_name", "N/A") if company_details else "N/A",
            "company_vat": company_details.get("company_vat", "N/A") if company_details else "N/A",
            "reporting_period": f"{year} (January - December {year})"
        },
        "quarterly_breakdown": quarterly_breakdown,
        "categories": categories,
        "vat_calculation": {
            "vat_collected": round(vat_collected, 2),
            "vat_deductible": round(vat_deductible, 2),
            "vat_payable": round(vat_payable, 2)
        }
    }

# ==================== MONTHLY VAT REPORT ====================

def normalize_month(month_str):
    """Normalize month input to abbreviated format (Jan, Feb, etc.)"""
    if not month_str:
        return datetime.now().strftime("%b")
    
    month_str = str(month_str).strip()
    
    # Month number to abbreviation mapping
    month_map = {
        "1": "Jan", "01": "Jan", "january": "Jan", "jan": "Jan",
        "2": "Feb", "02": "Feb", "february": "Feb", "feb": "Feb",
        "3": "Mar", "03": "Mar", "march": "Mar", "mar": "Mar",
        "4": "Apr", "04": "Apr", "april": "Apr", "apr": "Apr",
        "5": "May", "05": "May", "may": "May",
        "6": "Jun", "06": "Jun", "june": "Jun", "jun": "Jun",
        "7": "Jul", "07": "Jul", "july": "Jul", "jul": "Jul",
        "8": "Aug", "08": "Aug", "august": "Aug", "aug": "Aug",
        "9": "Sep", "09": "Sep", "september": "Sep", "sep": "Sep",
        "10": "Oct", "october": "Oct", "oct": "Oct",
        "11": "Nov", "november": "Nov", "nov": "Nov",
        "12": "Dec", "december": "Dec", "dec": "Dec"
    }
    
    # Check if it's already in correct format
    if month_str in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]:
        return month_str
    
    # Try to map it
    month_lower = month_str.lower()
    if month_lower in month_map:
        return month_map[month_lower]
    
    # If not found, try direct lookup
    if month_str in month_map:
        return month_map[month_str]
    
    # Default to current month if can't parse
    return datetime.now().strftime("%b")

@app.get("/vat-report-monthly")
async def get_vat_report_monthly(user_id: str = Header(..., alias="X-User-ID"), year: str = "", month: str = ""):
    """Get monthly VAT report for a specific month"""
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing X-User-ID header")

    if not year:
        year = str(datetime.now().year)
    
    # Normalize month to abbreviated format (Jan, Feb, etc.)
    month = normalize_month(month)

    # In-memory storage
    try:
        data = user_vat_data.get(user_id, {}).get(year, {"invoices": []})
        if not isinstance(data, dict) or "invoices" not in data:
            data = {"invoices": []}
    except:
        return {
            "report_type": "vat_tax_return",
            "period": f"{month} {year}",
            "generated_at": datetime.now().isoformat(),
            "categories": {},
            "vat_calculation": {"vat_collected": 0, "vat_deductible": 0, "vat_payable": 0},
            "notes": f"No data found for {month} {year}"
        }
    
    # ==================== COMMENTED OUT - S3 Integration ====================
    # json_key = f"users/{user_id}/results/VATanalysis_{year}.json"
    # try:
    #     obj = s3_client.get_object(Bucket=bucket_name, Key=json_key)
    #     data = json.loads(obj['Body'].read().decode('utf-8'))
    # except s3_client.exceptions.NoSuchKey:
    #     return {
    #         "report_type": "vat_tax_return",
    #         "period": f"{month} {year}",
    #         "generated_at": datetime.now().isoformat(),
    #         "categories": {},
    #         "vat_calculation": {"vat_collected": 0, "vat_deductible": 0, "vat_payable": 0},
    #         "notes": f"No data found for {month} {year}"
    #     }

    # Get company details (pass in-memory storage)
    company_details = get_user_company_details(user_id, storage_dict=user_company_details)
    if company_details is None:
        company_details = {}
    
    # Categorize transactions
    categories = {
        "1a": {"name": "Sales Taxed at the Standard Rate (21%)", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "1b": {"name": "Sales Taxed at the Reduced Rate (9%)", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "1c": {"name": "Sales Taxed at 0% (EU and Export)", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "1e": {"name": "Exempt / out-of-scope supplies", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "2a": {"name": "Reverse-Charge Supplies", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "3a": {"name": "Supplies of Goods to EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "3b": {"name": "Supplies of Services to EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "3c": {"name": "Intra-EU B2C goods (distance/installation sales)", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "4a": {"name": "Purchases of Goods from EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "4b": {"name": "Purchases of Services from EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "4c": {"name": "Purchases of Goods from Non-EU Countries (Imports)", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "5a": {"name": "Domestic purchases with Dutch VAT", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "5b": {"name": "Input VAT on Domestic Purchases", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}}
    }
    
    vat_collected = 0.0
    vat_deductible = 0.0
    
    for invoice in data.get("invoices", []):
        dt = try_parse_date(invoice.get("date", ""))
        if not dt: continue
        
        invoice_month = dt.strftime("%b")
        if invoice_month != month: continue
        
        invoice_no = invoice.get("invoice_no", "")
        date = invoice.get("date", "")
        transaction_type = invoice.get("transaction_type", "sale")
        
        # Get invoice-level VAT amount (handle both string and numeric)
        invoice_vat_total = normalize_amount(invoice.get("vat_amount", 0))
        invoice_net_total = normalize_amount(invoice.get("subtotal", invoice.get("total_amount", 0)))
        
        # Process transactions
        transactions_list = invoice.get("transactions", [])
        if not transactions_list:
            # If no transactions, create one from invoice-level data
            transactions_list = [{
                "description": invoice.get("invoice_to", "N/A"),
                "amount_pre_vat": invoice_net_total,
                "vat_percentage": "0%",
                "vat_category": ""
            }]
        
        # Distribute VAT proportionally if multiple transactions
        total_net = sum(normalize_amount(tx.get("amount_pre_vat", 0)) for tx in transactions_list)
        
        # If total_net is 0 but invoice has amount (positive or negative), use invoice amount for single transaction
        if total_net == 0 and invoice_net_total != 0 and len(transactions_list) == 1:
            total_net = invoice_net_total
        
        for tx in transactions_list:
            vat_category = tx.get("vat_category", "")
            description = tx.get("description", "")
            tx_amount = normalize_amount(tx.get("amount_pre_vat", 0))
            
            # CRITICAL FIX: Handle both positive and negative amounts (credit notes)
            # Credit notes have negative amounts and must be preserved for correct VAT calculation
            if tx_amount != 0:  # Use != 0 to handle both positive and negative
                amount_pre_vat = tx_amount
            elif invoice_net_total != 0:  # Use != 0 to handle both positive and negative
                # Use invoice amount - distribute if multiple transactions
                if len(transactions_list) == 1:
                    amount_pre_vat = invoice_net_total
                    # Update total_net for VAT calculation (preserve sign)
                    if total_net == 0:
                        total_net = invoice_net_total
                else:
                    # Multiple transactions - distribute invoice total proportionally (preserve sign)
                    if total_net == 0:
                        total_net = invoice_net_total
                    amount_pre_vat = invoice_net_total / len(transactions_list)
            else:
                amount_pre_vat = 0.0
            
            vat_percentage_str = tx.get("vat_percentage", "0")
            vat_percentage = float(vat_percentage_str.replace("%", "")) if isinstance(vat_percentage_str, str) else float(vat_percentage_str)
            
            # Handle VAT calculation for both positive and negative amounts (credit notes)
            # Credit notes have negative VAT that must be subtracted
            if invoice_vat_total != 0 and total_net != 0:
                # Distribute VAT proportionally (preserve sign for credit notes)
                vat_amount = round((amount_pre_vat / total_net) * invoice_vat_total, 2)
            elif invoice_vat_total != 0 and total_net == 0 and amount_pre_vat != 0:
                # If total_net is 0 but we have amount_pre_vat, use it directly (preserve sign)
                vat_amount = invoice_vat_total
            elif vat_percentage != 0:
                # Calculate from percentage (preserve sign - negative amount * positive % = negative VAT)
                vat_amount = round(amount_pre_vat * vat_percentage / 100, 2)
            else:
                vat_amount = 0.0
            
            # Get vendor/customer name from invoice
            invoice_to = invoice.get("invoice_to", "")
            
            transaction = {
                "date": date,
                "invoice_no": invoice_no,
                "description": description,
                "net_amount": round(amount_pre_vat, 2),
                "vat_percentage": vat_percentage,
                "vat_amount": vat_amount,
                "vat_category": vat_category,
                "vat_category_description": tx.get("vat_category_description", "")
            }
            
            # Add vendor_name for purchases, customer_name for sales (only if not empty)
            if transaction_type == "purchase" and invoice_to:
                transaction["vendor_name"] = invoice_to
            elif transaction_type == "sale" and invoice_to:
                transaction["customer_name"] = invoice_to
            
            if vat_category in categories:
                categories[vat_category]["transactions"].append(transaction)
                categories[vat_category]["totals"]["net"] += amount_pre_vat
                categories[vat_category]["totals"]["vat"] += vat_amount
                
                if transaction_type == "sale":
                    vat_collected += vat_amount
                else:
                    vat_deductible += vat_amount
    
    vat_payable = vat_collected - vat_deductible
    
    # Round all totals in categories
    for cat_code, cat_data in categories.items():
        cat_data["totals"]["net"] = round(cat_data["totals"]["net"], 2)
        cat_data["totals"]["vat"] = round(cat_data["totals"]["vat"], 2)
    
    # Debug: Check if we have any invoices
    total_invoices = len(data.get("invoices", []))
    invoices_in_month = sum(1 for inv in data.get("invoices", []) 
                           if try_parse_date(inv.get("date", "")) and 
                           try_parse_date(inv.get("date", "")).strftime("%b") == month)
    
    return {
        "report_type": "vat_tax_return",
        "period": f"{month} {year}",
        "generated_at": datetime.now().isoformat(),
        "company_info": {
            "company_name": company_details.get("company_name", "N/A") if company_details else "N/A",
            "company_vat": company_details.get("company_vat", "N/A") if company_details else "N/A",
            "reporting_period": f"{month} {year}"
        },
        "categories": categories,
        "vat_calculation": {
            "vat_collected": round(vat_collected, 2),
            "vat_deductible": round(vat_deductible, 2),
            "vat_payable": round(vat_payable, 2)
        },
        "_debug": {
            "total_invoices_in_year": total_invoices,
            "invoices_in_month": invoices_in_month,
            "month_requested": month,
            "year_requested": year
        }
    }

# ==================== HEALTH CHECK ====================

@app.delete("/clear-user-data")
async def clear_user_data(user_id: str = Header(..., alias="X-User-ID")):
    """Clear all stored data for a user (in-memory storage only)"""
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing X-User-ID header")
    
    # Clear in-memory storage
    if user_id in user_vat_data:
        del user_vat_data[user_id]
    if user_id in user_company_details:
        del user_company_details[user_id]
    if user_id in user_pdf_count:
        user_pdf_count[user_id] = 0
    
    return {
        "status": "success",
        "message": f"All data cleared for user {user_id}",
        "cleared": {
            "vat_data": True,
            "company_details": True,
            "pdf_count": True
        }
    }

@app.get("/dreport")
async def get_dreport(user_id: str = Header(..., alias="X-User-ID"), year: str = "", quarter: str = ""):
    """
    Generate VAT return report in Dutch tax authority format (Dreport)
    
    This endpoint generates a structured VAT return report with sections and rows
    matching the Dutch tax authority format.
    
    Query Parameters:
    - year: Year (e.g., "2025")
    - quarter: Quarter (e.g., "Q1", "Q2", "Q3", "Q4")
    
    Returns:
    - report_meta: Report metadata (company info, period, etc.)
    - sections: Array of sections with rows containing VAT category data
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing X-User-ID header")

    if not year:
        year = str(datetime.now().year)
    
    if not quarter:
        current_month = datetime.now().month
        if current_month <= 3:
            quarter = "Q1"
        elif current_month <= 6:
            quarter = "Q2"
        elif current_month <= 9:
            quarter = "Q3"
        else:
            quarter = "Q4"
    else:
        quarter = quarter.upper()

    # Get data from storage
    try:
        data = user_vat_data.get(user_id, {}).get(year, {"invoices": []})
        if not isinstance(data, dict) or "invoices" not in data:
            data = {"invoices": []}
    except:
        data = {"invoices": []}
    
    # Get company details
    company_details = get_user_company_details(user_id, storage_dict=user_company_details)
    if company_details is None:
        company_details = {}
    
    # Filter transactions by quarter
    quarter_months = {
        "Q1": ["Jan", "Feb", "Mar"],
        "Q2": ["Apr", "May", "Jun"], 
        "Q3": ["Jul", "Aug", "Sep"],
        "Q4": ["Oct", "Nov", "Dec"]
    }
    
    target_months = quarter_months.get(quarter, [])
    
    # Initialize category totals - using the new format codes
    category_totals = {
        "1a": {"net_amount": 0.0, "vat": 0.0},  # Standard rate (21%)
        "1b": {"net_amount": 0.0, "vat": 0.0},  # Reduced rate (9%)
        "1c": {"net_amount": 0.0, "vat": 0.0},  # Other rates (not 0%)
        "1d": {"net_amount": 0.0, "vat": 0.0},  # Private use
        "1e": {"net_amount": 0.0, "vat": 0.0},  # 0% or not taxed
        "2a": {"net_amount": 0.0, "vat": 0.0},  # Reverse charge
        "3a": {"net_amount": 0.0, "vat": 0.0},  # Exports (non-EU)
        "3b": {"net_amount": 0.0, "vat": 0.0},  # EU supplies
        "3c": {"net_amount": 0.0, "vat": 0.0},  # Installation/distance sales
        "4a": {"net_amount": 0.0, "vat": 0.0},  # Purchases from non-EU
        "4b": {"net_amount": 0.0, "vat": 0.0},  # Purchases from EU
        "5a": {"net_amount": 0.0, "vat": 0.0},  # Domestic purchases with Dutch VAT
        "5b": {"net_amount": 0.0, "vat": 0.0},  # Input VAT (deductible) - backward compatibility
    }
    
    # Process invoices
    invoices_processed = 0
    invoices_skipped = 0
    
    for invoice in data.get("invoices", []):
        dt = try_parse_date(invoice.get("date", ""))
        if not dt: 
            invoices_skipped += 1
            continue
        
        month = dt.strftime("%b")
        if month not in target_months: 
            invoices_skipped += 1
            continue
        
        invoices_processed += 1
        transaction_type = invoice.get("transaction_type", "sale")
        invoice_vat_total = normalize_amount(invoice.get("vat_amount", 0))
        invoice_net_total = normalize_amount(invoice.get("subtotal", invoice.get("total_amount", 0)))
        
        # Process transactions
        transactions_list = invoice.get("transactions", [])
        if not transactions_list:
            # If no transactions, create one from invoice-level data
            # Try to get VAT percentage from invoice if available
            invoice_vat_percentage = invoice.get("vat_percentage", "0")
            if isinstance(invoice_vat_percentage, str):
                invoice_vat_percentage = invoice_vat_percentage.replace("%", "").strip()
            try:
                invoice_vat_pct = float(invoice_vat_percentage)
            except:
                invoice_vat_pct = 0.0
            
            transactions_list = [{
                "description": invoice.get("invoice_to", "N/A"),
                "amount_pre_vat": invoice_net_total,
                "vat_percentage": f"{invoice_vat_pct}%",
                "vat_category": ""  # Will be determined from transaction type and VAT percentage
            }]
        
        total_net = sum(normalize_amount(tx.get("amount_pre_vat", 0)) for tx in transactions_list)
        if total_net == 0 and invoice_net_total != 0 and len(transactions_list) == 1:
            total_net = invoice_net_total
        
        for tx in transactions_list:
            vat_category = tx.get("vat_category", "")
            tx_amount = normalize_amount(tx.get("amount_pre_vat", 0))
            
            if tx_amount != 0:
                amount_pre_vat = tx_amount
            elif invoice_net_total != 0:
                if len(transactions_list) == 1:
                    amount_pre_vat = invoice_net_total
                    if total_net == 0:
                        total_net = invoice_net_total
                else:
                    if total_net == 0:
                        total_net = invoice_net_total
                    amount_pre_vat = invoice_net_total / len(transactions_list)
            else:
                amount_pre_vat = 0.0
            
            vat_percentage_str = tx.get("vat_percentage", "0")
            vat_percentage = float(vat_percentage_str.replace("%", "")) if isinstance(vat_percentage_str, str) else float(vat_percentage_str)
            
            # Calculate VAT amount
            if invoice_vat_total != 0 and total_net != 0:
                vat_amount = round((amount_pre_vat / total_net) * invoice_vat_total, 2)
            elif invoice_vat_total != 0 and total_net == 0 and amount_pre_vat != 0:
                vat_amount = invoice_vat_total
            elif vat_percentage != 0:
                vat_amount = round(amount_pre_vat * vat_percentage / 100, 2)
            else:
                vat_amount = 0.0
            
            # Use provided VAT Category (NL) Code directly - no remapping needed
            # The category code is already provided in the correct format
            target_code = vat_category
            
            # Only do remapping if category is empty or invalid (fallback for backward compatibility)
            if not target_code or target_code not in category_totals:
                # EU country codes for fallback mapping
                eu_countries = ["DE", "FR", "BE", "IT", "ES", "PL", "RO", "NL", "GR", "PT", "CZ", "HU", 
                               "SE", "AT", "BG", "DK", "FI", "IE", "HR", "LT", "LV", "SK", "SI", "EE", 
                               "CY", "LU", "MT"]
                
                invoice_country = invoice.get("country", "").upper()
                
                if transaction_type == "sale":
                    # Default mapping for sales based on VAT percentage
                    if vat_percentage == 21:
                        target_code = "1a"
                    elif vat_percentage == 9:
                        target_code = "1b"
                    elif vat_percentage == 0:
                        # Check country for 0% sales
                        if invoice_country in eu_countries and invoice_country != "NL":
                            target_code = "3b"
                        elif invoice_country and invoice_country not in eu_countries:
                            target_code = "3a"
                        else:
                            target_code = "1e"
                    else:
                        target_code = "1c"  # Other rates (not 0%, 9%, or 21%)
                else:
                    # Purchase - default mapping
                    if "reverse" in str(vat_category).lower() or "reverse-charge" in str(vat_category).lower():
                        target_code = "2a"
                    elif "eu" in str(vat_category).lower() or invoice_country in eu_countries:
                        target_code = "4b"
                    elif "import" in str(vat_category).lower() or (invoice_country and invoice_country not in eu_countries):
                        target_code = "4a"
                    else:
                        # Default to 5a for domestic purchases with VAT, 5b for backward compatibility
                        if vat_amount > 0:
                            target_code = "5a"
                        else:
                            target_code = "5b"
            
            # Add to totals
            if target_code and target_code in category_totals:
                category_totals[target_code]["net_amount"] += amount_pre_vat
                category_totals[target_code]["vat"] += vat_amount
    
    # Calculate section 5 totals
    # 5a: Turnover Tax (sum of sections 1-4 VAT)
    vat_5a = (category_totals["1a"]["vat"] + category_totals["1b"]["vat"] + 
              category_totals["1c"]["vat"] + category_totals["1d"]["vat"] + 
              category_totals["1e"]["vat"] + category_totals["2a"]["vat"] + 
              category_totals["3a"]["vat"] + category_totals["3b"]["vat"] + 
              category_totals["3c"]["vat"])
    
    # 5b: Input Tax (deductible VAT) - includes both 5a and 5b for purchases
    vat_5b = category_totals["5a"]["vat"] + category_totals["5b"]["vat"]
    
    # 5c: Subtotal (5a - 5b)
    vat_5c = vat_5a - vat_5b
    
    # Total: Same as 5c (final VAT payable)
    vat_total = vat_5c
    
    # Round all values
    for code in category_totals:
        category_totals[code]["net_amount"] = round(category_totals[code]["net_amount"], 2)
        category_totals[code]["vat"] = round(category_totals[code]["vat"], 2)
    
    vat_5a = round(vat_5a, 2)
    vat_5b = round(vat_5b, 2)
    vat_5c = round(vat_5c, 2)
    vat_total = round(vat_total, 2)
    
    # Build report structure
    report_meta = {
        "report_type": "VAT_Return",
        "jurisdiction": "NL",
        "company_name": company_details.get("company_name", "N/A") if company_details else "N/A",
        "vat_number": company_details.get("company_vat", "N/A") if company_details else "N/A",
        "period": f"{quarter} {year}",
        "submission_date": datetime.now().strftime("%Y-%m-%d")
    }
    
    sections = [
        {
            "id": "1",
            "title": "Domestic Performance",
            "rows": [
                {
                    "code": "1a",
                    "description": "Supplies/services taxed at standard rate (High)",
                    "net_amount": category_totals["1a"]["net_amount"],
                    "vat": category_totals["1a"]["vat"]
                },
                {
                    "code": "1b",
                    "description": "Supplies/services taxed at reduced rate (Low)",
                    "net_amount": category_totals["1b"]["net_amount"],
                    "vat": category_totals["1b"]["vat"]
                },
                {
                    "code": "1c",
                    "description": "Supplies/services taxed at other rates, except 0%",
                    "net_amount": category_totals["1c"]["net_amount"],
                    "vat": category_totals["1c"]["vat"]
                },
                {
                    "code": "1d",
                    "description": "Private use",
                    "net_amount": category_totals["1d"]["net_amount"],
                    "vat": category_totals["1d"]["vat"]
                },
                {
                    "code": "1e",
                    "description": "Supplies/services taxed at 0% or not taxed",
                    "net_amount": category_totals["1e"]["net_amount"],
                    "vat": category_totals["1e"]["vat"]
                }
            ]
        },
        {
            "id": "2",
            "title": "Domestic Reverse Charge Schemes",
            "rows": [
                {
                    "code": "2a",
                    "description": "Supplies/services where VAT liability is shifted to you",
                    "net_amount": category_totals["2a"]["net_amount"],
                    "vat": category_totals["2a"]["vat"]
                }
            ]
        },
        {
            "id": "3",
            "title": "Performance to or in Foreign Countries",
            "rows": [
                {
                    "code": "3a",
                    "description": "Supplies to countries outside the EU (Exports)",
                    "net_amount": category_totals["3a"]["net_amount"],
                    "vat": category_totals["3a"]["vat"]
                },
                {
                    "code": "3b",
                    "description": "Supplies to/in countries within the EU",
                    "net_amount": category_totals["3b"]["net_amount"],
                    "vat": category_totals["3b"]["vat"]
                },
                {
                    "code": "3c",
                    "description": "Installation/distance sales within the EU",
                    "net_amount": category_totals["3c"]["net_amount"],
                    "vat": category_totals["3c"]["vat"]
                }
            ]
        },
        {
            "id": "4",
            "title": "Performance from Abroad to You",
            "rows": [
                {
                    "code": "4a",
                    "description": "Supplies/services from countries outside the EU",
                    "net_amount": category_totals["4a"]["net_amount"],
                    "vat": category_totals["4a"]["vat"]
                },
                {
                    "code": "4b",
                    "description": "Supplies/services from countries within the EU",
                    "net_amount": category_totals["4b"]["net_amount"],
                    "vat": category_totals["4b"]["vat"]
                }
            ]
        },
        {
            "id": "5",
            "title": "Totals",
            "rows": [
                {
                    "code": "5a",
                    "description": "Turnover Tax (Subtotal sections 1 to 4)",
                    "net_amount": None,
                    "vat": vat_5a
                },
                {
                    "code": "5b",
                    "description": "Input Tax (Deductible VAT)",
                    "net_amount": None,
                    "vat": vat_5b
                },
                {
                    "code": "5c",
                    "description": "Subtotal (5a minus 5b)",
                    "net_amount": None,
                    "vat": vat_5c
                },
                {
                    "code": "5d",
                    "description": "Reduction according to small business scheme (KOR)",
                    "net_amount": None,
                    "vat": 0.00
                },
                {
                    "code": "5e",
                    "description": "Estimate previous return",
                    "net_amount": None,
                    "vat": 0.00
                },
                {
                    "code": "5f",
                    "description": "Estimate",
                    "net_amount": None,
                    "vat": 0.00
                },
                {
                    "code": "Total",
                    "description": "Total to Pay / Reclaim",
                    "net_amount": None,
                    "vat": vat_total
                }
            ]
        }
    ]
    
    # Debug info (can be removed in production)
    debug_info = {
        "total_invoices_in_year": len(data.get("invoices", [])),
        "invoices_in_quarter": invoices_processed,
        "invoices_skipped": invoices_skipped,
        "target_months": target_months,
        "quarter_requested": quarter,
        "year_requested": year
    }
    
    return {
        "report_meta": report_meta,
        "sections": sections,
        "_debug": debug_info  # Remove this in production if not needed
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "VAT Analysis API is running"}
