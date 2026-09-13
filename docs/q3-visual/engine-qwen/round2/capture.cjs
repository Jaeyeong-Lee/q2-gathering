// qwen round2 5컷 캡처 — 미리보기 빌드 후 장면별 스크린샷
const { chromium } = require('playwright');
const path = require('path');
const { execSync } = require('child_process');
const fs = require('fs');

(async () => {
  const cwd = process.cwd();
  const outDir = path.join(cwd, 'docs/q3-visual/engine-qwen/round2/shots');
  fs.mkdirSync(outDir, { recursive: true });
  // 1. 합성 데모 빌드
  execSync('NEBULA_STORY="" ./.venv/bin/python -m nebula demo --out data/q3-visual/engine-qwen-demo', { stdio: 'inherit' });
  const html = path.resolve('data/q3-visual/engine-qwen/nebula.html');
  const shots = [
    ['after-scene0', '#scene=0'],
    ['after-closeup', '#scene=0&person=3'],
    ['after-split', '#scene=1'],
    ['after-grid', '#scene=2'],
    ['after-pjt-nebula', '#scene=2&pjt=1'],
  ];
  const browser = await chromium.launch();
  const errors = [];
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', e => console.error('PAGEERROR:', e.message));
  for (const [name, hash] of shots) {
    await page.goto('file://' + html);
    await page.evaluate(h => { location.hash = h; window.dispatchEvent(new HashChangeEvent('hashchange')); }, hash);
    await page.reload();
    await page.waitForTimeout(2500);
    await page.screenshot({ path: path.join(outDir, name + '.png') });
    console.log('shot:', name);
  }
  await browser.close();
  console.log('DONE 5 shots');
})().catch(e => { console.error(e); process.exitCode = 1; });