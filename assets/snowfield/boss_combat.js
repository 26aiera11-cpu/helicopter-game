/* Issue #9: first-playtest attacks only; existing boss motion/HP stay in the engine. */
(() => {
  'use strict';
  const settings=Object.freeze({firstDelay:1.8,rest:gameRegionDifficulty.get('world-2:snowfield').bossRest,fanSpeed:80,fanSpread:Math.PI/10,
    radialSpeed:65,radialStep:Math.PI/12,radiusRatio:.18,minRadius:56,maxRadius:74,warning:1.4,burst:.25,bulletLife:3.4,bulletRadius:5,maxBullets:9});
  const names=['fan','radial','blast'],epsilon=1e-9;
  let active=null,validateHazard=false;
  const inRegion=()=>typeof stage!=='undefined'&&gameWorlds.region(stage)?.key==='world-2:snowfield'&&phase===5;
  const enabled=actor=>inRegion()&&actor&&actor===boss&&actor.hp>0;
  function reset() {
    if(active)enemyBullets=enemyBullets.filter(b=>!b.snowBossPattern);
    active=null;validateHazard=false;
  }
  function prepare(actor) {
    if(!enabled(actor))return false;
    reset();active={actor,age:0,phase:'rest',remaining:settings.firstDelay,next:0,radialAngle:0,hazard:null};return true;
  }
  function blockedRects() {
    const rects=['rotationJoystick','fire','hud','fullscreenToggle','exitGame','sensor','sensorStatus','worldPrototypeNotice'].flatMap(id=>{
      const e=document.getElementById(id);
      if(!e||e.hidden||!e.getClientRects().length||getComputedStyle(e).visibility==='hidden')return [];
      const r=e.getBoundingClientRect();return r.width&&r.height?[{left:r.left,right:r.right,top:r.top,bottom:r.bottom}]:[];
    });
    rects.push({left:W*.3,right:W*.7,top:31,bottom:66}); // Existing canvas boss name/HP.
    return rects;
  }
  const radiusForHeight=(height=H)=>Math.max(settings.minRadius,Math.min(settings.maxRadius,height*settings.radiusRatio));
  function safeCircle(x,y,r,rects=blockedRects()) {
    const gap=4;
    return x>=r+gap&&x<=W-r-gap&&y>=r+gap&&y<=H-r-gap&&rects.every(b=>{
      const dx=x-Math.max(b.left,Math.min(b.right,x)),dy=y-Math.max(b.top,Math.min(b.bottom,y));
      return dx*dx+dy*dy>(r+gap)**2;
    });
  }
  function safeTarget(x,y,radius=radiusForHeight()) {
    const r=radius+4,rects=blockedRects(),xs=[Math.max(r,Math.min(W-r,x)),r,W-r],ys=[Math.max(r,Math.min(H-r,y)),r,H-r];
    for(const b of rects){xs.push(b.left-r-1,b.right+r+1);ys.push(b.top-r-1,b.bottom+r+1);}
    let best=null,distance=Infinity;
    for(const cx of xs)for(const cy of ys)if(safeCircle(cx,cy,radius,rects)){
      const d=(cx-x)**2+(cy-y)**2;
      if(d<distance){best={x:cx,y:cy};distance=d;}
    }
    return best;
  }
  function fire(state,pattern) {
    const count=pattern==='fan'?3:6;
    if(enemyBullets.filter(b=>b.snowBossPattern&&b.life>0).length+count>settings.maxBullets)return;
    const center=pattern==='fan'?Math.atan2(player.y-state.actor.y,player.x-state.actor.x):state.radialAngle;
    gameSnowfield.attack(state.actor,true);
    for(let i=0;i<count;i++){
      const angle=center+(pattern==='fan'?(i-1)*settings.fanSpread:i*Math.PI/3),speed=pattern==='fan'?settings.fanSpeed:settings.radialSpeed;
      enemyBullets.push({x:state.actor.x,y:state.actor.y,vx:Math.cos(angle)*speed,vy:Math.sin(angle)*speed,
        life:settings.bulletLife,r:settings.bulletRadius,snowBossPattern:pattern});
    }
    if(pattern==='radial')state.radialAngle=(state.radialAngle+settings.radialStep)%(Math.PI*2);
  }
  function beginAttack(state) {
    const pattern=names[state.next];state.next=(state.next+1)%names.length;
    if(pattern==='blast'){
      const target={x:player.x,y:player.y},radius=radiusForHeight(),point=safeTarget(target.x,target.y,radius);
      if(point){state.hazard={...point,target,r:radius};state.phase='warning';state.remaining=settings.warning;return;}
    }else fire(state,pattern);
    state.phase='rest';state.remaining=settings.rest;
  }
  function resolve(state) {
    if(state.phase==='rest'){beginAttack(state);return;}
    if(state.phase==='warning'){
      state.phase='burst';state.remaining=settings.burst;
      gameSnowfield.attack(state.actor,true);
      const h=state.hazard;
      // One existing hurt() call at detonation, never once per burst frame.
      if(h&&Math.hypot(player.x-h.x,player.y-h.y)<=h.r)hurt();
      return;
    }
    state.hazard=null;state.phase='rest';state.remaining=settings.rest;
  }
  function backgroundPaused() {return Boolean(inRegion()&&boss&&document.hidden);}
  function update(actor,dt) {
    if(!enabled(actor)){if(active)reset();return false;}
    if(!started||gameOverPending||window.gameExitDialogOpen||document.hidden)return true;
    if(active?.actor!==actor)prepare(actor);
    const state=active;
    if(validateHazard&&state.hazard&&(!safeCircle(state.hazard.x,state.hazard.y,state.hazard.r)||Math.abs(state.hazard.r-radiusForHeight())>epsilon)){
      state.hazard=null;state.phase='rest';state.remaining=settings.rest;
    }
    validateHazard=false;
    let left=Math.max(0,dt);
    for(let guard=0;guard<64;guard++){
      if(state.remaining<=epsilon){
        if(transition>0)break;
        resolve(state);
        if(!started||active!==state)return true;
      }
      if(left<=epsilon)break;
      const slice=Math.min(left,state.remaining);state.age+=slice;state.remaining-=slice;left-=slice;
    }
    return true;
  }
  function drawBullet(ctx,b) {
    if(!b.snowBossPattern)return false;
    ctx.save();ctx.translate(b.x,b.y);ctx.fillStyle='#55b8f4';ctx.strokeStyle='#174e82';ctx.lineWidth=1.3;
    ctx.beginPath();ctx.arc(0,0,b.r,0,Math.PI*2);ctx.fill();ctx.stroke();
    if(b.snowBossPattern==='radial'){
      ctx.strokeStyle='#e9fbff';ctx.lineWidth=1.2;ctx.beginPath();
      for(let i=0;i<6;i++){const a=i*Math.PI/3;ctx.moveTo(0,0);ctx.lineTo(Math.cos(a)*b.r*.82,Math.sin(a)*b.r*.82);}ctx.stroke();
    }
    ctx.restore();return true;
  }
  function draw(ctx) {
    if(!active||!enabled(active.actor)||!active.hazard)return;
    const h=active.hazard,progress=1-active.remaining/(active.phase==='warning'?settings.warning:settings.burst);
    ctx.save();ctx.translate(h.x,h.y);ctx.lineWidth=3;
    if(active.phase==='warning'){
      ctx.fillStyle='#247bcb55';ctx.strokeStyle='#174e82';ctx.beginPath();ctx.arc(0,0,h.r,0,Math.PI*2);ctx.fill();ctx.stroke();
      ctx.strokeStyle='#68d9ff';ctx.lineWidth=4;ctx.beginPath();ctx.arc(0,0,h.r-5,-Math.PI/2,-Math.PI/2+Math.PI*2*progress);ctx.stroke();
    }else{
      ctx.globalAlpha=1-progress;ctx.fillStyle='#9de8ff';ctx.strokeStyle='#14558c';ctx.beginPath();ctx.arc(0,0,h.r*(.6+.4*progress),0,Math.PI*2);ctx.fill();ctx.stroke();
    }
    ctx.restore();
  }
  window.gameSnowfieldBoss=Object.freeze({settings,prepare,update,reset,draw,drawBullet,backgroundPaused,safeTarget,radiusForHeight,
    snapshot:()=>active?{age:active.age,phase:active.phase,remaining:active.remaining,next:names[active.next],radialAngle:active.radialAngle,
      hazard:active.hazard?{...active.hazard,target:{...active.hazard.target}}:null,
      bullets:enemyBullets.filter(b=>b.snowBossPattern&&b.life>0).length}:null});
  addEventListener('resize',()=>{validateHazard=true;});
  document.addEventListener('fullscreenchange',()=>{validateHazard=true;});
  document.addEventListener('visibilitychange',()=>{validateHazard=true;});
})();
