"""Archive 빌드 조립 — data/*.json 3종을 템플릿에 인라인해 단일 HTML 산출."""
import base64
import html as html_mod
import json
import math
from pathlib import Path

from config import TOPN_MAX

ROOT = Path(__file__).parent.parent
TEMPLATE = ROOT / "archive" / "template.html"

# "이렇게 만들었어요" 표본 인물 — 실데이터로 갈아탈 때 PPT/md 주인공의 id로 바꾼다
ABOUT_ANCHOR_ID = 0


def unit(v):
    n = math.hypot(*v)
    return [x / n for x in v]


def build_about(persons, neighbors, embeddings):
    """앵커 1명의 실벡터 + 전원 코사인에서 1위/중간/최하 비교 3명 + top-K 페이로드."""
    name_by_id = {p["id"]: p["name"] for p in persons}
    ids = [p["id"] for p in persons]

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


def build_tasks(vectors, clusters, wiki_dir):
    """과제 문장 그래프 페이로드 (#10): 노드=군집 items, 엣지 재료=벡터 top-K,
    외톨이=군집 중심 코사인이 (평균-표준편차) 미만인 문장(총평 소수 의견과 짝).
    빈 평면(항목 0건)이면 None — 호출부가 null을 주입해 토글을 숨긴다."""
    from similarity import top_k_neighbors

    # ponytail: (person_id, text)로 벡터 재결합 — vectors/clusters가 같은 run_all 산출이라는
    # 가정. 스테이지 캐시가 어긋나면 KeyError로 죽는 게 맞다(조용한 오배치보다 낫다)
    pool = {}
    for v in vectors:
        pool.setdefault((v["person_id"], v["text"]), []).append(v["vec"])
    nodes, vecs = [], []
    for c in clusters:
        for it in c["items"]:
            nodes.append({"id": len(nodes), "cluster": c["cluster_id"],
                          "person_id": it["person_id"], "name": it["name"],
                          "cl": it.get("cl_level", ""), "horizon": it.get("horizon", "불명"),
                          "text": it["text"], "quotes": it.get("quotes", [])})
            vecs.append(pool[(it["person_id"], it["text"])].pop(0))
    if not nodes:
        return None

    neighbors = {
        i: [{"id": e["id"], "w": e["similarity"]} for e in nb]
        for i, nb in top_k_neighbors({i: v for i, v in enumerate(vecs)}, k=6).items()
    }

    units = [unit(v) for v in vecs]
    cent = {}
    for n, u in zip(nodes, units):
        c = cent.setdefault(n["cluster"], [0.0] * len(u))
        for i, x in enumerate(u):
            c[i] += x
    for cid in cent:
        cent[cid] = unit(cent[cid])
    sims = [math.sumprod(u, cent[n["cluster"]]) for n, u in zip(nodes, units)]
    mean = sum(sims) / len(sims)
    std = math.sqrt(sum((s - mean) ** 2 for s in sims) / len(sims))
    # ponytail: 전역 평균-1σ 문턱 — 실데이터에서 표시가 과소/과다하면 군집별 문턱으로
    for n, s in zip(nodes, sims):
        n["outlier"] = s < mean - std

    clusters_meta = []
    for c in clusters:
        page = f"cluster-{c['cluster_id']:02d}.md"
        md = Path(wiki_dir) / page
        title = md.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip() if md.exists() \
            else f"군집 {c['cluster_id']}"
        clusters_meta.append({"id": c["cluster_id"], "title": title,
                              "page": "wiki/" + page, "count": len(c["items"])})
    return {"nodes": nodes, "neighbors": neighbors, "clusters": clusters_meta}


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
        md_html = f'<pre class="md-slot">{html_mod.escape(md.read_text(encoding="utf-8"))}</pre>'
    else:
        md_html = ('<div class="slot-placeholder">변환된 md 원문 자리<br>'
                   '<code>archive/about/sample.md</code> 추가 후 재빌드하면 여기에 인라인됩니다</div>')
    return html.replace("<!--__ABOUT_MD__-->", md_html)


def build(data_dir=ROOT / "data", out_path=ROOT / "dist" / "heritage-archive.html"):
    data_dir = Path(data_dir)
    persons = json.loads((data_dir / "persons.json").read_text(encoding="utf-8"))
    neighbors = json.loads((data_dir / "neighbors.json").read_text(encoding="utf-8"))
    freq = json.loads((data_dir / "freq.json").read_text(encoding="utf-8"))

    # 템플릿 JS는 프로토타입 필드명(team/w)을 쓰므로 스키마 필드에 별칭을 얹는다
    # ponytail: 별칭 대신 템플릿 JS 전체 개명은 화면 확장이 끝나는 시점에 정리
    nodes = [dict(p, team=p["pjt"]) for p in persons]
    # 임베딩 실패 등으로 neighbors에 빠진 인물은 빈 이웃으로 채워 JS가 죽지 않게 한다
    nb = {
        str(p["id"]): [{"id": e["id"], "w": e["similarity"]} for e in neighbors.get(str(p["id"]), [])]
        for p in persons
    }

    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("/*__ECHARTS_JS__*/", (ROOT / "archive" / "echarts.min.js").read_text(encoding="utf-8"))
    html = html.replace("/*__ECHARTS_WORDCLOUD_JS__*/", (ROOT / "archive" / "echarts-wordcloud.min.js").read_text(encoding="utf-8"))
    html = html.replace("/*__CLOUD_LOGIC_JS__*/", (ROOT / "archive" / "cloud_logic.js").read_text(encoding="utf-8"))
    html = html.replace("/*__DATA__*/null", json.dumps({"nodes": nodes, "neighbors": nb}, ensure_ascii=False))
    html = html.replace("/*__FREQ__*/null", json.dumps(freq, ensure_ascii=False))
    emb_path = data_dir / "embeddings.json"
    if emb_path.exists():
        embeddings = json.loads(emb_path.read_text(encoding="utf-8"))
        html = html.replace("/*__ABOUT__*/null", json.dumps(build_about(persons, neighbors, embeddings), ensure_ascii=False))
    else:
        html = html.replace("/*__ABOUT__*/null", "null")
    html = about_slots(html)
    html = html.replace('max="__TOPN_MAX__"', f'max="{TOPN_MAX}"')

    # 과제 문장 그래프 (#10): task-discovery 산출물이 있으면 주입, 없으면 null(토글 숨김)
    td = data_dir / "task_discovery"
    tasks = None
    if (td / "task_vectors.json").exists() and (td / "clusters.json").exists():
        tasks = build_tasks(json.loads((td / "task_vectors.json").read_text(encoding="utf-8")),
                            json.loads((td / "clusters.json").read_text(encoding="utf-8")),
                            Path(out_path).parent / "wiki")
    html = html.replace("/*__TASKS__*/null",
                        json.dumps(tasks, ensure_ascii=False) if tasks else "null")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


if __name__ == "__main__":
    print(build())
