# Deploying to Railway.app

## Step 1: Prepare Your Project

Create this folder structure:
```
customer-support-pipeline/
├── app.py
├── orchestrator.py
├── requirements.txt
├── .env
├── templates/
│   └── index.html
├── credentials.json (Gmail OAuth)
└── Procfile
```

## Step 2: Create Procfile

Create a file named `Procfile` (no extension) with this content:
```
web: gunicorn app:app
```

## Step 3: Create Railway Project

1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project"
4. Choose "Deploy from GitHub repo"
5. Select your repository (or create new one)

## Step 4: Add Environment Variables

In Railway dashboard:
1. Click on your project
2. Go to "Variables" tab
3. Add these variables:
   - `OPENAI_API_KEY`
   - `NOTION_TOKEN`
   - `NOTION_DATABASE_ID`
   - `SLACK_WEBHOOK_URL`
   - `PORT` (set to 5000)

## Step 5: Deploy

Railway will automatically deploy when you push to GitHub.

To deploy manually:
1. Install Railway CLI: `npm i -g @railway/cli`
2. Login: `railway login`
3. Link project: `railway link`
4. Deploy: `railway up`

## Step 6: Access Your App

Railway will give you a URL like: `your-app.railway.app`

Visit that URL to see your dashboard!

## Important Notes

- **Gmail OAuth**: The `credentials.json` file cannot be in the repo for security. You'll need to run the authentication locally first, then upload `token.json` to Railway through the dashboard.
- **Free Tier**: Railway gives $5 free credit per month (enough for this app)
- **Logs**: View logs in Railway dashboard under "Deployments"

## Troubleshooting

If deployment fails:
1. Check logs in Railway dashboard
2. Verify all environment variables are set
3. Make sure `requirements.txt` has all dependencies
4. Check that `Procfile` exists and is correct