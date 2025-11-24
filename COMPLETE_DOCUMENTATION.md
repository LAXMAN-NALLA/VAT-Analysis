# Complete Project Documentation - VAT Analysis System

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Data Flow](#data-flow)
4. [API Endpoints](#api-endpoints)
5. [Input/Output Formats](#inputoutput-formats)
6. [VAT Category Mapping](#vat-category-mapping)
7. [Usage Examples](#usage-examples)
8. [Error Handling](#error-handling)

---

## Project Overview

### What is This System?
A **VAT (Value Added Tax) Analysis System** that processes analyzed invoice data and generates VAT reports for Dutch tax compliance. The system accepts pre-analyzed invoice data in JSON format and generates quarterly, monthly, and yearly VAT reports.

### Key Features
- ✅ Accepts pre-analyzed invoice data (no processing needed)
- ✅ Automatic VAT category mapping
- ✅ Quarterly, monthly, and yearly report generation
- ✅ In-memory storage (data persists while server runs)
- ✅ Duplicate invoice detection
- ✅ Company details management
- ✅ VAT payable calculations

### Technology Stack
- **Backend**: FastAPI (Python)
- **Storage**: In-memory dictionaries (can be replaced with database/S3)
- **Data Format**: JSON
- **API Style**: RESTful

---

## System Architecture

### High-Level Flow
``
┌─────────────────┐
│  Client/User    │
│  (JSON Array)   │
└────────┬────────┘
`
         │
         │ POST /process-invoices
         ▼
┌─────────────────────────────────┐
│   FastAPI Backend (app.py)      │
│                                  │
│  1. Validate Input              │
│  2. Map VAT Categories          │
│  3. Store in Memory             │
│  4. Organize by Year            │
└────────┬────────────────────────┘
         │
         │ Store
         ▼
┌─────────────────────────────────┐
│   In-Memory Storage             │
│   user_vat_data[user_id][year]  │
└────────┬────────────────────────┘
         │
         │ Retrieve
         ▼
┌─────────────────────────────────┐
│   Report Generation             │
│   - Quarterly                   │
│   - Monthly                     │
│   - Yearly                      │
└────────┬────────────────────────┘
         │
         │ Return JSON
         ▼
┌─────────────────┐
│  Client/User    │
│  (VAT Report)   │
└─────────────────┘
```

### Data Storage Structure

```python
user_vat_data = {
    "user_id_1": {
        "2025": {
            "invoices": [
                {
                    "invoice_no": "INV_001",
                    "date": "2025-01-15",
                    "transactions": [...],
                    "subtotal": 1000.00,
                    "vat_amount": 210.00,
                    "transaction_type": "sale",
                    "vat_category": "1a",
                    ...
                },
                ...
            ]
        },
        "2024": {...}
    },
    "user_id_2": {...}
}
```

---

## Data Flow

### Step 1: Invoice Input
User sends a JSON array of analyzed invoices:

```json
[
  {
    "date": "2025-09-25",
    "type": "Purchase",
    "net_amount": 4357.46,
    "vat_amount": null,
    "vat_category": "Zero Rated",
    "vat_percentage": "0",
    "file_name": "Invoice_26411.pdf",
    ...
  }
]
```

### Step 2: Processing
1. **Validation**: Check required fields
2. **Year Extraction**: Extract year from date
3. **Duplicate Check**: Verify invoice not already stored
4. **VAT Category Mapping**: Convert category string to code
5. **Data Transformation**: Convert to internal format
6. **Storage**: Save to in-memory dictionary

### Step 3: Report Generation
1. **Retrieve Data**: Get invoices for specified period
2. **Filter by Period**: Filter by quarter/month/year
3. **Categorize**: Group by VAT category codes
4. **Calculate**: Sum net amounts and VAT amounts
5. **Format**: Structure as report JSON

### Step 4: Output
Return structured VAT report with:
- Transactions grouped by category
- Totals per category
- Quarterly breakdown (for yearly reports)
- VAT payable calculation

---

## API Endpoints

### Base URL
```
http://localhost:8000
```

### Authentication
All endpoints require the `X-User-ID` header:
```
X-User-ID: your_user_id
```

---

### 1. Process Invoices

**Endpoint**: `POST /process-invoices`

**Description**: Store analyzed invoice data directly. No processing needed - data is already analyzed.

**Headers**:
```
X-User-ID: 369
Content-Type: application/json
```

**Request Body**:
```json
[
  {
    "date": "2025-09-25",
    "type": "Purchase",
    "currency": "EUR",
    "file_name": "Invoice_26411.pdf",
    "net_amount": 4357.46,
    "vat_amount": null,
    "description": "SEPTEMBER SALES",
    "vendor_name": "PAE Business Ltd",
    "gross_amount": 4357.45,
    "vat_category": "Zero Rated",
    "vat_percentage": "0"
  },
  {
    "date": "2025-09-17",
    "type": "Sales",
    "currency": "EUR",
    "file_name": "24700492.pdf",
    "net_amount": 967.6,
    "vat_amount": 203.19,
    "description": "Premier Subscription Package",
    "vendor_name": "PAE NL B.V.",
    "gross_amount": 1170.79,
    "vat_category": "Standard VAT",
    "vat_percentage": "21"
  }
]
```

**Required Fields**:
- `date`: Invoice date (YYYY-MM-DD)
- `type`: "Sales" or "Purchase"
- `net_amount`: Net amount (before VAT)
- `vat_amount`: VAT amount (can be null)
- `vat_category`: VAT category string
- `vat_percentage`: VAT percentage as string ("0", "21", "9")
- `file_name`: Invoice filename
- `description`: Invoice description
- `vendor_name`: Vendor/customer name
- `gross_amount`: Total amount including VAT

**Response** (200 OK):
```json
{
  "status": "success",
  "message": "Processed 2 invoices, skipped 0, errors: 0",
  "details": {
    "processed": 2,
    "skipped": 0,
    "errors": 0,
    "updated_years": ["2025"]
  },
  "total_invoices_received": 2
}
```

**Error Responses**:
- `400 Bad Request`: Missing X-User-ID header or invalid JSON array
- `500 Internal Server Error`: Server error during processing

---

### 2. Get Quarterly VAT Report

**Endpoint**: `GET /vat-report-quarterly`

**Description**: Generate VAT report for a specific quarter.

**Headers**:
```
X-User-ID: 369
```

**Query Parameters**:
- `year` (required): Year (e.g., "2025")
- `quarter` (required): Quarter (e.g., "Q1", "Q2", "Q3", "Q4")

**Example Request**:
```
GET /vat-report-quarterly?year=2025&quarter=Q3
Headers: X-User-ID: 369
```

**Response** (200 OK):
```json
{
  "report_type": "vat_tax_return",
  "period": "Q3 2025",
  "generated_at": "2025-11-20T23:23:36.988773",
  "company_info": {
    "company_name": "Your Company B.V.",
    "company_vat": "NL123456789B01",
    "reporting_period": "Q3 2025"
  },
  "categories": {
    "1a": {
      "name": "Sales Taxed at the Standard Rate (21%)",
      "transactions": [
        {
          "date": "2025-07-10",
          "invoice_no": "INV_016_SALE_STANDARD_21_Q3",
          "description": "Q3 Product Sales - Standard VAT",
          "net_amount": 3000.00,
          "vat_percentage": 21,
          "vat_amount": 630.00
        }
      ],
      "totals": {
        "net": 3000.00,
        "vat": 630.00
      }
    },
    "1b": {...},
    "1c": {...},
    "2a": {...},
    "3a": {...},
    "3b": {...},
    "4a": {...},
    "4b": {...},
    "4c": {...},
    "5b": {...}
  },
  "vat_calculation": {
    "vat_collected": 711.00,
    "vat_deductible": 315.00,
    "vat_payable": 396.00
  }
}
```

**Error Responses**:
- `400 Bad Request`: Missing year or quarter parameter
- `404 Not Found`: No data found for specified period

---

### 3. Get Monthly VAT Report

**Endpoint**: `GET /vat-report-monthly`

**Description**: Generate VAT report for a specific month.

**Headers**:
```
X-User-ID: 369
```

**Query Parameters**:
- `year` (required): Year (e.g., "2025")
- `month` (required): Month number (1-12)

**Example Request**:
```
GET /vat-report-monthly?year=2025&month=9
Headers: X-User-ID: 369
```

**Response**: Same structure as quarterly report, filtered by month.

---

### 4. Get Yearly VAT Report

**Endpoint**: `GET /vat-report-yearly`

**Description**: Generate VAT report for an entire year with quarterly breakdown.

**Headers**:
```
X-User-ID: 369
```

**Query Parameters**:
- `year` (required): Year (e.g., "2025")

**Example Request**:
```
GET /vat-report-yearly?year=2025
Headers: X-User-ID: 369
```

**Response** (200 OK):
```json
{
  "report_type": "vat_tax_return",
  "period": "2025",
  "generated_at": "2025-11-20T23:23:36.988773",
  "company_info": {
    "company_name": "Your Company B.V.",
    "company_vat": "NL123456789B01",
    "reporting_period": "2025 (January - December 2025)"
  },
  "quarterly_breakdown": {
    "Q1": {
      "period": "Q1 2025 (Jan-Mar)",
      "vat_collected": 255.00,
      "vat_deductible": 378.00,
      "vat_payable": -123.00
    },
    "Q2": {
      "period": "Q2 2025 (Apr-Jun)",
      "vat_collected": 592.50,
      "vat_deductible": 462.00,
      "vat_payable": 130.50
    },
    "Q3": {
      "period": "Q3 2025 (Jul-Sep)",
      "vat_collected": 711.00,
      "vat_deductible": 315.00,
      "vat_payable": 396.00
    },
    "Q4": {
      "period": "Q4 2025 (Oct-Dec)",
      "vat_collected": 840.00,
      "vat_deductible": 420.00,
      "vat_payable": 420.00
    }
  },
  "categories": {
    "1a": {...},
    "1b": {...},
    ...
  },
  "vat_calculation": {
    "vat_collected": 2398.50,
    "vat_deductible": 1575.00,
    "vat_payable": 823.50
  }
}
```

---

### 5. Set Company Details

**Endpoint**: `POST /company-details`

**Description**: Store company information for VAT reports.

**Headers**:
```
X-User-ID: 369
Content-Type: application/json
```

**Request Body**:
```json
{
  "company_name": "Your Company B.V.",
  "company_vat": "NL123456789B01"
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "message": "Company details updated",
  "company_name": "Your Company B.V.",
  "company_vat": "NL123456789B01"
}
```

---

### 6. Get Company Details

**Endpoint**: `GET /company-details`

**Description**: Retrieve stored company information.

**Headers**:
```
X-User-ID: 369
```

**Response** (200 OK):
```json
{
  "company_name": "Your Company B.V.",
  "company_vat": "NL123456789B01",
  "updated_at": "2025-11-20T23:23:36.988773"
}
```

---

### 7. Clear User Data

**Endpoint**: `DELETE /clear-user-data`

**Description**: Clear all stored data for a user (in-memory storage only).

**Headers**:
```
X-User-ID: 369
```

**Response** (200 OK):
```json
{
  "status": "success",
  "message": "All data cleared for user 369",
  "cleared": {
    "vat_data": true,
    "company_details": true,
    "pdf_count": true
  }
}
```

---

### 8. Health Check

**Endpoint**: `GET /health`

**Description**: Check if the API is running.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "message": "VAT Analysis API is running"
}
```

---

## Input/Output Formats

### Input Format (Invoice Data)

Each invoice in the array must have:

```json
{
  "date": "2025-09-25",              // Required: YYYY-MM-DD
  "type": "Purchase",                // Required: "Sales" or "Purchase"
  "currency": "EUR",                 // Optional: Currency code
  "file_name": "Invoice_26411.pdf",  // Required: Unique filename
  "net_amount": 4357.46,             // Required: Amount before VAT
  "vat_amount": null,                // Required: VAT amount (null for zero-rated)
  "description": "SEPTEMBER SALES",  // Required: Invoice description
  "vendor_name": "PAE Business Ltd", // Required: Vendor/customer name
  "gross_amount": 4357.45,           // Required: Total including VAT
  "vat_category": "Zero Rated",      // Required: VAT category string
  "vat_percentage": "0",             // Required: VAT percentage as string
  "customer_name": "...",            // Optional: Customer name (for sales)
  "vendor_vat_id": "...",            // Optional: Vendor VAT ID (for purchases)
  "customer_vat_id": "...",          // Optional: Customer VAT ID (for sales)
  "country": "NL",                    // Optional: Country code
  "invoice_number": "INV-001"         // Optional: Invoice number
}
```

### Output Format (VAT Report)

```json
{
  "report_type": "vat_tax_return",
  "period": "Q3 2025",
  "generated_at": "2025-11-20T23:23:36.988773",
  "company_info": {
    "company_name": "Your Company B.V.",
    "company_vat": "NL123456789B01",
    "reporting_period": "Q3 2025"
  },
  "categories": {
    "1a": {
      "name": "Sales Taxed at the Standard Rate (21%)",
      "transactions": [
        {
          "date": "2025-07-10",
          "invoice_no": "INV_016",
          "description": "Product Sales",
          "net_amount": 3000.00,
          "vat_percentage": 21,
          "vat_amount": 630.00
        }
      ],
      "totals": {
        "net": 3000.00,
        "vat": 630.00
      }
    }
  },
  "vat_calculation": {
    "vat_collected": 711.00,
    "vat_deductible": 315.00,
    "vat_payable": 396.00
  }
}
```

---

## VAT Category Mapping

The system uses **Multi-Field Logic** to map VAT categories. This is NOT a simple lookup - it checks three fields in priority order:

### Priority Order:
1. **Check Category**: What is the `vat_category` string?
2. **Check Type**: Is it "Sales" or "Purchase"?
3. **Check Rate** (Crucial): If it's "Standard VAT", what is the `vat_percentage`? (This resolves 21% vs 9% ambiguity)

### Mapping Logic Table

| Input Category | Transaction Type | VAT % | Internal Code | Description |
|---------------|------------------|-------|---------------|-------------|
| "Standard VAT" | Sales | 21 | **1a** | Sales Taxed at Standard Rate (21%) |
| "Standard VAT" | Sales | 9 | **1b** | Sales Taxed at Reduced Rate (9%) - Resolves ambiguity |
| "Standard VAT" | Purchase | Any | **5b** | Input VAT on Domestic Purchases |
| "Reduced Rate" | Sales | Any | **1b** | Alternative label for 9% sales |
| "Reduced Rate" | Purchase | Any | **5b** | Alternative label for domestic input VAT |
| "Zero Rated" | Sales | 0 | **1c** | General Exports / Zero Rated sales |
| "Zero Rated" | Purchase | 0 | **4a** | Assumes EU Goods Purchase |
| "EU Goods" | Sales | 0 | **3a** | Specific EU Supply |
| "EU Goods" | Purchase | 0 | **4a** | Same code as Zero Rated Purchase |
| "EU Services" | Sales | 0 | **3b** | EU Service Supply |
| "EU Services" | Purchase | 0 | **4b** | EU Service Purchase |
| "Reverse Charge" | Purchase | 0 | **2a** | Reverse-Charge Supplies |
| "Import" | Purchase | 0 | **4c** | Non-EU Import |

### Key Points:
- **"Standard VAT" + Sales**: The percentage (21% or 9%) determines whether it maps to **1a** or **1b**
- **"Standard VAT" + Purchase**: Always maps to **5b** regardless of percentage
- **Percentage Check is Critical**: This is what resolves the 21% vs 9% ambiguity for "Standard VAT" sales

### VAT Category Codes Explained

**Sales Categories (Output VAT):**
- **1a**: Standard rate sales (21% VAT)
- **1b**: Reduced rate sales (9% VAT)
- **1c**: Zero-rated sales (0% VAT - exports, EU supplies)
- **3a**: Goods supplied to EU countries (0% VAT)
- **3b**: Services supplied to EU countries (0% VAT)

**Purchase Categories (Input VAT):**
- **2a**: Reverse-charge supplies (0% VAT - you account for VAT)
- **4a**: Goods purchased from EU countries (0% VAT)
- **4b**: Services purchased from EU countries (0% VAT)
- **4c**: Goods imported from non-EU countries (0% VAT)
- **5b**: Domestic purchases with VAT (21% or 9% VAT)

---

## Usage Examples

### Example 1: Complete Workflow

#### Step 1: Set Company Details
```bash
curl -X POST "http://localhost:8000/company-details" \
  -H "X-User-ID: 369" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Your Company B.V.",
    "company_vat": "NL123456789B01"
  }'
```

#### Step 2: Process Invoices
```bash
curl -X POST "http://localhost:8000/process-invoices" \
  -H "X-User-ID: 369" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "date": "2025-09-25",
      "type": "Purchase",
      "net_amount": 4357.46,
      "vat_amount": null,
      "vat_category": "Zero Rated",
      "vat_percentage": "0",
      "file_name": "Invoice_26411.pdf",
      "description": "SEPTEMBER SALES",
      "vendor_name": "PAE Business Ltd",
      "gross_amount": 4357.45
    }
  ]'
```

#### Step 3: Generate Quarterly Report
```bash
curl -X GET "http://localhost:8000/vat-report-quarterly?year=2025&quarter=Q3" \
  -H "X-User-ID: 369"
```

#### Step 4: Generate Yearly Report
```bash
curl -X GET "http://localhost:8000/vat-report-yearly?year=2025" \
  -H "X-User-ID: 369"
```

### Example 2: Using Swagger UI

1. **Start the server**:
   ```bash
   python start_backend.py
   ```

2. **Open Swagger UI**:
   ```
   http://localhost:8000/docs
   ```

3. **Process Invoices**:
   - Find `POST /process-invoices`
   - Click "Try it out"
   - Set `X-User-ID: 369`
   - Paste your JSON array in the request body
   - Click "Execute"

4. **View Reports**:
   - Find `GET /vat-report-quarterly`
   - Click "Try it out"
   - Set `X-User-ID: 369`
   - Set `year: 2025`, `quarter: Q3`
   - Click "Execute"

### Example 3: PowerShell

```powershell
# Set headers
$headers = @{
    "X-User-ID" = "369"
    "Content-Type" = "application/json"
}

# Process invoices
$body = @'
[
  {
    "date": "2025-09-25",
    "type": "Purchase",
    "net_amount": 4357.46,
    "vat_amount": null,
    "vat_category": "Zero Rated",
    "vat_percentage": "0",
    "file_name": "Invoice_26411.pdf",
    "description": "SEPTEMBER SALES",
    "vendor_name": "PAE Business Ltd",
    "gross_amount": 4357.45
  }
]
'@

Invoke-RestMethod -Uri "http://localhost:8000/process-invoices" `
  -Method Post -Headers $headers -Body $body

# Get quarterly report
$report = Invoke-RestMethod -Uri "http://localhost:8000/vat-report-quarterly?year=2025&quarter=Q3" `
  -Method Get -Headers @{"X-User-ID" = "369"}

$report | ConvertTo-Json -Depth 10
```

---

## Error Handling

### Common Errors

#### 1. Missing X-User-ID Header
**Error**: `400 Bad Request`
**Message**: "Missing X-User-ID header"
**Solution**: Include `X-User-ID` header in all requests

#### 2. Invalid JSON Format
**Error**: `422 Unprocessable Entity`
**Message**: "Expected a JSON array of invoices"
**Solution**: Ensure request body is a valid JSON array

#### 3. Missing Required Fields
**Error**: `500 Internal Server Error`
**Message**: Error during processing
**Solution**: Ensure all required fields are present in each invoice

#### 4. No Data Found
**Error**: `404 Not Found`
**Message**: "No data found for specified period"
**Solution**: Process invoices first, or check year/quarter/month parameters

#### 5. Duplicate Invoice
**Response**: `200 OK` but invoice is skipped
**Message**: "Processed X invoices, skipped Y"
**Solution**: Use different `file_name` or clear data first

---

## Data Storage

### In-Memory Storage

The system uses Python dictionaries for storage:

```python
# VAT Data Storage
user_vat_data = {
    "user_id": {
        "2025": {
            "invoices": [
                {
                    "invoice_no": "...",
                    "date": "...",
                    "transactions": [...],
                    "subtotal": 1000.00,
                    "vat_amount": 210.00,
                    "transaction_type": "sale",
                    "vat_category": "1a",
                    "source_file": "..."
                }
            ]
        }
    }
}

# Company Details Storage
user_company_details = {
    "user_id": {
        "company_name": "...",
        "company_vat": "...",
        "updated_at": "..."
    }
}
```

### Important Notes

- **Data Persistence**: Data is stored in memory and persists while the server is running
- **Data Loss**: Data is lost when the server restarts
- **Multi-User**: Each user's data is isolated by `user_id`
- **Year Organization**: Invoices are organized by year automatically

### Future Storage Options

The system can be extended to use:
- **Database**: PostgreSQL, MySQL, MongoDB
- **Cloud Storage**: AWS S3, Azure Blob Storage
- **File System**: JSON files, CSV files

---

## Report Generation Logic

### Quarterly Report

1. **Retrieve Data**: Get all invoices for the user and year
2. **Filter by Quarter**: 
   - Q1: January, February, March
   - Q2: April, May, June
   - Q3: July, August, September
   - Q4: October, November, December
3. **Categorize**: Group transactions by VAT category code
4. **Calculate Totals**: Sum net amounts and VAT amounts per category
5. **Calculate VAT Payable**: VAT Collected - VAT Deductible

### Monthly Report

Same as quarterly, but filters by specific month (1-12).

### Yearly Report

1. **Generate Quarterly Breakdown**: Calculate totals for each quarter
2. **Aggregate All Data**: Sum all quarters
3. **Categorize**: Group all transactions by VAT category
4. **Calculate Totals**: Sum net amounts and VAT amounts per category
5. **Calculate VAT Payable**: Total VAT Collected - Total VAT Deductible

### VAT Calculation

```python
# VAT Collected (Output VAT)
vat_collected = sum(
    transaction.vat_amount 
    for invoice in sales_invoices 
    for transaction in invoice.transactions
    if invoice.transaction_type == "sale"
)

# VAT Deductible (Input VAT)
vat_deductible = sum(
    transaction.vat_amount 
    for invoice in purchase_invoices 
    for transaction in invoice.transactions
    if invoice.transaction_type == "purchase"
)

# VAT Payable
vat_payable = vat_collected - vat_deductible
```

---

## Best Practices

### 1. Invoice Data Quality
- ✅ Ensure all required fields are present
- ✅ Use consistent date format (YYYY-MM-DD)
- ✅ Use unique `file_name` to avoid duplicates
- ✅ Provide accurate VAT amounts
- ✅ Use correct VAT category strings

### 2. API Usage
- ✅ Always include `X-User-ID` header
- ✅ Use appropriate HTTP methods (GET, POST, DELETE)
- ✅ Handle errors gracefully
- ✅ Validate JSON before sending

### 3. Report Generation
- ✅ Set company details before generating reports
- ✅ Process all invoices before generating reports
- ✅ Use correct year/quarter/month parameters
- ✅ Clear data if re-processing invoices

### 4. Testing
- ✅ Test with sample data first
- ✅ Verify VAT calculations manually
- ✅ Check all VAT categories are mapped correctly
- ✅ Test edge cases (zero amounts, null values)

---

## Troubleshooting

### Issue: All invoices skipped as duplicates
**Cause**: Invoices already processed and stored in memory
**Solution**: Use `DELETE /clear-user-data` to clear data, then re-process

### Issue: Reports show zero amounts
**Cause**: Transaction amounts not stored correctly
**Solution**: Check input data has correct `net_amount` and `vat_amount` values

### Issue: Wrong VAT category mapping
**Cause**: Incorrect `vat_category` string or `type` field
**Solution**: Use correct category strings: "Standard VAT", "Zero Rated", "Reverse Charge", etc.

### Issue: Server not responding
**Cause**: Server not running or crashed
**Solution**: Restart server with `python start_backend.py`

---

## API Reference Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/process-invoices` | Store analyzed invoice data |
| GET | `/vat-report-quarterly` | Get quarterly VAT report |
| GET | `/vat-report-monthly` | Get monthly VAT report |
| GET | `/vat-report-yearly` | Get yearly VAT report |
| POST | `/company-details` | Set company information |
| GET | `/company-details` | Get company information |
| DELETE | `/clear-user-data` | Clear all user data |
| GET | `/health` | Health check |

---

## Conclusion

This VAT Analysis System provides a simple, efficient way to process analyzed invoice data and generate VAT reports for Dutch tax compliance. The system is designed to be:

- **Simple**: Accepts pre-analyzed data, no complex processing
- **Fast**: In-memory storage for quick access
- **Accurate**: Automatic VAT category mapping and calculations
- **Flexible**: Supports quarterly, monthly, and yearly reports

For questions or issues, refer to the troubleshooting section or check the Swagger UI documentation at `http://localhost:8000/docs`.

