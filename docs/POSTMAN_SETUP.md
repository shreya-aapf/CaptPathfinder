# Postman Collection for inSided Webhook Subscriptions

This Postman collection helps you subscribe to inSided webhook events.

## Setup Instructions

### 1. Import this file into Postman
   - Open Postman
   - Click **Import**
   - Select this file

### 2. Set Collection Variables
   - Click on the collection name
   - Go to **Variables** tab
   - Set these variables:
     - `insided_api_base_url`: Your inSided API URL (e.g., `https://api2-us-west-2.insided.com`)
     - `insided_api_token`: Your inSided API token
     - `insided_api_secret`: Your inSided API secret
     - `supabase_project_ref`: Your Supabase project reference

### 3. Run the Requests
   - Execute "Subscribe to User Registration" first
   - Execute "Subscribe to Profile Updates" second
   - Execute "List All Subscriptions" to verify

---

## Postman Collection JSON

Save this as `insided-webhooks.postman_collection.json`:

```json
{
  "info": {
    "name": "CaptPathfinder - inSided Webhook Subscriptions",
    "description": "Subscribe to inSided webhook events for CaptPathfinder",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "insided_api_base_url",
      "value": "https://api2-us-west-2.insided.com",
      "type": "string"
    },
    {
      "key": "insided_api_token",
      "value": "YOUR_API_TOKEN_HERE",
      "type": "string"
    },
    {
      "key": "insided_api_secret",
      "value": "YOUR_API_SECRET_HERE",
      "type": "string"
    },
    {
      "key": "supabase_project_ref",
      "value": "YOUR_SUPABASE_PROJECT_REF",
      "type": "string"
    }
  ],
  "item": [
    {
      "name": "1. Subscribe to User Registration",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          },
          {
            "key": "Authorization",
            "value": "Bearer {{insided_api_token}}"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"url\": \"https://{{supabase_project_ref}}.supabase.co/functions/v1/webhook-handler\",\n  \"username\": \"{{insided_api_token}}\",\n  \"secret\": \"{{insided_api_secret}}\"\n}"
        },
        "url": {
          "raw": "{{insided_api_base_url}}/webhooks/integration.UserRegistered/subscriptions",
          "host": ["{{insided_api_base_url}}"],
          "path": ["webhooks", "integration.UserRegistered", "subscriptions"]
        },
        "description": "Subscribe to new user registration events"
      }
    },
    {
      "name": "2. Subscribe to Profile Updates",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          },
          {
            "key": "Authorization",
            "value": "Bearer {{insided_api_token}}"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"url\": \"https://{{supabase_project_ref}}.supabase.co/functions/v1/webhook-handler\",\n  \"username\": \"{{insided_api_token}}\",\n  \"secret\": \"{{insided_api_secret}}\"\n}"
        },
        "url": {
          "raw": "{{insided_api_base_url}}/webhooks/integration.UserProfileUpdated/subscriptions",
          "host": ["{{insided_api_base_url}}"],
          "path": ["webhooks", "integration.UserProfileUpdated", "subscriptions"]
        },
        "description": "Subscribe to user profile update events"
      }
    },
    {
      "name": "3. List All Subscriptions",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{insided_api_token}}"
          }
        ],
        "url": {
          "raw": "{{insided_api_base_url}}/webhooks/subscriptions",
          "host": ["{{insided_api_base_url}}"],
          "path": ["webhooks", "subscriptions"]
        },
        "description": "List all webhook subscriptions to verify setup"
      }
    },
    {
      "name": "4. Unsubscribe from User Registration",
      "request": {
        "method": "DELETE",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{insided_api_token}}"
          }
        ],
        "url": {
          "raw": "{{insided_api_base_url}}/webhooks/integration.UserRegistered/subscriptions/{{subscription_id}}",
          "host": ["{{insided_api_base_url}}"],
          "path": ["webhooks", "integration.UserRegistered", "subscriptions", "{{subscription_id}}"]
        },
        "description": "Unsubscribe from registration events (optional - for cleanup)"
      }
    },
    {
      "name": "5. Unsubscribe from Profile Updates",
      "request": {
        "method": "DELETE",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{insided_api_token}}"
          }
        ],
        "url": {
          "raw": "{{insided_api_base_url}}/webhooks/integration.UserProfileUpdated/subscriptions/{{subscription_id}}",
          "host": ["{{insided_api_base_url}}"],
          "path": ["webhooks", "integration.UserProfileUpdated", "subscriptions", "{{subscription_id}}"]
        },
        "description": "Unsubscribe from profile update events (optional - for cleanup)"
      }
    }
  ]
}
```

---

## Quick Test

After subscribing, test your webhook with a manual POST:

```json
POST https://YOUR_PROJECT_REF.supabase.co/functions/v1/webhook-handler

{
  "event": "integration.UserRegistered",
  "userId": "test-user-123",
  "username": "Test Executive",
  "user": {
    "id": "test-user-123",
    "username": "Test Executive",
    "jobTitle": "Chief Executive Officer"
  }
}
```

Expected response: `{"status":"accepted","event_id":1}`

