"""task-discovery 스테이지 2: taxonomy 유도 (S1-3, #18).

extracted.json의 facet들을 LLM이 배치 반복으로 읽어 역량/방향 taxonomy를 생성한다.
**임베딩 클러스터링을 카테고리화에 쓰지 않는다** — 도메인 용어 무지를 구조적으로 우회.
각 카테고리는 name·definition·inclusion_criteria. 카테고리 개수는 고정하지 않는다.

이 스테이지는 사내 LLM 생성 품질의 go/no-go 게이트다. 가짜 call 테스트는 코드가
병합·정제 응답을 잘 처리함만 증명 — 실제 생성 품질은 실 LLM 실행에서 사람이 판정한다.
LLM은 call(prompt)->str 주입, td_common.retry_call 재사용.
"""
import json
import sys
from pathlib import Path

from pipeline_log import get_logger
from td_common import iter_facets, load_json, retry_json

ROOT = Path(__file__).parent.parent
log = get_logger("td_taxonomy")

_REL_TYPES = {"broader", "related"}

_INSTRUCT = """너는 반도체 후공정 테스트 팀의 근원경쟁력 회고에서 뽑은 항목들을 읽고,
팀의 역량/방향 카테고리 taxonomy를 만든다. 카테고리 개수는 고정하지 말고 데이터가
자연스럽게 요구하는 만큼(대략 15~25개) 만든다. 각 카테고리는 name(짧은 명사구),
definition(1문장), inclusion_criteria(어떤 항목이 여기 들어오는지), relations(다른
카테고리와의 관계, 없으면 빈 배열)를 갖는다. relations의 각 항목은
{"to": "다른 카테고리 name", "type": "broader"|"related"} — broader는 이 카테고리가 to의
상위 개념일 때, related는 단순 연관일 때 쓴다. 확실하지 않으면 relations를 비워둬라.
JSON 객체로만 답하라: {"taxonomy": [{"name": "...", "definition": "...",
"inclusion_criteria": "...", "relations": [{"to": "...", "type": "broader"}]}]}"""


def _facet_texts(persons):
    """무신호 제외, 4축 항목 text 평면화 (공용 iter_facets)."""
    return [item["text"] for _, _, item in iter_facets(persons)]


def _normalize(taxo):
    """카테고리마다 필드를 보장(누락은 빈 문자열/빈 배열로 채움), name 없는 건 버린다.
    relations는 이 taxonomy 안의 다른 카테고리를 가리키는 것만 남긴다(댕글링·자기참조·
    잘못된 type 제거) — LLM이 이미 사라진 카테고리를 계속 가리키는 걸 방지."""
    out = []
    for c in taxo or []:
        name = (c.get("name") or "").strip()
        if not name:
            continue
        out.append({"name": name, "definition": c.get("definition", ""),
                    "inclusion_criteria": c.get("inclusion_criteria", ""),
                    "relations": c.get("relations") or []})
    names = {c["name"] for c in out}
    for c in out:
        rels = []
        for r in c["relations"]:
            to = (r.get("to") or "").strip() if isinstance(r, dict) else ""
            rtype = r.get("type") if isinstance(r, dict) else None
            if to and to != c["name"] and to in names and rtype in _REL_TYPES:
                rels.append({"to": to, "type": rtype})
        c["relations"] = rels
    return out


def _prompt(facets, existing):
    lines = "\n".join(f"- {t}" for t in facets)
    if existing:
        return (_INSTRUCT + "\n\n기존 taxonomy(병합·분할·정제 대상):\n"
                + json.dumps(existing, ensure_ascii=False)
                + "\n\n새 항목들:\n" + lines
                + "\n\n기존을 갱신한 전체 taxonomy를 반환하라(중복 카테고리 만들지 말 것).")
    return _INSTRUCT + "\n\n항목들:\n" + lines


def _progress_path(out_path):
    return out_path.parent / "taxonomy.progress.json"


def is_complete(out_path):
    """taxonomy.json이 끝까지 처리됐는지 — 존재만으로는 모른다(배치별 즉시저장이라 부분
    저장 상태로도 파일이 있을 수 있음). 진행 사이드카의 batches_done==total_batches로 판정.
    td_pipeline의 skip-if-exists 게이트가 부분 저장을 완료로 착각하지 않도록 이걸 쓴다."""
    out_path = Path(out_path)
    progress_path = _progress_path(out_path)
    if not out_path.exists() or not progress_path.exists():
        return False
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    return progress.get("batches_done") == progress.get("total_batches")


def induce(extracted, out_path, call, *, batch_size=30, attempts=4, sleep=None):
    """facet들을 배치 반복으로 LLM에 넣어 taxonomy 생성·정제. 반환: taxonomy(list).

    out_path가 있으면 배치마다 즉시 저장 + taxonomy.progress.json에 진행 상태를 남겨 중단된
    지점부터 재개한다. extracted가 경로로 주어지면 그 mtime을 사이드카와 비교 — 다르면
    (상류가 바뀜) 처음부터 다시 시작한다. 배치 하나가 재시도 끝에 실패하면 건너뛰지 않고
    그대로 전파해 스테이지를 중단한다 — taxonomy는 전체 facet을 봐야 의미가 있어서, 실패한
    배치를 조용히 건너뛰면 그만큼 누락된 채 정상 완료처럼 보이는 게 더 나쁘다.
    """
    persons = load_json(extracted)
    facets = _facet_texts(persons)
    kw = {"attempts": attempts} | ({"sleep": sleep} if sleep else {})

    out_path = Path(out_path) if out_path is not None else None
    progress_path = _progress_path(out_path) if out_path is not None else None
    extracted_mtime = Path(extracted).stat().st_mtime if isinstance(extracted, (str, Path)) else None

    batch_starts = list(range(0, len(facets), batch_size))
    total_batches = len(batch_starts)

    taxonomy, batches_done = [], 0
    if progress_path is not None and progress_path.exists() and out_path.exists():
        progress = json.loads(progress_path.read_text(encoding="utf-8"))
        if progress.get("extracted_mtime") == extracted_mtime:
            batches_done = progress.get("batches_done", 0)
            taxonomy = json.loads(out_path.read_text(encoding="utf-8"))
        # mtime이 다르면 상류가 바뀐 것 — batches_done=0/taxonomy=[] 그대로 둬 처음부터 재시작

    def save():
        if out_path is None:
            return
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(taxonomy, ensure_ascii=False, indent=1), encoding="utf-8")
        progress_path.write_text(json.dumps(
            {"batches_done": batches_done, "total_batches": total_batches,
             "extracted_mtime": extracted_mtime}, ensure_ascii=False, indent=1), encoding="utf-8")

    for batch_no, i in enumerate(batch_starts, start=1):
        if batch_no <= batches_done:
            continue
        batch = facets[i:i + batch_size]
        parsed = retry_json(call, _prompt(batch, taxonomy), stage="taxonomy", call_id=batch_no, **kw)
        taxonomy = _normalize(parsed.get("taxonomy"))
        batches_done = batch_no
        save()

    save()  # 무신호(배치 0개)거나 이미 완료 상태로 진입해도 항상 한 번은 저장 보장
    return taxonomy


def main(extracted_path=ROOT / "data" / "task_discovery" / "extracted.json"):
    import llm
    llm.init()
    out = Path(extracted_path).parent / "taxonomy.json"
    taxo = induce(extracted_path, out, llm.text_call())
    log.info(f"taxonomy {len(taxo)}개 생성 → {out}")


if __name__ == "__main__":
    main(*sys.argv[1:])
