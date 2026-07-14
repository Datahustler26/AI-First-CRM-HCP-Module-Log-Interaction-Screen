import os
import json
import logging
from typing import TypedDict, List, Dict, Any, Sequence, Optional
from datetime import datetime

# SQLAlchemy / DB imports
from app.database import get_session, HCP, Interaction, Product

# LangChain / LangGraph imports
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# State definition
class AgentState(TypedDict):
    messages: Sequence[BaseMessage]
    form_draft: Dict[str, Any]
    tools_called: List[str]
    current_hcp_id: Optional[int]
    response: str

# ----------------------------------------------------
# 1. Log Interaction Tool (Mandatory)
# ----------------------------------------------------
@tool
def log_interaction(
    hcp_name: str,
    interaction_type: str,
    date: str,
    time: str,
    topics_discussed: str,
    sentiment: str,
    attendees: str = "",
    materials_shared: str = "",
    samples_distributed: str = "",
    outcomes: str = "",
    follow_up_actions: str = ""
) -> str:
    """
    Logs a new interaction with a Healthcare Professional (HCP) into the CRM database.
    Captures HCP details, interaction metadata, sentiment, and outcomes.
    """
    db = get_session()
    try:
        # 1. Resolve HCP
        hcp = db.query(HCP).filter(HCP.name.ilike(f"%{hcp_name}%")).first()
        if not hcp:
            # Create a new HCP if they don't exist yet
            hcp = HCP(
                name=hcp_name,
                specialty="General Practitioner", # Default
                email=f"{hcp_name.lower().replace(' ', '.')}@medicalhcp.com",
                phone=""
            )
            db.add(hcp)
            db.flush() # Populate hcp.id
            logger.info(f"Created new HCP profile for: {hcp_name}")
        
        # 2. Extract entities and summarize (Simple placeholder for internal summary)
        ai_summary = f"Interaction Type: {interaction_type} on {date} at {time} with {hcp.name}. Topics: {topics_discussed}."
        
        # 3. Create Interaction
        interaction = Interaction(
            hcp_id=hcp.id,
            interaction_type=interaction_type,
            date=date,
            time=time,
            attendees=attendees,
            topics_discussed=topics_discussed,
            materials_shared=materials_shared,
            samples_distributed=samples_distributed,
            sentiment=sentiment,
            outcomes=outcomes,
            follow_up_actions=follow_up_actions,
            ai_summary=ai_summary
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)
        
        result = {
            "status": "success",
            "message": f"Successfully logged interaction ID {interaction.id} for HCP {hcp.name}.",
            "interaction_id": interaction.id,
            "hcp_id": hcp.id,
            "hcp_name": hcp.name,
            "hcp_specialty": hcp.specialty,
            "interaction_type": interaction.interaction_type,
            "date": interaction.date,
            "time": interaction.time,
            "sentiment": interaction.sentiment,
            "ai_summary": interaction.ai_summary
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        db.rollback()
        logger.error(f"Error in log_interaction tool: {e}")
        return json.dumps({"status": "error", "message": str(e)})
    finally:
        db.close()

# ----------------------------------------------------
# 2. Edit Interaction Tool (Mandatory)
# ----------------------------------------------------
@tool
def edit_interaction(
    interaction_id: int,
    interaction_type: Optional[str] = None,
    date: Optional[str] = None,
    time: Optional[str] = None,
    attendees: Optional[str] = None,
    topics_discussed: Optional[str] = None,
    materials_shared: Optional[str] = None,
    samples_distributed: Optional[str] = None,
    sentiment: Optional[str] = None,
    outcomes: Optional[str] = None,
    follow_up_actions: Optional[str] = None
) -> str:
    """
    Modifies an existing interaction in the database by its ID. Updates only the specified fields.
    """
    db = get_session()
    try:
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return json.dumps({"status": "error", "message": f"Interaction with ID {interaction_id} not found."})
        
        # Update fields if provided
        if interaction_type is not None:
            interaction.interaction_type = interaction_type
        if date is not None:
            interaction.date = date
        if time is not None:
            interaction.time = time
        if attendees is not None:
            interaction.attendees = attendees
        if topics_discussed is not None:
            interaction.topics_discussed = topics_discussed
        if materials_shared is not None:
            interaction.materials_shared = materials_shared
        if samples_distributed is not None:
            interaction.samples_distributed = samples_distributed
        if sentiment is not None:
            interaction.sentiment = sentiment
        if outcomes is not None:
            interaction.outcomes = outcomes
        if follow_up_actions is not None:
            interaction.follow_up_actions = follow_up_actions
            
        # Update summary
        interaction.ai_summary = f"[Updated] Interaction Type: {interaction.interaction_type} on {interaction.date} at {interaction.time}. Topics: {interaction.topics_discussed}."
        interaction.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(interaction)
        
        hcp = db.query(HCP).filter(HCP.id == interaction.hcp_id).first()
        
        result = {
            "status": "success",
            "message": f"Successfully updated interaction ID {interaction_id} for HCP {hcp.name if hcp else 'Unknown'}.",
            "interaction_id": interaction.id,
            "interaction_type": interaction.interaction_type,
            "date": interaction.date,
            "time": interaction.time,
            "sentiment": interaction.sentiment,
            "topics_discussed": interaction.topics_discussed,
            "follow_up_actions": interaction.follow_up_actions
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        db.rollback()
        logger.error(f"Error in edit_interaction tool: {e}")
        return json.dumps({"status": "error", "message": str(e)})
    finally:
        db.close()

# ----------------------------------------------------
# 3. Search HCP History Tool
# ----------------------------------------------------
@tool
def search_hcp_history(hcp_name: str) -> str:
    """
    Retrieves previous interactions, shared materials, and notes for a specific HCP.
    """
    db = get_session()
    try:
        hcp = db.query(HCP).filter(HCP.name.ilike(f"%{hcp_name}%")).first()
        if not hcp:
            return json.dumps({"status": "not_found", "message": f"No HCP profile found for name '{hcp_name}'."})
        
        interactions = db.query(Interaction).filter(Interaction.hcp_id == hcp.id).order_by(Interaction.date.desc()).all()
        
        history_list = []
        for inter in interactions:
            history_list.append({
                "interaction_id": inter.id,
                "type": inter.interaction_type,
                "date": inter.date,
                "time": inter.time,
                "topics_discussed": inter.topics_discussed,
                "sentiment": inter.sentiment,
                "materials_shared": inter.materials_shared,
                "samples_distributed": inter.samples_distributed,
                "outcomes": inter.outcomes,
                "follow_up_actions": inter.follow_up_actions
            })
            
        result = {
            "status": "success",
            "hcp_id": hcp.id,
            "hcp_name": hcp.name,
            "specialty": hcp.specialty,
            "email": hcp.email,
            "phone": hcp.phone,
            "total_interactions": len(interactions),
            "history": history_list
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in search_hcp_history tool: {e}")
        return json.dumps({"status": "error", "message": str(e)})
    finally:
        db.close()

# ----------------------------------------------------
# 4. Suggest Follow-Up Actions Tool
# ----------------------------------------------------
@tool
def suggest_follow_up(topics_discussed: str, hcp_specialty: Optional[str] = None) -> str:
    """
    Generates tailored sales follow-up strategies based on the topics discussed in the meeting.
    """
    suggestions = []
    topics_lower = topics_discussed.lower()
    
    # Generic suggestions
    suggestions.append("Schedule follow-up meeting in 2 weeks")
    
    # Context-specific suggestions
    if "oncoboost" in topics_lower or (hcp_specialty and "onco" in hcp_specialty.lower()):
        suggestions.append("Send OncoBoost Phase III trial data PDF")
        suggestions.append("Invite doctor to upcoming Oncology Roundtable webcast")
    if "cardiashield" in topics_lower or (hcp_specialty and "cardio" in hcp_specialty.lower()):
        suggestions.append("Provide CardiaShield Efficacy Study details")
        suggestions.append("Deliver CardiaShield 10mg Tablets sample samples")
    if "neurovigor" in topics_lower or (hcp_specialty and "neuro" in hcp_specialty.lower()):
        suggestions.append("Follow up with NeuroVigor prescribing information booklet")
        suggestions.append("Ask if doctor needs additional NeuroVigor samples for patient trials")
    if "pediatrix" in topics_lower or (hcp_specialty and "pedia" in hcp_specialty.lower()):
        suggestions.append("Deliver Pediatrix Vaccine Guidelines pamphlet")
        suggestions.append("Deliver Pediatrix Chewable Multivitamin samples")
        
    result = {
        "status": "success",
        "topics_discussed": topics_discussed,
        "specialty_context": hcp_specialty,
        "suggested_actions": suggestions
    }
    return json.dumps(result, indent=2)

# ----------------------------------------------------
# 5. Product Recommendation Tool
# ----------------------------------------------------
@tool
def product_recommendation(hcp_specialty: str) -> str:
    """
    Recommends products, promotional materials, and patient samples aligned with the doctor's medical specialty.
    """
    db = get_session()
    try:
        specialty_lower = hcp_specialty.lower()
        
        # Determine keywords to query products
        keyword = ""
        if "cardio" in specialty_lower:
            keyword = "cardia"
        elif "onco" in specialty_lower:
            keyword = "onco"
        elif "neuro" in specialty_lower:
            keyword = "neuro"
        elif "pedia" in specialty_lower:
            keyword = "pedia"
            
        products_query = db.query(Product)
        if keyword:
            products_query = products_query.filter(Product.name.ilike(f"%{keyword}%"))
            
        matched_products = products_query.all()
        
        recommendations = []
        for p in matched_products:
            recommendations.append({
                "product_name": p.name,
                "category": p.category,
                "description": p.description
            })
            
        result = {
            "status": "success",
            "hcp_specialty": hcp_specialty,
            "recommended_products": recommendations
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error in product_recommendation tool: {e}")
        return json.dumps({"status": "error", "message": str(e)})
    finally:
        db.close()

# List of all tools
ALL_TOOLS = {
    "log_interaction": log_interaction,
    "edit_interaction": edit_interaction,
    "search_hcp_history": search_hcp_history,
    "suggest_follow_up": suggest_follow_up,
    "product_recommendation": product_recommendation
}

# ----------------------------------------------------
# 6. Groq LLM Setup and LangGraph Agent Configuration
# ----------------------------------------------------
def get_groq_llm():
    """
    Attempts to initialize the ChatGroq model using the API key in environment.
    Returns None if missing/invalid to trigger self-healing fallback.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or "placeholder" in api_key or api_key == "gsk_your_groq_api_key_placeholder":
        logger.warning("GROQ_API_KEY is not set or holds placeholder value. Falling back to rule-based agent simulator.")
        return None
        
    try:
        from langchain_groq import ChatGroq
        model_name = os.getenv("GROQ_MODEL", "gemma2-9b-it")
        llm = ChatGroq(
            groq_api_key=api_key,
            model_name=model_name,
            temperature=0.2
        )
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize ChatGroq LLM: {e}")
        return None

# Fallback NLP Parser (Simulating LangGraph Agent)
def simulate_agent_nlp(message: str, current_form_draft: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rules-based parsing fallback to extract interaction details when Groq API key is missing.
    Ensures E2E functionality in local/test conditions.
    """
    msg_lower = message.lower()
    
    # 1. Attempt tool selection detection
    tools_called = []
    reply = ""
    form_draft = current_form_draft.copy() if current_form_draft else {
        "hcp_name": "",
        "interaction_type": "Meeting",
        "date": datetime.today().strftime('%Y-%m-%d'),
        "time": datetime.today().strftime('%H:%M'),
        "attendees": "",
        "topics_discussed": "",
        "materials_shared": "",
        "samples_distributed": "",
        "sentiment": "Neutral",
        "outcomes": "",
        "follow_up_actions": ""
    }
    
    # Resolve HCP name keywords
    hcp_names = ["Anita Sharma", "Rajesh Patel", "Sarah Connor", "Amit Verma", "Priya Nair"]
    detected_hcp = None
    for h in hcp_names:
        if h.lower() in msg_lower or h.split()[-1].lower() in msg_lower:
            detected_hcp = h
            break
            
    if detected_hcp:
        form_draft["hcp_name"] = detected_hcp
        
    # Resolve Interaction Type
    if "email" in msg_lower:
        form_draft["interaction_type"] = "Email"
    elif "call" in msg_lower:
        form_draft["interaction_type"] = "Call"
    elif "webcast" in msg_lower:
        form_draft["interaction_type"] = "Webcast"
    else:
        form_draft["interaction_type"] = "Meeting"
        
    # Resolve Sentiment
    if "positive" in msg_lower or "great" in msg_lower or "happy" in msg_lower:
        form_draft["sentiment"] = "Positive"
    elif "negative" in msg_lower or "upset" in msg_lower or "disappointed" in msg_lower:
        form_draft["sentiment"] = "Negative"
    elif "neutral" in msg_lower:
        form_draft["sentiment"] = "Neutral"

    # Search HCP History intent
    if "history" in msg_lower or "previous meetings" in msg_lower or "past interactions" in msg_lower:
        tools_called.append("search_hcp_history")
        target_name = detected_hcp or "Anita Sharma"
        tool_result_str = search_hcp_history.invoke({"hcp_name": target_name})
        tool_res = json.loads(tool_result_str)
        if tool_res["status"] == "success":
            reply = f"I've searched the history for **{tool_res['hcp_name']}** ({tool_res['specialty']}).\n\n"
            reply += f"Total historical interactions found: **{tool_res['total_interactions']}**.\n\n"
            for i, inter in enumerate(tool_res["history"][:3]):
                reply += f"{i+1}. **{inter['type']}** on {inter['date']} at {inter['time']}.\n"
                reply += f"   - Topics: {inter['topics_discussed']}\n"
                reply += f"   - Sentiment: {inter['sentiment']}\n"
                if inter['follow_up_actions']:
                    reply += f"   - Follow Up: {inter['follow_up_actions']}\n"
        else:
            reply = f"I couldn't find any historical records for HCP: '{target_name}'."
            
    # Edit interaction intent
    elif "edit" in msg_lower or "update" in msg_lower:
        tools_called.append("edit_interaction")
        # Try to find a number in message to represent interaction ID
        import re
        ids = re.findall(r'\b\d+\b', message)
        inter_id = int(ids[0]) if ids else 1
        
        # Modify sentiment/topics if specified
        sentiment_val = form_draft["sentiment"]
        topics_val = "Updated topics via AI Assistant" if "topic" in msg_lower else None
        
        tool_result_str = edit_interaction.invoke({
            "interaction_id": inter_id,
            "sentiment": sentiment_val,
            "topics_discussed": topics_val
        })
        tool_res = json.loads(tool_result_str)
        if tool_res["status"] == "success":
            reply = f"I have successfully executed the `edit_interaction` tool to update Interaction ID **{inter_id}**.\n"
            reply += f"- **HCP**: {tool_res.get('hcp_name', 'Dr. Anita Sharma')}\n"
            reply += f"- **Updated Date**: {tool_res['date']}\n"
            reply += f"- **Sentiment**: {tool_res['sentiment']}\n"
        else:
            reply = f"Failed to edit interaction: {tool_res['message']}"

    # Product recommendations intent
    elif "recommend" in msg_lower or "product" in msg_lower or "specialty" in msg_lower:
        tools_called.append("product_recommendation")
        specialty = "Cardiologist"
        if "onco" in msg_lower:
            specialty = "Oncologist"
        elif "pedia" in msg_lower:
            specialty = "Pediatrician"
        elif "neuro" in msg_lower:
            specialty = "Neurologist"
            
        tool_result_str = product_recommendation.invoke({"hcp_specialty": specialty})
        tool_res = json.loads(tool_result_str)
        if tool_res["status"] == "success":
            reply = f"Based on the specialty **{specialty}**, here are recommended products and materials:\n\n"
            for prod in tool_res["recommended_products"]:
                reply += f"- **{prod['product_name']}** ({prod['category']}): {prod['description']}\n"
        else:
            reply = "No product recommendations found for that specialty."
            
    # Suggest Follow-up intent
    elif "follow up" in msg_lower or "next steps" in msg_lower or "suggest" in msg_lower:
        tools_called.append("suggest_follow_up")
        topics = form_draft["topics_discussed"] or "Discussion on pharmaceutical options"
        specialty = "Cardiologist" if "cardio" in topics.lower() else ("Oncologist" if "onco" in topics.lower() else "General Practitioner")
        tool_result_str = suggest_follow_up.invoke({"topics_discussed": topics, "hcp_specialty": specialty})
        tool_res = json.loads(tool_result_str)
        
        reply = "Here are AI-suggested follow-up actions:\n\n"
        for act in tool_res["suggested_actions"]:
            reply += f"- {act}\n"
            
    # Default behavior: Extract details and prepare a mock log_interaction call
    else:
        # Extract details from message if user is describing a log
        # Example: "I met with Dr. Rajesh Patel today. Sentiment was positive. Topics discussed: oncology."
        if "met" in msg_lower or "log" in msg_lower or "discussed" in msg_lower:
            tools_called.append("log_interaction")
            
            # Simple extractor
            if "today" in msg_lower:
                form_draft["date"] = datetime.today().strftime('%Y-%m-%d')
            
            # Extract topics
            if "discussed" in msg_lower:
                parts = message.split("discussed")
                if len(parts) > 1:
                    form_draft["topics_discussed"] = parts[1].strip(" .,").capitalize()
            else:
                form_draft["topics_discussed"] = message
                
            # Log interaction directly
            hcp_name_val = form_draft["hcp_name"] or "Dr. Anita Sharma"
            tool_result_str = log_interaction.invoke({
                "hcp_name": hcp_name_val,
                "interaction_type": form_draft["interaction_type"],
                "date": form_draft["date"],
                "time": form_draft["time"],
                "topics_discussed": form_draft["topics_discussed"],
                "sentiment": form_draft["sentiment"],
                "attendees": form_draft["attendees"],
                "materials_shared": form_draft["materials_shared"],
                "samples_distributed": form_draft["samples_distributed"],
                "outcomes": form_draft["outcomes"],
                "follow_up_actions": form_draft["follow_up_actions"]
            })
            tool_res = json.loads(tool_result_str)
            if tool_res["status"] == "success":
                reply = f"I've successfully processed the interaction details and logged them to the CRM database.\n\n"
                reply += f"- **HCP Name**: {tool_res['hcp_name']} ({tool_res['hcp_specialty']})\n"
                reply += f"- **Type**: {tool_res['interaction_type']} on {tool_res['date']} at {tool_res['time']}\n"
                reply += f"- **Sentiment**: {tool_res['sentiment']}\n"
                reply += f"- **Generated Summary**: {tool_res['ai_summary']}\n\n"
                reply += f"The interaction has been saved under ID **{tool_res['interaction_id']}**."
            else:
                reply = f"Error logging interaction: {tool_res['message']}"
        else:
            reply = "Hello! I am your AI HCP CRM Assistant. You can describe a recent meeting, and I'll extract the details to log it (e.g. *'I met with Dr. Rajesh Patel today. The sentiment was positive and we discussed oncology'*). You can also search histories, edit logs, ask for product recommendations, or get follow-up suggestions."

    return {
        "reply": reply,
        "form_draft": form_draft,
        "tools_called": tools_called
    }

# ----------------------------------------------------
# 7. LangGraph Agent Logic (Standard Implementation)
# ----------------------------------------------------
def build_agent_graph():
    """
    Creates and compiles a LangGraph StateGraph agent.
    If the Groq LLM is not configured, it returns a mock wrapper that behaves identically
    from the API perspective, utilizing the simulate_agent_nlp engine.
    """
    llm = get_groq_llm()
    if llm is None:
        # Return a simulated compiled graph
        class MockCompiledGraph:
            def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
                # Extract message text
                messages = state.get("messages", [])
                last_msg = messages[-1].content if messages else ""
                form_draft = state.get("form_draft", {})
                
                sim_res = simulate_agent_nlp(last_msg, form_draft)
                
                # Append assistant reply to messages
                new_messages = list(messages)
                new_messages.append(AIMessage(content=sim_res["reply"]))
                
                return {
                    "messages": new_messages,
                    "form_draft": sim_res["form_draft"],
                    "tools_called": sim_res["tools_called"],
                    "current_hcp_id": None,
                    "response": sim_res["reply"]
                }
        return MockCompiledGraph()

    # 1. Setup LangGraph components
    from langchain_core.messages import ToolMessage
    from langchain_core.utils.function_calling import convert_to_openai_tool
    
    # Bind tools to the Groq LLM
    tools_list = [log_interaction, edit_interaction, search_hcp_history, suggest_follow_up, product_recommendation]
    llm_with_tools = llm.bind_tools(tools_list)
    
    def agent_node(state: AgentState):
        messages = state["messages"]
        system_prompt = SystemMessage(content=(
            "You are a premium, expert AI Assistant for a Healthcare Customer Relationship Management (CRM) system. "
            "Your job is to help pharmaceutical and medical sales representatives log and manage their interactions "
            "with Healthcare Professionals (HCPs).\n\n"
            "You have access to tools to: \n"
            "1. log_interaction: capture and save new meeting logs.\n"
            "2. edit_interaction: update a previous meeting record.\n"
            "3. search_hcp_history: fetch previous interactions with a doctor.\n"
            "4. suggest_follow_up: recommend sales follow-ups based on topics discussed.\n"
            "5. product_recommendation: suggest products based on HCP specialty.\n\n"
            "If the user is describing a meeting they had, extract as many details as possible and invoke log_interaction. "
            "Format your final responses clearly using Markdown. Make them look professional and helpful."
        ))
        
        # Call LLM
        response = llm_with_tools.invoke([system_prompt] + list(messages))
        
        # Update state
        return {
            "messages": [response],
            "response": response.content
        }

    def execute_tools_node(state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        
        tools_called = []
        new_messages = []
        form_draft = state.get("form_draft", {}).copy()
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]
                
                tools_called.append(tool_name)
                logger.info(f"LangGraph Agent invoking tool: {tool_name} with args: {tool_args}")
                
                # Execute tool
                tool_func = ALL_TOOLS[tool_name]
                tool_result_str = tool_func.invoke(tool_args)
                
                # Append tool message
                tool_msg = ToolMessage(content=tool_result_str, name=tool_name, tool_call_id=tool_id)
                new_messages.append(tool_msg)
                
                # If tool was log_interaction, sync form draft state
                if tool_name == "log_interaction":
                    try:
                        res = json.loads(tool_result_str)
                        if res["status"] == "success":
                            # Sync fields to form draft
                            form_draft.update({
                                "hcp_name": res.get("hcp_name", ""),
                                "interaction_type": res.get("interaction_type", "Meeting"),
                                "date": res.get("date", ""),
                                "time": res.get("time", ""),
                                "sentiment": res.get("sentiment", "Neutral"),
                                "ai_summary": res.get("ai_summary", "")
                            })
                    except Exception:
                        pass
                        
        return {
            "messages": new_messages,
            "tools_called": tools_called,
            "form_draft": form_draft
        }

    def should_continue(state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    # Build the StateGraph
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", execute_tools_node)
    
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()

# Singleton graph instance
compiled_graph = build_agent_graph()

def interact_with_agent(message: str, history: List[Dict[str, str]], form_draft: Dict[str, Any]) -> Dict[str, Any]:
    """
    High-level API to converse with the LangGraph agent.
    Converts history, invokes the Compiled StateGraph, and returns the response.
    """
    # 1. Reconstruct message objects
    msg_objects = []
    for msg in history:
        if msg["role"] == "user":
            msg_objects.append(HumanMessage(content=msg["content"]))
        else:
            msg_objects.append(AIMessage(content=msg["content"]))
            
    # Add new user message
    msg_objects.append(HumanMessage(content=message))
    
    # 2. Invoke Graph
    initial_state = {
        "messages": msg_objects,
        "form_draft": form_draft or {},
        "tools_called": [],
        "current_hcp_id": None,
        "response": ""
    }
    
    try:
        final_state = compiled_graph.invoke(initial_state)
        
        # 3. Format result
        last_msg = final_state["messages"][-1]
        reply_content = last_msg.content if hasattr(last_msg, "content") else final_state.get("response", "")
        
        return {
            "reply": reply_content,
            "form_draft": final_state.get("form_draft", form_draft),
            "tools_called": final_state.get("tools_called", [])
        }
    except Exception as e:
        logger.error(f"Error executing agent graph: {e}")
        # Fallback to simulated execution if execution fails
        sim_res = simulate_agent_nlp(message, form_draft)
        return {
            "reply": f"*(Simulated)* {sim_res['reply']}",
            "form_draft": sim_res["form_draft"],
            "tools_called": sim_res["tools_called"]
        }
