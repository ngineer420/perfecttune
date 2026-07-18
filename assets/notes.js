/*!
 * perfecttune.net — shared note/frequency math (equal temperament).
 * Used by both the tuner (frequency -> nearest note + cents off) and the
 * tone generator (note name -> frequency, for its note-name picker).
 */
(function (global) {
  "use strict";

  var NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

  // MIDI note number 69 = A4. Concert pitch (a4Hz) defaults to 440 but is
  // adjustable (some players tune to 442/443/432 etc).
  function freqToMidi(freq, a4Hz) {
    a4Hz = a4Hz || 440;
    return 69 + 12 * (Math.log(freq / a4Hz) / Math.LN2);
  }

  function midiToFreq(midi, a4Hz) {
    a4Hz = a4Hz || 440;
    return a4Hz * Math.pow(2, (midi - 69) / 12);
  }

  function midiToName(midi) {
    var rounded = Math.round(midi);
    var name = NOTE_NAMES[((rounded % 12) + 12) % 12];
    var octave = Math.floor(rounded / 12) - 1;
    return { name: name, octave: octave, midi: rounded };
  }

  // Returns { name, octave, midi, targetFreq, cents } for a detected freq.
  function analyze(freq, a4Hz) {
    var midi = freqToMidi(freq, a4Hz);
    var rounded = Math.round(midi);
    var target = midiToFreq(rounded, a4Hz);
    var cents = 1200 * (Math.log(freq / target) / Math.LN2);
    var n = midiToName(rounded);
    return { name: n.name, octave: n.octave, midi: rounded, targetFreq: target, cents: cents };
  }

  // Build a full list of playable notes (C0..B8) with frequencies, for the
  // tone generator's note-name <select>.
  function buildNoteList(a4Hz) {
    var list = [];
    for (var midi = 12; midi <= 119; midi++) {
      var n = midiToName(midi);
      list.push({ midi: midi, label: n.name + n.octave, freq: midiToFreq(midi, a4Hz) });
    }
    return list;
  }

  global.PerfectTuneNotes = {
    NOTE_NAMES: NOTE_NAMES,
    freqToMidi: freqToMidi,
    midiToFreq: midiToFreq,
    midiToName: midiToName,
    analyze: analyze,
    buildNoteList: buildNoteList,
  };
})(window);
