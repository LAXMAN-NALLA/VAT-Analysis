# Quick Deploy to Render - Step by Step

## 🚀 Quick Start (5 minutes)

### Step 1: Push to GitHub/GitLab/Bitbucket

```bash
# If not already a git repo
git init
git add .
git commit -m "Ready for Render deployment"

# Push to your Git provider
git remote add origin <your-repo-url>
git push -u origin main
```

### Step 2: Deploy on Render

1. **Go to**: https://dashboard.render.com
2. **Click**: "New +" → "Web Service"
3. **Connect**: Your Git repository
4. **Configure**:
   - **Name**: `vat-analysis-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. **Add Environment Variable** (if using OpenAI):
   - Key: `OPENAI_API_KEY`
   - Value: Your OpenAI API key
6. **Click**: "Create Web Service"

### Step 3: Wait for Deployment

- Build takes ~2-3 minutes
- First deployment may take longer
- Watch the logs in Render dashboard

### Step 4: Test Your API

Once deployed, you'll get a URL like: `https://vat-analysis-api.onrender.com`

**Test it:**
```bash
curl https://vat-analysis-api.onrender.com/health
```

**View API Docs:**
```
https://vat-analysis-api.onrender.com/docs
```

## ✅ Files Created for You

- ✅ `render.yaml` - Render configuration
- ✅ `Procfile` - Process file
- ✅ `runtime.txt` - Python version
- ✅ `.gitignore` - Git ignore file
- ✅ `requirements.txt` - Updated for production

## 📝 Important Notes

### Free Tier
- ⚠️ Service spins down after 15 min inactivity
- ⚠️ First request after spin-down is slow (30-60s)
- ✅ Perfect for testing and development

### Production
- 💰 Upgrade to paid plan to avoid spin-downs
- 💾 Consider adding PostgreSQL for data persistence
- 🔒 Update CORS settings for your frontend domain

## 🐛 Troubleshooting

**Build fails?**
- Check logs in Render dashboard
- Verify all files are committed to git

**Service won't start?**
- Check start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- Verify `app.py` is in root directory

**Environment variables?**
- Add them in Render dashboard → Environment tab
- Restart service after adding

## 📚 Full Documentation

See `RENDER_DEPLOYMENT.md` for complete guide.

## 🎉 You're Done!

Your API is now live at: `https://your-app-name.onrender.com`

