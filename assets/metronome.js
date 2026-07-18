/*!
 * perfecttune.net — Metronome (mt-).
 * Sample-accurate timing via the classic Web Audio lookahead scheduler
 * ("A Tale of Two Clocks" pattern): a setTimeout loop runs frequently and
 * schedules every upcoming click's exact start time on the audio clock
 * (audioCtx.currentTime), instead of firing one setInterval per beat —
 * setInterval alone drifts under tab throttling / GC pauses, this doesn't.
 * The pendulum and beat lights are driven every animation frame from that
 * same real schedule, not a separate decorative timer.
 */
(function () {
  "use strict";

  var Gauge = window.PerfectTuneGauge;

  function initMetronome() {
    var startBtn = document.getElementById("mt-start");
    if (!startBtn) return;
    var tapBtn = document.getElementById("mt-tap");
    var bpmInput = document.getElementById("mt-bpm");
    var bpmSlider = document.getElementById("mt-bpm-slider");
    var numSelect = document.getElementById("mt-num");
    var denSelect = document.getElementById("mt-den");
    var accentInput = document.getElementById("mt-accent");
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
    var currentBeat = 0;
    var nextNoteTime = 0;
    var noteQueue = [];
    var tapTimes = [];

    function getAudioCtx() {
      if (!audioCtx) {
        var AC = window.AudioContext || window.webkitAudioContext;
        audioCtx = new AC();
      }
      if (audioCtx.state === "suspended") audioCtx.resume();
      return audioCtx;
    }

    function secondsPerBeat() {
      return (60.0 / tempo) * (4 / beatUnit);
    }

    function playClick(time, isAccent) {
      var ctx = audioCtx;
      var osc = ctx.createOscillator();
      var gain = ctx.createGain();
      var freq = isAccent ? 1480 : 950;
      var peak = isAccent ? 0.5 : 0.3;
      osc.type = "sine";
      osc.frequency.setValueAtTime(freq, time);
      gain.gain.setValueAtTime(0.0001, time);
      gain.gain.exponentialRampToValueAtTime(peak, time + 0.002);
      gain.gain.exponentialRampToValueAtTime(0.0001, time + 0.045);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(time);
      osc.stop(time + 0.06);
    }

    function scheduleNote(beatNumber, time) {
      noteQueue.push({ beat: beatNumber, time: time, flashed: false });
      playClick(time, beatNumber === 0 && accentOn);
    }

    function advance() {
      nextNoteTime += secondsPerBeat();
      currentBeat = (currentBeat + 1) % beatsPerBar;
    }

    function scheduler() {
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

    function start() {
      getAudioCtx();
      currentBeat = 0;
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
      renderLights();
    });
    denSelect.addEventListener("change", function () {
      beatUnit = Number(denSelect.value) || 4;
    });
    accentInput.addEventListener("change", function () {
      accentOn = accentInput.checked;
    });

    document.addEventListener("perfecttune:panel-shown", function (e) {
      if (running && e.detail.slug !== "metronome") stop();
    });
    window.addEventListener("beforeunload", function () {
      if (timerId) window.clearTimeout(timerId);
    });

    renderLights();
    setBpm(120);
  }

  document.addEventListener("DOMContentLoaded", initMetronome);
})();
