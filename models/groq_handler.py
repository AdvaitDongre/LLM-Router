import os
import requests

class GroqHandler:
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        self.api_url = os.getenv('GROQ_API_URL', 'https://api.groq.com/openai/v1/chat/completions')
        self.model = os.getenv('GROQ_MODEL', 'mistral-7b')

    def generate(self, prompt: str) -> str:
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
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content'].strip() 