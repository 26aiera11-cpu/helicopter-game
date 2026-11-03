/* Approved snowfield art only. No combat, score, RNG or input configuration. */
(() => {
  'use strict';
  const manifest=JSON.parse(document.getElementById('snowfieldManifest').content.textContent);
  const backgroundImage=document.getElementById('snowfieldBackground');
  const species=manifest.monsters.map(spec=>Object.freeze({
    ...spec,baseImage:document.getElementById(`snowfield-${spec.id}-base`),
    atlasImage:document.getElementById(`snowfield-${spec.id}-atlas`)
  }));
  const byId=new Map(species.map(spec=>[spec.id,spec]));
  const normalIds=['snow_slime','penguin_raider','ice_yeti','frost_turtle'];
  const bossId='blizzard_king';
  const enabled=()=>typeof stage!=='undefined'&&gameWorlds.region(stage)?.key==='world-2:snowfield';
  let clock=0,states=new WeakMap(),observed=new Set(),defeated=new WeakSet(),ghosts=[];
  let pendingFinale=false,finale=false;
  const loaded=img=>Boolean(img?.complete&&img.naturalWidth>0);
  const length=(spec,state)=>spec.animations[state].frame_count*spec.animations[state].frame_duration_ms/1000;
  const ghostLength=ghost=>length(byId.get(ghost.id),'hit')+length(byId.get(ghost.id),'defeat');
  function track(actor,isBoss=false) {
    let state=states.get(actor);
    if(!state){
      const id=isBoss?bossId:normalIds.includes(actor.snowSpeciesId)?actor.snowSpeciesId:normalIds[Math.max(0,Math.min(3,phase-1))];
      state={id,actor,x:actor.x,y:actor.y,base:'idle',baseAt:clock,attackUntil:0,hitUntil:0};
      states.set(actor,state);observed.add(state);
    }
    return state;
  }
  function tick(dt) {
    if(!enabled()||document.hidden||window.gameExitDialogOpen)return;
    clock+=dt;ghosts=ghosts.filter(ghost=>clock-ghost.at<ghostLength(ghost));
  }
  function observe(actors,king) {
    if(!enabled())return;
    const alive=new Set([...actors,...(king?[king]:[])]);
    for(const actor of alive){
      const s=track(actor,actor===king);
      const base=Math.hypot(actor.x-s.x,actor.y-s.y)>.0001?'move':'idle';
      if(base!==s.base){s.base=base;s.baseAt=clock;}
      s.x=actor.x;s.y=actor.y;
    }
    for(const s of observed)if(!alive.has(s.actor))observed.delete(s);
  }
  function attack(actor,isBoss=false) {
    if(!enabled()||!actor||defeated.has(actor))return;
    const s=track(actor,isBoss);s.attackUntil=clock+length(byId.get(s.id),'attack');
  }
  function hit(actor,isBoss=false) {
    if(!enabled()||!actor||defeated.has(actor))return;
    const s=track(actor,isBoss);s.hitUntil=clock+length(byId.get(s.id),'hit');
    if(actor.hp<=0){
      defeated.add(actor);ghosts.push({id:s.id,x:actor.x,y:actor.y,at:clock});
      if(isBoss)pendingFinale=true;
    }
  }
  function pose(actor,isBoss=false) {
    const s=track(actor,isBoss),spec=byId.get(s.id);
    const name=clock<s.hitUntil?'hit':clock<s.attackUntil?'attack':s.base;
    const at=name==='hit'?s.hitUntil-length(spec,name):name==='attack'?s.attackUntil-length(spec,name):s.baseAt;
    return frame(spec,name,clock-at);
  }
  function frame(spec,name,elapsed) {
    const anim=spec.animations[name],step=Math.floor((Math.max(0,elapsed)+1e-9)*1000/anim.frame_duration_ms);
    const index=anim.loop?step%anim.frame_count:Math.min(step,anim.frame_count-1);
    return {id:spec.id,name,index,rect:[...anim.frames[index].rect_px]};
  }
  function geometry(spec,x,y,width,height) {
    const w=spec.suggested_render_width_px,h=w*spec.cell[1]/spec.cell[0];
    // Offset the visual cell only at the viewport edge; never move the collider.
    const cx=Math.max(w/2,Math.min(width-w/2,x)),cy=Math.max(h/2,Math.min(height-h/2,y));
    return {x:cx-w/2,y:cy-h/2,w,h};
  }
  function paint(ctx,spec,point,selected) {
    const box=geometry(spec,point.x,point.y,W,H);
    if(loaded(spec.atlasImage)){
      ctx.drawImage(spec.atlasImage,...selected.rect,box.x,box.y,box.w,box.h);return true;
    }
    if(loaded(spec.baseImage)){
      const w=box.w,h=w*spec.baseImage.naturalHeight/spec.baseImage.naturalWidth;
      ctx.drawImage(spec.baseImage,box.x,box.y+(box.h-h)/2,w,h);return true;
    }
    return false;
  }
  function drawActor(ctx,actor,isBoss=false) {
    if(!enabled())return false;
    const selected=pose(actor,isBoss);paint(ctx,byId.get(selected.id),actor,selected);return true;
  }
  function drawDefeats(ctx) {
    if(!enabled())return;
    for(const ghost of ghosts)paint(ctx,byId.get(ghost.id),ghost,ghostPose(ghost));
  }
  function ghostPose(ghost) {
    const spec=byId.get(ghost.id),elapsed=clock-ghost.at,hitLength=length(spec,'hit');
    return elapsed<hitLength?frame(spec,'hit',elapsed):frame(spec,'defeat',elapsed-hitLength);
  }
  function backgroundGeometry(width,height) {
    const scale=Math.max(width/backgroundImage.naturalWidth,height/backgroundImage.naturalHeight);
    const w=backgroundImage.naturalWidth*scale,h=backgroundImage.naturalHeight*scale;
    return {x:(width-w)/2,y:(height-h)/2,w,h,scale};
  }
  function drawBackground(ctx,width,height) {
    if(!enabled())return false;
    if(loaded(backgroundImage)){const b=backgroundGeometry(width,height);ctx.drawImage(backgroundImage,b.x,b.y,b.w,b.h);}
    // A single cover draw is static: no seamless processing, repetition or zoom.
    return true;
  }
  function tickFinale(dt) {
    if(pendingFinale&&!started&&!gameOverPending){
      pendingFinale=false;finale=true;document.body.classList.add('snowfield-finale');return;
    }
    if(!finale)return;
    if(started||gameOverPending){reset();return;}
    tick(dt);
    if(!ghosts.length)reset();
  }
  function reset() {
    clock=0;states=new WeakMap();observed=new Set();defeated=new WeakSet();ghosts=[];
    pendingFinale=finale=false;document.body.classList.remove('snowfield-finale');
  }
  new MutationObserver(()=>{
    if(!started&&!gameOverPending&&!pendingFinale&&!finale)reset();
  }).observe(document.getElementById('menu'),{attributes:true,attributeFilter:['class']});
  window.gameSnowfield=Object.freeze({manifest,species,backgroundImage,normalIds,bossId,
    tick,observe,attack,hit,pose,frame,geometry,drawActor,drawDefeats,drawBackground,backgroundGeometry,tickFinale,reset,
    ready:()=>loaded(backgroundImage)&&species.every(spec=>loaded(spec.atlasImage)&&loaded(spec.baseImage)),
    snapshot:()=>({clock,actors:[...observed].map(s=>({id:s.id,x:s.x,y:s.y,pose:pose(s.actor,s.id===bossId)})),
      ghosts:ghosts.map(g=>({...g,pose:ghostPose(g)})),finale:{active:finale,pending:pendingFinale}})
  });
})();
