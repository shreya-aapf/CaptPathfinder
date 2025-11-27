"""
Worker script for processing digests and reports.

This can be run as a scheduled job (e.g., via cron or cloud scheduler)
to process pending digests and reports independently from the web service.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import get_settings
from app.services.digest_builder import get_digest_sender
from app.services.report_builder import get_report_builder

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def process_digests():
    """Process and send pending digests."""
    logger.info("Starting digest processing...")
    
    try:
        sender = get_digest_sender()
        results = await sender.send_pending_digests()
        
        logger.info(f"Digest processing complete: {results}")
        return results
    except Exception as e:
        logger.error(f"Error processing digests: {e}", exc_info=True)
        raise


def process_reports():
    """Process and generate pending reports."""
    logger.info("Starting report processing...")
    
    try:
        builder = get_report_builder()
        results = builder.process_pending_reports()
        
        logger.info(f"Report processing complete: {results}")
        return results
    except Exception as e:
        logger.error(f"Error processing reports: {e}", exc_info=True)
        raise


async def main():
    """Main worker entry point."""
    settings = get_settings()
    logger.info(f"Worker started")
    
    # Process digests
    digest_results = await process_digests()
    
    # Process reports
    report_results = process_reports()
    
    logger.info("Worker completed successfully")
    
    return {
        "digests": digest_results,
        "reports": report_results
    }


if __name__ == "__main__":
    asyncio.run(main())

