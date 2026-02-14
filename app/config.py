import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("app.config")

class Config:
    """
    Centralized configuration for the application.
    """
    # LLM Settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
    
    # Twilio / WhatsApp
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
    MY_WHATSAPP_NUMBER = os.getenv("MY_WHATSAPP_NUMBER")
    
    # Email
    MY_EMAIL = os.getenv("MY_EMAIL") or os.getenv("EMAIL_ADDRESS")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    
    # Reminder Settings
    REMINDER_OFFSET_MINUTES = int(os.getenv("REMINDER_OFFSET_MINUTES", "10"))
    
    # Google Calendar Cloud Support
    GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    MEETINGS_FILE = os.path.join(DATA_DIR, "meetings.json")

    @classmethod
    def validate(cls):
        """Validating critical environment variables for cloud deployment."""
        critical = [
            "GEMINI_API_KEY", 
            "TWILIO_ACCOUNT_SID", 
            "TWILIO_AUTH_TOKEN", 
            "MY_EMAIL", 
            "EMAIL_PASSWORD"
        ]
        missing = [r for r in critical if not getattr(cls, r)]
        if missing:
            logger.error(f"CRITICAL MISSING CONFIG: {', '.join(missing)}")
            # We don't exit here to allow for partial feature testing, 
            # but in strict production, one might raise RuntimeError.
        else:
            logger.info("All critical production configurations validated.")

# Create data directory if it doesn't exist
os.makedirs(Config.DATA_DIR, exist_ok=True)

# Validate config on import
Config.validate()
