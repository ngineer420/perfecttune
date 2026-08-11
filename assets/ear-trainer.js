/*!
 * perfecttune.net — Interval Ear Trainer (et-).
 * Plays two notes through the shared playback engine (audio.js) and asks
 * you to name the distance between them. Every interval name and semitone
 * count comes from PerfectTuneTheory.INTERVALS, and every pitch from
 * PerfectTuneNotes.midiToFreq, so the answer buttons and the sound you hear
 * are the same table. Nothing plays until a button is pressed.
 */
(function () {
  "use strict";

  // Question pools, each a filter over the one interval table — never a
  // second list of interval names that could drift from it.
  var SETS = [
    { id: "all", name: "Everything (unison to octave)", semitones: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] },
    { id: "starter", name: "Starter — 4th, 5th, octave", semitones: [5, 7, 12] },
    { id: "thirds-sixths", name: "Thirds & sixths", semitones: [3, 4, 8, 9] },
    { id: "seconds-sevenths", name: "Seconds & sevenths", semitones: [1, 2, 10, 11] },
    { id: "inside-octave", name: "Inside the octave (m2 to M7)", semitones: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11] }
  ];

  var DIRECTIONS = [
    { id: "ascending", name: "Ascending" },
    { id: "descending", name: "Descending" },
    { id: "harmonic", name: "Harmonic (both at once)" },
    { id: "mixed", name: "Mixed" }
  ];

  var ROOT_LOW = 57; // A3 — keeps a descending octave at A2 and an ascending one at A5
  var ROOT_HIGH = 69;

  function initEarTrainer() {
    var playBtn = document.getElementById("et-play");
    if (!playBtn) return;

    var Theory = window.PerfectTuneTheory;
    var Notes = window.PerfectTuneNotes;
    var Audio = window.PerfectTuneAudio;

    var replayBtn = document.getElementById("et-replay");
    var revealBtn = document.getElementById("et-reveal");
    var answersEl = document.getElementById("et-answers");
    var feedbackEl = document.getElementById("et-feedback");
    var statusEl = document.getElementById("et-status");
    var scoreEl = document.getElementById("et-score");
    var totalEl = document.getElementById("et-total");
    var streakEl = document.getElementById("et-streak");
    var setSelect = document.getElementById("et-set");
    var dirSelect = document.getElementById("et-direction");
    var toneSelect = document.getElementById("et-tone");

    var current = null; // { semitones, rootMidi, direction, answered, scored }
    var score = 0,
      total = 0,
      streak = 0,
      best = 0;
    var statusTimer = null;

    /* -------------------------------------------------- option population */
    SETS.forEach(function (s) {
      var opt = document.createElement("option");
      opt.value = s.id;
      opt.textContent = s.name;
      setSelect.appendChild(opt);
    });
    DIRECTIONS.forEach(function (d) {
      var opt = document.createElement("option");
      opt.value = d.id;
      opt.textContent = d.name;
      if (d.id === "ascending") opt.selected = true;
      dirSelect.appendChild(opt);
    });

    function activeSet() {
      for (var i = 0; i < SETS.length; i++) if (SETS[i].id === setSelect.value) return SETS[i];
      return SETS[0];
    }

    /* -------------------------------------------------- answer buttons */
    function renderAnswers() {
      answersEl.innerHTML = "";
      activeSet().semitones.forEach(function (st) {
        var iv = Theory.intervalBySemitones(st);
        if (!iv) return;
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "answer-btn";
        btn.setAttribute("data-semitones", String(st));
        btn.innerHTML =
          '<span class="answer-name">' + iv.name + "</span>" +
          '<span class="answer-sub">' + iv.short + " &middot; " + st + (st === 1 ? " semitone" : " semitones") + "</span>";
        btn.addEventListener("click", function () {
          answer(st, btn);
        });
        answersEl.appendChild(btn);
      });
    }

    function clearMarks() {
      Array.prototype.forEach.call(answersEl.children, function (b) {
        b.classList.remove("is-right", "is-wrong");
      });
    }

    function markCorrect() {
      Array.prototype.forEach.call(answersEl.children, function (b) {
        if (Number(b.getAttribute("data-semitones")) === current.semitones) b.classList.add("is-right");
      });
    }

    /* -------------------------------------------------- status + score */
    function setStatus(text, state) {
      statusEl.textContent = text;
      statusEl.setAttribute("data-state", state);
    }

    function flashPlaying(seconds) {
      setStatus("Playing", "playing");
      if (statusTimer) window.clearTimeout(statusTimer);
      statusTimer = window.setTimeout(function () {
        setStatus(current && !current.answered ? "Your turn" : "Idle", current && !current.answered ? "listening" : "idle");
      }, Math.max(seconds, 0.2) * 1000);
    }

    function renderScore() {
      scoreEl.textContent = String(score);
      totalEl.textContent = String(total);
      streakEl.textContent = streak + (best > 0 ? " (best " + best + ")" : "");
    }

    /* -------------------------------------------------- playback */
    function directionFor() {
      var d = dirSelect.value;
      if (d !== "mixed") return d;
      var pool = ["ascending", "descending", "harmonic"];
      return pool[Math.floor(Math.random() * pool.length)];
    }

    function play() {
      if (!current || !Audio) return;
      Audio.stopAll();
      var rootFreq = Notes.midiToFreq(current.rootMidi, 440);
      var otherMidi =
        current.direction === "descending" ? current.rootMidi - current.semitones : current.rootMidi + current.semitones;
      var otherFreq = Notes.midiToFreq(otherMidi, 440);
      var type = toneSelect ? toneSelect.value : "triangle";
      var seconds;
      if (current.direction === "harmonic") {
        seconds = Audio.sequence([rootFreq, otherFreq], { spacing: 0, duration: 1.5, type: type, gain: 0.18 });
      } else {
        seconds = Audio.sequence([rootFreq, otherFreq], { spacing: 0.62, duration: 0.58, type: type, gain: 0.22 });
      }
      flashPlaying(seconds);
    }

    function newQuestion() {
      var pool = activeSet().semitones;
      var semitones = pool[Math.floor(Math.random() * pool.length)];
      var root = ROOT_LOW + Math.floor(Math.random() * (ROOT_HIGH - ROOT_LOW + 1));
      current = { semitones: semitones, rootMidi: root, direction: directionFor(), answered: false, scored: false };
      clearMarks();
      replayBtn.disabled = false;
      revealBtn.disabled = false;
      playBtn.textContent = "New interval";
      feedbackEl.textContent = "Which interval was that?";
      play();
    }

    /* -------------------------------------------------- answering */
    function answer(semitones, btn) {
      if (!current) {
        feedbackEl.textContent = "Press Play interval first — there is nothing to name yet.";
        return;
      }
      var iv = Theory.intervalBySemitones(semitones);
      var right = semitones === current.semitones;
      // A question is scored once, on the first attempt — further guesses and a
      // later reveal must not count again.
      if (!current.scored) {
        current.scored = true;
        total += 1;
        if (right) {
          score += 1;
          streak += 1;
          if (streak > best) best = streak;
        } else {
          streak = 0;
        }
        renderScore();
      }
      if (right) {
        current.answered = true;
        btn.classList.add("is-right");
        var actual = Theory.intervalBySemitones(current.semitones);
        feedbackEl.textContent =
          "Correct — " + actual.name + ", " + actual.semitones + (actual.semitones === 1 ? " semitone" : " semitones") +
          ". Press New interval to keep going.";
        setStatus("Correct", "playing");
        revealBtn.disabled = true;
      } else {
        btn.classList.add("is-wrong");
        feedbackEl.textContent =
          "Not " + iv.name + " — listen again, or press Reveal to see the answer.";
      }
    }

    function reveal() {
      if (!current || current.answered) return;
      if (!current.scored) {
        // Giving up counts as a miss, so the score stays honest.
        current.scored = true;
        total += 1;
        streak = 0;
        renderScore();
      }
      current.answered = true;
      var iv = Theory.intervalBySemitones(current.semitones);
      markCorrect();
      var dirText =
        current.direction === "harmonic" ? "played together" : current.direction;
      feedbackEl.textContent =
        "It was a " + iv.name + " (" + iv.semitones + (iv.semitones === 1 ? " semitone" : " semitones") + ", " + dirText + ").";
      revealBtn.disabled = true;
      setStatus("Revealed", "idle");
    }

    /* -------------------------------------------------- wiring */
    playBtn.addEventListener("click", newQuestion);
    replayBtn.addEventListener("click", play);
    revealBtn.addEventListener("click", reveal);

    setSelect.addEventListener("change", function () {
      current = null;
      replayBtn.disabled = true;
      revealBtn.disabled = true;
      playBtn.textContent = "Play interval";
      renderAnswers();
      feedbackEl.textContent = "Interval set changed — press Play interval for a new question.";
      if (Audio) Audio.stopAll();
      setStatus("Idle", "idle");
    });

    document.addEventListener("perfecttune:panel-shown", function (e) {
      if (e.detail.slug !== "ear-trainer" && Audio) Audio.stopAll();
    });
    window.addEventListener("beforeunload", function () {
      if (Audio) Audio.stopAll();
    });

    renderAnswers();
    renderScore();
    replayBtn.disabled = true;
    revealBtn.disabled = true;
  }

  document.addEventListener("DOMContentLoaded", initEarTrainer);
})();
