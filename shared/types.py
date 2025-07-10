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
    stress_level: Annotated[Optional[str], keep_first]  
    risk_score: Annotated[Optional[float], keep_first]  
    response_message: Annotated[Optional[str],keep_first]  
    timestamp: Annotated[Optional[str], keep_first]  
    recommended_path: Annotated[Optional[str], keep_first] 
    alert_sent: Annotated[bool,keep_first] 
    location: Annotated[str, keep_first]  
    suspected_diseases: Annotated[List[str], operator.add]
   
    
    _info_mode: Annotated[str,keep_first]  
    _search_topic: Annotated[Optional[str], keep_first]  
    _search_results: Annotated[List[Dict], operator.add]
    session_id: Annotated[str,keep_first] 
    memory_context: Annotated[List[str], operator.add]  
