import smtplib
import logging
from email.message import EmailMessage
from typing import List
from app.config import Config

# Configure logging
logger = logging.getLogger(__name__)

class EmailService:
    """
    Handles sending emails via SMTP.
    """
    def __init__(self):
        self.config = Config
        self.email_address = self.config.EMAIL_ADDRESS
        self.email_password = self.config.EMAIL_PASSWORD
        self.smtp_server = self.config.SMTP_SERVER
        self.smtp_port = self.config.SMTP_PORT

    def _connect_and_send(self, msg: EmailMessage):
        """Internal helper to connect to SMTP and send."""
        if not self.email_address or not self.email_password:
            raise ValueError("Email credentials (EMAIL_ADDRESS, EMAIL_PASSWORD) are missing in .env")

        try:
            # Connect to server
            # Note: For Gmail, use port 587 for TLS, 465 for SSL.
            # This implementation assumes TLS (587) which is common.
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(msg)
            logger.info(f"Email sent successfully to {msg['To']}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise e

    def send_email(self, to_email: str, subject: str, body: str) -> str:
        """
        Sends a single email.
        """
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = self.email_address
        msg['To'] = to_email
        msg.set_content(body)

        try:
            self._connect_and_send(msg)
            return f"✅ Email sent to {to_email}"
        except Exception as e:
            return f"❌ Failed to send email: {e}"

    def send_bulk_email(self, recipients: List[str], subject: str, body: str) -> str:
        """
        Sends the same email to multiple recipients.
        """
        success_count = 0
        failed_count = 0
        errors = []

        for recipient in recipients:
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = self.email_address
            msg['To'] = recipient
            msg.set_content(body)

            try:
                self._connect_and_send(msg)
                success_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"{recipient}: {str(e)}")

        result = f"Bulk send complete. Success: {success_count}, Failed: {failed_count}."
        if errors:
            result += f" Errors: {'; '.join(errors)}"
        return result

# Singleton instance
email_service = EmailService()
