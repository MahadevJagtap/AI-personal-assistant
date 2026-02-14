import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.schemas import ChatRequest, ChatResponse, EmailRequest, HealthResponse
from app.agent.chat_agent import ChatAgent
from app.scheduler import meeting_scheduler
from app.agent.email_service import email_service


# --------------------------------------------------
# Logging Configuration
# --------------------------------------------------
logger = logging.getLogger(__name__)


# --------------------------------------------------
# FastAPI App Initialization
# --------------------------------------------------
app = FastAPI(
    title="AI Personal Assistant API",
    version="1.0.0"
)


# --------------------------------------------------
# Resolve Absolute Frontend Path (Important Fix)
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

# Static files will be mounted at the end to allow API routes precedence



# --------------------------------------------------
# CORS Middleware
# --------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)





# --------------------------------------------------
# Health Check
# --------------------------------------------------
@app.get("/health", response_model=HealthResponse)
async def health_check():
    return {"status": "ok"}


# --------------------------------------------------
# Startup / Shutdown Events
# --------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """Starts the background scheduler on app startup."""
    logger.info("Application starting up...")
    try:
        # Start the scheduler
        if not meeting_scheduler.scheduler.running:
            meeting_scheduler.scheduler.start()
            logger.info("Background scheduler started.")
        
        # Add the minute-by-minute reminder check job
        job_id = "check_meeting_reminders"
        if not meeting_scheduler.scheduler.get_job(job_id):
            meeting_scheduler.scheduler.add_job(
                meeting_scheduler.reminder_service.check_reminders,
                "interval",
                minutes=1,
                id=job_id
            )
            logger.info(f"Scheduled periodic reminder check job: {job_id}")

        # Add the daily cleanup job
        cleanup_job_id = "cleanup_old_meetings"
        if not meeting_scheduler.scheduler.get_job(cleanup_job_id):
            meeting_scheduler.scheduler.add_job(
                meeting_scheduler.cleanup_meetings,
                "interval",
                hours=24,
                id=cleanup_job_id
            )
            logger.info(f"Scheduled daily cleanup job: {cleanup_job_id}")
            
    except Exception as e:
        logger.error(f"Failed to start scheduler/jobs: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Shuts down the background scheduler gracefully."""
    logger.info("Application shutting down...")
    if meeting_scheduler.scheduler.running:
        meeting_scheduler.scheduler.shutdown()
        logger.info("Background scheduler shut down.")


# --------------------------------------------------
# Chat Endpoint
# --------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat interface.
    Accepts natural language input and runs the AI agent.
    """
    try:
        from app.agent.chat_agent import run_agent
        response = run_agent(request.message)
        return {"response": str(response)}
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --------------------------------------------------
# Get Meetings
# --------------------------------------------------
@app.get("/meetings")
async def get_meetings():
    """
    Returns scheduled meetings.
    """
    try:
        meetings_text = meeting_scheduler.list_meetings()
        return {
            "meetings": meeting_scheduler.meetings,
            "formatted_text": meetings_text
        }
    except Exception as e:
        logger.error(f"Error serving meetings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --------------------------------------------------
# Send Email
# --------------------------------------------------
@app.post("/email")
async def send_email_endpoint(request: EmailRequest):
    """
    Direct email sending endpoint.
    """
    try:
        result = email_service.send_email(
            request.to,
            request.subject,
            request.body
        )

        if "❌" in result:
            raise HTTPException(status_code=500, detail=result)

        return {"status": "success", "detail": result}

    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --------------------------------------------------
# Static File Mounting (Catch-all)
# --------------------------------------------------
# This must be at the end to ensure API routes are checked first
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


# --------------------------------------------------
# Run Server (Development Mode)
# --------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=True)

