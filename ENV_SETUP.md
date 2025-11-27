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
# Control Room URL - your AA instance
AA_CONTROL_ROOM_URL=https://your-instance.automationanywhere.digital

# Authentication - use API key or OAuth token
AA_API_KEY=your-api-key-here
# OR use username/password (API key recommended)
AA_USERNAME=your-username
AA_PASSWORD=your-password

# Bot IDs - found in Control Room (Automation > Right-click bot > Properties)
AA_EMAIL_BOT_ID=12345678-1234-1234-1234-123456789abc
AA_TEAMS_BOT_ID=87654321-4321-4321-4321-cba987654321

# Bot Runner User ID (the user account that will run the bot)
AA_RUN_AS_USER_ID=your-user-id-here

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

# Automation Anywhere
AA_CONTROL_ROOM_URL=https://your-instance.automationanywhere.digital
AA_API_KEY=your-api-key
AA_EMAIL_BOT_ID=your-email-bot-file-id
AA_TEAMS_BOT_ID=your-teams-bot-file-id
AA_RUN_AS_USER_ID=your-user-id
```

### Step 4: Get Automation Anywhere Bot IDs

**Finding Bot IDs (File IDs) in Control Room:**
1. Log into your AA Control Room
2. Go to **Automation** tab
3. Find your email/Teams bot
4. Right-click the bot → **Properties**
5. Copy the **File ID** (looks like: `12345678-1234-1234-1234-123456789abc`)

**Finding your User ID:**
1. Control Room → **Administration** → **Users**
2. Click on your username
3. Copy the **User ID** from the URL or user details

**Getting API Key:**
1. Control Room → **Administration** → **Settings** → **Credentials**
2. Or use username/password authentication (API key recommended)

### Visual Guide:
```
AA Control Room
    ↓
Automation tab
    ↓
Right-click bot → Properties
    ↓
Copy File ID (Bot ID) 📋
    ↓
Paste into .env as AA_EMAIL_BOT_ID ✅
```

## Minimal Working Configuration

Your `.env` file only needs these lines:

```bash
SUPABASE_DB_URL=<copied-from-supabase-dashboard>

# Automation Anywhere
AA_CONTROL_ROOM_URL=https://your-instance.automationanywhere.digital
AA_API_KEY=your-api-key-here
AA_EMAIL_BOT_ID=your-email-bot-id
AA_TEAMS_BOT_ID=your-teams-bot-id
AA_RUN_AS_USER_ID=your-user-id
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

