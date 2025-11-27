"""
CaptPathfinder - Senior Executive Detection System
===================================================
FastAPI application for processing community profile updates and detecting senior executives.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from .models import WebhookEvent
from .config import get_settings
from .services.event_processor import get_event_processor
from .services.digest_builder import get_digest_sender
from .services.report_builder import get_report_builder

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    settings = get_settings()
    logger.info(f"Starting CaptPathfinder on {settings.api_host}:{settings.api_port}")
    logger.info(f"Database: {settings.supabase_db_url.split('@')[1] if '@' in settings.supabase_db_url else 'configured'}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down CaptPathfinder")


# Create FastAPI app
app = FastAPI(
    title="CaptPathfinder",
    description="Senior Executive Detection System for Community Profiles",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "CaptPathfinder",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",  # TODO: Add actual DB health check
        "timestamp": "2025-11-27T00:00:00Z"
    }


@app.post("/webhooks/community")
async def receive_webhook(event: WebhookEvent, background_tasks: BackgroundTasks):
    """
    Receive webhook from community platform.
    
    Processes user profile updates, specifically job title changes.
    
    Note: For production with Supabase Edge Functions, webhooks go to
    the Edge Function first, which stores in events_raw table.
    This endpoint can still be used for direct webhook integration.
    """
    logger.info(f"Received webhook for user {event.userId}, field: {event.profileField}")
    
    try:
        # Get event processor
        processor = get_event_processor()
        
        # Process event (async)
        result = await processor.process_event(event)
        
        logger.info(f"Webhook processed: {result}")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "accepted",
                "result": result
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing webhook: {str(e)}"
        )


@app.post("/process-event/{event_id}")
async def process_queued_event(event_id: int):
    """
    Process an event from the events_raw table.
    
    Called by Supabase Edge Function or worker process to process
    events that were queued via webhook.
    """
    logger.info(f"Processing queued event {event_id}")
    
    try:
        from .database import get_db
        db = get_db()
        
        # Fetch event from database
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT id, user_id, username, profile_field, value, old_value
                FROM events_raw
                WHERE id = %s AND NOT processed
            """, (event_id,))
            
            event_data = cur.fetchone()
        
        if not event_data:
            return JSONResponse(
                status_code=404,
                content={"status": "not_found", "message": f"Event {event_id} not found or already processed"}
            )
        
        # Convert to WebhookEvent model
        event = WebhookEvent(
            userId=event_data['user_id'],
            username=event_data['username'] or "Unknown",
            profileField=event_data['profile_field'],
            value=event_data['value'],
            oldValue=event_data['old_value']
        )
        
        # Process event
        processor = get_event_processor()
        result = await processor.process_event(event)
        
        # Mark as processed
        with db.get_cursor() as cur:
            cur.execute("""
                UPDATE events_raw
                SET processed = TRUE, processed_at = NOW()
                WHERE id = %s
            """, (event_id,))
        
        logger.info(f"Queued event {event_id} processed: {result}")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "processed",
                "event_id": event_id,
                "result": result
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing queued event {event_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing event: {str(e)}"
        )


@app.post("/admin/send-digests")
async def send_digests():
    """
    Manually trigger sending of pending digests.
    
    This is typically called by pg_cron via a scheduled job,
    but can also be triggered manually for testing.
    """
    logger.info("Manual digest send triggered")
    
    try:
        sender = get_digest_sender()
        results = await sender.send_pending_digests()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "completed",
                "results": results
            }
        )
        
    except Exception as e:
        logger.error(f"Error sending digests: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error sending digests: {str(e)}"
        )


@app.post("/admin/generate-reports")
async def generate_reports():
    """
    Manually trigger generation of pending reports.
    
    Generates CSV and HTML reports for months that need them.
    """
    logger.info("Manual report generation triggered")
    
    try:
        builder = get_report_builder()
        results = builder.process_pending_reports()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "completed",
                "results": results
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating reports: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating reports: {str(e)}"
        )


@app.get("/admin/stats")
async def get_stats():
    """
    Get system statistics.
    
    Returns counts of users, detections, pending digests, etc.
    """
    from .database import get_db
    
    db = get_db()
    stats = {}
    
    try:
        with db.get_cursor() as cur:
            # Count senior users
            cur.execute("SELECT COUNT(*) as count FROM user_state")
            stats['senior_users'] = cur.fetchone()['count']
            
            # Count by level
            cur.execute("""
                SELECT seniority_level, COUNT(*) as count
                FROM user_state
                GROUP BY seniority_level
            """)
            stats['by_level'] = {row['seniority_level']: row['count'] for row in cur.fetchall()}
            
            # Count pending digests
            cur.execute("SELECT COUNT(*) as count FROM digests WHERE NOT sent")
            stats['pending_digests'] = cur.fetchone()['count']
            
            # Count total detections
            cur.execute("SELECT COUNT(*) as count FROM detections")
            stats['total_detections'] = cur.fetchone()['count']
            
            # Count unprocessed events
            cur.execute("SELECT COUNT(*) as count FROM events_raw WHERE NOT processed")
            stats['unprocessed_events'] = cur.fetchone()['count']
        
        return JSONResponse(
            status_code=200,
            content={"stats": stats}
        )
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching stats: {str(e)}"
        )


@app.get("/admin/recent-detections")
async def get_recent_detections(limit: int = 10):
    """
    Get recent senior executive detections.
    
    Useful for monitoring and debugging.
    """
    from .database import get_db
    
    db = get_db()
    
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT 
                    user_id, username, title, seniority_level,
                    country, company, detected_at
                FROM detections
                ORDER BY detected_at DESC
                LIMIT %s
            """, (limit,))
            
            detections = cur.fetchall()
        
        # Convert datetime to string for JSON serialization
        for d in detections:
            if d['detected_at']:
                d['detected_at'] = d['detected_at'].isoformat()
        
        return JSONResponse(
            status_code=200,
            content={"detections": detections}
        )
        
    except Exception as e:
        logger.error(f"Error fetching recent detections: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching detections: {str(e)}"
        )


# Entry point for running with uvicorn
if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
        reload=True  # For development
    )

