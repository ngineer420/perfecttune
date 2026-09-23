/*!
 * perfecttune.net — guarded announcements for a role="status" node.
 *
 * A tuner writes a new note and a new cents figure many times a second. A
 * live region that mirrors that loop is not information, it is a stuck horn.
 * This helper puts two guards in front of every write:
 *
 *   1. A diff guard. Identical text never reaches the node twice, so a
 *      steady reading is announced once and then stays quiet.
 *   2. A throttle. The node is written at most once per `delay`
 *      milliseconds, and only the newest text survives the wait.
 *
 * The pattern is the one assets/metronome.js already uses for its trainer
 * readout. This file is that guard, extracted so the tuner and the other
 * tools share one copy.
 *
 * Load it before any tool script. The API is deliberately tiny:
 *
 *     var live = PTLive.announcer(document.getElementById("tn-live"));
 *     live.say("E2, in tune");   // spoken once
 *     live.say("E2, in tune");   // dropped by the diff guard
 *     live.reset();              // forget the last value
 */
(function (global) {
  "use strict";

  var DEFAULT_DELAY = 500;

  function announcer(el, delayMs) {
    var delay = typeof delayMs === "number" ? delayMs : DEFAULT_DELAY;
    var last = null;
    var pending = null;
    var timer = null;

    function flush() {
      timer = null;
      if (pending === null || pending === last) {
        pending = null;
        return;
      }
      last = pending;
      pending = null;
      el.textContent = last;
    }

    return {
      /* Queue one announcement. Identical text is dropped immediately. */
      say: function (text) {
        if (!el || text == null || text === last) return;
        pending = String(text);
        if (timer === null) timer = global.setTimeout(flush, delay);
      },

      /* Forget the last value, so the next say() always announces. */
      reset: function () {
        last = null;
        pending = null;
        if (timer !== null) {
          global.clearTimeout(timer);
          timer = null;
        }
      },

      /* Clear the node and the history together. */
      clear: function () {
        this.reset();
        if (el) el.textContent = "";
      }
    };
  }

  global.PTLive = { announcer: announcer };
})(window);
