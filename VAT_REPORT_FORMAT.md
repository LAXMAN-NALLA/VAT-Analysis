# VAT Report Format Documentation

## Overview

All VAT reports (Monthly, Quarterly, Yearly) follow the same standardized format. The system accepts invoice data in the JSON format you provided and generates VAT reports that match the structure shown below.

## Input Format

The system accepts invoice data in this format:

```json
{
  "status": "success",
  "results": [
    {
      "status": "success",
      "file_name": "invoice.pdf",
      "register_entry": {
        "Date": "2024-09-04",
        "Type": "Sales",
        "VAT %": 0,
        "Currency": "EUR",
        "VAT Amount": 0,
        "Description": "Product description",
        "Nett Amount": 7390.5,
        "Vendor Name": "Company Name",
        "Gross Amount": 7390.5,
        "VAT Category": "Zero Rated",
        "Customer Name": "Customer Name",
        "Invoice Number": "INV-001",
        "VAT Amount (EUR)": 0,
        "Nett Amount (EUR)": 7390.5,
        "FX Rate (ccy->EUR)": "1.0000",
        "Gross Amount (EUR)": 7390.5,
        "Full_Extraction_Data": {
          "line_items": [...],
          "vat_breakdown": [...]
        }
      }
    }
  ]
}
```

## Output Format

All VAT reports return data in this standardized format:

```json
{
  "report_type": "vat_tax_return",
  "period": "Jul 2024",
  "generated_at": "2024-10-22T10:30:00",
  "company_info": {
    "company_name": "Dutch Food Solutions B.V.",
    "company_vat": "NL858674257B01",
    "reporting_period": "Jul 2024"
  },
  "categories": {
    "1a": {
      "name": "Sales Taxed at the Standard Rate (21%)",
      "transactions": [
        {
          "date": "2024-07-15",
          "invoice_no": "INV-001",
          "description": "Service description",
          "net_amount": 1000.0,
          "vat_percentage": 21.0,
          "vat_amount": 210.0
        }
      ],
      "totals": {
        "net": 1000.0,
        "vat": 210.0
      }
    },
    "1b": {
      "name": "Sales Taxed at the Reduced Rate (9%)",
      "transactions": [],
      "totals": {
        "net": 0.0,
        "vat": 0.0
      }
    },
    "1c": {
      "name": "Sales Taxed at 0% (EU and Export)",
      "transactions": [],
      "totals": {
        "net": 0.0,
        "vat": 0.0
      }
    },
    "2a": {
      "name": "Reverse-Charge Supplies",
      "transactions": [],
      "totals": {
        "net": 0.0,
        "vat": 0.0
      }
    },
    "3a": {
      "name": "Supplies of Goods to EU Countries",
      "transactions": [],
      "totals": {
        "net": 0.0,
        "vat": 0.0
      }
    },
    "3b": {
      "name": "Supplies of Services to EU Countries",
      "transactions": [],
      "totals": {
        "net": 0.0,
        "vat": 0.0
      }
    },
    "4a": {
      "name": "Purchases of Goods from EU Countries",
      "transactions": [],
      "totals": {
        "net": 0.0,
        "vat": 0.0
      }
    },
    "4b": {
      "name": "Purchases of Services from EU Countries",
      "transactions": [],
      "totals": {
        "net": 0.0,
        "vat": 0.0
      }
    },
    "4c": {
      "name": "Purchases of Goods from Non-EU Countries (Imports)",
      "transactions": [],
      "totals": {
        "net": 0.0,
        "vat": 0.0
      }
    },
    "5b": {
      "name": "Input VAT on Domestic Purchases",
      "transactions": [],
      "totals": {
        "net": 0.0,
        "vat": 0.0
      }
    }
  },
  "vat_calculation": {
    "vat_collected": 2100.0,
    "vat_deductible": 500.0,
    "vat_payable": 1600.0
  }
}
```

## Report Endpoints

### 1. Monthly Report
**Endpoint**: `GET /vat-report-monthly`

**Query Parameters**:
- `year`: Year (e.g., "2024")
- `month`: Month abbreviation (e.g., "Jul", "Jan", "Dec")

**Example**:
```bash
GET /vat-report-monthly?year=2024&month=Jul
```

**Response**: Standard format with `period: "Jul 2024"`

---

### 2. Quarterly Report
**Endpoint**: `GET /vat-report-quarterly`

**Query Parameters**:
- `year`: Year (e.g., "2024")
- `quarter`: Quarter (e.g., "Q1", "Q2", "Q3", "Q4")

**Example**:
```bash
GET /vat-report-quarterly?year=2024&quarter=Q3
```

**Response**: Standard format with `period: "Q3 2024"`

---

### 3. Yearly Report
**Endpoint**: `GET /vat-report-yearly`

**Query Parameters**:
- `year`: Year (e.g., "2024")

**Example**:
```bash
GET /vat-report-yearly?year=2024
```

**Response**: Standard format with additional `quarterly_breakdown` field:

```json
{
  "report_type": "vat_tax_return",
  "period": "2024",
  "generated_at": "2024-10-22T10:30:00",
  "company_info": {
    "company_name": "Dutch Food Solutions B.V.",
    "company_vat": "NL858674257B01",
    "reporting_period": "2024 (January - December 2024)"
  },
  "quarterly_breakdown": {
    "Q1": {
      "period": "Q1 2024 (Jan-Mar)",
      "vat_collected": 5000.0,
      "vat_deductible": 1200.0,
      "vat_payable": 3800.0
    },
    "Q2": {
      "period": "Q2 2024 (Apr-Jun)",
      "vat_collected": 3500.0,
      "vat_deductible": 800.0,
      "vat_payable": 2700.0
    },
    "Q3": {
      "period": "Q3 2024 (Jul-Sep)",
      "vat_collected": 4000.0,
      "vat_deductible": 1000.0,
      "vat_payable": 3000.0
    },
    "Q4": {
      "period": "Q4 2024 (Oct-Dec)",
      "vat_collected": 4500.0,
      "vat_deductible": 1100.0,
      "vat_payable": 3400.0
    }
  },
  "categories": {
    // ... same as monthly/quarterly
  },
  "vat_calculation": {
    "vat_collected": 17000.0,
    "vat_deductible": 4100.0,
    "vat_payable": 12900.0
  }
}
```

---

## VAT Categories

All reports include all 10 VAT categories, even if they have no transactions:

| Code | Category Name | Description |
|------|---------------|-------------|
| **1a** | Sales Taxed at the Standard Rate (21%) | Domestic sales at 21% VAT |
| **1b** | Sales Taxed at the Reduced Rate (9%) | Domestic sales at 9% VAT |
| **1c** | Sales Taxed at 0% (EU and Export) | Zero-rated sales (EU/Export) |
| **2a** | Reverse-Charge Supplies | Reverse charge purchases |
| **3a** | Supplies of Goods to EU Countries | Goods sold to EU customers |
| **3b** | Supplies of Services to EU Countries | Services sold to EU customers |
| **4a** | Purchases of Goods from EU Countries | Goods bought from EU suppliers |
| **4b** | Purchases of Services from EU Countries | Services bought from EU suppliers |
| **4c** | Purchases of Goods from Non-EU Countries (Imports) | Imports from non-EU countries |
| **5b** | Input VAT on Domestic Purchases | Domestic purchases with VAT |

---

## VAT Calculation Logic

### VAT Amount Distribution

When an invoice has multiple line items, the VAT amount is distributed proportionally:

1. **If invoice has total VAT amount**: VAT is distributed proportionally based on net amounts
2. **If VAT percentage is provided**: VAT is calculated per transaction using the percentage
3. **If no VAT**: VAT amount is set to 0.0

### VAT Collected vs VAT Deductible

- **VAT Collected**: Sum of VAT from all sales transactions (Type: "Sales")
- **VAT Deductible**: Sum of VAT from all purchase transactions (Type: "Purchase")
- **VAT Payable**: VAT Collected - VAT Deductible

---

## Complete Workflow Example

### Step 1: Process Invoices
```bash
POST /process-invoices
Headers: X-User-ID: user123
Body: {
  "status": "success",
  "results": [
    {
      "status": "success",
      "file_name": "invoice.pdf",
      "register_entry": {
        "Date": "2024-07-15",
        "Type": "Sales",
        "VAT %": 21,
        "VAT Amount": 210,
        "Nett Amount": 1000,
        "VAT Category": "Standard Rate (21%)",
        "Invoice Number": "INV-001",
        ...
      }
    }
  ]
}
```

### Step 2: Get Monthly Report
```bash
GET /vat-report-monthly?year=2024&month=Jul
Headers: X-User-ID: user123
```

### Step 3: Get Quarterly Report
```bash
GET /vat-report-quarterly?year=2024&quarter=Q3
Headers: X-User-ID: user123
```

### Step 4: Get Yearly Report
```bash
GET /vat-report-yearly?year=2024
Headers: X-User-ID: user123
```

---

## Notes

1. **All amounts are rounded to 2 decimal places**
2. **All categories are always included**, even if empty
3. **Period format**:
   - Monthly: "Jul 2024"
   - Quarterly: "Q3 2024"
   - Yearly: "2024"
4. **Company info** is retrieved from stored company details (set via `/company-details`)
5. **Date format**: ISO 8601 format (e.g., "2024-10-22T10:30:00")
6. **Transaction dates**: Use the invoice date from the input data

---

## Testing

Use the provided `sample_10_invoices.json` file to test all report formats:

```bash
# 1. Process invoices
curl -X POST "http://localhost:8000/process-invoices" \
  -H "X-User-ID: test_user" \
  -H "Content-Type: application/json" \
  -d @sample_10_invoices.json

# 2. Get monthly report
curl -X GET "http://localhost:8000/vat-report-monthly?year=2024&month=Sep" \
  -H "X-User-ID: test_user"

# 3. Get quarterly report
curl -X GET "http://localhost:8000/vat-report-quarterly?year=2024&quarter=Q3" \
  -H "X-User-ID: test_user"

# 4. Get yearly report
curl -X GET "http://localhost:8000/vat-report-yearly?year=2024" \
  -H "X-User-ID: test_user"
```

