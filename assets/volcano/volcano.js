/* Volcano art adapter. Forest combat/music are temporary and remain in the engine. */
(() => {
  'use strict';
  const manifest=JSON.parse(document.getElementById('volcanoManifest').content.textContent);
  const backgroundImage=document.getElementById('volcanoBackground');
  const normalIds=['ember_bean','lava_lizard','volcano_bat','magma_beetle'],bossId='magma_dragon';
  // Visible idle silhouette widths, calibrated in game; not the review manifest widths.
  const renderWidths=Object.freeze({ember_bean:38,lava_lizard:42,volcano_bat:54,magma_beetle:58,magma_dragon:132});
  const species=manifest.monsters.map(data=>Object.freeze({...data,
    baseImage:document.getElementById(`volcano-${data.id}-base`),
    atlasImage:document.getElementById(`volcano-${data.id}-atlas`)
  }));
  const byId=new Map(species.map(spec=>[spec.id,spec]));
  const enabled=()=>typeof stage!=='undefined'&&gameWorlds.region(stage)?.key==='world-2:volcano';
  const loaded=img=>Boolean(img?.complete&&img.naturalWidth>0);
  const duration=(spec,name)=>spec.animations[name].frame_count*spec.animations[name].frame_duration_ms/1000;
  let clock=0,states=new WeakMap(),observed=new Set(),defeated=new WeakSet(),ghosts=[],advance=null;
  const frameCache=new Map();
  function prepare(actor) {
    if(enabled())actor.volcanoSpeciesId=normalIds[Math.max(0,Math.min(3,phase-1))];
    return actor;
  }
  function track(actor,isBoss=false) {
    let state=states.get(actor);
    if(!state){
      const id=isBoss?bossId:normalIds.includes(actor.volcanoSpeciesId)?actor.volcanoSpeciesId:normalIds[Math.max(0,Math.min(3,phase-1))];
      state={id,actor,x:actor.x,y:actor.y,base:'idle',baseAt:clock,attackAt:-Infinity,hitAt:-Infinity};
      states.set(actor,state);observed.add(state);
    }
    return state;
  }
  function tick(dt) {
    if(!enabled()||document.hidden||window.gameExitDialogOpen)return;
    clock+=dt;
    ghosts=ghosts.filter(g=>clock-g.at<duration(byId.get(g.id),'hit')+duration(byId.get(g.id),'defeat'));
  }
  function observe(actors,king) {
    if(!enabled())return;
    const alive=new Set([...actors,...(king?[king]:[])]);
    for(const actor of alive){
      const s=track(actor,actor===king),base=Math.hypot(actor.x-s.x,actor.y-s.y)>.0001?'move':'idle';
      if(s.base!==base){s.base=base;s.baseAt=clock;}
      s.x=actor.x;s.y=actor.y;
    }
    for(const s of observed)if(!alive.has(s.actor))observed.delete(s);
  }
  function attack(actor,isBoss=false) {
    if(enabled()&&actor&&!defeated.has(actor))track(actor,isBoss).attackAt=clock;
  }
  function hit(actor,isBoss=false) {
    if(!enabled()||!actor||defeated.has(actor))return;
    const s=track(actor,isBoss);s.hitAt=clock;
    if(actor.hp<=0){defeated.add(actor);ghosts.push({id:s.id,x:actor.x,y:actor.y,at:clock});}
  }
  function frame(spec,name,elapsed) {
    const animation=spec.animations[name],step=Math.floor((Math.max(0,elapsed)+1e-9)*1000/animation.frame_duration_ms);
    const index=animation.loop?step%animation.frame_count:Math.min(step,animation.frame_count-1);
    const selected=animation.frames[index];
    return {id:spec.id,name,index,rect:[...selected.rect_px],source:[...selected.sprite_source_rect_px],cell:[...selected.source_size_px]};
  }
  function pose(actor,isBoss=false) {
    const s=track(actor,isBoss),spec=byId.get(s.id);
    const name=clock-s.hitAt<duration(spec,'hit')?'hit':clock-s.attackAt<duration(spec,'attack')?'attack':s.base;
    return frame(spec,name,clock-(name==='hit'?s.hitAt:name==='attack'?s.attackAt:s.baseAt));
  }
  function ghostPose(g) {
    const spec=byId.get(g.id),elapsed=clock-g.at,hitDuration=duration(spec,'hit');
    return elapsed<hitDuration?frame(spec,'hit',elapsed):frame(spec,'defeat',elapsed-hitDuration);
  }
  function scaleFor(spec) {
    return renderWidths[spec.id]/(spec.animations.idle.frames[0].rect_px[2]-2*manifest.frame_format.trim_padding_px);
  }
  function geometry(spec,x,y,width,height,selected) {
    const scale=scaleFor(spec),[cellW,cellH]=selected.cell;
    let left=0,top=0,right=0,bottom=0;
    for(const animation of Object.values(spec.animations))for(const f of animation.frames){
      const [dx,dy,w,h]=f.sprite_source_rect_px;
      left=Math.min(left,dx-cellW/2);top=Math.min(top,dy-cellH/2);
      right=Math.max(right,dx+w-cellW/2);bottom=Math.max(bottom,dy+h-cellH/2);
    }
    // Move only the picture at the edge. Actor coordinates/radius remain untouched.
    const cx=Math.max(-left*scale,Math.min(width-right*scale,x));
    const cy=Math.max(-top*scale,Math.min(height-bottom*scale,y));
    const [dx,dy,w,h]=selected.source;
    return {x:cx+(dx-cellW/2)*scale,y:cy+(dy-cellH/2)*scale,w:w*scale,h:h*scale,cx,cy,scale,
      bounds:{x:cx+left*scale,y:cy+top*scale,w:(right-left)*scale,h:(bottom-top)*scale}};
  }
  function cachedFrame(spec,selected) {
    const key=spec.id+':'+selected.name+':'+selected.index;
    if(frameCache.has(key))return frameCache.get(key);
    if(!loaded(spec.atlasImage))return null;
    const [x,y,w,h]=selected.rect,canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    ctx.drawImage(spec.atlasImage,x,y,w,h,0,0,w,h);
    try{
      // Sampling cleanup in bounded, ephemeral frame canvases; source PNG stays exact.
      const image=ctx.getImageData(0,0,w,h),pixels=image.data;
      for(let i=3;i<pixels.length;i+=4)if(pixels[i]<8)pixels.fill(0,i-3,i+1);
      ctx.putImageData(image,0,0);
    }catch(ignore){ /* Canvas-taint restrictions never stop the game. */ }
    frameCache.set(key,canvas);return canvas;
  }
  function paint(ctx,spec,point,selected) {
    const box=geometry(spec,point.x,point.y,W,H,selected),image=cachedFrame(spec,selected);
    if(image){ctx.drawImage(image,box.x,box.y,box.w,box.h);return;}
    if(loaded(spec.baseImage)){
      const [x,y,right,bottom]=spec.base_content_bounds_px,w=right-x,h=bottom-y;
      const width=renderWidths[spec.id],height=width*h/w;
      const cx=Math.max(width/2,Math.min(W-width/2,point.x)),cy=Math.max(height/2,Math.min(H-height/2,point.y));
      ctx.drawImage(spec.baseImage,x,y,w,h,cx-width/2,cy-height/2,width,height);return;
    }
    ctx.fillStyle=spec.id==='volcano_bat'?'#9240b8':'#e88426';
    ctx.beginPath();ctx.arc(box.cx,box.cy,Math.min(renderWidths[spec.id]/2,36),0,Math.PI*2);ctx.fill();
  }
  function drawActor(ctx,actor,isBoss=false) {
    if(!enabled())return false;
    const selected=pose(actor,isBoss);paint(ctx,byId.get(selected.id),actor,selected);return true;
  }
  function drawDefeats(ctx) {if(enabled())for(const g of ghosts)paint(ctx,byId.get(g.id),g,ghostPose(g));}
  function backgroundGeometry(width,height) {
    const scale=Math.max(width/backgroundImage.naturalWidth,height/backgroundImage.naturalHeight);
    const w=backgroundImage.naturalWidth*scale,h=backgroundImage.naturalHeight*scale;
    return {x:(width-w)/2,y:(height-h)/2,w,h,scale};
  }
  function drawBackground(ctx,width,height) {
    if(!enabled())return false;
    ctx.fillStyle='#422728';ctx.fillRect(0,0,width,height);
    if(loaded(backgroundImage)){const b=backgroundGeometry(width,height);ctx.drawImage(backgroundImage,b.x,b.y,b.w,b.h);}
    return true; // No forest/tiled image even while a volcano resource is unavailable.
  }
  function deferAdvance(callback) {
    const snowContinuation=gameWorlds.region(stage)?.key==='world-2:snowfield'&&gameWorlds.nextRegion(stage)!==null;
    if(!enabled()&&!snowContinuation)return false;
    const art=snowContinuation?gameSnowfield:window.gameVolcano;
    if(!art.snapshot().ghosts.length)return false;
    advance={callback,art};return true;
  }
  function tickAdvance(dt) {
    if(!advance)return false;
    if(document.hidden||window.gameExitDialogOpen)return true;
    const current=advance;current.art.tick(dt);
    if(!current.art.snapshot().ghosts.length){advance=null;current.art.reset();current.callback();}
    return true;
  }
  function cancelAdvance() {
    if(advance?.art===window.gameSnowfield)gameSnowfield.reset();
    advance=null;
  }
  function reset() {
    cancelAdvance();clock=0;states=new WeakMap();observed=new Set();defeated=new WeakSet();ghosts=[];
  }
  new MutationObserver(()=>{
    if(!started&&!gameOverPending&&!advance)reset();
  }).observe(document.getElementById('menu'),{attributes:true,attributeFilter:['class']});
  window.gameVolcano=Object.freeze({manifest,species,normalIds,bossId,backgroundImage,renderWidths,enabled,prepare,
    tick,observe,attack,hit,pose,frame,geometry,drawActor,drawDefeats,backgroundGeometry,drawBackground,
    deferAdvance,tickAdvance,cancelAdvance,reset,
    ready:()=>loaded(backgroundImage)&&species.every(spec=>loaded(spec.baseImage)&&loaded(spec.atlasImage)),
    snapshot:()=>({clock,actors:[...observed].map(s=>({id:s.id,x:s.x,y:s.y,pose:pose(s.actor,s.id===bossId)})),
      ghosts:ghosts.map(g=>({...g,pose:ghostPose(g)})),advancing:Boolean(advance),cachedFrames:frameCache.size,
      cachedPixels:[...frameCache.values()].reduce((total,c)=>total+c.width*c.height,0)})
  });
})();
