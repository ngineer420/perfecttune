/*!
 * perfecttune.net — Chord Transposer (tr-).
 * Moves a progression by a number of semitones and spells the result.
 *
 * Enharmonic convention (stated on the page, implemented in theory.js):
 *   Auto    — every root is spelled as the nearest spelling to the target
 *             key on the circle of fifths. Up 3 from C gives Eb, not D#;
 *             the same transposition of a Gb progression keeps Cb rather
 *             than swapping to B mid-progression.
 *   Sharps  — the chromatic scale spelled C C# D D# E F F# G G# A A# B.
 *   Flats   — the chromatic scale spelled C Db D Eb E F Gb G Ab A Bb B.
 *
 * Quality suffixes are never interpreted: m7b5, add9, 13#11 and anything
 * else come out exactly as typed, only the letters move.
 */
(function () {
  "use strict";

  function initTransposer() {
    var input = document.getElementById("tr-input");
    if (!input) return;

    var Theory = window.PerfectTuneTheory;
    var stepSelect = document.getElementById("tr-semitones");
    var spellingSelect = document.getElementById("tr-spelling");
    var chipsEl = document.getElementById("tr-chips");
    var textEl = document.getElementById("tr-text");
    var summaryEl = document.getElementById("tr-summary");
    var noteEl = document.getElementById("tr-note");
    var copyBtn = document.getElementById("tr-copy");
    var downBtn = document.getElementById("tr-down");
    var upBtn = document.getElementById("tr-up");

    /* ------------------------------------------------- semitone selector */
    for (var n = -12; n <= 12; n++) {
      var opt = document.createElement("option");
      opt.value = String(n);
      if (n === 0) {
        opt.textContent = "0 — no change";
      } else {
        var iv = Theory.intervalBySemitones(Math.abs(n));
        opt.textContent =
          (n > 0 ? "+" : "−") + Math.abs(n) + " — " + iv.name.toLowerCase() + (n > 0 ? " up" : " down");
      }
      if (n === 0) opt.selected = true;
      stepSelect.appendChild(opt);
    }

    function steps() {
      return Number(stepSelect.value) || 0;
    }

    function keyNameFromFifths(K) {
      // Undo the relative-major shift only for display of the sharp/flat count.
      return (K === 0 ? "no sharps or flats" : Math.abs(K) + (Math.abs(K) === 1 ? (K > 0 ? " sharp" : " flat") : K > 0 ? " sharps" : " flats"));
    }

    function update() {
      var semis = steps();
      var spelling = spellingSelect.value;
      var raw = input.value;
      var tokens = raw.split(/(\s+)/);
      var firstChord = null;
      tokens.forEach(function (t) {
        if (firstChord === null && /^[A-Ga-g]/.test(t)) firstChord = t;
      });
      var K = firstChord ? Theory.targetKeyFifths(firstChord, semis) : 0;

      var outParts = [];
      var pairs = [];
      var passed = [];
      tokens.forEach(function (t) {
        if (/^\s*$/.test(t)) {
          outParts.push(t);
          return;
        }
        var moved = /^[A-Ga-g]/.test(t) ? Theory.transposeSymbol(t, semis, spelling, K) : null;
        if (moved === null) {
          outParts.push(t);
          if (passed.indexOf(t) === -1) passed.push(t);
          return;
        }
        outParts.push(moved);
        pairs.push({ from: t, to: moved });
      });

      var outText = outParts.join("");
      textEl.value = outText;

      chipsEl.innerHTML = "";
      pairs.forEach(function (p) {
        // Built as text nodes, never as HTML: a chord's quality suffix is
        // whatever the user typed and is copied through verbatim.
        var chip = document.createElement("span");
        chip.className = "chord-chip";
        var to = document.createElement("span");
        to.className = "chord-chip-to";
        to.textContent = p.to;
        var from = document.createElement("span");
        from.className = "chord-chip-from";
        from.textContent = "was " + p.from;
        chip.appendChild(to);
        chip.appendChild(from);
        chipsEl.appendChild(chip);
      });

      if (!pairs.length) {
        summaryEl.textContent = "Type some chord symbols above — for example: C  Am  F  G7";
      } else if (semis === 0) {
        summaryEl.textContent =
          pairs.length + (pairs.length === 1 ? " chord" : " chords") +
          ", unchanged — pick a number of semitones to move them.";
      } else {
        var iv = Theory.intervalBySemitones(Math.abs(semis));
        var direction = semis > 0 ? "up" : "down";
        var spellText =
          spelling === "sharps"
            ? "spelled with sharps"
            : spelling === "flats"
            ? "spelled with flats"
            : "spelled for a key of " + keyNameFromFifths(K);
        summaryEl.textContent =
          pairs[0].from + " → " + pairs[0].to + " · " + direction + " " + Math.abs(semis) +
          (Math.abs(semis) === 1 ? " semitone" : " semitones") + " (" + iv.name.toLowerCase() + ") · " + spellText + ".";
      }

      noteEl.hidden = passed.length === 0;
      if (passed.length) {
        noteEl.textContent =
          "Left untouched (not a chord symbol): " + passed.slice(0, 8).join("  ") +
          (passed.length > 8 ? " …" : "");
      }
    }

    function nudge(by) {
      var next = Math.max(-12, Math.min(12, steps() + by));
      stepSelect.value = String(next);
      update();
    }

    input.addEventListener("input", update);
    stepSelect.addEventListener("change", update);
    spellingSelect.addEventListener("change", update);
    downBtn.addEventListener("click", function () {
      nudge(-1);
    });
    upBtn.addEventListener("click", function () {
      nudge(1);
    });

    copyBtn.addEventListener("click", function () {
      var done = function () {
        copyBtn.textContent = "Copied";
        window.setTimeout(function () {
          copyBtn.textContent = "Copy result";
        }, 1400);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(textEl.value).then(done, function () {
          textEl.select();
        });
      } else {
        textEl.select();
        try {
          document.execCommand("copy");
          done();
        } catch (e) {}
      }
    });

    update();
  }

  document.addEventListener("DOMContentLoaded", initTransposer);
})();
