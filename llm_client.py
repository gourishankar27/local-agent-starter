# llm_client.py
"""
Small abstraction for LLM calls. By default supports OpenAI (via openai package)
and a local "echo" provider for testing.

The interface exposes `generate(prompt, max_tokens, ...)` and returns a string.
"""
import os
import json
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai')

if LLM_PROVIDER == 'openai':
    import openai
    openai.api_key = os.getenv('OPENAI_API_KEY')
    if os.getenv('OPENAI_API_BASE'):
        openai.api_base = os.getenv('OPENAI_API_BASE')


class LLMClient:
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or LLM_PROVIDER

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.2) -> str:
        if self.provider == 'openai':
            resp = openai.ChatCompletion.create(
                model='gpt-4o-mini' if hasattr(openai, 'ChatCompletion') else 'gpt-4o-mini',
                messages=[{'role': 'user', 'content': prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            # This handles both ChatCompletion or legacy responses
            if 'choices' in resp and len(resp.choices) > 0:
                return resp.choices[0].message.content.strip()
            return str(resp)
        # local echo/debug provider
        return f"[LOCAL_ECHO]\n{prompt[:1000]}"

if __name__ == '__main__':
    c = LLMClient()
    print(c.generate('Say hello in one sentence.'))
