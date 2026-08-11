/*!
 * perfecttune.net — shared music theory: the interval table, chord and
 * scale formulas, correct note spelling, and chord-symbol transposition.
 *
 * Everything here is derived, never stored as a lookup of finished answers:
 * a chord is a list of semitone offsets plus the scale degree each offset
 * belongs to, and the note name falls out of those two numbers. That is why
 * F# major spells its third A# and its seventh E# rather than Bb and F —
 * the letter comes from the degree, the accidental from the arithmetic.
 *
 * Pitch is equal temperament with A4 = 440 Hz; frequencies come from
 * PerfectTuneNotes.midiToFreq (notes.js), which is the single implementation
 * of 440 * 2^((n-69)/12) on the site.
 */
(function (global) {
  "use strict";

  var LETTERS = ["C", "D", "E", "F", "G", "A", "B"];
  var LETTER_SEMITONES = [0, 2, 4, 5, 7, 9, 11];
  // Each natural letter's position on the circle of fifths (F=-1, C=0, G=1,
  // D=2, A=3, E=4, B=5). One sharp moves a note seven fifths sharpwards.
  var LETTER_FIFTHS = [0, 2, 4, -1, 1, 3, 5];
  var MAJOR = [0, 2, 4, 5, 7, 9, 11];

  /* ------------------------------------------------------------ intervals */
  // Semitone counts are definitional. letterSteps is how many letter names
  // the interval spans (a 3rd moves two letters), which is what makes the
  // spelling of a transposed or stacked note come out right. The tritone is
  // spelled as an augmented 4th (three letter steps).
  var INTERVALS = [
    { semitones: 0, name: "Unison", short: "P1", letterSteps: 0 },
    { semitones: 1, name: "Minor 2nd", short: "m2", letterSteps: 1 },
    { semitones: 2, name: "Major 2nd", short: "M2", letterSteps: 1 },
    { semitones: 3, name: "Minor 3rd", short: "m3", letterSteps: 2 },
    { semitones: 4, name: "Major 3rd", short: "M3", letterSteps: 2 },
    { semitones: 5, name: "Perfect 4th", short: "P4", letterSteps: 3 },
    { semitones: 6, name: "Tritone", short: "TT", letterSteps: 3 },
    { semitones: 7, name: "Perfect 5th", short: "P5", letterSteps: 4 },
    { semitones: 8, name: "Minor 6th", short: "m6", letterSteps: 5 },
    { semitones: 9, name: "Major 6th", short: "M6", letterSteps: 5 },
    { semitones: 10, name: "Minor 7th", short: "m7", letterSteps: 6 },
    { semitones: 11, name: "Major 7th", short: "M7", letterSteps: 6 },
    { semitones: 12, name: "Octave", short: "P8", letterSteps: 7 }
  ];

  function intervalBySemitones(n) {
    for (var i = 0; i < INTERVALS.length; i++) {
      if (INTERVALS[i].semitones === n) return INTERVALS[i];
    }
    return null;
  }

  /* --------------------------------------------------------------- chords */
  // semitones: offsets from the root. degrees: letter steps for each of those
  // offsets (0 = root, 2 = a third, 4 = a fifth, 6 = a seventh).
  var CHORDS = [
    { id: "major", name: "Major", symbol: "", semitones: [0, 4, 7], degrees: [0, 2, 4] },
    { id: "minor", name: "Minor", symbol: "m", semitones: [0, 3, 7], degrees: [0, 2, 4] },
    { id: "dim", name: "Diminished", symbol: "dim", semitones: [0, 3, 6], degrees: [0, 2, 4] },
    { id: "aug", name: "Augmented", symbol: "aug", semitones: [0, 4, 8], degrees: [0, 2, 4] },
    { id: "dom7", name: "Dominant 7th", symbol: "7", semitones: [0, 4, 7, 10], degrees: [0, 2, 4, 6] },
    { id: "maj7", name: "Major 7th", symbol: "maj7", semitones: [0, 4, 7, 11], degrees: [0, 2, 4, 6] },
    { id: "min7", name: "Minor 7th", symbol: "m7", semitones: [0, 3, 7, 10], degrees: [0, 2, 4, 6] },
    { id: "sus2", name: "Sus2", symbol: "sus2", semitones: [0, 2, 7], degrees: [0, 1, 4] },
    { id: "sus4", name: "Sus4", symbol: "sus4", semitones: [0, 5, 7], degrees: [0, 3, 4] }
  ];

  /* --------------------------------------------------------------- scales */
  // A mode is the major scale started from a different degree, so the seven
  // modes are rotations rather than seven hand-typed rows that could drift.
  function rotateMode(n) {
    var out = [];
    for (var i = 0; i < 7; i++) out.push(mod(MAJOR[(i + n) % 7] - MAJOR[n], 12));
    return out;
  }

  var SCALES = [
    { id: "major", name: "Major (Ionian)", group: "Scales", semitones: MAJOR.slice() },
    { id: "natural-minor", name: "Natural minor (Aeolian)", group: "Scales", semitones: [0, 2, 3, 5, 7, 8, 10] },
    { id: "harmonic-minor", name: "Harmonic minor", group: "Scales", semitones: [0, 2, 3, 5, 7, 8, 11] },
    { id: "melodic-minor", name: "Melodic minor (ascending)", group: "Scales", semitones: [0, 2, 3, 5, 7, 9, 11] },
    { id: "ionian", name: "Ionian", group: "Modes", semitones: rotateMode(0) },
    { id: "dorian", name: "Dorian", group: "Modes", semitones: rotateMode(1) },
    { id: "phrygian", name: "Phrygian", group: "Modes", semitones: rotateMode(2) },
    { id: "lydian", name: "Lydian", group: "Modes", semitones: rotateMode(3) },
    { id: "mixolydian", name: "Mixolydian", group: "Modes", semitones: rotateMode(4) },
    { id: "aeolian", name: "Aeolian", group: "Modes", semitones: rotateMode(5) },
    { id: "locrian", name: "Locrian", group: "Modes", semitones: rotateMode(6) }
  ];

  SCALES.forEach(function (s) {
    s.degrees = [0, 1, 2, 3, 4, 5, 6]; // every scale here is heptatonic: one note per letter
  });

  /* ---------------------------------------------------------- note spelling */
  function mod(n, m) {
    return ((n % m) + m) % m;
  }

  function rep(s, n) {
    var out = "";
    for (var i = 0; i < n; i++) out += s;
    return out;
  }

  function accidentalText(alter) {
    if (alter === 0) return "";
    return alter > 0 ? rep("#", alter) : rep("b", -alter);
  }

  function noteName(note) {
    return LETTERS[note.letter] + accidentalText(note.alter);
  }

  function pitchClass(note) {
    return mod(LETTER_SEMITONES[note.letter] + note.alter, 12);
  }

  // Absolute MIDI number for a spelled note in a given octave (C4 = 60).
  function noteToMidi(note, octave) {
    return 12 * (octave + 1) + LETTER_SEMITONES[note.letter] + note.alter;
  }

  function parseNote(str) {
    // Longest alternatives first, or "F♯♯" would match a single ♯ and then fail.
    var m = /^([A-Ga-g])(##|bb|♯♯|♭♭|x|#|b|♯|♭)?$/.exec(String(str).trim());
    if (!m) return null;
    var letter = LETTERS.indexOf(m[1].toUpperCase());
    var acc = m[2] || "";
    var alter = 0;
    if (acc === "x") alter = 2;
    else {
      for (var i = 0; i < acc.length; i++) {
        var c = acc.charAt(i);
        if (c === "#" || c === "♯") alter += 1;
        else if (c === "b" || c === "♭") alter -= 1;
      }
    }
    return { letter: letter, alter: alter };
  }

  // The note a given number of letter steps and semitones above a root. The
  // letter comes from the degree; the accidental is whatever it takes to land
  // on the requested semitone. This is the whole spelling engine.
  function spell(root, letterSteps, semitones) {
    var idx = root.letter + letterSteps;
    var letter = mod(idx, 7);
    var octaves = Math.floor(idx / 7);
    var natural = LETTER_SEMITONES[letter] + 12 * octaves;
    var target = LETTER_SEMITONES[root.letter] + root.alter + semitones;
    return { letter: letter, alter: target - natural };
  }

  // "1", "b3", "#5", "b7" — derived by comparing the offset with the major
  // scale's offset for the same degree, never typed out by hand.
  function degreeLabel(degree, semitones) {
    var octaves = Math.floor(degree / 7);
    var diff = semitones - MAJOR[degree % 7] - 12 * octaves;
    return (diff === 0 ? "" : diff > 0 ? rep("#", diff) : rep("b", -diff)) + (degree + 1);
  }

  /* --------------------------------------------------- circle-of-fifths tools */
  // How many sharps (positive) or flats (negative) the major key on this note
  // carries: C = 0, G = 1, F = -1, F# = 6, Gb = -6.
  function keyFifths(note) {
    return LETTER_FIFTHS[note.letter] + 7 * note.alter;
  }

  function spellingsFor(pc) {
    var out = [];
    for (var letter = 0; letter < 7; letter++) {
      var alter = mod(pc - LETTER_SEMITONES[letter] + 6, 12) - 6;
      if (Math.abs(alter) <= 2) out.push({ letter: letter, alter: alter });
    }
    return out;
  }

  // The spelling of a pitch class with the fewest accidentals in its key
  // signature — Eb over D#, Bb over A#. Six-a-side ties (F#/Gb) go sharp.
  function autoSpell(pc) {
    var best = null,
      bestF = 0;
    spellingsFor(pc).forEach(function (n) {
      var f = keyFifths(n);
      if (best === null || Math.abs(f) < Math.abs(bestF) || (Math.abs(f) === Math.abs(bestF) && f > bestF)) {
        best = n;
        bestF = f;
      }
    });
    return best;
  }

  // The spelling of a pitch class nearest a given key on the circle of fifths.
  // In F# major (K = 6) pitch class 11 spells B; in Gb major (K = -6) the same
  // pitch class spells Cb. Ties go to the sharper spelling.
  function spellInKey(pc, K) {
    var best = null,
      bestF = 0;
    spellingsFor(pc).forEach(function (n) {
      var f = keyFifths(n);
      if (best === null || Math.abs(f - K) < Math.abs(bestF - K) || (Math.abs(f - K) === Math.abs(bestF - K) && f > bestF)) {
        best = n;
        bestF = f;
      }
    });
    return best;
  }

  var SHARP_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
  var FLAT_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"];

  /* ------------------------------------------------- chord / scale building */
  // Roots offered by the dictionary: the twelve pitch classes, with both
  // spellings wherever both are in common use.
  var ROOTS = ["C", "C#", "Db", "D", "D#", "Eb", "E", "F", "F#", "Gb", "G", "G#", "Ab", "A", "A#", "Bb", "B"];

  function build(rootStr, spec) {
    var root = parseNote(rootStr);
    if (!root || !spec) return null;
    var notes = spec.semitones.map(function (st, i) {
      var deg = spec.degrees[i];
      var n = spell(root, deg, st);
      return {
        note: n,
        name: noteName(n),
        semitones: st,
        degree: deg,
        label: degreeLabel(deg, st),
        pc: pitchClass(n)
      };
    });
    var theoretical = notes.some(function (n) {
      return Math.abs(n.note.alter) > 1;
    });
    var alt = null;
    if (theoretical) {
      var altRoot = autoSpell(pitchClass(root));
      if (noteName(altRoot) !== noteName(root)) alt = noteName(altRoot);
    }
    return {
      root: root,
      rootName: noteName(root),
      spec: spec,
      notes: notes,
      pcs: notes.map(function (n) { return n.pc; }),
      formula: spec.semitones.join("-"),
      degreeFormula: notes.map(function (n) { return n.label; }).join(" "),
      theoretical: theoretical,
      enharmonicRoot: alt
    };
  }

  function chordById(id) {
    for (var i = 0; i < CHORDS.length; i++) if (CHORDS[i].id === id) return CHORDS[i];
    return null;
  }

  function scaleById(id) {
    for (var i = 0; i < SCALES.length; i++) if (SCALES[i].id === id) return SCALES[i];
    return null;
  }

  /* ----------------------------------------------------------- transposition */
  // A chord symbol is a root, an untouched quality suffix, and an optional
  // slash bass. The suffix is never interpreted or rewritten — "m7b5" comes
  // out the far side exactly as it went in, only the letters move.
  function parseChordSymbol(sym) {
    var text = String(sym).trim();
    if (!text) return null;
    var bass = null,
      body = text;
    var slash = text.lastIndexOf("/");
    if (slash > 0) {
      var maybeBass = parseNote(text.slice(slash + 1));
      if (maybeBass) {
        bass = maybeBass;
        body = text.slice(0, slash);
      }
    }
    var m = /^([A-Ga-g])(##|bb|♯♯|♭♭|x|#|b|♯|♭)?(.*)$/.exec(body);
    if (!m) return null;
    var root = parseNote(m[1] + (m[2] || ""));
    if (!root) return null;
    return { root: root, suffix: m[3] || "", bass: bass, original: text };
  }

  function isMinorSuffix(suffix) {
    return /^(m|min|-)(?!aj)/.test(suffix || "");
  }

  // spelling: "auto" (nearest to the target key on the circle of fifths),
  // "sharps", or "flats".
  function transposeSymbol(sym, semitones, spelling, keyFifthsValue) {
    var parsed = parseChordSymbol(sym);
    if (!parsed) return null;
    function moveName(note) {
      var pc = mod(pitchClass(note) + semitones, 12);
      if (spelling === "sharps") return SHARP_NAMES[pc];
      if (spelling === "flats") return FLAT_NAMES[pc];
      return noteName(spellInKey(pc, keyFifthsValue || 0));
    }
    var out = moveName(parsed.root) + parsed.suffix;
    if (parsed.bass) out += "/" + moveName(parsed.bass);
    return out;
  }

  // The key the result is spelled in: the transposed first chord's root, taken
  // to the relative major when that chord is minor, so an A minor progression
  // moved up three semitones is spelled with C major's (empty) signature.
  function targetKeyFifths(firstSymbol, semitones) {
    var parsed = parseChordSymbol(firstSymbol);
    if (!parsed) return 0;
    var pc = mod(pitchClass(parsed.root) + semitones, 12);
    var tonic = autoSpell(pc);
    var K = keyFifths(tonic);
    if (isMinorSuffix(parsed.suffix)) K -= 3; // relative major of a minor tonic
    return K;
  }

  global.PerfectTuneTheory = {
    LETTERS: LETTERS,
    LETTER_SEMITONES: LETTER_SEMITONES,
    MAJOR: MAJOR,
    INTERVALS: INTERVALS,
    CHORDS: CHORDS,
    SCALES: SCALES,
    ROOTS: ROOTS,
    SHARP_NAMES: SHARP_NAMES,
    FLAT_NAMES: FLAT_NAMES,
    intervalBySemitones: intervalBySemitones,
    parseNote: parseNote,
    noteName: noteName,
    pitchClass: pitchClass,
    noteToMidi: noteToMidi,
    spell: spell,
    degreeLabel: degreeLabel,
    keyFifths: keyFifths,
    autoSpell: autoSpell,
    spellInKey: spellInKey,
    build: build,
    chordById: chordById,
    scaleById: scaleById,
    parseChordSymbol: parseChordSymbol,
    transposeSymbol: transposeSymbol,
    targetKeyFifths: targetKeyFifths
  };
})(window);
