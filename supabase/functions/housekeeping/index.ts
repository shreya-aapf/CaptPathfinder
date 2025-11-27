// =====================================================
// Supabase Edge Function: Housekeeping Tasks
// =====================================================
// Purges old events daily
// Scheduled for 2 AM EST daily
// Deploy: supabase functions deploy housekeeping

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
    
    console.log('Running housekeeping tasks...')
    
    // Call PostgreSQL function to purge old events
    const { data, error } = await supabase.rpc('purge_old_events')
    
    if (error) {
      throw error
    }
    
    console.log(`Housekeeping completed. Purged ${data} old events.`)
    
    return new Response(
      JSON.stringify({
        status: 'success',
        purged_count: data
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200
      }
    )
    
  } catch (error) {
    console.error('Error during housekeeping:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})

