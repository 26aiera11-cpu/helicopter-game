/* Regional tuning only. Consumers explicitly opt in; World1 keeps its engine values. */
(() => {
  'use strict';
  const regions=Object.freeze({
    'world-2:snowfield':Object.freeze({
      chaseSpeedScale:1.06,
      shotIntervalScale:.95,
      bossRest:3.0,
      spawnWeights:Object.freeze([
        [80,20,0,0],
        [45,40,15,0],
        [20,30,35,15],
        [10,20,35,35],
        [0,15,30,55]
      ].map(Object.freeze))
    })
  });
  window.gameRegionDifficulty=Object.freeze({regions,get:key=>regions[key]});
})();
