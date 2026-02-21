"""
Auto LinkedIn Poster - Silver Tier Skill
=========================================
Automatically drafts LinkedIn posts from sales/business leads.

Process:
1. Scans /Needs_Action for leads with keywords: sales, client, project
2. Drafts polite LinkedIn post following Company Handbook guidelines
3. Saves draft to /Plans/
4. Moves to /Pending_Approval for HITL review

Usage:
------
python skills/auto_linkedin_poster.py

Or trigger with: @Auto LinkedIn Poster process sales lead

Run with PM2:
-------------
pm2 start skills/auto_linkedin_poster.py --name "linkedin-poster" --interpreter python
"""

import os
import sys
import re
import shutil
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing dependency: pyyaml")
    print("Install with: pip install pyyaml")
    sys.exit(1)

# Configuration
NEEDS_ACTION_DIR = Path(__file__).parent.parent / 'Needs_Action'
PLANS_DIR = Path(__file__).parent.parent / 'Plans'
PENDING_APPROVAL_DIR = Path(__file__).parent.parent / 'Pending_Approval'
LOGS_DIR = Path(__file__).parent.parent / 'Logs'
LOG_FILE = LOGS_DIR / 'linkedin_poster.log'

KEYWORDS = ['sales', 'client', 'project', 'lead', 'opportunity']
SERVICE_PATTERNS = [
    r'(?:looking for|need|seeking|want|require)\s+(\w+(?:\s+\w+)*)',
    r'(?:developer|designer|service|solution|product)',
]

# Ensure directories exist
for directory in [PLANS_DIR, PENDING_APPROVAL_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


def log_message(message):
    """Log message to file and console."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry + '\n')


def extract_service_and_benefit(content, subject=''):
    """Extract service type and benefit from lead content."""
    text = f"{subject} {content}".lower()
    
    # Default service/benefit based on keywords
    service = "professional services"
    benefit = "your business needs"
    
    # Try to extract specific service
    if 'developer' in text:
        service = "development services"
    elif 'design' in text:
        service = "design services"
    elif 'solution' in text:
        service = "tailored solutions"
    elif 'product' in text:
        service = "quality products"
    
    # Try to extract benefit
    if 'project' in text:
        benefit = "your project success"
    elif 'client' in text:
        benefit = "client satisfaction"
    elif 'sales' in text:
        benefit = "business growth"
    
    return service, benefit


def create_linkedin_post(service, benefit):
    """Create LinkedIn post content following Company Handbook guidelines."""
    # Polite, professional tone as per Company Handbook
    post = f"""Excited to offer {service} for {benefit}! DM for more.

#BusinessGrowth #ProfessionalServices #Opportunity"""
    return post


def parse_markdown_file(filepath):
    """Parse markdown file and extract YAML frontmatter and content."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract YAML frontmatter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1])
                body = parts[2].strip()
                return frontmatter, body
            except yaml.YAMLError:
                return {}, content
    return {}, content


def process_lead(filepath):
    """Process a lead file and create LinkedIn post draft."""
    log_message(f"Processing lead: {filepath.name}")
    
    # Parse the lead file
    frontmatter, content = parse_markdown_file(filepath)
    
    # Check if it's a relevant type
    lead_type = frontmatter.get('type', '')
    if lead_type not in ['email', 'whatsapp_message', 'linkedin_notification']:
        log_message(f"  Skipping - Not a relevant type: {lead_type}")
        return None
    
    # Check for keywords
    full_text = f"{frontmatter.get('subject', '')} {content}".lower()
    matched_keywords = [kw for kw in KEYWORDS if kw in full_text]
    
    if not matched_keywords:
        log_message(f"  Skipping - No matching keywords")
        return None
    
    log_message(f"  Matched keywords: {', '.join(matched_keywords)}")
    
    # Extract service and benefit
    service, benefit = extract_service_and_benefit(
        content, 
        frontmatter.get('subject', '')
    )
    log_message(f"  Service: {service}, Benefit: {benefit}")
    
    # Create LinkedIn post
    post_content = create_linkedin_post(service, benefit)
    log_message(f"  Drafted post: {post_content[:50]}...")
    
    # Create draft file
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    draft_filename = f"linkedin_post_{timestamp}.md"
    
    draft_frontmatter = {
        'type': 'linkedin_draft',
        'source': filepath.name,
        'created': datetime.now().isoformat(),
        'status': 'draft',
        'keywords': ', '.join(matched_keywords),
        'original_from': frontmatter.get('from', 'Unknown'),
        'original_subject': frontmatter.get('subject', 'N/A')
    }
    
    draft_content = f"""---
type: {draft_frontmatter['type']}
source: {draft_frontmatter['source']}
created: {draft_frontmatter['created']}
status: {draft_frontmatter['status']}
keywords: {draft_frontmatter['keywords']}
original_from: {draft_frontmatter['original_from']}
original_subject: {draft_frontmatter['original_subject']}
---

# LinkedIn Post Draft

## Content

{post_content}

## Source Lead

- **From:** {frontmatter.get('from', 'Unknown')}
- **Original Subject:** {frontmatter.get('subject', 'N/A')}
- **Matched Keywords:** {', '.join(matched_keywords)}
- **Original File:** `{filepath.name}`

## Lead Content

{content[:500]}{'...' if len(content) > 500 else ''}

---
*Status: draft - Moving to /Pending_Approval/ for review*
*Generated by Auto LinkedIn Poster - Silver Tier*
"""
    
    # Save to Plans directory first
    plans_filepath = PLANS_DIR / draft_filename
    with open(plans_filepath, 'w', encoding='utf-8') as f:
        f.write(draft_content)
    
    log_message(f"  Saved draft to: {plans_filepath}")
    
    # Move to Pending_Approval for HITL
    approval_filepath = PENDING_APPROVAL_DIR / draft_filename
    shutil.copy2(plans_filepath, approval_filepath)
    
    log_message(f"  Moved to approval queue: {approval_filepath}")
    
    return {
        'draft_path': str(plans_filepath),
        'approval_path': str(approval_filepath),
        'post_content': post_content
    }


def scan_needs_action():
    """Scan Needs_Action folder for new leads."""
    log_message("=" * 50)
    log_message("Scanning /Needs_Action for sales leads...")
    
    processed_marker = Path(__file__).parent / '.linkedin_poster_processed'
    processed_files = set()
    
    if processed_marker.exists():
        with open(processed_marker, 'r') as f:
            processed_files = set(f.read().strip().split('\n'))
    
    new_leads = []
    
    for filepath in NEEDS_ACTION_DIR.glob('*.md'):
        if filepath.name not in processed_files:
            result = process_lead(filepath)
            if result:
                new_leads.append(result)
                processed_files.add(filepath.name)
    
    # Save processed marker
    with open(processed_marker, 'w') as f:
        f.write('\n'.join(processed_files))
    
    return new_leads


def main():
    """Main entry point for Auto LinkedIn Poster."""
    print("=" * 60)
    print("Auto LinkedIn Poster - Silver Tier Skill")
    print("=" * 60)
    print(f"Keywords: {', '.join(KEYWORDS)}")
    print(f"Plans Directory: {PLANS_DIR}")
    print(f"Approval Queue: {PENDING_APPROVAL_DIR}")
    print("=" * 60)
    print()
    
    try:
        # Scan and process leads
        results = scan_needs_action()
        
        if results:
            print()
            print("=" * 60)
            print(f"SUCCESS: Processed {len(results)} lead(s)")
            print("=" * 60)
            for i, result in enumerate(results, 1):
                print(f"\n[{i}] Draft created:")
                print(f"    Plans: {result['draft_path']}")
                print(f"    Pending Approval: {result['approval_path']}")
                print(f"    Post: {result['post_content'][:60]}...")
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No new leads found.")
        
        print()
        print("=" * 60)
        print("Skill execution complete.")
        print("=" * 60)
        
    except Exception as e:
        log_message(f"ERROR: {e}")
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
