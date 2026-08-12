/*!
 * perfecttune.net — pitch detector tests.
 *
 *   node test/pitch.test.js
 *
 * No dependencies and no framework: plain node with assert, matching the
 * rest of the repo's zero-toolchain approach. It requires assets/pitch.js
 * directly, so what is under test is the exact function the browser runs —
 * not a reimplementation of it.
 *
 * The point of these tests is the bottom octave. A 5-string bass low B is
 * 30.87 Hz, its fundamental is far quieter than its harmonics, and it is
 * the case a naive 2048-sample autocorrelation tuner gets wrong every
 * time. So the synthesised tones here are not pure sines: they carry a
 * plucked string's harmonic stack with a deliberately weak fundamental,
 * string inharmonicity, a decay envelope and broadband noise. (Pure sines
 * are tested too — they are the other hard case, since there is nothing
 * there but the weak part.)
 */
"use strict";

var assert = require("assert");
var Pitch = require("../assets/pitch.js");

var SR = 48000;
var results = [];
var failures = 0;

/* ------------------------------------------------------------ helpers -- */

// Deterministic PRNG so a run is reproducible and a failure is a real one.
function mulberry32(seed) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    var t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function cents(detected, expected) {
  return 1200 * (Math.log(detected / expected) / Math.LN2);
}

/*
 * A plucked-string tone.
 *   partials      per-harmonic amplitudes, [0] being the fundamental
 *   inharmonicity B in f_n = n*f0*sqrt(1 + B*n^2) — real strings are stiff
 *                 and their harmonics sit slightly sharp of exact multiples
 *   decay         amplitude multiplier reached by the end of the window
 *   noise         broadband noise amplitude relative to peak
 */
function pluck(freq, sampleRate, length, opts) {
  opts = opts || {};
  var partials = opts.partials || [1];
  var B = typeof opts.inharmonicity === "number" ? opts.inharmonicity : 0;
  var decay = typeof opts.decay === "number" ? opts.decay : 1;
  var noise = typeof opts.noise === "number" ? opts.noise : 0;
  var rand = mulberry32(opts.seed || 12345);
  var phases = partials.map(function () {
    return rand() * Math.PI * 2;
  });
  var buf = new Float32Array(length);
  var tail = Math.log(decay <= 0 ? 1e-6 : decay);
  for (var i = 0; i < length; i++) {
    var t = i / sampleRate;
    var env = Math.exp((tail * i) / length);
    var s = 0;
    for (var k = 0; k < partials.length; k++) {
      var n = k + 1;
      var fn = n * freq * Math.sqrt(1 + B * n * n);
      if (fn > sampleRate * 0.45) break;
      s += partials[k] * Math.sin(2 * Math.PI * fn * t + phases[k]);
    }
    buf[i] = s * env + (rand() * 2 - 1) * noise;
  }
  // Normalize to a realistic mic level rather than full scale.
  var peak = 0;
  for (i = 0; i < length; i++) if (Math.abs(buf[i]) > peak) peak = Math.abs(buf[i]);
  var g = peak > 0 ? 0.35 / peak : 1;
  for (i = 0; i < length; i++) buf[i] *= g;
  return buf;
}

// A bass string as a pickup actually sees it: the fundamental is roughly
// 20 dB below the second harmonic, which is why raw autocorrelation
// peak-picking reports the octave up.
var BASS_PARTIALS = [0.12, 1.0, 0.78, 0.55, 0.42, 0.31, 0.24, 0.18, 0.14, 0.1, 0.08, 0.06];
var GUITAR_PARTIALS = [1.0, 0.62, 0.48, 0.3, 0.24, 0.16, 0.12, 0.09, 0.07, 0.05];
var BOWED_PARTIALS = [0.8, 1.0, 0.7, 0.55, 0.4, 0.3, 0.2, 0.14, 0.1, 0.07];

function check(label, freq, buf, sampleRate, opts, tolerance) {
  var got = Pitch.detect(buf, sampleRate, opts);
  var row = {
    label: label,
    expected: freq,
    detected: got ? got.freq : null,
    cents: got ? cents(got.freq, freq) : null,
    clarity: got ? got.clarity : null,
    window: buf.length,
    tolerance: tolerance
  };
  results.push(row);
  try {
    assert.ok(got, label + ": expected a detection, got null");
    assert.ok(
      Math.abs(row.cents) <= tolerance,
      label + ": " + row.cents.toFixed(2) + " cents off (tolerance " + tolerance + ")"
    );
  } catch (e) {
    failures++;
    row.error = e.message;
  }
  return row;
}

function fmt(n, w, d) {
  var s = n === null || n === undefined ? "—" : n.toFixed(d);
  while (s.length < w) s = " " + s;
  return s;
}

/* ------------------------------------------- 1. window sizing contract -- */

assert.strictEqual(Pitch.windowSizeFor(48000, 30.87), 16384, "low B needs a 16384-sample window at 48k");
assert.strictEqual(Pitch.windowSizeFor(44100, 30.87), 16384, "low B needs a 16384-sample window at 44.1k");
assert.strictEqual(Pitch.windowSizeFor(48000, 51.5), 8192, "a guitar low E only needs 8192");
assert.strictEqual(Pitch.windowSizeFor(48000, 245), 2048, "a ukulele only needs the floor window");
assert.ok(Pitch.windowSizeFor(48000, 5) <= 32768, "window size is clamped to the AnalyserNode ceiling");

/* --------------------------------------- 2. the bottom octave, plucked -- */

var BASS = { fmin: 24, fmax: 900 };
var bassWindow = Pitch.windowSizeFor(SR, BASS.fmin);

[
  ["5-string low B (issue's 31 Hz)", 31.0],
  ["B0 low B, exact", 30.87],
  ["E1 (4-string low E)", 41.2],
  ["A1", 55.0],
  ["D2", 73.42],
  ["G2", 98.0]
].forEach(function (c, i) {
  var buf = pluck(c[1], SR, bassWindow, {
    partials: BASS_PARTIALS,
    inharmonicity: 3e-5,
    decay: 0.6,
    noise: 0.01,
    seed: 1000 + i
  });
  check(c[0], c[1], buf, SR, BASS, 5);
});

/* ---------------------------- 3. the bottom octave as bare sine waves --- */
// Nothing but the fundamental, at the level a fundamental actually arrives
// at. No harmonic stack to fall back on.

[
  ["31 Hz pure sine", 31.0],
  ["41.20 Hz pure sine", 41.2],
  ["55 Hz pure sine", 55.0]
].forEach(function (c, i) {
  var buf = pluck(c[1], SR, bassWindow, { partials: [1], decay: 0.8, noise: 0.004, seed: 2000 + i });
  check(c[0], c[1], buf, SR, BASS, 3);
});

/* --------------------------------- 4. the same notes at 44.1 kHz ------- */

[
  ["31 Hz @ 44.1 kHz", 31.0],
  ["41.20 Hz @ 44.1 kHz", 41.2],
  ["55 Hz @ 44.1 kHz", 55.0]
].forEach(function (c, i) {
  var sr = 44100;
  var buf = pluck(c[1], sr, Pitch.windowSizeFor(sr, BASS.fmin), {
    partials: BASS_PARTIALS,
    inharmonicity: 3e-5,
    decay: 0.6,
    noise: 0.01,
    seed: 3000 + i
  });
  check(c[0], c[1], buf, sr, BASS, 5);
});

/* --------------------------------------- 5. guitar, ukulele, bowed ----- */

var GUITAR = { fmin: 51.5, fmax: 1320 };
var guitarWindow = Pitch.windowSizeFor(SR, GUITAR.fmin);
[
  ["E2 guitar", 82.41],
  ["A2 guitar", 110.0],
  ["D3 guitar", 146.83],
  ["G3 guitar", 196.0],
  ["B3 guitar", 246.94],
  ["E4 guitar", 329.63],
  ["Eb2 half step down", 77.78],
  ["D2 drop D", 73.42]
].forEach(function (c, i) {
  var buf = pluck(c[1], SR, guitarWindow, {
    partials: GUITAR_PARTIALS,
    inharmonicity: 1e-5,
    decay: 0.5,
    noise: 0.008,
    seed: 4000 + i
  });
  check(c[0], c[1], buf, SR, GUITAR, 3);
});

var UKE = { fmin: 163, fmax: 1760 };
var ukeWindow = Pitch.windowSizeFor(SR, UKE.fmin);
[
  ["C4 ukulele", 261.63],
  ["E4 ukulele", 329.63],
  ["G4 ukulele", 392.0],
  ["A4 ukulele", 440.0]
].forEach(function (c, i) {
  var buf = pluck(c[1], SR, ukeWindow, {
    partials: GUITAR_PARTIALS,
    decay: 0.5,
    noise: 0.008,
    seed: 5000 + i
  });
  check(c[0], c[1], buf, SR, UKE, 3);
});

var VIOLIN = { fmin: 122, fmax: 2637 };
var violinWindow = Pitch.windowSizeFor(SR, VIOLIN.fmin);
[
  ["G3 violin", 196.0],
  ["D4 violin", 293.66],
  ["A4 violin", 440.0],
  ["E5 violin", 659.26]
].forEach(function (c, i) {
  var buf = pluck(c[1], SR, violinWindow, {
    partials: BOWED_PARTIALS,
    decay: 0.95,
    noise: 0.01,
    seed: 6000 + i
  });
  check(c[0], c[1], buf, SR, VIOLIN, 3);
});

var CELLO = { fmin: 41, fmax: 900 };
var celloWindow = Pitch.windowSizeFor(SR, CELLO.fmin);
[["C2 cello", 65.41], ["G2 cello", 98.0], ["D3 cello", 146.83], ["A3 cello", 220.0]].forEach(function (c, i) {
  var buf = pluck(c[1], SR, celloWindow, {
    partials: BOWED_PARTIALS,
    inharmonicity: 2e-5,
    decay: 0.95,
    noise: 0.01,
    seed: 7000 + i
  });
  check(c[0], c[1], buf, SR, CELLO, 3);
});

/* ------------------------------ 6. it measures, it does not snap -------- */
// A string 20 cents flat of low B has to read 20 cents flat, or the needle
// is decorative.

[-40, -20, -7, 7, 20, 40].forEach(function (off, i) {
  var target = 30.87 * Math.pow(2, off / 1200);
  var buf = pluck(target, SR, bassWindow, {
    partials: BASS_PARTIALS,
    inharmonicity: 3e-5,
    decay: 0.6,
    noise: 0.01,
    seed: 8000 + i
  });
  var row = check("B0 " + (off > 0 ? "+" : "") + off + " cents", target, buf, SR, BASS, 5);
  if (row.detected) {
    var readAgainstB0 = cents(row.detected, 30.87);
    assert.ok(
      Math.abs(readAgainstB0 - off) <= 5,
      "detuned B0 should read " + off + " cents off B0, read " + readAgainstB0.toFixed(2)
    );
  }
});

/* --------------------------------- 7. what a short window cannot do ---- */
// The regression this whole change exists for: at the 2048-sample window a
// conventional browser tuner uses, 31 Hz is 1.3 cycles and cannot be
// resolved. Either it refuses, or it is wildly wrong — never quietly right.

var shortBuf = pluck(31.0, SR, 2048, {
  partials: BASS_PARTIALS,
  inharmonicity: 3e-5,
  decay: 0.9,
  noise: 0.01,
  seed: 9001
});
var shortResult = Pitch.detect(shortBuf, SR, BASS);
var shortCents = shortResult ? cents(shortResult.freq, 31.0) : null;
assert.ok(
  shortResult === null || Math.abs(shortCents) > 50,
  "a 2048-sample window must not appear to resolve 31 Hz (got " +
    (shortResult ? shortResult.freq.toFixed(2) + " Hz" : "null") +
    ")"
);

/* ------------------------------------------- 8. silence and noise ------ */

assert.strictEqual(Pitch.detect(new Float32Array(bassWindow), SR, BASS), null, "silence is not a pitch");

var hiss = new Float32Array(bassWindow);
var rnd = mulberry32(4242);
for (var i = 0; i < hiss.length; i++) hiss[i] = (rnd() * 2 - 1) * 0.3;
var noiseResult = Pitch.detect(hiss, SR, BASS);
assert.ok(
  noiseResult === null || noiseResult.clarity < 0.75,
  "white noise must not be reported as a confident pitch"
);

/* ------------------------------------------------------------ report -- */

var head = "  " + "case".padEnd(30) + "  expected    detected    cents   clarity   window";
console.log("\nperfecttune pitch detector — measured results (" + SR + " Hz unless noted)\n");
console.log(head);
console.log("  " + "-".repeat(head.length - 2));
results.forEach(function (r) {
  console.log(
    "  " +
      r.label.padEnd(30) +
      fmt(r.expected, 9, 2) +
      "  " +
      fmt(r.detected, 10, 3) +
      "  " +
      fmt(r.cents, 7, 2) +
      "  " +
      fmt(r.clarity, 8, 3) +
      "  " +
      String(r.window).padStart(7) +
      (r.error ? "   FAIL: " + r.error : "")
  );
});

var worst = results.reduce(function (a, r) {
  return r.cents !== null && Math.abs(r.cents) > Math.abs(a) ? r.cents : a;
}, 0);
console.log(
  "\n  " +
    results.length +
    " tone cases, worst error " +
    worst.toFixed(2) +
    " cents, " +
    failures +
    " failure(s)."
);
console.log(
  "  2048-sample window at 31 Hz: " +
    (shortResult ? shortResult.freq.toFixed(2) + " Hz (" + shortCents.toFixed(0) + " cents off)" : "no detection") +
    " — correctly unusable, which is why the window grows.\n"
);

if (failures) {
  process.exitCode = 1;
  console.error("FAILED: " + failures + " case(s) outside tolerance.");
} else {
  console.log("All pitch detection tests passed.\n");
}
