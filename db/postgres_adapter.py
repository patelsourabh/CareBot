#postgres_adapter.py
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from typing import List, Dict
from shared.types import HealthBotState

load_dotenv()
Base = declarative_base()

# Load DB URL from env
engine = create_engine(os.getenv("POSTGRES_URL"))
SessionLocal = sessionmaker(bind=engine)

# Table Definition
class SymptomLog(Base):
    __tablename__ = "symptom_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String)
    query = Column(Text)
    symptoms = Column(Text)
    stress_level = Column(String)
    risk_score = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    final_response = Column(Text)

class ConversationLog(Base):
    __tablename__ = "conversation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    message = Column(Text)             # user query
    intents = Column(Text)             # classified intent
    results = Column(Text)             # output summary/agent result
    timestamp = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)

# Logging
def log_symptom_interaction(state: HealthBotState):
    session = SessionLocal()
    log = SymptomLog(
        user_id=state["user_id"],
        query=state["messages"][-1].content,
        symptoms=", ".join(state.get("symptoms") or []),
        stress_level=state.get("stress_level"),
        risk_score=state.get("risk_score"),
        timestamp=datetime.fromisoformat(state["timestamp"]),
        final_response=state.get("response_message")
    )
    session.add(log)
    session.commit()
    session.close()

def get_relevant_memory_chunks(user_id: str, latest_question: str) -> list:
    
    return [
        f"Past message by {user_id} related to '{latest_question}'",
        f"Memory: You once asked about something similar."
    ]


def store_conversation(entry: dict):
    session = SessionLocal()

    log = ConversationLog(
        user_id=entry.get("user_id"),
        message=entry.get("inputs", {}).get("message", ""),
        intents=", ".join(entry.get("intents", [])) if entry.get("intents") else "",
        results=str(entry.get("results", {})),
        timestamp=datetime.utcnow()
    )

    session.add(log)
    session.commit()
    session.close()


def get_recent_messages(user_id: str, limit: int = 5) -> List[str]:
    session = SessionLocal()
    logs = session.query(SymptomLog).filter(
        SymptomLog.user_id == user_id
    ).order_by(SymptomLog.timestamp.desc()).limit(limit).all()
    session.close()
    return [log.query for log in logs[::-1]]  # Return in forward order

# For Streamlit UI 
def get_message_history_ui(user_id: str, limit: int = 10) -> List[dict]:
    session = SessionLocal()
    logs = session.query(SymptomLog).filter(
        SymptomLog.user_id == user_id
    ).order_by(SymptomLog.timestamp.desc()).limit(limit).all()
    session.close()
    return [{
        "symptoms": log.symptoms,
        "response": log.final_response,
        "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M") if log.timestamp else "N/A"
    } for log in logs[::-1]]

# Frequency
def get_symptom_frequencies(user_id: str, symptoms: List[str], days: int = 7) -> Dict[str, int]:
    session = SessionLocal()
    freq_map = {}
    recent_time = datetime.utcnow() - timedelta(days=days)

    for symptom in symptoms:
        count = session.query(SymptomLog).filter(
            SymptomLog.user_id == user_id,
            SymptomLog.symptoms.ilike(f"%{symptom}%"),
            SymptomLog.timestamp >= recent_time
        ).count()
        freq_map[symptom] = count

    session.close()
    return freq_map



def db_handler_node(state: HealthBotState) -> HealthBotState:
    from datetime import datetime
    #if not state.get("timestamp"):
        #state["timestamp"] = datetime.utcnow().isoformat()

    freq_map = get_symptom_frequencies(state["user_id"], state.get("symptoms", []))

    if any(count >= 3 for count in freq_map.values()):
        #state["risk_score"] = max(state.get("risk_score", 0.0), 0.9)
        state["response_message"] += " ⚠️ This symptom has occurred frequently. Please consult a doctor."

    log_symptom_interaction(state)
    return state

