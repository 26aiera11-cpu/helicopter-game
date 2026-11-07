/* Issue26 first-playtest tuning. No snowfield/volcano or player values are shared. */
(()=>{
 'use strict';
 const freeze=rows=>Object.freeze(rows.map(Object.freeze));
 window.gameStormConfig=Object.freeze({
  key:'world-2:storm-sky',ids:Object.freeze(['cloud_bean','lightning_bat','tornado_spirit','storm_jellyfish']),
  weights:freeze([[75,25,0,0],[40,35,25,0],[20,30,35,15],[10,25,30,35],[5,25,30,40]]),
  spawnIntervals:Object.freeze([2,1.91,1.82,1.73,1.64]),spawnCaps:Object.freeze([3,4,4,5,5]),
  monsters:freeze([
   {id:'cloud_bean',hp:1,speed:43,interval:3.8,bullet:90},
   {id:'lightning_bat',hp:2,speed:50,interval:4.1,bullet:96,dash:155,warning:.5,dashTime:.75,rest:1.2},
   {id:'tornado_spirit',hp:2,speed:40,interval:3.6,bullet:87},
   {id:'storm_jellyfish',hp:3,speed:28,interval:3.2,bullet:82}
  ]),maxNormalBullets:24,perActorBullets:3,
  boss:Object.freeze({firstDelay:1.8,rest:1.9,minRest:1.5,warning:.8,secondVolley:.45,
   bulletSpeed:82,bulletLife:4,maxBullets:32,laserWarning:1,laserTime:2,laserTurn:Math.PI/12,laserWidth:10,
   windLife:5,maxWinds:3,windSpeed:34,windRadius:20,windCooldown:1.4,spinTime:.65,
   awakenTime:2,pullSpeed:22,phase2AttackRate:1.2,phase2BulletSpeed:1.1,step:1/120})
 });
})();
