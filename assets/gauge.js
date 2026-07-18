/*!
 * perfecttune.net — the brass gauge. This is the signature visual element
 * shared by the tuner (a needle reading cents-off-pitch, -50..+50, with
 * red/amber/green zones) and the metronome (the same physical dial used
 * as a swinging pendulum, driven every frame from the real Web Audio
 * clock rather than a decorative CSS animation).
 *
 * Built as inline SVG, no images. The needle pivots from a hub near the
 * bottom-center of a half-circle ivory meter face ringed in brass ticks.
 */
(function (global) {
  "use strict";

  var SVG_NS = "http://www.w3.org/2000/svg";
  var CX = 150,
    PIVOT_Y = 172,
    R_FACE = 148,
    R_TICK_OUT = 140;

  function el(name, attrs) {
    var node = document.createElementNS(SVG_NS, name);
    for (var k in attrs) {
      if (Object.prototype.hasOwnProperty.call(attrs, k)) {
        node.setAttribute(k, attrs[k]);
      }
    }
    return node;
  }

  function polar(angleDeg, r) {
    var rad = ((angleDeg - 90) * Math.PI) / 180;
    return { x: CX + r * Math.cos(rad), y: PIVOT_Y + r * Math.sin(rad) };
  }

  // angleDeg measured from straight-up (0) — negative = left, positive = right.
  function buildFace(sweepDeg) {
    var g = el("g", {});
    var p0 = polar(-sweepDeg, R_FACE);
    var p1 = polar(sweepDeg, R_FACE);
    var large = sweepDeg * 2 > 180 ? 1 : 0;
    var facePath = [
      "M", CX - R_FACE * 0.02, PIVOT_Y,
      "L", p0.x.toFixed(2), p0.y.toFixed(2),
      "A", R_FACE, R_FACE, 0, large, 1, p1.x.toFixed(2), p1.y.toFixed(2),
      "L", CX + R_FACE * 0.02, PIVOT_Y,
      "Z",
    ].join(" ");
    g.appendChild(el("path", { d: facePath, class: "gauge-face" }));
    return g;
  }

  // ticks: array of { at: -1..1 (fraction of sweep), major: bool, zone: "good"|"warn"|null }
  function buildTicks(ticks, sweepDeg) {
    var g = el("g", { class: "gauge-ticks" });
    ticks.forEach(function (t) {
      var angle = t.at * sweepDeg;
      var p1 = polar(angle, R_TICK_OUT);
      var p2 = polar(angle, t.major ? R_TICK_OUT - 16 : R_TICK_OUT - 9);
      var cls = "gauge-tick" + (t.major ? " major" : "") + (t.zone ? " zone-" + t.zone : "");
      g.appendChild(
        el("line", {
          class: cls,
          x1: p1.x.toFixed(2), y1: p1.y.toFixed(2),
          x2: p2.x.toFixed(2), y2: p2.y.toFixed(2),
        })
      );
      if (t.label !== undefined) {
        var lp = polar(angle, R_TICK_OUT - 28);
        var textEl = el("text", {
          class: "gauge-label", x: lp.x.toFixed(2), y: lp.y.toFixed(2),
          "text-anchor": "middle", "dominant-baseline": "middle",
        });
        textEl.textContent = t.label;
        g.appendChild(textEl);
      }
    });
    return g;
  }

  function buildNeedle(len) {
    var tip = polar(0, len);
    var needle = el("line", {
      class: "gauge-needle", x1: CX, y1: PIVOT_Y, x2: tip.x.toFixed(2), y2: tip.y.toFixed(2),
    });
    return needle;
  }

  // Mounts a cents gauge: sweep = degrees each side of center, range = value
  // each side (e.g. 50 cents), zones colored green near center / amber mid /
  // (implicit) red at the extremes via the needle itself, not the ticks.
  function mountCents(container, opts) {
    opts = opts || {};
    var sweep = opts.sweep || 55;
    var range = opts.range || 50;
    container.innerHTML = "";
    var svg = el("svg", { viewBox: "0 0 300 190", "aria-hidden": "true" });
    svg.appendChild(buildFace(sweep));

    var ticks = [];
    var majorStep = 10;
    for (var v = -range; v <= range; v += majorStep) {
      var isCenter = v === 0;
      var zone = Math.abs(v) <= 5 ? "good" : Math.abs(v) >= 30 ? "warn" : null;
      ticks.push({ at: v / range, major: isCenter || v % 25 === 0, zone: zone, label: v % 25 === 0 ? String(v) : undefined });
    }
    // fine ticks every 2 cents
    for (var v2 = -range; v2 <= range; v2 += 2) {
      if (v2 % majorStep === 0) continue;
      ticks.push({ at: v2 / range, major: false, zone: Math.abs(v2) <= 5 ? "good" : null });
    }
    svg.appendChild(buildTicks(ticks, sweep));

    var needle = buildNeedle(R_FACE - 22);
    svg.appendChild(needle);
    svg.appendChild(el("circle", { class: "gauge-hub", cx: CX, cy: PIVOT_Y, r: 8 }));
    container.appendChild(svg);

    return {
      // cents: -range..range (clamped); null/undefined = rest at center
      setValue: function (cents) {
        var c = cents == null ? 0 : Math.max(-range, Math.min(range, cents));
        var angle = (c / range) * sweep;
        needle.style.transform = "rotate(" + angle.toFixed(2) + "deg)";
      },
    };
  }

  // Mounts a pendulum gauge for the metronome: same physical dial, but the
  // needle swings continuously between -sweep..+sweep, driven every frame
  // by the caller from real elapsed audio-clock time (see metronome.js).
  function mountPendulum(container, opts) {
    opts = opts || {};
    var sweep = opts.sweep || 28;
    container.innerHTML = "";
    var svg = el("svg", { viewBox: "0 0 300 190", "aria-hidden": "true" });
    svg.appendChild(buildFace(sweep));

    var ticks = [];
    var count = opts.maxBeats || 12;
    for (var i = 0; i <= count; i++) {
      var at = (i / count) * 2 - 1;
      ticks.push({ at: at, major: i === count / 2 });
    }
    svg.appendChild(buildTicks(ticks, sweep));

    var needle = buildNeedle(R_FACE - 18);
    svg.appendChild(needle);
    svg.appendChild(el("circle", { class: "gauge-hub", cx: CX, cy: PIVOT_Y, r: 8 }));
    container.appendChild(svg);

    return {
      // fraction: -1..1 (left..right)
      setSwing: function (fraction) {
        var angle = Math.max(-1, Math.min(1, fraction)) * sweep;
        needle.style.transform = "rotate(" + angle.toFixed(2) + "deg)";
      },
    };
  }

  global.PerfectTuneGauge = {
    mountCents: mountCents,
    mountPendulum: mountPendulum,
  };
})(window);
