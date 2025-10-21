"""
Orchestrator module - handles Gmail, OpenAI, Notion, and Slack integrations
"""

import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from openai import OpenAI
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import re
from notion_client import Client
import requests

load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# Initialize clients
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
notion = Client(auth=NOTION_TOKEN) if NOTION_TOKEN else None

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# ============ GMAIL FUNCTIONS ============

def authenticate_gmail():
    """Authenticate with Gmail API"""
    creds = None
    
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        except Exception as e:
            print(f"Error loading token: {e}")
            creds = None
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing token: {e}")
                creds = None
        
        if not creds:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError("credentials.json not found. Please download from Google Cloud Console.")
            
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)


def fetch_customer_emails(service, hours_back=24):
    """Fetch customer support emails from the last N hours"""
    try:
        time_ago = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        query = f'after:{int(time_ago.timestamp())}'
        
        results = service.users().messages().list(
            userId='me', 
            q=query, 
            maxResults=50
        ).execute()
        
        messages = results.get('messages', [])
        
        emails = []
        for msg in messages:
            try:
                message = service.users().messages().get(
                    userId='me', 
                    id=msg['id'], 
                    format='full'
                ).execute()
                
                headers = message['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
                date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
                
                # Extract body
                body = ''
                if 'parts' in message['payload']:
                    for part in message['payload']['parts']:
                        if part['mimeType'] == 'text/plain' and 'data' in part.get('body', {}):
                            body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                            break
                elif 'body' in message['payload'] and 'data' in message['payload']['body']:
                    body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8', errors='ignore')
                
                emails.append({
                    'id': msg['id'],
                    'subject': subject,
                    'sender': sender,
                    'date': date,
                    'body': body[:500]  # First 500 chars
                })
            except Exception as e:
                print(f"Error processing message {msg['id']}: {e}")
                continue
        
        return emails
    
    except HttpError as e:
        print(f"Gmail API error: {e}")
        return []
    except Exception as e:
        print(f"Error fetching emails: {e}")
        return []


# ============ LLM CLASSIFICATION ============

def classify_issue(subject, body):
    """Use OpenAI to classify customer issue"""
    if not client:
        return {
            'category': 'Other',
            'priority': 'Medium',
            'summary': subject
        }
    
    prompt = f"""You are an IT maintenance assistant. Analyze this email and classify the issue.

Email Subject: {subject}
Email Body: {body[:500]}

Classify into ONE category:
- Hardware (physical equipment problems)
- Software (application/program issues)  
- Network (connectivity problems)
- User Error (user mistakes)
- Security (security threats)
- Other

Priority: High, Medium, or Low

Respond EXACTLY like this:
Category: [category]
Priority: [priority]
Summary: [one sentence summary]"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=150
        )
        
        result = response.choices[0].message.content.strip()
        
        # Parse the response
        category_match = re.search(r'Category:\s*(.+)', result, re.IGNORECASE)
        priority_match = re.search(r'Priority:\s*(.+)', result, re.IGNORECASE)
        summary_match = re.search(r'Summary:\s*(.+)', result, re.IGNORECASE)
        
        return {
            'category': category_match.group(1).strip() if category_match else 'Other',
            'priority': priority_match.group(1).strip() if priority_match else 'Medium',
            'summary': summary_match.group(1).strip() if summary_match else subject
        }
    except Exception as e:
        print(f"Error classifying: {e}")
        return {
            'category': 'Other',
            'priority': 'Medium',
            'summary': subject
        }


# ============ NOTION FUNCTIONS ============

def add_to_notion(email, classification):
    """Add classified issue to Notion database"""
    if not notion or not NOTION_DATABASE_ID:
        print("Notion not configured")
        return False
    
    try:
        # Truncate long text to avoid Notion limits
        subject_text = (email.get('subject') or 'No Subject')[:100]
        body_text = (email.get('body') or 'No content')[:2000]
        
        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Title": {
                    "title": [{"text": {"content": subject_text}}]
                },
                "Description": {
                    "rich_text": [{"text": {"content": body_text}}]
                },
                "Root Cause": {
                    "select": {"name": classification['category']}
                },
                "Priority": {
                    "select": {"name": classification['priority']}
                },
                "Status": {
                    "select": {"name": "New"}
                },
                "Date": {
                    "date": {"start": datetime.now().strftime("%Y-%m-%d")}
                }
            }
        )
        print(f"✅ Added to Notion: {subject_text[:50]}...")
        return True
    except Exception as e:
        print(f"❌ Error adding to Notion: {str(e)}")
        return False


def get_notion_summary():
    """Get daily summary from Notion"""
    if not notion or not NOTION_DATABASE_ID:
        return {'error': 'Notion not configured'}
    
    try:
        results = notion.databases.query(
            database_id=NOTION_DATABASE_ID
        ).get('results', [])
        
        summary = {
            'total': len(results),
            'by_category': {},
            'by_priority': {},
            'high_priority': []
        }
        
        for page in results:
            props = page.get('properties', {})
            
            # Count by root cause
            root_cause_obj = props.get('Root Cause', {}).get('select')
            if root_cause_obj:
                category = root_cause_obj.get('name', 'Other')
                summary['by_category'][category] = summary['by_category'].get(category, 0) + 1
            
            # Count by priority
            priority_obj = props.get('Priority', {}).get('select')
            if priority_obj:
                priority = priority_obj.get('name', 'Medium')
                summary['by_priority'][priority] = summary['by_priority'].get(priority, 0) + 1
                
                # Collect high priority items
                if priority == 'High':
                    title_array = props.get('Title', {}).get('title', [])
                    if title_array:
                        title = title_array[0].get('text', {}).get('content', 'No title')
                        summary['high_priority'].append(title)
        
        return summary
    except Exception as e:
        print(f"❌ Error getting Notion summary: {str(e)}")
        return {'error': str(e)}


# ============ SLACK FUNCTIONS ============

def send_slack_digest(summary):
    """Send daily digest to Slack"""
    if not SLACK_WEBHOOK_URL:
        print("Slack webhook not configured")
        return False
    
    if not summary or 'error' in summary:
        return False
    
    # Build category list
    category_lines = [f"• {cat}: {count}" for cat, count in summary['by_category'].items()]
    category_text = "\n".join(category_lines) if category_lines else "• None"
    
    # Build priority list
    priority_lines = [f"• {pri}: {count}" for pri, count in summary['by_priority'].items()]
    priority_text = "\n".join(priority_lines) if priority_lines else "• None"
    
    # Build high priority list
    if summary['high_priority']:
        high_priority_lines = [f"🔴 {item}" for item in summary['high_priority'][:5]]
        high_priority_text = "\n".join(high_priority_lines)
    else:
        high_priority_text = "✅ No high priority issues"
    
    message = f"""📊 *Daily Maintenance Report*

*Total Issues:* {summary['total']}

*By Category:*
{category_text}

*By Priority:*
{priority_text}

*High Priority Items:*
{high_priority_text}
"""
    
    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json={"text": message},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Slack digest sent successfully!")
            return True
        else:
            print(f"❌ Slack webhook failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending Slack message: {str(e)}")
        return False


# ============ MAIN WORKFLOW ============

def run_full_pipeline(hours_back=168):
    """Run the complete pipeline"""
    print("\n" + "="*60)
    print("🚀 STARTING AI MAINTENANCE PIPELINE")
    print("="*60 + "\n")
    
    # Step 1: Fetch emails
    print("📧 Step 1: Fetching emails from Gmail...")
    try:
        service = authenticate_gmail()
        emails = fetch_customer_emails(service, hours_back)
        print(f"✅ Found {len(emails)} emails\n")
    except Exception as e:
        print(f"❌ Gmail error: {str(e)}\n")
        return {
            'emails_found': 0,
            'emails_processed': 0,
            'digest_sent': False,
            'error': str(e)
        }
    
    # Step 2: Classify and add to Notion
    print(f"🤖 Step 2: Classifying {len(emails)} issues with AI...")
    processed = 0
    for i, email in enumerate(emails, 1):
        print(f"   Processing {i}/{len(emails)}: {email['subject'][:50]}...")
        try:
            classification = classify_issue(email['subject'], email['body'])
            print(f"   → Classified as: {classification['category']} ({classification['priority']})")
            
            if add_to_notion(email, classification):
                processed += 1
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            
    print(f"\n✅ Successfully processed {processed}/{len(emails)} issues\n")
    
    # Step 3: Generate and send Slack digest
    print("📊 Step 3: Generating Slack digest...")
    digest_sent = False
    try:
        summary = get_notion_summary()
        if summary and 'error' not in summary:
            digest_sent = send_slack_digest(summary)
        else:
            print("⚠️ Could not generate summary")
    except Exception as e:
        print(f"❌ Error with digest: {str(e)}")
    
    print("\n" + "="*60)
    print("✅ PIPELINE COMPLETE!")
    print("="*60 + "\n")
    
    return {
        'emails_found': len(emails),
        'emails_processed': processed,
        'digest_sent': digest_sent
    }


# ============ STANDALONE TESTING ============

if __name__ == "__main__":
    print("🧪 Running orchestrator in standalone mode...\n")
    result = run_full_pipeline()
    print(f"\n📊 Final Results:")
    print(f"   Emails found: {result['emails_found']}")
    print(f"   Emails processed: {result['emails_processed']}")
    print(f"   Digest sent: {'Yes' if result['digest_sent'] else 'No'}")