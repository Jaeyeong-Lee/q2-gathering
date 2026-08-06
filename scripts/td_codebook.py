"""task-discovery S2 스테이지: 코드북 모듈 (S2-1, #23).

사람이 확정한 역량/방향 분류틀(코드북)을 로드·검증한다. 코드북은 사람이 직접 편집하는
JSON(tag_synonyms.json 선례): 범주마다 name·definition·inclusion + exclusion(선택).
초안 제안은 td_taxonomy.induce를 재사용 — 사람이 이후 편집·확정한다(S1 taxonomy를
코드북으로 승격하는 경로와 동일 메커니즘).
"""
import json
import sys
from pathlib import Path

import td_taxonomy

REQUIRED = ("name", "definition", "inclusion")


def load(path):
    """코드북 로드 + 검증. 필수 필드 누락·범주명 중복이면 ValueError.

    예외 메시지는 범주명 대신 **인덱스**로 가리킨다 — 범주명이 사내 제품 코드명일 수 있고
    이 메시지는 콘솔로 나가 그대로 옮겨지기 쉽다. 어느 범주인지는 파일에서 확인해라.
    """
    cats = json.loads(Path(path).read_text(encoding="utf-8"))
    names = set()
    for i, c in enumerate(cats):
        missing = [f for f in REQUIRED if not (c.get(f) or "").strip()]
        if missing:
            raise ValueError(f"코드북 {i}번 범주 필수 필드 누락: {missing}")
        if c["name"] in names:
            raise ValueError(f"코드북 {i}번 범주명이 앞과 중복")
        names.add(c["name"])
    return cats


def propose_draft(extracted, out_path, call, *, batch_size=30, sleep=None):
    """td_taxonomy로 초안 생성 → 코드북 스키마(inclusion, 빈 exclusion)로 저장.
    사람이 이후 추가·병합·삭제·개명·정의/제외기준 작성으로 확정한다."""
    taxo = td_taxonomy.induce(extracted, None, call, batch_size=batch_size, sleep=sleep)
    draft = [{"name": c["name"], "definition": c.get("definition", ""),
              "inclusion": c.get("inclusion_criteria", ""), "exclusion": ""} for c in taxo]
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(draft, ensure_ascii=False, indent=1), encoding="utf-8")
    return draft


if __name__ == "__main__":
    # 초안 제안 CLI: extracted.json → codebook_draft.json
    import llm
    from pathlib import Path as _P
    llm.init()
    ex = _P(sys.argv[1]) if len(sys.argv) > 1 else \
        _P(__file__).parent.parent / "data" / "task_discovery" / "extracted.json"
    out = ex.parent / "codebook_draft.json"
    d = propose_draft(ex, out, llm.call_gemini)
    print(f"코드북 초안 {len(d)}개 → {out} (사람이 편집·확정할 것)", file=sys.stderr)
