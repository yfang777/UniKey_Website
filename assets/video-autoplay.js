(() => {
  "use strict";

  const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const states = new Map();

  function visible(video, state) {
    return state.inView && !video.closest("[hidden]") && !document.hidden;
  }

  function sync(video, state) {
    const allowed = visible(video, state) && !state.manuallyPaused &&
      (!motion.matches || state.manualPlay) && !video.ended;
    if (!allowed) {
      if (!visible(video, state)) state.manualPlay = false;
      video.pause();
    } else if (video.paused && !state.pending) {
      state.pending = true;
      video.play().then(() => {
        state.pending = false;
        // A task change or scroll can occur while the browser loads the clip.
        if (!visible(video, state) || state.manuallyPaused || (motion.matches && !state.manualPlay)) video.pause();
      }).catch(error => {
        state.pending = false;
        if (error.name === "AbortError" && visible(video, state)) sync(video, state);
        // The existing play button remains available when autoplay is blocked.
      });
    }
  }

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      const state = states.get(entry.target);
      if (entry.isIntersecting && entry.intersectionRatio >= 0.5) state.inView = true;
      else if (!entry.isIntersecting || entry.intersectionRatio < 0.15) state.inView = false;
      sync(entry.target, state);
    });
  }, { threshold: [0, 0.15, 0.5] });

  document.querySelectorAll(".article-shell video").forEach(video => {
    const state = { inView: false, manuallyPaused: false, manualPlay: false, pending: false };
    states.set(video, state);
    video.muted = true;
    video.playsInline = true;
    video.addEventListener("unikey:playback-intent", event => {
      state.manuallyPaused = event.detail === "pause";
      state.manualPlay = event.detail === "play";
    });
    video.addEventListener("pause", () => {
      // Native/fullscreen controls also preserve the reader's pause choice.
      if (visible(video, state) && !video.ended && (!motion.matches || state.manualPlay)) state.manuallyPaused = true;
    });
    video.addEventListener("play", () => {
      if ((video.controls || video.webkitDisplayingFullscreen) && visible(video, state)) {
        state.manuallyPaused = false;
        state.manualPlay = true;
      }
    });
    video.addEventListener("unikey:task-selected", () => {
      state.manuallyPaused = false;
      state.manualPlay = false;
      // Wait for fresh intersection geometry after revealing the task panel.
      state.inView = false;
      observer.unobserve(video);
      observer.observe(video);
    });
    observer.observe(video);
  });

  function syncAll() { states.forEach((state, video) => sync(video, state)); }
  document.addEventListener("visibilitychange", syncAll);
  motion.addEventListener("change", syncAll);
})();
