/* 헬리 트리오 — independent item monsters.
 * Loaded after the original gameplay and scoring scripts.  The original
 * monster/boss routines and rank storage stay unchanged.
 */
(() => {
 'use strict';
 const CONFIG=Object.freeze({
  hp:5, life:10, maxActive:1, startDelay:8, phaseDelay:7,
  intervalMin:11, intervalMax:16, warningTime:1
 });
 let monsters=[],entrances=[],bursts=[],timer=CONFIG.startDelay,previousStage=0,previousPhase=1,previousBoss=false;
 let wasPlaying=false;
 const art={};
 for(const [kind,count] of [['idle',6],['move',6],['hit',3],['explosion',4]]){
  art[kind]=Array.from({length:count},(_,index)=>{
   const img=new Image();
   img.src='assets/item_monster/frames/'+kind+'_'+String(index+1).padStart(2,'0')+'.png';
   return img;
  });
 }
 const reset=delay=>{monsters=[];entrances=[];bursts=[];timer=delay;};
 const randomInterval=()=>CONFIG.intervalMin+Math.random()*(CONFIG.intervalMax-CONFIG.intervalMin);
 const entry=()=>{
  const edge=Math.floor(Math.random()*4),pad=27;
  let x=edge===0?pad:edge===1?W-pad:pad+Math.random()*(W-2*pad);
  let y=edge===2?pad:edge===3?H-pad:pad+Math.random()*(H-2*pad);
  if(edge<2)y=pad+Math.random()*(H-2*pad);
  else x=pad+Math.random()*(W-2*pad);
  return{x,y,time:CONFIG.warningTime};
 };
 // Remove the old 22% substitution.  A regular spawn is always regular.
 warnEnemy=function(){
  const w=entry();
  warnings.push({...w,time:1.4,kind:Math.floor(Math.random()*enemySprites[stage].length),special:false});
 };
 const nativeUpdate=update;
 update=function(dt){
  // Before regular update, let guided Bingle shots seek an item monster
  // when no regular target or boss is within homing range.
  if(started&&!boss){
   for(const b of bullets){
    if(!b.homing||b.life<=0)continue;
    const nearbyEnemy=enemies.some(e=>e.hp>0&&Math.hypot(e.x-b.x,e.y-b.y)<260);
    if(nearbyEnemy)continue;
    let chosen=null,dist=260;
    for(const m of monsters){const d=Math.hypot(m.x-b.x,m.y-b.y);if(d<dist){chosen=m;dist=d;}}
    if(chosen){
     const wanted=Math.atan2(chosen.y-b.y,chosen.x-b.x),old=Math.atan2(b.vy,b.vx);
     const diff=Math.atan2(Math.sin(wanted-old),Math.cos(wanted-old));
     const turn=old+Math.max(-3.3*dt,Math.min(3.3*dt,diff));
     b.vx=Math.cos(turn)*b.speed;b.vy=Math.sin(turn)*b.speed;
    }
   }
  }
  nativeUpdate(dt);
  if(!started||window.gameExitDialogOpen)return;
  if(stage!==previousStage||phase!==previousPhase){
   reset(CONFIG.phaseDelay);previousStage=stage;previousPhase=phase;
  }
  if(boss){
   if(!previousBoss)reset(CONFIG.phaseDelay);
   previousBoss=true;return;
  }
  previousBoss=false;
  timer-=dt;
  if(timer<=0&&transition<=0&&phaseKills<requiredKills&&
     monsters.length+entrances.length<CONFIG.maxActive){
   entrances.push(entry());timer=randomInterval();
  }
  for(const w of entrances){
   w.time-=dt;
   if(w.time<=0)monsters.push({x:w.x,y:w.y,r:16,hp:CONFIG.hp,special:true,
    life:CONFIG.life,t:0,turn:0,vx:0,vy:0,flash:0});
  }
  entrances=entrances.filter(w=>w.time>0);
  for(const m of monsters){
   m.t+=dt;m.life-=dt;m.turn-=dt;m.flash=Math.max(0,m.flash-dt);
   if(m.life<=0){m.hp=0;continue;}
   if(m.turn<=0){
    const angle=Math.random()*Math.PI*2;
    m.vx=Math.cos(angle);m.vy=Math.sin(angle);m.turn=.4+Math.random()*.85;
   }
   // Random movement with gentle evasion, no shots and no contact damage.
   const dx=m.x-player.x,dy=m.y-player.y,d=Math.hypot(dx,dy)||1;
   const evade=d<125?.65:0,speed=45+stage*8;
   m.x+=((1-evade)*m.vx+evade*dx/d)*speed*dt;
   m.y+=((1-evade)*m.vy+evade*dy/d)*speed*dt;
   if(m.x<18||m.x>W-18)m.vx*=-1;
   if(m.y<18||m.y>H-18)m.vy*=-1;
   m.x=Math.max(18,Math.min(W-18,m.x));
   m.y=Math.max(18,Math.min(H-18,m.y));
   for(const b of bullets){
    if(b.life<=0||(b.hit||[]).includes(m)||!bulletHitsCircle(b,m.x,m.y,m.r))continue;
    if(b.kind===2){if(!consumeTankoPierce(b,m))continue;}
    else {b.hit.push(m);b.life=0;}
    m.hp-=b.damage||1;m.flash=.14;gameAudio.fx('hit');
    if(b.kind!==2){b.pierce=(b.pierce||1)-1;if(b.pierce>0)b.life=1;}
    if(m.hp<=0){
     if(gameScoring.enemyDefeated(m)){
      gameAudio.fx('destroy');dropItem(m.x,m.y);
      bursts.push({x:m.x,y:m.y,t:0});
      for(let i=0;i<9;i++)particles.push({
       x:m.x,y:m.y,vx:(Math.random()-.5)*180,vy:(Math.random()-.5)*180,life:.5
      });
     }
     break;
    }
   }
  }
  monsters=monsters.filter(m=>m.hp>0);
  for(const b of bursts)b.t+=dt;
  bursts=bursts.filter(b=>b.t<.48);
 };
 const nativeDraw=draw;
 draw=function(){
  nativeDraw();
  if(!started&&menu.classList.contains('hidden')===false)return;
  for(const w of entrances){
   ctx.save();ctx.globalAlpha=.65+.35*Math.sin(performance.now()/130);
   ctx.fillStyle='#f4bd28';ctx.strokeStyle='#fff';ctx.lineWidth=2;
   ctx.beginPath();ctx.arc(w.x,w.y,16,0,7);ctx.fill();ctx.stroke();
   ctx.fillStyle='#a82725';ctx.font='bold 18px system-ui';ctx.textAlign='center';
   ctx.fillText('★',w.x,w.y+6);ctx.restore();
  }
  for(const m of monsters){
   ctx.save();ctx.globalAlpha=.8+.2*Math.sin(m.t*8)**2;
   ctx.shadowColor='#ffbb19';ctx.shadowBlur=10;
   const imgs=art[Math.abs(m.vx)+Math.abs(m.vy)>.7?'move':'idle'];
   const wanted=imgs[Math.floor(m.t*9)%imgs.length];
   // Show the approved idle sprite until the remaining animation PNGs are uploaded.
   const img=wanted.complete&&wanted.naturalWidth?wanted:art.idle[0];
   if(img.complete&&img.naturalWidth)ctx.drawImage(img,m.x-25,m.y-23,50,46);
   else{
    ctx.fillStyle='#e93631';ctx.strokeStyle='#ffe05b';ctx.lineWidth=3;
    ctx.beginPath();ctx.arc(m.x,m.y,17,0,7);ctx.fill();ctx.stroke();
    ctx.fillStyle='#fff';ctx.font='bold 22px system-ui';ctx.textAlign='center';
    ctx.fillText('★',m.x,m.y+7);
   }
   if(m.flash>0){
    ctx.globalAlpha=.5*m.flash/.14;ctx.fillStyle='#fff';
    ctx.beginPath();ctx.arc(m.x,m.y,18,0,7);ctx.fill();
   }
   ctx.restore();
  }
  for(const b of bursts){
   const frame=Math.min(3,Math.floor(b.t/.12)),img=art.explosion[frame];
   ctx.save();ctx.globalAlpha=1-b.t/.48;
   if(img.complete&&img.naturalWidth)ctx.drawImage(img,b.x-32,b.y-30,64,60);
   else{ctx.fillStyle='#ffca35';ctx.beginPath();ctx.arc(b.x,b.y,26*(1-b.t/.48),0,7);ctx.fill();}
   ctx.restore();
  }
 };
 // The menu's hide/show transition runs on every new game, including when
 // the original start() was captured by an existing event listener.
 new MutationObserver(()=>{
  const playing=started&&menu.classList.contains('hidden');
  if(playing&&!wasPlaying){
   reset(CONFIG.startDelay);previousStage=stage;previousPhase=phase;previousBoss=false;
  }
  wasPlaying=playing;
 }).observe(menu,{attributes:true,attributeFilter:['class']});
 window.itemMonsterDebug=Object.freeze({
  get activeCount(){return monsters.length;},
  get warningCount(){return entrances.length;},
  get countdown(){return timer;},
  config:CONFIG
 });
})();
