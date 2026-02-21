"""
Gmail Watcher - Silver Tier
============================
Monitors Gmail for unread important emails with specific keywords.

Keywords: urgent, invoice, payment, sales
Check Interval: 120 seconds
Output: Markdown files in /Needs_Action with YAML metadata

Setup Instructions:
-------------------
1. Enable Gmail API: https://developers.google.com/gmail/api/quickstart/python
2. Download credentials.json to project root
3. Install dependencies: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

Run with PM2:
-------------
pm2 start watchers/gmail_watcher.py --name "gmail-watcher" --interpreter python

Test:
-----
1. Send yourself an email with subject containing "urgent" or "invoice"
2. Mark it as important in Gmail
3. Run script manually: python watchers/gmail_watcher.py
4. Check /Needs_Action folder for generated .md file
"""

import os
import sys
import time
import base64
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)

# Configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
KEYWORDS = ['urgent', 'invoice', 'payment', 'sales']
CHECK_INTERVAL = 120  # seconds
NEEDS_ACTION_DIR = Path(__file__).parent.parent / 'Needs_Action'
CREDENTIALS_FILE = Path(__file__).parent.parent / 'credentials.json'
TOKEN_FILE = Path(__file__).parent.parent / 'token.json'

# Ensure Needs_Action directory exists
NEEDS_ACTION_DIR.mkdir(parents=True, exist_ok=True)


def authenticate_gmail():
    """Authenticate with Gmail API and return service object."""
    creds = None
    
    # Load existing token if available
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    
    # Refresh or create new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(f"Error: credentials.json not found at {CREDENTIALS_FILE}")
                print("Download from: https://developers.google.com/gmail/api/quickstart/python")
                sys.exit(1)
            
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)


def decode_message(message_data):
    """Decode Gmail message parts."""
    try:
        if 'parts' in message_data['payload']:
            for part in message_data['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
        elif 'body' in message_data['payload']:
            return base64.urlsafe_b64decode(message_data['payload']['body']['data']).decode('utf-8')
    except Exception as e:
        print(f"Error decoding message: {e}")
    return ""


def contains_keyword(text, keywords):
    """Check if text contains any of the keywords (case-insensitive)."""
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)


def get_priority(subject, snippet):
    """Determine priority based on keywords."""
    text = f"{subject} {snippet}".lower()
    if 'urgent' in text:
        return 'high'
    elif 'invoice' in text or 'payment' in text:
        return 'medium'
    elif 'sales' in text:
        return 'medium'
    return 'low'


def create_markdown_file(email_data):
    """Create markdown file with YAML metadata in Needs_Action folder."""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"gmail_{email_data['subject'][:30].replace(' ', '_').replace('/', '_')}_{timestamp}.md"
    filepath = NEEDS_ACTION_DIR / filename
    
    # Escape pipe characters in content for markdown
    subject_escaped = email_data['subject'].replace('|', '\\|')
    from_escaped = email_data['from'].replace('|', '\\|')
    
    content = f"""---
type: email
from: {from_escaped}
subject: {subject_escaped}
received: {email_data['received']}
priority: {email_data['priority']}
status: pending
keywords: {', '.join(email_data['matched_keywords'])}
message_id: {email_data['message_id']}
---

# Email: {email_data['subject']}

## Metadata
- **From:** {email_data['from']}
- **Received:** {email_data['received']}
- **Priority:** {email_data['priority']}
- **Status:** {email_data['status']}
- **Matched Keywords:** {', '.join(email_data['matched_keywords'])}

## Content

{email_data['body']}

---
*Generated by Gmail Watcher - Silver Tier*
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath


def check_gmail(service):
    """Check Gmail for unread important emails with keywords."""
    try:
        # Search for unread messages
        results = service.users().messages().list(
            userId='me',
            q='is:unread is:important',
            maxResults=50
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No unread important emails found.")
            return
        
        for message in messages:
            msg = service.users().messages().get(
                userId='me',
                id=message['id'],
                format='full'
            ).execute()
            
            # Extract headers
            headers = {h['name']: h['value'] for h in msg['payload']['headers']}
            subject = headers.get('Subject', '')
            from_addr = headers.get('From', '')
            date_str = headers.get('Date', '')
            
            try:
                received = parsedate_to_datetime(date_str).isoformat()
            except:
                received = date_str
            
            # Get body content
            snippet = msg.get('snippet', '')
            body = decode_message(msg)
            
            # Check for keywords
            full_text = f"{subject} {snippet} {body}"
            matched_keywords = [kw for kw in KEYWORDS if contains_keyword(full_text, [kw])]
            
            if matched_keywords:
                email_data = {
                    'from': from_addr,
                    'subject': subject,
                    'received': received,
                    'priority': get_priority(subject, snippet),
                    'status': 'pending',
                    'matched_keywords': matched_keywords,
                    'message_id': msg['id'],
                    'body': body[:2000] if body else snippet  # Limit body length
                }
                
                filepath = create_markdown_file(email_data)
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Created: {filepath.name}")
                print(f"  - From: {from_addr}")
                print(f"  - Subject: {subject}")
                print(f"  - Keywords: {', '.join(matched_keywords)}")
                print(f"  - Priority: {email_data['priority']}")
        
    except HttpError as error:
        print(f"An error occurred: {error}")


def main():
    """Main loop for Gmail watcher."""
    print("=" * 60)
    print("Gmail Watcher - Silver Tier")
    print("=" * 60)
    print(f"Keywords: {', '.join(KEYWORDS)}")
    print(f"Check Interval: {CHECK_INTERVAL} seconds")
    print(f"Output Directory: {NEEDS_ACTION_DIR}")
    print("=" * 60)
    print("Starting watcher... (Press Ctrl+C to stop)")
    print()
    
    try:
        service = authenticate_gmail()
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Gmail authentication successful!")
        print()
        
        while True:
            check_gmail(service)
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\nWatcher stopped by user.")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
