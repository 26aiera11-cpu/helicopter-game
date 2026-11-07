/* Issue33 first Galaxy trial. Only Machine Fortress normal monsters opt in. */
(()=>{
 'use strict';
 const freeze=rows=>Object.freeze(rows.map(Object.freeze));
 window.gameMachineConfig=Object.freeze({key:'world-2:machine-fortress',
  ids:Object.freeze(['screw_bot','gear_wasp','laser_drone','armored_turret']),
  weights:freeze([[75,25,0,0],[45,35,20,0],[25,25,30,20],[15,20,35,30],[10,20,35,35]]),
  monsters:freeze([
   {id:'screw_bot',hp:1,speed:46,near:110,warning:.45,dash:100,dashTime:.35,rest:2.2},
   {id:'gear_wasp',hp:1,speed:50,initial:1.2,warning:.60,dash:145,dashTime:.65,rest:2.6},
   {id:'laser_drone',hp:2,speed:30,initial:1.2,near:150,far:210,warning:.65,active:.28,width:7,length:260,rest:3.1},
   {id:'armored_turret',hp:3,speed:20,initial:1.2,warning:.45,interval:3.6,bullet:75,bulletRadius:6,bulletLife:3.4}
  ]),maxNormalBullets:24,perActorBullets:2,playerLaserRadius:12,
  step:1/300,maxDt:.25
 });
})();
