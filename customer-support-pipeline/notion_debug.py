"""
Notion Database Property Diagnostic Tool
Run this to see what properties Notion actually has
"""

import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

notion = Client(auth=NOTION_TOKEN)

print("🔍 Checking Notion Database Properties...\n")
print(f"Database ID: {NOTION_DATABASE_ID}\n")

try:
    # Get database schema
    database = notion.databases.retrieve(database_id=NOTION_DATABASE_ID)
    properties = database.get('properties', {})
    
    print(f"✅ Found {len(properties)} properties:\n")
    
    for prop_name, prop_data in properties.items():
        prop_type = prop_data.get('type', 'unknown')
        print(f"  • '{prop_name}' (Type: {prop_type})")
        
        # Show select options if it's a select property
        if prop_type == 'select':
            options = prop_data.get('select', {}).get('options', [])
            if options:
                option_names = [opt.get('name') for opt in options]
                print(f"    Options: {', '.join(option_names)}")
    
    print("\n" + "="*60)
    print("📝 What the code expects:")
    print("="*60)
    print("  • 'Title' (Type: title)")
    print("  • 'Description' (Type: rich_text)")
    print("  • 'Root Cause' (Type: select)")
    print("    Options: Hardware, Software, Network, User Error, Security, Other")
    print("  • 'Priority' (Type: select)")
    print("    Options: High, Medium, Low")
    print("  • 'Status' (Type: select)")
    print("    Options: New, In Progress, Resolved, Closed")
    print("  • 'Date' (Type: date)")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    print("\nPossible issues:")
    print("  1. Database ID is incorrect")
    print("  2. Integration doesn't have access to the database")
    print("  3. API token is invalid")