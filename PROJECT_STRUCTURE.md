# Project Structure

## ✅ Essential Files (Keep These)

```
backend_functionality-master/
├── app.py                    # Main FastAPI application - API endpoints
├── processor.py              # Core processing logic - data transformation
├── start_backend.py          # Startup script for the backend server
├── requirements.txt          # Python dependencies
├── README.md                 # Main documentation
├── QUICK_START.md            # Quick start guide
├── NEW_JSON_FORMAT_GUIDE.md  # JSON format processing guide
└── .env                      # Environment variables (create this)
```

## ❌ Removed Files

The following unnecessary files have been removed:

### Test Files
- `test_two_step_approach.py` - Old test script
- `test_openai.py` - Old OpenAI test script

### Old Documentation
- `TWO_STEP_APPROACH_GUIDE.md` - Replaced by NEW_JSON_FORMAT_GUIDE.md
- `STREAMLIT_USAGE_GUIDE.md` - Streamlit UI removed
- `COMPANY_DETAILS_API_GUIDE.md` - Redundant
- `USER_COMPANY_DETAILS_SUMMARY.md` - Redundant
- `COMPLETE_SETUP_GUIDE.md` - Replaced by README.md

### Sample Data Files
- `sample_vat_report.json`
- `sample_quarterly_vat_report.json`
- `sample_quarterly_vat_report_simplified.json`
- `sample_yearly_vat_report.json`
- `sample_yearly_vat_report_simplified.json`

### Streamlit Files (UI Removed)
- `streamlit_app.py` - Streamlit UI application
- `start_streamlit.py` - Streamlit startup script

## 📋 File Descriptions

### app.py
Main FastAPI application with all API endpoints:
- `/process-invoices` - Process JSON invoice data
- `/vat-report-monthly` - Monthly VAT returns
- `/vat-report-quarterly` - Quarterly VAT returns
- `/vat-report-yearly` - Yearly VAT returns
- `/vat-summary` - VAT summaries
- `/company-details` - Company information management
- And more...

### processor.py
Core processing functions:
- `process_json_invoices()` - Process invoice JSON data
- `transform_register_entry_to_invoice()` - Transform data format
- `map_vat_category_to_code()` - Map VAT categories
- `get_user_company_details()` - Retrieve company info
- Helper functions for VAT calculations

### start_backend.py
Convenient startup script that:
- Checks for required packages
- Verifies .env file exists
- Starts the FastAPI server on port 8000

### requirements.txt
All Python dependencies needed:
- fastapi
- uvicorn
- boto3 (AWS S3)
- python-dotenv
- And more...

## 🚀 How to Run

See **QUICK_START.md** for detailed steps, or:

1. Install: `pip install -r requirements.txt`
2. Configure: Create `.env` file with AWS credentials
3. Start: `python start_backend.py`
4. Access: `http://localhost:8000/docs`

## 📚 Documentation Files

- **README.md** - Complete documentation with all endpoints
- **QUICK_START.md** - Quick setup guide
- **NEW_JSON_FORMAT_GUIDE.md** - Detailed JSON format specification

