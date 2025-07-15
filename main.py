import os
import time
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from utils.logger import log_interaction, log_rating, get_prompt_id, log_rating_v2
from utils.tokens import estimate_token_count
import json
from datetime import datetime
from dotenv import load_dotenv
from utils.cache import get_cached_response, store_response
from collections import defaultdict
import requests
import re

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
async def chat_endpoint(request: Request, model: str = Query(...), ignore_cache: bool = Query(False)):
    from models.groq_handler import GroqHandler
    from models.gemini_handler import GeminiHandler
    body = await request.json()
    prompt = body.get('prompt')
    template = body.get('template')
    template_id = body.get('template_id')
    template_vars = body.get('template_vars', {})
    # Prompt Template Logic
    if template_id:
        # Load templates as list
        with open('prompt_templates.json', 'r', encoding='utf-8') as f:
            templates = json.load(f)
        template_obj = next((t for t in templates if t['id'] == template_id), None)
        if not template_obj:
            raise HTTPException(status_code=400, detail=f'Template id {template_id} not found')
        # Substitute variables in template
        def sub_vars(tmpl, vars):
            def repl(match):
                key = match.group(1)
                return str(vars.get(key, f'{{{{{key}}}}}'))
            return re.sub(r'\{\{(.*?)\}\}', repl, tmpl)
        prompt = sub_vars(template_obj['prompt'], template_vars)
    elif template and template in PROMPT_TEMPLATES:
        prompt = PROMPT_TEMPLATES[template].replace('{prompt}', prompt)
    if not prompt:
        raise HTTPException(status_code=400, detail='Missing prompt')
    # Check cache first unless ignore_cache is True
    if not ignore_cache:
        cached_response, cached_timestamp = get_cached_response(prompt, model)
        if cached_response is not None:
            timestamp = cached_timestamp.isoformat() if cached_timestamp else None
            prompt_id = get_prompt_id(timestamp, prompt, model)
            log_interaction(timestamp, prompt, model, cached_response, 0, None, prompt_id, from_cache=True)
            return JSONResponse({
                'prompt_id': prompt_id,
                'model_used': model,
                'response_text': cached_response,
                'latency_ms': 0,
                'token_count': None,
                'from_cache': True
            })
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
    # Store in cache
    store_response(prompt, model_used, response_text, datetime.utcnow())
    log_interaction(timestamp, prompt, model_used, response_text, latency_ms, token_count, prompt_id, from_cache=False)
    return JSONResponse({
        'prompt_id': prompt_id,
        'model_used': model_used,
        'response_text': response_text,
        'latency_ms': latency_ms,
        'token_count': token_count,
        'from_cache': False
    })

@app.get('/models')
def list_models():
    return {
        "available_models": [
            "llama-3.1-8b-instant",  # via Groq
            "llama-3.3-70b-versatile",  # via Groq
            "deepseek-r1-distill-llama-70b",  # via Groq
            "meta-llama/llama-4-maverick-17b-128e-instruct",  # via Groq
            "meta-llama/llama-4-scout-17b-16e-instruct",  # via Groq
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
async def rate_endpoint(payload: dict):
    # Expects: {"prompt_id": ..., "model": ..., "rating": ..., "feedback": ...}
    prompt_id = payload.get('prompt_id')
    model = payload.get('model')
    rating = payload.get('rating')
    feedback = payload.get('feedback')
    if not (prompt_id and model and rating is not None):
        raise HTTPException(status_code=400, detail='Missing required fields')
    log_rating_v2(prompt_id, model, rating, feedback)
    return {'status': 'ok', 'prompt_id': prompt_id, 'model': model, 'rating': rating, 'feedback': feedback}

@app.get('/stats')
def stats_endpoint():
    import os
    import json
    import csv
    # Model usage and latency from prompts.json
    prompts_path = os.path.join('logs', 'prompts.json')
    ratings_path = os.path.join('logs', 'ratings.json')
    model_usage = defaultdict(int)
    latency_sum = defaultdict(float)
    latency_count = defaultdict(int)
    fallback_count = 0
    total_prompts = 0
    avg_rating = defaultdict(float)
    rating_count = defaultdict(int)
    # Prompts
    if os.path.exists(prompts_path):
        with open(prompts_path, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
        for entry in prompts:
            model = entry.get('model')
            model_usage[model] += 1
            total_prompts += 1
            latency = entry.get('latency_ms')
            if latency is not None:
                latency_sum[model] += float(latency) / 1000.0
                latency_count[model] += 1
            if entry.get('fallback_used'):
                fallback_count += 1
    # Ratings
    if os.path.exists(ratings_path):
        with open(ratings_path, 'r', encoding='utf-8') as f:
            ratings = json.load(f)
        for entry in ratings:
            model = entry.get('model')
            rating = entry.get('rating')
            if model and rating is not None:
                avg_rating[model] += float(rating)
                rating_count[model] += 1
    avg_latency = {m: (latency_sum[m] / latency_count[m]) if latency_count[m] else 0 for m in model_usage}
    avg_rating_out = {m: (avg_rating[m] / rating_count[m]) if rating_count[m] else 0 for m in model_usage}
    return {
        'model_usage': dict(model_usage),
        'avg_latency': avg_latency,
        'avg_rating': avg_rating_out,
        'total_fallbacks': fallback_count,
        'total_prompts': total_prompts
    } 