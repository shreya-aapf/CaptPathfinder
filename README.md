# CaptPathfinder

**Senior Executive Detection System for Community Profiles**

A production-ready system that detects C-suite and VP-level executives from community profile updates, sends weekly digests, and generates monthly reports.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Automation Anywhere Integration](#automation-anywhere-integration)
- [Scheduled Jobs](#scheduled-jobs)
- [Deployment](#deployment)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Customization](#customization)

---

## Overview

CaptPathfinder processes webhook events from a community platform to identify when users update their job titles to senior executive positions (VP or C-suite level). The system:

1. **Classifies** job titles using regex-based rules (easily configurable)
2. **Stores** only senior executives (minimizes database usage)
3. **Generates** weekly digests for stakeholders
4. **Creates** month-end reports with CSV and HTML output
5. **Integrates** with Automation Anywhere bots for email and Teams notifications

**Key Design Principles:**
- ✅ Simple and production-ready
- ✅ No external message queues (uses Postgres as queue with `SKIP LOCKED`)
- ✅ Minimal storage footprint (only senior execs persisted)
- ✅ Config-driven classification rules (no code changes needed to adjust patterns)
- ✅ Idempotent event processing (handles duplicates gracefully)

---

## Architecture

```
┌─────────────────┐
│  Community      │
│  Platform       │──────► Webhook Event
└─────────────────┘        (Job Title Update)
                               │
                               ▼
                    ┌──────────────────────┐
                    │   FastAPI Service    │
                    │  /webhooks/community │
                    └──────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Event Processor     │
                    │  - Idempotency check │
                    │  - Classification    │
                    │  - State management  │
                    └──────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
    ┌───────────────────┐          ┌──────────────────┐
    │  Supabase/Postgres│          │  Classification  │
    │  - events_raw     │          │  Rules Engine    │
    │  - user_state     │          │  (Regex-based)   │
    │  - detections     │          └──────────────────┘
    │  - digests        │
    │  - reports        │
    └───────────────────┘
               │
               │ pg_cron (scheduled jobs)
               │
    ┌──────────┴──────────────────┐
    ▼                             ▼
┌─────────────────┐     ┌──────────────────┐
│  Digest Builder │     │  Report Builder  │
│  (Weekly)       │     │  (Month-end)     │
└─────────────────┘     └──────────────────┘
         │                        │
         ▼                        ▼
┌──────────────────────────────────────┐
│   Automation Anywhere Bots           │
│   - Email Bot                        │
│   - Teams Sharer Bot                 │
└──────────────────────────────────────┘
```

---

## Features

### 🎯 Core Features

- **Webhook Ingestion**: Receives profile update events from community platform
- **Smart Classification**: Regex-based seniority detection (C-suite vs VP)
  - Configurable patterns in JSON
  - Exclusion rules (students, volunteers, etc.)
  - Promotion tracking (VP → C-suite)
- **Minimal Storage**: Only senior execs are kept in database
- **Idempotent Processing**: Duplicate events are automatically handled
- **Weekly Digests**: Batched notifications (max 10 entries per digest)
- **Month-End Reports**: CSV + HTML reports with aggregated stats
- **Automation Anywhere Integration**: Email and Teams notifications

### 🔧 Operational Features

- Health check endpoints
- Admin API for manual triggers
- Statistics dashboard
- Automatic housekeeping (purges old events)
- Comprehensive logging

---

## Tech Stack

- **Language**: Python 3.11+
- **Web Framework**: FastAPI
- **Database**: Supabase (PostgreSQL)
- **Scheduling**: pg_cron
- **HTTP Client**: httpx (async)
- **Validation**: Pydantic
- **Retry Logic**: tenacity

---

## Project Structure

```
CaptPathfinder/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application
│   ├── config.py                  # Configuration management
│   ├── models.py                  # Pydantic models
│   ├── database.py                # Database connection
│   ├── classification/
│   │   ├── __init__.py
│   │   ├── rules.py              # Classification logic
│   │   └── config.json           # Classification patterns (EDIT THIS!)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── event_processor.py    # Webhook processing
│   │   ├── digest_builder.py     # Weekly digest sender
│   │   ├── report_builder.py     # Monthly report generator
│   │   └── aa_integration.py     # Automation Anywhere client
│   └── utils/
│       ├── __init__.py
│       └── helpers.py             # Utility functions
├── migrations/
│   └── 001_initial_schema.sql     # Database schema
├── scripts/
│   ├── create_functions.sql       # Database functions
│   └── setup_pg_cron.sql          # Cron job setup
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
├── .gitignore
└── README.md                      # This file
```

---

## Setup & Installation

### Prerequisites

- Python 3.11 or higher
- Supabase account (or PostgreSQL 13+ with pg_cron extension)
- Automation Anywhere bots configured for email and Teams

### 1. Clone Repository

```bash
git clone <repository-url>
cd CaptPathfinder
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configuration

### 1. Create Environment File

```bash
cp .env.example .env
```

### 2. Edit `.env` File

```ini
# Database
SUPABASE_DB_URL=postgresql://user:password@db.your-project.supabase.co:5432/postgres

# Automation Anywhere Integration
AA_EMAIL_BOT_URL=https://your-aa-instance.com/api/v1/email/send
AA_EMAIL_BOT_API_KEY=your-api-key-here
AA_TEAMS_BOT_URL=https://your-aa-instance.com/api/v1/teams/send
AA_TEAMS_BOT_API_KEY=your-api-key-here

# Community Platform API (optional - for fetching user metadata)
COMMUNITY_API_URL=https://your-community-platform.com/api
COMMUNITY_API_KEY=your-api-key-here

# Application
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Supabase Storage (for reports)
SUPABASE_STORAGE_URL=https://your-project.supabase.co/storage/v1
SUPABASE_STORAGE_BUCKET=reports
SUPABASE_ANON_KEY=your-anon-key-here
```

### 3. Customize Classification Rules (Optional)

Edit `app/classification/config.json` to adjust which titles are classified as senior:

```json
{
  "version": "v1",
  "exclusion_patterns": [
    "student",
    "volunteer",
    "intern",
    "retired",
    "ex-",
    "former"
  ],
  "csuite_patterns": [
    "\\bchief\\b.*\\bofficer\\b",
    "\\bceo\\b",
    "\\bcfo\\b",
    "\\bpresident\\b(?!.*\\bvice\\b)"
  ],
  "vp_patterns": [
    "\\bvp\\b",
    "\\bvice president\\b",
    "\\bsvp\\b",
    "\\bevp\\b"
  ]
}
```

---

## Database Setup

### 1. Run Initial Schema Migration

Connect to your Supabase database using the SQL Editor or `psql`:

```bash
psql $SUPABASE_DB_URL -f migrations/001_initial_schema.sql
```

This creates:
- `field_registry`
- `events_raw`
- `user_state`
- `detections`
- `digests`
- `reports`

### 2. Create Database Functions

```bash
psql $SUPABASE_DB_URL -f scripts/create_functions.sql
```

This creates:
- `build_weekly_digest()`
- `build_month_end_report()`
- `purge_old_events()`
- Helper functions for digest processing

### 3. Setup pg_cron Scheduled Jobs

```bash
psql $SUPABASE_DB_URL -f scripts/setup_pg_cron.sql
```

This schedules:
- **Weekly digest**: Every Friday at 5 PM EST
- **Month-end report**: Last day of month at 11:55 PM EST
- **Housekeeping**: Daily at 2 AM EST

### 4. Verify Setup

```sql
-- Check tables
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

-- Check scheduled jobs
SELECT * FROM cron.job;

-- Check timezone
SHOW timezone;  -- Should be America/New_York
```

---

## Running the Application

### Development Mode

```bash
python -m app.main
```

Or with uvicorn directly:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Or with gunicorn:

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Docker (Optional)

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t captpathfinder .
docker run -p 8000:8000 --env-file .env captpathfinder
```

---

## API Endpoints

### Public Endpoints

#### `POST /webhooks/community`
Receive webhook from community platform.

**Request Body:**
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

### Admin Endpoints

#### `GET /health`
Health check with database status.

#### `GET /admin/stats`
Get system statistics (user counts, pending digests, etc.).

#### `GET /admin/recent-detections?limit=10`
View recent senior executive detections.

#### `POST /admin/send-digests`
Manually trigger sending of pending digests.

#### `POST /admin/generate-reports`
Manually trigger generation of pending reports.

---

## Automation Anywhere Integration

### Email Bot Integration

Edit `app/services/aa_integration.py` in the `_format_digest_for_email()` method:

```python
def _format_digest_for_email(self, digest: DigestPayload) -> Dict[str, Any]:
    # Customize based on your AA email bot's expected format
    return {
        "to": ["stakeholder1@company.com", "stakeholder2@company.com"],
        "subject": f"Weekly Senior Executive Digest: {digest.week_start} - {digest.week_end}",
        "body": html_body,
        "is_html": True
    }
```

### Teams Bot Integration

Edit `app/services/aa_integration.py` in the `_format_digest_for_teams()` method:

```python
def _format_digest_for_teams(self, digest: DigestPayload) -> Dict[str, Any]:
    # Customize based on your AA Teams bot's expected format
    return {
        "channel_url": "https://teams.microsoft.com/l/channel/...",
        "message": message_text,
        "message_type": "markdown"
    }
```

### Testing Integration

Use the admin endpoint to manually trigger a digest send:

```bash
curl -X POST http://localhost:8000/admin/send-digests
```

---

## Scheduled Jobs

### Weekly Digest (Friday 5 PM EST)

1. `pg_cron` calls `build_weekly_digest()` SQL function
2. Function creates digest records in `digests` table (batches of 10)
3. FastAPI service polls for pending digests and sends via AA bots
4. Digests are marked as `sent = TRUE` after successful delivery

**Manual trigger:**
```sql
SELECT build_weekly_digest();
```

### Month-End Report (Last day of month, 11:55 PM EST)

1. `pg_cron` calls `build_month_end_report()` SQL function
2. Function creates report record in `reports` table
3. FastAPI service generates CSV and HTML files
4. Files are stored in Supabase Storage (or local filesystem)
5. Report record is updated with file URIs

**Manual trigger:**
```sql
SELECT build_month_end_report();
```

### Housekeeping (Daily 2 AM EST)

Automatically purges events older than 14 days:

```sql
SELECT purge_old_events();
```

---

## Deployment

### Supabase + Cloud Platform

1. **Deploy FastAPI service** to:
   - Railway
   - Render
   - AWS ECS
   - Google Cloud Run
   - Azure Container Apps

2. **Configure webhook** in community platform to point to your deployed endpoint:
   ```
   https://your-app.railway.app/webhooks/community
   ```

3. **Enable pg_cron** in Supabase:
   - Go to Database → Extensions
   - Enable `pg_cron`
   - Run `scripts/setup_pg_cron.sql`

4. **Setup scheduled worker** to process digests/reports:
   - Option A: Add cron job in your cloud platform to call admin endpoints
   - Option B: Use pg_cron to directly call Python functions via pg_background

### Example: Railway Deployment

1. Create `railway.json`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

2. Add environment variables in Railway dashboard
3. Deploy: `railway up`

---

## Monitoring & Maintenance

### Logging

All components use Python's `logging` module. Logs include:
- Webhook receipt and processing
- Classification results
- Digest/report generation
- AA integration calls
- Errors and exceptions

### Metrics to Monitor

1. **Event processing rate**
   - Query: `SELECT COUNT(*) FROM events_raw WHERE received_at > NOW() - INTERVAL '1 hour'`

2. **Senior user count**
   - Query: `SELECT COUNT(*) FROM user_state`

3. **Pending digests**
   - Query: `SELECT COUNT(*) FROM digests WHERE NOT sent`

4. **Failed AA calls**
   - Check application logs for retry errors

### Database Maintenance

```sql
-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Vacuum and analyze
VACUUM ANALYZE events_raw;
VACUUM ANALYZE detections;
```

---

## Customization

### Adding New Classification Rules

Edit `app/classification/config.json`:

```json
{
  "csuite_patterns": [
    "\\bchief data officer\\b",
    "\\bcdo\\b"
  ]
}
```

Restart the application to reload config.

### Changing Digest Batch Size

Edit `scripts/create_functions.sql`, modify the weekly digest function:

```sql
IF array_length(chunk_array, 1) = 20 THEN  -- Changed from 10 to 20
```

### Adding More Channels

1. Add channel to enum in `migrations/001_initial_schema.sql`:
```sql
channel TEXT CHECK (channel IN ('email', 'teams', 'slack'))
```

2. Implement handler in `app/services/aa_integration.py`

3. Update `build_weekly_digest()` function to create digests for new channel

---

## Testing

### Unit Tests (Example)

Create `tests/test_classification.py`:

```python
from app.classification import classify_title

def test_csuite_detection():
    is_senior, level = classify_title("Chief Executive Officer")
    assert is_senior == True
    assert level == "csuite"

def test_vp_detection():
    is_senior, level = classify_title("VP of Engineering")
    assert is_senior == True
    assert level == "vp"

def test_exclusion():
    is_senior, level = classify_title("Student VP")
    assert is_senior == False
```

Run with:
```bash
pytest tests/
```

### Integration Testing

1. Send test webhook:
```bash
curl -X POST http://localhost:8000/webhooks/community \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "test-001",
    "username": "Test User",
    "profileField": "Job Title",
    "value": "CEO",
    "oldValue": "Director"
  }'
```

2. Check detection:
```bash
curl http://localhost:8000/admin/recent-detections?limit=1
```

---

## Troubleshooting

### Issue: Webhook not processing

**Check:**
1. Application logs for errors
2. Database connectivity: `psql $SUPABASE_DB_URL -c "SELECT 1"`
3. Event stored in `events_raw` table

### Issue: Digests not sending

**Check:**
1. Pending digests: `SELECT * FROM digests WHERE NOT sent`
2. AA bot credentials in `.env`
3. Network connectivity to AA endpoints
4. Application logs for retry errors

### Issue: pg_cron not running

**Check:**
1. Extension enabled: `SELECT * FROM pg_extension WHERE extname = 'pg_cron'`
2. Jobs scheduled: `SELECT * FROM cron.job`
3. Job run history: `SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 10`

---

## License

MIT License - see LICENSE file for details

---

## Support

For issues and questions, please contact your system administrator or open an issue in the repository.

---

**Built with ❤️ for efficient senior executive tracking**

