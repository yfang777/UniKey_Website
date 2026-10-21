(() => {
  const demo = document.querySelector('#recovery-live');
  if (!demo) return;
  const viewport = demo.querySelector('.recovery-viewport');
  const canvas = demo.querySelector('canvas');
  const context = canvas.getContext('2d');
  const poster = demo.querySelector('.recovery-poster');
  const task = demo.querySelector('#recovery-task');
  const connect = demo.querySelector('#recovery-connect');
  const pause = demo.querySelector('#recovery-pause');
  const reset = demo.querySelector('#recovery-reset');
  const connection = demo.querySelector('#recovery-connection');
  const motion = demo.querySelector('#recovery-motion');
  const latency = demo.querySelector('#recovery-latency');
  const notice = demo.querySelector('#recovery-notice');
  const buttons = [...demo.querySelectorAll('[data-key]')];
  const held = new Set();
  let socket = null, heartbeat = null, ready = false, painting = false;

  function send(message) {
    if (socket && socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify(message));
  }
  function highlight() {
    buttons.forEach(button => {
      const active = held.has(button.dataset.key);
      button.classList.toggle('active', active);
      button.setAttribute('aria-pressed', String(active));
    });
  }
  function key(key, pressed) {
    if (!ready || held.has(key) === pressed) return;
    if (pressed) held.add(key); else held.delete(key);
    highlight();
    send({type: 'key', key, pressed});
  }
  function release() {
    held.clear();
    highlight();
    send({type: 'release'});
  }
  function disconnect() {
    release();
    ready = false;
    clearInterval(heartbeat);
    if (socket) socket.close();
  }
  function setConnection(text, connected) {
    connection.textContent = text;
    connection.classList.toggle('connected', connected);
    connect.textContent = connected ? 'Disconnect' : 'Connect';
    pause.disabled = reset.disabled = !connected;
    task.disabled = connected;
  }
  function open(endpoint) {
    if (socket) disconnect();
    notice.textContent = '';
    poster.hidden = false;
    const url = new URL(endpoint, location.href);
    url.searchParams.set('task', task.value);
    const ws = new WebSocket(url);
    socket = ws;
    ws.binaryType = 'arraybuffer';
    setConnection('Connecting…', false);
    connect.textContent = 'Connecting…';
    connect.disabled = true;
    task.disabled = true;
    notice.textContent = 'Connecting to the simulator…';
    let timeout = setTimeout(() => {
      if (ws !== socket) return;
      notice.textContent = 'The simulator did not respond. Please try again.';
      ws.close();
    }, 10000);
    ws.addEventListener('open', () => {
      if (ws !== socket) return;
      clearTimeout(timeout);
      connection.textContent = 'Loading scene…';
      connect.textContent = 'Loading…';
      notice.textContent = 'Loading the selected task…';
      timeout = setTimeout(() => {
        if (ws !== socket) return;
        notice.textContent = 'The selected task took too long to load. Please try again.';
        ws.close();
      }, 90000);
      heartbeat = setInterval(() => send({type: 'ping', sent_at: performance.now()}), 1000);
    });
    ws.addEventListener('message', async event => {
      if (ws !== socket) return;
      if (typeof event.data !== 'string') {
        if (painting) return;
        painting = true;
        try {
          const bitmap = await createImageBitmap(new Blob([event.data], {type: 'image/jpeg'}));
          if (ws === socket) {
            canvas.width = bitmap.width;
            canvas.height = bitmap.height;
            context.drawImage(bitmap, 0, 0);
            poster.hidden = true;
          }
          bitmap.close();
        } finally { painting = false; }
        return;
      }
      const message = JSON.parse(event.data);
      if (message.type === 'ready' || message.type === 'state') {
        clearTimeout(timeout);
        notice.textContent = '';
        ready = true;
        connect.disabled = false;
        setConnection('Connected · LIVE', true);
        if (message.type === 'state') {
          motion.textContent = `Stage ${message.stage} · ${message.status}`;
          pause.textContent = message.paused ? 'Start / Resume' : 'Pause';
        }
      } else if (message.type === 'pong') {
        latency.textContent = `Latency ${Math.round(performance.now() - message.sent_at)} ms`;
      } else if (message.type === 'ended' || message.type === 'input_error') {
        notice.textContent = message.message;
      }
    });
    ws.addEventListener('error', () => {
      if (ws !== socket) return;
      clearTimeout(timeout);
      notice.textContent = 'Could not connect to the simulator. Please try again.';
    });
    ws.addEventListener('close', () => {
      if (ws !== socket) return;
      ready = false;
      held.clear();
      highlight();
      clearInterval(heartbeat);
      clearTimeout(timeout);
      connect.disabled = false;
      setConnection('Disconnected', false);
      latency.textContent = 'Latency —';
      motion.textContent = 'Connect, then select Start.';
      socket = null;
    });
  }
  connect.addEventListener('click', () => {
    if (ready) { disconnect(); return; }
    let endpoint = demo.dataset.backend;
    if (!endpoint && ['localhost', '127.0.0.1'].includes(location.hostname)) {
      endpoint = `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/ws`;
    }
    if (!endpoint) {
      notice.textContent = 'The demo server is not configured yet.';
      return;
    }
    open(endpoint);
  });
  pause.addEventListener('click', () => { release(); send({type: 'pause'}); });
  reset.addEventListener('click', () => { release(); send({type: 'reset'}); });
  viewport.addEventListener('keydown', event => {
    const value = event.key.toLowerCase();
    if (!'wasdqe'.includes(value) || value.length !== 1) return;
    event.preventDefault();
    key(value, true);
  });
  viewport.addEventListener('keyup', event => {
    const value = event.key.toLowerCase();
    if (!'wasdqe'.includes(value) || value.length !== 1) return;
    event.preventDefault();
    key(value, false);
  });
  viewport.addEventListener('focusout', event => {
    if (!viewport.contains(event.relatedTarget)) release();
  });
  canvas.addEventListener('pointerdown', () => viewport.focus({preventScroll: true}));
  poster.addEventListener('pointerdown', () => viewport.focus({preventScroll: true}));
  buttons.forEach(button => {
    button.addEventListener('pointerdown', event => {
      event.preventDefault();
      viewport.focus({preventScroll: true});
      button.setPointerCapture(event.pointerId);
      key(button.dataset.key, true);
    });
    ['pointerup', 'pointercancel', 'lostpointercapture'].forEach(name =>
      button.addEventListener(name, () => key(button.dataset.key, false)));
  });
  window.addEventListener('blur', release);
  document.addEventListener('visibilitychange', () => { if (document.hidden) release(); });
  window.addEventListener('pagehide', disconnect);
  highlight();
})();
