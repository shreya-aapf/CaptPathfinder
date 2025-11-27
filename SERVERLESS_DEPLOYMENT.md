# 100% Serverless Deployment Guide

**No Python service needed!** Everything runs on Supabase.

---

## Architecture

```
inSided Webhook
     ↓
Supabase Edge Function (webhook-handler)
     ↓
PostgreSQL events_raw table
     ↓
pg_cron (every minute)
     ↓
PostgreSQL function (process_pending_events)
  - Classification in pure SQL
  - Updates user_state
  - Creates detections
     ↓
pg_cron (Friday 5 PM)
     ↓
Supabase Edge Function (send-digests)
  - Authenticates with AA
  - Deploys email/Teams bots
     ↓
Automation Anywhere Bots
```

**Total cost: ~$25/month** (just Supabase Pro for pg_cron)

---

## Step 1: Database Functions

### Run SQL Migration

```bash
# Connect to your Supabase database
psql YOUR_SUPABASE_URL -f migrations/002_serverless_functions.sql
```

This creates:
- `classify_job_title(text)` - Classification in SQL
- `process_pending_events()` - Event processor
- `get_digest_data()` - Digest data retriever
- pg_cron job to process events every minute

---

## Step 2: Deploy Edge Functions

### Install Supabase CLI

```bash
npm install -g supabase
```

### Login and Link Project

```bash
supabase login
supabase link --project-ref your-project-ref
```

### Deploy Functions

```bash
# Deploy all functions
cd supabase/functions

supabase functions deploy webhook-handler
supabase functions deploy process-events
supabase functions deploy send-digests
```

### Set Environment Variables

```bash
# Automation Anywhere credentials
supabase secrets set AA_CONTROL_ROOM_URL=https://your-instance.automationanywhere.digital
supabase secrets set AA_USERNAME=your-username
supabase secrets set AA_API_KEY=your-api-key
supabase secrets set AA_EMAIL_BOT_ID=12345
supabase secrets set AA_TEAMS_BOT_ID=67890
supabase secrets set AA_AUTH_ENDPOINT=https://automationanywhere-be-prod.automationanywhere.com/v2/authentication
```

---

## Step 3: Configure pg_cron for Digests

The weekly digest needs to call the Edge Function:

```sql
-- Update the weekly digest cron job
SELECT cron.schedule(
    'weekly-digest-sender',
    '0 17 * * FRI',  -- Friday 5 PM EST
    $$
    SELECT
      net.http_post(
        url := 'https://YOUR_PROJECT_REF.supabase.co/functions/v1/send-digests',
        headers := '{"Content-Type": "application/json"}'::jsonb
      );
    $$
);
```

**Replace `YOUR_PROJECT_REF`** with your actual Supabase project reference!

---

## Step 4: Configure inSided Webhook

In inSided Admin:

1. **Settings** → **Webhooks**
2. **Create Webhook**:
   - URL: `https://YOUR_PROJECT_REF.supabase.co/functions/v1/webhook-handler`
   - Event: `integration.UserProfileUpdated`
   - Method: POST

---

## Step 5: Test Everything

### Test Webhook Receipt

```bash
curl -X POST \
  https://YOUR_PROJECT_REF.supabase.co/functions/v1/webhook-handler \
  -H "Content-Type: application/json" \
  -d '{
    "event": "integration.UserProfileUpdated",
    "userId": "2000",
    "username": "Test User",
    "profileField": "Job Title",
    "value": "CEO"
  }'
```

**Expected**: `{"status":"accepted","event_id":123}`

### Check Event Stored

```sql
SELECT * FROM events_raw ORDER BY received_at DESC LIMIT 5;
```

### Wait 1 Minute (pg_cron processes events)

```sql
-- Check if processed
SELECT * FROM events_raw WHERE processed = TRUE;

-- Check detections
SELECT * FROM detections ORDER BY detected_at DESC LIMIT 5;

-- Check user_state
SELECT * FROM user_state;
```

### Test Digest Sending

```bash
curl -X POST \
  https://YOUR_PROJECT_REF.supabase.co/functions/v1/send-digests
```

**Expected**: Bots deploy successfully

---

## How It Works

### 1. Webhook Received

Edge Function (`webhook-handler`) receives webhook → stores in `events_raw`

### 2. Event Processing (Every Minute)

pg_cron calls `process_pending_events()` PostgreSQL function:
- Fetches unprocessed events
- Runs SQL regex classification
- Updates `user_state` (only seniors)
- Creates `detections` records

### 3. Weekly Digest (Friday 5 PM)

pg_cron calls `send-digests` Edge Function:
- Fetches pending detections
- Authenticates with AA Control Room
- Deploys email bot with HTML content
- Deploys Teams bot with markdown message
- Marks detections as included

### 4. Monthly Report (Last Day of Month)

Existing pg_cron job calls `build_month_end_report()` - **already set up!**

---

## Advantages of This Approach

✅ **No Python service** - Everything runs on Supabase  
✅ **Lower cost** - Just Supabase Pro ($25/month)  
✅ **Auto-scaling** - Edge Functions scale automatically  
✅ **Fast processing** - SQL classification is very fast  
✅ **Simple deployment** - One command to deploy  
✅ **Built-in monitoring** - Supabase dashboard shows everything  

---

## Monitoring

### View Edge Function Logs

```bash
# Webhook handler
supabase functions logs webhook-handler --follow

# Event processor
supabase functions logs process-events --follow

# Digest sender
supabase functions logs send-digests --follow
```

### Check pg_cron Job Status

```sql
-- View cron jobs
SELECT * FROM cron.job;

-- View job run history
SELECT * FROM cron.job_run_details 
ORDER BY start_time DESC 
LIMIT 20;
```

### Database Stats

```sql
-- Pending events
SELECT COUNT(*) FROM events_raw WHERE NOT processed;

-- Senior users
SELECT seniority_level, COUNT(*) 
FROM user_state 
GROUP BY seniority_level;

-- Recent detections
SELECT * FROM detections 
ORDER BY detected_at DESC 
LIMIT 10;
```

---

## Troubleshooting

### Events Not Processing

**Check:**
```sql
-- Is pg_cron running?
SELECT * FROM cron.job WHERE jobname = 'process-pending-events';

-- Manually trigger
SELECT process_pending_events();
```

### Digests Not Sending

**Check:**
```bash
# Test Edge Function
curl -X POST \
  https://YOUR_PROJECT_REF.supabase.co/functions/v1/send-digests

# Check logs
supabase functions logs send-digests
```

**Verify secrets:**
```bash
supabase secrets list
```

### Classification Not Working

**Test SQL function:**
```sql
-- Test classification
SELECT * FROM classify_job_title('Chief Executive Officer');
-- Should return: true, 'csuite'

SELECT * FROM classify_job_title('VP of Sales');
-- Should return: true, 'vp'

SELECT * FROM classify_job_title('Software Engineer');
-- Should return: false, ''
```

---

## Updating Classification Rules

To change which titles are classified as senior, edit the SQL function:

```sql
-- Update the classify_job_title function in migrations/002_serverless_functions.sql
-- Then re-run:
psql YOUR_SUPABASE_URL -f migrations/002_serverless_functions.sql
```

Add new patterns to the regex in the function.

---

## Cost Breakdown

### Supabase Pro: $25/month

Includes:
- 100GB database
- 2GB file storage
- 2M Edge Function invocations
- pg_cron (requires Pro plan)
- Database functions (free)

### Automation Anywhere

- Your existing AA license

### Total: **$25/month** 🎉

---

## Next Steps

1. ✅ Run `migrations/002_serverless_functions.sql`
2. ✅ Deploy Edge Functions
3. ✅ Set secrets
4. ✅ Configure pg_cron for digests
5. ✅ Setup inSided webhook
6. ✅ Test end-to-end
7. ✅ Monitor for 24 hours

**You're fully serverless!** 🚀

