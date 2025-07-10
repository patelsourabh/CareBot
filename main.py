#main.py
# main.py
from fastapi import FastAPI, Request
from api.routes import router
from fastapi.middleware.cors import CORSMiddleware
from db.postgres_adapter import get_recent_messages
from fastapi.middleware.cors import CORSMiddleware
from db.postgres_adapter import get_message_history_ui

app = FastAPI(title="HealthBot API")

# CORS (Optional: if using a frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/history/{user_id}")
def fetch_history(user_id: str):
    messages = get_message_history_ui(user_id, limit=10)
    return {"history": messages}

# Include routes
app.include_router(router)
