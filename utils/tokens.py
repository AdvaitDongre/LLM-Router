def estimate_token_count(text: str) -> int:
    try:
        import tiktoken
        enc = tiktoken.get_encoding('cl100k_base')
        return len(enc.encode(text))
    except Exception:
        # Fallback: 1 token ≈ 4 chars (OpenAI heuristic)
        return max(1, len(text) // 4) 