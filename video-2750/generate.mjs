import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repository = join(here, "..");
const payloadPath = join(repository, "fixtures", "payload-2750-slim.json");
const payloadText = await readFile(payloadPath, "utf8");
const payload = JSON.parse(payloadText);

if (payload.synthetic !== true || payload.people.length !== 320 || payload.tasks.length !== 2750) {
  throw new Error("Expected the synthetic 320-person / 2,750-task slim fixture.");
}

const packageJson = `${JSON.stringify({
  name: "nebula-2750",
  private: true,
  type: "module",
  scripts: {
    dev: "npx --yes hyperframes@0.8.73 preview",
    lint: "npx --yes hyperframes@0.8.73 lint",
    check: "npx --yes hyperframes@0.8.73 check",
    render: "npx --yes hyperframes@0.8.73 render",
  },
}, null, 2)}\n`;

const hyperframesJson = `${JSON.stringify({
  $schema: "https://hyperframes.heygen.com/schema/hyperframes.json",
  registry: "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
  paths: {
    blocks: "compositions",
    components: "compositions/components",
    assets: "assets",
  },
  media: { autoProxy: true },
}, null, 2)}\n`;

function documentFor(mode) {
  const isExpand = mode === "expand";
  const noGlow = mode === "scene2-noglow";
  const title = isExpand
    ? "사람의 자리에서, 과제가 갈라져 나옵니다."
    : "흩어진 과제들이, 성운을 이룹니다.";
  const subtitle = isExpand
    ? "320명의 별에서 2,750개의 과제 별이 펼쳐집니다."
    : "PJT마다 다른 업무 언어를 존중하며, 비슷한 과제들을 함께 읽습니다.";

  return `<!doctype html>
<html lang="ko" data-resolution="landscape">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1920, height=1080" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"><\/script>
<style>
@font-face{font-family:'Apple SD Gothic Neo';src:local('Apple SD Gothic Neo'),local('AppleSDGothicNeo-Regular')}
@font-face{font-family:'Avenir Next';src:local('Avenir Next'),local('AvenirNext-Regular')}
*{margin:0;padding:0;box-sizing:border-box}
html,body{margin:0;width:1920px;height:1080px;overflow:hidden;background:#0e1225;font-family:"Apple SD Gothic Neo","Avenir Next",sans-serif}
#root{width:100%;height:100%;position:relative}
.scene{width:100%;height:100%;position:relative}
.bg-glow{position:absolute;inset:0;background:radial-gradient(ellipse at 45% 46%,#25223f99,transparent 66%);pointer-events:none}
svg#sky{width:100%;height:100%;display:block}
.title-overlay{position:absolute;bottom:50px;left:0;right:0;text-align:center;pointer-events:none;z-index:5}
.title-overlay h2{color:#f1eff8;font-size:32px;font-weight:500;letter-spacing:-0.055em;line-height:1.3}
.title-overlay p{color:#a19eb8;font-size:15px;margin-top:10px;letter-spacing:.02em}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="8" data-width="1920" data-height="1080">
  <div class="scene clip" id="nebula-scene" data-start="0" data-duration="8" data-track-index="0">
    <div class="bg-glow"></div>
    <svg id="sky" viewBox="0 0 1200 720" preserveAspectRatio="xMidYMid slice">
      <defs>
        <filter id="blur" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="22"/></filter>
        <filter id="starGlow" x="-150%" y="-150%" width="400%" height="400%"><feGaussianBlur stdDeviation="3"/></filter>
        <filter id="gas" x="-50%" y="-50%" width="200%" height="200%">
          <feTurbulence type="fractalNoise" baseFrequency="0.019" numOctaves="3" seed="11" result="noise"/>
          <feDisplacementMap in="SourceGraphic" in2="noise" scale="38"/>
          <feGaussianBlur stdDeviation="9"/>
        </filter>
      </defs>
      <g id="nebulas"></g>
      <g id="cells"></g>
      <g id="persons"></g>
      <g id="tasks"></g>
      <g id="labels"></g>
    </svg>
    <div class="title-overlay">
      <h2>${title}</h2>
      <p>${subtitle}</p>
    </div>
  </div>
</div>
<script type="application/json" id="data">${payloadText.trim()}<\/script>
<script>
'use strict';
const MODE=${JSON.stringify(mode)};
const D=JSON.parse(document.getElementById('data').textContent);
const NS='http://www.w3.org/2000/svg';
const COLS=4;
const HIGHLIGHT_PJT=0;
function el(tag,attrs){const e=document.createElementNS(NS,tag);if(attrs)for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);return e;}

const originals=new Map();
D.people.forEach((p,i)=>{
  if(p.x!==null) originals.set(p.id,[100+p.x*950,95+p.y*465]);
  else{const a=(i/D.people.length)*Math.PI*2-Math.PI/2;originals.set(p.id,[575+Math.cos(a)*440,327+Math.sin(a)*215]);}
});
function pjtCell(i){
  const rows=Math.max(1,Math.ceil(D.pjts.length/COLS)),w=1040/COLS,h=480/rows;
  return{x:80+(i%COLS)*w,y:115+Math.floor(i/COLS)*h,width:w,height:h};
}
function ring(index,total,rx,ry){
  const a=(index/Math.max(1,total))*Math.PI*2-Math.PI/2;
  return total<2?[0,0]:[Math.cos(a)*rx,Math.sin(a)*ry];
}
const categoriesByPjt=D.pjts.map((_,pjt)=>D.categories.filter(c=>c.pjt===pjt));
const categoryById=new Map(D.categories.map(c=>[c.id,c]));
function clusterCenter(c){
  const siblings=categoriesByPjt[c.pjt],index=siblings.findIndex(x=>x.id===c.id);
  const[dx,dy]=ring(index,siblings.length,90,70),cell=pjtCell(c.pjt);
  return[cell.x+cell.width/2+dx,cell.y+cell.height/2+dy];
}
function offsets(t,r){
  const angle=t.seed*Math.PI*2,dist=Math.sqrt((Math.sin(t.seed*7919)+1)/2)*r;
  return[Math.cos(angle)*dist,Math.sin(angle)*dist*.72];
}
function phase1Pos(t){const p=originals.get(t.person),a=t.seq*2.1+t.seed;return[p[0]+Math.cos(a)*22,p[1]+Math.sin(a)*22];}
function pjtCellPos(t){const c=pjtCell(t.pjt),o=offsets(t,Math.min(c.width*.39,c.height*.4));return[c.x+c.width/2+o[0],c.y+c.height*.59+o[1]];}
function clusterPos(t){const c=categoryById.get(t.category),[cx,cy]=clusterCenter(c),o=offsets(t,60);return[cx+o[0],cy+o[1]];}
function glowFor(pjt){return MODE!=='scene2-noglow'||pjt===HIGHLIGHT_PJT?'url(#starGlow)':null;}
function halo(radius,fill,opacity,pjt){
  const attrs={r:radius,fill,opacity},filter=glowFor(pjt);
  if(filter) attrs.filter=filter;
  return el('circle',attrs);
}

const personNodes=[];
D.people.forEach(p=>{
  const[x,y]=originals.get(p.id),color=D.pjts[p.pjt].color,g=el('g',{class:'person'});
  g.append(halo(14,color,.19,p.pjt),el('circle',{r:5,fill:color}));
  document.getElementById('persons').append(g);
  personNodes.push(g);
});

const taskNodes=[],originPos=[],p1Pos=[],cellPos=[],clusterPositions=[];
const pjtIndices={};
D.pjts.forEach((_,i)=>pjtIndices[i]=[]);
D.tasks.forEach((task,index)=>{
  const origin=originals.get(task.person),phase1=phase1Pos(task),cell=pjtCellPos(task),cluster=clusterPos(task);
  const color=D.pjts[task.pjt].color,g=el('g',{class:'task'});
  g.append(halo(9,color,.34,task.pjt),el('circle',{r:2.9,fill:color,class:'core'}));
  document.getElementById('tasks').append(g);
  taskNodes.push(g);originPos.push(origin);p1Pos.push(phase1);cellPos.push(cell);clusterPositions.push(cluster);
  pjtIndices[task.pjt].push(index);
});

const cellRects=[],cellLabels=[],nebulaGroups=[],categoryLabels=[];
if(MODE!=='expand'){
  D.pjts.forEach((pjt,index)=>{
    const cell=pjtCell(index);
    const rect=el('rect',{x:cell.x,y:cell.y,width:cell.width,height:cell.height,fill:'none',stroke:pjt.color,'stroke-width':1.5,'stroke-opacity':.3,rx:12});
    document.getElementById('cells').append(rect);cellRects.push(rect);
    const label=el('text',{x:cell.x+cell.width/2,y:cell.y+28,'text-anchor':'middle',fill:pjt.color,'font-size':14,'font-family':'"Apple SD Gothic Neo",sans-serif','font-weight':'500','letter-spacing':'.05em'});
    label.textContent=pjt.name;document.getElementById('labels').append(label);cellLabels.push(label);
  });
  categoriesByPjt[HIGHLIGHT_PJT].forEach(category=>{
    const[cx,cy]=clusterCenter(category),color=D.pjts[HIGHLIGHT_PJT].color,nebula=el('g',{});
    nebula.append(
      el('ellipse',{cx,cy,rx:80,ry:50,fill:color,opacity:.2,filter:'url(#gas)',transform:'rotate(-22 '+cx+' '+cy+')'}),
      el('ellipse',{cx:cx+80*.23,cy:cy-50*.18,rx:80*.68,ry:50*.48,fill:color,opacity:.13,filter:'url(#blur)',transform:'rotate(24 '+cx+' '+cy+')'})
    );
    document.getElementById('nebulas').append(nebula);nebulaGroups.push(nebula);
    const label=el('text',{x:cx,y:cy-55,'text-anchor':'middle',fill:'#d9d2ee','font-size':14,'font-family':'"Apple SD Gothic Neo",sans-serif','font-weight':'500'});
    label.textContent=category.name;document.getElementById('labels').append(label);categoryLabels.push(label);
  });
}

const tl=gsap.timeline({paused:true});
if(MODE==='expand'){
  gsap.set(personNodes,{x:i=>originals.get(D.people[i].id)[0],y:i=>originals.get(D.people[i].id)[1]});
  gsap.set(taskNodes,{x:i=>originPos[i][0],y:i=>originPos[i][1],opacity:0,scale:.15});
  tl.from(personNodes,{opacity:0,scale:.35,duration:.7,stagger:.002,ease:'power2.out'},0);
  tl.to(personNodes,{scale:1.18,duration:.35,ease:'power1.out'},1.25);
  tl.to(personNodes,{scale:1,duration:.45,ease:'power2.inOut'},1.6);
  tl.to(taskNodes,{opacity:1,scale:1,x:i=>p1Pos[i][0],y:i=>p1Pos[i][1],duration:3.7,stagger:{each:.00035,from:'start'},ease:'power2.inOut'},1.45);
  tl.to(personNodes,{opacity:.78,duration:1.2,ease:'power2.inOut'},3.3);
}else{
  gsap.set(taskNodes,{x:i=>p1Pos[i][0],y:i=>p1Pos[i][1]});
  gsap.set(personNodes,{x:i=>originals.get(D.people[i].id)[0],y:i=>originals.get(D.people[i].id)[1]});
  gsap.set([cellRects,cellLabels,nebulaGroups,categoryLabels],{opacity:0});
  tl.from(taskNodes,{opacity:0,scale:.2,duration:.8,stagger:.002,ease:'power2.out'},0);
  tl.from(personNodes,{opacity:0,duration:.6,stagger:.003,ease:'power2.out'},0);
  tl.to(taskNodes,{x:i=>cellPos[i][0],y:i=>cellPos[i][1],duration:2,ease:'power2.inOut'},1.5);
  tl.to(personNodes,{opacity:0,duration:1,ease:'power2.inOut'},1.5);
  tl.to(cellRects,{opacity:1,duration:.8,stagger:.08,ease:'power2.out'},2.2);
  tl.to(cellLabels,{opacity:1,duration:.8,stagger:.08,ease:'power2.out'},2.4);
  const otherPjtIndices=[];
  for(let p=1;p<D.pjts.length;p++) otherPjtIndices.push(...pjtIndices[p]);
  tl.to(otherPjtIndices.map(i=>taskNodes[i]),{opacity:.12,duration:.6,ease:'power2.inOut'},3.5);
  for(let p=1;p<D.pjts.length;p++){
    tl.to(cellRects[p],{'stroke-opacity':.08,duration:.6},3.5);
    tl.to(cellLabels[p],{opacity:.12,duration:.6},3.5);
  }
  tl.to(cellRects[HIGHLIGHT_PJT],{'stroke-opacity':.55,'stroke-width':2.5,duration:.6},3.5);
  const highlighted=pjtIndices[HIGHLIGHT_PJT],highlightedClusters=highlighted.map(i=>clusterPositions[i]);
  tl.to(highlighted.map(i=>taskNodes[i]),{x:j=>highlightedClusters[j][0],y:j=>highlightedClusters[j][1],duration:2.5,ease:'power2.inOut'},4.5);
  tl.to(nebulaGroups,{opacity:1,duration:1.5,stagger:.15,ease:'power2.out'},5);
  tl.to(categoryLabels,{opacity:1,duration:1,stagger:.1,ease:'power2.out'},5.5);
  tl.to(cellRects,{opacity:0,duration:.8,ease:'power2.inOut'},4.5);
  tl.to(cellLabels,{opacity:0,duration:.8,ease:'power2.inOut'},4.5);
}

window.__timelines['main']=tl;
tl.seek(0);
<\/script>
</body>
</html>
`;
}

for (const mode of ["expand", "scene2", "scene2-noglow"]) {
  const directory = join(here, mode);
  await mkdir(directory, { recursive: true });
  await writeFile(join(directory, "index.html"), documentFor(mode));
  await writeFile(join(directory, "package.json"), packageJson);
  await writeFile(join(directory, "hyperframes.json"), hyperframesJson);
  await writeFile(join(directory, "meta.json"), `${JSON.stringify({
    id: `nebula-${mode}-2750`,
    name: `nebula-${mode}-2750`,
    fixture: "../../fixtures/payload-2750-slim.json",
    synthetic: true,
  }, null, 2)}\n`);
}
