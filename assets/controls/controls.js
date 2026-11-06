/* Independent pointer owners for rotation, fire and auxiliary canvas movement. */
(() => {
  'use strict';
  const joystick = document.getElementById('rotationJoystick');
  const fire = document.getElementById('fire');
  const surface = document.getElementById('game');
  const menuElement = document.getElementById('menu');
  const DEAD_ZONE = .08;
  let rotationPointer = null, firePointer = null, raw = 0, value = 0, keyboard = null;
  const gameplayPointers = new Map();
  let pressSerial = 0, lastRelease = null;
  const active = () => started && !window.gameExitDialogOpen && menuElement.classList.contains('hidden');
  const primaryButton = event => event.pointerType !== 'mouse' || event.button === 0;
  const limit = input => Math.max(-1, Math.min(1, input));
  function claim(event) {
    if (!active() || !primaryButton(event)) return false;
    gameplayPointers.set(event.pointerId, ++pressSerial);return true;
  }
  function capture(element, id) { try { element.setPointerCapture(id); } catch (ignore) {} }
  function release(element, id) {
    if (id === null || id === undefined) return;
    try { if (element.hasPointerCapture(id)) element.releasePointerCapture(id); } catch (ignore) {}
  }
  function geometry() {
    const rect = joystick.getBoundingClientRect();
    const inset = parseFloat(getComputedStyle(joystick).getPropertyValue('--stick-inset'));
    return { rect, center: rect.left + rect.width / 2, travel: Math.max(1, rect.width / 2 - inset) };
  }
  function setRaw(input) {
    raw = limit(input);
    value = Math.abs(raw) <= DEAD_ZONE ? 0 : Math.sign(raw) * (Math.abs(raw) - DEAD_ZONE) / (1 - DEAD_ZONE);
    joystick.style.setProperty('--stick-offset', `${raw * geometry().travel}px`);
    joystick.setAttribute('aria-valuenow', String(Math.round(value * 100)));
    joystick.setAttribute('aria-valuetext', value === 0 ? '회전 정지' : `${value < 0 ? '반시계' : '시계'} 방향 ${Math.round(Math.abs(value) * 100)}%`);
  }
  function endRotation(id) {
    if (id !== rotationPointer) return;
    const owner = rotationPointer;rotationPointer = null;keyboard = null;
    joystick.classList.remove('is-held');setRaw(0);release(joystick, owner);
  }
  function endFire(id) {
    if (id !== firePointer) return;
    const owner = firePointer;firePointer = null;keys.fire = false;release(fire, owner);
  }
  function endDrag(id) {
    if (!drag || drag.id !== id) return;
    const owner = drag.id;drag = null;tilt = { x: 0, y: 0 };release(surface, owner);
  }
  function reset() {
    endRotation(rotationPointer);endFire(firePointer);
    if (drag) endDrag(drag.id);
    keys.left = keys.right = keys.fire = false;
    drag = null;tilt = { x: 0, y: 0 };
  }
  joystick.addEventListener('pointerdown', event => {
    event.preventDefault();event.stopPropagation();
    if (!claim(event) || rotationPointer !== null) return;
    rotationPointer = event.pointerId;keyboard = null;
    joystick.classList.add('is-held');capture(joystick, event.pointerId);
    const { center, travel } = geometry();setRaw((event.clientX - center) / travel);
  });
  joystick.addEventListener('pointermove', event => {
    if (event.pointerId !== rotationPointer) return;
    event.preventDefault();
    const { rect, center, travel } = geometry();
    // Leaving the actual control ends ownership; track overflow inside it clamps.
    if (!active() || event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) {
      endRotation(event.pointerId);return;
    }
    setRaw((event.clientX - center) / travel);
  });
  joystick.addEventListener('lostpointercapture', event => endRotation(event.pointerId));
  joystick.addEventListener('keydown', event => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key) || !active()) return;
    event.preventDefault();
    if (rotationPointer !== null) return;
    keyboard = event.key;setRaw(event.key === 'ArrowLeft' ? -1 : event.key === 'ArrowRight' || event.key === 'End' ? 1 : 0);
  });
  joystick.addEventListener('keyup', event => { if (event.key === keyboard) { keyboard = null;setRaw(0); } });
  joystick.addEventListener('blur', () => { if (rotationPointer === null) { keyboard = null;setRaw(0); } });
  fire.addEventListener('pointerdown', event => {
    event.preventDefault();event.stopPropagation();
    if (!claim(event) || firePointer !== null) return;
    firePointer = event.pointerId;capture(fire, event.pointerId);keys.fire = true;
  });
  fire.addEventListener('lostpointercapture', event => endFire(event.pointerId));
  surface.addEventListener('pointerdown', event => {
    if (!claim(event)) return;
    event.preventDefault();if (drag) return;
    drag = { id: event.pointerId, x: event.clientX, y: event.clientY };
    capture(surface, event.pointerId);
  });
  surface.addEventListener('pointermove', event => {
    if (!drag || drag.id !== event.pointerId) return;
    event.preventDefault();
    // Original auxiliary drag sensitivity. Sensor processing remains in index.html.
    tilt.x = Math.max(-1, Math.min(1, (event.clientX - drag.x) / 75));
    tilt.y = Math.max(-1, Math.min(1, (event.clientY - drag.y) / 75));
  });
  surface.addEventListener('lostpointercapture', event => endDrag(event.pointerId));
  for (const name of ['pointerup', 'pointercancel']) window.addEventListener(name, event => {
    endRotation(event.pointerId);endFire(event.pointerId);endDrag(event.pointerId);
    if (!gameplayPointers.has(event.pointerId)) return;
    if (name === 'pointercancel') { gameplayPointers.delete(event.pointerId);return; }
    const serial = gameplayPointers.get(event.pointerId);
    lastRelease = { time: performance.now(), x: event.clientX, y: event.clientY };
    setTimeout(() => { if (gameplayPointers.get(event.pointerId) === serial) gameplayPointers.delete(event.pointerId); }, 500);
  }, true);
  // A lifecycle reset may release capture while a finger remains down. Its final
  // native click belongs to gameplay, even if selection now lies underneath it.
  window.addEventListener('pointerdown', event => { gameplayPointers.delete(event.pointerId);lastRelease = null; }, true);
  document.addEventListener('click', event => {
    const oldMouseClick = event.pointerId === undefined && event.detail > 0 && lastRelease &&
      performance.now() - lastRelease.time < 500 && Math.hypot(event.clientX - lastRelease.x, event.clientY - lastRelease.y) < 3;
    if (gameplayPointers.has(event.pointerId) || oldMouseClick) {
      event.preventDefault();event.stopImmediatePropagation();gameplayPointers.delete(event.pointerId);lastRelease = null;
    }
  }, true);
  window.addEventListener('blur', reset);
  document.addEventListener('visibilitychange', () => { if (document.hidden) reset(); });
  document.addEventListener('gameover', reset);
  document.addEventListener('gameoverclose', reset);
  new MutationObserver(reset).observe(menuElement, { attributes: true, attributeFilter: ['class'] });
  window.addEventListener('resize', () => setRaw(raw));

  const protectedSurface = target => target instanceof Element &&
    !target.closest('input,textarea,select,[contenteditable]:not([contenteditable="false"])') &&
    Boolean(target.closest('#game,.controls,#hud,#sensor,#sensorStatus,#exitGame,#fullscreenToggle,#gameOverOverlay,#bossRewardNotice,#gameExitDialog'));
  for (const name of ['contextmenu', 'selectstart', 'dragstart']) document.addEventListener(name, event => {
    if (protectedSurface(event.target)) event.preventDefault();
  }, { capture: true });
  window.gameControls = Object.freeze({ reset, rotation: () => value,
    snapshot: () => ({ raw, value, deadZone: DEAD_ZONE, rotationPointer, firePointer, dragPointer: drag?.id ?? null }) });
})();
