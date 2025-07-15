from langchain_core.messages import HumanMessage
from shared.types import HealthBotState
from dotenv import load_dotenv
import os
from langchain_community.chat_models import ChatOpenAI

load_dotenv()

llm = ChatOpenAI(
    model="mistralai/mistral-7b-instruct",  # or any OpenRouter model
    openai_api_key=os.environ["OPENROUTER_API_KEY"],
    openai_api_base="https://openrouter.ai/api/v1"
)
def general_medical_agent(state: HealthBotState) -> HealthBotState:
    query = state["messages"][-1].content.strip()
    if not query:
        
        outputs = dict(state.get("agent_outputs", {}))
        outputs["general_medical"] = "**I didn't receive any clear question to respond to."
        state["agent_outputs"] = outputs

        return state

    prompt = f"""You are a general medical assistant in India.
Answer the following user query in a helpful, responsible, and medically informed way. 
Keep the language simple.
User: {query}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    outputs = dict(state.get("agent_outputs", {}))
    outputs["general_medical"] = response.content.strip()
    state["agent_outputs"] = outputs

    return state
