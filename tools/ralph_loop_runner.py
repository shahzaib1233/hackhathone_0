"""
Ralph Wiggum Reasoning Loop - Silver Tier
==========================================
Simple "repeat until done" loop for processing tasks in /Needs_Action.

Core Philosophy (Ralph Wiggum Pattern):
- Keep it simple: analyze → plan → execute → repeat
- Iterate until all tasks complete or max iterations reached
- Multi-step tasks handled naturally through iteration

Loop Instruction:
"Process all files in /Needs_Action: analyze task, create detailed Plan.md 
in /Plans with steps, checkboxes, priorities. Execute if possible. 
Complete → add 'TASK_COMPLETE' and move to /Done. Flag payments >$500. 
Iterate max 10 times or until Needs_Action empty."

Usage:
------
python tools/ralph_loop_runner.py --max-iterations 10

Or with custom message:
python tools/ralph_loop_runner.py "Process Needs_Action" --max-iterations 5
"""

import os
import sys
import re
import shutil
import argparse
from datetime import datetime
from pathlib import Path

# Configuration
NEEDS_ACTION_DIR = Path(__file__).parent.parent / 'Needs_Action'
PLANS_DIR = Path(__file__).parent.parent / 'Plans'
DONE_DIR = Path(__file__).parent.parent / 'Done'
PENDING_APPROVAL_DIR = Path(__file__).parent.parent / 'Pending_Approval'
APPROVED_DIR = Path(__file__).parent.parent / 'Approved'
REJECTED_DIR = Path(__file__).parent.parent / 'Rejected'
LOGS_DIR = Path(__file__).parent.parent / 'Logs'
LOG_FILE = LOGS_DIR / 'ralph_loop.log'

DEFAULT_MAX_ITERATIONS = 10
PAYMENT_THRESHOLD = 500  # Flag payments above this amount

# Ensure directories exist
for directory in [PLANS_DIR, DONE_DIR, PENDING_APPROVAL_DIR, APPROVED_DIR, REJECTED_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


def log_message(message, level="INFO"):
    """Log message to file and console."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry + '\n')


def extract_payment_amount(content):
    """Extract payment amount from content."""
    # Match patterns like $500, $1,000, 500 USD, etc.
    patterns = [
        r'\$([\d,]+(?:\.\d{2})?)',
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|dollars?)',
        r'amount[:\s]+\$?([\d,]+(?:\.\d{2})?)',
        r'payment[:\s]+\$?([\d,]+(?:\.\d{2})?)',
        r'invoice[:\s]+\$?([\d,]+(?:\.\d{2})?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                return float(amount_str)
            except ValueError:
                continue
    return None


def analyze_task(filepath):
    """Analyze a task file and return task details."""
    log_message(f"Analyzing: {filepath.name}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract metadata from YAML frontmatter if present
    task_type = 'unknown'
    priority = 'medium'
    keywords = []
    
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 2:
            frontmatter = parts[1].lower()
            if 'type:' in frontmatter:
                type_match = re.search(r'type:\s*(\w+)', frontmatter)
                if type_match:
                    task_type = type_match.group(1)
            if 'priority:' in frontmatter:
                priority_match = re.search(r'priority:\s*(\w+)', frontmatter)
                if priority_match:
                    priority = priority_match.group(1)
            if 'keywords:' in frontmatter:
                kw_match = re.search(r'keywords:\s*(.+)', frontmatter)
                if kw_match:
                    keywords = [k.strip() for k in kw_match.group(1).split(',')]
    
    # Check for payment amount
    payment_amount = extract_payment_amount(content)
    requires_approval = payment_amount is not None and payment_amount > PAYMENT_THRESHOLD
    
    # Determine task category
    category = 'general'
    if any(kw in content.lower() for kw in ['sales', 'client', 'project', 'lead']):
        category = 'business_lead'
    elif any(kw in content.lower() for kw in ['invoice', 'payment', 'bill']):
        category = 'financial'
    elif any(kw in content.lower() for kw in ['urgent', 'asap', 'emergency']):
        category = 'urgent'
        priority = 'high'
    
    # Determine number of steps (simple heuristic)
    step_indicators = ['first', 'then', 'next', 'finally', 'step 1', 'step 2', 'phase']
    is_multistep = any(ind in content.lower() for ind in step_indicators)
    
    # Check if it's already complete
    is_complete = 'TASK_COMPLETE' in content
    
    return {
        'filepath': filepath,
        'content': content,
        'task_type': task_type,
        'priority': priority,
        'keywords': keywords,
        'payment_amount': payment_amount,
        'requires_approval': requires_approval,
        'category': category,
        'is_multistep': is_multistep,
        'is_complete': is_complete
    }


def create_plan(task):
    """Create a detailed plan for the task."""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    plan_filename = f"plan_{task['filepath'].stem}_{timestamp}.md"
    plan_filepath = PLANS_DIR / plan_filename
    
    # Generate action steps based on task category
    steps = []
    
    if task['category'] == 'business_lead':
        steps = [
            "Review lead details and keywords",
            "Determine service type and benefit",
            "Draft response or LinkedIn post",
            "Submit for HITL approval if needed",
            "Follow up or mark complete"
        ]
    elif task['category'] == 'financial':
        if task['requires_approval']:
            steps = [
                f"FLAG: Payment ${task['payment_amount']:.2f} exceeds ${PAYMENT_THRESHOLD} threshold",
                "Review invoice/payment details",
                "Submit to Pending_Approval for review",
                "Await approval decision",
                "Process payment or reject"
            ]
        else:
            steps = [
                "Review payment details",
                "Verify amount and recipient",
                "Process payment",
                "Mark complete"
            ]
    elif task['category'] == 'urgent':
        steps = [
            "IMMEDIATE: Review urgent task",
            "Prioritize over other tasks",
            "Take immediate action",
            "Confirm resolution",
            "Mark complete"
        ]
    else:
        steps = [
            "Review task details",
            "Identify required actions",
            "Execute actions",
            "Verify completion",
            "Mark complete"
        ]
    
    # Create plan content
    plan_content = f"""---
type: action_plan
task_source: {task['filepath'].name}
created: {datetime.now().isoformat()}
status: in_progress
priority: {task['priority']}
category: {task['category']}
is_multistep: {task['is_multistep']}
requires_approval: {task['requires_approval']}
---

# Action Plan: {task['filepath'].stem}

## Task Summary
- **Source:** `{task['filepath'].name}`
- **Type:** {task['task_type']}
- **Category:** {task['category']}
- **Priority:** {task['priority']}
- **Payment Amount:** {f"${task['payment_amount']:.2f}" if task['payment_amount'] else 'N/A'}
- **Requires Approval:** {'Yes ⚠️' if task['requires_approval'] else 'No'}

## Action Steps

"""
    
    for i, step in enumerate(steps, 1):
        checkbox = "[ ]" if not step.startswith("FLAG:") else "[!]"
        plan_content += f"{checkbox} **Step {i}:** {step}\n"
    
    plan_content += f"""

## Original Content

```
{task['content'][:1000]}{'...' if len(task['content']) > 1000 else ''}
```

---
*Generated by Ralph Wiggum Loop - Silver Tier*
*Iteration: [ITERATION_PLACEHOLDER]*
"""
    
    with open(plan_filepath, 'w', encoding='utf-8') as f:
        f.write(plan_content)
    
    log_message(f"Created plan: {plan_filepath.name}")
    return plan_filepath, plan_content


def execute_task(task, plan_filepath):
    """Execute the task based on its category."""
    log_message(f"Executing task: {task['filepath'].name}")
    
    result = {
        'executed': False,
        'destination': None,
        'output_file': None,
        'notes': []
    }
    
    try:
        if task['category'] == 'financial' and task['requires_approval']:
            # Flag for approval
            result['notes'].append(f"FLAGGED: Payment ${task['payment_amount']:.2f} > ${PAYMENT_THRESHOLD}")
            result['destination'] = 'pending_approval'
            result['executed'] = True
            
        elif task['category'] == 'business_lead':
            # Trigger Auto LinkedIn Poster skill
            result['notes'].append("Business lead detected - ready for LinkedIn poster")
            result['destination'] = 'pending_approval'  # HITL required
            result['executed'] = True
            
        elif task['category'] == 'urgent':
            # Mark for immediate attention
            result['notes'].append("URGENT: Requires immediate attention")
            result['destination'] = 'pending_approval'
            result['executed'] = True
            
        else:
            # General task - mark complete
            result['notes'].append("Task processed successfully")
            result['destination'] = 'done'
            result['executed'] = True
        
        # Add TASK_COMPLETE marker to content
        completed_content = task['content']
        if 'TASK_COMPLETE' not in completed_content:
            completed_content += f"\n\n---\n**TASK_COMPLETE** - {datetime.now().isoformat()}\n"
        
        # Move file to appropriate destination
        if result['destination'] == 'done':
            dest_dir = DONE_DIR
        elif result['destination'] == 'pending_approval':
            dest_dir = PENDING_APPROVAL_DIR
        elif result['destination'] == 'approved':
            dest_dir = APPROVED_DIR
        elif result['destination'] == 'rejected':
            dest_dir = REJECTED_DIR
        else:
            dest_dir = DONE_DIR  # Default
        
        # Create destination file with completed content
        dest_filename = f"{task['filepath'].stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{task['filepath'].suffix}"
        dest_filepath = dest_dir / dest_filename
        
        with open(dest_filepath, 'w', encoding='utf-8') as f:
            f.write(completed_content)
        
        result['output_file'] = str(dest_filepath)
        
        # Remove original file
        task['filepath'].unlink()
        log_message(f"Moved to /{dest_dir.name}/: {dest_filename}")
        
    except Exception as e:
        log_message(f"Error executing task: {e}", level="ERROR")
        result['notes'].append(f"Error: {e}")
    
    return result


def run_iteration(iteration_num, max_iterations):
    """Run a single iteration of the Ralph Wiggum loop."""
    log_message("=" * 60)
    log_message(f"ITERATION {iteration_num}/{max_iterations}")
    log_message("=" * 60)
    
    # Get all files in Needs_Action
    files = list(NEEDS_ACTION_DIR.glob('*'))
    files = [f for f in files if f.is_file() and not f.name.startswith('.')]
    
    if not files:
        log_message("No files in /Needs_Action - All tasks complete!")
        return True  # All done
    
    log_message(f"Found {len(files)} file(s) to process")
    
    iteration_results = []
    
    for filepath in files:
        try:
            # Step 1: Analyze
            task = analyze_task(filepath)
            
            # Skip if already complete
            if task['is_complete']:
                log_message(f"Skipping {filepath.name} - already complete")
                # Move to Done
                dest = DONE_DIR / filepath.name
                shutil.move(str(filepath), str(dest))
                continue
            
            # Step 2: Create Plan
            plan_filepath, plan_content = create_plan(task)
            
            # Update plan with iteration number
            plan_content = plan_content.replace('[ITERATION_PLACEHOLDER]', str(iteration_num))
            with open(plan_filepath, 'w', encoding='utf-8') as f:
                f.write(plan_content)
            
            # Step 3: Execute
            result = execute_task(task, plan_filepath)
            result['plan'] = str(plan_filepath)
            iteration_results.append(result)
            
        except Exception as e:
            log_message(f"Error processing {filepath.name}: {e}", level="ERROR")
    
    # Summary
    log_message("-" * 60)
    log_message(f"Iteration {iteration_num} Summary:")
    log_message(f"  Processed: {len(iteration_results)} task(s)")
    for i, r in enumerate(iteration_results, 1):
        log_message(f"  [{i}] {r.get('output_file', 'N/A')} -> {r.get('destination', 'unknown')}")
        for note in r.get('notes', []):
            log_message(f"      - {note}")
    
    # Check if all tasks are complete
    remaining = list(NEEDS_ACTION_DIR.glob('*'))
    remaining = [f for f in remaining if f.is_file() and not f.name.startswith('.')]
    
    if not remaining:
        log_message("=" * 60)
        log_message("TASK_COMPLETE - All files processed!")
        log_message("=" * 60)
        return True
    
    return False  # More iterations needed


def main():
    """Main entry point for Ralph Wiggum Loop Runner."""
    parser = argparse.ArgumentParser(
        description='Ralph Wiggum Reasoning Loop - Process tasks in /Needs_Action',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/ralph_loop_runner.py
  python tools/ralph_loop_runner.py --max-iterations 5
  python tools/ralph_loop_runner.py "Process Needs_Action" --max-iterations 10

Test the loop:
  1. Drop a test file in /Needs_Action/
  2. Run: python tools/ralph_loop_runner.py --max-iterations 10
  3. Check /Plans/, /Done/, /Pending_Approval/ for results
        """
    )
    
    parser.add_argument(
        'message',
        nargs='?',
        default='Process Needs_Action',
        help='Loop instruction message (default: "Process Needs_Action")'
    )
    
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
        help=f'Maximum number of iterations (default: {DEFAULT_MAX_ITERATIONS})'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Ralph Wiggum Reasoning Loop - Silver Tier")
    print("=" * 60)
    print(f"Instruction: {args.message}")
    print(f"Max Iterations: {args.max_iterations}")
    print(f"Input: /Needs_Action/")
    print(f"Output: /Plans/, /Done/, /Pending_Approval/")
    print("=" * 60)
    print()
    
    log_message(f"Starting Ralph Wiggum Loop: {args.message}")
    log_message(f"Max iterations: {args.max_iterations}")
    
    try:
        all_complete = False
        
        for iteration in range(1, args.max_iterations + 1):
            all_complete = run_iteration(iteration, args.max_iterations)
            
            if all_complete:
                print()
                print("=" * 60)
                print("SUCCESS: All tasks completed!")
                print("=" * 60)
                break
            
            if iteration < args.max_iterations:
                log_message(f"Continuing to iteration {iteration + 1}...")
                print()
        
        if not all_complete:
            log_message(f"Max iterations ({args.max_iterations}) reached")
            print()
            print("=" * 60)
            print(f"Note: Max iterations ({args.max_iterations}) reached")
            print("Some tasks may remain in /Needs_Action/")
            print("=" * 60)
        
        print()
        print("Loop execution complete.")
        print(f"Logs: {LOG_FILE}")
        
    except KeyboardInterrupt:
        print("\n\nLoop interrupted by user.")
        log_message("Loop interrupted by user", level="WARN")
    except Exception as e:
        log_message(f"Fatal error: {e}", level="ERROR")
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
