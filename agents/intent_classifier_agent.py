# agents/intent_classifier_agent.py

from shared.types import HealthBotState
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.messages.ai import AIMessage

llm = ChatOpenAI(model="gpt-4", temperature=0)

def intent_classifier_agent(state: dict) -> dict:
    messages = state.get("messages", [])
    last_msg = ""

    
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_msg = msg.content
            break
        elif isinstance(msg, dict) and msg.get("type") == "human":
            last_msg = msg.get("content", "")
            break

    prompt = prompt = f"""
You are an intent classifier in a medical chatbot. Your role is to analyze the user's query and classify all applicable intents based on the context and meaning of the text.

Query: "{last_msg}"

Classify the intent(s) into one or more of the following categories:
- home_remedy: Queries about managing symptoms or conditions at home (e.g., pain relief, minor injuries, or home treatments).
- physical_relief: Queries related to stress relief, sleep improvement, or physical wellness practices (e.g., yoga, breathing exercises).
- info_search: Queries seeking information about healthcare services or resources (e.g., hospitals, clinics, medicine availability, or operating hours).
- general_medical: Queries about medical education, exercises, lifestyle, or other medical topics that don't fit the above categories (e.g., questions about diseases, preventive care, or general health advice).

Focus on the semantic meaning of the query rather than specific keywords. If the query contains multiple intents (e.g., symptoms and hospital information), return all relevant labels. If symptoms (e.g., pain, fever, stress) are mentioned, prioritize home_remedy or physical_relief based on context, but also include other applicable intents. Return a comma-separated list of all applicable intent labels (e.g., "home_remedy,info_search"). If only one intent applies, return a single label.
""".strip()

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        predicted_intent = response.content.strip()
        print("[Intent Classifier] Predicted:", predicted_intent)

        state["intents"] = [i.strip() for i in predicted_intent.split(",") if i.strip()]
    except Exception as e:
        print(f"[Intent Classifier Error] {e}")
        state["intents"] = ["fallback"]

    print("**[IntentClassifier] Final intents:", state.get("intents"))


    return state
