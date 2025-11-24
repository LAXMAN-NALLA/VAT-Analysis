from fastapi import FastAPI, Request, HTTPException, Header, UploadFile, File, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json
from fastapi.middleware.cors import CORSMiddleware
from processor import upload_pdf_to_user_folder, process_data, calculate_vat_amount, calculate_total_with_vat, validate_vat_calculation, get_vat_rate_by_category, calculate_vat_payable, process_json_invoices, get_user_company_details
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

# ==================== USER INFO ROUTE ====================

@app.get("/user-info")
async def get_user_info(user_id: str = Header(..., alias="X-User-ID")):
    """Get user's data information"""
    try:
        # In-memory storage
        pdf_count = user_pdf_count.get(user_id, 0)
        processed_years = list(user_vat_data.get(user_id, {}).keys())
        
        # ==================== COMMENTED OUT - S3 Integration ====================
        # # Check if user has any data
        # prefix = f"users/{user_id}/"
        # existing_files = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        # 
        # pdf_count = 0
        # if "Contents" in existing_files:
        #     for obj in existing_files["Contents"]:
        #         if obj["Key"].endswith(".pdf"):
        #             pdf_count += 1
        # 
        # # Check for existing results
        # results_prefix = f"users/{user_id}/results/"
        # results_files = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=results_prefix)
        # 
        # processed_years = []
        # if "Contents" in results_files:
        #     for obj in results_files["Contents"]:
        #         if obj["Key"].endswith(".json") and "VATanalysis_" in obj["Key"]:
        #             year = obj["Key"].split("VATanalysis_")[-1].split(".json")[0]
        #             processed_years.append(year)
        
        return {
            "user_id": user_id,
            "pdf_count": pdf_count,
            "processed_years": processed_years,
            "max_pdfs": 20
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user info: {str(e)}")

# ==================== PDF UPLOAD ROUTE ====================

from typing import List

@app.post("/upload")
async def upload_pdf(user_id: str = Header(..., alias="X-User-ID"), files: List[UploadFile] = File(...)):
    """Upload PDF files for VAT analysis"""
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing X-User-ID header")

    # In-memory storage
    pdf_count = user_pdf_count.get(user_id, 0)
    
    # ==================== COMMENTED OUT - S3 Integration ====================
    # # ✅ Check how many PDFs already exist in user folder
    # prefix = f"users/{user_id}/"
    # existing_pdfs = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    # 
    # pdf_count = 0
    # if "Contents" in existing_pdfs:
    #     for obj in existing_pdfs["Contents"]:
    #         if obj["Key"].endswith(".pdf"):
    #             pdf_count += 1

    # ✅ First check new files count
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="❌ You can only select up to 20 files at a time.")

    # ✅ Then check total files count after upload
    if pdf_count + len(files) > 20:
        raise HTTPException(
            status_code=400,
            detail=f"❌ Uploading {len(files)} files would exceed your limit of 20 PDFs. You currently have {pdf_count} PDFs."
        )

    # ✅ Upload the files one by one
    for file in files:
        # upload_pdf_to_user_folder(user_id, file)  # COMMENTED OUT - S3 upload disabled
        user_pdf_count[user_id] = user_pdf_count.get(user_id, 0) + 1  # Track PDF count in memory
        log_user_event(user_id, "PDF Uploaded", {"filename": file.filename})

    uploaded_files = [file.filename for file in files]

    return {
        "message": f"✅ Uploaded {len(files)} file(s) successfully.",
        "files_uploaded": uploaded_files
    }




# ==================== VAT PROCESSING ROUTE ====================

@app.post("/trigger")
async def trigger(
    user_id: str = Header(..., alias="X-User-ID"),
    company_name: str = Header(None, alias="X-Company-Name"),
    company_vat: str = Header(None, alias="X-Company-VAT")
):
    """Trigger VAT analysis processing for uploaded PDFs"""
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing X-User-ID header")

    result = process_data(user_id, company_name, company_vat)
    log_user_event(user_id, "Triggered VAT Analysis", {
        "company_name": company_name,
        "company_vat": company_vat
    })
    return {"message": result}

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
    Store analyzed invoice data directly (NEW SIMPLE APPROACH)
    
    **Input Format:**
    Simple JSON array of analyzed invoices:
    ```json
    [
      {
        "date": "2025-09-25",
        "type": "Purchase",
        "net_amount": 4357.46,
        "vat_amount": null,
        "vat_category": "Zero Rated",
        "vat_percentage": "0",
        "description": "SEPTEMBER SALES",
        "vendor_name": "PAE Business Ltd",
        "file_name": "Invoice_26411.pdf"
      },
      ...
    ]
    ```
    
    **Required Header:**
    - `X-User-ID`: Your user identifier
    
    **No processing needed** - data is already analyzed and ready to use!
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
                # Extract basic info
                date_str = invoice_item.get("date", "")
                invoice_type = invoice_item.get("type", "").lower()
                file_name = invoice_item.get("file_name", "")
                
                # Extract year from date
                year = "unknown"
                if date_str:
                    try:
                        # Try common date formats
                        for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"]:
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
                input_invoice_number = invoice_item.get("invoice_number") or invoice_item.get("invoice_no")
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
                
                # Map VAT category to code
                vat_category_str = invoice_item.get("vat_category", "")
                vat_percentage = invoice_item.get("vat_percentage", "0")
                vat_category_code = map_vat_category_simple(vat_category_str, transaction_type, vat_percentage)
                
                # Extract amounts
                net_amount = normalize_amount(invoice_item.get("net_amount", 0))
                vat_amount = normalize_amount(invoice_item.get("vat_amount", 0)) if invoice_item.get("vat_amount") is not None else 0.0
                gross_amount = normalize_amount(invoice_item.get("gross_amount", 0))
                
                # Extract vendor/customer name - handle both field name formats
                # For purchases: use vendor_name (the supplier)
                # For sales: use customer_name (the buyer)
                if transaction_type == "purchase":
                    # Try multiple field name variations for vendor
                    invoice_to = (
                        invoice_item.get("vendor_name") or 
                        invoice_item.get("Vendor Name") or 
                        invoice_item.get("vendor") or 
                        ""
                    )
                else:  # sale
                    # Try multiple field name variations for customer
                    invoice_to = (
                        invoice_item.get("customer_name") or 
                        invoice_item.get("Customer Name") or 
                        invoice_item.get("customer") or 
                        ""
                    )
                
                # Build invoice structure
                invoice = {
                    "invoice_no": invoice_item.get("invoice_number") or invoice_item.get("invoice_no") or file_name.replace(".pdf", ""),
                    "date": date_str,
                    "invoice_to": invoice_to,
                    "country": invoice_item.get("country", ""),
                    "vat_no": invoice_item.get("vendor_vat_id") if transaction_type == "purchase" else invoice_item.get("customer_vat_id", ""),
                    "transactions": [{
                        "description": invoice_item.get("description", ""),
                        "amount_pre_vat": net_amount,
                        "vat_percentage": f"{vat_percentage}%",
                        "vat_category": vat_category_code
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

def map_vat_category_simple(vat_category_str, transaction_type, vat_percentage):
    """
    Multi-Field VAT Category Mapping Logic
    
    Priority Order:
    1. Check Category (vat_category string)
    2. Check Type (Sales or Purchase)
    3. Check Rate (vat_percentage) - CRUCIAL for "Standard VAT" to resolve 21% vs 9%
    
    This follows the exact logic table:
    - "Standard VAT" + Sales + 21% → 1a
    - "Standard VAT" + Sales + 9% → 1b
    - "Standard VAT" + Purchase + Any% → 5b
    - "Reduced Rate" + Sales → 1b
    - "Reduced Rate" + Purchase → 5b
    - "Zero Rated" + Sales → 1c
    - "Zero Rated" + Purchase → 4a
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
    
    # --- LOGIC FOR ZERO RATED / EU ---
    if "zero rated" in category_lower or "zero-rated" in category_lower:
        if tx_type == "sale" or tx_type == "sales":
            return "1c"  # General Exports / Zero Rated sales
        elif tx_type == "purchase":
            return "4a"  # Assumes EU Goods Purchase
    
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
    # Default based on transaction type and VAT percentage
    if tx_type == "sale" or tx_type == "sales":
        if percentage == 21:
            return "1a"
        elif percentage == 9:
            return "1b"
        elif percentage == 0:
            return "1c"
        else:
            return "1a"  # Default to standard rate
    elif tx_type == "purchase":
        if percentage == 0:
            return "2a"  # Default to reverse charge for zero-rated purchases
        else:
            return "5b"  # Default to domestic input VAT
    
    # Final fallback
    return "5b"  # Default to domestic input VAT

# ==================== COMMENTED OUT - OLD PROCESSING APPROACH ====================
# @app.post("/process-invoices", response_model=Dict[str, Any])
# async def process_invoices_json(
#     user_id: str = Header(..., alias="X-User-ID"),
#     invoice_data: InvoiceProcessingRequest = Body(..., description="Invoice data in standard format. Use the form below or send raw JSON in 'Try it out'.")
# ):
#     """
#     Process invoices from JSON format (OLD APPROACH - COMMENTED OUT)
#     """
#     # ... old code commented out ...

# ==================== COMMENTED OUT - OLD PROCESSING APPROACH ====================
# @app.post("/process-invoices-raw")
# async def process_invoices_json_raw(
#     request: Request,
#     user_id: str = Header(..., alias="X-User-ID")
# ):
#     """
#     OLD APPROACH - Process invoices from raw JSON (COMMENTED OUT)
#     """
#     # ... old code commented out ...

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

# ==================== VAT SUMMARY ROUTE ====================

@app.get("/vat-summary")
async def get_vat_summary(user_id: str = Header(..., alias="X-User-ID"), year: str = ""):
    """Get VAT summary for a specific year"""
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
            "monthly_data": [], "total_vat": 0, "total_amount": 0, "transactions": []
        }
    
    # ==================== COMMENTED OUT - S3 Integration ====================
    # json_key = f"users/{user_id}/results/VATanalysis_{year}.json"
    # try:
    #     obj = s3_client.get_object(Bucket=bucket_name, Key=json_key)
    #     data = json.loads(obj['Body'].read().decode('utf-8'))
    # except s3_client.exceptions.NoSuchKey:
    #     return {
    #         "monthly_data": [], "total_vat": 0, "total_amount": 0, "transactions": []
    #     }

    monthly_vat = defaultdict(lambda: {"Domestic VAT": 0.0, "Intra-EU VAT": 0.0, "Import VAT": 0.0})
    quarterly_vat = defaultdict(lambda: {"Domestic VAT": 0.0, "Intra-EU VAT": 0.0, "Import VAT": 0.0})
    total_vat = 0.0
    total_amt = 0.0
    transactions = []

    for invoice in data.get("invoices", []):
        dt = try_parse_date(invoice.get("date", ""))
        if not dt: continue
        month = dt.strftime("%b")
        quarter = get_quarter_from_month(month)
        vat = normalize_amount(invoice.get("vat_amount", "0"))
        total = normalize_amount(invoice.get("total_amount", "0"))
        transaction_type = invoice.get("transaction_type", "sale")
        
        # Categorize VAT based on transaction type
        if transaction_type == "sale":
            # VAT collected from sales
            monthly_vat[month]["Domestic VAT"] += vat
            quarterly_vat[quarter]["Domestic VAT"] += vat
        else:
            # VAT paid on purchases (input VAT)
            monthly_vat[month]["Input VAT"] = monthly_vat[month].get("Input VAT", 0.0) + vat
            quarterly_vat[quarter]["Input VAT"] = quarterly_vat[quarter].get("Input VAT", 0.0) + vat
        
        total_vat += vat
        total_amt += total
        for tx in invoice.get("transactions", []):
            transactions.append({
                "invoice_no": invoice.get("invoice_no"),
                "date": invoice.get("date"),
                "description": tx.get("description"),
                "amount_pre_vat": tx.get("amount_pre_vat"),
                "vat_percentage": tx.get("vat_percentage"),
                "vat_category": tx.get("vat_category", "N/A"),
                "country": invoice.get("country", "N/A"),
                "transaction_type": transaction_type
            })

    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_data = [{ "month": m, **monthly_vat[m] } for m in month_order if m in monthly_vat]

    # Prepare quarterly data
    quarter_order = ['Q1', 'Q2', 'Q3', 'Q4']
    quarterly_data = []
    for quarter in quarter_order:
        if quarter in quarterly_vat:
            quarterly_data.append({
                "quarter": quarter,
                "quarter_name": get_quarter_name(quarter),
                **quarterly_vat[quarter]
            })

    return {
        "monthly_data": monthly_data,
        "quarterly_data": quarterly_data,
        "total_vat": round(total_vat, 2),
        "total_amount": round(total_amt, 2),
        "transactions": transactions
    }


# ===================== transactions

@app.get("/transactions")
async def get_transactions(user_id: str = Header(..., alias="X-User-ID"), year: str = ""):
    """Get detailed transactions for a specific year"""
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
        return {"transactions": []}
    
    # ==================== COMMENTED OUT - S3 Integration ====================
    # json_key = f"users/{user_id}/results/VATanalysis_{year}.json"
    # try:
    #     obj = s3_client.get_object(Bucket=bucket_name, Key=json_key)
    #     data = json.loads(obj['Body'].read().decode('utf-8'))
    # except s3_client.exceptions.NoSuchKey:
    #     return {"transactions": []}

    transactions = []
    for invoice in data.get("invoices", []):
        for txn in invoice.get("transactions", []):
            transactions.append({
                "invoice_no": invoice.get("invoice_no"),
                "date": invoice.get("date"),
                "description": txn.get("description"),
                "amount_pre_vat": txn.get("amount_pre_vat"),
                "vat_percentage": txn.get("vat_percentage"),
                "vat_category": txn.get("vat_category", "N/A"),
                "country": invoice.get("country", "N/A"),
                "transaction_type": invoice.get("transaction_type", "sale")
            })

    return {"transactions": transactions}


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


# ==================== QUARTERLY VAT SUMMARY ROUTE ====================

@app.get("/vat-quarterly")
async def get_vat_quarterly(user_id: str = Header(..., alias="X-User-ID"), year: str = ""):
    """Get quarterly VAT summary for a specific year"""
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
            "quarterly_data": [], 
            "total_vat": 0, 
            "total_amount": 0, 
            "year": year
        }
    
    # ==================== COMMENTED OUT - S3 Integration ====================
    # json_key = f"users/{user_id}/results/VATanalysis_{year}.json"
    # try:
    #     obj = s3_client.get_object(Bucket=bucket_name, Key=json_key)
    #     data = json.loads(obj['Body'].read().decode('utf-8'))
    # except s3_client.exceptions.NoSuchKey:
    #     return {
    #         "quarterly_data": [], 
    #         "total_vat": 0, 
    #         "total_amount": 0, 
    #         "year": year
    #     }

    quarterly_vat = defaultdict(lambda: {"Domestic VAT": 0.0, "Intra-EU VAT": 0.0, "Import VAT": 0.0})
    total_vat = 0.0
    total_amt = 0.0

    for invoice in data.get("invoices", []):
        dt = try_parse_date(invoice.get("date", ""))
        if not dt: continue
        month = dt.strftime("%b")
        quarter = get_quarter_from_month(month)
        vat = normalize_amount(invoice.get("vat_amount", "0"))
        total = normalize_amount(invoice.get("total_amount", "0"))
        transaction_type = invoice.get("transaction_type", "sale")
        
        # Categorize VAT based on transaction type
        if transaction_type == "sale":
            # VAT collected from sales
            quarterly_vat[quarter]["Domestic VAT"] += vat
        else:
            # VAT paid on purchases (input VAT)
            quarterly_vat[quarter]["Input VAT"] = quarterly_vat[quarter].get("Input VAT", 0.0) + vat
        
        total_vat += vat
        total_amt += total

    # Prepare quarterly data with proper ordering
    quarter_order = ['Q1', 'Q2', 'Q3', 'Q4']
    quarterly_data = []
    for quarter in quarter_order:
        if quarter in quarterly_vat:
            quarterly_data.append({
                "quarter": quarter,
                "quarter_name": get_quarter_name(quarter),
                **quarterly_vat[quarter]
            })

    return {
        "year": year,
        "quarterly_data": quarterly_data,
        "total_vat": round(total_vat, 2),
        "total_amount": round(total_amt, 2)
    }


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
        "2a": {"name": "Reverse-Charge Supplies", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "3a": {"name": "Supplies of Goods to EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "3b": {"name": "Supplies of Services to EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "4a": {"name": "Purchases of Goods from EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "4b": {"name": "Purchases of Services from EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "4c": {"name": "Purchases of Goods from Non-EU Countries (Imports)", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
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
        "2a": {"name": "Reverse-Charge Supplies", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "3a": {"name": "Supplies of Goods to EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "3b": {"name": "Supplies of Services to EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "4a": {"name": "Purchases of Goods from EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "4b": {"name": "Purchases of Services from EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "4c": {"name": "Purchases of Goods from Non-EU Countries (Imports)", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
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
        "2a": {"name": "Reverse-Charge Supplies", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "3a": {"name": "Supplies of Goods to EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "3b": {"name": "Supplies of Services to EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "4a": {"name": "Purchases of Goods from EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "4b": {"name": "Purchases of Services from EU Countries", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
        "4c": {"name": "Purchases of Goods from Non-EU Countries (Imports)", "transactions": [], "totals": {"net": 0.0, "vat": 0.0}},
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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "VAT Analysis API is running"}
