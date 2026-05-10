"""
Automation module for scheduled tasks.
Developed by: Developer C
Uses APScheduler for task scheduling.
"""

import os
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Global scheduler instance
scheduler = None


def init_scheduler():
    """
    Initialize and start the APScheduler scheduler.
    
    Returns:
        BackgroundScheduler: Initialized scheduler instance
    """
    global scheduler
    
    try:
        scheduler = BackgroundScheduler(daemon=True)
        
        # Schedule email reporting task for 08:00 AM daily
        scheduler.add_job(
            func=send_email_report,
            trigger=CronTrigger(hour=8, minute=0),
            id='email_report_job',
            name='Daily Email Report',
            replace_existing=True,
            misfire_grace_time=60
        )
        
        logger.info("Scheduler initialized successfully")
        logger.info("Jobs scheduled:")
        logger.info("- Daily Email Report: Every day at 08:00 AM")
        
        return scheduler
        
    except Exception as e:
        logger.error(f"Scheduler initialization failed: {str(e)}")
        raise


def start_scheduler():
    """
    Start the scheduler.
    
    Raises:
        RuntimeError: If scheduler is not initialized
    """
    if scheduler is None:
        raise RuntimeError("Scheduler not initialized. Call init_scheduler() first.")
    
    try:
        scheduler.start()
        logger.info("Scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")
        raise


def stop_scheduler():
    """
    Stop the scheduler gracefully.
    """
    if scheduler is not None:
        try:
            scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")


def send_email_report():
    """
    Send daily email report with business metrics and updates.
    
    TODO: Developer C - Implement email reporting logic here
    
    Steps to implement:
    1. Retrieve daily business metrics from ChromaDB
    2. Generate PDF/HTML report with:
       - Stock status summary
       - New orders received
       - Completed tasks
       - Pending tasks with due dates
       - Sales metrics
    3. Connect to email server (Gmail/SMTP)
    4. Send report to configured EMAIL_SENDER
    5. Log successful/failed attempts
    
    Configuration needed:
    - EMAIL_SENDER: Sender email address
    - EMAIL_PASSWORD: App-specific password for Gmail (or SMTP credentials)
    - RECIPIENT_EMAILS: Comma-separated list of recipients
    """
    
    logger.info(f"[SCHEDULED TASK] Executing email report job at {datetime.now()}")
    
    try:
        # Placeholder for email reporting logic
        logger.info("Email report job executed (placeholder)")
        
        # TODO: Replace with actual implementation
        # email_sender = os.getenv("EMAIL_SENDER")
        # email_password = os.getenv("EMAIL_PASSWORD")
        # 
        # if not email_sender or not email_password:
        #     logger.warning("Email credentials not configured in .env file")
        #     return
        # 
        # # Implementation here:
        # # 1. Generate report
        # # 2. Connect to email service
        # # 3. Send report
        # # 4. Log status
        
        logger.info("Email report sent successfully (implementation pending)")
        
    except Exception as e:
        logger.error(f"Email report job failed: {str(e)}")


def add_custom_job(func, trigger, job_id, job_name):
    """
    Add a custom scheduled job to the scheduler.
    
    Args:
        func: Callable function to execute
        trigger: APScheduler trigger (CronTrigger, IntervalTrigger, etc.)
        job_id: Unique identifier for the job
        job_name: Human-readable name for the job
    
    Returns:
        Scheduled job object
    
    Raises:
        RuntimeError: If scheduler is not initialized
    """
    if scheduler is None:
        raise RuntimeError("Scheduler not initialized. Call init_scheduler() first.")
    
    try:
        job = scheduler.add_job(
            func=func,
            trigger=trigger,
            id=job_id,
            name=job_name,
            replace_existing=True,
            misfire_grace_time=60
        )
        logger.info(f"Job '{job_name}' (ID: {job_id}) added successfully")
        return job
    except Exception as e:
        logger.error(f"Failed to add job '{job_name}': {str(e)}")
        raise


def get_jobs_info():
    """
    Get information about all scheduled jobs.
    
    Returns:
        List of dictionaries containing job information
    """
    if scheduler is None:
        return []
    
    jobs_info = []
    for job in scheduler.get_jobs():
        jobs_info.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": str(job.next_run_time),
            "trigger": str(job.trigger)
        })
    
    return jobs_info


# Application lifecycle integration
def setup_automation(app=None):
    """
    Setup automation module for FastAPI application.
    
    Args:
        app: FastAPI application instance (optional)
    """
    try:
        init_scheduler()
        start_scheduler()
        logger.info("Automation module initialized and running")
        
        # Register shutdown event if app is provided
        if app:
            @app.on_event("shutdown")
            async def shutdown_scheduler():
                stop_scheduler()
        
        return scheduler
        
    except Exception as e:
        logger.error(f"Automation setup failed: {str(e)}")
        raise


if __name__ == "__main__":
    # Standalone testing
    try:
        logger.info("Starting automation module in standalone mode...")
        setup_automation()
        
        # Keep the scheduler running
        import time
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        stop_scheduler()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        stop_scheduler()
