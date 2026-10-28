(() => {
  "use strict";

  const panel = document.querySelector("#iterations-hang-mug");
  if (!panel) return;
  const video = panel.querySelector("video");
  const chart = panel.querySelector(".round-improvement-plot");
  if (!video || !chart) return;

  const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const stages = JSON.parse(chart.dataset.stages);
  const layout = JSON.parse(chart.dataset.chartLayout);
  const reveal = chart.querySelector("[data-chart-reveal]");
  const series = Array.from(chart.querySelectorAll("[data-chart-series]"), node => ({
    id: node.dataset.chartSeries,
    points: JSON.parse(node.dataset.chartPoints),
    label: node.querySelector("[data-chart-label]")
  }));
  const finalRound = stages[stages.length - 1].round;
  const x = round => layout.xStart + (round - 1) * layout.xPerRound;
  const y = percent => layout.yBottom - percent * layout.yPerPercent;
  let frame = 0;

  function currentRound() {
    if (motion.matches || video.error) return finalRound;
    const time = video.currentTime || 0;
    let index = stages.length - 1;
    while (index > 0 && time < stages[index].start) index--;
    if (index === 0) return stages[0].round;
    const previous = stages[index - 1].round;
    // Draw each newly reached set of checkpoints over the first 0.9 seconds
    // of its correction clip. The media clock also handles pauses and seeking.
    const progress = Math.min(1, Math.max(0, (time - stages[index].start) / .9));
    return previous + (stages[index].round - previous) * progress;
  }

  function render() {
    const round = currentRound();
    reveal.setAttribute("width", String(round >= finalRound ? layout.clipWidth : x(round) + layout.markerRadius - layout.clipLeft));
    chart.dataset.round = round.toFixed(3);
    series.forEach(({ id, points, label }) => {
      const shownRound = Math.min(round, points[points.length - 1][0]);
      const nextIndex = points.findIndex(point => point[0] >= shownRound);
      const next = points[nextIndex];
      const previous = points[Math.max(0, nextIndex - 1)];
      const fraction = next[0] === previous[0] ? 1 : (shownRound - previous[0]) / (next[0] - previous[0]);
      const percent = previous[1] + (next[1] - previous[1]) * fraction;
      const right = shownRound >= layout.labelSwitchRound;
      label.setAttribute("x", String(x(shownRound) + (right ? -6 : 8)));
      label.setAttribute("y", String(y(percent) + layout[id + "LabelOffset"]));
      label.setAttribute("text-anchor", right ? "end" : "start");
    });
  }

  function stop() {
    if (frame) window.cancelAnimationFrame(frame);
    frame = 0;
    render();
  }

  function tick() {
    render();
    frame = !video.paused && !video.ended && !document.hidden && !motion.matches
      ? window.requestAnimationFrame(tick) : 0;
  }

  function start() {
    stop();
    tick();
  }

  ["play", "playing"].forEach(event => video.addEventListener(event, start));
  ["pause", "ended", "error"].forEach(event => video.addEventListener(event, stop));
  ["loadedmetadata", "durationchange", "timeupdate", "seeking", "seeked", "emptied", "unikey:task-selected"]
    .forEach(event => video.addEventListener(event, render));
  document.addEventListener("visibilitychange", () => document.hidden ? stop() : start());
  motion.addEventListener("change", start);
  start();
})();
