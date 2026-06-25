import os
import json
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "shopify_agent_db")

# Optional fallback file
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_history.json")

# Initialize MongoDB client
try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
    # Test connection
    client.admin.command('ping')
    db = client[MONGODB_DB_NAME]
    collection = db["chat_sessions"]
    DB_CONNECTED = True
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    DB_CONNECTED = False

def is_db_connected():
    return DB_CONNECTED

def _load_history_local():
    if not os.path.exists(HISTORY_FILE):
        return {"sessions": {}}
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"sessions": {}}

def _save_history_local(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_all_sessions():
    """Returns a list of dicts sorted by updated_at descending"""
    if DB_CONNECTED:
        sessions = []
        for doc in collection.find({}, {"session_id": 1, "title": 1, "updated_at": 1}).sort("updated_at", -1):
            sessions.append({
                "session_id": doc.get("session_id"),
                "title": doc.get("title", "New Chat"),
                "updated_at": doc.get("updated_at", "")
            })
        return sessions
    else:
        # Fallback to local
        data = _load_history_local()
        sessions = []
        for sid, sdata in data.get("sessions", {}).items():
            sessions.append({
                "session_id": sid,
                "title": sdata.get("title", "New Chat"),
                "updated_at": sdata.get("updated_at", "")
            })
        return sorted(sessions, key=lambda x: x["updated_at"], reverse=True)

def get_session_messages(session_id):
    if DB_CONNECTED:
        doc = collection.find_one({"session_id": session_id})
        if doc:
            return doc.get("messages", [])
        return []
    else:
        data = _load_history_local()
        return data.get("sessions", {}).get(session_id, {}).get("messages", [])

def delete_session(session_id):
    if DB_CONNECTED:
        collection.delete_one({"session_id": session_id})
    else:
        data = _load_history_local()
        if "sessions" in data and session_id in data["sessions"]:
            del data["sessions"][session_id]
            _save_history_local(data)

def save_message(session_id, role, content, tool_calls=None, name=None):
    timestamp = datetime.utcnow().isoformat() + "Z"
    msg = {"role": role, "content": content}
    if tool_calls: msg["tool_calls"] = tool_calls
    if name: msg["name"] = name

    if DB_CONNECTED:
        doc = collection.find_one({"session_id": session_id})
        if not doc:
            title = "New Chat"
            if role == "user":
                title = content[:30] + "..." if len(content) > 30 else content
            collection.insert_one({
                "session_id": session_id,
                "title": title,
                "created_at": timestamp,
                "updated_at": timestamp,
                "messages": [msg]
            })
        else:
            collection.update_one(
                {"session_id": session_id},
                {
                    "$push": {"messages": msg},
                    "$set": {"updated_at": timestamp}
                }
            )
    else:
        data = _load_history_local()
        if "sessions" not in data: data["sessions"] = {}
        if session_id not in data["sessions"]:
            title = "New Chat"
            if role == "user":
                title = content[:30] + "..." if len(content) > 30 else content
            data["sessions"][session_id] = {
                "title": title,
                "created_at": timestamp,
                "updated_at": timestamp,
                "messages": []
            }
        data["sessions"][session_id]["messages"].append(msg)
        data["sessions"][session_id]["updated_at"] = timestamp
        _save_history_local(data)

def save_full_session(session_id, messages, title=None):
    timestamp = datetime.utcnow().isoformat() + "Z"
    if DB_CONNECTED:
        doc = collection.find_one({"session_id": session_id})
        if not doc:
            collection.insert_one({
                "session_id": session_id,
                "title": title or "New Chat",
                "created_at": timestamp,
                "updated_at": timestamp,
                "messages": messages
            })
        else:
            update_fields = {"messages": messages, "updated_at": timestamp}
            if title: update_fields["title"] = title
            collection.update_one({"session_id": session_id}, {"$set": update_fields})
    else:
        data = _load_history_local()
        if "sessions" not in data: data["sessions"] = {}
        if session_id not in data["sessions"]:
            data["sessions"][session_id] = {
                "title": title or "New Chat",
                "created_at": timestamp,
                "updated_at": timestamp,
                "messages": messages
            }
        else:
            if title: data["sessions"][session_id]["title"] = title
            data["sessions"][session_id]["messages"] = messages
            data["sessions"][session_id]["updated_at"] = timestamp
        _save_history_local(data)
