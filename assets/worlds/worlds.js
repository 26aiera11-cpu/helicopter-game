/* World/region registry. Snowfield is an opt-in prototype, never a default route. */
(() => {
  'use strict';
  const regions = Object.freeze([
    [0,'world-1:forest',0,0,'🌲 숲 지역',0,'🌳 숲의 수호괴물'],
    [1,'world-1:rock',0,1,'🪨 바위 지역',1,'🪨 거대 바위 골렘'],
    [2,'world-1:sea',0,2,'🌊 바다 지역',2,'🐙 바다의 문어 대왕'],
    [3,'world-1:desert',0,3,'🏜️ 사막 지역',3,'🦂 사막 전갈왕'],
    [4,'world-2:snowfield',1,0,'❄ 설원 (시험)',0,'❄ 눈보라 거인왕 (시험)','snowfield-approved']
  ].map(([id,key,worldId,localIndex,name,profile,bossName,prototypeBackground],idIndex) => Object.freeze({
    id,key,worldId,worldName:`월드 ${worldId+1}`,localIndex,name,
    combatProfile:profile,assetProfile:profile,musicProfile:profile,
    normalPhases:4,bossPhase:5,bossName,prototypeBackground,prototype:Boolean(prototypeBackground)
  })));
  const worlds = Object.freeze([...new Set(regions.map(r=>r.worldId))].map(id => Object.freeze({
    id,key:`world-${id+1}`,name:`월드 ${id+1}`,
    regionIds:Object.freeze(regions.filter(r=>r.worldId===id).map(r=>r.id))
  })));
  let trialEnabled = new URLSearchParams(location.search).get('world2') === '1';
  let activeTrial = false, route = [...worlds[0].regionIds];
  let checkbox, notice;
  const region = id => Number.isInteger(id) ? regions.find(r=>r.id===id) : undefined;
  const isTrial = () => typeof started !== 'undefined' && started ? activeTrial : trialEnabled;
  function setTrialEnabled(value) {
    if (typeof started !== 'undefined' && (started || document.getElementById('menu').classList.contains('hidden'))) return false;
    trialEnabled=Boolean(value);if(checkbox)checkbox.checked=trialEnabled;
    document.dispatchEvent(new Event('worldmodechange'));syncUI();return true;
  }
  function beginRun() {
    activeTrial=trialEnabled;
    route=activeTrial ? worlds.flatMap(w=>w.regionIds) : [...worlds[0].regionIds];
  }
  function nextRegion(id) { const index=route.indexOf(id);return index>=0 ? route[index+1] ?? null : null; }
  function regionLabel(id) { const r=region(id);return r ? `${isTrial()?r.worldName+' · ':''}${r.name}` : '알 수 없는 지역'; }
  function recordFields(id) {
    const r=region(id);return {worldId:r.worldId,worldName:r.worldName,regionKey:r.key,localRegionIndex:r.localIndex,trialMode:isTrial()};
  }
  function recordLabel(record) {
    const r=region(record.regionId);return `${record.trialMode || r.worldId>0 ? r.worldName+' · ' : ''}${r.name}`;
  }
  function clearHeading(result) {
    return `${activeTrial?'🏁 설원 시험 완료!':'🏆 모든 지역 클리어!'} · ${result.record.characterName} · ${gameScoring.format(result.record.score)}점`;
  }
  function clearHint() { return activeTrial ? '설원 시험 구간을 완료했어요. 이후 지역은 아직 제공하지 않아요.' : '네 지역의 보스를 모두 물리쳤어! 다시 플레이하려면 헬기를 선택해.'; }
  function snowImage() { return gameSnowfield.backgroundImage; }
  function installLegacyRegions(data) {
    for(const r of regions){
      if(r.id<4)continue;
      data.terrainImgs[r.id]=r.prototypeBackground==='snowfield-approved'?snowImage():data.terrainImgs[r.assetProfile];data.enemySprites[r.id]=r.prototypeBackground==='snowfield-approved'?gameSnowfield.species.filter(s=>s.id!==gameSnowfield.bossId).map(s=>s.baseImage):data.enemySprites[r.assetProfile];data.bossSprites[r.id]=r.prototypeBackground==='snowfield-approved'?gameSnowfield.species.find(s=>s.id===gameSnowfield.bossId).baseImage:data.bossSprites[r.assetProfile];
      data.tactics[r.id]=data.tactics[r.combatProfile];data.stageNames[r.id]=r.name;data.stageColors[r.id]=['#e3f3fa','#b8d9eb','#7eaaca'];
    }
  }
  function syncUI() {
    if(checkbox)checkbox.checked=trialEnabled;
    if(notice)notice.hidden=!(typeof started!=='undefined' && started && region(stage)?.prototype);
  }
  function mount() {
    const help=document.getElementById('selectionHelpDialog');
    const settings=document.createElement('div');settings.id='worldTrialSettings';
    settings.innerHTML='<label><input id="worldTrialToggle" type="checkbox"> 월드 2 설원 시험 모드</label><p>기본 OFF · 사막 다음 설원 5단계를 시험합니다. 승인 설원 그래픽과 숲 시험용 전투·음악을 사용하며 기록은 별도 순위표에 저장합니다.</p>';
    help.querySelector('#selectionHelpClose').before(settings);checkbox=settings.querySelector('input');
    checkbox.addEventListener('change',()=>{if(!setTrialEnabled(checkbox.checked))checkbox.checked=trialEnabled;});
    notice=document.createElement('p');notice.id='worldPrototypeNotice';notice.textContent='설원 시험 · 승인 그래픽 / 숲 전투·BGM 임시';notice.hidden=true;document.body.append(notice);
    new MutationObserver(syncUI).observe(document.getElementById('menu'),{attributes:true,attributeFilter:['class']});syncUI();
  }
  window.gameWorlds=Object.freeze({worlds,regions,region,isTrial,setTrialEnabled,beginRun,nextRegion,regionLabel,recordFields,recordLabel,clearHeading,clearHint,installLegacyRegions,syncUI,
    profile:id=>region(id)?.combatProfile??0,musicProfile:id=>region(id)?.musicProfile??0,
    snapshot:()=>({trialEnabled,activeTrial,route:[...route]})});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});else mount();
})();
