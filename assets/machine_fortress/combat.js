/* Region-local normal combat. No boss patterns, player stats, art edits or audio owner. */
(()=>{
 'use strict';
 const settings=gameMachineConfig,profiles=settings.monsters,byId=new Map(profiles.map(p=>[p.id,p])),eps=1e-8;
 let states=new WeakMap(),owners=new WeakMap(),actors=new Set(),layout=null;
 const enabled=()=>gameMachineFortress.enabled();
 const clamp=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
 function direction(a){const dx=player.x-a.x,dy=player.y-a.y,d=Math.hypot(dx,dy)||1;return {dx:dx/d,dy:dy/d,d};}
 function ray(a,dir,length,margin=0){
  if(Math.hypot(dir.dx,dir.dy)<eps)return {x:a.x,y:a.y,endX:a.x,endY:a.y,length:0};
  let distance=length;
  if(dir.dx>eps)distance=Math.min(distance,(W-margin-a.x)/dir.dx);
  else if(dir.dx< -eps)distance=Math.min(distance,(margin-a.x)/dir.dx);
  if(dir.dy>eps)distance=Math.min(distance,(H-margin-a.y)/dir.dy);
  else if(dir.dy< -eps)distance=Math.min(distance,(margin-a.y)/dir.dy);
  distance=Math.max(0,distance);return {x:a.x,y:a.y,endX:a.x+dir.dx*distance,endY:a.y+dir.dy*distance,length:distance};
 }
 function aim(a,s){
  const d=direction(a);s.dx=d.dx;s.dy=d.dy;
  const length=s.spec.dash?H*s.spec.dashHeight:s.spec.length??s.spec.bullet*s.spec.bulletLife;
  s.path=ray(a,d,length,s.spec.dash?18:0);
  if(s.spec.dash){ // Use the stricter vertical margin for both axes; never slide at an edge.
   s.targetDistance=length;s.distance=s.path.length;s.dashDuration=s.distance/s.spec.dash;
  }
 }
 function prepare(a){
  if(!enabled()||!a||a===boss||a.special||states.has(a))return a;
  const id=gameMachineSpawns.select(phase),p=byId.get(id);
  Object.defineProperty(a,'machineSpeciesId',{value:id,enumerable:true});a.kind=settings.ids.indexOf(id);
  a.hp=p.hp;a.speed=p.speed;a.shot=Infinity;
  states.set(a,{spec:p,mode:'pursue',remaining:p.initial??Infinity,carry:0,ticks:0,age:0,dx:0,dy:0,path:null,distance:0,shots:0,denied:0,damageCalls:0,hitPlayer:false,retired:false});actors.add(a);return a;
 }
 function removeProjectiles(a){enemyBullets=enemyBullets.filter(b=>!b.machineNormal||owners.get(b)!==a);}
 function retire(a){const s=states.get(a);if(s){s.retired=true;s.path=null;s.mode='dead';}actors.delete(a);removeProjectiles(a);}
 function hit(a){if(enabled()&&a?.hp<=0)retire(a);}
 function cleanup(){enemyBullets=enemyBullets.filter(b=>!b.machineNormal);states=new WeakMap();owners=new WeakMap();actors=new Set();layout=null;}
 function beginFrame(){
  if(!enabled())return;
  const changed=layout&&(layout[0]!==W||layout[1]!==H);layout=[W,H];
  for(const a of actors){
   if(a.hp<=0||!enemies.includes(a)){retire(a);continue;}
   if(changed){const s=states.get(a);s.mode='rest';s.remaining=1.2;s.path=null;s.carry=0;s.hitPlayer=false;a.x=clamp(a.x,17,W-17);a.y=clamp(a.y,18,H-18);}
  }
  if(changed)enemyBullets=enemyBullets.filter(b=>!b.machineNormal);
 }
 function warning(a,s){s.mode='warning';s.remaining=s.spec.warning;s.hitPlayer=false;aim(a,s);gameMachineFortress.attack(a);}
 function fireShell(a,s,firstDt){
  const live=enemyBullets.filter(b=>b.life>0&&b.machineNormal);
  if(live.length<settings.maxNormalBullets&&live.filter(b=>owners.get(b)===a).length<settings.perActorBullets){
   emitEnemyShot(a);const b=enemyBullets.at(-1);
   Object.assign(b,{vx:s.dx*s.spec.bullet,vy:s.dy*s.spec.bullet,r:s.spec.bulletRadius,life:s.spec.bulletLife,machineNormal:s.spec.id,machineFirstDt:firstDt});owners.set(b,a);s.shots++;
  }else s.denied++;
 }
 function lineHits(point,line,radius=0){
  if(!line)return false;const dx=line.endX-line.x,dy=line.endY-line.y,n=dx*dx+dy*dy;
  const t=n?clamp(((point.x-line.x)*dx+(point.y-line.y)*dy)/n,0,1):0;
  return Math.hypot(point.x-line.x-dx*t,point.y-line.y-dy*t)<=radius;
 }
 function laserContains(point,a,radius=settings.playerLaserRadius){const s=states.get(a);return Boolean(enabled()&&s&&!s.retired&&s.mode==='laser'&&lineHits(point,s.path,s.spec.width/2+radius));}
 function damageLaser(a,s){if(started&&!s.hitPlayer&&invuln<=0&&laserContains(player,a)){s.hitPlayer=true;s.damageCalls++;hurt();}}
 function change(a,s,firstDt){
  if(s.mode==='warning'){
   if(s.spec.id==='gear_wasp'||s.spec.id==='armored_turret')aim(a,s);
   if(s.spec.dash){s.mode='dash';s.remaining=s.dashDuration;}
   else if(s.spec.active){s.mode='laser';s.remaining=s.spec.active;s.shots++;gameMachineFortress.attack(a);damageLaser(a,s);}
   else {fireShell(a,s,firstDt);s.mode='rest';s.remaining=s.spec.interval-s.spec.warning;s.path=null;}
  }else if(s.mode==='dash'||s.mode==='laser'){
   s.mode=s.spec.id==='screw_bot'?'cooldown':'rest';s.remaining=s.spec.rest;s.path=null;
  }else if(s.mode==='rest'){
   if(s.spec.id==='gear_wasp'||s.spec.id==='armored_turret'||s.spec.id==='laser_drone')warning(a,s);
   else {s.mode='pursue';s.remaining=Infinity;}
  }else if(s.mode==='cooldown'){s.mode='pursue';s.remaining=Infinity;}
  else warning(a,s);
 }
 function step(a,s,dt,firstDt){
  if(s.retired||a.hp<=0)return;
  if(s.mode==='pursue'&&s.spec.id==='screw_bot'&&transition<=0&&direction(a).d<=s.spec.near)warning(a,s);
  if(s.mode==='warning'&&(s.spec.id==='gear_wasp'||s.spec.id==='armored_turret'))aim(a,s);
  const d=direction(a);let vx=0,vy=0;
  const moving=s.mode==='pursue'||s.mode==='cooldown'||s.mode==='rest'&&s.spec.id!=='gear_wasp';
  if(moving){
   let forward=1,lateral=0;
   if(s.spec.id==='laser_drone'){forward=d.d<s.spec.near?-1:d.d>s.spec.far?1:0;lateral=forward?.45:1;}
   const norm=Math.hypot(forward,lateral);vx=(d.dx*forward-d.dy*lateral)*a.speed/norm;vy=(d.dy*forward+d.dx*lateral)*a.speed/norm;
  }
  if(s.mode==='dash'){
   const distance=Math.min(s.distance,s.spec.dash*dt);a.x+=s.dx*distance;a.y+=s.dy*distance;s.distance=Math.max(0,s.distance-distance);
  }else {a.x=clamp(a.x+vx*dt,17,W-17);a.y=clamp(a.y+vy*dt,18,H-18);}
  a.t+=dt;s.ticks++;s.age=s.ticks*settings.step;
  if(s.mode==='laser')damageLaser(a,s);
  if(!started||s.retired)return;
  if(transition<=0)s.remaining-=dt;
  if(s.remaining<=eps)change(a,s,firstDt);
 }
 function update(a,dt){
  const s=states.get(a);if(!enabled()||!s)return false;
  if(document.hidden||window.gameExitDialogOpen||s.retired||a.hp<=0)return true;
  const budget=Math.min(settings.maxDt,Math.max(0,Number.isFinite(dt)?dt:0)),before=s.carry;s.carry+=budget;
  const count=Math.floor((s.carry+eps)/settings.step);
  for(let i=0;i<count;i++){
   step(a,s,settings.step,Math.max(0,budget-((i+1)*settings.step-before)));
   if(!started||s.retired)break;
  }
  s.carry=Math.max(0,s.carry-count*settings.step);return true;
 }
 function bulletStep(b,dt){
  if(!b.machineNormal)return dt;
  if(b.machineFirstDt!==undefined){const value=b.machineFirstDt;delete b.machineFirstDt;return value;}
  return Math.min(settings.maxDt,Math.max(0,dt));
 }
 function drawTelegraph(ctx,a){
  const s=states.get(a);if(!enabled()||!s||s.retired||a.hp<=0||!s.path||!['warning','dash','laser'].includes(s.mode))return;
  const p=s.path,laser=s.spec.id==='laser_drone',color=laser?'#66e6ff':s.spec.id==='armored_turret'?'#ff9c39':s.spec.id==='gear_wasp'?'#e8c5ff':'#ffe08a';
  ctx.save();ctx.lineCap='round';ctx.lineJoin='round';
  if(s.spec.dash&&s.mode==='warning'){ctx.globalAlpha=.15;ctx.lineWidth=a.r*2;ctx.strokeStyle=color;ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(p.endX,p.endY);ctx.stroke();ctx.globalAlpha=1;}
  if(laser&&s.mode==='warning'){ctx.globalAlpha=.18;ctx.strokeStyle=color;ctx.lineWidth=s.spec.width;ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(p.endX,p.endY);ctx.stroke();ctx.globalAlpha=1;}
  ctx.strokeStyle=color;ctx.lineWidth=s.mode==='laser'?s.spec.width:2;ctx.setLineDash(s.mode==='warning'?[5,4]:[]);ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(p.endX,p.endY);ctx.stroke();
  if(s.mode==='laser'){ctx.strokeStyle='#e8fcff';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(p.endX,p.endY);ctx.stroke();}
  else if(s.spec.dash){const angle=Math.atan2(s.dy,s.dx);ctx.setLineDash([]);ctx.beginPath();ctx.moveTo(p.endX-8*Math.cos(angle-.5),p.endY-8*Math.sin(angle-.5));ctx.lineTo(p.endX,p.endY);ctx.lineTo(p.endX-8*Math.cos(angle+.5),p.endY-8*Math.sin(angle+.5));ctx.stroke();}
  ctx.restore();
 }
 function drawBullet(ctx,b){
  if(!b.machineNormal)return false;ctx.save();ctx.fillStyle='#ff982f';ctx.strokeStyle='#a9461d';ctx.lineWidth=1.5;ctx.beginPath();ctx.arc(b.x,b.y,b.r,0,Math.PI*2);ctx.fill();ctx.stroke();ctx.fillStyle='#ffe3a3';ctx.beginPath();ctx.arc(b.x,b.y,b.r*.42,0,Math.PI*2);ctx.fill();ctx.restore();return true;
 }
 function snapshot(a){const s=states.get(a);return s?{id:s.spec.id,mode:s.mode,remaining:s.remaining,age:s.age,carry:s.carry,shots:s.shots,denied:s.denied,damageCalls:s.damageCalls,hitPlayer:s.hitPlayer,retired:s.retired,direction:[s.dx,s.dy],distance:s.distance,targetDistance:s.targetDistance,dashDuration:s.dashDuration,path:s.path&&{...s.path}}:null;}
 window.gameMachineCombat=Object.freeze({settings,profiles,enabled,prepare,update,hit,cleanup,beginFrame,bulletStep,drawTelegraph,drawBullet,lineHits,laserContains,snapshot,
  summary:()=>({actors:actors.size,lasers:[...actors].filter(a=>states.get(a)?.mode==='laser').length,bullets:enemyBullets.filter(b=>b.machineNormal&&b.life>0).length}),backgroundPaused:()=>Boolean(enabled()&&document.hidden)});
})();
