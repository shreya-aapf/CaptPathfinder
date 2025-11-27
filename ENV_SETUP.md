# Environment Variables Configuration

Copy this file to `.env` and replace the placeholders with your actual values.

## Supabase Database Connection

**Format:**
```
postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_ID.supabase.co:5432/postgres
```

**How to find your Supabase Project ID:**
1. Go to your Supabase dashboard: https://app.supabase.com
2. Select your project
3. Go to Settings → General
4. Copy your "Reference ID" - this is your PROJECT_ID

**Example:**
```
SUPABASE_DB_URL=postgresql://postgres:mySecurePassword123@db.xyzabcdefgh.supabase.co:5432/postgres
```

## Required Environment Variables

```bash
# Database (Required)
SUPABASE_DB_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_ID.supabase.co:5432/postgres

# Automation Anywhere Integration (Required)
AA_EMAIL_BOT_URL=https://your-aa-instance.com/api/v1/email/send
AA_EMAIL_BOT_API_KEY=your-api-key-here
AA_TEAMS_BOT_URL=https://your-aa-instance.com/api/v1/teams/send
AA_TEAMS_BOT_API_KEY=your-api-key-here

# Application Settings (Optional - defaults provided)
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Community Platform API (Optional - only if fetching additional user metadata)
COMMUNITY_API_URL=https://your-community-platform.com/api
COMMUNITY_API_KEY=your-api-key-here

# Supabase Storage (Optional - only if storing reports in cloud)
SUPABASE_STORAGE_URL=https://YOUR_PROJECT_ID.supabase.co/storage/v1
SUPABASE_STORAGE_BUCKET=reports
SUPABASE_ANON_KEY=your-anon-key-here
```

## Quick Setup Steps

1. **Copy this template to `.env`:**
   ```bash
   cp ENV_SETUP.md .env
   # Then edit .env and remove everything except the variable definitions
   ```

2. **Get your Supabase credentials:**
   - Dashboard: https://app.supabase.com → Your Project → Settings
   - Project ID: Settings → General → Reference ID
   - Database Password: Settings → Database → Password (if you need to reset it)
   - Connection String: Settings → Database → Connection String → URI
     - **Note:** Supabase provides the full connection string - just copy it!

3. **Alternative: Use Supabase's Connection String:**
   - Go to: Settings → Database → Connection String
   - Select "URI" tab
   - Copy the entire connection string
   - Paste it as your `SUPABASE_DB_URL`

## Minimal Working Configuration

The minimum you need to get started:

```bash
# .env file
SUPABASE_DB_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_ID.supabase.co:5432/postgres
AA_EMAIL_BOT_URL=https://your-aa-bot-url.com/email
AA_EMAIL_BOT_API_KEY=your-key
AA_TEAMS_BOT_URL=https://your-aa-bot-url.com/teams
AA_TEAMS_BOT_API_KEY=your-key
```

Everything else has sensible defaults!

