# Task Analyzer Skill

## Purpose
Analyze files in /Needs_Action, identify type (file drop, etc.), create simple action plan in Plan.md,
check if approval needed (e.g., payments or sensitive info), write to /Pending_Approval if sensitive,
use Ralph Wiggum loop if multi-step task.

## Instructions
1. Check /Needs_Action folder for any files
2. Analyze each file to identify its type (file drop, payment request, etc.)
3. Create simple action plan in Plan.md
4. Check if approval is needed (for payments or sensitive information)
5. If sensitive/payment > $500, write to /Pending_Approval
6. If multi-step task, use Ralph Wiggum loop (simple repeat until done)
7. Output success message with file paths

## Implementation Steps
- Scan /Needs_Action for files
- For each file:
  - Determine file type
  - Check for payment amounts or sensitive info
  - If payment > $500, flag for approval per Company Handbook
  - Create action plan in Plan.md
  - If multi-step, implement simple loop
  - Move to appropriate folder based on sensitivity
- Report success with file paths