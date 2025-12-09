# API Endpoints - Sample Inputs and Outputs

This document provides comprehensive sample inputs and outputs for all API endpoints in the VAT Analysis System.

**Base URL:** `http://localhost:8000` (or your deployed URL)

**Common Header:** Most endpoints require `X-User-ID` header:
```
X-User-ID: 369
```

---

## Table of Contents

1. [Health Check](#1-health-check)
2. [User Info](#2-user-info)
3. [Upload PDFs](#3-upload-pdfs)
4. [Trigger VAT Analysis](#4-trigger-vat-analysis)
5. [Process Invoices](#5-process-invoices)
6. [Company Details](#6-company-details)
7. [VAT Summary](#7-vat-summary)
8. [Transactions](#8-transactions)
9. [VAT Quarterly](#9-vat-quarterly)
10. [VAT Payable](#10-vat-payable)
11. [Calculate VAT](#11-calculate-vat)
12. [Validate VAT](#12-validate-vat)
13. [VAT Report - Quarterly](#13-vat-report---quarterly)
14. [VAT Report - Monthly](#14-vat-report---monthly)
15. [VAT Report - Yearly](#15-vat-report---yearly)
16. [Dreport (Dutch Tax Format)](#16-dreport-dutch-tax-format)
17. [Clear User Data](#17-clear-user-data)

---

## 1. Health Check

### Endpoint
```
GET /health
```

### Request
**Headers:** None required

**Body:** None

### Sample Response (200 OK)
```json
{
  "status": "healthy",
  "message": "VAT Analysis API is running"
}
```

---

## 2. User Info

### Endpoint
```
GET /user-info
```

### Request
**Headers:**
```
X-User-ID: 369
```

**Body:** None

### Sample Response (200 OK)
```json
{
  "user_id": "369",
  "pdf_count": 5,
  "processed_years": ["2024", "2025"],
  "max_pdfs": 20
}
```

---

## 3. Upload PDFs

### Endpoint
```
POST /upload
```

### Request
**Headers:**
```
X-User-ID: 369
Content-Type: multipart/form-data
```

**Body:** Form data with files
- `files`: Array of PDF files (max 20 total)

### Sample Response (200 OK)
```json
{
  "message": "✅ Uploaded 2 file(s) successfully.",
  "files_uploaded": [
    "invoice_001.pdf",
    "invoice_002.pdf"
  ]
}
```

### Error Response (400 Bad Request)
```json
{
  "detail": "❌ Uploading 5 files would exceed your limit of 20 PDFs. You currently have 18 PDFs."
}
```

---

## 4. Trigger VAT Analysis

### Endpoint
```
POST /trigger
```

### Request
**Headers:**
```
X-User-ID: 369
X-Company-Name: Your Company B.V. (optional)
X-Company-VAT: NL123456789B01 (optional)
```

**Body:** None

### Sample Response (200 OK)
```json
{
  "message": "VAT analysis processing completed"
}
```

---

## 5. Process Invoices

### Endpoint
```
POST /process-invoices
```

### Request
**Headers:**
```
X-User-ID: 369
Content-Type: application/json
```

**Body:**
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
    "vat_percentage": "0",
    "VAT Category (NL) Code": "4a",
    "VAT Category (NL) Description": "Purchases of goods from EU countries"
  },
  {
    "date": "2025-09-17",
    "type": "Sales",
    "currency": "EUR",
    "file_name": "24700492.pdf",
    "net_amount": 967.6,
    "vat_amount": 203.19,
    "description": "Premier Subscription Package",
    "customer_name": "PAE NL B.V.",
    "gross_amount": 1170.79,
    "vat_percentage": "21",
    "VAT Category (NL) Code": "1a",
    "VAT Category (NL) Description": "Sales taxed at the standard rate (21%)"
  },
  {
    "date": "2025-09-20",
    "type": "Sales",
    "currency": "EUR",
    "file_name": "credit_note_001.pdf",
    "net_amount": -500.00,
    "vat_amount": -105.00,
    "description": "Credit Note - Return",
    "customer_name": "Customer ABC",
    "gross_amount": -605.00,
    "vat_percentage": "21",
    "invoice_number": "CN-001",
    "VAT Category (NL) Code": "1a",
    "VAT Category (NL) Description": "Sales taxed at the standard rate (21%)"
  },
  {
    "date": "2025-09-15",
    "type": "Sales",
    "currency": "EUR",
    "file_name": "invoice_eu_service.pdf",
    "net_amount": 5000.00,
    "vat_amount": 0.00,
    "description": "IT Consulting Services",
    "customer_name": "German Tech Solutions GmbH",
    "gross_amount": 5000.00,
    "vat_percentage": "0",
    "VAT Category (NL) Code": "3b",
    "VAT Category (NL) Description": "Supplies of services to EU countries"
  }
]
```

**Note:** The new approach uses `VAT Category (NL) Code` and `VAT Category (NL) Description` fields directly. The system no longer needs to classify VAT categories - it uses the provided codes.

**Backward Compatibility:** If `VAT Category (NL) Code` is not provided, the system will attempt to map from the old `vat_category` field for backward compatibility.

### Sample Response (200 OK)
```json
{
  "status": "success",
  "message": "Processed 3 invoices, skipped 0, errors: 0",
  "details": {
    "processed": 3,
    "skipped": 0,
    "errors": 0,
    "updated_years": ["2025"]
  },
  "total_invoices_received": 3
}
```

### Error Response (400 Bad Request)
```json
{
  "detail": "Expected a JSON array of invoices"
}
```

### Error Response (400 Bad Request - Missing Header)
```json
{
  "detail": "Missing X-User-ID header"
}
```

---

## 6. Company Details

### 6.1 Set Company Details

#### Endpoint
```
POST /company-details
```

#### Request
**Headers:**
```
X-User-ID: 369
X-Company-Name: Your Company B.V.
X-Company-VAT: NL123456789B01
```

**Body:** None

#### Sample Response (200 OK)
```json
{
  "message": "Company details updated successfully",
  "company_name": "Your Company B.V.",
  "company_vat": "NL123456789B01"
}
```

### 6.2 Get Company Details

#### Endpoint
```
GET /company-details
```

#### Request
**Headers:**
```
X-User-ID: 369
```

**Body:** None

#### Sample Response (200 OK)
```json
{
  "company_name": "Your Company B.V.",
  "company_vat": "NL123456789B01",
  "updated_at": "2025-11-20T23:23:36.988773Z"
}
```

#### Response (No Data Found)
```json
{
  "company_name": null,
  "company_vat": null,
  "updated_at": null,
  "message": "No company details found. Please set company details first."
}
```

---

## 7. VAT Summary

### Endpoint
```
GET /vat-summary?year=2025
```

### Request
**Headers:**
```
X-User-ID: 369
```

**Query Parameters:**
- `year` (optional): Year (defaults to current year)

**Body:** None

### Sample Response (200 OK)
```json
{
  "monthly_data": [
    {
      "month": "Jan",
      "Domestic VAT": 2100.00,
      "Input VAT": 1050.00
    },
    {
      "month": "Feb",
      "Domestic VAT": 450.00,
      "Input VAT": 0.00
    },
    {
      "month": "Sep",
      "Domestic VAT": 203.19,
      "Input VAT": 0.00
    }
  ],
  "quarterly_data": [
    {
      "quarter": "Q1",
      "quarter_name": "Quarter 1 (Jan-Mar)",
      "Domestic VAT": 2550.00,
      "Input VAT": 1050.00
    },
    {
      "quarter": "Q3",
      "quarter_name": "Quarter 3 (Jul-Sep)",
      "Domestic VAT": 203.19,
      "Input VAT": 0.00
    }
  ],
  "total_vat": 3603.19,
  "total_amount": 79750.00,
  "transactions": [
    {
      "invoice_no": "24700492",
      "date": "2025-09-17",
      "description": "Premier Subscription Package",
      "amount_pre_vat": 967.6,
      "vat_percentage": "21%",
      "vat_category": "1a",
      "country": "N/A",
      "transaction_type": "sale"
    }
  ]
}
```

---

## 8. Transactions

### Endpoint
```
GET /transactions?year=2025
```

### Request
**Headers:**
```
X-User-ID: 369
```

**Query Parameters:**
- `year` (optional): Year (defaults to current year)

**Body:** None

### Sample Response (200 OK)
```json
{
  "transactions": [
    {
      "invoice_no": "24700492",
      "date": "2025-09-17",
      "description": "Premier Subscription Package",
      "amount_pre_vat": 967.6,
      "vat_percentage": "21%",
      "vat_category": "1a",
      "country": "N/A",
      "transaction_type": "sale"
    },
    {
      "invoice_no": "Invoice_26411",
      "date": "2025-09-25",
      "description": "SEPTEMBER SALES",
      "amount_pre_vat": 4357.46,
      "vat_percentage": "0%",
      "vat_category": "4a",
      "country": "",
      "transaction_type": "purchase"
    }
  ]
}
```

---

## 9. VAT Quarterly

### Endpoint
```
GET /vat-quarterly?year=2025
```

### Request
**Headers:**
```
X-User-ID: 369
```

**Query Parameters:**
- `year` (optional): Year (defaults to current year)

**Body:** None

### Sample Response (200 OK)
```json
{
  "year": "2025",
  "quarterly_data": [
    {
      "quarter": "Q1",
      "quarter_name": "Quarter 1 (Jan-Mar)",
      "Domestic VAT": 2550.00,
      "Input VAT": 1050.00
    },
    {
      "quarter": "Q2",
      "quarter_name": "Quarter 2 (Apr-Jun)",
      "Domestic VAT": 0.00,
      "Input VAT": 0.00
    },
    {
      "quarter": "Q3",
      "quarter_name": "Quarter 3 (Jul-Sep)",
      "Domestic VAT": 203.19,
      "Input VAT": 0.00
    },
    {
      "quarter": "Q4",
      "quarter_name": "Quarter 4 (Oct-Dec)",
      "Domestic VAT": 0.00,
      "Input VAT": 0.00
    }
  ],
  "total_vat": 3803.19,
  "total_amount": 79750.00
}
```

---

## 10. VAT Payable

### Endpoint
```
GET /vat-payable?year=2025
```

### Request
**Headers:**
```
X-User-ID: 369
```

**Query Parameters:**
- `year` (optional): Year (defaults to current year)

**Body:** None

### Sample Response (200 OK)
```json
{
  "year": "2025",
  "vat_collected": 2753.19,
  "vat_paid": 1050.00,
  "vat_payable": 1703.19,
  "status": "payment_due"
}
```

### Sample Response (Refund Due)
```json
{
  "year": "2025",
  "vat_collected": 500.00,
  "vat_paid": 1500.00,
  "vat_payable": -1000.00,
  "status": "refund_due"
}
```

### Sample Response (Balanced)
```json
{
  "year": "2025",
  "vat_collected": 1000.00,
  "vat_paid": 1000.00,
  "vat_payable": 0.00,
  "status": "balanced"
}
```

---

## 11. Calculate VAT

### Endpoint
```
POST /calculate-vat
```

### Request
**Headers:**
```
X-User-ID: 369
Content-Type: application/json
```

**Body:**
```json
{
  "pre_vat_amount": 1000.00,
  "vat_percentage": "21",
  "vat_category": null
}
```

**OR with VAT category:**
```json
{
  "pre_vat_amount": 1000.00,
  "vat_percentage": null,
  "vat_category": "Standard VAT"
}
```

### Sample Response (200 OK)
```json
{
  "pre_vat_amount": 1000.00,
  "vat_percentage": "21%",
  "vat_category": null,
  "calculated_vat_amount": 210.00,
  "total_with_vat": 1210.00,
  "vat_rate_used": 21.0
}
```

### Error Response (400 Bad Request)
```json
{
  "detail": "pre_vat_amount and vat_percentage are required"
}
```

---

## 12. Validate VAT

### Endpoint
```
POST /validate-vat
```

### Request
**Headers:**
```
X-User-ID: 369
Content-Type: application/json
```

**Body:**
```json
{
  "pre_vat_amount": 1000.00,
  "vat_percentage": "21",
  "extracted_vat_amount": 210.00,
  "vat_category": null
}
```

### Sample Response (200 OK - Valid)
```json
{
  "pre_vat_amount": 1000.00,
  "vat_percentage": "21%",
  "extracted_vat_amount": 210.00,
  "calculated_vat_amount": 210.00,
  "is_valid": true,
  "difference": 0.00,
  "vat_category": null
}
```

### Sample Response (200 OK - Invalid)
```json
{
  "pre_vat_amount": 1000.00,
  "vat_percentage": "21%",
  "extracted_vat_amount": 200.00,
  "calculated_vat_amount": 210.00,
  "is_valid": false,
  "difference": 10.00,
  "vat_category": null
}
```

---

## 13. VAT Report - Quarterly

### Endpoint
```
GET /vat-report-quarterly?year=2025&quarter=Q3
```

### Request
**Headers:**
```
X-User-ID: 369
```

**Query Parameters:**
- `year` (optional): Year (defaults to current year)
- `quarter` (optional): Quarter Q1, Q2, Q3, or Q4 (defaults to current quarter)

**Body:** None

### Sample Response (200 OK)
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
          "date": "2025-09-17",
          "invoice_no": "24700492",
          "description": "Premier Subscription Package",
          "net_amount": 967.6,
          "vat_percentage": 21,
          "vat_amount": 203.19,
          "customer_name": "PAE NL B.V."
        }
      ],
      "totals": {
        "net": 967.6,
        "vat": 203.19
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
    "vat_collected": 203.19,
    "vat_deductible": 0.0,
    "vat_payable": 203.19
  }
}
```

---

## 14. VAT Report - Monthly

### Endpoint
```
GET /vat-report-monthly?year=2025&month=9
```

### Request
**Headers:**
```
X-User-ID: 369
```

**Query Parameters:**
- `year` (optional): Year (defaults to current year)
- `month` (optional): Month (1-12, "Sep", "September", etc.) (defaults to current month)

**Body:** None

### Sample Response (200 OK)
```json
{
  "report_type": "vat_tax_return",
  "period": "Sep 2025",
  "generated_at": "2025-11-20T23:23:36.988773",
  "company_info": {
    "company_name": "Your Company B.V.",
    "company_vat": "NL123456789B01",
    "reporting_period": "Sep 2025"
  },
  "categories": {
    "1a": {
      "name": "Sales Taxed at the Standard Rate (21%)",
      "transactions": [
        {
          "date": "2025-09-17",
          "invoice_no": "24700492",
          "description": "Premier Subscription Package",
          "net_amount": 967.6,
          "vat_percentage": 21,
          "vat_amount": 203.19,
          "customer_name": "PAE NL B.V."
        }
      ],
      "totals": {
        "net": 967.6,
        "vat": 203.19
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
    "4a": {
      "name": "Purchases of Goods from EU Countries",
      "transactions": [
        {
          "date": "2025-09-25",
          "invoice_no": "Invoice_26411",
          "description": "SEPTEMBER SALES",
          "net_amount": 4357.46,
          "vat_percentage": 0,
          "vat_amount": 0.0,
          "vendor_name": "PAE Business Ltd"
        }
      ],
      "totals": {
        "net": 4357.46,
        "vat": 0.0
      }
    }
  },
  "vat_calculation": {
    "vat_collected": 203.19,
    "vat_deductible": 0.0,
    "vat_payable": 203.19
  },
  "_debug": {
    "total_invoices_in_year": 3,
    "invoices_in_month": 2,
    "month_requested": "Sep",
    "year_requested": "2025"
  }
}
```

---

## 15. VAT Report - Yearly

### Endpoint
```
GET /vat-report-yearly?year=2025
```

### Request
**Headers:**
```
X-User-ID: 369
```

**Query Parameters:**
- `year` (optional): Year (defaults to current year)

**Body:** None

### Sample Response (200 OK)
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
      "vat_collected": 2550.00,
      "vat_deductible": 1050.00,
      "vat_payable": 1500.00
    },
    "Q2": {
      "period": "Q2 2025 (Apr-Jun)",
      "vat_collected": 0.00,
      "vat_deductible": 0.00,
      "vat_payable": 0.00
    },
    "Q3": {
      "period": "Q3 2025 (Jul-Sep)",
      "vat_collected": 203.19,
      "vat_deductible": 0.00,
      "vat_payable": 203.19
    },
    "Q4": {
      "period": "Q4 2025 (Oct-Dec)",
      "vat_collected": 0.00,
      "vat_deductible": 0.00,
      "vat_payable": 0.00
    }
  },
  "categories": {
    "1a": {
      "name": "Sales Taxed at the Standard Rate (21%)",
      "transactions": [
        {
          "date": "2025-01-15",
          "invoice_no": "INV-001",
          "description": "Consulting Services",
          "net_amount": 10000.00,
          "vat_percentage": 21,
          "vat_amount": 2100.00,
          "customer_name": "Customer A"
        },
        {
          "date": "2025-09-17",
          "invoice_no": "24700492",
          "description": "Premier Subscription Package",
          "net_amount": 967.6,
          "vat_percentage": 21,
          "vat_amount": 203.19,
          "customer_name": "PAE NL B.V."
        }
      ],
      "totals": {
        "net": 10967.6,
        "vat": 2303.19
      }
    },
    "1b": {
      "name": "Sales Taxed at the Reduced Rate (9%)",
      "transactions": [
        {
          "date": "2025-02-10",
          "invoice_no": "INV-002",
          "description": "Food Products",
          "net_amount": 5000.00,
          "vat_percentage": 9,
          "vat_amount": 450.00,
          "customer_name": "Customer B"
        }
      ],
      "totals": {
        "net": 5000.00,
        "vat": 450.00
      }
    },
    "5b": {
      "name": "Input VAT on Domestic Purchases",
      "transactions": [
        {
          "date": "2025-01-20",
          "invoice_no": "PUR-001",
          "description": "Office Supplies",
          "net_amount": 5000.00,
          "vat_percentage": 21,
          "vat_amount": 1050.00,
          "vendor_name": "Supplier X"
        }
      ],
      "totals": {
        "net": 5000.00,
        "vat": 1050.00
      }
    }
  },
  "vat_calculation": {
    "vat_collected": 2753.19,
    "vat_deductible": 1050.00,
    "vat_payable": 1703.19
  }
}
```

---

## 16. Dreport (Dutch Tax Format)

### Endpoint
```
GET /dreport?year=2025&quarter=Q3
```

### Request
**Headers:**
```
X-User-ID: 369
```

**Query Parameters:**
- `year` (optional): Year (defaults to current year)
- `quarter` (optional): Quarter Q1, Q2, Q3, or Q4 (defaults to current quarter)

**Body:** None

### Sample Response (200 OK)
```json
{
  "report_meta": {
    "report_type": "VAT_Return",
    "jurisdiction": "NL",
    "company_name": "Your Company B.V.",
    "vat_number": "NL123456789B01",
    "period": "Q3 2025",
    "submission_date": "2025-11-20"
  },
  "sections": [
    {
      "id": "1",
      "title": "Domestic Performance",
      "rows": [
        {
          "code": "1a",
          "description": "Supplies/services taxed at standard rate (High)",
          "net_amount": 967.6,
          "vat": 203.19
        },
        {
          "code": "1b",
          "description": "Supplies/services taxed at reduced rate (Low)",
          "net_amount": 0.0,
          "vat": 0.0
        },
        {
          "code": "1c",
          "description": "Supplies/services taxed at other rates, except 0%",
          "net_amount": 0.0,
          "vat": 0.0
        },
        {
          "code": "1d",
          "description": "Private use",
          "net_amount": 0.0,
          "vat": 0.0
        },
        {
          "code": "1e",
          "description": "Supplies/services taxed at 0% or not taxed",
          "net_amount": 0.0,
          "vat": 0.0
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
          "net_amount": 0.0,
          "vat": 0.0
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
          "net_amount": 0.0,
          "vat": 0.0
        },
        {
          "code": "3b",
          "description": "Supplies to/in countries within the EU",
          "net_amount": 0.0,
          "vat": 0.0
        },
        {
          "code": "3c",
          "description": "Installation/distance sales within the EU",
          "net_amount": 0.0,
          "vat": 0.0
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
          "net_amount": 0.0,
          "vat": 0.0
        },
        {
          "code": "4b",
          "description": "Supplies/services from countries within the EU",
          "net_amount": 0.0,
          "vat": 0.0
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
          "net_amount": null,
          "vat": 203.19
        },
        {
          "code": "5b",
          "description": "Input Tax (Deductible VAT)",
          "net_amount": null,
          "vat": 0.0
        },
        {
          "code": "5c",
          "description": "Subtotal (5a minus 5b)",
          "net_amount": null,
          "vat": 203.19
        },
        {
          "code": "5d",
          "description": "Reduction according to small business scheme (KOR)",
          "net_amount": null,
          "vat": 0.00
        },
        {
          "code": "5e",
          "description": "Estimate previous return",
          "net_amount": null,
          "vat": 0.00
        },
        {
          "code": "5f",
          "description": "Estimate",
          "net_amount": null,
          "vat": 0.00
        },
        {
          "code": "Total",
          "description": "Total to Pay / Reclaim",
          "net_amount": null,
          "vat": 203.19
        }
      ]
    }
  ],
  "_debug": {
    "total_invoices_in_year": 3,
    "invoices_in_quarter": 2,
    "invoices_skipped": 1,
    "target_months": ["Jul", "Aug", "Sep"],
    "quarter_requested": "Q3",
    "year_requested": "2025"
  }
}
```

---

## 17. Clear User Data

### Endpoint
```
DELETE /clear-user-data
```

### Request
**Headers:**
```
X-User-ID: 369
```

**Body:** None

### Sample Response (200 OK)
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

## Complete Workflow Example

### Step 1: Health Check
```bash
GET /health
```

### Step 2: Set Company Details
```bash
POST /company-details
Headers:
  X-User-ID: 369
  X-Company-Name: Your Company B.V.
  X-Company-VAT: NL123456789B01
```

### Step 3: Process Invoices
```bash
POST /process-invoices
Headers:
  X-User-ID: 369
  Content-Type: application/json
Body: [array of invoice objects]
```

### Step 4: Get Quarterly Report
```bash
GET /vat-report-quarterly?year=2025&quarter=Q3
Headers:
  X-User-ID: 369
```

### Step 5: Get Yearly Report
```bash
GET /vat-report-yearly?year=2025
Headers:
  X-User-ID: 369
```

---

## Common Error Responses

### 400 Bad Request - Missing Header
```json
{
  "detail": "Missing X-User-ID header"
}
```

### 400 Bad Request - Invalid Input
```json
{
  "detail": "Expected a JSON array of invoices"
}
```

### 404 Not Found - No Data
```json
{
  "detail": "No data found for specified period"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error processing invoices: [error message]"
}
```

---

## Notes

1. **Date Formats**: Use `YYYY-MM-DD` format (e.g., `2025-09-25`)
2. **Month Formats**: Accepts `9`, `09`, `Sep`, `September` for month parameter
3. **Quarter Formats**: Use `Q1`, `Q2`, `Q3`, or `Q4` (case-insensitive)
4. **VAT Category Codes (NEW APPROACH)**: 
   - **Required Fields**: `VAT Category (NL) Code` and `VAT Category (NL) Description`
   - **Dutch VAT Return Categories**:
     - **Sales boxes**: `1a` (21% NL), `1b` (9% NL), `1c` (0% other rates), `1e` (exempt), `2a` (reverse charge), `3a` (EU goods), `3b` (EU services), `3c` (EU B2C)
     - **Purchase boxes**: `4a` (non-EU goods), `4b` (EU goods/services), `5a` (domestic with VAT)
   - **Backward Compatibility**: If NL codes are not provided, system will attempt to map from old `vat_category` field
5. **Negative Amounts**: Credit notes should have negative `net_amount` and `vat_amount`
6. **Duplicate Detection**: Invoices with the same `file_name` or `invoice_number` in the same year will be skipped
7. **User Isolation**: Each user's data is isolated by `X-User-ID` header
8. **VAT Category Description**: The description is stored and included in reports for better readability

---

## Testing Tips

1. **Start with Health Check**: Always verify the API is running
2. **Set Company Details First**: This ensures reports show company information
3. **Process Sample Data**: Use the sample invoices provided above
4. **Check Different Periods**: Test monthly, quarterly, and yearly reports
5. **Test Edge Cases**: 
   - Credit notes (negative amounts)
   - Zero-rated transactions
   - EU transactions
   - Reverse charge transactions
6. **Verify Calculations**: Manually verify VAT calculations match expected results

---

## Additional Resources

- **Swagger UI**: Visit `http://localhost:8000/docs` for interactive API documentation
- **Complete Documentation**: See `COMPLETE_DOCUMENTATION.md` for detailed system documentation
- **Postman Guide**: See `POSTMAN_TESTING_GUIDE.md` for Postman-specific testing instructions


