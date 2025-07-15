import os
import google.generativeai as genai

class GeminiHandler:
    def __init__(self, model_override=None):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError('GEMINI_API_KEY is not set in environment')
        genai.configure(api_key=self.api_key)
        self.model = model_override
        if not self.model:
            raise ValueError('No model specified for GeminiHandler')

    def generate(self, prompt: str):
        model = genai.GenerativeModel(self.model)
        response = model.generate_content(prompt)
        text = response.text.strip() if hasattr(response, 'text') else str(response)
        # Try to get token count from response.usage_metadata if available
        token_count = None
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            token_count = getattr(response.usage_metadata, 'total_token_count', None)
        return text, token_count 