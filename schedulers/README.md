# Daily Scheduler - Silver Tier

## Overview
Automated daily scheduler that runs at 8:00 AM to generate summaries from completed tasks in `/Done/`.

## Files

| Platform | Script |
|----------|--------|
| Linux/Mac | `schedulers/daily_scheduler.sh` |
| Windows | `schedulers/daily_scheduler/daily_scheduler.ps1` |

## Setup Instructions

### Linux/Mac (cron)

1. **Make script executable:**
   ```bash
   chmod +x schedulers/daily_scheduler.sh
   ```

2. **Edit crontab:**
   ```bash
   crontab -e
   ```

3. **Add cron entry:**
   ```
   0 8 * * * /full/path/to/AI-Employee-Project/schedulers/daily_scheduler.sh
   ```

4. **Verify cron job:**
   ```bash
   crontab -l
   ```

5. **Check cron logs (if needed):**
   ```bash
   # Ubuntu/Debian
   grep CRON /var/log/syslog
   
   # Mac
   log show --predicate 'process == "cron"' --last 1h
   ```

### Windows (Task Scheduler)

#### Method 1: Using GUI

1. **Open Task Scheduler:**
   - Press `Win + R`
   - Type `taskschd.msc`
   - Press Enter

2. **Create Basic Task:**
   - Click "Create Basic Task..." in right panel
   - Name: `AI Employee Daily Scheduler`
   - Description: `Generates daily summary from /Done files`

3. **Set Trigger:**
   - Select "Daily"
   - Start time: `8:00:00 AM`
   - Recur every: `1` days

4. **Set Action:**
   - Select "Start a program"
   - Program/script: `powershell.exe`
   - Add arguments: `-ExecutionPolicy Bypass -File "D:\giaic\hackhathone_0\AI-Employee-Project\schedulers\daily_scheduler\daily_scheduler.ps1"`
   - Start in: `D:\giaic\hackhathone_0\AI-Employee-Project\schedulers\daily_scheduler`

5. **Finish and Test:**
   - Click Finish
   - Right-click the task → "Run" to test

#### Method 2: Using PowerShell (Automated)

Run this PowerShell script as Administrator:

```powershell
$taskName = "AI Employee Daily Scheduler"
$scriptPath = "D:\giaic\hackhathone_0\AI-Employee-Project\schedulers\daily_scheduler\daily_scheduler.ps1"
$workingDir = "D:\giaic\hackhathone_0\AI-Employee-Project\schedulers\daily_scheduler"

# Create scheduled task action
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"$scriptPath`"" `
    -WorkingDirectory $workingDir

# Create trigger (daily at 8 AM)
$trigger = New-ScheduledTaskTrigger -Daily -At 8:00AM

# Create settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false

# Register the task
Register-ScheduledTask -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Generates daily summary from /Done files at 8 AM daily"

Write-Host "Task '$taskName' created successfully!"
```

## Test Manually

### Linux/Mac
```bash
cd schedulers
./daily_scheduler.sh
```

### Windows
```powershell
cd schedulers\daily_scheduler
.\daily_scheduler.ps1
```

## Output

### Generated Files

| File | Location |
|------|----------|
| Daily Summary | `/Logs/daily_summary_YYYY-MM-DD.md` |
| Scheduler Log | `/Logs/scheduler.log` |

### Summary Format

```markdown
---
type: daily_summary
date: 2026-02-20
generated: 2026-02-20T08:00:00
files_processed: 5
status: complete
---

# Daily Summary - 2026-02-20

## Overview
- **Generated:** 2026-02-20 08:00:00
- **Files Processed:** 5
- **Status:** Complete

## Files Completed Today
| File | Type | Modified |
|------|------|----------|
| task_001.md | email | 2026-02-20 |

## Activity Summary
### Tasks Completed
- Total files in /Done/: 5

### Pending Actions
- Pending Approval: 2
```

## Troubleshooting

### Linux/Mac

| Issue | Solution |
|-------|----------|
| Script not running | Check cron daemon: `sudo systemctl status cron` |
| Permission denied | Run: `chmod +x daily_scheduler.sh` |
| Path issues | Use absolute paths in crontab |

### Windows

| Issue | Solution |
|-------|----------|
| PowerShell execution policy | Use `-ExecutionPolicy Bypass` flag |
| Task not triggering | Check "Run whether user is logged on or not" |
| Script errors | Run PowerShell as Administrator |

## Customization

### Change Schedule Time

**Linux/Mac (cron):**
```
# Change from 8 AM to 9 AM
0 8 * * * ...  →  0 9 * * * ...
```

**Windows (PowerShell):**
```powershell
# Change -At 8:00AM to -At 9:00AM
$trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM
```

### Change Summary Location

Edit the `SUMMARY_FILE` (Linux) or `$SummaryFile` (Windows) variable in the script.

## Integration

Works with other Silver Tier skills:
- **Ralph Loop:** Processes tasks that get moved to /Done/
- **HITL Handler:** Approved items logged in summary
- **Task Analyzer:** Completed tasks summarized daily
