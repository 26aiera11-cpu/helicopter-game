/* Issue19: volcano dragon only; approved frame pixels/HP/rewards stay unchanged. */
(()=>{
  'use strict';
  const mouthAnchors=Object.freeze({"idle":[[109.0,168],[111.0,169],[109.5,168],[111.0,167]],"move":[[113.0,160],[114.0,161],[117.5,170],[116.0,174],[115.0,172],[114.5,176]],"attack":[[114.5,168],[115.0,169],[116.0,169],[114.0,173]],"hit":[[114.0,152],[113.0,157],[113.0,163]],"defeat":[[109.5,165],[110.0,164],[110.0,163],[106.0,165]]});
  Object.values(mouthAnchors).forEach(rows=>{rows.forEach(Object.freeze);Object.freeze(rows);});
  const settings=Object.freeze({firstDelay:1.8,rest:2.8,fireAim:.4,fireWaves:3,fireGap:.32,fireSpread:Math.PI/15,
    fireSpeed:88,bulletRadius:5.5,bulletLife:3.2,maxBullets:18,eruptionRatio:.16,eruptionMin:48,eruptionMax:64,
    eruptionLead:.18,eruptionWarning:1.25,eruptionBurst:.25,breathWarning:1,breathDuration:3.8,
    breathRatio:.26,breathMin:85,breathMax:115,breathHalfAngle:Math.PI/10,fade:.18,positionSpeed:45,positionLimit:3,step:1/120});
  const patterns=['fireball','eruption','rotating_breath'],tau=Math.PI*2,epsilon=1e-9;
  const spec=gameVolcano.species.find(s=>s.id==='magma_dragon');
  const scale=gameVolcano.renderWidths.magma_dragon/(spec.animations.idle.frames[0].rect_px[2]-2*gameVolcano.manifest.frame_format.trim_padding_px);
  const bodyRadius=Math.max(...Object.values(spec.animations).flatMap(a=>a.frames.flatMap(f=>{
    const [x,y,w,h]=f.sprite_source_rect_px;return [Math.hypot(x-160,y-160),Math.hypot(x+w-160,y-160),Math.hypot(x-160,y+h-160),Math.hypot(x+w-160,y+h-160)];
  })))*scale;
  let active=null,death=null,frozen=null,layoutChanged=false;
  const inRegion=()=>typeof stage!=='undefined'&&gameWorlds.region(stage)?.key==='world-2:volcano'&&phase===5;
  const enabled=actor=>Boolean(inRegion()&&actor&&actor===boss&&actor.hp>0);
  const loaded=im=>im?.complete&&im.naturalWidth>0;
  function reset(){enemyBullets=enemyBullets.filter(b=>!b.volcanoBossPattern);active=null;death=null;frozen=null;layoutChanged=false;}
  function freeze(){
    const saved=active?.center?{actor:active.actor,angle:active.angle,center:{...active.center}}:null;
    reset();frozen=saved;
  }
  function prepare(actor){
    if(!enabled(actor))return false;
    reset();active={actor,age:0,phase:'rest',remaining:settings.firstDelay,next:0,pattern:null,
      angle:0,swept:0,center:null,hazard:null,fade:0,waves:0,volleys:0,shots:0,damageCalls:0,skipped:0,rects:blockedRects()};return true;
  }
  function blockedRects(){
    const canvasBox=canvas.getBoundingClientRect(),sx=canvasBox.width?W/canvasBox.width:1,sy=canvasBox.height?H/canvasBox.height:1;
    const rects=['rotationJoystick','fire','hud','fullscreenToggle','exitGame','sensor','sensorStatus','worldPrototypeNotice'].flatMap(id=>{
      const el=document.getElementById(id);if(!el||el.hidden||!el.getClientRects().length||getComputedStyle(el).visibility==='hidden')return [];
      const b=el.getBoundingClientRect();return b.width&&b.height?[{left:(b.left-canvasBox.left)*sx,right:(b.right-canvasBox.left)*sx,top:(b.top-canvasBox.top)*sy,bottom:(b.bottom-canvasBox.top)*sy}]:[];
    });
    rects.push({left:W*.3,right:W*.7,top:31,bottom:66});return rects;
  }
  function safeCircle(x,y,r,rects=blockedRects()){
    const gap=4;return x>=r+gap&&x<=W-r-gap&&y>=r+gap&&y<=H-r-gap&&rects.every(b=>{
      const dx=x-Math.max(b.left,Math.min(b.right,x)),dy=y-Math.max(b.top,Math.min(b.bottom,y));return dx*dx+dy*dy>(r+gap)**2;
    });
  }
  function safeTarget(x,y,r,rects=blockedRects()){
    const margin=r+4,xs=[Math.max(margin,Math.min(W-margin,x)),margin,W-margin],ys=[Math.max(margin,Math.min(H-margin,y)),margin,H-margin];
    for(const b of rects){xs.push(b.left-margin-1,b.right+margin+1);ys.push(b.top-margin-1,b.bottom+margin+1);}
    let best=null,distance=Infinity;
    for(const cx of xs)for(const cy of ys)if(safeCircle(cx,cy,r,rects)){const d=(cx-x)**2+(cy-y)**2;if(d<distance){best={x:cx,y:cy};distance=d;}}
    return best;
  }
  const eruptionRadius=(height=H)=>Math.max(settings.eruptionMin,Math.min(settings.eruptionMax,height*settings.eruptionRatio));
  const breathLength=(height=H)=>Math.max(settings.breathMin,Math.min(settings.breathMax,height*settings.breathRatio));
  function frameGeometry(actor,selected=gameVolcano.pose(actor,true),angle=active?.actor===actor?active.angle:0,center=null){
    const box=gameVolcano.geometry(spec,actor.x,actor.y,W,H,selected),pivot=center||active?.actor===actor&&active.center||{x:box.cx,y:box.cy};
    let local;
    if(loaded(spec.atlasImage)){
      const anchor=mouthAnchors[selected.name][selected.index];local={x:(selected.source[0]+anchor[0]-selected.cell[0]/2)*scale,y:(selected.source[1]+anchor[1]-selected.cell[1]/2)*scale};
    }else if(loaded(spec.baseImage)){
      const [x,y,right,bottom]=spec.base_content_bounds_px,ratio=132/(right-x);local={x:0,y:((bottom-y)/2-3)*ratio};
    }else local={x:0,y:36};
    const cos=Math.cos(angle),sin=Math.sin(angle),origin={x:pivot.x+local.x*cos-local.y*sin,y:pivot.y+local.x*sin+local.y*cos};
    const length=breathLength(),direction=Math.PI/2+angle,ux=Math.cos(direction),uy=Math.sin(direction),halfWidth=length*Math.tan(settings.breathHalfAngle);
    return {pivot:{x:pivot.x,y:pivot.y},local,origin,angle,direction,length,halfWidth,body:box,
      polygon:[origin,{x:origin.x+ux*length-uy*halfWidth,y:origin.y+uy*length+ux*halfWidth},{x:origin.x+ux*length+uy*halfWidth,y:origin.y+uy*length-ux*halfWidth}]};
  }
  const outsideUI=(x,y,rects)=>x>=0&&x<=W&&y>=0&&y<=H&&rects.every(b=>x<b.left||x>b.right||y<b.top||y>b.bottom);
  function contains(point,geometry,rects=active?.rects||blockedRects()){
    if(!outsideUI(point.x,point.y,rects))return false;
    const x=point.x-geometry.origin.x,y=point.y-geometry.origin.y,cos=Math.cos(geometry.direction),sin=Math.sin(geometry.direction);
    const along=x*cos+y*sin,across=-x*sin+y*cos;
    return along>=-epsilon&&along<=geometry.length+epsilon&&Math.abs(across)<=along*Math.tan(settings.breathHalfAngle)+epsilon;
  }
  function rest(state){state.phase='rest';state.remaining=settings.rest;state.hazard=null;state.pattern=null;}
  function startBreath(state){
    if(!safeCircle(state.actor.x,state.actor.y,bodyRadius+2,state.rects)){state.phase='position';state.remaining=settings.positionLimit;return;}
    state.center={x:state.actor.x,y:state.actor.y};state.phase='breath_warning';state.remaining=settings.breathWarning;state.angle=0;state.swept=0;
  }
  function begin(state){
    state.pattern=patterns[state.next];state.next=(state.next+1)%patterns.length;
    if(state.pattern==='fireball'){
      const mouth=frameGeometry(state.actor).origin;state.aim=Math.atan2(player.y-mouth.y,player.x-mouth.x);state.waves=0;state.phase='fire_aim';state.remaining=settings.fireAim;
    }else if(state.pattern==='eruption'){
      const r=eruptionRadius(),target={x:player.x+(player.vx||0)*settings.eruptionLead,y:player.y+(player.vy||0)*settings.eruptionLead},point=safeTarget(target.x,target.y,r,state.rects);
      if(!point){state.skipped++;rest(state);return;}
      state.hazard={...point,r,target,resolved:false};state.phase='eruption_warning';state.remaining=settings.eruptionWarning;
    }else startBreath(state);
  }
  function fire(state){
    if(enemyBullets.filter(b=>b.volcanoBossPattern&&b.life>0).length+3<=settings.maxBullets){
      const mouth=frameGeometry(state.actor).origin;
      for(let i=-1;i<=1;i++){
        emitEnemyShot(state.actor);const b=enemyBullets[enemyBullets.length-1],a=state.aim+i*settings.fireSpread;
        Object.assign(b,{x:mouth.x,y:mouth.y,vx:Math.cos(a)*settings.fireSpeed,vy:Math.sin(a)*settings.fireSpeed,life:settings.bulletLife,r:settings.bulletRadius,volcanoBossPattern:'fireball'});state.shots++;
      }
      state.volleys++;
    }
    state.waves++;if(state.waves<settings.fireWaves){state.phase='fire_burst';state.remaining=settings.fireGap;}else rest(state);
  }
  function resolve(state,damage){
    if(state.phase==='rest'){state.fade=0;state.center=null;state.angle=0;begin(state);}
    else if(state.phase==='fire_aim'||state.phase==='fire_burst')fire(state);
    else if(state.phase==='eruption_warning'){
      state.phase='eruption_burst';state.remaining=settings.eruptionBurst;state.hazard.resolved=true;gameVolcano.attack(state.actor,true);
      if(Math.hypot(player.x-state.hazard.x,player.y-state.hazard.y)<=state.hazard.r)damage();
    }else if(state.phase==='eruption_burst')rest(state);
    else if(state.phase==='position'){state.skipped++;state.center=null;rest(state);}
    else if(state.phase==='breath_warning'){state.phase='breath';state.remaining=settings.breathDuration;state.attackElapsed=0;gameVolcano.attack(state.actor,true);}
    else if(state.phase==='breath'){state.angle=tau;state.swept=tau;state.fade=settings.fade;rest(state);}
  }
  function move(state,dt){
    const actor=state.actor;actor.t+=dt;actor.shot=Math.max(0,actor.shot-dt);
    if(state.phase==='breath_warning'||state.phase==='breath'||state.fade>0)return;
    if(state.phase==='position'||state.phase==='rest'&&state.next===2){
      const target=safeTarget(W*.5,H*.53,bodyRadius+2,state.rects);
      if(!target)return;
      const dx=target.x-actor.x,dy=target.y-actor.y,d=Math.hypot(dx,dy),distance=Math.min(d,settings.positionSpeed*dt);
      if(d>epsilon){actor.x+=dx/d*distance;actor.y+=dy/d*distance;}
      return;
    }
    // Preserve the forest-profile radial/orbit formula outside breath positioning.
    const dx=player.x-actor.x,dy=player.y-actor.y,d=Math.hypot(dx,dy)||1,radial=(d-Math.min(W*.35,160))*.9;
    actor.x=Math.max(72,Math.min(W-72,actor.x+(dx/d*radial-dy/d*45*.48)*dt));
    actor.y=Math.max(85,Math.min(H-80,actor.y+(dy/d*radial+dx/d*45*.48)*dt));
  }
  function backgroundPaused(){return Boolean(inRegion()&&boss&&document.hidden);}
  function update(actor,dt){
    if(inRegion()&&actor&&actor===boss&&actor.hp<=0){if(active)reset();return true;}
    if(!enabled(actor)){if(active)reset();return false;}
    if(!started||gameOverPending||window.gameExitDialogOpen||document.hidden)return true;
    if(active?.actor!==actor)prepare(actor);
    const state=active;state.rects=blockedRects();let spent=false;
    const damage=()=>{if(!spent&&invuln<=0){spent=true;state.damageCalls++;hurt();}};
    if(layoutChanged||state.hazard&&!safeCircle(state.hazard.x,state.hazard.y,state.hazard.r,state.rects)||state.center&&!safeCircle(state.center.x,state.center.y,bodyRadius+2,state.rects)){
      if(state.hazard&&(!safeCircle(state.hazard.x,state.hazard.y,state.hazard.r,state.rects)||Math.abs(state.hazard.r-eruptionRadius())>epsilon)||state.center&&!safeCircle(state.center.x,state.center.y,bodyRadius+2,state.rects)){
        state.center=null;state.angle=0;state.fade=0;rest(state);state.skipped++;
      }
      layoutChanged=false;
    }
    let left=Math.max(0,dt);
    for(let guard=0;guard<512;guard++){
      if(state.phase==='position'&&safeCircle(actor.x,actor.y,bodyRadius+2,state.rects))startBreath(state);
      if(state.remaining<=epsilon){if(transition>0)break;resolve(state,damage);if(!started||active!==state)return true;}
      if(left<=epsilon)break;
      const slice=Math.min(left,state.remaining,settings.step);move(state,slice);state.age+=slice;state.remaining-=slice;left-=slice;
      if(state.phase==='breath'){
        state.angle=tau*Math.min(1,Math.max(0,1-state.remaining/settings.breathDuration));state.swept=state.angle;
        if(contains(player,frameGeometry(actor),state.rects))damage();
        if(!started||active!==state)return true;
        state.attackElapsed+=slice;
        const attackDuration=spec.animations.attack.frame_count*spec.animations.attack.frame_duration_ms/1000;
        if(state.attackElapsed>=attackDuration-epsilon){state.attackElapsed%=attackDuration;gameVolcano.attack(actor,true);}
      }
      if(state.fade>0){state.fade=Math.max(0,state.fade-slice);if(state.fade<=epsilon){state.fade=0;state.center=null;state.angle=0;}}
    }
    return true;
  }
  function defeated(actor){
    if(active?.actor!==actor)return;
    death={angle:active.angle,center:active.center?{...active.center}:null};enemyBullets=enemyBullets.filter(b=>!b.volcanoBossPattern);active=null;
  }
  function transform(ctx,point,selected,angle,center,paint){
    const box=gameVolcano.geometry(spec,point.x,point.y,W,H,selected),pivot=center||{x:box.cx,y:box.cy};
    ctx.save();ctx.translate(pivot.x,pivot.y);ctx.rotate(angle);ctx.translate(-box.cx,-box.cy);paint();ctx.restore();
  }
  function drawActor(ctx,actor){
    const state=active?.actor===actor?active:frozen?.actor===actor?frozen:null;
    if(!enabled(actor)||!state?.center)return false;
    transform(ctx,actor,gameVolcano.pose(actor,true),state.angle,state.center,()=>gameVolcano.drawActor(ctx,actor,true));return true;
  }
  function drawDefeat(ctx,ghost,selected,paint){
    if(!inRegion()||ghost.id!=='magma_dragon'||!death?.center)return false;
    transform(ctx,ghost,selected,death.angle,death.center,()=>paint(ctx,spec,ghost,selected));return true;
  }
  function clipUI(ctx,rects){
    ctx.beginPath();ctx.rect(0,0,W,H);ctx.clip();
    // Intersect each subtraction so overlapping UI boxes never cancel a cutout.
    for(const b of rects){ctx.beginPath();ctx.rect(0,0,W,H);ctx.rect(b.left,b.top,b.right-b.left,b.bottom-b.top);ctx.clip('evenodd');}
  }
  function triangle(ctx,geometry,ratio=1,widthRatio=1){
    const [o,a,b]=geometry.polygon,m={x:(a.x+b.x)/2,y:(a.y+b.y)/2},side={x:(a.x-b.x)/2,y:(a.y-b.y)/2};
    ctx.beginPath();ctx.moveTo(o.x,o.y);ctx.lineTo(o.x+(m.x-o.x)*ratio+side.x*ratio*widthRatio,o.y+(m.y-o.y)*ratio+side.y*ratio*widthRatio);ctx.lineTo(o.x+(m.x-o.x)*ratio-side.x*ratio*widthRatio,o.y+(m.y-o.y)*ratio-side.y*ratio*widthRatio);ctx.closePath();
  }
  function draw(ctx){
    if(!active||!enabled(active.actor))return;
    const state=active;ctx.save();clipUI(ctx,state.rects);
    if(state.hazard){
      const h=state.hazard;ctx.beginPath();ctx.arc(h.x,h.y,h.r,0,tau);
      if(state.phase==='eruption_warning'){
        ctx.fillStyle='#ff802f38';ctx.fill();ctx.strokeStyle='#ffce75';ctx.lineWidth=3;ctx.stroke();
        ctx.beginPath();ctx.arc(h.x,h.y,h.r-5,-Math.PI/2,-Math.PI/2+tau*(1-state.remaining/settings.eruptionWarning));ctx.strokeStyle='#ff5f35';ctx.stroke();
      }else{
        ctx.fillStyle='#ff742ecc';ctx.fill();ctx.strokeStyle='#ffe69a';ctx.lineWidth=2;ctx.stroke();ctx.beginPath();ctx.arc(h.x,h.y,h.r*.55,0,tau);ctx.fillStyle='#ffe28ecc';ctx.fill();
      }
    }
    if(state.phase==='breath_warning'||state.phase==='breath'||state.fade>0){
      const geo=frameGeometry(state.actor),o=geo.origin;
      if(state.phase==='breath_warning'){
        triangle(ctx,geo);ctx.fillStyle='#ff8b3428';ctx.fill();ctx.setLineDash([5,5]);ctx.strokeStyle='#ffd58a';ctx.lineWidth=2;ctx.stroke();ctx.setLineDash([]);
        ctx.beginPath();ctx.arc(geo.pivot.x,geo.pivot.y,bodyRadius*.85,Math.PI/2,Math.PI*1.2);ctx.strokeStyle='#ffbf6b';ctx.stroke();
        const a=Math.PI*1.2,r=bodyRadius*.85,x=geo.pivot.x+Math.cos(a)*r,y=geo.pivot.y+Math.sin(a)*r;
        ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+12,y+2);ctx.lineTo(x+4,y+10);ctx.closePath();ctx.fillStyle='#ffd58a';ctx.fill();
        ctx.beginPath();ctx.arc(o.x,o.y,6+3*(1-state.remaining/settings.breathWarning),0,tau);ctx.fillStyle='#ff5b36bb';ctx.fill();
      }else if(state.phase==='breath'){
        const end={x:(geo.polygon[1].x+geo.polygon[2].x)/2,y:(geo.polygon[1].y+geo.polygon[2].y)/2},gradient=ctx.createLinearGradient(o.x,o.y,end.x,end.y);
        gradient.addColorStop(0,'#fff2b3');gradient.addColorStop(.18,'#ffd06a');gradient.addColorStop(.6,'#ff9a39');gradient.addColorStop(1,'#e8481ddd');triangle(ctx,geo);ctx.fillStyle=gradient;ctx.fill();
        triangle(ctx,geo,.9,.42);ctx.fillStyle='#fff2a8bb';ctx.fill();
        // Moving tongues stay clipped inside the exact damaging outer cone.
        ctx.save();triangle(ctx,geo);ctx.clip();const ux=Math.cos(geo.direction),uy=Math.sin(geo.direction);
        for(let j=-2;j<=2;j++){
          ctx.beginPath();ctx.moveTo(o.x,o.y);
          for(let k=1;k<=8;k++){const t=k/8,side=geo.halfWidth*t*(j*.25+Math.sin(state.age*22-k*1.3+j)*.12);ctx.lineTo(o.x+ux*geo.length*t-uy*side,o.y+uy*geo.length*t+ux*side);}
          ctx.strokeStyle=j%2?'#ffdb78aa':'#ffeebbaa';ctx.lineWidth=1.5;ctx.stroke();
        }
        ctx.restore();
      }else{triangle(ctx,geo);ctx.globalAlpha=state.fade/settings.fade*.2;ctx.fillStyle='#dcb5a0';ctx.fill();}
    }
    if(state.phase==='fire_aim'){
      const o=frameGeometry(state.actor).origin;ctx.beginPath();ctx.arc(o.x,o.y,7,0,tau);ctx.fillStyle='#ffac55bb';ctx.fill();
    }
    ctx.restore();
  }
  function drawBullet(ctx,b){
    if(!b.volcanoBossPattern)return false;
    ctx.save();ctx.beginPath();ctx.arc(b.x,b.y,b.r,0,tau);ctx.fillStyle='#ff8f32';ctx.fill();ctx.strokeStyle='#ffe5a2';ctx.lineWidth=1.4;ctx.stroke();ctx.beginPath();ctx.arc(b.x,b.y,b.r*.45,0,tau);ctx.fillStyle='#fff5bc';ctx.fill();ctx.restore();return true;
  }
  const invalidate=()=>{layoutChanged=true;};addEventListener('resize',invalidate);document.addEventListener('fullscreenchange',invalidate);document.addEventListener('visibilitychange',invalidate);
  new MutationObserver(()=>{if(!started&&!gameOverPending&&!gameVolcano.snapshot().advancing)reset();}).observe(document.getElementById('menu'),{attributes:true,attributeFilter:['class']});
  window.gameVolcanoBoss=Object.freeze({settings,mouthAnchors,bodyRadius,enabled,prepare,reset,freeze,update,defeated,draw,drawActor,drawDefeat,drawBullet,backgroundPaused,
    blockedRects,safeCircle,safeTarget,eruptionRadius,breathLength,frameGeometry,contains,
    snapshot:()=>active?{age:active.age,phase:active.phase,remaining:active.remaining,pattern:active.pattern,next:patterns[active.next],angle:active.angle,swept:active.swept,
      center:active.center?{...active.center}:null,hazard:active.hazard?{...active.hazard,target:{...active.hazard.target}}:null,fade:active.fade,
      shots:active.shots,volleys:active.volleys,damageCalls:active.damageCalls,skipped:active.skipped,bullets:enemyBullets.filter(b=>b.volcanoBossPattern&&b.life>0).length}:null,
    deathSnapshot:()=>death?{angle:death.angle,center:death.center?{...death.center}:null}:null});
})();
