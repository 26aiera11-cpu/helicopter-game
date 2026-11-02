/* Independent item helicopters. Spawn cadence remains a provisional legacy policy. */
(() => {
  'use strict';
  const atlas = document.getElementById('itemMonsterAtlas');
  // Coordinates, anchors and timing are from the supplied, unmodified manifest.
  const groups = Object.freeze({
    idle: { row: 0, column: 0, count: 6, duration: .115 },
    move: { row: 1, column: 0, count: 6, duration: .105 },
    directions: { row: 2, column: 0, count: 8, duration: .12 },
    hit: { row: 3, column: 0, count: 3, duration: .095 },
    explosion: { row: 3, column: 3, count: 4, duration: .095 }
  });
  const legacyInterval = () => Math.max(.72, tactics[stage].spawn - (phase - 1) * .09);
  const legacyCapacity = () => Math.min(7, 3 + stage + Math.floor(phase / 2));
  const legacyProbability = .22;
  let settings = { intervalSeconds: null, probability: legacyProbability, maxActive: null,
    allowDuringBoss: false, stageRules: {} };
  let monsters = [], entrances = [], bursts = [], countdown = 0;
  let randomState = 1;
  function seed() {
    const word = new Uint32Array(1);
    globalThis.crypto?.getRandomValues?.(word);
    randomState = word[0] || (Date.now() >>> 0) || 1;
  }
  // Item movement/spawn draws do not consume the normal enemies/boss reward RNG.
  function random() {
    randomState ^= randomState << 13; randomState ^= randomState >>> 17; randomState ^= randomState << 5;
    return (randomState >>> 0) / 4294967296;
  }
  function rule() {
    const local = settings.stageRules[stage] || {};
    return { enabled: local.enabled !== false,
      intervalSeconds: local.intervalSeconds ?? settings.intervalSeconds ?? legacyInterval(),
      probability: local.probability ?? settings.probability,
      maxActive: local.maxActive ?? settings.maxActive ?? legacyCapacity(),
      allowDuringBoss: local.allowDuringBoss ?? settings.allowDuringBoss };
  }
  function ready() { return Boolean(atlas?.complete && atlas.naturalWidth === 2560 && atlas.naturalHeight === 1280); }
  function configure(patch) {
    const candidate = { ...settings, ...patch, stageRules: { ...settings.stageRules, ...patch.stageRules } };
    function validate(value) {
      if (value.intervalSeconds != null && (!Number.isFinite(value.intervalSeconds) || value.intervalSeconds <= 0)) throw new RangeError('Invalid item interval');
      if (value.probability != null && (!Number.isFinite(value.probability) || value.probability < 0 || value.probability > 1)) throw new RangeError('Invalid item probability');
      if (value.maxActive != null && (!Number.isInteger(value.maxActive) || value.maxActive < 0)) throw new RangeError('Invalid item capacity');
    }
    validate(candidate);
    for (const [key, value] of Object.entries(candidate.stageRules)) {
      if (!['0', '1', '2', '3'].includes(key) || !value || typeof value !== 'object') throw new RangeError('Invalid item stage rule');
      validate(value);
    }
    settings = candidate;
  }
  function reset() { monsters = []; entrances = []; bursts = []; countdown = 0; seed(); }
  function edge() {
    const side = Math.floor(random() * 4), pad = 27;
    return { x: side === 0 ? pad : side === 1 ? W - pad : pad + random() * (W - 2 * pad),
      y: side === 2 ? pad : side === 3 ? H - pad : pad + random() * (H - 2 * pad), time: 1.4 };
  }
  function spawn(position) {
    const policy = rule();
    if (!started || !ready() || !policy.enabled || (boss && !policy.allowDuringBoss) || monsters.length + entrances.length >= policy.maxActive) return null;
    const point = position || edge();
    const monster = { x: point.x, y: point.y, r: 16, hp: 5, special: true,
      life: 10, t: 0, turn: 0, vx: 0, vy: 0, angle: -Math.PI / 2,
      idleLeft: groups.idle.count * groups.idle.duration, hitLeft: 0, turnLeft: 0 };
    monsters.push(monster);
    return monster;
  }
  function bossPolicy() {
    if (boss && !rule().allowDuringBoss) { monsters = []; entrances = []; return false; }
    return true;
  }
  function update(dt) {
    if (!started || window.gameExitDialogOpen) return;
    const policy = rule();
    if (!bossPolicy()) return;
    countdown = Math.max(0, countdown - dt);
    if (policy.enabled && ready() && transition <= 0 && countdown <= 0 && monsters.length + entrances.length < policy.maxActive) {
      countdown = policy.intervalSeconds;
      if (random() < policy.probability) entrances.push(edge());
    }
    for (const entry of entrances) entry.time -= dt;
    const arriving = entrances.filter(entry => entry.time <= 0);
    entrances = entrances.filter(entry => entry.time > 0);
    for (const entry of arriving) spawn(entry);
    for (const monster of monsters) {
      monster.t += dt; monster.life -= dt; monster.turn -= dt;
      monster.hitLeft = Math.max(0, monster.hitLeft - dt);
      monster.turnLeft = Math.max(0, monster.turnLeft - dt);
      monster.idleLeft = Math.max(0, monster.idleLeft - dt);
      if (monster.life <= 0) continue;
      if (monster.turn <= 0) {
        const angle = random() * Math.PI * 2;
        monster.vx = Math.cos(angle); monster.vy = Math.sin(angle);
        monster.turn = .4 + random() * .85;
      }
      const dx = monster.x - player.x, dy = monster.y - player.y, distance = Math.hypot(dx, dy);
      const fleeing = distance < 125;
      const awayX = distance > .001 ? dx / distance : Math.cos(monster.angle);
      const awayY = distance > .001 ? dy / distance : Math.sin(monster.angle);
      const blend = fleeing ? .65 : 0;
      let vx = fleeing || monster.idleLeft <= 0 ? ((1 - blend) * monster.vx + blend * awayX) : 0;
      let vy = fleeing || monster.idleLeft <= 0 ? ((1 - blend) * monster.vy + blend * awayY) : 0;
      if (vx || vy) {
        const angle = Math.atan2(vy, vx);
        if (Math.abs(Math.atan2(Math.sin(angle - monster.angle), Math.cos(angle - monster.angle))) > Math.PI / 8) monster.turnLeft = groups.directions.duration;
        monster.angle = angle;
      }
      const speed = 45 + stage * 8;
      monster.x += vx * speed * dt; monster.y += vy * speed * dt;
      if (monster.x < 18 || monster.x > W - 18) monster.vx *= -1;
      if (monster.y < 18 || monster.y > H - 18) monster.vy *= -1;
      monster.x = Math.max(18, Math.min(W - 18, monster.x));
      monster.y = Math.max(18, Math.min(H - 18, monster.y));
      monster.moving = Boolean(vx || vy);
    }
    monsters = monsters.filter(monster => monster.life > 0 && monster.hp > 0);
    for (const burst of bursts) burst.t += dt;
    bursts = bursts.filter(burst => burst.t < groups.explosion.count * groups.explosion.duration);
  }
  function collide() {
    if (!started || window.gameExitDialogOpen || !bossPolicy()) return;
    for (const monster of monsters) for (const bullet of bullets) {
      if (monster.hp <= 0 || bullet.life <= 0 || (bullet.hit || []).includes(monster) || !bulletHitsCircle(bullet, monster.x, monster.y, monster.r)) continue;
      if (bullet.kind === 2) { if (!consumeTankoPierce(bullet, monster)) continue; }
      else { (bullet.hit ||= []).push(monster); bullet.life = 0; }
      monster.hp -= bullet.damage || 1;
      monster.hitLeft = groups.hit.count * groups.hit.duration;
      gameAudio.fx('hit');
      if (bullet.kind !== 2) { bullet.pierce = (bullet.pierce || 1) - 1; if (bullet.pierce > 0) bullet.life = 1; }
      if (monster.hp <= 0 && gameScoring.enemyDefeated(monster)) {
        gameAudio.fx('destroy'); dropItem(monster.x, monster.y);
        bursts.push({ x: monster.x, y: monster.y, t: 0 });
        for (let i = 0; i < 9; i++) particles.push({ x: monster.x, y: monster.y,
          vx: (Math.random() - .5) * 180, vy: (Math.random() - .5) * 180, life: .5 });
      }
    }
    monsters = monsters.filter(monster => monster.hp > 0);
    bullets = bullets.filter(bullet => bullet.kind !== 2 || bullet.life > 0);
  }
  function frame(monster) {
    let group = monster.hitLeft > 0 ? 'hit' : monster.turnLeft > 0 ? 'directions' : monster.moving ? 'move' : 'idle';
    const spec = groups[group];
    const index = group === 'directions' ? ((Math.round((monster.angle + Math.PI / 2) / (Math.PI / 4)) % 8) + 8) % 8 :
      group === 'hit' ? Math.min(2, Math.floor((spec.count * spec.duration - monster.hitLeft) / spec.duration)) : Math.floor(monster.t / spec.duration) % spec.count;
    return { group, index, column: spec.column + index, row: spec.row,
      rotation: group === 'directions' ? 0 : monster.angle + (group === 'move' ? 0 : Math.PI / 2) };
  }
  function paint(point, pose, width) {
    const height = width * 256 / 320;
    ctx.save(); ctx.translate(point.x, point.y); ctx.rotate(pose.rotation || 0);
    ctx.drawImage(atlas, pose.column * 320, pose.row * 256, 320, 256,
      -width * 160 / 320, -height * 127 / 256, width, height);
    ctx.restore();
  }
  function draw() {
    if (!ready() || !player || !menu.classList.contains('hidden')) return;
    for (const entry of entrances) {
      ctx.save(); ctx.globalAlpha = .65 + .35 * Math.sin(entry.time * 8);
      paint(entry, { column: 0, row: 0 }, 48); ctx.restore();
    }
    for (const monster of monsters) paint(monster, frame(monster), 64);
    for (const burst of bursts) paint(burst, { column: groups.explosion.column + Math.min(3, Math.floor(burst.t / groups.explosion.duration)), row: 3 }, 80);
  }
  window.itemMonsters = Object.freeze({ reset, update, collide, draw, configure, spawn, frame, ready,
    targets: () => monsters.filter(monster => monster.hp > 0 && monster.life > 0),
    snapshot: () => ({ monsters: monsters.map(monster => ({ ...monster })), entrances: entrances.map(entry => ({ ...entry })),
      bursts: bursts.map(burst => ({ ...burst })), countdown, policy: { ...rule() },
      mode: 'provisional-legacy-compatible', normalOpportunityProbability: 1 - legacyProbability }),
    legacyProbability
  });
  seed();
})();
