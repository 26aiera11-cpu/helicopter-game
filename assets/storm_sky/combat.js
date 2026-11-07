/* Four region-local roles; no existing movement or combat configuration is mutated. */
(()=>{
 'use strict';
 const profiles=gameStormConfig.monsters,byId=new Map(profiles.map(p=>[p.id,p]));let states=new WeakMap(),owners=new WeakMap();
 const enabled=()=>gameStormSky.enabled();
 function prepare(a){if(!enabled()||!a||a.special||states.has(a))return a;const p=byId.get(a.stormSpeciesId);if(!p)return a;
  a.hp=p.hp;a.speed=p.speed;a.shot=Math.min(a.shot,p.interval);states.set(a,{spec:p,age:0,mode:'pursue',remaining:p.dash?2.2:Infinity,dx:0,dy:0,shots:0});return a;}
 function shoot(a,s){const live=enemyBullets.filter(b=>b.life>0&&b.stormNormal);
  if(live.length<gameStormConfig.maxNormalBullets&&live.filter(b=>owners.get(b)===a).length<gameStormConfig.perActorBullets){
   emitEnemyShot(a);const b=enemyBullets.at(-1),angle=Math.atan2(player.y-a.y,player.x-a.x);Object.assign(b,{vx:Math.cos(angle)*s.spec.bullet,vy:Math.sin(angle)*s.spec.bullet,life:3.4,stormNormal:s.spec.id,r:s.spec.id==='storm_jellyfish'?6:5});owners.set(b,a);s.shots++;
  }a.shot=s.spec.interval;
 }
 function update(a,dt){const s=states.get(a);if(!enabled()||!s)return false;if(a.hp<=0)return true;let left=Math.max(0,dt);
  for(let guard=0;guard<256;guard++){
   if(s.remaining<=1e-9){if(s.mode==='pursue'){s.mode='warning';s.remaining=s.spec.warning;const d=Math.hypot(player.x-a.x,player.y-a.y)||1;s.dx=(player.x-a.x)/d;s.dy=(player.y-a.y)/d;gameStormSky.attack(a);}else if(s.mode==='warning'){s.mode='dash';s.remaining=s.spec.dashTime;}else if(s.mode==='dash'){s.mode='rest';s.remaining=s.spec.rest;}else{s.mode='pursue';s.remaining=2.2;}}
   const canShoot=s.mode!=='warning'&&s.mode!=='dash'&&transition<=0;
   if(canShoot&&a.shot<=1e-9)shoot(a,s);if(left<=1e-9)break;
   const slice=Math.min(left,1/120,s.remaining,canShoot?Math.max(a.shot,1e-9):Infinity),dx=player.x-a.x,dy=player.y-a.y,d=Math.hypot(dx,dy)||1,nx=dx/d,ny=dy/d;
   let vx=nx*a.speed,vy=ny*a.speed;
   if(s.spec.id==='tornado_spirit'){const lateral=Math.sin(s.age*4.5)*.95;vx=(nx*.7-ny*lateral)*a.speed;vy=(ny*.7+nx*lateral)*a.speed;}
   if(s.spec.id==='storm_jellyfish'){const f=d<145?-.55:d>205?.8:0;vx=(nx*f-ny*.25)*a.speed;vy=(ny*f+nx*.25)*a.speed;}
   if(s.mode==='warning'||s.mode==='rest'){vx=vy=0;}if(s.mode==='dash'){vx=s.dx*s.spec.dash;vy=s.dy*s.spec.dash;}
   a.x=Math.max(22,Math.min(W-22,a.x+vx*slice));a.y=Math.max(24,Math.min(H-24,a.y+vy*slice));a.t+=slice;a.shot=Math.max(0,a.shot-slice);s.age+=slice;s.remaining-=slice;left-=slice;
  }return true;
 }
 function drawTelegraph(ctx,a){const s=states.get(a);if(!enabled()||!s||s.mode!=='warning')return;ctx.save();ctx.strokeStyle='#fff48c';ctx.lineWidth=3;ctx.setLineDash([5,4]);ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(a.x+s.dx*110,a.y+s.dy*110);ctx.stroke();ctx.beginPath();ctx.arc(a.x,a.y,29,0,Math.PI*2);ctx.stroke();ctx.restore();}
 function drawBullet(ctx,b){if(!enabled()||!b.stormNormal)return false;ctx.save();ctx.fillStyle=b.stormNormal==='storm_jellyfish'?'#c690ff':'#b7f8ff';ctx.strokeStyle='#447cda';ctx.lineWidth=2;ctx.beginPath();ctx.arc(b.x,b.y,b.r,0,Math.PI*2);ctx.fill();ctx.stroke();if(b.stormNormal==='tornado_spirit'){ctx.beginPath();ctx.arc(b.x,b.y,b.r*.5,0,Math.PI*1.5);ctx.stroke();}ctx.restore();return true;}
 function cleanup(){states=new WeakMap();owners=new WeakMap();}
 window.gameStormCombat=Object.freeze({profiles,enabled,prepare,update,drawTelegraph,drawBullet,cleanup,snapshot:a=>{const s=states.get(a);return s?{id:s.spec.id,mode:s.mode,remaining:s.remaining,age:s.age,shots:s.shots,direction:[s.dx,s.dy]}:null;}});
})();
