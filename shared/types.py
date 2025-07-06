from typing import Annotated, TypedDict, List, Optional
from langgraph.graph import add_messages

class HealthBotState(TypedDict):
    messages: Annotated[List, add_messages]
    user_id: str
    symptoms: Optional[List[str]]
    stress_level: Optional[str]
    risk_score: Optional[float]
    response_message: Optional[str]
    timestamp: Optional[str]
    recommended_path: Optional[str]
    alert_sent: Optional[bool]              # <-- NEW
    location: Optional[str] 
    suspected_diseases: Optional[List[str]]
    recommended_path: Optional[str]
    # For internal control
    _info_mode: Optional[str]  # "medicine", "hospital", or None
    _search_topic: Optional[str]
    _search_results: Optional[List[dict]]
