# 🤖 AI Customer Support Pipeline

Automated email classification system that fetches customer support emails from Gmail, classifies them using OpenAI, stores them in Notion, and sends daily digests to Slack.

## 🌟 Features

- **Gmail Integration**: Automatically fetch support emails
- **AI Classification**: Uses OpenAI GPT-4 to categorize and prioritize issues
- **Notion Database**: Store and organize all support tickets
- **Slack Notifications**: Daily digest of support metrics
- **Web Dashboard**: Monitor and control the pipeline
- **Automated Scheduling**: Runs daily at 9 AM automatically

## 🏗️ Architecture

```
Gmail → OpenAI (Classification) → Notion (Storage) → Slack (Reporting)
                    ↓
            Flask Web Dashboard
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Gmail account with API access
- OpenAI API key
- Notion workspace
- Slack workspace

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd customer-support-pipeline
```

2. **Create virtual environment**
```bash
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

5. **Set up Gmail OAuth**
   - Download `credentials.json` from Google Cloud Console
   - Place it in project root
   - Run: `python orchestrator.py` to authenticate

6. **Run the application**
```bash
python app.py
```

Visit `http://localhost:5000` to see the dashboard!

## 📋 Configuration

### Environment Variables

Create a `.env` file with:

```env
OPENAI_API_KEY=sk-proj-your-key-here
NOTION_TOKEN=secret_your-token-here
NOTION_DATABASE_ID=your-database-id-here
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Gmail Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download as `credentials.json`

### Notion Setup

1. Create a Notion integration at [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Create a database with these properties:
   - **Title** (Title)
   - **Description** (Text)
   - **Category** (Select: Hardware, Software, Network, User Error, Security, Other)
   - **Priority** (Select: Critical, High, Medium, Low)
   - **Status** (Select: New, In Progress, Resolved)
   - **Sender** (Email)
   - **Date** (Date)
3. Share the database with your integration
4. Copy the database ID from the URL

### Slack Setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Create a new app
3. Enable Incoming Webhooks
4. Add webhook to a channel
5. Copy the webhook URL

## 🎮 Usage

### Web Dashboard

Access the dashboard at `http://localhost:5000`

**Features:**
- **Fetch Emails**: Test Gmail connection
- **Run Full Pipeline**: Process all new emails
- **Send Slack Digest**: Manually trigger digest
- **Refresh Status**: Update dashboard stats

### API Endpoints

- `GET /` - Dashboard
- `GET /health` - Health check
- `GET /api/status` - Get pipeline status
- `POST /api/fetch` - Fetch emails (body: `{hours: 24}`)
- `POST /api/classify` - Classify single email
- `POST /api/run-pipeline` - Run full pipeline (body: `{hours: 24}`)
- `POST /api/send-digest` - Send Slack digest

### Command Line

Run the pipeline directly:
```bash
python orchestrator.py
```

## 📅 Scheduling

The pipeline automatically runs daily at 9 AM. To change:

Edit `app.py`:
```python
scheduler.add_job(func=scheduled_job, trigger="cron", hour=17, minute=0)  # 5 PM
```

## 🚢 Deployment

### Railway

1. Create account at [railway.app](https://railway.app)
2. Connect your GitHub repository
3. Add environment variables in Railway dashboard
4. Deploy automatically on push

### Render

1. Create account at [render.com](https://render.com)
2. Create new Web Service from GitHub
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `gunicorn app:app --timeout 120`
5. Add environment variables
6. Deploy

**Important**: Upload `token.json` after first local authentication.

## 🐛 Troubleshooting

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### "Gmail authentication failed"
1. Delete `token.json`
2. Run `python orchestrator.py`
3. Complete OAuth flow

### "Notion database not found"
1. Check `NOTION_DATABASE_ID` in `.env`
2. Ensure integration has database access
3. Verify database properties match code

### "Duplicate emails processed"
Delete `processed_emails.json` to reset tracking.

## 🔒 Security

- Never commit `.env`, `credentials.json`, or `token.json`
- Regenerate OAuth credentials if exposed
- Use environment variables for all secrets
- Add authentication to production deployments

## 📊 Project Structure

```
customer-support-pipeline/
├── app.py                      # Flask web application
├── orchestrator.py             # Main pipeline logic
├── requirements.txt            # Python dependencies
├── Procfile                    # Deployment configuration
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── templates/
│   └── index.html             # Web dashboard
├── credentials.json           # Gmail OAuth (not in git)
├── token.json                 # Gmail token (not in git)
└── processed_emails.json      # Tracking file (not in git)
```

## 🧪 Testing

Test individual components:

```python
# Test Gmail
from orchestrator import authenticate_gmail, fetch_customer_emails
service = authenticate_gmail()
emails = fetch_customer_emails(service, 24)

# Test Classification
from orchestrator import classify_issue
result = classify_issue("App crashes", "The app won't open")

# Test Notion
from orchestrator import get_notion_summary
summary = get_notion_summary()

# Test Slack
from orchestrator import send_slack_digest
send_slack_digest(summary)
```

## 📝 License

MIT License - feel free to use for your projects!

## 🤝 Contributing

Issues and pull requests welcome!

## 📧 Support

For issues, please check:
1. Server logs
2. Environment variables
3. API credentials validity
4. Documentation above