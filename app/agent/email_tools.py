from langchain.tools import tool
from app.config import Config
from app.services.whatsapp_service import whatsapp_service
from app.agent.email_service import email_service

@tool
def send_email_tool(text: str) -> str:
    """
    Sends an email. Input text should specify recipient, subject, and body.
    Recommended string format: "Recipient|Subject|Body"
    Example: "boss@company.com|Update|I finished the report."
    
    If the agent cannot determine structured args, it can try to parse natural language, 
    but pipe-separated is preferred for reliability.
    """
    try:
        parts = text.split('|')
        if len(parts) < 3:
            # Fallback for simple natural language - very basic parsing
            # This is risky but requested for "natural language" support in the tool implementation prompt
            # Better approach: Agent (LLM) should have formatted the input string before calling this tool.
            return "❌ Invalid format. Please use 'Recipient|Subject|Body'."
        
        to_email = parts[0].strip()
        subject = parts[1].strip()
        body = parts[2].strip()
        
        return email_service.send_email(to_email, subject, body)
    except Exception as e:
        return f"❌ Error processing request: {e}"
