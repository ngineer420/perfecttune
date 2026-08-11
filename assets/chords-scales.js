/*!
 * perfecttune.net — Chord & Scale Dictionary (cs-).
 * Nothing here is a stored chart: pick a root and a quality and the notes,
 * the piano keys and every position on the fretboard are all generated from
 * the interval formula by PerfectTuneTheory, which is why F# major shows
 * A# and E# rather than Bb and F. Playback goes through the shared engine
 * and only ever happens on a button press.
 */
(function () {
  "use strict";

  var SVG_NS = "http://www.w3.org/2000/svg";

  // Standard tuning, low to high: E2 A2 D3 G3 B3 E4.
  var GUITAR_STRINGS = [
    { midi: 40, label: "E" },
    { midi: 45, label: "A" },
    { midi: 50, label: "D" },
    { midi: 55, label: "G" },
    { midi: 59, label: "B" },
    { midi: 64, label: "E" }
  ];
  var FRETS = 12;

  function el(name, attrs, text) {
    var node = document.createElementNS(SVG_NS, name);
    for (var k in attrs) {
      if (Object.prototype.hasOwnProperty.call(attrs, k)) node.setAttribute(k, attrs[k]);
    }
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function initDictionary() {
    var rootSelect = document.getElementById("cs-root");
    if (!rootSelect) return;

    var Theory = window.PerfectTuneTheory;
    var Notes = window.PerfectTuneNotes;
    var Audio = window.PerfectTuneAudio;

    var typeSelect = document.getElementById("cs-type");
    var titleEl = document.getElementById("cs-title");
    var formulaEl = document.getElementById("cs-formula");
    var notesEl = document.getElementById("cs-notes");
    var pianoEl = document.getElementById("cs-piano");
    var fretEl = document.getElementById("cs-fretboard");
    var advisoryEl = document.getElementById("cs-advisory");
    var playBtn = document.getElementById("cs-play");
    var altBtn = document.getElementById("cs-alt-play");
    var statusEl = document.getElementById("cs-status");
    var statusTimer = null;
    var currentBuild = null;

    /* --------------------------------------------------------- selectors */
    Theory.ROOTS.forEach(function (r) {
      var opt = document.createElement("option");
      opt.value = r;
      opt.textContent = r;
      if (r === "C") opt.selected = true;
      rootSelect.appendChild(opt);
    });

    var chordGroup = document.createElement("optgroup");
    chordGroup.label = "Chords";
    Theory.CHORDS.forEach(function (c) {
      var opt = document.createElement("option");
      opt.value = "chord:" + c.id;
      opt.textContent = c.name;
      if (c.id === "major") opt.selected = true;
      chordGroup.appendChild(opt);
    });
    typeSelect.appendChild(chordGroup);

    ["Scales", "Modes"].forEach(function (groupName) {
      var group = document.createElement("optgroup");
      group.label = groupName;
      Theory.SCALES.forEach(function (s) {
        if (s.group !== groupName) return;
        var opt = document.createElement("option");
        opt.value = "scale:" + s.id;
        opt.textContent = s.name;
        group.appendChild(opt);
      });
      typeSelect.appendChild(group);
    });

    function selection() {
      var parts = typeSelect.value.split(":");
      var isChord = parts[0] === "chord";
      var spec = isChord ? Theory.chordById(parts[1]) : Theory.scaleById(parts[1]);
      return { isChord: isChord, spec: spec };
    }

    /* ------------------------------------------------------------ piano */
    var WHITE_PCS = [0, 2, 4, 5, 7, 9, 11];
    var BLACK_AFTER = [0, 1, 3, 4, 5]; // white-key index each black key sits after
    var BLACK_PCS = [1, 3, 6, 8, 10];

    function renderPiano(built) {
      pianoEl.innerHTML = "";
      var names = {};
      built.notes.forEach(function (n) {
        if (names[n.pc] === undefined) names[n.pc] = n.name;
      });
      var rootPc = built.notes[0].pc;

      var whiteW = 28,
        whiteH = 116,
        blackW = 17,
        blackH = 72,
        octaves = 2,
        pad = 2;
      var width = whiteW * 7 * octaves + pad * 2;
      var svg = el("svg", {
        viewBox: "0 0 " + width + " " + (whiteH + pad * 2),
        role: "img",
        "aria-label": "Piano keyboard with the notes of " + titleText(built) + " highlighted"
      });

      var o, i, pc, x;
      for (o = 0; o < octaves; o++) {
        for (i = 0; i < 7; i++) {
          pc = WHITE_PCS[i];
          x = pad + (o * 7 + i) * whiteW;
          var on = names[pc] !== undefined;
          svg.appendChild(
            el("rect", {
              x: x, y: pad, width: whiteW, height: whiteH, rx: 3,
              class: "pk-white" + (on ? " is-on" : "") + (on && pc === rootPc ? " is-root" : "")
            })
          );
          if (on) {
            svg.appendChild(
              el("text", {
                x: x + whiteW / 2, y: pad + whiteH - 12,
                class: "pk-label" + (pc === rootPc ? " on-root" : "")
              }, names[pc])
            );
          }
        }
      }
      for (o = 0; o < octaves; o++) {
        for (i = 0; i < BLACK_AFTER.length; i++) {
          pc = BLACK_PCS[i];
          x = pad + (o * 7 + BLACK_AFTER[i] + 1) * whiteW - blackW / 2;
          var onB = names[pc] !== undefined;
          svg.appendChild(
            el("rect", {
              x: x, y: pad, width: blackW, height: blackH, rx: 2,
              class: "pk-black" + (onB ? " is-on" : "") + (onB && pc === rootPc ? " is-root" : "")
            })
          );
          if (onB) {
            svg.appendChild(
              el("text", { x: x + blackW / 2, y: pad + blackH - 8, class: "pk-label is-black" }, names[pc])
            );
          }
        }
      }
      pianoEl.appendChild(svg);
    }

    /* -------------------------------------------------------- fretboard */
    function renderFretboard(built) {
      fretEl.innerHTML = "";
      var names = {};
      built.notes.forEach(function (n) {
        if (names[n.pc] === undefined) names[n.pc] = n.name;
      });
      var rootPc = built.notes[0].pc;

      var left = 34,
        top = 16,
        fretW = 50,
        stringGap = 24;
      var width = left + fretW * FRETS + 16;
      var height = top + stringGap * 5 + 34;
      var svg = el("svg", {
        viewBox: "0 0 " + width + " " + height,
        role: "img",
        "aria-label": "Guitar fretboard in standard tuning showing every position of " + titleText(built) + " in the first twelve frets"
      });

      svg.appendChild(
        el("rect", { x: left, y: top - 8, width: fretW * FRETS, height: stringGap * 5 + 16, rx: 4, class: "fb-face" })
      );

      // Inlays: single dots at 3, 5, 7, 9 and a double at 12.
      [3, 5, 7, 9].forEach(function (f) {
        svg.appendChild(el("circle", { cx: left + (f - 0.5) * fretW, cy: top + stringGap * 2.5, r: 4, class: "fb-inlay" }));
      });
      svg.appendChild(el("circle", { cx: left + 11.5 * fretW, cy: top + stringGap * 1.5, r: 4, class: "fb-inlay" }));
      svg.appendChild(el("circle", { cx: left + 11.5 * fretW, cy: top + stringGap * 3.5, r: 4, class: "fb-inlay" }));

      var f, s;
      for (f = 0; f <= FRETS; f++) {
        svg.appendChild(
          el("line", {
            x1: left + f * fretW, y1: top, x2: left + f * fretW, y2: top + stringGap * 5,
            class: f === 0 ? "fb-nut" : "fb-fret"
          })
        );
      }
      for (s = 0; s < GUITAR_STRINGS.length; s++) {
        var y = top + (GUITAR_STRINGS.length - 1 - s) * stringGap; // low E at the bottom
        svg.appendChild(el("line", { x1: left, y1: y, x2: left + fretW * FRETS, y2: y, class: "fb-string" }));

        // Fret 0 is the open string, drawn in the label column left of the nut.
        var openPc = ((GUITAR_STRINGS[s].midi % 12) + 12) % 12;
        if (names[openPc] !== undefined) {
          svg.appendChild(
            el("circle", { cx: left - 15, cy: y, r: 9.5, class: "fb-note" + (openPc === rootPc ? " is-root" : "") })
          );
          svg.appendChild(
            el("text", { x: left - 15, y: y + 3.5, class: "fb-note-label" + (openPc === rootPc ? " on-root" : "") }, names[openPc])
          );
        } else {
          svg.appendChild(el("text", { x: left - 15, y: y + 4, class: "fb-open" }, GUITAR_STRINGS[s].label));
        }

        for (f = 1; f <= FRETS; f++) {
          var pc = ((GUITAR_STRINGS[s].midi + f) % 12 + 12) % 12;
          if (names[pc] === undefined) continue;
          var cx = left + (f - 0.5) * fretW;
          svg.appendChild(
            el("circle", { cx: cx, cy: y, r: 10, class: "fb-note" + (pc === rootPc ? " is-root" : "") })
          );
          svg.appendChild(
            el("text", { x: cx, y: y + 3.5, class: "fb-note-label" + (pc === rootPc ? " on-root" : "") }, names[pc])
          );
        }
      }
      for (f = 1; f <= FRETS; f++) {
        svg.appendChild(
          el("text", { x: left + (f - 0.5) * fretW, y: top + stringGap * 5 + 24, class: "fb-fret-number" }, String(f))
        );
      }
      fretEl.appendChild(svg);
    }

    /* ------------------------------------------------------------ output */
    function typeLabel() {
      var name = selection().spec.name;
      return name.charAt(0).toLowerCase() + name.slice(1);
    }

    function titleText(built) {
      return built.rootName + " " + typeLabel();
    }

    function renderNotes(built) {
      notesEl.innerHTML = "";
      built.notes.forEach(function (n, i) {
        var chip = document.createElement("span");
        chip.className = "note-chip" + (i === 0 ? " is-root" : "");
        var name = document.createElement("span");
        name.className = "note-chip-name";
        name.textContent = n.name;
        var degree = document.createElement("span");
        degree.className = "note-chip-degree";
        degree.textContent = n.label;
        chip.appendChild(name);
        chip.appendChild(degree);
        notesEl.appendChild(chip);
      });
    }

    function update() {
      var sel = selection();
      var built = Theory.build(rootSelect.value, sel.spec);
      if (!built) return;
      currentBuild = built;

      titleEl.textContent = titleText(built);
      formulaEl.textContent =
        built.degreeFormula + "  ·  " + built.formula + " semitones from the root";
      renderNotes(built);
      renderPiano(built);
      renderFretboard(built);

      if (built.theoretical) {
        advisoryEl.hidden = false;
        advisoryEl.textContent =
          "Spelled strictly from the formula, " + titleText(built) + " needs double accidentals. " +
          "That spelling is correct but almost never written" +
          (built.enharmonicRoot ? " — in practice this is notated as " + built.enharmonicRoot + " " + typeLabel() + "." : ".");
      } else {
        advisoryEl.hidden = true;
        advisoryEl.textContent = "";
      }

      playBtn.textContent = sel.isChord ? "Play chord" : "Play scale";
      altBtn.textContent = sel.isChord ? "Play as arpeggio" : "Play descending";
    }

    /* ---------------------------------------------------------- playback */
    function midiList() {
      var root = currentBuild.root;
      var rootMidi = Theory.noteToMidi(root, 4); // C4 = 60; roots land in the C4–B4 region
      if (rootMidi > 71) rootMidi -= 12;
      if (rootMidi < 59) rootMidi += 12;
      var list = currentBuild.notes.map(function (n) {
        return rootMidi + n.semitones;
      });
      return { rootMidi: rootMidi, list: list };
    }

    function flash(seconds) {
      statusEl.textContent = "Playing";
      statusEl.setAttribute("data-state", "playing");
      if (statusTimer) window.clearTimeout(statusTimer);
      statusTimer = window.setTimeout(function () {
        statusEl.textContent = "Idle";
        statusEl.setAttribute("data-state", "idle");
      }, Math.max(seconds, 0.2) * 1000);
    }

    function freqs(midis) {
      return midis.map(function (m) {
        return Notes.midiToFreq(m, 440);
      });
    }

    function play(mode) {
      if (!Audio || !currentBuild) return;
      Audio.stopAll();
      var sel = selection();
      var m = midiList();
      var midis = m.list.slice();
      if (!sel.isChord) midis.push(m.rootMidi + 12); // finish the scale on the octave
      if (mode === "descending") midis.reverse();
      var seconds;
      if (sel.isChord && mode === "block") {
        seconds = Audio.sequence(freqs(midis), { spacing: 0, duration: 1.6, gain: 0.14 });
      } else {
        seconds = Audio.sequence(freqs(midis), { spacing: 0.34, duration: 0.32, gain: 0.2 });
      }
      flash(seconds);
    }

    playBtn.addEventListener("click", function () {
      play(selection().isChord ? "block" : "ascending");
    });
    altBtn.addEventListener("click", function () {
      play(selection().isChord ? "ascending" : "descending");
    });
    rootSelect.addEventListener("change", update);
    typeSelect.addEventListener("change", update);

    document.addEventListener("perfecttune:panel-shown", function (e) {
      if (e.detail.slug !== "chords-scales" && Audio) Audio.stopAll();
    });
    window.addEventListener("beforeunload", function () {
      if (Audio) Audio.stopAll();
    });

    update();
  }

  document.addEventListener("DOMContentLoaded", initDictionary);
})();
