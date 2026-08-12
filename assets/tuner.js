/*!
 * perfecttune.net — Tuner (tn-).
 *
 * Two ways to tune, and only one of them asks for anything. The string
 * chart and its per-string reference tones are the primary interface:
 * they are rendered into the page by build.py, they work with the
 * microphone denied, blocked, absent or never requested, and they are what
 * this file enhances rather than creates. Live pitch detection is the
 * opt-in second half — getUserMedia and the AudioContext are only ever
 * reached from inside the Start button's click handler, and the mic audio
 * is analysed by assets/pitch.js entirely on-device, frame by frame, and
 * discarded.
 *
 * The needle either follows a string you have pinned, or auto-snaps to
 * whichever string of the active preset you are nearest — falling back to
 * plain chromatic note-naming when what you are playing is nowhere near
 * any of them.
 */
(function () {
  "use strict";

  var Notes = window.PerfectTuneNotes;
  var Gauge = window.PerfectTuneGauge;
  var Audio = window.PerfectTuneAudio;
  var Pitch = window.PerfectTunePitch;
  var Tunings = window.PerfectTuneTunings;

  // Beyond this many cents from every string in the preset, auto mode stops
  // pretending you are tuning one of them and just names the note.
  var AUTO_SNAP_CENTS = 350;
  // Detection is far cheaper than it used to be but still not free at a
  // 16384-sample window; a tuner that updates 25 times a second reads as
  // instant, and the needle's own CSS transition smooths the rest.
  var DETECT_INTERVAL_MS = 40;
  var TONE_SECONDS = 1.7;

  function centsBetween(freq, target) {
    return 1200 * (Math.log(freq / target) / Math.LN2);
  }

  function initTuner() {
    var root = document.querySelector(".tuner-instrument");
    if (!root || !Tunings || !Pitch) return;

    var startBtn = document.getElementById("tn-start");
    var stopBtn = document.getElementById("tn-stop");
    var statusEl = document.getElementById("tn-status");
    var noteEl = document.getElementById("tn-note");
    var centsEl = document.getElementById("tn-cents");
    var freqEl = document.getElementById("tn-freq");
    var targetEl = document.getElementById("tn-target");
    var errorEl = document.getElementById("tn-error");
    var a4Input = document.getElementById("tn-a4");
    var gaugeMount = document.getElementById("tn-gauge");
    var tuningSelect = document.getElementById("tn-tuning");
    var tuningName = document.getElementById("tn-tuning-name");
    var tbody = document.getElementById("tn-tbody");
    var autoBtn = document.getElementById("tn-auto");
    var playAllBtn = document.getElementById("tn-play-all");
    var chartNote = document.getElementById("tn-target-note");
    var gauge = Gauge ? Gauge.mountCents(gaugeMount, { sweep: 55, range: 50 }) : null;

    var tuning = Tunings.byId(root.getAttribute("data-default-tuning"));
    var targetIndex = null; // null = auto-snap to the nearest string
    var audioCtx = null;
    var analyser = null;
    var source = null;
    var stream = null;
    var buffer = null;
    var rafId = null;
    var running = false;
    var smoothedCents = 0;
    var hasReading = false;
    var lastDetect = 0;
    var muteUntil = 0; // while a reference tone is sounding, ignore the mic

    function a4() {
      var v = Number(a4Input && a4Input.value);
      return v && v > 380 && v < 480 ? v : 440;
    }

    function stringFreq(i) {
      return Tunings.freq(tuning.strings[i].midi, a4());
    }

    /* --------------------------------------------------- the string chart */

    // Rebuild the rows for a newly chosen tuning. The markup matches what
    // build.py wrote for the page's default tuning exactly — same classes,
    // same data attributes — so nothing downstream has to know which of the
    // two produced the row it is looking at.
    function renderChart() {
      if (!tbody) return;
      var html = "";
      tuning.strings.forEach(function (s, i) {
        html +=
          '<tr data-index="' + i + '" data-midi="' + s.midi + '">' +
          '<th scope="row" class="st-num">' + s.ord + "</th>" +
          '<td class="st-note">' + s.label + "</td>" +
          '<td class="st-freq mono">' + stringFreq(i).toFixed(2) + " Hz</td>" +
          '<td class="st-actions">' +
          '<button type="button" class="string-btn tone" data-tone="' + i + '">' +
          '<span aria-hidden="true">&#9834;</span> Tone<span class="visually-hidden"> for the ' +
          s.ord + " string, " + s.label + "</span></button>" +
          '<button type="button" class="string-btn target" data-target="' + i + '" aria-pressed="false">' +
          "Target<span class=\"visually-hidden\"> the " + s.ord + " string, " + s.label + "</span></button>" +
          "</td></tr>";
      });
      tbody.innerHTML = html;
      markTarget();
    }

    // Refresh only the frequency column — concert pitch moved, the notes
    // did not.
    function refreshFrequencies() {
      if (!tbody) return;
      var cells = tbody.querySelectorAll(".st-freq");
      for (var i = 0; i < cells.length; i++) cells[i].textContent = stringFreq(i).toFixed(2) + " Hz";
    }

    function markTarget() {
      if (!tbody) return;
      var rows = tbody.querySelectorAll("tr");
      for (var i = 0; i < rows.length; i++) {
        var on = targetIndex === i;
        rows[i].classList.toggle("is-target", on);
        var btn = rows[i].querySelector("[data-target]");
        if (btn) {
          btn.setAttribute("aria-pressed", String(on));
          btn.textContent = on ? "Targeted" : "Target";
          var sr = document.createElement("span");
          sr.className = "visually-hidden";
          sr.textContent = " the " + tuning.strings[i].ord + " string, " + tuning.strings[i].label;
          btn.appendChild(sr);
        }
      }
      if (autoBtn) {
        autoBtn.setAttribute("aria-pressed", String(targetIndex === null));
        autoBtn.classList.toggle("is-on", targetIndex === null);
      }
      if (chartNote) {
        chartNote.innerHTML =
          targetIndex === null
            ? "Tap <strong>Tone</strong> to hear a string and tune to it by ear &mdash; no microphone needed. <strong>Auto</strong> is on, so the needle below follows whichever string you are nearest."
            : "Tap <strong>Tone</strong> to hear a string and tune to it by ear &mdash; no microphone needed. The needle is pinned to the <strong>" +
              tuning.strings[targetIndex].ord +
              " string, " +
              tuning.strings[targetIndex].label +
              "</strong>; tap Auto to release it.";
      }
      if (!running) showIdleTarget();
    }

    /* ------------------------------------------------------ reference tone */

    // A bass low B's fundamental is 30.87 Hz, which a laptop speaker cannot
    // physically reproduce. Adding the octave and the twelfth quietly above
    // it gives the ear a pitch to lock onto through small speakers without
    // moving the fundamental — the same trick that makes a bass guitar
    // audible on a phone.
    function playFreq(f, when) {
      if (!Audio) return;
      var opts = { freq: f, duration: TONE_SECONDS, type: "triangle", gain: 0.22 };
      if (typeof when === "number") opts.when = when;
      Audio.note(opts);
      if (f < 130) {
        Audio.note({ freq: f * 2, when: opts.when, duration: TONE_SECONDS, type: "sine", gain: 0.09 });
        Audio.note({ freq: f * 3, when: opts.when, duration: TONE_SECONDS, type: "sine", gain: 0.045 });
      }
    }

    function suspendMic(seconds) {
      // Playing a tone out of the speakers while the mic is open would have
      // the tuner confidently detect its own reference note.
      muteUntil = Date.now() + seconds * 1000;
      if (running) {
        statusEl.textContent = "Reference tone";
        statusEl.setAttribute("data-state", "playing");
      }
    }

    function playString(i) {
      if (!Audio) return;
      Audio.stopAll();
      playFreq(stringFreq(i));
      suspendMic(TONE_SECONDS + 0.4);
    }

    function playAll() {
      if (!Audio) return;
      Audio.stopAll();
      var ctx = Audio.context();
      if (!ctx) return;
      var spacing = 1.15;
      var start = ctx.currentTime + 0.06;
      tuning.strings.forEach(function (s, i) {
        playFreq(stringFreq(i), start + i * spacing);
      });
      suspendMic(spacing * tuning.strings.length + TONE_SECONDS);
    }

    /* ------------------------------------------------------------ readout */

    function setStatus(text, state) {
      statusEl.textContent = text;
      statusEl.setAttribute("data-state", state);
    }

    function showIdleTarget() {
      if (running) return;
      noteEl.innerHTML = '<span class="octave">&mdash;</span>';
      noteEl.classList.remove("in-tune");
      centsEl.innerHTML =
        targetIndex === null
          ? "Optional. Tap Start listening for a live needle, or tune by ear with the tones above."
          : "Pinned to " +
            tuning.strings[targetIndex].label +
            ". Tap Start listening for a live needle, or tune by ear with the tones above.";
      freqEl.textContent = "—";
      targetEl.textContent = targetIndex === null ? "—" : stringFreq(targetIndex).toFixed(2) + " Hz";
      if (gauge) gauge.setValue(0);
    }

    function setIdle() {
      setStatus("Idle", "idle");
      startBtn.hidden = false;
      stopBtn.hidden = true;
      hasReading = false;
      showIdleTarget();
    }

    function showError(message) {
      setStatus("Mic blocked", "error");
      errorEl.innerHTML = message;
      errorEl.classList.add("is-visible");
      startBtn.hidden = false;
      stopBtn.hidden = true;
      // The page is not over: say so, and point at the half that still works.
      centsEl.innerHTML = "The string chart and its reference tones above still work &mdash; tune by ear.";
    }

    // Which string of the active preset is this frequency nearest, in cents?
    function nearestString(freq) {
      var best = -1;
      var bestAbs = Infinity;
      for (var i = 0; i < tuning.strings.length; i++) {
        var c = Math.abs(centsBetween(freq, stringFreq(i)));
        if (c < bestAbs) {
          bestAbs = c;
          best = i;
        }
      }
      return { index: best, cents: bestAbs };
    }

    function render(freq) {
      if (freq === null) {
        hasReading = false;
        setStatus("Listening…", "listening");
        centsEl.innerHTML = "No clear pitch — play one string and let it ring.";
        noteEl.classList.remove("in-tune");
        return;
      }

      var a4v = a4();
      var idx = targetIndex;
      if (idx === null) {
        var near = nearestString(freq);
        idx = near.cents <= AUTO_SNAP_CENTS ? near.index : -1;
      }

      var label, targetFreq, cents;
      if (idx >= 0) {
        var s = tuning.strings[idx];
        targetFreq = stringFreq(idx);
        cents = centsBetween(freq, targetFreq);
        label = s.name + '<span class="octave">' + s.octave + "</span>";
      } else {
        var a = Notes.analyze(freq, a4v);
        targetFreq = a.targetFreq;
        cents = a.cents;
        label = a.name + '<span class="octave">' + a.octave + "</span>";
      }

      smoothedCents = hasReading ? smoothedCents * 0.65 + cents * 0.35 : cents;
      hasReading = true;

      setStatus("Listening…", "listening");
      noteEl.innerHTML = label;
      var inTune = Math.abs(cents) < 5;
      noteEl.classList.toggle("in-tune", inTune);
      var sign = cents > 0 ? "+" : "";
      var which =
        idx >= 0
          ? (targetIndex === null ? "nearest: " : "pinned: ") + tuning.strings[idx].ord + " string"
          : "no string nearby";
      centsEl.innerHTML = inTune
        ? "<strong>In tune</strong> — " + which
        : sign + cents.toFixed(0) + " cents " + (cents > 0 ? "sharp" : "flat") + " — " + which;
      freqEl.textContent = freq.toFixed(1) + " Hz";
      targetEl.textContent = targetFreq.toFixed(2) + " Hz";
      if (gauge) gauge.setValue(Math.max(-50, Math.min(50, smoothedCents)));
    }

    /* ------------------------------------------------------- analysis loop */

    // The analysis window is a function of the lowest string in the active
    // preset: 2048 samples for a ukulele, 16384 for a 5-string bass, because
    // a 30.87 Hz cycle is 1555 samples long and you cannot measure a period
    // you cannot fit several of into the buffer.
    function configureAnalyser() {
      if (!analyser || !audioCtx) return;
      var range = Tunings.detectRange(tuning, a4());
      var size = Pitch.windowSizeFor(audioCtx.sampleRate, range.fmin);
      if (analyser.fftSize !== size) {
        analyser.fftSize = size;
        buffer = new Float32Array(size);
      } else if (!buffer || buffer.length !== size) {
        buffer = new Float32Array(size);
      }
    }

    function loop() {
      if (!running) return;
      rafId = requestAnimationFrame(loop);
      var now = Date.now();
      if (now < muteUntil) return;
      if (now - lastDetect < DETECT_INTERVAL_MS) return;
      lastDetect = now;
      analyser.getFloatTimeDomainData(buffer);
      var range = Tunings.detectRange(tuning, a4());
      var result = Pitch.detect(buffer, audioCtx.sampleRate, range);
      render(result ? result.freq : null);
    }

    /* -------------------------------------------------------------- events */

    if (tuningSelect) {
      tuningSelect.addEventListener("change", function () {
        tuning = Tunings.byId(tuningSelect.value);
        targetIndex = null;
        renderChart();
        if (tuningName) {
          tuningName.innerHTML =
            tuning.instrument +
            " &mdash; " +
            (tuning.name === tuning.label ? tuning.name : tuning.name + " (" + tuning.label + ")");
        }
        configureAnalyser();
        hasReading = false;
      });
    }

    if (a4Input) {
      a4Input.addEventListener("input", function () {
        refreshFrequencies();
        configureAnalyser();
        if (!running) showIdleTarget();
      });
    }

    if (tbody) {
      tbody.addEventListener("click", function (e) {
        var btn = e.target.closest && e.target.closest("button");
        if (!btn) return;
        if (btn.hasAttribute("data-tone")) {
          playString(Number(btn.getAttribute("data-tone")));
        } else if (btn.hasAttribute("data-target")) {
          var i = Number(btn.getAttribute("data-target"));
          targetIndex = targetIndex === i ? null : i;
          markTarget();
          hasReading = false;
        }
      });
    }

    if (autoBtn) {
      autoBtn.addEventListener("click", function () {
        targetIndex = null;
        markTarget();
        hasReading = false;
      });
    }

    if (playAllBtn) playAllBtn.addEventListener("click", playAll);

    startBtn.addEventListener("click", function () {
      errorEl.classList.remove("is-visible");
      startBtn.disabled = true;
      setStatus("Requesting mic…", "listening");

      var AC = window.AudioContext || window.webkitAudioContext;
      if (!AC || !navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showError("This browser doesn't support microphone input or Web Audio.");
        startBtn.disabled = false;
        return;
      }

      navigator.mediaDevices
        .getUserMedia({ audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false } })
        .then(function (mediaStream) {
          stream = mediaStream;
          audioCtx = new AC();
          if (audioCtx.state === "suspended") audioCtx.resume();
          analyser = audioCtx.createAnalyser();
          analyser.smoothingTimeConstant = 0;
          configureAnalyser();
          source = audioCtx.createMediaStreamSource(stream);
          source.connect(analyser); // never connected to destination: nothing is played back
          running = true;
          hasReading = false;
          startBtn.hidden = true;
          startBtn.disabled = false;
          stopBtn.hidden = false;
          setStatus("Listening…", "listening");
          rafId = requestAnimationFrame(loop);
        })
        .catch(function (err) {
          startBtn.disabled = false;
          if (err && err.name === "NotAllowedError") {
            showError("Microphone access was denied. Allow it in your browser's site settings for a live needle.");
          } else if (err && err.name === "NotFoundError") {
            showError("No microphone was found on this device.");
          } else {
            showError("Couldn't access the microphone: " + (err && err.message ? err.message : "unknown error"));
          }
        });
    });

    function stopAll() {
      running = false;
      if (rafId) cancelAnimationFrame(rafId);
      if (source) {
        try {
          source.disconnect();
        } catch (e) {}
      }
      if (stream) {
        stream.getTracks().forEach(function (t) {
          t.stop();
        });
      }
      if (audioCtx) {
        try {
          audioCtx.close();
        } catch (e) {}
      }
      audioCtx = null;
      analyser = null;
      source = null;
      stream = null;
      buffer = null;
      setIdle();
    }

    stopBtn.addEventListener("click", stopAll);

    // Release the mic if the user navigates away or switches homepage panels.
    window.addEventListener("beforeunload", stopAll);
    document.addEventListener("perfecttune:panel-shown", function (e) {
      if (e.detail.slug !== "tuner") {
        if (running) stopAll();
        if (Audio) Audio.stopAll();
      }
    });

    stopBtn.hidden = true;
    markTarget();
    setIdle();
  }

  document.addEventListener("DOMContentLoaded", initTuner);
})();
