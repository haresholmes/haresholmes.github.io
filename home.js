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

  /* ------------------------------------------------------------ footer: ANSI Shadow name */
  // The figlet "ANSI Shadow" lettering, drawn as vector shapes (solid blocks + double-line shadow)
  // so it never breaks apart the way box-drawing characters do in a browser font.
  const ANSI = [
    '███████╗██╗ █████╗ ██████╗     ██╗  ██╗ █████╗ ██████╗ ███████╗███████╗',
    '╚══███╔╝██║██╔══██╗██╔══██╗    ██║  ██║██╔══██╗██╔══██╗██╔════╝██╔════╝',
    '  ███╔╝ ██║███████║██║  ██║    ███████║███████║██████╔╝█████╗  ███████╗',
    ' ███╔╝  ██║██╔══██║██║  ██║    ██╔══██║██╔══██║██╔══██╗██╔══╝  ╚════██║',
    '███████╗██║██║  ██║██████╔╝    ██║  ██║██║  ██║██║  ██║███████╗███████║',
    '╚══════╝╚═╝╚═╝  ╚═╝╚═════╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝',
  ];
  const pxBanner = document.getElementById('pxBanner');
  if (pxBanner) {
    const CW = 6, CH = 11, A = 1.6, B = 4.4, U = 3.6, V = 7.4;   // cell size and the two rails of a double line
    const seg = (x1, y1, x2, y2) => `M${x1} ${y1}L${x2} ${y2}`;
    const SHAPES = {                                              // in cell units: [outer rail path, inner rail path]
      '═': () => seg(0, U, CW, U) + seg(0, V, CW, V),
      '║': () => seg(A, 0, A, CH) + seg(B, 0, B, CH),
      '╗': () => seg(0, U, B, U) + seg(B, U, B, CH) + seg(0, V, A, V) + seg(A, V, A, CH),
      '╔': () => seg(A, U, CW, U) + seg(A, U, A, CH) + seg(B, V, CW, V) + seg(B, V, B, CH),
      '╝': () => seg(B, 0, B, V) + seg(0, V, B, V) + seg(A, 0, A, U) + seg(0, U, A, U),
      '╚': () => seg(A, 0, A, V) + seg(A, V, CW, V) + seg(B, 0, B, U) + seg(B, U, CW, U),
    };
    let blocks = '', lines = '';
    ANSI.forEach((row, r) => [...row].forEach((ch, c) => {
      const x = c * CW, y = r * CH;
      if (ch === '█') blocks += `<rect x="${x}" y="${y}" width="${CW + 0.05}" height="${CH + 0.05}"/>`;
      else if (SHAPES[ch]) lines += `<path transform="translate(${x} ${y})" d="${SHAPES[ch]()}"/>`;
    }));
    const w = Math.max(...ANSI.map(r => [...r].length)) * CW, h = ANSI.length * CH;
    pxBanner.innerHTML = `<svg viewBox="0 0 ${w} ${h}" aria-hidden="true">
      <defs><linearGradient id="ansiFill" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="${h}"><stop offset="0" stop-color="#bfdbfe"/><stop offset=".5" stop-color="#60a5fa"/><stop offset="1" stop-color="#2563eb"/></linearGradient>
      <linearGradient id="ansiLine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="${w}" y2="0"><stop offset="0" stop-color="#3b82f6"/><stop offset="1" stop-color="#2dd4bf"/></linearGradient></defs>
      <g fill="none" stroke="url(#ansiLine)" stroke-width="1.05" stroke-linecap="square" opacity=".75">${lines}</g>
      <g fill="url(#ansiFill)" shape-rendering="crispEdges">${blocks}</g></svg>`;
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
  const revealSel = '.sec-head, .impact-head, .tile, .about-copy, .whoami, .experience-item, .skill-card, .project-card, .edu, .languages, .contact-panel, .marquee';
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

  const nums = document.querySelectorAll('[data-count]');
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

  /* ------------------------------------------------------------ the cool stuff: live tiles */
  // AI workforce: pixel agents light up as they pick up real tool calls (names from Begad's MCP servers).
  const bots = document.getElementById('bots'), botLog = document.getElementById('botLog');
  if (bots) {
    const BOT = ['....#....', '....#....', '.#######.', '#+++++++#', '#+e+++e+#', '#+++++++#', '#++###++#', '.#######.'];
    const svg = () => {
      let r = '';
      BOT.forEach((row, y) => [...row].forEach((ch, x) => {
        if (ch === '.') return;
        const cls = ch === 'e' ? 'eye' : ch === '+' ? 'face' : y < 2 ? 'lite' : 'body';
        r += `<rect class="${cls}" x="${x}" y="${y}" width="1.02" height="1.02"/>`;
      }));
      return `<svg viewBox="0 0 9 8" shape-rendering="crispEdges">${r}</svg>`;
    };
    const N = 16;
    bots.innerHTML = Array.from({ length: N }, () => `<div class="bot">${svg()}</div>`).join('');
    const els = [...bots.children];
    const TOOLS = ['invoice_create', 'list_products', 'update_products_batch', 'noon_orders', 'mail_draft', 'design_place_logo',
      'amazon_stock', 'check_listings', 'invoice_pdf', 'mail_search', 'noon_catalog', 'design_generate_image', 'amazon_invoices_due',
      'whiten_photos', 'save_product', 'noon_report', 'invoice_find', 'link_listings'];
    const log = [];
    const tick = () => {
      const i = Math.floor(Math.random() * N);
      els[i].classList.toggle('busy');
      const busy = els.filter(e => e.classList.contains('busy'));
      if (busy.length > 6) busy[0].classList.remove('busy');
      if (botLog && els[i].classList.contains('busy')) {
        log.unshift(`<div><span class="c-dim">agent_${String(i + 1).padStart(2, '0')} →</span> ${TOOLS[Math.floor(Math.random() * TOOLS.length)]} <span class="c-ok">✓</span></div>`);
        log.length = Math.min(log.length, 4);
        botLog.innerHTML = log.join('');
      }
    };
    for (let k = 0; k < 12; k++) tick();
    if (!reduceMotion) setInterval(tick, 900);
  }

  // Shipping pace: one pixel bar per day, real commits-per-day from git.
  const heat = document.getElementById('heat');
  if (heat) {
    const counts = new Map(heat.dataset.days.split(',').map(p => p.split(':')).map(([d, n]) => [d, +n]));
    const start = new Date('2026-08-12T00:00:00Z'), end = new Date('2026-11-26T00:00:00Z');
    const days = [];
    for (let d = new Date(start); d <= end; d.setUTCDate(d.getUTCDate() + 1)) {
      const key = d.toISOString().slice(0, 10);
      days.push([key, counts.get(key) || 0]);
    }
    const max = Math.max(...days.map(d => d[1])), H = 18;
    let rects = '';
    days.forEach(([key, n], i) => {
      const h = n ? Math.max(1, Math.round(n / max * H)) : 0;
      for (let y = 0; y < h; y++) {                                   // stack pixel blocks, brighter toward the top
        const t = y / H, peak = n === max;
        const fill = peak ? '#2dd4bf' : t > 0.66 ? '#93c5fd' : t > 0.33 ? '#3b82f6' : '#1d4ed8';
        rects += `<rect class="d" x="${i}" y="${H - 1 - y}" width=".78" height=".78" fill="${fill}" style="transition-delay:${i * 8}ms"/>`;
      }
      if (!n) rects += `<rect x="${i}" y="${H - 1}" width=".78" height=".78" fill="rgba(148,163,184,.25)"/>`;
      rects += `<rect x="${i}" y="0" width="1" height="${H}" fill="transparent"><title>${key}: ${n} commit${n === 1 ? '' : 's'}</title></rect>`;
    });
    heat.innerHTML = `<svg viewBox="0 0 ${days.length} ${H}" shape-rendering="crispEdges">${rects}</svg>`;
    if ('IntersectionObserver' in window && !reduceMotion) {
      const ho = new IntersectionObserver(e => { if (e[0].isIntersecting) { heat.classList.add('on'); ho.disconnect(); } }, { threshold: 0.15 });
      ho.observe(heat);
    } else heat.classList.add('on');
  }

  // Autopilot: countdown to the next scheduled jobs (systemd timers on the Begad servers, UTC).
  const nextUp = document.getElementById('nextUp');
  if (nextUp) {
    const JOBS = [
      ['New-hire setup', { every: 1 }], ['Video compression', { every: 2 }], ['Order sync', { every: 5 }],
      ['Price watch', { every: 20 }], ['Amazon invoices', { every: 60 }], ['Off-site backup', { at: [0, 30] }],
      ['Invoices', { at: [2, 15] }], ['Server updates', { at: [4, 0] }], ['Sales report', { at: [14, 30] }],
    ];
    const next = (job, now) => {
      if (job.every) { const m = job.every * 60000; return Math.ceil((now + 1) / m) * m; }
      const d = new Date(now); d.setUTCHours(job.at[0], job.at[1], 0, 0);
      return d.getTime() > now ? d.getTime() : d.getTime() + 864e5;
    };
    const fmt = ms => { const s = Math.ceil(ms / 1000), h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60);
      return h ? `${h}h ${String(m).padStart(2, '0')}m` : `${m}:${String(s % 60).padStart(2, '0')}`; };
    const render = () => {
      const now = Date.now();
      // show the two most frequent jobs plus the two next daily ones, so the list mixes rhythm and scale
      const daily = JOBS.filter(j => j[1].at).map(j => [j[0], next(j[1], now)]).sort((a, b) => a[1] - b[1]).slice(0, 2);
      const freq = JOBS.filter(j => j[1].every && j[1].every >= 5).map(j => [j[0], next(j[1], now)]).sort((a, b) => a[1] - b[1]).slice(0, 2);
      nextUp.innerHTML = [...freq, ...daily].sort((a, b) => a[1] - b[1]).map(([n, t]) => `<li><span>${n}</span><span>${fmt(t - now)}</span></li>`).join('');
    };
    render();
    setInterval(render, 1000);
  }

  // AI content: the language flips between English and Arabic.
  const flip = document.querySelector('.lang-flip');
  if (flip && !reduceMotion) {
    let ar = false;
    setInterval(() => { ar = !ar; flip.textContent = ar ? 'العربية' : 'English'; flip.lang = ar ? 'ar' : 'en'; }, 2200);
  }

  /* ------------------------------------------------------------ hero terminal (loops) */
  const termBody = document.getElementById('termBody');
  const TERM = [
    ['cat roles.txt', '<span class="c-ok">CTO @ Begad</span> · founder @ Computator'],
    ['cat education.txt', 'BSc Cybersecurity @ UOWD · <span class="c-amber">class of Dec 2026</span>'],
    ['cat clubs.txt', 'founder · UOWD Tech Club cyber team'],
    ['ls ~/shipped', '5 apps · 10,000+ products · 20+ services'],
    ['git log --oneline | wc -l', '<span class="c-amber">3,528</span> commits · 639 PRs in 107 days'],
    ['ls ~/agents/tools | wc -l', '<span class="c-amber">127</span> AI tools across 12 systems'],
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

  // Scene sprites from scripts/site_art.py: 1380×366, core x 200–1180, ground from row 356, Burj spire x 948.
  const SCENE = { w: 1380, h: 366, coreL: 200, coreR: 1180, ground: 356, spire: 948 };
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
    const coreW = SCENE.coreR - SCENE.coreL;
    S = Math.max(1, Math.min(half(cw / (coreW * 0.85)), half(ch / 430), 4));
    const nW = Math.ceil(cw / S), nH = Math.ceil(ch / S);
    if (nW === W && nH === H) return;
    W = nW; H = nH; horizon = H - (SCENE.h - SCENE.ground);
    canvas.width = W; canvas.height = H;
    const lo = Math.min(W - SCENE.coreR, -SCENE.coreL), hi = Math.max(W - SCENE.coreR, -SCENE.coreL);
    const centred = Math.round((W - coreW) / 2) - SCENE.coreL;
    if (window.matchMedia('(max-width: 880px)').matches && W < coreW) {
      // Phones: the terminal sits above the sky, so walk slowly from Giza to the Gulf and back.
      cam.max = -SCENE.coreL; cam.min = W - SCENE.coreR;
      cam.x = reduceMotion ? Math.min(cam.max, Math.max(cam.min, Math.round(W * 0.55 - SCENE.spire))) : cam.max;
    } else {
      // Desktop: centre the skyline, then slide it left if the terminal would cover the Burj Khalifa.
      let x = Math.min(hi, Math.max(lo, centred));
      const term = document.querySelector('.term');
      if (term) {
        const tr = term.getBoundingClientRect(), hr = hero.getBoundingClientRect();
        const termLeft = (tr.left - hr.left) / S, termBottom = (tr.bottom - hr.top) / S;
        const burjTop = H - SCENE.h + 2;
        const row = termBottom - (H - SCENE.h);                       // tower row level with the terminal's bottom
        const halfW = row < 92 ? 3 : 4 + (row - 92) * 0.14;
        if (termBottom > burjTop - 4) x = Math.max(lo, Math.min(x, Math.floor(termLeft - 12 / S - halfW - SCENE.spire)));
      }
      cam.min = cam.max = cam.x = x;
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
