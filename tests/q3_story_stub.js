// 검수용 최소 story — window.nebulaStory 계약과 비트별 엔진 호출 순서만 보여준다. 연출은 없다.
// 시각 후보는 docs/q3-visual/<agent-id>/story.js에 따로 만든다(docs/q3-visual-brief.md §2·§3).
(() => {
  if (new URLSearchParams(location.hash.slice(1)).get('mode') !== 'story') return;
  const engine = window.nebula;
  const copy = window.nebulaCopy;
  const data = JSON.parse(document.getElementById('data').textContent);
  const person = data.people.find(p => p.pid === 'P000');
  const task = data.tasks.find(t => t.person === person.id);
  const beats = ['1-0', '1-1', '1-2', '1-3', '1-4', '1-5', '1-6', '1-7', '1-8'];

  const layer = document.createElement('div');
  layer.style.cssText = 'position:fixed;inset:0;display:grid;place-items:center;white-space:pre-line;'
    + 'text-align:center;font:64px/1.3 sans-serif;color:#f2f0e9;pointer-events:none;z-index:40';
  document.body.append(layer);
  const blackout = on => { layer.style.background = on ? '#030506' : 'transparent'; };

  const steps = {
    '1-0': async () => blackout(true),
    '1-1': async () => blackout(true),
    '1-2': async () => { await engine.go(0); blackout(false); },
    '1-3': async () => { await engine.focusPerson(person.id, {split: false}); await engine.splitPerson(); },
    '1-4': async () => { await engine.clearPerson(); await engine.go(1); },
    '1-5': async () => engine.go(2),
    '1-6': async () => engine.enterPjt(person.pjt),
    '1-7': async () => engine.selectTask(task.id),
    '1-8': async () => blackout(true),
  };

  let index = 0;
  async function goto(id) {
    index = beats.indexOf(id);
    layer.textContent = copy[id].screen.join('\n');
    await steps[id]();
  }
  window.nebulaStory = {beats, goto, current: () => beats[index]};
  addEventListener('keydown', e => {
    if (e.key === ' ' || e.key === 'ArrowRight') goto(beats[Math.min(index + 1, beats.length - 1)]);
    else if (e.key === 'ArrowLeft') goto(beats[Math.max(index - 1, 0)]);
    else if (e.key.toLowerCase() === 'r') goto(beats[index]);
  });
  goto(beats[0]);
})();
