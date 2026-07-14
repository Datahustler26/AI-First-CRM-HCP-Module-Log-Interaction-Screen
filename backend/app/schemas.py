from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime

# HCP Schemas
class HCPBase(BaseModel):
    name: str
    specialty: str
    email: Optional[str] = None
    phone: Optional[str] = None

class HCPCreate(HCPBase):
    pass

class HCPResponse(HCPBase):
    id: int
    
    class Config:
        from_attributes = True

# Product Schemas
class ProductResponse(BaseModel):
    id: int
    name: str
    category: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

# Interaction Schemas
class InteractionBase(BaseModel):
    hcp_id: int
    interaction_type: str  # Meeting, Call, Email, Webcast
    date: str              # YYYY-MM-DD
    time: str              # HH:MM
    attendees: Optional[str] = ""
    topics_discussed: str
    voice_note_summary: Optional[str] = None
    materials_shared: Optional[str] = ""
    samples_distributed: Optional[str] = ""
    sentiment: str         # Positive, Neutral, Negative
    outcomes: Optional[str] = ""
    follow_up_actions: Optional[str] = ""
    ai_summary: Optional[str] = None

class InteractionCreate(InteractionBase):
    pass

class InteractionUpdate(BaseModel):
    hcp_id: Optional[int] = None
    interaction_type: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    voice_note_summary: Optional[str] = None
    materials_shared: Optional[str] = None
    samples_distributed: Optional[str] = None
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    ai_summary: Optional[str] = None

class InteractionResponse(InteractionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    hcp: HCPResponse

    class Config:
        from_attributes = True

# AI Chat Schemas
class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    # Contains the current state of the structured form so the agent can inspect or fill it
    form_draft: Optional[dict] = None

class ChatResponse(BaseModel):
    reply: str
    form_draft: Optional[dict] = None
    tools_called: List[str] = []
    status: str = "success"
