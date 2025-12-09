# Render Deployment Checklist ✅

## Pre-Deployment

- [ ] Code is working locally
- [ ] All files committed to Git
- [ ] Pushed to GitHub/GitLab/Bitbucket
- [ ] Render account created (https://render.com)

## Files Verification

- [x] `app.py` exists
- [x] `requirements.txt` exists
- [x] `Procfile` exists (correct)
- [x] `render.yaml` exists (updated)
- [x] `runtime.txt` exists

## Deployment Steps

### Step 1: Create Service on Render
- [ ] Go to https://dashboard.render.com
- [ ] Click "New +" → "Blueprint" (or "Web Service")
- [ ] Connect your Git repository
- [ ] Review configuration
- [ ] Click "Create" or "Apply"

### Step 2: Configure Environment Variables
- [ ] Go to service → Environment tab
- [ ] Add `OPENAI_API_KEY` (if using OpenAI features)
- [ ] Verify `PYTHON_VERSION` is set (3.10.0)

### Step 3: Deploy
- [ ] Wait for build to complete (~2-3 minutes)
- [ ] Check build logs for errors
- [ ] Verify service status is "Live"

### Step 4: Test
- [ ] Test health endpoint: `GET /health`
- [ ] Open API docs: `/docs`
- [ ] Test process invoices endpoint
- [ ] Test report generation endpoint

## Post-Deployment

- [ ] Save your API URL
- [ ] Test all endpoints
- [ ] Update frontend with API URL (if applicable)
- [ ] Monitor logs for any issues

## Your API URL

After deployment, your API will be at:
```
https://vat-analysis-api.onrender.com
```

(Or your custom name if you changed it)

## Quick Test Commands

```bash
# Health check
curl https://your-app-name.onrender.com/health

# View docs
open https://your-app-name.onrender.com/docs
```

---

**Need help?** See `DEPLOY_TO_RENDER.md` for detailed instructions.

