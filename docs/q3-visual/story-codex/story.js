// story-codex agent — 1부 9비트 연출
// 출발점: pitch-cosmos-v2의 조용한 시작·세 전환·정직한 태도, candidate-50의 분열→성운 모션
// 5모델 리뷰 공통 피드백: 첫 장면 임팩트, 작은 글자 제거, 15분 리듬
(() => {
  if (new URLSearchParams(location.hash.slice(1)).get('mode') !== 'story') return;
  
  const engine = window.nebula;
  const copy = window.nebulaCopy;
  const data = JSON.parse(document.getElementById('data').textContent);
  const person = data.people.find(p => p.pid === 'P000');
  const task = data.tasks.find(t => t.person === person.id);
  const beats = ['1-0', '1-1', '1-2', '1-3', '1-4', '1-5', '1-6', '1-7', '1-8'];
  
  const BLACK = '#030506';
  const WHITE = '#f2f0e9';
  const ACCENT = '#b4dccb';
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  
  // Story layer: 검은 배경 + 64px 중앙 텍스트 (1920×1080 기준)
  const layer = document.createElement('div');
  layer.id = 'story-layer';
  layer.style.cssText = 'position:fixed;inset:0;display:grid;place-items:center;'
    + 'white-space:pre-line;text-align:center;font:600 clamp(48px,3.5vw,64px)/1.3 sans-serif;'
    + 'color:' + WHITE + ';pointer-events:none;z-index:40;transition:background 1.4s ease-out';
  document.body.append(layer);
  
  // Canvas for pre-engine visuals (1-0, 1-1)
  const canvasWrap = document.createElement('div');
  canvasWrap.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:35;opacity:0;transition:opacity 1.2s';
  const canvas = document.createElement('canvas');
  canvas.width = 1920;
  canvas.height = 1080;
  canvas.style.cssText = 'width:100%;height:100%;object-fit:contain';
  canvasWrap.append(canvas);
  document.body.append(canvasWrap);
  const ctx = canvas.getContext('2d', {alpha: false});
  
  // Engine's #synthetic-mark is already present and visible in story mode
  
  const blackout = (on) => {
    layer.style.background = on ? BLACK : 'transparent';
  };
  
  const setText = (id) => {
    layer.textContent = copy[id].screen.join('\n');
  };
  
  const wait = (ms) => new Promise(r => setTimeout(r, ms));
  
  // Pre-computed positions for synthetic 320 people
  const peopleCount = data.people.length;
  const taskCount = data.tasks.length;
  
  // 1-0: 도입 — 조용한 시작, PPT 실루엣
  async function beat_1_0() {
    blackout(true);
    canvasWrap.style.opacity = '1';
    setText('1-0');
    
    // Draw three overlapping faint document silhouettes
    ctx.fillStyle = BLACK;
    ctx.fillRect(0, 0, 1920, 1080);
    ctx.globalAlpha = 0.08;
    ctx.fillStyle = WHITE;
    
    const docW = 280, docH = 380;
    const centerX = 960, centerY = 540;
    const offsets = [[-80, -60], [0, 0], [60, 40]];
    
    offsets.forEach(([dx, dy]) => {
      const x = centerX + dx - docW / 2;
      const y = centerY + dy - docH / 2;
      ctx.fillRect(x, y, docW, docH);
      // Faint title bar
      ctx.globalAlpha = 0.12;
      ctx.fillRect(x, y, docW, 28);
      ctx.globalAlpha = 0.08;
      // Faint lines (text placeholders)
      for (let i = 0; i < 8; i++) {
        const lineY = y + 60 + i * 32;
        ctx.fillRect(x + 24, lineY, docW - 48, 8);
      }
    });
    
    ctx.globalAlpha = 1;
  }
  
  // 1-1: wow1 임베딩 — 문서가 줄로 풀림 → 임베딩 아이콘 통과 → 별 하나
  async function beat_1_1() {
    blackout(true);
    setText('1-1');
    
    if (reduced) {
      // Skip animation
      await wait(400);
      ctx.fillStyle = BLACK;
      ctx.fillRect(0, 0, 1920, 1080);
      ctx.fillStyle = ACCENT;
      ctx.globalAlpha = 0.9;
      ctx.beginPath();
      ctx.arc(960, 540, 8, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = 1;
      return;
    }
    
    const steps = 90;
    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      ctx.fillStyle = BLACK;
      ctx.fillRect(0, 0, 1920, 1080);
      
      if (t < 0.3) {
        // Document → text lines
        const p = t / 0.3;
        ctx.globalAlpha = 0.12 * (1 - p);
        ctx.fillStyle = WHITE;
        const docW = 280 - p * 200;
        const docH = 380 - p * 340;
        ctx.fillRect(960 - docW / 2, 540 - docH / 2, docW, docH);
        
        // Lines appearing
        ctx.globalAlpha = 0.25 * p;
        for (let j = 0; j < 12; j++) {
          const lineY = 300 + j * 40;
          const lineW = 180 - Math.random() * 60;
          ctx.fillRect(960 - lineW / 2, lineY, lineW, 4);
        }
      } else if (t < 0.6) {
        // Lines → embedding icon (thin converging funnel)
        const p = (t - 0.3) / 0.3;
        ctx.globalAlpha = 0.25 * (1 - p);
        ctx.fillStyle = WHITE;
        for (let j = 0; j < 12; j++) {
          const lineY = 300 + j * 40 + p * 100;
          const lineW = (180 - j * 10) * (1 - p * 0.7);
          ctx.fillRect(960 - lineW / 2, lineY, lineW, 4);
        }
        
        // Embedding icon: thin converging lines forming a star-like point
        ctx.globalAlpha = 0.4 * p;
        ctx.strokeStyle = ACCENT;
        ctx.lineWidth = 2;
        ctx.beginPath();
        const radius = 60 - p * 50;
        for (let angle = 0; angle < Math.PI * 2; angle += Math.PI / 6) {
          const x1 = 960 + Math.cos(angle) * radius;
          const y1 = 540 + Math.sin(angle) * radius;
          ctx.moveTo(x1, y1);
          ctx.lineTo(960, 540);
        }
        ctx.stroke();
      } else {
        // Icon fades → one bright star
        const p = (t - 0.6) / 0.4;
        ctx.globalAlpha = 0.9 * p;
        ctx.fillStyle = ACCENT;
        ctx.beginPath();
        ctx.arc(960, 540, 8, 0, Math.PI * 2);
        ctx.fill();
        
        // Glow
        const glow = ctx.createRadialGradient(960, 540, 0, 960, 540, 80);
        glow.addColorStop(0, 'rgba(180, 220, 203, 0.3)');
        glow.addColorStop(1, 'rgba(180, 220, 203, 0)');
        ctx.globalAlpha = p * 0.6;
        ctx.fillStyle = glow;
        ctx.fillRect(0, 0, 1920, 1080);
      }
      
      ctx.globalAlpha = 1;
      await wait(reduced ? 0 : 16);
    }
  }
  
  // 1-2: wow2 유사도 — 별이 늘며 엔진 장면 0으로 전환
  async function beat_1_2() {
    setText('1-2');
    
    if (reduced) {
      canvasWrap.style.opacity = '0';
      blackout(false);
      await engine.go(0);
      return;
    }
    
    // Animate star multiplication before handing to engine
    const targetPositions = engine.peoplePositions(); // [{x, y}, ...]
    const steps = 120;
    
    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      ctx.fillStyle = BLACK;
      ctx.fillRect(0, 0, 1920, 1080);
      
      if (t < 0.5) {
        // Single star → multiple stars appearing
        const p = t / 0.5;
        const visibleCount = Math.floor(p * peopleCount);
        ctx.fillStyle = ACCENT;
        ctx.globalAlpha = 0.7;
        for (let j = 0; j < visibleCount; j++) {
          const angle = (j / peopleCount) * Math.PI * 2;
          const radius = 200 + (j % 3) * 80;
          const x = 960 + Math.cos(angle) * radius * p;
          const y = 540 + Math.sin(angle) * radius * p;
          ctx.beginPath();
          ctx.arc(x, y, 3, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.globalAlpha = 1;
      } else {
        // Stars move to engine positions
        const p = (t - 0.5) / 0.5;
        const easeP = p * p * (3 - 2 * p); // smoothstep
        ctx.fillStyle = ACCENT;
        ctx.globalAlpha = 0.7;
        for (let j = 0; j < Math.min(peopleCount, targetPositions.length); j++) {
          const angle = (j / peopleCount) * Math.PI * 2;
          const radius = 200 + (j % 3) * 80;
          const startX = 960 + Math.cos(angle) * radius;
          const startY = 540 + Math.sin(angle) * radius;
          const endX = targetPositions[j].x;
          const endY = targetPositions[j].y;
          const x = startX + (endX - startX) * easeP;
          const y = startY + (endY - startY) * easeP;
          ctx.beginPath();
          ctx.arc(x, y, 3, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.globalAlpha = 1;
      }
      
      await wait(16);
    }
    
    canvasWrap.style.opacity = '0';
    blackout(false);
    await engine.go(0);
  }
  
  // 1-3: wow3 추출 — 클로즈업 → LLM 아이콘 → 분열
  async function beat_1_3() {
    setText('1-3');
    await engine.focusPerson(person.id, {split: false});
    
    if (!reduced) {
      await wait(800);
      
      // Show LLM icon overlay (simplified: a brief pulsing circle with rays)
      const overlay = document.createElement('div');
      overlay.style.cssText = 'position:fixed;inset:0;display:grid;place-items:center;'
        + 'pointer-events:none;z-index:38;opacity:0;transition:opacity 0.6s';
      const icon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      icon.setAttribute('width', '120');
      icon.setAttribute('height', '120');
      icon.setAttribute('viewBox', '0 0 120 120');
      icon.style.cssText = 'filter:drop-shadow(0 0 20px rgba(180,220,203,0.4))';
      
      // Center circle
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', '60');
      circle.setAttribute('cy', '60');
      circle.setAttribute('r', '16');
      circle.setAttribute('fill', 'none');
      circle.setAttribute('stroke', ACCENT);
      circle.setAttribute('stroke-width', '2');
      icon.append(circle);
      
      // Rays
      for (let angle = 0; angle < Math.PI * 2; angle += Math.PI / 4) {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', 60 + Math.cos(angle) * 24);
        line.setAttribute('y1', 60 + Math.sin(angle) * 24);
        line.setAttribute('x2', 60 + Math.cos(angle) * 40);
        line.setAttribute('y2', 60 + Math.sin(angle) * 40);
        line.setAttribute('stroke', ACCENT);
        line.setAttribute('stroke-width', '2');
        line.setAttribute('opacity', '0.6');
        icon.append(line);
      }
      
      overlay.append(icon);
      document.body.append(overlay);
      
      requestAnimationFrame(() => {
        overlay.style.opacity = '1';
      });
      
      await wait(1200);
      overlay.style.opacity = '0';
      await wait(600);
      overlay.remove();
    }
    
    await engine.splitPerson();
  }
  
  // 1-4: wow4 전원 분열 — 전원의 과제 펼치기
  async function beat_1_4() {
    setText('1-4');
    await engine.clearPerson();
    await engine.go(1);
  }
  
  // 1-5: PJT 격자
  async function beat_1_5() {
    setText('1-5');
    await engine.go(2);
  }
  
  // 1-6: wow5 성운 — PJT로 들어가 과제군 응집
  async function beat_1_6() {
    setText('1-6');
    await engine.enterPjt(person.pjt);
  }
  
  // 1-7: 역량 — 과제 선택 + 카드 오버레이
  async function beat_1_7() {
    setText('1-7');
    await engine.selectTask(task.id);
    
    // Engine will show task details in its panel
    // Story layer fades text slightly to not compete
    layer.style.opacity = '0.8';
    await wait(400);
    layer.style.opacity = '1';
  }
  
  // 1-8: 맺음
  async function beat_1_8() {
    blackout(true);
    setText('1-8');
  }
  
  const steps = {
    '1-0': beat_1_0,
    '1-1': beat_1_1,
    '1-2': beat_1_2,
    '1-3': beat_1_3,
    '1-4': beat_1_4,
    '1-5': beat_1_5,
    '1-6': beat_1_6,
    '1-7': beat_1_7,
    '1-8': beat_1_8,
  };
  
  let index = 0;
  
  async function goto(id) {
    index = beats.indexOf(id);
    if (index === -1) return;
    await steps[id]();
  }
  
  window.nebulaStory = {
    beats,
    goto,
    current: () => beats[index]
  };
  
  // Keyboard navigation
  addEventListener('keydown', (e) => {
    if (e.key === ' ' || e.key === 'ArrowRight') {
      e.preventDefault();
      const next = Math.min(index + 1, beats.length - 1);
      if (next !== index) goto(beats[next]);
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      const prev = Math.max(index - 1, 0);
      if (prev !== index) goto(beats[prev]);
    } else if (e.key.toLowerCase() === 'r') {
      e.preventDefault();
      goto(beats[index]);
    }
  });
  
  // Start
  goto(beats[0]);
})();
