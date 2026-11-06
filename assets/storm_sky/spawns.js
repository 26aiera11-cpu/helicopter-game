/* Independent seeded species selection; existing region RNG streams are untouched. */
(()=>{
 'use strict';
 const {ids,weights}=gameStormConfig;let state=0x73027a31,draws=0,serial=0;
 function reset(seed){
  if(seed===undefined){const n=new Uint32Array(1);if(globalThis.crypto?.getRandomValues){crypto.getRandomValues(n);seed=n[0];}else seed=Date.now()^++serial;}
  if(!Number.isInteger(seed))throw new TypeError('Storm seed must be integer');state=(seed>>>0)||0x73027a31;draws=0;return state;
 }
 function chooseForRoll(phase,roll){
  if(!Number.isInteger(phase)||phase<1||phase>5||!Number.isFinite(roll)||roll<0||roll>=1)throw new RangeError('Invalid storm spawn draw');
  let sum=0;for(let i=0;i<ids.length;i++){sum+=weights[phase-1][i];if(roll*100<sum)return ids[i];}return ids.at(-1);
 }
 function select(phase){if(!Number.isInteger(phase)||phase<1||phase>5)throw new RangeError('Invalid storm phase');state^=state<<13;state^=state>>>17;state^=state<<5;state>>>=0;draws++;return chooseForRoll(phase,state/4294967296);}
 window.gameStormSpawns=Object.freeze({ids,weights,reset,select,chooseForRoll,snapshot:()=>({state,draws})});
})();
