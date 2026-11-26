/* Ziad Hares, homepage interactions.
 * The hero is a live pixel-art sky over an Egypt-to-Dubai skyline that follows the current
 * time in Dubai: dithered sky, sun and moon, stars, drifting pixel clouds tinted by the hour,
 * the odd shooting star, and city lights that come on at dusk. */
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

  /* ------------------------------------------------------------ footer: pixel name + pixel logo */
  const FONT = {
    Z: ['#####', '....#', '...#.', '..#..', '.#...', '#....', '#####'],
    I: ['###', '.#.', '.#.', '.#.', '.#.', '.#.', '###'],
    A: ['.###.', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
    D: ['####.', '#...#', '#...#', '#...#', '#...#', '#...#', '####.'],
    H: ['#...#', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
    R: ['####.', '#...#', '#...#', '####.', '#.#..', '#..#.', '#...#'],
    E: ['#####', '#....', '#....', '####.', '#....', '#....', '#####'],
    S: ['.####', '#....', '#....', '.###.', '....#', '....#', '####.'],
  };
  const pxBanner = document.getElementById('pxBanner');
  if (pxBanner) {
    const cells = [];
    let x = 0;
    for (const ch of 'ZIAD HARES') {
      if (ch === ' ') { x += 3; continue; }
      const g = FONT[ch];
      g.forEach((row, y) => [...row].forEach((c, dx) => { if (c === '#') cells.push([x + dx, y]); }));
      x += g[0].length + 1;
    }
    const w = x, h = 8;
    const rect = (cx, cy, fill) => `<rect x="${cx}" y="${cy}" width="1.04" height="1.04" fill="${fill}"/>`;
    pxBanner.innerHTML = `<svg viewBox="0 0 ${w + 1} ${h}" shape-rendering="crispEdges" aria-hidden="true">
      <defs><linearGradient id="pxg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#bfdbfe"/><stop offset=".45" stop-color="#60a5fa"/><stop offset="1" stop-color="#2563eb"/></linearGradient></defs>
      ${cells.map(([cx, cy]) => rect(cx + 0.35, cy + 0.35, '#1e3a8a')).join('')}
      ${cells.map(([cx, cy]) => rect(cx, cy, 'url(#pxg)')).join('')}</svg>`;
  }
  const pxLogo = document.getElementById('pxLogo');
  if (pxLogo) {
    const pixelate = () => {
      const n = 22, c = document.createElement('canvas');
      c.width = c.height = n;
      const g = c.getContext('2d');
      g.imageSmoothingEnabled = true;
      g.drawImage(pxLogo, 0, 0, n, n);
      const d = g.getImageData(0, 0, n, n);
      for (let i = 3; i < d.data.length; i += 4) d.data[i] = d.data[i] > 110 ? 255 : 0;   // hard pixel edges
      g.putImageData(d, 0, 0);
      c.setAttribute('aria-hidden', 'true');
      pxLogo.replaceWith(c);
    };
    if (pxLogo.complete && pxLogo.naturalWidth) pixelate(); else pxLogo.addEventListener('load', pixelate);
  }

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
  // Nav prompt: types a command, thinks better of it, backspaces. Forever.
  const typed = document.getElementById('brandTyped');
  if (typed && !reduceMotion) {
    const CMDS = ['sudo apt install chai', 'whoami', 'ssh root@dubai', 'ping cairo.eg', 'git push --force', 'rm -rf /',
      'nmap localhost', 'sudo make sandwich', 'hire ziad --now', 'cat ~/.secrets', './deploy.sh', 'top', 'exit'];
    let bag = [], prev = '';
    const next = () => {
      if (!bag.length) bag = CMDS.filter(c => c !== prev).sort(() => Math.random() - 0.5);
      return (prev = bag.pop());
    };
    const wait = ms => new Promise(r => setTimeout(r, ms));
    (async function run() {
      await wait(1600);
      for (;;) {
        const cmd = next();
        typed.textContent = ' ';
        for (let i = 1; i <= cmd.length; i++) { typed.textContent = ' ' + cmd.slice(0, i); await wait(55 + Math.random() * 90); }
        const panic = cmd === 'rm -rf /' || cmd === 'git push --force';
        await wait(panic ? 500 : 1300 + Math.random() * 900);
        for (let i = cmd.length - 1; i >= 0; i--) { typed.textContent = ' ' + cmd.slice(0, i); await wait(panic ? 18 : 40); }
        typed.textContent = '';
        await wait(900 + Math.random() * 1400);
      }
    })();
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

  /* ------------------------------------------------------------ hero terminal (loops) */
  const termBody = document.getElementById('termBody');
  const TERM = [
    ['cat roles.txt', '<span class="c-ok">CTO @ Begad</span> · founder @ Computator'],
    ['cat education.txt', 'BSc Cybersecurity @ UOWD · <span class="c-amber">class of Dec 2026</span>'],
    ['cat clubs.txt', 'founder · UOWD Tech Club cyber team'],
    ['ls ~/shipped', '5 apps · 10,000+ products · 20+ services'],
    ['git log --oneline | wc -l', '<span class="c-amber">2,400+</span> commits in 3.5 months'],
    ['systemctl status security', '<span class="c-ok">●</span> active (running) · ISO 27001'],
    ['cat languages.txt', 'Arabic (native) · English (proficient)'],
    ['echo $STATUS', '<span class="c-ok">open</span> to security roles &amp; consulting'],
  ];
  if (termBody && !reduceMotion) {
    const caret = '<span class="caret"></span>', prompt = '<span class="c-dim">$</span> ';
    let lines = [], li = 0, ci = 0;
    const render = typing => { termBody.innerHTML = lines.slice(-12).join('\n') + (lines.length ? '\n' : '') + prompt + typing + caret; };
    (function tick() {
      if (li >= TERM.length) {                               // end of the loop: type `clear`, start over
        if (ci <= 5) { render('clear'.slice(0, ci++)); return setTimeout(tick, 90); }
        lines = []; li = 0; ci = 0; render(''); return setTimeout(tick, 900);
      }
      const [cmd, out] = TERM[li];
      if (ci <= cmd.length) { render(cmd.slice(0, ci++)); return setTimeout(tick, 35 + Math.random() * 55); }
      lines.push(prompt + cmd, out); li++; ci = 0; render('');
      setTimeout(tick, li === TERM.length ? 4200 : 1500);
    })();
  }

  /* ------------------------------------------------------------ live pixel sky over Egypt → Dubai */
  const hero = document.getElementById('top');
  const canvas = document.getElementById('skyCanvas');
  if (!hero || !canvas || !canvas.getContext) return;
  const ctx = canvas.getContext('2d');
  const clock = document.getElementById('skyClock');

  // Scene sprites from scripts/site_art.py: 1230×366, core x 200–1030, ground from row 356, Burj spire x 818.
  const SCENE = { w: 1230, h: 366, coreL: 200, coreR: 1030, ground: 356, spire: 818 };
  const dayImg = new Image(), nightImg = new Image();
  dayImg.src = 'px-scene-day.png'; nightImg.src = 'px-scene-night.png';

  // [minute of day, sky top, sky bottom, cloud light, cloud shade, night 0..1]
  const KEYS = [
    [0,    '#03050f', '#0b1430', '#3a4572', '#232c50', 1],
    [300,  '#05081a', '#141a3d', '#3c4674', '#262f55', 0.95],
    [365,  '#1a1f4a', '#6b4a7a', '#8a7fa8', '#5e5580', 0.6],
    [405,  '#3b5aa0', '#f2a56b', '#ffd6b0', '#e8a08a', 0.15],
    [480,  '#3f86d6', '#bfe0f5', '#ffffff', '#cfdff0', 0],
    [720,  '#2f7fe0', '#cfe8f7', '#ffffff', '#d4e2f0', 0],
    [990,  '#3a80d0', '#ecdcbc', '#fffaf0', '#e0d4c2', 0],
    [1060, '#3c4f9a', '#f08a5d', '#ffc59e', '#d9776a', 0.2],
    [1110, '#1d2156', '#8a4a78', '#9c6b92', '#5a3e6e', 0.65],
    [1190, '#070b1f', '#18204a', '#3e4976', '#273055', 0.95],
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
      night: a[5] + (b[5] - a[5]) * t,
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
  // Deterministic randomness: today's clouds and stars are the same for every visitor.
  function rng(seed) { return () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296); }

  let S = 1, W = 0, H = 0, horizon = 0, bg = null, bgKey = '';
  let stars = [], clouds = [], shooting = null;
  let minute = dubaiMinutes(), pal = palette(minute);
  let cam = { x: 0, min: 0, max: 0, dir: -1, hold: 2.5 };

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
    for (let y = h - 4; y < h; y++) for (let x = 2; x < w - 2; x++) grid[y][x] = 1;
    grid[h - 1][2] = grid[h - 1][w - 3] = 0;
    fill(w * (0.45 + (r() - 0.5) * 0.15), h - 1 - h * 0.42, h * 0.5);
    const extra = 1 + Math.floor(r() * 3);
    for (let i = 0; i < extra; i++) {
      const rad = h * (0.26 + r() * 0.16);
      fill(w * (0.16 + r() * 0.68), h - 3 - rad * 0.55, rad);
    }
    const band = Math.max(20, Math.min(H * 0.5, horizon - 150));
    return { grid, w, h, layer, x: r() * (W + w) - w, y: Math.floor(6 + r() * band), speed: 0.5 + layer * 0.7 + r() * 0.4 };
  }

  function resize() {
    const cw = hero.clientWidth, ch = hero.clientHeight;
    const half = v => Math.max(1, Math.floor(v * 2) / 2);
    S = Math.max(1, Math.min(half(cw / (SCENE.coreR - SCENE.coreL)), half(ch / 430), 4));
    const nW = Math.ceil(cw / S), nH = Math.ceil(ch / S);
    if (nW === W && nH === H) return;
    W = nW; H = nH; horizon = H - (SCENE.h - SCENE.ground);
    canvas.width = W; canvas.height = H;
    // Camera: centre the core when it fits, otherwise pan slowly between Egypt and Dubai.
    const coreW = SCENE.coreR - SCENE.coreL;
    if (W >= coreW) { cam.min = cam.max = cam.x = Math.round((W - coreW) / 2) - SCENE.coreL; }
    else {
      cam.max = -SCENE.coreL; cam.min = W - SCENE.coreR;
      cam.x = reduceMotion ? Math.min(cam.max, Math.max(cam.min, Math.round(W * 0.55 - SCENE.spire))) : cam.max;
    }
    const r = rng(dubaiDayOfYear() * 7919 + 17);
    stars = Array.from({ length: Math.round(W * H / 900) }, () => ({ x: Math.floor(r() * W), y: Math.floor(r() * (horizon - 30)), b: r(), ph: r() * 6.28 }));
    const count = Math.max(2, Math.round((2 + r() * 4) * W / 360));   // some days are clearer than others
    clouds = Array.from({ length: count }, (_, i) => makeCloud(r, i % 2)).sort((a, b) => a.layer - b.layer);
    bgKey = '';
  }

  function paintBackground() {
    const key = W + 'x' + H + ':' + minute;
    if (key === bgKey) return;
    bgKey = key;
    bg = document.createElement('canvas'); bg.width = W; bg.height = H;
    const bctx = bg.getContext('2d'), img = bctx.createImageData(W, H), d = img.data, BANDS = 16;
    for (let y = 0; y < H; y++) {
      const t = Math.min(1, y / horizon);
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
  // The sun rises over the Dubai side (east, right) and sets over Egypt (west, left).
  function arc(p) { return { x: W * (0.96 - 0.7 * p), y: horizon - Math.sin(Math.PI * p) * (horizon - H * 0.1) }; }

  function drawBodies(t) {
    const p = (minute - SUNRISE) / (SUNSET - SUNRISE);
    if (p > -0.08 && p < 1.08) {
      const s = arc(p), high = Math.max(0, Math.sin(Math.PI * Math.min(1, Math.max(0, p))));
      const core = rgb(mix([255, 140, 70], [255, 247, 214], Math.min(1, high * 1.6)));
      disk(s.x, s.y, 14, core, 0.1); disk(s.x, s.y, 11, core, 0.2); disk(s.x, s.y, 8, core, 1);
    }
    const span = 1440 - (SUNSET - SUNRISE) - 50;
    const q = ((minute - (SUNSET + 25) + 1440) % 1440) / span;
    if (q > -0.05 && q < 1.05) {
      const mo = arc(q);
      disk(mo.x, mo.y, 11, '#c7d2fe', 0.1); disk(mo.x, mo.y, 6, '#e8eefc', 1);
      ctx.fillStyle = '#b9c4e4';
      [[-2, -1], [1, 2], [2, -2], [-1, 3]].forEach(([dx, dy]) => ctx.fillRect(Math.round(mo.x + dx), Math.round(mo.y + dy), 1, 1));
    }
    const starAlpha = Math.max(0, (pal.night - 0.25) / 0.75);
    if (starAlpha > 0.02) {
      stars.forEach(s => {
        const tw = reduceMotion ? 0.8 : 0.55 + 0.45 * Math.sin(t / 700 + s.ph * 3);
        ctx.globalAlpha = starAlpha * (0.35 + 0.65 * s.b) * tw;
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
      const ox = Math.round(c.x);
      ctx.globalAlpha = c.layer ? 0.95 : 0.72;
      for (let y = 0; y < c.h; y++) for (let x = 0; x < c.w; x++) {
        if (!c.grid[y][x]) continue;
        const top = y === 0 || !c.grid[y - 1][x], low = y >= c.h - 2 || x > c.w * 0.72;
        ctx.fillStyle = rgb(top && !low ? edge : low ? shade : light);
        ctx.fillRect(ox + x, c.y + y, 1, 1);
      }
    });
    ctx.globalAlpha = 1;
  }

  function drawShootingStar(dt) {
    if (reduceMotion || pal.night < 0.8) { shooting = null; return; }
    if (!shooting && Math.random() < dt * 0.06) shooting = { x: W * (0.2 + Math.random() * 0.7), y: H * (0.04 + Math.random() * 0.2), life: 0 };
    if (!shooting) return;
    shooting.life += dt;
    const sx = shooting.x - shooting.life * 70, sy = shooting.y + shooting.life * 35;
    for (let i = 0; i < 8; i++) {
      ctx.globalAlpha = (1 - i / 8) * Math.max(0, 1 - shooting.life / 0.9);
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(Math.round(sx + i * 2), Math.round(sy - i), 1, 1);
    }
    ctx.globalAlpha = 1;
    if (shooting.life > 0.9) shooting = null;
  }

  function drawScene(t) {
    if (!dayImg.complete || !dayImg.naturalWidth) return;
    const x = Math.round(cam.x), y = H - SCENE.h;
    const layer = (img, alpha) => {
      ctx.globalAlpha = alpha;
      ctx.drawImage(img, x, y);
      if (x > 0) ctx.drawImage(img, 0, 0, 1, SCENE.h, 0, y, x, SCENE.h);                       // extend the desert
      const right = x + SCENE.w;
      if (right < W) ctx.drawImage(img, SCENE.w - 1, 0, 1, SCENE.h, right, y, W - right, SCENE.h); // extend the sea
    };
    layer(dayImg, 1);
    if (pal.night > 0.01 && nightImg.complete && nightImg.naturalWidth) layer(nightImg, pal.night);
    ctx.globalAlpha = 1;
    if (Math.floor(t / 800) % 2 === 0) { ctx.fillStyle = '#ef4444'; ctx.fillRect(x + SCENE.spire, y + 2, 1, 2); }  // spire beacon
  }

  function moveCamera(dt) {
    if (reduceMotion || cam.min === cam.max) return;
    if (cam.hold > 0) { cam.hold -= dt; return; }
    cam.x += cam.dir * 7 * dt;                     // a slow walk from Giza to the Gulf and back
    if (cam.x <= cam.min) { cam.x = cam.min; cam.dir = 1; cam.hold = 4; }
    if (cam.x >= cam.max) { cam.x = cam.max; cam.dir = -1; cam.hold = 4; }
  }

  const pad = n => String(n).padStart(2, '0');
  function tickClock() {
    minute = dubaiMinutes(); pal = palette(minute);
    if (clock) clock.textContent = `GST ${pad(Math.floor(minute / 60))}:${pad(minute % 60)} · ${phaseName(minute)}`;
  }

  let last = performance.now(), visible = true, running = false;
  function frame(t) {
    const dt = Math.min(0.25, (t - last) / 1000); last = t;
    paintBackground();
    ctx.drawImage(bg, 0, 0);
    drawBodies(t);
    drawShootingStar(dt);
    drawClouds(dt);
    moveCamera(dt);
    drawScene(t);
  }
  function loop(t) {
    if (!visible || document.hidden) { running = false; return; }
    if (t - last >= 1000 / 15) frame(t);         // ~15 fps keeps the motion steppy and pixel-like
    requestAnimationFrame(loop);
  }
  function start() {
    if (running || reduceMotion) return;
    running = true; last = performance.now(); requestAnimationFrame(loop);
  }

  tickClock();
  resize();
  frame(performance.now());
  [dayImg, nightImg].forEach(img => img.addEventListener('load', () => frame(performance.now())));
  setInterval(() => { tickClock(); if (reduceMotion) frame(performance.now()); }, 30000);
  window.addEventListener('resize', () => { resize(); frame(performance.now()); });
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(entries => { visible = entries[0].isIntersecting; if (visible) start(); }).observe(hero);
  }
  document.addEventListener('visibilitychange', () => { if (!document.hidden) start(); });
  start();

  /* ------------------------------------------------------------ hello, fellow dev */
  console.log('%c\n  ▄▄▄▄▄ ▄ ▄▄▄ ▄▄▄    ▄ ▄ ▄▄▄ ▄▄▄ ▄▄▄ ▄▄▄\n    ▄▀  █ █▄█ █ █    █▄█ █▄█ █▄▀ █▄  ▀▄▄\n  ▄█▄▄▄ █ █ █ █▄▀    █ █ █ █ █ █ █▄▄ ▄▄▀\n', 'color:#60a5fa;font-family:monospace');
  console.log('%cPoking around? Respect. Found something? ziad@haresholmes.eu.org', 'color:#94a3b8');
})();
