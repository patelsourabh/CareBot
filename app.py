import streamlit as st
import requests
import speech_recognition as sr
from gtts import gTTS
from tempfile import NamedTemporaryFile
import json
import threading
import time
import numpy as np
import sounddevice as sd
import whisper
from scipy.io.wavfile import write  # Only used once, imported here

model = whisper.load_model("base")  # Load once globally

st.set_page_config(page_title="HealthBot AI", page_icon="🩺", layout="wide")

#  Inject Custom CSS 
st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: 'Segoe UI', sans-serif;
    }
    .chat-container {
        background-color: #f0f2f6;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
    }
    .chat-bubble-user {
        background-color: #d1e7dd;
        padding: 12px;
        border-radius: 15px 15px 0px 15px;
        margin-left: auto;
        width: fit-content;
    }
    .chat-bubble-bot {
        background-color: #f8d7da;
        padding: 12px;
        border-radius: 15px 15px 15px 0px;
        width: fit-content;
    }
    .typing {
        display: inline-block;
        width: 1em;
        animation: blink 1s steps(1) infinite;
    }
    @keyframes blink {
        0%, 100% {opacity: 0;}
        50% {opacity: 1;}
    }
    </style>
""", unsafe_allow_html=True)

#  Session state init 
defaults = {
    "user_id": "",
    "location": "",
    "chat_started": False,
    "messages": [],
    "voice_thread_started": False,
    "last_audio_file": None
}
for key, default in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

#  STT with Google Speech Recognition 
def record_and_transcribe():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.toast("# Listening...", icon="🎙️")
        audio = recognizer.listen(source, timeout=10)
        try:
            text = recognizer.recognize_google(audio)
            st.toast(f" You said: {text}")
            return text
        except sr.UnknownValueError:
            st.error(" Could not understand audio.")
        except sr.RequestError as e:
            st.error(f" STT API error: {e}")
    return ""

#  TTS 
def speak_text(text):
    tts = gTTS(text=text, lang='en')
    with NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
        tts.save(tmpfile.name)
        st.session_state.last_audio_file = tmpfile.name

#  Chat History 
def fetch_user_history(user_id):
    try:
        res = requests.get(f"http://localhost:8000/history/{user_id}")
        if res.status_code == 200:
            return res.json()["history"]
    except Exception as e:
        st.error(f" Error fetching history: {e}")
    return []

#  Real-time voice loop 
def realtime_voice_loop():
    duration = 10
    samplerate = 16000

    while st.session_state.get("chat_started", False):
        try:
            st.session_state.messages.append(("System", "🎤 Listening..."))
            audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1)
            sd.wait()
            audio = np.squeeze(audio)

            with NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                write(tmp_wav.name, samplerate, audio)
                result = model.transcribe(tmp_wav.name, fp16=False, condition_on_previous_text=False)
                text = result["text"].strip()

            if text:
                st.session_state.messages.append(("You", text))
                try:
                    res = requests.post("http://localhost:8000/chat", json={
                        "user_id": st.session_state.user_id,
                        "message": text,
                        "location": st.session_state.location
                    })
                    if res.status_code == 200:
                        reply = res.json()["response"]
                        st.session_state.messages.append(("HealthBot", reply))
                        speak_text(reply)
                    else:
                        st.session_state.messages.append(("HealthBot", " No reply."))
                except Exception as e:
                    st.session_state.messages.append(("HealthBot", f" Error: {e}"))

        except Exception as e:
            st.session_state.messages.append(("System", f" Voice Error: {e}"))
        time.sleep(5)

# Sidebar UI
with st.sidebar:
    st.markdown("##  User Setup")
    st.session_state.user_id = st.text_input("User ID", value=st.session_state.user_id)
    st.session_state.location = st.text_input(" Location", value=st.session_state.location)
    if st.button("Start Chat"):
        st.session_state.chat_started = True
        st.session_state.voice_thread_started = False

# Main Title
st.markdown("##  HealthBot AI Assistant")
st.markdown("Talk with your smart **HealthBot** using **voice or text**.\nGet help with symptoms, suggestions, and remedies.")

# Chat Section 
if st.session_state.chat_started:
    if not st.session_state.voice_thread_started:
        threading.Thread(target=realtime_voice_loop, daemon=True).start()
        st.session_state.voice_thread_started = True

    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input(" Type your message", key="text_input")
    with col2:
        if st.button(" Speak Once"):
            user_input = record_and_transcribe()

    if user_input:
        st.session_state.messages.append(("You", user_input))
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.chat_message("assistant"):
            with st.spinner("# HealthBot is thinking..."):
                try:
                    res = requests.post("http://localhost:8000/chat", json={
                        "user_id": st.session_state.user_id,
                        "message": user_input,
                        "location": st.session_state.location
                    })
                    if res.status_code == 200:
                        reply = res.json()["response"]
                        st.session_state.messages.append(("HealthBot", reply))
                        speak_text(reply)
                        st.markdown(reply)
                    else:
                        reply = " No response received."
                        st.session_state.messages.append(("HealthBot", reply))
                        st.markdown(reply)
                except Exception as e:
                    reply = f" Error: {e}"
                    st.session_state.messages.append(("HealthBot", reply))
                    st.markdown(reply)

    # Chat Bubble Display
    st.markdown("----")
    st.markdown("###  Recent Conversation")
    for sender, msg in reversed(st.session_state.messages[-8:]):
        with st.chat_message("user" if sender == "You" else "assistant" if sender == "HealthBot" else "system"):
            st.markdown(msg)

    if st.session_state.last_audio_file:
        st.audio(st.session_state.last_audio_file, format="audio/mp3")

else:
    st.info(" Enter user info and click **Start Chat** to begin.")

#  History Viewer 
with st.expander(" View Previous Chat History"):
    history = fetch_user_history(st.session_state.user_id)
    if history:
        for i, entry in enumerate(history, 1):
            if isinstance(entry, str):
                try:
                    entry = json.loads(entry)
                except json.JSONDecodeError:
                    continue
            timestamp = entry.get("timestamp", "N/A")
            symptoms = entry.get("symptoms", "N/A")
            response = entry.get("response", "No response")

            st.markdown(f"**{i}.** 🕒 *{timestamp}*")
            st.markdown(f"- 🧍‍♂️ **Symptoms:** `{symptoms}`")
            st.markdown(f"- 🤖 **Response:** {response}")
            st.markdown("---")
    else:
        st.info("No history available.")
