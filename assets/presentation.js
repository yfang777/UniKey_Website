(() => {
  "use strict";

  const trigger = document.querySelector(".contents-trigger");
  const dialog = document.querySelector("#contents-dialog");
  const closeButton = dialog.querySelector(".contents-close");
  const links = dialog.querySelector(".contents-links");
  const outline = document.querySelector(".section-nav");
  const mobile = window.matchMedia("(max-width: 820px)");
  let previousOverflow = "";

  function closeContents() {
    if (dialog.open) dialog.close();
  }

  trigger.addEventListener("click", () => {
    links.innerHTML = outline.innerHTML;
    previousOverflow = document.body.style.overflow;
    dialog.showModal();
    document.body.style.overflow = "hidden";
    trigger.setAttribute("aria-expanded", "true");
  });
  closeButton.addEventListener("click", closeContents);
  links.addEventListener("click", event => {
    if (event.target.closest("a")) closeContents();
  });
  dialog.addEventListener("click", event => {
    if (event.target !== dialog) return;
    const bounds = dialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right ||
        event.clientY < bounds.top || event.clientY > bounds.bottom) closeContents();
  });
  dialog.addEventListener("close", () => {
    document.body.style.overflow = previousOverflow;
    trigger.setAttribute("aria-expanded", "false");
  });
  mobile.addEventListener("change", event => { if (!event.matches) closeContents(); });
  trigger.hidden = false;

  const video = document.querySelector("#opening-video");
  const playback = document.querySelector(".hero-playback");
  const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
  let manuallyPaused = false;
  let inView = false;

  function updatePlayback() {
    playback.setAttribute("aria-label", video.paused ? "Play opening video" : "Pause opening video");
    playback.querySelector("path").setAttribute("d", video.paused ? "M8 5l11 7-11 7Z" : "M9 5v14M15 5v14");
  }

  function syncPlayback() {
    if (inView && !document.hidden && !manuallyPaused && !motion.matches) {
      video.play().catch(() => { /* The play button remains available if autoplay is blocked. */ });
    } else {
      video.pause();
    }
  }

  playback.addEventListener("click", () => {
    if (video.paused) {
      manuallyPaused = false;
      video.play().catch(updatePlayback);
    } else {
      manuallyPaused = true;
      video.pause();
    }
  });
  video.addEventListener("play", updatePlayback);
  video.addEventListener("pause", updatePlayback);
  motion.addEventListener("change", syncPlayback);
  document.addEventListener("visibilitychange", syncPlayback);
  new IntersectionObserver(entries => {
    inView = entries[0].isIntersecting && entries[0].intersectionRatio >= 0.01;
    syncPlayback();
  }, { threshold: 0.01 }).observe(video);
  if (motion.matches) {
    video.autoplay = false;
    video.pause();
  }
  updatePlayback();
  video.controls = false;
  playback.hidden = false;
})();
