/* Presentation hooks only; the original game functions remain unchanged. */
(() => {
  const selectionMenu = document.getElementById('menu');
  const settings = document.getElementById('selectionSettings');
  const audioControls = document.getElementById('audioControls');
  const help = document.getElementById('selectionHelpDialog');
  const heading = selectionMenu.querySelector('h1');
  const result = document.getElementById('selectionResult');

  function syncCharacters() {
    document.querySelectorAll('.heli-stage').forEach((element, index) => {
      element.classList.toggle('is-selected', index === selectedHeli);
    });
  }
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
