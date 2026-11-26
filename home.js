/* Ziad Hares, homepage interactions.
 * The hero sky is a live pixel-art scene that follows the current time in Dubai:
 * dithered sky gradient, sun or moon on an arc, stars, drifting pixel clouds tinted by
 * the time of day, the odd shooting star, and a time-travel slider to scrub the day. */
(function () {
  'use strict';
  document.documentElement.classList.add('js');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ------------------------------------------------------------ pixel icons */
  const PX = {
    target: ['..#####..', '.#.....#.', '#..###..#', '#.#...#.#', '#.#.+.#.#', '#.#...#.#', '#..###..#', '.#.....#.', '..#####..'],
    shield: ['#########', '#+++++++#', '#+++++#+#', '#++++#++#', '#+#+#+++#', '#++#++++#', '.#+++++#.', '..#+++#..', '...###...'],
    cloud: ['...###...', '..#+++#..', '.#+++++##', '#+++++++#', '#+++++++#', '.#######.'],
    lock: ['..#####..', '.#.....#.', '.#.....#.', '#########', '#+++++++#', '#+++#+++#', '#+++#+++#', '#+++++++#', '#########'],
    terminal: ['#########', '#+++++++#', '#########', '#.......#', '#.#.....#', '#..#....#', '#.#..##.#', '#.......#', '#########'],
    code: ['...#..+#...', '..#...+.#..', '.#...+...#.', '#....+....#', '.#...+...#.', '..#.+...#..', '...#+..#...'],
    db: ['.#######.', '#+++++++#', '#########', '#+++++#+#', '#########', '#+++++#+#', '.#######.'],
    bot: ['....#....', '....#....', '.#######.', '#+++++++#', '#+#+++#+#', '#+++++++#', '#++###++#', '.#######.'],
    mail: ['#########', '##+++++##', '#+#+++#+#', '#++#+#++#', '#+++#+++#', '#+++++++#', '#########'],
    phone: ['.#####.', '#+++++#', '#+++++#', '#+++++#', '#+++++#', '#######', '#++#++#', '.#####.'],
    linkedin: ['#########', '##+######', '#########', '##+#++###', '##+#+#+##', '##+#+#+##', '#########'],
    github: ['#.....#', '##...##', '#######', '#+###+#', '#######', '.#####.'],
    doc: ['#####..', '#+++##.', '#+++###', '#+++++#', '#+###+#', '#+++++#', '#+###+#', '#######'],
  };
  const EMOJI = { '🎯': 'target', '🛡': 'shield', '☁': 'cloud', '🔐': 'lock', '⚙': 'terminal', '🧩': 'code', '🗄': 'db', '🤖': 'bot' };

  function pxSvg(rows, a, b) {
    const w = Math.max(...rows.map(r => r.length)), h = rows.length;
    let rects = '';
    rows.forEach((row, y) => [...row].forEach((c, x) => {
      if (c === '#' || c === '+') rects += `<rect x="${x}" y="${y}" width="1.02" height="1.02" fill="${c === '#' ? a : b}"/>`;
    }));
    return `<svg viewBox="0 0 ${w} ${h}" shape-rendering="crispEdges" aria-hidden="true">${rects}</svg>`;
  }
  document.querySelectorAll('.skill-icon').forEach(el => {
    const key = EMOJI[el.textContent.replace(/️/g, '').trim()];
    if (key) el.innerHTML = pxSvg(PX[key], '#3b82f6', '#93c5fd');
  });
  document.querySelectorAll('[data-px]').forEach(el => {
    const rows = PX[el.dataset.px];
    if (rows) el.innerHTML = pxSvg(rows, '#60a5fa', '#1e3a8a');
  });

  /* ------------------------------------------------------------ nav */
  const nav = document.getElementById('nav');
  const toggle = document.getElementById('navToggle');
  const list = document.getElementById('navList');
  if (toggle && list) {
    toggle.addEventListener('click', () => {
      const open = list.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    list.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
      list.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
    }));
  }
  const progress = document.getElementById('scroll-progress');
  function onScroll() {
    const y = window.scrollY;
    if (nav) nav.classList.toggle('scrolled', y > 8);
    const max = document.documentElement.scrollHeight - window.innerHeight;
    if (progress) progress.style.width = (max > 0 ? (y / max) * 100 : 0) + '%';
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  const links = new Map([...document.querySelectorAll('.nav-list a[href^="#"]')].map(a => [a.getAttribute('href').slice(1), a]));
  if ('IntersectionObserver' in window) {
    const spy = new IntersectionObserver(entries => entries.forEach(e => {
      if (e.isIntersecting && links.has(e.target.id)) {
        links.forEach(a => a.classList.remove('active'));
        links.get(e.target.id).classList.add('active');
      }
    }), { rootMargin: '-45% 0px -50% 0px' });
    document.querySelectorAll('section[id]').forEach(s => spy.observe(s));
  }

  /* ------------------------------------------------------------ reveal + count-up */
  const revealSel = '.sec-head, .about-copy, .whoami, .experience-item, .skill-card, .project-card, .edu, .languages, .contact-panel, .stats, .marquee';
  const revealEls = document.querySelectorAll(revealSel);
  if ('IntersectionObserver' in window && !reduceMotion) {
    revealEls.forEach(el => {
      el.classList.add('reveal');
      const sibs = [...el.parentElement.children].filter(c => c.matches(revealSel));
      el.style.transitionDelay = Math.min(sibs.indexOf(el), 6) * 70 + 'ms';
    });
    const io = new IntersectionObserver(entries => entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    }), { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    revealEls.forEach(el => io.observe(el));
  }

  const nums = document.querySelectorAll('.stat-num[data-count]');
  function countUp(el) {
    const target = +el.dataset.count, suffix = el.dataset.suffix || '';
    const t0 = performance.now(), dur = 1400;
    (function step(t) {
      const p = Math.min(1, (t - t0) / dur), eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * eased).toLocaleString('en-US') + suffix;
      if (p < 1) requestAnimationFrame(step);
    })(t0);
  }
  if ('IntersectionObserver' in window && !reduceMotion) {
    const cio = new IntersectionObserver(entries => entries.forEach(e => {
      if (e.isIntersecting) { countUp(e.target); cio.unobserve(e.target); }
    }), { threshold: 0.6 });
    nums.forEach(n => cio.observe(n));
  }

  /* ------------------------------------------------------------ card spotlight */
  document.querySelectorAll('.project-card').forEach(card => {
    card.addEventListener('pointermove', e => {
      const r = card.getBoundingClientRect();
      card.style.setProperty('--mx', (e.clientX - r.left) + 'px');
      card.style.setProperty('--my', (e.clientY - r.top) + 'px');
    });
  });

  /* ------------------------------------------------------------ hero terminal */
  const termBody = document.getElementById('termBody');
  const TERM = [
    ['uptime --role', '<span class="c-ok">CTO @ Begad</span> · founder @ Computator'],
    ['git log --oneline | wc -l', '<span class="c-amber">2,400+</span> commits in 3.5 months'],
    ['systemctl status security', '<span class="c-ok">●</span> active (running) · ISO 27001'],
  ];
  if (termBody && !reduceMotion) {
    let html = '', li = 0, ci = 0;
    const caret = '<span class="caret"></span>';
    (function tick() {
      if (li >= TERM.length) { termBody.innerHTML = html + '<span class="c-dim">$</span> ' + caret; return; }
      const [cmd, out] = TERM[li];
      if (ci <= cmd.length) {
        termBody.innerHTML = html + '<span class="c-dim">$</span> ' + cmd.slice(0, ci) + caret;
        ci++;
        setTimeout(tick, 38 + Math.random() * 50);
      } else {
        html += '<span class="c-dim">$</span> ' + cmd + '\n' + out + '\n';
        termBody.innerHTML = html + caret;
        li++; ci = 0;
        setTimeout(tick, 420);
      }
    })();
  }

  /* ------------------------------------------------------------ live pixel sky */
  const sky = document.getElementById('sky');
  const canvas = document.getElementById('skyCanvas');
  if (!sky || !canvas || !canvas.getContext) return;
  const ctx = canvas.getContext('2d');
  const clock = document.getElementById('skyClock');
  const slider = document.getElementById('timeTravel');
  const liveBtn = document.getElementById('timeLive');

  // [minute of day, sky top, sky bottom, cloud light, cloud shade, star alpha]
  const KEYS = [
    [0,    '#03050f', '#0b1430', '#3a4572', '#232c50', 1],
    [300,  '#05081a', '#141a3d', '#3c4674', '#262f55', 0.9],
    [365,  '#1a1f4a', '#6b4a7a', '#8a7fa8', '#5e5580', 0.45],
    [405,  '#3b5aa0', '#f2a56b', '#ffd6b0', '#e8a08a', 0.05],
    [480,  '#3f86d6', '#bfe0f5', '#ffffff', '#cfdff0', 0],
    [720,  '#2f7fe0', '#cfe8f7', '#ffffff', '#d4e2f0', 0],
    [990,  '#3a80d0', '#ecdcbc', '#fffaf0', '#e0d4c2', 0],
    [1060, '#3c4f9a', '#f08a5d', '#ffc59e', '#d9776a', 0.05],
    [1110, '#1d2156', '#8a4a78', '#9c6b92', '#5a3e6e', 0.4],
    [1190, '#070b1f', '#18204a', '#3e4976', '#273055', 0.9],
    [1440, '#03050f', '#0b1430', '#3a4572', '#232c50', 1],
  ];
  const SUNRISE = 400, SUNSET = 1065;          // roughly Dubai year-round, in minutes
  const hex = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
  const mix = (a, b, t) => a.map((v, i) => Math.round(v + (b[i] - v) * t));
  const rgb = c => `rgb(${c[0]},${c[1]},${c[2]})`;
  const BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]];

  function palette(m) {
    let i = 0;
    while (i < KEYS.length - 2 && m >= KEYS[i + 1][0]) i++;
    const a = KEYS[i], b = KEYS[i + 1], t = (m - a[0]) / (b[0] - a[0]);
    return {
      top: mix(hex(a[1]), hex(b[1]), t), bottom: mix(hex(a[2]), hex(b[2]), t),
      light: mix(hex(a[3]), hex(b[3]), t), shade: mix(hex(a[4]), hex(b[4]), t),
      stars: a[5] + (b[5] - a[5]) * t,
    };
  }
  function phaseName(m) {
    if (m < 330 || m >= 1190) return 'night';
    if (m < SUNRISE - 10) return 'dawn';
    if (m < SUNRISE + 40) return 'sunrise';
    if (m < 690) return 'morning';
    if (m < 810) return 'noon';
    if (m < SUNSET - 30) return 'afternoon';
    if (m < SUNSET + 30) return 'sunset';
    return 'dusk';
  }
  function dubaiMinutes() {
    const parts = new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Dubai', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(new Date());
    const get = t => +parts.find(p => p.type === t).value;
    return get('hour') * 60 + get('minute');
  }
  function dubaiDayOfYear() {
    const d = new Date(new Date().toLocaleString('en-US', { timeZone: 'Asia/Dubai' }));
    return Math.floor((d - new Date(d.getFullYear(), 0, 0)) / 864e5);
  }

  // Deterministic randomness: today's weather and star field are the same for every visitor.
  function rng(seed) { return () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296); }

  let W = 0, H = 366, bg = null, bgKey = '', stars = [], clouds = [], shooting = null;
  let minute = dubaiMinutes(), live = true, pal = palette(minute);
  const tParam = /^(\d{1,2}):(\d{2})$/.exec(new URLSearchParams(location.search).get('t') || '');
  if (tParam && +tParam[1] < 24 && +tParam[2] < 60) {      // ?t=18:00 shares a fixed time of day
    minute = +tParam[1] * 60 + +tParam[2]; live = false; pal = palette(minute);
    if (liveBtn) liveBtn.classList.remove('on');
    if (slider) slider.value = minute;
  }

  function makeCloud(r, layer) {
    const w = Math.floor(18 + r() * 16 + layer * 10), h = Math.ceil(w * 0.5);
    const grid = [];
    for (let y = 0; y < h; y++) grid.push(new Array(w).fill(0));
    const fill = (cx, cy, rad) => {
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
        const dx = x - cx, dy = y - cy;
        if (dx * dx + dy * dy <= rad * rad + rad * 0.6) grid[y][x] = 1;
      }
    };
    for (let y = h - 4; y < h; y++) for (let x = 2; x < w - 2; x++) grid[y][x] = 1;        // flat base
    grid[h - 1][2] = grid[h - 1][w - 3] = 0;
    fill(w * (0.45 + (r() - 0.5) * 0.15), h - 1 - h * 0.42, h * 0.5);                      // main puff
    const extra = 1 + Math.floor(r() * 3);
    for (let i = 0; i < extra; i++) {
      const rad = h * (0.26 + r() * 0.16);
      fill(w * (0.16 + r() * 0.68), h - 3 - rad * 0.55, rad);
    }
    return { grid, w, h, layer, x: r() * (W + w) - w, y: Math.floor(8 + r() * H * 0.4 + layer * 22), speed: 0.5 + layer * 0.7 + r() * 0.4 };
  }

  function resize() {
    const scale = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--px')) || 1.5;
    const newW = Math.max(60, Math.round(sky.clientWidth / scale));
    if (newW === W) return;
    W = newW;
    canvas.width = W; canvas.height = H;
    const r = rng(dubaiDayOfYear() * 7919 + 17);
    stars = Array.from({ length: Math.round(W * 0.32) }, () => ({ x: Math.floor(r() * W), y: Math.floor(r() * H * 0.68), b: r(), ph: r() * 6.28 }));
    const count = 3 + Math.floor(r() * 5);                    // 3–7 clouds: some days are clearer than others
    clouds = Array.from({ length: count }, (_, i) => makeCloud(r, i % 2));
    clouds.sort((a, b) => a.layer - b.layer);
    bgKey = '';
  }

  function paintBackground() {
    const key = W + ':' + Math.round(minute);
    if (key === bgKey) return;
    bgKey = key;
    bg = document.createElement('canvas'); bg.width = W; bg.height = H;
    const bctx = bg.getContext('2d'), img = bctx.createImageData(W, H), d = img.data;
    const BANDS = 14;
    for (let y = 0; y < H; y++) {
      const t = y / (H - 1);
      for (let x = 0; x < W; x++) {
        const q = Math.min(1, Math.max(0, Math.round(t * BANDS + (BAYER[y & 3][x & 3] / 16 - 0.47)) / BANDS));
        const c = mix(pal.top, pal.bottom, q * q * 0.35 + q * 0.65);
        const i = (y * W + x) * 4;
        d[i] = c[0]; d[i + 1] = c[1]; d[i + 2] = c[2]; d[i + 3] = 255;
      }
    }
    bctx.putImageData(img, 0, 0);
    const g = mix(pal.bottom, [59, 130, 246], 0.35);
    document.documentElement.style.setProperty('--sky-glow', `rgba(${g[0]},${g[1]},${g[2]},0.24)`);
  }

  function disk(cx, cy, r, color, alpha) {
    ctx.globalAlpha = alpha; ctx.fillStyle = color;
    for (let y = -r; y <= r; y++) {
      const half = Math.floor(Math.sqrt(r * r - y * y) + 0.35);
      ctx.fillRect(Math.round(cx - half), Math.round(cy + y), half * 2 + 1, 1);
    }
    ctx.globalAlpha = 1;
  }
  function arc(p) { return { x: W * (0.08 + 0.84 * p), y: H * 0.6 - Math.sin(Math.PI * p) * H * 0.48 }; }

  function drawBodies(t) {
    if (minute >= SUNRISE - 20 && minute <= SUNSET + 20) {
      const p = (minute - SUNRISE) / (SUNSET - SUNRISE), s = arc(p);
      const high = Math.sin(Math.PI * Math.min(1, Math.max(0, p)));
      const core = rgb(mix([255, 150, 80], [255, 247, 214], high));
      disk(s.x, s.y, 11, core, 0.12); disk(s.x, s.y, 9, core, 0.22); disk(s.x, s.y, 6, core, 1);
    }
    if (minute >= SUNSET + 30 || minute <= SUNRISE - 25) {
      const span = (SUNRISE - 25) + 1440 - (SUNSET + 30);
      const p = ((minute - (SUNSET + 30) + 1440) % 1440) / span, mo = arc(p);
      disk(mo.x, mo.y, 9, '#c7d2fe', 0.1); disk(mo.x, mo.y, 5, '#e8eefc', 1);
      ctx.fillStyle = '#b9c4e4';
      [[-2, -1], [1, 1], [2, -2], [-1, 2]].forEach(([dx, dy]) => ctx.fillRect(Math.round(mo.x + dx), Math.round(mo.y + dy), 1, 1));
    }
    if (pal.stars > 0.02) {
      stars.forEach(s => {
        const tw = reduceMotion ? 0.8 : 0.55 + 0.45 * Math.sin(t / 700 + s.ph * 3);
        ctx.globalAlpha = pal.stars * (0.35 + 0.65 * s.b) * tw;
        ctx.fillStyle = s.b > 0.85 ? '#fde68a' : '#ffffff';
        ctx.fillRect(s.x, s.y, 1, 1);
        if (s.b > 0.93 && tw > 0.9) { ctx.globalAlpha *= 0.4; ctx.fillRect(s.x - 1, s.y, 3, 1); ctx.fillRect(s.x, s.y - 1, 1, 3); }
      });
      ctx.globalAlpha = 1;
    }
  }

  function drawClouds(dt) {
    const light = pal.light, shade = pal.shade, edge = mix(light, [255, 255, 255], 0.5);
    clouds.forEach(c => {
      if (!reduceMotion) c.x += c.speed * dt;
      if (c.x > W + 2) c.x = -c.w - 2;
      const ox = Math.round(c.x), alpha = c.layer ? 0.95 : 0.7;
      for (let y = 0; y < c.h; y++) for (let x = 0; x < c.w; x++) {
        if (!c.grid[y][x]) continue;
        const top = y === 0 || !c.grid[y - 1][x];
        const low = y >= c.h - 2 || x > c.w * 0.72;
        ctx.globalAlpha = alpha;
        ctx.fillStyle = rgb(top && !low ? edge : low ? shade : light);
        ctx.fillRect(ox + x, c.y + y, 1, 1);
      }
    });
    ctx.globalAlpha = 1;
  }

  function drawShootingStar(dt) {
    if (reduceMotion || pal.stars < 0.6) { shooting = null; return; }
    if (!shooting && Math.random() < dt * 0.06) {
      shooting = { x: W * (0.2 + Math.random() * 0.7), y: H * (0.04 + Math.random() * 0.25), life: 0 };
    }
    if (!shooting) return;
    shooting.life += dt;
    const len = 7, sx = shooting.x - shooting.life * 55, sy = shooting.y + shooting.life * 28;
    for (let i = 0; i < len; i++) {
      ctx.globalAlpha = (1 - i / len) * Math.max(0, 1 - shooting.life / 0.9);
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(Math.round(sx + i * 2), Math.round(sy - i), 1, 1);
    }
    ctx.globalAlpha = 1;
    if (shooting.life > 0.9) shooting = null;
  }

  function pad(n) { return String(n).padStart(2, '0'); }
  function updateClock() {
    const m = Math.floor(minute);
    if (clock) clock.textContent = `GST ${pad(Math.floor(m / 60))}:${pad(m % 60)} · ${phaseName(m)}`;
    if (slider && live) slider.value = m;
    if (slider) slider.setAttribute('aria-valuetext', `${pad(Math.floor(m / 60))}:${pad(m % 60)} Dubai time, ${phaseName(m)}`);
  }
  function setMinute(m) { minute = m; pal = palette(minute); updateClock(); }

  if (slider) {
    slider.addEventListener('input', () => {
      live = false; liveBtn && liveBtn.classList.remove('on');
      setMinute(+slider.value);
      if (reduceMotion) frame(performance.now());
    });
  }
  if (liveBtn) {
    liveBtn.addEventListener('click', () => {
      live = true; liveBtn.classList.add('on');
      setMinute(dubaiMinutes());
      if (reduceMotion) frame(performance.now());
    });
  }
  setInterval(() => { if (live) { setMinute(dubaiMinutes()); if (reduceMotion) frame(performance.now()); } }, 30000);

  let last = performance.now(), visible = true, running = false;
  function frame(t) {
    const dt = Math.min(0.25, (t - last) / 1000); last = t;
    paintBackground();
    ctx.drawImage(bg, 0, 0);
    drawBodies(t);
    drawShootingStar(dt);
    drawClouds(dt);
  }
  function loop(t) {
    if (!visible || document.hidden) { running = false; return; }
    if (t - last >= 1000 / 15) frame(t);       // ~15 fps keeps the motion steppy and pixel-like
    requestAnimationFrame(loop);
  }
  function start() {
    if (running || reduceMotion) return;
    running = true; last = performance.now(); requestAnimationFrame(loop);
  }

  resize();
  setMinute(minute);
  frame(performance.now());
  window.addEventListener('resize', () => { resize(); frame(performance.now()); });
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(entries => { visible = entries[0].isIntersecting; if (visible) start(); }).observe(sky);
  }
  document.addEventListener('visibilitychange', () => { if (!document.hidden) start(); });
  start();

  /* ------------------------------------------------------------ hello, fellow dev */
  console.log('%c\n  ▄▄▄▄▄ ▄ ▄▄▄ ▄▄▄    ▄ ▄ ▄▄▄ ▄▄▄ ▄▄▄ ▄▄▄\n    ▄▀  █ █▄█ █ █    █▄█ █▄█ █▄▀ █▄  ▀▄▄\n  ▄█▄▄▄ █ █ █ █▄▀    █ █ █ █ █ █ █▄▄ ▄▄▀\n', 'color:#60a5fa;font-family:monospace');
  console.log('%cPoking around? Respect. Found something? ziad@haresholmes.eu.org', 'color:#94a3b8');
})();
