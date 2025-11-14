import json
from flask import Flask
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from college_chatbot import app as chatbot_app

def test_index_route():
    client = chatbot_app.test_client()
    r = client.get('/')
    assert r.status_code == 200

def test_chat_empty():
    client = chatbot_app.test_client()
    r = client.post('/api/chat', json={'message': ''})
    assert r.status_code == 400

def test_chat_basic():
    client = chatbot_app.test_client()
    r = client.post('/api/chat', json={'message': 'What are the college timings?'})
    assert r.status_code == 200
    data = r.get_json()
    assert 'reply' in data
