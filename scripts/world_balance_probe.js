/* Issue39 diagnostic only; never included by the standalone builder. */
(()=>{
 const clone=x=>JSON.parse(JSON.stringify(x));
 function clean(){if(started)gameScoring.finish('abandoned');started=false;menu.classList.remove('hidden');clearGameOver();gameControls.reset();}
 function seed(n){let r=n>>>0,c=(n^0xa39d8127)>>>0;Math.random=()=>{r^=r<<13;r^=r>>>17;r^=r<<5;return (r>>>0)/4294967296};crypto.getRandomValues=a=>{for(let i=0;i<a.length;i++){c^=c<<13;c^=c>>>17;c^=c<<5;a[i]=c>>>0}return a};}
 function begin(hero,n=1001){clean();seed(n);gameWorlds.setDeveloperStart({enabled:false});gameWorlds.setTrialEnabled(true);itemMonsters.configure({opportunitiesPerRegion:3});start(hero);fireCooldown=0;gameAudio.fx=()=>{};}
 function definitions(){const weapons=[];
  for(let h=0;h<3;h++)for(let u=0;u<=5;u++){begin(h);player.upgrade=u;transition=0;spawn=999;fireCooldown=0;keys.fire=true;update(0);keys.fire=false;weapons.push({hero:h,upgrade:u,interval:fireCooldown,shotsPerSecond:1/fireCooldown,projectiles:bullets.length,nominalDPS:bullets.reduce((s,b)=>s+b.damage,0)/fireCooldown,damage:bullets[0].damage,speed:bullets[0].speed,homing:bullets.filter(b=>b.homing).length,pierce:bullets[0].pierce,width:h===2?tankoBulletWidth(u):null,height:29,life:bullets[0].life});}
  clean();return clone({regions:gameWorlds.regions,tactics,requiredKills,maxHP,playerSpeed,flightProfiles,bossMultipliers:[1,1.1,1.4,1.6,1.9,2.2],enemyArtCounts:enemySprites.map(x=>x.length),weapons,snowProfiles:gameSnowfieldCombat.profiles,volcanoProfiles:gameVolcanoCombat.profiles,difficulty:gameRegionDifficulty.regions,storm:gameStormConfig,machine:gameMachineConfig,bossSettings:{snow:gameSnowfieldBoss.settings,volcano:gameVolcanoBoss.settings,storm:gameStormConfig.boss,machine:gameMachineBoss.settings},items:itemMonsters.snapshot()});
 }
 function assay(hero,u,distance,radius,hpTarget=1e9,seconds=12,rate=120){
  begin(hero);player.upgrade=u;player.x=W/2;player.y=H*.8;player.a=-Math.PI;tilt={x:0,y:0};spawn=999;transition=0;fireCooldown=0;keys.fire=true;update(0);keys.fire=false;bullets=[];boss={x:player.x,y:player.y-distance,r:radius,hp:hpTarget,maxHp:hpTarget};
  let t=0,damage=0,shots=0,hits=0;const dt=1/rate,originalShoot=shoot;window.shoot=()=>{shots++;return originalShoot()};keys.fire=true;fireCooldown=0;
  try{for(;t<seconds&&damage<hpTarget;t+=dt){auditFireTick(dt);auditAdvanceBullets(dt);for(const b of bullets)if(b.life>0&&bulletHitsCircle(b,boss.x,boss.y,boss.r)){damage+=b.damage;hits++;b.life=0;}bullets=bullets.filter(b=>b.life>0);}}
  finally{window.shoot=originalShoot;boss=null;clean();}
  return {hero,upgrade:u,distance,radius,rate,seconds:t,damage,hits,shots,effectiveDPS:damage/t,TTK:damage>=hpTarget?t:null};
 }
 function steer(sign){document.getElementById('rotationJoystick').dispatchEvent(new KeyboardEvent('keydown',{key:sign<0?'ArrowLeft':sign>0?'ArrowRight':'Home',bubbles:true,cancelable:true}));}
 function run(hero,n,policy='opportunistic',limit=1800,encounter=null){
  begin(hero,n);if(encounter){stage=encounter.region;phase=encounter.normal?(encounter.phase||1):5;player.upgrade=encounter.upgrade;hp=encounter.lowHP?1:maxHP[hero];invuln=0;if(encounter.normal){itemMonsters.configure({opportunitiesPerRegion:0});itemMonsters.reset();}else spawnBossEncounter();if(encounter.item!=='none')items=[{x:player.x,y:player.y,type:encounter.item,life:7.25,r:13,t:0,turn:99,vx:0,vy:0}];}
  const dt=1/60;let time=0,last=null,bossRef=null,bossAt=0,deaths=0,firstDeath=null,turn=0,totals={damage:0,shots:0,blocked:0},phases=[],boundaries=[],segments=[];
  const originalShoot=shoot,originalHurt=hurt,originalBlock=blockEnemyBullet;window.shoot=function(){totals.shots++;return originalShoot()};window.hurt=function(){const before=hp;originalHurt();totals.damage+=before-hp};window.blockEnemyBullet=function(b){const out=originalBlock(b);if(out)totals.blocked++;return out};
  try{for(;time<limit;time+=dt){
   if(encounter?.normal&&(stage!==encounter.region||phase!==(encounter.phase||1)))break;
   if(encounter&&bossRef?.hp<=0)break;
   if(!started){if(gameOverPending){deaths++;firstDeath={time,stage,phase,upgrade:player.upgrade};}break;}
   const key=stage+':'+phase;
   if(last?.key!==key){if(last){last.seconds=time-last.time;last.exitUpgrade=player.upgrade;last.exitHP=hp;phases.push(last);if(last.region!==stage)boundaries.push({from:last.region,to:stage,time,upgrade:player.upgrade,hp,items:items.map(x=>({type:x.type,life:x.life})),deaths});}last={key,region:stage,phase,time,entryUpgrade:player.upgrade,entryHP:hp,maxEnemies:0,maxEnemyBullets:0};}
   last.maxEnemies=Math.max(last.maxEnemies,enemies.length);last.maxEnemyBullets=Math.max(last.maxEnemyBullets,enemyBullets.length);
   if(boss!==bossRef){if(bossRef)segments.push({region:bossRef.auditRegion,spawnTime:bossAt,defeatTime:time,bossSeconds:time-bossAt,startHP:bossRef.maxHp,upgrade:bossRef.auditUpgrade,deaths});bossRef=boss;if(boss){bossAt=time;boss.auditUpgrade=player.upgrade;boss.auditRegion=stage;if(stage===7)gameMachineBoss.prepare(boss,n^0x7639);}}
   const targets=[...enemies.filter(x=>x.hp>0),...(boss?[boss]:[])];if(policy!=='ignore')targets.push(...itemMonsters.targets());targets.sort((a,b)=>Math.hypot(a.x-player.x,a.y-player.y)-Math.hypot(b.x-player.x,b.y-player.y));
   const target=targets[0];let vx=0,vy=0;
   if(target){const dx=target.x-player.x,dy=target.y-player.y,d=Math.hypot(dx,dy)||1,wanted=Math.atan2(dy,dx)-Math.PI/2,delta=Math.atan2(Math.sin(wanted-player.a),Math.cos(wanted-player.a)),next=Math.abs(delta)<.03?0:Math.sign(delta);if(next!==turn){steer(next);turn=next;}const radial=d>235?.8:d<150?-1:0;vx=dx/d*radial-dy/d*.65;vy=dy/d*radial+dx/d*.65;}
   if(policy!=='ignore'&&items.length){const item=items.reduce((a,b)=>Math.hypot(a.x-player.x,a.y-player.y)<Math.hypot(b.x-player.x,b.y-player.y)?a:b);if(policy==='collect'||!target||Math.hypot(item.x-player.x,item.y-player.y)<150){vx=(item.x-player.x)/70;vy=(item.y-player.y)/70;}}
   for(const b of enemyBullets){const dx=player.x-b.x,dy=player.y-b.y,d=Math.hypot(dx,dy)||1;if(d<95&&dx*b.vx+dy*b.vy>0){const gain=(95-d)/25;vx+=dx/d*gain;vy+=dy/d*gain;}}
   for(const h of [gameSnowfieldBoss.snapshot()?.hazard,gameVolcanoBoss.snapshot()?.hazard])if(h){const dx=player.x-h.x,dy=player.y-h.y,d=Math.hypot(dx,dy)||1;if(d<(h.r||h.radius||64)+35){vx+=dx/d*3;vy+=dy/d*3;}}
   const m=gameMachineBoss.snapshot();if(m?.wall){vy=((m.wall.safe==='top'?28:H-28)-player.y)/25;vx=0;}
   const norm=Math.max(1,Math.hypot(vx,vy));tilt={x:vx/norm,y:vy/norm};keys.fire=!!target;update(dt);gameSnowfield.tickFinale(dt);
  }
  if(last){last.seconds=time-last.time;last.exitUpgrade=player?.upgrade;last.exitHP=hp;phases.push(last);}
  if(bossRef)segments.push({region:bossRef.auditRegion,spawnTime:bossAt,defeatTime:time,bossSeconds:time-bossAt,startHP:bossRef.maxHp,upgrade:bossRef.auditUpgrade,censored:!!boss&&boss===bossRef,deaths});
  const normalPhaseCleared=!!encounter?.normal&&(stage!==encounter.region||phase!==(encounter.phase||1));const measuredResult=encounter?gameScoring.finish('abandoned'):gameScoring.getLastResult();
  return clone({hero,seed:n,policy,continuation:false,encounter,normalPhaseCleared,encounterDefeated:!!encounter&&bossRef?.hp<=0,seconds:time,completed:!started&&!gameOverPending,timeout:time>=limit,stage,phase,hp,upgrade:player?.upgrade??gameScoring.getLastResult()?.record.finalUpgrade,deaths,firstDeath,totals,phases,boundaries,bosses:segments,result:measuredResult,itemsPlan:itemMonsters.snapshot().regions});
  }finally{window.shoot=originalShoot;window.hurt=originalHurt;window.blockEnemyBullet=originalBlock;clean();}
 }
 window.balanceAudit={definitions,assay,run,begin,clean};
})();
