# Email MCP Server - Silver Tier

## Overview
Node.js MCP server for drafting and sending emails via Gmail API with HITL (Human-In-The-Loop) approval workflow.

## Capabilities

| Tool | Description |
|------|-------------|
| `draft_email` | Create email draft saved as `.md` in `/Plans/` |
| `send_email` | Send email via Gmail API (requires approval) |
| `list_drafts` | List all email drafts |
| `approve_draft` | Approve draft for sending (HITL workflow) |

## Installation

```bash
cd mcp_servers/email-mcp
npm install
```

## Configuration

1. **Enable Gmail API:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Gmail API
   - Create OAuth 2.0 credentials
   - Download `credentials.json` to project root

2. **Place credentials:**
   - Copy `credentials.json` to `D:\giaic\hackhathone_0\AI-Employee-Project\`

## Run Server

```bash
node mcp_servers/email-mcp/index.js
```

## Test

```bash
node mcp_servers/email-mcp/test.js
```

## Usage Examples

### Draft an Email

```json
{
  "tool": "draft_email",
  "arguments": {
    "to": "client@example.com",
    "subject": "Project Proposal",
    "body": "Dear Client,\n\nPlease find attached our proposal...\n\nBest regards",
    "cc": "manager@company.com"
  }
}
```

**Output:** Draft saved to `/Plans/email_draft_2026-02-20T14-30-00.md`

### List Drafts

```json
{
  "tool": "list_drafts"
}
```

### Approve Draft (HITL)

```json
{
  "tool": "approve_draft",
  "arguments": {
    "filename": "email_draft_2026-02-20T14-30-00.md"
  }
}
```

### Send Email

```json
{
  "tool": "send_email",
  "arguments": {
    "to": "client@example.com",
    "subject": "Project Proposal",
    "body": "Dear Client,\n\nPlease find attached our proposal...\n\nBest regards"
  }
}
```

## HITL Workflow

```
1. draft_email → /Plans/email_draft_[date].md
2. Review draft content
3. Move to /Pending_Approval/ (if changes needed)
4. approve_draft → /Approved/
5. send_email → Email sent via Gmail API
```

## File Structure

```
mcp_servers/email-mcp/
├── index.js          # Main MCP server
├── package.json      # Dependencies
├── test.js           # Test script
└── README.md         # This file

Project Root:
├── mcp.json          # MCP server configuration
├── credentials.json  # Gmail API credentials (user-provided)
├── Plans/            # Email drafts
├── Pending_Approval/ # Drafts awaiting approval
└── Approved/         # Approved drafts ready to send
```

## Error Handling

| Error | Solution |
|-------|----------|
| `credentials.json not found` | Download from Google Cloud Console |
| `Authentication required` | Run OAuth flow to generate token.json |
| `Draft not found` | Check filename in /Plans/ directory |

## Logs

Server logs to stderr (console) when running. Check MCP client logs for tool call results.
