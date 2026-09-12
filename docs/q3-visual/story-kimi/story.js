// story-kimi 후보 — 1부 9비트. 계약: docs/q3-visual-brief.md §3.3.
// 콘셉트: "기록 한 장이 별이 되고, 별이 갈라져 성운을 이룬다."
// 화면은 별·선·빛 + Canvas 한 장(1-0~1-2)으로 말하고, 글자는 nebulaCopy에서만 읽는다.
(() => {
  if (new URLSearchParams(location.hash.slice(1)).get('mode') !== 'story') return;
  const engine = window.nebula;
  const copy = window.nebulaCopy;
  const data = JSON.parse(document.getElementById('data').textContent);
  const person = data.people.find(p => p.pid === 'P000');
  const task = data.tasks.filter(t => t.person === person.id)
    .sort((a, b) => String(a.id).localeCompare(String(b.id), undefined, {numeric: true}))[0];
  const beats = ['1-0', '1-1', '1-2', '1-3', '1-4', '1-5', '1-6', '1-7', '1-8'];
  const REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // 결정적 난수 — 같은 빌드면 같은 화면.
  let seed = 20260913;
  const rnd = () => (seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;

  // ---- 레이어 ----
  const ink = '#f2f0e9';
  const css = (el, style) => el.style.cssText = style;
  const veil = document.createElement('div');
  css(veil, 'position:fixed;inset:0;background:#030506;opacity:1;transition:opacity 1.1s ease;z-index:10;pointer-events:none');
  const canvas = document.createElement('canvas');
  css(canvas, 'position:fixed;inset:0;width:100%;height:100%;z-index:11;pointer-events:none');
  const stage = document.createElement('div');
  css(stage, 'position:fixed;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;'
    + 'text-align:center;z-index:12;pointer-events:none;padding:0 8vw;box-sizing:border-box');
  const linesEl = document.createElement('div');
  css(linesEl, 'font:500 64px/1.35 "Avenir Next","Apple SD Gothic Neo","Malgun Gothic",sans-serif;'
    + 'letter-spacing:-.02em;color:' + ink + ';transition:opacity .9s ease;word-break:keep-all');
  const subEl = document.createElement('div');
  css(subEl, 'margin-top:34px;font:28px/1.4 "Apple SD Gothic Neo","Malgun Gothic",sans-serif;'
    + 'color:#a8a2bd;letter-spacing:.04em;transition:opacity .9s ease');
  const cardBox = document.createElement('div');
  css(cardBox, 'position:fixed;left:6vw;bottom:12vh;display:flex;flex-direction:column;gap:22px;z-index:13;'
    + 'pointer-events:none;max-width:44vw;text-align:left');
  stage.append(linesEl, subEl);
  document.body.append(veil, canvas, stage, cardBox);
  const ctx = canvas.getContext('2d');
  let W = 0, H = 0, DPR = 1;
  function fit() {
    DPR = Math.min(devicePixelRatio || 1, 2);
    W = innerWidth; H = innerHeight;
    canvas.width = W * DPR; canvas.height = H * DPR;
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  }
  fit();
  addEventListener('resize', fit);

  // ---- 문장 ----
  let textGen = 0;
  function showLines(id) {
    const mine = ++textGen;
    const c = copy[id];
    linesEl.textContent = c.screen.join('\n');
    linesEl.style.whiteSpace = 'pre-line';
    subEl.textContent = c.sub || '';
    if (REDUCED) { linesEl.style.opacity = 1; subEl.style.opacity = c.sub ? 1 : 0; return; }
    linesEl.style.opacity = 0; subEl.style.opacity = 0;
    requestAnimationFrame(() => requestAnimationFrame(() => {
      if (mine !== textGen) return;
      linesEl.style.opacity = 1;
      subEl.style.opacity = c.sub ? 1 : 0;
    }));
  }
  function hideCards() { cardBox.textContent = ''; }

  // ---- 애니메이션 유틸 ----
  let gen = 0; // 비트 전환 토큰
  const wait = ms => new Promise(r => setTimeout(r, REDUCED ? 0 : ms));
  function animate(frames) { // frames(t 0..1) → raf 루프. reduced면 끝 프레임만.
    return new Promise(resolve => {
      if (REDUCED) { frames(1); resolve(); return; }
      const t0 = performance.now();
      const dur = frames.duration || 1200;
      (function tick(now) {
        if (gen !== animate.gen) { resolve(); return; } // 비트가 바뀌면 조용히 종료
        const t = Math.min(1, (now - t0) / dur);
        frames(t);
        if (t < 1) requestAnimationFrame(tick); else resolve();
      })(t0);
    });
  }
  const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  function star(x, y, r, color, glow) {
    ctx.save();
    if (glow) { ctx.shadowColor = color; ctx.shadowBlur = glow; }
    ctx.fillStyle = color;
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
  }
  function clear() { ctx.clearRect(0, 0, W, H); }

  // ---- 1-0: 판독 불가 PPT 실루엣 ----
  const pages = Array.from({length: 5}, (_, i) => ({
    x: .14 + rnd() * .72, y: .16 + rnd() * .6,
    w: 150 + rnd() * 60, rot: (rnd() - .5) * .14,
    dx: (rnd() - .5) * .0006, dy: (rnd() - .5) * .0004, hue: i,
    bars: Array.from({length: 5}, () => .4 + rnd() * .45),
  }));
  function drawPage(p, alpha) {
    ctx.save();
    ctx.translate(p.x * W, p.y * H);
    ctx.rotate(p.rot);
    const w = p.w, h = w * .72;
    ctx.fillStyle = `rgba(26,28,42,${alpha})`;
    ctx.strokeStyle = `rgba(120,116,150,${alpha * .5})`;
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.roundRect(-w / 2, -h / 2, w, h, 4); ctx.fill(); ctx.stroke();
    ctx.fillStyle = `rgba(150,146,175,${alpha * .35})`;
    for (let i = 0; i < 5; i++) {
      ctx.fillRect(-w * .38, -h * .3 + i * h * .15, w * p.bars[i], 3.5);
    }
    ctx.restore();
  }

  // ---- 1-1: 문서 → 텍스트 줄 → 임베딩 → 별 ----
  async function docToStar() {
    const cx = W / 2, cy = H * .46;
    // 페이지 하나가 중앙으로
    await animate(Object.assign(t => {
      clear();
      pages.forEach((p, i) => drawPage(p, .5 * (1 - t * (i === 0 ? 0 : 1))));
      const p = pages[0];
      const px = p.x * W + (cx - p.x * W) * ease(t);
      const py = p.y * H + (cy - p.y * H) * ease(t);
      drawPage({...p, x: px / W, y: py / H, rot: p.rot * (1 - t)}, .9);
    }, {duration: 1100}));
    if (!current.is('1-1')) return;
    // 텍스트 줄이 풀려나옴
    const bars = Array.from({length: 12}, (_, i) => ({
      y: (i - 5.5) * 12, len: 60 + rnd() * 130, off: rnd(),
    }));
    await animate(Object.assign(t => {
      clear();
      bars.forEach(b => {
        const a = Math.sin(Math.PI * Math.min(1, t + b.off * .2));
        ctx.fillStyle = `rgba(184,163,237,${.55 * a})`;
        ctx.fillRect(cx - b.len / 2, cy + b.y, b.len * t, 3);
      });
    }, {duration: 900}));
    if (!current.is('1-1')) return;
    // 얇은 임베딩 아이콘(다이아몬드)을 지나 별 하나로
    await animate(Object.assign(t => {
      clear();
      const e = ease(t);
      ctx.save();
      ctx.translate(cx, cy); ctx.rotate(Math.PI / 4);
      ctx.strokeStyle = `rgba(161,223,208,${.8 * Math.min(1, t * 2)})`;
      ctx.lineWidth = 1.4;
      const s = 46;
      ctx.strokeRect(-s / 2, -s / 2, s, s);
      ctx.restore();
      bars.forEach(b => {
        const bx = cx - b.len / 2 + (cx - (cx - b.len / 2)) * e;
        const squeeze = 1 - e;
        ctx.fillStyle = `rgba(184,163,237,${.55 * (1 - e)})`;
        ctx.fillRect(cx - (b.len / 2) * squeeze, cy + b.y * squeeze, b.len * squeeze, 3);
      });
      if (t > .55) star(cx, cy, 2 + 5 * ((t - .55) / .45), ink, 26 * t);
    }, {duration: 1300}));
  }

  // ---- 1-2: 별 증식 → 연결 → 엔진 장면 0으로 이어주기 ----
  async function starfieldHandoff() {
    const n = Math.min(data.people.length, 340);
    const pts = Array.from({length: n}, () => ({
      a: rnd() * Math.PI * 2, d: Math.pow(rnd(), .6), s: .8 + rnd() * 2,
    }));
    const cx = W / 2, cy = H * .46, R = Math.min(W, H) * .34;
    // 증식 + 연결선
    await animate(Object.assign(t => {
      clear();
      const e = ease(t);
      const positions = pts.map(p => [cx + Math.cos(p.a) * p.d * R * e, cy + Math.sin(p.a) * p.d * R * e]);
      ctx.strokeStyle = `rgba(168,162,189,${.14 * t})`;
      ctx.lineWidth = .7;
      for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j += 7) {
        const [x1, y1] = positions[i], [x2, y2] = positions[j];
        if ((x1 - x2) ** 2 + (y1 - y2) ** 2 < 5200) {
          ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
        }
      }
      positions.forEach(([x, y], i) => star(x, y, pts[i].s * (0.4 + .6 * e), 'rgba(242,240,233,.92)', 8));
    }, {duration: 1600}));
    if (!current.is('1-2')) return;
    // 엔진 장면 0 준비 + 베일 걷기
    const goP = engine.go(0);
    await wait(200);
    veil.style.opacity = 0;
    await goP;
    if (!current.is('1-2')) return;
    // 엔진 좌표로 이동
    const map = new Map(engine.peoplePositions().map(p => [String(p.id), p]));
    await animate(Object.assign(t => {
      clear();
      const e = ease(t);
      ctx.globalAlpha = 1 - t;
      pts.forEach((p, i) => {
        const personRow = data.people[i];
        const target = personRow ? map.get(String(personRow.id)) : null;
        const sx = cx + Math.cos(p.a) * p.d * R, sy = cy + Math.sin(p.a) * p.d * R;
        const x = target ? sx + (target.x - sx) * e : sx;
        const y = target ? sy + (target.y - sy) * e : sy;
        star(x, y, p.s, 'rgba(242,240,233,.9)', 8);
      });
      ctx.globalAlpha = 1;
    }, {duration: 1500}));
    clear();
  }

  // ---- 1-3: 클로즈업 → LLM 점화 → 분열 ----
  async function ignite() {
    await engine.focusPerson(person.id, {split: false});
    if (!current.is('1-3')) return;
    const spot = (engine.peoplePositions().find(p => String(p.id) === String(person.id)) || {x: W / 2, y: H / 2});
    // 예시 인물 자리에 옅은 고리
    await animate(Object.assign(t => {
      clear();
      ctx.strokeStyle = `rgba(242,240,233,${.5 * t})`;
      ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.arc(spot.x, spot.y, 34, 0, Math.PI * 2); ctx.stroke();
    }, {duration: 700}));
    if (!current.is('1-3')) return;
    // LLM 스파크가 내려와 별을 통과(점화)
    await animate(Object.assign(t => {
      const e = ease(t);
      const sx = spot.x, sy = H * .12 + (spot.y - H * .12) * e;
      clear();
      ctx.strokeStyle = 'rgba(242,240,233,.5)';
      ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.arc(spot.x, spot.y, 34, 0, Math.PI * 2); ctx.stroke();
      // 다이아몬드 아이콘
      ctx.save();
      ctx.translate(sx, sy); ctx.rotate(Math.PI / 4 + e * Math.PI);
      ctx.strokeStyle = 'rgba(161,223,208,.95)';
      ctx.lineWidth = 1.6;
      ctx.strokeRect(-11, -11, 22, 22);
      ctx.restore();
      if (t > .8) star(spot.x, spot.y, 5 + 10 * (t - .8) * 5, ink, 40 * (t - .8) * 5);
    }, {duration: 1100}));
    if (!current.is('1-3')) return;
    clear();
    await engine.splitPerson();
  }

  // ---- 1-5: PJT 격자, 예시 인물의 칸 강조 ----
  async function grid() {
    await engine.go(2);
    if (!current.is('1-5')) return;
    const cell = document.querySelector(`[data-pjt-cell="${person.pjt}"]`);
    if (!cell || !cell.getScreenCTM) return;
    try {
      const pt = new DOMPoint(0, 0).matrixTransform(cell.getScreenCTM());
      await animate(Object.assign(t => {
        clear();
        const r = 46 + t * 90;
        ctx.strokeStyle = `rgba(161,223,208,${.7 * (1 - t)})`;
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(pt.x, pt.y, r, 0, Math.PI * 2); ctx.stroke();
      }, {duration: 1400}));
      clear();
    } catch (e) { /* 강조 실패는 연출만 포기 */ }
  }

  // ---- 1-7: 역량 카드(story 오버레이) ----
  async function capabilityCards() {
    engine.selectTask(task.id);
    hideCards();
    const mk = (title, quote) => {
      const box = document.createElement('div');
      css(box, 'background:rgba(10,12,22,.82);border:1px solid rgba(184,163,237,.28);border-radius:10px;'
        + 'padding:20px 26px;opacity:0;transition:opacity .8s ease;transform:translateY(8px);'
        + 'transition:opacity .8s ease,transform .8s ease');
      const h = document.createElement('div');
      css(h, 'font:700 22px/1.4 "Apple SD Gothic Neo","Malgun Gothic",sans-serif;color:#d9d2ee;letter-spacing:.02em');
      h.textContent = title;
      const q = document.createElement('div');
      css(q, 'margin-top:8px;font:20px/1.55 "Apple SD Gothic Neo","Malgun Gothic",sans-serif;color:#a8a2bd');
      q.textContent = '“' + quote + '”';
      box.append(h, q);
      return box;
    };
    (task.skills || []).slice(0, 3).forEach(s => {
      cardBox.append(mk((s.kind === 'have' ? '● 보유 경험 · ' : '◯ 필요한 역량 · ') + s.label, s.quote));
    });
    const cards = [...cardBox.children];
    for (const c of cards) {
      c.style.opacity = 1; c.style.transform = 'translateY(0)';
      await wait(REDUCED ? 0 : 450);
    }
    await wait(REDUCED ? 0 : 300);
  }

  // ---- 비트 정의 ----
  const steps = {
    '1-0': async () => {
      hideCards(); veil.style.opacity = 1;
      if (REDUCED) { clear(); pages.forEach(p => drawPage(p, .5)); return; }
      const drift = () => {
        if (!current.is('1-0')) return;
        clear();
        pages.forEach(p => {
          p.x += p.dx; p.y += p.dy;
          if (p.x < .05 || p.x > .95) p.dx *= -1;
          if (p.y < .08 || p.y > .85) p.dy *= -1;
          drawPage(p, .5);
        });
        drift.raf = requestAnimationFrame(drift);
      };
      drift();
    },
    '1-1': async () => {
      hideCards(); veil.style.opacity = 1;
      if (REDUCED) { clear(); star(W / 2, H * .46, 7, ink, 26); return; }
      await docToStar();
    },
    '1-2': starfieldHandoff,
    '1-3': ignite,
    '1-4': async () => {
      hideCards(); veil.style.opacity = 0;
      await engine.clearPerson();
      if (!current.is('1-4')) return;
      await engine.go(1);
      if (REDUCED) return;
      // 전원 분열 직후 잔광
      await animate(Object.assign(t => {
        clear();
        ctx.fillStyle = `rgba(242,240,233,${.05 * (1 - t)})`;
        ctx.fillRect(0, 0, W, H);
      }, {duration: 700}));
      clear();
    },
    '1-5': grid,
    '1-6': async () => { hideCards(); await engine.enterPjt(person.pjt); },
    '1-7': capabilityCards,
    '1-8': async () => {
      clear(); hideCards(); veil.style.opacity = 1;
      await wait(REDUCED ? 0 : 900);
    },
  };

  // ---- 진행 관리 ----
  let index = -1;
  let playing = null;
  const current = Object.assign(() => beats[index], {is: id => beats[index] === id && gen === current._gen});
  async function goto(id) {
    if (!beats.includes(id)) return;
    const my = ++gen;
    animate.gen = my; current._gen = my;
    index = beats.indexOf(id);
    if (playing) await playing.catch(() => {}); // 이전 비트가 정리되길 기다림
    if (my !== gen) return;
    showLines(id);
    playing = steps[id]();
    await playing;
  }
  window.nebulaStory = {beats, goto, current: () => beats[index]};
  addEventListener('keydown', e => {
    if (e.key === ' ' || e.key === 'ArrowRight') goto(beats[Math.min(index + 1, beats.length - 1)]);
    else if (e.key === 'ArrowLeft') goto(beats[Math.max(index - 1, 0)]);
    else if (e.key.toLowerCase() === 'r') goto(beats[index]);
  });
  goto(beats[0]);
})();
