/* Approved Storm Sky art. Every animation frame uses its manifest rect and pivot. */
(()=>{
 'use strict';
 const manifest=JSON.parse(document.getElementById('stormSkyManifest').content.textContent),backgroundImage=document.getElementById('stormSkyBackground');
 const species=Object.freeze(manifest.monsters.map(s=>Object.freeze({...s,baseImage:document.getElementById('storm-'+s.id)})));
 const byId=new Map(species.map(s=>[s.id,s])),bossId='storm_overlord',normalIds=gameStormConfig.ids;
 let clock=0,states=new WeakMap(),ghosts=[],pending=null;
 const enabled=()=>typeof stage!=='undefined'&&gameWorlds.region(stage)?.key===gameStormConfig.key;
 const loaded=im=>im?.complete&&im.naturalWidth>0;
 const duration=(s,name)=>s.animations[name].frames.length*s.animations[name].frame_duration_ms/1000;
 function prepare(actor){if(enabled()&&actor&&!actor.special&&!normalIds.includes(actor.stormSpeciesId))Object.defineProperty(actor,'stormSpeciesId',{value:gameStormSpawns.select(phase),enumerable:true});return actor;}
 function track(actor,isBoss=false){let s=states.get(actor);if(!s){s={id:isBoss?bossId:actor.stormSpeciesId||normalIds[0],x:actor.x,y:actor.y,base:'idle',at:clock,attack:-Infinity,hit:-Infinity,dead:false};states.set(actor,s);}return s;}
 function tick(dt){if(enabled()&&!document.hidden&&!window.gameExitDialogOpen){clock+=dt;ghosts=ghosts.filter(g=>clock-g.at<duration(byId.get(g.id),'defeat'));}}
 function observe(actors,king){if(!enabled())return;for(const a of [...actors,...(king?[king]:[])]){const s=track(a,a===king),mode=Math.hypot(a.x-s.x,a.y-s.y)>.001?'move':'idle';if(s.base!==mode){s.base=mode;s.at=clock;}s.x=a.x;s.y=a.y;}}
 function attack(a,isBoss=false){if(enabled()&&a)track(a,isBoss).attack=clock;}
 function hit(a,isBoss=false){if(!enabled()||!a)return;const s=track(a,isBoss);if(s.dead)return;s.hit=clock;if(a.hp<=0){s.dead=true;ghosts.push({id:s.id,x:a.x,y:a.y,at:clock});}}
 function frame(spec,name,elapsed){const anim=spec.animations[name],step=Math.floor((Math.max(0,elapsed)+1e-9)*1000/anim.frame_duration_ms),index=anim.loop?step%anim.frames.length:Math.min(step,anim.frames.length-1);return {name,index,...anim.frames[index]};}
 function pose(actor,isBoss=false){const s=track(actor,isBoss),spec=byId.get(s.id),name=clock-s.hit<duration(spec,'hit')?'hit':clock-s.attack<duration(spec,'attack')?'attack':s.base;return {id:s.id,...frame(spec,name,clock-(name==='hit'?s.hit:name==='attack'?s.attack:s.at))};}
 function geometry(spec,point,selected){const [x,y,r,b]=spec.content_bounds_px,scale=spec.render_width/(r-x),[px,py]=selected.pivot_px;
  const margin=spec.render_width*.57;const cx=Math.max(margin,Math.min(W-margin,point.x)),cy=Math.max((py-y)*scale+4,Math.min(H-(b-py)*scale-4,point.y));
  return {cx,cy,scale,x:(x-px)*scale,y:(y-py)*scale,w:(r-x)*scale,h:(b-y)*scale};}
 function paint(ctx,spec,point,selected){if(!loaded(spec.baseImage))return;const g=geometry(spec,point,selected),[sx,sy,sw,sh]=selected.rect_px,[px,py]=selected.pivot_px;
  ctx.save();ctx.translate(g.cx,g.cy);ctx.rotate(selected.rotation);ctx.scale(selected.scale,selected.scale);ctx.globalAlpha=selected.alpha;
  ctx.drawImage(spec.baseImage,sx,sy,sw,sh,-px*g.scale,-py*g.scale,sw*g.scale,sh*g.scale);ctx.restore();}
 function drawActor(ctx,a,isBoss=false){if(!enabled())return false;const p=pose(a,isBoss);paint(ctx,byId.get(p.id),a,p);return true;}
 function drawDefeats(ctx){if(enabled())for(const g of ghosts)paint(ctx,byId.get(g.id),g,frame(byId.get(g.id),'defeat',clock-g.at));}
 function drawBackground(ctx,w,h){if(!enabled())return false;ctx.fillStyle='#10213e';ctx.fillRect(0,0,w,h);if(loaded(backgroundImage)){const scale=Math.max(w/backgroundImage.naturalWidth,h/backgroundImage.naturalHeight),dw=backgroundImage.naturalWidth*scale,dh=backgroundImage.naturalHeight*scale;ctx.drawImage(backgroundImage,(w-dw)/2,(h-dh)/2,dw,dh);}return true;}
 function deferAdvance(callback){if(!enabled()||!ghosts.length)return false;pending=callback;return true;}
 function tickAdvance(dt){if(!pending)return false;if(document.hidden||window.gameExitDialogOpen)return true;tick(dt);if(!ghosts.length){const fn=pending;pending=null;reset();fn();}return true;}
 function reset(){clock=0;states=new WeakMap();ghosts=[];pending=null;}
 window.gameStormSky=Object.freeze({manifest,species,normalIds,bossId,backgroundImage,enabled,prepare,tick,observe,attack,hit,pose,frame,geometry,paint,drawActor,drawDefeats,drawBackground,deferAdvance,tickAdvance,reset,ready:()=>loaded(backgroundImage)&&species.every(s=>loaded(s.baseImage)),snapshot:()=>({clock,ghosts:ghosts.map(g=>({...g})),advancing:Boolean(pending)})});
})();
