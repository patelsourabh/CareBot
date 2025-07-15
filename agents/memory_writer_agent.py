from db.postgres_adapter import store_conversation
from langchain_core.prompts import PromptTemplate
from langchain_community.chat_models import ChatOpenAI
import os


summarizer_llm = ChatOpenAI(
    model="mistralai/mistral-7b-instruct",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1"
)

# Short summary 
summary_prompt = PromptTemplate.from_template(
    "Summarize this AI response in 2-3 lines, keeping only important insights , so that it can be used for future diagnostics by providing this past record:\n\n{response}"
)


def memory_writer_agent(state: dict) -> dict:
    user_id = state.get("user_id", "unknown_user")

    # most recent user message
    user_messages = [m.content for m in state.get("messages", []) if m.type == "human"]
    if not user_messages:
        return state
    latest_user_message = user_messages[-1]

    #  AI response
    ai_response = state.get("agent_outputs", {}).get("final_summary", "")

    # Summarise the AI response
    try:
        short_summary = summary_prompt | summarizer_llm | (lambda x: x.content.strip())
        compressed_response = short_summary.invoke({"response": ai_response})
    except Exception as e:
        print(f"[Summarization Error] Using full response. Error: {e}")
        compressed_response = ai_response

    # Save to DB
    entry = {
        "user_id": user_id,
        "inputs": {"message": latest_user_message},
        "results": {"response": compressed_response},
        "intents": state.get("intents", [])
    }

    try:
        store_conversation(entry)
        print(f"&&& Compressed memory stored for {user_id}")
    except Exception as e:
        print(f"[Memory Write Error] {e}")

    return state
