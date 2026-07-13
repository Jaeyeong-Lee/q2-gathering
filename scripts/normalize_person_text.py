"""정제 전 사람별 회고 원문 → LLM으로 스키마 마크다운 정제 (좁은 스코프, 사람 1명 = 1콜).

scripts/llm.py의 openai_compat/internal provider(사내망 로컬 모델)를 그대로 재사용.
매니페스트(split_md_by_person.py 산출물)에서 status=정상인 사람만 대상으로 한다.
"""
import csv
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent

PROMPT = """다음은 한 구성원의 근원경쟁력 회고 원문(PPT 발췌, 정리 안 됨)이다.
아래 마크다운 형식으로 다듬어 그 형식만 답하라:

# 근원경쟁력

## 핵심 역량
...

## 주요 경력
...

## 강점
...

원문:
{raw}"""


def normalize_all(rows, raw_dir, call, retries=1, delay=0.5):
    """status=정상 & 미정제 행만 대상, 사람별 1콜, 실패한 사람만 개별 재시도.

    rows는 in-place로 normalized_filename이 채워진다 (실패자는 빈 값 유지).
    반환: 실패한 name 목록.
    """
    raw_dir = Path(raw_dir)
    failed = []
    targets = [r for r in rows if r["status"] == "정상" and not r.get("normalized_filename")]
    for i, r in enumerate(targets):
        raw_path = raw_dir / r["split_filename"]
        raw_text = raw_path.read_text(encoding="utf-8")
        for attempt in range(1 + retries):
            try:
                result = call(PROMPT.format(raw=raw_text))
                out_name = raw_path.stem + ".normalized.md"
                (raw_dir / out_name).write_text(result, encoding="utf-8")
                r["normalized_filename"] = out_name
                if i % 10 == 9:
                    print(f"정제: {i + 1}/{len(targets)}", file=sys.stderr)
                break
            except Exception:
                if attempt == retries:
                    failed.append(r["name"])
        if delay > 0:
            time.sleep(delay)
    return failed


def main(manifest_path=ROOT / "data" / "split_manifest.csv", raw_dir=ROOT / "data" / "raw_sections",
         call=None, retries=1, delay=0.5):
    """매니페스트의 normalized_filename을 채운다. 실패자는 다음 실행에서 재시도 대상으로 남는다."""
    if call is None:
        raise SystemExit("LLM 호출 함수 미연결 — call 파라미터에 실제 호출부(llm.call_gemini 등)를 꽂아 실행")
    manifest_path = Path(manifest_path)
    with open(manifest_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    failed = normalize_all(rows, raw_dir, call, retries=retries, delay=delay)

    with open(manifest_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    if failed:
        print(f"정제 실패 {len(failed)}명 (다음 실행에서 재시도 대상): {failed}", file=sys.stderr)
    return failed


if __name__ == "__main__":
    import llm
    llm.init()
    main(call=llm.call_gemini)
