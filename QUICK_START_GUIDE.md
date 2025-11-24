# Quick Start Guide - VAT Analysis System

## 🚀 Getting Started in 5 Minutes

### Step 1: Start the Server
```bash
python start_backend.py
```

Server will start at: `http://localhost:8000`

### Step 2: Open Swagger UI
Open in browser: `http://localhost:8000/docs`

### Step 3: Set Company Details (Optional)
```
POST /company-details
Headers: X-User-ID: 369
Body: {
  "company_name": "Your Company B.V.",
  "company_vat": "NL123456789B01"
}
```

### Step 4: Process Invoices
```
POST /process-invoices
Headers: X-User-ID: 369
Body: [
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

### Step 5: Generate Report
```
GET /vat-report-quarterly?year=2025&quarter=Q3
Headers: X-User-ID: 369
```

## 📋 Required Fields

Every invoice must have:
- ✅ `date` - Invoice date (YYYY-MM-DD)
- ✅ `type` - "Sales" or "Purchase"
- ✅ `net_amount` - Amount before VAT
- ✅ `vat_amount` - VAT amount (null for zero-rated)
- ✅ `vat_category` - Category string
- ✅ `vat_percentage` - "0", "21", or "9"
- ✅ `file_name` - Unique filename
- ✅ `description` - Invoice description
- ✅ `vendor_name` - Vendor/customer name
- ✅ `gross_amount` - Total including VAT

## 🎯 Common VAT Categories

| Category String | Use For |
|----------------|---------|
| "Standard VAT" | 21% VAT transactions |
| "Reduced Rate" | 9% VAT transactions |
| "Zero Rated" | 0% VAT (exports, EU supplies) |
| "Reverse Charge" | Services from outside NL |
| "EU Goods" | Goods to/from EU countries |
| "EU Services" | Services to/from EU countries |
| "Import" | Goods from non-EU countries |

## 📊 Report Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /vat-report-quarterly?year=2025&quarter=Q3` | Quarterly report |
| `GET /vat-report-monthly?year=2025&month=9` | Monthly report |
| `GET /vat-report-yearly?year=2025` | Yearly report with quarterly breakdown |

## 🔧 Common Commands

### Clear All Data
```
DELETE /clear-user-data
Headers: X-User-ID: 369
```

### Check Health
```
GET /health
```

### Get Company Details
```
GET /company-details
Headers: X-User-ID: 369
```

## ⚠️ Important Notes

1. **Always include `X-User-ID` header** in all requests
2. **Data is stored in memory** - lost on server restart
3. **Duplicate invoices are skipped** - use unique `file_name`
4. **Dates must be YYYY-MM-DD format**
5. **VAT amounts can be null** for zero-rated transactions

## 🐛 Troubleshooting

**All invoices skipped?**
→ Clear data: `DELETE /clear-user-data`

**Reports show zero amounts?**
→ Check `net_amount` and `vat_amount` in input

**Wrong VAT category?**
→ Use correct category strings (see table above)

**Server not responding?**
→ Restart: `python start_backend.py`

## 📚 Full Documentation

See `COMPLETE_DOCUMENTATION.md` for detailed information.

