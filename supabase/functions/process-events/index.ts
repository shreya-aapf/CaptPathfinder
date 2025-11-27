// =====================================================
// Supabase Edge Function: Process Events
// =====================================================
// Processes pending events using PostgreSQL functions
// Deploy: supabase functions deploy process-events

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey)
    
    console.log('Processing pending events...')
    
    // Call PostgreSQL function to process events
    const { data, error } = await supabase.rpc('process_pending_events')
    
    if (error) {
      throw error
    }
    
    console.log(`Processed ${data.processed_count} events, ${data.senior_count} new senior execs`)
    
    return new Response(
      JSON.stringify({
        status: 'success',
        processed: data.processed_count,
        senior_detections: data.senior_count
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200
      }
    )
    
  } catch (error) {
    console.error('Error processing events:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})

