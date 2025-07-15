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
    # Provider detection for Groq and Google
    def is_gemini(m):
        return m and m.startswith('gemini')
    def is_llama(m):
        return m and m.startswith((
            'llama-3.1-8b',
            'llama-3.3-70b',
            'deepseek',
            'meta-llama/llama-4-maverick',
            'meta-llama/llama-4-scout',
            'meta-llama/llama-prompt-guard-2-22m',
            'meta-llama/llama-prompt-guard-2-86m',
            'mistral',
            'moonshotai/'
        ))
    response_text = None
    model_used = None
    latency_ms = None
    token_count = None
    error = None
    errors = {}
    tried_models = []
    if is_llama(model):
        # Try user model, then fallback to llama-3.1-8b-instant
        for m in [model, 'llama-3.1-8b-instant']:
            if m in tried_models:
                continue
            tried_models.append(m)
            try:
                handler = GroqHandler(model_override=m)
                start = time.time()
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
                errors[m] = error
                response_text = None
        if response_text is None:
            detail = f"All Llama/Groq models failed. Errors: {errors}"
            raise HTTPException(status_code=500, detail=detail)
    elif is_gemini(model):
        # Try user model, then fallback to gemini-2.5-flash
        for m in [model, 'gemini-2.5-flash']:
            if m in tried_models:
                continue
            tried_models.append(m)
            try:
                handler = GeminiHandler(model_override=m)
                start = time.time()
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
                errors[m] = error
                response_text = None
        if response_text is None:
            detail = f"All Gemini/Google models failed. Errors: {errors}"
            raise HTTPException(status_code=500, detail=detail)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown model provider for model: {model}")
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
            "llama-3.3-70b-versatile",  # via Groq
            "meta-llama/llama-guard-4-12b",  # via Groq
            "deepseek-r1-distill-llama-70b",  # via Groq
            "meta-llama/llama-4-maverick-17b-128e-instruct",  # via Groq
            "meta-llama/llama-4-scout-17b-16e-instruct",  # via Groq
            "meta-llama/llama-prompt-guard-2-22m",  # via Groq
            "meta-llama/llama-prompt-guard-2-86m",  # via Groq
            "mistral-saba-24b",  # via Groq
            "moonshotai/kimi-k2-instruct",  # via Groq
            "gemini-2.5-pro",  # Gemini 2.5 Pro
            "gemini-2.5-flash",  # Gemini 2.5 Flash
            "gemini-2.5-flash-lite-preview-06-17",  # Gemini 2.5 Flash-Lite Preview 06-17
            "gemini-2.0-flash",  # Gemini 2.0 Flash
            "gemini-2.0-flash-lite"  # Gemini 2.0 Flash-Lite
        ],
        "note": "You can use any of these models by changing the model name in the query parameter if supported by your API key."
    }

@app.post('/rate')
async def rate_endpoint(prompt_id: str = Query(...), score: int = Query(..., ge=1, le=5)):
    timestamp = datetime.utcnow().isoformat()
    log_rating(prompt_id, score, timestamp)
    return {'status': 'ok', 'prompt_id': prompt_id, 'score': score} 