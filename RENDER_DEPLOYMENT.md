# Render Deployment Guide for VAT Analysis System

This guide will help you deploy the VAT Analysis Backend API to Render.

## Prerequisites

1. A Render account (sign up at https://render.com)
2. Your OpenAI API key (if you plan to use OpenAI features)
3. Git repository (GitHub, GitLab, or Bitbucket)

## Step 1: Prepare Your Repository

### 1.1 Update requirements.txt

Make sure your `requirements.txt` includes all necessary dependencies. The current file should work, but you can remove `streamlit` and `plotly` if you're only deploying the API:

```txt
fastapi
uvicorn[standard]
python-multipart
python-dotenv
openai
pandas
openpyxl
```

**Note:** `boto3` is optional since S3 integration is currently disabled.

### 1.2 Create/Update Files

The following files are already created for you:
- `render.yaml` - Render configuration file
- `Procfile` - Process file for Render
- `.gitignore` (if needed)

## Step 2: Push to Git Repository

1. Initialize git (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Render deployment"
   ```

2. Push to your Git provider (GitHub, GitLab, or Bitbucket):
   ```bash
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

## Step 3: Deploy on Render

### Option A: Using render.yaml (Recommended)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Blueprint"**
3. Connect your Git repository
4. Render will automatically detect `render.yaml` and use it
5. Review the configuration and click **"Apply"**

### Option B: Manual Setup

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your Git repository
4. Configure the service:
   - **Name**: `vat-analysis-api` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Choose Free or Starter plan

5. Click **"Create Web Service"**

## Step 4: Configure Environment Variables

In the Render dashboard, go to your service → **Environment** tab, and add:

### Required (if using OpenAI):
- `OPENAI_API_KEY` - Your OpenAI API key

### Optional:
- `PYTHON_VERSION` - Set to `3.10.0` (or your preferred version)
- `ENVIRONMENT` - Set to `production`

**Note:** Since S3 integration is disabled, you don't need AWS credentials.

## Step 5: Deploy

1. Render will automatically start building and deploying your service
2. Monitor the build logs in the Render dashboard
3. Once deployed, you'll get a URL like: `https://vat-analysis-api.onrender.com`

## Step 6: Verify Deployment

1. Health Check:
   ```bash
   curl https://your-app-name.onrender.com/health
   ```
   Should return: `{"status": "healthy", "message": "VAT Analysis API is running"}`

2. API Documentation:
   Visit: `https://your-app-name.onrender.com/docs`

3. Test an endpoint:
   ```bash
   curl -X GET "https://your-app-name.onrender.com/health" \
     -H "X-User-ID: test123"
   ```

## Important Notes

### Free Tier Limitations

- **Spinning Down**: Free services spin down after 15 minutes of inactivity
- **Cold Start**: First request after spin-down may take 30-60 seconds
- **Memory**: 512 MB RAM limit
- **CPU**: Shared CPU resources

### Production Considerations

1. **Upgrade to Paid Plan**: For production use, consider upgrading to avoid spin-downs
2. **Database**: For persistent storage, consider adding a PostgreSQL database
3. **Environment Variables**: Keep sensitive keys in Render's environment variables, not in code
4. **CORS**: Update CORS settings in `app.py` to allow only your frontend domain:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://your-frontend-domain.com"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

### Data Persistence

**Current Setup**: The system uses in-memory storage, which means:
- Data is lost when the service restarts
- Data is lost when the service spins down (free tier)
- Each user's data is isolated by `user_id`

**For Production**: Consider:
- Adding a PostgreSQL database (Render offers managed PostgreSQL)
- Or implementing file-based storage
- Or re-enabling S3 integration

## Troubleshooting

### Build Fails

1. Check build logs in Render dashboard
2. Verify `requirements.txt` has all dependencies
3. Check Python version compatibility

### Service Won't Start

1. Check logs in Render dashboard
2. Verify start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
3. Ensure `app.py` exists in root directory

### Environment Variables Not Working

1. Verify variables are set in Render dashboard
2. Restart the service after adding variables
3. Check variable names match exactly (case-sensitive)

### CORS Errors

1. Update CORS settings in `app.py`
2. Add your frontend domain to `allow_origins`
3. Restart the service

### Service Spins Down (Free Tier)

1. This is normal for free tier
2. First request after spin-down will be slow
3. Consider upgrading to paid plan for production

## API Endpoints

Once deployed, your API will be available at:
- Base URL: `https://your-app-name.onrender.com`
- Health Check: `GET /health`
- API Docs: `GET /docs`
- Process Invoices: `POST /process-invoices`
- VAT Reports: `GET /vat-report-quarterly`, `/vat-report-monthly`, `/vat-report-yearly`

## Example Usage

```bash
# Health check
curl https://your-app-name.onrender.com/health

# Process invoices
curl -X POST "https://your-app-name.onrender.com/process-invoices" \
  -H "X-User-ID: 369" \
  -H "Content-Type: application/json" \
  -d '[{
    "date": "2025-01-15",
    "type": "Sales",
    "net_amount": 1000.00,
    "vat_amount": 210.00,
    "vat_category": "Standard VAT",
    "vat_percentage": "21",
    "file_name": "invoice_001.pdf"
  }]'

# Get quarterly report
curl -X GET "https://your-app-name.onrender.com/vat-report-quarterly?year=2025&quarter=Q1" \
  -H "X-User-ID: 369"
```

## Support

For issues:
1. Check Render logs in dashboard
2. Review this documentation
3. Check `COMPLETE_DOCUMENTATION.md` for API details

