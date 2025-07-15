def estimate_token_count(text: str, model: str = None) -> int:
    try:
        import tiktoken
        enc = tiktoken.get_encoding('cl100k_base')
        return len(enc.encode(text))
    except Exception:
        # Model-specific heuristics by prefix
        if model and model.startswith('gemini'):
            # Gemini models: 1 token ≈ 3.5 chars (free tier)
            return max(1, len(text) // 3.5)
        elif model and model.startswith('llama-3.1-8b'):
            # Llama-3.1-8b models: 1 token ≈ 4 chars
            return max(1, len(text) // 4)
        # Add more model heuristics here as needed
        else:
            # Default fallback
            return max(1, len(text) // 4) 