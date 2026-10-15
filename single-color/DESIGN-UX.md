# Watch UX: modes, two buttons, seven indicator LEDs, buzzer, games

Revised 2026-10-11 (button model v3: mode selection) to match the simulator (`firmware/sim/`, behaviour in `firmware/sim/watch_core.js`). The user-facing wording lives in `firmware/sim/MANUAL.md`; this file is the design rationale and the spec the firmware is built to.
Hardware assumed: 132 white ring LEDs (12 hour, 60 minute, 60 second), 7 indicator LEDs (SET TMR ALM BAT FUN CFG LCK, board Y42), a piezo buzzer (Murata PKMCS0909E4000-R1 on PB4/PB5) on matrix row 11, 2 buttons (left, right; symmetric, low on the face), LIS2DW12 accelerometer (wake-up, tap, orientation, free-fall, ~1 uA), battery voltage read by the MCU itself, solar input.

## 1. Ground rules
One idea: **inside a mode, both buttons belong to the mode. Left LONG is the way out, from everywhere: it opens MODE SELECTION.**

| Gesture | What it does |
|---|---|
| **Left long (1 s)**, in any mode | open MODE SELECTION (in selection: jump to Time) |
| **Left short / Right short**, in a mode | whatever that mode defines (table in section 2) |
| **Right long / hold** | secondary action (Time: show the battery; Set: auto-repeat; Stopwatch: reset; Particles: remove particles) |
| **Both held 2 s** | LOCK / UNLOCK (see "Locking"); the LCK LED blinks while held |
| **Wrist raise / shake / double tap** | wake the display into Time (each switchable in CFG). Free-fall is detected but does NOT wake. |
| **Any button on a dark watch** | wakes only (which buttons: CFG 9); that first press is not also an action |

### Mode selection
Opened by Left long. **One** indicator blinks: the highlighted mode (Time has no indicator: it is shown as the 12 o'clock hour LED blinking). The highlight starts on the mode you were in.
- **Left short / Right short**: move the highlight one mode LEFT / RIGHT along the physical indicator row, wrapping at the ends. Order left to right: TIME, SET, TMR, ALM, BAT, FUN, CFG.
- **Wait 2.5 s**: enters the highlighted mode by itself. This is the normal way to confirm, so "hold Left, tap Right twice, wait" is a complete gesture.
- **Right long**: enter the highlighted mode immediately.  **Left long**: jump to Time.
Why: with Left long as the single way out, no mode has to give up a button for navigation, so games, the stopwatch and the editors can use both buttons freely; the two buttons map onto left/right movement along the indicator row; and a stray short tap can never change mode.

### Idle / decay
| Situation | After | Then |
|---|---|---|
| Time, display on | 2/3/5/10 s (CFG 3) | display off (MCU sleeps ~4 uA) |
| SET, BAT, CFG, game picker | 15 s | back to Time |
| Mode selection | 2.5 s | enters the highlighted mode |
| A game being played | 5 min | back to Time |
| **Stopwatch (running, or showing a time)** | **90 s** | **display off but stays in stopwatch mode; any wake returns to it; it keeps counting** |

## 2. Modes
Mode selection moves along TIME, SET, TMR, ALM, BAT, FUN, CFG (left to right, wrapping). Left long opens it from any of them.
| Mode | Indicator | Left short | Right short | Right long | Ring display |
|---|---|---|---|---|---|
| **Time** | none | - | date for 2 s | battery for 2 s | hour LED + minute LED (+ second LED); date: month on hour ring, day on minute ring, weekday = one indicator LED (SET = Sun ... LCK = Sat); battery: hour-ring bar |
| **Set time and date** | SET | next unit | +1 on the blinking unit | HOLD: auto-repeat (faster after 2.5 s) | units: hour, minute, second, month, day, year (year = minute-ring LED at the last two digits); the unit being set blinks |
| **Stopwatch** | TMR | reset (when stopped) | start / stop | reset | second LED = seconds, minute LED = minutes, hour ring = tenths (LEDs 1-5, 7-11; 6 and 12 skipped) |
| **Alarm** | ALM | next field (hour, minute, on/off) | +1 on the field / switch on or off | HOLD: auto-repeat +1 | hour LED = alarm hour, minute LED = alarm minute, outer LED at 6 = PM, three outer LEDs at 12 = on; rings up to 1 min (beeps), any button stops it |
| **Battery / status** | BAT | previous view | next view: charge, solar, charging | - | charge = hour-ring bar; solar = minute-ring bar (log); charging = spinner |
| **Fun** | FUN | picker: next game; in a game: the game's left action | picker: START; in a game: the game's right action | in a game: the game's secondary action (Particles: remove) | see "Fun: the game picker" |
| **Settings** | CFG | next setting | change value | - | hour LED n = setting n; minute-ring bar length = value |

### Fun: the game picker
Entering FUN never drops you straight into a game; it shows the **game picker**, so both buttons are free to be game controls once you start.
- **Hour LED n = game n** (numbered round the clock from 1), blinking, with the FUN indicator lit. **Left short** = next game, **Right short** = start it.
- In a game, Left and Right (and Right long where the game uses it) do what that game says (below). **Left long goes all the way out to mode selection**, from any game; FUN is highlighted there, so one more wait (or Right long) drops you back into the game picker.
- Games auto-exit after 5 minutes of no presses; the picker times out to Time after 15 s.

| # | Game | Kind | Left short | Right short | Right long |
|---|---|---|---|---|---|
| 1 | Particles (5 modes: sand, gravel, oil, water, bead) | tilt toy | next mode | add a particle (bead mode: next ring) | remove particles (bead mode: stop the bead) |
| 2 | Ring Runner | arcade, 1 player, scored | lane in | lane out | - |
| 3 | Target | arcade timing, 1 player, scored | hit | hit | - |
| 4 | Quick Draw | 2 players, 1 watch | player 1 | player 2 | - |
| 5 | Orbit (6 patterns) | light show | previous pattern | next pattern | - |
| 6 | Random (5 modes) | tool | next mode | roll (or shake the watch) | - |
| 7 | Pacer | metronome / breath pacer | slower | faster | switch metronome / breath pacer |
| 8 | Simon | memory game, scored | left symbol | right symbol | - |
| 9 | Pong | 2 players or solo | (ready screen: switch 2 players / solo) left paddle | (ready screen: start) right paddle | - |

### Settings (CFG), shown by which hour LED is lit
| Hour LED | Setting | Choices (bar length shows which) | Default |
|---|---|---|---|
| 1 | Brightness (LED duty) | 5, 10, 20, 30, 50 % | 20 % |
| 2 | Raise sensitivity (wrist raise) | low, medium, high | medium |
| 3 | Wake duration in Time | 2, 3, 5, 10 s | 10 s |
| 4 | Auto brightness (LED light sensing) | off, on | off |
| 5 | Seconds LED | always, never | always |
| 6 | Wake by raise | on, off | on |
| 7 | Wake by shake | on, off | on |
| 8 | Wake by tap | on, off | on |
| 9 | Buttons that wake | either, left only, right only, none | either |
| 10 | Lock display | motion wakes it, stays dark, always on (low brightness, no seconds) | motion wakes it |
| 11 | Key beeps | off, on (a click on every press outside the games) | off |
| 12 | Game sounds | on, off (hits, misses, wins, Simon tones, metronome tick) | on |
Protocol: open CFG from mode selection; the hour ring tells you WHICH setting, the minute-ring bar tells you its VALUE; Right short = next value, Left short = next setting; changes apply immediately (no save step); Left long to leave.

### Date display (Right short in Time; battery is Right long)
Month on the hour ring (Jan = 1 o'clock ... Dec = 12), day on the minute ring (the 15th = the 15-minute LED), weekday as ONE indicator LED: SET = Sunday, TMR = Monday, ALM = Tuesday, BAT = Wednesday, FUN = Thursday, CFG = Friday, LCK = Saturday (the board prints the weekday letter under each mode name, week starts on Sunday). Weekday is computed from the date (leap years handled); the date rolls over at midnight.

### Locking (not a mode)
Hold BOTH buttons 2 s from anywhere to lock; again to unlock. The LCK LED blinks while you hold (even on a dark watch), then is steady while locked. Locking drops to Time.
While locked no button acts and no button wakes the display; a press only lights LCK (about 1 s if the display was dark) to explain why nothing happened. CFG 10 chooses whether motion wakes a locked watch (default), nothing does, or the display stays on **at low brightness (quarter duty) with no seconds LED**. Motion wake in the locked state still obeys CFG 6-8.

## 3. Indicator LEDs
Seven tiny LEDs in a row under the solar cell, each with a silkscreen label (mode name and weekday letter), left to right: **SET, TMR, ALM, BAT, FUN, CFG, LCK**. Time lights none. The indicator of the current mode (first five) is lit; in mode selection only the highlighted mode's indicator blinks; LCK shows the lock state and is not a mode.
- Wiring: all seven on a 12th matrix ROW (IND7 = ALM is on COL6, physically third from the left; firmware indexes them in face order) (anode to the column nets, cathode to ROW11): one extra pin, no extra resistors, same brightness control as the ring.
- BAT blinks fast for low battery (BAT_OK low); low battery also halves brightness; below 3 % only BAT blinks.
- LCK blinks while both buttons are held, and blinks briefly on lock/unlock.

## 4. How the two buttons stay simple
- One way out of anything: Left long. One way to act: the mode's own buttons.
- The ring itself is the display: setting numbers on the hour ring, values on the minute ring.
- Pocket safety: lock gesture, each wake source can be turned off (CFG 6-9), idle time-outs.
- Energy: games light more LEDs; the row-sink limit (10 mA per row pin) auto-dims crowded pictures; games auto-exit after 5 minutes.
- Arcade games (Ring Runner, Target, Quick Draw) react on button PRESS rather than release, for timing.

## 5. The programs in detail

### 5.1 Particles (sand / gravel / oil / water / bead)
One tilt toy with five modes. **Left short** cycles the mode and the hour LED for the mode (1 to 5) lights for 1.2 s. It starts in sand with 14 particles.
- **Modes 1-4 are a particle simulator.** Up to 60 particles live on the ring track (the band that holds the three LED rings) and obey gravity from the accelerometer: tilt the watch and they pour toward the low side; shake and they scatter. Each particle lights the nearest LED. **Right short** adds one particle at 12 o'clock; **Right hold** removes particles (4 at once, then 2 every 0.2 s while held).
- **Mode 5, bead:** one bright LED rolls round a ring like a bead on a circular wire, swinging like a pendulum and settling at the low point; a short tail shows its speed. **Right short** moves the bead to the next ring (hour, minute, second); **Right hold** stops it dead. (The particles are kept while you are in bead mode.)

| Mode | Hour LED | Feel | Parameters (simulator) |
|---|---|---|---|
| Sand | 1 | grains lock together and pile up; a pile sticks on a gentle slope (static friction, angle of repose about 17 degrees) and slides when you tilt past it | high damping, little bounce, grains share momentum, wall stiction |
| Gravel | 2 | bouncier and rolls further; barely sticks | medium damping, bounce 0.2, light stiction |
| Oil | 3 | thick liquid: slow, flows, finds its level, no sloshing | very high damping, particles push each other apart (pressure) |
| Water | 4 | thin liquid: fast, sloshes back and forth, keeps moving on a gentle tilt | low damping, bounce 0.35, pressure |
| Bead | 5 | a single bead on a ring; an easy accelerometer sanity check (it should always settle at the low side) | pendulum with light damping |

Display: particles or the bead only; the FUN indicator is lit. Power: more particles light more rows, and a crowded pile is dimmed automatically by the row-current limit (the simulator shows by how much).
Ideas: a fifth liquid ("honey"); remember the mode across sleeps.

### 5.2 Ring Runner
You are one lit LED racing clockwise round the face on one of three lanes (inner = hour ring, middle = minute ring, outer = second ring). Obstacles appear ahead as flashing LEDs.
Left = move one lane in, Right = move one lane out (stopping at the edge lanes). Crash into an obstacle and the run ends.
Scoring: **10 points per obstacle passed**, cap 999. The speed rises every 10 obstacles (about 0.12 rad/s each step) and obstacles spawn faster. Game over shows the score on the three rings (see "Scoring display"); either button restarts. Reaching 999 plays the award animation.
Ideas: tilt left/right to change lane instead of buttons; a second life; two simultaneous obstacle patterns at high speed.

### 5.3 Target (arcade timing)
A bright light races round the minute ring. The target is the 12 o'clock LED (dim), with a faint zone either side showing how forgiving the hit window is. Press either button when the bright light is on the target.
Hit: the hour ring flashes, the light gets 10 % faster (14 LEDs/s up to 90) and the zone shrinks (3 LEDs down to 0.6). Level progress shows on the hour ring (12 steps). **Points per hit = 10 + the level number** (cap 999).
Difficulty also comes from clutter: from level 4 a second, dimmer decoy light joins, and from level 8 a third (only the bright one counts).
Miss: game over and the score is shown on the three rings (see "Scoring display"). Either button plays again. Reaching 999 plays the award animation.
Ideas: a "reverse" level where the light changes direction; two targets at once; a best-score memory in flash.

### Scoring display (all scoring games)
Scores run 0 to 999 and are shown as three decimal digits on the three rings, like the places of a number:
**hundreds on the HOUR ring (inner), tens on the MINUTE ring, ones on the OUTER (second) ring.** Each digit is a bar of that many LEDs counted clockwise from 12 o'clock (a dim marker at 12 on each ring shows a zero). Example: 237 lights 2 hour LEDs, 3 minute LEDs and 7 outer LEDs, 12 LEDs in all. The digits blink for 8 s, then stay steady until a button restarts the game or the game times out.
Every scoring game is scaled so that 999 is a real achievement and is the cap. Reaching 999 plays a 10 s **award animation** (spinning comets on all three rings in opposite directions and speeding up, random sparkles and flashing indicator LEDs), then shows 999 steady (9, 9, 9).
Scoring per game: Ring Runner = 10 points per obstacle passed (about 100 obstacles for 999); Target = 10 points plus the level number per hit (level 1 = 10, level 11 = 20, ...). Simon = 5 points per correct press; Pong (solo) = 10 points per return. Particles, Orbit, Random, Pacer and two-player Pong/Quick Draw have no 0-999 score (Random's 1-999 mode and the Pacer's tempo reuse the same digit display).
Alternatives considered: base-60 (seconds, minutes, hours as places: finer resolution but unreadable without a table), or one long bar (maximum 60 LEDs, so it caps too low).

### 5.4 Quick Draw (two players)
Both players hold their own button (Left = player 1, Right = player 2) for 0.5 s then release: armed. After a random 2-6 s the minute and second rings flash. First to press wins and their side of the watch lights (left half or right half). Pressing early is a false start: the other player wins and their side flashes.
Ideas: best of three with the match score on the hour ring; a one-player reaction-time mode that shows your time on the rings.

### 5.5 Orbit (light show, 6 patterns)
A light show for when you are bored. **Right = next pattern, Left = previous** (they wrap). Tilting the watch changes the speed.
1. **Radar**: a sweep with a fading trail on all three rings.
2. **Lissajous**: three dots on the three rings moving at 1:2:3 speeds.
3. **Comet**: a trail spiralling across the rings.
4. **Ripple**: brightness waves that travel from the inner ring to the outer ring (uses the dimming levels, so it breathes).
5. **Pendulums**: six dots, two per ring, swinging along the bottom of the face at slightly different rates; they drift in and out of step like a pendulum-wave toy.
6. **Twinkle**: random LEDs flash up and fade out slowly, like a starfield.

### 5.6 Random (5 modes)
**Left short** cycles the mode (hour LED 1-5 shows which for 1.2 s), **Right short** rolls, and **shaking the watch also rolls** (it uses the shake detector, which works even if wake-by-shake is off). A roll tumbles random LEDs for about 0.9 s, then the answer stays on until the next roll. Before the first roll the 12 o'clock hour LED blinks.
1. **Coin**: heads lights the whole right half of the outer ring (plus hour LED 3), tails the left half (plus hour LED 9).
2. **Die**: 1-6 shown as that many LEDs on the outer ring, counted from 12.
3. **Two dice**: first die as a bar on the minute ring, second die on the outer ring, and the total (2-12) as a bar on the hour ring.
4. **Number 1-999**: the three-digit score display (hundreds on the hour ring, tens on the minute ring, ones on the outer ring); blinks for 1.5 s, then steady.
5. **Random clock**: one random hour LED, one random minute LED and one random second LED, one from each ring, like three random clock hands.

### 5.7 Pacer (metronome and breath pacer)
A tempo you can dial up and down. **Left = slower, Right = faster, Right hold = switch between metronome and breath pacer.** Every time you change the tempo (or switch), the tempo is shown for 2.5 s as a base-10 number in the same hundreds / tens / ones digit display used for scores, then the animation resumes.
- **Metronome** (40-220 bpm in steps of 5, starts at 100): a bright dot swings back and forth along the bottom of the outer ring like a pendulum, reaching an end exactly on each beat, with a short trail. On every beat the 6 o'clock hour LED flashes; on the first beat of each 4 the 12 o'clock LED flashes too. A beat counter (12, 3, 6, 9 o'clock) dimly marks beats 1-4.
- **Breath pacer** (3-12 breaths per minute in steps of 1, starts at 6): the minute ring fills clockwise as you breathe in (40 % of the cycle) and empties as you breathe out (60 %), with the hour ring following dimly. At 6 breaths per minute a breath takes 10 s: 4 s in, 6 s out.
Ideas: a tap-tempo (tap Right in rhythm); box breathing (4-4-4-4); a silent vibration-style mode is not possible (no motor).

### 5.8 Simon (memory)
The watch shows a growing sequence of **left half** and **right half** flashes (the left or right half of the outer ring, plus hour LED 9 or 3); you repeat it with **Left** and **Right**. The two buttons are the two symbols, so unlike classic four-colour Simon this is a binary memory game; the sequence gets longer by one each round and the playback gets faster (600 ms per flash down to 200 ms).
- The hour ring shows the current sequence length (dimly, up to 12). While it is your turn a steady LED at 12 on the minute ring shows "go". Presses while the watch is still showing the sequence are ignored; taking more than 4 s to press, or pressing the wrong button, ends the game.
- **Points: 5 per correct press** (so completing round n scores the running total 5 x n(n+1)/2; round 20 reaches 1050 and the 999 cap), shown on the three-ring score display; 999 plays the award animation. Either button restarts.
Ideas: a four-symbol version using short and long presses; a two-player "copy my sequence" mode.

### 5.9 Pong (two players or solo)
The ball travels back and forth along the bottom half of the minute ring between two **paddle zones**, the dim LEDs at each end (around 9 and 3 o'clock). Press your button while the ball is **inside your zone and moving toward you** to hit it back; each return makes it a little faster, and hitting it at the very end of the zone is a **smash** (extra speed). A press outside the zone costs nothing.
- **Ready screen:** the hour LED blinks: LED 1 = two players, LED 2 = solo. **Left short** switches, **Right short** starts.
- **Two players:** Left button = left player, Right button = right player. First to **5** wins. Points show on the hour ring: the left player's score counts up the left side (11, 10, 9 ...), the right player's up the right side (1, 2, 3 ...). After a point the ball is served toward the player who lost it, at the starting speed; the winner's half of the outer ring blinks for 3 s and the game returns to the ready screen.
- **Solo:** the left end is a wall, so the ball always bounces back; either button defends the right end. **10 points per return**, game over on the first miss, scored on the three-ring display (cap 999, award animation at 999); either button restarts.
Ideas: a computer opponent for solo-versus; zones that shrink as the rally goes on; curved returns that change the ball's lane.

### 5.10 Ideas for later games (nothing built yet)
- **Whack-a-mole**: lights pop up around the ring, Left hits the left half, Right the right half.
- **Snake**: a growing tail circling the rings; Left and Right steer in or out.
- **Magic 8-ball**: shake the watch for one of a few answers (an extra mode for Random).
- **Spirit level**: a bubble that floats to the high side, with a steady LED when the watch is level; the accelerometer is already there.
- **Countdown timer** (not a game): set minutes on the minute ring, count down with a chase, flash at zero. Would fit best next to the stopwatch.
- **Lights Out, Higher/Lower, Tag**: small puzzle ideas that map to a 12-sector ring.

## 6. What this asks of the hardware / schematic
- Buttons: symmetric and low on the face; keep the KMR2 parts for now.
- Indicators: seven 0402 LEDs on matrix row 11 (in the netlist as IND1..IND7; PD5 drives the row; IND7 = ALM sits between TMR and BAT).
- Wake gestures use the accelerometer's wake-up and double-tap detection (INT on PE0); shake maps to the wake-up threshold, free-fall is read but not used to wake.
- Battery readout needs no pin (ADC VDD/10 channel on the AVR128DB48).
- Light meter / auto-brightness: reverse-bias a ring LED and time its discharge (to be prototyped).

## 7. Open questions
1. Weekday display: DECIDED 2026-10-13: one indicator LED lights (SET = Sunday ... LCK = Saturday).
2. Mode selection auto-enters after 2.5 s (now the main way to confirm): right length? (Too short and you cannot read the highlight; too long and it feels slow.)
3. Which of the game ideas in 5.8 do you want next?
4. Indicator colours: all one colour, or several? (More part types.)

## 8. Sound (piezo) - added 2026-10-14
Hardware: Murata PKMCS0909E4000-R1 between PB4 and PB5, driven in antiphase by TCA1 (split mode); about 4 kHz is loudest. The core (`watch.c` / `watch_core.js`) only reports the frequency to play (`watch_tone_hz()` / `out.tone`); `hw/buzzer.c` drives the pins, the simulator plays it with WebAudio.
- **Alarm** (ALM mode): rings when the clock reaches the set minute, up to 1 minute, 4 kHz beep-beep-beep-beep-pause. Wakes the display (also when locked), any button stops it and does nothing else, no snooze yet. Always sounds, even with a low battery.
- **Key beeps** (CFG 11, off by default): 3.5 kHz click on every press, except inside games.
- **Game sounds** (CFG 12, on by default): Ring Runner tick per obstacle / crash tune; Target hit pair / miss tune; Quick Draw GO beep, winner fanfare, false-start double beep; Simon low tone = Left, high tone = Right (shown and pressed), wrong tune; Pong tick on a return, pair on a point, fanfare for the winner, tune when a solo game ends; Pacer tick per beat with an accent on the first of four; a longer fanfare at 999 points.
- A low battery (BAT_OK low) mutes everything except the alarm. Power: the piezo is a capacitor, so a beep costs very little; the loop stays awake while a sound plays.
- Not built yet: snooze, a choice of alarm tunes, hourly chime, per-game volume.
