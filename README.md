# llm-router

A FastAPI-based backend to route chat prompts to either GROQ (OpenAI-compatible, e.g., Llama, Mistral, DeepSeek, Moonshot, Meta) or Gemini (Google Generative AI) models, with logging, fallback, rating, prompt templates, analytics, persistent caching, and a modern Streamlit frontend.

---

## Features
- **Supports 12+ models** (see below for full list; easily extensible)
- **/chat** endpoint: Route prompt to GROQ or Gemini, with fallback, retry, latency/tokens, and prompt templates (with variable substitution)
- **ignore_cache**: Force fresh response, bypassing persistent cache (see usage examples)
- **/rate** endpoint: Rate a previous response and provide feedback
- **/stats** endpoint: Analytics (model usage, avg latency, avg rating, fallback count, total prompts)
- **/models** endpoint: List all supported models
- **Prompt templates**: Use and customize prompt templates with variable substitution
- **Persistent SQLite caching**: Fast repeated responses, cache bypass option
- **Structured logging**: All interactions and ratings to `logs/prompts.json` and `logs/prompts.csv`
- **Token usage estimation**: Model-specific heuristics, tiktoken if available
- **Fallback and retry logic**: Automatic fallback to alternate provider/model on failure
- **Analytics**: Real-time stats, ratings, feedback, and usage
- **Streamlit frontend**: Modern UI for chat, analytics, ratings, and session management
- **Pytest test suite**: With mocks for endpoints and fallback
- **Docker support**: Easy deployment

---

## Project Structure

```
llm-chatservice/
├── main.py                # FastAPI app
├── models/
│   ├── groq_handler.py    # GROQ (OpenAI-compatible) handler
│   └── gemini_handler.py  # Gemini (Google Generative AI) handler
├── utils/
│   ├── cache.py           # Persistent SQLite cache
│   ├── logger.py          # Logging utilities (JSON/CSV)
│   └── tokens.py          # Token estimation utility
├── tests/
│   └── test_main.py       # Pytest test suite
├── logs/
│   ├── prompts.json       # JSON log of all prompts
│   └── prompts.csv        # CSV log of all prompts
├── prompt_templates.json  # Prompt templates
├── requirements.txt       # Python dependencies
├── codes.txt              # All curl commands (Windows & Bash)
├── Dockerfile             # Docker support
├── .env                   # Environment variables (not committed)
├── streamlit_app.py       # Streamlit frontend
└── README.md              # This file
```

### Models Available (12+)
- **GROQ (OpenAI-compatible, via Groq):**
  - llama-3.1-8b-instant
  - llama-3.3-70b-versatile
  - deepseek-r1-distill-llama-70b
  - meta-llama/llama-4-maverick-17b-128e-instruct
  - meta-llama/llama-4-scout-17b-16e-instruct
  - meta-llama/llama-prompt-guard-2-22m
  - meta-llama/llama-prompt-guard-2-86m
  - mistral-saba-24b
  - moonshotai/kimi-k2-instruct
- **Gemini (Google Generative AI):**
  - gemini-2.5-pro
  - gemini-2.5-flash
  - gemini-2.5-flash-lite-preview-06-17
  - gemini-2.0-flash
  - gemini-2.0-flash-lite

> **Note:** Model names are case-sensitive and must match those returned by `/models`. Use `/models` to see all available models for your API keys.

### Key Files
- **@models**
  - `groq_handler.py`: Handles GROQ API requests
  - `gemini_handler.py`: Handles Gemini API requests
- **@utils**
  - `logger.py`: Logs all interactions and ratings to JSON/CSV
  - `tokens.py`: Estimates token usage
  - `cache.py`: Persistent SQLite cache for (prompt, model) pairs
- **@tests**
  - `test_main.py`: Pytest test suite for endpoints and fallback

---

## Setup

1. **Clone and install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up your `.env` file:**
   Create a `.env` file in the project root with the following content:
   ```env
   GROQ_API_KEY=your_api_key
   GEMINI_API_KEY=your_api_key
   ```
   Replace the values with your actual API keys.

3. **Run the server:**
   ```bash
   uvicorn main:app --reload
   ```
   The API will be available at `http://127.0.0.1:8000`.

---

## Usage Examples

### 1. Chat with Llama-3.1-8b-instant (Groq)
#### Windows (PowerShell/cmd)
```powershell
curl -X POST "http://127.0.0.1:8000/chat?model=llama-3.1-8b-instant" -H "Content-Type: application/json" -d "{\"prompt\": \"What is the capital of France?\"}"
```
#### Bash (Linux/macOS/Git Bash)
```bash
curl -X POST 'http://127.0.0.1:8000/chat?model=llama-3.1-8b-instant' -H 'Content-Type: application/json' -d '{"prompt": "What is the capital of France?"}'
```

### 2. Chat with Gemini-2.5-flash
#### Windows
```powershell
curl -X POST "http://127.0.0.1:8000/chat?model=gemini-2.5-flash" -H "Content-Type: application/json" -d "{\"prompt\": \"Tell me a joke.\"}"
```
#### Bash
```bash
curl -X POST 'http://127.0.0.1:8000/chat?model=gemini-2.5-flash' -H 'Content-Type: application/json' -d '{"prompt": "Tell me a joke."}'
```

### 3. Chat with a prompt template (Llama-3.1-8b-instant)
#### Windows
```powershell
curl -X POST "http://127.0.0.1:8000/chat?model=llama-3.1-8b-instant" -H "Content-Type: application/json" -d "{\"template_id\": \"friendly\", \"template_vars\": {\"audience\": \"kids\", \"topic\": \"gravity\"}}"
```
#### Bash
```bash
curl -X POST 'http://127.0.0.1:8000/chat?model=llama-3.1-8b-instant' -H 'Content-Type: application/json' -d '{"template_id": "friendly", "template_vars": {"audience": "kids", "topic": "gravity"}}'
```

### 4. Chat with a prompt template (Gemini-2.5-flash)
#### Windows
```powershell
curl -X POST "http://127.0.0.1:8000/chat?model=gemini-2.5-flash" -H "Content-Type: application/json" -d "{\"template_id\": \"friendly\", \"template_vars\": {\"audience\": \"kids\", \"topic\": \"gravity\"}}"
```
#### Bash
```bash
curl -X POST 'http://127.0.0.1:8000/chat?model=gemini-2.5-flash' -H 'Content-Type: application/json' -d '{"template_id": "friendly", "template_vars": {"audience": "kids", "topic": "gravity"}}'
```

### 5. **Bypass Cache with ignore_cache**
Force a fresh response from the model, bypassing the persistent cache:
#### Windows
```powershell
curl -X POST "http://127.0.0.1:8000/chat?model=llama-3.1-8b-instant&ignore_cache=true" -H "Content-Type: application/json" -d "{\"prompt\": \"What is the capital of France?\"}"
```
#### Bash
```bash
curl -X POST 'http://127.0.0.1:8000/chat?model=llama-3.1-8b-instant&ignore_cache=true' -H 'Content-Type: application/json' -d '{"prompt": "What is the capital of France?"}'
```
> **Tip:** `ignore_cache` can be used with any /chat request (prompt or template).

### 6. Rate a response (works for any model)
Replace `YOUR_PROMPT_ID` with the `prompt_id` from a `/chat` response.
#### Windows
```powershell
curl -X POST "http://127.0.0.1:8000/rate" -H "Content-Type: application/json" -d "{\"prompt_id\": \"YOUR_PROMPT_ID\", \"model\": \"llama-3.1-8b-instant\", \"rating\": 5, \"feedback\": \"Great answer!\"}"
```
#### Bash
```bash
curl -X POST 'http://127.0.0.1:8000/rate' -H 'Content-Type: application/json' -d '{"prompt_id": "YOUR_PROMPT_ID", "model": "llama-3.1-8b-instant", "rating": 5, "feedback": "Great answer!"}'
```

### 7. Fallback test (Llama-3.1-8b-instant)
Remove or comment out `GROQ_API_KEY` in your `.env`, then run:
#### Windows
```powershell
curl -X POST "http://127.0.0.1:8000/chat?model=llama-3.1-8b-instant" -H "Content-Type: application/json" -d "{\"prompt\": \"Fallback test.\"}"
```
#### Bash
```bash
curl -X POST 'http://127.0.0.1:8000/chat?model=llama-3.1-8b-instant' -H 'Content-Type: application/json' -d '{"prompt": "Fallback test."}'
```

---

## Reference: codes.txt
All the above commands (and more) are available in `codes.txt` in both Windows and Bash formats. Use it as a quick reference for testing all endpoints.

---

## Streamlit Frontend

A modern Streamlit-based frontend is included for interactive use and analytics.

### Features
- **Model & Prompt Template Selection:** Choose from all supported models and prompt templates in the sidebar.
- **Chat Interface:** Send prompts (raw or templated), view responses, and see model/latency/cache/fallback info.
- **Prompt Templates Tab:** Browse and preview all available prompt templates by category.
- **Analytics Tab:** Real-time charts for model usage, average latency, average rating, fallback count, and total prompts.
- **Ratings & Feedback:** Rate and comment on responses directly in the chat history.
- **Session Management:** Reset chat history and manage session state.
- **Cache Bypass:** Option to ignore cache for any prompt.

### How to Run
```bash
streamlit run streamlit_app.py
```
The UI will be available at [http://localhost:8501](http://localhost:8501).

---

## Prompt Templates
- Edit `prompt_templates.json` to add or modify templates.
- Use `{{variable}}` placeholders for custom variables in your template.
- Use the `template_id` and `template_vars` fields in the `/chat` endpoint to select and fill templates.
- Example template usage:
  - `template_id`: "friendly"
  - `template_vars`: {"audience": "kids", "topic": "gravity"}

---

## Logs
- All prompts and responses are logged to `logs/prompts.json` and `logs/prompts.csv`.
- Each log includes: timestamp, prompt, model, response, latency, token count, prompt_id, rating, and feedback (if any).

---

## Analytics & Stats
- `/stats` endpoint returns model usage, average latency, average rating, fallback count, and total prompts.
- `/models` endpoint lists all supported models.

---

## Techniques & Architecture
- **FastAPI**: High-performance Python web framework
- **Persistent SQLite Caching**: All (prompt, model) pairs are cached for fast repeated responses
- **Fallback & Retry Logic**: If a model fails, the system retries and falls back to a default model/provider
- **Prompt Templates**: Variable substitution using `{{variable}}` syntax, loaded from JSON
- **Structured Logging**: All interactions and ratings are logged in both JSON and CSV for analytics
- **Token Counting**: Model-specific heuristics, with tiktoken support if available
- **Analytics**: Real-time stats, ratings, feedback, and usage
- **Streamlit Frontend**: Modern UI for all features, including analytics and session management
- **Pytest Test Suite**: Automated tests for endpoints, fallback, and caching
- **Docker Support**: Easy containerized deployment
- **Environment Variables**: API keys and config via `.env`
- **Modular Codebase**: Handlers, utils, and templates are cleanly separated

---

## Troubleshooting
- Make sure your `.env` file is present and contains valid API keys.
- Check `logs/prompts.json` and `logs/prompts.csv` for all interactions and ratings.
- If you encounter issues, check the FastAPI logs for error messages.

---

If you have any recommendations or suggestions, please let me know.

Thank you