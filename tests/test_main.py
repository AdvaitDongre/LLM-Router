import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app

client = TestClient(app)

@pytest.fixture
def mock_groq():
    with patch('models.groq_handler.GroqHandler.generate', return_value='groq response'):
        yield

@pytest.fixture
def mock_gemini():
    with patch('models.gemini_handler.GeminiHandler.generate', return_value='gemini response'):
        yield

def test_chat_groq(mock_groq):
    resp = client.post('/chat?model=groq', json={'prompt': 'Hello'})
    assert resp.status_code == 200
    data = resp.json()
    assert data['model_used'] == 'groq'
    assert 'response_text' in data
    assert data['response_text'] == 'groq response'
    assert 'latency_ms' in data
    assert 'token_count' in data

def test_chat_gemini(mock_gemini):
    resp = client.post('/chat?model=gemini', json={'prompt': 'Hi'})
    assert resp.status_code == 200
    data = resp.json()
    assert data['model_used'] == 'gemini'
    assert 'response_text' in data
    assert data['response_text'] == 'gemini response'
    assert 'latency_ms' in data
    assert 'token_count' in data

def test_chat_fallback(mock_groq, mock_gemini):
    with patch('models.groq_handler.GroqHandler.generate', side_effect=Exception('fail')):
        resp = client.post('/chat?model=groq', json={'prompt': 'Fallback'})
        assert resp.status_code == 200
        data = resp.json()
        assert data['model_used'] == 'gemini'
        assert data['response_text'] == 'gemini response'

def test_rate():
    # Insert a fake prompt_id into the log first
    from utils.logger import log_interaction, get_prompt_id
    import datetime
    prompt = 'test prompt'
    model = 'groq'
    timestamp = datetime.datetime.utcnow().isoformat()
    prompt_id = get_prompt_id(timestamp, prompt, model)
    log_interaction(timestamp, prompt, model, 'test response', 123, 10, prompt_id)
    resp = client.post(f'/rate?prompt_id={prompt_id}&score=4')
    assert resp.status_code == 200
    assert resp.json()['score'] == 4 