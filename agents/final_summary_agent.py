from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from shared.types import HealthBotState

llm = ChatOpenAI(model="gpt-4", temperature=0.5)

def final_summary_agent(state: HealthBotState) -> HealthBotState:
    current_results = state.get("agent_outputs", {})
    print("🧠 [final_summary_agent] incoming agent_outputs:", current_results.keys())
    memory = state.memory if hasattr(state, "memory") else []

    # Format past memory
    memory_text = "\n".join(
        f"- {entry.get('inputs', {}).get('message', '')} → {entry.get('results', {})}" 
        for entry in memory
    ) or "No past history."

    # Format current results
    current_text = "\n".join(
        f"- {k}: {v}" for k, v in current_results.items()
    ) or "No current results."

    print("✅ Available results before summarizing:", state.get("agent_outputs", {}).keys())

    prompt = prompt = f"""
You are a medical assistant in a chatbot powered by a multi-agent system. Your role is to process the current results from called agents, integrate past memory to identify symptom patterns or prior improvements, and provide medically responsible suggestions based solely on the defined agents' outputs. The response should be friendly, informative, and personalized, referencing the user's history.

### Current Results:
{current_text}
- For each agent called (e.g., home_remedy, info_search, physical_relief, general_medical), list exactly two key points from its response, verbatim, without modification.
- For home_remedy, include the suspected disease based on the symptoms provided in the agent's response.
- If medicines are explicitly mentioned in the query or agent response (e.g., home_remedy or general_medical), list two medicines under a separate 'Medicines' heading.
- if any information serach results are available, include them under the 'Info Search' heading(e.g., clinics).
- if information not lies in home_remedy, info_search, or physical_relief, include it under the 'General Medical' heading. and include it in your summary.

### Past Memory (latest 10 messages):
{memory_text}
- Identify patterns in symptoms (e.g., 'chest pain mentioned 3 times this week' may suggest heart attack risk; 'dizziness reported multiple times' may indicate iron deficiency).
- Reference prior improvements (e.g., 'your back pain improved last time') or recurring issues to provide context.
- Incorporate relevant user history (e.g., prior queries about symptoms or health bot development) to personalize the response.

### Instructions:
1. Format the response in a point-wise structure with clear headings for each agent (e.g., 'Home Remedies', 'Info Search') listing exactly two verbatim points from the agent's response.
2. For home_remedy, append the suspected disease as a third point under the 'Home Remedies' heading.
3. If medicines are mentioned in the query or agent response, include a 'Medicines' heading with exactly two medicines from the response, verbatim.
4. Provide a short summary (1–2 sentences) under a 'Summary' heading, combining the overall intent of the agent responses without adding new points.
5. Keep the tone friendly, professional, and empathetic, ensuring privacy and encouraging medical consultation for serious symptoms.

Reply with a point-wise, concise paragraph (120 - 200 words) using headings for each agent, medicines (if applicable), summary, and memory insights.
""".strip()

    response = llm.invoke([HumanMessage(content=prompt)])
    state.setdefault("agent_outputs", {})["final_summary"] = response.content.strip()
    print("✅ Final summary stored:", response.content.strip()[:300])

    return state
