// Build synthetic data first: python3 -m nebula demo --out data/nebula-demo
// npm install --prefix nebula/browser-tests && npx --prefix nebula/browser-tests playwright install chromium
// node tests/nebula_browser.cjs [output-directory]
// Optional NEBULA_BROWSER=/path/to/chrome, NEBULA_PYTHON=/path/to/python.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const { spawnSync } = require("node:child_process");
const { pathToFileURL } = require("node:url");
let chromium;
try {
  ({ chromium } = require("../nebula/browser-tests/node_modules/playwright"));
} catch {
  ({ chromium } = require("playwright"));
}
const out = path.resolve(process.argv[2] || "data/nebula-demo");
const temp = fs.mkdtempSync(path.join(os.tmpdir(), "nebula-browser-"));
const python = process.env.NEBULA_PYTHON || "python3";
function cli(args, code = 0) {
  const r = spawnSync(python, ["-m", "nebula", ...args], { encoding: "utf8" });
  assert.equal(r.status, code, r.stderr);
  return r;
}
(async () => {
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.NEBULA_BROWSER
      ? { executablePath: process.env.NEBULA_BROWSER }
      : {}),
  });
  const page = await browser.newPage({
    viewport: { width: 1600, height: 1000 },
    acceptDownloads: true,
  });
  const errors = [],
    requests = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("request", (r) => {
    if (/^https?:/.test(r.url())) requests.push(r.url());
  });
  page.on("dialog", (d) => d.accept());
  const url = (name) => pathToFileURL(path.join(out, name)).href;
  await page.goto(url("matrix.html"));
  assert.ok(await page.locator("#view .bubble").count());
  await page.locator("#view .bubble").first().click();
  assert.ok(await page.locator("#inspector blockquote").count());
  const svgBounds = await page.locator("#view svg").boundingBox();
  assert.ok(
    svgBounds.height < 650,
    "both capability bands should fit together",
  );
  await page.screenshot({ path: path.join(temp, "matrix.png") });
  await page.locator("#pjt").selectOption("");
  const allBubbleCount = await page.locator("#view .bubble").count();
  assert.ok(allBubbleCount > 20);
  const heights = await page.locator("#view svg").getAttribute("viewBox");
  assert.ok(heights.endsWith("500"));
  await page.locator("#tab-people").click();
  assert.ok(await page.locator("#view svg line").count());
  await page.locator("#tab-tasks").click();
  await page.locator(".orb").first().click();
  assert.ok(await page.locator("#inspector blockquote").count());
  await page.locator("#tab-matrix").click();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  assert.equal(
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
    false,
  );
  await page.screenshot({
    path: path.join(temp, "mobile.png"),
    fullPage: true,
  });
  await page.setViewportSize({ width: 1600, height: 1000 });
  await page.goto(url("review.html"));
  await page
    .locator("#detail")
    .getByRole("button", { name: "승인", exact: true })
    .click();
  const category = page.locator("#detail select");
  await category.selectOption("");
  await page.locator("#export").click();
  assert.ok((await page.locator("#message").textContent()).includes("메모"));
  await page
    .locator("#detail textarea")
    .fill("원문을 확인하여 미분류로 정정함");
  const downloadPromise = page.waitForEvent("download");
  await page.locator("#export").click();
  const reviewFile = path.join(temp, "review.json");
  await (await downloadPromise).saveAs(reviewFile);
  const review = JSON.parse(fs.readFileSync(reviewFile));
  assert.ok(
    Object.values(review.decisions).some(
      (d) => d.status === "approved" && d.category_id === null,
    ),
  );
  await page.screenshot({ path: path.join(temp, "review.png") });
  const editor = page
    .locator("details")
    .filter({
      has: page.locator("summary").filter({ hasText: "추출 결과 수정" }),
    })
    .first();
  await editor.locator("summary").first().click();
  const textarea = editor.locator("textarea");
  const original = JSON.parse(await textarea.inputValue());
  original.tasks[0].label += " 검토 정정";
  await textarea.fill(JSON.stringify(original));
  await editor
    .getByRole("button", { name: "JSON 검증 및 정정 저장", exact: true })
    .click();
  const correctionDownload = page.waitForEvent("download");
  await page.locator("#correction-export").click();
  const correctionFile = path.join(temp, "corrections.json");
  await (await correctionDownload).saveAs(correctionFile);
  const correction = JSON.parse(fs.readFileSync(correctionFile));
  assert.equal(correction.persons.length, 1);
  assert.equal(correction.taxonomies, undefined);
  cli(["build", "--out", out, "--review", reviewFile, "--approved-only"]);
  await page.goto(url("matrix.html"));
  const approved = await page.locator("#payload").textContent();
  assert.equal(JSON.parse(approved).tasks.length, 1);
  cli(["demo", "--out", out, "--corrections", correctionFile]);
  cli(["build", "--out", out, "--review", reviewFile, "--approved-only"], 1);
  cli(["demo", "--out", out]);
  assert.deepEqual(errors, []);
  assert.deepEqual(requests, []);
  await browser.close();
  console.log(
    "PASS: matrix, network, tasks, evidence, mobile, review/category correction, extraction correction, stale review, offline",
  );
  console.log("Screenshots: " + temp);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
