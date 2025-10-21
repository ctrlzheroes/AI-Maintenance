#!/bin/bash

echo "🚀 Setting up Customer Support Pipeline..."

# Create project directory
mkdir -p customer-support-pipeline
cd customer-support-pipeline

# Create templates folder
mkdir -p templates

# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Create .env file
cat > .env << 'EOF'
# OpenAI API Key
OPENAI_API_KEY=sk-your-openai-api-key-here

# Notion Integration
NOTION_TOKEN=secret_your-notion-integration-token-here
NOTION_DATABASE_ID=your-database-id-here

# Slack Webhook
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Flask
FLASK_ENV=production
PORT=5000
EOF

echo "✅ Project structure created"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

echo "✅ Virtual environment created and activated"

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install flask python-dotenv openai google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client notion-client requests APScheduler gunicorn

echo "✅ Dependencies installed"

# Create requirements.txt
pip freeze > requirements.txt

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy app.py, orchestrator.py, and templates/index.html into this folder"
echo "2. Add your credentials.json (from Google Cloud Console)"
echo "3. Edit .env file with your API keys"
echo "4. Run: python orchestrator.py (to authenticate Gmail)"
echo "5. Run: python app.py (to start the web server)"
echo "6. Visit: http://localhost:5000"
echo ""
echo "To deploy:"
echo "- Railway: railway up"
echo "- Render: Push to GitHub and connect repo"