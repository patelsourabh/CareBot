from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from shared.types import HealthBotState

llm = ChatOpenAI(model="gpt-4", temperature=0.5)

def general_medical_agent(state: HealthBotState) -> HealthBotState:
    query = state["messages"][-1].content.strip()
    if not query:
        # ❌ overwrite-free update into results:
        outputs = dict(state.get("agent_outputs", {}))
        outputs["general_medical"] = "⚠️ I didn't receive any clear question to respond to."
        state["agent_outputs"] = outputs

        return state

    prompt = f"""You are a general medical assistant. 
Answer the following user query in a helpful, responsible, and medically informed way. 
Keep the language simple. Mention that this does not replace a professional doctor's consultation.

User: {query}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    outputs = dict(state.get("agent_outputs", {}))
    outputs["general_medical"] = response.content.strip()
    state["agent_outputs"] = outputs

    return state
