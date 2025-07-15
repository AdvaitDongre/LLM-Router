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
async def chat_endpoint(request: Request, model: str = Query(..., regex='^(groq|gemini)$')):
    from models.groq_handler import GroqHandler
    from models.gemini_handler import GeminiHandler
    body = await request.json()
    prompt = body.get('prompt')
    template = body.get('template')
    if not prompt:
        raise HTTPException(status_code=400, detail='Missing prompt')
    if template and template in PROMPT_TEMPLATES:
        prompt = PROMPT_TEMPLATES[template].replace('{prompt}', prompt)
    handlers = []
    errors = {}
    for m in [model, 'gemini' if model == 'groq' else 'groq']:
        try:
            handler = GroqHandler() if m == 'groq' else GeminiHandler()
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
            response_text = handler.generate(prompt)
            latency_ms = int((time.time() - start) * 1000)
            model_used = m
            token_count = estimate_token_count(prompt + response_text)
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

@app.post('/rate')
async def rate_endpoint(prompt_id: str = Query(...), score: int = Query(..., ge=1, le=5)):
    timestamp = datetime.utcnow().isoformat()
    log_rating(prompt_id, score, timestamp)
    return {'status': 'ok', 'prompt_id': prompt_id, 'score': score} 