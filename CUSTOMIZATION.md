# Customization Guide

This guide shows you how to customize CaptPathfinder for your specific needs.

---

## 📝 Customizing Classification Rules

The classification system is fully config-driven. Edit `app/classification/config.json`:

### Adding New C-Suite Patterns

```json
{
  "csuite_patterns": [
    "\\bchief\\b.*\\bofficer\\b",
    "\\bceo\\b",
    "\\bchief data officer\\b",       // Add this
    "\\bcdo\\b",                       // Add this
    "\\bchief people officer\\b"       // Add this
  ]
}
```

### Adding New Exclusion Patterns

```json
{
  "exclusion_patterns": [
    "student",
    "volunteer",
    "contractor",     // Add this
    "freelance",      // Add this
    "consultant"      // Add this
  ]
}
```

### Testing Your Changes

```bash
# After modifying config.json, test it:
python test_classification.py

# Or test specific title:
python -c "from app.classification import classify_title; print(classify_title('Chief Data Officer'))"
```

---

## 🎨 Customizing Email Templates

Edit `app/services/aa_integration.py` in the `_format_digest_for_email()` method:

### Change Email Styling

```python
def _format_digest_for_email(self, digest: DigestPayload) -> Dict[str, Any]:
    html_body = f"""
    <html>
    <head>
        <style>
            /* Add your custom CSS here */
            body {{ font-family: 'Your Font', Arial, sans-serif; }}
            .header {{ background-color: #your-color; }}
        </style>
    </head>
    <body>
        <!-- Your custom HTML -->
    </body>
    </html>
    """
    
    return {
        "to": ["your-email@company.com"],  # Change recipients
        "subject": "Your Custom Subject",   # Change subject
        "body": html_body,
        "is_html": True
    }
```

### Add Your Company Logo

```python
html_body = f"""
<html>
<body>
    <img src="https://your-company.com/logo.png" alt="Logo" width="200">
    <h2>Weekly Senior Executive Detections</h2>
    <!-- rest of template -->
</body>
</html>
"""
```

---

## 📱 Customizing Teams Messages

Edit `app/services/aa_integration.py` in the `_format_digest_for_teams()` method:

### Use Adaptive Cards

```python
def _format_digest_for_teams(self, digest: DigestPayload) -> Dict[str, Any]:
    # Build adaptive card
    adaptive_card = {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "Weekly Senior Executive Digest",
                "size": "large",
                "weight": "bolder"
            },
            {
                "type": "FactSet",
                "facts": [
                    {"title": "Period", "value": f"{digest.week_start} to {digest.week_end}"},
                    {"title": "Total", "value": str(digest.total_count)}
                ]
            },
            # Add more sections...
        ]
    }
    
    return {
        "channel_url": "your-teams-channel-url",
        "message": adaptive_card,
        "message_type": "adaptive_card"
    }
```

---

## 🗓️ Changing Digest Schedule

Edit `scripts/setup_pg_cron.sql`:

### Change to Different Day/Time

```sql
-- Change from Friday 5 PM to Monday 9 AM
SELECT cron.schedule(
    'weekly-digest',
    '0 9 * * MON',  -- Changed
    $$SELECT build_weekly_digest();$$
);
```

### Change to Bi-Weekly

```sql
-- Run every 2 weeks (first and third Monday)
SELECT cron.schedule(
    'biweekly-digest',
    '0 9 1-7,15-21 * MON',
    $$SELECT build_weekly_digest();$$
);
```

---

## 📊 Customizing Report Content

Edit `app/services/report_builder.py`:

### Add Custom Columns to CSV

```python
def generate_csv(self, data: List[dict], month_label: str) -> str:
    fieldnames = [
        'User ID',
        'Username',
        'Title',
        'Seniority Level',
        'Country',
        'Company',
        'Department',      # Add this
        'LinkedIn URL',    # Add this
        'Joined At',
        'First Detected At'
    ]
    
    # Update row writing logic to include new fields
```

### Change HTML Styling

```python
def generate_html(self, data: List[dict], month_label: str, summary: Dict[str, Any]) -> str:
    html = f"""
    <style>
        /* Your custom styles */
        :root {{
            --primary-color: #your-color;
            --font-family: 'Your Font';
        }}
        
        body {{
            font-family: var(--font-family);
        }}
        
        /* Add more custom styles */
    </style>
    """
```

---

## 🔌 Adding New Channels

### 1. Update Database Schema

```sql
-- In migrations/001_initial_schema.sql, change:
channel TEXT CHECK (channel IN ('email', 'teams', 'slack'))  -- Add 'slack'
```

Run migration:
```bash
psql $DB_URL -c "ALTER TABLE digests DROP CONSTRAINT digests_channel_check;"
psql $DB_URL -c "ALTER TABLE digests ADD CONSTRAINT digests_channel_check CHECK (channel IN ('email', 'teams', 'slack'));"
```

### 2. Update Digest Builder Function

```sql
-- In scripts/create_functions.sql, add to loop:
FOR rec IN (
    SELECT 'email' AS channel
    UNION ALL
    SELECT 'teams' AS channel
    UNION ALL
    SELECT 'slack' AS channel  -- Add this
) LOOP
```

### 3. Implement Channel Handler

In `app/services/aa_integration.py`:

```python
def _format_digest_for_slack(self, digest: DigestPayload) -> Dict[str, Any]:
    """Format digest for Slack."""
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Weekly Senior Executive Digest"
            }
        },
        # Add more Slack blocks
    ]
    
    return {
        "webhook_url": self.settings.slack_webhook_url,
        "blocks": blocks
    }

async def send_slack_digest(self, digest: DigestPayload) -> bool:
    """Send digest to Slack."""
    try:
        payload = self._format_digest_for_slack(digest)
        result = await self._send_request(
            payload["webhook_url"],
            "",  # No API key for webhook
            {"blocks": payload["blocks"]}
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send Slack digest: {e}")
        return False

async def send_digest(self, digest: DigestPayload) -> bool:
    """Send digest to appropriate channel."""
    if digest.channel == "email":
        return await self.send_email_digest(digest)
    elif digest.channel == "teams":
        return await self.send_teams_digest(digest)
    elif digest.channel == "slack":
        return await self.send_slack_digest(digest)
    else:
        logger.error(f"Unknown channel: {digest.channel}")
        return False
```

### 4. Update Config

Add to `.env`:
```ini
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

Add to `app/config.py`:
```python
class Settings(BaseSettings):
    # ... existing fields ...
    slack_webhook_url: Optional[str] = None
```

---

## 🔍 Adding Custom Metadata Fields

### 1. Update Database Schema

```sql
-- In migrations, add columns to user_state:
ALTER TABLE user_state
ADD COLUMN department TEXT,
ADD COLUMN linkedin_url TEXT,
ADD COLUMN phone_number TEXT;
```

### 2. Update Pydantic Models

In `app/models.py`:

```python
class WebhookEvent(BaseModel):
    userId: str
    username: str
    profileField: str
    value: str
    oldValue: Optional[str] = None
    
    # Add new fields
    department: Optional[str] = None
    linkedin_url: Optional[str] = None
    phone_number: Optional[str] = None
```

### 3. Update Event Processor

In `app/services/event_processor.py`:

```python
def process_classification(
    self,
    user_id: str,
    username: str,
    title: str,
    country: Optional[str],
    company: Optional[str],
    joined_at: Optional[datetime],
    department: Optional[str] = None,  # Add
    linkedin_url: Optional[str] = None,  # Add
):
    # ... existing logic ...
    
    cur.execute("""
        INSERT INTO user_state (
            user_id, username, title, seniority_level,
            country, company, joined_at,
            department, linkedin_url,  -- Add
            first_detected_at, last_seen_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
    """, (
        user_id, username, title, seniority_level,
        country, company, joined_at,
        department, linkedin_url  -- Add
    ))
```

---

## 🎯 Changing Batch Sizes

### Digest Batch Size

In `scripts/create_functions.sql`:

```sql
-- Change from 10 to 20 users per digest
IF array_length(chunk_array, 1) = 20 THEN  -- Changed
    INSERT INTO digests (...)
```

### Processing Batch Size

In `app/services/digest_builder.py`:

```python
def get_pending_digests(self) -> List[dict]:
    with self.db.get_cursor() as cur:
        cur.execute("""
            SELECT ...
            FROM digests
            WHERE NOT sent
            ORDER BY created_at ASC
            LIMIT 50  -- Changed from 10
            FOR UPDATE SKIP LOCKED
        """)
```

---

## 🔧 Advanced Customizations

### Adding LLM-Based Classification

In `app/classification/rules.py`, implement `LLMClassifier`:

```python
import openai  # or anthropic, etc.

class LLMClassifier:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
    
    def classify(self, title: str) -> Tuple[bool, str]:
        """Classify title using GPT-4."""
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a job title classifier. Classify if the title is C-suite (CEO, CFO, etc.), VP level, or neither. Respond with: csuite, vp, or none."},
                {"role": "user", "content": f"Classify this job title: {title}"}
            ]
        )
        
        result = response.choices[0].message.content.strip().lower()
        
        if result == "csuite":
            return (True, "csuite")
        elif result == "vp":
            return (True, "vp")
        else:
            return (False, "")
```

Enable in `app/classification/rules.py`:

```python
# Use hybrid classifier
from .rules import HybridClassifier

classifier = HybridClassifier(use_llm=True)
is_senior, level = classifier.classify(title)
```

---

## 📈 Adding Analytics Dashboard

Create `app/routes/analytics.py`:

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/analytics/trends")
async def get_trends():
    """Get detection trends over time."""
    # Query detections grouped by week/month
    # Return data for charting
    pass

@router.get("/analytics/countries")
async def get_by_country():
    """Get senior execs by country."""
    # Query user_state grouped by country
    pass
```

Add to `app/main.py`:

```python
from .routes import analytics

app.include_router(analytics.router, prefix="/api", tags=["analytics"])
```

---

## 🚀 Next Steps

After customization:

1. **Test locally**: `python -m app.main`
2. **Run classification tests**: `python test_classification.py`
3. **Test webhook**: Use curl or Postman
4. **Deploy**: See [DEPLOYMENT.md](DEPLOYMENT.md)
5. **Monitor**: Check logs and metrics

---

**Need Help?**

- Check [README.md](README.md) for general documentation
- See [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Review [QUICKSTART.md](QUICKSTART.md) for getting started

