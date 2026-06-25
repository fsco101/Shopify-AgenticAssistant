"""
Shopify Agentic Assistant — Desktop Web UI
Uses pywebview to create a native floating window with the web-based chat interface.
Flask serves the API and static files in the background.
"""

import os
import uuid
import threading
import time
import re
import ctypes

from flask import Flask, send_from_directory, request, jsonify
import webview

import history_manager
import llm_router

# ------------------------------------------------------------------ App Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "chat_ui")

flask_app = Flask(__name__, static_folder=STATIC_DIR)

# In-memory session histories
active_sessions = {}


def strip_markdown(text):
    """Remove markdown formatting characters for clean display."""
    if not text:
        return text
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'(?<!\w)\*(.+?)\*(?!\w)', r'\1', text)
    text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\*\s+', '  •  ', text, flags=re.MULTILINE)
    return text


# ------------------------------------------------------------------ Flask Routes
@flask_app.route('/')
def index():
    return send_from_directory(STATIC_DIR, 'index.html')


@flask_app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)


@flask_app.route('/api/status')
def api_status():
    return jsonify({"db_connected": history_manager.is_db_connected()})


@flask_app.route('/api/sessions')
def api_sessions():
    sessions = history_manager.get_all_sessions()
    return jsonify({"sessions": sessions})


@flask_app.route('/api/session/new', methods=['POST'])
def api_new_session():
    session_id = str(uuid.uuid4())
    active_sessions[session_id] = []
    return jsonify({"session_id": session_id})


@flask_app.route('/api/session/<session_id>')
def api_get_session(session_id):
    messages = history_manager.get_session_messages(session_id)
    return jsonify({"session_id": session_id, "messages": messages})


@flask_app.route('/api/session/<session_id>', methods=['DELETE'])
def api_delete_session(session_id):
    history_manager.delete_session(session_id)
    active_sessions.pop(session_id, None)
    return jsonify({"status": "deleted"})


@flask_app.route('/api/send', methods=['POST'])
def api_send():
    data = request.get_json()
    session_id = data.get('session_id')
    user_message = data.get('message', '').strip()

    if not session_id or not user_message:
        return jsonify({"error": "session_id and message are required"}), 400

    if session_id in active_sessions:
        messages = active_sessions[session_id]
    else:
        messages = history_manager.get_session_messages(session_id)
        active_sessions[session_id] = messages

    history_manager.save_message(session_id, "user", user_message)
    messages.append({"role": "user", "content": user_message})

    try:
        response, messages = llm_router.process_agent_message(messages)
        active_sessions[session_id] = messages
        history_manager.save_full_session(session_id, messages)
    except Exception as e:
        response = f"Error processing with LLM: {str(e)}"
        history_manager.save_message(session_id, "assistant", response)

    clean_response = strip_markdown(response)
    return jsonify({"response": clean_response, "session_id": session_id})



# ------------------------------------------------------------------ Main
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  Shopify Agentic Assistant — Desktop UI")
    print("=" * 50 + "\n")

    # Start Flask in the background
    flask_thread = threading.Thread(
        target=lambda: flask_app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False),
        daemon=True
    )
    flask_thread.start()
    time.sleep(1)  # Wait for Flask to start

    # Main chat window (native desktop window)
    webview.create_window(
        'Shopify Agentic Assistant',
        'http://127.0.0.1:5000',
        width=960,
        height=680,
        min_size=(700, 500),
        on_top=True,
        text_select=True
    )

    webview.start()
