"""LLM API 호출 래퍼 (Gemini + OpenAI Compatible)."""
import os
import time

_provider = None
_gemini_client = None
_openai_client = None

def init():
    """API 키 및 provider 설정. LLM_PROVIDER 환경변수로 선택 (gemini|openai_compat|internal)."""
    global _provider, _gemini_client, _openai_client
    _provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    if _provider == "gemini":
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Gemini 선택 시 GEMINI_API_KEY 환경변수 필수")
        genai.configure(api_key=api_key)
        _gemini_client = genai

    elif _provider in ("openai_compat", "internal"):
        from openai import OpenAI
        api_key = os.getenv("LLM_API_KEY")
        api_base = os.getenv("LLM_API_BASE", "http://localhost:8000/v1")
        if not api_key:
            raise ValueError(f"{_provider} 선택 시 LLM_API_KEY 환경변수 필수")
        _openai_client = OpenAI(api_key=api_key, base_url=api_base)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {_provider}")

def call_gemini(prompt, model="models/gemini-2.5-flash", max_retries=5):
    """Gemini로 텍스트 생성. 기존 인터페이스 유지."""
    if _provider != "gemini":
        return _call_openai_compatible(prompt, model, max_retries)

    model_obj = _gemini_client.GenerativeModel(model)
    for attempt in range(max_retries):
        try:
            response = model_obj.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                wait = 2 ** attempt
                print(f"⏳ Rate limit, {wait}초 대기... ({attempt + 1}/{max_retries})", flush=True)
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"Max retries ({max_retries}) exceeded")

def _call_openai_compatible(prompt, model="gpt-3.5-turbo", max_retries=5):
    """OpenAI Compatible API 호출."""
    for attempt in range(max_retries):
        try:
            response = _openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                wait = 2 ** attempt
                print(f"⏳ Rate limit, {wait}초 대기... ({attempt + 1}/{max_retries})", flush=True)
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"Max retries ({max_retries}) exceeded")

def embed_text(text, model="models/gemini-embedding-2", max_retries=5):
    """텍스트를 벡터로 임베딩. 기존 인터페이스 유지."""
    if _provider != "gemini":
        return _embed_openai_compatible(text, model, max_retries)

    for attempt in range(max_retries):
        try:
            result = _gemini_client.embed_content(model=model, content=text)
            return result['embedding']
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                wait = 2 ** attempt
                print(f"⏳ Embedding Rate limit, {wait}초 대기... ({attempt + 1}/{max_retries})", flush=True)
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"Max retries ({max_retries}) exceeded for embedding")

def _embed_openai_compatible(text, model="text-embedding-3-small", max_retries=5):
    """OpenAI Compatible 임베딩 호출."""
    for attempt in range(max_retries):
        try:
            response = _openai_client.embeddings.create(
                model=model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                wait = 2 ** attempt
                print(f"⏳ Embedding Rate limit, {wait}초 대기... ({attempt + 1}/{max_retries})", flush=True)
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"Max retries ({max_retries}) exceeded for embedding")

if __name__ == "__main__":
    init()
    print(call_gemini("안녕하세요"))
