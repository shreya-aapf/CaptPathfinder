# Quick Start Guide

Get CaptPathfinder running in 5 minutes!

## Prerequisites

- Python 3.11+
- Supabase account
- Git

## Steps

### 1. Clone and Setup

```bash
git clone <repo-url>
cd CaptPathfinder
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database URL and API keys
```

### 3. Setup Database

```bash
# Connect to your Supabase database
psql YOUR_DB_URL -f migrations/001_initial_schema.sql
psql YOUR_DB_URL -f scripts/create_functions.sql
psql YOUR_DB_URL -f scripts/setup_pg_cron.sql
```

### 4. Run the Application

```bash
python -m app.main
```

The API will be available at `http://localhost:8000`

### 5. Test the Webhook

```bash
curl -X POST http://localhost:8000/webhooks/community \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "123",
    "username": "Jane Smith",
    "profileField": "Job Title",
    "value": "Chief Technology Officer",
    "oldValue": "VP Engineering"
  }'
```

### 6. Check Results

```bash
# View recent detections
curl http://localhost:8000/admin/recent-detections

# View stats
curl http://localhost:8000/admin/stats
```

## What's Next?

- Configure Automation Anywhere bot URLs in `.env`
- Customize classification rules in `app/classification/config.json`
- Setup webhook in your community platform
- Deploy to production (see README.md)

## Troubleshooting

**Database connection error?**
- Check your `SUPABASE_DB_URL` in `.env`
- Ensure your IP is allowed in Supabase settings

**Import errors?**
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt` again

**Webhook not detecting senior titles?**
- Check `app/classification/config.json` patterns
- View logs for classification decisions

## Need Help?

See the full [README.md](README.md) for detailed documentation.

