/* Check the chart against the actual media clock, including backwards seeks. */
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const root = __dirname + '/..';
const data = JSON.parse(fs.readFileSync(root + '/data/hang-mug-improvement.json', 'utf8'));
const html = fs.readFileSync(root + '/index.html', 'utf8');
const chartLayout = JSON.parse(html.match(/data-chart-layout="([^"]+)"/)[1].replace(/&quot;/g, '"'));

function element() {
  return {
    attrs: {}, handlers: {},
    setAttribute(name, value) { this.attrs[name] = value; },
    addEventListener(name, handler) { this.handlers[name] = handler; },
    fire(name) { this.handlers[name](); }
  };
}

function fixture(reducedMotion = false) {
  const video = Object.assign(element(), { currentTime: 0, paused: true, ended: false, error: null });
  const reveal = element();
  const nodes = data.series.map(series => {
    const label = element();
    return { label, dataset: { chartSeries: series.id, chartPoints: JSON.stringify(series.points.map(p => [p.round, 100 * p.successes / p.trials])) }, querySelector() { return label; } };
  });
  const chart = {
    dataset: { stages: JSON.stringify(data.timeline), chartLayout: JSON.stringify(chartLayout) },
    querySelector() { return reveal; }, querySelectorAll() { return nodes; }
  };
  const panel = { querySelector(selector) { return selector === 'video' ? video : chart; } };
  const doc = Object.assign(element(), { hidden: false, querySelector() { return panel; } });
  const motion = Object.assign(element(), { matches: reducedMotion });
  const scheduled = new Map(); let id = 0;
  const win = {
    matchMedia() { return motion; },
    requestAnimationFrame(callback) { scheduled.set(++id, callback); return id; },
    cancelAnimationFrame(id) { scheduled.delete(id); }
  };
  vm.runInNewContext(fs.readFileSync(root + '/assets/round-improvement.js', 'utf8'), { document: doc, window: win, JSON, Array, String, Math });
  return { video, chart, reveal, nodes, doc, motion, scheduled };
}

const f = fixture();
const round = () => Number(f.chart.dataset.round);
assert.strictEqual(round(), 1, 'initial checkpoint is shown before playback');
assert.strictEqual(f.scheduled.size, 0, 'a paused video does not schedule animation frames');
f.video.currentTime = data.timeline[1].start + .45;
f.video.fire('timeupdate');
assert.strictEqual(round(), 3.5, 'new checkpoints draw progressively within the correction clip');
f.video.currentTime = data.timeline[2].start + .9;
f.video.fire('seeked');
assert.strictEqual(round(), 11, 'a forward seek reveals the matching checkpoints');
f.video.currentTime = data.timeline[3].start + 1;
f.video.fire('timeupdate');
assert.strictEqual(round(), 19);
assert.strictEqual(Number(f.reveal.attrs.width), chartLayout.clipWidth, 'the entire chart and final star are visible');
f.video.currentTime = 0;
f.video.fire('seeking');
assert.strictEqual(round(), 1, 'seeking backwards hides later results');
f.video.paused = false;
f.video.fire('play');
assert.strictEqual(f.scheduled.size, 1);
f.video.paused = true;
f.video.fire('pause');
assert.strictEqual(f.scheduled.size, 0, 'pausing cancels the animation loop');
f.motion.matches = true;
f.motion.fire('change');
assert.strictEqual(round(), 19, 'reduced motion shows the complete static comparison');
assert.strictEqual(f.scheduled.size, 0);
f.motion.matches = false;
f.motion.fire('change');
assert.strictEqual(round(), 1);
f.video.error = {};
f.video.fire('error');
assert.strictEqual(round(), 19, 'results remain available if the video cannot load');
const reduced = fixture(true);
assert.strictEqual(Number(reduced.chart.dataset.round), 19);
assert.strictEqual(reduced.scheduled.size, 0);
assert(html.includes('class="round-chart-line"'));
assert(!html.includes('class="round-chart-line" stroke-dasharray'));
assert(html.includes('hang-mug-chart-description'));
assert(!html.includes('automatic-corrections-across-rounds.mp4'), 'the baked-in plot is no longer served');
console.log('Round improvement: progressive drawing, playback, seeking, reduced motion, and fallback checks passed.');
