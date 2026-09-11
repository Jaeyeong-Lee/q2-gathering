// Synthetic edge cases for the presentation. Uses the same optional Playwright runtime as nebula_browser.cjs.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const { pathToFileURL } = require("node:url");
let chromium;
try {
  ({ chromium } = require("../nebula/browser-tests/node_modules/playwright"));
} catch {
  ({ chromium } = require("playwright"));
}
const out = fs.mkdtempSync(path.join(os.tmpdir(), "nebula-presentation-"));
const fixture = spawnSync(
  process.env.NEBULA_PYTHON || "python3",
  [
    "-c",
    `
import sys
from pathlib import Path
from nebula.demo import source, FakeClient
from nebula.pipeline import run, with_review
from nebula.render import build
root = Path(sys.argv[1])
class Empty(FakeClient):
    def complete(self, stage, *args):
        return {stage: []}
build(run(source()[:1], root/'empty', Empty()), root/'empty')
# Fixture deliberately exercises real-data labels without using real records.
class RealLabels(FakeClient):
    cache_identity = {'provider': 'local-fixture'}
inputs = source()[:2]
inputs[0]['pjt'] = 'PJT "><img src=x onerror=alert(1)>'
data = run(inputs, root/'populated', RealLabels())
decisions = {t['id']: {'status':'approved', 'category_id': None, 'note': '분류 검토'} for t in data['tasks']}
build(with_review(data, {'run_id': data['run_id'], 'decisions': decisions}), root/'populated')
build(run(source()[:1], root/'unapproved', FakeClient()), root/'unapproved', True)
`,
    out,
  ],
  { encoding: "utf8" },
);
assert.equal(fixture.status, 0, fixture.stderr);
(async () => {
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.NEBULA_BROWSER
      ? { executablePath: process.env.NEBULA_BROWSER }
      : {}),
  });
  try {
    const page = await browser.newPage({
      viewport: { width: 1600, height: 1000 },
    });
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("dialog", async (d) => {
      errors.push("Unexpected dialog");
      await d.dismiss();
    });
    const url = (folder, hash = "") =>
      pathToFileURL(path.join(out, folder, "nebula.html")).href + hash;
    for (const folder of ["empty", "unapproved"]) {
      await page.goto(url(folder, "#scene=4"));
      await page.waitForTimeout(150);
      assert.deepEqual(errors, [], "empty presentation must render");
      assert.match(
        await page.locator("#panel").innerText(),
        /표시할 과제가 없습니다/,
      );
      await page.locator("#play").click();
      await page.waitForTimeout(10200);
      await page.locator("#play").click();
      assert.ok(
        (await page.locator(".step.active").innerText()).includes("02"),
      );
    }
    await page.goto(url("populated"));
    await page.waitForTimeout(150);
    assert.match(
      await page.locator("#panel h2").innerText(),
      /별 하나/,
      "absent person hash must not select index zero",
    );
    await page.locator('[data-person-node="0"]').press("Enter");
    assert.match(await page.locator("#panel h2").innerText(), /합성 인물/);
    assert.ok(new URL(await page.url()).hash.includes("person=0"));
    await page.reload();
    assert.match(await page.locator("#panel h2").innerText(), /합성 인물/);
    await page.locator('[data-scene="1"]').click();
    await page.locator("#tasks .task").first().press("Enter");
    assert.match(await page.locator("#panel").innerText(), /승인/);
    assert.doesNotMatch(
      await page.locator("#panel").innerText(),
      /합성 회고 원문/,
    );
    assert.equal(
      await page.locator("#panel img").count(),
      0,
      "PJT names must stay text",
    );
    await page
      .locator("#panel summary")
      .filter({ hasText: "시간 근거·분류 이유" })
      .click();
    assert.match(await page.locator("#panel").innerText(), /분류 검토/);
    const relation = page
      .locator("#panel summary")
      .filter({ hasText: "과제와 연결한 원문 근거" })
      .first();
    await relation.click();
    assert.ok((await relation.locator("..").innerText()).includes("과제"));
    await page.locator('[data-scene="4"]').click();
    await page.waitForTimeout(1800);
    await page.screenshot({ path: path.join(out, "capabilities.png") });
    assert.deepEqual(errors, []);
    console.log(
      "PASS: zero tasks, zero approvals, autoplay, first person, provenance, escaped unclassified PJT",
    );
    console.log(out);
  } finally {
    await browser.close();
  }
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
