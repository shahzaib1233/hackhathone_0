# Basic File Handler Skill

## Purpose
Read any .md file from /Needs_Action and summarize its content.
Write Plan.md in /Plans with simple checkboxes for next steps.
Move completed files to /Done folder.
Always reference Company_Handbook.md rules before any action.

## Instructions
1. Check /Needs_Action folder for any .md files
2. Read each file and summarize its content
3. Create or update Plan.md in /Plans with checkboxes for next steps
4. Move processed files to /Done folder
5. Always reference Company_Handbook.md rules before taking any action
6. Output success message with full file paths

## Implementation Steps
- Scan /Needs_Action for .md files
- For each file:
  - Read content
  - Summarize key points
  - Create action items in Plan.md
  - Move file to /Done
  - Confirm Company Handbook compliance
- Report success with file paths