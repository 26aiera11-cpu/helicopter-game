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

  function syncCharacters() {
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
