/* Issue22: independent per-actor volcano species draws; no shared RNG consumption. */
(() => {
  'use strict';
  const ids=Object.freeze(['ember_bean','lava_lizard','volcano_bat','magma_beetle']);
  const weights=gameRegionDifficulty.get('world-2:volcano').spawnWeights;
  let state=0x6d2b79f5,serial=0,draws=0;
  function reset(seed) {
    if(seed===undefined){
      if(globalThis.crypto?.getRandomValues){const word=new Uint32Array(1);crypto.getRandomValues(word);seed=word[0];}
      else seed=(Date.now()^Math.floor(performance.now()*1000)^++serial)>>>0;
    }
    if(!Number.isInteger(seed))throw new TypeError('Volcano spawn seed must be an integer');
    state=(seed>>>0)||0x6d2b79f5;draws=0;return state;
  }
  function chooseForRoll(phase,roll) {
    if(!Number.isInteger(phase)||phase<1||phase>weights.length||!Number.isFinite(roll)||roll<0||roll>=1)throw new RangeError('Invalid volcano spawn draw');
    let cumulative=0;
    for(let i=0;i<ids.length;i++){cumulative+=weights[phase-1][i];if(roll*100<cumulative)return ids[i];}
    return ids[ids.length-1];
  }
  function select(phase) {
    if(!Number.isInteger(phase)||phase<1||phase>weights.length)throw new RangeError('Invalid volcano phase');
    state^=state<<13;state^=state>>>17;state^=state<<5;state>>>=0;draws++;
    return chooseForRoll(phase,state/4294967296);
  }
  window.gameVolcanoSpawns=Object.freeze({ids,weights,reset,chooseForRoll,select,snapshot:()=>({state,draws})});
})();
