"""Test-only seeded species fixtures for historical fixed-species art/combat audits.
New mixed-spawn tests do not install these helpers or alter production selection.
"""
FIXED_VOLCANO_SPECIES=r'''(()=>{
 window.vmSeedFor=(step,id)=>{for(let i=1;i<100000;i++){const seed=Math.imul(i,0x9e3779b1)>>>0;let x=seed;x^=x<<13;x^=x>>>17;x^=x<<5;if(gameVolcanoSpawns.chooseForRoll(step,(x>>>0)/4294967296)===id)return seed;}throw Error('No seed for '+id);};
 window.vmFixedPhase=()=>{if(window.gameVolcanoSpawns&&gameWorlds.region(stage)?.key==='world-2:volcano')gameVolcanoSpawns.reset(vmSeedFor(phase,gameVolcanoSpawns.ids[Math.min(3,phase-1)]));};
})();'''
