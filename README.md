# Vehicle Damage Detection and Insurance Cost Estimation

An end-to-end web application for vehicle damage assessment from claim images. The system follows the project paper architecture:

`User Image -> Preprocessing -> RT-DETR-L Damage Detection -> Severity Analysis -> Cost Estimation -> Web Result`

The backend uses the trained RT-DETR checkpoint at `backend/models/best.pt`. The frontend provides account creation, login, claim upload, saved claim history, a blue insurance-company admin dashboard, annotated detection output, severity score, preprocessing audit, itemized repair estimate, review recommendation, and printable claim reports.

## Project Goal

Manual vehicle damage inspection is slow, subjective, and hard to scale for digital insurance claims. This project automates the first assessment step by detecting visible damage regions, estimating severity from spatial area and confidence, and mapping those results to an explainable repair-cost range.

The uploaded paper describes a data-centric RT-DETR-L framework trained on a refined VehiDE-derived dataset:

- Removed inconsistent/mislabeled classes.
- Filtered noisy and invalid annotations.
- Balanced six damage categories with targeted augmentation.
- Used preprocessing for real-world image issues such as low light, overexposure, blur, and noise.
- Reported RT-DETR-L performance: precision `0.84`, recall `0.63`, and `mAP50 0.71`.

## Damage Classes

The deployed checkpoint exposes these six classes:

- `broken_glass`
- `dent`
- `paint_damage`
- `missing_part`
- `scratch`
- `deformation`

## Current Runtime Architecture

```text
frontend/
  React claim assessment UI

backend/
  app/main.py                         FastAPI application and CORS setup
  app/routes/auth.py                  Register, login, logout, and session user APIs
  app/routes/claims.py                Saved claim history, detail, and review status APIs
  app/routes/predict.py               Upload endpoint
  app/services/auth.py                Password hashing and bearer-token sessions
  app/services/claims.py              Claim persistence helpers
  app/services/database.py            SQLite schema and connection helpers
  app/services/preprocessing.py       Real-world image preprocessing
  app/services/damage_detection.py    RT-DETR inference and annotation
  app/services/cost.py                Severity and repair-cost rules
  app/utils/image_utils.py            Base64 response image encoder
  models/best.pt                      Trained RT-DETR model
```

Training/conversion code was removed from the runtime source path. Dataset folders were left untouched because they may contain valuable training artifacts.

## Professional Workflow Added

The project now behaves like a real claim-assessment portal instead of a single image demo.

- Users can create an account and log in.
- Passwords are stored as salted PBKDF2 hashes.
- Login sessions use random bearer tokens.
- Every logged-in prediction is saved as a claim.
- Users can view claim history.
- Users can open a saved claim report.
- Reports can be printed or saved as PDF from the browser.
- Admin dashboard shows claim trend, status counts, damage-category counts, detail table, and global filters.
- Claims include status, severity, estimate, detections, preprocessing audit, and annotated image.
- High-risk cases are flagged for manual surveyor review.

Default claim status:

```text
AI Assessed
```

Supported review statuses in the backend:

```text
AI Assessed -> Needs Review -> Approved / Rejected
```

## Backend Logic

### 1. Image Validation

The API accepts `JPG`, `PNG`, and `WEBP` images under `12 MB`. Images below `320x240` are rejected because very small claim images are not reliable for visual damage assessment.

### 2. Preprocessing

Implemented in `backend/app/services/preprocessing.py`.

Before inference, the uploaded image is normalized using practical computer-vision rules:

- Converts input to safe `BGR uint8`.
- Resizes only very large images to a max long edge of `1920 px`.
- Applies gray-world white balance to reduce color cast.
- Applies gamma correction for dark or overexposed photos.
- Applies CLAHE on the luminance channel when contrast is low.
- Uses mild denoising when sensor/compression noise is high.
- Uses mild unsharp masking when blur score is low.
- Returns a preprocessing audit in the API response.

This matches the paper’s requirement to handle real-world claim-photo issues before passing the image into the model.

### 3. Detection

Implemented in `backend/app/services/damage_detection.py`.

- Loads `backend/models/best.pt` through Ultralytics.
- Runs prediction with `imgsz=768`, matching the paper’s fixed training resolution.
- Uses confidence threshold `0.25`.
- Returns bounding boxes, class names, confidence, per-box area ratio, total damage-area ratio, model metadata, and annotated image.

### 4. Severity Analysis

Implemented in `backend/app/services/cost.py`.

Severity is calculated from:

- Total union area of detected boxes.
- Average model confidence.
- Damage class weight.
- Number of detected damages.

Labels:

- `None`
- `Minor`
- `Moderate`
- `Major`
- `Severe`

### 5. Cost Estimation

The estimator is rule-based and explainable. It is designed for a sales/demo product for insurance companies, so it does not pretend to know hidden OEM part prices from one image. It combines:

- Detected damage type.
- Selected car model.
- Selected or automatically resolved damage category.
- Severity multiplier.
- Area multiplier.
- Confidence multiplier.
- Workshop type: `independent`, `standard`, `authorized`.
- Multiple-damage multiplier.
- Manual-review rules for severe, low-confidence, or high-value claims.

The output is an INR range plus line-item estimates for each detected damage. It is designed as insurance decision support, not final claim approval.

Large detector boxes are strongly capped during cost calculation. This avoids unrealistic demo output from one uploaded image. The estimator only uses the six trained RT-DETR damage categories, not unrelated part names.

## Cost Rule Examples

Damage-category ranges used by the demo estimator:

| Damage category | Base INR range |
| --- | ---: |
| Scratch | 1,500 - 7,000 |
| Paint damage | 2,500 - 12,000 |
| Dent | 4,000 - 18,000 |
| Broken glass | 5,000 - 30,000 |
| Missing part | 7,000 - 45,000 |
| Deformation | 8,000 - 50,000 |

Demo car models included:

- Maruti Suzuki Swift
- Hyundai i20
- Tata Altroz
- Maruti Suzuki Baleno
- Honda Amaze
- Hyundai Verna
- Honda City
- Skoda Slavia
- Tata Nexon
- Hyundai Creta
- Kia Seltos
- Mahindra XUV700
- Toyota Innova Crysta
- MG Hector
- Jeep Compass
- BMW 3 Series
- Mercedes-Benz C-Class
- Audi A4

These are intentionally configurable in code because real repair costs vary by city, vehicle brand, part availability, insurance policy, and workshop type.

## API

### Health Check

```bash
GET http://127.0.0.1:8000/
```

Returns:

```json
{
  "status": "ok",
  "model": "RT-DETR-L custom best.pt",
  "pipeline": ["preprocessing", "damage detection", "severity analysis", "cost estimation"]
}
```

### Predict

```bash
POST http://127.0.0.1:8000/api/predict
```

Form data:

- `file`: vehicle image.
- `vehicle_segment`: optional, default `sedan`.
- `workshop_type`: optional, default `standard`.
- `car_model`: optional, default `maruti_swift`.
- `damage_category`: optional, default `auto`. Allowed values: `auto`, `broken_glass`, `dent`, `paint_damage`, `missing_part`, `scratch`, `deformation`.
- `Authorization`: optional `Bearer <token>`. If present, the prediction is saved as a claim.

Example response fields:

```json
{
  "damage_detected": true,
  "num_damages": 3,
  "damage_types": ["broken_glass", "deformation", "paint_damage"],
  "damage_area_ratio": 0.65736,
  "severity": "Severe",
  "severity_score": 100,
  "estimated_cost_range": "INR 10,000 - INR 18,500",
  "detections": [],
  "cost_breakdown": {},
  "preprocessing": {},
  "model": {},
  "annotated_image": "base64-jpeg"
}
```

For demo admin access, register using:

```text
admin@demo.com
```

That account is assigned the `admin` role and can view all saved claims in the admin dashboard.

### Auth

Register:

```bash
POST http://127.0.0.1:8000/api/auth/register
```

```json
{
  "full_name": "Student User",
  "email": "student@example.com",
  "password": "secret123"
}
```

Login:

```bash
POST http://127.0.0.1:8000/api/auth/login
```

```json
{
  "email": "student@example.com",
  "password": "secret123"
}
```

Both return:

```json
{
  "token": "bearer-token",
  "user": {
    "id": 1,
    "full_name": "Student User",
    "email": "student@example.com",
    "role": "customer"
  }
}
```

### Claims

List saved claims:

```bash
GET http://127.0.0.1:8000/api/claims
Authorization: Bearer <token>
```

Open one saved claim:

```bash
GET http://127.0.0.1:8000/api/claims/{claim_id}
Authorization: Bearer <token>
```

## Frontend

Implemented in `frontend/src/App.js` and `frontend/src/App.css`.

The UI includes:

- Login and account creation.
- Vehicle image upload and preview.
- Car model selector with 18 demo models.
- Damage category selector aligned with the six trained model classes.
- Vehicle segment selector.
- Workshop type selector.
- Blue admin dashboard inspired by insurance claims BI dashboards.
- Claim snapshot metrics.
- Annotated model output.
- Detection table with confidence, area, and cost per damage.
- Preprocessing audit showing applied enhancement steps.
- Saved claim history.
- Printable/savable report page.
- Manual-review recommendation.

## Setup From Start

### 1. Open Project

```bash
cd "C:\Users\srira\Downloads\vehicle damage and insurance system"
```

### 2. Backend Environment

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

The required model must exist here:

```text
backend/models/best.pt
```

### 3. Start Backend

```bash
cd "C:\Users\srira\Downloads\vehicle damage and insurance system\backend"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend URL:

```text
http://127.0.0.1:8000
```

The backend creates this local SQLite database automatically:

```text
backend/data/insurance_app.db
```

### 4. Frontend Install

```bash
cd "C:\Users\srira\Downloads\vehicle damage and insurance system\frontend"
npm install
```

### 5. Start Frontend

```bash
npm start
```

Frontend URL:

```text
http://127.0.0.1:3000
```

Create an account from the login screen, upload a damaged vehicle image, and the claim will be saved into claim history automatically.

## Free Deployment Guide

This is not a static-only project. It has two parts:

- React frontend: can be hosted on Vercel, Netlify, or GitHub Pages.
- FastAPI backend with RT-DETR model: must run on a Python web service such as Render, Railway, or Hugging Face Spaces.

The React `index.html` already exists here:

```text
frontend/public/index.html
```

After building, the production file is generated here:

```text
frontend/build/index.html
```

### Recommended Free Setup

Use this split:

- Backend: Render free web service.
- Frontend: Vercel or Netlify free static site.

### Deploy Backend On Render

1. Push this project to GitHub.
2. Create a free hosted Postgres database first. Supabase or Neon are good demo choices.
3. Copy the Postgres connection string.
4. Go to Render and create a new Web Service.
5. Select the GitHub repo.
6. Use these settings:

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Or use the included root-level `render.yaml`.

Set these Render environment variables:

```text
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app,https://your-frontend-domain.netlify.app
```

For local development, you can leave `DATABASE_URL` empty. The backend will use local SQLite at `backend/data/insurance_app.db`.

For deployment, do not rely on local SQLite. Free web-service filesystems are usually temporary, so saved users and claims can disappear after restart/redeploy.

### Deploy Frontend On Vercel

1. Import the same GitHub repo in Vercel.
2. Set root directory to:

```text
frontend
```

3. Build command:

```text
npm run build
```

4. Output directory:

```text
build
```

5. Add environment variable:

```text
REACT_APP_API_BASE=https://your-render-backend.onrender.com/api
```

### Deploy Frontend On Netlify

Use these settings:

```text
Base directory: frontend
Build command: npm run build
Publish directory: frontend/build
```

The file `frontend/public/_redirects` is included so React routes work after refresh.

### GitHub Push Notes

Do not push dependency folders or local generated files. The root `.gitignore` excludes:

- `node_modules`
- `venv`
- local SQLite DB
- caches
- training folders such as `datasets`, `runs`, and `yolo_data`

The trained model `backend/models/best.pt` is about 66 MB, which is below GitHub's 100 MB single-file limit. If GitHub rejects it later, use Git LFS or host the model separately.

## Deployment Problems To Avoid

- **Local SQLite on hosted backend**: not safe for deployed data. Use `DATABASE_URL` with Supabase/Neon/Postgres.
- **CORS blocked frontend**: add your frontend domain to `ALLOWED_ORIGINS`.
- **Frontend cannot find backend**: set `REACT_APP_API_BASE=https://your-backend-domain/api` before building/deploying frontend.
- **Model file too large**: `best.pt` is currently under GitHub's 100 MB limit. If a future model is larger, use Git LFS or external model storage.
- **Free backend sleeps**: Render/Railway-style free services may sleep. First request can be slow.
- **Supabase/Neon free limits**: free database projects may pause after inactivity or have storage/compute limits. Good for demo, not final production.
- **Uploaded images in DB**: the demo stores base64 annotated images in DB for simplicity. For production, store images in object storage such as Supabase Storage, S3, or Cloudinary and save only URLs.
- **Secrets in repo**: never commit `.env`, database passwords, or service keys. Use host environment variables.

## Verification Commands

Backend import/model check:

```bash
cd backend
python -c "from app.services.damage_detection import MODEL; print(MODEL.names)"
```

Backend API test:

```bash
cd backend
python -c "from fastapi.testclient import TestClient; from app.main import app; c=TestClient(app); f=open(r'..\test_images\sample.jpg','rb'); r=c.post('/api/predict', files={'file':('sample.jpg', f, 'image/jpeg')}); print(r.status_code); print(r.json()['estimated_cost_range'])"
```

Damage-category sanity test:

```bash
cd backend
python -c "from fastapi.testclient import TestClient; from app.main import app; c=TestClient(app); f=open(r'..\test_images\sample.jpg','rb'); r=c.post('/api/predict', files={'file':('sample.jpg', f, 'image/jpeg')}, data={'car_model':'maruti_swift','damage_category':'scratch','vehicle_segment':'hatchback','workshop_type':'standard'}); print(r.status_code); print(r.json()['estimated_cost_range'], r.json()['severity'])"
```

Auth + saved claim test:

```bash
cd backend
python -c "from fastapi.testclient import TestClient; from app.main import app; import time; c=TestClient(app); email=f'user{int(time.time())}@test.com'; r=c.post('/api/auth/register', json={'full_name':'Test User','email':email,'password':'secret123'}); token=r.json()['token']; headers={'Authorization':f'Bearer {token}'}; f=open(r'..\test_images\sample.jpg','rb'); p=c.post('/api/predict', headers=headers, files={'file':('sample.jpg', f, 'image/jpeg')}); print(p.status_code, p.json()['claim']); print(c.get('/api/claims', headers=headers).status_code)"
```

Frontend build test:

```bash
cd frontend
npm run build
```

## Verified Locally

The project was checked with:

- Backend model import: passed.
- Direct preprocessing + RT-DETR + cost estimation on `test_images/sample.jpg`: passed.
- FastAPI `/api/predict` test request: returned `200`.
- Register -> authenticated prediction -> saved claim history -> claim detail: returned `200`.
- Damage-category pricing sanity checks passed for the six trained classes.
- React production build: compiled successfully.
- Backend health check: returned `status: ok`.
- Frontend dev server: running at `http://127.0.0.1:3000`.

## Important Notes

- The cost estimator is not a replacement for a licensed insurance surveyor.
- Single-image analysis cannot detect hidden frame, sensor, suspension, chassis, or ADAS calibration damage.
- Estimates should be calibrated with real insurer/body-shop invoices before production use.
- Very small, blurry, occluded, reflective, or poorly cropped images may reduce detection quality.

## Research References Used

- Project PDF: `Accident_damage_detection_and_cost_estimation.pdf`
- Ultralytics RT-DETR documentation: https://docs.ultralytics.com/models/rtdetr/
- OpenCV CLAHE documentation: https://docs.opencv.org/3.4/d6/dc7/group__imgproc__hist.html
- 2026 India denting/painting market range reference: https://www.ridenrepair.com/blog-details/car-denting-painting-cost-india-2026-full-breakdown
