// 1부 story 후보 — story-claude. 연출 설명은 같은 폴더 README.md.
// 기록의 줄이 한 가닥 빛이 되고(1-1), 닮음을 따라 번지고(1-2), 프리즘을 지나 여러 미래로 갈라진다(1-3).
// 계약: docs/q3-visual-brief.md §2·§3. 화면 문구는 window.nebulaCopy에서만, textContent로 넣는다.
(() => {
  if (new URLSearchParams(location.hash.slice(1)).get('mode') !== 'story') return;
  const engine = window.nebula;
  const copy = window.nebulaCopy;
  const data = JSON.parse(document.getElementById('data').textContent);
  const person = data.people.find(p => p.pid === 'P000');
  const task = data.tasks.find(t => t.person === person.id);
  const personTasks = data.tasks.filter(t => t.person === person.id);
  const beats = ['1-0', '1-1', '1-2', '1-3', '1-4', '1-5', '1-6', '1-7', '1-8'];
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const W = 1920, H = 1080, INK = '#080b16', PAPER = '#f2f0e9', MINT = '#a1dfd0';
  const P = person.id, PJT = person.pjt, HUE = data.pjts[PJT].color;

  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const smooth = t => t * t * t * (t * (t * 6 - 15) + 10);
  const seg = (p, a, b) => smooth(clamp((p - a) / (b - a)));
  const lerp = (a, b, t) => a + (b - a) * t;
  const mix = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t)];

  // ---- 레이어: 덮개(엔진 가림) < 캔버스 < 하단 그늘 < 1920×1080 무대(문장·카드) < 베일(reduced-motion) < 노트. 합성 표시(z 20)는 늘 위.
  const style = document.createElement('style');
  style.textContent = `
#nbs-cover,#nbs-canvas,#nbs-foot,#nbs-veil{position:fixed;inset:0;pointer-events:none}
#nbs-cover{z-index:11;background:${INK}}
#nbs-canvas{z-index:12;width:100%;height:100%}
#nbs-foot{z-index:13;top:auto;height:300px;background:linear-gradient(#080b1600,#080b16e8 72%);opacity:0}
#nbs-stage{position:fixed;left:0;top:0;width:${W}px;height:${H}px;transform-origin:0 0;z-index:14;pointer-events:none;color:${PAPER};font-family:var(--font)}
#nbs-copy{position:absolute;left:140px;right:140px;text-align:center;opacity:0}
#nbs-copy .line{font-size:68px;line-height:1.3;font-weight:500;letter-spacing:-.04em;word-break:keep-all}
#nbs-copy .sub{margin-top:16px;font-size:30px;color:#aca8c0;letter-spacing:-.01em}
#nbs-copy[data-at=center]{top:540px;transform:translateY(-50%)}
#nbs-copy[data-at=low]{top:720px}
#nbs-copy[data-at=foot]{bottom:46px}
#nbs-cards{position:absolute;left:0;right:0;top:0;display:flex;justify-content:center;gap:40px;opacity:0}
.nbs-card{position:relative;width:840px;padding:26px 34px 28px 82px;border-radius:14px;background:#0b0f21;border:1.5px solid #ffffff22}
.nbs-card i{position:absolute;left:34px;top:37px;width:24px;height:24px;border-radius:50%;box-sizing:border-box}
.nbs-card.have{border-color:#a1dfd05c}.nbs-card.have i{background:${MINT};box-shadow:0 0 18px #a1dfd088}
.nbs-card.gap{border-color:#eeb3ce5c}.nbs-card.gap i{border:2.5px dashed #eeb3ce}
.nbs-card b{display:block;font-size:38px;font-weight:500;letter-spacing:-.035em;line-height:1.3}
.nbs-card span{display:block;margin-top:10px;font-size:28px;line-height:1.5;color:#c6c2d6;letter-spacing:-.02em;word-break:keep-all}
.nbs-card span::before{content:'\\201C'}.nbs-card span::after{content:'\\201D'}
#nbs-veil{z-index:15;background:${INK};opacity:0}
#nbs-note{position:fixed;left:24px;bottom:24px;z-index:16;max-width:640px;padding:14px 18px;border-radius:8px;background:#141833f2;color:#d9d6e5;font:17px/1.7 var(--font);pointer-events:none}
body.nbs-snap *{transition:none!important}`;
  document.head.append(style);
  const layer = (tag, id, parent = document.body) => {
    const e = document.createElement(tag);
    e.id = id;
    parent.append(e);
    return e;
  };
  const cover = layer('div', 'nbs-cover');
  const canvas = layer('canvas', 'nbs-canvas');
  const foot = layer('div', 'nbs-foot');
  const stage = layer('div', 'nbs-stage');
  const cards = layer('div', 'nbs-cards', stage);
  const text = layer('div', 'nbs-copy', stage);
  const veil = layer('div', 'nbs-veil');
  const note = layer('div', 'nbs-note');
  note.hidden = true;
  const g = canvas.getContext('2d');

  // ---- 좌표: 무대(1920×1080, 레터박스) ↔ 뷰포트 px. 엔진 좌표(peoplePositions 등)는 뷰포트 px다.
  let view;
  function fit() {
    const w = innerWidth, h = innerHeight, s = Math.min(w / W, h / H), dpr = devicePixelRatio || 1;
    view = {w, h, s, dpr, ox: (w - W * s) / 2, oy: (h - H * s) / 2};
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    stage.style.transform = `translate(${view.ox}px,${view.oy}px) scale(${s})`;
  }
  fit();
  const toView = ([x, y]) => [view.ox + x * view.s, view.oy + y * view.s];
  const toStage = ([x, y]) => [(x - view.ox) / view.s, (y - view.oy) / view.s];
  const inView = () => g.setTransform(view.dpr, 0, 0, view.dpr, 0, 0);
  const inStage = () => g.setTransform(view.dpr * view.s, 0, 0, view.dpr * view.s, view.dpr * view.ox, view.dpr * view.oy);

  const sprites = new Map();
  function glow(x, y, r, alpha, color = PAPER) {
    if (alpha <= 0 || r <= 0) return;
    if (!sprites.has(color)) {
      const c = document.createElement('canvas');
      c.width = c.height = 96;
      const x2 = c.getContext('2d'), grad = x2.createRadialGradient(48, 48, 0, 48, 48, 48);
      grad.addColorStop(0, color);
      grad.addColorStop(.12, color + 'aa');
      grad.addColorStop(.4, color + '22');
      grad.addColorStop(1, color + '00');
      x2.fillStyle = grad;
      x2.fillRect(0, 0, 96, 96);
      sprites.set(color, c);
    }
    g.globalAlpha = clamp(alpha);
    g.drawImage(sprites.get(color), x - r, y - r, r * 2, r * 2);
    g.globalAlpha = 1;
  }
  function dot(x, y, r, alpha, color = PAPER) {
    if (alpha <= 0) return;
    g.globalAlpha = clamp(alpha);
    g.fillStyle = color;
    g.beginPath();
    g.arc(x, y, r, 0, Math.PI * 2);
    g.fill();
    g.globalAlpha = 1;
  }
  function line(a, b, alpha, color = PAPER, width = 1) {
    if (alpha <= 0) return;
    g.globalAlpha = clamp(alpha);
    g.strokeStyle = color;
    g.lineWidth = width;
    g.beginPath();
    g.moveTo(a[0], a[1]);
    g.lineTo(b[0], b[1]);
    g.stroke();
    g.globalAlpha = 1;
  }

  // ---- 진행: 새 비트가 오면 token이 바뀌어 옛 비트의 남은 단계는 멈춘다. run.snap이면 끝 상태로 바로 간다.
  let token = 0, index = 0, shown = null, busy = false, painter = () => {}, painted = 1, snapping = 0;
  const alive = run => run.token === token;
  function paint(fn, p) {
    painter = fn;
    painted = p;
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.clearRect(0, 0, canvas.width, canvas.height);
    fn(p);
  }
  function animate(run, ms, fn) {
    if (run.snap || ms <= 0) {
      fn(1);
      return Promise.resolve();
    }
    return new Promise(resolve => {
      const start = performance.now();
      const step = now => {
        if (!alive(run)) return resolve();
        const p = Math.min(1, (now - start) / ms);
        fn(p);
        if (p < 1) requestAnimationFrame(step);
        else resolve();
      };
      requestAnimationFrame(step);
    });
  }
  const tween = (run, ms, fn) => animate(run, ms, p => paint(fn, p));
  const wait = (run, ms) => run.snap ? Promise.resolve() : new Promise(resolve => setTimeout(resolve, ms));
  const blank = () => { cover.style.opacity = 0; };
  // 가려진 곳이나 건너뛸 때의 엔진 호출은 CSS 전환 없이 즉시 끝낸다.
  async function still(fn) {
    snapping++;
    document.body.classList.add('nbs-snap');
    try {
      await fn();
      void document.body.offsetHeight;
    } finally {
      if (--snapping === 0) document.body.classList.remove('nbs-snap');
    }
  }
  const moving = (run, fn) => run.snap ? still(fn) : fn();

  const showCopy = v => {
    text.style.opacity = v;
    text.style.translate = `0 ${(1 - v) * 14}px`;
  };
  async function swapCopy(run, id, at) {
    const from = +text.style.opacity || 0;
    if (text.dataset.beat !== id) await animate(run, 260 * from, p => showCopy(from * (1 - p)));
    const c = copy[id];
    text.replaceChildren(...c.screen.map(s => {
      const d = document.createElement('div');
      d.className = 'line';
      d.textContent = s;
      return d;
    }));
    if (c.sub) {
      const d = document.createElement('div');
      d.className = 'sub';
      d.textContent = c.sub;
      text.append(d);
    }
    text.dataset.beat = id;
    text.dataset.at = at;
    showCopy(0);
    foot.style.opacity = at === 'foot' ? 1 : 0;
    if (id !== '1-8') cards.style.opacity = 0;
    note.textContent = c.note || '';
  }

  const personAt = () => {
    const q = engine.peoplePositions().find(p => p.id === P);
    return [q.x, q.y];
  };
  const centerOf = selector => {
    const e = document.querySelector(selector);
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [r.left + r.width / 2, r.top + r.height / 2];
  };
  const taskNode = id => `[data-task-node="${CSS.escape(id)}"]`;
  const cellRect = () => document.querySelector(`[data-pjt-cell="${PJT}"]`)?.getBoundingClientRect();

  // ---- 1-0·1-1: 판독할 수 없는 슬라이드 실루엣(16:9). [x, y, 크기, 기울기, 밝기, 떠오르는 거리] — 마지막이 맨 앞 장.
  const SLIDES = [
    [470, 470, .56, .1, .2, 34], [1450, 460, .6, -.11, .22, 30], [650, 330, .76, -.09, .38, 26],
    [1290, 320, .8, .07, .42, 22], [780, 560, .7, .05, .32, 30], [1160, 570, .72, -.06, .36, 24],
    [960, 420, 1.05, -.02, .8, 18],
  ];
  const BARS = [[-188, -96, 170, 14], [-168, -55, 210, 8], [-168, -21, 160, 8], [-168, 13, 190, 8], [-168, 47, 120, 8]];
  function slide(x, y, s, r, alpha, bars = true) {
    if (alpha <= 0) return;
    inStage();
    g.translate(x, y);
    g.rotate(r);
    g.scale(s, s);
    g.globalAlpha = clamp(alpha);
    g.fillStyle = '#0d1124';
    g.beginPath();
    g.roundRect(-220, -124, 440, 248, 8);
    g.fill();
    g.globalAlpha = clamp(alpha) * .55;
    g.strokeStyle = PAPER;
    g.lineWidth = 1.6 / s;
    g.stroke();
    g.fillStyle = PAPER;
    BARS.forEach(([bx, by, bw, bh], j) => {
      g.globalAlpha = clamp(alpha) * (j ? .34 : .62);
      if (j) g.fillRect(-190, by, 8, 8);
      if (bars) g.fillRect(bx, by, bw, bh);
    });
    g.globalAlpha = clamp(alpha) * .24;
    g.strokeRect(78, -55, 110, 110);
    g.globalAlpha = 1;
  }
  const onSlide = ([x, y, s, r], lx, ly) => [x + (lx * Math.cos(r) - ly * Math.sin(r)) * s, y + (lx * Math.sin(r) + ly * Math.cos(r)) * s];

  function prologue(p) {
    cover.style.opacity = 1;
    SLIDES.forEach(([x, y, s, r, a, rise], i) => {
      const q = seg(p, .02 + i * .05, .6 + i * .05);
      slide(x, y + rise * (1 - q), s, r, a * q);
    });
    showCopy(seg(p, .45, .92));
  }

  const HERO = SLIDES[SLIDES.length - 1], HERO_AT = [560, 430, 1.3, 0], LENS = [960, 430];
  // 임베딩 아이콘: 얇은 원 + 세 축(벡터 공간). 흡수한 빛만큼 가운데가 밝아진다.
  function lens([x, y], alpha, charge) {
    if (alpha <= 0) return;
    inStage();
    g.globalAlpha = alpha * .7;
    g.strokeStyle = PAPER;
    g.lineWidth = 1.5;
    g.beginPath();
    g.arc(x, y, 60, 0, Math.PI * 2);
    g.stroke();
    for (const a of [-Math.PI / 2, Math.PI / 6, Math.PI * 5 / 6]) {
      const end = [x + Math.cos(a) * 40, y + Math.sin(a) * 40];
      line([x, y], end, alpha * .7, PAPER, 1.5);
      dot(end[0], end[1], 3, alpha * .8);
    }
    glow(x, y, 30 + charge * 60, alpha * charge * .7);
  }
  function born(alpha) { // 1-1의 끝 별. 1-2가 여기서 출발한다.
    inStage();
    glow(LENS[0], LENS[1], 72, .5 * alpha);
    dot(LENS[0], LENS[1], 7, alpha);
  }
  function ignite(p) {
    cover.style.opacity = 1;
    SLIDES.slice(0, -1).forEach(([x, y, s, r, a]) => {
      const q = seg(p, 0, .26);
      slide(x + (x < 960 ? -70 : 70) * q, y, s, r, a * (1 - q));
    });
    const m = seg(p, 0, .3), hero = HERO_AT.map((v, i) => lerp(HERO[i], v, m));
    slide(...hero, HERO[4] * (1 - seg(p, .34, .52)), p < .3);
    // 슬라이드의 줄이 막대에서 빛줄기로 풀려 렌즈로 들어간다.
    let absorbed = 0;
    if (p >= .3) {
      inStage();
      g.lineCap = 'round';
      BARS.forEach(([bx, by, bw, bh], j) => {
        const start = .3 + j * .03, head = seg(p, start, start + .22), tail = seg(p, start + .05, start + .26);
        absorbed += tail / BARS.length;
        if (tail >= 1) return;
        const bend = Math.sin(head * Math.PI) * (j - 2) * 18;
        const a = mix(onSlide(hero, bx + bw, by + bh / 2), LENS, head), b = mix(onSlide(hero, bx, by + bh / 2), LENS, tail);
        a[1] += bend;
        b[1] += bend * .6;
        line(b, a, lerp(HERO[4] * (j ? .34 : .62), .95, head), PAPER, lerp(bh * hero[2], 2.4, head));
      });
      g.lineCap = 'butt';
    }
    lens(LENS, seg(p, .16, .32) * (1 - seg(p, .8, .94)), absorbed);
    // 짧은 정적 뒤 점화.
    const f = seg(p, .76, .9);
    inStage();
    if (p > .66 && f === 0) dot(LENS[0], LENS[1], 2.4, 1);
    if (f > 0) {
      glow(LENS[0], LENS[1], lerp(40, 300, f), Math.sin(f * Math.PI) * .8);
      g.globalAlpha = (1 - f) * .4;
      g.strokeStyle = PAPER;
      g.lineWidth = 1.2;
      g.beginPath();
      g.arc(LENS[0], LENS[1], lerp(10, 460, f), 0, Math.PI * 2);
      g.stroke();
      g.globalAlpha = 1;
      born(f);
    }
    showCopy(seg(p, .86, 1));
  }

  // ---- 1-2: 예시 인물의 별에서 유사도 연결을 따라(BFS) 가까운 이웃부터 번지고, 카메라가 빠지며 엔진 좌표에 내려앉는다.
  function growth() {
    const at = new Map(engine.peoplePositions().map(q => [q.id, [q.x, q.y]]));
    const next = new Map(data.people.map(q => [q.id, []]));
    [...data.edges].sort((a, b) => b.w - a.w).forEach(e => {
      next.get(e.a)?.push(e.b);
      next.get(e.b)?.push(e.a);
    });
    const parent = new Map([[P, P]]), order = [P];
    for (let i = 0; i < order.length; i++) {
      for (const n of next.get(order[i])) if (!parent.has(n)) { parent.set(n, order[i]); order.push(n); }
    }
    for (const q of data.people) if (!parent.has(q.id)) { parent.set(q.id, P); order.push(q.id); }
    return {
      at, parent,
      rank: new Map(order.map((id, i) => [id, i / order.length])),
      hue: new Map(data.people.map(q => [q.id, data.pjts[q.pjt].color])),
      // 엔진이 실제로 그린 연결선만 따라 그려야 걷힐 때 선이 튀지 않는다.
      links: [...document.querySelectorAll('#links line')].map(l => [+l.dataset.a, +l.dataset.b]).filter(([a, b]) => at.has(a) && at.has(b)),
      scale: document.getElementById('sky').getScreenCTM().a,
      from: toView(LENS),
    };
  }
  function spread(k, p) {
    if (p < .02) { cover.style.opacity = 1; born(1); }
    const e0 = k.at.get(P), m = seg(p, .2, .84), zoom = lerp(2.6, 1, m), anchor = mix(k.from, e0, m);
    const place = id => { const e = k.at.get(id); return [anchor[0] + (e[0] - e0[0]) * zoom, anchor[1] + (e[1] - e0[1]) * zoom]; };
    const grown = id => id === P ? 1 : seg(p, .03 + k.rank.get(id) * .5, .17 + k.rank.get(id) * .5);
    const reveal = seg(p, .84, 1), fade = 1 - reveal, tint = seg(p, .4, .8);
    cover.style.opacity = fade;
    showCopy(seg(p, .45, .75));
    if (fade <= 0) return;
    inView();
    const where = new Map();
    for (const q of data.people) {
      const t = grown(q.id);
      if (t > 0) where.set(q.id, mix(place(k.parent.get(q.id)), place(q.id), t));
    }
    for (const [a, b] of k.links) {
      if (!where.has(a) || !where.has(b)) continue;
      line(where.get(a), where.get(b), .15 * Math.min(grown(a), grown(b)) * fade, '#bfb8db', .7 * k.scale);
    }
    for (const [id, pos] of where) {
      const t = grown(id), hue = k.hue.get(id), r = lerp(2.6, 4 * k.scale, m);
      if (t < 1) line(place(k.parent.get(id)), pos, .4 * Math.sin(t * Math.PI) * fade);
      glow(pos[0], pos[1], 13 * k.scale, .3 * t * fade * (1 - tint));
      glow(pos[0], pos[1], 13 * k.scale, .3 * t * fade * tint, hue);
      dot(pos[0], pos[1], r, t * fade * (1 - tint));
      dot(pos[0], pos[1], r, t * fade * tint, hue);
    }
    const origin = place(P);
    glow(origin[0], origin[1], lerp(72 * view.s, 20, seg(p, 0, .35)), .5 * (1 - seg(p, 0, .4)) * fade);
  }

  // ---- 1-3: 얇은 프리즘(LLM)이 별을 통과하며 점화 → 분열하는 과제 별까지 빛줄기가 따라간다.
  function prism(p) {
    blank();
    const [x, y] = personAt(), cx = x + lerp(-460, 460, p), size = 70;
    inView();
    g.globalAlpha = Math.sin(p * Math.PI) * .85;
    g.strokeStyle = PAPER;
    g.lineWidth = 1.6;
    g.beginPath();
    for (let i = 0; i < 3; i++) {
      const a = -Math.PI / 2 + i * Math.PI * 2 / 3;
      g.lineTo(cx + Math.cos(a) * size, y + 14 + Math.sin(a) * size);
    }
    g.closePath();
    g.stroke();
    g.globalAlpha = 1;
    const hit = clamp(1 - Math.abs(cx - x) / 110);
    glow(x, y, 40 + hit * 130, hit * .75);
    glow(x, y, 70, .5 * seg(p, .45, .7));
  }
  function beams(p) {
    blank();
    const s = personAt(), fade = 1 - seg(p, .55, 1);
    inView();
    glow(s[0], s[1], 70, .5 * (1 - seg(p, 0, .6)));
    for (const t of personTasks) {
      const e = centerOf(taskNode(t.id));
      if (!e) continue;
      line(s, e, .6 * fade, HUE, 1.6);
      glow(e[0], e[1], 36, .5 * fade, HUE);
    }
  }

  // ---- 1-5·1-6: 예시 인물의 PJT 칸을 표시하고, 그 칸이 창이 되어 화면 전체로 열리며 들어간다.
  function cellMark(p) {
    blank();
    const r = cellRect();
    if (!r) return;
    inView();
    g.globalAlpha = seg(p, .5, 1);
    g.strokeStyle = MINT;
    g.lineWidth = 2.2;
    g.shadowColor = MINT;
    g.shadowBlur = 22;
    g.beginPath();
    g.roundRect(r.left - 3, r.top - 3, r.width + 6, r.height + 6, 10);
    g.stroke();
    g.shadowBlur = 0;
    g.globalAlpha = 1;
  }
  function iris(from, dark, open) {
    blank();
    const q = smooth(open), [x, y, w, h] = from.map((v, i) => lerp(v, [-3, -3, view.w + 6, view.h + 6][i], q));
    inView();
    g.fillStyle = INK;
    g.globalAlpha = .9 * smooth(dark) * (1 - seg(open, .45, 1));
    g.beginPath();
    g.rect(0, 0, view.w, view.h);
    g.roundRect(x, y, w, h, 10);
    g.fill('evenodd');
    g.globalAlpha = 1 - seg(open, .3, 1);
    g.strokeStyle = MINT;
    g.lineWidth = 2.2;
    g.shadowColor = MINT;
    g.shadowBlur = 22;
    g.beginPath();
    g.roundRect(x, y, w, h, 10);
    g.stroke();
    g.shadowBlur = 0;
    g.globalAlpha = 1;
  }

  // ---- 1-7: 과제 하나만 남기고 어둡게, 역량 카드는 반대편에 세로로.
  function buildCards() {
    if (cards.childElementCount) return;
    for (const s of [...task.skills].sort((a, b) => (a.kind === 'gap') - (b.kind === 'gap'))) {
      const card = document.createElement('div'), label = document.createElement('b'), quote = document.createElement('span');
      card.className = 'nbs-card ' + s.kind;
      label.textContent = s.label;
      quote.textContent = s.quote;
      card.append(document.createElement('i'), label, quote);
      cards.append(card);
    }
  }
  function spotlight(p) {
    blank();
    const e = centerOf(taskNode(task.id));
    if (!e) return;
    const a = seg(p, .2, .7), c = seg(p, .55, .9);
    inView();
    g.fillStyle = INK;
    g.globalAlpha = .82 * a;
    g.fillRect(0, 0, view.w, view.h);
    g.globalCompositeOperation = 'destination-out';
    const hole = g.createRadialGradient(e[0], e[1], 0, e[0], e[1], 150);
    hole.addColorStop(0, '#000');
    hole.addColorStop(.4, '#000d');
    hole.addColorStop(1, '#0000');
    g.fillStyle = hole;
    g.globalAlpha = a;
    g.fillRect(e[0] - 150, e[1] - 150, 300, 300);
    g.globalCompositeOperation = 'source-over';
    g.globalAlpha = 1;
    glow(e[0], e[1], 48, .6 * a, HUE);
    // 카드는 과제 아래 한 줄(자리가 없으면 위). 확보 왼쪽 · 필요 오른쪽은 엔진의 역량 원 배치와 같은 방향이다.
    const sy = toStage(e)[1], height = cards.offsetHeight, below = sy + 120 + height <= 870;
    const top = below ? sy + 120 : sy - 120 - height;
    cards.style.top = top + 'px';
    cards.style.opacity = c;
    for (const card of cards.children) {
      const anchor = toView([card.offsetLeft + card.offsetWidth / 2, below ? top : top + height]);
      line(e, anchor, .4 * c, PAPER, 1.2);
      dot(anchor[0], anchor[1], 3, c);
    }
  }

  function closing(p) {
    cover.style.opacity = seg(p, 0, .45);
    inView();
    g.fillStyle = INK;
    g.globalAlpha = .82 * (1 - seg(p, 0, .45));
    g.fillRect(0, 0, view.w, view.h);
    g.globalAlpha = 1;
    cards.style.opacity = Math.min(+cards.style.opacity || 0, 1 - seg(p, 0, .3));
    inStage();
    const s = seg(p, .6, 1);
    glow(960, 330, 60, .35 * s);
    dot(960, 330, 4, .9 * s);
    showCopy(seg(p, .4, .8));
  }

  // ---- 비트. 각 비트는 run.snap일 때 어떤 상태에서 불려도 자기 끝 상태를 만든다(←·건너뛰기·reduced-motion).
  const steps = {
    '1-0': async run => {
      cover.style.opacity = 1;
      await swapCopy(run, '1-0', 'low');
      await still(() => engine.go(0));
      if (alive(run)) await tween(run, 3400, prologue);
    },
    '1-1': async run => {
      cover.style.opacity = 1;
      await swapCopy(run, '1-1', 'low');
      if (run.snap) await still(() => engine.go(0));
      if (alive(run)) await tween(run, 4000, ignite);
    },
    '1-2': async run => {
      await swapCopy(run, '1-2', 'foot');
      if (!alive(run)) return;
      cover.style.opacity = 1;
      await still(() => engine.go(0));
      if (!alive(run)) return;
      const plan = growth();
      await tween(run, 4200, p => spread(plan, p));
    },
    '1-3': async run => {
      await swapCopy(run, '1-3', 'foot');
      if (!alive(run)) return;
      paint(blank, 1);
      const zoom = moving(run, () => engine.focusPerson(P, {split: false}));
      await wait(run, 900);
      if (!alive(run)) return;
      await tween(run, 1400, prism);
      await zoom;
      await wait(run, 300);
      if (!alive(run)) return;
      await Promise.all([moving(run, () => engine.splitPerson()), tween(run, 1700, beams), animate(run, 900, showCopy)]);
    },
    '1-4': async run => {
      await swapCopy(run, '1-4', 'foot');
      if (!alive(run)) return;
      paint(blank, 1);
      if (run.snap) await still(() => engine.focusPerson(P));
      if (alive(run)) await Promise.all([moving(run, () => engine.go(1)), animate(run, 1400, showCopy)]);
    },
    '1-5': async run => {
      await swapCopy(run, '1-5', 'foot');
      if (!alive(run)) return;
      paint(blank, 1);
      await moving(run, () => engine.clearPerson());
      if (run.snap) await still(() => engine.go(1));
      if (alive(run)) await Promise.all([moving(run, () => engine.go(2)), tween(run, 2000, cellMark), animate(run, 1200, showCopy)]);
    },
    '1-6': async run => {
      await swapCopy(run, '1-6', 'foot');
      if (!alive(run)) return;
      if (run.snap) {
        paint(blank, 1);
        await still(async () => { await engine.clearPerson(); await engine.enterPjt(PJT); });
        showCopy(1);
        return;
      }
      const r = cellRect(), from = r ? [r.left - 3, r.top - 3, r.width + 6, r.height + 6] : [0, 0, view.w, view.h];
      await tween(run, 500, p => iris(from, p, 0));
      if (!alive(run)) return;
      await Promise.all([engine.enterPjt(PJT), tween(run, 1800, p => iris(from, 1, p)), animate(run, 1400, showCopy)]);
    },
    '1-7': async run => {
      await swapCopy(run, '1-7', 'foot');
      if (!alive(run)) return;
      buildCards();
      await moving(run, async () => {
        engine.selectTask(task.id);
        await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
      });
      if (alive(run)) await Promise.all([tween(run, 2400, spotlight), animate(run, 1200, showCopy)]);
    },
    '1-8': async run => {
      await swapCopy(run, '1-8', 'center');
      if (alive(run)) await tween(run, 3000, closing);
    },
  };

  async function play(id, snap = false) {
    const i = beats.indexOf(id);
    if (i < 0) return;
    const before = shown, run = {token: ++token, snap: snap || reduced}, fader = {token: run.token};
    index = i;
    shown = null;
    busy = !run.snap;
    // reduced-motion: 이동 없이 어둡게 가렸다가 끝 상태로 밝힌다.
    if (reduced) {
      const v0 = +veil.style.opacity || 0;
      await animate(fader, 220 * (1 - v0), p => { veil.style.opacity = lerp(v0, 1, p); });
    }
    if (!snap && i > 0 && before !== beats[i - 1] && alive(run)) await steps[beats[i - 1]]({token: run.token, snap: true});
    if (alive(run)) await steps[id](run);
    if (reduced && alive(run)) await animate(fader, 320, p => { veil.style.opacity = 1 - p; });
    if (alive(run)) {
      shown = id;
      busy = false;
    }
  }

  window.nebulaStory = {beats, goto: id => play(id), current: () => beats[index]};
  addEventListener('keydown', e => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    const key = e.key.toLowerCase();
    if (key === ' ' || key === 'arrowright') {
      e.preventDefault();
      if (busy) play(beats[index], true);
      else if (index < beats.length - 1) play(beats[index + 1]);
    } else if (key === 'arrowleft') {
      e.preventDefault();
      if (index > 0) play(beats[index - 1], true);
    } else if (key === 'r') {
      play(beats[index]);
    } else if (key === 'n') {
      note.hidden = !note.hidden;
    }
  });
  addEventListener('resize', () => {
    fit();
    paint(painter, painted);
  });
  play('1-0');
})();
