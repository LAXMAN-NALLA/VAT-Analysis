# New JSON Format Processing Guide

## Overview

The system has been updated to accept pre-processed invoice data in JSON format instead of processing PDFs directly. This allows for integration with external invoice processing systems.

## New Endpoint

### POST `/process-invoices`

**Description**: Accepts invoice data in the new JSON format and processes it into the VAT analysis system.

**Headers Required**:
- `X-User-ID`: User identifier

**Request Body**: JSON object with the following structure:

```json
{
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
        "Description": "Invoice description",
        "Nett Amount": 440,
        "Vendor Name": "Vendor Name",
        "Gross Amount": 440,
        "VAT Category": "Reverse Charge",
        "Customer Name": "Customer Name",
        "Invoice Number": "INV-001",
        "VAT Amount (EUR)": 0,
        "Nett Amount (EUR)": 440,
        "Gross Amount (EUR)": 440,
        "Full_Extraction_Data": {
          "vendor_vat_id": "NL123456789B01",
          "customer_vat_id": "NL987654321B02"
        }
      }
    }
  ]
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Processed 5 invoices, skipped 2, errors: 0",
  "details": {
    "processed": 5,
    "skipped": 2,
    "errors": 0,
    "updated_years": ["2025"]
  }
}
```

## VAT Category Mapping

The system automatically maps VAT Category strings to standard category codes:

| Input VAT Category | Transaction Type | Mapped Category | Description |
|-------------------|------------------|-----------------|-------------|
| Reverse Charge | Purchase | 2a | Reverse-charge supplies |
| Zero Rated | Sale | 1c | Sales with 0% VAT |
| Zero Rated | Purchase | 4a | Goods from EU |
| Standard Rate | Sale (21%) | 1a | Standard rate sales |
| Standard Rate | Sale (9%) | 1b | Reduced rate sales |
| Standard Rate | Purchase | 5b | Input VAT on purchases |
| EU Goods | Sale | 3a | Goods supplied to EU |
| EU Services | Sale | 3b | Services supplied to EU |
| EU Goods | Purchase | 4a | Goods purchased from EU |
| EU Services | Purchase | 4b | Services purchased from EU |
| Import | Purchase | 4c | Imports from non-EU |

## VAT Report Endpoints

### Monthly Report
**GET** `/vat-report-monthly?year=2025&month=Jul`

Returns VAT return for a specific month with:
- Company information
- Transactions by VAT category
- VAT calculation (collected, deductible, payable)

### Quarterly Report
**GET** `/vat-report-quarterly?year=2025&quarter=Q3`

Returns VAT return for a specific quarter with:
- Company information
- Transactions by VAT category
- VAT calculation (collected, deductible, payable)

### Yearly Report
**GET** `/vat-report-yearly?year=2025`

Returns VAT return for a full year with:
- Company information
- Quarterly breakdown
- Transactions by VAT category
- VAT calculation (collected, deductible, payable)

## Report Structure

All reports follow this structure:

```json
{
  "report_type": "vat_tax_return",
  "period": "Q3 2025",
  "generated_at": "2025-10-22T10:30:00",
  "company_info": {
    "company_name": "Company Name",
    "company_vat": "NL123456789B01",
    "reporting_period": "Q3 2025"
  },
  "categories": {
    "1a": {
      "name": "Sales Taxed at the Standard Rate (21%)",
      "transactions": [
        {
          "date": "2025-07-15",
          "invoice_no": "INV-001",
          "description": "Product description",
          "net_amount": 1000.0,
          "vat_percentage": 21.0,
          "vat_amount": 210.0
        }
      ],
      "totals": {
        "net": 1000.0,
        "vat": 210.0
      }
    }
  },
  "vat_calculation": {
    "vat_collected": 210.0,
    "vat_deductible": 50.0,
    "vat_payable": 160.0
  },
  "quarterly_breakdown": {
    "Q1": {
      "period": "Q1 2025 (Jan-Mar)",
      "vat_collected": 500.0,
      "vat_deductible": 100.0,
      "vat_payable": 400.0
    }
  }
}
```

## Usage Example

### 1. Process Invoices

```python
import requests

url = "http://localhost:8000/process-invoices"
headers = {
    "X-User-ID": "user123",
    "Content-Type": "application/json"
}

data = {
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
                "Vendor Name": "Vendor",
                "Gross Amount": 440,
                "VAT Category": "Reverse Charge",
                "Customer Name": "Customer",
                "Invoice Number": "INV-001",
                "VAT Amount (EUR)": 0,
                "Nett Amount (EUR)": 440,
                "Gross Amount (EUR)": 440
            }
        }
    ]
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

### 2. Get Quarterly Report

```python
url = "http://localhost:8000/vat-report-quarterly"
headers = {"X-User-ID": "user123"}
params = {"year": "2025", "quarter": "Q3"}

response = requests.get(url, headers=headers, params=params)
report = response.json()
print(f"VAT Payable: €{report['vat_calculation']['vat_payable']}")
```

## Key Features

1. **Automatic Category Mapping**: VAT categories are automatically mapped from string format to standard codes
2. **EUR Conversion**: System prefers EUR converted amounts when available
3. **Duplicate Detection**: Prevents processing the same invoice twice
4. **Year-based Organization**: Data is automatically organized by year
5. **Clean Reports**: Reports contain only essential information for VAT returns

## Transaction Type Detection

The system uses the `Type` field from `register_entry`:
- `"Purchase"` or `"Purchases"` → `transaction_type: "purchase"`
- `"Sales"` or `"Sale"` → `transaction_type: "sale"`
- `"Unclassified"` → Inferred from VAT percentage and category

## Notes

- The system automatically extracts the year from the invoice date
- Invoices are stored in year-based JSON files: `VATanalysis_{year}.json`
- Duplicate invoices (by invoice number) are skipped
- Failed entries are counted but not processed
- All amounts are normalized and rounded to 2 decimal places

