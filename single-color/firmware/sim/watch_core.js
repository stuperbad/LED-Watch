/* watch_core.js - the watch "firmware", written C-style so it can be ported to the AVR128DB48 nearly line by line.
 *
 * No DOM in here. The simulator feeds it the same things the real hardware gives the MCU:
 *   io = { btn:[left,right] (pressed), accel:{x,y,z} (LIS2DW12 reading in g, flat face-up = 0,0,1),
 *          wakeStrength (0..1, 0 = no wrist-raise event this tick), tap (double-tap event), ff (free-fall event),
 *          vdd (V), soc (0..1), batOk (BAT_OK pin), solarMw, charging, ambient (0..1 light sense) }
 * and calls step(dtReal, dtSim, io). dtReal = wall-clock ms (buttons, blinking, games); dtSim = RTC ms (can be sped up).
 * It returns the 12x12 framebuffer (what the matrix driver would scan out) plus status.
 *
 * Accelerometer frame: x = toward 3 o'clock, y = toward 12 o'clock, z = out of the glass.
 * The sensor measures specific force, so at rest it reads +1 g on whichever axis points UP.
 * Raise the 12 o'clock edge -> y reads +; sand then slides toward 6 o'clock.
 */
(function (global) {
  'use strict';
  const ROWS = 12, COLS = 12;
  const MODE = { TIME: 0, SET: 1, TMR: 2, BAT: 3, FUN: 4, CFG: 5 };
  const MODE_NAME = ['TIME', 'SET', 'TMR', 'BAT', 'FUN', 'CFG'];
  const MODE_IND = [-1, 0, 1, 2, 3, 4];               // mode -> indicator index (IND1..IND6 = SET TMR BAT FUN CFG LCK); LCK is a state, not a mode
  const IND_NAME = ['SET', 'TMR', 'BAT', 'FUN', 'CFG', 'LCK'];
  const NEXT_MODE = [1, 2, 3, 4, 5, 0];            // LEFT SHORT while browsing: TIME > SET > TMR > BAT > FUN > CFG > TIME
  const LONG_MS = 1000, LOCK_MS = 2000, HOLD_MS = 400, REPEAT_MS = 120;   // HOLD_MS: Right hold in Time (date) and in Set (auto-repeat)
  const DAYS_IN = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  const SET_FIELDS = ['hour', 'minute', 'second', 'month', 'day', 'year'];
  function isLeap(y) { return (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0; }
  function daysIn(y, m) { return DAYS_IN[m - 1] + (m === 2 && isLeap(y) ? 1 : 0); }
  function weekdayIso(y, m, d) {                      // Mon=1 .. Sun=7 (Sakamoto's algorithm, integer only)
    const t = [0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4]; if (m < 3) y -= 1;
    const dow = (y + Math.floor(y / 4) - Math.floor(y / 100) + Math.floor(y / 400) + t[m - 1] + d) % 7;   // 0 = Sunday
    return ((dow + 6) % 7) + 1;
  }
  const BRI = [0.05, 0.10, 0.20, 0.30, 0.50];       // CFG 1: LED duty (fraction of reference current)
  const WAKE_SENS = [0.70, 0.50, 0.30];            // CFG 2: wrist-raise strength needed (low, med, high sensitivity)
  const DUR = [2000, 3000, 5000, 10000];           // CFG 3: how long the display stays on in Time
  const SEC_MODE = ['always', 'never'];
  const GAMES = ['Particles', 'Ring Runner', 'Target', 'Quick Draw', 'Orbit', 'Random', 'Pacer', 'Simon', 'Pong'];
  const RNG_MODES = ['coin', 'die', 'two dice', 'number 1-999', 'random clock'];
  const ORBIT_PATTERNS = ['radar', 'lissajous', 'comet', 'ripple', 'pendulums', 'twinkle'];
  const PONG_Z = 0.16, PONG_WIN = 5;
  const SCORE_CAP = 999;
  // Particles: four friction modes from dry sand to water, plus a 5th 'bead' mode (Left short cycles them)
  const PARTICLE_MODES = [
    { name: 'sand',   damp: 1.5, rest: 0.05, fric: 0.04, mix: 0.30, press: 0, mu: 0.30 },   // grains lock together and pile up
    { name: 'gravel', damp: 0.9, rest: 0.20, fric: 0.02, mix: 0.10, press: 0, mu: 0.12 },   // bouncier, rolls further
    { name: 'oil',    damp: 5.0, rest: 0.05, fric: 0.00, mix: 0.00, press: 1, mu: 0 },   // thick liquid: slow, flows, finds its level
    { name: 'water',  damp: 0.4, rest: 0.35, fric: 0.00, mix: 0.00, press: 1, mu: 0 },   // thin liquid: sloshes
    { name: 'bead',   damp: 0,   rest: 0,    fric: 0,    mix: 0,    press: 0, mu: 0 } ]; // not particles: one bead rolling on a ring (Right = next ring)
  const CFG_NAMES = ['brightness', 'raise sensitivity', 'wake duration', 'auto brightness', 'seconds LED', 'wake by raise', 'wake by shake', 'wake by tap', 'buttons that wake', 'lock display'];
  const CFG_COUNT = [5, 3, 4, 2, 2, 2, 2, 2, 4, 3];
  const MENU_CONFIRM_MS = 2500;                    // mode selection enters the highlighted mode by itself after this
  const TMR_KEEP_MS = 90000;                        // stopwatch mode keeps the display (and the mode) this long
  const CFG_KEYS = ['bri', 'wake', 'dur', 'auto', 'sec', 'raise', 'shake', 'tap', 'btnw', 'lockd'];
  const TENTHS_LED = [1, 2, 3, 4, 5, 7, 8, 9, 10, 11];   // hour-ring LED for tenths 0..9 (6 and 12 o'clock left out)
  const SHAKE_JERK = 3.0;                           // accumulated |delta a| (g) that counts as a shake
  const GAME_IDLE_MS = 300000, MODE_IDLE_MS = 15000;
  const I_REF_MA = 1.6, ROW_SINK_MA = 10;
  const TAU = Math.PI * 2;

  /* LED current through the 220 ohm + LED at a given supply (handoff: 1.6 mA @ 3.0 V ... 4.8 mA @ 4.2 V) */
  function ledMa(vdd) { return I_REF_MA + (vdd - 3.0) * 2.667; }

  function createWatch(face) {
    /* ---------- LED lookup tables (from the real netlist export) ---------- */
    const hourLed = [], minLed = [], secLed = [], ringLeds = [[], [], []];
    for (const L of face.leds) {
      const n = parseInt(L.ref.slice(1), 10);
      const led = { row: L.row, col: L.col, x: L.x, y: L.y, ang: (Math.atan2(L.x, -L.y) + TAU) % TAU, ref: L.ref };
      if (L.ring === 'H') { hourLed[n] = led; ringLeds[0].push(led); }
      else if (L.ring === 'M') { minLed[n] = led; ringLeds[1].push(led); }
      else { secLed[n] = led; ringLeds[2].push(led); }
    }
    for (const r of ringLeds) r.sort((a, b) => a.ang - b.ang);
    const indLed = face.inds.map(d => ({ row: d.row, col: d.col, x: d.x, y: d.y }));
    const allLeds = ringLeds[0].concat(ringLeds[1], ringLeds[2]);
    const radii = face.radii;

    const fb = new Uint8Array(ROWS * COLS);
    const evq = [];
    function log(m) { evq.push(m); }
    function put(led, lvl) { if (led) { const i = led.row * COLS + led.col; if (lvl > fb[i]) fb[i] = lvl; } }
    function ind(i, lvl) { put(indLed[i], lvl); }
    function ringAt(r, ang) {                       // nearest LED on ring r to an angle (rad, cw from 12)
      const a = ringLeds[r], n = a.length;
      const k = Math.round((((ang % TAU) + TAU) % TAU) / TAU * n) % n;
      return { led: a[k], k };
    }
    function bar(ring, frac, lvl) {                 // fill a ring clockwise from 12 o'clock, frac 0..1
      const a = ringLeds[ring], n = Math.round(Math.max(0, Math.min(1, frac)) * a.length);
      for (let i = 0; i < n; i++) put(a[i], lvl);
    }

    /* ---------- persistent state ---------- */
    const S = {
      mode: MODE.TIME, awake: false, idle: 0, tms: 0, locked: false, lockFlash: 0,
      rtcMs: 10 * 3600e3 + 8 * 60e3 + 37e3,
      set: { bri: 2, wake: 1, dur: 3, auto: 0, sec: 0, raise: 0, shake: 0, tap: 0, btnw: 0, lockd: 0 },   // 0 = first choice; raise/shake/tap 0 = ON (default)
      peek: 0, datePeek: 0, indOnly: false, shaken: false,
      menu: { on: false, sel: 0, t: 0, from: 0 },        // mode selection (Left long from anywhere)
      date: { y: 2026, m: 10, d: 11 },
      setField: 0,
      tmr: { run: false, el: 0 },
      bat: { view: 0 },
      cfgSel: 0,
      fun: { g: 0, playing: false },
      dead: false
    };
    const B = [{ down: false, t: 0, long: false, chord: false, eat: false, rep: 0 },
               { down: false, t: 0, long: false, chord: false, eat: false, rep: 0 }];
    let bothT = 0, lockDone = false, io = null;

    /* ---------- time helpers ---------- */
    function hms() {
      const s = Math.floor(S.rtcMs / 1000) % 86400;
      return { h: Math.floor(s / 3600), m: Math.floor(s / 60) % 60, s: s % 60 };
    }
    function setHms(h, m, s) { S.rtcMs = ((h % 24) * 3600 + (m % 60) * 60 + (s % 60)) * 1000; }

    function setDate(y, m, d) { S.date.y = y; S.date.m = m; S.date.d = Math.min(d, daysIn(y, m)); }
    function nextDay() {
      const D = S.date; D.d++;
      if (D.d > daysIn(D.y, D.m)) { D.d = 1; D.m++; if (D.m > 12) { D.m = 1; D.y++; } }
    }
    function wake() { if (!S.awake) { S.awake = true; log('display on'); } S.idle = 0; S.indOnly = false; }
    function wakeInd() { if (!S.awake) { S.awake = true; S.indOnly = true; } S.idle = 0; }   // light ONLY the LCK LED (lock feedback)
    function tmrKeep() { return S.mode === MODE.TMR && (S.tmr.run || S.tmr.el > 0); }
    function btnWakeOk(i) { const v = S.set.btnw; return v === 0 || (v === 1 && i === 0) || (v === 2 && i === 1); }
    function motionWake(what) {
      if (!S.awake || S.indOnly) { wake(); if (!tmrKeep()) S.mode = MODE.TIME; log(what + ' -> wake'); } else S.idle = 0;
    }
    function toMode(m) {
      S.mode = m; S.idle = 0; S.datePeek = 0; S.peek = 0; S.menu.on = false;
      if (m === MODE.SET) S.setField = 0;
      if (m === MODE.FUN) S.fun.playing = false;                          // entering FUN always shows the game picker
      log('mode -> ' + MODE_NAME[m]);
    }
    function menuOpen() { S.menu.on = true; S.menu.sel = S.mode; S.menu.from = S.mode; S.menu.t = 0; log('mode selection: Left = next mode, Right = enter it (or wait)'); }
    function menuConfirm() { const m = S.menu.sel; S.menu.on = false; toMode(m); }

    /* ---------- button events ---------- */
    /* BUTTON MODEL
       LEFT LONG (1 s), from anywhere, opens MODE SELECTION. In mode selection: LEFT short = next mode, RIGHT short (or waiting 2.5 s)
       = enter the highlighted mode, LEFT long = cancel. Inside a mode, both buttons belong to the mode:
       TIME: -/battery  SET: Left next unit, Right +1  TMR: Left reset, Right start/stop  BAT: Left/Right views
       FUN: picker (Left next game, Right start) then the game owns both buttons  CFG: Left next setting, Right change value. */
    function onShort(b) {
      S.idle = 0;
      if (S.menu.on) {
        const n = NEXT_MODE.length;                                      // Left = one mode to the left, Right = one to the right (wraps)
        S.menu.sel = (S.menu.sel + (b === 1 ? 1 : n - 1)) % n; S.menu.t = 0; log('highlight: ' + MODE_NAME[S.menu.sel]);
        return;
      }
      switch (S.mode) {
        case MODE.TIME: if (b === 1) { S.datePeek = 2000; S.peek = 0; log('date (2 s)'); } break;
        case MODE.SET:
          if (b === 0) { S.setField = (S.setField + 1) % SET_FIELDS.length; log('field: ' + SET_FIELDS[S.setField]); }
          else setAdd(1);
          break;
        case MODE.TMR:
          if (b === 1) { S.tmr.run = !S.tmr.run; log(S.tmr.run ? 'stopwatch start' : 'stopwatch stop'); }
          else if (!S.tmr.run && S.tmr.el > 0) { S.tmr.el = 0; log('stopwatch reset'); }
          break;
        case MODE.BAT: S.bat.view = (S.bat.view + (b === 1 ? 1 : 2)) % 3; break;
        case MODE.FUN:
          if (!S.fun.playing) {
            if (b === 0) { S.fun.g = (S.fun.g + 1) % GAMES.length; log('game: ' + GAMES[S.fun.g]); }
            else { S.fun.playing = true; gameStart(S.fun.g); log('start ' + GAMES[S.fun.g]); }
          } else gameButton(S.fun.g, b, false);
          break;
        case MODE.CFG:
          if (b === 0) { S.cfgSel = (S.cfgSel + 1) % CFG_COUNT.length; log('setting: ' + CFG_NAMES[S.cfgSel] + ' = ' + cfgValueText(S.cfgSel)); }
          else cfgChange();
          break;
      }
    }
    function onLong(b) {
      S.idle = 0;
      if (S.menu.on) {                                                   // in mode selection: Left long = Time, Right long = enter now
        if (b === 0) { toMode(MODE.TIME); } else menuConfirm();
        return;
      }
      if (b === 0) { menuOpen(); return; }
      switch (S.mode) {
        case MODE.TIME: S.peek = 2000; S.datePeek = 0; log('battery (2 s)'); break;
        case MODE.SET: setAdd(1); break;                                // then auto-repeats while held
        case MODE.TMR: S.tmr.run = false; S.tmr.el = 0; log('stopwatch reset'); break;
        case MODE.FUN:
          if (S.fun.playing && S.fun.g === 0) { if (G.sand.mode === 4) G.bead.w = 0; else sandRemove(4); }
          else if (S.fun.playing && S.fun.g === 6) { G.pc.kind = 1 - G.pc.kind; G.pc.t = 0; G.pc.show = 2500; log(G.pc.kind ? 'breath pacer' : 'metronome'); }
          break;   // Particles: Right hold removes particles (repeats); bead mode: stops the bead
      }
    }
    function longMs(i) { return i === 1 && S.mode === MODE.SET ? HOLD_MS : LONG_MS; }   // Right in SET: hold = auto-repeat after 0.4 s
    function setAdd(n) {
      const t = hms(), D = S.date;
      switch (S.setField) {
        case 0: setHms(t.h + n, t.m, t.s); break;
        case 1: setHms(t.h, t.m + n, t.s); break;
        case 2: setHms(t.h, t.m, t.s + n); break;
        case 3: setDate(D.y, D.m % 12 + 1, D.d); break;
        case 4: D.d = D.d % daysIn(D.y, D.m) + 1; break;
        case 5: D.y = D.y >= 2099 ? 2024 : D.y + 1; D.d = Math.min(D.d, daysIn(D.y, D.m)); break;
      }
    }
    function cfgChange() {
      const k = CFG_KEYS[S.cfgSel];
      S.set[k] = (S.set[k] + 1) % CFG_COUNT[S.cfgSel];
      log(CFG_NAMES[S.cfgSel] + ' = ' + cfgValueText(S.cfgSel));
    }
    function cfgValueText(i) {
      const v = S.set[CFG_KEYS[i]];
      return [BRI[v] * 100 + '%', ['low', 'medium', 'high'][v], DUR[v] / 1000 + ' s', v ? 'on' : 'off', SEC_MODE[v], v ? 'off' : 'on', v ? 'off' : 'on', v ? 'off' : 'on',
        ['either', 'left only', 'right only', 'none'][v], ['motion wakes it', 'stays dark', 'always on'][v]][i];
    }

    function toggleLock() {
      S.locked = !S.locked; S.lockFlash = 600; S.menu.on = false; if (S.mode !== MODE.TIME) toMode(MODE.TIME);
      log(S.locked ? 'buttons LOCKED' : 'buttons unlocked');
    }

    function buttons(dt) {
      const down = io.btn;
      // chord (both held) handling: lock/unlock after 2 s, no other action
      if (down[0] && down[1]) {
        bothT += dt; B[0].chord = B[1].chord = true;
        if (bothT >= 400 && !lockDone) wakeInd();                  // LCK blinks while both are held
        if (bothT >= LOCK_MS && !lockDone) { lockDone = true; toggleLock(); wakeInd(); }
      } else if (!down[0] && !down[1]) { bothT = 0; lockDone = false; }
      for (let i = 0; i < 2; i++) {
        const b = B[i];
        if (down[i] && !b.down) {                  // press
          b.down = true; b.t = 0; b.long = false; b.chord = down[1 - i]; b.rep = 0;
          b.eat = false; b.raw = false;
          if (!S.awake) {
            b.eat = true;                                            // a press on a dark watch is never also an action
            if (S.locked) { if (!b.chord) { wakeInd(); S.lockFlash = 600; log('locked: LCK lit, hold both 2 s to unlock'); } }   // buttons do not wake a locked watch, they just show LCK
            else if (btnWakeOk(i)) wake();
          }
          else if (S.locked && !b.chord) { b.eat = true; S.lockFlash = 600; wakeInd(); log('locked: press ignored (hold both 2 s to unlock)'); }
          else if (!b.chord && !S.menu.on && S.mode === MODE.FUN && S.fun.playing && (S.fun.g === 1 || S.fun.g === 2 || S.fun.g === 7 || S.fun.g === 8)) { gameButton(S.fun.g, i, false); b.raw = true; }   // arcade games react on press, not release
          S.idle = 0;
        } else if (down[i] && b.down) {
          b.t += dt;
          if (!b.eat && !b.chord && !(down[0] && down[1])) {
            if (!b.long && b.t >= longMs(i)) { b.long = true; b.rep = 0; onLong(i); }
            else if (b.long && i === 1 && S.mode === MODE.FUN && S.fun.playing && S.fun.g === 0 && G.sand.mode < 4 && !S.menu.on) { b.rep += dt; if (b.rep >= 200) { b.rep -= 200; sandRemove(2); } }
            else if (b.long && i === 1 && S.mode === MODE.SET && !S.menu.on) { b.rep += dt; const gap = b.t > 2500 ? 50 : REPEAT_MS; if (b.rep >= gap) { b.rep -= gap; setAdd(1); } }   // hold RIGHT = auto-repeat
          }
        } else if (!down[i] && b.down) {           // release
          b.down = false;
          if (!b.eat && !b.long && !b.chord && !b.raw && !S.locked) onShort(i);
          if (!b.eat && !b.long && S.locked && !b.chord) { /* flashed on press */ }
        }
      }
    }

    /* ---------- FUN: games ---------- */
    const G = {};                                   // per-game state
    function gameStart(g) {
      if (g === 0) { const m = G.sand ? G.sand.mode : 0; G.sand = { mode: m, p: [], flash: 0 }; for (let i = 0; i < 14; i++) sandAdd(true); G.bead = { ring: 1, th: Math.PI * 0.5, w: 0 }; }
      else if (g === 1) G.run = { lane: 1, dir: 1, th: 0, passed: 0, pts: 0, obs: [], over: false, award: false, spawn: 0, flash: 0 };
      else if (g === 2) G.tg = { lvl: 0, pts: 0, pos: 0, spd: 14, tol: 3.0, posq: 0, spdq: 14 * 65536, tolq: 3 * 65536, over: false, award: false, hitFlash: 0, t: 0, lastK: 0 };   // *q = the same values in Q16 integers (the C port uses these, so both cores round identically)
      else if (g === 3) G.qd = { st: 'idle', t: 0, wait: 0, win: 0, who: -1 };
      else if (g === 4) G.orb = { pat: G.orb ? G.orb.pat : 0, ph: 0, stars: new Float32Array(allLeds.length) };
      else if (g === 5) G.rng = { mode: G.rng ? G.rng.mode : 0, roll: 0, res: null, age: 0, cool: 0, flash: 0 };
      else if (g === 6) G.pc = { kind: G.pc ? G.pc.kind : 0, bpm: G.pc ? G.pc.bpm : 100, br: G.pc ? G.pc.br : 6, t: 0, show: 2500 };
      else if (g === 7) G.sim = { st: 'ready', seq: [], i: 0, t: 0, pts: 0, over: false, award: false, flash: 0, fside: 0 };
      else if (g === 8) G.pg = { st: 'ready', mode: G.pg ? G.pg.mode : 0, pos: 0.5, dir: 1, spd: 0.8, s1: 0, s2: 0, pts: 0, t: 0, hit: [0, 0], winner: 0, award: false };
    }
    function gameButton(g, b, long) {                // b = 0 left, 1 right (Quick Draw reads the buttons itself)
      if (g === 0) {                                                                         // Particles (modes: sand, gravel, oil, water, bead)
        const s = G.sand;
        if (b === 1) { if (s.mode === 4) G.bead.ring = (G.bead.ring + 1) % 3; else sandAdd(false); }   // Right: add a particle / bead: next ring
        else { s.mode = (s.mode + 1) % PARTICLE_MODES.length; s.flash = 1200; log('particles: ' + PARTICLE_MODES[s.mode].name); }   // Left: next mode
      }
      else if (g === 1) {
        const r = G.run;
        if (r.over) { gameStart(1); return; }
        r.lane = Math.max(0, Math.min(2, r.lane + (b === 0 ? -1 : 1)));                   // Left: lane in, Right: lane out
      } else if (g === 2) {
        const t = G.tg;
        if (t.over) { gameStart(2); return; }
        const k = Math.round(t.pos) % 60, dist = Math.min(k, 60 - k);                     // either button hits
        if (dist <= t.tol) {
          t.pts = Math.min(SCORE_CAP, t.pts + 10 + t.lvl); t.lvl++; t.spdq = Math.min(90 * 65536, Math.floor(t.spdq * 11 / 10)); t.tolq = Math.max(39322, Math.floor(t.tolq * 23 / 25)); t.spd = t.spdq / 65536; t.tol = t.tolq / 65536; t.hitFlash = 600;
          log('hit! level ' + t.lvl + ', ' + t.pts + ' points');
          if (t.pts >= SCORE_CAP) { t.over = true; t.award = true; t.t = 0; log('999 - AWARD!'); }
        } else { t.over = true; t.t = 0; t.lastK = k; log('missed by ' + dist + ' LEDs, score ' + t.pts); }
      } else if (g === 4) { G.orb.pat = (G.orb.pat + (b === 1 ? 1 : ORBIT_PATTERNS.length - 1)) % ORBIT_PATTERNS.length; log('orbit: ' + ORBIT_PATTERNS[G.orb.pat]); }   // Right: next pattern, Left: previous
      else if (g === 5) {                                                                    // Random
        const r = G.rng;
        if (b === 1) { if (r.roll <= 0) rngRoll(); }
        else { r.mode = (r.mode + 1) % RNG_MODES.length; r.res = null; r.roll = 0; r.flash = 1200; log('random: ' + RNG_MODES[r.mode]); }
      } else if (g === 6) {                                                                  // Pacer: Left slower, Right faster
        const p = G.pc;
        if (p.kind === 0) p.bpm = Math.max(40, Math.min(220, p.bpm + (b === 1 ? 5 : -5))); else p.br = Math.max(3, Math.min(12, p.br + (b === 1 ? 1 : -1)));
        p.show = 2500; p.t = 0; log(p.kind ? p.br + ' breaths/min' : p.bpm + ' bpm');
      } else if (g === 7) simonPress(b);
      else if (g === 8) pongPress(b);
    }

    /* ---- score display shared by all scoring games: 0-999 as three digits ----
       hundreds on the HOUR ring, tens on the MINUTE ring, ones on the OUTER (second) ring.
       Each digit is a bar of that many LEDs counted from 12 o'clock (a dim marker sits at 12 so a zero is visible).
       The digits blink for 8 s, then stay steady. Reaching the 999 cap plays the award animation instead (10 s), then shows 999. */
    function showScore(score, t) {
      const d = [Math.floor(score / 100) % 10, Math.floor(score / 10) % 10, score % 10];
      const on = t > 8000 || Math.floor(t / 200) % 2 === 0;
      for (let r = 0; r < 3; r++) { put(ringLeds[r][0], 35); if (on) for (let i = 0; i < d[r]; i++) put(ringLeds[r][i], 255); }
    }
    function awardStep(t) {                          // t ms since the 999 was reached: comets, sparkles and flashing indicators
      const ph = t / 1000;
      for (let r = 0; r < 3; r++) {
        const sp = (r % 2 ? -1 : 1) * (1.2 + ph * 0.5 + r * 0.7);
        for (let c = 0; c < 6; c++) for (let k = 0; k < 4; k++) put(ringAt(r, sp * ph + c * TAU / 6 - Math.sign(sp) * k * 0.09).led, Math.round(255 / (1 + k)));
      }
      for (let i = 0; i < 10; i++) put(allLeds[Math.floor(Math.random() * allLeds.length)], 255);
      if (Math.floor(t / 250) % 2 === 0) for (let i = 0; i < 5; i++) ind(i, 255);
    }
    function gameOverDisplay(score, award, t) {
      if (award && t < 10000) awardStep(t); else showScore(score, t);
    }

    /* sand / water: particles live in the annulus that holds the LED rings */
    const R_IN = radii.H - 1.5, R_OUT = radii.S + 1.2, PR = 0.8;
    function sandRemove(n) { const p = G.sand.p; if (p.length) { p.splice(0, Math.min(n, p.length)); log('particles: ' + p.length); } }
    function sandAdd(init) {
      const p = G.sand.p; if (p.length >= 60) return;
      const a = Math.random() * TAU, r = init ? R_IN + 1 + Math.random() * (R_OUT - R_IN - 2) : (R_IN + R_OUT) / 2;
      const ang = init ? a : -0.2 + Math.random() * 0.4;               // drop near 12 o'clock
      p.push({ x: r * Math.sin(ang), y: -r * Math.cos(ang), vx: 0, vy: 0 });
    }
    function sandStep(dt, f) {
      const s = G.sand, p = s.p, n = Math.max(1, Math.ceil(dt / 4)), h = dt / n / 1000;
      const gx = -f.x * 700, gy = f.y * 700;                            // board coords: y down
      const PM = PARTICLE_MODES[s.mode], damp = PM.damp, rest = PM.rest, fric = PM.fric;
      for (let it = 0; it < n; it++) {
        for (const q of p) {
          q.vx += gx * h; q.vy += gy * h;
          const d = Math.max(0, 1 - damp * h); q.vx *= d; q.vy *= d;
          q.x += q.vx * h; q.y += q.vy * h;
        }
        for (let i = 0; i < p.length; i++) for (let j = i + 1; j < p.length; j++) {
          const dx = p[j].x - p[i].x, dy = p[j].y - p[i].y, d2 = dx * dx + dy * dy, md = PR * 2;
          if (d2 < md * md && d2 > 1e-9) {
            const d = Math.sqrt(d2), nx = dx / d, ny = dy / d, ov = (md - d) / 2;
            p[i].x -= nx * ov; p[i].y -= ny * ov; p[j].x += nx * ov; p[j].y += ny * ov;
            const rv = (p[j].vx - p[i].vx) * nx + (p[j].vy - p[i].vy) * ny;
            if (rv < 0) {
              const k = -(1 + rest) * rv / 2;
              p[i].vx -= k * nx; p[i].vy -= k * ny; p[j].vx += k * nx; p[j].vy += k * ny;
              if (PM.mix > 0) { const m = (p[i].vx + p[j].vx) / 2, mm = (p[i].vy + p[j].vy) / 2, k0 = 1 - PM.mix; p[i].vx = p[i].vx * k0 + m * PM.mix; p[j].vx = p[j].vx * k0 + m * PM.mix; p[i].vy = p[i].vy * k0 + mm * PM.mix; p[j].vy = p[j].vy * k0 + mm * PM.mix; }
            }
            if (PM.press) { const push = ov * 60 * h; p[i].vx -= nx * push; p[i].vy -= ny * push; p[j].vx += nx * push; p[j].vy += ny * push; }
          }
        }
        for (const q of p) {
          const r = Math.hypot(q.x, q.y) || 1e-6, nx = q.x / r, ny = q.y / r;
          let lim = -1;
          if (r > R_OUT - PR) lim = R_OUT - PR; else if (r < R_IN + PR) lim = R_IN + PR;
          if (lim > 0) {
            q.x = nx * lim; q.y = ny * lim;
            const vn = q.vx * nx + q.vy * ny;
            if ((lim === R_OUT - PR && vn > 0) || (lim !== R_OUT - PR && vn < 0)) {
              q.vx -= (1 + rest) * vn * nx; q.vy -= (1 + rest) * vn * ny;
              const vn2 = q.vx * nx + q.vy * ny, tx = q.vx - vn2 * nx, ty = q.vy - vn2 * ny;
              q.vx -= tx * fric; q.vy -= ty * fric;
            }
            if (PM.mu > 0 && lim === R_OUT - PR) {                                          // static friction on the OUTER wall only (a pile on a dome would never fall): a grain stays put until the slope is steeper than atan(mu)
              const gN = -(gx * nx + gy * ny) * (lim === R_OUT - PR ? -1 : 1), gT = Math.abs(-gx * ny + gy * nx);
              const vt = Math.abs(-q.vx * ny + q.vy * nx);
              if (gN > 0 && gT < PM.mu * gN && vt < 25) { q.vx *= 0.5; q.vy *= 0.5; if (vt < 8) { q.vx = 0; q.vy = 0; } }
            }
          }
        }
      }
      if (s.flash > 0) { s.flash -= dt; put(hourLed[s.mode + 1], 255); }   // friction mode 1-4 on the hour ring for 1.2 s after changing
      for (const q of p) {                                              // light nearest LED
        let best = null, bd = 4.84;
        for (const L of allLeds) { const d = (L.x - q.x) ** 2 + (L.y - q.y) ** 2; if (d < bd) { bd = d; best = L; } }
        put(best, 255);
      }
    }

    function beadStep(dt, f) {
      const b = G.bead, R = radii[['H', 'M', 'S'][b.ring]], h = dt / 1000;
      const gx = -f.x, gy = f.y;                                        // board coords
      const at = (gx * Math.cos(b.th) + gy * Math.sin(b.th)) * 700 / R;  // tangential accel (rad/s^2)
      b.w += at * h; b.w *= Math.max(0, 1 - 0.8 * h); b.th += b.w * h;
      const tail = Math.min(4, Math.round(Math.abs(b.w) / 2.5));
      const dir = b.w >= 0 ? -1 : 1, a = ringLeds[b.ring], n = a.length;
      const k = ringAt(b.ring, b.th).k;
      put(a[k], 255);
      for (let i = 1; i <= tail; i++) put(a[((k + dir * i) % n + n) % n], Math.round(255 / (i + 1.2)));
    }

    function runStep(dt) {
      const r = G.run;
      if (r.over) {
        r.flash += dt;
        gameOverDisplay(r.pts, r.award, r.flash);
        if (r.flash < 8000 && Math.floor(r.flash / 400) % 2 === 0) ind(3, 255);
        return;
      }
      const speed = 0.9 + 0.12 * Math.floor(r.passed / 10);               // faster every 10 obstacles
      r.th += speed * dt / 1000;
      r.spawn -= dt;
      const lookahead = 2.4;
      if (r.spawn <= 0 && r.obs.length < 8) {
        const lane = Math.floor(Math.random() * 3), ang = r.th + lookahead + Math.random() * 0.6;
        const k = ringAt(lane, ang).k;
        const same = r.obs.filter(o => Math.abs(o.ang - ang) < 0.5).length;
        if (same < 2) r.obs.push({ lane, k, ang: ringAt(lane, ang).led.ang + Math.floor(ang / TAU) * TAU, passed: false });
        r.spawn = Math.max(350, 1000 - r.passed * 12) * (0.6 + Math.random() * 0.8);
      }
      const me = ringAt(r.lane, r.th);
      for (const o of r.obs) {
        if (o.lane === r.lane && o.k === me.k && Math.abs(o.ang - r.th) < 0.35) { r.over = true; r.flash = 0; log('crash! ' + r.pts + ' points'); return; }
        if (!o.passed && r.th > o.ang + 0.4) {
          o.passed = true; r.passed++; r.pts = Math.min(SCORE_CAP, r.pts + 10);                    // 10 points per obstacle
          if (r.pts >= SCORE_CAP) { r.over = true; r.award = true; r.flash = 0; log('999 - AWARD!'); return; }
        }
      }
      r.obs = r.obs.filter(o => r.th - o.ang < 1.0);
      for (const o of r.obs) if (Math.floor(S.tms / 150) % 2 === 0) put(ringLeds[o.lane][o.k], 200);
      put(me.led, 255);
    }

    function targetStep(dt) {
      const t = G.tg; t.t += dt;
      const ring = ringLeds[1], blink = Math.floor(S.tms / 250) % 2 === 0;
      if (t.over) { gameOverDisplay(t.pts, t.award, t.t); if (t.t < 8000 && Math.floor(t.t / 400) % 2 === 0) ind(3, 255); return; }
      t.posq = (t.posq + Math.floor(t.spdq * dt / 1000)) % (60 * 65536); t.pos = t.posq / 65536;
      const nrun = 1 + Math.min(2, Math.floor(t.lvl / 4));            // decoy lights join as you level up
      put(ring[Math.round(t.pos) % 60], 255);
      for (let i = 1; i < nrun; i++) put(ring[Math.round(t.pos + i * 60 / nrun) % 60], 110);
      const tol = Math.floor(t.tol);                                  // target zone: shrinks as you improve
      put(ring[0], 70); for (let i = 1; i <= tol; i++) { put(ring[i], 30); put(ring[60 - i], 30); }
      put(hourLed[12], 120);
      if (t.hitFlash > 0) { t.hitFlash -= dt; if (Math.floor(t.hitFlash / 100) % 2 === 0) { for (let i = 0; i < 12; i++) put(ringLeds[0][i], 255); put(ring[0], 255); } }
      else bar(0, Math.min(12, t.lvl) / 12, 120);                       // level on the hour ring
    }

    function qdStep(dt) {
      const q = G.qd; q.t += dt;
      const half = (side, lvl) => { for (const L of allLeds) if ((side < 0 ? Math.sin(L.ang) < -0.02 : Math.sin(L.ang) > 0.02)) put(L, lvl); };
      const blink = Math.floor(S.tms / 300) % 2 === 0;
      if (q.st === 'idle') {                                           // hold both buttons 0.5 s, release both = armed
        ind(3, blink ? 255 : 60);
        if (B[0].down && B[1].down && B[0].t > 500 && B[1].t > 500) { q.armHeld = true; for (const L of ringLeds[2]) if (L.ang < 0.2 || L.ang > TAU - 0.2) put(L, 180); }
        else if (q.armHeld && !B[0].down && !B[1].down) { q.armHeld = false; q.st = 'wait'; q.t = 0; q.wait = 2000 + Math.floor(Math.random() * 4000); log('armed, wait for flash'); }
      } else if (q.st === 'wait') {
        ind(3, 255);
        if (io.btn[0] || io.btn[1]) { q.who = io.btn[0] ? 0 : 1; q.win = 1 - q.who; q.st = 'result'; q.t = 0; q.false = true; log('false start! player ' + (q.win + 1) + ' wins'); }
        else if (q.t >= q.wait) { q.st = 'go'; q.t = 0; log('GO!'); }
      } else if (q.st === 'go') {
        for (const L of ringLeds[2]) put(L, 255);
        for (const L of ringLeds[1]) put(L, 255);
        if (io.btn[0] || io.btn[1]) { q.win = io.btn[0] ? 0 : 1; log('player ' + (q.win + 1) + ' wins in ' + Math.round(q.t) + ' ms'); q.st = 'result'; q.t = 0; q.false = false; }
        else if (q.t > 2500) { q.st = 'idle'; }
      } else {                                                         // result: winner's side lights (left = 270 deg half)
        half(q.win === 0 ? -1 : 1, q.false ? (Math.floor(q.t / 150) % 2 ? 255 : 90) : 255);
        if (q.t > 3000) { q.st = 'idle'; }
      }
    }

    function orbitStep(dt, f) {
      const o = G.orb; o.ph += dt / 1000 * (1.0 + f.x * 1.5 + f.y * 1.0);
      if (o.pat === 0) {                                               // radar sweep with trail
        for (let r = 0; r < 3; r++) for (let t = 0; t < 7; t++) put(ringAt(r, o.ph * 1.5 - t * 0.09).led, Math.round(255 / (1 + t * 0.9)));
      } else if (o.pat === 1) {                                        // 1:2:3 Lissajous, three dots
        put(ringAt(0, o.ph).led, 255); put(ringAt(1, -o.ph * 2).led, 255); put(ringAt(2, o.ph * 3).led, 255);
      } else if (o.pat === 2) {                                        // spiral comet across the rings
        const n = 3 * 20, k = Math.floor(o.ph * 10) % n;
        for (let t = 0; t < 8; t++) { const kk = ((k - t) % n + n) % n; put(ringAt(kk % 3, (kk / 3) * TAU / 20 * 3 + kk * 0.2).led, Math.round(255 / (1 + t * 0.7))); }
      } else if (o.pat === 3) {                                        // ripple: brightness waves travel from the inner ring to the outer ring
        for (let r = 0; r < 3; r++) { const lvl = Math.max(0, Math.sin(o.ph * 3 - r * 1.6)); if (lvl > 0.05) for (let i = 0; i < ringLeds[r].length; i += (r === 0 ? 1 : 3)) put(ringLeds[r][i], Math.round(255 * lvl)); }
      } else if (o.pat === 4) {                                        // pendulums: six dots swinging at slightly different rates drift in and out of step
        for (let r = 0; r < 3; r++) for (let k = 0; k < 2; k++) put(ringAt(r, Math.PI + 1.25 * Math.sin(o.ph * (1.6 + 0.22 * (r * 2 + k)))).led, 255);
      } else {                                                         // twinkle: random LEDs fade in and out
        const st = o.stars, d = Math.exp(-dt / 450);
        for (let i = 0; i < st.length; i++) st[i] *= d;
        for (let n = 0; n < Math.floor(dt / 50); n++) st[Math.floor(Math.random() * st.length)] = 255;   // about 20 new stars a second
        if (Math.random() < (dt % 50) / 50) st[Math.floor(Math.random() * st.length)] = 255;
        for (let i = 0; i < st.length; i++) if (st[i] > 20) put(allLeds[i], Math.round(st[i]));
      }
    }

    /* ---------- Random: coin / die / two dice / 1-999 / random clock. Right = roll (or shake the watch), Left = next mode ---------- */
    function rngRoll() {
      const r = G.rng, R = (n) => 1 + Math.floor(Math.random() * n);
      r.roll = 900; r.age = 0; r.cool = 1500;
      const N = (n) => Math.floor(Math.random() * n);                          // draw only what this mode needs (the C port makes the same draws in the same order)
      if (r.mode === 0) r.res = { c: R(2) };
      else if (r.mode === 1) r.res = { d: [R(6)] };
      else if (r.mode === 2) { const a = R(6), b = R(6); r.res = { d: [a, b] }; }
      else if (r.mode === 3) r.res = { n: R(999) };
      else { const h = R(12), m = N(60), s2 = N(60); r.res = { h, m, s: s2 }; }
      log(RNG_MODES[r.mode] + ' -> ' + JSON.stringify(r.res));
    }
    function rngStep(dt) {
      const r = G.rng; r.age += dt; if (r.cool > 0) r.cool -= dt;
      if (S.shaken && r.cool <= 0 && r.roll <= 0) rngRoll();
      if (r.flash > 0) { r.flash -= dt; put(hourLed[r.mode + 1], 255); }      // mode number on the hour ring for 1.2 s
      if (r.roll > 0) {                                                       // tumbling
        r.roll -= dt;
        const rings = r.mode <= 1 ? [2] : r.mode === 2 ? [1, 2] : [0, 1, 2];
        for (const rg of rings) for (let i = 0; i < 4; i++) put(ringLeds[rg][Math.floor(Math.random() * ringLeds[rg].length)], 255);
        return;
      }
      if (!r.res) { if (Math.floor(S.tms / 500) % 2 === 0) put(hourLed[12], 160); return; }   // waiting for a roll
      const q = r.res;
      if (r.mode === 0) { const heads = q.c === 1; for (const L of ringLeds[2]) if (heads ? Math.sin(L.ang) > 0.02 : Math.sin(L.ang) < -0.02) put(L, 255); put(hourLed[heads ? 3 : 9], 255); }   // heads = right half, tails = left half
      else if (r.mode === 1) bar(2, q.d[0] / 60, 255);                        // die: that many outer LEDs
      else if (r.mode === 2) { bar(1, q.d[0] / 60, 255); bar(2, q.d[1] / 60, 255); bar(0, (q.d[0] + q.d[1]) / 12, 120); }   // die 1 minute ring, die 2 outer ring, total on the hour ring
      else if (r.mode === 3) showScore(q.n, r.age + 6500);                    // 1-999 as hundreds / tens / ones
      else { put(hourLed[q.h], 255); put(minLed[q.m], 255); put(secLed[q.s], 255); }   // three random "clock hands"
    }

    /* ---------- Pacer: metronome (40-220 bpm) and breath pacer (3-12 breaths/min). Left slower, Right faster, Right long switches ---------- */
    function pacerStep(dt) {
      const p = G.pc; p.t += dt;
      if (p.show > 0) { p.show -= dt; showScore(p.kind ? p.br : p.bpm, 9000); return; }   // the tempo as a number for 2.5 s after any change
      if (p.kind === 0) {                                                    // metronome: a dot swings along the bottom of the outer ring, ticking at the ends
        const per = 60000 / p.bpm, beat = Math.floor(p.t / per), since = p.t - beat * per;
        const pos = (t) => -Math.cos(Math.PI * t / per);
        put(ringAt(2, Math.PI - 1.3 * pos(p.t)).led, 255);
        put(ringAt(2, Math.PI - 1.3 * pos(p.t - 60)).led, 90);
        if (since < 80) { if (beat % 4 === 0) { put(hourLed[12], 255); put(hourLed[6], 255); } else put(hourLed[6], 160); }
        put(hourLed[[12, 3, 6, 9][beat % 4]], 110);                         // beat counter 1-4 on the hour ring
      } else {                                                               // breath pacer: the minute ring fills while you breathe in (40 %) and empties as you breathe out (60 %)
        const per = 60000 / p.br, ph = (p.t % per) / per, ease = (x) => 0.5 - 0.5 * Math.cos(Math.PI * x);
        const f = ph < 0.4 ? ease(ph / 0.4) : 1 - ease((ph - 0.4) / 0.6);
        bar(1, f, 255); bar(0, f, 110);
      }
    }

    /* ---------- Simon: Left and Right are the two symbols (left half / right half of the face). Watch, then repeat. 5 points per correct press ---------- */
    function simHalf(side, lvl) { for (const L of ringLeds[2]) if (side === 0 ? Math.sin(L.ang) < -0.02 : Math.sin(L.ang) > 0.02) put(L, lvl); put(hourLed[side === 0 ? 9 : 3], lvl); }
    function simonPress(side) {
      const m = G.sim;
      if (m.over) { gameStart(7); return; }
      if (m.st !== 'input') return;                                           // presses while the watch is showing the sequence are ignored
      m.flash = 220; m.fside = side; m.t = 0;
      if (m.seq[m.i] === side) {
        m.i++; m.pts = Math.min(SCORE_CAP, m.pts + 5);
        if (m.pts >= SCORE_CAP) { m.over = true; m.award = true; m.t = 0; log('999 - AWARD!'); }
        else if (m.i === m.seq.length) { m.st = 'next'; m.t = 0; log('round ' + m.seq.length + ' done, ' + m.pts + ' points'); }
      } else { m.over = true; m.t = 0; log('wrong! ' + m.pts + ' points'); }
    }
    function simonStep(dt) {
      const m = G.sim; m.t += dt;
      if (m.over) { gameOverDisplay(m.pts, m.award, m.t); if (m.t < 8000 && Math.floor(m.t / 400) % 2 === 0) ind(3, 255); return; }
      if (m.flash > 0) { m.flash -= dt; simHalf(m.fside, 255); }
      bar(0, Math.min(12, m.seq.length) / 12, 70);                           // sequence length on the hour ring
      if (m.st === 'ready' || m.st === 'next') {
        if (m.t > (m.st === 'ready' ? 900 : 700)) { m.seq.push(Math.random() < 0.5 ? 0 : 1); m.st = 'show'; m.t = 0; }
        return;
      }
      if (m.st === 'show') {
        const on = Math.max(200, 600 - 22 * m.seq.length), slot = on + 140, i = Math.floor(m.t / slot);
        if (i >= m.seq.length) { m.st = 'input'; m.i = 0; m.t = 0; return; }
        if (m.t % slot < on) simHalf(m.seq[i], 255);
        return;
      }
      put(ringLeds[1][0], 170);                                              // "your turn": a steady LED at 12 on the minute ring
      if (m.t > 4000) { m.over = true; m.t = 0; log('too slow! ' + m.pts + ' points'); }
    }

    /* ---------- Pong: the ball travels the bottom half of the minute ring between two paddle zones (9 and 3 o'clock). ----------
       Press your button while the ball is inside your zone to hit it back; each return is faster, a hit at the very end is a smash.
       2 players: first to 5 (Left = left player, Right = right player). Solo: the left end is a wall, either button defends the right end; 10 points per return. */
    function pongPos(pos) { return ringAt(1, 1.5 * Math.PI - pos * Math.PI).led; }
    function pongServe(loser) { const g = G.pg; g.st = 'play'; g.pos = 0.5; g.dir = loser === 0 ? -1 : 1; g.spd = 0.8; }
    function pongPoint(winner) {
      const g = G.pg;
      if (winner === 0) g.s1++; else g.s2++;
      if (g.s1 >= PONG_WIN || g.s2 >= PONG_WIN) { g.st = 'over'; g.t = 0; g.winner = winner; log('player ' + (winner + 1) + ' wins ' + g.s1 + '-' + g.s2); }
      else { g.st = 'point'; g.t = 0; g.winner = winner; log('point to player ' + (winner + 1) + ': ' + g.s1 + '-' + g.s2); }
    }
    function pongPress(b) {
      const g = G.pg;
      if (g.st === 'ready') { if (b === 0) { g.mode = 1 - g.mode; log(g.mode ? 'solo (wall on the left)' : 'two players'); } else pongServe(1); return; }
      if (g.st === 'over') { if (g.mode === 0 && g.t < 3000) return; gameStart(8); return; }
      if (g.st !== 'play') return;
      const side = g.mode === 1 ? 1 : b;
      const inZone = side === 0 ? g.pos <= PONG_Z : g.pos >= 1 - PONG_Z, toward = side === 0 ? g.dir < 0 : g.dir > 0;
      if (!inZone || !toward) return;                                        // a swing and a miss costs nothing
      const edge = side === 0 ? g.pos : 1 - g.pos;
      g.dir = -g.dir; g.spd = Math.min(2.2, g.spd + 0.07 + (edge < 0.05 ? 0.12 : 0)); g.hit[side] = 200;
      if (g.mode === 1) { g.pts = Math.min(SCORE_CAP, g.pts + 10); if (g.pts >= SCORE_CAP) { g.st = 'over'; g.award = true; g.t = 0; log('999 - AWARD!'); } }
    }
    function pongStep(dt) {
      const g = G.pg; g.t += dt; g.hit[0] = Math.max(0, g.hit[0] - dt); g.hit[1] = Math.max(0, g.hit[1] - dt);
      if (g.st === 'over' && g.mode === 1) { gameOverDisplay(g.pts, g.award, g.t); if (g.t < 8000 && Math.floor(g.t / 400) % 2 === 0) ind(3, 255); return; }
      for (let k = 0; k <= 30; k++) {                                        // the field: paddle zones at both ends of the ball's path
        const pos = k / 30, inL = pos <= PONG_Z, inR = pos >= 1 - PONG_Z;
        if (inL || inR) put(pongPos(pos), (inL && g.hit[0] > 0) || (inR && g.hit[1] > 0) ? 255 : 45);
      }
      if (g.st === 'ready') { put(hourLed[g.mode + 1], Math.floor(S.tms / 300) % 2 ? 255 : 120); put(pongPos(0.5), 255); return; }   // hour LED 1 = two players, 2 = solo
      if (g.mode === 0) { for (let i = 1; i <= g.s1; i++) put(hourLed[12 - i], 255); for (let i = 1; i <= g.s2; i++) put(hourLed[i], 255); }   // scores: left player counts up the left of the hour ring, right player up the right
      if (g.st === 'over') {                                                 // two players: the winner's half lights and blinks for 3 s
        if (Math.floor(g.t / 200) % 2 === 0) for (const L of ringLeds[2]) if (g.winner === 0 ? Math.sin(L.ang) < -0.02 : Math.sin(L.ang) > 0.02) put(L, 255);
        if (g.t > 3000) gameStart(8);
        return;
      }
      if (g.st === 'point') { put(pongPos(g.winner === 0 ? 0 : 1), 255); if (g.t > 900) pongServe(1 - g.winner); return; }
      g.pos += g.dir * g.spd * dt / 1000;
      if (g.pos <= 0) { if (g.mode === 1) { g.pos = 0; g.dir = 1; } else { pongPoint(1); return; } }
      else if (g.pos >= 1) { if (g.mode === 1) { g.st = 'over'; g.t = 0; log('missed, ' + g.pts + ' points'); return; } else { pongPoint(0); return; } }
      put(pongPos(Math.max(0, Math.min(1, g.pos))), 255);
    }

    /* ---------- rendering of the non-game modes ---------- */
    function renderTime(blinkOn) {
      const t = hms();
      put(hourLed[t.h % 12 === 0 ? 12 : t.h % 12], 255);
      put(minLed[t.m], 255);
      if (S.set.sec === 0 && !(S.locked && S.set.lockd === 2)) put(secLed[t.s], 255);   // locked always-on display: no seconds LED
    }
    /* date: MONTH on the hour ring (Jan = 1 o'clock ... Dec = 12), DAY on the minute ring (day 15 = the 15-minute LED),
       WEEKDAY as a bar on the outer ring: Mon = 1 LED ... Sun = 7 LEDs, counted from 12 o'clock */
    function renderDate(blinkField, blinkOn) {
      const D = S.date, show = (f) => (blinkField === f ? (blinkOn ? 255 : 0) : 255);
      put(hourLed[D.m], show(3)); put(minLed[D.d], show(4));
      const wd = weekdayIso(D.y, D.m, D.d); const a = ringLeds[2];
      for (let i = 0; i < wd; i++) put(a[i], blinkField === 3 || blinkField === 4 ? 140 : 255);
    }

    function render(dt) {
      fb.fill(0);
      S.tms += dt;
      const blink2 = Math.floor(S.tms / 250) % 2 === 0, blink4 = Math.floor(S.tms / 125) % 2 === 0;
      if (!S.awake) return;
      const holdingBoth = bothT >= 400 && !lockDone;
      if (S.indOnly) {                                                     // lock feedback: only the LCK LED
        if (S.lockFlash > 0) S.lockFlash -= dt;
        ind(5, holdingBoth || S.lockFlash > 0 ? (blink4 ? 255 : 0) : (S.locked ? 255 : 0));
        return;
      }
      if (S.menu.on) {                                                     // mode selection: only the highlighted mode's indicator blinks
        const sel = S.menu.sel;
        if (blink2) { if (sel === 0) put(hourLed[12], 255); else ind(MODE_IND[sel], 255); }   // just the highlighted mode's LED blinks (Time = the 12 o'clock hour LED)
        return;
      }
      const lowBat = !io.batOk;
      if (S.dead) { if (blink4) ind(2, 255); return; }
      switch (S.mode) {
        case MODE.TIME:
          if (S.peek > 0) { bar(0, io.soc, 255); ind(2, 255); S.peek -= dt; }
          else if (S.datePeek > 0) { renderDate(-1, true); S.datePeek -= dt; }
          else renderTime();
          break;
        case MODE.SET: {                                                    // the unit being set blinks
          const t = hms(), f = S.setField, on = blink2;
          const h12 = t.h % 12 === 0 ? 12 : t.h % 12, dim = 70;
          if (f <= 2) { put(hourLed[h12], f === 0 ? (on ? 255 : 0) : dim); put(minLed[t.m], f === 1 ? (on ? 255 : 0) : dim); put(secLed[t.s], f === 2 ? (on ? 255 : 0) : dim); }
          else if (f <= 4) renderDate(f, on);                               // month / day: date view, chosen unit blinks
          else { put(minLed[(S.date.y - 2000) % 60], on ? 255 : 0); put(hourLed[12], 60); }   // year: LED at yy on the minute ring
          break;
        }
        case MODE.TMR: {
          const e = S.tmr.el, sec = Math.floor(e / 1000) % 60, min = Math.floor(e / 60000) % 60;
          put(secLed[sec], 255); put(minLed[min], 160);
          put(hourLed[TENTHS_LED[Math.floor(e / 100) % 10]], 90);   // tenths of a second on the hour ring: 10 LEDs, 6 and 12 skipped
          break;
        }
        case MODE.BAT:
          if (S.bat.view === 0) { bar(0, io.soc, 255); }
          else if (S.bat.view === 1) { bar(1, Math.min(1, Math.log10(1 + io.solarMw) / Math.log10(31)), 200); }
          else { if (io.charging) { const k = Math.floor(S.tms / 90) % 12; put(hourLed[k === 0 ? 12 : k], 255); put(hourLed[(k + 11) % 12 || 12], 90); } else put(hourLed[12], 120); }
          ind(2, io.charging && S.bat.view === 2 ? Math.round(120 + 135 * (0.5 + 0.5 * Math.sin(S.tms / 250))) : 255);
          break;
        case MODE.FUN:
          if (!S.fun.playing) put(hourLed[S.fun.g + 1], blink2 ? 255 : 120);   // game picker: hour LED n = game n
          break;
        case MODE.CFG: {
          put(hourLed[S.cfgSel + 1], 255);
          const v = S.set[CFG_KEYS[S.cfgSel]];
          bar(1, (v + 1) / CFG_COUNT[S.cfgSel], 255);
          break;
        }
      }
      if (S.mode === MODE.FUN && S.fun.playing) {
        const f = io.accel, g = S.fun.g;
        if (g === 0) { if (G.sand.mode === 4) { beadStep(dt, f); if (G.sand.flash > 0) { G.sand.flash -= dt; put(hourLed[5], 255); } } else sandStep(dt, f); }
        else if (g === 1) runStep(dt); else if (g === 2) targetStep(dt); else if (g === 3) qdStep(dt); else if (g === 4) orbitStep(dt, f);
        else if (g === 5) rngStep(dt); else if (g === 6) pacerStep(dt); else if (g === 7) simonStep(dt); else pongStep(dt);
      }
      if (MODE_IND[S.mode] >= 0 && !(S.mode === MODE.BAT)) ind(MODE_IND[S.mode], 255);
      if (S.locked && !holdingBoth) ind(5, 255);
      if (holdingBoth && blink4) ind(5, 255);
      if (S.lockFlash > 0) { S.lockFlash -= dt; if (blink4) for (let i = 0; i < 6; i++) ind(i, 255); }
      if (lowBat && S.mode === MODE.TIME && blink4) ind(2, 255);
    }

    /* ---------- the scan plan: what the matrix driver would actually do ---------- */
    function scanPlan(vdd, dutySetting) {
      const I = ledMa(vdd), m = Math.max(1, Math.floor(ROW_SINK_MA / I));
      const slots = [];
      for (let r = 0; r < ROWS; r++) {
        const cols = [];
        for (let c = 0; c < COLS; c++) if (fb[r * COLS + c]) cols.push(c);
        for (let i = 0; i < cols.length; i += m) slots.push({ row: r, cols: cols.slice(i, i + m) });
      }
      const N = Math.max(1, slots.length);
      const needed = dutySetting * I_REF_MA / I;                        // on-time fraction that keeps brightness constant vs VDD
      const achievable = Math.min(needed, 1 / N);
      let avgMa = 0;
      for (let i = 0; i < fb.length; i++) avgMa += fb[i] / 255 * achievable * I;
      return { slots, N, I, m, needed, achievable, limited: achievable < needed - 1e-9, avgMa, relBright: needed ? achievable / needed : 1 };
    }

    /* ---------- the main step ---------- */
    let prev = { x: 0, y: 0, z: 1 }, shakeAcc = 0;
    function step(dtReal, dtSim, ioIn) {
      io = ioIn; evq.length = 0; S.shaken = false;
      S.rtcMs += dtSim;
      while (S.rtcMs >= 86400000) { S.rtcMs -= 86400000; nextDay(); }
      S.dead = io.soc < 0.03;
      // accelerometer events (the LIS2DW12 would raise INT on PE0 and wake the MCU). Each motion has its own CFG switch;
      // a locked watch can be told (CFG lock display) to stay dark, ignoring all motion.
      const okM = (k) => S.set[k] === 0 && !(S.locked && S.set.lockd === 1);
      const jerk = Math.hypot(io.accel.x - prev.x, io.accel.y - prev.y, io.accel.z - prev.z); prev = { x: io.accel.x, y: io.accel.y, z: io.accel.z };
      shakeAcc = shakeAcc * Math.exp(-dtReal / 250) + jerk;
      if (shakeAcc > SHAKE_JERK) { shakeAcc = 0; S.shaken = true; if (okM('shake')) motionWake('shake'); }   // S.shaken also drives the Random game
      if (io.wakeStrength > 0 && okM('raise')) {
        if (io.wakeStrength >= WAKE_SENS[S.set.wake]) motionWake('wrist raise');
        else log('wrist raise too weak for sensitivity (' + ['low', 'medium', 'high'][S.set.wake] + ')');
      }
      if (io.tap && okM('tap')) motionWake('double tap');
      if (io.ff) log('free-fall detected (no wake: raise, shake and tap already cover it)');
      buttons(dtReal);
      if (S.menu.on) { S.menu.t += dtReal; if (S.menu.t >= MENU_CONFIRM_MS) menuConfirm(); }
      const alwaysOn = S.locked && S.set.lockd === 2;                     // locked, display stays lit showing Time
      if (S.awake) {
        S.idle += dtReal;
        const lim = S.dead ? 1000 : S.indOnly ? 1200 : S.mode === MODE.TIME ? DUR[S.set.dur] : S.mode === MODE.FUN ? (S.fun.playing ? GAME_IDLE_MS : MODE_IDLE_MS) : tmrKeep() ? TMR_KEEP_MS : MODE_IDLE_MS;
        if (alwaysOn) S.idle = 0;
        else if (S.idle > lim) {
          if (S.mode !== MODE.TIME && !tmrKeep() && !S.indOnly) { toMode(MODE.TIME); S.idle = 0; log('idle: back to Time'); }
          else { S.awake = false; S.indOnly = false; S.menu.on = false; log('display off, MCU sleeps' + (tmrKeep() ? ' (stays in stopwatch mode)' : '')); }
        }
      }
      if (alwaysOn && !S.awake) { S.awake = true; S.indOnly = false; S.idle = 0; }
      if (S.tmr.run) S.tmr.el += dtReal;                                      // the stopwatch keeps counting whatever the display is doing
      render(dtReal);
      let duty = BRI[S.set.bri];
      if (S.set.auto) duty = Math.min(0.8, duty * (0.35 + 1.65 * io.ambient));
      if (!io.batOk) duty *= 0.5;
      if (S.locked && S.set.lockd === 2) duty *= 0.25;                 // always-on lock display: low brightness
      const scan = S.awake ? scanPlan(io.vdd, duty) : { slots: [], N: 0, I: ledMa(io.vdd), m: 0, needed: 0, achievable: 0, limited: false, avgMa: 0, relBright: 1 };
      return { fb, scan, duty, state: S, mode: S.mode, modeName: MODE_NAME[S.mode], awake: S.awake, locked: S.locked, events: evq.slice(), time: hms(), date: Object.assign({ wd: weekdayIso(S.date.y, S.date.m, S.date.d) }, S.date), menu: S.menu.on,
               sub: S.menu.on ? 'MODE SELECTION: ' + MODE_NAME[S.menu.sel] : S.mode === MODE.FUN ? (S.fun.playing ? GAMES[S.fun.g] : 'pick a game: ' + GAMES[S.fun.g]) : S.mode === MODE.SET ? 'editing ' + SET_FIELDS[S.setField] : S.mode === MODE.CFG ? CFG_NAMES[S.cfgSel] + ' = ' + cfgValueText(S.cfgSel) : S.mode === MODE.BAT ? ['charge', 'solar', 'state'][S.bat.view] : '' };
    }

    /* what each button does RIGHT NOW (shown in the simulator, mirrored in MANUAL.md) */
    function controls() {
      const c = { ls: '', ll: 'MODE SELECTION', rs: '', rl: '', note: '', menu: S.menu.on ? S.menu.sel : -1 };
      c.both = S.locked ? 'hold 2 s: UNLOCK' : 'hold 2 s: LOCK (LCK LED blinks while you hold)';
      if (S.locked) { c.ls = c.ll = c.rs = c.rl = 'ignored (locked; LCK lights if you press)'; c.note = 'Hold BOTH buttons 2 s to unlock. Lock display: ' + cfgValueText(9) + '.'; return c; }
      if (S.menu.on) {
        const n = NEXT_MODE.length;
        c.ls = 'move left (' + MODE_NAME[(S.menu.sel + n - 1) % n] + ')'; c.ll = 'go to TIME';
        c.rs = 'move right (' + MODE_NAME[(S.menu.sel + 1) % n] + ')'; c.rl = 'ENTER ' + MODE_NAME[S.menu.sel] + ' now';
        c.note = 'MODE SELECTION: the one blinking indicator is the highlighted mode (Time = the 12 o\'clock hour LED). Moves left/right like the indicator row and wraps. It enters by itself after 2.5 s with no press.';
        return c;
      }
      switch (S.mode) {
        case MODE.TIME: c.ls = '-'; c.rs = 'show the DATE (2 s)'; c.rl = 'show the BATTERY (2 s)'; c.note = 'No indicator lit in Time. Date: month = hour ring, day = minute ring, weekday = bar on the outer ring (Mon 1 LED ... Sun 7). Battery: hour-ring bar, BAT lit.'; break;
        case MODE.SET: c.ls = 'next unit (' + SET_FIELDS[(S.setField + 1) % 6] + ')'; c.rs = '+1 on ' + SET_FIELDS[S.setField]; c.rl = 'HOLD: auto-repeat +1'; c.note = 'Units: hour, minute, second, month, day, year. The chosen unit blinks. Changes apply immediately.'; break;
        case MODE.TMR: c.ls = S.tmr.run ? '-' : (S.tmr.el > 0 ? 'RESET to zero' : '-'); c.rs = S.tmr.run ? 'stop' : 'start'; c.rl = 'reset to zero';
          c.note = 'Seconds LED = elapsed s, minute LED = elapsed min, hour ring = tenths (1-5, 7-11). Display stays on 90 s, then sleeps still in this mode.'; break;
        case MODE.BAT: c.ls = 'previous view'; c.rs = 'next view (charge / solar / charging)'; c.rl = '-'; c.note = 'Charge: hour-ring bar. Solar: minute-ring bar. Charging: spinner.'; break;
        case MODE.FUN:
          if (!S.fun.playing) { c.ls = 'next game (' + GAMES[(S.fun.g + 1) % GAMES.length] + ')'; c.rs = 'START ' + GAMES[S.fun.g]; c.rl = '-'; c.note = 'Game picker: hour LED n = game n (' + GAMES.map((g, i) => (i + 1) + ' ' + g).join(', ') + '). Left long = mode selection.'; }
          else {
            const g = S.fun.g, sm = G.sand ? G.sand.mode : 0, nm = PARTICLE_MODES.length, rg = G.rng ? G.rng.mode : 0, pc = G.pc || { kind: 0 };
            const pgReady = G.pg && G.pg.st === 'ready';
            const L = ['next mode (' + PARTICLE_MODES[(sm + 1) % nm].name + ')', 'lane IN', 'HIT (either button)', 'PLAYER 1 button', 'previous pattern',
                       'next mode (' + RNG_MODES[(rg + 1) % RNG_MODES.length] + ')', pc.kind ? 'slower (-1 breath/min)' : 'slower (-5 bpm)', 'LEFT symbol',
                       pgReady ? 'switch 2 players / solo' : 'left paddle (hit in the zone)'][g];
            const R = [sm === 4 ? 'bead: next ring' : 'add a particle', 'lane OUT', 'HIT (either button)', 'PLAYER 2 button', 'next pattern',
                       'ROLL (or shake the watch)', pc.kind ? 'faster (+1 breath/min)' : 'faster (+5 bpm)', 'RIGHT symbol', pgReady ? 'START' : 'right paddle (hit in the zone)'][g];
            c.ls = L; c.rs = R;
            c.rl = g === 0 ? (sm === 4 ? 'HOLD: stop the bead' : 'HOLD: remove particles') : g === 6 ? 'switch metronome / breath pacer' : '-';
            c.note = GAMES[g] + (g === 0 ? ' (mode ' + (sm + 1) + ': ' + PARTICLE_MODES[sm].name + (sm < 4 ? ', ' + G.sand.p.length + ' particles' : '') + '). Tilt to move things.' : g === 4 ? ' (' + ORBIT_PATTERNS[G.orb.pat] + ').' : g === 5 ? ' (' + RNG_MODES[rg] + ').' : g === 6 ? ' (' + (pc.kind ? 'breath pacer' : 'metronome') + ').' : '.') + ' Left long = mode selection (FUN is highlighted: wait to come back to the game picker).';
          }
          break;
        case MODE.CFG: c.ls = 'next setting (' + CFG_NAMES[(S.cfgSel + 1) % CFG_COUNT.length] + ')'; c.rs = 'change value'; c.rl = '-'; c.note = 'Hour LED ' + (S.cfgSel + 1) + ' = ' + CFG_NAMES[S.cfgSel] + '; minute-ring bar = value (' + cfgValueText(S.cfgSel) + ').'; break;
      }
      return c;
    }

    return { controls, step, setHms, setDate, getHms: hms, S, ledMa, indLed, hourLed, minLed, secLed, ringLeds, GAMES, IND_NAME, MODE_NAME, ROWS, COLS, I_REF_MA,
             dim: () => ({ rIn: R_IN, rOut: R_OUT }), sandParticles: () => (G.sand ? G.sand.p : []), game: () => G };
  }
  global.createWatch = createWatch;
})(window);
