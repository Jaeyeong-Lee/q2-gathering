import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectDir = path.resolve(scriptDir, '..');
const repoDir = path.resolve(projectDir, '..');
const fixturePath = path.join(repoDir, 'fixtures', 'payload-320-slim.json');
const outputDir = path.join(projectDir, 'compositions');
const payload = JSON.parse(fs.readFileSync(fixturePath, 'utf8'));
const serializedPayload = JSON.stringify(payload).replaceAll('<', '\\u003c');
const gasPngPath = path.join(projectDir, 'assets', 'nebula-gas-320.png');
const gasPngDataUri = `data:image/png;base64,${fs.readFileSync(gasPngPath).toString('base64')}`;

function composition({ id, nofilter }) {
  const gasLayer = nofilter ? `<image id="gas-background" href="${gasPngDataUri}" x="0" y="0" width="1200" height="720"/>` : '';
  const nebulaOverflow = nofilter ? ' data-layout-allow-overflow' : '';
  const gasFilter = nofilter ? '' : `<filter id="gas" x="-50%" y="-50%" width="200%" height="200%">
          <feTurbulence type="fractalNoise" baseFrequency="0.019" numOctaves="3" seed="11" result="noise"/>
          <feDisplacementMap in="SourceGraphic" in2="noise" scale="38"/>
          <feGaussianBlur stdDeviation="9"/>
        </filter>`;

  return `<!doctype html>
<html lang="ko" data-resolution="landscape">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1920, height=1080" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
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
.title-overlay h2{color:#f1eff8;font-size:32px;font-weight:500;letter-spacing:-.055em;line-height:1.3}
.title-overlay p{color:#a19eb8;font-size:15px;margin-top:10px;letter-spacing:.02em}
</style>
</head>
<body>
<div id="root" data-composition-id="${id}" data-start="0" data-duration="8" data-fps="30" data-width="1920" data-height="1080">
  <div class="scene clip" id="nebula-scene" data-start="0" data-duration="8" data-track-index="0">
    <div class="bg-glow"></div>
    <svg id="sky" viewBox="0 0 1200 720" preserveAspectRatio="xMidYMid slice">
      <defs>
        <filter id="blur" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="22"/></filter>
        <filter id="starGlow" x="-150%" y="-150%" width="400%" height="400%"><feGaussianBlur stdDeviation="3"/></filter>
        ${gasFilter}
      </defs>
      <g id="nebulas"${nebulaOverflow}>${gasLayer}</g>
      <g id="cells"></g>
      <g id="persons"></g>
      <g id="tasks"></g>
      <g id="labels"></g>
    </svg>
    <div class="title-overlay">
      <h2>흩어진 과제들이, 성운을 이룹니다.</h2>
      <p>PJT마다 다른 업무 언어를 존중하며, 비슷한 과제들을 함께 읽습니다.</p>
    </div>
  </div>
</div>
<script type="application/json" id="data">${serializedPayload}</script>
<script>
'use strict';
const D=JSON.parse(document.getElementById('data').textContent);
const NS='http://www.w3.org/2000/svg';
const COLS=4;
const FOCUS_PJT=0;
const NOFILTER=${nofilter};
function el(tag,attrs){const e=document.createElementNS(NS,tag);if(attrs)for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);return e;}

const originals=new Map();
D.people.forEach((p,i)=>{
  if(p.x!==null) originals.set(p.id,[100+p.x*950,95+p.y*465]);
  else{const a=(i/D.people.length)*Math.PI*2-Math.PI/2;originals.set(p.id,[575+Math.cos(a)*440,327+Math.sin(a)*215]);}
});
function pjtCell(i){
  const rows=Math.max(1,Math.ceil(D.pjts.length/COLS)),width=1040/COLS,height=480/rows;
  return{x:80+(i%COLS)*width,y:115+Math.floor(i/COLS)*height,width,height};
}
function ring(index,total,rx,ry){
  const a=(index/Math.max(1,total))*Math.PI*2-Math.PI/2;
  return total<2?[0,0]:[Math.cos(a)*rx,Math.sin(a)*ry];
}
function clusterCenter(c){
  const siblings=D.categories.filter(x=>x.pjt===c.pjt),index=siblings.findIndex(x=>x.id===c.id);
  const[dx,dy]=ring(index,siblings.length,265,160);return[555+dx,375+dy];
}
function offsets(t,r){
  const angle=t.seed*Math.PI*2,dist=Math.sqrt((Math.sin(t.seed*7919)+1)/2)*r;
  return[Math.cos(angle)*dist,Math.sin(angle)*dist*.72];
}
function phase1Pos(t){const p=originals.get(t.person),a=t.seq*2.1+t.seed;return[p[0]+Math.cos(a)*22,p[1]+Math.sin(a)*22];}
function pjtCellPos(t){const c=pjtCell(t.pjt),o=offsets(t,Math.min(c.width*.39,c.height*.4));return[c.x+c.width/2+o[0],c.y+c.height*.59+o[1]];}
function clusterPos(t){const c=D.categories.find(x=>x.id===t.category),[cx,cy]=clusterCenter(c),o=offsets(t,115);return[cx+o[0],cy+o[1]];}

const personNodes=[];
D.people.forEach(p=>{
  const c=D.pjts[p.pjt].color,g=el('g',{class:'person'});
  g.append(el('circle',{r:14,fill:c,opacity:.19,filter:'url(#starGlow)'}),el('circle',{r:5,fill:c}));
  document.getElementById('persons').append(g);personNodes.push(g);
});

const taskNodes=[],phase1Positions=[],cellPositions=[],clusterPositions=[],focusIndexes=[],nonfocusIndexes=[];
D.tasks.forEach((t,i)=>{
  const[a,b]=phase1Pos(t),[c,d]=pjtCellPos(t),[e,f]=clusterPos(t),color=D.pjts[t.pjt].color;
  const g=el('g',{class:'task'});
  g.append(el('circle',{r:9,fill:color,opacity:.34,filter:'url(#starGlow)'}),el('circle',{r:2.9,fill:color,class:'core'}));
  document.getElementById('tasks').append(g);
  taskNodes.push(g);phase1Positions.push([a,b]);cellPositions.push([c,d]);clusterPositions.push([e,f]);
  (t.pjt===FOCUS_PJT?focusIndexes:nonfocusIndexes).push(i);
});

gsap.set(taskNodes,{x:i=>phase1Positions[i][0],y:i=>phase1Positions[i][1]});
gsap.set(personNodes,{x:i=>originals.get(D.people[i].id)[0],y:i=>originals.get(D.people[i].id)[1]});

const cellRects=[],cellLabels=[];
D.pjts.forEach((pjt,i)=>{
  const cell=pjtCell(i);
  const rect=el('rect',{x:cell.x,y:cell.y,width:cell.width,height:cell.height,fill:'none',stroke:pjt.color,'stroke-width':1.5,'stroke-opacity':.3,rx:12});
  document.getElementById('cells').append(rect);cellRects.push(rect);
  const label=el('text',{x:cell.x+cell.width/2,y:cell.y+32,'text-anchor':'middle',fill:pjt.color,'font-size':16,'font-family':'"Apple SD Gothic Neo",sans-serif','font-weight':'500','letter-spacing':'.05em'});
  label.textContent=pjt.name;document.getElementById('labels').append(label);cellLabels.push(label);
});

const nebulaGroups=[],categoryLabels=[];
const gasBackground=document.getElementById('gas-background');
D.categories.filter(c=>c.pjt===FOCUS_PJT).forEach(c=>{
  const[cx,cy]=clusterCenter(c),color=D.pjts[FOCUS_PJT].color,animatedGroups=[];
  if(NOFILTER){
    const blurGroup=el('g',{});
    blurGroup.append(el('ellipse',{cx:cx+160*.23,cy:cy-100*.18,rx:160*.68,ry:100*.48,fill:color,opacity:.13,filter:'url(#blur)',transform:'rotate(24 '+cx+' '+cy+')'}));
    document.getElementById('nebulas').append(blurGroup);animatedGroups.push(blurGroup);
  }else{
    const group=el('g',{});
    group.append(
      el('ellipse',{cx,cy,rx:160,ry:100,fill:color,opacity:.2,filter:'url(#gas)',transform:'rotate(-22 '+cx+' '+cy+')'}),
      el('ellipse',{cx:cx+160*.23,cy:cy-100*.18,rx:160*.68,ry:100*.48,fill:color,opacity:.13,filter:'url(#blur)',transform:'rotate(24 '+cx+' '+cy+')'})
    );
    document.getElementById('nebulas').append(group);animatedGroups.push(group);
  }
  nebulaGroups.push(animatedGroups);
  const label=el('text',{x:cx,y:cy-103,'text-anchor':'middle',fill:'#d9d2ee','font-size':16,'font-family':'"Apple SD Gothic Neo",sans-serif','font-weight':'500'});
  label.textContent=c.name;document.getElementById('labels').append(label);categoryLabels.push(label);
});

gsap.set([cellRects,cellLabels,nebulaGroups.flat(),categoryLabels,gasBackground].filter(Boolean),{opacity:0});

const tl=gsap.timeline({paused:true});
tl.from(taskNodes,{opacity:0,scale:.2,duration:.8,stagger:.0015,ease:'power2.out'},0);
tl.from(personNodes,{opacity:0,duration:.6,stagger:.0025,ease:'power2.out'},0);

tl.to(taskNodes,{x:i=>cellPositions[i][0],y:i=>cellPositions[i][1],duration:2,ease:'power2.inOut'},1.5);
tl.to(personNodes,{opacity:0,duration:1,ease:'power2.inOut'},1.5);
tl.to(cellRects,{opacity:1,duration:.8,stagger:.06,ease:'power2.out'},2.2);
tl.to(cellLabels,{opacity:1,duration:.8,stagger:.06,ease:'power2.out'},2.4);

tl.to(nonfocusIndexes.map(i=>taskNodes[i]),{opacity:.12,duration:.6,ease:'power2.inOut'},3.5);
tl.to(cellRects.filter((_,i)=>i!==FOCUS_PJT),{'stroke-opacity':.08,duration:.6},3.5);
tl.to(cellLabels.filter((_,i)=>i!==FOCUS_PJT),{opacity:.12,duration:.6},3.5);
tl.to(cellRects[FOCUS_PJT],{'stroke-opacity':.55,'stroke-width':2.5,duration:.6},3.5);

const focusedClusterPositions=focusIndexes.map(i=>clusterPositions[i]);
tl.to(focusIndexes.map(i=>taskNodes[i]),{x:j=>focusedClusterPositions[j][0],y:j=>focusedClusterPositions[j][1],duration:2.5,ease:'power2.inOut'},4.5);
if(gasBackground)tl.to(gasBackground,{opacity:1,duration:1.5,ease:'power2.out'},5);
nebulaGroups.forEach((groups,index)=>tl.to(groups,{opacity:1,duration:1.5,ease:'power2.out'},5+index*.15));
tl.to(categoryLabels,{opacity:1,duration:1,stagger:.1,ease:'power2.out'},5.5);
tl.to(cellRects,{opacity:0,duration:.8,ease:'power2.inOut'},4.5);
tl.to(cellLabels,{opacity:0,duration:.8,ease:'power2.inOut'},4.5);

window.__timelines=window.__timelines||{};
window.__timelines['${id}']=tl;
tl.seek(0);
</script>
</body>
</html>
`;
}

fs.mkdirSync(outputDir, { recursive: true });
fs.writeFileSync(path.join(outputDir, 'nebula-scene2-320.html'), composition({ id: 'nebula-scene2-320', nofilter: false }));
fs.writeFileSync(path.join(outputDir, 'nebula-scene2-320-nofilter.html'), composition({ id: 'nebula-scene2-320-nofilter', nofilter: true }));
