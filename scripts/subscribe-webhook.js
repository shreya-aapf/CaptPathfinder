#!/usr/bin/env node

/**
 * Subscribe to inSided webhook events
 * 
 * This script subscribes your Supabase Edge Function to inSided webhook events
 * so that profile updates trigger the CaptPathfinder detection system.
 * 
 * Usage:
 *   node subscribe-webhook.js
 * 
 * Environment variables needed:
 *   - INSIDED_API_BASE_URL: Your inSided API base URL (e.g., https://api2-us-west-2.insided.com)
 *   - INSIDED_API_TOKEN: Your inSided API token
 *   - INSIDED_API_SECRET: Your inSided API secret
 *   - SUPABASE_PROJECT_REF: Your Supabase project reference
 */

const https = require('https');
const http = require('http');
const { URL } = require('url');

// Configuration from environment variables
const config = {
  insidedApiBaseUrl: process.env.INSIDED_API_BASE_URL || 'https://api2-us-west-2.insided.com',
  insidedApiToken: process.env.INSIDED_API_TOKEN,
  insidedApiSecret: process.env.INSIDED_API_SECRET,
  supabaseProjectRef: process.env.SUPABASE_PROJECT_REF,
};

// Validate configuration
function validateConfig() {
  const missing = [];
  
  if (!config.insidedApiToken) missing.push('INSIDED_API_TOKEN');
  if (!config.insidedApiSecret) missing.push('INSIDED_API_SECRET');
  if (!config.supabaseProjectRef) missing.push('SUPABASE_PROJECT_REF');
  
  if (missing.length > 0) {
    console.error('❌ Missing required environment variables:');
    missing.forEach(v => console.error(`   - ${v}`));
    console.error('\nUsage:');
    console.error('  INSIDED_API_TOKEN=xxx INSIDED_API_SECRET=yyy SUPABASE_PROJECT_REF=zzz node subscribe-webhook.js');
    process.exit(1);
  }
}

// Subscribe to webhook
function subscribeToWebhook(eventName) {
  const callbackUrl = `https://${config.supabaseProjectRef}.supabase.co/functions/v1/webhook-handler`;
  const apiUrl = new URL(`/webhooks/${eventName}/subscriptions`, config.insidedApiBaseUrl);
  
  const payload = JSON.stringify({
    url: callbackUrl,
    username: config.insidedApiToken,
    secret: config.insidedApiSecret
  });
  
  const options = {
    hostname: apiUrl.hostname,
    port: apiUrl.port || (apiUrl.protocol === 'https:' ? 443 : 80),
    path: apiUrl.pathname,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(payload),
      'Authorization': `Bearer ${config.insidedApiToken}`,
    }
  };
  
  console.log(`\n📡 Subscribing to inSided webhook: ${eventName}`);
  console.log(`   Callback URL: ${callbackUrl}`);
  console.log(`   API Endpoint: ${apiUrl.href}`);
  
  return new Promise((resolve, reject) => {
    const client = apiUrl.protocol === 'https:' ? https : http;
    
    const req = client.request(options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          console.log(`✅ Successfully subscribed to ${eventName}`);
          console.log(`   Response: ${data}`);
          resolve({ eventName, success: true, data });
        } else {
          console.error(`❌ Failed to subscribe to ${eventName}`);
          console.error(`   Status: ${res.statusCode}`);
          console.error(`   Response: ${data}`);
          reject(new Error(`HTTP ${res.statusCode}: ${data}`));
        }
      });
    });
    
    req.on('error', (error) => {
      console.error(`❌ Request error for ${eventName}:`, error.message);
      reject(error);
    });
    
    req.write(payload);
    req.end();
  });
}

// Main execution
async function main() {
  console.log('🚀 inSided Webhook Subscription Tool');
  console.log('=====================================\n');
  
  validateConfig();
  
  console.log('Configuration:');
  console.log(`  inSided API: ${config.insidedApiBaseUrl}`);
  console.log(`  Supabase Project: ${config.supabaseProjectRef}`);
  console.log(`  API Token: ${config.insidedApiToken.substring(0, 10)}...`);
  
  // Subscribe to the profile update event
  const eventName = 'integration.UserProfileUpdated';
  
  try {
    await subscribeToWebhook(eventName);
    
    console.log('\n✅ Webhook subscription complete!');
    console.log('\n📝 Next steps:');
    console.log('   1. Test the webhook by updating a user profile in inSided');
    console.log('   2. Check Edge Function logs: supabase functions logs webhook-handler');
    console.log('   3. Verify events in database: SELECT * FROM events_raw;');
    
  } catch (error) {
    console.error('\n❌ Webhook subscription failed!');
    console.error('Error:', error.message);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main().catch(console.error);
}

module.exports = { subscribeToWebhook, validateConfig };

