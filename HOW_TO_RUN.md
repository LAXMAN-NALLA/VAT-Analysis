# How to Run the VAT Analysis API

## Quick Start

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

Or if you're using the startup script (it will auto-install):

```bash
python start_backend.py
```

### Step 2: Start the Server

**Option A: Using the startup script (Recommended)**
```bash
python start_backend.py
```

**Option B: Using uvicorn directly**
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Access the API

Once the server is running, you'll see:
```
🚀 Starting VAT Analysis Backend API...
🔗 API will be available at: http://localhost:8000
📚 API Documentation: http://localhost:8000/docs
```

## Testing the `/dreport` Endpoint

### Method 1: Using Swagger UI (Easiest)

1. Open your browser and go to: `http://localhost:8000/docs`
2. Find the `/dreport` endpoint
3. Click "Try it out"
4. Enter:
   - `X-User-ID`: Your user ID (e.g., "user_123")
   - `year`: "2025" (optional)
   - `quarter`: "Q3" (optional)
5. Click "Execute"
6. See the response

### Method 2: Using cURL

```bash
curl -X GET "http://localhost:8000/dreport?year=2025&quarter=Q3" \
  -H "X-User-ID: user_123"
```

### Method 3: Using Python

```python
import requests

response = requests.get(
    "http://localhost:8000/dreport",
    headers={"X-User-ID": "user_123"},
    params={"year": "2025", "quarter": "Q3"}
)

print(response.json())
```

### Method 4: Using PowerShell

```powershell
$headers = @{
    "X-User-ID" = "user_123"
}

$response = Invoke-RestMethod -Uri "http://localhost:8000/dreport?year=2025&quarter=Q3" `
    -Method Get -Headers $headers

$response | ConvertTo-Json -Depth 10
```

### Method 5: Using Browser

Simply open:
```
http://localhost:8000/dreport?year=2025&quarter=Q3
```

(Note: You'll need to add the `X-User-ID` header using a browser extension or Postman)

## Complete Workflow Example

### 1. Start the Server

```bash
python start_backend.py
```

### 2. Set Company Details (Optional but Recommended)

```bash
curl -X POST "http://localhost:8000/company-details" \
  -H "X-User-ID: user_123" \
  -H "X-Company-Name: PAE NL B.V." \
  -H "X-Company-VAT: NL860816709B01"
```

### 3. Process Some Invoices

```bash
curl -X POST "http://localhost:8000/process-invoices" \
  -H "X-User-ID: user_123" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "date": "2025-09-25",
      "type": "Sales",
      "net_amount": 1000.00,
      "vat_amount": 210.00,
      "vat_category": "Standard VAT",
      "vat_percentage": "21",
      "description": "Service provided",
      "customer_name": "Customer ABC",
      "gross_amount": 1210.00,
      "file_name": "INV_001.pdf"
    }
  ]'
```

### 4. Generate Dreport

```bash
curl -X GET "http://localhost:8000/dreport?year=2025&quarter=Q3" \
  -H "X-User-ID: user_123"
```

## Troubleshooting

### Issue: Port 8000 already in use

**Solution**: Use a different port:
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8001
```

### Issue: Module not found errors

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### Issue: No data in report

**Solution**: 
1. Make sure you've processed invoices first using `/process-invoices`
2. Check that the year and quarter match your invoice dates
3. Verify invoices are in the correct format

### Issue: Company name shows "N/A"

**Solution**: Set company details first:
```bash
curl -X POST "http://localhost:8000/company-details" \
  -H "X-User-ID: user_123" \
  -H "X-Company-Name: Your Company Name" \
  -H "X-Company-VAT: NL123456789B01"
```

## Testing with Sample Data

### Quick Test Script

Create a file `test_dreport.py`:

```python
import requests

BASE_URL = "http://localhost:8000"
USER_ID = "test_user"

# 1. Set company details
print("Setting company details...")
response = requests.post(
    f"{BASE_URL}/company-details",
    headers={
        "X-User-ID": USER_ID,
        "X-Company-Name": "PAE NL B.V.",
        "X-Company-VAT": "NL860816709B01"
    }
)
print(f"Company details: {response.json()}")

# 2. Process sample invoices
print("\nProcessing invoices...")
invoices = [
    {
        "date": "2025-09-25",
        "type": "Sales",
        "net_amount": 1000.00,
        "vat_amount": 210.00,
        "vat_category": "Standard VAT",
        "vat_percentage": "21",
        "description": "Service provided",
        "customer_name": "Customer ABC",
        "gross_amount": 1210.00,
        "file_name": "INV_001.pdf"
    },
    {
        "date": "2025-08-15",
        "type": "Sales",
        "net_amount": 500.00,
        "vat_amount": 105.00,
        "vat_category": "Standard VAT",
        "vat_percentage": "21",
        "description": "Another service",
        "customer_name": "Customer XYZ",
        "gross_amount": 605.00,
        "file_name": "INV_002.pdf"
    }
]

response = requests.post(
    f"{BASE_URL}/process-invoices",
    headers={"X-User-ID": USER_ID},
    json=invoices
)
print(f"Invoices processed: {response.json()}")

# 3. Generate dreport
print("\nGenerating dreport...")
response = requests.get(
    f"{BASE_URL}/dreport",
    headers={"X-User-ID": USER_ID},
    params={"year": "2025", "quarter": "Q3"}
)

report = response.json()
print(f"\nReport generated:")
print(f"Company: {report['report_meta']['company_name']}")
print(f"Period: {report['report_meta']['period']}")
print(f"\nSection 1 (Domestic Performance):")
for row in report['sections'][0]['rows']:
    if row['net_amount'] > 0 or row['vat'] > 0:
        print(f"  {row['code']}: {row['description']}")
        print(f"    Net Amount: €{row['net_amount']}")
        print(f"    VAT: €{row['vat']}")

print(f"\nSection 5 (Totals):")
total_row = report['sections'][4]['rows'][-1]
print(f"  Total VAT: €{total_row['vat']}")
```

Run it:
```bash
python test_dreport.py
```

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/dreport` | GET | Generate Dutch VAT return report |
| `/process-invoices` | POST | Process invoice data |
| `/vat-report-quarterly` | GET | Quarterly VAT report |
| `/vat-report-monthly` | GET | Monthly VAT report |
| `/vat-report-yearly` | GET | Yearly VAT report |
| `/company-details` | POST/GET | Set/Get company information |
| `/clear-user-data` | DELETE | Clear all user data |

## Next Steps

1. ✅ Start the server
2. ✅ Process your invoices using `/process-invoices`
3. ✅ Generate reports using `/dreport` or other report endpoints
4. ✅ Use the Swagger UI at `http://localhost:8000/docs` for interactive testing

---

**Need Help?** Check the API documentation at `http://localhost:8000/docs` for all available endpoints and their parameters.


