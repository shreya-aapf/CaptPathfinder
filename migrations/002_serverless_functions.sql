-- =====================================================
-- Classification Function in PostgreSQL
-- =====================================================
-- This replaces the Python classification logic with pure SQL/plpgsql
-- Runs directly in the database for maximum performance

CREATE OR REPLACE FUNCTION classify_job_title(title TEXT)
RETURNS TABLE(is_senior BOOLEAN, seniority_level TEXT) AS $$
DECLARE
    normalized_title TEXT;
BEGIN
    -- Normalize title
    normalized_title := lower(trim(regexp_replace(title, '\s+', ' ', 'g')));
    
    -- Check exclusions first
    IF normalized_title ~* '(student|club|volunteer|intern|retired|ex-|former|seeking|aspiring|head of|head,)' THEN
        RETURN QUERY SELECT FALSE, ''::TEXT;
        RETURN;
    END IF;
    
    -- Check C-suite patterns
    IF normalized_title ~* '(\mboss\M|\bchief\M.*\bofficer\M|\bc[a-z]o\M|\bceo\M|\bcfo\M|\bcoo\M|\bcto\M|\bciso\M|\bcio\M|\bcro\M|\bcmo\M|\bchro\M|\bcpo\M|\bcdo\M|\bcso\M|\bcco\M|\bcao\M|\bclo\M|\bpresident\M)' 
       AND normalized_title !~* 'vice' THEN
        RETURN QUERY SELECT TRUE, 'csuite'::TEXT;
        RETURN;
    END IF;
    
    -- Check VP patterns
    IF normalized_title ~* '(\bvp\M|\bv\.p\.\M|\bvice president\M|\bsvp\M|\bevp\M|\bavp\M|\bexecutive vice president\M|\bsenior vice president\M|\bassociate vice president\M)' THEN
        RETURN QUERY SELECT TRUE, 'vp'::TEXT;
        RETURN;
    END IF;
    
    -- Not senior
    RETURN QUERY SELECT FALSE, ''::TEXT;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =====================================================
-- Event Processing Function
-- =====================================================
-- Processes events from events_raw table
-- Called by pg_cron or Edge Function

CREATE OR REPLACE FUNCTION process_pending_events()
RETURNS TABLE(processed_count INTEGER, senior_count INTEGER) AS $$
DECLARE
    event_record RECORD;
    classification RECORD;
    total_processed INTEGER := 0;
    total_senior INTEGER := 0;
    user_metadata RECORD;
BEGIN
    -- Process unprocessed events (with lock to prevent concurrent processing)
    FOR event_record IN
        SELECT * FROM events_raw
        WHERE NOT processed
        ORDER BY received_at ASC
        LIMIT 100
        FOR UPDATE SKIP LOCKED
    LOOP
        -- Only process Job Title updates
        IF lower(event_record.profile_field) = 'job title' THEN
            -- Classify the title
            SELECT * INTO classification FROM classify_job_title(event_record.value);
            
            IF classification.is_senior THEN
                -- Check if user already exists
                SELECT * INTO user_metadata FROM user_state WHERE user_id = event_record.user_id;
                
                IF user_metadata IS NULL THEN
                    -- First time detection - insert into user_state and detections
                    INSERT INTO user_state (
                        user_id, username, title, seniority_level,
                        first_detected_at, last_seen_at
                    ) VALUES (
                        event_record.user_id,
                        event_record.username,
                        event_record.value,
                        classification.seniority_level,
                        NOW(),
                        NOW()
                    );
                    
                    INSERT INTO detections (
                        user_id, username, title, seniority_level,
                        detected_at, rules_version
                    ) VALUES (
                        event_record.user_id,
                        event_record.username,
                        event_record.value,
                        classification.seniority_level,
                        NOW(),
                        'v1'
                    );
                    
                    total_senior := total_senior + 1;
                    
                ELSE
                    -- Update existing user
                    UPDATE user_state
                    SET 
                        username = event_record.username,
                        title = event_record.value,
                        seniority_level = classification.seniority_level,
                        last_seen_at = NOW()
                    WHERE user_id = event_record.user_id;
                    
                    -- Check for promotion
                    IF user_metadata.seniority_level = 'vp' AND classification.seniority_level = 'csuite' THEN
                        INSERT INTO detections (
                            user_id, username, title, seniority_level,
                            detected_at, rules_version
                        ) VALUES (
                            event_record.user_id,
                            event_record.username,
                            event_record.value,
                            classification.seniority_level,
                            NOW(),
                            'v1'
                        );
                        total_senior := total_senior + 1;
                    END IF;
                END IF;
            ELSE
                -- Not senior - remove from user_state if exists
                DELETE FROM user_state WHERE user_id = event_record.user_id;
            END IF;
        END IF;
        
        -- Mark event as processed
        UPDATE events_raw
        SET processed = TRUE, processed_at = NOW()
        WHERE id = event_record.id;
        
        total_processed := total_processed + 1;
    END LOOP;
    
    RAISE NOTICE 'Processed % events, % new senior executives', total_processed, total_senior;
    
    RETURN QUERY SELECT total_processed, total_senior;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Setup pg_cron job to process events every minute
-- =====================================================
SELECT cron.schedule(
    'process-pending-events',
    '* * * * *',  -- Every minute
    $$SELECT process_pending_events();$$
);

-- =====================================================
-- Helper function to get pending digest data
-- =====================================================
CREATE OR REPLACE FUNCTION get_digest_data()
RETURNS JSONB AS $$
DECLARE
    digest_payload JSONB;
BEGIN
    SELECT jsonb_build_object(
        'email', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'user_id', user_id,
                    'username', username,
                    'title', title,
                    'seniority_level', seniority_level,
                    'country', country,
                    'company', company,
                    'detected_at', detected_at
                )
            )
            FROM detections
            WHERE NOT included_in_digest
            ORDER BY detected_at DESC
            LIMIT 10
        ),
        'teams', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'user_id', user_id,
                    'username', username,
                    'title', title,
                    'seniority_level', seniority_level,
                    'country', country,
                    'company', company,
                    'detected_at', detected_at
                )
            )
            FROM detections
            WHERE NOT included_in_digest
            ORDER BY detected_at DESC
            LIMIT 10
        )
    ) INTO digest_payload;
    
    RETURN digest_payload;
END;
$$ LANGUAGE plpgsql;

