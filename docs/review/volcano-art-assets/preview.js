'use strict';
// Standalone art viewer. Does not import/execute the game or write storage.
const assetRoot = '../../../assets/volcano/';
const params = new URLSearchParams(location.search);
if (params.get('view') === 'scene') document.body.classList.add('scene-only');
const errors = [];
const loadImage = async url => {
  const im = new Image(); im.src = url; await im.decode(); return im;
};
let manifest, actors, background, helicopters, state = 'move', elapsed = 0, paused = false;
let previous = performance.now();
const stage = document.getElementById('scene');
const select = document.getElementById('state');
const pause = document.getElementById('pause');
const allDrawn = new Set();
const fitImage = (ctx, im, x, y, width) => {
  const height = width * im.height / im.width;
  ctx.drawImage(im, x - width/2, y - height/2, width, height);
};
function checker(ctx, x, y, w, h) {
  ctx.fillStyle = '#dde3e7'; ctx.fillRect(x, y, w, h);
  ctx.fillStyle = '#bbc4cc';
  for (let yy=0; yy<h; yy+=12) for (let xx=0; xx<w; xx+=12) {
    if (((xx/12+yy/12)%2)===0) ctx.fillRect(x+xx, y+yy, Math.min(12,w-xx), Math.min(12,h-yy));
  }
}
function actorFrame(actor, requestedState, time) {
  const animation = actor.data.animations[requestedState];
  const i = Math.floor(time/animation.frame_duration_ms) % animation.frame_count;
  return animation.frames[i];
}
function drawActor(ctx, actor, frame, x, y, visibleWidth) {
  const idle = actor.data.animations.idle.frames[0];
  const scale = visibleWidth / (idle.rect_px[2] - 16);
  const [sx,sy,sw,sh] = frame.rect_px;
  const [dx,dy,dw,dh] = frame.sprite_source_rect_px;
  ctx.drawImage(actor.atlas,sx,sy,sw,sh,x+(dx-160)*scale,y+(dy-160)*scale,dw*scale,dh*scale);
  allDrawn.add(actor.data.id+':'+frame.index);
}
function drawScene() {
  const rect = stage.getBoundingClientRect();
  const w = Math.round(rect.width), h = Math.round(rect.height);
  if (stage.width!==w || stage.height!==h) {stage.width=w;stage.height=h;}
  const ctx = stage.getContext('2d');
  const scale = Math.max(w/background.width,h/background.height);
  ctx.drawImage(background,(w-background.width*scale)/2,(h-background.height*scale)/2,background.width*scale,background.height*scale);
  const positions = [[.20,.29],[.4,.27],[.63,.3],[.81,.28],[.5,.56]];
  actors.forEach((actor,i)=>drawActor(ctx,actor,actorFrame(actor,state,elapsed),positions[i][0]*w,positions[i][1]*h,actor.data.preview_content_width_px));
  // Literal original gameplay PNG data from index.html, not its executable code.
  helicopters.forEach((image,i)=>fitImage(ctx,image,w*[.2,.5,.8][i],h*.84,46));
  // Static contrast swatches only; not combat, collision or balancing logic.
  ['#ffea67','#71dcff','#a4ff95'].forEach((color,i)=>{
    ctx.fillStyle=color;ctx.strokeStyle='#162029';ctx.lineWidth=1;
    for(let j=0;j<3;j++) {ctx.beginPath();ctx.ellipse(w*[.2,.5,.8][i],h*.73-j*12,i===2?9:3,3,0,0,Math.PI*2);ctx.fill();ctx.stroke();}
  });
}
function drawCards() {
  actors.forEach(actor=>{
    const ctx=actor.canvas.getContext('2d');ctx.clearRect(0,0,320,320);
    const frame=actorFrame(actor,state,elapsed);
    const [x,y,w,h]=frame.rect_px,[dx,dy,dw,dh]=frame.sprite_source_rect_px;
    ctx.drawImage(actor.atlas,x,y,w,h,dx,dy,dw,dh);allDrawn.add(actor.data.id+':'+frame.index);
  });
}
function drawContact() {
  const canvas=document.getElementById('contact'),ctx=canvas.getContext('2d');
  canvas.width=1152;canvas.height=840;
  ctx.fillStyle='#17212b';ctx.fillRect(0,0,canvas.width,canvas.height);
  actors.forEach((actor,row)=>{
    const y=row*168;ctx.fillStyle='#fff';ctx.font='bold 15px sans-serif';ctx.fillText(actor.data.name_ko,y?10:10,y+19);
    let offset=0;
    for(const [name,animation] of Object.entries(actor.data.animations)) {
      animation.frames.forEach((frame,j)=>{
        const x=10+offset*53;checker(ctx,x,y+30,48,104);
        const [sx,sy,sw,sh]=frame.rect_px,[dx,dy,dw,dh]=frame.sprite_source_rect_px;
        const k=Math.min(48/320,104/320);
        ctx.drawImage(actor.atlas,sx,sy,sw,sh,x+24+(dx-160)*k,y+82+(dy-160)*k,dw*k,dh*k);
        ctx.fillStyle='#dce4ed';ctx.font='9px sans-serif';ctx.fillText(name+' '+(j+1),x,y+148);offset++;
        allDrawn.add(actor.data.id+':'+frame.index);
      });
    }
  });
}
function redraw() {drawCards();drawScene();}
function tick(now) {
  if(!paused) elapsed += Math.min(now-previous,100);
  previous=now;redraw();requestAnimationFrame(tick);
}
window.volcanoPreview = {
  ready: (async()=>{
    manifest=await (await fetch(assetRoot+'asset_manifest.json')).json();
    background=await loadImage(assetRoot+manifest.background.path);
    actors=await Promise.all(manifest.monsters.map(async data=>({data,atlas:await loadImage(assetRoot+data.atlas),base:await loadImage(assetRoot+data.base)})));
    const original=await (await fetch('../../../index.html')).text();
    const literal=original.match(/const gameplayHeliImages=(\[[^\n]*?\]);/);
    if(!literal) throw new Error('Original gameplay image literals not found');
    helicopters=await Promise.all(JSON.parse(literal[1]).map(loadImage));
    actors.forEach(actor=>{
      const figure=document.createElement('figure');figure.className='card';
      const canvas=document.createElement('canvas');canvas.width=canvas.height=320;actor.canvas=canvas;
      const caption=document.createElement('figcaption');caption.textContent=actor.data.name_ko;
      const detail=document.createElement('small');detail.textContent=actor.data.frame_count+'프레임 · PNG alpha';
      figure.append(canvas,caption,detail);document.getElementById('cards').append(figure);
    });
    select.onchange=()=>{state=select.value;elapsed=0;redraw();};
    pause.onclick=()=>{paused=!paused;pause.textContent=paused?'재생':'일시 정지';};
    drawContact();redraw();document.getElementById('status').textContent='배경·5종·69프레임 로드 완료 / 게임 미적용';
    requestAnimationFrame(tick);return true;
  })().catch(error=>{errors.push(String(error));document.getElementById('status').textContent=String(error);throw error;}),
  setFrame(requestedState,time=0){state=requestedState;select.value=state;elapsed=time;paused=true;redraw();},
  report(){return {state,elapsed,paused,loadedActors:actors.length,decodedFrames:allDrawn.size,errors,scenePixels:[stage.width,stage.height],integratedIntoGame:false};},
  auditFrames(){
    const canvas=document.createElement('canvas');canvas.width=canvas.height=320;
    const ctx=canvas.getContext('2d'),result=[];
    for(const actor of actors) for(const [name,animation] of Object.entries(actor.data.animations)) for(const frame of animation.frames){
      ctx.clearRect(0,0,320,320);
      const [x,y,w,h]=frame.rect_px,[dx,dy,dw,dh]=frame.sprite_source_rect_px;
      ctx.drawImage(actor.atlas,x,y,w,h,dx,dy,dw,dh);
      const pixels=ctx.getImageData(0,0,320,320).data;let visible=0,edge=0;
      for(let i=3;i<pixels.length;i+=4)if(pixels[i]>=8){visible++;const p=(i-3)/4;if(p<320||p>=320*319||p%320===0||p%320===319)edge++;}
      result.push({id:actor.data.id,state:name,index:frame.index,visiblePixels:visible,edgePixels:edge});
    }
    return result;
  }
};
