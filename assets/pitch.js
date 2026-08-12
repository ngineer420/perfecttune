/*!
 * perfecttune.net — pitch detection.
 *
 * Normalized square difference (McLeod peak picking) over a decimated
 * signal, refined at the full sample rate. Pure functions over a
 * Float32Array: no DOM, no Web Audio, no state — which is what lets the
 * node test in test/pitch.test.js feed it synthesised reference tones and
 * assert cent-accurate results against the exact code the browser runs.
 *
 * WHY THIS IS NOT A PLAIN AUTOCORRELATION LOOP
 *
 * A 5-string bass low B is 30.87 Hz. One cycle of that is 1555 samples at
 * 48 kHz, so the 2048-sample window a "normal" browser tuner uses holds
 * barely 1.3 cycles — not enough for any period estimator to lock onto,
 * and the classic first-dip-then-argmax autocorrelation reliably reports
 * garbage there. Resolving it needs several complete cycles, so the window
 * has to grow to 16384 samples (341 ms). But a direct O(n^2) correlation
 * over 16384 samples is ~30M multiplies per estimate, far too slow to run
 * per animation frame.
 *
 * So the work is split:
 *   1. Low-pass and decimate by D (a symmetric triangular FIR, so linear
 *      phase and no lag shift), then compute the NSDF across the whole
 *      plausible lag range on the short decimated signal. For a 5-string
 *      bass that is ~2700 samples instead of 16384, and the lag range
 *      shrinks by D as well — three orders of magnitude less arithmetic.
 *   2. Take that coarse period, and recompute the NSDF at the ORIGINAL
 *      sample rate over the handful of lags either side of it, with
 *      parabolic interpolation for sub-sample precision. Accuracy comes
 *      from full-rate data; speed comes from only ever asking for it in a
 *      window we already know the answer is inside.
 *
 * NSDF rather than raw autocorrelation matters just as much down there: a
 * plucked bass string's fundamental is much quieter than its second and
 * third harmonics, and a raw autocorrelation peak-picker will happily
 * report the harmonic. The NSDF is normalized by the energy actually
 * overlapping at each lag, and McLeod's "first key maximum within K of the
 * strongest" rule then prefers the longest period consistent with the
 * signal — which is the fundamental, weak or not.
 */
(function (root, factory) {
  "use strict";
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.PerfectTunePitch = api;
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  // Complete cycles of the lowest note we want inside one analysis window.
  // Six is the point where the NSDF peak for a 31 Hz fundamental stops
  // competing with its own harmonics; below four it is not reliable at all.
  var MIN_PERIODS = 6;
  var MIN_WINDOW = 2048;
  var MAX_WINDOW = 32768; // AnalyserNode.fftSize ceiling
  // How close to the strongest key maximum a shorter-lag peak has to be
  // before it is preferred (McLeod's K). Lower prefers the fundamental
  // more aggressively at the cost of the occasional half-pitch report.
  var KEY_MAX_RATIO = 0.86;

  function nextPow2(n) {
    var p = 1;
    while (p < n) p *= 2;
    return p;
  }

  /*
   * The analyser window (in samples, a power of two) needed to resolve a
   * fundamental of fmin Hz at this sample rate. This is the number that has
   * to change per tuning: 8192 is plenty for a guitar's low E at 82 Hz and
   * useless for a 5-string bass's low B.
   */
  function windowSizeFor(sampleRate, fmin) {
    if (!(fmin > 0)) fmin = 55;
    var size = nextPow2(Math.ceil((sampleRate / fmin) * MIN_PERIODS));
    if (size < MIN_WINDOW) size = MIN_WINDOW;
    if (size > MAX_WINDOW) size = MAX_WINDOW;
    return size;
  }

  /*
   * Decimate by an integer factor with a triangular-weighted FIR (two box
   * filters cascaded). Symmetric and centred on the output sample, so it is
   * linear-phase with zero group delay — the coarse lag it produces maps
   * straight back onto the original sample grid without a correction term.
   */
  function decimate(x, D) {
    var N = x.length;
    var M = Math.floor(N / D);
    var out = new Float32Array(M);
    var norm = D * D; // sum of the weights D-|j| for j in -(D-1)..(D-1)
    for (var k = 0; k < M; k++) {
      var c = k * D;
      var acc = 0;
      for (var j = -(D - 1); j <= D - 1; j++) {
        var idx = c + j;
        if (idx < 0) idx = 0;
        else if (idx >= N) idx = N - 1;
        acc += x[idx] * (D - (j < 0 ? -j : j));
      }
      out[k] = acc / norm;
    }
    return out;
  }

  /*
   * n(tau) = 2 * r(tau) / m(tau), the normalized square difference function.
   *   r(tau) = sum x[j] * x[j+tau]
   *   m(tau) = sum x[j]^2 + x[j+tau]^2   over the same overlapping window
   * m is read off a prefix sum of squares rather than recomputed per lag,
   * which is what keeps this O(lagMax * N) instead of O(lagMax * N * 2).
   */
  function nsdf(x, lagFrom, lagTo) {
    var N = x.length;
    var P = new Float64Array(N + 1);
    var i;
    for (i = 0; i < N; i++) P[i + 1] = P[i] + x[i] * x[i];
    var out = new Float64Array(lagTo + 1);
    if (lagFrom < 1) lagFrom = 1;
    for (var tau = lagFrom; tau <= lagTo; tau++) {
      var lim = N - tau;
      if (lim <= 0) break;
      var r = 0;
      for (var j = 0; j < lim; j++) r += x[j] * x[j + tau];
      var m = P[lim] + (P[N] - P[tau]);
      out[tau] = m > 0 ? (2 * r) / m : 0;
    }
    return out;
  }

  /*
   * McLeod peak picking. Skip the lobe around lag 0 (which always decays
   * from 1 and is not a period), collect the maximum of every positive
   * region after it, then take the FIRST of those within KEY_MAX_RATIO of
   * the strongest. Taking the strongest instead is the classic octave
   * error: a signal one octave up correlates just as well at twice the
   * period, and "first good enough" is what breaks the tie towards the
   * true fundamental.
   */
  function pickLag(n, lagMax) {
    var tau = 1;
    while (tau <= lagMax && n[tau] > 0) tau++;
    if (tau > lagMax) return -1; // never crosses zero: no usable period here

    var positions = [];
    var values = [];
    var inRegion = false;
    var bestPos = -1;
    var bestVal = -1;
    for (; tau <= lagMax; tau++) {
      var v = n[tau];
      if (v > 0) {
        if (!inRegion) {
          inRegion = true;
          bestVal = v;
          bestPos = tau;
        } else if (v > bestVal) {
          bestVal = v;
          bestPos = tau;
        }
      } else if (inRegion) {
        positions.push(bestPos);
        values.push(bestVal);
        inRegion = false;
      }
    }
    if (inRegion) {
      positions.push(bestPos);
      values.push(bestVal);
    }
    if (!positions.length) return -1;

    var globalMax = 0;
    for (var i = 0; i < values.length; i++) if (values[i] > globalMax) globalMax = values[i];
    if (globalMax <= 0) return -1;
    var floor = globalMax * KEY_MAX_RATIO;
    for (i = 0; i < values.length; i++) if (values[i] >= floor) return positions[i];
    return -1;
  }

  // Sub-sample peak position and height from three samples around an index.
  function parabolic(n, idx) {
    var y1 = n[idx - 1],
      y2 = n[idx],
      y3 = n[idx + 1];
    var denom = y1 - 2 * y2 + y3;
    if (!isFinite(denom) || denom === 0) return { tau: idx, value: y2 };
    var delta = (0.5 * (y1 - y3)) / denom;
    if (!(delta > -1 && delta < 1)) delta = 0;
    return { tau: idx + delta, value: y2 - 0.25 * (y1 - y3) * delta };
  }

  /*
   * detect(buffer, sampleRate, options) -> { freq, clarity, tau } | null
   *
   * options:
   *   fmin, fmax    the frequency range to look inside (Hz). Narrowing these
   *                 to the active tuning is what lets the decimation factor
   *                 grow, and is why a bass preset is not slower than a
   *                 ukulele one despite its far longer window.
   *   rmsFloor      below this the buffer is treated as silence.
   *   clarityFloor  minimum NSDF peak height to accept as a pitch.
   *
   * Returns null rather than a bad guess: "no clear pitch" is a legitimate
   * and frequent answer when someone is between notes.
   */
  function detect(input, sampleRate, options) {
    var opts = options || {};
    var fmin = opts.fmin > 0 ? opts.fmin : 55;
    var fmax = opts.fmax > 0 ? opts.fmax : 1500;
    var rmsFloor = typeof opts.rmsFloor === "number" ? opts.rmsFloor : 0.004;
    var clarityFloor = typeof opts.clarityFloor === "number" ? opts.clarityFloor : 0.5;
    var N = input.length;
    if (!N || !(sampleRate > 0) || fmax <= fmin) return null;

    // Remove DC before anything else: an offset adds a constant to every
    // correlation and biases the NSDF towards long lags. Mic preamps and
    // room rumble both put one there, and at 31 Hz it is not separable by
    // eye from the signal.
    var mean = 0;
    var i;
    for (i = 0; i < N; i++) mean += input[i];
    mean /= N;
    var x = new Float32Array(N);
    var energy = 0;
    for (i = 0; i < N; i++) {
      var v = input[i] - mean;
      x[i] = v;
      energy += v * v;
    }
    var rms = Math.sqrt(energy / N);
    if (rms < rmsFloor) return null;

    var lagMin = Math.max(2, Math.floor(sampleRate / fmax));
    var lagMax = Math.ceil(sampleRate / fmin);
    // Past N/2 the NSDF is averaging over fewer samples than it discards,
    // and its peaks stop meaning anything.
    var halfN = Math.floor(N / 2);
    if (lagMax > halfN) lagMax = halfN;
    if (lagMin >= lagMax) return null;

    // Decimate hard enough that the coarse pass is cheap, but keep at least
    // 8 decimated samples inside the shortest period we care about, or the
    // coarse peak lands on the wrong side of the true one.
    var D = Math.floor(lagMin / 8);
    if (D < 1) D = 1;
    if (D > 32) D = 32;
    while (D > 1 && Math.floor(N / D) < 512) D--;

    var coarseLag;
    if (D === 1) {
      coarseLag = pickLag(nsdf(x, 1, lagMax), lagMax);
    } else {
      var y = decimate(x, D);
      var M = y.length;
      var lagMaxC = Math.min(Math.floor(M / 2), Math.ceil(lagMax / D) + 1);
      if (lagMaxC < 2) return null;
      var c = pickLag(nsdf(y, 1, lagMaxC), lagMaxC);
      coarseLag = c < 0 ? -1 : c * D;
    }
    if (coarseLag < 0) return null;

    // Full-rate refinement in a narrow band around the coarse period. One
    // extra lag either side so the parabola has three real samples.
    var span = D === 1 ? 2 : 2 * D;
    var lo = Math.max(lagMin, coarseLag - span);
    var hi = Math.min(lagMax, coarseLag + span);
    if (hi <= lo) {
      lo = Math.max(2, coarseLag - 2);
      hi = Math.min(halfN - 1, coarseLag + 2);
    }
    var fine = nsdf(x, lo - 1 < 1 ? 1 : lo - 1, hi + 1 < halfN ? hi + 1 : halfN);
    var bestIdx = -1;
    var bestVal = -Infinity;
    for (var t = lo; t <= hi; t++) {
      if (fine[t] > bestVal) {
        bestVal = fine[t];
        bestIdx = t;
      }
    }
    if (bestIdx < 1) return null;

    var peak =
      bestIdx > 1 && bestIdx + 1 < fine.length ? parabolic(fine, bestIdx) : { tau: bestIdx, value: bestVal };
    if (!(peak.tau > 0)) return null;
    var clarity = peak.value;
    if (!(clarity >= clarityFloor)) return null;

    var freq = sampleRate / peak.tau;
    if (freq < fmin || freq > fmax) return null;
    return { freq: freq, clarity: clarity > 1 ? 1 : clarity, tau: peak.tau };
  }

  return {
    detect: detect,
    windowSizeFor: windowSizeFor,
    decimate: decimate,
    nsdf: nsdf,
    MIN_PERIODS: MIN_PERIODS,
    MAX_WINDOW: MAX_WINDOW
  };
});
