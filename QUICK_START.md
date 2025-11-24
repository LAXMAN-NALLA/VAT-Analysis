# Quick Start Guide

## 🚀 Running the VAT Analysis System

### Prerequisites
- Python 3.8 or higher
- AWS account with S3 access
- AWS credentials (Access Key ID and Secret Access Key)

### Step-by-Step Setup

#### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2. Configure Environment
Create a `.env` file in the project root:

```env
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=ap-south-1
S3_BUCKET_NAME=vat-analysis-new
```

#### 3. Start the Server
```bash
python start_backend.py
```

The API will be running at: **http://localhost:8000**

#### 4. Test the API
Open your browser and visit: **http://localhost:8000/docs**

This will show the interactive API documentation where you can test all endpoints.

## 📝 Basic Usage

### Process Invoices
```bash
POST http://localhost:8000/process-invoices
Headers: X-User-ID: user123
Body: JSON with invoice data (see NEW_JSON_FORMAT_GUIDE.md)
```

### Get VAT Reports
```bash
# Monthly
GET http://localhost:8000/vat-report-monthly?year=2025&month=Jul
Headers: X-User-ID: user123

# Quarterly
GET http://localhost:8000/vat-report-quarterly?year=2025&quarter=Q3
Headers: X-User-ID: user123

# Yearly
GET http://localhost:8000/vat-report-yearly?year=2025
Headers: X-User-ID: user123
```

## ✅ Verification

1. Check health: `GET http://localhost:8000/health`
2. View API docs: `http://localhost:8000/docs`
3. Process test invoice (see example in README.md)
4. Retrieve VAT report

That's it! Your VAT Analysis API is ready to use.

