// 워드클라우드 순수 로직 (todos/005) — 빌드 시 template.html에 인라인, node로 단위 테스트.
"use strict";

var CLOUD_MIN_PEOPLE = 5;   // 미만이면 렌더 회피 (스포일러/식별 방지)
var CLOUD_MAX_WORDS = 80;   // 렌더 단어 수 상한 (재렌더 체감 지연 방지)

// 스코프("all"|"team"|"cl"|"ego") → 합산 대상 인물 id 목록
function cloudScopeIds(scope, value, persons, egoIds){
  if (scope === "team") return persons.filter(function(p){ return p.pjt === value; }).map(function(p){ return p.id; });
  if (scope === "cl") return persons.filter(function(p){ return p.cl_level === value; }).map(function(p){ return p.id; });
  if (scope === "ego") return egoIds || [];
  return persons.map(function(p){ return p.id; });
}

// (007) 회고 원문 md → HTML — 경량 서브셋(#/##/###, 문단, - 불릿, **굵게**), 외부 의존 없음
function mdToHtml(md){
  var esc = String(md).replace(/[&<>"']/g, function(c){
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
  });
  var blocks = esc.split(/\n{2,}/);
  return blocks.map(function(block){
    var lines = block.split("\n").filter(function(l){ return l.trim(); });
    if (!lines.length) return "";
    return lines.map(function(line){
      var h = line.match(/^(#{1,3})\s+(.*)$/);
      var tag = h ? "h" + h[1].length : null;
      var body = (h ? h[2] : line).replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>");
      if (tag) return "<" + tag + ">" + body + "</" + tag + ">";
      var li = line.match(/^[-*]\s+(.*)$/);
      if (li) return "<li>" + li[1].replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>") + "</li>";
      return "<p>" + body + "</p>";
    }).join("").replace(/(<li>.*<\/li>)/, "<ul>$1</ul>");
  }).join("");
}

// (006) 에고 엣지 라벨용 공통 태그 — 앞사람 태그 순서 유지, 없으면 빈 배열(라벨 생략)
function commonTags(tagsA, tagsB){
  var b = tagsB || [];
  return (tagsA || []).filter(function(t){ return b.indexOf(t) !== -1; });
}

// (006) 태그 필터 — 활성 태그가 없으면 전원 통과, 있으면 보유자만 점등
function passesTagFilter(person, tag){
  return !tag || (person.tags || []).indexOf(tag) !== -1;
}

// 선택 집합의 인당 빈도를 단순 합산
function cloudState(freq, ids){
  if (ids.length < CLOUD_MIN_PEOPLE) return { ok: false, count: ids.length };
  var sum = {};
  ids.forEach(function(id){
    var f = freq[String(id)] || {};
    for (var w in f) sum[w] = (sum[w] || 0) + f[w];
  });
  var entries = Object.keys(sum).map(function(w){ return [w, sum[w]]; });
  entries.sort(function(a, b){ return b[1] - a[1] || (a[0] < b[0] ? -1 : 1); });
  entries = entries.slice(0, CLOUD_MAX_WORDS);
  return { ok: true, list: entries };
}
