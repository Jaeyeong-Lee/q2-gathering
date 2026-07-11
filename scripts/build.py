"""Archive 빌드 조립 — data/*.json 3종을 템플릿에 인라인해 단일 HTML 산출."""
import json
from pathlib import Path

from config import EGO_DISPLAY_N, TOPN_MAX

ROOT = Path(__file__).parent.parent
TEMPLATE = ROOT / "archive" / "template.html"


def build(data_dir=ROOT / "data", out_path=ROOT / "dist" / "heritage-archive.html"):
    data_dir = Path(data_dir)
    persons = json.loads((data_dir / "persons.json").read_text())
    neighbors = json.loads((data_dir / "neighbors.json").read_text())
    freq = json.loads((data_dir / "freq.json").read_text())

    # 템플릿 JS는 프로토타입 필드명(team/w)을 쓰므로 스키마 필드에 별칭을 얹는다
    # ponytail: 별칭 대신 템플릿 JS 전체 개명은 화면 확장이 끝나는 시점에 정리
    nodes = [dict(p, team=p["pjt"]) for p in persons]
    nb = {k: [{"id": e["id"], "w": e["similarity"]} for e in v] for k, v in neighbors.items()}

    html = TEMPLATE.read_text()
    html = html.replace("/*__WORDCLOUD2_JS__*/", (ROOT / "archive" / "wordcloud2.min.js").read_text())
    html = html.replace("/*__CLOUD_LOGIC_JS__*/", (ROOT / "archive" / "cloud_logic.js").read_text())
    html = html.replace("/*__DATA__*/null", json.dumps({"nodes": nodes, "neighbors": nb}, ensure_ascii=False))
    html = html.replace("/*__FREQ__*/null", json.dumps(freq, ensure_ascii=False))
    html = html.replace("/*__EGO_DISPLAY_N__*/10", str(EGO_DISPLAY_N))
    html = html.replace('max="__TOPN_MAX__"', f'max="{TOPN_MAX}"')

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    return out_path


if __name__ == "__main__":
    print(build())
