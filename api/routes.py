# api/routes.py
from fastapi import APIRouter, Request
from pydantic import BaseModel
from workflows.workflow import build_healthbot_workflow
from langchain_core.messages import HumanMessage
from uuid import uuid4
from datetime import datetime
from shared.types import HealthBotState
from db.postgres_adapter import get_recent_messages
router = APIRouter()

# Load the compiled LangGraph
graph = build_healthbot_workflow()

# Input model
class ChatRequest(BaseModel):
    user_id: str
    message: str
    location: str = "your city"

# Output model
class ChatResponse(BaseModel):
    response: str
    symptoms: list
    risk_score: float
    alert_sent: bool
    suspected_diseases: list
    recommended_path: str
    history: list[str]

@router.get("/history/{user_id}")
async def get_history(user_id: str):
    return {"history": get_recent_messages(user_id, limit=10)}    

@router.post("/chat", response_model=ChatResponse)
@router.post("/chat", response_model=ChatResponse)
async def chat_with_bot(request: ChatRequest):
    # ✅ Correctly initialized state with lists for Annotated[list, ...] fields
    state: HealthBotState = {
    "user_id": request.user_id,  # ✅ str, NOT list
    "messages": [HumanMessage(content=request.message)],
    "symptoms": [],  # ✅ list (Annotated[List[str]])
    "stress_level": "",  # ✅ string, NOT list
    "risk_score": 0.0,
    "response_message": "",
    "timestamp": datetime.utcnow().isoformat(),
    "location": request.location,
    "suspected_diseases": [],  # ✅ list (Annotated[List[str]])
    "alert_sent": False,
    "recommended_path": "",
    "_info_mode": None,
    "_search_topic": None,
    "_search_results": [],  # ✅ list of dicts
    "agent_outputs": {},  # ✅ dict
    "session_id": str(uuid4()),
    "memory_context": []  # ✅ list of str
    }


    final_state = graph.invoke(state)

    print("🧠 Returning summary response 1:", final_state.get("agent_outputs", {}).get("final_summary", "None"))

    

    return ChatResponse(
        response=final_state.get("agent_outputs", {}).get("final_summary", "Sorry, I couldn’t find a helpful summary."),
        symptoms=final_state.get("symptoms", []),
        risk_score=final_state.get("risk_score", 0.0) or 0.0,
        alert_sent=final_state.get("alert_sent", False),
        suspected_diseases=final_state.get("suspected_diseases", []),
        recommended_path=final_state.get("recommended_path", ""),
        history=final_state.get("memory_context", [])
    )


