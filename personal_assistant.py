#!/usr/bin/env python3
"""
Scashyyyy - Complete Personal AI Assistant
Features: Web UI, Voice, Tasks, Notes, Web Search
"""

import os
import json
import re
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from groq import Groq
from dotenv import load_dotenv
from prompt import get_system_prompt  # Import from prompt.py

# Web Search
try:
    from duckduckgo_search import DDGS
    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')

# ===========================================
# DATA STORAGE
# ===========================================

DATA_FILE = "bot_data.json"

def load_data():
    """Load tasks and notes from file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"tasks": [], "notes": [], "reminders": []}

def save_data(data):
    """Save tasks and notes to file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# ===========================================
# WEB SEARCH
# ===========================================

def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo."""
    if not SEARCH_AVAILABLE:
        return "Search not available. Install: pip install duckduckgo-search"

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return f"No results found for: {query}"

        search_text = f"🔍 Search Results for: {query}\n\n"
        for i, r in enumerate(results, 1):
            search_text += f"{i}. {r['title']}\n"
            search_text += f"   {r['body'][:150]}...\n\n"

        return search_text
    except Exception as e:
        return f"Search error: {str(e)}"

# ===========================================
# AI SETUP
# ===========================================

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
conversation_history = []

def get_context_strings():
    """Get formatted tasks and notes for prompt."""
    data = load_data()

    tasks_str = ""
    for i, task in enumerate(data["tasks"], 1):
        status = "✓" if task.get("done") else "○"
        tasks_str += f"{i}. [{status}] {task['text']}\n"

    notes_str = ""
    for note in data["notes"][-5:]:
        notes_str += f"- {note['text']} ({note['date']})\n"

    return tasks_str, notes_str

def build_system_prompt(search_results: str = ""):
    """Build system prompt using prompt.py config."""
    current_time = datetime.now().strftime("%I:%M %p")
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    tasks_str, notes_str = get_context_strings()

    prompt = get_system_prompt(current_time, current_date, tasks_str, notes_str)

    if search_results:
        prompt += f"\n\n=== SEARCH RESULTS ===\n{search_results}"

    return prompt

def process_actions(response: str, data: dict) -> tuple[str, bool, str]:
    """Process actions in AI response."""
    needs_search = False
    search_query = ""

    # Search action - remove ALL search action tags
    while "[ACTION:SEARCH:" in response:
        start = response.find("[ACTION:SEARCH:")
        end = response.find("]", start)
        if end != -1:
            search_query = response[start+15:end]
            needs_search = True
            response = response[:start] + response[end+1:]
        else:
            break

    # Clean up any remaining action tags
    response = re.sub(r'\[ACTION:[^\]]*\]', '', response)

    # Add Task
    if "[ACTION:ADD_TASK:" in response:
        start = response.find("[ACTION:ADD_TASK:") + 17
        end = response.find("]", start)
        task_text = response[start:end]
        data["tasks"].append({"text": task_text, "done": False, "date": datetime.now().strftime("%Y-%m-%d")})
        save_data(data)
        response = response.replace(f"[ACTION:ADD_TASK:{task_text}]", f"✅ Added: {task_text}")

    # Complete Task
    if "[ACTION:COMPLETE_TASK:" in response:
        start = response.find("[ACTION:COMPLETE_TASK:") + 22
        end = response.find("]", start)
        try:
            task_num = int(response[start:end]) - 1
            if 0 <= task_num < len(data["tasks"]):
                data["tasks"][task_num]["done"] = True
                save_data(data)
                response = response.replace(f"[ACTION:COMPLETE_TASK:{task_num+1}]", f"✅ Done!")
        except:
            pass

    # Add Note
    if "[ACTION:ADD_NOTE:" in response:
        start = response.find("[ACTION:ADD_NOTE:") + 17
        end = response.find("]", start)
        note_text = response[start:end]
        data["notes"].append({"text": note_text, "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
        save_data(data)
        response = response.replace(f"[ACTION:ADD_NOTE:{note_text}]", f"📝 Noted!")

    return response.strip(), needs_search, search_query

def should_auto_search(message: str) -> bool:
    """Check if message should trigger automatic search."""
    message_lower = message.lower()

    # Keywords that indicate search intent
    search_keywords = [
        'search', 'find', 'look up', 'google', 'what is', 'who is',
        'where is', 'how to', 'best', 'top', 'latest', 'news',
        'weather', 'places to', 'restaurants', 'hotels', 'near me',
        'reviews', 'price of', 'cost of', 'meaning of', 'define',
        'when is', 'why is', 'tell me about', 'information about'
    ]

    for keyword in search_keywords:
        if keyword in message_lower:
            return True
    return False

def chat(message: str) -> dict:
    """Send message and get response."""

    # Auto-search for certain queries
    auto_search_results = ""
    if should_auto_search(message):
        auto_search_results = web_search(message)

    conversation_history.append({"role": "user", "content": message})

    if len(conversation_history) > 20:
        conversation_history.pop(0)

    # Use auto-search results if available
    messages = [{"role": "system", "content": build_system_prompt(auto_search_results)}]
    messages.extend(conversation_history)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=500,
        temperature=0.7
    )

    reply = response.choices[0].message.content

    data = load_data()
    reply, needs_search, search_query = process_actions(reply, data)

    search_results = ""
    if needs_search and search_query:
        search_results = web_search(search_query)

        messages = [{"role": "system", "content": build_system_prompt(search_results)}]
        messages.append({"role": "user", "content": f"Based on search results, answer: {message}"})

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        reply = response.choices[0].message.content

    # Final cleanup - remove any action tags that slipped through
    reply = re.sub(r'\[ACTION:[^\]]*\]', '', reply)
    reply = reply.strip()

    conversation_history.append({"role": "assistant", "content": reply})

    # Combine search results
    all_search_results = auto_search_results or search_results

    return {"response": reply, "search_results": all_search_results}

# ===========================================
# WEB ROUTES
# ===========================================

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    message = request.json.get('message', '')
    if not message:
        return jsonify({"error": "No message"}), 400
    return jsonify(chat(message))

@app.route('/search', methods=['POST'])
def search_endpoint():
    query = request.json.get('query', '')
    if not query:
        return jsonify({"error": "No query"}), 400
    return jsonify({"results": web_search(query)})

@app.route('/tasks', methods=['GET', 'POST', 'PUT', 'DELETE'])
def tasks_endpoint():
    data = load_data()

    if request.method == 'GET':
        return jsonify(data["tasks"])

    elif request.method == 'POST':
        task_text = request.json.get('text', '')
        if task_text:
            data["tasks"].append({"text": task_text, "done": False, "date": datetime.now().strftime("%Y-%m-%d")})
            save_data(data)
        return jsonify(data["tasks"])

    elif request.method == 'PUT':
        task_id = request.json.get('id', 0)
        if 0 <= task_id < len(data["tasks"]):
            data["tasks"][task_id]["done"] = not data["tasks"][task_id]["done"]
            save_data(data)
        return jsonify(data["tasks"])

    elif request.method == 'DELETE':
        task_id = request.json.get('id', 0)
        if 0 <= task_id < len(data["tasks"]):
            data["tasks"].pop(task_id)
            save_data(data)
        return jsonify(data["tasks"])

@app.route('/notes', methods=['GET', 'POST', 'DELETE'])
def notes_endpoint():
    data = load_data()

    if request.method == 'GET':
        return jsonify(data["notes"])

    elif request.method == 'POST':
        note_text = request.json.get('text', '')
        if note_text:
            data["notes"].append({"text": note_text, "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
            save_data(data)
        return jsonify(data["notes"])

    elif request.method == 'DELETE':
        note_id = request.json.get('id', 0)
        if 0 <= note_id < len(data["notes"]):
            data["notes"].pop(note_id)
            save_data(data)
        return jsonify(data["notes"])

@app.route('/clear', methods=['POST'])
def clear_conversation():
    global conversation_history
    conversation_history = []
    return jsonify({"status": "cleared"})

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for deployment monitoring."""
    return jsonify({
        "status": "healthy",
        "service": "scashyyyy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })

# ===========================================
# RUN
# ===========================================

if __name__ == '__main__':
    if not os.path.exists(DATA_FILE):
        save_data({"tasks": [], "notes": [], "reminders": []})

    print("\n" + "="*50)
    print("   🤖 SCASHYYYY - Personal Assistant")
    print("="*50)
    print("\n🌐 Open: http://localhost:8000")
    print("📝 Edit: prompt.py to customize personality")
    print("\nPress Ctrl+C to stop\n")

    app.run(host='0.0.0.0', port=8000, debug=True)
