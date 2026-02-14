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
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
    
    # Twilio / WhatsApp
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
    MY_WHATSAPP_NUMBER = os.getenv("MY_WHATSAPP_NUMBER")
    
    # Email
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    
    # Reminder Settings
    REMINDER_OFFSET_MINUTES = int(os.getenv("REMINDER_OFFSET_MINUTES", "10"))
    
    # Google Calendar Cloud Support
    # This can be the path to a file OR the raw JSON string itself
    GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
    GOOGLE_TOKEN_PICKLE = os.getenv("GOOGLE_TOKEN_PICKLE") # Optional base64 or path
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    MEETINGS_FILE = os.path.join(DATA_DIR, "meetings.json")

    @classmethod
    def validate(cls):
        """Validating critical environment variables."""
        critical = ["GOOGLE_API_KEY", "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"]
        missing = [r for r in critical if not getattr(cls, r)]
        if missing:
            logger.error(f"CRITICAL MISSING CONFIG: {', '.join(missing)}")
        else:
            logger.info("Critical configuration validated.")

# Create data directory if it doesn't exist
os.makedirs(Config.DATA_DIR, exist_ok=True)

# Validate config on import
Config.validate()
