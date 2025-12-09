# Code Walkthrough - Key Code Snippets Explained

## 1. Storage Initialization

```python
# app.py lines 30-41
from collections import defaultdict

# In-memory storage dictionaries
user_vat_data = defaultdict(dict)  # {user_id: {year: {invoices: []}}}
user_company_details = {}          # {user_id: {company_name, company_vat}}
user_pdf_count = defaultdict(int)  # {user_id: count}
```

**Explanation**:
- `defaultdict(dict)` automatically creates nested dictionaries
- Structure: `user_vat_data[user_id][year]["invoices"]`
- No need to check if keys exist - defaultdict handles it
- Simple but effective for MVP

---

## 2. Field Name Flexibility Helper

```python
# app.py lines 280-288
def get_field_value(*field_names, default=None):
    """Try multiple field name variations"""
    for field_name in field_names:
        value = invoice_item.get(field_name)
        if value is not None and value != "":
            # Handle NaN values from Excel/CSV exports
            if isinstance(value, float) and (value != value):  # NaN check
                return default
            return value
    return default

# Usage example:
vat_category_code = get_field_value(
    "VAT Category (NL) Code", 
    "vat_category_nl_code",
    "vat_category_code",
    default=""
)
```

**Explanation**:
- Accepts multiple field name variations (handles different input formats)
- Checks each name until one is found
- Handles NaN values (common from Excel exports)
- Returns default if none found
- **Why**: Different systems use different field names - this makes it flexible

---

## 3. Duplicate Detection

```python
# app.py lines 319-330
existing_invoices = user_vat_data[user_id][year].get("invoices", [])
is_duplicate = any(
    # Check by file name (always check this)
    inv.get("source_file") == file_name or inv.get("file_name") == file_name or
    # Check by invoice number (if provided and different from file_name)
    (input_invoice_number and 
     input_invoice_number != file_name_base and 
     inv.get("invoice_no") == input_invoice_number)
    for inv in existing_invoices
)

if is_duplicate:
    skipped_count += 1
    continue
```

**Explanation**:
- Uses `any()` with generator expression for efficiency
- Checks two conditions:
  1. File name match (primary check)
  2. Invoice number match (if provided and different from filename)
- Stops at first match (efficient)
- **Why**: Prevents processing same invoice multiple times

---

## 4. VAT Category Extraction (New Approach)

```python
# app.py lines 339-375
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
    # ... mapping logic ...
    vat_category_code = map_vat_category_simple(vat_category_str, transaction_type, vat_percentage, country)
```

**Explanation**:
- **Primary**: Uses provided `VAT Category (NL) Code` directly (e.g., "1a", "1b")
- **Fallback**: If not provided, uses old mapping function for backward compatibility
- Stores both code and description
- **Why**: New approach is more accurate, but we keep backward compatibility

---

## 5. Invoice Storage Structure

```python
# app.py lines 406-425
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
        "vat_category": vat_category_code,  # Direct NL code
        "vat_category_description": vat_category_description
    }],
    "subtotal": net_amount,
    "vat_amount": vat_amount,
    "total_amount": gross_amount,
    "transaction_type": transaction_type,
    "source_file": file_name
}

# Store
user_vat_data[user_id][year]["invoices"].append(invoice)
```

**Explanation**:
- Each invoice has metadata (date, invoice_no, etc.)
- `transactions` array (supports multiple line items per invoice)
- Stores VAT category code directly (no mapping needed later)
- Organized by user and year
- **Why**: Structured format makes report generation easy

---

## 6. Quarter Filtering

```python
# app.py lines 1641-1680
quarter_months = {
    "Q1": ["Jan", "Feb", "Mar"],
    "Q2": ["Apr", "May", "Jun"], 
    "Q3": ["Jul", "Aug", "Sep"],
    "Q4": ["Oct", "Nov", "Dec"]
}

target_months = quarter_months.get(quarter, [])

for invoice in data.get("invoices", []):
    dt = try_parse_date(invoice.get("date", ""))
    if not dt: 
        invoices_skipped += 1
        continue
    
    month = dt.strftime("%b")  # "Jan", "Feb", etc.
    if month not in target_months: 
        invoices_skipped += 1
        continue
    
    # Process invoice for this quarter
    invoices_processed += 1
```

**Explanation**:
- Maps quarter to months
- Parses date and extracts month abbreviation
- Filters invoices by month
- Tracks processed vs skipped
- **Why**: Need to filter invoices by quarter for quarterly reports

---

## 7. Category Aggregation

```python
# app.py lines 1650-1665
# Initialize category totals
category_totals = {
    "1a": {"net_amount": 0.0, "vat": 0.0},
    "1b": {"net_amount": 0.0, "vat": 0.0},
    "1c": {"net_amount": 0.0, "vat": 0.0},
    # ... more categories
    "5a": {"net_amount": 0.0, "vat": 0.0},
    "5b": {"net_amount": 0.0, "vat": 0.0},
}

# Accumulate totals
for invoice in invoices:
    for tx in invoice.get("transactions", []):
        vat_category = tx.get("vat_category", "")
        amount_pre_vat = normalize_amount(tx.get("amount_pre_vat", 0))
        vat_amount = normalize_amount(tx.get("vat_amount", 0))
        
        if vat_category in category_totals:
            category_totals[vat_category]["net_amount"] += amount_pre_vat
            category_totals[vat_category]["vat"] += vat_amount
```

**Explanation**:
- Initialize all categories with zero totals
- Iterate through all invoices and transactions
- Group by VAT category code
- Accumulate net amounts and VAT
- **Why**: Need totals per category for reports

---

## 8. VAT Calculation (Sales vs Purchases)

```python
# app.py lines 1083-1088
vat_collected = 0.0
vat_deductible = 0.0

for invoice in data.get("invoices", []):
    transaction_type = invoice.get("transaction_type", "sale")
    for tx in invoice.get("transactions", []):
        vat_amount = normalize_amount(tx.get("vat_amount", 0))
        
        if transaction_type == "sale":
            vat_collected += vat_amount  # Output VAT
        else:
            vat_deductible += vat_amount  # Input VAT

vat_payable = vat_collected - vat_deductible
```

**Explanation**:
- Separate tracking for sales (collected) and purchases (deductible)
- Sum all VAT amounts based on transaction type
- Calculate net payable
- **Why**: Dutch VAT return requires separate output and input VAT

---

## 9. Dreport Section 5 Calculations

```python
# app.py lines 1791-1806
# 5a: Turnover Tax (sum of sections 1-4 VAT)
vat_5a = (
    category_totals["1a"]["vat"] +
    category_totals["1b"]["vat"] +
    category_totals["1c"]["vat"] +
    category_totals["1d"]["vat"] +
    category_totals["1e"]["vat"] +
    category_totals["2a"]["vat"] +
    category_totals["3a"]["vat"] +
    category_totals["3b"]["vat"] +
    category_totals["3c"]["vat"]
)

# 5b: Input Tax (deductible VAT) - includes both 5a and 5b for purchases
vat_5b = category_totals["5a"]["vat"] + category_totals["5b"]["vat"]

# 5c: Subtotal (5a - 5b)
vat_5c = vat_5a - vat_5b

# Total: Same as 5c (final VAT payable)
vat_total = vat_5c
```

**Explanation**:
- **5a**: Sum of all output VAT (sections 1-4) - what you collected
- **5b**: Sum of all input VAT (purchases) - what you can deduct
- **5c**: Net VAT payable (5a - 5b)
- **Why**: This matches Dutch tax authority format exactly

---

## 10. Date Parsing (Multiple Formats)

```python
# app.py lines 48-54
def try_parse_date(date_str):
    """Try multiple date formats"""
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%d-%m-%y", 
                "%d/%m/%y", "%d.%m.%y", "%d %B %Y", "%d %b %Y", 
                "%b %d, %Y", "%B %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except:
            continue
    return None
```

**Explanation**:
- Tries multiple date formats in order
- Returns first successful parse
- Returns None if all fail
- **Why**: Different systems export dates in different formats

---

## 11. Amount Normalization

```python
# processor.py
def normalize_amount(value):
    """Convert various types to float, handle NaN/None"""
    if value is None:
        return 0.0
    if isinstance(value, str):
        # Remove currency symbols, commas
        value = value.replace("€", "").replace("$", "").replace(",", "").strip()
        try:
            return float(value)
        except:
            return 0.0
    if isinstance(value, (int, float)):
        # Handle NaN
        if value != value:  # NaN check
            return 0.0
        return float(value)
    return 0.0
```

**Explanation**:
- Handles None, strings, numbers
- Removes currency symbols
- Handles NaN values
- Returns 0.0 for invalid values
- **Why**: Input data comes in various formats - need consistent float values

---

## 12. Report Generation Structure

```python
# app.py lines 1828-1950
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
            # ... more rows
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
            # ... more rows
        ]
    }
]

return {
    "report_meta": {...},
    "sections": sections,
    "_debug": {...}
}
```

**Explanation**:
- Structured into sections matching Dutch tax format
- Each section has rows with code, description, amounts
- Section 5 contains calculated totals
- Includes metadata and debug info
- **Why**: Matches official Dutch tax authority format

---

## Key Patterns Summary

1. **Flexible Field Names**: `get_field_value()` handles variations
2. **Efficient Filtering**: List comprehensions and `any()` for duplicates
3. **Structured Storage**: Nested dictionaries for organization
4. **Category Aggregation**: Initialize → Iterate → Accumulate
5. **Date Handling**: Multiple format support
6. **Amount Normalization**: Handle various input types
7. **Report Structure**: Match official format exactly

---

## Code Quality Features

- **Type Hints**: FastAPI uses for validation
- **Error Handling**: Try-except blocks with meaningful errors
- **Default Values**: Safe defaults for missing data
- **Validation**: Check for None, empty strings, NaN
- **Documentation**: Docstrings for all endpoints
- **Modular**: Helper functions in `processor.py`

