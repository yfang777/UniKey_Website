(() => {
  'use strict';
  const demo = document.querySelector('#program-demo');
  if (!demo) return;
  const taskPicker = demo.querySelector('#program-task');
  const stagePicker = demo.querySelector('#program-stage');
  const instruction = demo.querySelector('#program-instruction');
  const code = demo.querySelector('#program-code');
  const codeWindow = demo.querySelector('.program-code-window');
  const empty = demo.querySelector('#program-code-empty');
  const context = demo.querySelector('#program-context');
  const source = demo.querySelector('#program-source');
  const video = demo.querySelector('#program-video');
  const phase = demo.querySelector('#program-phase');
  const steps = Array.from(demo.querySelectorAll('.program-steps li'));
  const play = demo.querySelector('#program-play');
  const replay = demo.querySelector('#program-replay');
  const seek = demo.querySelector('#program-seek');
  const time = demo.querySelector('#program-time');
  const notice = demo.querySelector('#program-notice');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let tasks, currentTask, views = [], characterCount = 0;
  let activeBlock = -1, revealed = -1, animationFrame = 0, pendingSeek = 0;
  let mediaRequest = null, mediaUrl = null, loadingVideo = false;

  function update() {
    if (!currentTask) return;
    const position = pendingSeek === null ? video.currentTime : pendingSeek;
    const mode = position < currentTask.orbit_end_s ? 'orbit' :
      position < currentTask.execution_start_s ? 'generation' : 'execution';
    const progress = Math.min(1, Math.max(0, (position - currentTask.orbit_end_s) /
      (currentTask.execution_start_s - currentTask.orbit_end_s)));
    const count = reducedMotion.matches ? characterCount : Math.floor(progress * characterCount);
    if (count !== revealed) {
      let offset = 0;
      views.forEach((view, index) => {
        const text = currentTask.blocks[index].code;
        const shown = Math.min(text.length, Math.max(0, count - offset));
        view.section.hidden = shown === 0;
        view.text.textContent = text.slice(0, shown);
        offset += text.length;
      });
      empty.hidden = count > 0;
      revealed = count;
      if (mode === 'generation') codeWindow.scrollTop = codeWindow.scrollHeight;
    }
    let block = -1;
    if (mode === 'execution') {
      const elapsed = position - currentTask.execution_start_s;
      currentTask.blocks.forEach((item, index) => {
        if (item.start_s !== null && item.start_s <= elapsed + 0.000002) block = index;
      });
    }
    if (block !== activeBlock) {
      views.forEach((view, index) => view.section.classList.toggle('is-active', index === block));
      activeBlock = block;
      if (block >= 1) {
        stagePicker.value = String(block - 1);
        codeWindow.scrollTop = views[block].section.offsetTop - 12;
      } else {
        codeWindow.scrollTop = 0;
      }
    }
    const message = mode === 'orbit' ? (position === 0 && video.paused ?
      'Ready to explore the 3D keypoints' : '3D keypoints · Camera orbit') :
      mode === 'generation' ? 'Generating keypoint program · Scene held still' :
      `${video.ended ? 'Completed' : 'Executing'} · ${currentTask.blocks[block].label}`;
    if (phase.textContent !== message) phase.textContent = message;
    const stepIndex = ['orbit', 'generation', 'execution'].indexOf(mode);
    steps.forEach((step, index) => {
      step.classList.toggle('is-active', index === stepIndex);
      step.classList.toggle('is-complete', index < stepIndex);
      if (index === stepIndex) step.setAttribute('aria-current', 'step');
      else step.removeAttribute('aria-current');
    });
    demo.dataset.phase = mode;
    seek.value = String(position);
    seek.setAttribute('aria-valuetext', `${position.toFixed(2)} of ${currentTask.duration_s.toFixed(2)} seconds`);
    time.textContent = `${position.toFixed(2)} / ${currentTask.duration_s.toFixed(2)} s`;
    play.textContent = video.paused ? 'Play' : 'Pause';
  }

  function tick() {
    update();
    if (!video.paused && !video.ended) animationFrame = requestAnimationFrame(tick);
  }

  function seekTo(position) {
    pendingSeek = position;
    if (!loadingVideo && video.readyState >= 1) {
      video.currentTime = position;
      pendingSeek = null;
    }
    update();
  }

  async function loadVideo(task) {
    const request = new AbortController();
    mediaRequest = request;
    loadingVideo = true;
    play.disabled = replay.disabled = seek.disabled = stagePicker.disabled = true;
    notice.textContent = 'Loading demonstration…';
    notice.hidden = false;
    try {
      // Blob playback supports seeking on the local Python server, too.
      const response = await fetch(task.video, {signal: request.signal});
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const blob = await response.blob();
      if (request.signal.aborted) return;
      const previousUrl = mediaUrl;
      mediaUrl = URL.createObjectURL(blob);
      loadingVideo = false;
      video.src = mediaUrl;
      video.preload = 'auto';
      video.load();
      if (previousUrl) URL.revokeObjectURL(previousUrl);
    } catch (error) {
      if (error.name === 'AbortError') return;
      notice.textContent = 'The demonstration could not load. Select another task or reload the page to retry.';
      notice.hidden = false;
    }
  }

  function selectTask(id) {
    video.pause();
    if (mediaRequest) mediaRequest.abort();
    cancelAnimationFrame(animationFrame);
    currentTask = tasks.find(task => task.id === id);
    taskPicker.value = id;
    activeBlock = revealed = -1;
    pendingSeek = 0;
    instruction.textContent = currentTask.instruction;
    context.textContent = currentTask.context;
    source.href = currentTask.program;
    characterCount = currentTask.blocks.reduce((sum, block) => sum + block.code.length, 0);
    views = currentTask.blocks.map(block => {
      const section = document.createElement('section');
      section.className = 'program-code-block';
      const label = document.createElement('h4');
      label.textContent = block.label;
      const pre = document.createElement('pre');
      pre.className = 'program-code';
      const text = document.createElement('code');
      pre.append(text);
      section.append(label, pre);
      return {section, text};
    });
    code.replaceChildren(...views.map(view => view.section));
    codeWindow.scrollTop = 0;
    stagePicker.replaceChildren(...currentTask.blocks.slice(1).map((block, index) =>
      new Option(block.label, String(index))));
    seek.max = String(currentTask.duration_s);
    seek.step = String(1 / currentTask.fps);
    video.poster = currentTask.poster;
    video.setAttribute('aria-label', `${currentTask.title}: 3D keypoints, program generation, and execution`);
    [video.width, video.height] = currentTask.resolution;
    demo.dataset.task = id;
    update();
    loadVideo(currentTask);
  }

  async function startPlayback() {
    const task = currentTask;
    if (reducedMotion.matches && video.currentTime < task.execution_start_s) seekTo(task.execution_start_s);
    notice.hidden = true;
    try {
      await video.play();
    } catch (error) {
      if (currentTask !== task || error.name === 'AbortError') return;
      notice.textContent = 'Playback could not start. Try Play again.';
      notice.hidden = false;
      update();
    }
  }

  play.addEventListener('click', () => {
    if (!video.paused) { video.pause(); return; }
    if (video.ended) seekTo(0);
    startPlayback();
  });
  replay.addEventListener('click', () => {
    video.pause();
    seekTo(0);
    startPlayback();
  });
  seek.addEventListener('input', () => {
    let position = Number(seek.value);
    if (reducedMotion.matches && position < currentTask.execution_start_s) position = currentTask.execution_start_s;
    seekTo(position);
  });
  stagePicker.addEventListener('change', () => {
    video.pause();
    seekTo(currentTask.execution_start_s + currentTask.blocks[Number(stagePicker.value) + 1].start_s);
  });
  taskPicker.addEventListener('change', () => selectTask(taskPicker.value));
  video.addEventListener('loadedmetadata', () => {
    if (loadingVideo || video.currentSrc !== mediaUrl) return;
    if (pendingSeek !== null) seekTo(pendingSeek);
    play.disabled = replay.disabled = seek.disabled = stagePicker.disabled = false;
    notice.hidden = true;
    update();
  });
  video.addEventListener('play', () => { cancelAnimationFrame(animationFrame); tick(); });
  video.addEventListener('pause', () => cancelAnimationFrame(animationFrame));
  ['pause', 'ended', 'seeking', 'seeked', 'timeupdate'].forEach(event => video.addEventListener(event, update));
  video.addEventListener('error', () => {
    notice.textContent = 'The demonstration could not decode. Select another task or reload the page.';
    notice.hidden = false;
  });
  reducedMotion.addEventListener('change', () => {
    if (!currentTask) return;
    if (reducedMotion.matches && !video.paused && video.currentTime < currentTask.execution_start_s)
      seekTo(currentTask.execution_start_s);
    revealed = -1;
    update();
  });
  document.addEventListener('visibilitychange', () => { if (document.hidden) video.pause(); });
  // On mobile, the code panel can stay in view while the scene scrolls above it.
  const visibility = new IntersectionObserver(([entry]) => {
    if (!entry.isIntersecting) video.pause();
  });
  visibility.observe(demo);
  window.addEventListener('pagehide', () => {
    video.pause();
    if (mediaRequest) mediaRequest.abort();
    if (mediaUrl) URL.revokeObjectURL(mediaUrl);
  });

  async function initialize() {
    try {
      const response = await fetch(demo.dataset.manifest);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const manifest = await response.json();
      if (!Array.isArray(manifest.tasks) || !manifest.tasks.length || manifest.tasks.some(task =>
        !Array.isArray(task.blocks) || task.blocks.length < 2 || task.blocks.some(block =>
          typeof block.code !== 'string' || typeof block.label !== 'string') ||
        !Number.isFinite(task.duration_s) || task.duration_s <= task.execution_start_s ||
        task.orbit_end_s <= 0 || task.execution_start_s <= task.orbit_end_s))
        throw new Error('Invalid demonstration manifest');
      tasks = manifest.tasks;
      selectTask(taskPicker.value);
      taskPicker.disabled = false;
      demo.querySelector('.program-controls').hidden = false;
      demo.querySelector('.program-stage-control').hidden = false;
      video.controls = false;
    } catch {
      notice.textContent = 'The programs could not load. The recorded example and full source are still available.';
      notice.hidden = false;
    }
  }
  initialize();
})();
