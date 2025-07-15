#postgres_adapter.py
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
from typing import List, Dict
from shared.types import HealthBotState

load_dotenv()

print("&&&&&[DB DEBUG] using POSTGRES_URL:", os.getenv("POSTGRES_URL"))

Base = declarative_base()


engine = create_engine(os.getenv("POSTGRES_URL"))
SessionLocal = sessionmaker(bind=engine)

# Table
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
    message = Column(Text)             
    intents = Column(Text)             
    results = Column(Text)             
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
        timestamp=datetime.now(timezone.utc),
        final_response=state.get("response_message")
    )
    session.add(log)
    session.commit()
    session.close()


def store_conversation(entry: dict):
    session = SessionLocal()
    log = ConversationLog(
        user_id=entry.get("user_id"),
        message=entry.get("inputs", {}).get("message", ""),
        intents=", ".join(entry.get("intents", [])) if entry.get("intents") else "",
        results=entry.get("results", {}).get("response", ""),
        timestamp=datetime.now(timezone.utc),
    )
    session.add(log)
    session.commit()
    session.close()

def get_memory_pairs(user_id: str, limit: int = 5) -> List[dict]:
    session = SessionLocal()
    logs = (
        session.query(ConversationLog)
        .filter(ConversationLog.user_id == user_id)
        .order_by(ConversationLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    session.close()

    results = []
    for log in logs[::-1]: 
        user_msg = log.message or "..."
        ai_msg = log.results or "..."
        results.append({"user": user_msg.strip(), "ai": ai_msg.strip()})
    return results



def get_recent_messages(user_id: str, limit: int = 5) -> List[str]:
    session = SessionLocal()
    logs = session.query(SymptomLog).filter(
        SymptomLog.user_id == user_id
    ).order_by(SymptomLog.timestamp.desc()).limit(limit).all()
    session.close()
    return [log.query for log in logs] 

# For Streamlit UI 
def get_message_history_ui(user_id: str, limit: int = 10) -> List[dict]:
    session = SessionLocal()
    logs = (
      session
      .query(SymptomLog)
      .filter(SymptomLog.user_id == user_id)
      .order_by(SymptomLog.timestamp.desc())  
      .limit(limit)
      .all()
    )
    session.close()

   
    return [{
        "symptoms":  log.symptoms,
        "response":  log.final_response,
        "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M UTC")
    } for log in logs]



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
    import os
    from datetime import datetime
    print("&&&&&[DB DEBUG] db_handler_node invoked")
    print("&&&&&[DB DEBUG] POSTGRES_URL:", os.getenv("POSTGRES_URL"))
    print(f"&&&&&[DB DEBUG] incoming state.timestamp = {state.get('timestamp')}")

    #timestamp
    if not state.get("timestamp"):
        state["timestamp"] = datetime.utcnow().isoformat()
        print(f"&&&&&[DB DEBUG] timestamp was missing, set to {state['timestamp']}")

    # frequency 
    freq_map = get_symptom_frequencies(state["user_id"], state.get("symptoms", []))
    if any(c >= 3 for c in freq_map.values()):
        state["response_message"] += "  This symptom has occurred frequently. Please consult a doctor."
        print("&&&&&[DB DEBUG] emergency appended for", freq_map)

    # now log
    print(f"&&&&&[DB DEBUG] calling log_symptom_interaction(...)")
    log_symptom_interaction(state)
    print("&&&&&[DB DEBUG] log_symptom_interaction returned")
    return state

