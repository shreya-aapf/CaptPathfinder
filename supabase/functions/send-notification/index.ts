// =====================================================
// Supabase Edge Function: Send Immediate Notification
// =====================================================
// Sends immediate notification via AA Bot when senior exec detected
// Triggered by webhook-handler after detection
// Deploy: supabase functions deploy send-notification

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

// Authenticate with AA Control Room
async function authenticateAA(username: string, apiKey: string, authEndpoint: string) {
  const response = await fetch(authEndpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: username,
      apiKey: apiKey,
      multipleLogin: false
    })
  })
  
  if (!response.ok) {
    throw new Error(`AA authentication failed: ${response.statusText}`)
  }
  
  const data = await response.json()
  return data.token
}

// Deploy AA bot
async function deployBot(
  controlRoomUrl: string,
  token: string,
  botId: string,
  botInputs: Record<string, string>
) {
  // Format inputs for AA
  const formattedInputs: Record<string, any> = {}
  for (const [key, value] of Object.entries(botInputs)) {
    formattedInputs[key] = {
      type: 'STRING',
      string: value
    }
  }
  
  const payload = {
    botId: parseInt(botId),
    automationName: 'Senior Executive Detection Alert',
    description: `Deployed by CaptPathfinder - Immediate notification`,
    botInput: formattedInputs,
    automationPriority: 'PRIORITY_HIGH',
    runElevated: false,
    hideBotAgentUi: false
  }
  
  console.log('Deploying AA bot...')
  
  const response = await fetch(`${controlRoomUrl}/v3/automations/deploy`, {
    method: 'POST',
    headers: {
      'X-Authorization': token,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  })
  
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`Bot deployment failed: ${response.statusText} - ${errorText}`)
  }
  
  const result = await response.json()
  console.log(`✅ Bot deployed successfully. ID: ${result.deploymentId || result.automationId}`)
  
  return result
}

// Build email HTML for single detection
function buildEmailHTML(user: any): string {
  return `
  <html>
  <head>
    <style>
      body { font-family: Arial, sans-serif; }
      .header { background-color: #007bff; color: white; padding: 20px; }
      .content { padding: 20px; }
      .alert { background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }
      .details { background-color: #f8f9fa; padding: 15px; border-radius: 5px; }
      .label { font-weight: bold; color: #495057; }
    </style>
  </head>
  <body>
    <div class="header">
      <h2>🎯 Senior Executive Detected!</h2>
    </div>
    <div class="content">
      <div class="alert">
        <strong>New senior executive detected in the community platform.</strong>
      </div>
      <div class="details">
        <p><span class="label">Name:</span> ${user.username || 'N/A'}</p>
        <p><span class="label">Title:</span> ${user.title || 'N/A'}</p>
        <p><span class="label">Level:</span> ${(user.seniority_level || '').toUpperCase()}</p>
        <p><span class="label">Detected:</span> ${new Date().toLocaleString()}</p>
      </div>
      <p style="margin-top: 20px; color: #6c757d; font-size: 12px;">
        This is an automated notification from CaptPathfinder.
      </p>
    </div>
  </body>
  </html>
  `
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Get environment variables
    const aaControlRoomUrl = Deno.env.get('AA_CONTROL_ROOM_URL')!
    const aaUsername = Deno.env.get('AA_USERNAME')!
    const aaApiKey = Deno.env.get('AA_API_KEY')!
    const aaAuthEndpoint = Deno.env.get('AA_AUTH_ENDPOINT') || 
      'https://automationanywhere-be-prod.automationanywhere.com/v2/authentication'
    const aaEmailBotId = Deno.env.get('AA_EMAIL_BOT_ID')!
    
    // Parse request
    const payload = await req.json()
    const { user_id, username, title, seniority_level, detection_id } = payload
    
    console.log(`📧 Sending immediate notification for: ${username} (${seniority_level})`)
    
    // Authenticate with AA
    console.log('Authenticating with AA Control Room...')
    const token = await authenticateAA(aaUsername, aaApiKey, aaAuthEndpoint)
    
    // Prepare email inputs
    const emailInputs = {
      emailTo: 'stakeholder1@company.com;stakeholder2@company.com', // TODO: Make configurable
      emailSubject: `🎯 Senior Executive Detected: ${username}`,
      emailBody: buildEmailHTML({ username, title, seniority_level }),
      isHTML: 'true',
      userId: user_id,
      detectedAt: new Date().toISOString()
    }
    
    // Deploy email bot
    const result = await deployBot(
      aaControlRoomUrl,
      token,
      aaEmailBotId,
      emailInputs
    )
    
    // Update detection record
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey)
    
    await supabase
      .from('detections')
      .update({ 
        included_in_digest: true, // Mark as notified
        updated_at: new Date().toISOString()
      })
      .eq('id', detection_id)
    
    console.log('✅ Notification sent successfully')
    
    return new Response(
      JSON.stringify({
        status: 'success',
        deployment_id: result.deploymentId || result.automationId,
        user: username,
        seniority_level: seniority_level
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200
      }
    )
    
  } catch (error) {
    console.error('Error sending notification:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})

