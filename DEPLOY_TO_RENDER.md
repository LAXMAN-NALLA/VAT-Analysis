# Deploy to Render - Step by Step Guide

## 🚀 Quick Deployment (10 minutes)

### Prerequisites
- ✅ Render account (sign up at https://render.com - free tier available)
- ✅ Git repository (GitHub, GitLab, or Bitbucket)
- ✅ Your code pushed to Git

---

## Step 1: Verify Your Files

Make sure these files exist in your project root:

- ✅ `app.py` - Main FastAPI application
- ✅ `requirements.txt` - Python dependencies
- ✅ `Procfile` - Process file (already created)
- ✅ `render.yaml` - Render configuration (already created)
- ✅ `runtime.txt` - Python version (already created)

**All files are ready!** ✅

---

## Step 2: Push to Git (if not already done)

```bash
# If not already a git repository
git init
git add .
git commit -m "Ready for Render deployment"

# If you have a remote repository
git remote add origin <your-repo-url>
git push -u origin main
```

**Or if you already have a repo:**
```bash
git add .
git commit -m "Prepare for Render deployment"
git push
```

---

## Step 3: Deploy on Render

### Option A: Using render.yaml (Easiest - Recommended)

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Click**: "New +" → "Blueprint"
3. **Connect Repository**: 
   - Connect your GitHub/GitLab/Bitbucket account
   - Select your repository
4. **Render will detect `render.yaml` automatically**
5. **Review Configuration**:
   - Service name: `vat-analysis-api`
   - Environment: Python 3
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
6. **Click**: "Apply" or "Create Blueprint"

### Option B: Manual Setup

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Click**: "New +" → "Web Service"
3. **Connect Repository**: Select your Git repository
4. **Configure Service**:
   - **Name**: `vat-analysis-api` (or your preferred name)
   - **Region**: Choose closest to you
   - **Branch**: `main` (or `master`)
   - **Root Directory**: Leave empty (if app.py is in root)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Choose **Free** (for testing) or **Starter** (for production)
5. **Click**: "Create Web Service"

---

## Step 4: Configure Environment Variables

In Render dashboard, go to your service → **Environment** tab:

### Optional (if using OpenAI features):
- **Key**: `OPENAI_API_KEY`
- **Value**: Your OpenAI API key
- **Sync**: No (set manually)

### Optional (already in render.yaml):
- **Key**: `PYTHON_VERSION`
- **Value**: `3.10.0`
- **Key**: `ENVIRONMENT`
- **Value**: `production`

**Note**: Since S3 is disabled, you don't need AWS credentials.

---

## Step 5: Deploy

1. **Render will automatically start building**
2. **Watch the build logs** in the Render dashboard
3. **Build time**: ~2-3 minutes
4. **First deployment**: May take 5-10 minutes

### What to Watch For:

✅ **Build Success**: "Build successful"
✅ **Service Started**: "Your service is live at..."
✅ **Health Check**: Should show healthy status

---

## Step 6: Test Your Deployment

Once deployed, you'll get a URL like: `https://vat-analysis-api.onrender.com`

### 1. Health Check
```bash
curl https://your-app-name.onrender.com/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "message": "VAT Analysis API is running"
}
```

### 2. API Documentation
Open in browser:
```
https://your-app-name.onrender.com/docs
```

### 3. Test Process Invoices
```bash
curl -X POST "https://your-app-name.onrender.com/process-invoices" \
  -H "X-User-ID: test123" \
  -H "Content-Type: application/json" \
  -d '[{
    "date": "2025-01-15",
    "type": "Sales",
    "net_amount": 1000.00,
    "vat_amount": 210.00,
    "vat_percentage": "21",
    "VAT Category (NL) Code": "1a",
    "VAT Category (NL) Description": "Sales taxed at standard rate (21%)",
    "file_name": "test_invoice.pdf",
    "customer_name": "Test Customer",
    "country": "NL"
  }]'
```

---

## ✅ Deployment Checklist

- [ ] Code pushed to Git repository
- [ ] Render account created
- [ ] Web service created on Render
- [ ] Environment variables set (if needed)
- [ ] Build successful
- [ ] Service is live
- [ ] Health check passes
- [ ] API docs accessible

---

## 📝 Important Notes

### Free Tier Limitations

⚠️ **Spinning Down**: 
- Free services spin down after **15 minutes** of inactivity
- First request after spin-down takes **30-60 seconds** (cold start)
- Perfect for testing and development

### Production Recommendations

1. **Upgrade to Paid Plan**: 
   - Avoids spin-downs
   - Better performance
   - More resources

2. **Update CORS** (if you have a frontend):
   ```python
   # In app.py, line 24
   allow_origins=["https://your-frontend-domain.com"],  # Replace "*"
   ```

3. **Add Database** (for persistent storage):
   - Render offers managed PostgreSQL
   - Current in-memory storage is lost on restart

4. **Environment Variables**:
   - Keep sensitive keys in Render dashboard
   - Never commit API keys to Git

---

## 🐛 Troubleshooting

### Build Fails

**Problem**: Build command fails
**Solution**:
- Check build logs in Render dashboard
- Verify `requirements.txt` has all dependencies
- Ensure Python version in `runtime.txt` is compatible

### Service Won't Start

**Problem**: Service shows "Failed" status
**Solution**:
- Check logs in Render dashboard
- Verify start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- Ensure `app.py` is in root directory
- Check for import errors in logs

### 502 Bad Gateway

**Problem**: Service returns 502 error
**Solution**:
- Service might be spinning up (free tier)
- Wait 30-60 seconds and try again
- Check service logs for errors

### CORS Errors

**Problem**: Frontend can't access API
**Solution**:
- Update CORS in `app.py` to allow your frontend domain
- Restart service after changes

### Environment Variables Not Working

**Problem**: Variables not accessible
**Solution**:
- Verify variables are set in Render dashboard → Environment tab
- Restart service after adding variables
- Check variable names match exactly (case-sensitive)

---

## 📊 Your API Endpoints (After Deployment)

Base URL: `https://your-app-name.onrender.com`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/docs` | GET | API documentation (Swagger UI) |
| `/process-invoices` | POST | Process invoice data |
| `/vat-report-quarterly` | GET | Quarterly VAT report |
| `/vat-report-monthly` | GET | Monthly VAT report |
| `/vat-report-yearly` | GET | Yearly VAT report |
| `/dreport` | GET | Dutch tax format report |
| `/company-details` | POST/GET | Company information |
| `/vat-payable` | GET | Calculate VAT payable |
| `/clear-user-data` | DELETE | Clear user data |

---

## 🔄 Updating Your Deployment

After making code changes:

1. **Commit and push to Git**:
   ```bash
   git add .
   git commit -m "Update code"
   git push
   ```

2. **Render automatically detects changes** and redeploys
3. **Monitor deployment** in Render dashboard
4. **Test** after deployment completes

---

## 🎉 Success!

Your VAT Analysis API is now live on Render!

**Next Steps**:
- Test all endpoints
- Share API URL with your frontend team
- Monitor usage in Render dashboard
- Consider upgrading for production use

---

## 📞 Need Help?

1. **Check Render Logs**: Dashboard → Your Service → Logs
2. **Render Documentation**: https://render.com/docs
3. **Review Project Docs**: See `COMPLETE_DOCUMENTATION.md`

---

## 🚀 Quick Commands Reference

```bash
# Health check
curl https://your-app-name.onrender.com/health

# Process invoices
curl -X POST "https://your-app-name.onrender.com/process-invoices" \
  -H "X-User-ID: 369" \
  -H "Content-Type: application/json" \
  -d @test_inputs_minimal.json

# Get quarterly report
curl -X GET "https://your-app-name.onrender.com/vat-report-quarterly?year=2025&quarter=Q1" \
  -H "X-User-ID: 369"

# View API docs
open https://your-app-name.onrender.com/docs
```

---

**Good luck with your deployment!** 🎉

