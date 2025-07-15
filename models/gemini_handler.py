import os
import google.generativeai as genai

class GeminiHandler:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=self.api_key)
        self.model = os.getenv('GEMINI_MODEL', 'gemini-pro')

    def generate(self, prompt: str) -> str:
        model = genai.GenerativeModel(self.model)
        response = model.generate_content(prompt)
        return response.text.strip() if hasattr(response, 'text') else str(response) 