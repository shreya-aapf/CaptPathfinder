# Visual System Diagrams

ASCII diagrams to help visualize CaptPathfinder's architecture.

---

## System Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                         CaptPathfinder System                          │
└────────────────────────────────────────────────────────────────────────┘

External Systems                    Core Services                   Storage
─────────────────                  ─────────────                   ─────────

┌──────────────┐                   ┌──────────────┐               ┌──────────────┐
│  Community   │  ──webhook──►     │   FastAPI    │◄────conn──────│  Supabase/   │
│  Platform    │                   │   Web App    │               │  PostgreSQL  │
└──────────────┘                   └──────────────┘               └──────────────┘
                                          │                               │
                                          │                               │
                                          ▼                               ▼
┌──────────────┐                   ┌──────────────┐               ┌──────────────┐
│  Automation  │◄──HTTP/REST───    │   Worker     │◄────query─────│   pg_cron    │
│  Anywhere    │                   │   Process    │               │  Scheduler   │
│  Bots        │                   └──────────────┘               └──────────────┘
└──────────────┘
│
├─ Email Bot
└─ Teams Bot
```

---

## Data Flow: Webhook to Database

```
Webhook Event Arrives
         │
         ▼
   ┌─────────────────┐
   │ Validate Payload│
   │  (Pydantic)     │
   └─────────────────┘
         │
         ▼
   ┌─────────────────┐
   │ Generate        │
   │ Idempotency Key │
   └─────────────────┘
         │
         ├──► Check if "Job Title" field?
         │         │
         │         ├── NO ──► Skip (or store minimal)
         │         │
         │         └── YES
         │              │
         ▼              ▼
   ┌─────────────────────────┐
   │ INSERT INTO events_raw  │
   │ ON CONFLICT DO NOTHING  │
   └─────────────────────────┘
         │
         ├──► Duplicate? ──► Return "duplicate"
         │
         └──► New event
              │
              ▼
   ┌─────────────────────────┐
   │ Fetch User Metadata     │
   │ (country, company, etc) │
   └─────────────────────────┘
         │
         ▼
   ┌─────────────────────────┐
   │ Classify Title          │
   │ (Regex Rules)           │
   └─────────────────────────┘
         │
         ├──────────────┬──────────────┐
         │              │              │
    NOT SENIOR      VP LEVEL      C-SUITE
         │              │              │
         ▼              ▼              ▼
   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │ DELETE   │   │ INSERT/  │   │ INSERT/  │
   │ from     │   │ UPDATE   │   │ UPDATE   │
   │ user_    │   │ user_    │   │ user_    │
   │ state    │   │ state    │   │ state    │
   └──────────┘   └──────────┘   └──────────┘
                        │              │
                        └──────┬───────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │ INSERT INTO        │
                    │ detections         │
                    │ (if first time or  │
                    │  promotion)        │
                    └────────────────────┘
```

---

## Weekly Digest Flow

```
Friday 5 PM EST
      │
      ▼
┌──────────────────────────────┐
│ pg_cron triggers             │
│ build_weekly_digest()        │
└──────────────────────────────┘
      │
      ▼
┌──────────────────────────────┐
│ SELECT from detections       │
│ WHERE detected_at > -7 days  │
│   AND NOT included_in_digest │
└──────────────────────────────┘
      │
      ▼
┌──────────────────────────────┐
│ Batch into chunks of 10      │
│ For each channel:            │
│   - email                    │
│   - teams                    │
└──────────────────────────────┘
      │
      ▼
┌──────────────────────────────┐
│ INSERT INTO digests          │
│ (sent = FALSE)               │
└──────────────────────────────┘
      │
      ▼
┌──────────────────────────────┐
│ UPDATE detections            │
│ SET included_in_digest=TRUE  │
└──────────────────────────────┘
      │
      │ (Later, worker picks up)
      ▼
┌──────────────────────────────┐
│ Worker: SELECT pending       │
│ FOR UPDATE SKIP LOCKED       │
└──────────────────────────────┘
      │
      ▼
┌──────────────────────────────┐
│ Format for channel           │
│ - Build email HTML           │
│ - Build Teams message        │
└──────────────────────────────┘
      │
      ▼
┌──────────────────────────────┐
│ HTTP POST to AA Bot          │
│ (with retry logic)           │
└──────────────────────────────┘
      │
      ├── Success ──►┌────────────────┐
      │              │ UPDATE digests │
      │              │ SET sent=TRUE  │
      │              └────────────────┘
      │
      └── Failure ──► Retry (exponential backoff)
```

---

## Classification Logic

```
Job Title String
      │
      ▼
┌──────────────────────────────┐
│ Normalize:                   │
│ - Lowercase                  │
│ - Trim spaces                │
│ - Remove punctuation         │
└──────────────────────────────┘
      │
      ▼
┌──────────────────────────────┐
│ Check Exclusion Patterns     │
│ - student                    │
│ - retired                    │
│ - volunteer                  │
│ - intern                     │
│ - etc.                       │
└──────────────────────────────┘
      │
      ├── MATCH ──► Return (False, "")
      │
      └── NO MATCH
          │
          ▼
┌──────────────────────────────┐
│ Check C-Suite Patterns       │
│ - \\bceo\\b                  │
│ - \\bcfo\\b                  │
│ - \\bchief.*officer\\b       │
│ - \\bpresident\\b            │
│ - etc.                       │
└──────────────────────────────┘
      │
      ├── MATCH ──► Return (True, "csuite")
      │
      └── NO MATCH
          │
          ▼
┌──────────────────────────────┐
│ Check VP Patterns            │
│ - \\bvp\\b                   │
│ - \\bvice president\\b       │
│ - \\bsvp\\b                  │
│ - \\bevp\\b                  │
│ - etc.                       │
└──────────────────────────────┘
      │
      ├── MATCH ──► Return (True, "vp")
      │
      └── NO MATCH ──► Return (False, "")
```

---

## Database Tables Relationship

```
┌─────────────────┐
│ field_registry  │
│─────────────────│
│ id              │◄── Configuration table
│ field_name      │    (stores "Job Title")
│ is_active       │
└─────────────────┘


┌─────────────────┐
│ events_raw      │◄── Audit trail (14 day retention)
│─────────────────│
│ id              │
│ user_id         │
│ profile_field   │
│ value           │
│ idempotency_key │◄── UNIQUE constraint
│ processed       │
└─────────────────┘


┌─────────────────┐         ┌─────────────────┐
│ user_state      │         │ detections      │
│─────────────────│         │─────────────────│
│ user_id (PK)    │◄────┐   │ id              │
│ username        │     │   │ user_id         │◄── History of all
│ title           │     └───│ (FK)            │    detections
│ seniority_level │         │ username        │
│ country         │         │ title           │
│ company         │         │ seniority_level │
│ joined_at       │         │ detected_at     │
│ first_detected  │         │ included_in     │
│ last_seen_at    │         │  _digest        │
└─────────────────┘         └─────────────────┘
      │                             │
      │ Only seniors                │
      │ stored here                 │
      │                             │
      └─────────────────────────────┘
                  │
                  │ Referenced by
                  ▼
         ┌─────────────────┐
         │ digests         │
         │─────────────────│
         │ id              │
         │ week_start      │
         │ week_end        │
         │ channel         │◄── 'email' or 'teams'
         │ payload         │◄── JSON with user list
         │ sent            │◄── Boolean flag
         └─────────────────┘


         ┌─────────────────┐
         │ reports         │
         │─────────────────│
         │ id              │
         │ month_label     │◄── "2025-11"
         │ file_uri        │◄── CSV/HTML paths
         │ summary         │◄── JSON stats
         │ generated_at    │
         └─────────────────┘
```

---

## Concurrent Processing (SKIP LOCKED)

```
┌─────────────────┐
│ digests table   │
│ (sent = FALSE)  │
└─────────────────┘
      │
      │
      ├─────────────────────┬─────────────────────┐
      │                     │                     │
      ▼                     ▼                     ▼
┌──────────┐          ┌──────────┐          ┌──────────┐
│ Worker 1 │          │ Worker 2 │          │ Worker 3 │
└──────────┘          └──────────┘          └──────────┘
      │                     │                     │
      │ SELECT              │ SELECT              │ SELECT
      │ FOR UPDATE          │ FOR UPDATE          │ FOR UPDATE
      │ SKIP LOCKED         │ SKIP LOCKED         │ SKIP LOCKED
      │                     │                     │
      ▼                     ▼                     ▼
┌──────────┐          ┌──────────┐          ┌──────────┐
│ Digest A │          │ Digest B │          │ Digest C │
│ (LOCKED) │          │ (LOCKED) │          │ (LOCKED) │
└──────────┘          └──────────┘          └──────────┘
      │                     │                     │
      │ Process             │ Process             │ Process
      │ independently       │ independently       │ independently
      │                     │                     │
      ▼                     ▼                     ▼
┌──────────┐          ┌──────────┐          ┌──────────┐
│ sent=TRUE│          │ sent=TRUE│          │ sent=TRUE│
└──────────┘          └──────────┘          └──────────┘

No duplicate processing! Each worker gets different records.
```

---

## Deployment Architecture (Example: AWS)

```
Internet
   │
   ▼
┌──────────────────────────────────┐
│ Application Load Balancer        │
│ - SSL Termination                │
│ - Health Checks                  │
└──────────────────────────────────┘
   │
   ├─────────────────────┬─────────────────────┐
   │                     │                     │
   ▼                     ▼                     ▼
┌─────────┐       ┌─────────┐       ┌─────────┐
│ ECS     │       │ ECS     │       │ ECS     │
│ Task 1  │       │ Task 2  │       │ Task 3  │
│ FastAPI │       │ FastAPI │       │ FastAPI │
└─────────┘       └─────────┘       └─────────┘
   │                     │                     │
   └─────────────────────┴─────────────────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ RDS PostgreSQL      │
        │ - pg_cron enabled   │
        │ - Multi-AZ          │
        └─────────────────────┘
                  │
                  │ Triggers
                  ▼
        ┌─────────────────────┐
        │ Lambda Function     │
        │ (Worker)            │
        │ - Process digests   │
        │ - Generate reports  │
        └─────────────────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ Automation Anywhere │
        │ - Email Bot         │
        │ - Teams Bot         │
        └─────────────────────┘
```

---

## State Transitions

```
User Lifecycle
──────────────

    [New User]
         │
         │ Update: "Software Engineer"
         ▼
    [Not in DB] ───────────┐
         │                 │
         │ Update:         │ Update: "Manager"
         │ "VP Sales"      │ (still not senior)
         ▼                 │
   [user_state]◄───────────┘
   level='vp'
         │
         │ Update: "CEO"
         ▼
   [user_state]
   level='csuite'
         │
         │ Update: "Retired CEO"
         ▼
    [Not in DB]
   (removed due to exclusion)


Digest Lifecycle
────────────────

  [SQL Function]
  creates digest
         │
         ▼
    [sent=FALSE] ──┐
         │         │ Worker crashes
         │         │ or fails
         ▼         │
   [Processing]◄───┘
   (LOCKED)
         │
         ├── Success ──►[sent=TRUE]
         │
         └── Failure ──►[sent=FALSE]
                        (retry later)
```

---

## Technology Stack

```
┌─────────────────────────────────────────────────┐
│              Application Layer                  │
├─────────────────────────────────────────────────┤
│ Python 3.11+                                    │
│ FastAPI (Web Framework)                         │
│ Pydantic (Validation)                           │
│ httpx (Async HTTP)                              │
│ tenacity (Retry Logic)                          │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│              Data Layer                         │
├─────────────────────────────────────────────────┤
│ PostgreSQL 13+ (Supabase)                       │
│ psycopg3 (Database Driver)                      │
│ pg_cron (Scheduling)                            │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│              Integration Layer                  │
├─────────────────────────────────────────────────┤
│ Automation Anywhere Bots                        │
│ - Email Bot (HTTP/REST)                         │
│ - Teams Bot (HTTP/REST)                         │
└─────────────────────────────────────────────────┘
```

---

These diagrams complement the detailed documentation and help visualize
how all the components work together!

