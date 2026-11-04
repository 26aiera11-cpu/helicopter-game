/* Issue18 first-playtest values. Only world-2:volcano normal actors opt in.
 * Keep the approved art adapter, forest/snow combat and dragon engine unchanged.
 */
(() => {
  'use strict';
  const profiles=Object.freeze([
    {id:'ember_bean',hp:1,move:1.2,interval:.8,bullet:1},
    {id:'lava_lizard',hp:2,move:1,interval:1,bullet:1.05,
      strafe:.32,pursue:.88,initialDelay:.6,lateral:1.6},
    {id:'volcano_bat',hp:2,move:1.08,interval:1.15,bullet:1.12,
      zigzag:Object.freeze([.55,.8,.65,1]),lateral:.95},
    {id:'magma_beetle',hp:4,move:.5,interval:1.45,bullet:.95,
      windup:.25,guard:.7,recovery:4.5,initialDelay:2.5,guardMove:.35}
  ].map(Object.freeze));
  const limits=Object.freeze({maxBullets:28,perActorBullets:3,step:1/120});
  const byId=new Map(profiles.map(p=>[p.id,p])),epsilon=1e-9;
  let states=new WeakMap(),bulletOwners=new WeakMap();
  const enabled=()=>typeof stage!=='undefined'&&gameWorlds.region(stage)?.key==='world-2:volcano';
  function prepare(actor) {
    if(!enabled()||!actor||actor===boss||actor.special||states.has(actor))return actor;
    const spec=byId.get(actor.volcanoSpeciesId);
    if(!spec)return actor;
    const base=tactics[0],interval=base.interval*spec.interval;
    actor.hp=spec.hp;actor.speed=base.move*spec.move;actor.shot=Math.min(actor.shot,interval);
    const pattern=Math.floor(Math.abs(actor.t||0)*10)%4;
    states.set(actor,{spec,age:0,mode:spec.zigzag?'zigzag':'pursue',
      remaining:spec.zigzag?spec.zigzag[pattern]:spec.initialDelay??Infinity,
      pattern,direction:pattern%2?1:-1,elapsed:0,interval,bulletSpeed:base.bullet*spec.bullet,
      guardAvailable:false,blocked:0,shots:0,flash:0});
    return actor;
  }
  function changeMode(state) {
    const spec=state.spec;
    state.elapsed=0;
    if(spec.strafe){
      state.mode=state.mode==='pursue'?'strafe':'pursue';
      state.remaining=state.mode==='strafe'?spec.strafe:spec.pursue;
      if(state.mode==='strafe')state.direction*=-1;
    }else if(spec.zigzag){
      state.pattern=(state.pattern+1)%spec.zigzag.length;
      state.direction*=-1;state.remaining=spec.zigzag[state.pattern];
    }else if(spec.guard){
      if(state.mode==='pursue'){state.mode='windup';state.remaining=spec.windup;}
      else if(state.mode==='windup'){state.mode='guard';state.remaining=spec.guard;state.guardAvailable=true;}
      else{state.mode='pursue';state.remaining=spec.recovery;state.guardAvailable=false;}
    }
  }
  function shoot(actor,state) {
    const live=enemyBullets.filter(b=>b.life>0&&byId.has(b.volcanoFire));
    if(live.length<limits.maxBullets&&live.filter(b=>bulletOwners.get(b)===actor).length<limits.perActorBullets){
      emitEnemyShot(actor);
      const bullet=enemyBullets[enemyBullets.length-1],angle=Math.atan2(player.y-actor.y,player.x-actor.x);
      bullet.vx=Math.cos(angle)*state.bulletSpeed;bullet.vy=Math.sin(angle)*state.bulletSpeed;
      bullet.volcanoFire=state.spec.id;bulletOwners.set(bullet,actor);state.shots++;
    }
    actor.shot=state.interval;
  }
  function update(actor,dt) {
    const state=states.get(actor);
    if(!enabled()||!state)return false;
    if(actor.hp<=0)return true;
    let left=Math.max(0,dt);
    // Engine dt is <=.04s; split at motion/shot boundaries and use <=120Hz slices.
    for(let guard=0;guard<256;guard++){
      if(state.remaining<=epsilon)changeMode(state);
      const canShoot=state.mode!=='windup'&&state.mode!=='guard'&&transition<=0;
      if(canShoot&&actor.shot<=epsilon)shoot(actor,state);
      if(left<=epsilon)break;
      const slice=Math.min(left,state.remaining,canShoot?actor.shot:Infinity,limits.step);
      const dx=player.x-actor.x,dy=player.y-actor.y,d=Math.hypot(dx,dy)||1,nx=dx/d,ny=dy/d;
      let lateral=0,forward=1;
      if(state.mode==='strafe')lateral=state.direction*state.spec.lateral;
      if(state.mode==='zigzag'){
        lateral=state.direction*state.spec.lateral*Math.sin(Math.PI*(state.elapsed+slice/2)/state.spec.zigzag[state.pattern]);
        forward=.8;
      }
      const norm=Math.hypot(forward,lateral),scale=actor.speed*(state.mode==='guard'||state.mode==='windup'?state.spec.guardMove:1)/norm;
      actor.x=Math.max(17,Math.min(W-17,actor.x+(nx*forward-ny*lateral)*scale*slice));
      actor.y=Math.max(18,Math.min(H-18,actor.y+(ny*forward+nx*lateral)*scale*slice));
      actor.t+=slice;actor.shot=Math.max(0,actor.shot-slice);
      state.age+=slice;state.elapsed+=slice;state.remaining-=slice;left-=slice;state.flash=Math.max(0,state.flash-slice);
    }
    return true;
  }
  function blockHit(actor) {
    const state=states.get(actor);
    if(!enabled()||!state||actor.hp<=0||state.mode!=='guard'||!state.guardAvailable)return false;
    state.guardAvailable=false;state.mode='pursue';state.remaining=state.spec.recovery;state.elapsed=0;
    state.blocked++;state.flash=.18;
    return true;
  }
  function drawTelegraph(ctx,actor) {
    const state=states.get(actor);
    if(!enabled()||!state||actor.hp<=0||!(state.mode==='windup'||state.mode==='guard'||state.flash>0))return;
    const spec=gameVolcano.species.find(s=>s.id===state.spec.id);
    const box=gameVolcano.geometry(spec,actor.x,actor.y,W,H,gameVolcano.pose(actor));
    ctx.save();ctx.translate(box.cx,box.cy);ctx.beginPath();ctx.ellipse(0,0,35,27,0,0,Math.PI*2);
    ctx.globalAlpha=state.flash>0?state.flash/.18:state.mode==='guard'?.9:.4+.4*(1-state.remaining/state.spec.windup);
    if(state.mode==='windup')ctx.setLineDash([4,4]);
    ctx.strokeStyle='#3a2433';ctx.lineWidth=5;ctx.stroke();ctx.strokeStyle=state.flash>0?'#fff6c9':'#ffc569';ctx.lineWidth=2;ctx.stroke();ctx.restore();
  }
  function drawBullet(ctx,bullet) {
    if(!enabled()||!byId.has(bullet.volcanoFire))return false;
    ctx.save();ctx.beginPath();ctx.arc(bullet.x,bullet.y,bullet.r,0,Math.PI*2);
    ctx.fillStyle=bullet.volcanoFire==='volcano_bat'?'#ffb04e':'#ff8b31';ctx.fill();
    ctx.strokeStyle=bullet.volcanoFire==='volcano_bat'?'#ce8aff':'#a53d22';ctx.lineWidth=1.5;ctx.stroke();
    ctx.beginPath();ctx.arc(bullet.x,bullet.y,bullet.r*.45,0,Math.PI*2);ctx.fillStyle='#fff0ae';ctx.fill();ctx.restore();
    return true;
  }
  function cleanup() {states=new WeakMap();bulletOwners=new WeakMap();}
  window.gameVolcanoCombat=Object.freeze({profiles,limits,enabled,prepare,update,blockHit,drawTelegraph,drawBullet,cleanup,
    snapshot:actor=>{const s=states.get(actor);return s?{id:s.spec.id,mode:s.mode,age:s.age,remaining:s.remaining,
      direction:s.direction,interval:s.interval,bulletSpeed:s.bulletSpeed,guardAvailable:s.guardAvailable,
      blocked:s.blocked,shots:s.shots,flash:s.flash}:null;}
  });
})();
