# How to Use the VAT Analysis System

## Quick Start Guide

### Step 1: Start the Server

```bash
python start_backend.py
```

The server will start at: `http://localhost:8000`

---

## Step 2: Process Your Invoices

### Endpoint: `POST /process-invoices`

**This is where you paste your 10 invoices JSON input!**

#### Option A: Using Swagger UI (Easiest)

1. Open your browser and go to: `http://localhost:8000/docs`
2. Find the endpoint: **`POST /process-invoices`**
3. Click **"Try it out"**
4. In the **Request body** field, paste your JSON (from `sample_10_invoices.json`)
5. Set the header:
   - **X-User-ID**: `test_user` (or any user ID you want)
6. Click **"Execute"**

#### Option B: Using cURL

```bash
curl -X POST "http://localhost:8000/process-invoices" \
  -H "X-User-ID: test_user" \
  -H "Content-Type: application/json" \
  -d @sample_10_invoices.json
```

#### Option C: Using Python

```python
import requests

url = "http://localhost:8000/process-invoices"
headers = {
    "X-User-ID": "test_user",
    "Content-Type": "application/json"
}

# Read your JSON file
with open("sample_10_invoices.json", "r") as f:
    data = json.load(f)

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

#### Expected Response:

```json
{
  "status": "success",
  "message": "Processed 10 invoices, skipped 0, errors: 0",
  "details": {
    "processed": 10,
    "skipped": 0,
    "errors": 0,
    "updated_years": ["2024", "2025"]
  },
  "total_invoices_detected": 10
}
```

---

## Step 3: Set Company Details (Optional but Recommended)

### Endpoint: `POST /company-details`

This helps populate company info in your VAT reports.

**Using Swagger UI:**
1. Go to `http://localhost:8000/docs`
2. Find **`POST /company-details`**
3. Click **"Try it out"**
4. Set headers:
   - **X-User-ID**: `test_user`
   - **X-Company-Name**: `Dutch Food Solutions B.V.`
   - **X-Company-VAT**: `NL858674257B01`
5. Click **"Execute"**

**Using cURL:**
```bash
curl -X POST "http://localhost:8000/company-details" \
  -H "X-User-ID: test_user" \
  -H "X-Company-Name: Dutch Food Solutions B.V." \
  -H "X-Company-VAT: NL858674257B01"
```

---

## Step 4: View VAT Returns

Now you can view VAT calculations in three formats:

### 1. Monthly VAT Report

**Endpoint:** `GET /vat-report-monthly`

**Using Swagger UI:**
1. Go to `http://localhost:8000/docs`
2. Find **`GET /vat-report-monthly`**
3. Click **"Try it out"**
4. Set:
   - **X-User-ID**: `test_user`
   - **year**: `2024` (query parameter)
   - **month**: `Sep` (query parameter - use: Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec)
5. Click **"Execute"**

**Using cURL:**
```bash
curl -X GET "http://localhost:8000/vat-report-monthly?year=2024&month=Sep" \
  -H "X-User-ID: test_user"
```

**Response includes:**
- All VAT categories (1a, 1b, 1c, 2a, 3a, 3b, 4a, 4b, 4c, 5b)
- Transactions for that month
- VAT calculation (collected, deductible, payable)

---

### 2. Quarterly VAT Report

**Endpoint:** `GET /vat-report-quarterly`

**Using Swagger UI:**
1. Go to `http://localhost:8000/docs`
2. Find **`GET /vat-report-quarterly`**
3. Click **"Try it out"**
4. Set:
   - **X-User-ID**: `test_user`
   - **year**: `2024`
   - **quarter**: `Q3` (use: Q1, Q2, Q3, Q4)
5. Click **"Execute"**

**Using cURL:**
```bash
curl -X GET "http://localhost:8000/vat-report-quarterly?year=2024&quarter=Q3" \
  -H "X-User-ID: test_user"
```

---

### 3. Yearly VAT Report

**Endpoint:** `GET /vat-report-yearly`

**Using Swagger UI:**
1. Go to `http://localhost:8000/docs`
2. Find **`GET /vat-report-yearly`**
3. Click **"Try it out"**
4. Set:
   - **X-User-ID**: `test_user`
   - **year**: `2024`
5. Click **"Execute"**

**Using cURL:**
```bash
curl -X GET "http://localhost:8000/vat-report-yearly?year=2024" \
  -H "X-User-ID: test_user"
```

**Response includes:**
- Quarterly breakdown
- All VAT categories for the entire year
- Total VAT calculation

---

## Complete Example Workflow

### 1. Process Invoices
```bash
# Paste your JSON in Swagger UI or use:
curl -X POST "http://localhost:8000/process-invoices" \
  -H "X-User-ID: test_user" \
  -H "Content-Type: application/json" \
  -d @sample_10_invoices.json
```

### 2. Set Company Details
```bash
curl -X POST "http://localhost:8000/company-details" \
  -H "X-User-ID: test_user" \
  -H "X-Company-Name: Dutch Food Solutions B.V." \
  -H "X-Company-VAT: NL858674257B01"
```

### 3. View Monthly Report
```bash
curl -X GET "http://localhost:8000/vat-report-monthly?year=2024&month=Sep" \
  -H "X-User-ID: test_user"
```

### 4. View Quarterly Report
```bash
curl -X GET "http://localhost:8000/vat-report-quarterly?year=2024&quarter=Q3" \
  -H "X-User-ID: test_user"
```

### 5. View Yearly Report
```bash
curl -X GET "http://localhost:8000/vat-report-yearly?year=2024" \
  -H "X-User-ID: test_user"
```

---

## Understanding the VAT Report Response

Each report returns:

```json
{
  "report_type": "vat_tax_return",
  "period": "Sep 2024",
  "generated_at": "2024-10-22T10:30:00",
  "company_info": {
    "company_name": "Dutch Food Solutions B.V.",
    "company_vat": "NL858674257B01",
    "reporting_period": "Sep 2024"
  },
  "categories": {
    "1a": {
      "name": "Sales Taxed at the Standard Rate (21%)",
      "transactions": [
        {
          "date": "2024-09-04",
          "invoice_no": "DFS 001/2024",
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
    "1b": {...},
    "1c": {...},
    // ... all 10 categories
  },
  "vat_calculation": {
    "vat_collected": 2100.0,    // VAT from sales
    "vat_deductible": 500.0,    // VAT from purchases
    "vat_payable": 1600.0       // Net VAT to pay
  }
}
```

---

## Quick Reference

| Step | Endpoint | Method | Purpose |
|------|----------|--------|---------|
| 1 | `/process-invoices` | POST | **Paste your JSON here!** |
| 2 | `/company-details` | POST | Set company info (optional) |
| 3 | `/vat-report-monthly` | GET | View monthly VAT return |
| 4 | `/vat-report-quarterly` | GET | View quarterly VAT return |
| 5 | `/vat-report-yearly` | GET | View yearly VAT return |

---

## Important Notes

1. **User ID**: Use the same `X-User-ID` for all requests (e.g., `test_user`)
2. **Year**: Use the year from your invoice dates (e.g., `2024`, `2025`)
3. **Month**: Use 3-letter abbreviation (Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec)
4. **Quarter**: Use Q1, Q2, Q3, or Q4
5. **Data Persistence**: Currently using in-memory storage (data lost on server restart)

---

## Troubleshooting

### No data in reports?
- Make sure you processed invoices first using `/process-invoices`
- Check that the year/month/quarter matches your invoice dates
- Verify invoices were processed successfully (check the response from `/process-invoices`)

### Wrong year?
- Check your invoice dates in the JSON
- Use the correct year parameter in the report endpoint

### Need to see all transactions?
- Use `/transactions?year=2024` endpoint to see all transactions for a year

---

## Example: Using sample_10_invoices.json

Your `sample_10_invoices.json` has invoices from 2024 and 2025:

1. **Process all invoices:**
   ```bash
   curl -X POST "http://localhost:8000/process-invoices" \
     -H "X-User-ID: test_user" \
     -H "Content-Type: application/json" \
     -d @sample_10_invoices.json
   ```

2. **View 2024 Q3 report:**
   ```bash
   curl -X GET "http://localhost:8000/vat-report-quarterly?year=2024&quarter=Q3" \
     -H "X-User-ID: test_user"
   ```

3. **View 2024 yearly report:**
   ```bash
   curl -X GET "http://localhost:8000/vat-report-yearly?year=2024" \
     -H "X-User-ID: test_user"
   ```

4. **View September 2024 monthly report:**
   ```bash
   curl -X GET "http://localhost:8000/vat-report-monthly?year=2024&month=Sep" \
     -H "X-User-ID: test_user"
   ```

---

**That's it! You're ready to process invoices and view VAT returns!** 🎉

