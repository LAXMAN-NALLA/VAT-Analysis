
# import boto3  # COMMENTED OUT - S3 integration disabled for now
import json
from fastapi import UploadFile
from io import BytesIO
import openai
from datetime import datetime
import time
import base64
import os  # Still needed for environment variables
from dotenv import load_dotenv  # Still needed for environment variables

# Load environment variables
load_dotenv()

# OpenAI Configuration
openai.api_key = os.getenv('OPENAI_API_KEY', 'your-openai-api-key-here')

# ==================== COMMENTED OUT - S3 Integration (for future use) ====================
# # Configuration
# bucket_name = os.getenv('S3_BUCKET_NAME', 'vat-analysis-new')
# region_name = os.getenv('AWS_DEFAULT_REGION', 'ap-south-1')
# 
# # AWS Credentials
# aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
# aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
# 
# # Initialize AWS clients with credentials
# s3_client = boto3.client(
#     's3', 
#     region_name=region_name,
#     aws_access_key_id=aws_access_key_id,
#     aws_secret_access_key=aws_secret_access_key
# )
# textract_client = boto3.client(
#     'textract', 
#     region_name=region_name,
#     aws_access_key_id=aws_access_key_id,
#     aws_secret_access_key=aws_secret_access_key
# )

# ==================== IN-MEMORY STORAGE (Replaces S3) ====================
# These will be set by app.py when it imports this module
# Simple in-memory storage dictionaries
user_vat_data_storage = None  # Will be set to app.user_vat_data
user_company_details_storage = None  # Will be set to app.user_company_details

# Step 1: Invoice Classification Prompt
LLM_CLASSIFICATION_PROMPT = """
You are an expert invoice classifier. Your task is to categorize an invoice as either a **SALE** or **PURCHASE** transaction.

## Instructions:
Carefully analyze the invoice text and classify the transaction type based on the following guidelines:

### PURCHASE Indicators:
- Mentions "Purchase Order", "PO", "P.O.", "PO Number"
- Invoice is FROM a supplier TO your company
- Contains supplier/vendor information
- Your company is listed as the buyer/recipient
- Mentions procurement-related terms (e.g., "procurement", "purchasing", "order")
- References terms like "supplier", "vendor", or "purchase"

### SALE Indicators:
- Invoice is FROM your company TO a customer
- Contains customer/client information
- Your company is listed as the seller/supplier
- Mentions sales-related terms (e.g., "sale", "sold", "transaction")
- References terms like "customer", "client", or "sale"

## Company Context:
- Company Name: {company_name_placeholder}
- VAT Number: {company_vat_placeholder}

### Output Format:
Return ONLY the following JSON format:
{
  "transaction_type": "sale" // or "purchase"
}

Do not include any other explanations or text outside this JSON output.
"""

# Step 2: Data Extraction Prompt  
LLM_EXTRACTION_PROMPT = """
You are a VAT data extraction specialist. Your task is to extract specific invoice data for Dutch VAT reporting.

## Instructions:
Given an invoice document, extract the required fields and return the data in the exact JSON format below.

### Required Fields:
{
  "invoice_no": "",          # The invoice number
  "client_no": "",           # Client number
  "date": "",                # Invoice date
  "invoice_to": "",          # Name of the customer/client (invoice recipient)
  "country": "",             # Country of the client
  "vat_no": "",              # VAT number of the client
  "transactions": [          # List of transactions on the invoice
    {
      "description": "",     # Description of the transaction
      "amount_pre_vat": "",  # Amount before VAT
      "vat_percentage": "",  # VAT rate applied to the transaction
      "vat_category": ""     # One of the predefined VAT categories (see below)
    }
  ],
  "subtotal": "",            # Subtotal (excluding VAT)
  "vat_amount": "",          # VAT amount
  "total_amount": "",        # Total amount (including VAT)
  "source_file": ""          # Filename of the invoice PDF
}

## VAT Categories:

**SALE Categories:**
- 1a → Domestic sales taxed at 21% (standard rate, NL)  
- 1b → Domestic sales taxed at 9% (reduced rate: food, books, etc.)  
- 1c → Sales with 0% VAT to EU countries or exports  
- 3a → Goods supplied to EU countries  
- 3b → Services supplied to EU countries  
- 1d → Exempt sales (e.g., healthcare, financial services, education)  
- 1e → Zero-rated sales (exports, intra-community supplies)

**PURCHASE Categories:**
- 2a → Reverse-charge: services received from foreign vendors  
- 4a → Goods purchased from EU countries  
- 4b → Services purchased from EU countries  
- 5b → Input VAT on domestic purchases  
- 2b → Imports from non-EU countries (import VAT)  
- 5c → Adjustments for Bad Debts (VAT corrections for unpaid invoices)  
- 6a → Exempt purchases related to exempt sales (e.g., healthcare, education)


### Extraction Guidelines:
- Extract the **country** of the **client (invoice recipient)**, not the company issuing the invoice.
- Use the provided filename for the **source_file** (do not include sensitive info or API keys).
- For each transaction, assign the appropriate **vat_category** based on the transaction's description and VAT rate.

### Output Format:
Return ONLY valid JSON. Do not include any explanations, markdown, or additional text. The **source_file** should contain only the filename, no API keys or sensitive info.
"""

import platform

def get_company_context(company_name=None, company_vat=None):
    """Get company context for better invoice classification and extraction"""
    # Use provided values or fall back to environment variables
    company_name = company_name or os.getenv('COMPANY_NAME', 'Your Company Name')
    company_vat = company_vat or os.getenv('COMPANY_VAT_NUMBER', 'NL123456789B01')
    return {
        'company_name': company_name,
        'company_vat': company_vat
    }

def format_date_human_readable(date_str):
    try:
        for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d", "%d %B %Y", "%d %b %Y", "%d-%m-%y", "%d/%m/%y", "%d.%m.%y", "%b %d, %Y", "%B %d, %Y", "%d %B %Y", "%d %b %Y"):
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                day_format = "%#d" if platform.system() == "Windows" else "%-d"
                return dt.strftime(f"{day_format} %B %Y")  # → 8 January 2024
            except ValueError:
                continue
        return date_str
    except:
        return date_str


def normalize_amount(euro_str):
    try:
        # Handle None
        if euro_str is None:
            return 0.0
        
        # Handle NaN values (from Excel/CSV exports)
        if isinstance(euro_str, float):
            # Check if it's NaN (NaN != NaN is True)
            if euro_str != euro_str:
                return 0.0
            return round(float(euro_str), 2)
        
        # If already a number (int), return it
        if isinstance(euro_str, int):
            return round(float(euro_str), 2)
        
        # If string, clean and convert
        if isinstance(euro_str, str):
            # Remove euro sign and space, convert to float using '.' as decimal separator
            clean = euro_str.replace("€", "").replace(",", "").strip()
            if not clean or clean == "" or clean.lower() == "nan":
                return 0.0
            return round(float(clean), 2)
        
        return 0.0
    except (ValueError, TypeError, AttributeError):
        return 0.0

def calculate_vat_amount(pre_vat_amount, vat_percentage):
    """Calculate VAT amount from pre-VAT amount and percentage"""
    try:
        # Extract percentage number from string like "21%" or "21"
        if isinstance(vat_percentage, str):
            vat_percentage = vat_percentage.replace("%", "").strip()
        
        vat_rate = float(vat_percentage) / 100
        vat_amount = pre_vat_amount * vat_rate
        return round(vat_amount, 2)
    except:
        return 0.0

def calculate_total_with_vat(pre_vat_amount, vat_amount):
    """Calculate total amount including VAT"""
    return round(pre_vat_amount + vat_amount, 2)

def validate_vat_calculation(extracted_vat, calculated_vat, tolerance=0.01):
    """Validate if extracted VAT matches calculated VAT within tolerance"""
    return abs(extracted_vat - calculated_vat) <= tolerance

def get_vat_rate_by_category(vat_category):
    """Get VAT rate based on category"""
    vat_rates = {
        # SALE Categories
        "1a": 21.0,  # Domestic sales at 21% (standard rate, NL)
        "1b": 9.0,   # Domestic sales at 9% (reduced rate: food, books, etc.)
        "1c": 0.0,   # Sales with 0% VAT to EU countries or exports
        "3a": 0.0,   # Goods supplied to EU countries
        "3b": 0.0,   # Services supplied to EU countries
        
        # PURCHASE Categories
        "2a": 0.0,   # Reverse-charge: services received from foreign vendors
        "4a": 0.0,   # Goods purchased from EU countries
        "4b": 0.0,   # Services purchased from EU countries
        "5b": 21.0   # Input VAT on domestic purchases (typically 21%)
    }
    return vat_rates.get(vat_category, 21.0)  # Default to 21% if unknown

def calculate_vat_payable(vat_collected, vat_paid):
    """Calculate net VAT payable (VAT collected - VAT paid)"""
    return round(vat_collected - vat_paid, 2)

def map_vat_category_to_code(vat_category_str, transaction_type, vat_percentage=0):
    """
    Map VAT Category string from new format to standard category codes
    
    Args:
        vat_category_str: String like "Reverse Charge", "Zero Rated", etc.
        transaction_type: "Purchase" or "Sales" or "Unclassified"
        vat_percentage: VAT percentage as number (0-100)
    
    Returns:
        Standard VAT category code (1a, 1b, 1c, 2a, 3a, 3b, 4a, 4b, 5b, etc.)
    """
    vat_category_str = str(vat_category_str).strip().lower()
    transaction_type = str(transaction_type).strip().lower()
    
    # Reverse Charge - always 2a
    if "reverse charge" in vat_category_str or "reverse-charge" in vat_category_str:
        return "2a"
    
    # Zero Rated
    if "zero rated" in vat_category_str or "zero-rated" in vat_category_str or "zero rated" in vat_category_str.lower():
        if transaction_type in ["sales", "sale"]:
            # Check if it's EU supply or export
            if "eu" in vat_category_str.lower() or "intra" in vat_category_str.lower():
                return "3a"  # Goods to EU countries
            else:
                return "1c"  # Sales with 0% VAT (exports or zero-rated)
        elif transaction_type in ["purchase", "purchases"]:
            # Check if it's from EU
            if "eu" in vat_category_str.lower() or "intra" in vat_category_str.lower():
                return "4a"  # Goods from EU countries
            else:
                return "4a"  # Default to goods from EU for zero-rated purchases
        else:
            return "1c"  # Default to sales category
    
    # Standard Rate
    if "standard rate" in vat_category_str:
        if transaction_type in ["sales", "sale"]:
            if vat_percentage == 21:
                return "1a"  # Standard 21%
            elif vat_percentage == 9:
                return "1b"  # Reduced 9%
            else:
                return "1a"  # Default to 1a
        elif transaction_type in ["purchase", "purchases"]:
            return "5b"  # Input VAT on domestic purchases
        else:
            return "1a"  # Default
    
    # EU Supplies
    if "eu" in vat_category_str or "intra-community" in vat_category_str:
        if transaction_type in ["sales", "sale"]:
            if "goods" in vat_category_str:
                return "3a"  # Goods to EU
            elif "services" in vat_category_str:
                return "3b"  # Services to EU
            else:
                return "3a"  # Default to goods
        elif transaction_type in ["purchase", "purchases"]:
            if "goods" in vat_category_str:
                return "4a"  # Goods from EU
            elif "services" in vat_category_str:
                return "4b"  # Services from EU
            else:
                return "4a"  # Default to goods
    
    # Import/Export
    if "import" in vat_category_str:
        return "4c"  # Imports from non-EU
    if "export" in vat_category_str:
        return "1c"  # Exports (zero-rated)
    
    # Default mapping based on transaction type and VAT percentage
    if transaction_type in ["sales", "sale"]:
        if vat_percentage == 21:
            return "1a"
        elif vat_percentage == 9:
            return "1b"
        elif vat_percentage == 0:
            return "1c"
        else:
            return "1a"  # Default
    elif transaction_type in ["purchase", "purchases"]:
        if vat_percentage == 0:
            return "2a"  # Likely reverse charge
        else:
            return "5b"  # Input VAT
    else:
        # Unclassified - try to infer from VAT percentage
        if vat_percentage == 0:
            return "1c"
        elif vat_percentage == 9:
            return "1b"
        else:
            return "1a"

def transform_register_entry_to_invoice(register_entry, file_name=""):
    """
    Transform register_entry from new JSON format to internal invoice structure
    
    Args:
        register_entry: Dictionary with fields like Date, Type, VAT %, etc.
        file_name: Original filename
    
    Returns:
        Dictionary in internal invoice format
    """
    try:
        # Extract date and normalize
        date_str = register_entry.get("Date", "")
        
        # Extract amounts - prefer EUR converted amounts, but handle null values
        vat_amount_eur = register_entry.get("VAT Amount (EUR)")
        nett_amount_eur = register_entry.get("Nett Amount (EUR)")
        gross_amount_eur = register_entry.get("Gross Amount (EUR)")
        
        # Fallback to original currency if EUR not available or is null
        if vat_amount_eur is not None:
            vat_amount = vat_amount_eur
        else:
            vat_amount = register_entry.get("VAT Amount", 0)
        
        if nett_amount_eur is not None:
            nett_amount = nett_amount_eur
        else:
            nett_amount = register_entry.get("Nett Amount", 0)
        
        if gross_amount_eur is not None:
            gross_amount = gross_amount_eur
        else:
            gross_amount = register_entry.get("Gross Amount", 0)
        
        # Normalize amounts - handle None, string, or numeric values
        try:
            vat_amount = float(vat_amount) if vat_amount is not None else 0.0
        except (ValueError, TypeError):
            vat_amount = 0.0
        
        try:
            nett_amount = float(nett_amount) if nett_amount is not None else 0.0
        except (ValueError, TypeError):
            nett_amount = 0.0
        
        try:
            gross_amount = float(gross_amount) if gross_amount is not None else 0.0
        except (ValueError, TypeError):
            gross_amount = 0.0
        
        # Extract transaction type - handle "Unclassified" and other variations
        transaction_type_str = register_entry.get("Type", "Unclassified")
        transaction_type_str_lower = str(transaction_type_str).lower() if transaction_type_str else "unclassified"
        
        if transaction_type_str_lower in ["sales", "sale"]:
            transaction_type = "sale"
        elif transaction_type_str_lower in ["purchase", "purchases"]:
            transaction_type = "purchase"
        else:
            # For "Unclassified", try to infer from other fields
            # If it's a purchase, vendor name would be present; if sale, customer name
            vendor_name = register_entry.get("Vendor Name", "")
            customer_name = register_entry.get("Customer Name", "")
            # Default to purchase if unclear
            transaction_type = "purchase" if vendor_name else "sale"
        
        # Map VAT category
        vat_category_str = register_entry.get("VAT Category", "")
        vat_percentage = register_entry.get("VAT %", 0)
        vat_category = map_vat_category_to_code(vat_category_str, transaction_type_str, vat_percentage)
        
        # Build transaction entry
        transaction = {
            "description": register_entry.get("Description", ""),
            "amount_pre_vat": nett_amount,  # Store as number, not string
            "vat_percentage": f"{vat_percentage}%" if vat_percentage is not None else "0%",
            "vat_category": vat_category
        }
        
        # Extract country and VAT numbers from Full_Extraction_Data if available
        full_data = register_entry.get("Full_Extraction_Data", {})
        vendor_vat_id = full_data.get("vendor_vat_id", "")
        customer_vat_id = full_data.get("customer_vat_id", "")
        
        # Extract country from address if available
        country = ""
        if transaction_type == "purchase":
            vendor_address = full_data.get("vendor_address", "")
            # Try to extract country from address (last part usually)
            if vendor_address:
                parts = vendor_address.split(",")
                if parts:
                    country = parts[-1].strip()
        else:
            customer_address = full_data.get("customer_address", "")
            if customer_address:
                parts = customer_address.split(",")
                if parts:
                    country = parts[-1].strip()
        
        # Determine invoice_to and vat_no based on transaction type
        if transaction_type == "purchase":
            invoice_to = register_entry.get("Vendor Name", "")
            vat_no = vendor_vat_id
        else:
            invoice_to = register_entry.get("Customer Name", "")
            vat_no = customer_vat_id
        
        # Build invoice structure
        # Ensure invoice number is extracted correctly (handle both "Invoice Number" and variations)
        invoice_number = register_entry.get("Invoice Number") or register_entry.get("invoice_number") or register_entry.get("Invoice_Number") or ""
        
        invoice = {
            "invoice_no": invoice_number,
            "date": date_str,
            "invoice_to": invoice_to,
            "country": country,
            "vat_no": vat_no,
            "transactions": [transaction],
            "subtotal": nett_amount,  # Store as number, not string
            "vat_amount": vat_amount,  # Store as number, not string
            "total_amount": gross_amount,  # Store as number, not string
            "transaction_type": transaction_type,
            "source_file": file_name
        }
        
        return invoice
    except Exception as e:
        print(f"Error transforming register_entry: {e}")
        return None

def process_json_invoices(user_id, json_data, storage_dict=None):
    """
    Process invoices from new JSON format and store in memory (or S3 if enabled)
    
    Args:
        user_id: User identifier
        json_data: Dictionary with 'results' array containing register_entry objects
        storage_dict: Optional dictionary to store data (for in-memory storage)
    
    Returns:
        Dictionary with processing results
    """
    # Use in-memory storage if provided, otherwise use S3 (if enabled)
    if storage_dict is not None:
        # In-memory storage - load existing data for this user
        all_year_data = storage_dict.get(user_id, {}).copy()  # Make a copy to avoid modifying original during processing
        if not all_year_data:
            all_year_data = {}
    else:
        # ==================== COMMENTED OUT - S3 Integration ====================
        # results_folder = f"users/{user_id}/results"
        # 
        # # Load existing year-wise data
        # all_year_data = {}
        # existing_keys = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=results_folder).get("Contents", [])
        # for obj in existing_keys:
        #     key = obj["Key"]
        #     if key.endswith(".json") and "VATanalysis_" in key:
        #         content = s3_client.get_object(Bucket=bucket_name, Key=key)['Body'].read().decode('utf-8')
        #         year = key.split("VATanalysis_")[-1].split(".json")[0]
        #         all_year_data[year] = json.loads(content)
        all_year_data = {}
    
    updated_years = set()
    processed_count = 0
    skipped_count = 0
    error_count = 0
    
    # Process each result
    results = json_data.get("results", [])
    for result in results:
        if result.get("status") != "success" or not result.get("register_entry"):
            error_count += 1
            continue
        
        register_entry = result.get("register_entry")
        file_name = result.get("file_name", "")
        
        # Transform to internal format
        invoice = transform_register_entry_to_invoice(register_entry, file_name)
        if not invoice:
            error_count += 1
            continue
        
        # Check for duplicates
        invoice_no = invoice.get("invoice_no", "")
        date_str = invoice.get("date", "")
        source_file = invoice.get("source_file", "")
        
        # Extract year from date - handle multiple formats
        year = "unknown"
        if date_str:
            try:
                # Try common date formats
                date_formats = [
                    "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", 
                    "%Y/%m/%d", "%Y-%m-%d", "%d %B %Y", "%d %b %Y",
                    "%B %d, %Y", "%b %d, %Y", "%Y%m%d"
                ]
                for fmt in date_formats:
                    try:
                        dt = datetime.strptime(str(date_str).strip(), fmt)
                        year = str(dt.year)
                        break
                    except (ValueError, TypeError):
                        continue
            except Exception as e:
                print(f"Error parsing date '{date_str}': {e}")
        
        # Check if invoice already exists (by invoice number or source file)
        is_duplicate = False
        duplicate_reason = ""
        if invoice_no:
            for year_data in all_year_data.values():
                for inv in year_data.get("invoices", []):
                    if inv.get("invoice_no") == invoice_no:
                        is_duplicate = True
                        duplicate_reason = f"Invoice number '{invoice_no}' already exists"
                        break
                if is_duplicate:
                    break
        elif source_file:
            # If no invoice number, check by source file
            for year_data in all_year_data.values():
                for inv in year_data.get("invoices", []):
                    if inv.get("source_file") == source_file:
                        is_duplicate = True
                        duplicate_reason = f"Source file '{source_file}' already exists"
                        break
                if is_duplicate:
                    break
        
        if is_duplicate:
            skipped_count += 1
            print(f"⚠️ Skipping duplicate invoice: {duplicate_reason} (Invoice: {invoice_no or source_file})")
            continue
        
        # Add to year data
        if year not in all_year_data:
            all_year_data[year] = {"invoices": []}
        
        all_year_data[year]["invoices"].append(invoice)
        updated_years.add(year)
        processed_count += 1
    
    # Save updated files
    if storage_dict is not None:
        # In-memory storage
        if user_id not in storage_dict:
            storage_dict[user_id] = {}
        # Merge with existing data (don't overwrite, merge years)
        for year, year_data in all_year_data.items():
            if year in storage_dict[user_id]:
                # Merge invoices - avoid duplicates
                existing_invoices = {inv.get("invoice_no"): inv for inv in storage_dict[user_id][year].get("invoices", [])}
                new_invoices = year_data.get("invoices", [])
                for new_inv in new_invoices:
                    inv_no = new_inv.get("invoice_no")
                    if inv_no and inv_no not in existing_invoices:
                        existing_invoices[inv_no] = new_inv
                storage_dict[user_id][year]["invoices"] = list(existing_invoices.values())
            else:
                storage_dict[user_id][year] = year_data
    else:
        # ==================== COMMENTED OUT - S3 Integration ====================
        # # Save updated files
        # for year in updated_years:
        #     key = f"{results_folder}/VATanalysis_{year}.json"
        #     s3_client.put_object(
        #         Bucket=bucket_name,
        #         Key=key,
        #         Body=json.dumps(all_year_data[year], indent=2),
        #         ContentType='application/json'
        #     )
        pass
    
    return {
        "processed": processed_count,
        "skipped": skipped_count,
        "errors": error_count,
        "updated_years": list(updated_years)
    }

def upload_pdf_to_user_folder(user_id: str, file: UploadFile):
    # ==================== COMMENTED OUT - S3 Integration ====================
    # folder_key = f"users/{user_id}/"
    # file_key = f"{folder_key}{file.filename}"
    # s3_client.put_object(Bucket=bucket_name, Key=folder_key)
    # s3_client.upload_fileobj(file.file, bucket_name, file_key)
    # return f"✅ Uploaded '{file.filename}' to s3://{bucket_name}/{file_key}"
    
    # In-memory: Just return success message (PDF count is tracked in app.py)
    return f"✅ Uploaded '{file.filename}' (in-memory storage)"

def is_file_processed(file_name, existing_data):
    """Check if a PDF file is already processed based on source_file field."""
    return any(inv.get("source_file") == file_name for inv in existing_data.get("invoices", []))

def is_invoice_processed(invoice_no, existing_data):
    """Check if the invoice number already exists in the dataset."""
    return any(inv.get("invoice_no") == invoice_no for inv in existing_data.get("invoices", []))

import time

# def contains_nulls_or_empty(obj):
#     if isinstance(obj, dict):
#         for value in obj.values():
#             if contains_nulls_or_empty(value):
#                 return True
#     elif isinstance(obj, list):
#         for item in obj:
#             if contains_nulls_or_empty(item):
#                 return True
#     else:
#         return obj in [None, "", "null"]
#     return False

def is_gemini_data_valid(data):
    if not isinstance(data, dict):
        return False

    required_keys = ["invoice_no", "date", "transactions"]
    if not all(data.get(k) for k in required_keys):
        return False

    # Validate that at least one transaction is fully filled
    for txn in data["transactions"]:
        if all(txn.get(f) for f in ["description", "amount_pre_vat", "vat_percentage", "vat_category"]):
            return True

    return False


def get_user_company_details(user_id, storage_dict=None):
    """Get company details for a user from memory (or S3 if enabled)"""
    if storage_dict is not None:
        # In-memory storage
        company_data = storage_dict.get(user_id)
        if company_data:
            return {
                'company_name': company_data.get('company_name'),
                'company_vat': company_data.get('company_vat')
            }
        return None
    else:
        # ==================== COMMENTED OUT - S3 Integration ====================
        # company_key = f"users/{user_id}/company_details.json"
        # try:
        #     obj = s3_client.get_object(Bucket=bucket_name, Key=company_key)
        #     company_data = json.loads(obj['Body'].read().decode('utf-8'))
        #     return {
        #         'company_name': company_data.get('company_name'),
        #         'company_vat': company_data.get('company_vat')
        #     }
        # except s3_client.exceptions.NoSuchKey:
        #     return None
        return None

def process_data(user_id, company_name=None, company_vat=None):
    # ==================== COMMENTED OUT - Legacy PDF Processing (S3 Integration) ====================
    # This function is for legacy PDF processing with S3. Currently disabled.
    # Use /process-invoices endpoint instead for JSON input processing.
    
    return "❌ Legacy PDF processing is disabled. Please use /process-invoices endpoint with JSON input."
    
    # pdf_folder = f"users/{user_id}/"
    # results_folder = f"users/{user_id}/results"
    # pdf_files = fetch_pdf_from_s3(bucket_name, pdf_folder)
    # 
    # # If company details not provided, try to get from stored user data
    # if not company_name or not company_vat:
    #     stored_company = get_user_company_details(user_id)
    #     if stored_company:
    #         company_name = company_name or stored_company['company_name']
    #         company_vat = company_vat or stored_company['company_vat']
    # 
    # # Load all existing year-wise files
    # all_year_data = {}
    # existing_keys = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=results_folder).get("Contents", [])
    # for obj in existing_keys:
    #     key = obj["Key"]
    #     if key.endswith(".json") and "VATanalysis_" in key:
    #         content = s3_client.get_object(Bucket=bucket_name, Key=key)['Body'].read().decode('utf-8')
    #         year = key.split("VATanalysis_")[-1].split(".json")[0]
    #         all_year_data[year] = json.loads(content)
    # 
    #     updated_years = set()
    # 
    #     # ==================== COMMENTED OUT - S3 Integration ====================
    #     # for pdf_file_name in pdf_files:
    #     #     pdf_file_simple_name = pdf_file_name.split('/')[-1]
    #     # 
    #     #     if any(inv.get("source_file") == pdf_file_simple_name for year_data in all_year_data.values() for inv in year_data.get("invoices", [])):
    #     #         continue
    #     # 
    #     #     try:
    #     #         obj = s3_client.get_object(Bucket=bucket_name, Key=pdf_file_name)
    #     #         pdf_file_bytes = obj['Body'].read()
    #     #     except Exception as e:
    #     #         print(f"❌ Failed to read file {pdf_file_name}: {e}")
    #     #         continue
    #     # 
    #     #     textract_data = extract_with_textract(pdf_file_bytes)
    #     # 
    #     #     # Step 1: Classify the invoice
    #     #     transaction_type = classify_invoice_with_openai(pdf_file_bytes, pdf_file_simple_name, company_name, company_vat)
    #     #     
    #     #     # Step 2: Extract data with classification context
    #     #     openai_data = None
    #     #     for attempt in range(3):
    #     #         openai_data = extract_with_openai(pdf_file_bytes, transaction_type, pdf_file_simple_name, company_name, company_vat)
    #     #         if is_gemini_data_valid(openai_data):  # Reusing the same validation function
    #     #             break
    #     #         print(f"🟡 OpenAI call returned incomplete data (attempt {attempt + 1}/3). Retrying after 60s...")
    #     #         time.sleep(60)
    #     # 
    #     #     # time.sleep(30)  # Always wait 30s between Gemini calls
    #     # 
    #     #     final_invoice = resolve_invoice(textract_data, openai_data)
    #     # 
    #     #     if final_invoice:
    #     #         invoice_no = final_invoice.get("invoice_no", "")
    #     #         if any(invoice_no == inv.get("invoice_no") for year_data in all_year_data.values() for inv in year_data.get("invoices", [])):
    #     #             continue
    #     # 
    #     #         final_invoice["source_file"] = pdf_file_simple_name
    #     # 
    #     #         date_str = final_invoice.get("date", "")
    #     #         try:
    #     #             # Try multiple date formats to extract year
    #     #             for fmt in ("%d %B %Y", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d", "%d %b %Y", "%d-%m-%y", "%d/%m/%y", "%d.%m.%y", "%b %d, %Y", "%B %d, %Y", "%d %B %Y", "%d %b %Y"):
    #     #                 try:
    #     #                     dt = datetime.strptime(date_str.strip(), fmt)
    #     #                     year = str(dt.year)
    #     #                     break
    #     #                 except ValueError:
    #     #                     continue
    #     #             else:
    #     #                 year = "unknown"
    #     #         except:
    #     #             year = "unknown"
    #     # 
    #     #         if year not in all_year_data:
    #     #             all_year_data[year] = {"invoices": []}
    #     # 
    #     #         all_year_data[year]["invoices"].append(final_invoice)
    #     #         updated_years.add(year)

    # ==================== COMMENTED OUT - S3 Integration ====================
    # # Save updated files
    # for year in updated_years:
    #     key = f"{results_folder}/VATanalysis_{year}.json"
    #     s3_client.put_object(
    #         Bucket=bucket_name,
    #         Key=key,
    #         Body=json.dumps(all_year_data[year], indent=2),
    #         ContentType='application/json'
    #     )
    # 
    # total = sum(len(ydata["invoices"]) for ydata in all_year_data.values())
    # return f"✅ Processing complete. Total invoices stored across all years: {total}"



# ==================== COMMENTED OUT - S3 Integration ====================
# def fetch_pdf_from_s3(bucket, folder):
#     try:
#         response = s3_client.list_objects_v2(Bucket=bucket, Prefix=folder)
#         return [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.pdf')]
#     except Exception as e:
#         print(f"Error: {e}")
#         return []
# 
# def load_existing_json(results_folder):
#     key = f"{results_folder}/VATanalysis.json"
#     try:
#         obj = s3_client.get_object(Bucket=bucket_name, Key=key)
#         return json.loads(obj['Body'].read().decode('utf-8'))
#     except:
#         return {"invoices": []}
# 
# def save_json(data, results_folder, updated=False):
#     if updated:
#         key = f"{results_folder}/VATanalysis.json"
#         s3_client.put_object(
#             Bucket=bucket_name,
#             Key=key,
#             Body=json.dumps(data, indent=2),
#             ContentType='application/json'
#         )

def is_pdf_processed(invoice_no, existing_data):
    return any(inv.get("invoice_no") == invoice_no for inv in existing_data.get("invoices", []))

def extract_with_textract(pdf_bytes):
    extracted = {
        "invoice_no": None, "client_no": None, "date": None,
        "invoice_to": None, "vat_no": None,"country": None, "transactions": [],
        "subtotal": None, "vat_amount": None, "total_amount": None
    }
    try:
        response = textract_client.analyze_expense(Document={'Bytes': pdf_bytes})
        for doc in response.get('ExpenseDocuments', []):
            for field in doc.get('SummaryFields', []):
                ftype = field.get('Type', {}).get('Text')
                val = field.get('ValueDetection', {}).get('Text', '')
                if ftype == 'INVOICE_RECEIPT_ID':
                    extracted["invoice_no"] = val
                elif ftype == 'CLIENT_ID':
                    extracted["client_no"] = val
                elif ftype == 'INVOICE_RECEIPT_DATE':
                    extracted["date"] = val
                elif ftype == 'VENDOR_NAME':
                    extracted["invoice_to"] = val
                elif ftype == 'VAT_ID':
                    extracted["vat_no"] = val
                elif ftype == 'SUBTOTAL':
                    extracted["subtotal"] = val
                elif ftype == 'TAX':
                    extracted["vat_amount"] = val
                elif ftype == 'TOTAL':
                    extracted["total_amount"] = val

            for group in doc.get('LineItemGroups', []):
                for item in group.get('LineItems', []):
                    txn = {"description": None, "amount_pre_vat": None, "vat_percentage": "21%", "vat_category": None}
                    for field in item.get('LineItemExpenseFields', []):
                        ftype = field.get('Type', {}).get('Text')
                        val = field.get('ValueDetection', {}).get('Text', '')
                        if ftype == 'ITEM':
                            txn["description"] = val
                        elif ftype == 'PRICE':
                            txn["amount_pre_vat"] = val
                        elif ftype == 'TAX_PERCENTAGE':
                            txn["vat_percentage"] = val or "21%"
                    extracted["transactions"].append(txn)
        return extracted
    except Exception as e:
        print(f"Textract error: {e}")
        return extracted

def classify_invoice_with_openai(pdf_bytes, filename="", company_name=None, company_vat=None):
    """Step 1: Classify invoice as SALE or PURCHASE"""
    try:
        print("🔍 Classifying invoice type...")
        
        # Convert PDF bytes to base64
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        # Get company context and format the prompt
        company_context = get_company_context(company_name, company_vat)
        classification_prompt = LLM_CLASSIFICATION_PROMPT.format(
            company_name_placeholder=company_context['company_name'],
            company_vat_placeholder=company_context['company_vat']
        )
        
        # Add filename context to the prompt
        if filename:
            classification_prompt += f"\n\n## Context:\n- Filename: {filename}"
        
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": classification_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:application/pdf;base64,{pdf_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=100,
            temperature=0.1
        )

        raw = response.choices[0].message.content.strip()

        # Clean any markdown wrapper if present
        if raw.startswith("```"):
            raw = raw.split("```json")[-1].strip("` \n")

        classification = json.loads(raw)
        transaction_type = classification.get("transaction_type", "sale").lower()
        
        print(f"✅ Invoice classified as: {transaction_type.upper()}")
        return transaction_type

    except Exception as e:
        print(f"Classification error: {e}")
        return "sale"  # Default to sale if classification fails

def extract_with_openai(pdf_bytes, transaction_type="sale", filename="", company_name=None, company_vat=None):
    """Step 2: Extract invoice data with transaction type context"""
    try:
        print("🧠 Extracting invoice data...")
        
        # Convert PDF bytes to base64
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        # Get company context and format the prompt
        company_context = get_company_context(company_name, company_vat)
        extraction_prompt = LLM_EXTRACTION_PROMPT.format(
            company_name_placeholder=company_context['company_name'],
            company_vat_placeholder=company_context['company_vat']
        )
        
        # Add transaction type and filename context to the prompt
        if transaction_type or filename:
            context_info = []
            if transaction_type:
                context_info.append(f"- Transaction Type: {transaction_type.upper()}")
            if filename:
                context_info.append(f"- Filename: {filename}")
            
            extraction_prompt += f"\n\n## Context:\n" + "\n".join(context_info)
        
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": extraction_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:application/pdf;base64,{pdf_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=4000,
            temperature=0.1
        )

        raw = response.choices[0].message.content.strip()

        # Clean any markdown wrapper if present
        if raw.startswith("```"):
            raw = raw.split("```json")[-1].strip("` \n")

        structured = json.loads(raw)
        
        # Add transaction type to the extracted data
        structured["transaction_type"] = transaction_type

        print("✅ OpenAI structured JSON extracted.")
        return structured

    except Exception as e:
        print(f"OpenAI error: {e}")
        return {}


def resolve_invoice(textract_data, llm_data):
    resolved = textract_data.copy()  # Start with Textract values

    # For each top-level field, if Textract missed it, use Gemini's value
    

    for key in resolved:
        if not resolved[key] and llm_data.get(key):
            # Format date field consistently
            if key == "date":
                resolved[key] = format_date_human_readable(llm_data[key])
            else:
                resolved[key] = llm_data[key]


    if resolved.get("date"):
        resolved["date"] = format_date_human_readable(resolved["date"])


    # Prefer OpenAI's transactions entirely (it includes vat_category + country)
    if llm_data.get("transactions"):
        resolved["transactions"] = llm_data["transactions"]

    return resolved


def log_user_event(user_id, event, details=None):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": event,
        "details": details or {}
    }
    
    # ==================== COMMENTED OUT - S3 Integration ====================
    # s3_key = f"users/{user_id}/activity_log.jsonl"
    # 
    # try:
    #     existing = s3_client.get_object(Bucket=bucket_name, Key=s3_key)['Body'].read().decode('utf-8')
    # except s3_client.exceptions.NoSuchKey:
    #     existing = ""
    # 
    # updated_log = existing + json.dumps(log_entry) + "\n"
    # s3_client.put_object(Bucket=bucket_name, Key=s3_key, Body=updated_log.encode('utf-8'))
    
    # In-memory: Just print log (can be extended to store in memory if needed)
    print(f"[LOG] {user_id}: {event} - {json.dumps(details or {})}")

