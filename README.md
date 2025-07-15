# llm-router

A FastAPI-based backend to route chat prompts to either GROQ (OpenAI-compatible, e.g. Mistral-7B) or Gemini (Google Generative AI) models, with logging, fallback, rating, and prompt templates.

## Features
- `/chat` endpoint: Route prompt to GROQ or Gemini, with fallback if one fails
- `/rate` endpoint: Rate a previous response
- Logs all interactions to `logs/prompts.json` and `logs/prompts.csv`
- Supports prompt templates from `prompt_templates.json`
- Token usage estimation (tiktoken if available, else heuristic)
- Model logic isolated in `models/`
- Structured logging in `utils/`
- Pytest test suite with mocks
- Docker support (optional)

## Setup

1. **Clone and install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   - `GROQ_API_KEY` (required for GROQ)
   - `GROQ_API_URL` (optional, default: https://api.groq.com/openai/v1/chat/completions)
   - `GROQ_MODEL` (optional, default: mistral-7b)
   - `GEMINI_API_KEY` (required for Gemini)
   - `GEMINI_MODEL` (optional, default: gemini-pro)

   Example (Windows):
   ```powershell
   $env:GROQ_API_KEY="sk-..."
   $env:GEMINI_API_KEY="..."
   ```

3. **Run the server:**
   ```bash
   uvicorn main:app --reload
   ```

## Usage

### /chat
POST `/chat?model=groq|gemini`
```json
{
  "prompt": "Your question here",
  "template": "friendly" // optional, see prompt_templates.json
}
```
**Returns:**
- `prompt_id`, `model_used`, `response_text`, `latency_ms`, `token_count`

### /rate
POST `/rate?prompt_id=...&score=1-5`
- Appends a rating to the log for a previous prompt

## Prompt Templates
Edit `prompt_templates.json` to add or modify templates. Use `{prompt}` as a placeholder.

## Logs
- All prompts and responses are logged to `logs/prompts.json` and `logs/prompts.csv`.
- Each log includes: timestamp, prompt, model, response, latency, token count, prompt_id, and rating (if any).

## Testing
```bash
pytest
```

## Docker (optional)
A sample Dockerfile is provided. Build and run:
```bash
docker build -t llm-router .
docker run -e GROQ_API_KEY=... -e GEMINI_API_KEY=... -p 8000:8000 llm-router
```

## Sample Logs
See `logs/prompts.json` and `logs/prompts.csv` for example entries after running a few prompts.
