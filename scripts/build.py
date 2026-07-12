"""Archive 빌드 조립 — data/*.json 3종을 템플릿에 인라인해 단일 HTML 산출."""
import base64
import html as html_mod
import json
import math
from pathlib import Path

from config import EGO_DISPLAY_N, TOPN_MAX

ROOT = Path(__file__).parent.parent
TEMPLATE = ROOT / "archive" / "template.html"

# "이렇게 만들었어요" 표본 인물 — 실데이터로 갈아탈 때 PPT/md 주인공의 id로 바꾼다
ABOUT_ANCHOR_ID = 0


def build_about(persons, neighbors, embeddings):
    """앵커 1명의 실벡터 + 전원 코사인에서 1위/중간/최하 비교 3명 + top-K 페이로드."""
    name_by_id = {p["id"]: p["name"] for p in persons}
    ids = [p["id"] for p in persons]

    def unit(v):
        n = math.hypot(*v)
        return [x / n for x in v]

    anchor_u = unit(embeddings[str(ABOUT_ANCHOR_ID)])
    scored = sorted(
        ((round(math.sumprod(anchor_u, unit(embeddings[str(i)])), 4), i)
         for i in ids if i != ABOUT_ANCHOR_ID and str(i) in embeddings),
        reverse=True,
    )
    picks = [
        (scored[0], "유사 1위"),
        (scored[len(scored) // 2], f"중간 ({len(scored) // 2 + 1}위)"),
        (scored[-1], f"최하위 ({len(scored)}위)"),
    ]
    round3 = lambda v: [round(x, 3) for x in v]
    return {
        "anchor": {"name": name_by_id[ABOUT_ANCHOR_ID], "vec": round3(embeddings[str(ABOUT_ANCHOR_ID)])},
        "compares": [
            {"name": name_by_id[i], "label": label, "sim": s, "vec": round3(embeddings[str(i)])}
            for (s, i), label in picks
        ],
        "topk": [
            {"name": name_by_id[e["id"]], "sim": e["similarity"]}
            for e in neighbors.get(str(ABOUT_ANCHOR_ID), [])
        ],
    }


def about_slots(html):
    """archive/about/의 ppt.png·sample.md가 있으면 인라인, 없으면 플레이스홀더."""
    ppt = ROOT / "archive" / "about" / "ppt.png"
    if ppt.exists():
        uri = "data:image/png;base64," + base64.b64encode(ppt.read_bytes()).decode()
        ppt_html = f'<img class="slot-img" src="{uri}" alt="근원경쟁력 회고 PPT 캡처" />'
    else:
        ppt_html = ('<div class="slot-placeholder">PPT 캡처 자리<br>'
                    '<code>archive/about/ppt.png</code> 추가 후 재빌드하면 여기에 인라인됩니다</div>')
    html = html.replace("<!--__ABOUT_PPT__-->", ppt_html)

    md = ROOT / "archive" / "about" / "sample.md"
    if md.exists():
        md_html = f'<pre class="md-slot">{html_mod.escape(md.read_text())}</pre>'
    else:
        md_html = ('<div class="slot-placeholder">변환된 md 원문 자리<br>'
                   '<code>archive/about/sample.md</code> 추가 후 재빌드하면 여기에 인라인됩니다</div>')
    return html.replace("<!--__ABOUT_MD__-->", md_html)


def build(data_dir=ROOT / "data", out_path=ROOT / "dist" / "heritage-archive.html"):
    data_dir = Path(data_dir)
    persons = json.loads((data_dir / "persons.json").read_text())
    neighbors = json.loads((data_dir / "neighbors.json").read_text())
    freq = json.loads((data_dir / "freq.json").read_text())

    # 템플릿 JS는 프로토타입 필드명(team/w)을 쓰므로 스키마 필드에 별칭을 얹는다
    # ponytail: 별칭 대신 템플릿 JS 전체 개명은 화면 확장이 끝나는 시점에 정리
    nodes = [dict(p, team=p["pjt"]) for p in persons]
    # 임베딩 실패 등으로 neighbors에 빠진 인물은 빈 이웃으로 채워 JS가 죽지 않게 한다
    nb = {
        str(p["id"]): [{"id": e["id"], "w": e["similarity"]} for e in neighbors.get(str(p["id"]), [])]
        for p in persons
    }

    html = TEMPLATE.read_text()
    html = html.replace("/*__ECHARTS_JS__*/", (ROOT / "archive" / "echarts.min.js").read_text())
    html = html.replace("/*__ECHARTS_WORDCLOUD_JS__*/", (ROOT / "archive" / "echarts-wordcloud.min.js").read_text())
    html = html.replace("/*__CLOUD_LOGIC_JS__*/", (ROOT / "archive" / "cloud_logic.js").read_text())
    html = html.replace("/*__DATA__*/null", json.dumps({"nodes": nodes, "neighbors": nb}, ensure_ascii=False))
    html = html.replace("/*__FREQ__*/null", json.dumps(freq, ensure_ascii=False))
    emb_path = data_dir / "embeddings.json"
    if emb_path.exists():
        embeddings = json.loads(emb_path.read_text())
        html = html.replace("/*__ABOUT__*/null", json.dumps(build_about(persons, neighbors, embeddings), ensure_ascii=False))
    else:
        html = html.replace("/*__ABOUT__*/null", "null")
    html = about_slots(html)
    html = html.replace("/*__EGO_DISPLAY_N__*/10", str(EGO_DISPLAY_N))
    html = html.replace('max="__TOPN_MAX__"', f'max="{TOPN_MAX}"')

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    return out_path


if __name__ == "__main__":
    print(build())
