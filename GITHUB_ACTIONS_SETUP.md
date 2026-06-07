# Instructions for Automatic Deployment (Optional)

You can set up GitHub Actions to automatically deploy your application whenever you push to the main branch.

## Option A: Manual Deploy (Recommended for First Time)

Follow the steps in **QUICK_START_DEPLOYMENT.md** - it's simple and only takes 15 minutes.

## Option B: GitHub Actions Auto-Deploy

This will automatically redeploy when you push changes to GitHub.

### For Backend (Render)

1. Go to https://render.com/account/api-tokens
2. Create an API Token → **Copy it**
3. Go to GitHub → Your Repo → Settings → Secrets and Variables → Actions
4. Click **"New repository secret"**
   - Name: `RENDER_API_KEY`
   - Value: (paste the token)
5. Create `.github/workflows/render-deploy.yml`:

```yaml
name: Deploy Backend to Render

on:
  push:
    branches:
      - main
    paths:
      - 'backend/**'
      - 'render.yaml'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Render
        run: |
          curl -X POST https://api.render.com/v1/services/your-service-id/deploys \
            -H "authorization: Bearer ${{ secrets.RENDER_API_KEY }}" \
            -d "gitCommitSha=${{ github.sha }}"
```

### For Frontend (Vercel)

1. Go to https://vercel.com/account/tokens
2. Create Token → **Copy it**
3. Go to GitHub → Settings → Secrets → Add Secret
   - Name: `VERCEL_TOKEN`
   - Value: (paste the token)
4. Create `.github/workflows/vercel-deploy.yml`:

```yaml
name: Deploy Frontend to Vercel

on:
  push:
    branches:
      - main
    paths:
      - 'frontend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: vercel/action@main
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          scope: ${{ secrets.VERCEL_ORG_ID }}
```

## Getting Vercel IDs

After deploying on Vercel manually:

1. Run: `npm i -g vercel`
2. Run: `vercel link` in the frontend folder
3. Get the IDs from `.vercel/project.json`

---

**For now, stick with manual deployment.** Auto-deploy can be set up later.
