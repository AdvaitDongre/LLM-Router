# llm-router

A FastAPI-based backend to route chat prompts to either GROQ (OpenAI-compatible, e.g. llama-3.1-8b-instant) or Gemini (Google Generative AI) models, with logging, fallback, rating, and prompt templates.

---

## Features
- **/chat** endpoint: Route prompt to GROQ or Gemini, with fallback if one fails
- **/rate** endpoint: Rate a previous response
- Logs all interactions to `logs/prompts.json` and `logs/prompts.csv`
- Supports prompt templates from `prompt_templates.json`
- Token usage estimation (tiktoken if available, else heuristic)
- Model logic isolated in `models/`
- Structured logging and token counting in `utils/`
- Pytest test suite with mocks in `tests/`
- Docker support

---

## Project Structure

```
llm-chatservice/
├── main.py                # FastAPI app
├── models/
│   ├── groq_handler.py    # GROQ (OpenAI-compatible) handler
│   └── gemini_handler.py  # Gemini (Google Generative AI) handler
├── utils/
│   ├── logger.py          # Logging utilities (JSON/CSV)
│   └── tokens.py          # Token estimation utility
├── tests/
│   └── test_main.py       # Pytest test suite
├── logs/
│   ├── prompts.json       # JSON log of all prompts
│   └── prompts.csv        # CSV log of all prompts
├── prompt_templates.json  # Prompt templates
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker support
├── .env                   # Environment variables (not committed)
└── README.md              # This file
```

### Models Used
- **GROQ (OpenAI-compatible, e.g. Mistral-7B)**
- **Gemini (Google Generative AI, e.g. gemini-pro)**

### Key Files
- **@models**
  - `groq_handler.py`: Handles GROQ API requests
  - `gemini_handler.py`: Handles Gemini API requests
- **@utils**
  - `logger.py`: Logs all interactions and ratings to JSON/CSV
  - `tokens.py`: Estimates token usage
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
   # GROQ API
   GROQ_API_KEY=your-groq-api-key-here
   GROQ_API_URL=https://api.groq.com/openai/v1/chat/completions
   GROQ_MODEL=mistral-7b

   # GEMINI API
   GEMINI_API_KEY=your-gemini-api-key-here
   GEMINI_MODEL=gemini-pro
   ```
   Replace the values with your actual API keys.

3. **Run the server:**
   ```bash
   uvicorn main:app --reload
   ```
   The API will be available at `http://127.0.0.1:8000`.

---

## Usage Examples

### 1. Chat with GROQ
```bash
curl -X POST "http://127.0.0.1:8000/chat?model=groq" -H "Content-Type: application/json" -d "{\"prompt\": \"What is the capital of France?\"}"
```

### 2. Chat with Gemini
```bash
curl -X POST "http://127.0.0.1:8000/chat?model=gemini" -H "Content-Type: application/json" -d "{\"prompt\": \"Tell me a joke.\"}"
```

### 3. Chat with a prompt template
```bash
curl -X POST "http://127.0.0.1:8000/chat?model=groq" -H "Content-Type: application/json" -d "{\"prompt\": \"Explain gravity.\", \"template\": \"friendly\"}"
```

### 4. Rate a response
Replace `YOUR_PROMPT_ID` with the `prompt_id` from a `/chat` response:
```bash
curl -X POST "http://127.0.0.1:8000/rate?prompt_id=YOUR_PROMPT_ID&score=5"
```

### 5. Fallback test
Remove or comment out `GROQ_API_KEY` in your `.env`, then run:
```bash
curl -X POST "http://127.0.0.1:8000/chat?model=groq" -H "Content-Type: application/json" -d "{\"prompt\": \"Fallback test.\"}"
```
You should get an error if both models are misconfigured, or a Gemini response if only GROQ is misconfigured.

---

## Prompt Templates
- Edit `prompt_templates.json` to add or modify templates.
- Use `{prompt}` as a placeholder in your template.

---

## Logs
- All prompts and responses are logged to `logs/prompts.json` and `logs/prompts.csv`.
- Each log includes: timestamp, prompt, model, response, latency, token count, prompt_id, and rating (if any).

---

## Testing
Run all tests with:
```bash
pytest
```

---

## Docker
A sample Dockerfile is provided. To build and run with Docker:
```bash
docker build -t llm-router .
docker run --env-file .env -p 8000:8000 llm-router
```

---

## Troubleshooting
- Make sure your `.env` file is present and contains valid API keys.
- Check `logs/prompts.json` and `logs/prompts.csv` for all interactions and ratings.
- If you encounter issues, check the FastAPI logs for error messages.

---

## License
MIT
