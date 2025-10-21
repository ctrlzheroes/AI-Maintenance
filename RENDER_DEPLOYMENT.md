# Deploying to Render.com

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
└── credentials.json (Gmail OAuth)
```

## Step 2: Push to GitHub

1. Create a GitHub repository
2. Push your code:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

## Step 3: Create Render Account

1. Go to https://render.com
2. Sign up with GitHub
3. Click "New +" button
4. Select "Web Service"

## Step 4: Configure Render Service

Fill in these settings:
- **Name**: `customer-support-pipeline`
- **Region**: Choose closest to you
- **Branch**: `main`
- **Root Directory**: Leave blank
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`

## Step 5: Add Environment Variables

Click "Advanced" and add:
- `OPENAI_API_KEY`: Your OpenAI key
- `NOTION_TOKEN`: Your Notion integration token
- `NOTION_DATABASE_ID`: Your Notion database ID
- `SLACK_WEBHOOK_URL`: Your Slack webhook URL
- `PYTHON_VERSION`: `3.11.0`

## Step 6: Deploy

1. Click "Create Web Service"
2. Wait 5-10 minutes for first deployment
3. Render will give you a URL like: `https://your-app.onrender.com`

## Step 7: Gmail Authentication

Since we can't run OAuth in the cloud easily:

1. Run locally first:
```bash
python orchestrator.py
```

2. This creates `token.json`
3. Upload `token.json` to Render using their file upload feature in dashboard

## Free Tier Notes

- Render free tier sleeps after 15 min of inactivity
- First request after sleep takes 30 seconds to wake up
- 750 hours/month free (enough for this project)

## Troubleshooting

**App won't start?**
- Check logs in Render dashboard
- Verify Python version is 3.11+
- Check all env variables are set

**OAuth errors?**
- Make sure `token.json` is uploaded
- Verify `credentials.json` is in root directory

**Scheduled jobs not running?**
- Free tier apps sleep - upgrade to paid ($7/mo) for 24/7 uptime
- Alternative: Use external cron service to ping your app hourly