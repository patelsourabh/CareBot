**README.md**

---

# HealthBot – Intelligent Healthcare Assistant

**HealthBot** is a next-gen AI-powered health assistant designed for quick, accessible, and personalized symptom assessment and relief suggestions—especially helpful for users with limited access to medical knowledge or digital literacy. It combines modular AI agents, memory logging, escalation protocols, and even WhatsApp alerts to enhance healthcare accessibility.

---

## 🚀 Why HealthBot?

* **Accessible AI Healthcare**: Enables even digitally unaware users (like the elderly) to access medical suggestions using **voice interface**.
* **Smart Escalation**: Tracks **symptom trends** and triggers **WhatsApp alerts to caregivers** in case of emergencies.
* **All-in-One Workflow**: Central AI Intent Classifier decides the most appropriate agent to handle the user's request.
* **Offline Memory Logging**: Keeps a log of historical interactions to identify recurring issues.
* **Multi-Modal Remedy Suggestions**: Combines home remedies, physical exercises, hospitals info, medicine information, search-based guidance and general health and lifestyle queries.

---

## 🌟 Unique Features

| Feature                          | Description                                                                                                                                |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| 🩺 Symptom Analyzer              | Identifies probable conditions via OpenAI's model.                                                                                         |
| 🧘 Home Remedy & Physical Relief | Gives safe natural remedies and stretch/exercise suggestions.                                                                              |
| 🧠 Memory Engine                 | Logs previous symptoms to detect patterns.                                                                                                 |
| 🔍 Trusted Info Agent            | Fetches trustworthy online information.                                                                                                    |
| 📞 Emergency Escalation Agent    | Sends **WhatsApp alert** using **Twilio** when repeated critical symptoms are detected or any emergency symptom deteted like Heart Attack. |
| 🧑‍⚕️ Medical Triage Logic       | Advises when to consult professionals.                                                                                                     |
| 🗣️ Voice-first Access           | Great for **non-tech-savvy users** or elders.                                                                                              |

---

## 🧠 Problem It Solves

* Many people **self-diagnose wrongly** or delay treatment.
* **Elderly users struggle** with app-based healthcare solutions.
* Lack of centralized memory leads to **missed patterns** in symptoms.
* Users often **don’t know when a symptom is serious**.
* In emergencies, **no auto-escalation** or alert mechanism exists.

**HealthBot** solves these via:

* AI-driven analysis
* Workflow agent management
* Memory logging
* WhatsApp alerts
* Intent classification

---

## Tech Stack

* **Language**: Python 3.10+
* **Frameworks/Libraries**:

  * FastAPI (API server)
  * OpenAI Python SDK (chat/completion)
  * LangGraph (agent orchestration)
  * SQLAlchemy / psycopg2 (DB access)
* **Databases**:

  * SQLite (local development)
  * PostgreSQL (production)

## 🧩 Project Structure

```
CareBot/
├── app.py                  # FastAPI app loader
├── main.py                 
├── requirements.txt        # Dependencies
├── healthbot.db            # SQLite DB
├── .env                    # API and cloud postgres credentials (exclude from Git)
│
├── agents/                 # AI agents directory
│   ├── supervisor_agent.py
│   ├── symptom_agent.py
│   ├── intent_classifier_agent.py
│   ├── emergency_alert_agent.py
│   ├── home_remedy_agent.py
│   ├── physical_relief_agent.py
│   ├── info_search_agent.py
│   ├── general_medical_agent.py
│   ├── final_summary_agent.py
│   ├── memory_writer_agent.py
│   └── memory_reader_agent.py
├── workflows/            # Workflow orchestration logic
    │   └── workflow.py
    ├── api/                  # REST API routes
    │   └── routes.py
    ├── db/                   # Database adapters
    │   └── postgres_adapter.py
    └── shared/               # Shared type definitions
        └── types.py
```

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/patelsourabh/CareBot.git
cd CareBot
```

### 2. Create & Activate Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate.ps1
```

### 3. Install Requirements

```bash
pip install -r requirements.txt
```

### 4. Setup `.env` File

Create a `.env` file in the root directory with:

```env
TAVILY_API_KEY=your_tavily_api_key_here
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth
TWILIO_WHATSAPP_FROM=whatsapp:+14XXXXXXXXX
EMERGENCY_CONTACT=whatsapp:+91706784XXXX
POSTGRES_URL=postgresql://postgres:
OPENROUTER_API_KEY=

```

### 5. Where to Get These:
* **OPEN ROUTER API**: from (https://openrouter.ai/), signup and get your api key from settings.
* **PostgreSQL Cloud DB**: Use  [Supabase](https://supabase.io).
* **Twilio Setup**:

  * Create account: [https://www.twilio.com/](https://www.twilio.com/)
  * Verify number.
  * Buy a Twilio number with WhatsApp capability.
  * Enable WhatsApp sandbox in Twilio Dashboard.

### 6. Run Server

```bash
uvicorn app:app --reload
```

Server will run at `http://localhost:8000`

### 7. Run Streamlit

```bash
streamlit run app.py
```

You can now view your Streamlit app in your browser.

      Local URL: http\://localhost:8501

---

## 📲 API Overview

| Endpoint           | Method | Description                                     |
| ------------------ | ------ | ----------------------------------------------- |
| `/analyze`         | POST   | Accepts symptom input, starts analysis pipeline |
| `/remedy/home`     | POST   | Suggests home treatments                        |
| `/remedy/physical` | POST   | Suggests exercises, stretches                   |
| `/search/info`     | GET    | Fetches medical info                            |
| `/alert/whatsapp`  | POST   | Sends emergency message to WhatsApp             |

---

