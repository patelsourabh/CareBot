# tests/test_full_workflow.py
from datetime import datetime, timezone
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from workflows.workflow import build_healthbot_workflow
from shared.types import HealthBotState
from langchain_core.messages import HumanMessage
from datetime import datetime
import uuid

def test_full_workflow():
    # 🔐 Generate a unique user_id
    user_id = "user_6"

    # 💬 Simulated message from user
    user_message = HumanMessage(content="what ymptoms i am experincing , previosuly?")
    #"hello,which medicines you have suggested me previously for my health condition?"

    # 🧠 Construct the initial state
    initial_state = HealthBotState(
        user_id=user_id,
        messages=[user_message],
        symptoms=None,
        stress_level=None,
        risk_score=None,
        timestamp=datetime.now(timezone.utc).isoformat(),
        response_message="",
        alert_sent=False,
        location="Delhi",  # Needed for hospital info search
        suspected_diseases=[],
        recommended_path=None,
        _info_mode=None,
        _search_topic=None,
        _search_results=[]
    )

    # ⚙️ Build and invoke LangGraph workflow
    workflow = build_healthbot_workflow()
    final_state = workflow.invoke(initial_state)

    # ✅ Results
    print("\n=== TEST RESULT ===")
    print(f"User ID: {final_state['user_id']}")
    print(f"Symptoms: {final_state['symptoms']}")
    print(f"Stress Level: {final_state['stress_level']}")
    print(f"Risk Score: {final_state['risk_score']}")
    print(f"Alert Sent: {final_state['alert_sent']}")
    print(f"Suspected Disease(s): {final_state.get('suspected_diseases')}")
    print(f"\nFinal Response Message:\n{final_state['response_message']}")
    print("====================")

# Run when executed directly
if __name__ == "__main__":
    test_full_workflow()
