/* Presentation hooks only; the original game functions remain unchanged. */
(() => {
  const selectionMenu = document.getElementById('menu');
  const settings = document.getElementById('selectionSettings');
  const audioControls = document.getElementById('audioControls');
  const help = document.getElementById('selectionHelpDialog');
  const heading = selectionMenu.querySelector('h1');
  const result = document.getElementById('selectionResult');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const settling = new Map();
  const accents = [...selectionMenu.querySelectorAll('.character-details')];
  selectionMenu.querySelectorAll('.heli-stage').forEach(stage => {
    const light = document.createElement('div');
    light.className = 'podium-light';
    light.dataset.heli = stage.dataset.heli;
    light.setAttribute('aria-hidden', 'true');
    stage.before(light);
    accents.push(light);
  });

  function syncCharacters() {
    accents.forEach(element => element.classList.toggle('is-selected', Number(element.dataset.heli) === selectedHeli));
    document.querySelectorAll('.heli-stage').forEach((element, index) => {
      const selected = index === selectedHeli;
      if (selected === element.classList.contains('is-selected')) {
        if (selected && !reducedMotion.matches && !settling.has(element)) {
          element.classList.add('is-hovering');
        }
        return;
      }

      // Capture the current pose before stopping a hover or an earlier landing.
      // This also keeps rapid selection changes continuous.
      const from = getComputedStyle(element).transform;
      settling.get(element)?.cancel();
      settling.delete(element);
      element.classList.remove('is-hovering');
      element.classList.toggle('is-selected', selected);
      if (reducedMotion.matches) return;

      const movement = element.animate([
        { transform: from },
        { transform: selected ? 'translateY(-4px) scale(1.015)' : 'translateY(0) scale(1)' }
      ], { duration: 220, easing: 'ease-out' });
      settling.set(element, movement);
      movement.finished.then(() => {
        if (settling.get(element) !== movement) return;
        settling.delete(element);
        if (element.classList.contains('is-selected')) element.classList.add('is-hovering');
      }).catch(() => {}); // Re-selection intentionally cancels an in-flight move.
    });
  }
  reducedMotion.addEventListener('change', () => {
    settling.forEach(animation => animation.cancel());
    settling.clear();
    document.querySelectorAll('.heli-stage').forEach(element => element.classList.remove('is-hovering'));
    syncCharacters();
  });
  function closeSettings() {
    audioControls.classList.remove('settings-open');
    settings.setAttribute('aria-expanded', 'false');
  }
  function syncMenu() {
    const visible = !selectionMenu.classList.contains('hidden');
    document.body.classList.toggle('selection-open', visible);
    if (!visible) {
      closeSettings();
      if (help.open) help.close();
    }
    const message = heading.textContent || '';
    result.textContent = /게임 오버|모든 지역 클리어/.test(message) ? message : '';
    syncCharacters();
  }

  document.querySelectorAll('.select-hit').forEach(button => {
    button.addEventListener('click', syncCharacters);
  });
  settings.addEventListener('click', () => {
    const opened = audioControls.classList.toggle('settings-open');
    settings.setAttribute('aria-expanded', String(opened));
    if (opened) document.getElementById('musicToggle').focus();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') closeSettings();
  });
  document.getElementById('selectionHelp').addEventListener('click', () => help.showModal());
  document.getElementById('selectionHelpClose').addEventListener('click', () => help.close());
  new MutationObserver(syncMenu).observe(selectionMenu, { attributes: true, attributeFilter: ['class'] });
  new MutationObserver(syncMenu).observe(heading, { childList: true, characterData: true, subtree: true });
  syncMenu();
})();

/* Standard fullscreen controls, shared by the menu and gameplay. */
(() => {
  const root = document.documentElement;
  const button = document.createElement('button');
  button.id = 'fullscreenToggle';
  button.type = 'button';
  button.className = 'fullscreen-toggle';
  button.setAttribute('aria-describedby', 'fullscreenStatus');
  const status = document.createElement('p');
  status.id = 'fullscreenStatus';
  status.className = 'fullscreen-status';
  status.setAttribute('role', 'status');
  status.setAttribute('aria-live', 'polite');
  document.body.append(button, status);
  let busy = false;
  let timeout = null;

  const active = () => Boolean(document.fullscreenElement || document.webkitFullscreenElement);
  const supported = () => Boolean(root.requestFullscreen || root.webkitRequestFullscreen);
  function clearPending() {
    clearTimeout(timeout);
    timeout = null;
    busy = false;
  }
  function render() {
    const on = active();
    button.disabled = busy || !supported();
    button.textContent = !supported() ? '⛶ 미지원' : on ? '⛶ 화면 복원' : '⛶ 전체화면';
    button.setAttribute('aria-label', !supported() ? '전체화면을 지원하지 않는 브라우저' : on ? '전체화면 해제' : '전체화면으로 보기');
    button.setAttribute('aria-pressed', String(on));
    button.setAttribute('aria-busy', String(busy));
    button.title = button.getAttribute('aria-label');
  }
  function unavailable() {
    clearPending();
    status.textContent = '전체화면으로 전환할 수 없어요. 현재 화면에서 계속할 수 있어요.';
    render();
  }
  function changed() {
    clearPending();
    status.textContent = '';
    render();
    if (active()) {
      try { screen.orientation?.lock?.('landscape').catch(() => {}); } catch (ignore) {}
    }
  }
  button.addEventListener('click', () => {
    if (busy || !supported()) return;
    const expected = !active();
    busy = true;
    status.textContent = '';
    render();
    try {
      if (expected) {
        // Reuse the original synchronous user-gesture helper and its legacy fallback.
        enterGameFullscreen();
      } else {
        const exit = document.exitFullscreen || document.webkitExitFullscreen;
        if (!exit) { unavailable(); return; }
        const result = exit.call(document);
        if (result && typeof result.catch === 'function') result.catch(unavailable);
      }
      // The existing helper intentionally swallows rejected promises. Native error
      // events handle normal failures; this timeout also covers silent rejections.
      timeout = setTimeout(() => {
        if (active() !== expected) unavailable();
        else { clearPending(); render(); }
      }, 1500);
    } catch (error) { unavailable(); }
  });
  for (const event of ['fullscreenchange', 'webkitfullscreenchange']) document.addEventListener(event, changed);
  for (const event of ['fullscreenerror', 'webkitfullscreenerror']) document.addEventListener(event, unavailable);
  render();
})();

/* In-page exit confirmation: no native browser prompt or fullscreen request. */
(() => {
  const dialog = document.createElement('dialog');
  dialog.id = 'gameExitDialog';
  dialog.setAttribute('aria-labelledby', 'gameExitTitle');
  dialog.innerHTML = '<h2 id="gameExitTitle">게임을 종료할까요?</h2>' +
    '<div class="game-exit-actions"><button id="gameExitCancel" type="button" autofocus>계속 플레이</button>' +
    '<button id="gameExitConfirm" type="button">선택화면으로</button></div>';
  document.body.append(dialog);
  let onConfirm = null;
  let previousFocus = null;
  window.gameExitDialogOpen = false;

  function clearInput() {
    keys.left = keys.right = keys.fire = false;
    drag = null;
    tilt = { x: 0, y: 0 };
  }
  function finish(confirmed) {
    if (!dialog.open && !window.gameExitDialogOpen) return;
    const callback = onConfirm;
    onConfirm = null;
    if (dialog.open) dialog.close();
    window.gameExitDialogOpen = false;
    clearInput();
    if (confirmed && callback) callback();
    else if (started && previousFocus?.isConnected) previousFocus.focus({ preventScroll: true });
    previousFocus = null;
  }
  window.showGameExitDialog = callback => {
    if (!started || dialog.open) return;
    previousFocus = document.activeElement;
    onConfirm = callback;
    clearInput();
    window.gameExitDialogOpen = true;
    try { dialog.showModal(); }
    catch (error) {
      window.gameExitDialogOpen = false;
      onConfirm = null;
      previousFocus = null;
    }
  };
  dialog.querySelector('#gameExitCancel').addEventListener('click', () => finish(false));
  dialog.querySelector('#gameExitConfirm').addEventListener('click', () => finish(true));
  dialog.addEventListener('cancel', event => { event.preventDefault(); finish(false); });
  dialog.addEventListener('close', () => {
    if (!dialog.open && window.gameExitDialogOpen) finish(false);
  });
  new MutationObserver(() => {
    if (!started && window.gameExitDialogOpen) finish(false);
  }).observe(document.getElementById('menu'), { attributes: true, attributeFilter: ['class'] });
})();

/* Boss reward notice only; gameplay owns reward selection and application. */
(() => {
  const notice = document.createElement('p');
  notice.id = 'bossRewardNotice';
  notice.setAttribute('role', 'status');
  notice.setAttribute('aria-live', 'polite');
  notice.setAttribute('aria-atomic', 'true');
  notice.hidden = true;
  document.body.append(notice);
  let timeout;
  function hide() {
    clearTimeout(timeout);
    notice.hidden = true;
    notice.textContent = '';
  }
  document.addEventListener('bossreward', event => {
    const { type, amount } = event.detail;
    if (type !== 'hp' && type !== 'power') return;
    clearTimeout(timeout);
    const label = type === 'hp' ? '❤️ 체력' : '⚡ 무기 강화';
    notice.textContent = amount > 0 ? `${label} +${amount}` : `${label} 최대`;
    notice.hidden = false;
    timeout = setTimeout(hide, 1800);
  });
  new MutationObserver(() => {
    if (document.getElementById('menu').classList.contains('hidden')) hide();
  }).observe(document.getElementById('menu'), { attributes: true, attributeFilter: ['class'] });
})();
