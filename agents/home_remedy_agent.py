# agents/home_remedy_agent.py

from shared.types import HealthBotState
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from db.postgres_adapter import log_symptom_interaction
from datetime import datetime
import os
from langchain_community.chat_models import ChatOpenAI

load_dotenv()

llm = ChatOpenAI(
    model="mistralai/mistral-7b-instruct", 
    openai_api_key=os.environ["OPENROUTER_API_KEY"],
    openai_api_base="https://openrouter.ai/api/v1"
)

def home_remedy_agent(state: HealthBotState) -> HealthBotState:
    symptoms = state.get("symptoms", [])
    response_lines = []

    # Remedy home
    remedy_system_prompt = (
        "You are a cautious medical assistant. Your task is to:\n"
        "1. Identify 1–2 suspected Disease(s) based on the user's symptoms.\n"
        "2. Provide a remedies per major symptom.\n"
        "3. Format exactly as:\n"
        "Suspected Disease(s):\n- Disease1\n- Disease2\n\n"
        "Remedies:\n1. Remedy1\n2. Remedy2\n3. Remedy3\n\n"
    )
    remedy_response = llm.invoke([
        SystemMessage(content=remedy_system_prompt),
        HumanMessage(content=f"Symptoms: {', '.join(symptoms)}")
    ])
    remedies_text = remedy_response.content.strip()
    response_lines.append(remedies_text)

    
    suspected_diseases = []
    lines = remedies_text.splitlines()
    in_disease_section = False
    for line in lines:
        if line.strip().lower().startswith("suspected disease"):
            in_disease_section = True
            continue
        if line.strip().lower().startswith("remedies:"):
            break
        if in_disease_section and line.strip().startswith("-"):
            suspected_diseases.append(line.strip().lstrip('-').strip())
    state["suspected_diseases"] = suspected_diseases or []

    # Final output
    state["response_message"] = "\n\n".join(response_lines).strip()
    print("[Home Remedy] Final response:", state["response_message"])
    outputs = dict(state.get("agent_outputs", {}))
    outputs["home_remedy"] = remedies_text
    state["agent_outputs"] = outputs


    # if not state.get("timestamp"):
    #     state["timestamp"] = datetime.utcnow().isoformat()

    #log_symptom_interaction(state)
    return state
