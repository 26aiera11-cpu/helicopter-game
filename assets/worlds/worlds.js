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
  let developerEnabled=false, activeDeveloper=false;
  let developerStart={regionId:worlds[0].regionIds[0],phase:1};
  let activeStart={...developerStart};
  let devToggle,devWorld,devRegion,devPhase,devFields;
  const region = id => Number.isInteger(id) ? regions.find(r=>r.id===id) : undefined;
  const isTrial = () => typeof started !== 'undefined' && started ? activeTrial : trialEnabled;
  const isDeveloper=()=>typeof started!=='undefined'&&started?activeDeveloper:developerEnabled;
  function canConfigure() {
    const art=window.gameSnowfield?.snapshot().finale;
    return !(typeof started!=='undefined'&&(started||document.getElementById('menu').classList.contains('hidden'))) && !art?.active && !art?.pending;
  }
  function setDeveloperStart(options={}) {
    if(!canConfigure()||!options||typeof options!=='object')return false;
    const id=options.regionId??developerStart.regionId,step=options.phase??developerStart.phase;
    const r=region(id),on=options.enabled??developerEnabled;
    if(!r||!Number.isInteger(step)||step<1||step>r.bossPhase||typeof on!=='boolean')return false;
    developerStart={regionId:id,phase:step};developerEnabled=on;
    if(on)trialEnabled=false;
    document.dispatchEvent(new Event('worldmodechange'));syncUI();return true;
  }
  function fillRegions(worldId) {
    devRegion.replaceChildren();
    for(const r of regions.filter(r=>r.worldId===worldId)){
      const option=document.createElement('option');option.value=String(r.id);option.textContent=r.name;devRegion.append(option);
    }
  }
  function syncDeveloperUI() {
    if(!devToggle)return;
    const mutable=canConfigure(),r=region(developerStart.regionId);
    devToggle.checked=developerEnabled;devToggle.disabled=!mutable;
    devFields.hidden=!developerEnabled;devFields.disabled=!developerEnabled||!mutable;
    if(devWorld.value!==String(r.worldId)){devWorld.value=String(r.worldId);fillRegions(r.worldId);}
    devRegion.value=String(r.id);devPhase.value=String(developerStart.phase);
    checkbox.disabled=!mutable||developerEnabled;
    document.getElementById('developerStartPriority').hidden=!developerEnabled;
  }

  function setTrialEnabled(value) {
    if(!canConfigure())return false;
    if(value)developerEnabled=false;
    trialEnabled=Boolean(value);if(checkbox)checkbox.checked=trialEnabled;
    document.dispatchEvent(new Event('worldmodechange'));syncUI();return true;
  }
  function beginRun() {
    activeDeveloper=developerEnabled;activeStart=activeDeveloper?{...developerStart}:{regionId:worlds[0].regionIds[0],phase:1};
    activeTrial=!activeDeveloper&&trialEnabled;
    route=activeDeveloper?[activeStart.regionId]:activeTrial ? worlds.flatMap(w=>w.regionIds) : [...worlds[0].regionIds];
  }
  function nextRegion(id) { const index=route.indexOf(id);return index>=0 ? route[index+1] ?? null : null; }
  function regionLabel(id) { const r=region(id);return r ? `${isDeveloper()?'🧪 '+r.worldName+' · ':isTrial()?r.worldName+' · ':''}${r.name}` : '알 수 없는 지역'; }
  function recordFields(id) {
    const r=region(id);return {worldId:r.worldId,worldName:r.worldName,regionKey:r.key,localRegionIndex:r.localIndex,trialMode:isTrial()};
  }
  function recordLabel(record) {
    const r=region(record.regionId);return `${record.trialMode || r.worldId>0 ? r.worldName+' · ' : ''}${r.name}`;
  }
  function clearHeading(result) {
    return `${activeDeveloper?'🧪 지역 테스트 완료!':activeTrial?'🏁 설원 시험 완료!':'🏆 모든 지역 클리어!'} · ${result.record.characterName} · ${gameScoring.format(result.record.score)}점`;
  }
  function clearHint() { return activeDeveloper ? '선택한 지역의 테스트를 완료했어요. 테스트 점수와 분석 기록은 저장하지 않아요.' : activeTrial ? '설원 시험 구간을 완료했어요. 이후 지역은 아직 제공하지 않아요.' : '네 지역의 보스를 모두 물리쳤어! 다시 플레이하려면 헬기를 선택해.'; }
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
    syncDeveloperUI();
    if(notice)notice.hidden=!(typeof started!=='undefined' && started && region(stage)?.prototype);
  }
  function mount() {
    const help=document.getElementById('selectionHelpDialog');
    const settings=document.createElement('div');settings.id='worldTrialSettings';
    settings.innerHTML='<label><input id="worldTrialToggle" type="checkbox"> 월드 2 설원 시험 모드</label><p>기본 OFF · 사막 다음 설원 5단계를 시험합니다. 승인 그래픽·일반 몬스터 1차 전투 시험, 보스/BGM은 숲 임시값입니다. 기록은 별도 순위표에 저장합니다.</p>';
    help.querySelector('#selectionHelpClose').before(settings);checkbox=settings.querySelector('input');
    checkbox.addEventListener('change',()=>{if(!setTrialEnabled(checkbox.checked))checkbox.checked=trialEnabled;});
    const dev=document.createElement('section');dev.id='developerStartSettings';
    dev.innerHTML='<label class="developer-start-toggle"><input id="developerStartToggle" type="checkbox"> 🧪 지역 바로 시작 (개발 테스트)</label>'+
      '<p>선택 지역의 보스 처치 후 종료 · 기록 저장 안 함 · 최대 체력/강화 0</p>'+
      '<fieldset id="developerStartFields" aria-label="개발 테스트 시작 위치" hidden disabled>'+
      '<label>월드<select id="developerStartWorld" aria-label="테스트 월드"></select></label>'+
      '<label>지역<select id="developerStartRegion" aria-label="테스트 지역"></select></label>'+
      '<label>시작 단계<select id="developerStartPhase" aria-label="테스트 시작 단계"></select></label></fieldset>'+
      '<p id="developerStartPriority" hidden>개발 테스트가 켜져 있어 설원 25단계 시험은 OFF입니다.</p>';
    settings.before(dev);devToggle=dev.querySelector('input');devWorld=dev.querySelector('#developerStartWorld');
    devRegion=dev.querySelector('#developerStartRegion');devPhase=dev.querySelector('#developerStartPhase');devFields=dev.querySelector('fieldset');
    for(const w of worlds.filter(w=>regions.some(r=>r.worldId===w.id))){
      const option=document.createElement('option');option.value=String(w.id);option.textContent=w.name;devWorld.append(option);
    }
    fillRegions(region(developerStart.regionId).worldId);
    for(let step=1;step<=Math.max(...regions.map(r=>r.bossPhase));step++){
      const option=document.createElement('option');option.value=String(step);option.textContent=step+'단계'+(step===5?' · 보스 바로':'');devPhase.append(option);
    }
    devToggle.addEventListener('change',()=>{if(!setDeveloperStart({enabled:devToggle.checked}))syncUI();});
    devWorld.addEventListener('change',()=>{
      const first=regions.find(r=>r.worldId===Number(devWorld.value));
      if(first){fillRegions(first.worldId);setDeveloperStart({regionId:first.id});}syncUI();
    });
    devRegion.addEventListener('change',()=>{setDeveloperStart({regionId:Number(devRegion.value)});syncUI();});
    devPhase.addEventListener('change',()=>{setDeveloperStart({phase:Number(devPhase.value)});syncUI();});
    new MutationObserver(syncUI).observe(document.body,{attributes:true,attributeFilter:['class']});

    notice=document.createElement('p');notice.id='worldPrototypeNotice';notice.textContent='설원 시험 · 일반 적 1차 전투 / 보스·BGM 숲 임시';notice.hidden=true;document.body.append(notice);
    new MutationObserver(syncUI).observe(document.getElementById('menu'),{attributes:true,attributeFilter:['class']});syncUI();
  }
  window.gameWorlds=Object.freeze({worlds,regions,region,isTrial,setTrialEnabled,isDeveloper,setDeveloperStart,
    isDeveloperRun:()=>activeDeveloper,runStart:()=>({...activeStart}),
    developerSnapshot:()=>({enabled:developerEnabled,selected:{...developerStart},active:activeDeveloper,start:{...activeStart}}),beginRun,nextRegion,regionLabel,recordFields,recordLabel,clearHeading,clearHint,installLegacyRegions,syncUI,
    profile:id=>region(id)?.combatProfile??0,musicProfile:id=>region(id)?.musicProfile??0,
    snapshot:()=>({trialEnabled,activeTrial,route:[...route]})});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});else mount();
})();
