# Scashyyyy - Personal AI Assistant

A simple, personal AI assistant with web interface, voice support, task management, and web search.

## Features

- **AI Chat** - Powered by Groq (Llama 3.3 70B)
- **Voice Input/Output** - Speak to your assistant, hear responses in female voice
- **Task Management** - Add, complete, and delete tasks
- **Notes** - Save quick notes
- **Web Search** - Auto-searches when you ask about places, news, facts, etc.
- **Personal Context** - Knows your schedule, interests, and goals

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/personal_bot.git
cd personal_bot
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env` and add your Groq API key (free at [console.groq.com](https://console.groq.com)):

```
GROQ_API_KEY=your_key_here
```

### 3. Customize (Optional)

Edit `prompt.py` to update:
- Your name and info
- Daily routine
- Interests and goals
- Bot personality

### 4. Run

```bash
python personal_assistant.py
```

Open [http://localhost:8000](http://localhost:8000)

## Usage

### Chat
Just type or speak to Scashyyyy. It understands context and can:
- Answer questions about your schedule
- Search the web for information
- Manage your tasks and notes

### Voice
- Click the mic button or just start speaking (always listening mode)
- Bot responds with female voice

### Example Commands
- "What should I be doing now?"
- "Add task buy groceries"
- "Search best restaurants in Delhi"
- "Save note meeting at 3pm tomorrow"
- "Mark task 1 as done"

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/chat` | POST | Send message, get AI response |
| `/search` | POST | Web search |
| `/tasks` | GET/POST/PUT/DELETE | Task management |
| `/notes` | GET/POST/DELETE | Notes management |
| `/clear` | POST | Clear conversation history |
| `/health` | GET | Health check |

## Deployment

### Railway (Recommended)

1. Push to GitHub
2. Connect repo on [railway.app](https://railway.app)
3. Add `GROQ_API_KEY` environment variable
4. Deploy

### Render

1. Push to GitHub
2. Create Web Service on [render.com](https://render.com)
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn personal_assistant:app`
5. Add `GROQ_API_KEY` environment variable

## CI/CD

GitHub Actions automatically:
- Runs linting and syntax checks on every push
- Auto-deploys to Railway/Render on push to main

Set these secrets in GitHub:
- `RAILWAY_TOKEN` - Railway API token
- `RAILWAY_SERVICE_ID` - Railway service ID

## Tech Stack

- **Backend**: Flask + Gunicorn
- **AI**: Groq API (Llama 3.3 70B)
- **Search**: DuckDuckGo
- **Voice**: Web Speech API
- **Storage**: JSON file

## Project Structure

```
personal_bot/
├── personal_assistant.py  # Main Flask app
├── prompt.py              # Bot personality & prompts
├── templates/
│   └── index.html         # Web UI
├── bot_data.json          # Tasks & notes storage
├── requirements.txt       # Dependencies
├── Procfile               # Deployment config
├── runtime.txt            # Python version
└── .github/
    └── workflows/
        └── deploy.yml     # CI/CD pipeline
```

## License

MIT

---

Made with love by Ritik Pal
