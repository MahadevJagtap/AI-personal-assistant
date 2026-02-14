import uvicorn
import logging
from fastapi import FastAPI
from app.api.main import app as api_app
from app.scheduler import meeting_scheduler
from app.config import Config

# Configure logging
logger = logging.getLogger("app.main")

# We use the app instance from api.main but we could also wrap it here
app = api_app

@app.get("/health")
async def health_check():
    """Lightweight health check for uptime monitoring."""
    return {"status": "running"}

@app.on_event("startup")
async def startup_event():
    """Starts the background scheduler on app startup."""
    logger.info("Starting up AI Personal Assistant...")
    try:
        if not meeting_scheduler.scheduler.running:
            meeting_scheduler.scheduler.start()
            logger.info("Background scheduler started.")
        
        # Periodic jobs
        if not meeting_scheduler.scheduler.get_job("check_meeting_reminders"):
            meeting_scheduler.scheduler.add_job(
                meeting_scheduler.reminder_service.check_reminders,
                "interval",
                minutes=1,
                id="check_meeting_reminders"
            )
        
        if not meeting_scheduler.scheduler.get_job("cleanup_old_meetings"):
            meeting_scheduler.scheduler.add_job(
                meeting_scheduler.cleanup_meetings,
                "interval",
                hours=24,
                id="cleanup_old_meetings"
            )
        logger.info("Background jobs initialized.")
    except Exception as e:
        logger.error(f"Failed to start scheduler/jobs: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Graceful shutdown."""
    logger.info("Shutting down AI Personal Assistant...")
    if meeting_scheduler.scheduler.running:
        meeting_scheduler.scheduler.shutdown()
        logger.info("Background scheduler shut down.")

if __name__ == "__main__":
    # Entry point for production execution
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
