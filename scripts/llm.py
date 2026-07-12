"""LLM API 호출 래퍼. 텍스트 생성(태그)과 임베딩을 독립적인 API로 관리."""
import os
import time

# 텍스트 생성 (태그 추출용)
_text_provider = None
_text_gemini_client = None
_text_openai_client = None

# 임베딩
_embed_provider = None
_embed_gemini_client = None
_embed_openai_client = None

def init():
    """텍스트 생성과 임베딩을 독립적으로 초기화.

    텍스트 생성: TEXT_PROVIDER (gemini|openai_compat|internal) + TEXT_API_KEY, TEXT_API_BASE
    임베딩: EMBED_PROVIDER (gemini|openai_compat|internal) + EMBED_API_KEY, EMBED_API_BASE

    기본값: 둘 다 gemini (GEMINI_API_KEY 사용)
    """
    global _text_provider, _text_gemini_client, _text_openai_client
    global _embed_provider, _embed_gemini_client, _embed_openai_client

    # 텍스트 생성
    _text_provider = os.getenv("TEXT_PROVIDER", os.getenv("LLM_PROVIDER", "gemini")).lower()
    _init_text_provider(_text_provider)

    # 임베딩
    _embed_provider = os.getenv("EMBED_PROVIDER", os.getenv("LLM_PROVIDER", "gemini")).lower()
    _init_embed_provider(_embed_provider)

def _init_text_provider(provider):
    global _text_gemini_client, _text_openai_client
    if provider == "gemini":
        import google.generativeai as genai
        api_key = os.getenv("TEXT_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("텍스트 생성(Gemini) 선택 시 GEMINI_API_KEY 또는 TEXT_API_KEY 환경변수 필수")
        genai.configure(api_key=api_key)
        _text_gemini_client = genai
    elif provider in ("openai_compat", "internal"):
        from openai import OpenAI
        api_key = os.getenv("TEXT_API_KEY")
        api_base = os.getenv("TEXT_API_BASE", "http://localhost:8000/v1")
        if not api_key:
            raise ValueError(f"텍스트 생성({provider}) 선택 시 TEXT_API_KEY 환경변수 필수")
        _text_openai_client = OpenAI(api_key=api_key, base_url=api_base)
    else:
        raise ValueError(f"Unknown TEXT_PROVIDER: {provider}")

def _init_embed_provider(provider):
    global _embed_gemini_client, _embed_openai_client
    if provider == "gemini":
        import google.generativeai as genai
        api_key = os.getenv("EMBED_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("임베딩(Gemini) 선택 시 GEMINI_API_KEY 또는 EMBED_API_KEY 환경변수 필수")
        genai.configure(api_key=api_key)
        _embed_gemini_client = genai
    elif provider in ("openai_compat", "internal"):
        from openai import OpenAI
        api_key = os.getenv("EMBED_API_KEY")
        api_base = os.getenv("EMBED_API_BASE", "http://localhost:8000/v1")
        if not api_key:
            raise ValueError(f"임베딩({provider}) 선택 시 EMBED_API_KEY 환경변수 필수")
        _embed_openai_client = OpenAI(api_key=api_key, base_url=api_base)
    else:
        raise ValueError(f"Unknown EMBED_PROVIDER: {provider}")

def call_gemini(prompt, model="models/gemini-2.5-flash", max_retries=5):
    """텍스트 생성 (태그 추출용). 기존 인터페이스 유지."""
    if _text_provider != "gemini":
        return _call_openai_text(prompt, model, max_retries)

    model_obj = _text_gemini_client.GenerativeModel(model)
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

def _call_openai_text(prompt, model="gpt-3.5-turbo", max_retries=5):
    """OpenAI Compatible 텍스트 생성."""
    for attempt in range(max_retries):
        try:
            response = _text_openai_client.chat.completions.create(
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
    if _embed_provider != "gemini":
        return _embed_openai_text(text, model, max_retries)

    for attempt in range(max_retries):
        try:
            result = _embed_gemini_client.embed_content(model=model, content=text)
            return result['embedding']
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                wait = 2 ** attempt
                print(f"⏳ Embedding Rate limit, {wait}초 대기... ({attempt + 1}/{max_retries})", flush=True)
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"Max retries ({max_retries}) exceeded for embedding")

def _embed_openai_text(text, model="text-embedding-3-small", max_retries=5):
    """OpenAI Compatible 임베딩."""
    for attempt in range(max_retries):
        try:
            response = _embed_openai_client.embeddings.create(
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
