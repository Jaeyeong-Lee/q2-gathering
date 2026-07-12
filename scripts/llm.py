"""Gemini API 호출 래퍼."""
import os
import time
import google.generativeai as genai

def init():
    """API 키 설정."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경변수 필수")
    genai.configure(api_key=api_key)

def call_gemini(prompt, model="models/gemini-2.5-flash", max_retries=5):
    """Gemini로 텍스트 생성 호출 (리트라이 + 백오프)."""
    model_obj = genai.GenerativeModel(model)
    for attempt in range(max_retries):
        try:
            response = model_obj.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                wait = 2 ** attempt  # 1, 2, 4, 8, 16초
                print(f"⏳ Rate limit, {wait}초 대기... ({attempt + 1}/{max_retries})", flush=True)
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"Max retries ({max_retries}) exceeded")

def embed_text(text, model="models/gemini-embedding-2", max_retries=5):
    """텍스트를 벡터로 임베딩 (리트라이 + 백오프)."""
    for attempt in range(max_retries):
        try:
            result = genai.embed_content(model=model, content=text)
            return result['embedding']
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                wait = 2 ** attempt  # 1, 2, 4, 8, 16초
                print(f"⏳ Embedding Rate limit, {wait}초 대기... ({attempt + 1}/{max_retries})", flush=True)
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"Max retries ({max_retries}) exceeded for embedding")

if __name__ == "__main__":
    init()
    print(call_gemini("안녕하세요"))
