/* Android-only lifecycle gate. The original frame/update/physics stay intact. */
(() => {
  const native = window.Capacitor?.isNativePlatform() && Capacitor.getPlatform() === 'android';
  const state = window.heliAndroidState = {native: Boolean(native), paused: false, active: true};
  if (!native) return;
  const raf = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = callback => raf(time => {
    if (callback.name === 'frame' && (state.paused || document.hidden)) {
      window.requestAnimationFrame(callback);
      return;
    }
    callback(time);
  });
})();
