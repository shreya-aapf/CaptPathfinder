# Environment Variables Configuration

Copy this file to `.env` and replace the placeholders with your actual values.

## Supabase Database Connection - THE EASY WAY! 🎯

**Don't construct the URL manually!** Supabase gives it to you:

### Option 1: Copy from Supabase Dashboard (Recommended ✅)

1. Go to https://app.supabase.com → Your Project
2. Click **Settings** (gear icon in sidebar)
3. Click **Database** 
4. Scroll to **Connection String** section
5. Select **URI** tab
6. Click **Copy** button
7. Paste it as your `SUPABASE_DB_URL`

**That's it!** The connection string is already formatted correctly.

### Option 2: Use Connection Pooler (Even Simpler for Production)

Supabase also provides a connection pooler URL (recommended for serverless/production):

1. Same steps as above, but select **Connection pooling** → **Transaction** mode
2. Copy that URL instead
3. Ends with `:6543/postgres` instead of `:5432/postgres`

**Example of what you'll copy:**
```
postgresql://postgres.xyzabcdefgh:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

## Required Environment Variables

```bash
# Database (Required) - Just copy from Supabase dashboard!
SUPABASE_DB_URL=<paste-connection-string-from-supabase>

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
# For these, you can use Supabase Project Settings → API
SUPABASE_STORAGE_URL=<project-url>/storage/v1
SUPABASE_STORAGE_BUCKET=reports
SUPABASE_ANON_KEY=<copy-from-supabase-api-settings>
```

## Quick Setup Steps (2 Minutes!)

### Step 1: Create `.env` file
```bash
# Create empty .env file
New-Item -Path .env -ItemType File  # Windows PowerShell
# or
touch .env  # Mac/Linux
```

### Step 2: Get Supabase Connection String (30 seconds)
1. Open https://app.supabase.com
2. Select your project
3. **Settings** → **Database** → **Connection String**
4. Click **URI** tab
5. Click **Copy** 📋

### Step 3: Paste into .env
Open `.env` and add:
```bash
SUPABASE_DB_URL=<paste-here>
AA_EMAIL_BOT_URL=https://your-aa-url.com/email
AA_EMAIL_BOT_API_KEY=your-key
AA_TEAMS_BOT_URL=https://your-aa-url.com/teams
AA_TEAMS_BOT_API_KEY=your-key
```

### Visual Guide:
```
Supabase Dashboard
    ↓
Settings (⚙️ in sidebar)
    ↓
Database
    ↓
Connection String section
    ↓
URI tab
    ↓
Copy button 📋
    ↓
Paste into .env ✅
```

## Minimal Working Configuration

Your `.env` file only needs these 5 lines:

```bash
SUPABASE_DB_URL=<copied-from-supabase-dashboard>
AA_EMAIL_BOT_URL=https://your-aa-bot-url.com/email
AA_EMAIL_BOT_API_KEY=your-key
AA_TEAMS_BOT_URL=https://your-aa-bot-url.com/teams
AA_TEAMS_BOT_API_KEY=your-key
```

Everything else has sensible defaults!

## Troubleshooting

**"Connection refused" error?**
- Make sure you copied the **entire** connection string from Supabase
- Check if you're using the right password (visible in the connection string)

**"SSL required" error?**
- The Supabase connection string already includes SSL settings
- If you see this, you might have modified the string - re-copy from dashboard

**Want to use connection pooler?**
- For production/serverless: Use the **Connection pooling** tab instead of URI
- Ends with `:6543` instead of `:5432`
- Better for applications with many concurrent connections

