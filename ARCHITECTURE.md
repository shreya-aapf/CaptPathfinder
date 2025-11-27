# System Architecture & Flow

This document explains how all components of CaptPathfinder work together.

---

## 🔄 Complete System Flow

### 1. Webhook Reception & Event Processing

```
Community Platform
      │
      │ HTTP POST
      ▼
┌─────────────────────────────────────────┐
│  FastAPI: POST /webhooks/community      │
│  Handler: app/main.py                   │
└─────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────┐
│  EventProcessor                          │
│  File: app/services/event_processor.py  │
│                                          │
│  1. Generate idempotency key            │
│  2. Check if "Job Title" field          │
│  3. Store in events_raw table           │
│  4. Fetch user metadata (if needed)     │
│  5. Call classification                 │
└─────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────┐
│  SeniorityClassifier                     │
│  File: app/classification/rules.py      │
│  Config: app/classification/config.json │
│                                          │
│  1. Normalize title (lowercase, trim)   │
│  2. Check exclusion patterns            │
│  3. Check C-suite patterns              │
│  4. Check VP patterns                   │
│  5. Return (is_senior, level)           │
└─────────────────────────────────────────┘
      │
      ├─── NOT SENIOR ────► Delete from user_state (if exists)
      │
      └─── IS SENIOR ─────► Update/Insert user_state
                                   │
                                   └─► Insert into detections (if first time or promotion)
```

### 2. Weekly Digest Flow

```
┌─────────────────────────────────────┐
│  pg_cron Scheduler                  │
│  Every Friday 5 PM EST              │
│  Job: 'weekly-digest'               │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  SQL Function: build_weekly_digest()│
│  File: scripts/create_functions.sql│
│                                      │
│  1. Get last 7 days detections      │
│  2. Filter not included_in_digest   │
│  3. Chunk into batches of 10        │
│  4. For each channel (email, teams):│
│     - Insert into digests table     │
│  5. Mark detections as included     │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  Database: digests table            │
│  Status: sent = FALSE               │
└─────────────────────────────────────┘
      │
      │ (Polled by worker or triggered via API)
      ▼
┌─────────────────────────────────────┐
│  DigestSender                        │
│  File: app/services/digest_builder.py│
│                                      │
│  1. Get pending digests (SKIP LOCKED)│
│  2. Build DigestPayload              │
│  3. Call AA client                  │
│  4. Mark digest as sent             │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  AutomationAnywhereClient            │
│  File: app/services/aa_integration.py│
│                                      │
│  1. Format for email or Teams        │
│  2. HTTP POST to AA bot endpoint    │
│  3. Retry on failure (tenacity)     │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  Automation Anywhere Bots            │
│  - Email Bot → Sends email          │
│  - Teams Bot → Posts to Teams       │
└─────────────────────────────────────┘
```

### 3. Month-End Report Flow

```
┌─────────────────────────────────────┐
│  pg_cron Scheduler                  │
│  Last day of month, 11:55 PM EST    │
│  Job: 'month-end-report'            │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  SQL Function:                       │
│  build_month_end_report()           │
│                                      │
│  1. Get current month label         │
│  2. Calculate summary stats         │
│  3. Insert into reports table       │
│     (file_uri = NULL initially)     │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  Database: reports table             │
│  Status: file_uri = NULL            │
└─────────────────────────────────────┘
      │
      │ (Polled by worker or triggered via API)
      ▼
┌─────────────────────────────────────┐
│  ReportBuilder                       │
│  File: app/services/report_builder.py│
│                                      │
│  1. Get pending reports             │
│  2. Query user_state for month data │
│  3. Generate CSV content            │
│  4. Generate HTML content           │
│  5. Save to storage                 │
│  6. Update report with file_uri     │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  File Storage                        │
│  - Local: ./reports/                │
│  - Or: Supabase Storage             │
│                                      │
│  Files:                             │
│  - report_2025-11.csv               │
│  - report_2025-11.html              │
└─────────────────────────────────────┘
```

### 4. Housekeeping Flow

```
┌─────────────────────────────────────┐
│  pg_cron Scheduler                  │
│  Daily at 2 AM EST                  │
│  Job: 'housekeeping'                │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  SQL Function: purge_old_events()   │
│                                      │
│  DELETE FROM events_raw             │
│  WHERE received_at < NOW() - 14d    │
└─────────────────────────────────────┘
```

---

## 📊 Data Model Relationships

```
┌─────────────────┐
│  field_registry │  (Configuration: "Job Title")
└─────────────────┘

┌─────────────────┐
│  events_raw     │  (Short-lived audit trail)
│  - idempotency  │
│  - processed    │
└─────────────────┘

┌─────────────────┐         ┌─────────────────┐
│  user_state     │◄────────│  detections     │
│  (Only seniors) │ FK      │  (History)      │
│                 │         │                 │
│  - user_id (PK) │         │  - user_id (FK) │
│  - title        │         │  - title        │
│  - level        │         │  - detected_at  │
│  - joined_at    │         │  - included_in  │
└─────────────────┘         └─────────────────┘
                                     │
                                     │ Referenced by
                                     ▼
                            ┌─────────────────┐
                            │  digests        │
                            │  - payload      │
                            │  - sent         │
                            └─────────────────┘

                            ┌─────────────────┐
                            │  reports        │
                            │  - month_label  │
                            │  - file_uri     │
                            │  - summary      │
                            └─────────────────┘
```

---

## 🔐 Security Flow

### Request Authentication

```
External Request
      │
      ▼
┌─────────────────────────────────────┐
│  Cloud Load Balancer                │
│  - SSL Termination                  │
│  - DDoS Protection                  │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  Rate Limiter (FastAPI middleware)  │
│  - 100 req/min per IP               │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  Admin Endpoint Guard (if admin)    │
│  - Verify X-Admin-Token header      │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  Request Handler                     │
└─────────────────────────────────────┘
```

---

## 🔄 State Transitions

### User State Machine

```
┌────────────┐
│  New User  │
└────────────┘
      │
      │ Job Title Update (not senior)
      ▼
┌────────────────────┐
│  Not in Database   │ ◄─────┐
└────────────────────┘       │
      │                      │
      │ Job Title Update     │ Demotion
      │ (VP/C-suite)         │ (no longer senior)
      ▼                      │
┌────────────────────┐       │
│  user_state        │───────┘
│  level = 'vp'      │
└────────────────────┘
      │
      │ Promotion
      │ (VP → C-suite)
      ▼
┌────────────────────┐
│  user_state        │
│  level = 'csuite'  │
└────────────────────┘
```

### Digest State Machine

```
┌──────────────────┐
│  SQL Function    │
│  creates digest  │
└──────────────────┘
        │
        ▼
┌──────────────────┐
│  digests table   │
│  sent = FALSE    │
└──────────────────┘
        │
        │ Worker polls
        ▼
┌──────────────────┐
│  Processing      │
│  (SKIP LOCKED)   │
└──────────────────┘
        │
        ├─── Success ───►┌──────────────┐
        │                │ sent = TRUE  │
        │                └──────────────┘
        │
        └─── Failure ───►┌──────────────┐
                         │ Retry later  │
                         └──────────────┘
```

---

## 🎯 Key Design Patterns

### 1. Idempotency Pattern

**Problem:** Duplicate webhooks should not create multiple records.

**Solution:**
```python
idempotency_key = hash(event_id + user_id + field + value)

INSERT INTO events_raw (...)
ON CONFLICT (idempotency_key) DO NOTHING
```

### 2. Queue Pattern (SKIP LOCKED)

**Problem:** Multiple workers should not process same digest/report.

**Solution:**
```sql
SELECT * FROM digests
WHERE NOT sent
FOR UPDATE SKIP LOCKED
LIMIT 10
```

### 3. Storage Minimization Pattern

**Problem:** Database should only contain senior executives.

**Solution:**
```python
if not is_senior:
    DELETE FROM user_state WHERE user_id = ?
else:
    INSERT/UPDATE user_state
```

### 4. Config-Driven Classification

**Problem:** Classification rules change frequently.

**Solution:**
- Rules in JSON config file
- Reload without code changes
- Version tracked for auditing

### 5. Retry with Backoff

**Problem:** External API calls (AA bots) may fail transiently.

**Solution:**
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def _send_request(...):
    # HTTP call
```

---

## 📈 Scaling Considerations

### Horizontal Scaling

**Stateless Services:**
- FastAPI web service (multiple replicas)
- Worker processes (multiple instances)

**Coordination via Database:**
- `SKIP LOCKED` prevents duplicate work
- Idempotency keys prevent duplicate events

### Vertical Scaling

**Database:**
- Connection pooling
- Read replicas for analytics
- Indexes on frequently queried columns

---

## 🧪 Testing Strategy

### Unit Tests
- `test_classification.py` - Classification rules
- Test event processor logic
- Test digest formatting

### Integration Tests
- End-to-end webhook flow
- Database transactions
- AA integration (mocked)

### Load Tests
- Simulate 1000 webhooks/sec
- Monitor database performance
- Check worker throughput

---

## 📝 Configuration Management

### Development
```
.env (local)
└─► app/config.py (loads)
    └─► Services (use)
```

### Production
```
Cloud Secrets Manager
└─► Container Environment Variables
    └─► app/config.py (loads)
        └─► Services (use)
```

---

## 🔍 Monitoring Points

### Application Metrics
- Request rate: `/webhooks/community`
- Response latency: P50, P95, P99
- Error rate: 4xx, 5xx responses
- Classification results: senior vs non-senior ratio

### Business Metrics
- Senior execs detected per day
- Digest send success rate
- Report generation time
- AA bot call latency

### Database Metrics
- Connection pool utilization
- Query performance
- Table sizes
- Index usage

---

## 🚨 Alert Rules

### Critical
- Error rate > 5% for 5 minutes
- Database connection failures
- No digests sent in 2 weeks

### Warning
- Response latency > 2s for 10 minutes
- Pending digests > 50
- Classification taking > 500ms

### Info
- Weekly digest sent successfully
- Monthly report generated
- Database maintenance completed

---

**For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)**

**For quick start guide, see [QUICKSTART.md](QUICKSTART.md)**

