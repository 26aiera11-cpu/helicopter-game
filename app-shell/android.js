/* Native app compatibility only; original combat, input math and sound settings are reused. */
(() => {
  const state = window.heliAndroidState;
  if (!state?.native) return;
  const App = Capacitor.registerPlugin('App');
  const Motion = Capacitor.registerPlugin('HeliMotion');
  let nativeMotion = false, nativeAngle = 90, lastWebSignal = 0, checking = false, exiting = false;
  const originalAngle = screenAngle;
  window.screenAngle = () => nativeMotion ? nativeAngle : originalAngle();
  function panel(id, text, buttons) {
    const dialog = document.createElement('dialog');
    dialog.id = id; dialog.className = 'heli-native-panel';
    const message = document.createElement('p');message.textContent = text;dialog.append(message);
    for (const [label, action] of buttons) {
      const button = document.createElement('button');button.type = 'button';button.textContent = label;
      button.addEventListener('click', action);dialog.append(button);
    }
    dialog.addEventListener('cancel', e => {e.preventDefault(); if (dialog === exitPanel) dialog.close();});
    document.body.append(dialog);return dialog;
  }
  const resumePanel = panel('nativeResumeDialog', '게임을 계속할까요?', [['계속 플레이', () => {
    resumePanel.close();state.paused = false;last = performance.now();
    gameAudio.resume();ensureMotion();
  }]]);
  const exitPanel = panel('nativeExitDialog', '앱을 종료할까요?', [
    ['계속하기', () => exitPanel.close()],
    ['앱 종료', async () => {
      if (exiting) return;exiting = true;gameAudio.pause();
      try {await App.exitApp();} catch {exiting = false;exitPanel.close();}
    }]
  ]);
  function clearInput() {
    gameControls.reset();tilt = {x:0,y:0};neutral = null;
    if (player) player.vx = player.vy = 0;
  }
  function pause() {
    state.paused = true;clearInput();gameAudio.pause();Motion.stop().catch(() => {});
  }
  function foreground() {
    if (!state.active || document.hidden || !state.paused) return;
    clearInput();last = performance.now();
    if (started && !gameOverPending && !window.gameExitDialogOpen) {
      if (!resumePanel.open) resumePanel.showModal();
    } else {state.paused = false;ensureMotion();}
  }
  const tick = gameAudio.tick;
  gameAudio.tick = function(...args) {if (!state.paused && state.active) return tick.apply(this,args);};
  App.addListener('appStateChange', ({isActive}) => {
    state.active = isActive;if (!isActive) pause();else foreground();
  });
  document.addEventListener('visibilitychange', () => {if (document.hidden) pause();else foreground();});
  App.addListener('backButton', () => {
    if (!state.active || document.hidden || gameOverPending) return;
    if (resumePanel.open) return;
    if (exitPanel.open) {exitPanel.close();return;}
    if (window.gameExitDialogOpen) {document.getElementById('gameExitCancel').click();return;}
    const dialog = document.querySelector('dialog[open]');
    if (dialog) {dialog.close();return;}
    if (started) document.getElementById('exitGame').click();
    else exitPanel.showModal();
  });
  function webSignal(event) {
    if (!event.isTrusted || !sensorOn) return;
    const valid = event.type === 'deviceorientation'
      ? event.gamma != null && event.beta != null
      : event.accelerationIncludingGravity?.x != null && event.accelerationIncludingGravity?.y != null;
    if (!valid) return;
    if (nativeMotion) {event.stopImmediatePropagation();return;}
    lastWebSignal = Date.now();
  }
  window.addEventListener('deviceorientation',webSignal,true);
  window.addEventListener('devicemotion',webSignal,true);
  Motion.addListener('gravity', ({x,y,rotation}) => {
    if (!nativeMotion || state.paused || !state.active || !started || !sensorOn) return;
    nativeAngle = rotation;applyTilt(x*3,y*3,'기울기');
  });
  async function ensureMotion() {
    if (!sensorOn || !started || state.paused || !state.active || checking) return;
    checking = true;
    try {
      if (!nativeMotion) {
        await new Promise(resolve => setTimeout(resolve,850));
        if (Date.now()-lastWebSignal < 1000) return;
      }
      if (!sensorOn || !started || state.paused || !state.active) return;
      const result = await Motion.start();nativeMotion = Boolean(result.available);
      if (!nativeMotion) sensorStatus.textContent = '센서 사용 불가 · 드래그 이동 가능';
    } catch {sensorStatus.textContent = '센서 사용 불가 · 드래그 이동 가능';}
    finally {checking = false;}
  }
  const originalSensorClick = sensorBtn.onclick;
  sensorBtn.onclick = async function(event) {
    const requested = Date.now();
    await originalSensorClick.call(this,event);
    ensureMotion();
    setTimeout(() => {if (sensorOn && lastSensor < requested) sensorStatus.textContent = '센서 신호 없음 · 드래그 이동 가능';},2000);
  };
  new MutationObserver(() => {
    if (menu.classList.contains('hidden')) ensureMotion();else Motion.stop().catch(() => {});
  }).observe(menu,{attributes:true,attributeFilter:['class']});
  window.heliAndroid = {pause,foreground,back:() => document.getElementById('exitGame').click()};
})();
