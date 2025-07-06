import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict
from langchain_core.messages import HumanMessage
from shared.types import HealthBotState# shared type

conn = sqlite3.connect("healthbot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS symptom_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    query TEXT,
    symptoms TEXT,
    stress_level TEXT,
    risk_score REAL,
    timestamp TEXT,
    final_response TEXT
)
""")
conn.commit()


def log_symptom_interaction(state: HealthBotState):
    cursor.execute("""
    INSERT INTO symptom_logs (user_id, query, symptoms, stress_level, risk_score, timestamp, final_response)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        state["user_id"],
        state["messages"][-1].content,
        ", ".join(state.get("symptoms") or []),
        state.get("stress_level"),
        state.get("risk_score"),
        state.get("timestamp"),
        state.get("response_message"),
    ))
    conn.commit()


def get_symptom_frequencies(user_id: str, symptoms: List[str], days: int = 7) -> Dict[str, int]:
    recent_window = (datetime.utcnow() - timedelta(days=days)).isoformat()
    freq_map = {}

    for symptom in symptoms:
        cursor.execute("""
        SELECT COUNT(*) FROM symptom_logs
        WHERE user_id=? AND symptoms LIKE ? AND timestamp >= ?
        """, (
            user_id,
            f"%{symptom}%",
            recent_window
        ))
        count = cursor.fetchone()[0]
        freq_map[symptom] = count

    return freq_map


# LangGraph Node
def db_handler_node(state: HealthBotState) -> HealthBotState:
    from datetime import datetime
    if not state.get("timestamp"):
        state["timestamp"] = datetime.utcnow().isoformat()

    freq_map = get_symptom_frequencies(state["user_id"], state.get("symptoms", []))

    if any(count >= 3 for count in freq_map.values()):
        state["risk_score"] = max(state.get("risk_score", 0.0), 0.9)
        state["response_message"] += " ⚠️ This symptom has occurred frequently. Please consult a doctor."

    log_symptom_interaction(state)
    return state
