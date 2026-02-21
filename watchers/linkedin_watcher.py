"""
LinkedIn Watcher - Silver Tier (Updated)
=========================================
Monitors LinkedIn for business leads in messages and notifications.

Keywords: sales, client, project, lead, opportunity
Check Interval: 60 seconds
Output: Markdown files in /Needs_Action with YAML metadata

Run: python watchers/linkedin_watcher.py
"""

import os
import sys
import time
import re
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install playwright")
    print("Then run: playwright install")
    sys.exit(1)

# Configuration
KEYWORDS = ['sales', 'client', 'project', 'lead', 'opportunity', 'partnership']
CHECK_INTERVAL = 60  # seconds
NEEDS_ACTION_DIR = Path(__file__).parent.parent / 'Needs_Action'
SESSION_PATH = Path(__file__).parent.parent / 'session' / 'linkedin'
PROCESSED_NOTIFICATIONS_FILE = Path(__file__).parent.parent / 'watchers' / '.linkedin_processed'

# Ensure directories exist
NEEDS_ACTION_DIR.mkdir(parents=True, exist_ok=True)
SESSION_PATH.mkdir(parents=True, exist_ok=True)

# Track processed notification IDs to avoid duplicates
processed_notifications = set()
if PROCESSED_NOTIFICATIONS_FILE.exists():
    with open(PROCESSED_NOTIFICATIONS_FILE, 'r') as f:
        processed_notifications = set(f.read().strip().split('\n'))


def save_processed_notification(notif_id):
    """Save processed notification ID to avoid duplicates."""
    processed_notifications.add(notif_id)
    with open(PROCESSED_NOTIFICATIONS_FILE, 'w') as f:
        f.write('\n'.join(processed_notifications))


def contains_keyword(text, keywords):
    """Check if text contains any of the keywords (case-insensitive)."""
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)


def get_priority(text):
    """Determine priority based on keywords."""
    text_lower = text.lower()
    if 'urgent' in text_lower or 'immediate' in text_lower:
        return 'high'
    elif 'project' in text_lower or 'client' in text_lower:
        return 'medium'
    elif 'sales' in text_lower or 'lead' in text_lower:
        return 'medium'
    return 'low'


def create_markdown_file(notification_data):
    """Create markdown file with YAML metadata in Needs_Action folder."""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    safe_sender = re.sub(r'[^\w\s-]', '', notification_data['sender'])[:20]
    filename = f"linkedin_{safe_sender}_{timestamp}.md"
    filepath = NEEDS_ACTION_DIR / filename
    
    content = f"""---
type: linkedin_notification
from: {notification_data['sender']}
subject: {notification_data['title']}
received: {notification_data['received']}
priority: {notification_data['priority']}
status: pending
keywords: {', '.join(notification_data['matched_keywords'])}
notification_id: {notification_data['notification_id']}
source: {notification_data['source']}
---

# LinkedIn Business Lead

## Metadata
- **From:** {notification_data['sender']}
- **Received:** {notification_data['received']}
- **Priority:** {notification_data['priority']}
- **Status:** pending
- **Matched Keywords:** {', '.join(notification_data['matched_keywords'])}
- **Source:** {notification_data['source']}

## Content

{notification_data['content']}

---
*Detected by LinkedIn Watcher - Silver Tier*
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath


def monitor_linkedin():
    """Monitor LinkedIn for business leads in messages and notifications."""
    print("[*] Starting LinkedIn monitoring...")
    
    with sync_playwright() as p:
        # Launch browser with persistent context
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_PATH),
            headless=False,  # Keep visible for monitoring
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        print("[*] Navigating to LinkedIn...")
        page.goto('https://www.linkedin.com/feed/', wait_until='networkidle', timeout=120000)
        
        print("[*] Waiting for LinkedIn to load...")
        
        try:
            # Wait for feed to appear (indicates successful login)
            page.wait_for_selector('div[id="mdu-val"], div.feed-shared-update-v2', timeout=60000)
            print("[*] LinkedIn loaded successfully!")
            print("[*] Starting monitoring cycle...")
            print()
            
            check_count = 0
            
            while True:
                check_count += 1
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Check #{check_count}")
                
                try:
                    # Check Notifications
                    print("  [*] Checking notifications...")
                    
                    # Click notifications bell
                    notif_btn = page.query_selector('a[href*="/notifications"]')
                    if notif_btn:
                        try:
                            notif_btn.click()
                            time.sleep(2)
                            
                            # Get notification items - updated selectors
                            notification_items = page.query_selector_all(
                                'ul[role="list"] li, div.notification-item, div.mn-notification-card'
                            )
                            
                            print(f"    Found {len(notification_items)} notifications")
                            
                            for notif in notification_items[:15]:  # Check last 15 notifications
                                try:
                                    notif_text = notif.inner_text()
                                    
                                    if not notif_text or len(notif_text) < 10:
                                        continue
                                    
                                    # Create unique notification ID
                                    notif_id = f"notif_{hash(notif_text[:50])}_{datetime.now().strftime('%H%M')}"
                                    
                                    if notif_id in processed_notifications:
                                        continue
                                    
                                    # Check for business keywords
                                    if contains_keyword(notif_text, KEYWORDS):
                                        matched_keywords = [kw for kw in KEYWORDS if kw.lower() in notif_text.lower()]
                                        
                                        # Extract sender name
                                        lines = notif_text.split('\n')
                                        sender = lines[0] if lines else 'Unknown'
                                        content = '\n'.join(lines[1:4]) if len(lines) > 1 else notif_text[:300]
                                        
                                        notification_data = {
                                            'sender': sender,
                                            'title': 'LinkedIn Notification',
                                            'content': content,
                                            'received': datetime.now().isoformat(),
                                            'priority': get_priority(notif_text),
                                            'status': 'pending',
                                            'matched_keywords': matched_keywords,
                                            'notification_id': notif_id,
                                            'source': 'notifications'
                                        }
                                        
                                        filepath = create_markdown_file(notification_data)
                                        save_processed_notification(notif_id)
                                        
                                        print(f"    [+] Business lead detected!")
                                        print(f"        From: {sender}")
                                        print(f"        Keywords: {', '.join(matched_keywords)}")
                                        print(f"        Saved: {filepath.name}")
                                        print()
                                
                                except Exception as e:
                                    continue
                            
                            # Navigate back to feed
                            page.goto('https://www.linkedin.com/feed/', wait_until='networkidle')
                            time.sleep(1)
                            
                        except Exception as e:
                            print(f"    Error checking notifications: {e}")
                    
                    # Check Messaging
                    print("  [*] Checking messages...")
                    
                    msg_btn = page.query_selector('a[href*="/messaging"]')
                    if msg_btn:
                        try:
                            msg_btn.click()
                            time.sleep(2)
                            
                            # Get conversation list - updated selectors
                            conversations = page.query_selector_all(
                                'ul[role="list"] li[role="listitem"], div.conversation-item'
                            )
                            
                            print(f"    Found {len(conversations)} conversations")
                            
                            for conv in conversations[:15]:  # Check last 15 conversations
                                try:
                                    conv_text = conv.inner_text()
                                    
                                    if not conv_text or len(conv_text) < 5:
                                        continue
                                    
                                    # Check for unread indicator
                                    is_unread = 'unread' in conv_text.lower() or 'new' in conv_text.lower()
                                    
                                    if not is_unread:
                                        continue
                                    
                                    # Create unique message ID
                                    msg_id = f"msg_{hash(conv_text[:50])}_{datetime.now().strftime('%H%M')}"
                                    
                                    if msg_id in processed_notifications:
                                        continue
                                    
                                    # Check for business keywords
                                    if contains_keyword(conv_text, KEYWORDS):
                                        matched_keywords = [kw for kw in KEYWORDS if kw.lower() in conv_text.lower()]
                                        
                                        lines = conv_text.split('\n')
                                        sender = lines[0] if lines else 'Unknown'
                                        content = '\n'.join(lines[1:4]) if len(lines) > 1 else conv_text[:300]
                                        
                                        message_data = {
                                            'sender': sender,
                                            'title': 'LinkedIn Message',
                                            'content': content,
                                            'received': datetime.now().isoformat(),
                                            'priority': get_priority(conv_text),
                                            'status': 'pending',
                                            'matched_keywords': matched_keywords,
                                            'notification_id': msg_id,
                                            'source': 'messages'
                                        }
                                        
                                        filepath = create_markdown_file(message_data)
                                        save_processed_notification(msg_id)
                                        
                                        print(f"    [+] Business message detected!")
                                        print(f"        From: {sender}")
                                        print(f"        Keywords: {', '.join(matched_keywords)}")
                                        print(f"        Saved: {filepath.name}")
                                        print()
                                
                                except Exception as e:
                                    continue
                            
                            # Navigate back to feed
                            page.goto('https://www.linkedin.com/feed/', wait_until='networkidle')
                            time.sleep(1)
                            
                        except Exception as e:
                            print(f"    Error checking messages: {e}")
                    
                    print(f"  [*] Waiting {CHECK_INTERVAL}s before next check...")
                    print()
                    time.sleep(CHECK_INTERVAL)
                    
                except Exception as e:
                    print(f"Error during monitoring: {e}")
                    time.sleep(5)
                    
        except PlaywrightTimeout:
            print("[!] Timeout waiting for LinkedIn to load.")
            print("[*] Please ensure you're logged in to LinkedIn.")
            print("[*] The browser window should show your LinkedIn feed.")
        finally:
            browser.close()


def main():
    """Main entry point for LinkedIn watcher."""
    print("=" * 60)
    print("LinkedIn Watcher - Silver Tier")
    print("=" * 60)
    print(f"Keywords: {', '.join(KEYWORDS)}")
    print(f"Check Interval: {CHECK_INTERVAL} seconds")
    print(f"Output Directory: {NEEDS_ACTION_DIR}")
    print(f"Session Path: {SESSION_PATH}")
    print("=" * 60)
    print()
    print("NOTE: Browser will open. Keep it open for continuous monitoring.")
    print("      Logs will appear here in real-time.")
    print()
    
    try:
        monitor_linkedin()
    except KeyboardInterrupt:
        print("\n\nWatcher stopped by user.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
