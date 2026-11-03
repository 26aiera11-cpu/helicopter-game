/* Issue #10: independent, per-actor snow species draw. Never consumes Math.random. */
(() => {
  'use strict';
  const ids=Object.freeze(['snow_slime','penguin_raider','ice_yeti','frost_turtle']);
  const weights=Object.freeze([[80,20,0,0],[50,40,10,0],[25,30,35,10],[10,25,35,30],[0,20,30,50]].map(Object.freeze));
  let state=0x6d2b79f5,serial=0;
  function reset(seed) {
    if(seed===undefined){
      if(globalThis.crypto?.getRandomValues){const word=new Uint32Array(1);crypto.getRandomValues(word);seed=word[0];}
      else seed=(Date.now()^Math.floor(performance.now()*1000)^++serial)>>>0;
    }
    if(!Number.isInteger(seed))throw new TypeError('Snow spawn seed must be an integer');
    state=(seed>>>0)||0x6d2b79f5;return state;
  }
  function chooseForRoll(step,roll) {
    if(!Number.isInteger(step)||step<1||step>weights.length||!Number.isFinite(roll)||roll<0||roll>=1)throw new RangeError('Invalid snow spawn draw');
    let cumulative=0;
    for(let i=0;i<ids.length;i++){cumulative+=weights[step-1][i];if(roll*100<cumulative)return ids[i];}
    return ids[ids.length-1];
  }
  function select(step) {
    state^=state<<13;state^=state>>>17;state^=state<<5;state>>>=0;
    return chooseForRoll(step,state/4294967296);
  }
  window.gameSnowfieldSpawns=Object.freeze({ids,weights,reset,chooseForRoll,select,snapshot:()=>({state})});
})();
