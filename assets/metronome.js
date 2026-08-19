/*!
 * perfecttune.net — Metronome (mt-).
 * Sample-accurate timing via the classic Web Audio lookahead scheduler
 * ("A Tale of Two Clocks" pattern): a setTimeout loop runs frequently and
 * schedules every upcoming click's exact start time on the audio clock
 * (audioCtx.currentTime), instead of firing one setInterval per beat —
 * setInterval alone drifts under tab throttling / GC pauses, this doesn't.
 * The pendulum and beat lights are driven every animation frame from that
 * same real schedule, not a separate decorative timer.
 *
 * The beat clock is deliberately the only clock. Subdivisions, swing and the
 * tempo trainer are all layered on top of it rather than folded into it:
 *   * secondsPerBeat() still returns the length of a BEAT. Dividing it by the
 *     subdivision here would land the accent on every Nth click, make the
 *     lights and the pendulum count sixteenths as beats, and flutter the
 *     gauge four times a beat at 4x.
 *   * Subdivision clicks are scheduled straight into playClick() at a lower
 *     gain and never touch noteQueue, so only beat boundaries reach the
 *     lights and the pendulum.
 *   * Swing displaces the odd-numbered subdivision inside a beat. Index 0 is
 *     the beat itself and is never in that set, so no amount of swing can
 *     move a downbeat.
 */
(function () {
  "use strict";

  var Gauge = window.PerfectTuneGauge;

  /*
   * Clicks per beat, and whether a swing feel means anything at that
   * division. Swing delays the second half of a pair towards the triplet
   * grid — with sixteenths as the primary division there is no pair left to
   * delay (you are already playing the grid swing would push towards), and a
   * plain quarter has nothing inside the beat at all.
   */
  var SUBDIVISIONS = {
    1: { swings: false },
    2: { swings: true },
    3: { swings: true },
    4: { swings: false }
  };

  /*
   * The three voices. The subdivision click is a fifth of the beat click's
   * peak and decays faster: it has to be countable without competing with the
   * pulse it is subdividing.
   */
  var CLICK = {
    accent: { freq: 1480, peak: 0.5, decay: 0.045 },
    beat: { freq: 950, peak: 0.3, decay: 0.045 },
    sub: { freq: 1270, peak: 0.06, decay: 0.028 }
  };

  function initMetronome() {
    var startBtn = document.getElementById("mt-start");
    if (!startBtn) return;
    var tapBtn = document.getElementById("mt-tap");
    var bpmInput = document.getElementById("mt-bpm");
    var bpmSlider = document.getElementById("mt-bpm-slider");
    var numSelect = document.getElementById("mt-num");
    var denSelect = document.getElementById("mt-den");
    var accentInput = document.getElementById("mt-accent");
    var subdivSelect = document.getElementById("mt-subdiv");
    var swingSlider = document.getElementById("mt-swing");
    var swingOut = document.getElementById("mt-swing-out");
    var rampInput = document.getElementById("mt-ramp");
    var rampFromInput = document.getElementById("mt-ramp-from");
    var rampStepInput = document.getElementById("mt-ramp-step");
    var rampBarsInput = document.getElementById("mt-ramp-bars");
    var rampToInput = document.getElementById("mt-ramp-to");
    var rampStatusEl = document.getElementById("mt-ramp-status");
    var rampCountEl = document.getElementById("mt-ramp-count");
    var barCountEl = document.getElementById("mt-bar-count");
    var statusEl = document.getElementById("mt-status");
    var bpmDisplay = document.getElementById("mt-bpm-display");
    var lightsEl = document.getElementById("mt-lights");
    var gaugeMount = document.getElementById("mt-gauge");
    var gauge = Gauge ? Gauge.mountPendulum(gaugeMount, { sweep: 26, maxBeats: 12 }) : null;

    var LOOKAHEAD_MS = 25.0;
    var SCHEDULE_AHEAD = 0.12;
    var audioCtx = null;
    var timerId = null;
    var rafId = null;
    var running = false;
    var tempo = 120;
    var beatsPerBar = 4;
    var beatUnit = 4;
    var accentOn = true;
    var subdivision = 1;
    var swingPercent = 0;
    var currentBeat = 0;
    var barsPlayed = 0;
    var nextNoteTime = 0;
    var noteQueue = [];
    var tapTimes = [];

    var rampOn = false;
    var rampFrom = 80;
    var rampStep = 4;
    var rampBars = 8;
    var rampTo = 140;
    var rampDone = false;
    var lastRampText = "";
    var lastCountText = "";
    var lastBarText = "";

    // One AudioContext for the whole site (assets/audio.js), created on the
    // first user gesture and shared with the other sound-making tools.
    function getAudioCtx() {
      audioCtx = window.PerfectTuneAudio.context();
      return audioCtx;
    }

    // The length of one BEAT — never one subdivision. Everything the lights,
    // the pendulum, the bar counter and the trainer count is measured in these.
    function secondsPerBeat() {
      return (60.0 / tempo) * (4 / beatUnit);
    }

    function subdivisionInfo() {
      // Guarded because swingActive() is on the audio hot path: a select that
      // ever offered a value this table does not have would throw inside the
      // scheduler and stop the metronome dead rather than degrade.
      return SUBDIVISIONS[subdivision] || SUBDIVISIONS[1];
    }

    function swingActive() {
      return swingPercent > 0 && subdivisionInfo().swings;
    }

    function playClick(time, kind) {
      var ctx = audioCtx;
      var voice = CLICK[kind];
      var osc = ctx.createOscillator();
      var gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(voice.freq, time);
      gain.gain.setValueAtTime(0.0001, time);
      gain.gain.exponentialRampToValueAtTime(voice.peak, time + 0.002);
      gain.gain.exponentialRampToValueAtTime(0.0001, time + voice.decay);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(time);
      osc.stop(time + voice.decay + 0.015);
    }

    /*
     * One beat's worth of audio. The beat itself is the only thing pushed
     * onto noteQueue; its subdivisions are sounded and forgotten, which is
     * what keeps the visuals counting beats.
     *
     * Offsets are measured from the beat, so index 0 — the downbeat — is not
     * in the loop and cannot be swung. Odd indices are pushed later by
     * swing% of one subdivision: at 33% an eighth-note pair lands on the
     * triplet grid (the classic shuffle), at 50% on a dotted eighth and a
     * sixteenth, and the slider's 66% ceiling is harder than either.
     */
    function scheduleNote(beatNumber, time) {
      noteQueue.push({ beat: beatNumber, time: time, flashed: false });
      playClick(time, beatNumber === 0 && accentOn ? "accent" : "beat");
      if (subdivision > 1) {
        var sub = secondsPerBeat() / subdivision;
        var swing = swingActive() ? (swingPercent / 100) * sub : 0;
        for (var i = 1; i < subdivision; i++) {
          playClick(time + i * sub + (i % 2 === 1 ? swing : 0), "sub");
        }
      }
    }

    /*
     * The trainer, evaluated once per completed bar. It writes through
     * setBpm(), which is the only function that owns `tempo` — going around
     * it would leave the slider, the number field and the big readout showing
     * a tempo the scheduler is no longer using. setBpm() touches three DOM
     * properties and reads no geometry, so it forces no layout; at one call
     * per `rampBars` bars it is nowhere near the hot path.
     */
    function rampDelta() {
      var step = Math.abs(rampStep);
      if (!step) return 0;
      return rampTo >= rampFrom ? step : -step;
    }

    function rampBoundary() {
      if (!rampOn || rampDone) return;
      // advance() increments barsPlayed before calling this, so bar 0 is
      // already excluded — the first step lands after rampBars whole bars.
      if (barsPlayed % rampBars !== 0) return;
      var delta = rampDelta();
      if (!delta) {
        rampDone = true;
        return;
      }
      var next = tempo + delta;
      if (delta > 0 ? next >= rampTo : next <= rampTo) {
        next = rampTo;
        rampDone = true;
      }
      setBpm(next);
    }

    function advance() {
      nextNoteTime += secondsPerBeat();
      currentBeat = (currentBeat + 1) % beatsPerBar;
      if (currentBeat === 0) {
        barsPlayed++;
        rampBoundary();
      }
    }

    function scheduler() {
      /*
       * A long main-thread stall (GC, a backgrounded tab that kept its timers)
       * can leave nextNoteTime well in the past. Catching up beat by beat
       * would dump every missed click into the same instant and walk the
       * trainer through several rungs at once, so jump the clock forward
       * instead and carry on from now. The threshold is far outside anything
       * normal scheduling produces, where nextNoteTime is always ahead of the
       * audio clock by up to SCHEDULE_AHEAD.
       */
      if (running && nextNoteTime < audioCtx.currentTime - 0.25) {
        nextNoteTime = audioCtx.currentTime + 0.02;
      }
      while (nextNoteTime < audioCtx.currentTime + SCHEDULE_AHEAD) {
        scheduleNote(currentBeat, nextNoteTime);
        advance();
      }
      timerId = window.setTimeout(scheduler, LOOKAHEAD_MS);
    }

    function renderLights() {
      lightsEl.innerHTML = "";
      for (var i = 0; i < beatsPerBar; i++) {
        var span = document.createElement("span");
        span.className = "beat-light" + (i === 0 ? " is-down" : "");
        lightsEl.appendChild(span);
      }
    }

    function lightBeat(index) {
      var lights = lightsEl.children;
      for (var i = 0; i < lights.length; i++) {
        lights[i].classList.toggle("is-lit", i === index);
      }
    }

    function visualLoop() {
      if (!running) return;
      var now = audioCtx.currentTime;
      // Drop stale entries but always keep the most recent past note.
      while (noteQueue.length > 2 && noteQueue[1].time <= now) noteQueue.shift();

      var prev = null,
        next = null;
      for (var i = 0; i < noteQueue.length; i++) {
        if (noteQueue[i].time <= now) prev = noteQueue[i];
        else {
          next = noteQueue[i];
          break;
        }
      }
      if (prev && !prev.flashed) {
        prev.flashed = true;
        lightBeat(prev.beat);
        // Once a beat, not once a frame: the trainer's readout only ever
        // changes on a beat boundary, and rebuilding that string sixty times
        // a second would be sixty times the garbage for the same text.
        syncTrainerReadout();
      }
      if (gauge && prev && next) {
        var span = next.time - prev.time;
        var frac = span > 0 ? (now - prev.time) / span : 0;
        var dir = prev.beat % 2 === 0 ? 1 : -1;
        var pos = dir * -Math.cos(frac * Math.PI);
        gauge.setSwing(pos);
      }
      rafId = requestAnimationFrame(visualLoop);
    }

    function setBpm(v) {
      tempo = Math.max(30, Math.min(300, Math.round(v)));
      bpmInput.value = tempo;
      bpmSlider.value = tempo;
      bpmDisplay.textContent = tempo;
    }

    // ------------------------------------------------------ trainer readout --

    function plural(n, word) {
      return n + " " + word + (n === 1 ? "" : "s");
    }

    /*
     * Two readouts, deliberately. The state sentence lives in a polite live
     * region and only changes when something a screen reader should hear
     * changes — armed, disarmed, started, target reached. The bar countdown
     * changes every bar, so it sits in its own aria-live="off" node: a
     * "next change in 5 bars" announcement every two seconds for a ten-minute
     * practice session is not information, it is a stuck horn.
     */
    function trainerState() {
      if (!rampOn) return "Trainer off — the tempo stays exactly where you put it.";
      var delta = rampDelta();
      if (!delta) return "Set a step other than 0 for the trainer to move anywhere.";
      var sign = delta > 0 ? "+" : "−";
      var plan =
        rampFrom + " to " + rampTo + " BPM, " + sign + Math.abs(delta) +
        " every " + plural(rampBars, "bar") + ".";
      if (!running) return "Ready: " + plan + " Press Start.";
      if (rampDone) return "Target reached — holding " + tempo + " BPM.";
      return plan;
    }

    function trainerCount() {
      if (!rampOn || !running || rampDone || !rampDelta()) return "";
      return " Next change in " + plural(rampBars - (barsPlayed % rampBars), "bar") + ".";
    }

    function syncTrainerReadout() {
      var text = trainerState();
      if (text !== lastRampText) {
        lastRampText = text;
        rampStatusEl.textContent = text;
      }
      var count = trainerCount();
      if (count !== lastCountText) {
        lastCountText = count;
        rampCountEl.textContent = count;
      }
      var bars = running ? String(barsPlayed + 1) : "—";
      if (bars !== lastBarText) {
        lastBarText = bars;
        barCountEl.textContent = bars;
      }
    }

    function syncSwingUI() {
      var swings = subdivisionInfo().swings;
      swingSlider.disabled = !swings;
      if (!swings) {
        swingOut.textContent = "Eighths or triplets only";
        return;
      }
      // Percentages are of one SUBDIVISION, not of the beat: 33% lands the
      // offbeat on the triplet grid and 50% on a dotted eighth. That is a
      // different scale from a sequencer's swing knob, where 50% is straight,
      // so the readout names the feel rather than leaving the number to be
      // read against the wrong reference.
      if (!swingPercent) swingOut.textContent = "Straight";
      else if (swingPercent < 25) swingOut.textContent = swingPercent + "% — a light lilt";
      else if (swingPercent <= 40) swingOut.textContent = swingPercent + "% — triplet shuffle";
      else if (swingPercent < 47) swingOut.textContent = swingPercent + "% — past the shuffle";
      else if (swingPercent <= 53) swingOut.textContent = swingPercent + "% — dotted eighth";
      else swingOut.textContent = swingPercent + "% — harder than dotted";
    }

    // ---------------------------------------------------------- transport --

    function start() {
      getAudioCtx();
      currentBeat = 0;
      barsPlayed = 0;
      rampDone = false;
      if (rampOn && rampDelta()) setBpm(rampFrom);
      nextNoteTime = audioCtx.currentTime + 0.05;
      noteQueue = [];
      running = true;
      startBtn.textContent = "Stop";
      startBtn.classList.remove("primary");
      startBtn.classList.add("stop");
      statusEl.textContent = "Running";
      statusEl.setAttribute("data-state", "running");
      scheduler();
      rafId = requestAnimationFrame(visualLoop);
    }

    function stop() {
      running = false;
      if (timerId) window.clearTimeout(timerId);
      if (rafId) cancelAnimationFrame(rafId);
      noteQueue = [];
      startBtn.textContent = "Start";
      startBtn.classList.remove("stop");
      startBtn.classList.add("primary");
      statusEl.textContent = "Idle";
      statusEl.setAttribute("data-state", "idle");
      var lights = lightsEl.children;
      for (var i = 0; i < lights.length; i++) lights[i].classList.remove("is-lit");
      if (gauge) gauge.setSwing(0);
      syncTrainerReadout();
    }

    startBtn.addEventListener("click", function () {
      if (running) stop();
      else start();
    });

    tapBtn.addEventListener("click", function () {
      getAudioCtx();
      var t = performance.now();
      if (tapTimes.length && t - tapTimes[tapTimes.length - 1] > 2200) tapTimes = [];
      tapTimes.push(t);
      if (tapTimes.length > 8) tapTimes.shift();
      if (tapTimes.length >= 2) {
        var intervals = [];
        for (var i = 1; i < tapTimes.length; i++) intervals.push(tapTimes[i] - tapTimes[i - 1]);
        var avg = intervals.reduce(function (a, b) { return a + b; }, 0) / intervals.length;
        setBpm(60000 / avg);
      }
    });

    bpmInput.addEventListener("input", function () {
      var v = Number(bpmInput.value);
      if (!isNaN(v)) setBpm(v);
    });
    bpmSlider.addEventListener("input", function () {
      setBpm(Number(bpmSlider.value));
    });

    numSelect.addEventListener("change", function () {
      beatsPerBar = Number(numSelect.value) || 4;
      // Going from 7 beats to 2 mid-bar would leave currentBeat past the end
      // of the new bar, and the next beat would light a beat-light that no
      // longer exists — one visibly dropped flash. Restart the bar instead.
      if (currentBeat >= beatsPerBar) currentBeat = 0;
      renderLights();
    });
    denSelect.addEventListener("change", function () {
      beatUnit = Number(denSelect.value) || 4;
    });
    accentInput.addEventListener("change", function () {
      accentOn = accentInput.checked;
    });

    subdivSelect.addEventListener("change", function () {
      subdivision = Number(subdivSelect.value) || 1;
      syncSwingUI();
    });
    swingSlider.addEventListener("input", function () {
      swingPercent = Math.max(0, Math.min(66, Number(swingSlider.value) || 0));
      syncSwingUI();
    });

    /*
     * Read one trainer field, keeping the value it already had if the box is
     * empty or unparseable. Falling back to the field's minimum instead would
     * mean that clearing "Stop at" to retype it left the target at 30 for the
     * length of the keystrokes — and with a start of 80 that inverts the ramp,
     * so a bar boundary landing in that window would step the tempo DOWN.
     */
    function readField(el, previous, lo, hi) {
      var raw = el.value.trim();
      if (raw === "") return previous;
      var v = Number(raw);
      if (!isFinite(v)) return previous;
      return Math.max(lo, Math.min(hi, Math.round(v)));
    }

    function readTrainer() {
      rampOn = rampInput.checked;
      rampFrom = readField(rampFromInput, rampFrom, 30, 300);
      rampStep = Math.abs(readField(rampStepInput, rampStep, 0, 30));
      rampBars = readField(rampBarsInput, rampBars, 1, 64);
      rampTo = readField(rampToInput, rampTo, 30, 300);
      rampDone = false;
      syncTrainerReadout();
    }

    /*
     * "change", not "input", on the number fields: "input" fires per keystroke,
     * and a half-typed target is not an instruction. The checkbox has no
     * half-typed state, so it commits immediately.
     */
    [rampFromInput, rampStepInput, rampBarsInput, rampToInput].forEach(function (el) {
      el.addEventListener("change", readTrainer);
    });
    rampInput.addEventListener("change", readTrainer);
    rampInput.addEventListener("change", function () {
      // Arming the trainer moves the tempo to its starting point, so the
      // number you are about to hear is the number on the screen.
      if (rampOn && !running && rampDelta()) setBpm(rampFrom);
    });

    document.addEventListener("perfecttune:panel-shown", function (e) {
      if (running && e.detail.slug !== "metronome") stop();
    });
    window.addEventListener("beforeunload", function () {
      if (timerId) window.clearTimeout(timerId);
      if (rafId) cancelAnimationFrame(rafId);
    });

    renderLights();
    setBpm(120);
    readTrainer();
    syncSwingUI();

    // A per-tempo landing page ships its own tempo on the chassis, so the
    // readout, the slider and the scheduler all agree before any script has
    // had a chance to disagree with the headline.
    var chassis = document.querySelector(".instrument[data-bpm]");
    if (chassis) {
      var preset = Number(chassis.getAttribute("data-bpm"));
      if (preset >= 30 && preset <= 300) setBpm(preset);
    }

    // The BPM Tapper hands a tempo over as /metronome/?bpm=NNN. It only
    // pre-loads the number — nothing starts until Start is pressed — and it
    // wins over a page's own data-bpm, because it is the more specific ask.
    var fromQuery = /[?&]bpm=(\d+(?:\.\d+)?)/.exec(window.location.search);
    if (fromQuery) {
      var handed = Number(fromQuery[1]);
      if (handed >= 30 && handed <= 300) {
        setBpm(handed);
        statusEl.textContent = "Tempo set";
      }
    }
  }

  document.addEventListener("DOMContentLoaded", initMetronome);
})();
