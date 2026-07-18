/*!
 * perfecttune.net — Tone Generator (tg-).
 * A drone oscillator (sine/square/triangle/sawtooth) feeding an
 * AnalyserNode so the on-page oscilloscope draws the real, currently
 * playing waveform rather than a decorative loop. AudioContext + the
 * oscillator are only created inside the Start button's click handler.
 */
(function () {
  "use strict";

  var Notes = window.PerfectTuneNotes;

  function initToneGenerator() {
    var startBtn = document.getElementById("tg-start");
    if (!startBtn) return;
    var waveButtons = Array.prototype.slice.call(document.querySelectorAll(".wave-btn"));
    var freqInput = document.getElementById("tg-freq");
    var freqSlider = document.getElementById("tg-freq-slider");
    var noteSelect = document.getElementById("tg-note");
    var volumeSlider = document.getElementById("tg-volume");
    var statusEl = document.getElementById("tg-status");
    var freqReadout = document.getElementById("tg-freq-readout");
    var canvas = document.getElementById("tg-scope");
    var ctx2d = canvas ? canvas.getContext("2d") : null;

    var audioCtx = null,
      osc = null,
      gainNode = null,
      analyser = null,
      dataArray = null,
      rafId = null,
      playing = false;
    var waveform = "sine";
    var freq = 440;
    var volume = 0.4;

    /* ---------------------------------------------------------- note list */
    if (noteSelect && Notes) {
      var notes = Notes.buildNoteList(440);
      notes.forEach(function (n) {
        var opt = document.createElement("option");
        opt.value = n.freq.toFixed(3);
        opt.textContent = n.label + " — " + n.freq.toFixed(1) + " Hz";
        if (n.label === "A4") opt.selected = true;
        noteSelect.appendChild(opt);
      });
    }

    /* ---------------------------------------------------------- canvas */
    function resizeCanvas() {
      if (!canvas) return;
      var dpr = window.devicePixelRatio || 1;
      var w = canvas.clientWidth,
        h = canvas.clientHeight || 120;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx2d.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function strokeColor() {
      var v = getComputedStyle(document.documentElement).getPropertyValue("--ember-500");
      return v ? v.trim() : "#c8461f";
    }

    function shapeValue(type, phase) {
      // phase in 0..1 (one cycle)
      var t = phase - Math.floor(phase);
      if (type === "sine") return Math.sin(t * Math.PI * 2);
      if (type === "square") return t < 0.5 ? 1 : -1;
      if (type === "sawtooth") return 2 * (t - Math.floor(t + 0.5));
      // triangle
      return 2 * Math.abs(2 * (t - Math.floor(t + 0.5))) - 1;
    }

    function drawStatic() {
      if (!ctx2d) return;
      var w = canvas.clientWidth,
        h = canvas.clientHeight || 120;
      ctx2d.clearRect(0, 0, w, h);
      ctx2d.beginPath();
      var cycles = 3;
      for (var x = 0; x <= w; x++) {
        var v = shapeValue(waveform, (x / w) * cycles);
        var y = h / 2 - v * (h / 2 - 10);
        if (x === 0) ctx2d.moveTo(x, y);
        else ctx2d.lineTo(x, y);
      }
      ctx2d.strokeStyle = strokeColor();
      ctx2d.lineWidth = 2;
      ctx2d.globalAlpha = 0.55;
      ctx2d.stroke();
      ctx2d.globalAlpha = 1;
    }

    function drawLive() {
      if (!playing || !ctx2d) return;
      analyser.getFloatTimeDomainData(dataArray);
      var w = canvas.clientWidth,
        h = canvas.clientHeight || 120;
      ctx2d.clearRect(0, 0, w, h);
      ctx2d.beginPath();
      var sliceWidth = w / dataArray.length;
      var x = 0;
      for (var i = 0; i < dataArray.length; i++) {
        var v = dataArray[i];
        var y = h / 2 - v * (h / 2 - 10);
        if (i === 0) ctx2d.moveTo(x, y);
        else ctx2d.lineTo(x, y);
        x += sliceWidth;
      }
      ctx2d.strokeStyle = strokeColor();
      ctx2d.lineWidth = 2;
      ctx2d.stroke();
      rafId = requestAnimationFrame(drawLive);
    }

    /* ---------------------------------------------------------- audio */
    function getAudioCtx() {
      if (!audioCtx) {
        var AC = window.AudioContext || window.webkitAudioContext;
        audioCtx = new AC();
      }
      if (audioCtx.state === "suspended") audioCtx.resume();
      return audioCtx;
    }

    function updateReadout() {
      freqReadout.textContent = freq.toFixed(1);
    }

    function start() {
      getAudioCtx();
      osc = audioCtx.createOscillator();
      gainNode = audioCtx.createGain();
      analyser = audioCtx.createAnalyser();
      analyser.fftSize = 1024;
      dataArray = new Float32Array(analyser.fftSize);
      osc.type = waveform;
      osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
      gainNode.gain.setValueAtTime(0.0001, audioCtx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(Math.max(volume, 0.0001), audioCtx.currentTime + 0.06);
      osc.connect(gainNode);
      gainNode.connect(analyser);
      analyser.connect(audioCtx.destination);
      osc.start();
      playing = true;
      startBtn.textContent = "Stop";
      startBtn.classList.remove("primary");
      startBtn.classList.add("stop");
      statusEl.textContent = "Playing";
      statusEl.setAttribute("data-state", "playing");
      rafId = requestAnimationFrame(drawLive);
    }

    function stop() {
      if (osc && gainNode && audioCtx) {
        var t = audioCtx.currentTime;
        gainNode.gain.cancelScheduledValues(t);
        gainNode.gain.setValueAtTime(gainNode.gain.value, t);
        gainNode.gain.exponentialRampToValueAtTime(0.0001, t + 0.05);
        var deadOsc = osc;
        window.setTimeout(function () {
          try {
            deadOsc.stop();
          } catch (e) {}
        }, 90);
      }
      playing = false;
      osc = null;
      gainNode = null;
      if (rafId) cancelAnimationFrame(rafId);
      startBtn.textContent = "Play";
      startBtn.classList.remove("stop");
      startBtn.classList.add("primary");
      statusEl.textContent = "Idle";
      statusEl.setAttribute("data-state", "idle");
      drawStatic();
    }

    startBtn.addEventListener("click", function () {
      if (playing) stop();
      else start();
    });

    waveButtons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        waveform = btn.getAttribute("data-wave");
        waveButtons.forEach(function (b) {
          b.setAttribute("aria-pressed", String(b === btn));
        });
        if (playing && osc) osc.type = waveform;
        if (!playing) drawStatic();
      });
    });

    function setFreq(v, fromNote) {
      freq = Math.max(20, Math.min(5000, v));
      freqInput.value = freq.toFixed(1);
      freqSlider.value = Math.round(Math.log2(freq) * 100);
      updateReadout();
      if (!fromNote) noteSelect.value = "";
      if (playing && osc) osc.frequency.setTargetAtTime(freq, audioCtx.currentTime, 0.01);
    }

    freqInput.addEventListener("input", function () {
      var v = Number(freqInput.value);
      if (!isNaN(v) && v > 0) setFreq(v, false);
    });
    freqSlider.addEventListener("input", function () {
      var v = Math.pow(2, Number(freqSlider.value) / 100);
      setFreq(v, false);
    });
    if (noteSelect) {
      noteSelect.addEventListener("change", function () {
        var v = Number(noteSelect.value);
        if (!isNaN(v) && v > 0) setFreq(v, true);
      });
    }

    volumeSlider.addEventListener("input", function () {
      volume = Number(volumeSlider.value) / 100;
      if (playing && gainNode) gainNode.gain.setTargetAtTime(volume, audioCtx.currentTime, 0.01);
    });

    document.addEventListener("perfecttune:panel-shown", function (e) {
      if (playing && e.detail.slug !== "tone-generator") stop();
      if (e.detail.slug === "tone-generator") {
        resizeCanvas();
        drawStatic();
      }
    });
    window.addEventListener("resize", function () {
      resizeCanvas();
      if (!playing) drawStatic();
    });
    window.addEventListener("beforeunload", function () {
      if (rafId) cancelAnimationFrame(rafId);
    });

    updateReadout();
    freqSlider.value = Math.round(Math.log2(freq) * 100);
    volumeSlider.value = Math.round(volume * 100);
    // Canvas may be in a hidden panel on first load (homepage); size it once
    // visible via a rAF (hidden elements report 0 clientWidth).
    requestAnimationFrame(function () {
      resizeCanvas();
      drawStatic();
    });
  }

  document.addEventListener("DOMContentLoaded", initToneGenerator);
})();
