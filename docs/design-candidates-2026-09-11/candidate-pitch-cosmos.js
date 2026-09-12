'use strict';
// Deliberately synthetic: coordinates, assignments and document marks are illustrative.
const $ = id => document.getElementById(id);
const ctx = $('art').getContext('2d');
const palette = ['#9dd8c3', '#edb58e', '#eeeae1'];
const scenes = [
  {name:'성찰',duration:18,title:'지나온 나.<br>지금의 나.<br><em>앞으로의 나.</em>',description:'한 장에 담기기 전,\n몇 번이고 되짚었을 생각들.',note:'과거 · 근원경쟁력 · 미래\n작성 과정을 상상한 연출',reflection:true},
  {name:'기록',duration:12,title:'개의 기록.<br>각자의 다음이 모이다.',number:'300',description:'서로 다른 경험, 서로 다른 고민.\n그 흔적을 함께 펼쳐봅니다.',note:'300개 문서를 가정한 합성 시연'},
  {name:'점화',duration:12,title:'파일 뒤에는,<br><em>사람이 있습니다.</em>',description:'기록 하나가, 하나의 별로.',note:'별 하나 = 한 사람의 기록',dark:true},
  {name:'연결',duration:14,title:'닮은 경험은<br>서로를 발견합니다.',description:'기록을 임베딩하고 유사도를 살펴봅니다.',note:'임베딩·유사도의 개념 연출\n실제 계산 결과가 아닌 합성 배치',dark:true},
  {name:'추출',duration:18,title:'한 사람에게도,<br>여러 개의 미래가.',description:'LLM 추출 · 기록 속 미래 과제를 각각 펼칩니다.',note:'개념 시연 · 과제명은 합성 예시',dark:true,center:true},
  {name:'확장',duration:12,title:'관점이 바뀌면,<br>새로운 지도가 열립니다.',description:'사람의 지도에서, 미래 과제의 지도로.',note:'빛의 색은 과제군을 따라갑니다.\n이동 경로는 설명을 위한 연출입니다.',dark:true},
  {name:'합성',duration:14,title:'각자의 다음에서,<br><em>함께 그릴 미래로.</em>',description:'LLM 합성 · 닮은 미래 과제를 함께 읽습니다.',note:'합성 과제군 · 중요도나 실행 순서가 아님\n실제 적용 시 PJT별로 독립 분류',dark:true,center:true}
];
const starts = scenes.map((_,i)=>scenes.slice(0,i).reduce((n,s)=>n+s.duration,0));
const total = scenes.reduce((n,s)=>n+s.duration,0);
const reducedQuery = matchMedia('(prefers-reduced-motion: reduce)');
let reduced = reducedQuery.matches, time = 0, running = false, scene = -1, last = 0;
try {time = Math.max(0,Math.min(total,Number(localStorage.getItem('pitch-cosmos-time'))||0));} catch {}
const clamp = (x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const ease = x=>{x=clamp(x);return x*x*x*(x*(x*6-15)+10);};
const mix = (a,b,t)=>a+(b-a)*t;
const rand = i=>{const x=Math.sin(i*127.1+19.7)*43758.5453;return x-Math.floor(x);};
const point = (a,b,t)=>[mix(a[0],b[0],t),mix(a[1],b[1],t)];
const people = Array.from({length:300},(_,i)=>{
  const a=i*2.39996,r=Math.sqrt(rand(i+41));
  return [1110+(i%3===1?410:i%3===2?160:0)+Math.cos(a)*r*235,370+(i%3===2?320:0)+Math.sin(a)*r*205];
});
const sky = people.map((_,i)=>[970+rand(i+61)*800,230+rand(i+801)*630]);
const targets = [[480,670],[970,690],[1480,660]];
const tasks = Array.from({length:900},(_,i)=>{
  const group=i%3,a=i*2.39996,r=Math.sqrt(rand(i+81))*240;
  return {person:Math.floor(i/3),group,offset:[Math.cos(i*2.1)*20,Math.sin(i*2.1)*20],to:[targets[group][0]+Math.cos(a)*r,targets[group][1]+Math.sin(a)*r*.46]};
});
const docPos = Array.from({length:70},(_,i)=>{
  const a=i*2.39996,r=60+Math.sqrt(i/70)*445;
  return [1360+Math.cos(a)*r,555+Math.sin(a)*r*.8];
});
function glow(x,y,r,color,alpha=1){ctx.save();ctx.globalAlpha=clamp(alpha);const g=ctx.createRadialGradient(x,y,0,x,y,r);g.addColorStop(0,color);g.addColorStop(1,'transparent');ctx.fillStyle=g;ctx.fillRect(x-r,y-r,r*2,r*2);ctx.restore();}
function dot(x,y,r,color='#eeeae1',alpha=1){if(r<=0)return;ctx.save();ctx.globalAlpha=clamp(alpha);ctx.fillStyle=color;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill();ctx.restore();}
function line(a,b,color,alpha=1,width=1){ctx.save();ctx.strokeStyle=color;ctx.globalAlpha=clamp(alpha);ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke();ctx.restore();}
function label(text,x,y,color='#eeeae1',size=27,alpha=1){ctx.save();ctx.globalAlpha=clamp(alpha);ctx.font=`${size}px "Apple SD Gothic Neo", "Malgun Gothic", sans-serif`;ctx.fillStyle=color;ctx.textAlign='center';ctx.fillText(text,x,y);ctx.restore();}
function documentIcon(x,y,s,a,alpha=1,marks=1){ctx.save();ctx.globalAlpha=clamp(alpha);ctx.translate(x,y);ctx.rotate(a);ctx.scale(s,s);ctx.shadowColor='#18201918';ctx.shadowBlur=30;ctx.shadowOffsetY=12;ctx.fillStyle='#faf8f1';ctx.fillRect(-60,-77,120,154);ctx.shadowColor='transparent';ctx.strokeStyle='#c5bcb0';ctx.strokeRect(-60,-77,120,154);ctx.fillStyle='#b45234';ctx.fillRect(-72,-45,45,43);ctx.fillStyle='#fff5ec';ctx.font='bold 15px sans-serif';ctx.fillText('PPT',-66,-18);ctx.fillStyle='#d3c7b7';ctx.fillRect(-13,-31,52,5);for(let k=0;k<3;k++)ctx.fillRect(-35,20+k*13,Math.max(0,Math.min(1,marks*3-k))*(k===1?57:73),4);ctx.restore();}
function background(){for(let i=0;i<130;i++)dot(rand(i+950)*1920,180+rand(i+1200)*700,.5+rand(i)*1.1,'#b6c6be',.3);}
function reflection(p){
  // Revision appears as moving abstract marks, never fabricated personal quotations.
  for(let i=9;i>=0;i--){const retreat=Math.sin(p*9+i*.5)*8;documentIcon(1350+i*16+retreat,565-i*14,2.25,-.06+i*.012,.13+(9-i)*.025);}
  const phase=p*3,index=Math.floor(phase),f=phase-index;
  documentIcon(1290,580,2.65,-.025,1,clamp(f*2));
  const words=['과거','근원경쟁력','미래'];
  for(let i=0;i<3;i++){const x=1070+i*205,active=i===Math.min(2,index);label(words[i],x,850,active?'#b45234':'#72786f',active?33:28);dot(x,800,active?5:3,active?'#b45234':'#a7aba2');}
  // A line is reconsidered, erased and redrawn with a different length.
  const revision=Math.sin(p*Math.PI*8)*.5+.5;ctx.fillStyle='#faf8f1';ctx.fillRect(1200,617,190,25);ctx.fillStyle='#b4523480';ctx.fillRect(1200,624,45+revision*125,5);ctx.fillRect(1240+revision*120,610,2,22);
}
function gathering(p){for(let i=0;i<70;i++){const q=ease((p*1.7-i/110)),d=docPos[i],from=[960+(d[0]-1360)*3.4,(d[1]-555)*3.4+540];const pos=point(from,d,q);documentIcon(...pos,.4+rand(i)*.6,(rand(i+77)-.5)*.85,q);}}
function ignite(p){
  const compress=ease(p/.29),release=ease((p-.32)/.59),cx=1330,cy=540;
  if(p<.34)for(let i=0;i<70;i++){const pos=point(docPos[i],[cx,cy],compress);documentIcon(...pos,(.4+rand(i)*.6)*(1-compress*.92),(rand(i+77)-.5)*.85*(1-compress),1-ease((p-.23)/.1));}
  glow(cx,cy,50+release*580,'#9dd8c3',(.17+Math.sin(clamp((p-.2)/.6)*Math.PI)*.35)*ease(p/.15));
  if(p>.28){for(let i=0;i<300;i++){const q=ease((p-.3-rand(i)*.12)/.5),pos=point([cx,cy],sky[i],q);const prev=point([cx,cy],sky[i],Math.max(0,q-.06*(1-q)));line(prev,pos,'#dbebd4',Math.sin(q*Math.PI)*.7,1.5);dot(...pos,1.2+rand(i)*2.7,'#eeeae1',q);}
    ctx.strokeStyle='#d5e6d2';ctx.globalAlpha=(1-release)*.3;ctx.lineWidth=2;ctx.beginPath();ctx.ellipse(cx,cy,30+release*580,20+release*430,-.3,0,Math.PI*2);ctx.stroke();ctx.globalAlpha=1;}
}
function constellation(p){const q=ease(p/.65),positions=people.map((v,i)=>point(sky[i],v,q));
  positions.forEach((pos,i)=>{if(i>2){const other=positions[i-3];if(Math.hypot(pos[0]-other[0],pos[1]-other[1])<105)line(pos,other,'#9dd8c3',clamp((p-.25)*2)*.19);}dot(...pos,1.8+rand(i)*1.8,palette[i%3]);});
  if(p<.8){const y=mix(210,850,ease(p/.8));const grad=ctx.createLinearGradient(950,y-45,950,y+3);grad.addColorStop(0,'transparent');grad.addColorStop(1,'#9dd8c31c');ctx.fillStyle=grad;ctx.fillRect(950,y-45,870,48);line([950,y],[1820,y],'#9dd8c3',.24);}
  label('기록의 의미 → 임베딩 → 유사도',1380,920,'#b9cec0',27,ease((p-.5)*3));
}
const focus=people[16],splitTo=[[605,615],[960,730],[1320,615]];
function extraction(p){const zoom=ease(p/.32),split=ease((p-.4)/.4);
  people.forEach((v,i)=>{if(i===16)return;const x=960+(v[0]-focus[0])*mix(1,7,zoom),y=570+(v[1]-focus[1])*mix(1,7,zoom);dot(x,y,2+zoom*3,palette[i%3],(1-zoom)*.75);});
  const center=point(focus,[960,565],zoom);glow(...center,80+zoom*100,'#9dd8c340',1-split*.6);dot(...center,4+zoom*15,'#eeeae1',1-split);
  label('합성 인물 017',960,850,'#a5b6ac',26,zoom*(1-split));
  const names=['검증 절차 자동화','불량 징후 조기 진단','경험의 지식화'];
  for(let j=0;j<3;j++){const pos=point([960,565],splitTo[j],split),alpha=ease((p-.4)/.13);line([960,565],pos,palette[j],alpha*(1-split)*.5,2);glow(...pos,60,palette[j]+'44',alpha);dot(...pos,9,palette[j],alpha);label(names[j],pos[0],pos[1]+68,palette[j],33,ease((p-.68)/.25));}
}
function expansion(p){const q=ease(p/.68);tasks.forEach((t,i)=>{const own=people[t.person],end=[own[0]+t.offset[0],own[1]+t.offset[1]],origin=splitTo[t.group];const delay=rand(t.person)*.13;const k=ease((p-delay)/.7);const pos=point(origin,end,k);dot(...pos,mix(7,1.6+rand(i)*1.4,k),palette[t.group],t.person===16?1:ease((p-.05)/.4));});label('하나의 사람 → 여러 미래 과제',1350,915,'#a5b6ac',28,q);}
function synthesis(p){const q=ease(p/.78);for(let g=0;g<3;g++){const c=targets[g];for(let k=0;k<9;k++)glow(c[0]+Math.cos(k*2.3)*100,c[1]+Math.sin(k*2.3)*48,135+rand(k)*100,palette[g]+'13',ease((p-.35)/.6));}
  tasks.forEach((t,i)=>{const own=people[t.person],origin=[own[0]+t.offset[0],own[1]+t.offset[1]],k=ease((p-rand(i)*.13)/.72);const pos=point(origin,t.to,k),arc=Math.sin(k*Math.PI);pos[0]+=Math.sin(i*.1)*arc*100;pos[1]-=arc*(90+rand(i)*170);line([pos[0]-arc*15,pos[1]+arc*20],pos,palette[t.group],arc*.27);dot(...pos,1.2+rand(i)*2,palette[t.group]);});
  ['검증 절차의 자동화','불량 징후의 조기 진단','경험을 재사용 가능한 지식으로'].forEach((name,i)=>label(name,targets[i][0],880,palette[i],31,ease((p-.73)/.25)));
}
const draws=[reflection,gathering,ignite,constellation,extraction,expansion,synthesis];
function sceneAt(t){return Math.max(0,starts.findLastIndex(s=>t>=s));}
function save(){try{localStorage.setItem('pitch-cosmos-time',String(time));}catch{}}
function updateCopy(index){scene=index;const s=scenes[index];$('stage').className=[s.dark?'dark':'',s.center?'center':'',s.reflection?'reflection':''].join(' ');$('stage').dataset.screenLabel=`0${index+1} ${s.name}`;$('title').innerHTML=s.title;$('description').textContent=s.description;$('number').textContent=s.number||'';$('quote').textContent='';$('chapter').innerHTML=`0${index+1} <span>/ 07 &nbsp; ${s.name}</span>`;$('scene-note').innerText=s.note;$('draft').textContent=index===0?'모션 스터디 · 작성 과정은 상상한 연출':'합성 시연 · 실제 인물·추출·임베딩 결과 아님';$('prev').disabled=index===0;$('next').disabled=index===6;document.querySelectorAll('[data-go]').forEach(b=>b.setAttribute('aria-current',String(+b.dataset.go===index)));save();}
function render(){const index=sceneAt(time);if(scene!==index)updateCopy(index);const progress=clamp((time-starts[index])/scenes[index].duration);ctx.clearRect(0,0,1920,1080);if(scenes[index].dark)background();draws[index](reduced?.98:progress);$('scrub').value=time/total;$('scrub').setAttribute('aria-valuetext',`${index+1}장면 ${Math.round(progress*100)}%`);}
function play(value){running=value;$('play').textContent=running?'일시정지':'재생';$('play').setAttribute('aria-pressed',String(running));last=performance.now();save();}
function go(index){time=starts[clamp(index,0,6)];play(false);render();}
scenes.forEach((s,i)=>{const b=document.createElement('button');b.textContent=`0${i+1} ${s.name}`;b.dataset.go=i;b.onclick=()=>{go(i);play(!reduced);};$('steps').append(b);});
$('play').onclick=()=>{if(time>=total)time=0;play(!running);};$('prev').onclick=()=>{go(scene-1);play(!reduced);};$('next').onclick=()=>{go(scene+1);play(!reduced);};$('replay').onclick=()=>{go(scene);play(!reduced);};$('scrub').oninput=e=>{play(false);time=Number(e.target.value)*total;render();};
$('calm').checked=reduced;$('calm').onchange=e=>{reduced=e.target.checked;render();};reducedQuery.addEventListener('change',e=>{reduced=e.matches;$('calm').checked=reduced;render();});
$('tweaks-button').onclick=()=>{$('tweaks').hidden=!$('tweaks').hidden;};$('close-tweaks').onclick=()=>{$('tweaks').hidden=true;$('tweaks-button').focus();};
addEventListener('keydown',e=>{if(['INPUT','SELECT','BUTTON'].includes(e.target.tagName))return;if(e.key===' '){e.preventDefault();if(time>=total)time=0;play(!running);}else if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();go(scene+(e.key==='ArrowRight'?1:-1));play(!reduced);}});
document.addEventListener('visibilitychange',()=>{if(document.hidden)play(false);});
function fit(){const v=$('viewport');$('stage').style.position='absolute';$('stage').style.left='50%';$('stage').style.top='50%';$('stage').style.transform=`translate(-50%,-50%) scale(${Math.min(v.clientWidth/1920,v.clientHeight/1080)})`;}
addEventListener('resize',fit);fit();render();
function frame(now){if(running){time=Math.min(total,time+Math.min((now-last)/1000,.1)*Number($('speed').value));render();if(time>=total)play(false);}last=now;requestAnimationFrame(frame);}
requestAnimationFrame(frame);
