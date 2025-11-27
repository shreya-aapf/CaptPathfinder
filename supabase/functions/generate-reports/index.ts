// =====================================================
// Supabase Edge Function: Monthly Report Generator
// =====================================================
// Generates month-end reports
// Scheduled for last day of month at 11:55 PM EST
// Deploy: supabase functions deploy generate-reports

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
    
    console.log('Generating month-end report...')
    
    // Call PostgreSQL function to generate report
    const { data, error } = await supabase.rpc('build_month_end_report')
    
    if (error) {
      throw error
    }
    
    console.log(`Report generated successfully`)
    
    return new Response(
      JSON.stringify({
        status: 'success',
        report_id: data
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200
      }
    )
    
  } catch (error) {
    console.error('Error generating report:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      }
    )
  }
})

