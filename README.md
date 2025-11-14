# College Chatbot (MVP)

This is a minimal Flask-based College Chatbot MVP implementing core features requested: information retrieval, context awareness, dynamic responses from data files, sentiment-aware replies, admin logging, and a simple web UI.

Overview
- Flask server at `app.py` serves a single-page chat UI and an API at `/api/chat`.
- Data is loaded from JSON files in `data/` (college_info.json, courses.json, faculty.json, events.json).
- Logs are stored in `chat_logs.db` (SQLite).

Quick start (Windows PowerShell):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r college_chatbot/requirements.txt
cd college_chatbot
$env:FLASK_APP = 'app.py'; $env:FLASK_ENV='development'
flask run --host=127.0.0.1 --port=5000
```

Open http://127.0.0.1:5000 in a browser. The chat UI supports typed chat and basic voice input using the browser Web Speech API.

Notes & next steps
- Add admin dashboard for analytics (frequent queries, failure queries).
- Improve NLP with transformer embeddings or Rasa for richer language understanding.
- Add server-side TTS/audio streaming for environments without Web Speech API.
