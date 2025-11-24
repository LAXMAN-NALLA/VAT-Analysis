# S3 Integration Code Documentation

This file contains all S3 integration code that has been commented out. When you want to restore S3 integration, you can use this as a reference.

## Table of Contents
1. [app.py S3 Integration](#apppy-s3-integration)
2. [processor.py S3 Integration](#processorpy-s3-integration)
3. [Environment Variables](#environment-variables)
4. [Restoration Steps](#restoration-steps)

---

## app.py S3 Integration

### 1. Imports and Configuration

```python
import boto3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# S3 Client
s3_client = boto3.client('s3')
bucket_name = os.getenv('S3_BUCKET_NAME', 'vat-analysis-new')
```

### 2. User Info Endpoint

**Location**: `@app.get("/user-info")`

```python
# Check if user has any data
prefix = f"users/{user_id}/"
existing_files = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

pdf_count = 0
if "Contents" in existing_files:
    for obj in existing_files["Contents"]:
        if obj["Key"].endswith(".pdf"):
            pdf_count += 1

# Check for existing results
results_prefix = f"users/{user_id}/results/"
results_files = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=results_prefix)

processed_years = []
if "Contents" in results_files:
    for obj in results_files["Contents"]:
        if obj["Key"].endswith(".json") and "VATanalysis_" in obj["Key"]:
            year = obj["Key"].split("VATanalysis_")[-1].split(".json")[0]
            processed_years.append(year)
```

### 3. PDF Upload Endpoint

**Location**: `@app.post("/upload")`

```python
# Check how many PDFs already exist in user folder
prefix = f"users/{user_id}/"
existing_pdfs = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

pdf_count = 0
if "Contents" in existing_pdfs:
    for obj in existing_pdfs["Contents"]:
        if obj["Key"].endswith(".pdf"):
            pdf_count += 1

# Upload the files one by one
for file in files:
    upload_pdf_to_user_folder(user_id, file)
    log_user_event(user_id, "PDF Uploaded", {"filename": file.filename})
```

### 4. VAT Summary Endpoint

**Location**: `@app.get("/vat-summary")`

```python
json_key = f"users/{user_id}/results/VATanalysis_{year}.json"
try:
    obj = s3_client.get_object(Bucket=bucket_name, Key=json_key)
    data = json.loads(obj['Body'].read().decode('utf-8'))
except s3_client.exceptions.NoSuchKey:
    return {
        "monthly_data": [], "total_vat": 0, "total_amount": 0, "transactions": []
    }
```

### 5. Transactions Endpoint

**Location**: `@app.get("/transactions")`

```python
json_key = f"users/{user_id}/results/VATanalysis_{year}.json"
try:
    obj = s3_client.get_object(Bucket=bucket_name, Key=json_key)
    data = json.loads(obj['Body'].read().decode('utf-8'))
except s3_client.exceptions.NoSuchKey:
    return {"transactions": []}
```

### 6. Company Details - POST Endpoint

**Location**: `@app.post("/company-details")`

```python
# Store company details in S3
company_data = {
    "user_id": user_id,
    "company_name": company_name,
    "company_vat": company_vat,
    "updated_at": datetime.utcnow().isoformat() + "Z"
}

company_key = f"users/{user_id}/company_details.json"
s3_client.put_object(
    Bucket=bucket_name,
    Key=company_key,
    Body=json.dumps(company_data, indent=2),
    ContentType='application/json'
)
```

### 7. Company Details - GET Endpoint

**Location**: `@app.get("/company-details")`

```python
company_key = f"users/{user_id}/company_details.json"
try:
    obj = s3_client.get_object(Bucket=bucket_name, Key=company_key)
    company_data = json.loads(obj['Body'].read().decode('utf-8'))
    return {
        "company_name": company_data.get("company_name"),
        "company_vat": company_data.get("company_vat"),
        "updated_at": company_data.get("updated_at")
    }
except s3_client.exceptions.NoSuchKey:
    return {
        "company_name": None,
        "company_vat": None,
        "updated_at": None,
        "message": "No company details found. Please set company details first."
    }
```

### 8. VAT Quarterly Endpoint

**Location**: `@app.get("/vat-quarterly")`

```python
json_key = f"users/{user_id}/results/VATanalysis_{year}.json"
try:
    obj = s3_client.get_object(Bucket=bucket_name, Key=json_key)
    data = json.loads(obj['Body'].read().decode('utf-8'))
except s3_client.exceptions.NoSuchKey:
    return {
        "quarterly_data": [], 
        "total_vat": 0, 
        "total_amount": 0, 
        "year": year
    }
```

### 9. VAT Payable Endpoint

**Location**: `@app.get("/vat-payable")`

```python
json_key = f"users/{user_id}/results/VATanalysis_{year}.json"
try:
    obj = s3_client.get_object(Bucket=bucket_name, Key=json_key)
    data = json.loads(obj['Body'].read().decode('utf-8'))
except s3_client.exceptions.NoSuchKey:
    return {
        "vat_collected": 0,
        "vat_paid": 0,
        "vat_payable": 0,
        "year": year
    }
```

### 10. VAT Report Quarterly Endpoint

**Location**: `@app.get("/vat-report-quarterly")`

```python
json_key = f"users/{user_id}/results/VATanalysis_{year}.json"
try:
    obj = s3_client.get_object(Bucket=bucket_name, Key=json_key)
    data = json.loads(obj['Body'].read().decode('utf-8'))
except s3_client.exceptions.NoSuchKey:
    return {
        "report_type": "vat_tax_return",
        "period": f"{quarter} {year}",
        "generated_at": datetime.now().isoformat(),
        "categories": {},
        "vat_calculation": {"vat_collected": 0, "vat_deductible": 0, "vat_payable": 0},
    }
```

### 11. VAT Report Yearly Endpoint

**Location**: `@app.get("/vat-report-yearly")`

```python
json_key = f"users/{user_id}/results/VATanalysis_{year}.json"
try:
    obj = s3_client.get_object(Bucket=bucket_name, Key=json_key)
    data = json.loads(obj['Body'].read().decode('utf-8'))
except s3_client.exceptions.NoSuchKey:
    return {
        "report_type": "vat_tax_return",
        "period": year,
        "generated_at": datetime.now().isoformat(),
        "categories": {},
        "vat_calculation": {"vat_collected": 0, "vat_deductible": 0, "vat_payable": 0},
    }
```

### 12. VAT Report Monthly Endpoint

**Location**: `@app.get("/vat-report-monthly")`

```python
json_key = f"users/{user_id}/results/VATanalysis_{year}.json"
try:
    obj = s3_client.get_object(Bucket=bucket_name, Key=json_key)
    data = json.loads(obj['Body'].read().decode('utf-8'))
except s3_client.exceptions.NoSuchKey:
    return {
        "report_type": "vat_tax_return",
        "period": f"{month} {year}",
        "generated_at": datetime.now().isoformat(),
        "categories": {},
        "vat_calculation": {"vat_collected": 0, "vat_deductible": 0, "vat_payable": 0},
        "notes": f"No data found for {month} {year}"
    }
```

---

## processor.py S3 Integration

### 1. Imports and Configuration

```python
import boto3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
bucket_name = os.getenv('S3_BUCKET_NAME', 'vat-analysis-new')
region_name = os.getenv('AWS_DEFAULT_REGION', 'ap-south-1')

# AWS Credentials
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

# Initialize AWS clients with credentials
s3_client = boto3.client(
    's3', 
    region_name=region_name,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)
textract_client = boto3.client(
    'textract', 
    region_name=region_name,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)
```

### 2. process_json_invoices Function

**Location**: `def process_json_invoices(user_id, json_data)`

```python
def process_json_invoices(user_id, json_data):
    """
    Process invoices from new JSON format and store in S3
    """
    results_folder = f"users/{user_id}/results"
    
    # Load existing year-wise data
    all_year_data = {}
    existing_keys = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=results_folder).get("Contents", [])
    for obj in existing_keys:
        key = obj["Key"]
        if key.endswith(".json") and "VATanalysis_" in key:
            content = s3_client.get_object(Bucket=bucket_name, Key=key)['Body'].read().decode('utf-8')
            year = key.split("VATanalysis_")[-1].split(".json")[0]
            all_year_data[year] = json.loads(content)
    
    # ... processing logic ...
    
    # Save updated files
    for year in updated_years:
        key = f"{results_folder}/VATanalysis_{year}.json"
        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=json.dumps(all_year_data[year], indent=2),
            ContentType='application/json'
        )
    
    return {
        "processed": processed_count,
        "skipped": skipped_count,
        "errors": error_count,
        "updated_years": list(updated_years)
    }
```

### 3. upload_pdf_to_user_folder Function

**Location**: `def upload_pdf_to_user_folder(user_id: str, file: UploadFile)`

```python
def upload_pdf_to_user_folder(user_id: str, file: UploadFile):
    folder_key = f"users/{user_id}/"
    file_key = f"{folder_key}{file.filename}"
    s3_client.put_object(Bucket=bucket_name, Key=folder_key)
    s3_client.upload_fileobj(file.file, bucket_name, file_key)
    return f"✅ Uploaded '{file.filename}' to s3://{bucket_name}/{file_key}"
```

### 4. get_user_company_details Function

**Location**: `def get_user_company_details(user_id)`

```python
def get_user_company_details(user_id):
    """Get company details for a user from S3"""
    company_key = f"users/{user_id}/company_details.json"
    try:
        obj = s3_client.get_object(Bucket=bucket_name, Key=company_key)
        company_data = json.loads(obj['Body'].read().decode('utf-8'))
        return {
            'company_name': company_data.get('company_name'),
            'company_vat': company_data.get('company_vat')
        }
    except s3_client.exceptions.NoSuchKey:
        return None
```

### 5. log_user_event Function

**Location**: `def log_user_event(user_id, event, details=None)`

```python
def log_user_event(user_id, event, details=None):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": event,
        "details": details or {}
    }
    s3_key = f"users/{user_id}/activity_log.jsonl"
    
    try:
        existing = s3_client.get_object(Bucket=bucket_name, Key=s3_key)['Body'].read().decode('utf-8')
    except s3_client.exceptions.NoSuchKey:
        existing = ""

    updated_log = existing + json.dumps(log_entry) + "\n"
    s3_client.put_object(Bucket=bucket_name, Key=s3_key, Body=updated_log.encode('utf-8'))
```

### 6. fetch_pdf_from_s3 Function

**Location**: `def fetch_pdf_from_s3(bucket, folder)`

```python
def fetch_pdf_from_s3(bucket, folder):
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=folder)
        return [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.pdf')]
    except Exception as e:
        print(f"Error: {e}")
        return []
```

### 7. load_existing_json Function

**Location**: `def load_existing_json(results_folder)`

```python
def load_existing_json(results_folder):
    key = f"{results_folder}/VATanalysis.json"
    try:
        obj = s3_client.get_object(Bucket=bucket_name, Key=key)
        return json.loads(obj['Body'].read().decode('utf-8'))
    except:
        return {"invoices": []}
```

### 8. save_json Function

**Location**: `def save_json(data, results_folder, updated=False)`

```python
def save_json(data, results_folder, updated=False):
    if updated:
        key = f"{results_folder}/VATanalysis.json"
        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=json.dumps(data, indent=2),
            ContentType='application/json'
        )
```

---

## Environment Variables

Required environment variables for S3 integration:

```env
# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=ap-south-1
S3_BUCKET_NAME=vat-analysis-new

# OpenAI (if using AI features)
OPENAI_API_KEY=your_openai_api_key
```

---

## Restoration Steps

### Step 1: Restore Imports in app.py

1. Uncomment the imports:
```python
import boto3
import os
from dotenv import load_dotenv
load_dotenv()
```

2. Uncomment S3 client initialization:
```python
s3_client = boto3.client('s3')
bucket_name = os.getenv('S3_BUCKET_NAME', 'vat-analysis-new')
```

### Step 2: Restore Imports in processor.py

1. Uncomment the imports and configuration
2. Restore S3 and Textract client initialization

### Step 3: Replace In-Memory Storage with S3 Calls

For each endpoint:
1. Remove the in-memory storage code
2. Uncomment the corresponding S3 code from this document
3. Update function calls to remove `storage_dict` parameters

### Step 4: Update Function Signatures

1. In `processor.py`:
   - Remove `storage_dict` parameter from `process_json_invoices()`
   - Remove `storage_dict` parameter from `get_user_company_details()`

2. In `app.py`:
   - Remove `storage_dict=user_vat_data` from `process_json_invoices()` calls
   - Remove `storage_dict=user_company_details` from `get_user_company_details()` calls

### Step 5: Remove In-Memory Storage Dictionaries

Remove these from `app.py`:
```python
# Remove these dictionaries:
user_vat_data = defaultdict(dict)
user_company_details = {}
user_pdf_count = defaultdict(int)
```

### Step 6: Test S3 Integration

1. Ensure `.env` file has all required AWS credentials
2. Test each endpoint to verify S3 read/write operations
3. Check S3 bucket for proper file structure

---

## S3 File Structure

The S3 bucket should have this structure:

```
vat-analysis-new/
├── users/
│   ├── {user_id}/
│   │   ├── invoice1.pdf
│   │   ├── invoice2.pdf
│   │   ├── company_details.json
│   │   ├── activity_log.jsonl
│   │   └── results/
│   │       ├── VATanalysis_2024.json
│   │       ├── VATanalysis_2025.json
│   │       └── ...
```

---

## Notes

- All S3 code is currently commented out with clear markers: `# ==================== COMMENTED OUT - S3 Integration ====================`
- In-memory storage is used as a replacement
- Data structure remains the same - only storage mechanism changed
- When restoring, ensure AWS credentials are properly configured
- Test thoroughly after restoration to ensure no data loss

---

## Quick Reference: What to Change

### In app.py:
- ✅ Uncomment S3 imports and client
- ✅ Replace all `user_vat_data.get()` with S3 `get_object()` calls
- ✅ Replace all `user_company_details.get()` with S3 `get_object()` calls
- ✅ Remove `storage_dict` parameters from function calls
- ✅ Remove in-memory storage dictionaries

### In processor.py:
- ✅ Uncomment S3 imports and clients
- ✅ Restore S3 save operations in `process_json_invoices()`
- ✅ Restore S3 operations in `upload_pdf_to_user_folder()`
- ✅ Restore S3 operations in `get_user_company_details()`
- ✅ Restore S3 operations in `log_user_event()`
- ✅ Remove `storage_dict` parameters from function signatures

---

**Last Updated**: When S3 integration was removed
**Status**: All S3 code preserved in comments, ready for restoration

