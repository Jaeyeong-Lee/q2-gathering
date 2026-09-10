// Optional browser check: NODE_PATH=/private/tmp/auk-atlas-browser/node_modules node check_nebula.cjs
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const {pathToFileURL}=require('node:url');
const path=require('node:path');
(async()=>{
 const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const page=await browser.newPage({viewport:{width:1600,height:1000}});
 const errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url());});
 await page.goto(pathToFileURL(path.join(__dirname,'future-nebula.html')).href);
 await page.waitForTimeout(1900);
 const data=await page.evaluate(()=>JSON.parse(document.getElementById('data').textContent));
 assert.equal(data.people.length,200);assert.equal(data.tasks.length,440);assert.equal(data.categories.length,24);
 for(const t of data.tasks){const p=data.people.find(p=>p.id===t.person);assert.ok(p.text.includes(t.quote));for(const sk of t.skills)assert.ok(p.text.includes(sk.quote));if(t.horizon==='short')assert.ok(t.quote.includes('단기'));if(t.horizon==='long')assert.ok(t.quote.includes('장기'));}
 const visibleNodes=()=>page.locator('.task').evaluateAll(ns=>ns.filter(n=>Number(n.style.opacity)>0).length);
 await page.locator('[data-person="1"]').click();await page.locator('[data-scene="1"]').click();assert.ok(await page.locator('#panel h2').textContent());
 await page.locator('#clear').click();assert.equal(await visibleNodes(),440);
 await page.locator('[data-scene="2"]').click();await page.locator('#pjt').selectOption('0');await page.waitForTimeout(1900);
 assert.equal(await visibleNodes(),data.tasks.filter(t=>t.pjt===0).length);
 assert.equal(await page.locator('[data-category-node]').count(),3);
 await page.screenshot({path:'/private/tmp/nebula-pjt.png'});
 await page.locator('[data-category-node="0-0"]').click();assert.ok((await page.locator('#panel h2').textContent()).includes('병렬'));
 await page.locator('[data-capabilities]').click();await page.waitForTimeout(1900);
 assert.equal(await page.locator('.skill').count(),3);
 await page.locator('[data-skill="gap:병렬 실행 설계"]').click();assert.ok((await page.locator('#panel h2').textContent()).includes('병렬 실행 설계'));
 await page.locator('#panel [data-task]').first().click();assert.ok(await page.locator('#panel .quote').isVisible());assert.ok(await page.locator('#panel .evidence').count());
 const taskHash=new URL(page.url()).hash;await page.reload();await page.waitForTimeout(150);assert.equal(new URL(page.url()).hash,taskHash);assert.ok(await page.locator('#panel .quote').isVisible());
 await page.locator('#clear').click();await page.locator('[data-scene="3"]').click();await page.locator('#pjt').selectOption('all');await page.waitForTimeout(1900);
 assert.equal(await visibleNodes(),440);assert.ok(await page.getByText('시점 미명시',{exact:true}).first().isVisible());await page.screenshot({path:'/private/tmp/nebula-time-final.png'});
 await page.locator('#search').fill('김서윤');assert.equal(await page.locator('#panel [data-task]').count(),data.tasks.filter(t=>t.person===1).length);
 await page.locator('#about').click();assert.ok(await page.locator('dialog').isVisible());await page.locator('#close').click();
 await page.locator('[data-scene="4"]').click();await page.waitForTimeout(1900);await page.screenshot({path:'/private/tmp/nebula-skills-final.png'});
 await page.setViewportSize({width:390,height:844});await page.emulateMedia({reducedMotion:'reduce'});await page.waitForTimeout(500);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await page.screenshot({path:'/private/tmp/nebula-mobile.png',fullPage:true});
 await page.clock.install();await page.locator('[data-scene="0"]').click();await page.locator('#play').click();await page.clock.fastForward(10010);assert.ok((await page.locator('[data-scene="1"]').getAttribute('class')).includes('active'));await page.locator('#play').click();
 assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);console.log('PASS: source evidence, time labels, PJT filtering, task split, category drill-down, skill evidence, reload, search, offline, mobile, autoplay');await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
