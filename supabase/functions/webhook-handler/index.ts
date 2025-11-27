"""
Supabase Edge Function for CaptPathfinder Webhook Handler
==========================================================

This Edge Function receives webhooks from inSided (Gainsight Community)
and processes senior executive detections.

Deploy to Supabase: supabase functions deploy webhook-handler
"""

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Parse webhook payload from inSided
    const payload = await req.json()
    
    console.log('Received webhook:', JSON.stringify(payload, null, 2))
    
    // Extract event data
    const event = payload.event || payload.type
    let userId = payload.userId || payload.user_id
    let username = payload.username
    let profileField = payload.profileField || payload.profile_field
    let value = payload.value
    let oldValue = payload.oldValue || payload.old_value
    
    console.log(`Event type: ${event}`)
    
    // Handle different event types
    if (event === 'integration.UserRegistered') {
      // User registration event - check if they have a job title
      console.log('Processing user registration event')
      
      // Extract user data from registration payload
      userId = userId || payload.user?.id || payload.user?.userId
      username = username || payload.user?.username || payload.user?.displayName
      
      // Get job title from user object
      const jobTitle = payload.user?.jobTitle || payload.user?.job_title || payload.jobTitle
      
      if (!jobTitle || jobTitle.trim() === '') {
        console.log('Registration event without job title, skipping')
        return new Response(
          JSON.stringify({ status: 'skipped', reason: 'no_job_title_on_registration' }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
      }
      
      // Set up for processing
      profileField = 'Job Title'
      value = jobTitle
      oldValue = null // No old value for new users
      
      console.log(`New user registered: ${username} (${userId}) with title: ${value}`)
      
    } else if (event === 'integration.UserProfileUpdated') {
      // Profile update event - only process Job Title changes
      console.log('Processing profile update event')
      
      if (profileField !== 'Job Title') {
        console.log(`Skipping non-Job Title field: ${profileField}`)
        return new Response(
          JSON.stringify({ status: 'skipped', reason: 'not_job_title' }),
          { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
      }
      
      console.log(`Job title updated: ${username} (${userId}): "${oldValue}" → "${value}"`)
      
    } else {
      // Unknown event type
      console.log(`Unknown or unsupported event type: ${event}`)
      return new Response(
        JSON.stringify({ status: 'skipped', reason: 'unsupported_event_type', event }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }
    
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey)
    
    // Generate idempotency key
    const idempotencyKey = await crypto.subtle.digest(
      'SHA-256',
      new TextEncoder().encode(`${userId}|${profileField}|${value}`)
    ).then(buffer => 
      Array.from(new Uint8Array(buffer))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('')
    )
    
    // Store raw event (idempotent)
    const { data: existingEvent } = await supabase
      .from('events_raw')
      .select('id')
      .eq('idempotency_key', idempotencyKey)
      .single()
    
    if (existingEvent) {
      console.log('Duplicate event, skipping')
      return new Response(
        JSON.stringify({ status: 'duplicate' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }
    
    // Insert raw event
    const { data: eventData, error: eventError } = await supabase
      .from('events_raw')
      .insert({
        user_id: userId,
        username: username,
        profile_field: profileField,
        value: value,
        old_value: oldValue,
        idempotency_key: idempotencyKey,
        processed: false
      })
      .select()
      .single()
    
    if (eventError) {
      throw new Error(`Failed to store event: ${eventError.message}`)
    }
    
    console.log(`✅ Stored ${event} event (ID: ${eventData.id}) - Will be processed by background worker`)
    
    // Trigger processing via HTTP call to main Python service
    // Or queue for async processing
    const pythonServiceUrl = Deno.env.get('PYTHON_SERVICE_URL')
    if (pythonServiceUrl) {
      // Call Python service to process event
      await fetch(`${pythonServiceUrl}/process-event/${eventData.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
    }
    
    return new Response(
      JSON.stringify({ 
        status: 'accepted',
        event_id: eventData.id 
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
    
  } catch (error) {
    console.error('Error processing webhook:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})

