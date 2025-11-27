// =====================================================
// Supabase Edge Function: Send Digests via AA Bots
// =====================================================
// Deploys Automation Anywhere bots to send email/Teams digests
// Deploy: supabase functions deploy send-digests

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
  botInputs: Record<string, string>,
  botName: string
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
    automationName: botName,
    description: `Deployed by CaptPathfinder - ${botName}`,
    botInput: formattedInputs,
    automationPriority: 'PRIORITY_MEDIUM',
    runElevated: false,
    hideBotAgentUi: false
  }
  
  console.log(`Deploying ${botName}...`)
  
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
  console.log(`${botName} deployed successfully. ID: ${result.deploymentId || result.automationId}`)
  
  return result
}

// Build email HTML
function buildEmailHTML(users: any[]): string {
  let html = `
  <html>
  <head>
    <style>
      body { font-family: Arial, sans-serif; }
      table { border-collapse: collapse; width: 100%; }
      th { background-color: #007bff; color: white; padding: 12px; text-align: left; }
      td { padding: 10px; border-bottom: 1px solid #ddd; }
      .header { background-color: #007bff; color: white; padding: 20px; }
    </style>
  </head>
  <body>
    <div class="header">
      <h2>Weekly Senior Executive Detections</h2>
    </div>
    <p><strong>Total detections:</strong> ${users.length}</p>
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Title</th>
          <th>Level</th>
          <th>Country</th>
          <th>Company</th>
          <th>Detected</th>
        </tr>
      </thead>
      <tbody>
  `
  
  for (const user of users) {
    html += `
        <tr>
          <td>${user.username || 'N/A'}</td>
          <td>${user.title || 'N/A'}</td>
          <td>${(user.seniority_level || '').toUpperCase()}</td>
          <td>${user.country || 'N/A'}</td>
          <td>${user.company || 'N/A'}</td>
          <td>${new Date(user.detected_at).toLocaleDateString()}</td>
        </tr>
    `
  }
  
  html += `
      </tbody>
    </table>
  </body>
  </html>
  `
  
  return html
}

// Build Teams message
function buildTeamsMessage(users: any[]): string {
  let message = `**Weekly Senior Executive Detections**\n\n**Total detections:** ${users.length}\n\n`
  
  for (const user of users) {
    message += `- **${user.username}** - ${user.title} (${(user.seniority_level || '').toUpperCase()})\n`
    message += `  ${user.company || 'Company N/A'} | ${user.country || 'Country N/A'}\n`
    message += `  Detected: ${new Date(user.detected_at).toLocaleDateString()}\n\n`
  }
  
  return message
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
    const aaTeamsBotId = Deno.env.get('AA_TEAMS_BOT_ID')!
    
    // Initialize Supabase
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey)
    
    console.log('Fetching pending digests...')
    
    // Get digest data from PostgreSQL function
    const { data: digestData, error: digestError } = await supabase.rpc('get_digest_data')
    
    if (digestError) {
      throw digestError
    }
    
    const emailUsers = digestData.email || []
    const teamsUsers = digestData.teams || []
    
    if (emailUsers.length === 0 && teamsUsers.length === 0) {
      return new Response(
        JSON.stringify({ status: 'no_pending_digests' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }
    
    // Authenticate with AA
    console.log('Authenticating with AA Control Room...')
    const token = await authenticateAA(aaUsername, aaApiKey, aaAuthEndpoint)
    
    const results: any = {
      email: null,
      teams: null
    }
    
    // Send email digest
    if (emailUsers.length > 0) {
      console.log(`Sending email digest with ${emailUsers.length} users...`)
      
      const emailInputs = {
        emailTo: 'stakeholder1@company.com;stakeholder2@company.com',
        emailSubject: 'Weekly Senior Executive Digest',
        emailBody: buildEmailHTML(emailUsers),
        isHTML: 'true',
        totalCount: emailUsers.length.toString()
      }
      
      results.email = await deployBot(
        aaControlRoomUrl,
        token,
        aaEmailBotId,
        emailInputs,
        'Email Bot'
      )
    }
    
    // Send Teams digest
    if (teamsUsers.length > 0) {
      console.log(`Sending Teams digest with ${teamsUsers.length} users...`)
      
      const teamsInputs = {
        teamsChannelWebhook: 'https://outlook.office.com/webhook/your-webhook-url',
        messageText: buildTeamsMessage(teamsUsers),
        messageType: 'markdown',
        totalCount: teamsUsers.length.toString()
      }
      
      results.teams = await deployBot(
        aaControlRoomUrl,
        token,
        aaTeamsBotId,
        teamsInputs,
        'Teams Bot'
      )
    }
    
    // Mark detections as included in digest
    await supabase
      .from('detections')
      .update({ included_in_digest: true })
      .eq('included_in_digest', false)
    
    console.log('Digests sent successfully')
    
    return new Response(
      JSON.stringify({
        status: 'success',
        results: results
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200
      }
    )
    
  } catch (error) {
    console.error('Error sending digests:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})

