# 🚀 CaptPathfinder - Production Deployment Guide

**One comprehensive guide to deploy CaptPathfinder 100% serverless on Supabase.**

---

## 📋 What You'll Deploy

```
inSided (Gainsight Community)
     ↓ webhook (real-time)
Supabase Edge Functions (webhook-handler)
     ↓
PostgreSQL (classification in SQL - instant)
     ↓
AA Bot Deploy API v4 (immediate notification)
     ↓
Email sent RIGHT AWAY ✉️
```

**Total Cost: $0/month** (100% Free Tier!)

**Processing Time: < 2 seconds** (Real-time!)

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
5. Generate database password (you can skip saving it - we won't need it!)
6. Select region: US East (or closest to you)
7. Click **Create Project**
8. Wait ~2 minutes for provisioning

#### 1.2 Get Project Reference

You'll need your **Project Reference** (Project ID) for later steps:

1. Look at your browser URL: `https://supabase.com/dashboard/project/YOUR_PROJECT_REF`
2. The `YOUR_PROJECT_REF` is your project reference
3. **OR** go to **Project Settings** → **General** → copy **Reference ID**

**Example:** `abcdefghijklmnop`

Save this - you'll use it for:
- Edge Function URLs
- inSided webhook configuration

#### 1.3 Verify Plan

Good news! **This works on Supabase Free Tier!**

We use Supabase Edge Function cron triggers instead of pg_cron, so no Pro plan needed.

---

### Step 2: Run Database Migrations (5 minutes)

**Use Supabase SQL Editor - No connection string needed!**

#### 2.1 Run Migration 001 (Create Tables)

1. In your Supabase project, click **SQL Editor** in the left sidebar
2. Click **+ New Query**
3. Open `migrations/001_initial_schema.sql` from your project folder on your computer
4. Copy **all** the contents (Ctrl+A, Ctrl+C)
5. Paste into the Supabase SQL Editor (Ctrl+V)
6. Click **Run** (or press Ctrl+Enter)
7. Wait for "Success. No rows returned" ✅

#### 2.2 Run Migration 002 (Add Classification Functions)

1. Click **+ New Query** again
2. Open `migrations/002_serverless_functions.sql`
3. Copy all contents and paste into SQL Editor
4. Click **Run**
5. Wait for success ✅

#### 2.3 Run Migration 003 (Add Digest/Report Functions)

1. Click **+ New Query** again
2. Open `scripts/create_functions.sql`
3. Copy all contents and paste into SQL Editor
4. Click **Run**
5. Wait for success ✅

#### 2.4 Verify Tables Created

In SQL Editor, run this query:

```sql
SELECT tablename FROM pg_tables WHERE schemaname = 'public';
```

**You should see:**
- `field_registry`
- `events_raw`
- `user_state`
- `detections`
- `digests`
- `reports`

✅ **Database setup complete!**

---

### Step 3: Install Supabase CLI (2 minutes)

**Windows:**
```bash
npm install -g supabase
```

**Mac/Linux:**
```bash
brew install supabase/tap/supabase
```

**Or use npx (no install needed):**
```bash
npx supabase login
```

---

### Step 4: Deploy Supabase Edge Functions (5 minutes)

#### 4.1 Login to Supabase CLI

Open your terminal and run:

```bash
supabase login
```

This will open a browser for authentication. Click **Allow** to authorize.

#### 4.2 Link Your Project

```bash
# Navigate to your project folder
cd "C:\Users\ShreyaKumar\OneDrive - Automation Anywhere\Documents\code\community\CaptPathfinder"

# Link to your Supabase project (use your Project Reference from Step 1.2)
supabase link --project-ref YOUR_PROJECT_REF
```

**Replace `YOUR_PROJECT_REF`** with your actual project reference (e.g., `abcdefghijklmnop`)

#### 4.3 Deploy All Edge Functions

```bash
# Navigate to functions directory
cd supabase/functions

# Deploy each function
supabase functions deploy webhook-handler
supabase functions deploy process-events
supabase functions deploy send-digests
supabase functions deploy generate-reports
supabase functions deploy housekeeping
```

**Note:** No `--no-verify-jwt` flag needed! JWT verification settings are already configured in each function's `config.json` file:
- `webhook-handler` - `verify_jwt: false` (accepts external webhooks from inSided)
- `process-events` - `verify_jwt: false` (scheduled function, no user context)
- `send-digests` - `verify_jwt: false` (scheduled function)
- `generate-reports` - `verify_jwt: false` (scheduled function)
- `housekeeping` - `verify_jwt: false` (scheduled function)

**What each function does:**
- `webhook-handler` - Receives inSided webhooks (real-time)
- `process-events` - Processes pending events (runs every minute via cron)
- `send-digests` - Sends weekly digests (runs Friday 5 PM EST via cron)
- `generate-reports` - Creates month-end reports (runs last day of month via cron)
- `housekeeping` - Purges old events (runs daily 2 AM EST via cron)

#### 4.4 Note Your Webhook URL

**Your webhook URL will be:**
```
https://aiepzfpaxolupbagqcdd.supabase.co/functions/v1/webhook-handler
```

Replace `YOUR_PROJECT_REF` with your actual project reference.
---

### Step 5: Configure Automation Anywhere (10 minutes)

#### 5.1 Get AA Control Room Details

You need:
- Control Room URL: `https://your-instance.automationanywhere.digital`
- Username: Your AA login username
- API Key: Generate from Control Room

**To generate API Key:**
1. Log into AA Control Room
2. Go to **My Settings** → **My Credentials**
3. Click **Generate API Key**
4. Copy immediately (won't be shown again)

#### 5.2 Get Bot IDs

For each bot (email and Teams):
1. Go to **Automation** tab in Control Room
2. Find your bot
3. Note the **Bot ID** (numeric ID visible in bot list or URL)
4. Example: `12345` or `67890`

#### 5.3 Set Supabase Secrets

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

### Step 6: Verify Cron Schedules (1 minute)

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

### Step 6: Subscribe to inSided Webhooks via Postman (5 minutes)

The webhook handler is configured to accept **both** registration and profile update events at the **same URL**:

```
https://YOUR_PROJECT_REF.supabase.co/functions/v1/webhook-handler
```

#### 6.1 Get Your Webhook URL

Replace `YOUR_PROJECT_REF` with your actual Supabase project reference from Step 1.2.

**Example:**
```
https://abcdefghijklmnop.supabase.co/functions/v1/webhook-handler
```

#### 6.2 Get inSided API Credentials

From your inSided admin panel:
1. Go to **Admin** → **Settings** → **API**
2. Copy your **API Token** (for Authorization header)
3. Copy your **API Secret** (for webhook payload)
4. Note your **API Base URL** (usually `https://api2-us-west-2.insided.com`)

#### 6.3 Subscribe to Events via Postman

You need to subscribe to **TWO events** using the **same webhook URL**:

##### **Event 1: User Registration**

**Postman Setup:**
- **Method:** `POST`
- **URL:** `https://api2-us-west-2.insided.com/webhooks/integration.UserRegistered/subscriptions`
- **Headers:**
  - `Content-Type: application/json`
  - `Authorization: Bearer YOUR_INSIDED_API_TOKEN`
- **Body (raw JSON):**
```json
{
  "url": "https://YOUR_PROJECT_REF.supabase.co/functions/v1/webhook-handler",
  "username": "YOUR_INSIDED_API_TOKEN",
  "secret": "YOUR_INSIDED_API_SECRET"
}
```

**Expected Response:**
```json
{
  "id": "subscription-id-1",
  "event": "integration.UserRegistered",
  "url": "https://YOUR_PROJECT_REF.supabase.co/functions/v1/webhook-handler",
  "status": "active"
}
```

##### **Event 2: Profile Updates**

**Postman Setup:**
- **Method:** `POST`
- **URL:** `https://api2-us-west-2.insided.com/webhooks/integration.UserProfileUpdated/subscriptions`
- **Headers:**
  - `Content-Type: application/json`
  - `Authorization: Bearer YOUR_INSIDED_API_TOKEN`
- **Body (raw JSON):**
```json
{
  "url": "https://YOUR_PROJECT_REF.supabase.co/functions/v1/webhook-handler",
  "username": "YOUR_INSIDED_API_TOKEN",
  "secret": "YOUR_INSIDED_API_SECRET"
}
```

**Expected Response:**
```json
{
  "id": "subscription-id-2",
  "event": "integration.UserProfileUpdated",
  "url": "https://YOUR_PROJECT_REF.supabase.co/functions/v1/webhook-handler",
  "status": "active"
}
```

#### 6.4 Verify Subscriptions

**Postman Setup:**
- **Method:** `GET`
- **URL:** `https://api2-us-west-2.insided.com/webhooks/subscriptions` (or check specific event endpoints)
- **Headers:**
  - `Authorization: Bearer YOUR_INSIDED_API_TOKEN`

You should see both subscriptions pointing to your webhook handler URL.

#### 6.5 How Real-Time Processing Works

The **same webhook URL** handles both events and processes them **immediately**:

| Event Type | What Happens | Latency |
|------------|--------------|---------|
| `integration.UserRegistered` | Extract job title → Classify → If senior → Send email | < 2 seconds |
| `integration.UserProfileUpdated` | Extract job title → Classify → If senior → Send email | < 2 seconds |

**Flow:**
1. Webhook received
2. Event stored in `events_raw`
3. **Classification runs immediately** (SQL function)
4. If senior executive detected:
   - Update `user_state` table
   - Create `detections` record
   - **Deploy AA email bot RIGHT NOW**
   - Email sent instantly
5. If not senior: Event marked as processed, no notification

**No waiting, no batching, no cron jobs!** ⚡

---

### Step 7: Test Real-Time Detection (5 minutes)

#### 7.1 Test Webhook Receipt & Immediate Processing

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

**Expected Response (Senior Executive):**
```json
{
  "status":"accepted",
  "event_id":1,
  "classification":"senior",
  "seniority_level":"csuite",
  "notification":"sent"
}
```

**Expected Response (Not Senior):**
```json
{
  "status":"accepted",
  "event_id":1,
  "classification":"not_senior"
}
```

✅ **If senior: Email should be sent within 2 seconds!**

#### 7.2 Check Detection in Database

**In Supabase SQL Editor:**
```sql
-- Check if event was stored and processed
SELECT * FROM events_raw ORDER BY received_at DESC LIMIT 5;

-- Check if detection was created (for senior execs only)
SELECT * FROM detections ORDER BY detected_at DESC LIMIT 5;

-- Check user_state (senior execs only)
SELECT * FROM user_state;
```

You should see:
- Event in `events_raw` with `processed = TRUE`
- Detection record created (if senior)
- User in `user_state` table (if senior)

#### 7.3 Check AA Control Room

1. Log into your AA Control Room
2. Go to **Activity** → **In Progress** (or **Activity Log**)
3. You should see the bot deployment within seconds
4. Check the bot execution status

**Check your email!** You should receive the notification email instantly.

#### 7.4 Check Edge Function Logs

```bash
# View webhook handler logs
supabase functions logs webhook-handler

# View notification logs
supabase functions logs send-notification
```

Look for:
- "SENIOR EXECUTIVE DETECTED"
- "Notification sent successfully"
- "Bot deployed successfully"

#### 7.5 Test with Real inSided User

1. Log into inSided as a test user (or create a new user)
2. Update your **Job Title** to: `Chief Technology Officer`
3. Save the profile
4. **Check your email inbox within 30 seconds** - you should receive the alert!
5. Check Supabase SQL Editor to verify detection was recorded

---

### Step 9: Test with Real inSided User (Production Test)

#### 9.1 Test with Real inSided User

1. Log into inSided as a test user
2. Go to **Profile** → **Edit Profile**
3. Update **Job Title** field to: `Chief Technology Officer`
4. Save

#### 9.2 Monitor the Flow

**Check webhook received:**
```bash
supabase functions logs webhook-handler --follow
```

**Check database in SQL Editor:**
```sql
-- After 1 minute, event should be processed
SELECT * FROM detections ORDER BY detected_at DESC LIMIT 1;
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

## 🗂️ Complete Deployment Checklist

### Step 1: Create Supabase Project
1. ✅ Go to https://app.supabase.com
2. ✅ Create new project
3. ✅ Get your Project Reference (from URL or Settings)

### Step 2: Run Migrations (No connection string needed!)
**Use Supabase SQL Editor:**
1. ✅ Open SQL Editor in Supabase Dashboard
2. ✅ Run `migrations/001_initial_schema.sql`
3. ✅ Run `migrations/002_serverless_functions.sql`
4. ✅ Run `scripts/create_functions.sql`

### Step 3-4: Deploy Edge Functions
```bash
# Install Supabase CLI
npm install -g supabase

# Login and link
supabase login
supabase link --project-ref YOUR_PROJECT_REF

# Deploy all functions
cd supabase/functions
supabase functions deploy webhook-handler
supabase functions deploy process-events
supabase functions deploy send-digests
supabase functions deploy generate-reports
supabase functions deploy housekeeping
```

### Step 5: Set AA Secrets
```bash
supabase secrets set AA_CONTROL_ROOM_URL=https://your-instance.automationanywhere.digital
supabase secrets set AA_USERNAME=your-username
supabase secrets set AA_API_KEY=your-api-key
supabase secrets set AA_EMAIL_BOT_ID=12345
supabase secrets set AA_TEAMS_BOT_ID=67890
```

### Step 6-7: Configure Webhooks

**Step 6:** Cron schedules automatically set (from config.json files)

**Step 7:** Subscribe to inSided webhooks via Postman:
1. ✅ Subscribe to `integration.UserRegistered` (new users)
2. ✅ Subscribe to `integration.UserProfileUpdated` (profile changes)
3. ✅ Both use the same URL: `https://YOUR_PROJECT_REF.supabase.co/functions/v1/webhook-handler`

### Step 8-9: Test
✅ Send test webhook  
✅ Verify in SQL Editor  
✅ Test with real user

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

**Run in Supabase SQL Editor:**

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
- Run the updated SQL in Supabase SQL Editor, or
- `psql $SUPABASE_DB_URL -f migrations/002_serverless_functions.sql`

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

## 🔒 Security Notes

### JWT Verification

All Edge Functions have `verify_jwt: false` because:
- **webhook-handler** - Needs to accept webhooks from inSided (external service)
- **Scheduled functions** - No user context (triggered by cron, not user requests)

### Optional: Add Webhook Signature Verification

For production, consider adding webhook signature verification in `webhook-handler`:

1. Get webhook secret from inSided
2. Add to Supabase secrets:
   ```bash
   supabase secrets set INSIDED_WEBHOOK_SECRET=your-secret
   ```
3. Update `webhook-handler/index.ts` to verify signatures

### Row Level Security (RLS)

Consider enabling RLS on sensitive tables if you build a UI later:

```sql
-- Enable RLS
ALTER TABLE detections ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_state ENABLE ROW LEVEL SECURITY;

-- Add policies as needed
```

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

# Manually trigger digest
curl -X POST https://YOUR_PROJECT_REF.supabase.co/functions/v1/send-digests
```

**Check database (use Supabase SQL Editor):**
```sql
-- Check recent detections
SELECT * FROM detections ORDER BY detected_at DESC LIMIT 10;

-- Manually process events
SELECT process_pending_events();
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

