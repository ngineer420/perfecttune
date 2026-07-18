/*!
 * perfecttune.net — Tuner (tn-).
 * Mic audio never leaves the browser: getUserMedia + AnalyserNode feed a
 * classic autocorrelation pitch detector running entirely on-device. The
 * AudioContext and the mic stream are only created inside the Start
 * button's click handler (an explicit user gesture), never on page load.
 */
(function () {
  "use strict";

  var Notes = window.PerfectTuneNotes;
  var Gauge = window.PerfectTuneGauge;

  // Classic time-domain autocorrelation pitch detector with parabolic
  // interpolation for sub-sample precision. Returns -1 when the signal is
  // too quiet or no clear periodicity is found.
  function autoCorrelate(buf, sampleRate) {
    var SIZE = buf.length;
    var rms = 0;
    for (var i = 0; i < SIZE; i++) rms += buf[i] * buf[i];
    rms = Math.sqrt(rms / SIZE);
    if (rms < 0.008) return -1;

    // Trim leading/trailing near-silence so the window is centered on signal.
    var thres = 0.2;
    var r1 = 0,
      r2 = SIZE - 1;
    for (i = 0; i < SIZE / 2; i++) {
      if (Math.abs(buf[i]) < thres) {
        r1 = i;
        break;
      }
    }
    for (i = 1; i < SIZE / 2; i++) {
      if (Math.abs(buf[SIZE - i]) < thres) {
        r2 = SIZE - i;
        break;
      }
    }
    var trimmed = buf.slice(r1, r2);
    var n = trimmed.length;
    if (n < 512) return -1;

    var c = new Array(n).fill(0);
    for (var lag = 0; lag < n; lag++) {
      var sum = 0;
      for (var j = 0; j < n - lag; j++) sum += trimmed[j] * trimmed[j + lag];
      c[lag] = sum;
    }

    var d = 0;
    while (d < n - 1 && c[d] > c[d + 1]) d++;
    var maxVal = -1,
      maxPos = -1;
    for (i = d; i < n; i++) {
      if (c[i] > maxVal) {
        maxVal = c[i];
        maxPos = i;
      }
    }
    var T0 = maxPos;
    if (T0 <= 0) return -1;

    if (T0 > 0 && T0 < n - 1) {
      var x1 = c[T0 - 1],
        x2 = c[T0],
        x3 = c[T0 + 1];
      var a = (x1 + x3 - 2 * x2) / 2;
      var b = (x3 - x1) / 2;
      if (a !== 0) T0 = T0 - b / (2 * a);
    }

    var freq = sampleRate / T0;
    if (freq < 55 || freq > 1500) return -1; // outside a typical instrument's range
    return freq;
  }

  function initTuner() {
    var startBtn = document.getElementById("tn-start");
    if (!startBtn) return;
    var stopBtn = document.getElementById("tn-stop");
    var statusEl = document.getElementById("tn-status");
    var noteEl = document.getElementById("tn-note");
    var centsEl = document.getElementById("tn-cents");
    var freqEl = document.getElementById("tn-freq");
    var targetEl = document.getElementById("tn-target");
    var errorEl = document.getElementById("tn-error");
    var a4Input = document.getElementById("tn-a4");
    var gaugeMount = document.getElementById("tn-gauge");
    var gauge = Gauge ? Gauge.mountCents(gaugeMount, { sweep: 55, range: 50 }) : null;

    var audioCtx = null;
    var analyser = null;
    var source = null;
    var stream = null;
    var buffer = null;
    var rafId = null;
    var running = false;
    var smoothedCents = 0;
    var hasReading = false;

    function a4() {
      var v = Number(a4Input && a4Input.value);
      return v && v > 380 && v < 480 ? v : 440;
    }

    function setIdle() {
      statusEl.textContent = "Idle";
      statusEl.setAttribute("data-state", "idle");
      startBtn.hidden = false;
      stopBtn.hidden = true;
      noteEl.innerHTML = '<span class="octave">&mdash;</span>';
      noteEl.classList.remove("in-tune");
      centsEl.innerHTML = "Waiting for a signal&hellip;";
      freqEl.textContent = "&mdash;";
      targetEl.textContent = "—";
      if (gauge) gauge.setValue(0);
    }

    function showError(message) {
      statusEl.textContent = "Mic blocked";
      statusEl.setAttribute("data-state", "error");
      errorEl.textContent = message;
      errorEl.classList.add("is-visible");
      startBtn.hidden = false;
      stopBtn.hidden = true;
    }

    function render(freq) {
      if (freq === -1) {
        hasReading = false;
        statusEl.textContent = "Listening…";
        statusEl.setAttribute("data-state", "listening");
        centsEl.innerHTML = "No clear pitch — play a single sustained note.";
        noteEl.classList.remove("in-tune");
        return;
      }
      hasReading = true;
      var a = Notes.analyze(freq, a4());
      smoothedCents = hasReading ? smoothedCents * 0.65 + a.cents * 0.35 : a.cents;

      statusEl.textContent = "Listening…";
      statusEl.setAttribute("data-state", "listening");
      noteEl.innerHTML = a.name + '<span class="octave">' + a.octave + "</span>";
      var inTune = Math.abs(a.cents) < 5;
      noteEl.classList.toggle("in-tune", inTune);
      var sign = a.cents > 0 ? "+" : "";
      centsEl.innerHTML = inTune
        ? "<strong>In tune</strong>"
        : sign + a.cents.toFixed(0) + " cents " + (a.cents > 0 ? "sharp" : "flat");
      freqEl.textContent = freq.toFixed(1) + " Hz";
      targetEl.textContent = a.targetFreq.toFixed(1) + " Hz";
      if (gauge) gauge.setValue(smoothedCents);
    }

    function loop() {
      if (!running) return;
      analyser.getFloatTimeDomainData(buffer);
      var freq = autoCorrelate(buffer, audioCtx.sampleRate);
      render(freq);
      rafId = requestAnimationFrame(loop);
    }

    startBtn.addEventListener("click", function () {
      errorEl.classList.remove("is-visible");
      startBtn.disabled = true;
      statusEl.textContent = "Requesting mic…";
      statusEl.setAttribute("data-state", "listening");

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
          analyser.fftSize = 2048;
          buffer = new Float32Array(analyser.fftSize);
          source = audioCtx.createMediaStreamSource(stream);
          source.connect(analyser); // never connected to destination: nothing is played back
          running = true;
          startBtn.hidden = true;
          startBtn.disabled = false;
          stopBtn.hidden = false;
          rafId = requestAnimationFrame(loop);
        })
        .catch(function (err) {
          startBtn.disabled = false;
          if (err && err.name === "NotAllowedError") {
            showError("Microphone access was denied. Allow it in your browser's site settings to tune.");
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
      setIdle();
    }

    stopBtn.addEventListener("click", stopAll);

    // Release the mic if the user navigates away or switches homepage panels.
    window.addEventListener("beforeunload", stopAll);
    document.addEventListener("perfecttune:panel-shown", function (e) {
      if (running && e.detail.slug !== "tuner") stopAll();
    });

    stopBtn.hidden = true;
    setIdle();
  }

  document.addEventListener("DOMContentLoaded", initTuner);
})();
