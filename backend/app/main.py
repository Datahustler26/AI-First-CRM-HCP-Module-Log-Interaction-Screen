import os
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db, init_db, HCP, Interaction, Product
from app.schemas import (
    HCPResponse, HCPCreate,
    InteractionResponse, InteractionCreate, InteractionUpdate,
    ChatRequest, ChatResponse,
    ProductResponse
)
from app.agent import interact_with_agent

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI-First CRM HCP Module API",
    description="Backend API for Healthcare Professionals interaction logging with LangGraph AI Assistant",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow React dev server or any origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to ensure database is created and seeded
@app.on_event("startup")
def on_startup():
    logger.info("Initializing database and tables...")
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")

@app.get("/")
def read_root():
    return {"message": "AI-First CRM HCP Module API is running. Access /docs for Swagger documentation."}

# ----------------------------------------------------
# HCP Endpoints
# ----------------------------------------------------
@app.get("/api/hcps", response_model=List[HCPResponse])
def get_hcps(db: Session = Depends(get_db)):
    return db.query(HCP).all()

@app.post("/api/hcps", response_model=HCPResponse, status_code=status.HTTP_201_CREATED)
def create_hcp(hcp_in: HCPCreate, db: Session = Depends(get_db)):
    existing = db.query(HCP).filter(HCP.name.ilike(hcp_in.name)).first()
    if existing:
        return existing
        
    db_hcp = HCP(
        name=hcp_in.name,
        specialty=hcp_in.specialty,
        email=hcp_in.email,
        phone=hcp_in.phone
    )
    db.add(db_hcp)
    db.commit()
    db.refresh(db_hcp)
    return db_hcp

# ----------------------------------------------------
# Product / Material Endpoints (for autocomplete)
# ----------------------------------------------------
@app.get("/api/products", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

# ----------------------------------------------------
# Interaction Endpoints
# ----------------------------------------------------
@app.get("/api/interactions", response_model=List[InteractionResponse])
def get_interactions(db: Session = Depends(get_db)):
    return db.query(Interaction).order_by(Interaction.date.desc(), Interaction.time.desc()).all()

@app.post("/api/interactions", response_model=InteractionResponse, status_code=status.HTTP_201_CREATED)
def create_interaction(inter_in: InteractionCreate, db: Session = Depends(get_db)):
    # Verify HCP exists
    hcp = db.query(HCP).filter(HCP.id == inter_in.hcp_id).first()
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found.")
        
    ai_summary = inter_in.ai_summary
    if not ai_summary:
        ai_summary = f"Logged via form. Interaction Type: {inter_in.interaction_type} on {inter_in.date}. Topics: {inter_in.topics_discussed}."
        
    db_inter = Interaction(
        hcp_id=inter_in.hcp_id,
        interaction_type=inter_in.interaction_type,
        date=inter_in.date,
        time=inter_in.time,
        attendees=inter_in.attendees,
        topics_discussed=inter_in.topics_discussed,
        voice_note_summary=inter_in.voice_note_summary,
        materials_shared=inter_in.materials_shared,
        samples_distributed=inter_in.samples_distributed,
        sentiment=inter_in.sentiment,
        outcomes=inter_in.outcomes,
        follow_up_actions=inter_in.follow_up_actions,
        ai_summary=ai_summary
    )
    db.add(db_inter)
    db.commit()
    db.refresh(db_inter)
    return db_inter

@app.put("/api/interactions/{interaction_id}", response_model=InteractionResponse)
def update_interaction(interaction_id: int, inter_in: InteractionUpdate, db: Session = Depends(get_db)):
    db_inter = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not db_inter:
        raise HTTPException(status_code=404, detail="Interaction not found.")
        
    # Update fields if provided
    update_data = inter_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_inter, key, value)
        
    db_inter.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_inter)
    return db_inter

@app.delete("/api/interactions/{interaction_id}")
def delete_interaction(interaction_id: int, db: Session = Depends(get_db)):
    db_inter = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not db_inter:
        raise HTTPException(status_code=404, detail="Interaction not found.")
    db.delete(db_inter)
    db.commit()
    return {"status": "success", "message": f"Deleted interaction ID {interaction_id}."}

# ----------------------------------------------------
# AI Chat Interface Endpoint
# ----------------------------------------------------
@app.post("/api/chat", response_model=ChatResponse)
def chat_with_agent(payload: ChatRequest):
    """
    Passes user input and history to the LangGraph agent.
    Returns the agent's message response, any updated form drafts,
    and a list of tools invoked.
    """
    logger.info(f"Received chat message: {payload.message}")
    
    # Translate schema models to raw dictionaries for LangGraph agent
    history_dicts = []
    for msg in payload.history:
        history_dicts.append({
            "role": msg.role,
            "content": msg.content
        })
        
    try:
        agent_result = interact_with_agent(
            message=payload.message,
            history=history_dicts,
            form_draft=payload.form_draft or {}
        )
        return ChatResponse(
            reply=agent_result["reply"],
            form_draft=agent_result["form_draft"],
            tools_called=agent_result["tools_called"],
            status="success"
        )
    except Exception as e:
        logger.error(f"Error in chat_with_agent endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------
# Voice Note Summarization Endpoint
# ----------------------------------------------------
@app.post("/api/voice-summarize")
def summarize_voice_note(payload: Dict[str, str], db: Session = Depends(get_db)):
    """
    Mocks voice note summarization.
    Accepts raw transcription text and extracts interaction fields.
    """
    transcription = payload.get("transcription", "")
    if not transcription:
        raise HTTPException(status_code=400, detail="No transcription text provided.")
        
    logger.info(f"Summarizing voice note transcription: {transcription}")
    
    # Simple extraction logic for voice note
    # In a fully deployed environment with Groq API keys, this would call Groq.
    # We will provide a robust simulation or Groq call if available.
    
    trans_lower = transcription.lower()
    extracted = {
        "hcp_name": "",
        "topics_discussed": transcription,
        "sentiment": "Neutral",
        "follow_up_actions": "",
        "materials_shared": "",
        "samples_distributed": ""
    }
    
    # Check for doctor names
    hcps = db.query(HCP).all()
    for hcp in hcps:
        if hcp.name.lower() in trans_lower or hcp.name.split()[-1].lower() in trans_lower:
            extracted["hcp_name"] = hcp.name
            break
            
    # Check for products/materials
    products = db.query(Product).all()
    materials = []
    samples = []
    for prod in products:
        if prod.name.lower() in trans_lower:
            if prod.category == "Material":
                materials.append(prod.name)
            else:
                samples.append(prod.name)
                
    extracted["materials_shared"] = ", ".join(materials)
    extracted["samples_distributed"] = ", ".join(samples)
    
    # Extract sentiment
    if any(w in trans_lower for w in ["positive", "great", "happy", "excited", "interested"]):
        extracted["sentiment"] = "Positive"
    elif any(w in trans_lower for w in ["negative", "unhappy", "complained", "reject"]):
        extracted["sentiment"] = "Negative"
        
    # Generate mock follow ups
    if "follow up" in trans_lower or "schedule" in trans_lower or "next week" in trans_lower:
        extracted["follow_up_actions"] = "Schedule follow-up meeting as requested."
        
    return {
        "status": "success",
        "transcription": transcription,
        "extracted_fields": extracted
    }

# ----------------------------------------------------
# DB Reinit Endpoint (for testing)
# ----------------------------------------------------
@app.post("/api/init-db")
def reinit_database():
    try:
        init_db()
        return {"status": "success", "message": "Database initialized/seeded."}
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise HTTPException(status_code=500, detail=str(e))
