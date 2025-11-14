import json
import sqlite3
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, send_file
import tempfile
import pyttsx3
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import sys
sys.path.append(os.path.dirname(__file__))
from src.chatbot import Chatbot

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, 'data')

def load_json(fname):
    with open(os.path.join(DATA_DIR, fname), 'r', encoding='utf-8') as f:
        return json.load(f)

college = load_json('college_info.json')
courses = load_json('courses.json')
faculty = load_json('faculty.json')
events = load_json('events.json')

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret-key')

DB_PATH = os.path.join(BASE_DIR, 'chat_logs.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT,
        user_msg TEXT,
        bot_resp TEXT,
        sentiment REAL,
        intent TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

analyzer = SentimentIntensityAnalyzer()

# Initialize NLP chatbot
print("Loading NLP chatbot...")
chatbot = Chatbot()
print("✓ Chatbot ready!")

def log_chat(user_msg, bot_resp, sentiment, intent=''):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO logs (ts, user_msg, bot_resp, sentiment, intent) VALUES (?, ?, ?, ?, ?)',
              (datetime.utcnow().isoformat(), user_msg, bot_resp, sentiment, intent))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        payload = request.get_json() or {}
        msg = payload.get('message', '').strip()
        if not msg:
            return jsonify({'error': 'empty message'}), 400

        # Get response from NLP chatbot
        reply = chatbot.get_response(msg)
        
        # Get intent from context
        intent = ''
        if chatbot.context:
            intent = chatbot.context[-1].get('intent', '')

        # Calculate sentiment
        sentiment = analyzer.polarity_scores(msg)['compound']

        # Tone adjustment based on sentiment
        if sentiment < -0.5:
            reply = "I can see you're upset. " + reply
        elif sentiment > 0.5:
            reply = "Glad to hear that! " + reply

        # Log chat
        log_chat(msg, reply, sentiment, intent)

        return jsonify({
            'reply': reply, 
            'sentiment': sentiment, 
            'intent': intent,
            'context_len': len(chatbot.context)
        })
    except Exception as e:
        print(f"ERROR in /api/chat: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/tts', methods=['POST'])
def tts():
    payload = request.get_json() or {}
    text = payload.get('text', '').strip()
    if not text:
        return jsonify({'error': 'empty text'}), 400

    # create a temporary WAV file and synthesize speech
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    tmp_path = tmp.name
    tmp.close()

    engine = pyttsx3.init()
    engine.save_to_file(text, tmp_path)
    engine.runAndWait()

    return send_file(tmp_path, mimetype='audio/wav')

@app.route('/admin/analytics')
def analytics():
    # quick analytics: top 50 most recent logs and average sentiment
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT user_msg, bot_resp, sentiment, intent, ts FROM logs ORDER BY id DESC LIMIT 50')
    rows = c.fetchall()
    c.execute('SELECT AVG(sentiment) FROM logs')
    avg = c.fetchone()[0]
    
    # Get intent distribution
    c.execute('SELECT intent, COUNT(*) as count FROM logs WHERE intent != "" GROUP BY intent ORDER BY count DESC LIMIT 10')
    intent_stats = c.fetchall()
    
    conn.close()
    return jsonify({
        'recent': [{'user': r[0], 'bot': r[1], 'sentiment': r[2], 'intent': r[3], 'ts': r[4]} for r in rows], 
        'avg_sentiment': avg,
        'top_intents': [{'intent': i[0], 'count': i[1]} for i in intent_stats]
    })

if __name__ == '__main__':
    app.run(debug=True)
