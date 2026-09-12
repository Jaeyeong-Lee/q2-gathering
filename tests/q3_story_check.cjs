// 1부 story 후보 검수 — docs/q3-visual-brief.md §3.3·§4·§6.
// 합성 픽스처로 빌드 → #mode=story → 비트마다 goto·스크린샷 → 계약 확인. reduced-motion으로 한 번 더.
// 사용: NEBULA_PYTHON=$PWD/.venv/bin/python node tests/q3_story_check.cjs <story.js> <shots dir>
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const {pathToFileURL} = require('node:url');
const {chromium} = require('../nebula/browser-tests/node_modules/playwright');

const [storyArg, shotsArg] = process.argv.slice(2);
if (!storyArg || !shotsArg) {
  console.error('usage: node tests/q3_story_check.cjs <story.js> <shots dir>');
  process.exit(2);
}
const BEATS = ['1-0', '1-1', '1-2', '1-3', '1-4', '1-5', '1-6', '1-7', '1-8'];
const BEAT_TIMEOUT_MS = 20000;
const out = path.resolve('data/q3-visual/check');
const shots = path.resolve(shotsArg);
fs.rmSync(out, {recursive: true, force: true});
fs.mkdirSync(shots, {recursive: true});
const build = spawnSync(process.env.NEBULA_PYTHON || 'python3', ['-m', 'nebula', 'demo',
  '--input', 'nebula/fixtures/q3/persons.json', '--network', 'nebula/fixtures/q3/neighbors.json', '--out', out],
  {encoding: 'utf8', env: {...process.env, NEBULA_STORY: path.resolve(storyArg)}});
assert.equal(build.status, 0, build.stderr);
const url = pathToFileURL(path.join(out, 'nebula.html')).href;
const hashOf = page => new URLSearchParams(new URL(page.url()).hash.slice(1));

function withTimeout(promise, label) {
  let timer;
  const limit = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(`${label}: did not resolve in ${BEAT_TIMEOUT_MS}ms`)), BEAT_TIMEOUT_MS);
  });
  return Promise.race([promise, limit]).finally(() => clearTimeout(timer));
}

async function live(browser) {
  const page = await browser.newPage({viewport: {width: 1920, height: 1080}});
  await page.goto(url);
  const [title, expected, hasStory] = await page.evaluate(() => [
    document.getElementById('title').textContent,
    window.nebulaCopy['scene-0'].screen.join(' '),
    'nebulaStory' in window,
  ]);
  assert.equal(title, expected, 'engine scene titles come from deck.md');
  assert.equal(hasStory, false, 'story stays inactive outside #mode=story');
  await page.close();
}

async function walk(browser, reducedMotion, capture) {
  const page = await browser.newPage({viewport: {width: 1920, height: 1080}, reducedMotion});
  const errors = [];
  const requests = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('request', r => { if (!/^(file|data|blob):/.test(r.url())) requests.push(r.url()); });
  await page.goto(url + '#mode=story');
  await page.waitForFunction(() => window.nebulaStory && window.nebulaCopy, null, {timeout: BEAT_TIMEOUT_MS});
  assert.deepEqual(await page.evaluate(() => window.nebulaStory.beats), BEATS);
  const copy = await page.evaluate(() => window.nebulaCopy);
  const started = Date.now();
  for (const beat of BEATS) {
    await withTimeout(page.evaluate(id => window.nebulaStory.goto(id), beat), `${reducedMotion} ${beat}`);
    assert.equal(await page.evaluate(() => window.nebulaStory.current()), beat);
    const line = copy[beat].screen[0];
    if (line) {
      assert.ok(await page.evaluate(text => document.body.innerText.includes(text), line),
        `${beat}: the deck.md screen line must be on screen`);
    }
    if (beat === '1-2') assert.equal(hashOf(page).get('scene'), '0', '1-2 must hand off to engine scene 0');
    if (beat === '1-6') assert.ok(hashOf(page).has('pjt'), '1-6 must enter a PJT');
    assert.equal(await page.locator('#synthetic-mark').isVisible(), true, `${beat}: synthetic mark must stay visible`);
    if (capture) await page.screenshot({path: path.join(shots, `${beat}.png`)});
  }
  assert.deepEqual(errors, [], 'no page or console errors');
  assert.deepEqual(requests, [], 'offline: no network requests');
  await page.close();
  return Date.now() - started;
}

(async () => {
  const browser = await chromium.launch({headless: true,
    ...(process.env.NEBULA_BROWSER ? {executablePath: process.env.NEBULA_BROWSER} : {})});
  try {
    await live(browser);
    const motion = await walk(browser, 'no-preference', true);
    const reduced = await walk(browser, 'reduce', false);
    console.log(`PASS: ${storyArg} — 9 beats ${motion}ms, reduced motion ${reduced}ms`);
    console.log(`shots: ${shots}`);
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
