# 🔧 Troubleshooting Guide

## Common Deployment Issues & Fixes

### ❌ Backend Won't Build on Render

**Error in logs:**
```
ModuleNotFoundError: No module named 'xxx'
```

**Solution:**
1. Check that all imports in `backend/app/` have corresponding packages in `requirements.txt`
2. Add missing package:
   ```
   echo "missing-package" >> backend/requirements.txt
   git add backend/requirements.txt
   git commit -m "Add missing dependency"
   git push
   ```
3. Manually redeploy on Render dashboard

**Common missing packages:**
- `python-dotenv` - For .env files ✓ Already added
- `sqlalchemy` - For database ORM ✓ Already added
- `aiofiles` - For async file handling
- `python-jose` - For JWT tokens

---

### ❌ Frontend Won't Build on Vercel

**Error in logs:**
```
npm ERR! Missing required argument: script
npm ERR! Did you mean this?
```

**Solution:**
1. Verify `frontend/package.json` has build script:
   ```json
   "scripts": {
     "build": "react-scripts build",
     ...
   }
   ```
2. If missing, re-run: `npm install` in frontend folder
3. Check all dependencies are in `package.json` (React, React-DOM, React-Scripts)

---

### ❌ "Cannot reach backend" Error on Frontend

**You see:**
```
Cannot reach backend at https://vehicle-damage-insurance-api.onrender.com/api
Start the backend locally or set REACT_APP_API_BASE for deployment.
```

**Solutions (in order):**

1. **Check Backend is Running**
   - Visit: `https://vehicle-damage-insurance-api.onrender.com/`
   - Should see JSON response with status "ok"
   - If 404 or timeout → Backend not running

2. **Check REACT_APP_API_BASE on Vercel**
   - Vercel dashboard → Your project → Settings → Environment Variables
   - Look for `REACT_APP_API_BASE`
   - Should be: `https://vehicle-damage-insurance-api.onrender.com/api`
   - If missing or wrong → Add/fix it and redeploy

3. **Cold Start Delay (Free Tier)**
   - First request might take 30 seconds on free tier
   - Wait, then try again
   - Solution: Upgrade to paid tier or use pro tier

4. **Clear Browser Cache**
   - Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
   - Or open in private/incognito window

---

### ❌ CORS Errors

**You see in browser console:**
```
Access to XMLHttpRequest at 'https://...' from origin 'https://your-app.vercel.app' 
has been blocked by CORS policy
```

**Solution:**
1. Go to Render dashboard → Your Backend Service → Environment
2. Find `ALLOWED_ORIGINS` variable
3. Update to include your Vercel URL:
   ```
   ALLOWED_ORIGINS=https://your-app.vercel.app,http://localhost:3000
   ```
4. Save and click "Manual Deploy" to restart service
5. Wait 2 minutes, then refresh browser

**Quick test:**
```bash
# From your browser console, run:
fetch('https://your-backend.onrender.com/', {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json'
  }
}).then(r => r.json()).then(console.log)
```

---

### ❌ Image Upload Fails with 413 Error

**Error:**
```
413 Payload Too Large
```

**Solution:**
- Vercel max upload: 4.5 MB
- Render max upload: 100 MB (usually)
- Reduce image size before upload
- Or update FastAPI request size limit:

In `backend/app/main.py`:
```python
app = FastAPI(max_upload_size=104857600)  # 100 MB
```

---

### ❌ Database Connection Fails

**Error in Render logs:**
```
psycopg2.OperationalError: could not connect to server
```

**Solutions:**

1. **Check DATABASE_URL is Set**
   - Render dashboard → Your Backend → Environment
   - `DATABASE_URL` should be populated
   - If empty, manually paste from your database service

2. **Check Database Service is Running**
   - Render dashboard → Your Database → Status
   - Should show "Available"

3. **Verify Connection String Format**
   - Should look like: `postgresql://user:pass@host:5432/dbname`
   - No special characters that need escaping

4. **Wait for Database to Initialize**
   - New database takes 1-2 minutes to be ready
   - Try redeploying backend after waiting

---

### ❌ React App Shows "Connection Refused"

**Error:**
```
ECONNREFUSED: Connection refused at 127.0.0.1:8000
```

**Cause:** Frontend is trying to connect to localhost backend

**Solution:**
1. `frontend/.env.local` uses `http://localhost:8000/api` (This is correct for development)
2. But `.env.production` must have your Render URL:
   ```
   REACT_APP_API_BASE=https://vehicle-damage-insurance-api.onrender.com/api
   ```
3. Vercel automatically uses `.env.production` on deployment
4. For local development, `.env.local` is used (only in dev mode)

---

### ❌ Blank Page on Vercel

**You see:** Just a white screen, no errors

**Solutions:**

1. **Check Browser Console for Errors**
   - Press F12 → Console tab
   - Look for red errors
   - Take action based on error type

2. **Check Build Logs**
   - Vercel dashboard → Deployments → Click latest
   - Look for "Build failed" or warnings
   - Scroll to see the actual error

3. **Check if React-Scripts is Installed**
   - `frontend/package.json` should have: `"react-scripts": "5.0.1"`
   - If using `create-react-app`, verify all deps are there

4. **Hard Refresh**
   - Press `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
   - Clear cache and reload

---

### ❌ "Port Already in Use" Error (Local Development)

**Error when running locally:**
```
Address already in use: ('0.0.0.0', 8000)
```

**Solutions:**

1. **Kill the Process**
   ```bash
   # Find process on port 8000
   lsof -i :8000
   
   # Kill it (Windows - use Task Manager)
   # Or on Linux/Mac:
   kill -9 <PID>
   ```

2. **Use Different Port**
   ```bash
   uvicorn app.main:app --port 8001
   # Then update frontend .env.local:
   # REACT_APP_API_BASE=http://localhost:8001/api
   ```

---

## Quick Verification Checklist

Before asking for help, verify:

- [ ] Backend URL returns JSON when visited in browser
- [ ] Frontend URL loads without errors
- [ ] `REACT_APP_API_BASE` is set on Vercel
- [ ] `ALLOWED_ORIGINS` includes your Vercel URL on Render
- [ ] Browser console has no errors (F12 → Console)
- [ ] Render/Vercel logs show successful deployments (no errors)
- [ ] You waited 2+ minutes after making changes

---

## Getting Help

If issues persist:

1. **Check Logs**
   - Render: Dashboard → Service → Logs → View logs
   - Vercel: Dashboard → Project → Deployments → View build logs

2. **Copy Full Error Message**
   - Don't summarize - include complete error
   - Include what you were trying to do

3. **Check Configuration**
   - List all environment variables being used
   - Paste the exact URLs you're using

4. **Try Redeploying**
   - Sometimes a fresh deploy fixes transient issues
   - Click "Manual Deploy" on Render
   - Click "Redeploy" on Vercel

---

## Still Stuck?

Review these files in order:
1. `QUICK_START_DEPLOYMENT.md` - Quick start guide
2. `DEPLOYMENT_GUIDE.md` - Comprehensive guide  
3. `README_DEPLOYMENT.md` - Visual overview
4. This file - Troubleshooting

If none of these help, check the official docs:
- Render: https://render.com/docs
- Vercel: https://vercel.com/docs
