# Run Commands - AI Employee Project (Silver Tier)

Complete guide to running, stopping, and managing all components.

---

## Table of Contents

1. [Quick Start - Run Everything](#quick-start---run-everything)
2. [Individual Components](#individual-components)
3. [PM2 Management Commands](#pm2-management-commands)
4. [File System Impact](#file-system-impact)
5. [Troubleshooting](#troubleshooting)

---

## Quick Start - Run Everything

### Step 1: Install Dependencies (First Time Only)

```bash
cd D:\giaic\hackhathone_0\AI-Employee-Project

# Python dependencies
pip install -r requirements.txt
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib playwright
playwright install

# Node.js dependencies (for Email MCP)
cd mcp_servers\email-mcp
npm install
cd ../..
```

### Step 2: Start All Services with PM2

```bash
# Navigate to project root
cd D:\giaic\hackhathone_0\AI-Employee-Project

# Start Gmail Watcher
pm2 start watchers\gmail_watcher.py --name "gmail-watcher" --interpreter python

# Start WhatsApp Watcher
pm2 start watchers\whatsapp_watcher.py --name "whatsapp-watcher" --interpreter python

# Start LinkedIn Watcher
pm2 start watchers\linkedin_watcher.py --name "linkedin-watcher" --interpreter python

# Start Auto LinkedIn Poster Skill
pm2 start Skills\auto_linkedin_poster.py --name "linkedin-poster" --interpreter python

# Start HITL Approval Handler
pm2 start Skills\hitl_approval_handler.py --name "hitl-handler" --interpreter python

# Start Ralph Loop (Reasoning Loop)
pm2 start tools\ralph_loop_runner.py --name "ralph-loop" --interpreter python -- --max-iterations 5

# Save configuration for startup
pm2 save

# Setup PM2 to start on Windows boot
pm2 startup
```

### Step 3: View All Running Services

```bash
pm2 list
```

### Step 4: View All Logs

```bash
# All logs combined
pm2 logs

# Specific service logs
pm2 logs gmail-watcher
pm2 logs whatsapp-watcher
pm2 logs linkedin-watcher
pm2 logs linkedin-poster
pm2 logs hitl-handler
pm2 logs ralph-loop
```

---

## Individual Components

### 1. Gmail Watcher

**What it does:** Monitors Gmail for unread important emails with keywords (urgent, invoice, payment, sales). Creates `.md` files in `/Needs_Action/`.

| Action | Command |
|--------|---------|
| **Run manually** | `python watchers\gmail_watcher.py` |
| **Start with PM2** | `pm2 start watchers\gmail_watcher.py --name "gmail-watcher" --interpreter python` |
| **Stop** | `pm2 stop gmail-watcher` |
| **Restart** | `pm2 restart gmail-watcher` |
| **View logs** | `pm2 logs gmail-watcher` |
| **Delete from PM2** | `pm2 delete gmail-watcher` |

**What happens:**
- ✅ Browser opens for first-time authentication
- ✅ `token.json` saved for future runs
- ✅ Checks Gmail every 120 seconds
- ✅ Creates `.md` files in `/Needs_Action/` when matching emails found
- ✅ Logs activity to console/PM2 logs

**Files affected:**
- Creates: `/Needs_Action/gmail_*.md`
- Creates: `/token.json` (authentication)
- Logs: PM2 logs

---

### 2. WhatsApp Watcher

**What it does:** Monitors WhatsApp Web for unread messages with keywords. Creates `.md` files in `/Needs_Action/`.

| Action | Command |
|--------|---------|
| **Run manually** | `python watchers\whatsapp_watcher.py` |
| **Start with PM2** | `pm2 start watchers\whatsapp_watcher.py --name "whatsapp-watcher" --interpreter python` |
| **Stop** | `pm2 stop whatsapp-watcher` |
| **Restart** | `pm2 restart whatsapp-watcher` |
| **View logs** | `pm2 logs whatsapp-watcher` |
| **Delete from PM2** | `pm2 delete whatsapp-watcher` |

**What happens:**
- ✅ Browser opens with WhatsApp Web QR code
- ✅ Scan QR with your phone (first time only)
- ✅ Session saved to `/session/whatsapp/`
- ✅ Checks WhatsApp every 30 seconds
- ✅ Creates `.md` files in `/Needs_Action/` when matching messages found

**Files affected:**
- Creates: `/Needs_Action/whatsapp_*.md`
- Creates: `/session/whatsapp/` (browser session)
- Creates: `/watchers/.whatsapp_processed` (processed message tracking)

**Note:** Browser window must stay open. For production, use WhatsApp Business API.

---

### 3. LinkedIn Watcher

**What it does:** Monitors LinkedIn for business leads (messages/notifications with keywords: sales, client, project). Creates `.md` files in `/Needs_Action/`.

| Action | Command |
|--------|---------|
| **Run manually** | `python watchers\linkedin_watcher.py` |
| **Start with PM2** | `pm2 start watchers\linkedin_watcher.py --name "linkedin-watcher" --interpreter python` |
| **Stop** | `pm2 stop linkedin-watcher` |
| **Restart** | `pm2 restart linkedin-watcher` |
| **View logs** | `pm2 logs linkedin-watcher` |
| **Delete from PM2** | `pm2 delete linkedin-watcher` |

**What happens:**
- ✅ Browser opens to LinkedIn
- ✅ Log in (first time only)
- ✅ Session saved to `/session/linkedin/`
- ✅ Checks LinkedIn every 60 seconds
- ✅ Creates `.md` files in `/Needs_Action/` for business leads

**Files affected:**
- Creates: `/Needs_Action/linkedin_*.md`
- Creates: `/session/linkedin/` (browser session)
- Creates: `/watchers/.linkedin_processed` (processed notification tracking)

---

### 4. Auto LinkedIn Poster Skill

**What it does:** Scans `/Needs_Action/` for sales leads, drafts LinkedIn posts, saves to `/Plans/`, moves to `/Pending_Approval/` for HITL review.

| Action | Command |
|--------|---------|
| **Run manually** | `python Skills\auto_linkedin_poster.py` |
| **Start with PM2** | `pm2 start Skills\auto_linkedin_poster.py --name "linkedin-poster" --interpreter python` |
| **Stop** | `pm2 stop linkedin-poster` |
| **Restart** | `pm2 restart linkedin-poster` |
| **View logs** | `pm2 logs linkedin-poster` |
| **Delete from PM2** | `pm2 delete linkedin-poster` |

**What happens:**
- ✅ Scans `/Needs_Action/` for files with keywords (sales, client, project)
- ✅ Extracts service/benefit from lead content
- ✅ Drafts LinkedIn post following Company Handbook (polite language)
- ✅ Saves draft to `/Plans/linkedin_post_[date].md`
- ✅ Moves to `/Pending_Approval/` for human review

**Files affected:**
- Reads: `/Needs_Action/*.md`
- Creates: `/Plans/linkedin_post_*.md`
- Creates: `/Pending_Approval/linkedin_post_*.md`
- Logs: `/Logs/linkedin_poster.log`

---

### 5. HITL Approval Handler

**What it does:** Monitors `/Pending_Approval/` for items awaiting human approval. On APPROVE → executes action and moves to `/Approved/`. On REJECT → moves to `/Rejected/`.

| Action | Command |
|--------|---------|
| **Run manually** | `python Skills\hitl_approval_handler.py` |
| **Start with PM2** | `pm2 start Skills\hitl_approval_handler.py --name "hitl-handler" --interpreter python` |
| **Stop** | `pm2 stop hitl-handler` |
| **Restart** | `pm2 restart hitl-handler` |
| **View logs** | `pm2 logs hitl-handler` |
| **Delete from PM2** | `pm2 delete hitl-handler` |

**What happens:**
- ✅ Scans `/Pending_Approval/` every 30 seconds
- ✅ Checks for approval decisions in files (APPROVED/REJECTED)
- ✅ On APPROVE: Executes action (email send, post publish) and moves to `/Approved/`
- ✅ On REJECT: Moves to `/Rejected/` with reason
- ✅ Logs all actions to `/Logs/hitl_[date].md`

**Files affected:**
- Reads: `/Pending_Approval/*.md`
- Moves to: `/Approved/*.md` (on approval)
- Moves to: `/Rejected/*.md` (on rejection)
- Logs: `/Logs/hitl_YYYY-MM-DD.md`

---

### 6. Ralph Wiggum Reasoning Loop

**What it does:** Processes all files in `/Needs_Action/`. Analyzes tasks, creates plans in `/Plans/`, executes or routes to HITL. Iterates until complete (max 10 iterations).

| Action | Command |
|--------|---------|
| **Run manually** | `python tools\ralph_loop_runner.py --max-iterations 10` |
| **With custom message** | `python tools\ralph_loop_runner.py "Process Needs_Action" --max-iterations 10` |
| **Start with PM2** | `pm2 start tools\ralph_loop_runner.py --name "ralph-loop" --interpreter python -- --max-iterations 5` |
| **Stop** | `pm2 stop ralph-loop` |
| **Restart** | `pm2 restart ralph-loop` |
| **View logs** | `pm2 logs ralph-loop` |
| **Delete from PM2** | `pm2 delete ralph-loop` |

**What happens:**
- ✅ Scans `/Needs_Action/` for files
- ✅ Analyzes each file (type, priority, category, payment amount)
- ✅ Creates action plan in `/Plans/plan_*.md`
- ✅ Executes simple tasks → moves to `/Done/`
- ✅ Flags payments >$500 → moves to `/Pending_Approval/`
- ✅ Detects business leads → moves to `/Pending_Approval/`
- ✅ Adds `TASK_COMPLETE` marker to processed files
- ✅ Iterates until `/Needs_Action/` is empty or max iterations reached

**Files affected:**
- Reads: `/Needs_Action/*.md`
- Creates: `/Plans/plan_*.md`
- Moves to: `/Done/*.md` (completed tasks)
- Moves to: `/Pending_Approval/*.md` (requires approval)
- Logs: `/Logs/ralph_loop.log`

---

### 7. Email MCP Server

**What it does:** MCP server for drafting and sending emails via Gmail API with HITL approval workflow.

| Action | Command |
|--------|---------|
| **Run server** | `node mcp_servers\email-mcp\index.js` |
| **Test server** | `node mcp_servers\email-mcp\test.js` |
| **Install dependencies** | `cd mcp_servers\email-mcp && npm install` |

**What happens:**
- ✅ Starts MCP server on stdio
- ✅ Provides tools: `draft_email`, `send_email`, `list_drafts`, `approve_draft`
- ✅ Drafts saved to `/Plans/email_draft_*.md`
- ✅ Sends emails via Gmail API (after approval)

**Files affected:**
- Creates: `/Plans/email_draft_*.md`
- Creates: `/token.json` (Gmail authentication)
- Reads: `credentials.json` (Gmail API credentials)

**Note:** Requires `credentials.json` from Google Cloud Console.

---

### 8. Daily Scheduler

**What it does:** Runs daily at 8:00 AM to generate summary from `/Done/` files. Creates daily report in `/Logs/daily_summary_[date].md`.

#### Windows (PowerShell)

| Action | Command |
|--------|---------|
| **Run manually** | `cd schedulers\daily_scheduler && .\daily_scheduler.ps1` |
| **Setup Task Scheduler** | See setup instructions below |

#### Linux/Mac (Shell)

| Action | Command |
|--------|---------|
| **Run manually** | `chmod +x schedulers/daily_scheduler.sh && ./schedulers/daily_scheduler.sh` |
| **Setup cron** | `crontab -e` → `0 8 * * * /full/path/to/schedulers/daily_scheduler.sh` |

**What happens:**
- ✅ Counts files in `/Done/`
- ✅ Lists recently completed tasks
- ✅ Counts pending approvals
- ✅ Creates daily summary in `/Logs/daily_summary_[date].md`
- ✅ Logs run to `/Logs/scheduler.log`

**Files affected:**
- Reads: `/Done/*.md`
- Creates: `/Logs/daily_summary_YYYY-MM-DD.md`
- Logs: `/Logs/scheduler.log`

---

## PM2 Management Commands

### Start Services

```bash
# Start single service
pm2 start <script> --name "<name>" --interpreter python

# Start with arguments
pm2 start tools\ralph_loop_runner.py --name "ralph-loop" --interpreter python -- --max-iterations 5

# Start all at once (create ecosystem.config.js)
pm2 start ecosystem.config.js
```

### View Status

```bash
# List all services
pm2 list

# Detailed info on specific service
pm2 show gmail-watcher

# View logs
pm2 logs

# View logs for specific service
pm2 logs gmail-watcher --lines 100
```

### Stop Services

```bash
# Stop single service
pm2 stop gmail-watcher

# Stop all services
pm2 stop all
```

### Restart Services

```bash
# Restart single service
pm2 restart gmail-watcher

# Restart all services
pm2 restart all

# Restart with no delay
pm2 restart all --no-daemon
```

### Delete Services

```bash
# Delete single service from PM2
pm2 delete gmail-watcher

# Delete all services from PM2
pm2 delete all
```

### Monitor Services

```bash
# Real-time monitoring dashboard
pm2 monit

# View logs in real-time
pm2 logs --lines 1000

# View specific log level
pm2 logs --err --lines 100
```

### Save for Startup

```bash
# Save current process list for respawn after reboot
pm2 save

# Setup PM2 to start on system boot (Windows)
pm2 startup

# Setup PM2 to start on system boot (Linux/Mac)
pm2 startup systemd
```

### Advanced Commands

```bash
# Scale a service (run multiple instances)
pm2 scale gmail-watcher 2

# Update environment variables
pm2 set pm2_log_date_format YYYY-MM-DD HH:mm:ss

# Reload all services (zero downtime)
pm2 reload all

# Flush logs
pm2 flush
```

---

## File System Impact

### When You Run Commands, Here's What Changes:

| Command | Files Created | Files Modified | Files Moved |
|---------|---------------|----------------|-------------|
| `gmail_watcher.py` | `/Needs_Action/gmail_*.md`, `/token.json` | - | - |
| `whatsapp_watcher.py` | `/Needs_Action/whatsapp_*.md`, `/session/whatsapp/*` | `/watchers/.whatsapp_processed` | - |
| `linkedin_watcher.py` | `/Needs_Action/linkedin_*.md`, `/session/linkedin/*` | `/watchers/.linkedin_processed` | - |
| `auto_linkedin_poster.py` | `/Plans/linkedin_post_*.md`, `/Pending_Approval/linkedin_post_*.md` | - | Needs_Action → Pending_Approval |
| `hitl_approval_handler.py` | `/Approved/*.md` or `/Rejected/*.md`, `/Logs/hitl_*.md` | - | Pending_Approval → Approved/Rejected |
| `ralph_loop_runner.py` | `/Plans/plan_*.md`, `/Logs/ralph_loop.log` | - | Needs_Action → Done/Pending_Approval |
| `email-mcp/index.js` | `/Plans/email_draft_*.md`, `/token.json` | - | - |
| `daily_scheduler.ps1` | `/Logs/daily_summary_*.md` | `/Logs/scheduler.log` | - |

### Directory Structure After Running

```
AI-Employee-Project/
├── Needs_Action/       # New files from watchers
├── Plans/              # Action plans, email drafts, LinkedIn drafts
├── Pending_Approval/   # Items awaiting human approval
├── Approved/           # Approved and executed items
├── Rejected/           # Rejected items
├── Done/               # Completed tasks
├── Logs/               # All activity logs
│   ├── ralph_loop.log
│   ├── hitl_YYYY-MM-DD.md
│   ├── daily_summary_YYYY-MM-DD.md
│   ├── scheduler.log
│   └── Silver_Complete.md
├── session/            # Browser sessions (WhatsApp, LinkedIn)
│   ├── whatsapp/
│   └── linkedin/
├── watchers/           # Processed tracking files
│   ├── .whatsapp_processed
│   └── .linkedin_processed
└── token.json          # Gmail API token
```

---

## Complete Workflow Example

### Scenario: Receive Email → Process → Approve → Send

```bash
# 1. Start Gmail Watcher
pm2 start watchers\gmail_watcher.py --name "gmail-watcher" --interpreter python

# 2. Wait for email to arrive (or send test email)
# Email arrives → /Needs_Action/gmail_*.md created

# 3. Run Ralph Loop to process
python tools\ralph_loop_runner.py --max-iterations 3
# Result: Plan created, file moved to /Pending_Approval/

# 4. Check Pending_Approval
# Open file, add decision:
# Decision: [APPROVED]
# Reviewed by: Your Name

# 5. Run HITL Handler
python Skills\hitl_approval_handler.py
# Result: Action executed, file moved to /Approved/

# 6. Check logs
pm2 logs hitl-handler
cat Logs/hitl_*.md
```

---

## Troubleshooting

### Common Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError` | Missing Python package | `pip install -r requirements.txt` |
| `credentials.json not found` | Missing Gmail credentials | Download from Google Cloud Console |
| `playwright not installed` | Playwright browsers missing | `playwright install` |
| `pm2: command not found` | PM2 not installed | `npm install -g pm2` |
| WhatsApp QR not showing | Session corrupted | Delete `/session/whatsapp/` and restart |
| LinkedIn login fails | Session corrupted | Delete `/session/linkedin/` and restart |
| Service won't start | Port already in use | `pm2 stop all && pm2 start all` |
| Logs not appearing | Log file locked | `pm2 flush` |

### Reset Everything

```bash
# Stop all services
pm2 stop all
pm2 delete all

# Clear sessions
rmdir /s /q session
rmdir /s /q watchers\.whatsapp_processed
rmdir /s /q watchers\.linkedin_processed

# Restart fresh
pm2 start watchers\gmail_watcher.py --name "gmail-watcher" --interpreter python
# ... restart other services as needed
```

### Check Service Health

```bash
# View all services status
pm2 list

# Check CPU/Memory usage
pm2 monit

# View error logs only
pm2 logs --err

# Test Python scripts manually
python watchers\gmail_watcher.py
python Skills\hitl_approval_handler.py
```

---

## Quick Reference Card

### Start All Services
```bash
cd D:\giaic\hackhathone_0\AI-Employee-Project
pm2 start watchers\gmail_watcher.py --name "gmail-watcher" --interpreter python
pm2 start watchers\whatsapp_watcher.py --name "whatsapp-watcher" --interpreter python
pm2 start watchers\linkedin_watcher.py --name "linkedin-watcher" --interpreter python
pm2 start Skills\auto_linkedin_poster.py --name "linkedin-poster" --interpreter python
pm2 start Skills\hitl_approval_handler.py --name "hitl-handler" --interpreter python
pm2 start tools\ralph_loop_runner.py --name "ralph-loop" --interpreter python -- --max-iterations 5
pm2 save
```

### View Everything
```bash
pm2 list      # Status
pm2 logs      # All logs
pm2 monit     # Dashboard
```

### Stop Everything
```bash
pm2 stop all
```

### Start Everything Again
```bash
pm2 start all
```

### Complete Reset
```bash
pm2 stop all
pm2 delete all
pm2 flush
```

---

**Last Updated:** 2026-02-20  
**Tier:** Silver  
**Status:** Complete ✅
