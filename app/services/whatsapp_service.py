import logging
from twilio.rest import Client
from app.config import Config

# Configure logging
logger = logging.getLogger(__name__)

class WhatsAppService:
    """
    Service to send WhatsApp notifications via Twilio.
    """
    def __init__(self):
        self.config = Config
        self.account_sid = self.config.TWILIO_ACCOUNT_SID
        self.auth_token = self.config.TWILIO_AUTH_TOKEN
        self.from_whatsapp_number = self.config.TWILIO_WHATSAPP_NUMBER
        self.to_whatsapp_number = self.config.MY_WHATSAPP_NUMBER
        
        if not all([self.account_sid, self.auth_token, self.from_whatsapp_number, self.to_whatsapp_number]):
            logger.error("Twilio credentials or numbers not found in environment variables.")
            self.client = None
        else:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.client = None

    def send_message(self, message: str) -> str:
        """
        Sends a WhatsApp message using Twilio.
        """
        if not self.client:
            return "❌ Twilio client not initialized. Check credentials."

        try:
            msg = self.client.messages.create(
                body=message,
                from_=self.from_whatsapp_number,
                to=self.to_whatsapp_number
            )
            logger.info(f"WhatsApp message sent successfully: {msg.sid}")
            return f"✅ WhatsApp notification sent: {msg.sid}"
        except Exception as e:
            error_msg = f"❌ Failed to send WhatsApp message: {e}"
            logger.error(error_msg)
            return error_msg

# Singleton instance
whatsapp_service = WhatsAppService()
