/* Issue #8: first-playtest normal-enemy values, scoped to world-2:snowfield.
 * Forest tactics[0] is the 1.0 reference; boss/combatProfile is not changed.
 */
(() => {
  'use strict';
  const profiles=Object.freeze([
    {id:'snow_slime',hp:1,move:.85,interval:1.2,bullet:1},
    {id:'penguin_raider',hp:2,move:.95,interval:1,bullet:1,
      windup:.45,dash:.4,dashSpeed:1.8,rest:.65,cooldown:3.75},
    {id:'ice_yeti',hp:2,move:.75,interval:1.4,bullet:.9},
    {id:'frost_turtle',hp:3,move:.55,interval:1.5,bullet:1}
  ].map(Object.freeze));
  const states=new WeakMap(),epsilon=1e-9;
  const enabled=()=>typeof stage!=='undefined'&&gameWorlds.region(stage)?.key==='world-2:snowfield';
  function prepare(actor) {
    if(!enabled())return actor;
    const spec=profiles[Math.max(0,Math.min(profiles.length-1,phase-1))],base=tactics[0];
    actor.hp=spec.hp;actor.speed=base.move*spec.move;actor.shot=base.interval*spec.interval;
    actor.snowSpeciesId=spec.id;
    states.set(actor,{spec,mode:'pursue',remaining:spec.cooldown??Infinity,age:0,
      direction:{x:0,y:1},interval:actor.shot,bulletSpeed:base.bullet*spec.bullet,dashSpeed:base.move*(spec.dashSpeed??0)});
    return actor;
  }
  function changeMode(actor,state) {
    const spec=state.spec;
    if(state.mode==='pursue'){
      const dx=player.x-actor.x,dy=player.y-actor.y,d=Math.hypot(dx,dy);
      state.direction=d>epsilon?{x:dx/d,y:dy/d}:{x:0,y:1};
      state.mode='windup';state.remaining=spec.windup;
    }else if(state.mode==='windup'){
      state.mode='dash';state.remaining=spec.dash;
    }else if(state.mode==='dash'){
      state.mode='rest';state.remaining=spec.rest;
    }else{
      state.mode='pursue';state.remaining=spec.cooldown-spec.windup-spec.dash-spec.rest;
    }
  }
  function shoot(actor,state) {
    // Reuse the actual shot event, art hook, life, radius and damage path.
    emitEnemyShot(actor);
    const bullet=enemyBullets[enemyBullets.length-1],angle=Math.atan2(player.y-actor.y,player.x-actor.x);
    bullet.vx=Math.cos(angle)*state.bulletSpeed;bullet.vy=Math.sin(angle)*state.bulletSpeed;
    if(state.spec.id==='ice_yeti')bullet.snowIce=true;
    actor.shot=state.interval;
  }
  function update(actor,dt) {
    const state=states.get(actor);
    if(!enabled()||!state)return false;
    if(actor.hp<=0)return true;
    let left=Math.max(0,dt);
    // Split at state/shot boundaries rather than adding one frame to each phase.
    for(let guard=0;guard<64;guard++){
      if(state.remaining<=epsilon)changeMode(actor,state);
      const canShoot=state.mode==='pursue'&&transition<=0;
      if(canShoot&&actor.shot<=epsilon)shoot(actor,state);
      if(left<=epsilon)break;
      const slice=Math.min(left,state.remaining,canShoot?actor.shot:Infinity);
      let vx=0,vy=0;
      if(state.mode==='pursue'){
        const dx=player.x-actor.x,dy=player.y-actor.y,d=Math.hypot(dx,dy)||1;
        vx=dx/d*actor.speed;vy=dy/d*actor.speed;
      }else if(state.mode==='dash'){
        vx=state.direction.x*state.dashSpeed;vy=state.direction.y*state.dashSpeed;
      }
      actor.x=Math.max(17,Math.min(W-17,actor.x+vx*slice));
      actor.y=Math.max(18,Math.min(H-18,actor.y+vy*slice));
      actor.t+=slice;actor.shot=Math.max(0,actor.shot-slice);
      state.age+=slice;state.remaining-=slice;left-=slice;
    }
    return true;
  }
  function drawTelegraph(ctx,actor) {
    const state=states.get(actor);
    if(!enabled()||state?.mode!=='windup')return;
    const spec=gameSnowfield.species.find(s=>s.id===state.spec.id);
    const box=gameSnowfield.geometry(spec,actor.x,actor.y,W,H);
    const x=box.x+box.w/2,y=box.y+box.h/2;
    ctx.save();ctx.translate(x,y);ctx.rotate(Math.atan2(state.direction.y,state.direction.x));
    ctx.globalAlpha=.65+.3*Math.sin((1-state.remaining/state.spec.windup)*Math.PI*4)**2;
    ctx.strokeStyle='#fff3a6';ctx.lineWidth=3;ctx.beginPath();ctx.arc(0,0,25,0,Math.PI*2);ctx.stroke();
    ctx.beginPath();ctx.moveTo(29,-7);ctx.lineTo(38,0);ctx.lineTo(29,7);ctx.stroke();ctx.restore();
  }
  window.gameSnowfieldCombat=Object.freeze({profiles,enabled,prepare,update,drawTelegraph,
    snapshot:actor=>{const s=states.get(actor);return s?{id:s.spec.id,mode:s.mode,remaining:s.remaining,age:s.age,
      direction:{...s.direction},interval:s.interval,bulletSpeed:s.bulletSpeed,dashSpeed:s.dashSpeed}:null;}
  });
})();
