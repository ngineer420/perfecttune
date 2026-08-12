/*!
 * perfecttune.net — shared chrome: theme toggle, mobile nav, and the
 * homepage's instant tool-switching (no reload, real clean-path URLs via
 * pushState). Each tool's actual engine lives in its own file
 * (tuner.js / metronome.js / tone-generator.js) and is defensive about
 * missing elements so the same script can load on every page.
 */
(function () {
  "use strict";

  /* ============================== THEME ============================== */
  function initTheme() {
    var btn = document.getElementById("theme-toggle");
    if (!btn) return;
    btn.addEventListener("click", function () {
      var root = document.documentElement;
      var current = root.getAttribute("data-theme");
      var isDark =
        current === "dark" ||
        (!current && window.matchMedia("(prefers-color-scheme: dark)").matches);
      var next = isDark ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try {
        localStorage.setItem("perfecttune-theme", next);
      } catch (e) {}
    });
  }

  /* ================================================================== *
   * toolbar v1 — the portfolio navigation pattern.                      *
   * Spec: github.com/ngineer420/ngineer420.github.io/issues/13          *
   *                                                                     *
   * Copied verbatim from the photoshrink pilot. Pure enhancement: with  *
   * JS off, <details>/<summary> still discloses the sheet, the rail is  *
   * still a native scroll container of real links, the edge fades are   *
   * still CSS and the scrim is still CSS. Only the active-chip          *
   * centring, Escape and click-outside are lost.                        *
   * ================================================================== */
  (function toolbar() {
    var bar = document.querySelector('.toolbar');
    if (!bar) return;
    var rail = bar.querySelector('.tb-rail');
    var menu = bar.querySelector('details.tb-menu');

    if (rail) {
      /* js-on hands the right-hand fade over to measurement. Until then the
         CSS keeps it on, so a JS-disabled visitor never gets a chip clipped
         mid-word with nothing to say there is more of the row. */
      rail.classList.add('js-on');
      var fades = function () {
        var max = rail.scrollWidth - rail.clientWidth;
        rail.classList.toggle('can-l', rail.scrollLeft > 1);
        rail.classList.toggle('can-r', rail.scrollLeft < max - 1);
      };
      /* Centre the current chip, measured from the rail's own box rather than
         through offsetLeft. The chips' offsetParent is .toolbar — the rail
         itself is not positioned — so offsetLeft carries the trigger's width
         with it, and centring on that number lands the active chip a whole
         trigger-width left of centre, half under the left fade at 320px. This
         is still a direct scrollLeft assignment and never scrollIntoView,
         which would also scroll every ancestor and the document and so drop a
         phone visitor below the header on arrival. */
      var current = rail.querySelector('[aria-current]');
      if (current) {
        var cbox = current.getBoundingClientRect();
        var rbox = rail.getBoundingClientRect();
        rail.scrollLeft += (cbox.left - rbox.left) - (rbox.width - cbox.width) / 2;
      }
      rail.addEventListener('scroll', fades, { passive: true });
      window.addEventListener('resize', fades);
      fades();
    }

    if (menu) {
      /* A disclosure, not a modal: focus is deliberately not trapped, Tab
         walks the links and straight out the other side. */
      window.addEventListener('keydown', function (e) {
        if (e.key !== 'Escape' || !menu.open) return;
        menu.open = false;
        var summary = menu.querySelector('summary');
        if (summary) summary.focus();
      });
      document.addEventListener('click', function (e) {
        if (menu.open && !menu.contains(e.target)) menu.open = false;
      });
    }
  })();

  /* ============================ PANEL SWITCHING ============================ */
  // Homepage only: instant tool switching with pushState, no reload.
  function initPanelSwitching() {
    var panels = document.querySelectorAll("[data-panel]");
    var overview = document.getElementById("overview-panel");
    if (!panels.length || !overview) return;

    var navLinks = document.querySelectorAll("[data-panel-link]");
    var defaultTitle = document.title;
    var hero = document.querySelector(".hero");

    // The homepage lands on the tuner rather than a menu — a live tool is the
    // better first screen. But an explicit "All tools" or "Home" click (and a
    // Back to a page that was showing the grid) has to reach the overview: with
    // seven tools that grid is the only place each one is described.
    function show(slug, push, fromHistory) {
      if (!slug && !push && !fromHistory) slug = "tuner";
      var target = slug ? document.querySelector('[data-panel="' + slug + '"]') : overview;
      if (!target) target = overview;

      panels.forEach(function (p) {
        p.hidden = true;
      });
      overview.hidden = true;
      // Hide the tall marketing hero when a specific tool is shown so the tool
      // sits right under the nav instead of below a banner.
      if (hero) hero.hidden = !!slug;
      target.hidden = false;

      navLinks.forEach(function (a) {
        var isCurrent = slug
          ? a.getAttribute("data-panel-link") === slug
          : a.getAttribute("data-panel-link") === "";
        if (isCurrent) {
          a.setAttribute("aria-current", "page");
        } else {
          a.removeAttribute("aria-current");
        }
      });

      if (push) {
        var path = slug ? "/" + slug + "/" : "/";
        var title = slug ? target.getAttribute("data-title") || document.title : defaultTitle;
        document.title = title;
        history.pushState({ panel: slug || null }, "", path);
      }

      // Only scroll on user-initiated switches, never on initial load.
      if (push) target.scrollIntoView({ behavior: "instant", block: "start" });
      var heading = target.querySelector("h1, h2");
      if (heading) {
        heading.setAttribute("tabindex", "-1");
        heading.focus({ preventScroll: true });
      }

      document.dispatchEvent(new CustomEvent("perfecttune:panel-shown", { detail: { slug: slug } }));
    }

    document.addEventListener("click", function (e) {
      var link = e.target.closest && e.target.closest("[data-panel-link]");
      if (!link) return;
      if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      e.preventDefault();
      show(link.getAttribute("data-panel-link") || null, true);
    });

    window.addEventListener("popstate", function (e) {
      var slug = e.state && e.state.panel ? e.state.panel : null;
      show(slug, false, !!e.state);
    });

    show(null, false);
  }

  document.addEventListener("DOMContentLoaded", function () {
    initTheme();
    initPanelSwitching();
  });
})();
