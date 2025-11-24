# New Simple Approach - Direct JSON Array Input

## Overview

The system now accepts **pre-analyzed invoice data** directly as a simple JSON array. No processing or transformation needed!

## Input Format

Send a JSON array of analyzed invoices:

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

## Required Fields

- `date`: Invoice date (format: "YYYY-MM-DD")
- `type`: "Sales" or "Purchase"
- `net_amount`: Net amount (before VAT)
- `vat_amount`: VAT amount (can be null for zero-rated)
- `vat_category`: VAT category string (e.g., "Zero Rated", "Standard VAT", "Reverse Charge")
- `vat_percentage`: VAT percentage as string (e.g., "0", "21", "9")
- `file_name`: Invoice filename
- `description`: Invoice description
- `vendor_name`: Vendor/customer name
- `gross_amount`: Total amount including VAT

## Optional Fields

- `invoice_number`: Invoice number (if not provided, uses filename)
- `customer_name`: Customer name (for sales)
- `vendor_vat_id`: Vendor VAT ID (for purchases)
- `customer_vat_id`: Customer VAT ID (for sales)
- `country`: Country code

## API Endpoint

### POST `/process-invoices`

**Headers:**
```
X-User-ID: your_user_id
```

**Request Body:**
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
    "description": "SEPTEMBER SALES",
    "vendor_name": "PAE Business Ltd",
    "gross_amount": 4357.45
  }
]
```

**Response:**
```json
{
  "status": "success",
  "message": "Processed 1 invoices, skipped 0, errors: 0",
  "details": {
    "processed": 1,
    "skipped": 0,
    "errors": 0,
    "updated_years": ["2025"]
  },
  "total_invoices_received": 1
}
```

## VAT Category Mapping

The system automatically maps VAT categories to internal codes:

| Input Category | Transaction Type | Internal Code | Description |
|---------------|------------------|---------------|-------------|
| "Zero Rated" | Sale | 1c | Sales Taxed at 0% (EU and Export) |
| "Zero Rated" | Purchase | 4a | Purchases of Goods from EU Countries |
| "Standard VAT" | Sale (21%) | 1a | Sales Taxed at Standard Rate (21%) |
| "Standard VAT" | Sale (9%) | 1b | Sales Taxed at Reduced Rate (9%) |
| "Standard VAT" | Purchase | 5b | Input VAT on Domestic Purchases |
| "Reverse Charge" | Purchase | 2a | Reverse-Charge Supplies |
| "Reduced" | Sale | 1b | Sales Taxed at Reduced Rate (9%) |
| "EU" (goods) | Sale | 3a | Supplies of Goods to EU Countries |
| "EU" (services) | Sale | 3b | Supplies of Services to EU Countries |
| "Import" | Purchase | 4c | Purchases of Goods from Non-EU Countries |

## Report Generation

After processing invoices, generate reports:

### Quarterly Report
```
GET /vat-report-quarterly?year=2025&quarter=Q3
Headers: X-User-ID: your_user_id
```

### Monthly Report
```
GET /vat-report-monthly?year=2025&month=9
Headers: X-User-ID: your_user_id
```

### Yearly Report
```
GET /vat-report-yearly?year=2025
Headers: X-User-ID: your_user_id
```

## Example: Complete Workflow

### 1. Process Invoices
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

### 2. Generate Quarterly Report
```bash
curl -X GET "http://localhost:8000/vat-report-quarterly?year=2025&quarter=Q3" \
  -H "X-User-ID: 369"
```

## Benefits

✅ **No Processing Needed** - Data is already analyzed  
✅ **Simple Format** - Just a JSON array  
✅ **Fast** - Direct storage, no transformation  
✅ **Flexible** - Works with any analyzed invoice data  

## Notes

- Duplicate invoices are automatically skipped (checked by `file_name`)
- Data is stored in-memory (cleared on server restart)
- Use `/clear-user-data` to reset and re-process invoices
- Reports are automatically categorized by VAT code

