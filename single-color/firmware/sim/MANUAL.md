LED WATCH - USER MANUAL (simulator build, draft 2026-10-11, button model v3: mode selection)
==========================================================================================
Design rationale lives in DESIGN-UX.md; this file is the user-facing wording.
The simulator's "Controls right now" panel shows the same rules live for whatever mode you are in.

THE TWO BUTTONS IN ONE PARAGRAPH
--------------------------------
Inside a mode, BOTH buttons belong to that mode (what they do is listed per mode below).
To change mode, hold LEFT for 1 second: that opens MODE SELECTION from anywhere (then tap Left/Right to move, or just wait).
To lock or unlock, hold BOTH buttons for 2 seconds.

MODE SELECTION (Left long, from anywhere)
-----------------------------------------
   ONE indicator blinks: the highlighted mode (it starts on the mode you were in).
   Time has no indicator: it shows as the 12 o'clock hour LED blinking.
   The buttons move the highlight like the row of indicators under the solar cell (SET TMR ALM BAT FUN CFG LCK):
   LEFT short  : move LEFT one mode        RIGHT short : move RIGHT one mode      (both wrap round)
                 order left to right:  TIME  SET  TMR  ALM  BAT  FUN  CFG
   LEFT long   : jump to TIME
   RIGHT long  : enter the highlighted mode right now
   (do nothing) : after 2.5 s it enters the highlighted mode by itself - this is the normal way
So "hold Left, tap Right, tap Right, wait" is a complete gesture. A stray short tap can never change mode.
Indicators, left to right under the solar cell:   SET   TMR   ALM   BAT   FUN   CFG   LCK
TIME lights none. LCK is not a mode: it shows the lock state (see LOCKING).

DECAY (everything drifts back to Time on its own)
-------------------------------------------------
   Time          : display off after 2, 3, 5 or 10 s (CFG 3)
   Set, Battery, Config, game picker : back to Time after 15 s without a press
   A game being played : back to Time after 5 minutes
   STOPWATCH     : stays lit 90 s, then the display sleeps STILL IN the stopwatch mode; a shake, raise, tap or
                   button press wakes it straight back to the stopwatch (which kept counting the whole time)

WAKING THE DISPLAY
------------------
The display is dark and the MCU sleeps (about 4 uA) until something wakes it. What wakes it is set in CFG:
   raise your wrist       -> wakes into TIME (needs enough movement, CFG 2 "raise sensitivity")   CFG 6: on/off
   shake the watch        -> wakes into TIME                                                     CFG 7: on/off
   double-tap the glass   -> wakes into TIME                                                     CFG 8: on/off
   press a button         -> wakes it; that first press ONLY wakes (it is not also an action)    CFG 9: either / left only / right only / none
   (free-fall is detected by the accelerometer but deliberately does NOT wake the display)
Raise, shake and tap are all ON by default; either button wakes by default.

LOCKING
-------
To lock: hold BOTH buttons for 2 s, from any mode.
   While you hold, the LCK LED blinks (even on a dark watch); at 2 s it locks (a short blink, then steady LCK) and drops to TIME.
   To unlock: hold BOTH buttons 2 s again (LCK blinks while you hold, then goes out).
While locked:
   - No button does anything and no button wakes the display. Pressing a button only lights the LCK LED
     (for about 1 s on a dark watch) so you know why nothing happened.
   - Whether the display wakes is set in CFG 10 "lock display":
       motion wakes it (default): raise / shake / tap (if enabled in CFG 6-8) show TIME with LCK lit
       stays dark               : nothing wakes it; only a button press shows LCK
       always on                : TIME stays lit at LOW brightness (quarter duty) with NO seconds LED, and LCK lit
                                  (costs battery; the simulator shows how much)
   - The lock survives sleep; only the both-buttons hold unlocks it.

READING THE DATE (RIGHT short in TIME)
-------------------------------------
Tap RIGHT in TIME: the date shows for 2 s, then the time returns.
   hour ring   = MONTH   (January = 1 o'clock ... November = 11, December = 12 o'clock)
   minute ring = DAY     (the LED at that minute mark: the 15th = the 15-minute LED)
   indicator row = WEEKDAY: ONE of the seven indicator LEDs lights. They are printed with the weekday letter under the mode name:
                   SET-S = Sunday, TMR-M = Monday, ALM-T = Tuesday, BAT-W = Wednesday, FUN-T = Thursday, CFG-F = Friday, LCK-S = Saturday
Example: Sunday 11 October = hour LED 10, minute LED 11, the SET indicator lit.
(Weekdays are worked out from the date, leap years included; the date rolls over at midnight.)

THE MODES
---------
TIME  (no indicator)
   hour LED + minute LED (+ seconds LED, CFG 5)
   LEFT : -
   RIGHT short : the DATE for 2 s (see READING THE DATE)
   RIGHT long  : the BATTERY level for 2 s (hour ring fills like a bar, BAT lit)
   A dim ALM indicator means an alarm is set.

SET   (set the time and date)   - no "edit" step: you are editing as soon as you are in
   The unit being changed BLINKS. Units, in order: hour, minute, second, month, day, year.
   LEFT short  : next unit
   RIGHT short : +1        RIGHT hold : auto-repeat +1 (speeds up after 2.5 s)
   Month and day show the date view with the chosen unit blinking.
   Year: one minute-ring LED at the last two digits (2026 = the 26-minute LED) blinks; range 2024-2099.
   Changes apply immediately; there is no save step. The day clamps to the month length.
   Leave with LEFT long (mode selection).

ALM   (alarm clock)   - like SET there is no edit step; the field being changed BLINKS. Fields: hour, minute, on/off.
   hour LED = alarm hour (12-hour clock), minute LED = alarm minute, one outer LED at 6 o'clock = PM, three outer LEDs at 12 = alarm ON.
   An alarm that is off shows dim.
   LEFT short  : next field          RIGHT short : +1 hour / +1 minute / switch the alarm on or off
   RIGHT hold  : auto-repeat +1 (hour and minute)
   When the minute comes the alarm RINGS for up to a minute: beep beep beep beep, pause (4 kHz); the display wakes (even a locked or dark
   watch), the 12 hour LEDs flash with the time and the ALM LED blinks. ANY button stops it (and does nothing else). No snooze yet.
   With a low battery (BAT_OK low) the alarm still rings; every other sound is muted.
   Setting the alarm to the current minute waits for tomorrow.

TMR   (stopwatch)
   seconds LED = elapsed seconds, minute LED = elapsed minutes,
   hour ring = tenths of a second: one LED at a time, 10 positions (hour LEDs 1-5 and 7-11; 6 and 12 skipped)
   RIGHT short : start / stop      RIGHT long : reset
   LEFT short  : reset (when stopped with a time on it)
   Stays lit 90 s, then sleeps still in stopwatch mode (see DECAY).

BAT   (battery and solar)
   RIGHT short = next view, LEFT short = previous view. Three views:
     1 charge   : hour ring bar, 12 steps
     2 solar    : minute ring bar (log scale, full = about 30 mW)
     3 charging : spinner on the hour ring while charging, BAT breathes
   Low battery (BAT_OK low): BAT blinks in TIME mode and brightness is halved.
   Below 3 %: only BAT blinks for 1 s when woken.

FUN   (games)  - see the next section
CFG   (settings) - see the section after

FUN: THE GAME PICKER
--------------------
Entering FUN does NOT start a game; it shows the GAME PICKER, so both buttons are free for the game once it starts.
   Picker: the FUN indicator is lit and the hour LED for the current game BLINKS
           (numbered round the clock: hour LED 1 = game 1 ... hour LED 9 = game 9).
     LEFT short  : next game      RIGHT short : START the game
   In a game: LEFT and RIGHT do what the game says (table below).
     LEFT long   : all the way out to MODE SELECTION (from any game). FUN is highlighted there, so just wait
                   (or hold RIGHT) and you are back at the game picker.
   A game that is left alone for 5 minutes returns to Time.

   hour LED  game                    kind                       LEFT short        RIGHT short            RIGHT long
   1         Particles (5 modes)     tilt toy                   next mode         add a particle /       remove particles /
                                                                                  bead: next ring        bead: stop it
   2         Ring Runner             arcade, scored             lane IN           lane OUT               -
   3         Target                  arcade timing, scored      HIT               HIT                    -
   4         Quick Draw              2 players, 1 watch         player 1          player 2               -
   5         Orbit (6 patterns)      light show                 previous pattern  next pattern           -
   6         Random (5 modes)        coin / dice / numbers      next mode         ROLL (or shake)        -
   7         Pacer                   metronome / breath pacer   slower            faster                 switch metronome/breath
   8         Simon                   memory game, scored        LEFT symbol       RIGHT symbol           -
   9         Pong                    2 players or solo          left paddle       right paddle           -
                                                                (ready screen: switch 2P / solo)  (ready screen: start)

SCORES (Ring Runner, Target, Simon, Pong solo)
-------------------------------
Scores run 0-999 and show as three digits on the rings, like places in a number:
   HOUR ring (inner) = hundreds     MINUTE ring = tens     OUTER ring = ones
Each digit is a BAR of that many LEDs counted clockwise from 12 o'clock (a dim LED at 12 marks a zero).
Example: 237 = 2 hour LEDs + 3 minute LEDs + 7 outer LEDs (12 lit in all).
The digits blink for 8 s, then stay steady until you restart.
999 is the cap. Reach it and the watch plays a 10 s AWARD ANIMATION (comets spinning round all three rings in
opposite directions and speeding up, sparkles, flashing indicators), then shows 999 (9, 9, 9).

THE GAMES
---------
1 PARTICLES (tilt) - five modes: 1 sand, 2 gravel, 3 oil, 4 water, 5 bead
   LEFT short cycles the mode; the hour LED 1-5 shows which for a moment. It starts in sand with 14 particles.
   Modes 1-4 are a particle simulator: up to 60 particles live on the ring track and fall toward whichever side
   is low. Tilt the watch and they pour; shake it and they scatter.
     RIGHT short adds a particle at 12 o'clock. HOLD RIGHT removes particles (and keeps removing while held).
     1 SAND    grains lock together, pile up, and stick on a gentle slope until you tilt further
     2 GRAVEL  bouncier, rolls further, barely sticks
     3 OIL     thick liquid: slow, flows and finds its level, no sloshing
     4 WATER   thin liquid: fast, sloshes back and forth, keeps moving on a gentle tilt
   Mode 5 BEAD: one bright LED rolls round a ring like a bead on a circular wire. Tilt and it accelerates, swings
   like a pendulum and slowly settles at the low point; a short tail shows its speed.
     RIGHT short moves the bead to the next ring (hour, minute, second). HOLD RIGHT stops it dead.
     (Your particles are kept while you play with the bead.)

2 RING RUNNER (arcade, scored)
   You are one lit LED racing clockwise round three lanes: inner = hour ring, middle = minute ring, outer = second ring.
   Flashing LEDs are obstacles. LEFT moves you one lane in, RIGHT one lane out. Touch an obstacle and the run ends.
   10 points per obstacle passed; every 10 obstacles it gets faster and busier.
   Game over: your score shows on the rings (see SCORES). Either button restarts.

3 TARGET (arcade timing, scored)
   A bright light races round the minute ring. The target is the 12 o'clock LED (dim), with a faint zone either
   side that shows how forgiving the hit window is. Press EITHER button when the bright light is on the target.
   Hit : the hour ring flashes, the light gets 10 % faster and the zone shrinks. Level shows on the hour ring.
         Points per hit = 10 + the level number.
   Harder: from level 4 a dim DECOY light joins, from level 8 a second decoy (only the bright one counts).
   Miss: game over, score on the rings (see SCORES). Either button plays again.

4 QUICK DRAW (two players, one watch)
   Each player holds their own button (LEFT = player 1, RIGHT = player 2) for 0.5 s, then both let go: armed.
   After a random 2-6 s the minute and second rings flash. First to press wins and their side lights.
   Pressing early is a false start: the other player wins and their side flashes.

5 ORBIT (light show, 6 patterns)
   RIGHT = next pattern, LEFT = previous (they wrap). Tilting the watch changes the speed.
     1 RADAR      a sweep with a trail on all three rings
     2 LISSAJOUS  three dots at 1:2:3 speeds
     3 COMET      a trail spiralling across the rings
     4 RIPPLE     brightness waves travelling from the inner ring to the outer ring
     5 PENDULUMS  six dots swinging at slightly different rates, drifting in and out of step
     6 TWINKLE    random LEDs flash and fade slowly, like stars

6 RANDOM (5 modes)
   LEFT cycles the mode (hour LED 1-5 shows which), RIGHT rolls, and SHAKING THE WATCH also rolls. A roll tumbles
   random LEDs for about a second, then the answer stays lit. Before the first roll the 12 o'clock hour LED blinks.
     1 COIN         heads = the whole right half of the outer ring (and hour LED 3), tails = the left half (and hour LED 9)
     2 DIE          1-6 as that many LEDs on the outer ring, counted from 12
     3 TWO DICE     first die on the minute ring, second die on the outer ring, the total (2-12) on the hour ring
     4 NUMBER 1-999 shown as hundreds / tens / ones on the hour / minute / outer rings (see SCORES)
     5 CLOCK        one random hour LED, one random minute LED, one random second LED (three random "hands")

7 PACER (metronome and breath pacer)
   LEFT = slower, RIGHT = faster, HOLD RIGHT = switch between metronome and breath pacer.
   Each time you change the tempo (or switch), the tempo shows for 2.5 s as a number in the hundreds / tens / ones
   display (like a score), then the animation resumes.
   METRONOME (40-220 bpm, steps of 5, starts at 100): a bright dot swings along the bottom of the outer ring like a
   pendulum, reaching an end exactly on each beat. The 6 o'clock hour LED flashes on every beat, plus 12 o'clock on
   beat 1 of 4; a dim marker at 12, 3, 6, 9 o'clock counts the beats.
   BREATH PACER (3-12 breaths per minute, starts at 6): the minute ring fills as you breathe in (40 % of the cycle)
   and empties as you breathe out (60 %). At 6 breaths a minute that is 4 s in, 6 s out.

8 SIMON (memory, scored)
   The watch plays a growing sequence of LEFT-half and RIGHT-half flashes; you repeat it with LEFT and RIGHT.
   Each round adds one flash and the playback gets faster. The hour ring shows the sequence length (dim). When it is
   your turn a steady LED at 12 on the minute ring is lit. Wrong button, or more than 4 s without pressing, ends it.
   5 points per correct press (999 = round 20). Score on the three rings; either button restarts.

9 PONG (two players or solo)
   The ball travels back and forth along the bottom half of the minute ring between two paddle zones: the dim LEDs at
   each end (about 9 and 3 o'clock). Press your button while the ball is inside your zone and moving toward you to hit
   it back. Every return is faster; hitting it at the very end of the zone is a smash (extra speed). A press outside
   the zone costs nothing.
   Ready screen: the hour LED blinks (1 = two players, 2 = solo). LEFT switches, RIGHT starts.
   TWO PLAYERS: LEFT = left player, RIGHT = right player. First to 5 wins. Points show on the hour ring (left player
   counts up the left side, right player up the right side). The ball is served toward whoever lost the point.
   SOLO: the left end is a wall; either button defends the right end. 10 points per return, game over on a miss,
   score on the three rings (999 = award animation).

IDEAS FOR LATER GAMES (nothing built yet)
   Whack-a-mole (Left hits the left half, Right the right half), Breakout, Snake, a magic 8-ball mode for Random,
   spirit level (accelerometer), a countdown timer next to the stopwatch, tap-tempo for the metronome.

CFG: HOW TO CHANGE A SETTING
----------------------------
1. Open CFG from mode selection (hold LEFT, tap RIGHT until CFG blinks, then wait).
2. The HOUR RING shows ONE steady LED: hour LED 1..12 = setting 1..12.
   The MINUTE RING shows a bar from 12 o'clock: bar length = which choice (short bar = first choice, full ring = last).
3. RIGHT short = next value (wraps).   LEFT short = next setting.
4. Changes apply immediately (no save step). Leave with LEFT long.

   hour LED  setting             choices (the order the bar counts them; default marked)
   1         brightness          5 %, 10 %, 20 % (default), 30 %, 50 %
   2         raise sensitivity   low, medium (default), high   (how hard a wrist raise must be)
   3         wake duration       2 s, 3 s, 5 s, 10 s (default)
   4         auto brightness     off (default), on (uses the ambient-light sense)
   5         seconds LED         always (default), never
   6         wake by raise       on (default), off
   7         wake by shake       on (default), off
   8         wake by tap         on (default), off
   9         buttons that wake   either (default), left only, right only, none
   10        lock display        motion wakes it (default), stays dark, always on (low brightness, no seconds)
   11        key beeps           off (default), on: a 3.5 kHz click on every button press (not inside games; games make their own sounds)
   12        game sounds         on (default), off: hits, misses, wins, Simon tones, the metronome tick, Quick Draw GO

POWER NOTES
-----------
Only about 3 LEDs are lit at a time in normal use. Games and bars light more, and because each row
pin can only sink 10 mA, a crowded picture is automatically dimmed (the simulator shows
"brightness limited" and the lost percentage). LED brightness is held constant against battery
voltage by changing the on-time (3.0 V -> 4.2 V changes LED current from 1.6 to 4.8 mA).

OPEN QUESTIONS (design calls to confirm)
----------------------------------------
1. Weekday display: bar of 1-7 outer LEDs (current) vs one LED on a 7-position "hand" (outer LEDs 0, 9, 17, 26, 34, 43, 51)
   vs silkscreen ticks (60 LEDs do not divide by 7).
2. Mode selection auto-enters after 2.5 s: right length? (This is now the main way to confirm.)
3. Which game idea next?

SOUNDS (the piezo, Murata PKMCS0909E4000-R1 on PB4/PB5)
-------------------------------------------------------
What beeps is decided by CFG 11 / CFG 12 and the alarm; the simulator plays the same frequencies the watch would (Sound panel).
   alarm            beep beep beep beep, pause, repeating (4 kHz), up to a minute, always on while the alarm is set; any button stops it
   key beeps        CFG 11 (off by default): short click on every press
   games (CFG 12)   Ring Runner: tick per obstacle, falling tune on a crash   Target: rising pair on a hit, falling tune on a miss
                    Quick Draw: a long beep on GO, a fanfare for the winner, a low double beep for a false start
                    Simon: a low tone for LEFT, a high tone for RIGHT (while it shows the sequence and when you press), falling tune if wrong
                    Pong: tick on every return, rising pair for a point, fanfare for the winner, falling tune when a solo game ends
                    Pacer (metronome): a tick on every beat, a higher one on the first of four
                    999 points: a longer fanfare with the award animation
   A low battery (BAT_OK low) mutes everything except the alarm. No sound is shorter than 20 ms (the watch loop steps every 16 ms).
