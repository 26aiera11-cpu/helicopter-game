/* Issue26 Storm Overlord: independent, bounded, game-time-only attack lifecycle. */
(()=>{
 'use strict';
 const settings=gameStormConfig.boss,tau=Math.PI*2,epsilon=1e-9,patterns=Object.freeze(['barrage','tornado','laser']);
 let active=null,layoutChanged=false;
 const enabled=a=>Boolean(gameStormSky.enabled()&&phase===5&&a&&a===boss&&a.hp>0);
 function blockedRects(){const c=canvas.getBoundingClientRect(),sx=W/(c.width||W),sy=H/(c.height||H);
  const out=['rotationJoystick','fire','hud','fullscreenToggle','exitGame','sensor','sensorStatus','worldPrototypeNotice'].flatMap(id=>{const e=document.getElementById(id);if(!e||e.hidden||!e.getClientRects().length||getComputedStyle(e).visibility==='hidden')return [];const b=e.getBoundingClientRect();return [{left:(b.left-c.left)*sx,right:(b.right-c.left)*sx,top:(b.top-c.top)*sy,bottom:(b.bottom-c.top)*sy}];});
  out.push({left:W*.3,right:W*.7,top:30,bottom:68});return out;
 }
 const outsideUI=(p,rects)=>p.x>=0&&p.x<=W&&p.y>=0&&p.y<=H&&rects.every(r=>p.x<r.left||p.x>r.right||p.y<r.top||p.y>r.bottom);
 function clearBullets(){enemyBullets=enemyBullets.filter(b=>!b.stormBoss);}
 function reset(){clearBullets();active=null;layoutChanged=false;}
 function prepare(a){if(!enabled(a))return false;reset();active={actor:a,age:0,phase:'rest',remaining:settings.firstDelay,last:null,pattern:null,sequence:[],phase2:false,awakened:false,awakenCount:0,
  shots:0,damageCalls:0,waves:0,winds:[],windSerial:0,windCooldown:0,teleports:0,teleportLog:[],trail:null,spin:0,spinAngle:0,laserAngle:0,laserOrigins:[],rects:blockedRects()};return true;}
 const rate=s=>s.phase2?settings.phase2AttackRate:1;
 const timed=(seconds,s)=>seconds/rate(s);
 function rest(s){s.phase='rest';s.remaining=Math.max(settings.minRest,timed(settings.rest,s));s.pattern=null;s.laserOrigins=[];}
 function cue(s){gameStormSky.attack(s.actor,true);}
 function choose(s){s.rects=blockedRects();const choices=patterns.filter(p=>p!==s.last),name=choices[Math.floor(Math.random()*choices.length)];s.pattern=name;s.last=name;s.sequence.push(name);s.sequence=s.sequence.slice(-30);s.waves=0;
  if(name==='barrage'){s.phase='barrage_warning';s.remaining=timed(settings.warning,s);}
  else if(name==='tornado'){s.phase='tornado_warning';s.remaining=timed(settings.warning,s);}
  else{s.phase='laser_warning';s.remaining=timed(settings.laserWarning,s);s.laserAngle=0;s.laserOrigins=turbinelines(s);}
  cue(s);
 }
 function awaken(s){s.rects=blockedRects();s.awakened=true;s.awakenCount++;s.pattern='awakening';s.phase='awakening';s.remaining=settings.awakenTime;s.sequence.push('awakening');s.winds=[];s.laserOrigins=[];clearBullets();cue(s);}
 function volley(s,count,offset=0){
  const live=enemyBullets.filter(b=>b.life>0&&b.stormBoss).length;if(live+count>settings.maxBullets)return;
  const speed=settings.bulletSpeed*(s.phase2?settings.phase2BulletSpeed:1);
  for(let i=0;i<count;i++){const angle=offset+tau*i/count;enemyBullets.push({x:s.actor.x+Math.cos(angle)*30,y:s.actor.y+Math.sin(angle)*30,vx:Math.cos(angle)*speed,vy:Math.sin(angle)*speed,r:5,life:settings.bulletLife,stormBoss:s.phase==='awakening'?'awakening':'barrage'});}
  s.shots+=count;s.waves++;cue(s);
 }
 function summon(s){const count=2+Math.floor(Math.random()*2);s.winds=[];
  for(let i=0;i<count&&i<settings.maxWinds;i++){
   const target=safeTarget(s,{avoidWinds:false});if(!target)continue;const a=Math.random()*tau;
   s.winds.push({id:++s.windSerial,...target,vx:Math.cos(a)*settings.windSpeed,vy:Math.sin(a)*settings.windSpeed,life:settings.windLife,t:0,turn:.6+Math.random()*.6});
  }cue(s);
 }
 function turbinePoints(s){const spec=gameStormSky.species.find(s=>s.id==='storm_overlord'),p=gameStormSky.pose(s.actor,true),g=gameStormSky.geometry(spec,s.actor,p),scale=g.scale*p.scale,cos=Math.cos(p.rotation),sin=Math.sin(p.rotation);
  // Centers in the separated1536×1024 source sprite; apply the exact body keyframe transform.
  return [[330,460],[1200,460]].map(([x,y])=>{const dx=(x-768)*scale,dy=(y-512)*scale;return {x:g.cx+dx*cos-dy*sin,y:g.cy+dx*sin+dy*cos};});}
 function turbinelines(s){return turbinePoints(s).map((p,index)=>({...p,index,angle:Math.atan2(player.y-p.y,player.x-p.x)}));}
 function laserLength(){return Math.max(120,Math.min(185,H*.53));}
 function segment(s,origin){const point=turbinePoints(s)[origin.index],a=origin.angle+s.laserAngle,length=laserLength();return {x:point.x,y:point.y,endX:point.x+Math.cos(a)*length,endY:point.y+Math.sin(a)*length,width:settings.laserWidth};}
 function lineHits(p,line,radius=12){const dx=line.endX-line.x,dy=line.endY-line.y,den=dx*dx+dy*dy,t=Math.max(0,Math.min(1,((p.x-line.x)*dx+(p.y-line.y)*dy)/(den||1)));return Math.hypot(p.x-line.x-t*dx,p.y-line.y-t*dy)<=line.width/2+radius;}
 function laserContains(p,s=active,radius=12){return Boolean(s&&s.phase==='laser'&&outsideUI(p,s.rects)&&s.laserOrigins.some(o=>lineHits(p,segment(s,o),radius)));}
 function safeCircle(p,s=active,avoidWinds=true){if(!s)return false;const r=22;if(p.x<r||p.x>W-r||p.y<r||p.y>H-r)return false;
  if(!s.rects.every(b=>Math.hypot(p.x-Math.max(b.left,Math.min(b.right,p.x)),p.y-Math.max(b.top,Math.min(b.bottom,p.y)))>r+5))return false;
  if(Math.hypot(p.x-s.actor.x,p.y-s.actor.y)<s.actor.r+r+18)return false;
  if(enemies.some(e=>e.hp>0&&Math.hypot(p.x-e.x,p.y-e.y)<e.r+r+8))return false;
  if(enemyBullets.some(b=>b.life>0&&Math.hypot(p.x-b.x,p.y-b.y)<b.r+r+12))return false;
  if(avoidWinds&&s.winds.some(w=>w.life>0&&Math.hypot(p.x-w.x,p.y-w.y)<settings.windRadius+r+10))return false;
  return !laserContains(p,s,r);
 }
 function safeTarget(s=active,{avoidWinds=true}={}){if(!s)return null;const points=[];
  for(let i=0;i<64;i++)points.push({x:25+Math.random()*Math.max(1,W-50),y:25+Math.random()*Math.max(1,H-50)});
  for(let x=30;x<W-25;x+=32)for(let y=35;y<H-25;y+=32)points.push({x,y});
  return points.find(p=>safeCircle(p,s,avoidWinds)&&Math.hypot(p.x-player.x,p.y-player.y)>65)||null;
 }
 function transport(s,w){if(s.windCooldown>0)return false;s.rects=blockedRects();const target=safeTarget(s);if(!target){s.windCooldown=.3;return false;}
  const before={x:player.x,y:player.y},entry={from:before,to:{...target},hp,score:runScore,age:s.age};
  player.x=target.x;player.y=target.y;player.vx=player.vy=0;invuln=Math.max(invuln,.75);
  s.trail={from:before,to:{...target},life:settings.spinTime};s.spin=settings.spinTime;s.spinAngle=0;s.windCooldown=settings.windCooldown;s.teleports++;
  entry.afterHP=hp;entry.afterScore=runScore;entry.safe=true;s.teleportLog.push(entry);s.teleportLog=s.teleportLog.slice(-20);return true;
 }
 function tickWinds(s,dt){s.windCooldown=Math.max(0,s.windCooldown-dt);if(s.trail){s.trail.life-=dt;if(s.trail.life<=0)s.trail=null;}
  s.spin=Math.max(0,s.spin-dt);s.spinAngle=s.spin>0?(1-s.spin/settings.spinTime)*tau*2:0;
  for(const w of s.winds){w.life-=dt;w.t+=dt;w.turn-=dt;if(w.turn<=0){const a=Math.atan2(w.vy,w.vx)+(Math.random()-.5)*1.8;w.vx=Math.cos(a)*settings.windSpeed;w.vy=Math.sin(a)*settings.windSpeed;w.turn=.5+Math.random()*.7;}
   w.x+=w.vx*dt;w.y+=w.vy*dt;const r=settings.windRadius;
   if(w.x<r||w.x>W-r)w.vx*=-1;if(w.y<r||w.y>H-r)w.vy*=-1;w.x=Math.max(r,Math.min(W-r,w.x));w.y=Math.max(r,Math.min(H-r,w.y));
   if(w.life>0&&s.windCooldown<=0&&Math.hypot(player.x-w.x,player.y-w.y)<r+12)transport(s,w);
  }s.winds=s.winds.filter(w=>w.life>0);
 }
 function resolve(s){if(s.phase==='rest')choose(s);
  else if(s.phase==='barrage_warning'){volley(s,8,0);s.phase='barrage_gap';s.remaining=timed(settings.secondVolley,s);}
  else if(s.phase==='barrage_gap'){volley(s,8,Math.PI/8);rest(s);}
  else if(s.phase==='tornado_warning'){summon(s);rest(s);}
  else if(s.phase==='laser_warning'){s.phase='laser';s.remaining=timed(settings.laserTime,s);cue(s);}
  else if(s.phase==='laser')rest(s);
  else if(s.phase==='awakening'){s.phase2=true;volley(s,12,Math.PI/12);rest(s);}
 }
 function update(a,dt){if(!enabled(a))return false;const s=active?.actor===a?active:(prepare(a),active);if(document.hidden)return true;
  if(layoutChanged){s.rects=blockedRects();s.winds=[];s.spin=0;s.trail=null;if(s.phase==='awakening')s.phase2=true;rest(s);layoutChanged=false;}
  if(!s.awakened&&a.hp<=a.maxHp*.5)awaken(s);
  let left=Math.max(0,dt),damaged=false;
  for(let guard=0;guard<512;guard++){
   if(s.remaining<=epsilon)resolve(s);if(left<=epsilon)break;
   const slice=Math.min(left,s.remaining,settings.step);
   if(!['laser','laser_warning','awakening'].includes(s.phase)){
    const dx=player.x-a.x,dy=player.y-a.y,d=Math.hypot(dx,dy)||1,radial=(d-Math.min(W*.35,160))*.65;
    a.x=Math.max(78,Math.min(W-78,a.x+(dx/d*radial-dy/d*18)*slice));a.y=Math.max(100,Math.min(H-82,a.y+(dy/d*radial+dx/d*18)*slice));
   }
   if(s.phase==='awakening'){
    const dx=a.x-player.x,dy=a.y-player.y,d=Math.hypot(dx,dy)||1,step=Math.min(settings.pullSpeed*slice,Math.max(0,d-a.r-26));
    player.x=Math.max(15,Math.min(W-15,player.x+dx/d*step));player.y=Math.max(15,Math.min(H-15,player.y+dy/d*step));
   }
   if(s.phase==='laser')s.laserAngle+=settings.laserTurn*rate(s)*slice;
   tickWinds(s,slice);
   if(!damaged&&laserContains(player,s)){damaged=true;s.damageCalls++;hurt();if(!started)return true;}
   a.t+=slice;s.age+=slice;s.remaining-=slice;left-=slice;
  }return true;
 }
 function clip(ctx,s){for(const r of s.rects){ctx.beginPath();ctx.rect(0,0,W,H);ctx.rect(r.left,r.top,r.right-r.left,r.bottom-r.top);ctx.clip('evenodd');}}
 function draw(ctx){const s=active;if(!s||!gameStormSky.enabled())return;
  ctx.save();clip(ctx,s);
  if(s.phase==='barrage_warning'||s.phase==='tornado_warning'||s.phase==='awakening'){
   const progress=s.phase==='awakening'?1-s.remaining/settings.awakenTime:1-s.remaining/timed(settings.warning,s);
   ctx.strokeStyle=s.phase==='awakening'?'#be9bff':'#f4ee8d';ctx.lineWidth=3;ctx.globalAlpha=.5+.35*Math.sin(progress*12)**2;
   ctx.beginPath();ctx.arc(s.actor.x,s.actor.y,55+progress*12,0,tau);ctx.stroke();
   if(s.phase==='awakening'){ctx.lineWidth=1.5;for(let i=0;i<6;i++){const angle=s.age*2+i*tau/6;ctx.beginPath();ctx.arc(s.actor.x,s.actor.y,80+i*8,angle,angle+1.5);ctx.stroke();}}
  }
  for(const w of s.winds){ctx.save();ctx.translate(w.x,w.y);ctx.rotate(w.t*2);ctx.strokeStyle='#bcefff';ctx.lineWidth=3;ctx.globalAlpha=Math.min(1,w.life);for(let i=0;i<4;i++){ctx.beginPath();ctx.ellipse(0,i*4-8,settings.windRadius-i*3,8-i,0,0,tau);ctx.stroke();}ctx.restore();}
  if(s.trail){ctx.globalAlpha=s.trail.life/settings.spinTime;ctx.strokeStyle='#b7eeff';ctx.setLineDash([5,8]);ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(s.trail.from.x,s.trail.from.y);ctx.lineTo(s.trail.to.x,s.trail.to.y);ctx.stroke();ctx.setLineDash([]);for(const p of [s.trail.from,s.trail.to]){ctx.beginPath();ctx.arc(p.x,p.y,23,0,tau);ctx.stroke();}}
  if(s.phase==='laser_warning'||s.phase==='laser'){
   const on=s.phase==='laser';ctx.globalAlpha=on?1:.65;
   for(const origin of s.laserOrigins){const line=segment(s,origin);ctx.strokeStyle=on?'#3998ed':'#ffed8f';ctx.lineWidth=on?settings.laserWidth:3;ctx.lineCap='round';ctx.setLineDash(on?[]:[6,5]);ctx.beginPath();ctx.moveTo(line.x,line.y);ctx.lineTo(line.endX,line.endY);ctx.stroke();
    if(on){ctx.strokeStyle='#e4fcff';ctx.lineWidth=4;ctx.stroke();}ctx.beginPath();ctx.arc(line.x,line.y,on?7:5+3*Math.sin(s.age*15)**2,0,tau);ctx.fillStyle='#f5feff';ctx.fill();}
  }ctx.restore();
 }
 function drawBullet(ctx,b){if(!gameStormSky.enabled()||!b.stormBoss)return false;ctx.save();ctx.fillStyle=b.stormBoss==='awakening'?'#d9bbff':'#c4faff';ctx.strokeStyle='#468cdd';ctx.lineWidth=2;ctx.beginPath();ctx.arc(b.x,b.y,b.r,0,tau);ctx.fill();ctx.stroke();ctx.restore();return true;}
 function defeated(a){if(active?.actor===a)reset();}
 function snapshot(){const s=active;return s?{phase:s.phase,remaining:s.remaining,age:s.age,last:s.last,pattern:s.pattern,sequence:[...s.sequence],phase2:s.phase2,awakened:s.awakened,awakenCount:s.awakenCount,shots:s.shots,waves:s.waves,damageCalls:s.damageCalls,winds:s.winds.map(w=>({...w})),windCooldown:s.windCooldown,teleports:s.teleports,teleportLog:s.teleportLog.map(t=>({...t})),laserAngle:s.laserAngle,lasers:s.laserOrigins.map(o=>segment(s,o)),spin:s.spin,rects:s.rects.map(r=>({...r}))}:null;}
 addEventListener('resize',()=>{layoutChanged=true;});document.addEventListener('fullscreenchange',()=>{layoutChanged=true;});
 window.gameStormBoss=Object.freeze({settings,patterns,enabled,prepare,reset,freeze:reset,update,draw,drawBullet,defeated,blockedRects,safeCircle,safeTarget,laserContains,lineHits,laserLength,visualSpin:()=>gameStormSky.enabled()?active?.spinAngle||0:0,snapshot,backgroundPaused:()=>Boolean(gameStormSky.enabled()&&document.hidden)});
})();
