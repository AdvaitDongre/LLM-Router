import os
import requests

class GroqHandler:
    def __init__(self, model_override=None):
        self.api_key = os.getenv('GROQ_API_KEY')
        self.api_url = os.getenv('GROQ_API_URL', 'https://api.groq.com/openai/v1/chat/completions')
        self.model = model_override
        if not self.api_key:
            raise ValueError('GROQ_API_KEY is not set in environment')
        if not self.model:
            raise ValueError('No model specified for GroqHandler')

    def generate(self, prompt: str):
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        data = {
            'model': self.model,
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 512,
            'temperature': 0.7
        }
        response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
        try:
            response.raise_for_status()
        except requests.HTTPError:
            try:
                err_json = response.json()
                err_msg = err_json.get('error', {}).get('message', str(err_json))
            except Exception:
                err_msg = response.text
            raise RuntimeError(f'Groq API error for model {self.model}: {err_msg}')
        result = response.json()
        text = result['choices'][0]['message']['content'].strip()
        token_count = result.get('usage', {}).get('total_tokens')
        return text, token_count 