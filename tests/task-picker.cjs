// Run the production task-selection handlers without browser dependencies.
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const root = require('path').resolve(__dirname, '..');
const taskData = JSON.parse(fs.readFileSync(root + '/data/robotwin-results.json', 'utf8')).tasks;
const html = fs.readFileSync(root + '/index.html', 'utf8');
const source = fs.readFileSync(root + '/assets/site.js', 'utf8');
const pipelineSource = fs.readFileSync(root + '/assets/pipeline.js', 'utf8');
const pipelineTasks = ['hang-mug', 'arrange-table', 'flip-and-arrange-shoe', 'pack-battery'];
const readingOrder = ['Introducing UniKey', 'Data Generation', 'Corrective Data Generation', 'Sim-to-Real', 'Technical Details'];
const navigation = html.match(/<nav class="section-nav"[\s\S]*?<\/nav>/)[0];
assert.deepStrictEqual(Array.from(navigation.matchAll(/<a href="#[^"]+" data-level="1"[^>]*>([^<]+)<\/a>/g), match => match[1]), readingOrder);
assert.deepStrictEqual(Array.from(html.matchAll(/<h2[^>]*>([^<]+)<\/h2>/g), match => match[1]), readingOrder);
assert.deepStrictEqual(Array.from(html.matchAll(/<div class="technical-subsection"[^>]*>\s*<h3[^>]*>([^<]+)<\/h3>/g), match => match[1]),
  ['Policy Failure Detection and Correction', 'Data Efficiency and Robustness', 'Robotwin Benchmark']);
for (const match of navigation.matchAll(/href="#([^"]+)"/g)) {
  assert(html.includes('id="' + match[1] + '"'), 'section navigation must resolve to an existing section');
}

class Element {
  constructor(tag = 'div') {
    this.tag = tag; this.listeners = {}; this.attrs = {}; this.style = {}; this.hidden = false;
    this.textContent = ''; this.children = {}; this.paused = true; this.readyState = 2; this.currentTime = 0;
    const classes = new Set();
    this.classList = { contains: name => classes.has(name), toggle: (name, yes) => yes ? classes.add(name) : classes.delete(name) };
  }
  addEventListener(name, callback) { (this.listeners[name] || (this.listeners[name] = [])).push(callback); }
  fire(name, props = {}) {
    const event = Object.assign({ target: this, currentTarget: this, preventDefault() { this.prevented = true; } }, props);
    (this.listeners[name] || []).forEach(fn => fn(event)); return event;
  }
  click() { this.fire('click'); }
  querySelector(selector) { return this.children[selector]; }
  querySelectorAll(selector) { return selector === 'video' ? (this.children.videos || [this.children.video]) : this.children[selector]; }
  setAttribute(key, value) { this.attrs[key] = value; }
  removeAttribute(key) { delete this.attrs[key]; }
  getBoundingClientRect() { return { top: 500 }; }
  scrollIntoView() { this.scrolledIntoView = true; }
  focus() { this.focused = true; }
  pause() { this.paused = true; }
}

function fixture(hash = '') {
  const visualization = new Element(), picker = new Element(), announcement = new Element();
  const cards = taskData.map(task => {
    const markup = html.match(new RegExp('<article class="task-card" id="' + task.id + '"[^>]*>([\\s\\S]*?)</article>'))[1];
    assert(markup.includes('./media/robotwin/' + task.media_directory + '/rollout.mp4'));
    assert(markup.includes('./media/robotwin/' + task.media_directory + '/success-rate.svg'));
    const card = new Element('article'); card.id = task.id; card.children.video = new Element('video'); return card;
  });
  const buttons = taskData.map(task => {
    const markup = html.match(new RegExp('<button type="button" data-task="' + task.id + '"([^>]*)>(.*?)</button>'));
    assert(markup[1].includes('aria-controls="' + task.id + '"'));
    const button = new Element('button'); button.textContent = markup[2]; return button;
  });
  visualization.children['.task-card'] = cards; picker.children.button = buttons;
  const pipelinePicker = new Element(), pipelineAnnouncement = new Element();
  const pipelinePanels = pipelineTasks.map((task, index) => {
    const markup = html.match(new RegExp('<figure class="pipeline-video" id="pipeline-' + task + '"([^>]*)>([\\s\\S]*?)</figure>'));
    assert.strictEqual(/\bhidden\b/.test(markup[1]), index !== 0, 'Hang Mug is the only default visible video');
    assert(markup[2].includes('./assets/videos/pipeline/' + task + '/combined.mp4'));
    const panel = new Element('figure'); panel.id = 'pipeline-' + task; panel.children.video = new Element('video'); return panel;
  });
  const pipelineButtons = pipelineTasks.map(task => {
    const markup = html.match(new RegExp('<button type="button" data-pipeline-task="' + task + '"([^>]*)>(.*?)</button>'));
    assert(markup[1].includes('aria-controls="pipeline-' + task + '"'));
    const button = new Element('button'); button.textContent = markup[2]; return button;
  });
  pipelinePicker.children.button = pipelineButtons;
  const domainPicker = new Element(), domainAnnouncement = new Element();
  const domainPanels = pipelineTasks.map((task, index) => {
    const markup = html.match(new RegExp('<figure class="domain-randomization-video" id="domain-randomization-' + task + '"([^>]*)>([\\s\\S]*?)</figure>'));
    assert.strictEqual(/\bhidden\b/.test(markup[1]), index !== 0, 'Hang Mug is the only default domain randomization video');
    assert(markup[2].includes('./assets/videos/pipeline/domain-randomization/' + task + '.mp4'));
    assert(markup[2].includes('width="960" height="720"'));
    for (const attribute of ['src', 'poster']) {
      const mediaPath = markup[2].match(new RegExp(attribute + '="([^"?]+)'))[1];
      assert(fs.existsSync(root + '/' + mediaPath), 'domain randomization media must exist: ' + mediaPath);
    }
    const panel = new Element('figure'); panel.id = 'domain-randomization-' + task; panel.children.video = new Element('video'); return panel;
  });
  const domainButtons = pipelineTasks.map(task => {
    const markup = html.match(new RegExp('<button type="button" data-domain-randomization-task="' + task + '"([^>]*)>(.*?)</button>'));
    assert(markup[1].includes('aria-controls="domain-randomization-' + task + '"'));
    const button = new Element('button'); button.textContent = markup[2]; return button;
  });
  domainPicker.children.button = domainButtons;
  const detectionPicker = new Element(), detectionAnnouncement = new Element();
  const detectionPanels = pipelineTasks.map((task, index) => {
    const markup = html.match(new RegExp('<div class="detection-task" id="detection-' + task + '"([^>]*)>([\\s\\S]*?)\\n            </div>'));
    assert.strictEqual(/\bhidden\b/.test(markup[1]), index !== 0, 'Hang Mug is the default corrective data generation video');
    const directory = './assets/videos/pipeline/failure-detection-correction/' + task + '/';
    for (const name of ['rollout.mp4', 'poster.jpg']) {
      assert(markup[2].includes(directory + name));
      assert(fs.existsSync(root + '/' + directory + name));
    }
    assert.strictEqual((markup[2].match(/<video\b/g) || []).length, 1);
    assert(!/<figcaption\b|detection-correction-grid|policy_brown|correction_green/.test(markup[2]));
    assert(markup[2].includes('width="1920" height="1080"'));
    const panel = new Element(); panel.id = 'detection-' + task;
    panel.children.videos = [new Element('video')];
    return panel;
  });
  const detectionButtons = pipelineTasks.map(task => {
    const markup = html.match(new RegExp('<button type="button" data-detection-task="' + task + '"([^>]*)>(.*?)</button>'));
    assert(markup[1].includes('aria-controls="detection-' + task + '"'));
    const button = new Element('button'); button.textContent = markup[2]; return button;
  });
  detectionPicker.children.button = detectionButtons;
  const sections = Array.from(navigation.matchAll(/href="#([^"]+)"/g), match => { const section = new Element(); section.id = match[1]; return section; });
  const navLinks = sections.map(section => { const link = new Element('a'); link.hash = '#' + section.id; return link; });
  const elements = { '.task-list': visualization, '.task-picker': pipelinePicker, '#robotwin .task-picker': picker,
    '#task-announcement': announcement, '.scroll-progress': new Element(),
    '#data-generation .pipeline-picker': pipelinePicker, '#pipeline-announcement': pipelineAnnouncement,
    '#sim-to-real .domain-randomization-picker': domainPicker, '#domain-randomization-announcement': domainAnnouncement,
    '#corrective-data-generation .detection-picker': detectionPicker, '#detection-announcement': detectionAnnouncement };
  sections.forEach(section => { elements['#' + section.id] = section; });
  const win = new Element(); win.location = { hash }; win.innerHeight = 900; win.scrollY = 0;
  win.history = { pushState: (_, __, target) => { win.location.hash = target; } };
  const frames = []; win.requestAnimationFrame = callback => frames.push(callback);
  const doc = new Element(); doc.documentElement = { scrollHeight: 5000 };
  doc.querySelector = selector => elements[selector];
  doc.querySelectorAll = selector => selector === '.section-nav a' ? navLinks :
    selector === '#data-generation .pipeline-video' ? pipelinePanels :
    selector === '#sim-to-real .domain-randomization-video' ? domainPanels :
    selector === '#corrective-data-generation .detection-task' ? detectionPanels :
    [...cards, ...pipelinePanels, ...domainPanels, ...detectionPanels].flatMap(panel => panel.children.videos || [panel.children.video]);
  const observers = [];
  vm.runInNewContext(source, { window: win, document: doc,
    IntersectionObserver: class { constructor(callback) { observers.push(callback); } observe() {} } });
  vm.runInNewContext(pipelineSource, { document: doc });
  function selected(index) {
    assert.deepStrictEqual(cards.map(card => card.hidden), cards.map((_, i) => i !== index));
    assert.deepStrictEqual(buttons.map(button => button.attrs['aria-pressed']), cards.map((_, i) => String(i === index)));
    assert.strictEqual(cards.filter(card => !card.hidden).length, 1);
    assert(buttons[index].classList.contains('active'));
  }
  function pipelineSelected(index) {
    assert.deepStrictEqual(pipelinePanels.map(panel => panel.hidden), pipelinePanels.map((_, i) => i !== index));
    assert.deepStrictEqual(pipelineButtons.map(button => button.attrs['aria-pressed']), pipelinePanels.map((_, i) => String(i === index)));
    assert.strictEqual(pipelinePanels.filter(panel => !panel.hidden).length, 1);
    assert(pipelineButtons[index].classList.contains('active'));
  }
  function domainSelected(index) {
    assert.deepStrictEqual(domainPanels.map(panel => panel.hidden), domainPanels.map((_, i) => i !== index));
    assert.deepStrictEqual(domainButtons.map(button => button.attrs['aria-pressed']), domainPanels.map((_, i) => String(i === index)));
    assert.strictEqual(domainPanels.filter(panel => !panel.hidden).length, 1);
    assert(domainButtons[index].classList.contains('active'));
  }
  function detectionSelected(index) {
    assert.deepStrictEqual(detectionPanels.map(panel => panel.hidden), detectionPanels.map((_, i) => i !== index));
    assert.deepStrictEqual(detectionButtons.map(button => button.attrs['aria-pressed']), detectionPanels.map((_, i) => String(i === index)));
    assert.strictEqual(detectionPanels.filter(panel => !panel.hidden).length, 1);
    assert(detectionButtons[index].classList.contains('active'));
  }
  return { visualization, picker, announcement, cards, buttons, win, doc, observers, frames, selected,
    pipelinePicker, pipelineAnnouncement, pipelinePanels, pipelineButtons, pipelineSelected,
    domainPicker, domainAnnouncement, domainPanels, domainButtons, domainSelected,
    detectionPicker, detectionAnnouncement, detectionPanels, detectionButtons, detectionSelected };
}

assert(!/id="(?:method|recovery|main-results)"/.test(html));
assert(!/<table\b|class="task-meta"|UniKey Success Rate:/.test(html));
assert(!/src="\.\/assets\/(?:method-demo|recovery-demo)\.js/.test(html));
const f = fixture(); f.selected(0);
assert(!f.picker.hidden);
f.buttons.forEach((button, index) => {
  button.click(); f.selected(index);
  assert.strictEqual(f.win.location.hash, '#' + taskData[index].id);
});
f.cards[9].children.video.paused = false;
f.cards[0].children.video.currentTime = 4;
f.buttons[0].click(); f.selected(0);
assert(f.cards[9].children.video.paused, 'switching tasks pauses the previous video');
assert.strictEqual(f.cards[0].children.video.currentTime, 0, 'switching back resets the selected clip');
f.cards[0].children.video.paused = false; f.cards[0].children.video.currentTime = 2;
f.buttons[0].click(); assert.strictEqual(f.cards[0].children.video.currentTime, 2, 'clicking the active task preserves playback');
f.picker.fire('keydown', { key: 'End' }); f.selected(9); assert(f.buttons[9].focused);
f.picker.fire('keydown', { key: 'ArrowRight' }); f.selected(9);
f.picker.fire('keydown', { key: 'Home' }); f.selected(0);
f.visualization.fire('keydown', { key: 'ArrowRight' }); f.selected(1);
f.visualization.fire('keydown', { key: 'ArrowRight', target: f.cards[1].children.video }); f.selected(1);
f.picker.fire('keydown', { key: 'End', ctrlKey: true }); f.selected(1);
f.win.location.hash = '#rank-blocks-color'; f.win.fire('popstate'); f.selected(2);
f.win.location.hash = '#dump-bin-bigbin'; f.win.fire('hashchange'); f.selected(6);
assert(f.visualization.scrolledIntoView);
assert(f.announcement.textContent.includes(f.buttons[6].textContent));
f.cards[6].children.video.paused = false;
f.observers[0]([{ target: f.cards[6].children.video, isIntersecting: false }]); assert(f.cards[6].children.video.paused);
f.cards[6].children.video.paused = false;
f.doc.hidden = true; f.doc.fire('visibilitychange'); assert(f.cards[6].children.video.paused);
f.win.fire('resize'); f.frames.forEach(callback => callback()); f.selected(6);
const linked = fixture('#move-stapler-pad'); linked.selected(9);
f.pipelineSelected(0); assert(!f.pipelinePicker.hidden);
const beforeHash = f.win.location.hash, beforeScroll = f.win.scrollY;
f.pipelineButtons.forEach((button, index) => {
  button.click(); f.pipelineSelected(index); f.selected(6); f.domainSelected(0);
  assert.strictEqual(f.win.location.hash, beforeHash, 'pipeline buttons must not navigate');
  assert.strictEqual(f.win.scrollY, beforeScroll, 'pipeline buttons must not scroll');
  assert(f.pipelinePanels.every(panel => !panel.scrolledIntoView));
});
f.pipelinePanels[3].children.video.paused = false;
f.pipelinePanels[0].children.video.currentTime = 4;
f.pipelineButtons[0].click(); f.pipelineSelected(0);
assert(f.pipelinePanels[3].children.video.paused, 'pipeline switching pauses the previous video');
assert.strictEqual(f.pipelinePanels[0].children.video.currentTime, 0);
f.pipelinePanels[0].children.video.currentTime = 2;
f.pipelineButtons[0].click(); assert.strictEqual(f.pipelinePanels[0].children.video.currentTime, 2);
f.pipelinePicker.fire('keydown', { key: 'End' }); f.pipelineSelected(3); assert(f.pipelineButtons[3].focused);
f.pipelinePicker.fire('keydown', { key: 'ArrowRight' }); f.pipelineSelected(3);
f.pipelinePicker.fire('keydown', { key: 'ArrowLeft' }); f.pipelineSelected(2);
f.pipelinePicker.fire('keydown', { key: 'Home' }); f.pipelineSelected(0);
assert(f.pipelineAnnouncement.textContent.includes('Hang Mug'));
f.pipelinePanels[0].children.video.paused = false;
f.observers[0]([{ target: f.pipelinePanels[0].children.video, isIntersecting: false }]);
assert(f.pipelinePanels[0].children.video.paused);
linked.pipelineSelected(0);
f.domainSelected(0); assert(!f.domainPicker.hidden);
f.pipelinePanels[0].children.video.paused = false;
f.pipelinePanels[0].children.video.currentTime = 3;
f.domainButtons.forEach((button, index) => {
  button.click(); f.domainSelected(index); f.pipelineSelected(0); f.selected(6);
  assert.strictEqual(f.win.location.hash, beforeHash, 'domain randomization buttons must not navigate');
  assert.strictEqual(f.win.scrollY, beforeScroll, 'domain randomization buttons must not scroll');
  assert(f.domainPanels.every(panel => !panel.scrolledIntoView));
  assert(!f.pipelinePanels[0].children.video.paused, 'domain switching must preserve agentic playback');
  assert.strictEqual(f.pipelinePanels[0].children.video.currentTime, 3);
});
f.domainPanels[3].children.video.paused = false;
f.domainPanels[0].children.video.currentTime = 4;
f.domainButtons[0].click(); f.domainSelected(0);
assert(f.domainPanels[3].children.video.paused, 'domain switching pauses the previous video');
assert.strictEqual(f.domainPanels[0].children.video.currentTime, 0);
f.domainPanels[0].children.video.paused = false;
f.domainPanels[0].children.video.currentTime = 2;
f.domainButtons[0].click();
assert.strictEqual(f.domainPanels[0].children.video.currentTime, 2, 'clicking the active domain task preserves playback');
assert(!f.domainPanels[0].children.video.paused);
f.pipelineButtons[3].click(); f.pipelineSelected(3); f.domainSelected(0);
assert.strictEqual(f.domainPanels[0].children.video.currentTime, 2, 'agentic switching must preserve domain playback');
assert(!f.domainPanels[0].children.video.paused);
f.domainPicker.fire('keydown', { key: 'End' }); f.domainSelected(3); assert(f.domainButtons[3].focused);
f.domainPicker.fire('keydown', { key: 'ArrowRight' }); f.domainSelected(3);
f.domainPicker.fire('keydown', { key: 'ArrowLeft' }); f.domainSelected(2);
f.domainPicker.fire('keydown', { key: 'Home' }); f.domainSelected(0);
f.domainPicker.fire('keydown', { key: 'ArrowLeft' }); f.domainSelected(0);
f.domainPicker.fire('keydown', { key: 'End', ctrlKey: true }); f.domainSelected(0);
assert(f.domainAnnouncement.textContent.includes('Hang Mug: Domain Randomization'));
f.domainPanels[0].children.video.paused = false;
f.observers[0]([{ target: f.domainPanels[0].children.video, isIntersecting: false }]);
assert(f.domainPanels[0].children.video.paused, 'domain video pauses when offscreen');
f.domainPanels[0].children.video.paused = false;
f.doc.fire('visibilitychange'); assert(f.domainPanels[0].children.video.paused, 'domain video pauses when the page is hidden');
linked.domainSelected(0);
f.pipelineButtons[0].click();
f.domainButtons[0].click();
f.detectionSelected(0); assert(!f.detectionPicker.hidden);
f.detectionButtons.forEach((button, index) => {
  button.click(); f.detectionSelected(index); f.pipelineSelected(0); f.domainSelected(0); f.selected(6);
  assert.strictEqual(f.win.location.hash, beforeHash);
  assert.strictEqual(f.win.scrollY, beforeScroll);
});
f.detectionPanels[3].children.videos.forEach(video => { video.paused = false; });
f.detectionPanels[0].children.videos.forEach(video => { video.currentTime = 2; });
f.detectionButtons[0].click(); f.detectionSelected(0);
assert(f.detectionPanels[3].children.videos.every(video => video.paused), 'switching tasks pauses the outgoing video');
assert(f.detectionPanels[0].children.videos.every(video => video.currentTime === 0), 'switching tasks resets the incoming video');
f.detectionPanels[0].children.videos.forEach(video => { video.paused = false; video.currentTime = 1; });
f.detectionButtons[0].click();
assert(f.detectionPanels[0].children.videos.every(video => !video.paused && video.currentTime === 1), 'active task clicks preserve playback');
f.domainButtons[2].click(); f.domainSelected(2); f.detectionSelected(0);
assert(f.detectionPanels[0].children.videos.every(video => !video.paused && video.currentTime === 1));
f.detectionPicker.fire('keydown', { key: 'End' }); f.detectionSelected(3); assert(f.detectionButtons[3].focused);
f.detectionPicker.fire('keydown', { key: 'ArrowLeft' }); f.detectionSelected(2);
f.detectionPicker.fire('keydown', { key: 'Home' }); f.detectionSelected(0);
assert(f.detectionAnnouncement.textContent.includes('Hang Mug: Policy Failure Detection and Correction'));
f.detectionPanels[0].children.videos.forEach(video => { video.paused = false; });
f.doc.fire('visibilitychange');
assert(f.detectionPanels[0].children.videos.every(video => video.paused), 'the video pauses when the page is hidden');
linked.detectionSelected(0);
console.log('PASS: independent four-task agentic/domain/detection selectors, four single-player corrective videos without captions, matching media, playback controls, keyboard behavior, and all ten RoboTwin tasks.');
