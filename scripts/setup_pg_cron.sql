-- =====================================================
-- pg_cron Setup for CaptPathfinder
-- =====================================================
-- Prerequisites:
-- 1. Enable pg_cron extension in Supabase dashboard or run:
--    CREATE EXTENSION IF NOT EXISTS pg_cron;
-- 2. Ensure timezone is set to America/New_York
-- =====================================================

-- Enable pg_cron extension
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- =====================================================
-- Weekly Digest Job
-- =====================================================
-- Runs every Friday at 5 PM EST
SELECT cron.schedule(
    'weekly-digest',           -- job name
    '0 17 * * FRI',           -- cron expression (5 PM every Friday)
    $$SELECT build_weekly_digest();$$
);

-- =====================================================
-- Month-End Report Job
-- =====================================================
-- Runs on the last day of every month at 11:55 PM EST
-- Note: pg_cron doesn't support 'L' for last day, so we use a workaround
-- This runs daily at 11:55 PM but only executes the function if it's the last day
SELECT cron.schedule(
    'month-end-report',
    '55 23 * * *',  -- Every day at 11:55 PM
    $$
    DO $$
    BEGIN
        -- Only run if tomorrow is a different month (i.e., today is last day of month)
        IF EXTRACT(MONTH FROM CURRENT_DATE + INTERVAL '1 day') != EXTRACT(MONTH FROM CURRENT_DATE) THEN
            PERFORM build_month_end_report();
        END IF;
    END $$;
    $$
);

-- =====================================================
-- Housekeeping Job
-- =====================================================
-- Runs daily at 2 AM EST to purge old events
SELECT cron.schedule(
    'housekeeping',
    '0 2 * * *',  -- Every day at 2 AM
    $$SELECT purge_old_events();$$
);

-- =====================================================
-- View Scheduled Jobs
-- =====================================================
-- Run this to see all scheduled jobs:
-- SELECT * FROM cron.job;

-- =====================================================
-- View Job Run History
-- =====================================================
-- Run this to see job execution history:
-- SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 20;

-- =====================================================
-- Unscheduling Jobs (if needed)
-- =====================================================
-- To remove a job, use:
-- SELECT cron.unschedule('job-name');
-- Example:
-- SELECT cron.unschedule('weekly-digest');
-- SELECT cron.unschedule('month-end-report');
-- SELECT cron.unschedule('housekeeping');

-- =====================================================
-- Manual Testing
-- =====================================================
-- To manually trigger the jobs for testing:
-- SELECT build_weekly_digest();
-- SELECT build_month_end_report();
-- SELECT purge_old_events();

