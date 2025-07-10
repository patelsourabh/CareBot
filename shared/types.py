from typing import Annotated, TypedDict, List, Optional, Dict, Any
from langgraph.graph import add_messages
import operator

def keep_first(a, b):
    return a if a else b




class HealthBotState(TypedDict, total=False):
    messages: Annotated[List, add_messages]
    agent_outputs: Annotated[dict, operator.or_]
    intents: Annotated[List[str], operator.add]
    user_id: Annotated[str, keep_first]
    symptoms: Annotated[list[str], keep_first]
    stress_level: Annotated[Optional[str], keep_first]  # Optional, can be empty string
    risk_score: Annotated[Optional[float], keep_first]  # Optional, can be None or float
    response_message: Annotated[Optional[str],keep_first]  # Optional, can be None or string
    timestamp: Annotated[Optional[str], keep_first]  # Optional, can be None or ISO format string
    recommended_path: Annotated[Optional[str], keep_first]  # Optional, can be None or string
    alert_sent: Annotated[bool,keep_first]              # <-- NEW
    location: Annotated[str, keep_first]  # Default location, can be empty string
    suspected_diseases: Annotated[List[str], operator.add]
   
    # For internal control
    _info_mode: Annotated[str,keep_first]  # "medicine", "hospital", or None
    _search_topic: Annotated[Optional[str], keep_first]  # 🆕 For search topic
    _search_results: Annotated[List[Dict], operator.add]
    session_id: Annotated[str,keep_first]  # 🆕 For multi-session support
    memory_context: Annotated[List[str], operator.add]  # 🆕 For conversation memory
