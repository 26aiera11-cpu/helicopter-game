/* Issue31: original single-pose PNGs + display-only transforms. No combat AI. */
(()=>{
 'use strict';
 const manifest=JSON.parse(document.getElementById('machineFortressManifest').content.textContent);
 const backgroundImage=document.getElementById('machineFortressBackground');
 const normalIds=Object.freeze(['screw_bot','gear_wasp','laser_drone','armored_turret']),bossId='giga_core';
 const images=new Map(manifest.files.map(row=>[row.path,document.getElementById('machine-'+row.path.replace(/\.png$/,'').replaceAll('/','-'))]));
 const species=Object.freeze([...normalIds.map(id=>({id,path:'enemies/'+id+'.png',renderWidth:40})),{id:bossId,path:'boss/giga_core_normal.png',renderWidth:132}].map(row=>Object.freeze({...row,baseImage:images.get(row.path)})));
 const byId=new Map(species.map(row=>[row.id,row]));
 const durations=Object.freeze({idle:1.2,move:.7,attack:.28,hit:.18,defeat:.65});
 let clock=0,states=new WeakMap(),ghosts=[],pending=null;
 const enabled=()=>typeof stage!=='undefined'&&gameWorlds.region(stage)?.key==='world-2:machine-fortress';
 const loaded=image=>image?.complete&&image.naturalWidth>0;
 function track(actor,isBoss=false){
  let state=states.get(actor);
  if(!state){state={id:isBoss?bossId:actor.machineSpeciesId||normalIds[(actor.kind??0)%normalIds.length],x:actor.x,y:actor.y,base:'idle',at:clock,attack:-Infinity,hit:-Infinity,dead:false};states.set(actor,state);}
  return state;
 }
 function tick(dt){if(enabled()&&!document.hidden&&!window.gameExitDialogOpen){clock+=dt;ghosts=ghosts.filter(g=>clock-g.at<durations.defeat);}}
 function observe(actors,king){
  if(!enabled())return;
  for(const actor of [...actors,...(king?[king]:[])]){
   const s=track(actor,actor===king),mode=Math.hypot(actor.x-s.x,actor.y-s.y)>.001?'move':'idle';
   if(s.base!==mode){s.base=mode;s.at=clock;}s.x=actor.x;s.y=actor.y;
  }
 }
 function attack(actor,isBoss=false){if(enabled()&&actor)track(actor,isBoss).attack=clock;}
 function hit(actor,isBoss=false){
  if(!enabled()||!actor)return;const s=track(actor,isBoss);if(s.dead)return;s.hit=clock;
  if(actor.hp<=0){s.dead=true;ghosts.push({id:s.id,x:actor.x,y:actor.y,at:clock});}
 }
 function frame(name,elapsed){
  const t=Math.max(0,elapsed),p=Math.min(1,t/durations[name]);
  if(name==='defeat')return {name,scale:1+.12*p,rotation:.06*Math.sin(p*Math.PI*3),alpha:1-p,offsetX:0};
  if(name==='hit')return {name,scale:1.025,rotation:0,alpha:.55+.45*Math.abs(Math.cos(t*48)),offsetX:Math.sin(t*85)*1.2};
  if(name==='attack')return {name,scale:1+.018*Math.sin(p*Math.PI),rotation:0,alpha:1,offsetX:0};
  return {name,scale:1+.012*Math.sin(t*Math.PI*2/durations[name]),rotation:(name==='move'?.025:.01)*Math.sin(t*7),alpha:1,offsetX:0};
 }
 function pose(actor,isBoss=false){
  const s=track(actor,isBoss),name=clock-s.hit<durations.hit?'hit':clock-s.attack<durations.attack?'attack':s.base;
  return {id:s.id,...frame(name,clock-(name==='hit'?s.hit:name==='attack'?s.attack:s.at))};
 }
 function geometry(image,point,width,selected){
  const scale=width/image.naturalWidth;
  return {cx:point.x+selected.offsetX,cy:point.y,scale,width,height:image.naturalHeight*scale,pivot:[image.naturalWidth/2,image.naturalHeight/2]};
 }
 function paint(ctx,spec,point,selected){
  const image=spec.baseImage;if(!loaded(image))return;
  const g=geometry(image,point,spec.renderWidth,selected);
  ctx.save();ctx.translate(g.cx,g.cy);ctx.rotate(selected.rotation);ctx.scale(selected.scale,selected.scale);ctx.globalAlpha=selected.alpha;
  ctx.drawImage(image,0,0,image.naturalWidth,image.naturalHeight,-g.width/2,-g.height/2,g.width,g.height);ctx.restore();
 }
 function drawActor(ctx,actor,isBoss=false){if(!enabled())return false;const p=pose(actor,isBoss);paint(ctx,byId.get(p.id),actor,p);return true;}
 function drawDefeats(ctx){if(enabled())for(const ghost of ghosts)paint(ctx,byId.get(ghost.id),ghost,frame('defeat',clock-ghost.at));}
 function drawBackground(ctx,w,h){
  if(!enabled())return false;ctx.fillStyle='#252c36';ctx.fillRect(0,0,w,h);
  if(loaded(backgroundImage)){const scale=Math.min(w/backgroundImage.naturalWidth,h/backgroundImage.naturalHeight),dw=backgroundImage.naturalWidth*scale,dh=backgroundImage.naturalHeight*scale;ctx.drawImage(backgroundImage,(w-dw)/2,(h-dh)/2,dw,dh);}
  return true;
 }
 function deferAdvance(callback){if(!enabled()||!ghosts.length)return false;pending=callback;return true;}
 function tickAdvance(dt){if(!pending)return false;if(document.hidden||window.gameExitDialogOpen)return true;tick(dt);if(!ghosts.length){const callback=pending;pending=null;reset();callback();}return true;}
 function reset(){clock=0;states=new WeakMap();ghosts=[];pending=null;}
 // Explicit graphics-only inspection: never called by combat, HP or movement code.
 function preview(ctx,path,x,y,width=132){const image=images.get(path);if(!loaded(image))return false;paint(ctx,{baseImage:image,renderWidth:width},{x,y},frame('idle',0));return true;}
 window.gameMachineFortress=Object.freeze({manifest,species,normalIds,bossId,backgroundImage,overdriveImage:images.get('boss/giga_core_overdrive.png'),durations,enabled,tick,observe,attack,hit,frame,pose,geometry,paint,drawActor,drawDefeats,drawBackground,deferAdvance,tickAdvance,reset,preview,
  ready:()=>loaded(backgroundImage)&&[...images.values()].every(loaded),snapshot:()=>({clock,ghosts:ghosts.map(g=>({...g})),advancing:Boolean(pending),combat:'machine normal trial / legacy boss profile0',overdriveCombat:false,wallCombat:false})});
})();
