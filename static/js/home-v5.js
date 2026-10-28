/* Presentation fallback only; no network requests, state, authentication or APIs. */
(() => {
  const hideBroken = image => { image.hidden = true; image.parentElement.dataset.fallback = 'true'; };
  document.querySelectorAll('.v5-story-media img').forEach(image => {
    image.addEventListener('error', () => hideBroken(image), {once:true});
    if (image.complete && image.naturalWidth === 0) hideBroken(image);
  });
})();
