# 🚀 CaptPathfinder - Production Deployment Guide

**One comprehensive guide to deploy CaptPathfinder 100% serverless on Supabase.**

---

## 📋 What You'll Deploy

```
inSided (Gainsight Community)
     ↓ webhook
Supabase Edge Functions
     ↓
PostgreSQL (classification + processing)
     ↓ pg_cron (scheduled)
Automation Anywhere Bots
     ↓
Email & Teams notifications ✉️
```

**Total Cost: ~$25/month** (just Supabase Pro)

---

## ✅ Prerequisites

- [ ] Supabase account (sign up at https://supabase.com)
- [ ] Supabase CLI installed: `npm install -g supabase`
- [ ] inSided (Gainsight Community) admin access
- [ ] Automation Anywhere Control Room access
- [ ] AA email and Teams bots created

---

## 📝 Complete Deployment Steps

### Step 1: Setup Supabase Project (5 minutes)

#### 1.1 Create Project

1. Go to https://app.supabase.com
2. Click **New Project**
3. Choose organization
4. Set project name: `captpathfinder`
5. Generate database password (save it!)
6. Select region: US East (or closest to you)
7. Click **Create Project**
8. Wait ~2 minutes for provisioning

#### 1.2 Get Database Connection String

1. In your project, go to **Settings** (⚙️)
2. Click **Database**
3. Scroll to **Connection String** section
4. Select **URI** tab
5. Click **Copy** 📋
6. Save this - you'll need it!

#### 1.3 Enable pg_cron (Pro Plan Required)

**Note:** pg_cron requires Supabase Pro plan ($25/month)

1. Go to **Settings** → **Billing**
2. Upgrade to Pro if needed
3. pg_cron will be automatically available

---

### Step 2: Run Database Migrations (3 minutes)

Open your terminal and run these commands **in order**:

```bash
# Set your connection string
export SUPABASE_DB_URL="<paste-connection-string-from-step-1.2>"

# Run migration 1: Create tables
psql $SUPABASE_DB_URL -f migrations/001_initial_schema.sql

# Run migration 2: Add classification & processing functions
psql $SUPABASE_DB_URL -f migrations/002_serverless_functions.sql

# Run migration 3: Setup cron jobs
psql $SUPABASE_DB_URL -f scripts/create_functions.sql
```

**Verify tables created:**
```sql
psql $SUPABASE_DB_URL -c "\dt"
```

You should see: `field_registry`, `events_raw`, `user_state`, `detections`, `digests`, `reports`

---

### Step 3: Deploy Supabase Edge Functions (5 minutes)

#### 3.1 Login to Supabase CLI

```bash
supabase login
```

This will open a browser for authentication.

#### 3.2 Link Your Project

```bash
# Get your project ref from URL: https://app.supabase.com/project/YOUR_PROJECT_REF
supabase link --project-ref YOUR_PROJECT_REF
```

#### 3.3 Deploy Edge Functions

```bash
# Navigate to functions directory
cd supabase/functions

# Deploy webhook handler (receives inSided webhooks)
supabase functions deploy webhook-handler

# Deploy digest sender (sends AA bot notifications)
supabase functions deploy send-digests
```

**Your webhook URL will be:**
```
https://YOUR_PROJECT_REF.supabase.co/functions/v1/webhook-handler
```

---

### Step 4: Configure Automation Anywhere (10 minutes)

#### 4.1 Get AA Control Room Details

You need:
- Control Room URL: `https://your-instance.automationanywhere.digital`
- Username: Your AA login username
- API Key: Generate from Control Room

**To generate API Key:**
1. Log into AA Control Room
2. Go to **My Settings** → **My Credentials**
3. Click **Generate API Key**
4. Copy immediately (won't be shown again)

#### 4.2 Get Bot IDs

For each bot (email and Teams):
1. Go to **Automation** tab in Control Room
2. Find your bot
3. Note the **Bot ID** (numeric ID visible in bot list or URL)
4. Example: `12345` or `67890`

#### 4.3 Set Supabase Secrets

```bash
# Set AA credentials as Supabase secrets
supabase secrets set AA_CONTROL_ROOM_URL=https://your-instance.automationanywhere.digital
supabase secrets set AA_USERNAME=your-username
supabase secrets set AA_API_KEY=your-api-key-from-step-4.1
supabase secrets set AA_EMAIL_BOT_ID=12345
supabase secrets set AA_TEAMS_BOT_ID=67890

# Optional: Override auth endpoint if needed
# supabase secrets set AA_AUTH_ENDPOINT=https://your-custom-endpoint.com/v2/authentication
```

**Verify secrets:**
```bash
supabase secrets list
```

---

### Step 5: Configure pg_cron for Weekly Digests (2 minutes)

Run this SQL to setup weekly digest job:

```sql
-- Get your project ref from Supabase dashboard URL
-- Replace YOUR_PROJECT_REF below with your actual project ref

SELECT cron.schedule(
    'weekly-digest-sender',
    '0 17 * * FRI',  -- Friday 5 PM EST
    $$
    SELECT net.http_post(
        url := 'https://YOUR_PROJECT_REF.supabase.co/functions/v1/send-digests',
        headers := '{"Content-Type": "application/json"}'::jsonb
    );
    $$
);
```

Run this command:
```bash
psql $SUPABASE_DB_URL -c "SELECT cron.schedule('weekly-digest-sender', '0 17 * * FRI', \$\$SELECT net.http_post(url := 'https://YOUR_PROJECT_REF.supabase.co/functions/v1/send-digests', headers := '{\"Content-Type\": \"application/json\"}'::jsonb);\$\$);"
```

**Don't forget to replace `YOUR_PROJECT_REF`!**

---

### Step 6: Configure inSided Webhooks (5 minutes)

#### 6.1 Get inSided API Key

1. Log into your inSided (Gainsight Community) admin panel
2. Go to **Admin** → **Settings** → **API**
3. Click **Generate API Key**
4. Copy the key

#### 6.2 Create Webhook in inSided

1. **Admin** → **Settings** → **Webhooks** or **Integrations**
2. Click **Create New Webhook**
3. Configure:
   - **Name**: `CaptPathfinder Senior Exec Detection`
   - **URL**: `https://YOUR_PROJECT_REF.supabase.co/functions/v1/webhook-handler`
   - **Method**: `POST`
   - **Event Type**: `integration.UserProfileUpdated`
   - **Headers**: `Content-Type: application/json`
4. Click **Save**

---

### Step 7: Test the System (10 minutes)

#### 7.1 Test Webhook Receipt

```bash
# Replace YOUR_PROJECT_REF with your actual project ref
curl -X POST \
  https://YOUR_PROJECT_REF.supabase.co/functions/v1/webhook-handler \
  -H "Content-Type: application/json" \
  -d '{
    "event": "integration.UserProfileUpdated",
    "userId": "test-123",
    "username": "Test User",
    "profileField": "Job Title",
    "value": "Chief Executive Officer",
    "oldValue": "Director"
  }'
```

**Expected Response:**
```json
{"status":"accepted","event_id":1}
```

#### 7.2 Check Event Stored

```bash
psql $SUPABASE_DB_URL -c "SELECT * FROM events_raw ORDER BY received_at DESC LIMIT 5;"
```

You should see your test event.

#### 7.3 Wait 1 Minute (pg_cron processes events)

The `process-pending-events` cron job runs every minute.

After 1 minute, check:

```bash
# Check if event was processed
psql $SUPABASE_DB_URL -c "SELECT * FROM events_raw WHERE processed = TRUE;"

# Check if detection was created
psql $SUPABASE_DB_URL -c "SELECT * FROM detections ORDER BY detected_at DESC LIMIT 5;"

# Check user_state
psql $SUPABASE_DB_URL -c "SELECT * FROM user_state;"
```

You should see:
- Event marked as `processed = TRUE`
- Detection record created
- User in `user_state` table with `seniority_level = 'csuite'`

#### 7.4 Test Classification

```bash
# Test SQL classification function
psql $SUPABASE_DB_URL -c "SELECT * FROM classify_job_title('CEO');"
# Expected: is_senior = t, seniority_level = csuite

psql $SUPABASE_DB_URL -c "SELECT * FROM classify_job_title('VP of Sales');"
# Expected: is_senior = t, seniority_level = vp

psql $SUPABASE_DB_URL -c "SELECT * FROM classify_job_title('Software Engineer');"
# Expected: is_senior = f, seniority_level = (empty)
```

#### 7.5 Test Digest Sending

```bash
# Manually trigger digest send
curl -X POST \
  https://YOUR_PROJECT_REF.supabase.co/functions/v1/send-digests
```

**Check Edge Function logs:**
```bash
supabase functions logs send-digests
```

Look for:
- "Authenticating with AA Control Room..."
- "Sending email digest..."
- "Email Bot deployed successfully"

---

### Step 8: Update inSided Test (Production Test)

#### 8.1 Test with Real inSided User

1. Log into inSided as a test user
2. Go to **Profile** → **Edit Profile**
3. Update **Job Title** field to: `Chief Technology Officer`
4. Save

#### 8.2 Monitor the Flow

**Check webhook received:**
```bash
supabase functions logs webhook-handler --follow
```

**Check database:**
```bash
# After 1 minute, event should be processed
psql $SUPABASE_DB_URL -c "SELECT * FROM detections ORDER BY detected_at DESC LIMIT 1;"
```

**Check pg_cron logs:**
```bash
psql $SUPABASE_DB_URL -c "SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 10;"
```

---

## 🎯 Summary: What Runs Where

| Component | Where It Runs | When |
|-----------|---------------|------|
| Webhook listener | Supabase Edge Function | Real-time (on webhook) |
| Event processing | PostgreSQL function | Every minute (pg_cron) |
| Classification | PostgreSQL function | During event processing |
| Weekly digests | Supabase Edge Function | Friday 5 PM EST (pg_cron) |
| Monthly reports | PostgreSQL function | Last day of month (pg_cron) |
| AA bot deployment | Supabase Edge Function | When sending digests |

---

## 🗂️ Complete File Checklist

Run these in order:

```bash
# ✅ Step 1: Create tables
psql $SUPABASE_DB_URL -f migrations/001_initial_schema.sql

# ✅ Step 2: Add classification & processing
psql $SUPABASE_DB_URL -f migrations/002_serverless_functions.sql

# ✅ Step 3: Add digest/report functions  
psql $SUPABASE_DB_URL -f scripts/create_functions.sql

# ✅ Step 4: Deploy Edge Functions
cd supabase/functions
supabase functions deploy webhook-handler
supabase functions deploy send-digests

# ✅ Step 5: Set secrets
supabase secrets set AA_CONTROL_ROOM_URL=...
supabase secrets set AA_USERNAME=...
supabase secrets set AA_API_KEY=...
supabase secrets set AA_EMAIL_BOT_ID=...
supabase secrets set AA_TEAMS_BOT_ID=...

# ✅ Step 6: Setup weekly digest cron
# (Replace YOUR_PROJECT_REF with your actual project ref!)
psql $SUPABASE_DB_URL -c "SELECT cron.schedule('weekly-digest-sender', '0 17 * * FRI', \$\$SELECT net.http_post(url := 'https://YOUR_PROJECT_REF.supabase.co/functions/v1/send-digests', headers := '{\"Content-Type\": \"application/json\"}'::jsonb);\$\$);"
```

---

## 🔧 Configuration Quick Reference

### Environment Variables Needed

**In Supabase Secrets** (via `supabase secrets set`):

```bash
AA_CONTROL_ROOM_URL=https://your-instance.automationanywhere.digital
AA_USERNAME=your-aa-username
AA_API_KEY=your-aa-api-key
AA_EMAIL_BOT_ID=12345
AA_TEAMS_BOT_ID=67890
```

**Already Available** (automatic in Edge Functions):
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

---

## ❓ Troubleshooting

### Error: "schema 'cron' does not exist"

**Solution:** pg_cron not enabled

1. Check Supabase plan (must be Pro for pg_cron)
2. Enable extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS pg_cron;
   ```
3. Re-run migration 002

### Events Not Processing

**Check pg_cron job:**
```sql
-- View jobs
SELECT * FROM cron.job;

-- View job history
SELECT * FROM cron.job_run_details 
ORDER BY start_time DESC 
LIMIT 10;

-- Manually trigger
SELECT process_pending_events();
```

### Edge Function Errors

**View logs:**
```bash
supabase functions logs webhook-handler
supabase functions logs send-digests
```

**Common issues:**
- Missing secrets: Run `supabase secrets list`
- Wrong project ref: Check Supabase URL
- CORS errors: Already handled in code

### AA Bot Not Deploying

**Check:**
1. Secrets are set correctly: `supabase secrets list`
2. Bot IDs are correct (numeric, not file IDs)
3. Username has permission to deploy bots
4. Test authentication manually:
   ```bash
   curl -X POST \
     https://automationanywhere-be-prod.automationanywhere.com/v2/authentication \
     -H "Content-Type: application/json" \
     -d '{"username":"your-username","apiKey":"your-key","multipleLogin":false}'
   ```

### Classification Not Working

**Test SQL function:**
```sql
SELECT * FROM classify_job_title('CEO');
-- Should return: t | csuite

SELECT * FROM classify_job_title('Software Engineer');
-- Should return: f | (empty)
```

---

## 📊 Monitoring

### View All Cron Jobs

```sql
SELECT 
    jobname,
    schedule,
    command
FROM cron.job;
```

Expected jobs:
- `process-pending-events` - Every minute
- `weekly-digest` - Friday 5 PM
- `month-end-report` - Last day of month, 11:55 PM
- `housekeeping` - Daily 2 AM
- `weekly-digest-sender` - Friday 5 PM

### Check System Health

```sql
-- Pending events
SELECT COUNT(*) FROM events_raw WHERE NOT processed;

-- Senior users by level
SELECT seniority_level, COUNT(*) 
FROM user_state 
GROUP BY seniority_level;

-- Recent detections
SELECT * FROM detections 
ORDER BY detected_at DESC 
LIMIT 10;

-- Pending digests
SELECT COUNT(*) FROM digests WHERE NOT sent;
```

### Edge Function Logs

```bash
# Follow webhook logs
supabase functions logs webhook-handler --follow

# Follow digest logs
supabase functions logs send-digests --follow
```

---

## 🎨 Customization

### Change Classification Rules

Edit the SQL function in `migrations/002_serverless_functions.sql`:

**To add new C-suite pattern:**
```sql
-- Find this line (around line 23):
IF normalized_title ~* '(\mboss\M|\bchief\M.*\bofficer\M|\bceo\M|...)' 

-- Add your pattern:
IF normalized_title ~* '(...|\bchief data officer\M|\bcdo\M)' 
```

**Re-apply:**
```bash
psql $SUPABASE_DB_URL -f migrations/002_serverless_functions.sql
```

### Change Email Template

Edit `supabase/functions/send-digests/index.ts` → `buildEmailHTML()` function.

**Re-deploy:**
```bash
supabase functions deploy send-digests
```

### Change Schedule

```sql
-- Change digest to Monday 9 AM instead of Friday 5 PM
SELECT cron.unschedule('weekly-digest-sender');
SELECT cron.schedule('weekly-digest-sender', '0 9 * * MON', 
  $$SELECT net.http_post(...);$$
);
```

---

## 🔒 Security Checklist

- [ ] API keys stored in Supabase secrets (not in code)
- [ ] Database password is strong
- [ ] Service role key never exposed to client
- [ ] Webhook endpoint accepts only POST requests
- [ ] Consider adding webhook signature validation
- [ ] Enable Row Level Security (RLS) if needed

---

## 📈 What Happens Automatically

### Every Minute
pg_cron calls `process_pending_events()`:
- Processes events from `events_raw`
- Classifies job titles (SQL regex)
- Updates `user_state` (only seniors)
- Creates `detections` records

### Every Friday at 5 PM EST
pg_cron triggers `send-digests` Edge Function:
- Fetches detections from past week
- Authenticates with AA Control Room
- Deploys email bot with HTML digest
- Deploys Teams bot with markdown message

### Last Day of Month at 11:55 PM EST
pg_cron calls `build_month_end_report()`:
- Generates CSV and HTML reports
- Stores metadata in `reports` table

### Daily at 2 AM EST
pg_cron calls `purge_old_events()`:
- Deletes events older than 14 days

---

## 🎉 You're Live!

After completing all steps:

1. ✅ Webhook endpoint is live
2. ✅ Events are processed automatically
3. ✅ Classification runs in database
4. ✅ Weekly digests will send Friday 5 PM
5. ✅ Monthly reports generate automatically
6. ✅ Everything is serverless

**Total deployment time: ~30 minutes**

**Total cost: ~$25/month** (just Supabase Pro)

---

## 📞 Need Help?

### Quick Commands Reference

```bash
# View webhook logs
supabase functions logs webhook-handler

# View digest logs
supabase functions logs send-digests

# Check cron jobs
psql $SUPABASE_DB_URL -c "SELECT * FROM cron.job;"

# Check recent detections
psql $SUPABASE_DB_URL -c "SELECT * FROM detections ORDER BY detected_at DESC LIMIT 10;"

# Manually trigger digest
curl -X POST https://YOUR_PROJECT_REF.supabase.co/functions/v1/send-digests

# Manually process events
psql $SUPABASE_DB_URL -c "SELECT process_pending_events();"
```

### Common Issues

**"pg_cron not available"** → Upgrade to Supabase Pro  
**"Authentication failed"** → Check AA_USERNAME and AA_API_KEY  
**"Bot not found"** → Verify bot IDs are correct (numeric)  
**"Events not processing"** → Check pg_cron job status  

---

## 🚀 Next Steps

After deployment:
1. Monitor logs for 24 hours
2. Update a test user's job title in inSided
3. Verify detection appears in database
4. Wait for Friday 5 PM for first automated digest
5. Check AA Control Room activity logs

**Your system is production-ready!** 🎊

---

**Questions?** Check the [README.md](README.md) for full documentation.

**Repository:** https://github.com/shreya-aapf/CaptPathfinder

