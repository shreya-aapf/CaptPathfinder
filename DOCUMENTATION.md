# CaptPathfinder - Complete Documentation

**Senior Executive Detection System for Community Profiles**

A production-ready system that detects C-suite and VP-level executives from community profile updates, sends weekly digests, and generates monthly reports.

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue)](https://github.com/shreya-aapf/CaptPathfinder)

---

## 📋 Quick Navigation

- [🚀 Quick Start (5 Minutes)](#-quick-start-5-minutes)
- [📖 Overview](#-overview)
- [🏗️ Architecture](#️-architecture)
- [⚙️ Setup & Configuration](#️-setup--configuration)
- [🔌 API Reference](#-api-reference)
- [🚢 Deployment](#-deployment)
- [🎨 Customization](#-customization)
- [📊 Monitoring](#-monitoring)
- [❓ Troubleshooting](#-troubleshooting)

---

## 🚀 Quick Start (5 Minutes)

<details open>
<summary><b>Click to expand Quick Start Guide</b></summary>

### Prerequisites
- Python 3.11+
- Supabase account
- Git

### Step 1: Clone and Setup

```bash
git clone https://github.com/shreya-aapf/CaptPathfinder.git
cd CaptPathfinder
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### Step 2: Configure Environment

Get your Supabase connection string:
1. Go to https://app.supabase.com → Your Project
2. Settings → Database → Connection String → URI
3. Click Copy 📋

Create `.env` file:
```bash
SUPABASE_DB_URL=<paste-connection-string-here>
AA_EMAIL_BOT_URL=https://your-aa-instance.com/api/email
AA_EMAIL_BOT_API_KEY=your-key
AA_TEAMS_BOT_URL=https://your-aa-instance.com/api/teams
AA_TEAMS_BOT_API_KEY=your-key
```

### Step 3: Setup Database

```bash
# Get your connection string from step 2
psql YOUR_DB_URL -f migrations/001_initial_schema.sql
psql YOUR_DB_URL -f scripts/create_functions.sql
psql YOUR_DB_URL -f scripts/setup_pg_cron.sql
```

### Step 4: Run the Application

```bash
python -m app.main
```

API available at: `http://localhost:8000`

### Step 5: Test It!

```bash
# Send test webhook
curl -X POST http://localhost:8000/webhooks/community \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "123",
    "username": "Jane Smith",
    "profileField": "Job Title",
    "value": "Chief Technology Officer",
    "oldValue": "VP Engineering"
  }'

# View recent detections
curl http://localhost:8000/admin/recent-detections

# View stats
curl http://localhost:8000/admin/stats
```

✅ **You're all set!** Continue reading for detailed configuration and deployment.

</details>

---

## 📖 Overview

<details>
<summary><b>Click to expand Overview</b></summary>

### What is CaptPathfinder?

CaptPathfinder processes webhook events from a community platform to identify when users update their job titles to senior executive positions (VP or C-suite level).

### What It Does

1. **Classifies** job titles using regex-based rules (easily configurable)
2. **Stores** only senior executives (minimizes database usage)
3. **Generates** weekly digests for stakeholders
4. **Creates** month-end reports with CSV and HTML output
5. **Integrates** with Automation Anywhere bots for email and Teams notifications

### Key Features

✅ **Simple** - No external message queues (uses Postgres as queue)  
✅ **Efficient** - Minimal storage footprint (only senior execs persisted)  
✅ **Flexible** - Config-driven classification rules  
✅ **Production-Ready** - Idempotent processing, retry logic, comprehensive logging  
✅ **Scalable** - Stateless services, horizontal scaling ready  

### Project Structure

```
CaptPathfinder/
├── app/                     # Application code
│   ├── main.py             # FastAPI application
│   ├── classification/     # Seniority detection
│   ├── services/           # Business logic
│   └── utils/              # Helpers
├── migrations/             # Database schema
├── scripts/                # SQL functions & cron
├── worker.py               # Background worker
├── test_classification.py  # Test script
└── requirements.txt        # Dependencies
```

</details>

---

## 🏗️ Architecture

<details>
<summary><b>Click to expand Architecture Details</b></summary>

### System Flow

```
Community Platform
      │
      │ Webhook
      ▼
┌─────────────────┐
│ FastAPI Service │ → Validates, deduplicates
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ Classification  │ → Regex-based rules
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ Supabase/       │ → Only stores seniors
│ PostgreSQL      │
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ pg_cron Jobs    │ → Weekly digests, monthly reports
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ Automation      │ → Email & Teams notifications
│ Anywhere Bots   │
└─────────────────┘
```

### Database Tables

- **`field_registry`** - Configuration (stores "Job Title")
- **`events_raw`** - Short-lived audit trail (14-day retention)
- **`user_state`** - Current senior executives only
- **`detections`** - Historical detections for reporting
- **`digests`** - Pending/sent weekly digests
- **`reports`** - Month-end reports

### Scheduled Jobs (pg_cron)

| Job | Schedule | Purpose |
|-----|----------|---------|
| Weekly Digest | Friday 5 PM EST | Send email & Teams digests |
| Month-End Report | Last day of month, 11:55 PM EST | Generate CSV/HTML reports |
| Housekeeping | Daily 2 AM EST | Purge events older than 14 days |

### Data Flow: Webhook to Database

```
1. Webhook arrives → Validate with Pydantic
2. Generate idempotency key → Check for duplicates
3. Is "Job Title" field? → Store in events_raw
4. Classify title → Apply regex rules
5. Is senior? 
   YES → Insert/update user_state + detections
   NO  → Delete from user_state (if exists)
6. Return response
```

### Classification Logic

```
Job Title
    ↓
Normalize (lowercase, trim, remove punctuation)
    ↓
Check exclusions (student, retired, etc.)
    ↓ No match
Check C-suite patterns (CEO, CFO, Chief...)
    ↓ Match → Return (True, "csuite")
Check VP patterns (VP, Vice President, SVP...)
    ↓ Match → Return (True, "vp")
No match → Return (False, "")
```

</details>

---

## ⚙️ Setup & Configuration

<details>
<summary><b>Click to expand Setup & Configuration</b></summary>

### Environment Variables

Create a `.env` file with:

```bash
# Database (Required)
SUPABASE_DB_URL=postgresql://postgres:password@db.projectid.supabase.co:5432/postgres

# Automation Anywhere Integration (Required)
AA_EMAIL_BOT_URL=https://your-aa-instance.com/api/v1/email/send
AA_EMAIL_BOT_API_KEY=your-api-key-here
AA_TEAMS_BOT_URL=https://your-aa-instance.com/api/v1/teams/send
AA_TEAMS_BOT_API_KEY=your-api-key-here

# Application Settings (Optional)
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Community Platform API (Optional)
COMMUNITY_API_URL=https://your-community-platform.com/api
COMMUNITY_API_KEY=your-api-key-here

# Supabase Storage (Optional)
SUPABASE_STORAGE_URL=https://projectid.supabase.co/storage/v1
SUPABASE_STORAGE_BUCKET=reports
SUPABASE_ANON_KEY=your-anon-key-here
```

### Getting Supabase Connection String (Easy Way!)

**Don't construct it manually - just copy from Supabase:**

1. Open https://app.supabase.com → Your Project
2. **Settings** (⚙️) → **Database**
3. Scroll to **Connection String** section
4. Click **URI** tab
5. Click **Copy** button 📋
6. Paste into your `.env` file

### Database Setup

Run these SQL scripts in order:

```bash
# 1. Create tables
psql $SUPABASE_DB_URL -f migrations/001_initial_schema.sql

# 2. Create functions
psql $SUPABASE_DB_URL -f scripts/create_functions.sql

# 3. Setup cron jobs
psql $SUPABASE_DB_URL -f scripts/setup_pg_cron.sql
```

### Classification Rules

Edit `app/classification/config.json` to customize which titles are classified as senior:

```json
{
  "version": "v1",
  "exclusion_patterns": [
    "student",
    "volunteer",
    "intern",
    "retired"
  ],
  "csuite_patterns": [
    "\\bceo\\b",
    "\\bcfo\\b",
    "\\bchief.*officer\\b",
    "\\bpresident\\b"
  ],
  "vp_patterns": [
    "\\bvp\\b",
    "\\bvice president\\b",
    "\\bsvp\\b"
  ]
}
```

Test your rules:
```bash
python test_classification.py
```

</details>

---

## 🔌 API Reference

<details>
<summary><b>Click to expand API Reference</b></summary>

### Public Endpoints

#### `POST /webhooks/community`
Receive webhook from community platform.

**Request:**
```json
{
  "userId": "2000",
  "username": "John Doe",
  "profileField": "Job Title",
  "value": "VP of Sales",
  "oldValue": "Sales Manager"
}
```

**Response:**
```json
{
  "status": "accepted",
  "result": {
    "status": "processed",
    "user_id": "2000",
    "is_senior": true,
    "seniority_level": "vp",
    "event_id": 12345
  }
}
```

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-11-27T00:00:00Z"
}
```

### Admin Endpoints

#### `GET /admin/stats`
Get system statistics.

**Response:**
```json
{
  "stats": {
    "senior_users": 150,
    "by_level": {
      "csuite": 45,
      "vp": 105
    },
    "pending_digests": 2,
    "total_detections": 230
  }
}
```

#### `GET /admin/recent-detections?limit=10`
View recent senior executive detections.

**Response:**
```json
{
  "detections": [
    {
      "user_id": "123",
      "username": "Jane Doe",
      "title": "CEO",
      "seniority_level": "csuite",
      "country": "USA",
      "company": "Tech Corp",
      "detected_at": "2025-11-27T10:30:00Z"
    }
  ]
}
```

#### `POST /admin/send-digests`
Manually trigger sending of pending digests.

#### `POST /admin/generate-reports`
Manually trigger generation of pending reports.

</details>

---

## 🚢 Deployment

<details>
<summary><b>Click to expand Deployment Guide</b></summary>

### Deployment Options

#### Option 1: Railway (Recommended for Quick Deploy)

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and initialize
railway login
railway init

# Add environment variables in dashboard
# Deploy
railway up
```

#### Option 2: Render

1. Connect GitHub repository
2. Select Python environment
3. Build: `pip install -r requirements.txt`
4. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables in dashboard

#### Option 3: Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

```bash
docker build -t captpathfinder .
docker run -p 8000:8000 --env-file .env captpathfinder
```

#### Option 4: AWS ECS / GCP Cloud Run / Azure

See detailed guides in the original DEPLOYMENT.md for:
- AWS ECS setup
- Google Cloud Run deployment
- Azure Container Apps
- Kubernetes configuration

### Worker Setup

For processing digests/reports independently:

**Option A: Cron (Linux/Mac)**
```bash
crontab -e

# Add line (every 10 minutes)
*/10 * * * * cd /path/to/CaptPathfinder && /path/to/venv/bin/python worker.py
```

**Option B: Task Scheduler (Windows)**
- Create scheduled task
- Run `python worker.py` every 10 minutes

**Option C: Cloud Scheduler**
- Set up HTTP trigger to `/admin/send-digests`
- Or deploy worker.py as separate function

### Environment Variables in Production

**Railway/Render:** Use dashboard  
**AWS:** Use AWS Secrets Manager  
**GCP:** Use Secret Manager  
**Docker:** Use `--env-file` or orchestrator secrets

</details>

---

## 🎨 Customization

<details>
<summary><b>Click to expand Customization Guide</b></summary>

### Changing Classification Rules

Edit `app/classification/config.json`:

```json
{
  "csuite_patterns": [
    "\\bchief data officer\\b",  // Add this
    "\\bcdo\\b"                   // Add this
  ],
  "exclusion_patterns": [
    "contractor",                  // Add this
    "consultant"                   // Add this
  ]
}
```

Restart app and test:
```bash
python test_classification.py
```

### Customizing Email Templates

Edit `app/services/aa_integration.py` → `_format_digest_for_email()`:

```python
def _format_digest_for_email(self, digest: DigestPayload) -> Dict[str, Any]:
    html_body = f"""
    <html>
    <head>
        <style>
            /* Your custom CSS */
            body {{ font-family: 'Your Font', Arial; }}
        </style>
    </head>
    <body>
        <img src="https://your-logo.png" width="200">
        <h2>Your Custom Title</h2>
        <!-- Your custom template -->
    </body>
    </html>
    """
    
    return {
        "to": ["your-email@company.com"],
        "subject": "Your Custom Subject",
        "body": html_body
    }
```

### Customizing Teams Messages

Edit `app/services/aa_integration.py` → `_format_digest_for_teams()`:

```python
def _format_digest_for_teams(self, digest: DigestPayload) -> Dict[str, Any]:
    # Use Adaptive Cards
    adaptive_card = {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "Your Custom Title",
                "size": "large"
            }
        ]
    }
    
    return {
        "channel_url": "your-teams-channel",
        "message": adaptive_card
    }
```

### Changing Digest Schedule

Edit `scripts/setup_pg_cron.sql`:

```sql
-- Change to Monday 9 AM instead of Friday 5 PM
SELECT cron.schedule(
    'weekly-digest',
    '0 9 * * MON',  -- Changed
    $$SELECT build_weekly_digest();$$
);
```

### Adding New Metadata Fields

1. **Update database:**
```sql
ALTER TABLE user_state ADD COLUMN department TEXT;
```

2. **Update models** in `app/models.py`:
```python
class WebhookEvent(BaseModel):
    # ... existing fields ...
    department: Optional[str] = None
```

3. **Update processor** in `app/services/event_processor.py`

</details>

---

## 📊 Monitoring

<details>
<summary><b>Click to expand Monitoring Guide</b></summary>

### Key Metrics to Track

| Metric | Query |
|--------|-------|
| Senior users count | `SELECT COUNT(*) FROM user_state` |
| Pending digests | `SELECT COUNT(*) FROM digests WHERE NOT sent` |
| Events processed/hour | `SELECT COUNT(*) FROM events_raw WHERE received_at > NOW() - INTERVAL '1 hour'` |

### Application Logs

All components use Python `logging`:

```bash
# View logs
tail -f app.log

# Or if using systemd
journalctl -u captpathfinder -f
```

### Database Monitoring

```sql
-- Check table sizes
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size('public.'||tablename))
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size('public.'||tablename) DESC;

-- Check cron job status
SELECT * FROM cron.job_run_details 
ORDER BY start_time DESC 
LIMIT 10;
```

### Alerts to Setup

- API response time > 2s
- Error rate > 1%
- Pending digests > 50
- Database connection failures
- AA bot call failures

</details>

---

## ❓ Troubleshooting

<details>
<summary><b>Click to expand Troubleshooting Guide</b></summary>

### Webhook Not Processing

**Check:**
1. Application logs for errors
2. Database connectivity: `psql $SUPABASE_DB_URL -c "SELECT 1"`
3. Event stored in `events_raw` table

**Solution:**
```bash
# View recent errors
curl http://localhost:8000/admin/stats

# Check database
psql $SUPABASE_DB_URL -c "SELECT * FROM events_raw ORDER BY received_at DESC LIMIT 5"
```

### Digests Not Sending

**Check:**
1. Pending digests: `SELECT * FROM digests WHERE NOT sent`
2. AA bot credentials in `.env`
3. Network connectivity to AA endpoints

**Solution:**
```bash
# Manually trigger
curl -X POST http://localhost:8000/admin/send-digests

# Check logs for retry errors
```

### pg_cron Not Running

**Check:**
1. Extension enabled: `SELECT * FROM pg_extension WHERE extname = 'pg_cron'`
2. Jobs scheduled: `SELECT * FROM cron.job`
3. Job history: `SELECT * FROM cron.job_run_details ORDER BY start_time DESC`

**Solution:**
```sql
-- Enable extension
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Re-run setup
\i scripts/setup_pg_cron.sql
```

### Classification Not Working

**Check:**
```bash
# Test classification
python test_classification.py

# Test specific title
python -c "from app.classification import classify_title; print(classify_title('CEO'))"
```

**Solution:**
- Review patterns in `app/classification/config.json`
- Check for typos in regex patterns
- Verify no exclusions are matching unintentionally

### Database Connection Issues

**Error:** `Connection refused`

**Solution:**
- Verify connection string in `.env`
- Check IP whitelist in Supabase settings
- Test connection: `psql $SUPABASE_DB_URL -c "SELECT NOW()"`

**Error:** `SSL required`

**Solution:**
- Use connection string directly from Supabase dashboard
- Ensure `?sslmode=require` is included (Supabase adds this automatically)

</details>

---

## 📚 Additional Resources

### Testing

```bash
# Test classification rules
python test_classification.py

# Test webhook
curl -X POST http://localhost:8000/webhooks/community \
  -H "Content-Type: application/json" \
  -d @test_webhook.json

# Run worker manually
python worker.py
```

### Tech Stack

- **Language:** Python 3.11+
- **Web Framework:** FastAPI
- **Database:** Supabase (PostgreSQL)
- **Validation:** Pydantic
- **HTTP Client:** httpx (async)
- **Retry Logic:** tenacity
- **Scheduling:** pg_cron

### License

MIT License

### Support

- **GitHub:** https://github.com/shreya-aapf/CaptPathfinder
- **Issues:** Open an issue on GitHub
- **Documentation:** This file!

---

**Built with ❤️ for efficient senior executive tracking**

Ready to deploy? Check the [Deployment section](#-deployment) above! 🚀

