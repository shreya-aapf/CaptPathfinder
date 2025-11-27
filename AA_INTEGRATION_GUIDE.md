# Automation Anywhere Bot Integration Guide

This guide explains how to integrate CaptPathfinder with your Automation Anywhere bots using the Bot Deploy API v4.

## 📋 Overview

CaptPathfinder deploys AA bots with input variables to send:
- **Email digests** - Weekly summary of senior executives detected
- **Teams messages** - Same digest posted to Microsoft Teams

## 🤖 How It Works

```
CaptPathfinder
    ↓
Calls AA Control Room API v4
    ↓
Deploys bot with input variables
    ↓
Bot runs with provided inputs
    ↓
Sends email/Teams message
```

## ⚙️ Configuration

### 1. Environment Variables Needed

In your `.env` file:

```bash
# AA Control Room URL
AA_CONTROL_ROOM_URL=https://your-instance.automationanywhere.digital

# Authentication (API Key recommended)
AA_API_KEY=your-api-key-here

# Bot File IDs (from Control Room)
AA_EMAIL_BOT_ID=12345678-1234-1234-1234-123456789abc
AA_TEAMS_BOT_ID=87654321-4321-4321-4321-cba987654321

# User ID to run bots as
AA_RUN_AS_USER_ID=your-user-id-here
```

### 2. Finding Your Bot IDs

**In Control Room:**
1. Navigate to **Automation** tab
2. Find your bot in the list
3. Right-click → **Properties**
4. Copy the **File ID** (this is your Bot ID)

**Example File ID:** `a1b2c3d4-1234-5678-90ab-cdef12345678`

### 3. Finding Your User ID

**In Control Room:**
1. Go to **Administration** → **Users**
2. Click on your username
3. The User ID appears in the URL or user details panel
4. Copy it to `AA_RUN_AS_USER_ID`

### 4. Getting API Key

**Option A: Generate API Key (Recommended)**
1. Control Room → **My Settings** → **My Credentials**
2. Click **Generate API Key**
3. Copy the key immediately (won't be shown again)

**Option B: Use Username/Password**
Add to `.env`:
```bash
AA_USERNAME=your-username
AA_PASSWORD=your-password
```

## 🏗️ Creating Your AA Bots

### Email Bot Requirements

Your email bot should accept these input variables:

| Variable Name | Type | Description |
|--------------|------|-------------|
| `emailTo` | String | Semicolon-separated email addresses |
| `emailSubject` | String | Email subject line |
| `emailBody` | String | HTML email body |
| `isHTML` | String | "true" or "false" |
| `weekStart` | String | Start date of the week (YYYY-MM-DD) |
| `weekEnd` | String | End date of the week (YYYY-MM-DD) |
| `totalCount` | String | Number of detections |

**Example Bot Logic:**
```
1. Read input variables
2. Send email using Office 365/Outlook package
   - To: $emailTo$
   - Subject: $emailSubject$
   - Body: $emailBody$
   - Format: HTML
3. Log success/failure
```

### Teams Bot Requirements

Your Teams bot should accept these input variables:

| Variable Name | Type | Description |
|--------------|------|-------------|
| `teamsChannelWebhook` | String | Teams incoming webhook URL |
| `messageText` | String | Message content (markdown format) |
| `messageType` | String | "markdown" or "plain" |
| `weekStart` | String | Start date of the week |
| `weekEnd` | String | End date of the week |
| `totalCount` | String | Number of detections |

**Example Bot Logic:**
```
1. Read input variables
2. Format message as Teams card (optional)
3. Send HTTP POST to webhook URL
   - URL: $teamsChannelWebhook$
   - Body: {"text": "$messageText$"}
4. Log success/failure
```

## 📝 Customizing Input Variables

If your bots use different variable names, edit `app/services/aa_integration.py`:

### For Email Bot

Find `_prepare_email_bot_inputs()` method:

```python
def _prepare_email_bot_inputs(self, digest: DigestPayload) -> Dict[str, Any]:
    bot_inputs = {
        "emailTo": "your@email.com",           # Change variable name here
        "emailSubject": f"Subject...",         # Change variable name here
        "emailBody": html_body,                # Change variable name here
        "isHTML": "true",
        # Add more variables as needed
        "customField": "customValue"
    }
    return bot_inputs
```

### For Teams Bot

Find `_prepare_teams_bot_inputs()` method:

```python
def _prepare_teams_bot_inputs(self, digest: DigestPayload) -> Dict[str, Any]:
    bot_inputs = {
        "teamsChannelWebhook": "https://...",  # Change variable name here
        "messageText": message_text,           # Change variable name here
        # Add more variables as needed
    }
    return bot_inputs
```

## 🧪 Testing Your Integration

### Step 1: Test Bot Manually in Control Room

1. Open your bot in Control Room
2. Click **Run** → **Run with inputs**
3. Provide sample input values
4. Verify bot executes successfully

### Step 2: Test via API (curl)

```bash
# Test deployment
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

### Step 3: Test via CaptPathfinder

```bash
# Manually trigger digest sending
curl -X POST http://localhost:8000/admin/send-digests
```

Check application logs for deployment status.

## 📊 API Response Format

Successful bot deployment returns:

```json
{
  "deploymentId": "550e8400-e29b-41d4-a716-446655440000",
  "statusUrl": "/v4/activity/execution/550e8400-e29b-41d4-a716-446655440000"
}
```

You can use the `statusUrl` to check execution status if needed.

## 🔍 Troubleshooting

### Error: "Invalid API Key"

- Verify `AA_API_KEY` is correct
- Check if API key has expired
- Ensure API key has permissions to deploy bots

### Error: "Bot not found"

- Verify `AA_EMAIL_BOT_ID` or `AA_TEAMS_BOT_ID` is correct
- Check bot exists in Control Room
- Ensure bot is in the correct folder

### Error: "User not authorized"

- Verify `AA_RUN_AS_USER_ID` is correct
- Ensure user has "Run Bot" permission
- Check if bot is shared with the user

### Bot Deploys but Doesn't Send Email/Message

- Check bot logs in Control Room Activity tab
- Verify input variable names match bot expectations
- Ensure bot has required packages installed
- Check email/Teams credentials in bot

## 📖 API Reference

**Documentation:** https://docs.automationanywhere.com/bundle/enterprise-v2019/page/deploy-api-supported-v4.html

**Endpoint:** `POST /v4/automations/deploy`

**Headers:**
```
X-Authorization: YOUR_API_KEY
Content-Type: application/json
```

**Request Body:**
```json
{
  "fileId": "bot-file-id",
  "runAsUserIds": ["user-id"],
  "botInput": [
    {"name": "variable1", "value": "value1"},
    {"name": "variable2", "value": "value2"}
  ],
  "poolIds": [],
  "overrideDefaultDevice": false
}
```

## 🎯 Best Practices

1. **Use API Key Authentication** - More secure than username/password
2. **Test Bots Manually First** - Ensure bots work before API integration
3. **Handle Errors Gracefully** - Bots may fail; retry logic is included
4. **Monitor Bot Runs** - Check Activity tab regularly
5. **Keep Variables Simple** - Use string values for all inputs
6. **Log Everything** - Bot should log all actions for debugging

## 🚀 Next Steps

1. ✅ Create email and Teams bots in Control Room
2. ✅ Get Bot IDs and User ID
3. ✅ Configure `.env` file
4. ✅ Test manually via Control Room
5. ✅ Test via CaptPathfinder
6. ✅ Monitor first automated run

---

**Need Help?** Check the [Troubleshooting](#-troubleshooting) section or review AA Control Room logs.

