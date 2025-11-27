# CaptPathfinder

**Senior Executive Detection System for Community Profiles**

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue)](https://github.com/shreya-aapf/CaptPathfinder)
[![Python](https://img.shields.io/badge/Python-3.11+-green)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688)](https://fastapi.tiangolo.com/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E)](https://supabase.com/)

A production-ready system that detects C-suite and VP-level executives from community profile updates, sends weekly digests via Automation Anywhere bots, and generates monthly reports.

**Key Features:**
- ✅ Regex-based classification (config-driven, no code changes)
- ✅ Minimal storage (only senior execs)
- ✅ Weekly digests via AA bots
- ✅ Monthly CSV/HTML reports
- ✅ Idempotent processing
- ✅ Production-ready

---

## 📋 Table of Contents

- [🚀 Quick Start](#-quick-start-5-minutes)
- [⚙️ Environment Setup](#️-environment-setup)
- [📖 System Overview](#-system-overview)
- [🏗️ Architecture](#️-architecture)
- [🔌 API Reference](#-api-reference)
- [🤖 Automation Anywhere Integration](#-automation-anywhere-integration)
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
- Automation Anywhere Control Room access

### Step 1: Clone and Install

```bash
git clone https://github.com/shreya-aapf/CaptPathfinder.git
cd CaptPathfinder

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

**Get Supabase Connection String:**
1. Go to https://app.supabase.com → Your Project
2. Settings → Database → Connection String → URI
3. Click Copy 📋

**Create `.env` file:**
```bash
# Database
SUPABASE_DB_URL=<paste-supabase-connection-string>

# Automation Anywhere
AA_CONTROL_ROOM_URL=https://your-instance.automationanywhere.digital
AA_API_KEY=your-api-key
AA_EMAIL_BOT_ID=your-email-bot-file-id
AA_TEAMS_BOT_ID=your-teams-bot-file-id
AA_RUN_AS_USER_ID=your-user-id
```

### Step 3: Setup Database

```bash
# Run migrations
psql YOUR_SUPABASE_URL -f migrations/001_initial_schema.sql
psql YOUR_SUPABASE_URL -f scripts/create_functions.sql
psql YOUR_SUPABASE_URL -f scripts/setup_pg_cron.sql
```

### Step 4: Run Application

```bash
python -m app.main
```

API available at: `http://localhost:8000`

### Step 5: Test It

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

✅ **You're running!** Continue reading for detailed configuration.

</details>

---

## ⚙️ Environment Setup

<details>
<summary><b>Click to expand Environment Setup Guide</b></summary>

### Supabase Database Connection - THE EASY WAY! 🎯

**Don't construct the URL manually!** Supabase gives it to you:

#### Copy from Supabase Dashboard (Recommended ✅)

1. Go to https://app.supabase.com → Your Project
2. Click **Settings** (gear icon in sidebar)
3. Click **Database**
4. Scroll to **Connection String** section
5. Select **URI** tab
6. Click **Copy** button 📋
7. Paste it as your `SUPABASE_DB_URL`

**That's it!** The connection string is already formatted correctly.

#### Use Connection Pooler (For Production)

Supabase also provides a connection pooler URL (recommended for serverless/production):

1. Same steps as above, but select **Connection pooling** → **Transaction** mode
2. Copy that URL instead
3. Ends with `:6543/postgres` instead of `:5432/postgres`

**Example:**
```
postgresql://postgres.xyzabcdefgh:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

### Automation Anywhere Configuration

#### Required Environment Variables

```bash
# Control Room URL
AA_CONTROL_ROOM_URL=https://your-instance.automationanywhere.digital

# Authentication - API Key (recommended)
AA_API_KEY=your-api-key-here

# Bot File IDs (from Control Room)
AA_EMAIL_BOT_ID=12345678-1234-1234-1234-123456789abc
AA_TEAMS_BOT_ID=87654321-4321-4321-4321-cba987654321

# User ID to run bots as
AA_RUN_AS_USER_ID=your-user-id-here
```

#### Finding Bot IDs (File IDs)

**In Control Room:**
1. Navigate to **Automation** tab
2. Find your bot in the list
3. Right-click → **Properties**
4. Copy the **File ID** (this is your Bot ID)

**Example File ID:** `a1b2c3d4-1234-5678-90ab-cdef12345678`

#### Finding Your User ID

**In Control Room:**
1. Go to **Administration** → **Users**
2. Click on your username
3. Copy the User ID from URL or details panel

#### Getting API Key

**Option A: Generate API Key (Recommended)**
1. Control Room → **My Settings** → **My Credentials**
2. Click **Generate API Key**
3. Copy immediately (won't be shown again)

**Option B: Username/Password**
```bash
AA_USERNAME=your-username
AA_PASSWORD=your-password
```

### Optional Configuration

```bash
# Community Platform API (for fetching user metadata)
COMMUNITY_API_URL=https://your-community-platform.com/api
COMMUNITY_API_KEY=your-api-key-here

# Application Settings
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Supabase Storage (for cloud report storage)
SUPABASE_STORAGE_URL=https://projectid.supabase.co/storage/v1
SUPABASE_STORAGE_BUCKET=reports
SUPABASE_ANON_KEY=your-anon-key-here
```

### Minimal Working Configuration

Your `.env` file only needs:

```bash
SUPABASE_DB_URL=<copied-from-supabase>
AA_CONTROL_ROOM_URL=https://your-instance.automationanywhere.digital
AA_API_KEY=your-api-key
AA_EMAIL_BOT_ID=your-bot-id
AA_TEAMS_BOT_ID=your-bot-id
AA_RUN_AS_USER_ID=your-user-id
```

Everything else has sensible defaults!

### Troubleshooting Environment Setup

**"Connection refused" error?**
- Make sure you copied the entire connection string from Supabase
- Check if you're using the right password

**"SSL required" error?**
- The Supabase connection string already includes SSL
- Re-copy from dashboard if you modified it

**"Invalid API Key" error?**
- Verify AA_API_KEY is correct
- Check if it has expired
- Ensure it has bot deployment permissions

</details>

---

## 📖 System Overview

<details>
<summary><b>Click to expand System Overview</b></summary>

### What is CaptPathfinder?

CaptPathfinder processes webhook events from a community platform to identify when users update their job titles to senior executive positions (VP or C-suite level).

### What It Does

1. **Receives Webhooks** - Accepts profile update events from your community platform
2. **Classifies Titles** - Uses regex-based rules to detect C-suite and VP-level positions
3. **Stores Selectively** - Only keeps senior executives in database (minimizes storage)
4. **Sends Weekly Digests** - Deploys AA bots to send email and Teams notifications
5. **Generates Monthly Reports** - Creates CSV and HTML reports with statistics

### How It Works

```
Community Platform
      │
      │ Webhook: Job Title Updated
      ▼
┌─────────────────────┐
│  FastAPI Service    │ → Validates, deduplicates
│  (This App)         │
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│  Classification     │ → Regex rules (config-driven)
│  Engine             │
└─────────────────────┘
      │
      ├─ Senior? → Store in database
      └─ Not Senior? → Delete if exists
      │
      ▼
┌─────────────────────┐
│  Supabase/          │ → Only senior execs stored
│  PostgreSQL         │
└─────────────────────┘
      │
      │ pg_cron (scheduled)
      ▼
┌─────────────────────┐
│  Weekly Digests     │ → Friday 5 PM EST
│  Monthly Reports    │ → Last day of month
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│  Automation         │ → Deploys bots with
│  Anywhere Bots      │   input variables
└─────────────────────┘
```

### Key Features

✅ **Config-Driven Classification** - Edit `app/classification/config.json` without code changes  
✅ **Idempotent Processing** - Safe to replay webhooks  
✅ **Minimal Storage** - Only senior execs kept in database  
✅ **Automated Scheduling** - pg_cron handles all scheduling  
✅ **Production-Ready** - Retry logic, error handling, comprehensive logging  
✅ **Scalable** - Stateless services, horizontal scaling ready  

### Project Structure

```
CaptPathfinder/
├── app/                     # Application code
│   ├── main.py             # FastAPI application
│   ├── classification/     # Seniority detection
│   │   ├── rules.py       # Classification logic
│   │   └── config.json    # 🔧 EDIT: Classification patterns
│   ├── services/           # Business logic
│   │   ├── event_processor.py
│   │   ├── digest_builder.py
│   │   ├── report_builder.py
│   │   └── aa_integration.py
│   └── utils/              # Helpers
├── migrations/             # Database schema
│   └── 001_initial_schema.sql
├── scripts/                # SQL functions & cron
│   ├── create_functions.sql
│   └── setup_pg_cron.sql
├── worker.py               # Background worker
├── test_classification.py  # Test script
└── requirements.txt        # Dependencies
```

### Database Tables

- **`field_registry`** - Configuration (stores "Job Title")
- **`events_raw`** - Short-lived audit trail (14-day retention)
- **`user_state`** - Current senior executives ONLY
- **`detections`** - Historical detections for reporting
- **`digests`** - Pending/sent weekly digests
- **`reports`** - Month-end reports metadata

### Scheduled Jobs

| Job | Schedule | Purpose |
|-----|----------|---------|
| Weekly Digest | Friday 5 PM EST | Send email & Teams digests |
| Month-End Report | Last day @ 11:55 PM EST | Generate CSV/HTML reports |
| Housekeeping | Daily 2 AM EST | Purge events >14 days old |

</details>

---

## 🏗️ Architecture

<details>
<summary><b>Click to expand Architecture Details</b></summary>

### System Flow Diagram

```
┌─────────────────┐
│  Community      │
│  Platform       │
└─────────────────┘
         │
         │ POST /webhooks/community
         ▼
┌─────────────────────────────┐
│  FastAPI Web Service        │
│  - Validate with Pydantic   │
│  - Generate idempotency key │
│  - Store in events_raw      │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Event Processor            │
│  - Fetch user metadata      │
│  - Call classification      │
│  - Update user_state        │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Classification Engine      │
│  - Normalize title          │
│  - Check exclusions         │
│  - Match C-suite patterns   │
│  - Match VP patterns        │
└─────────────────────────────┘
         │
         ├─── Senior? ───────┐
         │                   │
         ▼                   ▼
   ┌──────────┐      ┌──────────────┐
   │  DELETE  │      │ INSERT/UPDATE│
   │  from    │      │ user_state   │
   │  user_   │      │ + detections │
   │  state   │      └──────────────┘
   └──────────┘              │
                             │
         ┌───────────────────┘
         ▼
┌─────────────────────────────┐
│  Supabase PostgreSQL        │
│  - user_state (seniors only)│
│  - detections (history)     │
│  - digests (pending)        │
└─────────────────────────────┘
         │
         │ pg_cron triggers
         ▼
┌─────────────────────────────┐
│  SQL Functions              │
│  - build_weekly_digest()    │
│  - build_month_end_report() │
│  - purge_old_events()       │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Worker Process             │
│  - Poll pending digests     │
│  - Deploy AA bots           │
│  - Generate reports         │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Automation Anywhere        │
│  POST /v4/automations/deploy│
│  - Email bot with inputs    │
│  - Teams bot with inputs    │
└─────────────────────────────┘
```

### Classification Logic Flow

```
Job Title Input
      │
      ▼
Normalize (lowercase, trim, remove punctuation)
      │
      ▼
Check Exclusions (student, retired, volunteer, etc.)
      │
      ├─ Match? → Return (False, "")
      │
      ▼
Check C-Suite Patterns (CEO, CFO, Chief..., President)
      │
      ├─ Match? → Return (True, "csuite")
      │
      ▼
Check VP Patterns (VP, Vice President, SVP, EVP)
      │
      ├─ Match? → Return (True, "vp")
      │
      ▼
No Match → Return (False, "")
```

### Data Flow: Webhook to Detection

1. **Webhook Arrives**
   - Validate JSON with Pydantic
   - Extract userId, profileField, value

2. **Idempotency Check**
   - Generate hash: SHA256(userId + field + value)
   - Check if already processed

3. **Job Title Check**
   - Is profileField == "Job Title"?
   - If NO → Skip or store minimal
   - If YES → Continue

4. **Store Raw Event**
   - INSERT INTO events_raw
   - ON CONFLICT DO NOTHING (idempotency)

5. **Fetch Metadata**
   - Get country, company, joined_at
   - From webhook or community API

6. **Classify Title**
   - Run through classification engine
   - Return (is_senior, level)

7. **Update State**
   - If NOT senior → DELETE from user_state
   - If senior → INSERT/UPDATE user_state + detections

8. **Response**
   - Return success with classification result

### Scheduled Jobs Architecture

```
PostgreSQL pg_cron
      │
      ├─ Friday 5 PM ──►┌──────────────────────┐
      │                  │ build_weekly_digest()│
      │                  └──────────────────────┘
      │                           │
      │                           ▼
      │                  ┌──────────────────────┐
      │                  │ INSERT INTO digests  │
      │                  │ (batches of 10)      │
      │                  └──────────────────────┘
      │
      ├─ Last day 11:55 PM ──►┌────────────────────────┐
      │                        │build_month_end_report()│
      │                        └────────────────────────┘
      │                                 │
      │                                 ▼
      │                        ┌────────────────────────┐
      │                        │ INSERT INTO reports    │
      │                        │ (metadata only)        │
      │                        └────────────────────────┘
      │
      └─ Daily 2 AM ──►┌────────────────┐
                       │purge_old_events()│
                       └────────────────┘
```

### Worker Process Flow

```
Worker Runs (every 10 min or triggered)
      │
      ├─►┌──────────────────────────┐
      │  │ Get pending digests      │
      │  │ (SELECT ... SKIP LOCKED) │
      │  └──────────────────────────┘
      │           │
      │           ▼
      │  ┌──────────────────────────┐
      │  │ For each digest:         │
      │  │ - Prepare bot inputs     │
      │  │ - Deploy AA bot          │
      │  │ - Mark as sent           │
      │  └──────────────────────────┘
      │
      └─►┌──────────────────────────┐
         │ Get pending reports      │
         │ (file_uri IS NULL)       │
         └──────────────────────────┘
                  │
                  ▼
         ┌──────────────────────────┐
         │ For each report:         │
         │ - Generate CSV           │
         │ - Generate HTML          │
         │ - Update file_uri        │
         └──────────────────────────┘
```

### Concurrency & Queue Management

Uses PostgreSQL's `SKIP LOCKED` for safe concurrent processing:

```sql
-- Multiple workers can run simultaneously
-- Each gets different records (no duplicates)

SELECT * FROM digests
WHERE NOT sent
FOR UPDATE SKIP LOCKED
LIMIT 10;
```

```
Worker 1 ──►  Digest A (locked)
Worker 2 ──►  Digest B (locked)  
Worker 3 ──►  Digest C (locked)

All process independently!
No external queue needed.
```

</details>

---

## 🔌 API Reference

<details>
<summary><b>Click to expand API Reference</b></summary>

### Base URL

```
http://localhost:8000  (development)
https://your-app.com   (production)
```

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
  "oldValue": "Sales Manager",
  "country": "USA",          // Optional
  "company": "Tech Corp",    // Optional
  "joined_at": "2024-01-15"  // Optional
}
```

**Response (200 OK):**
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

**Response (Duplicate):**
```json
{
  "status": "accepted",
  "result": {
    "status": "duplicate",
    "user_id": "2000"
  }
}
```

**Response (Not Job Title):**
```json
{
  "status": "accepted",
  "result": {
    "status": "skipped",
    "reason": "not_job_title",
    "user_id": "2000"
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
  "timestamp": "2025-11-27T10:30:00Z"
}
```

#### `GET /`

Root endpoint with service info.

**Response:**
```json
{
  "service": "CaptPathfinder",
  "status": "running",
  "version": "1.0.0"
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
    "total_detections": 230,
    "unprocessed_events": 0
  }
}
```

#### `GET /admin/recent-detections?limit=10`

View recent senior executive detections.

**Parameters:**
- `limit` (optional): Number of results (default: 10)

**Response:**
```json
{
  "detections": [
    {
      "user_id": "123",
      "username": "Jane Doe",
      "title": "Chief Executive Officer",
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

**Response:**
```json
{
  "status": "completed",
  "results": {
    "total": 4,
    "sent": 3,
    "failed": 1,
    "errors": ["Digest 123: Connection timeout"]
  }
}
```

#### `POST /admin/generate-reports`

Manually trigger generation of pending reports.

**Response:**
```json
{
  "status": "completed",
  "results": {
    "total": 1,
    "generated": 1,
    "failed": 0,
    "errors": []
  }
}
```

### Error Responses

**400 Bad Request:**
```json
{
  "detail": "Invalid request: userId is required"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Error processing webhook: Database connection failed"
}
```

### Rate Limiting

Consider adding rate limiting in production:
- Webhook endpoint: 100 requests/minute per IP
- Admin endpoints: Require authentication

### Authentication

Admin endpoints can be protected with API key:

```python
# Add to headers
X-Admin-Token: your-secret-token
```

</details>

---

## 🤖 Automation Anywhere Integration

<details>
<summary><b>Click to expand AA Integration Guide</b></summary>

### Overview

CaptPathfinder deploys AA bots using the Bot Deploy API v4. Bots receive input variables and execute to send emails or Teams messages.

**API Documentation:** https://docs.automationanywhere.com/bundle/enterprise-v2019/page/deploy-api-supported-v4.html

### How It Works

```
CaptPathfinder
    ↓
POST /v4/automations/deploy
    ↓
{
  "fileId": "bot-id",
  "runAsUserIds": ["user-id"],
  "botInput": [
    {"name": "emailTo", "value": "email@example.com"},
    {"name": "emailSubject", "value": "Subject"}
  ]
}
    ↓
Bot executes with input variables
    ↓
Email/Teams message sent
```

### Creating Your Bots

#### Email Bot Requirements

Your bot should accept these input variables:

| Variable Name | Type | Description | Example |
|--------------|------|-------------|---------|
| `emailTo` | String | Semicolon-separated emails | `user1@company.com;user2@company.com` |
| `emailSubject` | String | Email subject | `Weekly Digest: 2025-11-20 - 2025-11-27` |
| `emailBody` | String | HTML email body | `<html>...</html>` |
| `isHTML` | String | "true" or "false" | `true` |
| `weekStart` | String | Week start date | `2025-11-20` |
| `weekEnd` | String | Week end date | `2025-11-27` |
| `totalCount` | String | Number of detections | `15` |

**Sample Bot Flow:**
```
1. Read input variables ($emailTo$, $emailSubject$, etc.)
2. Use Office 365/Outlook package:
   - Send email
   - To: $emailTo$
   - Subject: $emailSubject$
   - Body: $emailBody$
   - Format: HTML
3. Log success/failure
```

#### Teams Bot Requirements

Your bot should accept these input variables:

| Variable Name | Type | Description | Example |
|--------------|------|-------------|---------|
| `teamsChannelWebhook` | String | Teams webhook URL | `https://outlook.office.com/webhook/...` |
| `messageText` | String | Message (markdown) | `**Title**\nMessage content...` |
| `messageType` | String | "markdown" or "plain" | `markdown` |
| `weekStart` | String | Week start date | `2025-11-20` |
| `weekEnd` | String | Week end date | `2025-11-27` |
| `totalCount` | String | Number of detections | `15` |

**Sample Bot Flow:**
```
1. Read input variables
2. Use HTTP package:
   - POST to $teamsChannelWebhook$
   - Body: {"text": "$messageText$"}
   - Headers: Content-Type: application/json
3. Log response
```

### Customizing Input Variables

If your bots use different variable names, edit `app/services/aa_integration.py`:

**For Email Bot:**

Find `_prepare_email_bot_inputs()`:

```python
def _prepare_email_bot_inputs(self, digest: DigestPayload) -> Dict[str, Any]:
    bot_inputs = {
        "emailTo": "your@email.com",      # 🔧 Change name here
        "emailSubject": f"Subject...",    # 🔧 Change name here
        "emailBody": html_body,           # 🔧 Change name here
        "isHTML": "true",
        # Add custom variables:
        "customField": "customValue"
    }
    return bot_inputs
```

**For Teams Bot:**

Find `_prepare_teams_bot_inputs()`:

```python
def _prepare_teams_bot_inputs(self, digest: DigestPayload) -> Dict[str, Any]:
    bot_inputs = {
        "teamsWebhook": "https://...",    # 🔧 Change name here
        "message": message_text,          # 🔧 Change name here
        # Add custom variables
    }
    return bot_inputs
```

### Testing Your Integration

#### Step 1: Test Bot Manually

1. Open bot in Control Room
2. **Run** → **Run with inputs**
3. Provide sample values
4. Verify execution

#### Step 2: Test via API (curl)

```bash
curl -X POST \
  https://your-instance.automationanywhere.digital/v4/automations/deploy \
  -H "X-Authorization: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "fileId": "YOUR_BOT_ID",
    "runAsUserIds": ["YOUR_USER_ID"],
    "botInput": [
      {"name": "emailTo", "value": "test@example.com"},
      {"name": "emailSubject", "value": "Test"},
      {"name": "emailBody", "value": "<h1>Test</h1>"},
      {"name": "isHTML", "value": "true"}
    ]
  }'
```

#### Step 3: Test via CaptPathfinder

```bash
# Trigger digest manually
curl -X POST http://localhost:8000/admin/send-digests
```

Check logs for deployment status.

### API Response Format

Successful deployment:

```json
{
  "deploymentId": "550e8400-e29b-41d4-a716-446655440000",
  "statusUrl": "/v4/activity/execution/550e8400-e29b-41d4-a716-446655440000"
}
```

### Troubleshooting AA Integration

**Error: "Invalid API Key"**
- Verify `AA_API_KEY` in `.env`
- Check if key expired
- Ensure key has deploy permissions

**Error: "Bot not found"**
- Verify Bot ID is correct
- Check bot exists in Control Room
- Ensure bot is in accessible folder

**Error: "User not authorized"**
- Verify `AA_RUN_AS_USER_ID`
- User needs "Run Bot" permission
- Check bot is shared with user

**Bot deploys but doesn't send**
- Check bot logs in Control Room Activity
- Verify input variable names match
- Ensure bot has required packages
- Check email/Teams credentials in bot

### Best Practices

1. ✅ Use API Key auth (more secure)
2. ✅ Test bots manually first
3. ✅ Handle errors gracefully
4. ✅ Monitor bot runs in Activity tab
5. ✅ Keep variables simple (all strings)
6. ✅ Log everything in bots

</details>

---

## 🚢 Deployment

<details>
<summary><b>Click to expand Deployment Guide</b></summary>

### Deployment Options

#### Option 1: Railway (Recommended)

**Pros:** Simple, fast, auto-HTTPS  
**Cons:** Can be expensive at scale

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Add environment variables in dashboard
# Run migrations
railway run psql $DATABASE_URL -f migrations/001_initial_schema.sql
```

#### Option 2: Render

**Pros:** Free tier available  
**Cons:** Cold starts on free tier

1. Connect GitHub repo
2. Select Python environment
3. Build: `pip install -r requirements.txt`
4. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add env vars in dashboard

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

#### Option 4: AWS / GCP / Azure

- AWS ECS with Fargate
- Google Cloud Run
- Azure Container Apps
- Deploy Docker image
- Configure environment variables
- Setup load balancer
- Enable auto-scaling

### Worker Setup

Process digests/reports independently:

**Option A: Cron (Linux/Mac)**
```bash
crontab -e

# Every 10 minutes
*/10 * * * * cd /path/to/CaptPathfinder && /path/to/venv/bin/python worker.py
```

**Option B: Windows Task Scheduler**
- Create task
- Run `python worker.py` every 10 min

**Option C: Cloud Scheduler**
- Setup HTTP trigger to `/admin/send-digests`
- Or deploy worker.py as separate function

### Environment Variables in Production

- **Railway/Render:** Use dashboard
- **AWS:** AWS Secrets Manager
- **GCP:** Secret Manager
- **Docker:** `--env-file` or orchestrator secrets

### Database Considerations

**Supabase (Recommended):**
- Managed PostgreSQL
- pg_cron built-in
- Auto backups
- No maintenance

**Self-Managed:**
- Requires pg_cron installation
- Manual backups
- More control

### Scaling

**Horizontal Scaling:**
- Add more web service replicas
- Stateless design allows easy scaling
- Use load balancer

**Database:**
- Connection pooling (use Supabase pooler)
- Read replicas for analytics
- Regular vacuuming

### SSL/HTTPS

- Railway/Render: Automatic
- Custom domain: Configure DNS + SSL cert
- Use Let's Encrypt for free certs

### Monitoring

Setup these:
- Application logs
- Error tracking (Sentry)
- Uptime monitoring
- Database metrics
- AA bot run tracking

</details>

---

## 🎨 Customization

<details>
<summary><b>Click to expand Customization Guide</b></summary>

### Changing Classification Rules

Edit `app/classification/config.json`:

```json
{
  "version": "v1",
  "exclusion_patterns": [
    "student",
    "volunteer",
    "contractor"     // Add this
  ],
  "csuite_patterns": [
    "\\bceo\\b",
    "\\bcdo\\b"      // Add Chief Data Officer
  ],
  "vp_patterns": [
    "\\bvp\\b",
    "\\bavp\\b"      // Add AVP
  ]
}
```

Test changes:
```bash
python test_classification.py
```

### Customizing Email Templates

Edit `app/services/aa_integration.py` → `_build_email_html()`:

```python
def _build_email_html(self, digest: DigestPayload) -> str:
    html = f"""
    <html>
    <head>
        <style>
            /* Your custom CSS */
            body {{ font-family: 'Your Font'; }}
            .logo {{ width: 200px; }}
        </style>
    </head>
    <body>
        <img src="https://your-logo.png" class="logo">
        <h1>Your Custom Title</h1>
        <!-- Your template -->
    </body>
    </html>
    """
    return html
```

### Customizing Teams Messages

Edit `app/services/aa_integration.py` → `_prepare_teams_bot_inputs()`:

```python
# Use Adaptive Cards
adaptive_card = {
    "type": "AdaptiveCard",
    "version": "1.4",
    "body": [
        {
            "type": "TextBlock",
            "text": "Custom Title",
            "size": "large"
        }
    ]
}
```

### Changing Digest Schedule

Edit `scripts/setup_pg_cron.sql`:

```sql
-- Change to Monday 9 AM
SELECT cron.schedule(
    'weekly-digest',
    '0 9 * * MON',  -- Changed
    $$SELECT build_weekly_digest();$$
);
```

Re-run setup:
```bash
psql $DB_URL -f scripts/setup_pg_cron.sql
```

### Adding Custom Metadata Fields

1. **Update database:**
```sql
ALTER TABLE user_state ADD COLUMN department TEXT;
```

2. **Update models:**
```python
# app/models.py
class WebhookEvent(BaseModel):
    # ...
    department: Optional[str] = None
```

3. **Update processor:**
```python
# app/services/event_processor.py
# Add department to INSERT/UPDATE queries
```

### Changing Batch Sizes

Edit `scripts/create_functions.sql`:

```sql
-- Change from 10 to 20
IF array_length(chunk_array, 1) = 20 THEN
```

### Adding New Channels (Slack, etc.)

1. **Update enum:**
```sql
ALTER TABLE digests DROP CONSTRAINT digests_channel_check;
ALTER TABLE digests ADD CONSTRAINT digests_channel_check 
  CHECK (channel IN ('email', 'teams', 'slack'));
```

2. **Add bot config:**
```bash
# .env
AA_SLACK_BOT_ID=your-slack-bot-id
```

3. **Implement handler:**
```python
# app/services/aa_integration.py
async def send_slack_digest(self, digest):
    # Implementation
```

</details>

---

## 📊 Monitoring

<details>
<summary><b>Click to expand Monitoring Guide</b></summary>

### Key Metrics

```sql
-- Senior users count
SELECT COUNT(*) FROM user_state;

-- By level
SELECT seniority_level, COUNT(*) 
FROM user_state 
GROUP BY seniority_level;

-- Pending digests
SELECT COUNT(*) FROM digests WHERE NOT sent;

-- Events processed today
SELECT COUNT(*) FROM events_raw 
WHERE received_at > CURRENT_DATE;
```

### Application Logs

```bash
# View logs
tail -f app.log

# Or systemd
journalctl -u captpathfinder -f
```

### Database Monitoring

```sql
-- Table sizes
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size('public.'||tablename))
FROM pg_tables
WHERE schemaname = 'public';

-- Cron job history
SELECT * FROM cron.job_run_details 
ORDER BY start_time DESC 
LIMIT 10;
```

### Alerts to Setup

- API response time > 2s
- Error rate > 1%
- Pending digests > 50
- Database connection failures
- AA bot deployment failures

### Health Checks

```bash
# Basic health
curl http://localhost:8000/health

# Detailed stats
curl http://localhost:8000/admin/stats
```

</details>

---

## ❓ Troubleshooting

<details>
<summary><b>Click to expand Troubleshooting Guide</b></summary>

### Webhook Not Processing

**Symptoms:** Webhooks received but no detections

**Check:**
1. Application logs: `tail -f app.log`
2. Database: `SELECT * FROM events_raw ORDER BY received_at DESC LIMIT 5`
3. Classification: `python test_classification.py`

**Solutions:**
- Verify `profileField` exactly matches "Job Title"
- Check classification rules in `config.json`
- Ensure database connection is working

### Digests Not Sending

**Symptoms:** Digests created but not sent

**Check:**
```sql
SELECT * FROM digests WHERE NOT sent ORDER BY created_at DESC;
```

**Solutions:**
- Verify AA credentials in `.env`
- Check Bot IDs are correct
- Test manual trigger: `curl -X POST http://localhost:8000/admin/send-digests`
- Check AA bot logs in Control Room

### pg_cron Not Running

**Check:**
```sql
-- Extension enabled?
SELECT * FROM pg_extension WHERE extname = 'pg_cron';

-- Jobs scheduled?
SELECT * FROM cron.job;

-- Job history
SELECT * FROM cron.job_run_details 
ORDER BY start_time DESC 
LIMIT 10;
```

**Solutions:**
```sql
-- Enable extension
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Re-run setup
\i scripts/setup_pg_cron.sql
```

### Classification Not Working

**Test specific title:**
```bash
python -c "from app.classification import classify_title; print(classify_title('CEO'))"
```

**Review patterns:**
```bash
cat app/classification/config.json
```

**Test all rules:**
```bash
python test_classification.py
```

### Database Connection Issues

**Error: Connection refused**

Solutions:
- Verify `SUPABASE_DB_URL` in `.env`
- Test: `psql $SUPABASE_DB_URL -c "SELECT 1"`
- Check IP whitelist in Supabase

**Error: SSL required**

Solutions:
- Re-copy connection string from Supabase
- Ensure `?sslmode=require` is included

### AA Integration Issues

**Error: Invalid API Key**
- Check `AA_API_KEY` in `.env`
- Verify key hasn't expired
- Test in Control Room API docs

**Error: Bot not found**
- Verify Bot ID (File ID) is correct
- Check bot exists in Control Room
- Right-click bot → Properties → Copy File ID

**Bot deploys but fails**
- Check Activity logs in Control Room
- Verify input variable names match bot
- Ensure bot has required packages
- Check credentials in bot

### Performance Issues

**Slow webhook response:**
- Check database query performance
- Review classification regex complexity
- Add database indexes if needed

**High memory usage:**
- Check for connection leaks
- Review async task handling
- Monitor with `htop` or similar

</details>

---

## 📚 Additional Resources

### Testing

```bash
# Test classification
python test_classification.py

# Test webhook
curl -X POST http://localhost:8000/webhooks/community \
  -H "Content-Type: application/json" \
  -d @test_webhook.json

# Test digests
curl -X POST http://localhost:8000/admin/send-digests

# Run worker
python worker.py
```

### Tech Stack

- **Language:** Python 3.11+
- **Web Framework:** FastAPI
- **Database:** Supabase (PostgreSQL 13+)
- **Validation:** Pydantic
- **HTTP Client:** httpx (async)
- **Retry Logic:** tenacity
- **Scheduling:** pg_cron

### API Documentation

- **Automation Anywhere:** https://docs.automationanywhere.com/bundle/enterprise-v2019/page/deploy-api-supported-v4.html
- **Supabase:** https://supabase.com/docs
- **FastAPI:** https://fastapi.tiangolo.com/

### Project Links

- **GitHub:** https://github.com/shreya-aapf/CaptPathfinder
- **Issues:** https://github.com/shreya-aapf/CaptPathfinder/issues

### License

MIT License - Free to use and modify

### Support

- Open an issue on GitHub
- Check documentation sections above
- Review inline code comments

---

## 🎯 Quick Reference

### Start Application
```bash
python -m app.main
```

### Test Classification
```bash
python test_classification.py
```

### Run Worker
```bash
python worker.py
```

### Test Webhook
```bash
curl -X POST http://localhost:8000/webhooks/community \
  -H "Content-Type: application/json" \
  -d '{"userId":"123","username":"Jane","profileField":"Job Title","value":"CEO"}'
```

### View Stats
```bash
curl http://localhost:8000/admin/stats
```

### Send Digests
```bash
curl -X POST http://localhost:8000/admin/send-digests
```

### Check Logs
```bash
tail -f app.log
```

---

**Built with ❤️ for efficient senior executive tracking**

**Ready to deploy? See the [Deployment section](#-deployment) above!** 🚀
