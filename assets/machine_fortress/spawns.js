/* Private seeded draws. No other region's RNG or global Math.random is consumed. */
(()=>{
 'use strict';
 const {ids,weights}=gameMachineConfig;let state=0x6d330725,draws=0,serial=0;
 function reset(seed){
  if(seed===undefined){const word=new Uint32Array(1);if(globalThis.crypto?.getRandomValues){crypto.getRandomValues(word);seed=word[0];}else seed=Date.now()^++serial;}
  if(!Number.isInteger(seed))throw new TypeError('Machine spawn seed must be integer');
  state=(seed>>>0)||0x6d330725;draws=0;return state;
 }
 function chooseForRoll(phase,roll){
  if(!Number.isInteger(phase)||phase<1||phase>5||!Number.isFinite(roll)||roll<0||roll>=1)throw new RangeError('Invalid Machine spawn draw');
  let sum=0;for(let i=0;i<ids.length;i++){sum+=weights[phase-1][i];if(roll*100<sum)return ids[i];}return ids.at(-1);
 }
 function select(phase){
  if(!Number.isInteger(phase)||phase<1||phase>5)throw new RangeError('Invalid Machine phase');
  state^=state<<13;state^=state>>>17;state^=state<<5;state>>>=0;draws++;return chooseForRoll(phase,state/4294967296);
 }
 window.gameMachineSpawns=Object.freeze({ids,weights,reset,select,chooseForRoll,snapshot:()=>({state,draws})});
})();
