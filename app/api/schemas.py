
from pydantic import BaseModel, EmailStr
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

class EmailRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str

class HealthResponse(BaseModel):
    status: str
