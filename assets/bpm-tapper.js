/*!
 * perfecttune.net — BPM Tapper / tap tempo (bt-).
 * Tap the pad (or press space with it focused) and the tempo is the average
 * of the intervals between your last several taps, exactly as the
 * metronome's own Tap Tempo button works. The steadiness figure is the
 * standard deviation of those intervals, so you can see whether the number
 * is a real tempo or a guess. The optional click is opt-in and only ever
 * fires from your own tap.
 */
(function () {
  "use strict";

  var WINDOW = 12; // taps averaged
  var RESET_AFTER_MS = 2200; // a gap longer than this starts a new measurement

  function initTapper() {
    var pad = document.getElementById("bt-pad");
    if (!pad) return;

    var Audio = window.PerfectTuneAudio;
    var bpmEl = document.getElementById("bt-bpm");
    var tapsEl = document.getElementById("bt-taps");
    var msEl = document.getElementById("bt-ms");
    var steadyEl = document.getElementById("bt-steady");
    var noteValuesEl = document.getElementById("bt-note-values");
    var resetBtn = document.getElementById("bt-reset");
    var sendLink = document.getElementById("bt-send");
    var clickToggle = document.getElementById("bt-click");
    var statusEl = document.getElementById("bt-status");
    var roundedEl = document.getElementById("bt-rounded");

    var taps = [];
    var bpm = null;

    function setStatus(text, state) {
      statusEl.textContent = text;
      statusEl.setAttribute("data-state", state);
    }

    function render() {
      tapsEl.textContent = taps.length ? String(taps.length) : "—";
      if (bpm === null) {
        bpmEl.textContent = "—";
        msEl.textContent = "—";
        steadyEl.textContent = "—";
        roundedEl.textContent = "Tap at least twice.";
        noteValuesEl.textContent = "";
        sendLink.setAttribute("aria-disabled", "true");
        sendLink.removeAttribute("href");
        return;
      }
      var beatMs = 60000 / bpm;
      bpmEl.textContent = bpm.toFixed(1);
      msEl.textContent = beatMs.toFixed(1) + " ms";
      roundedEl.textContent = "Nearest whole tempo: " + Math.round(bpm) + " BPM";
      noteValuesEl.textContent =
        "Quarter " + beatMs.toFixed(0) + " ms · eighth " + (beatMs / 2).toFixed(0) +
        " ms · dotted eighth " + (beatMs * 0.75).toFixed(0) + " ms · half " + (beatMs * 2).toFixed(0) + " ms";
      sendLink.setAttribute("href", "/metronome/?bpm=" + Math.round(bpm));
      sendLink.removeAttribute("aria-disabled");
    }

    function intervals() {
      var out = [];
      for (var i = 1; i < taps.length; i++) out.push(taps[i] - taps[i - 1]);
      return out;
    }

    function recompute() {
      var iv = intervals();
      if (!iv.length) {
        bpm = null;
        steadyEl.textContent = "—";
        render();
        return;
      }
      var sum = iv.reduce(function (a, b) { return a + b; }, 0);
      var mean = sum / iv.length;
      bpm = 60000 / mean;
      render();
      if (iv.length < 2) {
        steadyEl.textContent = "—";
        return;
      }
      var variance = iv.reduce(function (a, b) { return a + (b - mean) * (b - mean); }, 0) / iv.length;
      var sd = Math.sqrt(variance);
      steadyEl.textContent = "± " + sd.toFixed(0) + " ms";
    }

    function tap() {
      var now = performance.now();
      if (taps.length && now - taps[taps.length - 1] > RESET_AFTER_MS) taps = [];
      taps.push(now);
      if (taps.length > WINDOW) taps.shift();
      recompute();
      setStatus(taps.length > 1 ? "Counting" : "Listening…", "running");
      pad.classList.add("is-hit");
      window.setTimeout(function () {
        pad.classList.remove("is-hit");
      }, 90);
      if (clickToggle && clickToggle.checked && Audio) {
        Audio.note({ freq: 1200, duration: 0.02, gain: 0.28, type: "square" });
      }
    }

    function reset() {
      taps = [];
      bpm = null;
      render();
      setStatus("Idle", "idle");
    }

    pad.addEventListener("click", tap);
    resetBtn.addEventListener("click", reset);

    // Space anywhere on the page taps too, as long as the tool is on screen
    // and you are not typing in a field.
    document.addEventListener("keydown", function (e) {
      if (e.code !== "Space" && e.key !== " ") return;
      if (e.target === pad) return; // the button's own activation already fires click
      var tag = e.target && e.target.tagName ? e.target.tagName.toLowerCase() : "";
      if (tag === "input" || tag === "textarea" || tag === "select" || tag === "button" || tag === "a") return;
      if (!pad.offsetParent && pad.offsetHeight === 0) return; // hidden homepage panel
      e.preventDefault();
      tap();
    });

    render();
  }

  document.addEventListener("DOMContentLoaded", initTapper);
})();
