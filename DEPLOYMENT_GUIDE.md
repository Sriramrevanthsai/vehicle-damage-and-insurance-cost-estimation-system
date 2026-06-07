# Deployment Guide: Vehicle Damage & Insurance System

This guide covers deploying the backend on **Render** and frontend on **Vercel**.

## Prerequisites

1. **Render Account**: https://render.com
2. **Vercel Account**: https://vercel.com
3. **GitHub Repository**: Project must be pushed to GitHub

## Backend Deployment (Render)

### Step 1: Prepare Your Backend

```bash
# Ensure render.yaml is in root (already done ✓)
# Check backend/requirements.txt is complete (already done ✓)
```

### Step 2: Create PostgreSQL Database on Render

1. Go to https://render.com/dashboard
2. Click "New +" → "PostgreSQL"
3. Fill in details:
   - **Name**: vehicle-damage-db
   - **Region**: Oregon (or your preference)
   - **PostgreSQL Version**: 15
4. Click "Create Database"
5. **Copy the Internal Database URL** (you'll need it)

### Step 3: Deploy from GitHub

1. Go to https://render.com/dashboard
2. Click "New +" → "Web Service"
3. Select "Deploy from GitHub"
4. Choose your repository
5. Fill in:
   - **Name**: vehicle-damage-insurance-api
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
6. Click "Advanced" and set Environment Variables:

```
DATABASE_URL = (paste from Step 2)
ALLOWED_ORIGINS = https://your-vercel-frontend.vercel.app
PYTHONUNBUFFERED = 1
```

7. Click "Create Web Service"
8. **Wait 5-10 minutes** for deployment
9. **Copy your backend URL** (e.g., `https://vehicle-damage-insurance-api.onrender.com`)

### Step 4: Update Backend CORS

Once you know your Vercel frontend URL, update the `ALLOWED_ORIGINS` environment variable on Render:

1. In Render dashboard → Your service → "Environment"
2. Edit `ALLOWED_ORIGINS` to include both URLs:

```
ALLOWED_ORIGINS = https://your-vercel-frontend.vercel.app,http://localhost:3000
```

---

## Frontend Deployment (Vercel)

### Step 1: Update Environment Variables

The frontend files are already configured ✓

- `.env.production` → Production environment
- `.env.local` → Local development (don't commit)

Update `.env.production` with your Render backend URL:

```bash
REACT_APP_API_BASE=https://your-render-backend.onrender.com/api
```

### Step 2: Deploy to Vercel

#### Option A: Manual Deploy via Dashboard

1. Go to https://vercel.com/dashboard
2. Click "Add New..." → "Project"
3. Select your GitHub repository
4. Configure project:
   - **Framework**: React
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`
5. Click "Environment Variables"
6. Add:
   - **Key**: `REACT_APP_API_BASE`
   - **Value**: `https://your-render-backend.onrender.com/api`
7. Click "Deploy"

#### Option B: Deploy via CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
cd frontend
vercel --prod \
  --env REACT_APP_API_BASE=https://your-render-backend.onrender.com/api
```

### Step 3: Verify Deployment

1. Access your Vercel URL
2. Try uploading a vehicle damage image
3. Verify it calls the correct backend API

---

## Common Issues & Solutions

### ❌ "Cannot reach backend" Error

**Solution**: 
- Verify `REACT_APP_API_BASE` environment variable is set correctly in Vercel
- Check Render backend is running: Visit `https://your-backend.onrender.com/`
- Wait a few minutes if Render service just started (free tier is slow to spin up)

### ❌ CORS Error

**Solution**:
- Go to Render dashboard
- Update `ALLOWED_ORIGINS` to include your Vercel domain
- Restart the service: "Manual Deploy" → Re-deploy

### ❌ Build Fails on Render

**Solution**:
- Check that `backend/requirements.txt` has all dependencies
- Look for the error in Render's build logs
- Common fix: Add `python-dotenv` and `sqlalchemy` to requirements.txt (already done ✓)

### ❌ Build Fails on Vercel

**Solution**:
- Check `.env.production` has correct `REACT_APP_API_BASE`
- Verify `frontend/package.json` has all dependencies
- Check build output in Vercel dashboard

---

## Environment Variables Reference

### Backend (Render)

| Variable | Example | Notes |
|----------|---------|-------|
| `DATABASE_URL` | `postgresql://...` | Auto-created by Render database |
| `ALLOWED_ORIGINS` | `https://app.vercel.app` | Your Vercel frontend URL |
| `PYTHONUNBUFFERED` | `1` | Shows logs in real-time |

### Frontend (Vercel)

| Variable | Example | Notes |
|----------|---------|-------|
| `REACT_APP_API_BASE` | `https://api.onrender.com/api` | Your Render backend URL |

---

## Monitoring & Troubleshooting

### Check Backend Logs (Render)

1. Go to your service → "Logs"
2. Look for errors or startup issues

### Check Frontend Logs (Vercel)

1. Go to your project → "Deployments"
2. Click latest deployment → "View Build Logs"

### Test API Endpoint

```bash
# Test backend health
curl https://your-backend.onrender.com/

# Response should be:
# {"status":"ok","model":"RT-DETR-L custom best.pt",...}
```

---

## Performance Tips

- **Cold Starts**: Render free tier services sleep after 15 mins. First request takes ~30s.
- **Database**: Keep database on same region as backend for speed.
- **Build Time**: npm build can take 3-5 mins on free tier. Be patient.

---

## Next Steps

1. Push changes to GitHub
2. Deploy backend first (takes ~10 mins)
3. Note the backend URL
4. Update frontend `.env.production` 
5. Deploy frontend (takes ~5 mins)
6. Test the full application

**Questions?** Check error logs in Render/Vercel dashboards or reach out!
