/* Independent item helicopters: regional kill-count reservations and carried lifetime. */
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
  const BODY_WIDTH = 80, HIT_RADIUS = 20;
  // Kept only for the unchanged normal-enemy admission roll in index.html.
  const legacyProbability = .22;
  let settings = { opportunitiesPerRegion: 3 };
  let monsters = [], entrances = [], bursts = [];
  let regions = new Map();
  let randomState = 1;
  function seed() {
    const word = new Uint32Array(1);
    globalThis.crypto?.getRandomValues?.(word);
    randomState = word[0] || (Date.now() >>> 0) || 1;
  }
  // Item planning/movement draws do not consume normal enemies/boss reward RNG.
  function random() {
    randomState ^= randomState << 13; randomState ^= randomState >>> 17; randomState ^= randomState << 5;
    return (randomState >>> 0) / 4294967296;
  }
  function ready() { return Boolean(atlas?.complete && atlas.naturalWidth === 2560 && atlas.naturalHeight === 1280); }
  function configure(patch) {
    if (Object.keys(patch).some(key => key !== 'opportunitiesPerRegion')) throw new RangeError('Unknown item spawn setting');
    const candidate = { ...settings, ...patch };
    if (!Number.isInteger(candidate.opportunitiesPerRegion) || candidate.opportunitiesPerRegion < 0 || candidate.opportunitiesPerRegion > 4) throw new RangeError('Item opportunities must be 0–4');
    // Already chosen regions stay fixed. New settings affect the next region/run.
    settings = candidate;
  }
  function enterRegion(region = stage) {
    if (regions.has(region)) return regions.get(region);
    const shuffled = [1, 2, 3, 4];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    const selected = shuffled.slice(0, settings.opportunitiesPerRegion);
    const plan = { region, regionKey: gameWorlds.region(region).key, worldId: gameWorlds.region(region).worldId, opportunities: selected.length, spawned: 0, phases: [1, 2, 3, 4].map(step => ({
      phase: step, selected: selected.includes(step),
      requiredKills: selected.includes(step) ? 1 + Math.floor(random() * 4) : null,
      normalKills: 0, status: selected.includes(step) ? 'waiting' : 'not-selected'
    })) };
    regions.set(region, plan);
    return plan;
  }
  function reset() { monsters = []; entrances = []; bursts = []; regions = new Map(); seed(); enterRegion(stage); }
  function edge() {
    const side = Math.floor(random() * 4), pad = 27;
    return { x: side === 0 ? pad : side === 1 ? W - pad : pad + random() * (W - 2 * pad),
      y: side === 2 ? pad : side === 3 ? H - pad : pad + random() * (H - 2 * pad), time: 1.4 };
  }
  function normalDefeated() {
    if (!started || phase < 1 || phase > 4) return;
    const plan = enterRegion(stage), slot = plan.phases[phase - 1];
    slot.normalKills++;
    if (!slot.selected || slot.status !== 'waiting' || slot.normalKills < slot.requiredKills) return;
    // Reserve synchronously in the actual kill path, before nextPhase can run.
    slot.status = 'reserved';
    entrances.push({ ...edge(), region: stage, phase, id: `${stage}:${phase}` });
  }
  function materialize(point) {
    const pad = HIT_RADIUS + 2;
    const monster = { x: Math.max(pad, Math.min(W - pad, point.x)), y: Math.max(pad, Math.min(H - pad, point.y)),
      r: HIT_RADIUS, hp: 5, special: true, origin: point.id || null,
      life: 10, t: 0, turn: 0, vx: 0, vy: 0, angle: -Math.PI / 2,
      idleLeft: groups.idle.count * groups.idle.duration, hitLeft: 0, turnLeft: 0 };
    monsters.push(monster);
    return monster;
  }
  // Manual scene/inspection helper; automatic gameplay uses reserved entries only.
  function spawn(position) {
    if (!started || !ready() || boss || phase === 5) return null;
    return materialize(position || edge());
  }
  function update(dt) {
    if (!started || window.gameExitDialogOpen) return;
    enterRegion(stage);
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
      const speed = 45 + gameWorlds.profile(stage) * 8;
      monster.x += vx * speed * dt; monster.y += vy * speed * dt;
      const pad = HIT_RADIUS + 2;
      if (monster.x < pad || monster.x > W - pad) monster.vx *= -1;
      if (monster.y < pad || monster.y > H - pad) monster.vy *= -1;
      monster.x = Math.max(pad, Math.min(W - pad, monster.x));
      monster.y = Math.max(pad, Math.min(H - pad, monster.y));
      monster.moving = Boolean(vx || vy);
    }
    monsters = monsters.filter(monster => monster.life > 0 && monster.hp > 0);
    for (const burst of bursts) burst.t += dt;
    bursts = bursts.filter(burst => burst.t < groups.explosion.count * groups.explosion.duration);
    // Materialize after aging existing actors: new arrivals start with ten full seconds.
    for (const entry of entrances) entry.time = Math.max(0, entry.time - dt);
    if (ready()) {
      const arriving = entrances.filter(entry => entry.time <= 0);
      entrances = entrances.filter(entry => entry.time > 0);
      for (const entry of arriving) {
        const plan = regions.get(entry.region), slot = plan?.phases[entry.phase - 1];
        if (!slot || slot.status !== 'reserved') continue;
        materialize(entry);slot.status = 'spawned';plan.spawned++;
      }
    }
  }
  function collide() {
    if (!started || window.gameExitDialogOpen) return;
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
    for (const monster of monsters) paint(monster, frame(monster), BODY_WIDTH);
    for (const burst of bursts) paint(burst, { column: groups.explosion.column + Math.min(3, Math.floor(burst.t / groups.explosion.duration)), row: 3 }, 80);
  }
  window.itemMonsters = Object.freeze({ reset, update, collide, draw, configure, spawn, frame, ready, enterRegion, normalDefeated,
    targets: () => monsters.filter(monster => monster.hp > 0 && monster.life > 0),
    snapshot: () => ({ monsters: monsters.map(monster => ({ ...monster })), entrances: entrances.map(entry => ({ ...entry })),
      bursts: bursts.map(burst => ({ ...burst })), regions: [...regions.values()].map(plan => ({ ...plan, phases: plan.phases.map(slot => ({ ...slot })) })),
      settings: { ...settings }, mode: 'regional-kill-count', bodyWidth: BODY_WIDTH, bodyHeight: BODY_WIDTH * 256 / 320,
      hitRadius: HIT_RADIUS, normalOpportunityProbability: 1 - legacyProbability }),
    legacyProbability
  });
  seed();
})();
