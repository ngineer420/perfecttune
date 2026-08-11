/*!
 * perfecttune.net — the shared playback engine.
 *
 * One AudioContext for the whole site, created lazily on the first user
 * gesture and reused by every tool that makes sound (metronome, tone
 * generator, ear trainer, chord dictionary, tap tempo click). Nothing here
 * runs at load time: context() is only ever reached from inside a click or
 * keypress handler, which is both what browsers require and what keeps a
 * page silent until someone asks for a sound.
 *
 * Notes are scheduled on the audio clock (ctx.currentTime + offset), the
 * same clock the metronome's lookahead scheduler uses, so a two-note
 * interval or an arpeggio is sample-accurate rather than setTimeout-timed.
 */
(function (global) {
  "use strict";

  var ctx = null;
  var master = null;
  var live = [];

  function context() {
    if (!ctx) {
      var AC = global.AudioContext || global.webkitAudioContext;
      if (!AC) return null;
      ctx = new AC();
    }
    if (ctx.state === "suspended" && ctx.resume) ctx.resume();
    return ctx;
  }

  function masterGain() {
    var c = context();
    if (!c) return null;
    if (!master) {
      master = c.createGain();
      master.gain.value = 1;
      master.connect(c.destination);
    }
    return master;
  }

  function forget(voice) {
    var i = live.indexOf(voice);
    if (i !== -1) live.splice(i, 1);
  }

  /*
   * Schedule one note. Options:
   *   freq      Hz (required)
   *   when      absolute audio-clock time; defaults to now
   *   duration  seconds of sustain before the release (default 0.6)
   *   type      oscillator waveform (default "triangle")
   *   gain      peak level 0..1 (default 0.22)
   * Envelope is a short exponential attack and release — an instant start or
   * stop on an oscillator is an audible click.
   */
  function note(opts) {
    var c = context();
    if (!c) return null;
    var out = masterGain();
    var freq = opts.freq;
    var at = typeof opts.when === "number" ? opts.when : c.currentTime;
    if (at < c.currentTime) at = c.currentTime;
    var dur = typeof opts.duration === "number" ? opts.duration : 0.6;
    var peak = typeof opts.gain === "number" ? opts.gain : 0.22;
    var attack = 0.012;
    var release = 0.14;

    var osc = c.createOscillator();
    var g = c.createGain();
    osc.type = opts.type || "triangle";
    osc.frequency.setValueAtTime(freq, at);
    g.gain.setValueAtTime(0.0001, at);
    g.gain.exponentialRampToValueAtTime(Math.max(peak, 0.0001), at + attack);
    g.gain.setValueAtTime(Math.max(peak, 0.0001), at + Math.max(dur, attack));
    g.gain.exponentialRampToValueAtTime(0.0001, at + Math.max(dur, attack) + release);
    osc.connect(g);
    g.connect(out);
    osc.start(at);
    osc.stop(at + Math.max(dur, attack) + release + 0.02);
    var voice = { osc: osc, gain: g };
    live.push(voice);
    osc.onended = function () {
      forget(voice);
      try {
        g.disconnect();
      } catch (e) {}
    };
    return osc;
  }

  /*
   * Play a list of frequencies. spacing = seconds between note starts (0 for
   * a block chord); duration = how long each note holds. Returns the total
   * length in seconds so a caller can re-enable its button afterwards.
   */
  function sequence(freqs, opts) {
    opts = opts || {};
    var c = context();
    if (!c) return 0;
    var spacing = typeof opts.spacing === "number" ? opts.spacing : 0.42;
    var dur = typeof opts.duration === "number" ? opts.duration : spacing > 0 ? spacing * 0.92 : 1.1;
    var start = c.currentTime + 0.06;
    freqs.forEach(function (f, i) {
      note({
        freq: f,
        when: start + i * spacing,
        duration: dur,
        type: opts.type,
        gain: opts.gain
      });
    });
    var span = spacing * Math.max(freqs.length - 1, 0) + dur;
    return span + 0.2;
  }

  // Cut everything currently sounding or scheduled (panel switches, Stop
  // buttons, a new question before the old one has finished). Faded over a
  // few milliseconds rather than hard-stopped, which would click.
  function stopAll() {
    var c = ctx;
    if (!c) return;
    var t = c.currentTime;
    live.slice().forEach(function (voice) {
      try {
        voice.gain.gain.cancelScheduledValues(t);
        voice.gain.gain.setValueAtTime(Math.max(voice.gain.gain.value, 0.0001), t);
        voice.gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.03);
        voice.osc.stop(t + 0.05);
      } catch (e) {}
      forget(voice);
    });
  }

  global.PerfectTuneAudio = {
    context: context,
    note: note,
    sequence: sequence,
    stopAll: stopAll
  };
})(window);
