"""task-discovery S4 스테이지: 하이브리드 질의 (S4-2, #27).

색인(td_index)에 대해 키워드 채널(어휘 정확 매칭) + 벡터 채널(의미 근접)을 각각 실행하고
순위 기반(RRF)으로 통합한다 — BM25 점수는 상한 없고 코사인은 0~1이라 단순 합산 금지.
전문 용어·약어는 키워드 채널이 잡고, 표현이 다른 동의는 벡터 채널이 잡아 임베딩 도메인
무지를 우회. 축·pjt·cl_level·horizon 필터 + 분포 집계(기여 인원=중복 제외)를 반환한다.
사전묶음·(후속)UI의 단일 진입점.
"""
from collections import Counter
from math import sqrt


def _tokens(text):
    return [t for t in text.replace("·", " ").split() if t]


def _keyword_scores(docs, q):
    """질의 토큰이 문서 text에 등장한 수. 0인 문서는 키워드 채널에서 제외."""
    qs = _tokens(q)
    scores = {}
    for i, d in enumerate(docs):
        s = sum(1 for t in qs if t in d["text"])
        if s > 0:
            scores[i] = s
    return scores


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = sqrt(sum(x * x for x in a)), sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _rank(score_map):
    """{idx: score} → {idx: rank(1부터)} 내림차순."""
    ranked = sorted(score_map, key=lambda i: -score_map[i])
    return {i: r + 1 for r, i in enumerate(ranked)}


def _matches(doc, axis, pjt, cl_level, horizon):
    return ((axis is None or doc["axis"] == axis)
            and (pjt is None or doc["pjt"] == pjt)
            and (cl_level is None or doc["cl_level"] == cl_level)
            and (horizon is None or doc["horizon"] == horizon))


def query(index, embed, q=None, *, axis=None, pjt=None, cl_level=None,
          horizon=None, top_k=10, rrf_k=60):
    """하이브리드 질의. q=None이면 필터만. 반환: {results, distribution}."""
    docs = [d for d in index.all() if _matches(d, axis, pjt, cl_level, horizon)]

    if q:
        kw_rank = _rank(_keyword_scores(docs, q))
        qvec = embed(q)
        vec_rank = _rank({i: _cosine(qvec, d["vec"]) for i, d in enumerate(docs)})
        fused = {}
        for i in set(kw_rank) | set(vec_rank):          # RRF: 순위 기반 통합
            fused[i] = (1 / (rrf_k + kw_rank[i]) if i in kw_rank else 0) + \
                       (1 / (rrf_k + vec_rank[i]) if i in vec_rank else 0)
        order = sorted(fused, key=lambda i: -fused[i])[:top_k]
        results = [docs[i] for i in order]
    else:
        results = docs[:top_k]

    return {"results": results, "distribution": _distribution(results)}


def _distribution(results):
    return {
        "people": len({r["person_id"] for r in results}),
        "count": len(results),
        "by_pjt": dict(Counter(r["pjt"] for r in results)),
        "by_cl": dict(Counter(r["cl_level"] for r in results)),
        "by_horizon": dict(Counter(r["horizon"] for r in results)),
    }
