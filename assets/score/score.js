/* Local scoring and result storage. Combat and progression stay in index.html. */
(() => {
  'use strict';
  const VERSION = 1;
  const HISTORY_LIMIT = 100;
  const normalKeys = Object.freeze({ top: 'heliTrio.top10.v1', history: 'heliTrio.playHistory.v1' });
  const trialKeys = Object.freeze({ top: 'heliTrio.world2Trial.top10.v1', history: 'heliTrio.world2Trial.playHistory.v1' });
  let storageKeys = normalKeys, scope = 'normal';
  const stores = new Map();
  const names = ['뾰코', '빙글', '탱코'];
  const number = new Intl.NumberFormat('en-US');
  const format = value => number.format(value);
  let storageMessage = '';
  let serial = 0;
  let activeRun = null;
  let lastResult = null;

  function validRecord(record) {
    return record && typeof record.id === 'string' && record.id.length > 0 && record.id.length < 160 &&
      Number.isSafeInteger(record.score) && record.score >= 0 &&
      Number.isInteger(record.characterId) && record.characterId >= 0 && record.characterId < 3 &&
      Boolean(gameWorlds.region(record.regionId)) && (scope === 'trial' || gameWorlds.region(record.regionId).worldId === 0) &&
      Number.isInteger(record.phase) && record.phase >= 1 && record.phase <= 5 &&
      Number.isSafeInteger(record.order) && record.order > 0 &&
      typeof record.createdAt === 'string' && Number.isFinite(Date.parse(record.createdAt)) &&
      ['game_over', 'clear', 'abandoned'].includes(record.outcome) &&
      ['normalKills', 'itemKills', 'bossKills', 'clearedPhases'].every(key =>
        Number.isSafeInteger(record[key]) && record[key] >= 0) &&
      Number.isFinite(record.playTimeSeconds) && record.playTimeSeconds >= 0 &&
      Number.isInteger(record.finalUpgrade) && record.finalUpgrade >= 0 && record.finalUpgrade <= 5;
  }
  function read(key) {
    let raw;
    try {
      raw = localStorage.getItem(key);
    } catch (error) {
      storageMessage = '기록 저장을 사용할 수 없어 이번 실행 동안만 기록을 표시합니다.';
      return [];
    }
    if (raw === null) return [];
    try {
      const data = JSON.parse(raw);
      if (data.version !== VERSION || !Array.isArray(data.records)) throw new Error('Invalid record version');
      const records = data.records.filter(validRecord).map(record => ({
        id: record.id, score: record.score, characterId: record.characterId,
        characterName: names[record.characterId], regionId: record.regionId,
        regionName: typeof record.regionName === 'string' ? record.regionName : stageNames[record.regionId], worldId: gameWorlds.region(record.regionId).worldId, worldName: gameWorlds.region(record.regionId).worldName,
        regionKey: gameWorlds.region(record.regionId).key, localRegionIndex: gameWorlds.region(record.regionId).localIndex, trialMode: scope === 'trial', phase: record.phase, order: record.order,
        createdAt: record.createdAt, outcome: record.outcome, normalKills: record.normalKills,
        itemKills: record.itemKills, bossKills: record.bossKills, clearedPhases: record.clearedPhases,
        playTimeSeconds: record.playTimeSeconds, finalUpgrade: record.finalUpgrade
      }));
      if (records.length !== data.records.length) storageMessage = '일부 저장 기록을 읽을 수 없어 정상 기록만 표시합니다.';
      return records;
    } catch (error) {
      storageMessage = '저장된 기록을 읽을 수 없어 새 기록부터 표시합니다.';
      return [];
    }
  }
  function write(key, records) {
    try {
      localStorage.setItem(key, JSON.stringify({ version: VERSION, records }));
      return true;
    } catch (error) {
      storageMessage = '기록 저장을 사용할 수 없어 이번 실행 동안만 기록을 표시합니다.';
      return false;
    }
  }
  const unique = records => [...new Map(records.map(record => [record.id, record])).values()];
  const ranked = records => unique(records).filter(record => record.outcome !== 'abandoned')
    .sort((a, b) => b.score - a.score || a.order - b.order || a.createdAt.localeCompare(b.createdAt) || a.id.localeCompare(b.id)).slice(0, 10);
  const recent = records => unique(records).sort((a, b) => a.order - b.order).slice(-HISTORY_LIMIT);
  let top = ranked(read(storageKeys.top));
  let history = recent(read(storageKeys.history));
  function selectStorage() {
    const next = gameWorlds.isTrial() ? 'trial' : 'normal';
    if (scope === next) return;
    stores.set(scope, { top, history, storageMessage, lastResult });
    scope = next;storageKeys = next === 'trial' ? trialKeys : normalKeys;storageMessage = '';
    const cached = stores.get(next);
    if (cached) ({ top, history, storageMessage, lastResult } = cached);
    else { top = ranked(read(storageKeys.top));history = recent(read(storageKeys.history));lastResult = null; }
  }
  function refresh() {
    top = ranked([...read(storageKeys.top), ...top]);
    history = recent([...read(storageKeys.history), ...history]);
  }
  function newId() {
    if (globalThis.crypto?.randomUUID) return crypto.randomUUID();
    const entropy = new Uint32Array(2);
    globalThis.crypto?.getRandomValues?.(entropy);
    return `${Date.now().toString(36)}-${entropy[0].toString(36)}-${entropy[1].toString(36)}-${++serial}`;
  }
  function updateHUD() {
    if (!player) return;
    gameWorlds.syncUI();
    hud.textContent = `${gameWorlds.regionLabel(stage)} · ${phase}/5　🏆 ${format(runScore)}　❤️ ${Math.max(0, hp)}/${maxHP[player.type]}　⚡ ${player.upgrade}/5`;
  }
  function add(points) {
    runScore = Math.min(Number.MAX_SAFE_INTEGER, runScore + points);
    updateHUD();
  }
  function startRun(type) {
    if (activeRun && !activeRun.result) finish('abandoned');
    gameWorlds.beginRun();selectStorage();
    activeRun = {
      id: newId(), characterId: type, developerTest: gameWorlds.isDeveloperRun(), normalKills: 0, itemKills: 0, bossKills: 0,
      clearedPhases: new Set(), enemies: new WeakSet(), bosses: new WeakSet(), playTimeSeconds: 0, result: null
    };
    updateHUD();
  }
  function enemyDefeated(enemy) {
    if (!activeRun || activeRun.result || enemy.hp > 0 || activeRun.enemies.has(enemy)) return false;
    activeRun.enemies.add(enemy);
    activeRun[enemy.special ? 'itemKills' : 'normalKills']++;
    add(enemy.special ? 200 : 100);
    return true;
  }
  function bossDefeated(defeatedBoss) {
    if (!activeRun || activeRun.result || defeatedBoss.hp > 0 || activeRun.bosses.has(defeatedBoss)) return;
    activeRun.bosses.add(defeatedBoss);
    activeRun.bossKills++;
    add(2000);
  }
  function phaseCleared(region, step) {
    if (!activeRun || activeRun.result || step < 1 || step > 4) return;
    const key = `${region}:${step}`;
    if (activeRun.clearedPhases.has(key)) return;
    activeRun.clearedPhases.add(key);
    add(500);
  }
  function tick(dt) {
    if (activeRun && !activeRun.result) activeRun.playTimeSeconds += dt;
  }
  function finish(outcome) {
    if (!activeRun) return null;
    if (activeRun.result) return activeRun.result;
    if(!activeRun.developerTest)refresh();
    const record = {
      id: activeRun.id, score: runScore, characterId: activeRun.characterId,
      characterName: names[activeRun.characterId], regionId: stage, regionName: stageNames[stage], ...gameWorlds.recordFields(stage), phase,
      order: activeRun.developerTest ? 0 : Math.max(0, ...top.map(row => row.order), ...history.map(row => row.order)) + 1,
      createdAt: new Date().toISOString(), outcome, normalKills: activeRun.normalKills,
      itemKills: activeRun.itemKills, bossKills: activeRun.bossKills, clearedPhases: activeRun.clearedPhases.size,
      playTimeSeconds: Math.round(activeRun.playTimeSeconds * 1000) / 1000, finalUpgrade: player.upgrade
    };
    if(activeRun.developerTest){
      record.developerTest=true;
      activeRun.result={record,rank:0,isTop10:false,saved:false,developerTest:true};
      return activeRun.result;
    }
    history = recent([...history, record]);
    if (outcome !== 'abandoned') top = ranked([...top, record]);
    const rank = top.findIndex(row => row.id === record.id) + 1;
    const topSaved = write(storageKeys.top, top);
    const historySaved = write(storageKeys.history, history);
    if (topSaved && historySaved) storageMessage = '';
    lastResult = activeRun.result = { record, rank, isTop10: rank > 0, saved: topSaved && historySaved };
    return activeRun.result;
  }

  const dialog = document.createElement('dialog');
  dialog.id = 'leaderboardDialog';
  dialog.setAttribute('aria-labelledby', 'leaderboardTitle');
  dialog.innerHTML = '<header><div><h2 id="leaderboardTitle">🏆 TOP 10</h2><p>세 헬기의 통합 점수 순위표</p></div>' +
    '<button id="leaderboardClose" type="button" autofocus>닫기</button></header>' +
    '<div class="leaderboard-scroll" tabindex="0" role="region" aria-label="TOP 10 기록 목록">' +
    '<table><thead><tr><th scope="col">순위</th><th scope="col">캐릭터</th><th scope="col">점수</th>' +
    '<th scope="col">도달 지역</th><th scope="col">기록 날짜</th></tr></thead><tbody id="leaderboardRows"></tbody></table>' +
    '<p id="leaderboardEmpty">아직 기록이 없습니다</p></div>' +
    '<p id="leaderboardStorage" role="status"></p><p class="leaderboard-note">이 브라우저에 저장된 기록 · 중도 종료는 순위에서 제외</p>';
  document.body.append(dialog);
  function render() {
    selectStorage();refresh();
    dialog.querySelector('#leaderboardTitle').textContent = scope === 'trial' ? '🏆 40단계 TOP 10' : '🏆 TOP 10';
    dialog.querySelector('.leaderboard-note').textContent = scope === 'trial' ? '40단계 기록 · 20단계 기록과 별도 저장 · 중도 종료 제외' : '이 브라우저에 저장된 기록 · 중도 종료는 순위에서 제외';
    const rows = dialog.querySelector('#leaderboardRows');
    rows.replaceChildren();
    top.forEach((record, index) => {
      const row = document.createElement('tr');
      row.dataset.recordId = record.id;
      row.dataset.character = record.characterId;
      if (lastResult?.isTop10 && lastResult.record.id === record.id) {
        row.classList.add('latest-record');
        row.setAttribute('aria-label', '방금 달성한 TOP 10 기록');
      }
      const values = [String(index + 1), record.characterName, format(record.score),
        `${gameWorlds.recordLabel(record)} · ${record.phase}/5`, new Date(record.createdAt).toLocaleString('ko-KR', {
          year: '2-digit', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false
        })];
      values.forEach((value, column) => {
        const cell = document.createElement('td');
        if (column === 1) {
          const icon = document.createElement('img');
          icon.src = document.querySelector(`#heliStage${record.characterId} .heli-body image`).getAttribute('href');
          icon.alt = '';
          cell.append(icon);
          cell.className = 'leaderboard-character';
        }
        cell.append(document.createTextNode(value));
        row.append(cell);
      });
      rows.append(row);
    });
    dialog.querySelector('#leaderboardEmpty').hidden = top.length > 0;
    dialog.querySelector('table').hidden = top.length === 0;
    dialog.querySelector('#leaderboardStorage').textContent = storageMessage;
  }
  const button = document.getElementById('selectionSettings');
  button.addEventListener('click', () => {
    if (started || menu.classList.contains('hidden') || dialog.open) return;
    render();
    dialog.querySelector('.leaderboard-scroll').scrollTop = 0;
    dialog.showModal();
  });
  dialog.querySelector('#leaderboardClose').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => {
    if (!menu.classList.contains('hidden')) button.focus({ preventScroll: true });
  });
  new MutationObserver(() => {
    if (menu.classList.contains('hidden') && dialog.open) dialog.close();
  }).observe(menu, { attributes: true, attributeFilter: ['class'] });
  document.addEventListener('worldmodechange', () => { selectStorage();if (dialog.open) render(); });
  addEventListener('storage', event => {
    if (Object.values(storageKeys).includes(event.key) && dialog.open) render();
  });
  window.gameScoring = Object.freeze({
    start: startRun, enemyDefeated, bossDefeated, phaseCleared, tick, finish, format, updateHUD,
    getTop: () => { selectStorage();refresh(); return top.map(row => ({ ...row })); },
    getHistory: () => { selectStorage();refresh(); return history.map(row => ({ ...row })); },
    getLastResult: () => activeRun?.developerTest ? activeRun.result : lastResult, get storageKeys() { selectStorage();return storageKeys; }
  });
})();
