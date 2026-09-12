'use strict';
/* Motion study only. All documents, people, task groupings and positions are synthetic. */
const $ = id => document.getElementById(id);
const canvas = $('space');
const ctx = canvas.getContext('2d', {alpha:false});
const W = 1920, H = 1080;
const BLACK = '#030506';
const WHITE = '#f2f0e9';
const COLORS = ['#b4dccb','#dfb185','#c8cedf'];
const scenes = [
  {name:'고민의 흔적', title:'나의 근원경쟁력은 무엇인가.', unit:'기록하기 전의 생각', duration:11,
    description:'검은 화면 중앙의 세 기록이 겹쳤다가 펼쳐진다. 과거·경쟁력·미래를 오가며 추상적인 수정 흔적이 나타난다.',
    say:'과거에 무엇을 해왔는지. 지금 나에게 남은 경쟁력이 무엇인지. 앞으로 어떤 일을 하고 싶은지. 한 장을 작성하기까지의 생각에서 시작합니다.',
    caution:'실제 작성 과정의 재현이 아니라 상상한 연출입니다. 글·감정·노력을 특정 인물의 사실로 주장하지 않습니다.'},
  {name:'300개의 기록', title:'각자의 다음이 모였습니다.', unit:'PPT 기록', duration:8,
    description:'수십 개의 PPT 문서가 주변에서 중앙으로 들어와 300이라는 숫자 주위에 모인다.',
    say:'이렇게 서로 다른 사람들이 남긴 기록을 한곳에 모았습니다. 발표 시연에서는 300개의 기록을 가정합니다.',
    caution:'300은 시연 설정입니다. 실제 자료 수나 실제 고유 인원 수를 확인한 값이 아닙니다.'},
  {name:'별의 탄생', title:'파일 뒤에는 사람이 있습니다.', unit:'별 하나 = 사람 하나', duration:10,
    description:'문서가 중앙의 작은 빛으로 압축된다. 짧은 정적 뒤 빛이 퍼지며 300개의 별이 화면 전체를 채운다.',
    say:'파일 목록에서 한 발 더 들어가 봤습니다. 기록 하나하나를, 그 기록을 남긴 사람의 자리로 펼쳐봅니다.',
    caution:'문서에서 사람으로 바뀌는 시각적 은유입니다. 실제 적용 시 작성자 ID와 문서의 대응을 확인해야 합니다.'},
  {name:'닮은 경험', title:'닮은 경험을 찾아봤습니다.', method:'임베딩 · 유사도', unit:'사람의 지도', duration:9,
    description:'넓게 흩어진 사람의 별이 세 개의 느슨한 이웃으로 이동하고 일부 연결선이 나타난다.',
    say:'기록의 의미를 임베딩해 서로 닮은 경험을 살펴봤습니다. 여기까지는 사람을 중심으로 보는 지도입니다.',
    caution:'이 시안은 실제 임베딩을 계산하지 않습니다. 좌표·연결선·거리는 합성 연출이며 사람의 가치나 능력 점수가 아닙니다.'},
  {name:'한 사람의 다음', title:'그 사람이 바라보는 다음은?', unit:'한 사람의 기록', duration:7,
    description:'하나의 별을 선택해 확대한다. 주변의 별들이 화면 밖으로 밀려나고 한 사람의 빛과 기록만 남는다.',
    say:'그런데 한 사람이 앞으로 하고 싶은 일은 하나일까요? 한 사람의 기록으로 가까이 들어가 보겠습니다.',
    caution:'합성 인물 한 명을 선택한 연출입니다. 개인정보나 실제 원문은 포함하지 않습니다.'},
  {name:'미래 과제 추출', title:'한 사람에게도, 여러 미래가.', method:'LLM 추출', unit:'별 하나 = 미래 과제 하나', duration:10,
    description:'큰 별 하나가 세 개의 과제로 분열한다. 검증 절차 자동화, 불량 조기 진단, 경험의 지식화라는 합성 과제가 각각 나타난다.',
    say:'LLM으로 그 사람이 기록한 미래 과제를 분리해 읽습니다. 이제 별 하나가 뜻하는 것이 사람에서 과제로 바뀝니다.',
    caution:'모든 사람이 세 과제를 갖는다는 뜻이 아닙니다. 실제 추출은 원문 근거를 검증하고, 과제가 없거나 모호한 경우도 보존해야 합니다.'},
  {name:'과제의 지도', title:'사람의 지도에서, 과제의 지도로.', unit:'미래 과제들의 지도', duration:9,
    description:'카메라가 멀어지며 다른 사람들의 자리에서도 과제 별들이 연쇄적으로 갈라진다.',
    say:'같은 관점을 전체 기록으로 넓혀봅니다. 한 사람 안의 서로 다른 과제도, 서로 다른 사람이 적은 닮은 과제도 볼 수 있습니다.',
    caution:'300명 × 세 과제는 이 모션 스터디의 합성 구성입니다. 움직임은 실제 계산 궤적이 아닙니다.'},
  {name:'미래 과제군 합성', title:'각자의 다음이, 함께 빛납니다.', method:'LLM 합성', unit:'미래 과제군', duration:13,
    description:'과제 별이 긴 곡선을 따라 세 개의 불규칙한 성운으로 모인다. 그 주변에 가스 같은 빛이 서서히 피어난다.',
    say:'닮은 미래 과제를 함께 읽어 과제군으로 묶습니다. 각자의 다음에서, 함께 이야기할 수 있는 미래의 모습이 드러납니다.',
    caution:'합성 예시 한 PJT 안의 세 과제군입니다. 실제 적용은 PJT별 독립 분류와 사람 검토가 필요합니다. 크기·빛·거리는 중요도, 준비 수준, 실행 순서가 아닙니다.'}
];
const clamp = (v,a=0,b=1) => Math.min(b,Math.max(a,v));
const ease = value => {const t=clamp(value);return t*t*t*(t*(t*6-15)+10);};
const lerp = (a,b,t) => a+(b-a)*t;
const mix = (a,b,t) => [lerp(a[0],b[0],t),lerp(a[1],b[1],t)];
const rand = i => {const n=Math.sin(i*127.1+84.3)*43758.5453;return n-Math.floor(n);};
const focusIndex = 17;
const core = [960,615];
const burstPoints = Array.from({length:300},(_,i)=>{
  const a=i*2.399963,r=Math.sqrt(rand(i+71));
  return [960+Math.cos(a)*r*880,590+Math.sin(a)*r*380];
});
const neighborCenters = [[545,540],[1270,490],[1050,815]];
const personPoints = Array.from({length:300},(_,i)=>{
  if(i===focusIndex)return [1010,635];
  const a=i*2.399963,r=Math.sqrt(rand(i+391)),c=neighborCenters[i%3];
  return [c[0]+Math.cos(a)*r*290,c[1]+Math.sin(a)*r*170];
});
const selected = personPoints[focusIndex];
const splitPoints = [[565,625],[960,775],[1355,625]];
const cloudCenters = [[465,640],[970,610],[1460,650]];
const taskNames = ['검증 절차 자동화','불량 조기 진단','경험의 지식화'];
const cloudNames = ['검증 절차의 자동화','불량 징후의 조기 진단','경험을 재사용 가능한 지식으로'];
const taskPoints = Array.from({length:900},(_,i)=>{
  const person=Math.floor(i/3),group=i%3,a=i*2.399963,r=Math.sqrt(rand(i+700));
  const c=cloudCenters[group],arm=Math.sin(a*3+r*8)*40;
  return {person,group,offset:[Math.cos(i*2.1)*24,Math.sin(i*2.1)*24],
    target:[c[0]+Math.cos(a)*(r*275+arm),c[1]+Math.sin(a)*(r*140+arm*.3)]};
});
const docs = Array.from({length:66},(_,i)=>{const a=i*2.399963,r=180+Math.sqrt(i/66)*380;return [960+Math.cos(a)*r*1.12,610+Math.sin(a)*r*.65];});
const bgStars = Array.from({length:180},(_,i)=>[rand(i+1000)*W,rand(i+2100)*H,.35+rand(i)*1.2]);

// Reusable pre-rendered light sprites keep hundreds of stars inexpensive to draw.
function lightSprite(color){const c=document.createElement('canvas');c.width=c.height=128;const g=c.getContext('2d');const gradient=g.createRadialGradient(64,64,0,64,64,64);gradient.addColorStop(0,color);gradient.addColorStop(.08,color+'c0');gradient.addColorStop(.32,color+'26');gradient.addColorStop(1,color+'00');g.fillStyle=gradient;g.fillRect(0,0,128,128);return c;}
const sprites = [WHITE,...COLORS].map(lightSprite);
function hazeSprite(color,index){const c=document.createElement('canvas');c.width=600;c.height=360;const g=c.getContext('2d');g.globalCompositeOperation='screen';for(let i=0;i<115;i++){const a=i*2.3999,r=Math.sqrt(rand(i+index*60))*160,x=300+Math.cos(a)*r*1.5,y=180+Math.sin(a)*r*.66;const radius=18+rand(i+4)*65;const gradient=g.createRadialGradient(x,y,0,x,y,radius);gradient.addColorStop(0,color+'15');gradient.addColorStop(1,color+'00');g.fillStyle=gradient;g.fillRect(x-radius,y-radius,radius*2,radius*2);}return c;}
const clouds=COLORS.map(hazeSprite);
function glow(x,y,r,alpha=1,color=0){if(alpha<=0)return;ctx.save();ctx.globalAlpha=clamp(alpha);ctx.globalCompositeOperation='screen';ctx.drawImage(sprites[color],x-r,y-r,r*2,r*2);ctx.restore();}
function dot(x,y,r=2,color=WHITE,alpha=1){if(alpha<=0||x<-100||x>W+100||y<-100||y>H+100)return;ctx.save();ctx.globalAlpha*=clamp(alpha);ctx.fillStyle=color;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill();ctx.restore();}
function line(a,b,color=WHITE,alpha=.2,width=1){if(alpha<=0)return;ctx.save();ctx.globalAlpha=clamp(alpha);ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke();ctx.restore();}
function ring(x,y,r,alpha,color=WHITE,flatten=1){ctx.save();ctx.strokeStyle=color;ctx.globalAlpha=clamp(alpha);ctx.lineWidth=1.4;ctx.beginPath();ctx.ellipse(x,y,r,r*flatten,0,0,Math.PI*2);ctx.stroke();ctx.restore();}
function sheet(x,y,scale,angle,alpha=1,revision=1){ctx.save();ctx.globalAlpha=clamp(alpha);ctx.translate(x,y);ctx.rotate(angle);ctx.scale(scale,scale);ctx.fillStyle='#12191c';ctx.strokeStyle='#52615b';ctx.lineWidth=1;ctx.beginPath();ctx.roundRect(-72,-95,144,190,3);ctx.fill();ctx.stroke();ctx.fillStyle='#bd8868';ctx.fillRect(-83,-63,50,36);ctx.font='bold 16px "Apple SD Gothic Neo",sans-serif';ctx.fillStyle='#080d0b';ctx.fillText('PPT',-75,-39);ctx.fillStyle='#8e9d934d';ctx.fillRect(-16,-50,63,5);for(let j=0;j<4;j++){ctx.fillStyle=j===2?'#b4dccb70':'#8e9d9340';ctx.fillRect(-43,-6+j*22,(j===2?lerp(15,84,revision):[83,57,84,70][j]),4);}ctx.restore();}
let labels=[];
function setLabels(items){$('scene-labels').replaceChildren();labels=items.map(item=>{const el=document.createElement('div');el.className='visual-label'+(item.small?' small':'');el.textContent=item.text;el.style.left=item.x+'px';el.style.top=item.y+'px';el.style.color=item.color||WHITE;el.style.opacity='0';$('scene-labels').append(el);return el;});}
function showLabel(i,alpha){if(labels[i])labels[i].style.opacity=String(clamp(alpha));}
function backdrop(alpha=1){ctx.save();ctx.globalAlpha=clamp(alpha);bgStars.forEach(([x,y,r],i)=>dot(x,y,r,'#b8c8be',.16+rand(i)*.18));ctx.restore();}
function reflection(p){
  const arrivals=[ease(p/.26),ease((p-.17)/.28),ease((p-.36)/.3)];
  const final=[650,960,1270];
  for(let i=0;i<3;i++){
    const a=arrivals[i],x=lerp(960,final[i],a),rotation=lerp((i-1)*.18,(i-1)*.035,a);
    for(let j=3;j>0;j--)sheet(x+j*7,590-j*9,1.28,rotation,.05+Math.sin(p*7+j)*.02);
    const revision=p>.22&&p<.83?.5+.5*Math.sin(p*29+i*2):1;
    sheet(x,595,1.4,rotation,a,revision);
    showLabel(i,ease((p-.2-i*.17)/.2));
  }
  // The eye revisits earlier experience rather than racing linearly through a timeline.
  if(p>.3&&p<.88){const x=960+Math.sin(p*10)*305;glow(x,608,140,.1,1);}
}
function collection(p){
  docs.forEach((target,i)=>{const q=ease((p-rand(i)*.3)/.62),a=i*2.3999;const origin=[960+Math.cos(a)*1600,600+Math.sin(a)*1050];const pos=mix(origin,target,q);sheet(...pos,.28+rand(i+2)*.42,(rand(i+6)-.5)*.7,q*.87);});
  showLabel(0,ease((p-.35)/.4));
}
function ignition(p){
  const compress=ease(p/.28),expand=ease((p-.36)/.61);
  if(p<.34)docs.forEach((v,i)=>{const pos=mix(v,core,compress);sheet(...pos,(.28+rand(i+2)*.42)*(1-compress*.94),(rand(i+6)-.5)*.7*(1-compress),1-ease((p-.2)/.13));});
  const breath=ease((p-.25)/.1)*(1-ease((p-.38)/.22));
  glow(...core,lerp(50,540,expand),.75*breath+.32*(1-expand));
  if(p>.3){dot(...core,lerp(5,0,ease((p-.4)/.35)),WHITE,(1-expand)*.9);ring(...core,20+expand*1100,(1-expand)*.26,WHITE,.66);}
  burstPoints.forEach((target,i)=>{const q=ease((p-.37-rand(i)*.08)/.53);if(q<=0)return;const pos=mix(core,target,q),tail=mix(core,target,Math.max(0,q-(1-q)*.06));line(tail,pos,WHITE,Math.sin(q*Math.PI)*.65,1.4);dot(...pos,1.3+rand(i)*2.3,WHITE,q);if(i%7===0)glow(...pos,18,.27*q);});
  backdrop(expand*.65);
  $('heading').style.opacity=String(1-ease((p-.12)/.13)+ease((p-.84)/.16));
}
function neighbors(p){
  const q=ease(p/.72),positions=personPoints.map((v,i)=>mix(burstPoints[i],v,q));backdrop(.65);
  positions.forEach((v,i)=>{
    if(i>=3){const b=positions[i-3];if(Math.hypot(v[0]-b[0],v[1]-b[1])<145)line(v,b,COLORS[i%3],.18*ease((p-.37)/.4));}
    dot(...v,1.4+rand(i)*2.2,WHITE);if(i%15===0)glow(...v,23,.18);
  });
  if(p<.65){const y=lerp(350,980,ease(p/.65));line([220,y],[1700,y],COLORS[0],Math.sin(clamp(p/.65)*Math.PI)*.18);}
  const select=ease((p-.75)/.25);glow(...selected,80,select*.65);ring(...selected,22,select*.45);showLabel(0,select);
}
function closeup(p){
  const q=ease(p/.79),scale=lerp(1,8,q),cx=lerp(selected[0],960,q),cy=lerp(selected[1],625,q);
  backdrop(1-q);
  personPoints.forEach((v,i)=>{const pos=[cx+(v[0]-selected[0])*scale,cy+(v[1]-selected[1])*scale];if(i===focusIndex){glow(...pos,lerp(35,190,q),.55);dot(...pos,lerp(3,18,q));}else{dot(...pos,lerp(2,4,q),WHITE,1-q*.98);}});
  // The selected record is an abstract mark, not a fabricated source quote.
  const a=ease((p-.5)/.4);for(let i=0;i<5;i++)line([860,765+i*14],[860+[200,150,180,125,165][i],765+i*14],WHITE,a*.12);
  showLabel(0,a);
}
function extraction(p){
  const q=ease((p-.22)/.63),center=[960,625];
  const tension=Math.sin(clamp(p/.3)*Math.PI);
  glow(...center,190-tension*80,(1-q)*.55);
  dot(...center,18*(1-q)+.01,WHITE,1-q);
  if(p>.2)ring(...center,25+q*410,(1-q)*.22,WHITE,.7);
  splitPoints.forEach((target,i)=>{const s=ease((p-.24-i*.025)/.57),pos=mix(center,target,s);pos[1]-=Math.sin(s*Math.PI)*70;line(center,pos,COLORS[i],Math.sin(s*Math.PI)*.3,1.5);glow(...pos,90,s*.55,i+1);dot(...pos,lerp(5,8,s),COLORS[i],ease((p-.24)/.16));showLabel(i,ease((p-.68)/.24));});
}
function spread(p){
  const zoom=ease(p/.71),scale=lerp(8,1,zoom),cx=lerp(960,selected[0],zoom),cy=lerp(625,selected[1],zoom);
  backdrop(zoom*.65);
  taskPoints.forEach((t,i)=>{const own=personPoints[t.person],base=[cx+(own[0]-selected[0])*scale,cy+(own[1]-selected[1])*scale];const split=ease((p-.24-rand(t.person)*.28)/.42);const end=[base[0]+t.offset[0]*split,base[1]+t.offset[1]*split];let pos=end;
    if(t.person===focusIndex)pos=mix(splitPoints[t.group],end,zoom);
    const alpha=t.person===focusIndex?1:ease((p-.1)/.55);
    dot(...pos,lerp(3,1.65+rand(i)*1.25,zoom),COLORS[t.group],alpha);
    if(t.person===focusIndex)glow(...pos,lerp(90,24,zoom),.45,t.group+1);
  });
}
function synthesize(p){
  const q=ease((p-.08)/.75),bloom=ease((p-.48)/.5);backdrop(.65+q*.35);
  // Haze is subordinate to the actual moving points, appearing only as they gather.
  ctx.save();ctx.globalCompositeOperation='screen';ctx.globalAlpha=bloom*.7;
  clouds.forEach((image,i)=>{const c=cloudCenters[i];ctx.drawImage(image,c[0]-385,c[1]-230,770,460);});ctx.restore();
  taskPoints.forEach((t,i)=>{const own=personPoints[t.person],origin=[own[0]+t.offset[0],own[1]+t.offset[1]],k=ease((p-.06-rand(i)*.12)/.7),pos=mix(origin,t.target,k),arc=Math.sin(k*Math.PI);pos[0]+=Math.sin(i*.16)*arc*140;pos[1]-=arc*(90+rand(i)*170);const tail=[pos[0]-arc*18,pos[1]+arc*22];line(tail,pos,COLORS[t.group],arc*.27);dot(...pos,1.3+rand(i)*1.7,COLORS[t.group]);if(i%17===0)glow(...pos,30,bloom*.32,t.group+1);});
  cloudCenters.forEach((c,i)=>{glow(...c,155,bloom*.3,i+1);showLabel(i,ease((p-.77)/.22));});
}
const draws=[reflection,collection,ignition,neighbors,closeup,extraction,spread,synthesize];
const motionPreference=matchMedia('(prefers-reduced-motion: reduce)');
let reduced=motionPreference.matches,index=0,elapsed=0,running=!reduced,last=0,hideTimer;
try{const remembered=JSON.parse(localStorage.getItem('cosmos-v2-position')||'null');if(remembered&&Number.isInteger(remembered.index)&&remembered.index>=0&&remembered.index<scenes.length){index=remembered.index;elapsed=clamp(Number(remembered.elapsed)||0,0,scenes[index].duration);running=false;}}catch{}
function save(){try{localStorage.setItem('cosmos-v2-position',JSON.stringify({index,elapsed}));}catch{}}
function setupLabels(){
  const entries=[
    ['과거','경쟁력','미래'].map((text,i)=>({text,x:650+i*310,y:790})),
    [{text:'300',x:960,y:595}],
    [],
    [{text:'한 사람의 기록',x:selected[0],y:selected[1]+50,small:true}],
    [{text:'한 사람의 기록',x:960,y:875,small:true}],
    taskNames.map((text,i)=>({text,x:splitPoints[i][0],y:splitPoints[i][1]+83,color:COLORS[i]})),
    [],
    cloudNames.map((text,i)=>({text,x:cloudCenters[i][0],y:875,color:COLORS[i]}))
  ];setLabels(entries[index]);if(index===1){labels[0].replaceChildren();const n=document.createElement('b');n.textContent='300';const unit=document.createElement('em');unit.textContent='개의 기록';labels[0].append(n,unit);}
}
function syncPlayback(){const b=$('play');b.textContent=running?'Ⅱ':'▷';b.setAttribute('aria-label',running?'현재 장면 일시정지':'현재 장면 재생');b.setAttribute('aria-pressed',String(running));}
function updateScene(){
  const s=scenes[index];$('title').textContent=s.title;$('method').textContent=s.method||'';$('unit').textContent=s.unit;$('counter').textContent=`${String(index+1).padStart(2,'0')} / 08`;$('scene-picker').value=String(index);$('stage').dataset.screenLabel=`${index+1} ${s.name}`;$('visual-description').textContent=s.description;$('note-title').textContent=s.name;$('note-body').textContent=s.say;$('note-caution').textContent=s.caution;$('previous').disabled=index===0;$('next').disabled=index===scenes.length-1;$('heading').style.opacity='1';$('status').textContent=`${index+1}장면. ${s.title}`;setupLabels();syncPlayback();render();save();
}
function render(){
  ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';ctx.fillStyle=BLACK;ctx.fillRect(0,0,W,H);
  const p=reduced?1:clamp(elapsed/scenes[index].duration);draws[index](p);$('progress').value=String(clamp(elapsed/scenes[index].duration));$('progress').setAttribute('aria-valuetext',`${Math.round(p*100)}%`);
}
function awake(){document.body.classList.remove('quiet');clearTimeout(hideTimer);hideTimer=setTimeout(()=>{if($('notes').hidden&&$('settings').hidden&&!$('controls').querySelector(':focus-visible'))document.body.classList.add('quiet');},2600);}
function go(next){index=clamp(next,0,scenes.length-1);elapsed=reduced?scenes[index].duration:0;running=!reduced;last=performance.now();updateScene();awake();}
function togglePlay(){if(reduced)return;if(elapsed>=scenes[index].duration)elapsed=0;running=!running;last=performance.now();syncPlayback();render();save();awake();}
function panel(id,visible){$(id).hidden=!visible;$(id==='notes'?'notes-toggle':'settings-toggle').setAttribute('aria-expanded',String(visible));awake();}
function fullscreen(){const request=document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen?.();Promise.resolve(request).catch(()=>{$('status').textContent='이 브라우저에서는 전체 화면을 사용할 수 없습니다.';});}
scenes.forEach((s,i)=>{const option=document.createElement('option');option.value=String(i);option.textContent=`${i+1}. ${s.name}`;$('scene-picker').append(option);});
$('scene-picker').onchange=e=>go(Number(e.target.value));$('previous').onclick=()=>go(index-1);$('next').onclick=()=>go(index+1);$('replay').onclick=()=>go(index);$('play').onclick=togglePlay;
$('progress').oninput=e=>{running=false;elapsed=Number(e.target.value)*scenes[index].duration;syncPlayback();render();save();awake();};
$('notes-toggle').onclick=()=>panel('notes',$('notes').hidden);$('close-notes').onclick=()=>{panel('notes',false);$('notes-toggle').focus();};
$('settings-toggle').onclick=()=>panel('settings',$('settings').hidden);$('close-settings').onclick=()=>{panel('settings',false);$('settings-toggle').focus();};$('fullscreen').onclick=fullscreen;
function setReduced(value){reduced=value;$('reduced').checked=value;if(reduced){running=false;elapsed=scenes[index].duration;}syncPlayback();render();save();}
$('reduced').checked=reduced;$('reduced').onchange=e=>setReduced(e.target.checked);motionPreference.addEventListener('change',e=>setReduced(e.matches));
addEventListener('keydown',e=>{
  if(e.key==='Escape'){panel('notes',false);panel('settings',false);return;}
  if(['INPUT','SELECT','TEXTAREA'].includes(e.target.tagName))return;
  if(e.target.tagName==='BUTTON'&&(e.key===' '||e.key==='Enter'))return;
  if(e.key==='ArrowRight'||e.key===' '){e.preventDefault();if(index<scenes.length-1)go(index+1);}
  else if(e.key==='ArrowLeft'){e.preventDefault();if(index>0)go(index-1);}
  else if(e.key.toLowerCase()==='r')go(index);
  else if(e.key.toLowerCase()==='p')togglePlay();
  else if(e.key.toLowerCase()==='n')panel('notes',$('notes').hidden);
  else if(e.key.toLowerCase()==='f')fullscreen();
});
addEventListener('pointermove',awake);addEventListener('pointerdown',awake);addEventListener('focusin',awake);
document.addEventListener('visibilitychange',()=>{if(document.hidden){running=false;syncPlayback();save();}});
function fit(){const box=$('viewport');const scale=Math.min(box.clientWidth/W,box.clientHeight/H);$('stage').style.transform=`translate(-50%,-50%) scale(${scale})`;}
addEventListener('resize',fit);fit();updateScene();awake();
function frame(now){
  if(running){const dt=last?Math.min((now-last)/1000,.08):0;elapsed=Math.min(scenes[index].duration,elapsed+dt*Number($('speed').value));render();if(elapsed>=scenes[index].duration){running=false;syncPlayback();save();}}
  last=now;requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
