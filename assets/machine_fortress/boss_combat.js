/* Issue36: GigaCore only. Original art, Cover, normal enemies, health/rewards and audio stay owned by existing systems. */
(()=>{
 'use strict';
 const settings=Object.freeze({firstDelay:1.4,rest:2.8,minRest:1.2,overdriveRest:.75,awakenTime:.8,
  laserWarning:.9,laserTime:1.8,laserWidth:8,laserRatio:.55,laserMax:220,laserSweep:Math.PI,overdriveLaser:1.25,
  missileWarning:.7,missileSpeed:80,overdriveMissile:1.1,missileRadius:6,missileLife:3.4,missileTurn:1.6,maxMissiles:12,
  wallWarning:1.2,wallTime:3,wallWidth:56,wallHeight:.75,safeHeight:.25,playerRadius:12,step:1/300,maxDt:.25});
 const patterns=Object.freeze(['laser','missiles','wall']),eps=1e-8,tau=Math.PI*2;
 // Orange emitter cores measured in the original402x322 and394x322 PNGs (not the old sheet source_rect).
 const anchors=Object.freeze({normal:Object.freeze([[55,230],[342,230]].map(Object.freeze)),overdrive:Object.freeze([[53,230],[338,230]].map(Object.freeze))});
 const effect=name=>document.getElementById('machine-effects-'+name);
 const wallImages=Object.freeze({wall:effect('electromagnetic_wall'),dim:effect('electromagnetic_wall_dim'),motion:effect('electromagnetic_wall_motion'),warning:effect('electromagnetic_warning')});
 let active=null,owners=new WeakMap(),overdriven=new WeakSet(),layoutChanged=false,seedSerial=0;
 const inRegion=()=>typeof stage!=='undefined'&&gameWorlds.region(stage)?.key==='world-2:machine-fortress'&&phase===5;
 const enabled=a=>Boolean(inRegion()&&a&&a===boss&&a.hp>0);
 const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
 const wrapped=a=>Math.atan2(Math.sin(a),Math.cos(a));
 const isOverdrive=a=>Boolean(a&&overdriven.has(a));
 function clearMissiles(){enemyBullets=enemyBullets.filter(b=>!b.machineBoss);}
 function reset(){clearMissiles();active=null;owners=new WeakMap();layoutChanged=false;}
 function seedValue(seed){if(seed===undefined){const word=new Uint32Array(1);if(globalThis.crypto?.getRandomValues){crypto.getRandomValues(word);seed=word[0];}else seed=Date.now()^++seedSerial;}return (seed>>>0)||0x6d360725;}
 function random(s){let n=s.rng;n^=n<<13;n^=n>>>17;n^=n<<5;s.rng=n>>>0;s.draws++;return s.rng/4294967296;}
 function blockedRects(){const c=canvas.getBoundingClientRect(),sx=W/(c.width||W),sy=H/(c.height||H);
  const rects=['hud','rotationJoystick','fire','fullscreenToggle','exitGame','sensor','sensorStatus','worldPrototypeNotice'].flatMap(id=>{const el=document.getElementById(id);if(!el||el.hidden||!el.getClientRects().length||getComputedStyle(el).visibility==='hidden')return [];const r=el.getBoundingClientRect();return [{x:(r.left-c.left)*sx,y:(r.top-c.top)*sy,w:r.width*sx,h:r.height*sy}];});
  rects.push({x:W*.3,y:30,w:W*.4,h:38});return rects;
 }
 function prepare(a,seed){
  if(!enabled(a))return false;reset();overdriven.delete(a);a.shot=Infinity;
  active={actor:a,seed:seedValue(seed),rng:0,draws:0,age:0,carry:0,ticks:0,phase:'rest',pattern:null,last:null,remaining:settings.firstDelay,elapsed:0,sequence:[],history:[],
   overdrive:false,awakenCount:0,shots:0,denied:0,damageCalls:0,damage:0,hitPlayer:false,laserOrigins:[],laserSweep:0,laserSign:1,wall:null,paused:false,
   layout:[W,H],rects:blockedRects(),previousTarget:{x:player.x,y:player.y},target:{x:player.x,y:player.y},frameDt:0};active.rng=active.seed;return true;
 }
 function rest(s){s.phase='rest';s.pattern=null;s.remaining=Math.max(settings.minRest,settings.rest*(s.overdrive?settings.overdriveRest:1));s.elapsed=0;s.wall=null;s.laserOrigins=[];s.hitPlayer=false;}
 function pause(){const s=active;if(s&&!s.paused){clearMissiles();rest(s);s.carry=0;s.paused=true;}}
 function awaken(s){clearMissiles();s.overdrive=true;overdriven.add(s.actor);s.awakenCount++;s.phase='awakening';s.pattern='awakening';s.remaining=settings.awakenTime;s.elapsed=0;s.wall=null;s.laserOrigins=[];s.hitPlayer=false;gameMachineFortress.attack(s.actor,true);}
 function hit(a){if(active?.actor===a&&a.hp>0&&!active.overdrive&&a.hp<=a.maxHp*.5)awaken(active);}
 function armPoints(a=active?.actor,offset=0){
  if(!a)return [];const image=gameMachineFortress.bossImage(a),pose=gameMachineFortress.bossPose(a,offset),iw=image.naturalWidth||(isOverdrive(a)?394:402),ih=image.naturalHeight||322,g={cx:a.x+pose.offsetX,cy:a.y,scale:132/iw},scale=g.scale*pose.scale,cos=Math.cos(pose.rotation),sin=Math.sin(pose.rotation);
  return anchors[isOverdrive(a)?'overdrive':'normal'].map(([x,y],index)=>{const dx=(x-iw/2)*scale,dy=(y-ih/2)*scale;return {index,source:[x,y],x:g.cx+dx*cos-dy*sin,y:g.cy+dx*sin+dy*cos};});
 }
 function ray(origin,angle,length,rects=[]){const dx=Math.cos(angle),dy=Math.sin(angle);let distance=length;
  if(dx>eps)distance=Math.min(distance,(W-origin.x)/dx);else if(dx< -eps)distance=Math.min(distance,-origin.x/dx);
  if(dy>eps)distance=Math.min(distance,(H-origin.y)/dy);else if(dy< -eps)distance=Math.min(distance,-origin.y/dy);
  for(const r of rects){const margin=settings.laserWidth/2,lo=[r.x-margin,r.y-margin],hi=[r.x+r.w+margin,r.y+r.h+margin],p=[origin.x,origin.y],v=[dx,dy];let near=0,far=Infinity;
   for(let axis=0;axis<2;axis++){if(Math.abs(v[axis])<eps){if(p[axis]<lo[axis]||p[axis]>hi[axis]){far=-1;break;}}else {let t0=(lo[axis]-p[axis])/v[axis],t1=(hi[axis]-p[axis])/v[axis];if(t0>t1)[t0,t1]=[t1,t0];near=Math.max(near,t0);far=Math.min(far,t1);}}
   if(far>=near&&far>=0)distance=Math.min(distance,Math.max(0,near));
  }
  distance=Math.max(0,distance);return {x:origin.x,y:origin.y,endX:origin.x+dx*distance,endY:origin.y+dy*distance,width:settings.laserWidth,length:distance};
 }
 function laserSegments(s=active){if(!s||!['laser_warning','laser'].includes(s.phase))return [];const points=armPoints(s.actor),length=Math.min(settings.laserMax,H*settings.laserRatio);
  return s.laserOrigins.map(o=>({...ray(points[o.index],o.angle+s.laserSweep,length,s.rects),index:o.index}));
 }
 function lineHits(p,line,radius=settings.playerRadius){if(!line||line.length<=eps)return false;const dx=line.endX-line.x,dy=line.endY-line.y,n=dx*dx+dy*dy,t=clamp(((p.x-line.x)*dx+(p.y-line.y)*dy)/(n||1),0,1);return Math.hypot(p.x-line.x-dx*t,p.y-line.y-dy*t)<=line.width/2+radius;}
 function laserContains(p,s=active,radius=settings.playerRadius){return Boolean(s&&s.phase==='laser'&&laserSegments(s).some(line=>lineHits(p,line,radius)));}
 function rectHits(p,r,radius=settings.playerRadius){return Boolean(r&&Math.hypot(p.x-clamp(p.x,r.x,r.x+r.w),p.y-clamp(p.y,r.y,r.y+r.h))<=radius);}
 function wallRect(s=active){if(!s?.wall)return null;return {x:s.phase==='wall_warning'?(s.wall.side==='left'?0:W-settings.wallWidth):s.wall.x-settings.wallWidth/2,y:s.wall.y,w:settings.wallWidth,h:s.wall.height};}
 function wallContains(p,s=active,radius=settings.playerRadius){return Boolean(s&&s.phase==='wall'&&rectHits(p,wallRect(s),radius));}
 function damage(s){if(!started||s.hitPlayer||invuln>0)return;s.hitPlayer=true;s.damageCalls++;const before=hp;hurt();s.damage+=before-hp;}
 function frameTarget(s,firstDt=0){const t=clamp(1-firstDt/(s.frameDt||settings.step),0,1);return {x:s.previousTarget.x+(s.target.x-s.previousTarget.x)*t,y:s.previousTarget.y+(s.target.y-s.previousTarget.y)*t};}
 function choose(s,firstDt){
  const choices=patterns.filter(p=>p!==s.last),name=choices[Math.floor(random(s)*choices.length)];s.last=name;s.pattern=name;s.sequence.push(name);s.sequence=s.sequence.slice(-40);s.elapsed=0;s.hitPlayer=false;s.rects=blockedRects();
  if(name==='laser'){s.phase='laser_warning';s.remaining=settings.laserWarning;s.laserSweep=0;s.laserSign=random(s)<.5?-1:1;s.laserOrigins=armPoints(s.actor).map(p=>({index:p.index,angle:Math.atan2(frameTarget(s,firstDt).y-p.y,frameTarget(s,firstDt).x-p.x)}));}
  else if(name==='missiles'){s.phase='missile_warning';s.remaining=settings.missileWarning;}
  else {clearMissiles();const combo=Math.floor(random(s)*4),side=combo<2?'left':'right',safe=combo%2===0?'top':'bottom';s.phase='wall_warning';s.remaining=settings.wallWarning;
   s.wall={combo,side,safe,x:side==='left'?-settings.wallWidth:W+settings.wallWidth,y:safe==='top'?H*settings.safeHeight:0,height:H*settings.wallHeight,elapsed:0};}
  gameMachineFortress.attack(s.actor,true,-firstDt);
 }
 function missiles(s,firstDt){
  const count=s.overdrive?3:2,live=enemyBullets.filter(b=>b.machineBoss&&b.life>0).length;
  if(live+count>settings.maxMissiles){s.denied+=count;return;}
  gameMachineFortress.attack(s.actor,true,-firstDt);
  const speed=settings.missileSpeed*(s.overdrive?settings.overdriveMissile:1),points=armPoints(s.actor,-firstDt);
  for(let i=0;i<count;i++){const p=count===3&&i===1?{x:s.actor.x,y:s.actor.y+38}:points[i===0?0:1],angle=Math.PI/2-(i-(count-1)/2)*.35;
   const b={x:p.x,y:p.y,vx:Math.cos(angle)*speed,vy:Math.sin(angle)*speed,r:settings.missileRadius,life:settings.missileLife,machineBoss:'missile',overdrive:s.overdrive,speed,carry:0,firstDt,turn:0,age:0};enemyBullets.push(b);owners.set(b,s);s.shots++;
  }
 }
 function resolve(s,firstDt){
  if(s.phase==='rest')choose(s,firstDt);
  else if(s.phase==='laser_warning'){s.phase='laser';s.remaining=settings.laserTime/(s.overdrive?settings.overdriveLaser:1);s.elapsed=0;gameMachineFortress.attack(s.actor,true,-firstDt);}
  else if(s.phase==='missile_warning'){missiles(s,firstDt);rest(s);}
  else if(s.phase==='wall_warning'){s.phase='wall';s.remaining=settings.wallTime;s.elapsed=0;}
  else {if(s.phase==='laser'||s.phase==='wall'){s.history.push({pattern:s.pattern,duration:s.elapsed,sweep:s.laserSweep,wall:s.wall&&{...s.wall}});s.history=s.history.slice(-20);}rest(s);}
 }
 function step(s,dt,firstDt){
  if(s.phase==='rest'||s.phase==='missile_warning'){
   const a=s.actor,target=frameTarget(s,firstDt),dx=target.x-a.x,dy=target.y-a.y,d=Math.hypot(dx,dy)||1,radial=(d-Math.min(W*.35,160))*.9;
   a.x=clamp(a.x+(dx/d*radial-dy/d*45*.48)*dt,72,W-72);a.y=clamp(a.y+(dy/d*radial+dx/d*45*.48)*dt,85,H-80);
  }
  s.elapsed+=dt;s.ticks++;s.age=s.ticks*settings.step;s.actor.t+=dt;
  if(s.phase==='laser'){s.laserSweep=s.laserSign*settings.laserSweep*Math.min(1,s.elapsed/(settings.laserTime/(s.overdrive?settings.overdriveLaser:1)));if(laserContains(player,s))damage(s);}
  if(s.phase==='wall'){const progress=Math.min(1,s.elapsed/settings.wallTime),start=s.wall.side==='left'?-settings.wallWidth:W+settings.wallWidth,end=s.wall.side==='left'?W+settings.wallWidth:-settings.wallWidth;
   s.wall.x=start+(end-start)*progress;s.wall.elapsed=s.elapsed;if(wallContains(player,s))damage(s);}
  if(!started||active!==s)return;s.remaining-=dt;if(s.remaining<=eps)resolve(s,firstDt);
 }
 function update(a,dt){
  if(!enabled(a))return false;const s=active?.actor===a?active:(prepare(a),active);
  if(document.hidden||window.gameExitDialogOpen){pause();return true;}
  if(layoutChanged||s.layout[0]!==W||s.layout[1]!==H){clearMissiles();rest(s);s.carry=0;s.layout=[W,H];s.rects=blockedRects();layoutChanged=false;}
  s.paused=false;if(!s.overdrive&&a.hp<=a.maxHp*.5)awaken(s);if(transition>0)return true;
  const budget=Math.min(settings.maxDt,Math.max(0,Number.isFinite(dt)?dt:0)),before=s.carry;s.previousTarget=s.target;s.target={x:player.x,y:player.y};s.frameDt=budget;s.carry+=budget;
  const count=Math.floor((s.carry+eps)/settings.step);
  for(let i=0;i<count;i++){step(s,settings.step,Math.max(0,budget-((i+1)*settings.step-before)));if(!started||active!==s)break;}
  s.carry=Math.max(0,s.carry-count*settings.step);return true;
 }
 function updateBullet(b,dt){
  if(!b.machineBoss)return false;const s=owners.get(b);
  if(!s||active!==s||!enabled(s.actor)){b.life=0;return true;}
  if(document.hidden||window.gameExitDialogOpen||s.paused)return true;
  const budget=Math.min(settings.maxDt,Math.max(0,b.firstDt??dt)),offset=Math.max(0,s.frameDt-budget),before=b.carry;delete b.firstDt;b.carry+=budget;
  const count=Math.floor((b.carry+eps)/settings.step);
  for(let i=0;i<count&&b.life>0;i++){const t=clamp((offset+(i+1)*settings.step-before)/(s.frameDt||settings.step),0,1),target={x:s.previousTarget.x+(s.target.x-s.previousTarget.x)*t,y:s.previousTarget.y+(s.target.y-s.previousTarget.y)*t},angle=Math.atan2(b.vy,b.vx),wanted=Math.atan2(target.y-b.y,target.x-b.x),turn=clamp(wrapped(wanted-angle),-settings.missileTurn*settings.step,settings.missileTurn*settings.step),next=angle+turn;
   b.vx=Math.cos(next)*b.speed;b.vy=Math.sin(next)*b.speed;b.x+=b.vx*settings.step;b.y+=b.vy*settings.step;b.life-=settings.step;if(b.life<=eps)b.life=0;b.age+=settings.step;b.turn+=Math.abs(turn);
   if(b.x< -b.r||b.x>W+b.r||b.y< -b.r||b.y>H+b.r)b.life=0;
  }b.carry=Math.max(0,b.carry-count*settings.step);return true;
 }
 function bulletHit(b,amount){if(b.machineBoss&&active&&owners.get(b)===active&&amount>0){active.damageCalls++;active.damage+=amount;}}
 function tileWall(ctx,image,r,alpha=1,flip=false){
  if(!image?.complete||!image.naturalWidth)return;const iw=image.naturalWidth,ih=image.naturalHeight,scale=r.w/iw,cap=24,capH=cap*scale,middleH=(ih-cap*2)*scale;
  ctx.save();ctx.beginPath();ctx.rect(r.x,r.y,r.w,r.h);ctx.clip();ctx.globalAlpha=alpha;
  if(flip){ctx.translate(r.x*2+r.w,0);ctx.scale(-1,1);}
  ctx.drawImage(image,0,0,iw,cap,r.x,r.y,r.w,capH);
  for(let y=r.y+capH,index=0;y<r.y+r.h-capH;y+=middleH,index++){ctx.save();ctx.beginPath();ctx.rect(r.x,r.y+capH,r.w,Math.max(0,r.h-2*capH));ctx.clip();
   if(index%2){ctx.translate(0,2*y+middleH);ctx.scale(1,-1);}ctx.drawImage(image,0,cap,iw,ih-cap*2,r.x,y,r.w,middleH);ctx.restore();}
  ctx.drawImage(image,0,ih-cap,iw,cap,r.x,r.y+r.h-capH,r.w,capH);ctx.restore();
 }
 function draw(ctx){const s=active;if(!s||!inRegion())return;ctx.save();
  if(s.phase==='laser'||s.phase==='laser_warning'){const on=s.phase==='laser';ctx.lineCap='round';ctx.strokeStyle=on?(s.overdrive?'#ff984c':'#58dcff'):'#ffe49b';ctx.lineWidth=on?settings.laserWidth:2;ctx.setLineDash(on?[]:[5,4]);
   for(const line of laserSegments(s)){if(line.length<=eps)continue;ctx.beginPath();ctx.moveTo(line.x,line.y);ctx.lineTo(line.endX,line.endY);ctx.stroke();if(on){ctx.save();ctx.strokeStyle='#f1fdff';ctx.lineWidth=2;ctx.stroke();ctx.restore();}}
  }else if(s.phase==='wall'||s.phase==='wall_warning'){const r=wallRect(s);ctx.save();ctx.beginPath();ctx.rect(r.x,r.y,r.w,r.h);ctx.clip();ctx.fillStyle=s.phase==='wall'?'rgba(43,172,255,.28)':'rgba(255,114,67,.12)';ctx.fillRect(r.x,r.y,r.w,r.h);
   if(s.phase==='wall_warning'){tileWall(ctx,wallImages.dim,r,.6);tileWall(ctx,wallImages.warning,r,.6+.25*Math.sin(s.age*14)**2);}
   else {tileWall(ctx,wallImages.wall,r);tileWall(ctx,wallImages.motion,r,.22,s.wall.side==='right');}ctx.restore();
  }else if(s.phase==='awakening'||s.phase==='missile_warning'){ctx.strokeStyle=s.phase==='awakening'?'#ffb370':'#ffdc86';ctx.lineWidth=2;ctx.globalAlpha=.6+.3*Math.sin(s.age*16)**2;ctx.beginPath();ctx.arc(s.actor.x,s.actor.y,60+3*Math.sin(s.age*12),0,tau);ctx.stroke();}
  ctx.restore();
 }
 function drawBullet(ctx,b){if(!b.machineBoss)return false;ctx.save();ctx.translate(b.x,b.y);ctx.rotate(Math.atan2(b.vy,b.vx));ctx.fillStyle=b.overdrive?'#ffbe73':'#79e8ff';ctx.strokeStyle='#effcff';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(b.r,0);ctx.quadraticCurveTo(1,-b.r,-b.r,-b.r*.65);ctx.lineTo(-b.r,b.r*.65);ctx.quadraticCurveTo(1,b.r,b.r,0);ctx.fill();ctx.stroke();ctx.strokeStyle='#ffad51';ctx.beginPath();ctx.moveTo(-b.r-1,0);ctx.lineTo(-b.r-6,0);ctx.stroke();ctx.restore();return true;}
 function safeTargets(s=active){if(!s?.wall)return [];const r=settings.playerRadius+1,y0=s.wall.safe==='top'?r:H*(1-settings.safeHeight)+r,y1=s.wall.safe==='top'?H*settings.safeHeight-r:H-r,points=[];
  for(let y=y0;y<=y1;y+=4)for(let x=r;x<=W-r;x+=6){const p={x,y};if(s.rects.some(rect=>rectHits(p,rect,r))||Math.hypot(x-s.actor.x,y-s.actor.y)<s.actor.r+r+4)continue;points.push(p);}return points;
 }
 function defeated(a){if(active?.actor===a)reset();}
 function snapshot(){const s=active;return s?{phase:s.phase,pattern:s.pattern,last:s.last,remaining:s.remaining,elapsed:s.elapsed,age:s.age,seed:s.seed,rng:s.rng,draws:s.draws,hp:s.actor.hp,maxHp:s.actor.maxHp,overdrive:s.overdrive,awakenCount:s.awakenCount,paused:s.paused,
  sequence:[...s.sequence],history:s.history.map(v=>({...v})),shots:s.shots,denied:s.denied,damageCalls:s.damageCalls,damage:s.damage,hitPlayer:s.hitPlayer,laserSweep:s.laserSweep,lasers:laserSegments(s),arms:armPoints(s.actor),wall:s.wall&&{...s.wall,rect:wallRect(s),safeHeight:H*settings.safeHeight},
  missiles:enemyBullets.filter(b=>b.machineBoss&&b.life>0).map(b=>({x:b.x,y:b.y,vx:b.vx,vy:b.vy,r:b.r,life:b.life,age:b.age,turn:b.turn,speed:b.speed,overdrive:b.overdrive})),rects:s.rects.map(r=>({...r}))}:null;}
 addEventListener('resize',()=>{if(active)layoutChanged=true;});document.addEventListener('fullscreenchange',()=>{if(active)layoutChanged=true;});document.addEventListener('visibilitychange',()=>{if(document.hidden)pause();});
 window.gameMachineBoss=Object.freeze({settings,patterns,anchors,wallImages,enabled,prepare,reset,freeze:reset,pause,hit,isOverdrive,armPoints,update,updateBullet,bulletHit,draw,drawBullet,defeated,snapshot,laserSegments,lineHits,laserContains,wallRect,rectHits,wallContains,safeTargets});
})();
