-- =====================================================
-- Database Functions for Scheduled Jobs
-- =====================================================

-- =====================================================
-- Weekly Digest Builder Function
-- =====================================================
CREATE OR REPLACE FUNCTION build_weekly_digest()
RETURNS TABLE(digests_created INTEGER) AS $$
DECLARE
    week_start_date DATE;
    week_end_date DATE;
    digest_count INTEGER := 0;
    rec RECORD;
    digest_payload JSONB;
    chunk_array JSONB[];
    chunk JSONB;
BEGIN
    -- Calculate week window (last 7 days)
    week_end_date := CURRENT_DATE;
    week_start_date := week_end_date - INTERVAL '7 days';
    
    RAISE NOTICE 'Building weekly digest for % to %', week_start_date, week_end_date;
    
    -- Process for each channel: email and teams
    FOR rec IN (
        SELECT 'email' AS channel
        UNION ALL
        SELECT 'teams' AS channel
    ) LOOP
        -- Get all detections from the past week that haven't been included in a digest yet
        chunk_array := ARRAY[]::JSONB[];
        
        FOR digest_payload IN (
            SELECT jsonb_build_object(
                'user_id', d.user_id,
                'username', d.username,
                'title', d.title,
                'seniority_level', d.seniority_level,
                'country', d.country,
                'company', d.company,
                'joined_at', d.joined_at,
                'detected_at', d.detected_at
            )
            FROM detections d
            WHERE d.detected_at >= week_start_date
              AND d.detected_at <= week_end_date
              AND NOT d.included_in_digest
            ORDER BY d.detected_at DESC
        ) LOOP
            chunk_array := chunk_array || digest_payload;
            
            -- If we have 10 items, create a digest
            IF array_length(chunk_array, 1) = 10 THEN
                INSERT INTO digests (week_start, week_end, channel, payload)
                VALUES (week_start_date, week_end_date, rec.channel, 
                        jsonb_build_object('users', to_jsonb(chunk_array)));
                digest_count := digest_count + 1;
                chunk_array := ARRAY[]::JSONB[];
            END IF;
        END LOOP;
        
        -- Create digest for remaining items (if any)
        IF array_length(chunk_array, 1) > 0 THEN
            INSERT INTO digests (week_start, week_end, channel, payload)
            VALUES (week_start_date, week_end_date, rec.channel,
                    jsonb_build_object('users', to_jsonb(chunk_array)));
            digest_count := digest_count + 1;
        END IF;
    END LOOP;
    
    -- Mark all detections from this week as included in digest
    UPDATE detections
    SET included_in_digest = TRUE
    WHERE detected_at >= week_start_date
      AND detected_at <= week_end_date
      AND NOT included_in_digest;
    
    RAISE NOTICE 'Created % digest records', digest_count;
    RETURN QUERY SELECT digest_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Month-End Report Builder Function
-- =====================================================
CREATE OR REPLACE FUNCTION build_month_end_report()
RETURNS TABLE(report_id BIGINT) AS $$
DECLARE
    month_start TIMESTAMPTZ;
    month_end TIMESTAMPTZ;
    month_label TEXT;
    report_summary JSONB;
    new_report_id BIGINT;
BEGIN
    -- Calculate current month in EST
    month_start := date_trunc('month', CURRENT_TIMESTAMP);
    month_end := month_start + INTERVAL '1 month' - INTERVAL '1 second';
    month_label := to_char(month_start, 'YYYY-MM');
    
    RAISE NOTICE 'Building month-end report for %', month_label;
    
    -- Build summary statistics
    SELECT jsonb_build_object(
        'month', month_label,
        'total_detections', COUNT(*),
        'csuite_count', COUNT(*) FILTER (WHERE seniority_level = 'csuite'),
        'vp_count', COUNT(*) FILTER (WHERE seniority_level = 'vp'),
        'countries', jsonb_object_agg(COALESCE(country, 'Unknown'), country_count)
    )
    INTO report_summary
    FROM (
        SELECT 
            seniority_level,
            country,
            COUNT(*) as country_count
        FROM detections
        WHERE detected_at >= month_start
          AND detected_at <= month_end
        GROUP BY seniority_level, country
    ) subq;
    
    -- Insert report record (file generation happens in Python service)
    INSERT INTO reports (month_label, rules_version, summary)
    VALUES (month_label, 'v1', COALESCE(report_summary, '{}'::JSONB))
    RETURNING id INTO new_report_id;
    
    RAISE NOTICE 'Created report record with ID %', new_report_id;
    RETURN QUERY SELECT new_report_id;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Function to send pending digests (called by Python service)
-- =====================================================
CREATE OR REPLACE FUNCTION get_pending_digests()
RETURNS TABLE(
    digest_id BIGINT,
    week_start DATE,
    week_end DATE,
    channel TEXT,
    payload JSONB,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id,
        d.week_start,
        d.week_end,
        d.channel,
        d.payload,
        d.created_at
    FROM digests d
    WHERE NOT d.sent
    ORDER BY d.created_at ASC
    FOR UPDATE SKIP LOCKED
    LIMIT 10;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Function to mark digest as sent
-- =====================================================
CREATE OR REPLACE FUNCTION mark_digest_sent(digest_id_param BIGINT)
RETURNS VOID AS $$
BEGIN
    UPDATE digests
    SET sent = TRUE, sent_at = NOW()
    WHERE id = digest_id_param;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Functions complete
-- =====================================================

