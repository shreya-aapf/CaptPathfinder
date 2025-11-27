# inSided (Gainsight Community) Integration

Guide for integrating CaptPathfinder with inSided Community Platform.

---

## Overview

inSided (now part of Gainsight) is a community platform. CaptPathfinder integrates via:
1. **Webhooks** - Real-time profile update notifications
2. **API** - Fetch additional user profile data

**API Documentation**: https://api2-us-west-2.insided.com/docs/

---

## Webhook Setup

### Event Type

Subscribe to: `integration.UserProfileUpdated`

**Documentation**: https://api2-us-west-2.insided.com/docs/#section/Webhooks/Event-payload-examples

### Webhook Configuration in inSided

1. **Admin Panel** → **Settings** → **Webhooks**
2. **Create New Webhook**:
   - **URL**: `https://YOUR_PROJECT.supabase.co/functions/v1/webhook-handler`
   - **Event**: `integration.UserProfileUpdated`
   - **Method**: `POST`
   - **Headers**: 
     ```
     Content-Type: application/json
     ```

### Webhook Payload Format

inSided sends payloads like this:

```json
{
  "event": "integration.UserProfileUpdated",
  "userId": "2000",
  "username": "John Doe",
  "profileFieldId": "123",
  "profileField": "Job Title",
  "value": "VP of Sales",
  "oldValue": "Sales Manager",
  "timestamp": "2025-11-27T10:30:00Z",
  "communityId": "your-community-id"
}
```

**Fields we use:**
- `userId` - User's ID in inSided
- `username` - User's display name
- `profileField` - Which field changed (we filter for "Job Title")
- `value` - New value
- `oldValue` - Previous value

---

## API Integration

### Get API Key

1. **inSided Admin** → **Settings** → **API**
2. Click **Generate API Key**
3. Copy key and set in `.env`:
   ```bash
   COMMUNITY_API_KEY=your-insided-api-key
   ```

### API Base URL

Set in `.env`:
```bash
COMMUNITY_API_URL=https://api2-us-west-2.insided.com
```

**Note**: URL may vary by region:
- US West: `api2-us-west-2.insided.com`
- EU: `api2-eu-central-1.insided.com`
- Check your inSided admin panel for correct URL

### Fetch User Profile

**Endpoint**: `GET /users/{userId}`

**Documentation**: https://api2-us-west-2.insided.com/docs/user/

**Request:**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api2-us-west-2.insided.com/users/2000
```

**Response:**
```json
{
  "id": "2000",
  "username": "johndoe",
  "email": "john@example.com",
  "displayName": "John Doe",
  "customFields": {
    "Job Title": "VP of Sales",
    "Company": "Tech Corp",
    "Country": "USA"
  },
  "registeredAt": "2024-01-15T10:30:00Z"
}
```

**What we extract:**
- `customFields["Job Title"]` - For classification
- `customFields["Company"]` - For digest
- `customFields["Country"]` - For digest
- `registeredAt` - User's community signup date (maps to `joined_at`)

---

## How It Works

### Flow Diagram

```
User updates profile in inSided
         ↓
inSided sends webhook
         ↓
Supabase Edge Function receives webhook
         ↓
Validates & stores in events_raw table
         ↓
Calls Python service /process-event/{id}
         ↓
Python service:
  1. Fetches event from DB
  2. Calls inSided API to get full profile
  3. Classifies job title
  4. Updates user_state + detections
         ↓
Returns success
```

### Code Flow

**1. Webhook received** (Supabase Edge Function)
```typescript
// supabase/functions/webhook-handler/index.ts
serve(async (req) => {
  const payload = await req.json()
  
  // Store in events_raw
  await supabase.from('events_raw').insert({...})
  
  // Trigger processing
  await fetch(`${pythonServiceUrl}/process-event/${eventId}`)
})
```

**2. Event processed** (Python Service)
```python
# app/main.py - /process-event/{event_id}
@app.post("/process-event/{event_id}")
async def process_queued_event(event_id: int):
    # Fetch event from events_raw
    # Call inSided API for full profile
    # Classify title
    # Update database
```

**3. Fetch user data** (inSided API Client)
```python
# app/services/insided_client.py
class InSidedAPIClient:
    async def get_user(self, user_id: str) -> InSidedUser:
        # GET /users/{user_id}
        # Returns user profile with custom fields
```

**4. Classification** (Existing logic)
```python
# app/classification/rules.py
classify_title("VP of Sales")
# Returns: (True, "vp")
```

---

## Field Mapping

inSided → CaptPathfinder:

| inSided Field | CaptPathfinder Field | Source |
|---------------|----------------------|--------|
| `userId` | `user_id` | Webhook |
| `username` or `displayName` | `username` | Webhook/API |
| `customFields["Job Title"]` | `title` | API |
| `customFields["Company"]` | `company` | API |
| `customFields["Country"]` | `country` | API |
| `registeredAt` | `joined_at` | API |

---

## Custom Fields Configuration

### Ensure Fields Exist in inSided

1. **Admin** → **Community Settings** → **Profile Fields**
2. Verify these fields exist:
   - **Job Title** (Text)
   - **Company** (Text)
   - **Country** (Dropdown or Text)

3. Make fields **editable by users**

### Field Names

If your inSided uses different field names, update in:

**`app/services/insided_client.py`:**
```python
field_mapping = {
    "Job Title": user.customFields.get("Job Title"),
    "Company": user.customFields.get("Company Name"),  # Adjust name
    "Country": user.customFields.get("Location"),      # Adjust name
}
```

---

## Testing

### 1. Test Webhook Receipt

```bash
curl -X POST \
  https://YOUR_PROJECT.supabase.co/functions/v1/webhook-handler \
  -H "Content-Type: application/json" \
  -d '{
    "event": "integration.UserProfileUpdated",
    "userId": "2000",
    "username": "Test User",
    "profileField": "Job Title",
    "value": "CEO",
    "oldValue": "Director"
  }'
```

**Expected**: Event stored in `events_raw` table

### 2. Test API Access

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api2-us-west-2.insided.com/users/2000
```

**Expected**: User profile JSON returned

### 3. Test Full Flow

1. Log into inSided as a test user
2. Update profile: Job Title → "Chief Technology Officer"
3. Check logs:
   ```bash
   supabase functions logs webhook-handler
   # Should show webhook received
   
   # Check Python service logs
   # Should show event processed
   ```
4. Check database:
   ```sql
   SELECT * FROM detections ORDER BY detected_at DESC LIMIT 1;
   ```

---

## Troubleshooting

### Webhooks not received

**Check:**
1. Webhook URL is correct in inSided admin
2. Edge Function is deployed: `supabase functions list`
3. Test with curl (see above)

### API calls failing

**Check:**
1. `COMMUNITY_API_KEY` is set correctly
2. API key has not expired
3. Base URL matches your region
4. Test API manually with curl

### Profile fields not found

**Check:**
1. Field names match exactly (case-sensitive)
2. Fields are enabled in inSided admin
3. User has values set for these fields
4. Check `customFields` structure in API response

---

## Rate Limits

inSided API rate limits (typical):
- **Webhooks**: Unlimited (pushed by inSided)
- **API Calls**: ~1000 requests/hour per API key

**Best practices:**
- Cache user data if making multiple calls
- Use webhooks for real-time updates
- Only call API when webhook doesn't have enough data

---

## Security

### Webhook Validation

inSided may include a signature header for webhook validation.

**To implement** (if supported):
```typescript
// In Edge Function
const signature = req.headers.get('X-InSided-Signature')
const isValid = validateSignature(payload, signature, secret)
if (!isValid) throw new Error('Invalid signature')
```

### API Key Security

- Store in environment variables
- Rotate periodically
- Use different keys for dev/prod
- Never commit to git

---

## Next Steps

1. ✅ Get inSided API key
2. ✅ Configure webhook in inSided admin
3. ✅ Deploy Edge Function
4. ✅ Test webhook receipt
5. ✅ Test API access
6. ✅ Update a test user's job title
7. ✅ Verify detection in database

**Ready for production!** 🎉

