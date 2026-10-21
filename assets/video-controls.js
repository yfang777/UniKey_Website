(() => {
  "use strict";

  const playPath = "M8 5l11 7-11 7Z";
  const pausePath = "M9 5v14M15 5v14";
  const expandPath = "M15 3h6v6M21 3l-7 7M3 15v6h6M3 21l7-7";
  const collapsePath = "M9 3v6H3M9 9 2 2M15 21v-6h6M15 15l7 7";

  function iconButton(path, label) {
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("aria-label", label);
    button.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${path}" /></svg>`;
    return button;
  }

  function timeLabel(seconds) {
    if (!Number.isFinite(seconds)) return "—";
    return `${Math.round(seconds)}s`;
  }

  document.querySelectorAll(".article-shell video").forEach(video => {
    const label = video.getAttribute("aria-label") || "Demonstration";
    const player = document.createElement("div");
    player.className = "video-player";
    const toolbar = document.createElement("div");
    toolbar.className = "video-controls";
    toolbar.setAttribute("role", "group");
    toolbar.setAttribute("aria-label", `${label} video controls`);
    const toggle = iconButton(playPath, `Play ${label}`);
    const speed = document.createElement("button");
    speed.type = "button";
    speed.className = "video-speed";
    const seek = document.createElement("input");
    seek.type = "range";
    seek.min = "0";
    seek.max = "1000";
    seek.step = "1";
    seek.value = "0";
    seek.disabled = true;
    seek.setAttribute("aria-label", `${label} video progress`);
    const duration = document.createElement("span");
    duration.className = "video-duration";
    const expand = iconButton(expandPath, `Expand ${label} video`);
    // Real-world clips already contain 30× footage; 60× and 100× use 2× and 10/3× file playback.
    const baseSpeed = Number(video.dataset.baseSpeed) || 1;
    const rates = baseSpeed === 30 ? [1, 2, 100 / 30] : [0.5, 1, 2, 4, 8];
    const durationHint = Number(video.dataset.duration) || NaN;

    function updatePlayback() {
      toggle.setAttribute("aria-label", `${video.paused ? "Play" : "Pause"} ${label}`);
      toggle.querySelector("path").setAttribute("d", video.paused ? playPath : pausePath);
      const effectiveSpeed = Number((video.playbackRate * baseSpeed).toFixed(2));
      speed.textContent = `${effectiveSpeed}×`;
      speed.setAttribute("aria-label", `${label} playback speed ${effectiveSpeed}×. Click to change speed.`);
      updateProgress();
    }

    function updateProgress() {
      const ready = Number.isFinite(video.duration) && video.duration > 0;
      const total = ready ? video.duration : durationHint;
      seek.disabled = !ready;
      const fraction = ready ? video.currentTime / video.duration : 0;
      seek.value = String(Math.round(fraction * 1000));
      seek.style.setProperty("--progress", `${fraction * 100}%`);
      seek.setAttribute("aria-valuetext", `${timeLabel(video.currentTime / video.playbackRate)} of ${timeLabel(total / video.playbackRate)}`);
      duration.textContent = timeLabel(total / video.playbackRate);
      duration.setAttribute("aria-label", `${label} video length ${duration.textContent} at the selected speed`);
    }

    toggle.addEventListener("click", () => {
      if (video.paused) video.play().catch(() => { video.controls = true; });
      else video.pause();
    });
    speed.addEventListener("click", () => {
      video.playbackRate = rates[(rates.indexOf(video.playbackRate) + 1) % rates.length];
      updatePlayback();
    });
    seek.addEventListener("input", () => {
      if (Number.isFinite(video.duration)) video.currentTime = Number(seek.value) / 1000 * video.duration;
      updateProgress();
    });
    expand.addEventListener("click", () => {
      if (document.fullscreenElement === player) document.exitFullscreen().catch(() => {});
      else if (player.requestFullscreen) player.requestFullscreen().catch(() => { video.controls = true; });
      else if (video.webkitEnterFullscreen) video.webkitEnterFullscreen();
    });
    if (!player.requestFullscreen && !video.webkitEnterFullscreen) expand.hidden = true;
    player.addEventListener("fullscreenchange", () => {
      const expanded = document.fullscreenElement === player;
      expand.setAttribute("aria-label", `${expanded ? "Exit fullscreen for" : "Expand"} ${label} video`);
      expand.querySelector("path").setAttribute("d", expanded ? collapsePath : expandPath);
    });
    ["play", "pause", "ended", "ratechange"].forEach(event => video.addEventListener(event, updatePlayback));
    ["loadedmetadata", "durationchange", "timeupdate", "seeked", "emptied"].forEach(event => video.addEventListener(event, updateProgress));
    video.addEventListener("error", () => { video.controls = true; });
    toolbar.append(toggle, speed, seek, duration, expand);
    video.replaceWith(player);
    player.append(video, toolbar);
    video.controls = false;
    updatePlayback();
  });
})();
