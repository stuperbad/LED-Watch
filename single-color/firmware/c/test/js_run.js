// js_run.js - run the JavaScript simulator core on the same scenario file as host_run.c and print the same lines.
// usage: node js_run.js scenario.scn
global.window = global;
const fs = require('fs'), path = require('path');
const simDir = path.join(__dirname, '..', '..', 'sim');
require(path.join(simDir, 'face_data.js')); require(path.join(simDir, 'watch_core.js'));
let rs = 1;
Math.random = () => { rs ^= rs << 13; rs >>>= 0; rs ^= rs >>> 17; rs ^= rs << 5; rs >>>= 0; return rs / 4294967296; };   // same xorshift32 as the C core
let W = null; const KEYS = ['bri', 'wake', 'dur', 'auto', 'sec', 'raise', 'shake', 'tap', 'btnw', 'lockd'];
const out = [];
for (const line of fs.readFileSync(process.argv[2], 'utf8').split('\n')) {
  const t = line.trim().split(/\s+/); if (!t[0] || t[0][0] === '#') continue;
  const n = t.slice(1).map(Number);
  if (t[0] === 'SEED') { rs = n[0] >>> 0; W = createWatch(FACE); }
  else if (t[0] === 'TIME') W.setHms(n[0], n[1], n[2]);
  else if (t[0] === 'DATE') W.setDate(n[0], n[1], n[2]);
  else if (t[0] === 'CFG') W.S.set[KEYS[n[0]]] = n[1];
  else if (t[0] === 'R') {
    const [cnt, dt, btn, ax, ay, az, wake, tap, ff, vdd, soc, bat, solar, chg, amb] = n;
    const io = { btn: [!!(btn & 1), !!(btn & 2)], accel: { x: ax / 1000, y: ay / 1000, z: az / 1000 }, wakeStrength: wake / 100, tap: !!tap, ff: !!ff,
                 vdd: vdd / 1000, soc: soc / 1000, batOk: !!bat, solarMw: solar, charging: !!chg, ambient: amb / 100 };
    for (let i = 0; i < cnt; i++) {
      const o = W.step(dt, dt, io), S = W.S;
      out.push([S.mode, S.awake ? 1 : 0, S.locked ? 1 : 0, S.menu.on ? 1 : 0, S.menu.sel, S.indOnly ? 1 : 0, o.scan.slots.length, Buffer.from(o.fb).toString('hex')].join(' '));
    }
  }
}
process.stdout.write(out.join('\n') + '\n');
