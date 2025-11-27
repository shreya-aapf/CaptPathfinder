# Supabase Deployment Guide

Complete guide for deploying CaptPathfinder to Supabase.

---

## Architecture Overview

```
inSided Webhook
     ↓
Supabase Edge Function (webhook-handler)
     ↓
Stores in events_raw table
     ↓
Python Service (Railway/Cloud Run)
     ↓
Processes events, classifies, updates DB
     ↓
pg_cron triggers digests/reports
     ↓
Automation Anywhere Bots
```

---

## Prerequisites

1. **Supabase Project**: https://supabase.com
2. **Supabase CLI**: `npm install -g supabase`
3. **Python Service Hosting**: Railway, Cloud Run, or similar

---

## Part 1: Setup Supabase Edge Function

### 1. Login to Supabase CLI

```bash
supabase login
supabase link --project-ref your-project-ref
```

### 2. Deploy Edge Function

```bash
# From project root
cd supabase/functions
supabase functions deploy webhook-handler
```

### 3. Set Environment Variables

```bash
# Set Python service URL (where your FastAPI app is hosted)
supabase secrets set PYTHON_SERVICE_URL=https://your-app.railway.app

# Other secrets are automatically available:
# - SUPABASE_URL
# - SUPABASE_SERVICE_ROLE_KEY
```

### 4. Get Edge Function URL

Your webhook URL will be:
```
https://YOUR_PROJECT_REF.supabase.co/functions/v1/webhook-handler
```

---

## Part 2: Deploy Python Service

### Option 1: Railway

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Set environment variables in Railway dashboard
# Get Railway URL: https://your-app.railway.app
```

### Option 2: Google Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/captpathfinder
gcloud run deploy captpathfinder \
  --image gcr.io/PROJECT_ID/captpathfinder \
  --platform managed \
  --region us-east1
```

---

## Part 3: Configure inSided Webhooks

### 1. Access inSided Admin Panel

1. Log into your Gainsight Community (inSided)
2. Go to **Admin** → **Settings** → **Webhooks** or **Integrations**

### 2. Create Webhook

**Webhook Configuration:**
- **URL**: `https://YOUR_PROJECT_REF.supabase.co/functions/v1/webhook-handler`
- **Method**: `POST`
- **Event Type**: `integration.UserProfileUpdated`
- **Headers** (optional):
  ```
  Content-Type: application/json
  ```

### 3. Subscribe to Events

**Event Filter:**
- Event: `integration.UserProfileUpdated`
- Condition: When profile field changes
- Field: "Job Title" or all profile fields

**Payload Example** (what inSided will send):
```json
{
  "event": "integration.UserProfileUpdated",
  "userId": "2000",
  "username": "John Doe",
  "profileFieldId": "123",
  "profileField": "Job Title",
  "value": "VP of Sales",
  "oldValue": "Sales Manager",
  "timestamp": "2025-11-27T10:30:00Z"
}
```

---

## Part 4: Configure Python Service

### Environment Variables

Set these in your hosting platform (Railway, Cloud Run, etc.):

```bash
# Database
SUPABASE_DB_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres

# Community API (inSided)
COMMUNITY_API_URL=https://api2-us-west-2.insided.com
COMMUNITY_API_KEY=your-insided-api-key

# Automation Anywhere
AA_CONTROL_ROOM_URL=https://your-instance.automationanywhere.digital
AA_USERNAME=your-username
AA_API_KEY=your-api-key
AA_EMAIL_BOT_ID=12345
AA_TEAMS_BOT_ID=67890

# Application
API_HOST=0.0.0.0
API_PORT=8000
```

### Get inSided API Key

1. inSided Admin → **Settings** → **API**
2. Generate API Key
3. Copy and set as `COMMUNITY_API_KEY`

---

## Part 5: Database Setup

Already done! Your Supabase database should have all tables from earlier setup:

```bash
# Verify tables exist
psql $SUPABASE_DB_URL -c "\dt"
```

---

## Part 6: Worker Setup

### Option A: Separate Worker Service

Deploy `worker.py` as a separate service:

```bash
# Cloud Run scheduled job
gcloud scheduler jobs create http captpathfinder-worker \
  --schedule="*/10 * * * *" \
  --uri="https://your-app.com/admin/send-digests" \
  --http-method=POST
```

### Option B: pg_cron (Already Setup)

Your pg_cron jobs are already configured and will run automatically:
- Weekly digests: Friday 5 PM EST
- Monthly reports: Last day of month
- Housekeeping: Daily 2 AM EST

---

## Testing the Setup

### 1. Test Edge Function

```bash
curl -X POST \
  https://YOUR_PROJECT_REF.supabase.co/functions/v1/webhook-handler \
  -H "Content-Type: application/json" \
  -d '{
    "event": "integration.UserProfileUpdated",
    "userId": "test123",
    "username": "Test User",
    "profileField": "Job Title",
    "value": "Chief Executive Officer",
    "oldValue": "Director"
  }'
```

**Expected Response:**
```json
{
  "status": "accepted",
  "event_id": 12345
}
```

### 2. Check Database

```sql
SELECT * FROM events_raw ORDER BY received_at DESC LIMIT 5;
```

### 3. Check Python Service Logs

```bash
# Railway
railway logs

# Cloud Run
gcloud run services logs read captpathfinder
```

### 4. Test Full Flow

1. Update a user's job title in inSided to "CEO"
2. Check Edge Function logs: `supabase functions logs webhook-handler`
3. Check database: `SELECT * FROM detections ORDER BY detected_at DESC LIMIT 1`
4. Verify classification worked

---

## Monitoring

### Edge Function Logs

```bash
# View logs
supabase functions logs webhook-handler

# Follow logs
supabase functions logs webhook-handler --follow
```

### Database Monitoring

```sql
-- Pending events
SELECT COUNT(*) FROM events_raw WHERE NOT processed;

-- Recent detections
SELECT * FROM detections ORDER BY detected_at DESC LIMIT 10;

-- Pending digests
SELECT COUNT(*) FROM digests WHERE NOT sent;
```

---

## Troubleshooting

### Issue: Edge Function not receiving webhooks

**Check:**
1. Verify Edge Function URL in inSided webhook config
2. Check inSided webhook logs (if available)
3. Test with curl (see above)

### Issue: Events not being processed

**Check:**
1. Verify Python service is running
2. Check `PYTHON_SERVICE_URL` in Edge Function secrets
3. Query `events_raw` table for unprocessed events

### Issue: Classification not working

**Check:**
1. Verify `COMMUNITY_API_KEY` is set
2. Test inSided API manually:
   ```bash
   curl -H "Authorization: Bearer YOUR_KEY" \
     https://api2-us-west-2.insided.com/users/USER_ID
   ```

---

## Cost Estimates

### Supabase
- **Edge Functions**: 500K invocations free/month
- **Database**: Free tier: 500MB, paid: $25/month for 8GB

### Python Service
- **Railway**: ~$5-20/month
- **Cloud Run**: Pay per request, ~$10-30/month

### Total: **~$15-80/month** depending on traffic

---

## Security Best Practices

1. **Use Supabase RLS** (Row Level Security) if storing sensitive data
2. **Validate webhook signatures** if inSided supports it
3. **Use service role key** only in Edge Functions (server-side)
4. **Rotate API keys** periodically
5. **Monitor for anomalies** in webhook traffic

---

## Next Steps

1. ✅ Deploy Edge Function
2. ✅ Deploy Python service
3. ✅ Configure inSided webhooks
4. ✅ Test end-to-end
5. ✅ Monitor for 24 hours
6. ✅ Configure AA bots
7. ✅ Enable weekly digests

**You're production-ready!** 🚀

