import os
import time
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from utils.logger import log_interaction, log_rating, get_prompt_id
from utils.tokens import estimate_token_count
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Load prompt templates
try:
    with open('prompt_templates.json', 'r', encoding='utf-8') as f:
        PROMPT_TEMPLATES = json.load(f)
except Exception:
    PROMPT_TEMPLATES = {}

class ChatRequest(BaseModel):
    prompt: str
    template: Optional[str] = None

@app.post('/chat')
async def chat_endpoint(request: Request, model: str = Query(...)):
    from models.groq_handler import GroqHandler
    from models.gemini_handler import GeminiHandler
    body = await request.json()
    prompt = body.get('prompt')
    template = body.get('template')
    if not prompt:
        raise HTTPException(status_code=400, detail='Missing prompt')
    if template and template in PROMPT_TEMPLATES:
        prompt = PROMPT_TEMPLATES[template].replace('{prompt}', prompt)
    # Try the requested model, then fallback to the other provider
    handlers = []
    errors = {}
    # Determine provider by model name
    def is_gemini(m):
        return m.startswith('gemini')
    def is_llama(m):
        return m.startswith('llama-3.1-8b')
    # Try requested model, then fallback
    fallback_model = 'gemini-2.5-flash' if is_llama(model) else 'llama-3.1-8b-instant'
    for m in [model, fallback_model]:
        try:
            if is_llama(m):
                handler = GroqHandler(model_override=m)
            elif is_gemini(m):
                handler = GeminiHandler(model_override=m)
            else:
                raise ValueError(f'Unknown model: {m}')
            handlers.append((m, handler))
        except Exception as e:
            errors[m] = str(e)
    response_text = None
    model_used = None
    latency_ms = None
    token_count = None
    error = None
    for m, handler in handlers:
        start = time.time()
        try:
            result = handler.generate(prompt)
            if isinstance(result, tuple):
                response_text, model_token_count = result
            else:
                response_text, model_token_count = result, None
            latency_ms = int((time.time() - start) * 1000)
            model_used = m
            if model_token_count is not None:
                token_count = model_token_count
            else:
                token_count = estimate_token_count(prompt + response_text, model=m)
            break
        except Exception as e:
            error = str(e)
            continue
    if response_text is None:
        detail = f'Both models failed. Errors: {errors}. Last error: {error}'
        raise HTTPException(status_code=500, detail=detail)
    timestamp = datetime.utcnow().isoformat()
    prompt_id = get_prompt_id(timestamp, prompt, model_used)
    log_interaction(timestamp, prompt, model_used, response_text, latency_ms, token_count, prompt_id)
    return JSONResponse({
        'prompt_id': prompt_id,
        'model_used': model_used,
        'response_text': response_text,
        'latency_ms': latency_ms,
        'token_count': token_count
    })

@app.get('/models')
def list_models():
    return {
        "available_models": [
            "llama-3.1-8b-instant",  # via Groq
            "gemini-2.5-flash"  # Gemini 2.5 Flash
        ],
        "note": "You can use other Llama-3.1-8b or Gemini models by changing the model name in the query parameter if supported by your API key."
    }

@app.post('/rate')
async def rate_endpoint(prompt_id: str = Query(...), score: int = Query(..., ge=1, le=5)):
    timestamp = datetime.utcnow().isoformat()
    log_rating(prompt_id, score, timestamp)
    return {'status': 'ok', 'prompt_id': prompt_id, 'score': score} 