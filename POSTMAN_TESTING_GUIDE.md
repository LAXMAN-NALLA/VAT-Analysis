# Postman Testing Guide for VAT Analysis API

**Base URL:** `https://vat-analysis.onrender.com`

## 📋 Table of Contents
1. [Health Check](#1-health-check)
2. [Process Invoices](#2-process-invoices)
3. [Get VAT Reports](#3-get-vat-reports)
4. [Company Details](#4-company-details)
5. [Other Endpoints](#5-other-endpoints)

---

## 1. Health Check

### Endpoint
```
GET https://vat-analysis.onrender.com/health
```

### Postman Setup
- **Method:** GET
- **URL:** `https://vat-analysis.onrender.com/health`
- **Headers:** None required
- **Body:** None

### Expected Response
```json
{
  "status": "healthy",
  "message": "VAT Analysis API is running"
}
```

---

## 2. Process Invoices

### Endpoint
```
POST https://vat-analysis.onrender.com/process-invoices
```

### Postman Setup

**Step 1: Create New Request**
- Click "New" → "HTTP Request"
- Set method to **POST**
- Enter URL: `https://vat-analysis.onrender.com/process-invoices`

**Step 2: Add Headers**
Go to "Headers" tab and add:
```
Key: X-User-ID
Value: test-user-123
```

**Step 3: Set Body**
- Go to "Body" tab
- Select **raw**
- Select **JSON** from dropdown
- Paste the following JSON:

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
    "vat_percentage": "0",
    "customer_name": "Your Company B.V."
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
    "vat_category": "Standard VAT",
    "vat_percentage": "21"
  }
]
```

**Step 4: Send Request**
- Click "Send"
- You should see a success response with processed count

### Expected Response
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

---

## 3. Get VAT Reports

### 3.1 Monthly Report

**Endpoint:**
```
GET https://vat-analysis.onrender.com/vat-report-monthly?year=2025&month=09
```

**Postman Setup:**
- **Method:** GET
- **URL:** `https://vat-analysis.onrender.com/vat-report-monthly`
- **Params Tab:**
  - `year`: `2025`
  - `month`: `09` (or `Sep`)
- **Headers:**
  ```
  X-User-ID: test-user-123
  ```

**Expected Response:**
```json
{
  "report_type": "vat_tax_return",
  "period": "Sep 2025",
  "generated_at": "2025-11-24T...",
  "company_info": {
    "company_name": "N/A",
    "company_vat": "N/A",
    "reporting_period": "Sep 2025"
  },
  "categories": {
    "1a": {
      "name": "Sales Taxed at the Standard Rate (21%)",
      "transactions": [...],
      "totals": {
        "net": 967.6,
        "vat": 203.19
      }
    },
    ...
  },
  "vat_calculation": {
    "vat_collected": 203.19,
    "vat_deductible": 0,
    "vat_payable": 203.19
  }
}
```

### 3.2 Quarterly Report

**Endpoint:**
```
GET https://vat-analysis.onrender.com/vat-report-quarterly?year=2025&quarter=Q3
```

**Postman Setup:**
- **Method:** GET
- **URL:** `https://vat-analysis.onrender.com/vat-report-quarterly`
- **Params:**
  - `year`: `2025`
  - `quarter`: `Q3`
- **Headers:**
  ```
  X-User-ID: test-user-123
  ```

### 3.3 Yearly Report

**Endpoint:**
```
GET https://vat-analysis.onrender.com/vat-report-yearly?year=2025
```

**Postman Setup:**
- **Method:** GET
- **URL:** `https://vat-analysis.onrender.com/vat-report-yearly`
- **Params:**
  - `year`: `2025`
- **Headers:**
  ```
  X-User-ID: test-user-123
  ```

---

## 4. Company Details

### 4.1 Set Company Details

**Endpoint:**
```
POST https://vat-analysis.onrender.com/company-details
```

**Postman Setup:**
- **Method:** POST
- **URL:** `https://vat-analysis.onrender.com/company-details`
- **Headers:**
  ```
  X-User-ID: test-user-123
  X-Company-Name: Your Company B.V.
  X-Company-VAT: NL123456789B01
  ```
- **Body:** None

### 4.2 Get Company Details

**Endpoint:**
```
GET https://vat-analysis.onrender.com/company-details
```

**Postman Setup:**
- **Method:** GET
- **URL:** `https://vat-analysis.onrender.com/company-details`
- **Headers:**
  ```
  X-User-ID: test-user-123
  ```

---

## 5. Other Endpoints

### 5.1 VAT Summary
```
GET https://vat-analysis.onrender.com/vat-summary?year=2025
Headers: X-User-ID: test-user-123
```

### 5.2 Transactions List
```
GET https://vat-analysis.onrender.com/transactions?year=2025
Headers: X-User-ID: test-user-123
```

### 5.3 VAT Payable
```
GET https://vat-analysis.onrender.com/vat-payable?year=2025
Headers: X-User-ID: test-user-123
```

### 5.4 User Info
```
GET https://vat-analysis.onrender.com/user-info
Headers: X-User-ID: test-user-123
```

### 5.5 Clear User Data
```
DELETE https://vat-analysis.onrender.com/clear-user-data
Headers: X-User-ID: test-user-123
```

---

## 🎯 Quick Test Workflow

### Step 1: Health Check
Test if API is running:
```
GET /health
```

### Step 2: Set Company Details (Optional)
```
POST /company-details
Headers: X-User-ID, X-Company-Name, X-Company-VAT
```

### Step 3: Process Sample Invoices
```
POST /process-invoices
Headers: X-User-ID
Body: [array of invoice objects]
```

### Step 4: Get Reports
```
GET /vat-report-monthly?year=2025&month=09
Headers: X-User-ID
```

---

## 📝 Sample Invoice JSON (Full Example)

Use this complete example for testing:

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
    "vat_percentage": "0",
    "customer_name": "Your Company B.V."
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
    "vat_category": "Standard VAT",
    "vat_percentage": "21"
  },
  {
    "date": "2025-09-25",
    "type": "Sales",
    "currency": "EUR",
    "file_name": "credit_24700493.pdf",
    "net_amount": -770.58,
    "vat_amount": null,
    "description": "KATUN Premier Monthly Support Rebate",
    "customer_name": "PAE NL B.V.",
    "gross_amount": -770.58,
    "vat_category": "Zero Rated",
    "vat_percentage": "0"
  }
]
```

---

## ⚠️ Important Notes

1. **Always include `X-User-ID` header** for all endpoints except `/health`
2. **Month format:** Use `09` or `Sep` (both work)
3. **Quarter format:** Use `Q1`, `Q2`, `Q3`, or `Q4`
4. **Date format:** Use `YYYY-MM-DD` (e.g., `2025-09-25`)
5. **Negative amounts:** Credit notes should have negative `net_amount` and `vat_amount`
6. **Duplicate detection:** Same `file_name` or `invoice_number` in same year will be skipped

---

## 🔧 Troubleshooting

### Error: "Missing X-User-ID header"
- **Solution:** Add `X-User-ID` header with any value (e.g., `test-user-123`)

### Error: "No data found"
- **Solution:** Make sure you've processed invoices first using `/process-invoices`

### Error: Connection timeout
- **Solution:** Render free tier may spin down after inactivity. First request may take 30-60 seconds to wake up the service.

### Empty report
- **Solution:** 
  1. Check if invoices were processed successfully
  2. Verify the year/month/quarter matches invoice dates
  3. Check the `_debug` section in response for diagnostic info

---

## 📚 Additional Resources

- **API Documentation:** Check `/docs` endpoint for Swagger UI (if enabled)
- **Sample Data:** See `sample_all_vat_categories.json` for more examples
- **Full Documentation:** See `COMPLETE_DOCUMENTATION.md`

---

## 🚀 Postman Collection Setup

### Create a Postman Collection

1. Click "New" → "Collection"
2. Name it "VAT Analysis API"
3. Add all requests as shown above
4. Set collection variable:
   - Variable: `base_url`
   - Value: `https://vat-analysis.onrender.com`
5. Use `{{base_url}}` in all request URLs

### Environment Variables (Optional)

Create a Postman Environment with:
- `base_url`: `https://vat-analysis.onrender.com`
- `user_id`: `test-user-123`
- `company_name`: `Your Company B.V.`
- `company_vat`: `NL123456789B01`

Then use `{{base_url}}` and `{{user_id}}` in your requests!

