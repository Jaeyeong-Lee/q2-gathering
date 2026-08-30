"""정적 화면 공용 렌더 헬퍼 (#012에서 #011을 흡수).

td_inspect·td_roadmap이 각자 복붙해 들고 있던 세 가지 — 페이로드 주입 이스케이프,
출력 경로 가드, CLI 인자 처리 — 를 한곳으로 모은다. 두 파일의 `ponytail:` 주석이
"세 번째 화면이 생기면 그때 옮긴다"고 트리거를 명시해 뒀고, 성좌 지도(#012)·히트맵(#018)·
질문 카드(#019)·임원 한 장(#020)이 생기면서 그 트리거가 발화했다.

화면 마크업(_TEMPLATE)은 각 스크립트가 계속 들고 있는다. 화면마다 달라질 이유가 없는 것만
여기 모은다.
"""
import json
from pathlib import Path

from pipeline_log import OUT_DIR
from td_common import reject_public_path


def embed_payload(payload):
    """</script>가 데이터에 있어도 HTML이 깨지지 않게 이스케이프. JSON 문자열 안에서
    \\u003c는 <와 같으므로 파서에는 영향이 없고, HTML 파서만 태그로 오인하지 않게 된다."""
    return (json.dumps(payload, ensure_ascii=False)
            .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))


def render(template, payload, **tokens):
    """__PAYLOAD__ 치환 + 화면별 추가 토큰(예: td_roadmap의 __LIVE__)."""
    html = template.replace("__PAYLOAD__", embed_payload(payload))
    for name, value in tokens.items():
        html = html.replace(f"__{name.upper()}__", value)
    return html


def write_html(html, out_path):
    """공개 배포 경로 가드를 먼저 태우고 파일로 쓴다."""
    reject_public_path(out_path)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


def parse_args(argv, default_name):
    """[데이터디렉터리] [출력경로] [--anonymize] → (data_dir, out_path, anonymize).

    기본 출력은 TD_OUT_DIR 안 — 리포에 쓰지 않는다.
    """
    args = [a for a in argv if a != "--anonymize"]
    data_dir = Path(args[0]) if len(args) > 0 else OUT_DIR / "task_discovery"
    out_path = Path(args[1]) if len(args) > 1 else data_dir / default_name
    return data_dir, out_path, "--anonymize" in argv
