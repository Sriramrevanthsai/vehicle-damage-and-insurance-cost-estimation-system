# Pre-Deployment Checklist

## Backend (Render) - Ready ✓

- [x] `backend/requirements.txt` - Updated with python-dotenv & sqlalchemy
- [x] `render.yaml` - Complete configuration with database setup
- [x] Health check endpoint `/` - Returns status ✓
- [x] CORS middleware - Configured ✓
- [x] Routes - All three routers registered ✓
  - auth_router
  - claims_router  
  - predict_router

## Frontend (Vercel) - Ready ✓

- [x] `frontend/vercel.json` - Created with proper build config
- [x] `frontend/.env.production` - Created for production API endpoint
- [x] `frontend/.env.local` - Created for local development
- [x] `frontend/package.json` - All dependencies present
- [x] `App.js` - Uses REACT_APP_API_BASE environment variable
- [x] Build command - `npm run build` works

## Deployment Steps

### Before Deploying

1. **Push to GitHub** - Ensure all files are committed
   ```bash
   git add .
   git commit -m "Add deployment configuration for Render & Vercel"
   git push origin main
   ```

2. **Create Accounts**
   - Render: https://render.com
   - Vercel: https://vercel.com

### Deploy Backend (Render)

1. Create PostgreSQL database on Render
2. Copy DATABASE_URL from Render
3. Connect GitHub to Render
4. Set environment variables:
   - DATABASE_URL
   - ALLOWED_ORIGINS=* (initially, update later)
   - PYTHONUNBUFFERED=1
5. Deploy from render.yaml
6. **Copy your backend URL** (e.g., vehicle-damage-insurance-api.onrender.com)
7. Update ALLOWED_ORIGINS with Vercel frontend URL

### Deploy Frontend (Vercel)

1. Update `.env.production` with backend URL
2. Connect GitHub to Vercel
3. Set Root Directory: `frontend`
4. Set environment variable: `REACT_APP_API_BASE=<your-backend-url>/api`
5. Deploy
6. Test the application

## Current Changes Made

✓ `backend/requirements.txt` - Added python-dotenv, sqlalchemy, uvicorn[standard]
✓ `render.yaml` - Updated with complete service and database config
✓ `frontend/vercel.json` - Created with React framework config
✓ `frontend/.env.production` - Created with backend URL placeholder
✓ `frontend/.env.local` - Created for local development
✓ `DEPLOYMENT_GUIDE.md` - Created comprehensive guide
