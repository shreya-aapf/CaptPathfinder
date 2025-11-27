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

**Total Cost: $0/month** (100% Free Tier!)

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

#### 1.3 Verify Plan

Good news! **This works on Supabase Free Tier!**

We use Supabase Edge Function cron triggers instead of pg_cron, so no Pro plan needed.

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

# Run migration 3: Setup digest/report functions
psql $SUPABASE_DB_URL -f scripts/create_functions.sql

# Note: No pg_cron setup needed - we use Edge Function cron triggers!
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

# Deploy all functions
supabase functions deploy webhook-handler
supabase functions deploy process-events
supabase functions deploy send-digests
supabase functions deploy generate-reports
supabase functions deploy housekeeping
```

**What each function does:**
- `webhook-handler` - Receives inSided webhooks (real-time)
- `process-events` - Processes pending events (runs every minute via cron)
- `send-digests` - Sends weekly digests (runs Friday 5 PM EST via cron)
- `generate-reports` - Creates month-end reports (runs last day of month via cron)
- `housekeeping` - Purges old events (runs daily 2 AM EST via cron)

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

### Step 5: Verify Cron Schedules (1 minute)

**Good news:** Cron schedules are already configured in the Edge Function `config.json` files!

**No additional setup needed.** When you deployed the functions, the schedules were automatically set up:

- `process-events` - Every minute (`* * * * *`)
- `send-digests` - Friday 5 PM EST (`0 17 * * FRI`)
- `generate-reports` - Last day of month 11:55 PM EST (`55 23 28-31 * *`)
- `housekeeping` - Daily 2 AM EST (`0 2 * * *`)

**Verify schedules in Supabase Dashboard:**
1. Go to your project
2. Click **Edge Functions** in sidebar
3. Each function shows its schedule

---

### Step 6: Configure inSided Webhooks (3 minutes)

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

### Step 7: Test the System (5 minutes)

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

#### 7.3 Wait 1 Minute (Edge Function processes events)

The `process-events` Edge Function runs every minute automatically.

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

### Step 8: Test with Real inSided User (Production Test)

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

**Check Edge Function logs:**
```bash
supabase functions logs process-events --follow
```

---

## 🎯 Summary: What Runs Where

| Component | Where It Runs | When |
|-----------|---------------|------|
| Webhook listener | Edge Function (`webhook-handler`) | Real-time (on webhook) |
| Event processing | Edge Function (`process-events`) | Every minute (cron) |
| Classification | PostgreSQL function | During event processing |
| Weekly digests | Edge Function (`send-digests`) | Friday 5 PM EST (cron) |
| Monthly reports | Edge Function (`generate-reports`) | Last day of month (cron) |
| Housekeeping | Edge Function (`housekeeping`) | Daily 2 AM EST (cron) |
| AA bot deployment | Edge Function (`send-digests`) | When sending digests |

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
supabase functions deploy process-events
supabase functions deploy send-digests
supabase functions deploy generate-reports
supabase functions deploy housekeeping

# ✅ Step 5: Set secrets
supabase secrets set AA_CONTROL_ROOM_URL=...
supabase secrets set AA_USERNAME=...
supabase secrets set AA_API_KEY=...
supabase secrets set AA_EMAIL_BOT_ID=...
supabase secrets set AA_TEAMS_BOT_ID=...

# ✅ Step 6: Cron schedules automatically set (no action needed!)
# Schedules are defined in config.json files for each Edge Function
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

### Error: "Failed to deploy function"

**Solution:** Check configuration

1. Verify you're logged in: `supabase login`
2. Verify project is linked: `supabase link --project-ref YOUR_REF`
3. Check function logs: `supabase functions logs FUNCTION_NAME`

### Events Not Processing

**Check Edge Function:**
```bash
# View logs
supabase functions logs process-events --follow

# Manually trigger
curl -X POST https://YOUR_PROJECT_REF.supabase.co/functions/v1/process-events

# Check if scheduled
# Go to Supabase Dashboard → Edge Functions → process-events
# Should show: Schedule: * * * * * (every minute)
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

### View All Edge Functions and Schedules

**In Supabase Dashboard:**
1. Go to **Edge Functions**
2. See all deployed functions with their schedules

**Or via CLI:**
```bash
supabase functions list
```

Expected functions:
- `webhook-handler` - No schedule (triggered by webhook)
- `process-events` - Every minute (`* * * * *`)
- `send-digests` - Friday 5 PM (`0 17 * * FRI`)
- `generate-reports` - Last day of month 11:55 PM (`55 23 28-31 * *`)
- `housekeeping` - Daily 2 AM (`0 2 * * *`)

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
# Follow logs for each function
supabase functions logs webhook-handler --follow
supabase functions logs process-events --follow
supabase functions logs send-digests --follow
supabase functions logs generate-reports --follow
supabase functions logs housekeeping --follow
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

Edit the `config.json` file for the function:

```json
// supabase/functions/send-digests/config.json
{
  "name": "send-digests",
  "verify_jwt": false,
  "import_map": "./import_map.json",
  "schedule": "0 9 * * MON"  // Change to Monday 9 AM
}
```

**Re-deploy:**
```bash
supabase functions deploy send-digests
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
`process-events` Edge Function runs:
- Calls PostgreSQL `process_pending_events()` function
- Processes events from `events_raw`
- Classifies job titles (SQL regex)
- Updates `user_state` (only seniors)
- Creates `detections` records

### Every Friday at 5 PM EST
`send-digests` Edge Function runs:
- Fetches detections from past week
- Authenticates with AA Control Room
- Deploys email bot with HTML digest
- Deploys Teams bot with markdown message

### Last Day of Month at 11:55 PM EST
`generate-reports` Edge Function runs:
- Calls PostgreSQL `build_month_end_report()` function
- Generates CSV and HTML reports
- Stores metadata in `reports` table

### Daily at 2 AM EST
`housekeeping` Edge Function runs:
- Calls PostgreSQL `purge_old_events()` function
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

**Total deployment time: ~25 minutes**

**Total cost: $0/month** (100% Free Tier!) 🎉

---

## 📞 Need Help?

### Quick Commands Reference

```bash
# View webhook logs
supabase functions logs webhook-handler

# View digest logs
supabase functions logs send-digests

# List Edge Functions
supabase functions list

# Check recent detections
psql $SUPABASE_DB_URL -c "SELECT * FROM detections ORDER BY detected_at DESC LIMIT 10;"

# Manually trigger digest
curl -X POST https://YOUR_PROJECT_REF.supabase.co/functions/v1/send-digests

# Manually process events
psql $SUPABASE_DB_URL -c "SELECT process_pending_events();"
```

### Common Issues

**"Function not found"** → Deploy all Edge Functions  
**"Authentication failed"** → Check AA_USERNAME and AA_API_KEY  
**"Bot not found"** → Verify bot IDs are correct (numeric)  
**"Events not processing"** → Check Edge Function logs and schedules  

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

