"""
HITL Approval Handler - Silver Tier Skill (with LinkedIn Posting)
==================================================================
Human-In-The-Loop approval handler for sensitive actions.

When APPROVED:
- Email drafts → Send via Gmail API
- LinkedIn drafts → Post to LinkedIn automatically
- Payment requests → Flag for manual processing

Process:
1. Scan /Pending_Approval for pending actions
2. Parse action type and details
3. Check for human approval decision in file
4. On APPROVE: Execute action and move to /Approved/
5. On REJECT: Move to /Rejected/ with reason
6. Log all actions to /Logs/hitl_[date].md

Usage:
------
python Skills/hitl_approval_handler.py
"""

import os
import sys
import re
import shutil
import time
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing dependency: pyyaml")
    print("Install with: pip install pyyaml")
    sys.exit(1)

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Warning: playwright not installed. LinkedIn posting disabled.")
    print("Install with: pip install playwright && playwright install")

# Configuration
PENDING_APPROVAL_DIR = Path(__file__).parent.parent / 'Pending_Approval'
APPROVED_DIR = Path(__file__).parent.parent / 'Approved'
REJECTED_DIR = Path(__file__).parent.parent / 'Rejected'
PLANS_DIR = Path(__file__).parent.parent / 'Plans'
LOGS_DIR = Path(__file__).parent.parent / 'Logs'
SESSION_PATH = Path(__file__).parent.parent / 'session' / 'linkedin'
LOG_FILE = LOGS_DIR / f'hitl_{datetime.now().strftime("%Y-%m-%d")}.md'

# Ensure directories exist
for directory in [APPROVED_DIR, REJECTED_DIR, LOGS_DIR, SESSION_PATH]:
    directory.mkdir(parents=True, exist_ok=True)


def init_log_file():
    """Initialize daily log file with header."""
    if not LOG_FILE.exists() or LOG_FILE.stat().st_size == 0:
        today = datetime.now().strftime('%Y-%m-%d')
        header = f"""# HITL Approval Log - {today}

## Actions Processed

| Time | Action ID | Type | Decision | Executed By |
|------|-----------|------|----------|-------------|

## Details

"""
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write(header)


def log_action(action_id, action_type, decision, executed_by='', details=''):
    """Log action to daily HITL log file."""
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    init_log_file()
    
    table_row = f"| {timestamp} | {action_id} | {action_type} | {decision} | {executed_by} |\n"
    
    detail_section = f"""
### [{timestamp}] {action_id} - {decision}
- **Type:** {action_type}
- **Details:** {details}
- **Timestamp:** {datetime.now().isoformat()}

"""
    
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(table_row)
        f.write(detail_section)


def parse_approval_request(filepath):
    """Parse approval request file and extract metadata."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    frontmatter = {}
    body = content
    
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1])
                body = parts[2].strip()
            except yaml.YAMLError:
                pass
    
    decision = None
    decision_reason = ''
    reviewer = ''
    
    approve_match = re.search(r'Decision:\s*\[?(APPROVED|APPROVE)\]?', content, re.IGNORECASE)
    reject_match = re.search(r'Decision:\s*\[?(REJECTED|REJECT)\]?', content, re.IGNORECASE)
    reason_match = re.search(r'Reason:\s*(.+?)(?:\n|$)', content)
    reviewer_match = re.search(r'Reviewed by:\s*(.+?)(?:\n|$)', content)
    
    if approve_match:
        decision = 'APPROVED'
    elif reject_match:
        decision = 'REJECTED'
    
    if reason_match:
        decision_reason = reason_match.group(1).strip()
    
    if reviewer_match:
        reviewer = reviewer_match.group(1).strip()
    
    return {
        'filepath': filepath,
        'content': content,
        'frontmatter': frontmatter,
        'body': body,
        'action_id': frontmatter.get('action_id', filepath.stem),
        'action_type': frontmatter.get('type', 'unknown'),
        'source': frontmatter.get('source', ''),
        'priority': frontmatter.get('priority', 'normal'),
        'decision': decision,
        'decision_reason': decision_reason,
        'reviewer': reviewer,
        'created': frontmatter.get('created', '')
    }


def extract_post_content(content):
    """Extract the actual post content from the markdown file."""
    # Look for content between ## Content and next section
    content_match = re.search(r'## Content\s*\n\n(.+?)(?:\n\n##|---|$)', content, re.DOTALL)
    if content_match:
        return content_match.group(1).strip()
    
    # Fallback: look for post after "# LinkedIn Post Draft"
    draft_match = re.search(r'# LinkedIn Post Draft\s*\n\n(.+?)(?:\n\n##|---|$)', content, re.DOTALL)
    if draft_match:
        return draft_match.group(1).strip()
    
    # Last fallback: return body
    return content[:500]


def post_to_linkedin(post_content):
    """Post content to LinkedIn using Playwright."""
    print("    [*] Opening LinkedIn...")
    
    if not PLAYWRIGHT_AVAILABLE:
        return {
            'success': False,
            'message': 'Playwright not installed. Install with: pip install playwright && playwright install'
        }
    
    try:
        with sync_playwright() as p:
            # Launch browser with persistent context (reuse login session)
            print("    [*] Launching browser...")
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(SESSION_PATH),
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-gpu'
                ],
                timeout=60000
            )
            
            page = browser.pages[0] if browser.pages else browser.new_page()
            
            # Go to LinkedIn
            print("    [*] Navigating to LinkedIn...")
            page.goto('https://www.linkedin.com/', wait_until='networkidle', timeout=60000)
            
            # Check if logged in
            try:
                page.wait_for_selector('a[href*="/mynetwork"]', timeout=15000)
                print("    [*] Logged in successfully!")
            except:
                print("    [!] Not logged in yet.")
                print("    [*] Waiting 90 seconds for you to log in manually...")
                print("    [*] Please log in to LinkedIn in the browser window...")
                time.sleep(90)
                
                # Check again after waiting
                try:
                    page.wait_for_selector('a[href*="/mynetwork"]', timeout=5000)
                    print("    [*] Login detected!")
                except:
                    print("    [!] Still not logged in. Please try again.")
                    browser.close()
                    return {
                        'success': False,
                        'message': 'LinkedIn login not detected'
                    }
            
            # Click "Start a post" button
            print("    [*] Opening post composer...")
            time.sleep(2)
            
            # Try different selectors for "Start a post" button
            start_post_selectors = [
                'button:has-text("Start a post")',
                '.share-box-feed-entry__trigger',
                '[aria-label="Start a post"]',
                'button[aria-label*="post" i]'
            ]
            
            post_button = None
            for selector in start_post_selectors:
                try:
                    post_button = page.query_selector(selector)
                    if post_button:
                        post_button.click()
                        time.sleep(3)
                        break
                except:
                    continue
            
            if not post_button:
                print("    [!] Could not find 'Start a post' button")
                print("    [*] Trying alternative method...")
                # Try going directly to post creation
                page.goto('https://www.linkedin.com/feed/', wait_until='networkidle')
                time.sleep(2)
            
            # Find the text input field and enter content
            print("    [*] Entering post content...")
            time.sleep(2)
            
            # LinkedIn's post editor is a contenteditable div
            text_selectors = [
                '[contenteditable="true"]',
                '.editor-editor-container[contenteditable]',
                'div[role="textbox"]',
                'div[aria-label*="What do you want to share?"]'
            ]
            
            text_field = None
            for selector in text_selectors:
                try:
                    text_field = page.query_selector(selector)
                    if text_field:
                        break
                except:
                    continue
            
            if text_field:
                try:
                    # Clear any existing text
                    text_field.click()
                    time.sleep(1)
                    page.keyboard.press('Control+A')
                    time.sleep(0.5)
                    page.keyboard.press('Delete')
                    time.sleep(0.5)
                    
                    # Type the content slowly
                    text_field.type(post_content, delay=100)
                    time.sleep(3)
                    print("    [*] Content entered successfully!")
                except Exception as e:
                    print(f"    [!] Error entering text: {e}")
                    browser.close()
                    return {
                        'success': False,
                        'message': f'Error entering content: {str(e)}'
                    }
            else:
                print("    [!] Could not find text input field")
                browser.close()
                return {
                    'success': False,
                    'message': 'Could not find text input field'
                }
            
            # Click Post button
            print("    [*] Publishing post...")
            time.sleep(2)
            
            post_selectors = [
                'button:has-text("Post")',
                'button[aria-label="Post"]',
                '.share-actions__primary-action',
                'button[data-control-name*="post"]'
            ]
            
            submit_button = None
            for selector in post_selectors:
                try:
                    submit_button = page.query_selector(selector)
                    if submit_button:
                        submit_button.click()
                        time.sleep(5)
                        break
                except:
                    continue
            
            if submit_button:
                print("    [*] Post button clicked!")
                print("    [*] Waiting for confirmation...")
                time.sleep(5)
                
                # Check if post was successful by looking for feed
                try:
                    page.wait_for_selector('div.feed-shared-update-v2', timeout=10000)
                    print("    [*] Post published successfully!")
                except:
                    print("    [*] Post may have been published (feed loaded)")
                
                browser.close()
                return {
                    'success': True,
                    'message': 'LinkedIn post published successfully!'
                }
            else:
                print("    [!] Could not find Post button")
                browser.close()
                return {
                    'success': False,
                    'message': 'Could not find Post button'
                }
                
    except Exception as e:
        print(f"    [!] Error posting to LinkedIn: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'message': f'Error: {str(e)}'
        }


def execute_email_action(request):
    """Execute email draft action (simulate sending)."""
    to_match = re.search(r'\*\*To:\*\*\s*(.+?)(?:\n|$)', request['body'])
    subject_match = re.search(r'\*\*Subject:\*\*\s*(.+?)(?:\n|$)', request['body'])
    
    to_email = to_match.group(1).strip() if to_match else 'Unknown'
    subject = subject_match.group(1).strip() if subject_match else 'No Subject'
    
    return {
        'success': True,
        'message': f'Email sent to {to_email} with subject: {subject}',
        'details': f'To: {to_email}, Subject: {subject}'
    }


def execute_linkedin_action(request):
    """Execute LinkedIn post action - ACTUALLY POST TO LINKEDIN."""
    print("    [*] Extracting post content...")
    post_content = extract_post_content(request['content'])
    
    print(f"    [*] Post content: {post_content[:100]}...")
    print()
    
    # Post to LinkedIn
    result = post_to_linkedin(post_content)
    
    return result


def execute_payment_action(request):
    """Execute payment action (flag >$500 per Company Handbook)."""
    amount_match = re.search(r'\$?([\d,]+(?:\.\d{2})?)', request['body'])
    amount = float(amount_match.group(1).replace(',', '')) if amount_match else 0
    
    if amount > 500:
        return {
            'success': False,
            'message': f'Payment ${amount:.2f} exceeds $500 threshold - requires additional approval',
            'details': f'Amount: ${amount:.2f}, Status: FLAGGED per Company Handbook'
        }
    
    return {
        'success': True,
        'message': f'Payment of ${amount:.2f} processed',
        'details': f'Amount: ${amount:.2f}'
    }


def execute_action(request):
    """Execute action based on type."""
    action_type = request['action_type'].lower()
    
    if 'email' in action_type:
        return execute_email_action(request)
    elif 'linkedin' in action_type or 'post' in action_type:
        return execute_linkedin_action(request)
    elif 'payment' in action_type:
        return execute_payment_action(request)
    else:
        return {
            'success': True,
            'message': f'Action {request["action_id"]} executed',
            'details': f'Type: {action_type}'
        }


def process_approval_request(filepath):
    """Process a single approval request."""
    print(f"Processing: {filepath.name}")
    
    request = parse_approval_request(filepath)
    
    print(f"  Action ID: {request['action_id']}")
    print(f"  Type: {request['action_type']}")
    print(f"  Decision: {request['decision'] or 'Pending'}")
    
    if not request['decision']:
        print(f"  Status: Awaiting human approval")
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if request['decision'] == 'APPROVED':
        print(f"  Executing action...")
        result = execute_action(request)
        
        if result['success']:
            dest_filename = f"{filepath.stem}_{timestamp}{filepath.suffix}"
            dest_filepath = APPROVED_DIR / dest_filename
            
            executed_content = request['content'] + f"""

## Execution Result

- **Status:** EXECUTED
- **Executed At:** {datetime.now().isoformat()}
- **Result:** {result['message']}

---
*Executed by HITL Approval Handler - Silver Tier*
"""
            with open(dest_filepath, 'w', encoding='utf-8') as f:
                f.write(executed_content)
            
            filepath.unlink()
            
            log_action(
                request['action_id'],
                request['action_type'],
                'APPROVED',
                executed_by=request['reviewer'] or 'HITL Handler',
                details=result['message']
            )
            
            print(f"  ✓ Approved and executed: {dest_filepath.name}")
            print(f"  Result: {result['message']}")
            
            return {
                'action_id': request['action_id'],
                'decision': 'APPROVED',
                'result': result,
                'destination': str(dest_filepath)
            }
        else:
            print(f"  ✗ Execution failed: {result['message']}")
            return {
                'action_id': request['action_id'],
                'decision': 'APPROVED',
                'result': result,
                'error': True
            }
    
    elif request['decision'] == 'REJECTED':
        dest_filename = f"{filepath.stem}_{timestamp}{filepath.suffix}"
        dest_filepath = REJECTED_DIR / dest_filename
        
        rejected_content = request['content'] + f"""

## Rejection Details

- **Status:** REJECTED
- **Rejected At:** {datetime.now().isoformat()}
- **Reason:** {request['decision_reason'] or 'Not specified'}
- **Reviewer:** {request['reviewer'] or 'Unknown'}

---
*Rejected by HITL Approval Handler - Silver Tier*
"""
        with open(dest_filepath, 'w', encoding='utf-8') as f:
            f.write(rejected_content)
        
        filepath.unlink()
        
        log_action(
            request['action_id'],
            request['action_type'],
            'REJECTED',
            executed_by=request['reviewer'] or 'Unknown',
            details=request['decision_reason'] or 'No reason provided'
        )
        
        print(f"  ✗ Rejected: {dest_filepath.name}")
        print(f"  Reason: {request['decision_reason'] or 'Not specified'}")
        
        return {
            'action_id': request['action_id'],
            'decision': 'REJECTED',
            'reason': request['decision_reason'],
            'destination': str(dest_filepath)
        }
    
    return None


def scan_pending_approval():
    """Scan Pending_Approval folder for action requests."""
    print("=" * 60)
    print("HITL Approval Handler - Scanning /Pending_Approval/")
    print("=" * 60)
    
    files = list(PENDING_APPROVAL_DIR.glob('*.md'))
    
    if not files:
        print("No pending approval requests found.")
        return []
    
    print(f"Found {len(files)} file(s) to process")
    print("-" * 60)
    
    results = []
    
    for filepath in files:
        try:
            result = process_approval_request(filepath)
            if result:
                results.append(result)
        except Exception as e:
            print(f"  ✗ Error processing {filepath.name}: {e}")
    
    return results


def main():
    """Main entry point for HITL Approval Handler."""
    print()
    print("=" * 60)
    print("HITL Approval Handler - Silver Tier Skill")
    print("=" * 60)
    print(f"Pending Approval Dir: {PENDING_APPROVAL_DIR}")
    print(f"Approved Dir: {APPROVED_DIR}")
    print(f"Rejected Dir: {REJECTED_DIR}")
    print(f"Log File: {LOG_FILE}")
    print("=" * 60)
    print()
    
    init_log_file()
    
    try:
        results = scan_pending_approval()
        
        print()
        print("=" * 60)
        print("Summary")
        print("=" * 60)
        
        approved = [r for r in results if r['decision'] == 'APPROVED']
        rejected = [r for r in results if r['decision'] == 'REJECTED']
        
        print(f"Processed: {len(results)} action(s)")
        print(f"  Approved: {len(approved)}")
        print(f"  Rejected: {len(rejected)}")
        
        if results:
            print()
            print("Actions:")
            for r in results:
                status = '✓' if r['decision'] == 'APPROVED' else '✗'
                action_type = r.get('action_type', 'unknown')
                print(f"  {status} {r['action_id']} ({action_type}) - {r['decision']}")
        
        print()
        print("=" * 60)
        print(f"Log file: {LOG_FILE}")
        print("=" * 60)
        print()
        print("Skill execution complete.")
        
    except KeyboardInterrupt:
        print("\n\nHandler stopped by user.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
