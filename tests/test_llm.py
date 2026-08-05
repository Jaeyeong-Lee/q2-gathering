import llm


def test_text_call_uses_td_text_model_env(monkeypatch):
    monkeypatch.setenv("TD_TEXT_MODEL", "internal-text-model")
    captured = {}

    def fake_call_gemini(prompt, model="models/gemini-2.5-flash", max_retries=5):
        captured["model"] = model
        return "ok"

    monkeypatch.setattr(llm, "call_gemini", fake_call_gemini)
    call = llm.text_call()
    assert call("prompt") == "ok"
    assert captured["model"] == "internal-text-model"


def test_text_call_falls_back_to_default_without_env(monkeypatch):
    monkeypatch.delenv("TD_TEXT_MODEL", raising=False)
    assert llm.text_call() is llm.call_gemini


def test_embed_call_uses_td_embed_model_env(monkeypatch):
    monkeypatch.setenv("TD_EMBED_MODEL", "internal-embed-model")
    captured = {}

    def fake_embed_text(text, model="models/gemini-embedding-2", max_retries=5):
        captured["model"] = model
        return [0.1]

    monkeypatch.setattr(llm, "embed_text", fake_embed_text)
    embed = llm.embed_call()
    assert embed("text") == [0.1]
    assert captured["model"] == "internal-embed-model"


def test_embed_call_falls_back_to_default_without_env(monkeypatch):
    monkeypatch.delenv("TD_EMBED_MODEL", raising=False)
    assert llm.embed_call() is llm.embed_text
