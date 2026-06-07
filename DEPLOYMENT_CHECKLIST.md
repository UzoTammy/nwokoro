# Deployment Checklist: Fix Orphaned Investments to Heroku

## Pre-Deployment (Local Machine)

### Step 1: Verify the fix works locally ✓ DONE
- [x] Management command created: `fix_orphaned_investments.py`
- [x] Tested locally: Successfully created 11 missing CR transactions
- [x] Verified with `verify_business_logic`: All investments now have transactions

### Step 2: Ensure all files are committed to Git
```bash
# Check git status
git status

# Files to commit:
# - networth/management/__init__.py
# - networth/management/commands/__init__.py
# - networth/management/commands/fix_orphaned_investments.py
# - networth/management/commands/verify_business_logic.py

# Stage files
git add networth/management/

# Commit with message
git commit -m "Add management commands: fix orphaned investments and verify business logic"

# Verify commit
git log --oneline -5
```

---

## Deployment to Heroku

### Step 3: Prepare for deployment
```bash
# Verify Heroku CLI is installed
heroku --version

# Login to Heroku (if not already logged in)
heroku login

# List your apps to confirm app name
heroku apps

# Set the app name (replace with your actual app name)
# You can also set this as default:
heroku apps:set --app=your-app-name
```

### Step 4: Create database backup (CRITICAL)
```bash
# This creates a backup of your production database
heroku pg:backups:capture --app=your-app-name

# Verify backup was created
heroku pg:backups --app=your-app-name

# Note: Keep this backup ID in case we need to rollback
```

### Step 5: Push code to Heroku
```bash
# Push to Heroku (this automatically deploys)
git push heroku main
# or if your branch is different:
# git push heroku your-branch-name:main

# Wait for deployment to complete
# You should see: "remote: Verifying deploy... done."
```

### Step 6: Run the management command on Heroku (DRY RUN first)
```bash
# First, run WITHOUT --fix to see what will be changed (RECOMMENDED)
heroku run "python manage.py fix_orphaned_investments" --app=your-app-name

# This will show:
# - Total investments: 32
# - Investments with CR transactions: 21
# - Orphaned investments: 11
# - List of all 11 orphaned investments

# Take note of the output and verify it matches local results
```

### Step 7: Run the fix command (WITH --fix flag)
```bash
# Now actually apply the fix
heroku run "python manage.py fix_orphaned_investments --fix" --app=your-app-name

# Watch the output - you should see:
# ✓ Created CR transaction for Investment X
# [for each of 11 investments]
# ✓ All investments now have CR transactions!
```

---

## Post-Deployment Verification

### Step 8: Verify the fix worked on production
```bash
# Run the business logic verification command
heroku run "python manage.py verify_business_logic" --app=your-app-name

# Look for:
# TEST 5: Data Integrity Checks
# ✓ No orphaned investment transactions
# ✓ All investments have associated transactions
```

### Step 9: Check application logs for errors
```bash
# View recent logs (last 100 lines)
heroku logs --tail --app=your-app-name

# If you see any errors, note them and investigate
```

### Step 10: Manual verification in application
1. Open your deployed application: `https://your-app-name.herokuapp.com`
2. Login as user "Nwokoro"
3. Navigate to Networth dashboard
4. Check "Investment Score" card:
   - Verify "This Year" and "All Time" metrics are displayed
   - Verify Yield percentages (should be 9.5% and 10.3% respectively)
   - Verify "Unrealised Earnings" shows 58.6% completion

---

## Rollback Procedures (If Issues Occur)

### Option 1: Rollback to Previous Release
```bash
# View release history
heroku releases --app=your-app-name

# Rollback to previous release
heroku releases:rollback --app=your-app-name

# Verify rollback completed
heroku logs --app=your-app-name | head -20
```

### Option 2: Restore from Database Backup
```bash
# List available backups
heroku pg:backups --app=your-app-name

# Restore from backup (WARNING: This restores the entire database)
# First, note the backup ID from earlier
heroku pg:backups:restore <BACKUP_ID> DATABASE --app=your-app-name --confirm your-app-name

# This will restore the database to state before the fix
# You'll need to redeploy the application code
```

---

## Troubleshooting

### Command timeout on Heroku
If the command times out (rare - command runs in ~2 seconds):
```bash
# Run with longer timeout
heroku run "timeout 30 python manage.py fix_orphaned_investments --fix" --app=your-app-name
```

### Database connection errors
```bash
# Check database status
heroku pg:info --app=your-app-name

# Restart database if needed
heroku restart --app=your-app-name
```

### View command output in detail
```bash
# Redirect output to file if output is cut off
heroku run "python manage.py fix_orphaned_investments --fix > /tmp/fix_output.txt 2>&1" --app=your-app-name
heroku run "cat /tmp/fix_output.txt" --app=your-app-name
```

---

## Final Checklist

- [ ] Code committed to Git
- [ ] Database backup created (`heroku pg:backups`)
- [ ] Code pushed to Heroku (`git push heroku main`)
- [ ] Dry run executed (without --fix flag)
- [ ] Fix command executed (with --fix flag)
- [ ] Business logic verification passed
- [ ] No errors in Heroku logs
- [ ] Manual verification in application successful
- [ ] Team notified of successful deployment

---

## Command Reference

| Command | Purpose |
|---------|---------|
| `heroku --version` | Check Heroku CLI version |
| `heroku login` | Authenticate with Heroku |
| `heroku apps` | List your Heroku apps |
| `heroku pg:backups:capture` | Create database backup |
| `heroku pg:backups` | List all backups |
| `git push heroku main` | Deploy code to Heroku |
| `heroku run "command"` | Run one-off command on Heroku |
| `heroku logs --tail` | Stream live logs |
| `heroku releases` | View deployment history |
| `heroku releases:rollback` | Rollback to previous release |
| `heroku pg:info` | Check database status |

---

## Estimated Timeline

- Code review & testing: ✓ (already done)
- Git commit & push: 2-3 minutes
- Heroku deployment: 2-5 minutes
- Database backup: 1-2 minutes
- Dry run: 30 seconds
- Fix execution: 2-3 seconds
- Verification: 2-3 minutes

**Total: ~10-15 minutes**

---

## Success Criteria

✅ All 11 missing CR transactions created  
✅ No errors in application logs  
✅ Investment Score metrics displaying correctly  
✅ All investments have transaction records  
✅ Yield calculations accurate and complete
