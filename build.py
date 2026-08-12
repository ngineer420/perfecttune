#!/usr/bin/env python3
"""
One-off static-page generator for perfecttune.net. The shipped site has
zero build step — this script just avoids hand-duplicating the shared
head/header/footer boilerplate (and the erabbit mark's exact placement)
across the homepage panels, seven standalone tool pages, two legal pages,
the 404, and three articles. Add a tool by adding one entry to TOOLS: the
nav, the homepage card and panel, the tool page, and the sitemap all follow
from it. Nothing here is hand-edited afterwards.

Clean-path implementation: GitHub Pages 301-redirects "/slug" -> "/slug/"
and serves that directory's index.html with the correct text/html type
(an extensionless FILE gets served as application/octet-stream and forces
a download). So every tool/legal page ships as BOTH "<slug>/index.html"
(the true clean path) and "<slug>.html" (a flat alias, also text/html).
"""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = "https://perfecttune.net"
TODAY = "2026-07-18"      # first publication date — articles keep it
UPDATED = "2026-08-11"    # last build: sitemap lastmod and the legal pages
PUB_ID = "ca-pub-7560786263587509"

THEME_SCRIPT = (
    '<script>(function(){try{var r=document.documentElement;'
    'var t=localStorage.getItem("perfecttune-theme");'
    'if(!t){t=window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light";}'
    'r.setAttribute("data-theme",t);}catch(e){}})();</script>'
)

ERABBIT = (
    '<a href="https://erabb.it" class="erabbit-mark" aria-label="erabb.it">'
    '<img src="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 '
    'viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>\U0001F407</text></svg>" '
    'width="10" height="10" alt=""></a>'
)

# ------------------------------------------------- theory reference tables --
# The runtime source of truth for all of this is assets/theory.js; these lists
# exist so the tool pages carry the same numbers as readable HTML rather than
# only as JavaScript. They are checked against theory.js in the browser, so a
# change to one without the other shows up as a mismatch, not as silence.

LETTERS = ["C", "D", "E", "F", "G", "A", "B"]
LETTER_SEMITONES = [0, 2, 4, 5, 7, 9, 11]

INTERVAL_TABLE = [
    # (name, short, semitones, letter steps)
    ("Unison", "P1", 0, 0),
    ("Minor 2nd", "m2", 1, 1),
    ("Major 2nd", "M2", 2, 1),
    ("Minor 3rd", "m3", 3, 2),
    ("Major 3rd", "M3", 4, 2),
    ("Perfect 4th", "P4", 5, 3),
    ("Tritone", "TT", 6, 3),
    ("Perfect 5th", "P5", 7, 4),
    ("Minor 6th", "m6", 8, 5),
    ("Major 6th", "M6", 9, 5),
    ("Minor 7th", "m7", 10, 6),
    ("Major 7th", "M7", 11, 6),
    ("Octave", "P8", 12, 7),
]

CHORD_TABLE = [
    # (name, semitone offsets, letter steps per offset)
    ("Major", [0, 4, 7], [0, 2, 4]),
    ("Minor", [0, 3, 7], [0, 2, 4]),
    ("Diminished", [0, 3, 6], [0, 2, 4]),
    ("Augmented", [0, 4, 8], [0, 2, 4]),
    ("Dominant 7th", [0, 4, 7, 10], [0, 2, 4, 6]),
    ("Major 7th", [0, 4, 7, 11], [0, 2, 4, 6]),
    ("Minor 7th", [0, 3, 7, 10], [0, 2, 4, 6]),
    ("Sus2", [0, 2, 7], [0, 1, 4]),
    ("Sus4", [0, 5, 7], [0, 3, 4]),
]

MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]

SCALE_TABLE = [
    ("Major (Ionian)", MAJOR_SCALE),
    ("Natural minor (Aeolian)", [0, 2, 3, 5, 7, 8, 10]),
    ("Harmonic minor", [0, 2, 3, 5, 7, 8, 11]),
    ("Melodic minor (ascending)", [0, 2, 3, 5, 7, 9, 11]),
    ("Dorian", [(MAJOR_SCALE[(i + 1) % 7] - MAJOR_SCALE[1]) % 12 for i in range(7)]),
    ("Phrygian", [(MAJOR_SCALE[(i + 2) % 7] - MAJOR_SCALE[2]) % 12 for i in range(7)]),
    ("Lydian", [(MAJOR_SCALE[(i + 3) % 7] - MAJOR_SCALE[3]) % 12 for i in range(7)]),
    ("Mixolydian", [(MAJOR_SCALE[(i + 4) % 7] - MAJOR_SCALE[4]) % 12 for i in range(7)]),
    ("Locrian", [(MAJOR_SCALE[(i + 6) % 7] - MAJOR_SCALE[6]) % 12 for i in range(7)]),
]


def spell_from_c(letter_steps, semitones):
    """Note name that many letters and semitones above C — the same rule
    theory.js uses: the letter comes from the degree, the accidental is
    whatever it takes to land on the requested semitone."""
    letter = letter_steps % 7
    octaves = letter_steps // 7
    natural = LETTER_SEMITONES[letter] + 12 * octaves
    alter = semitones - natural
    acc = "#" * alter if alter > 0 else "b" * (-alter)
    return LETTERS[letter] + acc


def degree_label(degree, semitones):
    octaves = degree // 7
    diff = semitones - MAJOR_SCALE[degree % 7] - 12 * octaves
    prefix = "" if diff == 0 else ("#" * diff if diff > 0 else "b" * (-diff))
    return f"{prefix}{degree + 1}"


def interval_table_html():
    rows = "".join(
        f'          <tr><td>{name}</td><td class="mono">{short}</td>'
        f'<td class="mono">{semis}</td><td class="mono">C &rarr; {spell_from_c(steps, semis)}</td></tr>\n'
        for name, short, semis, steps in INTERVAL_TABLE
    )
    return f"""
    <section class="content-section">
      <div class="wrap">
        <h2>The thirteen intervals</h2>
        <p>Every question this trainer asks is one row of this table. The semitone count is what the two notes are actually built from; the example shows the interval measured up from C, spelled the way that degree has to be spelled.</p>
        <div class="table-scroll">
        <table class="data-table">
          <thead><tr><th>Interval</th><th>Short</th><th>Semitones</th><th>Above C</th></tr></thead>
          <tbody>
{rows}          </tbody>
        </table>
        </div>
      </div>
    </section>
"""


def formula_tables_html():
    chord_rows = ""
    for name, semis, degrees in CHORD_TABLE:
        degs = " ".join(degree_label(d, s) for d, s in zip(degrees, semis))
        notes = " ".join(spell_from_c(d, s) for d, s in zip(degrees, semis))
        chord_rows += (
            f'          <tr><td>{name}</td><td class="mono">{degs}</td>'
            f'<td class="mono">{"-".join(str(s) for s in semis)}</td><td class="mono">{notes}</td></tr>\n'
        )
    scale_rows = ""
    for name, semis in SCALE_TABLE:
        notes = " ".join(spell_from_c(i, s) for i, s in enumerate(semis))
        scale_rows += (
            f'          <tr><td>{name}</td>'
            f'<td class="mono">{"-".join(str(s) for s in semis)}</td><td class="mono">{notes}</td></tr>\n'
        )
    return f"""
    <section class="content-section">
      <div class="wrap">
        <h2>Chord formulas</h2>
        <p>Semitones counted up from the root. The degree column is what those semitones are called &mdash; a minor triad's <span class="mono">b3</span> is a third that has been flattened, which is why it is still spelled as some kind of third.</p>
        <div class="table-scroll">
        <table class="data-table">
          <thead><tr><th>Chord</th><th>Degrees</th><th>Semitones</th><th>On C</th></tr></thead>
          <tbody>
{chord_rows}          </tbody>
        </table>
        </div>
      </div>
    </section>

    <section class="content-section">
      <div class="wrap">
        <h2>Scale formulas</h2>
        <p>The modes are the major scale started from each of its own degrees, so they are generated by rotating that one row rather than written out separately. Aeolian is the natural minor and Ionian is the major scale, which is why they are not repeated here.</p>
        <div class="table-scroll">
        <table class="data-table">
          <thead><tr><th>Scale</th><th>Semitones</th><th>On C</th></tr></thead>
          <tbody>
{scale_rows}          </tbody>
        </table>
        </div>
      </div>
    </section>
"""


# ------------------------------------------------------------------ tunings --
# The single source of truth for every string of every preset. This one table
# is written out three ways and typed once:
#   * assets/tunings.js  — what the running tuner aims the needle at
#   * the string chart baked into each page's HTML — indexable, and usable
#     before (or without) microphone permission
#   * the tuning reference tables at the bottom of each page
# A string is (string number, MIDI note, optional spelling). Frequencies are
# never written down: they are derived from the MIDI number, so concert pitch
# moves every number on the site consistently and nothing can drift.

NOTE_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
ACC_HTML = {"": "", "#": "&#9839;", "b": "&#9837;"}
ACC_JS = {"": "", "#": "\\u266f", "b": "\\u266d"}
ORDINALS = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th", 6: "6th", 7: "7th"}


def midi_freq(midi, a4=440.0):
    return a4 * (2.0 ** ((midi - 69) / 12.0))


def split_note(midi, spell=None):
    """(letter, accidental, octave) for a MIDI number, honouring a spelling
    override — a half-step-down guitar is written E flat, not D sharp."""
    if spell:
        letter, acc, octave = spell[0], "", spell[1:]
        if octave and octave[0] in "#b":
            acc, octave = octave[0], octave[1:]
        return letter, acc, octave
    n = NOTE_SHARP[midi % 12]
    return n[0], n[1:], str(midi // 12 - 1)


def note_html(midi, spell=None):
    letter, acc, octave = split_note(midi, spell)
    return f"{letter}{ACC_HTML[acc]}{octave}"


def note_js(midi, spell=None):
    letter, acc, octave = split_note(midi, spell)
    return f"{letter}{ACC_JS[acc]}", octave


TUNINGS = [
    dict(id="guitar-standard", instrument="Guitar", name="Standard", label="EADGBE",
         strings=[(6, 40), (5, 45), (4, 50), (3, 55), (2, 59), (1, 64)]),
    dict(id="guitar-drop-d", instrument="Guitar", name="Drop D", label="DADGBE",
         strings=[(6, 38), (5, 45), (4, 50), (3, 55), (2, 59), (1, 64)]),
    dict(id="guitar-dadgad", instrument="Guitar", name="DADGAD", label="DADGAD",
         strings=[(6, 38), (5, 45), (4, 50), (3, 55), (2, 57), (1, 62)]),
    dict(id="guitar-open-g", instrument="Guitar", name="Open G", label="DGDGBD",
         strings=[(6, 38), (5, 43), (4, 50), (3, 55), (2, 59), (1, 62)]),
    dict(id="guitar-open-d", instrument="Guitar", name="Open D", label="DADF#AD",
         strings=[(6, 38), (5, 45), (4, 50), (3, 54), (2, 57), (1, 62)]),
    dict(id="guitar-half-step", instrument="Guitar", name="Half step down", label="E&#9837; standard",
         strings=[(6, 39, "Eb2"), (5, 44, "Ab2"), (4, 49, "Db3"), (3, 54, "Gb3"), (2, 58, "Bb3"), (1, 63, "Eb4")]),
    dict(id="bass-4", instrument="Bass", name="4-string", label="EADG",
         strings=[(4, 28), (3, 33), (2, 38), (1, 43)]),
    dict(id="bass-5", instrument="Bass", name="5-string", label="BEADG",
         strings=[(5, 23), (4, 28), (3, 33), (2, 38), (1, 43)]),
    dict(id="ukulele-gcea", instrument="Ukulele", name="Standard", label="GCEA",
         strings=[(4, 67, None, "high G"), (3, 60), (2, 64), (1, 69)]),
    dict(id="violin-gdae", instrument="Violin", name="Standard", label="GDAE",
         strings=[(4, 55), (3, 62), (2, 69), (1, 76)]),
    dict(id="cello-cgda", instrument="Cello", name="Standard", label="CGDA",
         strings=[(4, 36), (3, 43), (2, 50), (1, 57)]),
    dict(id="banjo-open-g", instrument="Banjo", name="Open G", label="gDGBD",
         strings=[(5, 67, None, "drone"), (4, 50), (3, 55), (2, 59), (1, 62)]),
]

TUNING_BY_ID = {t["id"]: t for t in TUNINGS}


def tuning_strings(t):
    """Normalize a tuning's terse string tuples into dicts."""
    out = []
    for s in t["strings"]:
        num, midi = s[0], s[1]
        spell = s[2] if len(s) > 2 else None
        tag = s[3] if len(s) > 3 else None
        out.append(dict(num=num, midi=midi, spell=spell, tag=tag,
                        ord=ORDINALS[num] + (f" ({tag})" if tag else ""),
                        html=note_html(midi, spell), freq=midi_freq(midi)))
    return out


def tuning_title(t):
    """'Guitar — Standard (EADGBE)', the one label used everywhere."""
    if t["name"] == t["label"]:
        return f"{t['instrument']} &mdash; {t['name']}"
    return f"{t['instrument']} &mdash; {t['name']} ({t['label']})"


def tuning_note_line(t):
    return " ".join(s["html"] for s in tuning_strings(t))


def build_tunings_js():
    """assets/tunings.js — generated from TUNINGS above. Never hand-edited."""
    rows = []
    for t in TUNINGS:
        strings = []
        for s in tuning_strings(t):
            name, octave = note_js(s["midi"], s["spell"])
            strings.append(
                '{ num: %d, midi: %d, name: "%s", octave: "%s", label: "%s%s", ord: "%s" }'
                % (s["num"], s["midi"], name, octave, name, octave, s["ord"])
            )
        rows.append(
            '    {\n      id: "%s",\n      instrument: "%s",\n      name: "%s",\n      label: "%s",\n'
            '      strings: [\n        %s\n      ]\n    }'
            % (t["id"], t["instrument"], t["name"],
               t["label"].replace("&#9837;", "\\u266d").replace("&#9839;", "\\u266f"),
               ",\n        ".join(strings))
        )
    body = ",\n".join(rows)
    return f"""/*!
 * perfecttune.net — instrument tunings.
 *
 * GENERATED BY build.py FROM ITS TUNINGS TABLE. Do not hand-edit: the same
 * table renders the static string chart in every page's HTML, so an edit
 * here alone would put the note a page advertises and the note the needle
 * aims at out of step — which is the one bug a tuner cannot afford.
 *
 * Frequencies are derived from MIDI numbers at whatever concert pitch is
 * set, never stored, so A=442 moves every string on the site at once.
 */
(function (global) {{
  "use strict";

  var TUNINGS = [
{body}
  ];

  var BY_ID = {{}};
  TUNINGS.forEach(function (t) {{
    BY_ID[t.id] = t;
  }});

  function freq(midi, a4Hz) {{
    return (a4Hz || 440) * Math.pow(2, (midi - 69) / 12);
  }}

  /*
   * The frequency band the pitch detector should search for this tuning.
   * Narrow is good twice over: it keeps a neighbouring string's harmonic
   * from being mistaken for a fundamental, and it is what lets the detector
   * decimate hard enough to afford the long analysis window a low B needs.
   * The floor is set below the lowest string (a badly slack string still has
   * to read), the ceiling well above the highest (you fret notes above the
   * open strings).
   */
  function detectRange(tuning, a4Hz) {{
    var lo = Infinity;
    var hi = 0;
    tuning.strings.forEach(function (s) {{
      var f = freq(s.midi, a4Hz);
      if (f < lo) lo = f;
      if (f > hi) hi = f;
    }});
    return {{ fmin: Math.max(22, lo / 1.6), fmax: Math.min(1800, Math.max(hi * 4, 900)) }};
  }}

  global.PerfectTuneTunings = {{
    list: TUNINGS,
    byId: function (id) {{
      return BY_ID[id] || TUNINGS[0];
    }},
    freq: freq,
    detectRange: detectRange
  }};
}})(window);
"""


def tuning_select_html(default_id):
    """The instrument/tuning picker, grouped by instrument, with this page's
    tuning pre-selected server-side so the chart and the picker agree before
    a single line of JavaScript has run."""
    groups = []
    for t in TUNINGS:
        if not groups or groups[-1][0] != t["instrument"]:
            groups.append((t["instrument"], []))
        groups[-1][1].append(t)
    out = ['<select id="tn-tuning">']
    for instrument, items in groups:
        out.append(f'            <optgroup label="{instrument}">')
        for t in items:
            sel = " selected" if t["id"] == default_id else ""
            name = t["name"] if t["name"] == t["label"] else f'{t["name"]} &mdash; {t["label"]}'
            out.append(f'              <option value="{t["id"]}"{sel}>{name}</option>')
        out.append("            </optgroup>")
    out.append("          </select>")
    return "\n".join(out)


def string_rows_html(t):
    rows = ""
    for i, s in enumerate(tuning_strings(t)):
        rows += (
            f'              <tr data-index="{i}" data-midi="{s["midi"]}">\n'
            f'                <th scope="row" class="st-num">{s["ord"]}</th>\n'
            f'                <td class="st-note">{s["html"]}</td>\n'
            f'                <td class="st-freq mono">{s["freq"]:.2f} Hz</td>\n'
            f'                <td class="st-actions">'
            f'<button type="button" class="string-btn tone" data-tone="{i}">'
            f'<span aria-hidden="true">&#9834;</span> Tone<span class="visually-hidden"> for the '
            f'{s["ord"]} string, {s["html"]}</span></button>'
            f'<button type="button" class="string-btn target" data-target="{i}" aria-pressed="false">'
            f'Target<span class="visually-hidden"> the {s["ord"]} string, {s["html"]}</span></button>'
            f"</td>\n"
            f"              </tr>\n"
        )
    return rows


def string_chart_html(t):
    """The static chart. Present and useful with JavaScript off, with the
    microphone denied, and before the page has finished loading — which is
    the whole point: a visitor arriving from a search for "drop d tuner"
    gets the notes and the frequencies immediately, and the needle only if
    they choose to grant a permission they did not ask for."""
    return f"""      <div class="string-chart" id="tn-strings" data-tuning="{t['id']}">
        <div class="string-chart-head">
          <h3 class="string-chart-title" id="tn-tuning-name">{tuning_title(t)}</h3>
          <div class="string-chart-actions">
            <button type="button" class="chip-btn" id="tn-play-all">Play all strings</button>
            <button type="button" class="chip-btn is-on" id="tn-auto" aria-pressed="true">Auto</button>
          </div>
        </div>
        <table class="string-table" id="tn-table">
          <caption class="visually-hidden">{tuning_title(t)}: string number, note and frequency at A4 = 440 Hz</caption>
          <thead>
            <tr><th scope="col">String</th><th scope="col">Note</th><th scope="col">Frequency</th><th scope="col">Reference tone</th></tr>
          </thead>
          <tbody id="tn-tbody">
{string_rows_html(t)}          </tbody>
        </table>
        <p class="hint string-chart-hint" id="tn-target-note">Tap <strong>Tone</strong> to hear a string and tune to it by ear &mdash; no microphone needed. <strong>Auto</strong> is on, so the needle below follows whichever string you are nearest.</p>
      </div>
"""


def tuner_workspace(t, nameplate):
    """The tuner chassis, baked with one tuning. The string chart comes
    first and the microphone panel second, deliberately: the part that works
    without a permission prompt is the part above the fold."""
    return f"""
    <div class="instrument tuner-instrument" data-default-tuning="{t['id']}">
      <div class="nameplate">
        <span class="nameplate-label">{nameplate}</span>
        <span class="status-led" id="tn-status" data-state="idle">Idle</span>
      </div>
      <div class="field-row">
        <div class="field wide"><label for="tn-tuning">Instrument &amp; tuning</label>
          {tuning_select_html(t['id'])}
        </div>
        <div class="field"><label for="tn-a4">Concert pitch (A4)</label><input type="number" id="tn-a4" min="415" max="466" value="440" inputmode="numeric"></div>
      </div>
{string_chart_html(t)}
      <div class="tuner-live">
        <h3 class="live-title">Live pitch &mdash; microphone</h3>
        <div class="gauge-wrap"><div class="gauge-mount" id="tn-gauge"></div></div>
        <div class="screen">
          <div class="note-name" id="tn-note"><span class="octave">&mdash;</span></div>
          <div class="cents-readout" id="tn-cents">Optional. Tap Start listening for a live needle, or tune by ear with the tones above.</div>
        </div>
        <div class="field-row" style="margin-top:14px">
          <div class="field"><label>Detected</label><div class="readout-sub" id="tn-freq" style="font-size:15px">&mdash;</div></div>
          <div class="field"><label>Target</label><div class="readout-sub" id="tn-target" style="font-size:15px">&mdash;</div></div>
        </div>
        <div class="controls-row">
          <button type="button" class="ctrl-btn primary" id="tn-start">Start listening</button>
          <button type="button" class="ctrl-btn stop" id="tn-stop">Stop</button>
        </div>
        <p class="error-msg" id="tn-error"></p>
      </div>
      <p class="hint">Microphone audio is processed on-device and never leaves your browser &mdash; and the chart and reference tones above never need it at all.</p>
    </div>
"""


def tuning_reference_html(ids, heading, blurb, current=None):
    """A comparison table of whole tunings, generated from the same list the
    tuner runs on. Cross-links every tuning that has its own page, except
    back to the page doing the rendering."""
    rows = ""
    for tid in ids:
        t = TUNING_BY_ID[tid]
        strings = tuning_strings(t)
        label = tuning_title(t)
        page = TUNING_PAGE_BY_TUNING.get(tid)
        if page and page != current:
            label = f'<a href="/{page}/">{label}</a>'
        notes = " ".join(s["html"] for s in strings)
        freqs = " ".join("%.2f" % s["freq"] for s in strings)
        rows += (
            f'          <tr><td>{label}</td>'
            f'<td class="mono">{notes}</td>'
            f'<td class="mono">{freqs}</td></tr>\n'
        )
    return f"""
    <section class="content-section">
      <div class="wrap">
        <h2>{heading}</h2>
        <p>{blurb}</p>
        <div class="table-scroll">
        <table class="data-table">
          <thead><tr><th>Tuning</th><th>Strings, low to high</th><th>Frequency (Hz, A4 = 440)</th></tr></thead>
          <tbody>
{rows}          </tbody>
        </table>
        </div>
      </div>
    </section>
"""


# ---------------------------------------------------------------- tools --

TOOLS = [
    dict(
        slug="tuner",
        name="Tuner",
        script="tuner.js",
        deps=["pitch.js", "tunings.js"],
        tagline="Tune by ear's evil twin — real-time pitch, read off a brass needle.",
        description="Free real-time instrument tuner with presets for guitar, bass, ukulele, violin, cello and banjo. Reference tone per string plus microphone pitch detection down to 31 Hz — 100% on-device, audio never leaves your browser.",
        icon='<path d="M4.5 16a7.5 7.5 0 0 1 15 0"/><path d="M12 16L16.2 7.6"/><circle cx="12" cy="16" r="1.6" fill="currentColor" stroke="none"/>',
        intro="Pick an instrument and a tuning, then tune it either way round: tap a string to hear its exact pitch and match it by ear, or start the microphone and read how many cents sharp or flat you are off a brass needle. The reference tones and the string chart need no permissions at all &mdash; the microphone is an upgrade, not a gate.",
        how_to=[
            "Choose your instrument and tuning from the picker &mdash; twelve presets from a 5-string bass to a reentrant ukulele, with every string's target frequency listed underneath.",
            "Tap Tone on any string to hear that exact pitch, and tune to it by ear. Nothing is requested and nothing is recorded; this alone will get an instrument in tune.",
            "For a needle, tap Start listening and allow microphone access. Audio is analyzed locally, frame by frame, and never uploaded.",
            "Leave Auto on to have the needle follow whichever string you are closest to, or tap Target on one string to pin it there &mdash; useful when a string is so far out that the nearest string is the wrong one.",
        ],
        faq=[
            ("Do I need to give microphone permission to use this?", "No. Every string in every preset has a reference tone you can play through your speakers or headphones and tune to by ear, and the full chart of notes and target frequencies is on the page before anything is requested. Microphone access adds a live needle; it is not required for the page to do its job."),
            ("Does my microphone audio get uploaded anywhere?", "No. The microphone stream is only ever connected to a local Web Audio AnalyserNode in your own browser tab — it is analyzed and immediately discarded, frame by frame. Nothing is recorded, saved, or sent to any server."),
            ("Will it detect a 5-string bass low B?", "Yes. That note is 30.87 Hz, and one cycle of it is over 1500 samples at 48 kHz — a conventional 2048-sample tuner window holds barely one and a third cycles and cannot resolve it. Selecting a low tuning here lengthens the analysis window to 16384 samples, and the detector normalizes for the fact that a bass string's fundamental is far quieter than its harmonics, so it reports the fundamental rather than the octave above it."),
            ("Why does it say \"No clear pitch\"?", "The detector needs a single, sustained, reasonably clean tone. Chords, percussive plucks, background noise, or a very quiet signal won't produce a stable enough waveform to lock onto — let the note ring and try again a little louder."),
            ("Can I tune to something other than A440?", "Yes — the concert pitch field accepts any value from 415–466 Hz, so you can match an orchestra tuning to A442 or a period-instrument ensemble tuning lower. Every string's target frequency in the chart is recomputed from that value, so the numbers on screen are always the numbers being aimed at."),
        ],
        related=["metronome", "tone-generator", "ear-trainer"],
        extra=lambda: tuning_reference_html(
            [t["id"] for t in TUNINGS],
            "Every preset, every string",
            "Twelve tunings, generated from the one table the tuner itself runs on &mdash; so what is printed here is exactly what the needle aims at. Frequencies are equal temperament at A4 = 440 Hz; the tunings with a page of their own are linked.",
        ),
        workspace=lambda: tuner_workspace(TUNING_BY_ID["guitar-standard"], "Tuner"),
    ),
    dict(
        slug="metronome",
        name="Metronome",
        script="metronome.js",
        tagline="A pendulum that never drifts — scheduled on the real audio clock.",
        description="Free browser-based metronome with tap tempo, adjustable time signature and an accented downbeat. Sample-accurate lookahead scheduling on the Web Audio clock, not setInterval, so it never drifts.",
        icon='<path d="M7.5 21h9L15 4H9L7.5 21z"/><path d="M12 6.5v9"/><circle cx="12" cy="16.5" r="1.3" fill="currentColor" stroke="none"/>',
        intro="A swinging brass pendulum keeps time the way a real metronome does, but the clicks underneath it are scheduled a fraction of a second ahead on the Web Audio clock rather than fired one at a time from a JavaScript timer — the standard lookahead-scheduler technique that keeps tempo sample-accurate even if the browser tab is busy or briefly throttled.",
        how_to=[
            "Set a tempo with the number field, the slider, or tap it live with Tap Tempo (tap at least twice at the beat you want).",
            "Choose a time signature — beats per bar and the beat unit — to set how the accent lights group.",
            "Tap Start. The first light in each bar (and the pendulum's turnaround) is accented louder unless you switch Accent off.",
            "Change tempo or time signature freely while it's running — the next beat picks up the new setting without a stutter.",
        ],
        faq=[
            ("Why not just use setInterval for the beat?", "setInterval fires late whenever the browser tab is busy, backgrounded, or the OS deprioritizes it — the errors accumulate and the tempo audibly drifts over a long run. Instead, every click's exact start time is scheduled on the Web Audio clock a fraction of a second ahead of when it plays, which is immune to that kind of jitter."),
            ("What does the pendulum represent?", "It's a real-time view of the same schedule driving the clicks — its position each frame is computed directly from the current and next scheduled beat times, easing between them the way a physical pendulum decelerates at each turnaround, so what you see always matches what you hear."),
            ("How does tap tempo work?", "Each tap is timestamped; once you've tapped at least twice, perfecttune averages the intervals between your last several taps and sets the BPM from that average — tap steadily for a few beats for the most accurate result."),
            ("Can I use time signatures like 6/8 or 7/8?", "Yes — set beats-per-bar to the numerator and the beat unit to the denominator (2, 4, 8 or 16); the metronome computes each beat's real duration from both, so a 6/8 bar at a given tempo ticks at the correct eighth-note speed, not a quarter-note one."),
        ],
        related=["tuner", "tone-generator", "bpm-tapper"],
        workspace="""
    <div class="instrument">
      <div class="nameplate">
        <span class="nameplate-label">Metronome</span>
        <span class="status-led" id="mt-status" data-state="idle">Idle</span>
      </div>
      <div class="gauge-wrap"><div class="gauge-mount" id="mt-gauge"></div></div>
      <div class="beat-lights" id="mt-lights"></div>
      <div class="screen">
        <div class="readout"><span id="mt-bpm-display">120</span><span class="unit">BPM</span></div>
      </div>
      <div class="field-row">
        <div class="field field-slider" style="min-width:220px">
          <label for="mt-bpm-slider">Tempo</label>
          <div style="display:flex;align-items:center;gap:10px;width:100%">
            <input type="range" id="mt-bpm-slider" min="30" max="300" value="120">
            <input type="number" id="mt-bpm" min="30" max="300" value="120" style="width:70px">
          </div>
        </div>
      </div>
      <div class="field-row">
        <div class="field"><label for="mt-num">Beats / bar</label>
          <select id="mt-num">
            <option>2</option><option>3</option><option selected>4</option><option>5</option><option>6</option><option>7</option><option>9</option><option>12</option>
          </select>
        </div>
        <div class="field"><label for="mt-den">Beat unit</label>
          <select id="mt-den">
            <option value="2">2</option><option value="4" selected>4</option><option value="8">8</option><option value="16">16</option>
          </select>
        </div>
        <div class="field" style="align-self:flex-end;padding-bottom:8px">
          <label style="display:flex;align-items:center;gap:6px;font-size:13px;text-transform:none;letter-spacing:normal;color:var(--fg)">
            <input type="checkbox" id="mt-accent" checked style="width:auto"> Accent downbeat
          </label>
        </div>
      </div>
      <div class="controls-row">
        <button type="button" class="ctrl-btn primary" id="mt-start">Start</button>
        <button type="button" class="ctrl-btn ghost" id="mt-tap">Tap Tempo</button>
      </div>
    </div>
""",
    ),
    dict(
        slug="tone-generator",
        name="Tone Generator",
        script="tone-generator.js",
        tagline="A steady drone to tune, warm up, or check an interval against.",
        description="Free browser-based tone generator / drone. Sine, square, triangle and sawtooth waveforms, frequency or note-name selection, and a live oscilloscope — 100% client-side, no audio files.",
        icon='<path d="M2 13h3l1.5-5 3 10 3-13 3 8h3.5"/>',
        intro="A steady drone oscillator you can set by frequency in Hz or by note name — useful for tuning by ear against a reference pitch, checking an interval, or just warming up. The scope beneath it draws the actual waveform coming out of the oscillator in real time, not a canned animation.",
        how_to=[
            "Pick a waveform — sine for a pure reference tone, or square/triangle/sawtooth for a brighter, more cutting drone.",
            "Set the frequency directly in Hz, drag the slider, or choose a note name from the dropdown (equal temperament, A4 = 440 Hz).",
            "Tap Play — the oscilloscope starts tracing the live waveform. Adjust frequency, waveform or volume freely while it plays; changes are smoothed to avoid clicks.",
            "Tap Stop when you're done, or just navigate away — the oscillator is always released on Stop or on leaving the page.",
        ],
        faq=[
            ("Is this a pure tone, and can I trust the frequency?", "Yes — the sine waveform is a single oscillator frequency with no harmonics, generated directly by the Web Audio API's OscillatorNode, which is accurate to the sample rate. It's suitable as a genuine reference pitch."),
            ("Why do frequency changes fade instead of jumping instantly?", "An instant frequency or volume jump on a live oscillator produces an audible click or pop. Changes are applied with a short exponential ramp instead, so you can sweep or nudge the pitch smoothly while it's playing."),
            ("What does the oscilloscope actually show?", "It reads the oscillator's real output through an AnalyserNode and redraws the exact waveform shape every animation frame — when you switch from sine to square, you're watching the actual signal change, not an illustration of one."),
            ("What frequency range is available?", "20 Hz to 5000 Hz by direct entry or slider, and the note dropdown covers C0 through B8 — well beyond any acoustic instrument's fundamental range."),
        ],
        related=["tuner", "metronome", "ear-trainer"],
        workspace="""
    <div class="instrument">
      <div class="nameplate">
        <span class="nameplate-label">Tone Generator</span>
        <span class="status-led" id="tg-status" data-state="idle">Idle</span>
      </div>
      <div class="waveform-select">
        <button type="button" class="wave-btn" data-wave="sine" aria-pressed="true"><svg viewBox="0 0 34 20" fill="none" stroke-width="2"><path d="M1 10c3-9 5-9 8 0s5 9 8 0 5-9 8 0 5 9 8 0"/></svg><span>Sine</span></button>
        <button type="button" class="wave-btn" data-wave="square" aria-pressed="false"><svg viewBox="0 0 34 20" fill="none" stroke-width="2"><path d="M1 3h6v14h8V3h8v14h8"/></svg><span>Square</span></button>
        <button type="button" class="wave-btn" data-wave="triangle" aria-pressed="false"><svg viewBox="0 0 34 20" fill="none" stroke-width="2"><path d="M1 17l8-14 8 14 8-14 8 14"/></svg><span>Triangle</span></button>
        <button type="button" class="wave-btn" data-wave="sawtooth" aria-pressed="false"><svg viewBox="0 0 34 20" fill="none" stroke-width="2"><path d="M1 17V3l8 14V3l8 14V3l8 14V3l8 14"/></svg><span>Saw</span></button>
      </div>
      <div class="screen">
        <div class="readout"><span id="tg-freq-readout">440.0</span><span class="unit">Hz</span></div>
      </div>
      <div class="scope-wrap"><canvas id="tg-scope"></canvas></div>
      <div class="field-row">
        <div class="field field-slider" style="min-width:220px">
          <label for="tg-freq-slider">Frequency (Hz)</label>
          <div style="display:flex;align-items:center;gap:10px;width:100%">
            <input type="range" id="tg-freq-slider" min="432" max="1237" value="878">
            <input type="number" id="tg-freq" min="20" max="5000" step="0.1" value="440" style="width:80px">
          </div>
        </div>
        <div class="field wide"><label for="tg-note">Note name</label><select id="tg-note"><option value="">Custom</option></select></div>
        <div class="field field-slider" style="min-width:160px">
          <label for="tg-volume">Volume</label>
          <input type="range" id="tg-volume" min="0" max="100" value="40">
        </div>
      </div>
      <div class="controls-row">
        <button type="button" class="ctrl-btn primary" id="tg-start">Play</button>
      </div>
      <p class="hint">A steady drone — start at a low volume, especially with headphones.</p>
    </div>
""",
    ),
    dict(
        slug="ear-trainer",
        name="Interval Ear Trainer",
        nav="Ear Trainer",
        script="ear-trainer.js",
        tagline="Two notes, one question — name the distance between them.",
        description="Free interval ear trainer. Hear two notes ascending, descending or together and name the interval, from unison to the octave. Equal temperament, A4 = 440 Hz, generated in your browser with no samples.",
        icon='<circle cx="7" cy="17.5" r="2.4" fill="currentColor" stroke="none"/><circle cx="17" cy="15.5" r="2.4" fill="currentColor" stroke="none"/><path d="M9.4 17.5V6.2l10-2v11.3"/><path d="M9.4 8.6l10-2"/>',
        intro="A tuner tells you when one note is right. Interval training is how you learn to hear whether the <em>next</em> note is right — the exact distance between two pitches, named. Press play, listen to two notes, and pick the interval from unison up to the octave. Every pitch is generated on the spot from equal temperament with A4 at 440 Hz, so the intervals you are learning here are the same ones the tuner measures.",
        how_to=[
            "Press Play interval. Two notes sound — ascending by default — and nothing plays until you press it.",
            "Name what you heard with the answer buttons. The first answer you give for each question is the one that counts.",
            "Press Replay to hear it again, or Reveal to give up on the current question — a reveal is scored as a miss.",
            "Narrow the interval set while you're learning (start with the 4th, 5th and octave), then switch direction to descending or harmonic once ascending feels easy.",
        ],
        faq=[
            ("Which intervals does it test?", "All thirteen from unison to the octave: unison (0 semitones), minor 2nd (1), major 2nd (2), minor 3rd (3), major 3rd (4), perfect 4th (5), tritone (6), perfect 5th (7), minor 6th (8), major 6th (9), minor 7th (10), major 7th (11) and the octave (12). The answer buttons and the notes you hear are both generated from that one table, so they cannot disagree with each other."),
            ("What tuning does it use?", "Equal temperament with A4 = 440 Hz: every pitch is 440 × 2^((n−69)/12) for MIDI note n, the same formula the tuner uses to decide what is sharp or flat. A perfect fifth above A4 is E5 at 659.26 Hz — the equal-tempered fifth, about two cents narrower than a pure 3:2 ratio."),
            ("Why does the starting note keep moving?", "Because recognizing a note is a different skill from measuring a distance. Each question picks a fresh root between A3 and A4, so the only thing held constant is the interval itself — you have to hear the gap rather than the notes."),
            ("Should I train ascending, descending or harmonic?", "Ascending first: upward melodic leaps are the easiest to hear and the ones your musical memory is already full of. Descending is a genuinely separate skill and deserves its own practice. Harmonic — both notes at once — is the hardest, because you are judging one blended sound rather than two events."),
        ],
        related=["tuner", "chords-scales", "tone-generator"],
        extra=interval_table_html(),
        workspace="""
    <div class="instrument">
      <div class="nameplate">
        <span class="nameplate-label">Interval Ear Trainer</span>
        <span class="status-led" id="et-status" data-state="idle">Idle</span>
      </div>
      <div class="screen">
        <div class="readout"><span id="et-score">0</span><span class="unit">/ <span id="et-total">0</span> correct</span></div>
        <div class="cents-readout" id="et-feedback" role="status" aria-live="polite">Press Play interval &mdash; two notes will sound, and you name the distance between them.</div>
      </div>
      <div class="stat-row">
        <div class="stat"><div class="stat-label">Streak</div><div class="stat-value" id="et-streak">0</div></div>
      </div>
      <div class="controls-row">
        <button type="button" class="ctrl-btn primary" id="et-play">Play interval</button>
        <button type="button" class="ctrl-btn ghost" id="et-replay">Replay</button>
        <button type="button" class="ctrl-btn ghost" id="et-reveal">Reveal</button>
      </div>
      <div class="answer-grid" id="et-answers"></div>
      <div class="field-row">
        <div class="field wide"><label for="et-set">Interval set</label><select id="et-set"></select></div>
        <div class="field wide"><label for="et-direction">Direction</label><select id="et-direction"></select></div>
        <div class="field"><label for="et-tone">Tone</label>
          <select id="et-tone">
            <option value="triangle" selected>Triangle</option>
            <option value="sine">Sine</option>
            <option value="square">Square</option>
            <option value="sawtooth">Saw</option>
          </select>
        </div>
      </div>
      <p class="hint">Nothing plays until you press a button. A revealed answer counts as a miss, so the score stays honest.</p>
    </div>
""",
    ),
    dict(
        slug="chords-scales",
        name="Chord and Scale Dictionary",
        nav="Chords",
        script="chords-scales.js",
        tagline="Every chord and scale drawn from its formula, spelled the way its key spells it.",
        description="Free chord and scale dictionary. Pick a root and a quality to get the notes, the piano keys and every fretboard position — generated from interval formulas and spelled correctly for the key, not looked up in a table of pictures.",
        icon='<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M9 5v9M15 5v9M3 14h18"/>',
        intro="Pick a root and a quality and this builds the answer from the formula rather than looking it up: a major triad is the root plus 4 and 7 semitones, a major scale is 0-2-4-5-7-9-11, and the note names follow from which scale degree each of those intervals lands on. That is why F&#9839; major here spells A&#9839; and E&#9839; rather than B&#9837; and F — the letter comes from the degree, the accidental from the arithmetic.",
        how_to=[
            "Choose a root note, then a chord quality, scale or mode.",
            "Read the notes and the degree under each one — 1, 3, 5 for a major triad; 1, &#9837;3, 5 for a minor one.",
            "Press Play chord to hear it as a block, or Play as arpeggio for one note at a time. Scales play up, or down.",
            "Use the fretboard map to find a shape: it marks every position of those notes in the first twelve frets of a standard-tuned guitar, with the root in red.",
        ],
        faq=[
            ("Which chords and scales are included?", "Nine chord qualities — major (0-4-7), minor (0-3-7), diminished (0-3-6), augmented (0-4-8), dominant 7th (0-4-7-10), major 7th (0-4-7-11), minor 7th (0-3-7-10), sus2 (0-2-7) and sus4 (0-5-7) — plus the major scale (0-2-4-5-7-9-11), natural minor (0-2-3-5-7-8-10), harmonic minor (0-2-3-5-7-8-11), melodic minor ascending (0-2-3-5-7-9-11), and the seven diatonic modes, which are generated as rotations of the major scale rather than typed out as seven separate rows that could drift apart."),
            ("Why does it write E# instead of F?", "Because a seven-note scale uses each letter name exactly once, and a chord's third has to be spelled as a third of some kind. In F# major the seventh degree sits a semitone below the octave and has to be an E of some sort, so it is E#, not F — writing F would use the letter F twice and leave the scale with no E at all. The tool takes the letter from the degree and then works out the accidental, which is what you would do by hand."),
            ("What is the fretboard diagram showing?", "Every place those notes fall on a standard-tuned guitar (E A D G B E) between the open strings and the twelfth fret, with the root highlighted — a map of the available material, not one fingering. A real voicing picks a handful of those positions, and which handful depends on your hand, the register you want, and the chord you came from."),
            ("What does the double-accidentals note mean?", "Some roots spell out correctly but impractically. The D# major triad is D#–F##–A#, which is right and is almost never written; the same three pitches are notated Eb–G–Bb. When a selection needs double sharps or double flats, the tool still shows the strict spelling and then names the enharmonic key you would actually meet on paper."),
        ],
        related=["ear-trainer", "transposer", "tuner"],
        extra=formula_tables_html(),
        workspace="""
    <div class="instrument">
      <div class="nameplate">
        <span class="nameplate-label">Chord and Scale Dictionary</span>
        <span class="status-led" id="cs-status" data-state="idle">Idle</span>
      </div>
      <div class="field-row">
        <div class="field"><label for="cs-root">Root</label><select id="cs-root"></select></div>
        <div class="field wide"><label for="cs-type">Chord, scale or mode</label><select id="cs-type"></select></div>
      </div>
      <div class="screen">
        <div class="note-name" id="cs-title" style="font-size:34px;line-height:1.25">&mdash;</div>
        <div class="cents-readout" id="cs-formula">&mdash;</div>
      </div>
      <div class="note-chips" id="cs-notes"></div>
      <div class="controls-row">
        <button type="button" class="ctrl-btn primary" id="cs-play">Play chord</button>
        <button type="button" class="ctrl-btn ghost" id="cs-alt-play">Play as arpeggio</button>
      </div>
      <div class="diagram">
        <h3>Piano &mdash; two octaves</h3>
        <div class="diagram-scroll"><div class="piano-mount" id="cs-piano"></div></div>
      </div>
      <div class="diagram">
        <h3>Guitar &mdash; standard tuning, every position in the first 12 frets</h3>
        <div class="diagram-scroll"><div class="fretboard-mount" id="cs-fretboard"></div></div>
      </div>
      <p class="advisory" id="cs-advisory" hidden></p>
      <p class="hint">Notes are spelled for the key you pick, and nothing sounds until you press Play.</p>
    </div>
""",
    ),
    dict(
        slug="bpm-tapper",
        name="BPM Tapper",
        nav="BPM Tapper",
        script="bpm-tapper.js",
        tagline="Tap a couple of bars, read the tempo, hand it to the metronome.",
        description="Free tap tempo tool: tap along with any track to read its BPM, see how steady your taps actually were, and send the tempo straight to the metronome. No microphone, no upload, no permissions.",
        icon='<circle cx="12" cy="12" r="3.2" fill="currentColor" stroke="none"/><path d="M6.6 6.6a7.6 7.6 0 0 0 0 10.8M17.4 6.6a7.6 7.6 0 0 1 0 10.8"/>',
        intro="Tap the pad along with whatever you're listening to and the tempo appears: the BPM is the average of the intervals between your last twelve taps, the same averaging the metronome's own Tap Tempo button does. The steadiness figure beside it is the standard deviation of those intervals, which is how you tell a tempo you actually found from one you only approximated.",
        how_to=[
            "Tap the pad on the beat — twice gives you a number, eight or more gives you a tempo. The space bar taps too.",
            "Watch the steadiness reading: the smaller the &plusmn; milliseconds, the more your own taps agreed with each other.",
            "Press Send to the metronome to open the metronome with this tempo already loaded. Nothing plays there until you press Start.",
            "Pause for more than about two seconds and the next tap begins a fresh measurement, so two different songs never end up in one average.",
        ],
        faq=[
            ("How many taps do I need?", "Two taps give you one interval and therefore a number; eight give you a tempo. Every extra tap adds another interval to the average and the last twelve are kept, so a couple of bars of steady tapping settles the reading to within a fraction of a BPM."),
            ("What is the steadiness figure?", "The standard deviation of the intervals between your taps, in milliseconds. At 120 BPM one beat is 500 ms, so ±10 ms means your taps agreed to within about two percent and the reading is real; ±80 ms means the number is an average of some fairly loose tapping rather than a tempo."),
            ("Does it listen to my music?", "No — there is no microphone involved in this tool at all. It measures the timing of your own taps and nothing else. The only sound it can make is an optional click on each tap, which is switched off by default."),
            ("Why does it reset when I stop?", "A gap of more than 2.2 seconds is treated as the end of a measurement rather than as one very slow beat. Without that rule, coming back after a pause would fold a long idle gap into the average and drag the tempo down with it."),
        ],
        related=["metronome", "tuner", "transposer"],
        workspace="""
    <div class="instrument">
      <div class="nameplate">
        <span class="nameplate-label">BPM Tapper</span>
        <span class="status-led" id="bt-status" data-state="idle">Idle</span>
      </div>
      <div class="screen">
        <div class="readout"><span id="bt-bpm">&mdash;</span><span class="unit">BPM</span></div>
        <div class="cents-readout" id="bt-rounded" role="status" aria-live="polite">Tap at least twice.</div>
      </div>
      <button type="button" class="tap-pad" id="bt-pad">Tap here on the beat<small>or press space</small></button>
      <div class="stat-row">
        <div class="stat"><div class="stat-label">Taps</div><div class="stat-value" id="bt-taps">&mdash;</div></div>
        <div class="stat"><div class="stat-label">Beat length</div><div class="stat-value" id="bt-ms">&mdash;</div></div>
        <div class="stat"><div class="stat-label">Steadiness</div><div class="stat-value" id="bt-steady">&mdash;</div></div>
      </div>
      <p class="hint" id="bt-note-values"></p>
      <div class="controls-row">
        <a class="ctrl-btn primary" id="bt-send" aria-disabled="true">Send to the metronome</a>
        <button type="button" class="ctrl-btn ghost" id="bt-reset">Reset</button>
      </div>
      <div class="field-row">
        <div class="field" style="min-width:0">
          <label style="display:flex;align-items:center;gap:6px;font-size:13px;text-transform:none;letter-spacing:normal;color:var(--fg)">
            <input type="checkbox" id="bt-click" style="width:auto"> Click on each tap
          </label>
        </div>
      </div>
      <p class="hint">Your taps are the only thing that can make a sound here, and only with the click switched on.</p>
    </div>
""",
    ),
    dict(
        slug="transposer",
        name="Chord Transposer",
        nav="Transposer",
        script="transposer.js",
        tagline="Move a progression to a new key with the accidentals spelled properly.",
        description="Free chord transposer. Move a progression up or down by any number of semitones and get the chords spelled for the key you land in, with slash basses and quality suffixes preserved exactly as typed.",
        icon='<path d="M4 9h13l-3.4-3.4M20 15H7l3.4 3.4"/>',
        intro="Type a progression, choose how far to move it, and get the chords back spelled for the key you land in. Quality suffixes are never touched — m7&#9837;5 and add9 come out exactly as they went in — and the enharmonic convention is stated rather than guessed at: by default every root is spelled as the nearest spelling to the target key on the circle of fifths, so three semitones up from C gives E&#9837;, not D&#9839;.",
        how_to=[
            "Type or paste your chords into the top box, separated by spaces or line breaks.",
            "Choose how far to move them. Each step in the dropdown is labelled with its interval name, so &ldquo;+7&rdquo; also reads &ldquo;perfect 5th up&rdquo;.",
            "Leave spelling on Auto to have the result spelled for the target key, or force sharps or flats if your chart needs them.",
            "Read the chips, or copy the plain-text result — it keeps your original spacing and line breaks.",
        ],
        faq=[
            ("How does it choose between F# and Gb?", "Auto spells every root as the nearest spelling to the target key on the circle of fifths. Transposing C Am F G7 up three semitones lands in E♭, a key with three flats, so the result is E♭ Cm A♭ B♭7 rather than the D♯ Cm G♯ A♯7 that a sharps-only tool would hand you. Where two spellings sit equally far from the key — F♯ and G♭ are both six accidentals — it takes the sharp. The Sharps and Flats options override the whole thing."),
            ("What happens to chord qualities and slash chords?", "Nothing at all happens to the quality: everything after the root letter and its accidental is copied through untouched, so 7, maj7, m7b5, sus4, add9 and 13#11 all survive intact. A slash bass is parsed as its own note and transposed with the chord, so Am7/G up two semitones is Bm7/A."),
            ("Can I paste a lyric sheet?", "Not usefully. Anything starting with a letter from A to G is treated as a chord symbol, so a word like “And” would be transposed along with the chords. Give it chords — anything it does not read as one is passed through untouched and listed underneath the result."),
            ("Does transposing change how the progression sounds?", "In equal temperament the intervals inside every chord are preserved exactly, which is the whole point of twelve equal semitones, so the harmony is identical. What changes is the register, which open strings and easy keyboard shapes are available, and how the voicings sit under the hand."),
        ],
        related=["chords-scales", "ear-trainer", "metronome"],
        workspace="""
    <div class="instrument">
      <div class="nameplate">
        <span class="nameplate-label">Chord Transposer</span>
        <span class="status-led" data-state="idle">Silent tool</span>
      </div>
      <div class="io-block">
        <label for="tr-input">Chords in</label>
        <textarea id="tr-input" rows="3" spellcheck="false">C  Am  F  G7</textarea>
      </div>
      <div class="field-row">
        <div class="field wide"><label for="tr-semitones">Transpose by</label><select id="tr-semitones"></select></div>
        <div class="field wide"><label for="tr-spelling">Spelling</label>
          <select id="tr-spelling">
            <option value="auto" selected>Auto &mdash; spell for the target key</option>
            <option value="sharps">Sharps &mdash; C# D# F# G# A#</option>
            <option value="flats">Flats &mdash; Db Eb Gb Ab Bb</option>
          </select>
        </div>
      </div>
      <div class="controls-row">
        <button type="button" class="ctrl-btn ghost" id="tr-down">&minus;1 semitone</button>
        <button type="button" class="ctrl-btn ghost" id="tr-up">+1 semitone</button>
      </div>
      <div class="chord-chips" id="tr-chips"></div>
      <p class="summary-line" id="tr-summary" role="status" aria-live="polite"></p>
      <p class="advisory" id="tr-note" hidden></p>
      <div class="io-block">
        <label for="tr-text">Chords out</label>
        <textarea id="tr-text" class="io-text" rows="3" readonly></textarea>
      </div>
      <div class="controls-row">
        <button type="button" class="ctrl-btn primary" id="tr-copy">Copy result</button>
      </div>
      <p class="hint">Enharmonic convention: Auto spells each root as the nearest spelling to the target key on the circle of fifths.</p>
    </div>
""",
    ),
]

TOOL_BY_SLUG = {t["slug"]: t for t in TOOLS}

# Nav follows the tool list, so a new tool can never be added without one.
NAV_ITEMS = [("", "Home")] + [(t["slug"], t.get("nav", t["name"])) for t in TOOLS]


# ------------------------------------------------------------ tuner pages --
# One page per instrument and per alternate tuning. Structure lives here;
# the prose lives in PRESET_COPY below. Both are keyed on the slug, and the
# tuning is a TUNINGS id — so a page cannot advertise a tuning that does not
# exist, and its chart cannot disagree with its heading.

PRESET_PAGES = [
    dict(slug="guitar-tuner", nav="Guitar", h1="Guitar Tuner", tuning="guitar-standard",
         related=["chords-scales", "metronome", "transposer"],
         ref=["guitar-standard", "guitar-drop-d", "guitar-dadgad", "guitar-open-g", "guitar-open-d", "guitar-half-step"],
         ref_heading="Every guitar tuning in the picker",
         ref_blurb="All six are selectable from the dropdown above without leaving this page, and the four with the most repertoire behind them have a page of their own. The frequencies are the ones the needle actually aims at, derived from equal temperament at A4 = 440 Hz &mdash; change concert pitch in the tuner and every one of them moves with it."),
    dict(slug="bass-tuner", nav="Bass", h1="Bass Tuner", tuning="bass-4",
         related=["metronome", "bpm-tapper", "tone-generator"],
         ref=["bass-4", "bass-5"],
         ref_heading="4-string and 5-string bass",
         ref_blurb="The 5-string adds a low B a fourth below the E, at 30.87 Hz &mdash; low enough that most laptop and phone speakers cannot reproduce its fundamental at all, and low enough that it is the one note a short-window tuner gets wrong. Switch between the two in the picker above."),
    dict(slug="ukulele-tuner", nav="Ukulele", h1="Ukulele Tuner", tuning="ukulele-gcea",
         related=["chords-scales", "metronome", "ear-trainer"],
         ref=["ukulele-gcea"],
         ref_heading="Standard ukulele tuning",
         ref_blurb="Soprano, concert and tenor ukuleles all use the same GCEA pitches; only the scale length and the string gauges change. Note the order: the 4th string is the highest-sounding one, not the lowest."),
    dict(slug="violin-tuner", nav="Violin", h1="Violin Tuner", tuning="violin-gdae",
         related=["ear-trainer", "tone-generator", "chords-scales"],
         ref=["violin-gdae", "cello-cgda"],
         ref_heading="Violin and cello, both tuned in fifths",
         ref_blurb="Both instruments are tuned in perfect fifths; the cello sits an octave and a fifth below the violin, so the two share only the pitch names, not the octaves. Equal-tempered fifths are about two cents narrower than the pure 3:2 fifth a string player tunes by ear, which is why the numbers below and your ear can politely disagree."),
    dict(slug="banjo-tuner", nav="Banjo", h1="Banjo Tuner", tuning="banjo-open-g",
         related=["chords-scales", "metronome", "bpm-tapper"],
         ref=["banjo-open-g", "guitar-open-g"],
         ref_heading="Banjo open G, and the guitar tuning named after it",
         ref_blurb="The 5-string banjo's open G is where the instrument lives; the guitar tuning of the same name reaches the same chord with six strings and a different voicing. Both sound a G major triad with nothing fretted, which is what open tuning means."),
    dict(slug="cello-tuner", nav="Cello", h1="Cello Tuner", tuning="cello-cgda",
         related=["ear-trainer", "tone-generator", "metronome"],
         ref=["cello-cgda", "violin-gdae"],
         ref_heading="Cello, and the violin a twelfth above it",
         ref_blurb="The cello's C2 at 65.41 Hz is the lowest open string on this site apart from the bass, and it needs the same long analysis window a bass does. The violin's strings are laid out in the same fifths, an octave and a fifth higher."),
    dict(slug="drop-d-tuner", nav="Drop D", h1="Drop D Tuner", tuning="guitar-drop-d",
         related=["chords-scales", "transposer", "metronome"],
         ref=["guitar-standard", "guitar-drop-d"],
         ref_heading="Drop D against standard tuning",
         ref_blurb="One string moves and five do not. The 6th drops a whole tone from E2 to D2 &mdash; 82.41 Hz down to 73.42 Hz &mdash; and everything above it stays exactly where it was, which is why drop D is the cheapest alternate tuning there is to get into and out of."),
    dict(slug="dadgad-tuner", nav="DADGAD", h1="DADGAD Tuner", tuning="guitar-dadgad",
         related=["chords-scales", "ear-trainer", "transposer"],
         ref=["guitar-standard", "guitar-drop-d", "guitar-dadgad"],
         ref_heading="How DADGAD is reached from standard",
         ref_blurb="Three strings move down a whole tone each: the 6th E2 to D2, the 2nd B3 to A3, and the 1st E4 to D4. The 5th, 4th and 3rd never move. Read the three rows below as one instruction and the retune takes under a minute."),
    dict(slug="open-g-tuner", nav="Open G", h1="Open G Tuner", tuning="guitar-open-g",
         related=["chords-scales", "transposer", "metronome"],
         ref=["guitar-standard", "guitar-open-g", "guitar-open-d", "banjo-open-g"],
         ref_heading="Open G, open D, and the banjo tuning behind both",
         ref_blurb="An open tuning sounds a full chord with no fingers on the fretboard. Open G gives a G major triad, open D gives a D major triad with the same shapes moved, and the 5-string banjo has been tuned to open G all along &mdash; which is where guitarists borrowed it from."),
    dict(slug="half-step-down-tuner", nav="Half Step", h1="Half Step Down Tuner", tuning="guitar-half-step",
         related=["transposer", "chords-scales", "metronome"],
         ref=["guitar-standard", "guitar-half-step"],
         ref_heading="E flat standard against E standard",
         ref_blurb="Every string moves down by exactly one semitone, so every interval between them is unchanged and every shape you know still works &mdash; the whole instrument has simply been transposed. Note the spelling: these are flats, because the key you land in from a flat key is a flat key."),
]

PRESET_BY_SLUG = {p["slug"]: p for p in PRESET_PAGES}

# Which page is the canonical home of each tuning, for cross-linking the
# reference tables. Tunings with no page of their own stay unlinked.
TUNING_PAGE_BY_TUNING = {p["tuning"]: p["slug"] for p in PRESET_PAGES}
TUNING_PAGE_BY_TUNING["bass-5"] = "bass-tuner"

# The second nav row, carried on every page. The main tool nav stays at
# seven items; ten more would drown it, and these are all one tool anyway.
PRESET_NAV = [("tuner", "Chromatic")] + [(p["slug"], p["nav"]) for p in PRESET_PAGES]

ARTICLES = [
    dict(
        slug="how-instrument-tuners-actually-work",
        title="How Instrument Tuners Actually Work: Pitch Detection Explained",
        description="A plain-language look at autocorrelation pitch detection — how a browser tuner turns raw microphone audio into a note name and a cents-off reading, entirely on your device.",
    ),
    dict(
        slug="why-your-metronome-should-not-use-setinterval",
        title="Why Your Metronome Should Never Use setInterval (And How Ours Does)",
        description="The Web Audio lookahead scheduler pattern that keeps a software metronome sample-accurate, and why naive setInterval-per-beat timers drift.",
    ),
    dict(
        slug="practicing-with-a-drone-tone",
        title="A Musician's Guide to Practicing With a Drone Tone",
        description="How singers and instrumentalists use a steady reference pitch to build intonation, tune by ear, and hear intervals — and how to set one up for your own practice.",
    ),
]

# ---------------------------------------------------------------- helpers --

def head(title, description, canonical_path, json_ld, extra_style=""):
    url = SITE + canonical_path
    return f"""<!doctype html>
<html lang="en">
<head>
  {THEME_SCRIPT}
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <link rel="canonical" href="{url}">
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
  <meta name="theme-color" content="#241a14">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="perfecttune.net">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{url}">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{description}">
  <link rel="stylesheet" href="/assets/style.css">
  {extra_style}
  <script type="application/ld+json">{json_ld}</script>
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={PUB_ID}" crossorigin="anonymous"></script>
</head>
"""


def preset_nav(current_slug):
    """The tuner-preset strip, under the main nav on every page. Ten more
    entries in the header itself would swamp seven tools; as its own row it
    also gives every page on the site a direct link to every tuner, which is
    the internal linking these pages need to be found in the first place.
    The Chromatic entry keeps its data-panel-link so it still switches
    panels rather than reloading when it is clicked on the homepage."""
    items = []
    for slug, label in PRESET_NAV:
        current = ' aria-current="page"' if slug == current_slug else ""
        panel = ' data-panel-link="tuner"' if slug == "tuner" else ""
        items.append(f'        <li><a href="/{slug}/"{panel}{current}>{label}</a></li>')
    links = "\n".join(items)
    return f"""  <nav class="preset-nav" aria-label="Instrument tuners">
    <div class="wrap">
      <span class="preset-nav-label">Tuners</span>
      <ul>
{links}
      </ul>
    </div>
  </nav>
"""


def header(current_slug, section=None):
    """section marks the tool a page belongs to without claiming to BE that
    page: /drop-d-tuner/ is part of the Tuner, but aria-current="page" on the
    Tuner link there would be a lie to a screen reader."""
    links = []
    for slug, label in NAV_ITEMS:
        href = "/" if slug == "" else f"/{slug}/"
        current = ' aria-current="page"' if slug == current_slug else ""
        cls = ' class="is-section"' if section and slug == section and slug != current_slug else ""
        panel = slug
        links.append(f'      <li><a href="{href}" data-panel-link="{panel}"{current}{cls}>{label}</a></li>')
    nav = "\n".join(links)
    return f"""<body>
  <header class="site-header">
    <div class="wrap">
      <a href="/" class="wordmark" data-panel-link=""><span class="fork">&#127932;</span> perfecttune</a>
      <button type="button" class="nav-toggle" id="nav-toggle" aria-expanded="false" aria-controls="tool-nav" aria-label="Toggle menu">&#9776;</button>
      <ul class="tool-nav" id="tool-nav">
{nav}
      </ul>
      <div class="header-controls">
        <button type="button" class="theme-toggle" id="theme-toggle" aria-label="Toggle light and dark theme"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg></button>
      </div>
    </div>
  </header>
{preset_nav(current_slug)}"""


def footer_and_close(scripts, faq_json_ld=None):
    faq_script = f'<script type="application/ld+json">{faq_json_ld}</script>\n  ' if faq_json_ld else ""
    script_tags = "\n  ".join(f'<script src="/assets/{s}"></script>' for s in scripts)
    return f"""  <footer class="site-footer">
    <div class="wrap">
      <p class="footer-tag">perfecttune.net &mdash; a musician's toolkit. Audio is processed on-device and never leaves your browser.</p>
      <ul class="footer-links">
        <li><a href="/privacy/">Privacy</a></li>
        <li><a href="/terms/">Terms</a></li>
      </ul>
    </div>
  </footer>
  {ERABBIT}
  {faq_script}<script src="/assets/notes.js"></script>
  <script src="/assets/theory.js"></script>
  <script src="/assets/audio.js"></script>
  <script src="/assets/gauge.js"></script>
  {script_tags}
  <script src="/assets/app.js"></script>
</body>
</html>
"""


def privacy_note_html():
    return """        <p class="privacy-note"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3z"/></svg> Microphone audio is processed entirely in your browser and never uploaded.</p>"""


def faq_jsonld(faq):
    import json as _json
    entities = [
        {
            "@type": "Question",
            "name": q,
            "acceptedAnswer": {"@type": "Answer", "text": a},
        }
        for q, a in faq
    ]
    return _json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": entities}, ensure_ascii=False)


def resolve(value):
    """A tool's workspace/extra may be a callable when it needs data defined
    further down the file (the tuner's chart needs the preset page map).
    Everything else stays a plain string."""
    return value() if callable(value) else value


def workspace_of(t):
    return resolve(t["workspace"])


def extra_of(t):
    return resolve(t.get("extra", ""))


def scripts_for(tools):
    """Dependency-ordered, de-duplicated script list: a tool's deps always
    load before the tool itself."""
    out = []
    for t in tools:
        for s in list(t.get("deps", [])) + [t["script"]]:
            if s not in out:
                out.append(s)
    return out


def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


# ---------------------------------------------------------------- homepage --

def build_homepage():
    title = "perfecttune.net &mdash; Tuner, Metronome, Ear Trainer &amp; Practice Tools"
    description = "Free browser-based musician's toolkit: a real-time instrument tuner, a sample-accurate metronome, a drone tone generator, an interval ear trainer, a chord and scale dictionary, a BPM tapper and a chord transposer. 100% client-side &mdash; nothing you play or say ever leaves your device."
    json_ld = (
        '{"@context":"https://schema.org","@type":"WebSite","name":"perfecttune.net",'
        '"url":"https://perfecttune.net/",'
        f'"description":"{description}"}}'
    )
    h = head(title, description, "/", json_ld)
    b = header("")

    hero = f"""  <main>
    <section class="hero">
      <svg class="hero-waveform" viewBox="0 0 1000 200" preserveAspectRatio="none" aria-hidden="true">
        <path d="M0 100 Q 62 20 125 100 T 250 100 T 375 100 T 500 100 T 625 100 T 750 100 T 875 100 T 1000 100" fill="none" stroke="var(--brass-500)" stroke-width="2" opacity="0.25"/>
        <path d="M0 100 Q 62 170 125 100 T 250 100 T 375 100 T 500 100 T 625 100 T 750 100 T 875 100 T 1000 100" fill="none" stroke="var(--teal-600)" stroke-width="2" opacity="0.15"/>
      </svg>
      <div class="wrap">
        <p class="eyebrow">Tuner &middot; Metronome &middot; Ear Trainer &middot; Chords &middot; Tempo &middot; Transposer</p>
        <h1>A whole practice session, one brass panel.</h1>
        <p class="lede">Tune up, set a tempo, train your ear, look up a chord and move a progression into a new key &mdash; seven instruments built like pieces of analog gear, all running entirely in this browser tab.</p>
        {privacy_note_html()}
      </div>
    </section>

    <section class="panel" id="overview-panel">
      <div class="wrap">
        <h2 class="visually-hidden">All tools</h2>
        <div class="tool-grid">
"""
    for t in TOOLS:
        hero += f"""          <a class="tool-card" href="/{t['slug']}/" data-panel-link="{t['slug']}">
            <span class="chip"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{t['icon']}</svg></span>
            <h3>{t['name']}</h3>
            <p>{t['tagline']}</p>
          </a>
"""
    hero += """        </div>
      </div>
    </section>
"""

    panels = ""
    for t in TOOLS:
        panels += f"""    <section class="panel" data-panel="{t['slug']}" data-title="{t['name']} &mdash; perfecttune.net" hidden>
      <div class="wrap">
        <div class="panel-head">
          <h2 tabindex="-1">{t['name']}</h2>
          <a class="back-to-tools" href="/" data-panel-link="">&larr; All tools</a>
        </div>
        <p>{t['intro']}</p>
{workspace_of(t)}
        <p style="margin-top:16px;font-size:14px"><a href="/{t['slug']}/#how-it-works">Full guide &amp; FAQ for the {t['name']} &rarr;</a></p>
      </div>
    </section>
"""

    tuner_pages = """    <section class="content-section" id="instrument-tuners">
      <div class="wrap">
        <h2>Tune your instrument</h2>
        <p>The same tuner with the strings already filled in: every string's target frequency printed on the page, a reference tone on each one, and a needle if you want to give it a microphone. Alternate guitar tunings have their own pages too.</p>
        <div class="preset-grid">
"""
    for p in PRESET_PAGES:
        tuner_pages += f"""          <a class="preset-card" href="/{p['slug']}/">
            <span class="preset-card-name">{p['h1']}</span>
            <span class="preset-card-notes mono">{tuning_note_line(TUNING_BY_ID[p['tuning']])}</span>
          </a>
"""
    tuner_pages += """        </div>
      </div>
    </section>
"""

    learn_more = """    <section class="content-section">
      <div class="wrap">
        <h2>Learn more</h2>
        <ul>
"""
    for a in ARTICLES:
        learn_more += f'          <li><a href="/articles/{a["slug"]}.html">{a["title"]}</a> &mdash; {a["description"]}</li>\n'
    learn_more += """        </ul>
      </div>
    </section>
  </main>
"""

    body = b + hero + panels + tuner_pages + learn_more
    scripts = scripts_for(TOOLS)
    full = h + body + footer_and_close(scripts)
    write("index.html", full)


# ---------------------------------------------------------------- tool pages --

def build_tool_page(t):
    title = f"{t['name']} &mdash; Free, Private, Browser-Only | perfecttune.net"
    description = t["description"]
    json_ld = (
        '{"@context":"https://schema.org","@type":"WebApplication","name":"'
        + t["name"] + " \\u2014 perfecttune.net" + '",'
        f'"url":"{SITE}/{t["slug"]}/",'
        '"applicationCategory":"MusicApplication",'
        '"operatingSystem":"Any (runs in browser)",'
        f'"description":"{description}",'
        '"offers":{"@type":"Offer","price":"0","priceCurrency":"USD"},'
        '"publisher":{"@type":"Organization","name":"perfecttune.net"}}'
    )
    h = head(title, description, f"/{t['slug']}/", json_ld)
    b = header(t["slug"])

    priv = privacy_note_html() + "\n" if t["slug"] == "tuner" else ""

    body = f"""  <main>
    <section class="panel">
      <div class="wrap">
        <div class="panel-head">
          <h1 tabindex="-1">{t['name']}</h1>
          <a class="back-to-tools" href="/" data-panel-link="">&larr; All tools</a>
        </div>
        <p>{t['intro']}</p>
{priv}{workspace_of(t)}
      </div>
    </section>

    <section class="content-section" id="how-it-works">
      <div class="wrap">
        <h2>How to use the {t['name']}</h2>
        <div class="how-to">
          <ol>
"""
    for step in t["how_to"]:
        body += f"        <li>{step}</li>\n"
    body += """          </ol>
        </div>
      </div>
    </section>

    <section class="content-section">
      <div class="wrap">
        <h2>FAQ</h2>
        <dl class="faq">
"""
    for q, a in t["faq"]:
        body += f"        <dt>{q}</dt>\n        <dd>{a}</dd>\n"
    body += """        </dl>
      </div>
    </section>
"""

    # Reference tables (intervals, chord and scale formulas) for the tools that
    # have one — real page content for a reader without JavaScript, and the
    # same numbers the tool itself runs on.
    body += extra_of(t)

    body += """
    <section class="content-section">
      <div class="wrap">
        <h2>Related tools</h2>
        <div class="related-links">
"""
    for rel in t["related"]:
        rt = TOOL_BY_SLUG[rel]
        body += f'        <a href="/{rel}/">{rt["name"]} &rarr;</a>\n'
    body += """        </div>
      </div>
    </section>
  </main>
"""

    full = h + b + body + footer_and_close(scripts_for([t]), faq_jsonld(t["faq"]))
    write(f"{t['slug']}/index.html", full)
    write(f"{t['slug']}.html", full)


# The prose for the tuner pages. Kept apart from PRESET_PAGES above so the
# structure of a page — its tuning, its cross-links, its reference table —
# stays readable at a glance instead of being buried in copy.
PRESET_COPY = {
    'guitar-tuner': dict(
        title='Guitar Tuner - Standard, Drop D, DADGAD and More',
        description='Tune a guitar in your browser using reference tones for every string or live microphone pitch detection. Standard, drop D, DADGAD, open G and open D.',
        intro='Standard tuning is E2 82.41 Hz, A2 110.00 Hz, D3 146.83 Hz, G3 196.00 Hz, B3 246.94 Hz and E4 329.63 Hz, sixth string to first. Tap any string in the chart and the browser plays that exact pitch, so the whole guitar can be tuned by ear with no microphone at all. Allow the mic and you get live pitch detection as well &mdash; the note you are actually playing, read on the fly and measured against the target.',
        how_to=[
            'Choose your tuning from the selector &mdash; standard EADGBE is loaded by default, and drop D, DADGAD, open G, open D and half step down sit alongside it.',
            'Tap a string in the chart to hear its reference pitch, then turn the peg until the beating between your string and the tone slows to nothing.',
            'For live readings, allow microphone access and play one string at a time, letting the note ring while the needle settles.',
            'Go through all six strings and then start again from the sixth, because every string you tighten pulls the neck a little further forward and drags the others flat.',
        ],
        faq=[
            ('Can I tune without a microphone?',
             'Yes, and nothing is missing if you do. Every string in the chart is a playable reference tone at its exact frequency, so with the mic denied or absent you still have all six pitches on tap. Play the tone, play your string, and listen for the beating between them to slow down and stop. The microphone only adds the second mode: live detection of the pitch you are actually producing, reported in cents.'),
            ('Is anything I play sent to a server?',
             'No. The microphone stream is only ever connected to a local Web Audio AnalyserNode in your own browser tab, where it is analyzed for pitch and discarded frame by frame. The detection itself &mdash; a normalized square difference autocorrelation with McLeod peak picking &mdash; runs on your own device. Nothing is recorded, saved, or sent anywhere, and closing the tab ends the stream.'),
            ('Why is my guitar out of tune again a minute later?',
             'Usually one of three things. New strings are still stretching and will keep dropping for their first few hours. Tuning down to a note leaves the winding slack at the post, so always arrive from below &mdash; if you overshoot, go flat and come back up. And the neck behaves like a spring, so tightening one string releases a little tension on the other five. A second pass answers all three.'),
            ('What does the A4 setting do?',
             'It sets the reference the entire chart is derived from. Every frequency above follows from A4 by equal temperament, so moving A4 moves all six targets together. The default is 440 Hz and the range is 415 to 466 Hz. Use 415 Hz for baroque pitch, or match a piano that has settled a few Hz off standard rather than tuning the guitar into a fight with it.'),
        ],
        sections=[
            ('Tuning by ear with the reference tones',
             '<p>The reference tones are not a fallback for when the microphone fails. Matching two pitches by ear is quick and it is the only method that works on a noisy stage, where a mic hears the drummer as clearly as it hears you.</p><p>What you are listening for is beating. Two pitches close but not identical reinforce and cancel each other in turn, and the combined sound pulses at the rate of their difference in Hz &mdash; a string two Hz below the reference wobbles twice a second. Tighten it and the wobble slows; when it disappears the two pitches are identical. There is no in-between reading to interpret.</p><p>Beating is easiest to hear on the middle strings, D3 146.83 Hz and G3 196.00 Hz. Down on E2 82.41 Hz the pulses are slow and easy to miss, so sound the reference and the string one after the other instead of together, and judge which of the two sits higher.</p>'),
            ('The five alternate tunings on this page',
             '<p>Switching tuning rewrites both halves of the tool: the reference tones you tap, and the targets that live detection measures against.</p><ul><li><strong>Drop D</strong> moves the sixth string alone, E2 82.41 Hz down to D2 73.42 Hz.</li><li><strong>DADGAD</strong> takes drop D and lowers the second and first strings a whole tone as well, to A3 220.00 Hz and D4 293.66 Hz.</li><li><strong>Open G</strong> drops the sixth, fifth and first so the open set sounds a G major chord: D2 73.42, G2 98.00, D3 146.83, G3 196.00, B3 246.94 and D4 293.66 Hz.</li><li><strong>Open D</strong> lowers the sixth, third, second and first, giving D2 73.42, A2 110.00, D3 146.83, F&#9839;3 185.00, A3 220.00 and D4 293.66 Hz.</li><li><strong>Half step down</strong> takes every string down one semitone, to E&#9837;2 77.78, A&#9837;2 103.83, D&#9837;3 138.59, G&#9837;3 185.00, B&#9837;3 233.08 and E&#9837;4 311.13 Hz.</li></ul>'),
        ],
    ),
    'bass-tuner': dict(
        title='Bass Guitar Tuner - 4 String and 5 String, Low B to G',
        description='Tune a 4 or 5 string bass in the browser. Reference tones from E1 41.20 Hz up to G2 98.00 Hz, plus live mic detection that resolves a low B at 30.87 Hz.',
        intro='A four string bass sits at E1 41.20 Hz, A1 55.00 Hz, D2 73.42 Hz and G2 98.00 Hz; a five string adds a low B0 at 30.87 Hz underneath all of it. Tap a string to hear its pitch played back and tune by ear, or allow the microphone for live detection. The analysis window lengthens automatically down there, which is what makes a 31 Hz fundamental readable at all.',
        how_to=[
            'Select four or five string, then tap any string in the chart to hear its target pitch through your speakers or headphones.',
            'Allow microphone access if you want live readings, and play one string at a time with the others damped under your palm.',
            'Pluck gently over the neck pickup rather than hard at the bridge, because a soft pluck puts more energy into the fundamental and less into the harmonics that confuse a reading.',
            'Give the low strings a moment to settle, since the tuner needs several complete cycles of a slow wave before it can report a stable number.',
        ],
        faq=[
            ('Will it detect the low B on a five string?',
             'Yes. B0 is 30.87 Hz, and the analysis window lengthens automatically when the tuner is looking that low. One cycle of a 30.87 Hz wave lasts about 32 milliseconds, so half a dozen cycles take roughly a fifth of a second of continuous audio &mdash; the window has to be long enough to contain them or there is nothing periodic to measure. Let the note ring rather than stabbing at it.'),
            ('Why does the reading jump to a note an octave up?',
             "Because a bass string's fundamental is weak next to its harmonics. Pluck hard near the bridge and the second or third partial can dominate the waveform, and a naive detector locks onto that instead. Autocorrelation on the normalized square difference function measures the repeat period of the whole wave rather than the loudest partial, which is why it holds the octave &mdash; but plucking softly over the neck pickup with the tone rolled back makes its job much easier."),
            ('Should I tune through the amp or acoustically?',
             'Either, but keep the amp quiet. The microphone hears the room, so a cabinet pointed straight at the machine will overload the input and can start feeding back. Tuning acoustically works because the string itself is what the mic is reading, not the pickup. If your bass is very quiet unplugged, move it closer to the microphone rather than digging in harder, since a hard pluck bends the pitch sharp for the first moments.'),
            ('Do I need the microphone at all?',
             'No. Every string in the chart plays its own reference tone, so the whole instrument can be tuned by ear with the mic denied. One caution about playback: E1 41.20 Hz and B0 30.87 Hz are below what most laptop speakers can reproduce, so use headphones or a real speaker. Otherwise you will be matching a harmonic of the reference rather than the reference, and land an octave high.'),
        ],
        sections=[
            ('Why low strings need a long analysis window',
             '<p>Autocorrelation works by sliding a copy of the incoming waveform against itself and finding the lag at which it best matches. That lag is the period, and the period inverted is the frequency. The method needs several complete cycles inside the buffer before it can call a match with confidence.</p><p>At the top of the bass that is trivial. G2 98.00 Hz repeats every 10 milliseconds, so even a short window already holds dozens of repetitions. At the bottom it is not. B0 30.87 Hz repeats roughly every 32 milliseconds and E1 41.20 Hz every 24, so the buffer has to grow to hold the same evidence. That is the tradeoff you feel as a slightly slower reading on the low strings &mdash; a longer window is the price of resolving a slow wave, not a fault.</p>'),
            ('Making the low B sound like a note',
             '<p>The B string is the one most likely to feel dead, and the cause is usually mechanical rather than a tuning error. B0 30.87 Hz on a 34 inch scale is a long, slack string; the same pitch on a 35 inch scale carries more tension at the same gauge, which is the entire reason longer scale five strings exist. Before blaming the tuner, check the following.</p><ul><li>Break angle over the nut and saddle. A B string that does not sit down firmly will rattle, and a rattling string reads as unstable pitch.</li><li>Pluck strength. Hit it hard and it starts sharp, so wait for the note to settle before you judge the number.</li><li>Order. Tune B first, work up to G2 98.00 Hz, then come back to B once the neck is carrying the full set of tension.</li></ul>'),
        ],
    ),
    'ukulele-tuner': dict(
        title='Ukulele Tuner - Standard GCEA with a Reentrant High G',
        description='Tune a soprano, concert or tenor ukulele to GCEA. Tap a string for its reference tone, from G4 392.00 Hz down to C4 261.63 Hz, or use live mic detection.',
        intro='Standard ukulele tuning is G4 392.00 Hz, C4 261.63 Hz, E4 329.63 Hz and A4 440.00 Hz, fourth string to first. Read those numbers again and the oddity shows up: the fourth string is not the lowest one. Tap any string in the chart to hear its exact pitch and tune by ear, or allow the microphone for live detection, which names whatever you actually play rather than what the chart expects.',
        how_to=[
            'Tap the third string in the chart, C4 261.63 Hz, and tune that one first &mdash; it is the lowest note on the instrument and the easiest anchor to hear against.',
            'Work outward to E4 329.63 Hz and A4 440.00 Hz, then finish with the fourth string at G4 392.00 Hz, which sits between the two.',
            'Turn the peg slowly, since a ukulele string is short and a small movement covers a surprising amount of pitch.',
            'Go round all four strings two or three more times, and expect to keep repeating that for the first week on a new set.',
        ],
        faq=[
            ('Why is my fourth string higher than my third?',
             'That is reentrant tuning, and it is standard on a ukulele. The fourth string is G4 392.00 Hz while the third is C4 261.63 Hz, so the set does not climb steadily from one side to the other &mdash; it drops, then climbs. Sorted low to high the strings are C4 261.63, E4 329.63, G4 392.00 and A4 440.00 Hz, which means only your first string is higher than your fourth.'),
            ('I have fitted a low G. What changes?',
             'A low G is a wound string sounding an octave below the chart, at G3 196.00 Hz, and it makes the instrument linear: the strings then rise in pitch from fourth to first the way a guitar does. Live detection reports the pitch you actually produce, so it will read G3. Tuning by ear still works &mdash; sound the G4 392.00 Hz reference and tune to the octave below it, which locks in cleanly with no beating.'),
            ('Why will a new ukulele not stay in tune?',
             'Nylon and fluorocarbon creep. Under tension the polymer keeps stretching for days rather than minutes, so a fresh set falls in pitch every time you put the instrument down. Retune several times a session and it will stabilise inside about a week. Friction pegs add a second, different cause: if a string gives way suddenly rather than drifting, the peg needs its screw tightened a fraction, not more turning.'),
            ('Does the size of the ukulele change the tuning?',
             'No. Soprano, concert and tenor all use these same GCEA pitches, so this chart covers all three; scale length changes tension and tone, not the notes. A baritone is the exception, tuned D3 146.83 Hz, G3 196.00 Hz, B3 246.94 Hz and E4 329.63 Hz like the top four strings of a guitar, so none of the numbers on this page apply to one.'),
        ],
        sections=[
            ('What reentrant tuning does to the sound',
             '<p>Because the fourth string is high rather than low, a strummed chord has no bass note underneath it. Every note lands inside a single octave, which is why a ukulele chord sounds like a cluster rather than a stack &mdash; the ear cannot pick out a root at the bottom, so the voicings sit close together and blend.</p><p>It also opens up campanella playing. In a scale spread across a reentrant set, consecutive notes fall on different strings and ring into each other rather than stopping when the next one starts, giving a harp-like overlap that a linear instrument cannot produce without careful voicing.</p><p>The open strings also spell the tuning phrase everyone learns: G, C, E and A, sung as my dog has fleas. Sorted, those four notes are a C6 chord, which is one more reason idle strumming on a ukulele so rarely sounds wrong.</p>'),
            ('Nylon strings, friction pegs and holding pitch',
             '<p>Two different failures both get called going out of tune, and they want different fixes. Creep is the string lengthening under load: pitch falls smoothly and evenly, it is worst on a new set, and playing time cures it. Slipping is the tuner giving way: pitch drops suddenly, often mid song, and retuning changes nothing.</p><p>If yours is slipping, look at the peg. A friction peg is a tapered shaft held by pressure alone, and the small screw in the button sets that pressure; a quarter turn clockwise is usually enough. Geared tuners do not slip, so on a geared instrument a falling pitch is either creep or a bad winding at the post &mdash; two or three neat turns down the shaft, each below the last, is what holds.</p><p>Temperature counts too. A ukulele brought from a cold car into a warm room goes sharp as it warms, so let it settle before you bother tuning it.</p>'),
        ],
    ),
    'violin-tuner': dict(
        title='Violin Tuner - GDAE Reference Tones and Live Mic',
        description='Tune a violin to G3 196.00, D4 293.66, A4 440.00 and E5 659.26 Hz. Tap any string for a reference tone, or allow the microphone for live pitch detection.',
        intro='The four strings are G3 196.00 Hz, D4 293.66 Hz, A4 440.00 Hz and E5 659.26 Hz, a perfect fifth apart at every step. Tap a string in the chart to hear its pitch and tune to it by ear, exactly as you would to an oboe or a piano. Allow the microphone instead and you get live detection, reading the bowed note continuously so you can watch what a quarter turn of a fine tuner really does.',
        how_to=[
            'Start with the A string: sound A4 440.00 Hz from the chart and bring your A to it, since every other string is set in relation to this one.',
            'Bow a steady stroke at moderate pressure rather than plucking, because a sustained tone gives the detector a continuous waveform to lock onto.',
            'Use the fine tuners on the tailpiece for anything inside roughly a quarter tone, and the pegs only for larger corrections.',
            'Tune D and then G downward from A, tune E upward, and check A once more at the end.',
        ],
        faq=[
            ('Why is the A string tuned first?',
             'Because it is the reference everything else is measured from. In an orchestra the oboe gives an A and the section matches it; alone with a tuner, A4 440.00 Hz plays the same part. It also sits in the middle of the set, so you can check A against D below and E above as double stops without ever needing an outer string to be correct first.'),
            ('My peg slips back as soon as I let go.',
             'A peg is a tapered wooden shaft held in a tapered hole by friction alone, so it has to be pushed into the pegbox as it is turned, not simply rotated. Slipping usually means dry air has shrunk the peg; sticking means humidity has swollen it. Peg compound applied sparingly to the two contact bands treats both. Wind the string so it beds against the pegbox wall, which puts some of the friction back.'),
            ('The tuner says my fifths are slightly off. Are they?',
             'Probably not. A pure fifth tuned by ear is 702 cents wide, while the equal tempered fifth this chart is built on is 700. Tune outward from A in pure fifths and your G lands about four cents below G3 196.00 Hz and your E about two cents above E5 659.26 Hz. That is not an error &mdash; it is the gap between beatless fifths and a tempered scale, and string players live on the pure side of it.'),
            ('Can I tune without a microphone?',
             'Yes. Each string in the chart is a playable reference pitch, which is the traditional method anyway: sound the tone, bow your string, and listen for the beating between them. Beats are unusually easy to hear on a violin because the tone is sustained and rich in harmonics. The microphone adds a cents readout, which is useful when you want to see how far a half turn of a fine tuner actually moves a string.'),
        ],
        sections=[
            ('Pegs first, fine tuners last',
             '<p>The two adjusters do different jobs and the order matters. A peg moves pitch in large, coarse jumps and is the only way to travel more than a semitone. A fine tuner at the tailpiece changes tension by a tiny amount per turn, which is exactly what you want when you are a few cents out.</p><p>Most violins carry a fine tuner on the E string and nothing on the others, because a steel E is under high tension and short in wavelength: a peg movement that barely nudges the G string sends the E flying past the note. If your tailpiece has all four, use all four.</p><p>Two habits save trouble. Do not run a fine tuner to the end of its thread &mdash; if it bottoms out, back it off to the middle and reset the string with the peg. And check that a screw driven far down is not touching the belly of the instrument, which deadens the sound and will eventually mark the varnish.</p>'),
            ('Bowing for a stable reading',
             '<p>Pitch detection is only as steady as the note you hand it. A stroke that starts with a scratch, wanders in pressure, or runs out of bow halfway produces a reading that dances, and the temptation is to keep adjusting a string that was never the problem.</p><p>Draw a slow, even stroke at moderate pressure, roughly halfway between bridge and fingerboard, and read the number from the middle of the stroke rather than either end. Too much bow pressure flattens the pitch measurably; too little gives a thin tone with an unstable fundamental. Both show up on the display as movement you will be tempted to chase.</p><p>Pizzicato is fine for a quick check but it decays fast, and the pitch of a plucked string falls slightly as the initial displacement relaxes, so the reading you catch at the attack is not the one a sustained note would give.</p>'),
        ],
    ),
    'banjo-tuner': dict(
        title='Banjo Tuner - Open G Tuning gDGBD by Ear or Mic',
        description='Tune a 5 string banjo to open G. Tap a string for its reference tone, from the short fifth string at g4 392.00 Hz down to D3 146.83 Hz, or use the mic.',
        intro='Open G on a five string banjo is D3 146.83 Hz, G3 196.00 Hz, B3 246.94 Hz and D4 293.66 Hz across the four long strings, with the short fifth string at g4 392.00 Hz &mdash; the highest note on the instrument. Tap any string in the chart to hear its exact pitch and tune by ear, or allow the microphone for live detection that follows the note continuously as you turn the peg.',
        how_to=[
            'Tune the fourth string to D3 146.83 Hz first, then work across to the first string at D4 293.66 Hz.',
            'Finish with the short fifth string at g4 392.00 Hz, using the small peg mounted in the side of the neck.',
            'Strum all five open strings together and listen &mdash; they should sound one settled G major chord with nothing fighting.',
            'Check the second string, B3 246.94 Hz, last of all, because the major third is where a badly placed bridge shows up first.',
        ],
        faq=[
            ('Why is the fifth string the highest?',
             'Because it is the shortest. It runs from a small nut at the fifth fret down to the bridge, so only about three quarters of the scale is vibrating, and it gets its own peg sticking out of the side of the neck at that point. It is a drone: in Scruggs style your thumb strikes it open, over and over, while the melody happens on the long strings. Position on the instrument tells you nothing about pitch here.'),
            ('The open strings already sound like a chord.',
             'They do, and that is the whole point of open G. The five strings sound G, B and D with two of the Ds doubled, which is a G major triad and nothing else, so a bare strum is already a chord and a straight barre at any fret gives you another one. The fifth fret is C, the seventh is D. It is a large part of why so much bluegrass and clawhammer repertoire sits in G.'),
            ('How do I play in another key without retuning?',
             'A capo handles the four long strings, but it cannot reach the fifth string, which starts past it. The usual answer is small spikes fitted under the fifth string at the seventh and ninth frets: hook the string under one and the drone jumps to a4 or b4, matching a capo at the second or fourth fret. Failing that, you retune that one string with its peg each time you move.'),
            ('My banjo drifts constantly. Is that normal?',
             'More than a guitar does, yes. The head is a stretched membrane that reacts to humidity and temperature, and the bridge stands on it unglued, held down by string pressure alone, so anything that changes the head changes the pitch. Friction pegs, where fitted, add slipping on top of that. Tune, play for a minute, tune again &mdash; a banjo settles rather than staying put.'),
        ],
        sections=[
            ('The fifth string, and the spikes that go with it',
             '<p>The short string is what makes a five string banjo a five string banjo. It is anchored at the fifth fret and tuned to g4 392.00 Hz, an octave above the third string at G3 196.00 Hz, and its job is to ring open as a drone rather than to be fretted.</p><p>Practical consequences follow. A capo clamped across the neck cannot reach it, so raising the other four leaves the drone behind and out of key; sliding spikes at the seventh and ninth frets are the standard answer, giving the drone two extra pitches without touching its peg. And because it is short and thin, it goes sharp faster than any other string under pressure from the fretting hand, so a heavy grip up at the fifth fret will sound out of tune even when the display insists it is not.</p>'),
            ('Bridge, head and why intonation drifts',
             '<p>A banjo bridge is not fixed to anything. It stands on the head under string tension, and its position sets the intonation of every fretted note. Measure from the nut to the twelfth fret, double it, and stand the bridge feet that distance from the nut &mdash; then confirm it by comparing the twelfth fret harmonic against the fretted twelfth. Fretted notes running sharp mean the bridge is sitting too close to the neck.</p><p>The head is the second variable. Tightening it brightens the whole instrument and lifts pitch slightly as the bridge sinks less; damp weather slackens it and everything turns dull and flat. That is why a banjo tuned in a cold room needs a full pass again under stage lights, and why open strings are only half the job. Strum the open chord and listen to the B3 246.94 Hz third, which is the note that sours first.</p>'),
        ],
    ),
    'cello-tuner': dict(
        title='Cello Tuner - Tune CGDA in Fifths by Ear or Mic',
        description='Tune a cello to C2 65.41, G2 98.00, D3 146.83 and A3 220.00 Hz. Tap any string for a reference tone, or allow the microphone for live pitch detection.',
        intro='A cello is tuned in fifths like a violin but far lower: C2 65.41 Hz, G2 98.00 Hz, D3 146.83 Hz and A3 220.00 Hz. Those are the same four letters a viola uses, sounding an octave beneath it. Tap a string in the chart to hear the pitch, or allow the microphone for live detection &mdash; the window it analyses lengthens for the C string, which is the only way a 65 Hz fundamental resolves cleanly.',
        how_to=[
            'Sit with the cello in playing position before you start, since the pegbox ends up behind your left ear and you will be reaching for it blind.',
            'Set A3 220.00 Hz first, then D, then G, then C, tuning each string as a fifth below the one above it.',
            'Use the fine tuners on the tailpiece for small corrections and the pegs only when a string is more than a quarter tone out.',
            'Bow each string with a long, even stroke and read the pitch from the middle of the stroke rather than the attack.',
        ],
        faq=[
            ('Why does the C reference tone sound thin on my laptop?',
             'Because C2 is 65.41 Hz and a laptop speaker cannot move enough air that low. What reaches you is mostly the harmonics above the fundamental, and your ear reconstructs the missing pitch from their spacing &mdash; convincing enough to tune to, but weak and easy to mishear by an octave. Headphones or any speaker with a real driver will play the actual fundamental, and the difference is obvious the moment you switch.'),
            ('Pegs or fine tuners?',
             'Fine tuners for everyday work. Most cellos carry four of them, one per string, because the tension involved makes peg work coarse: a few degrees of rotation can move a string most of a semitone. Keep the pegs for restringing or for a string that has dropped badly, and push the peg inward as you turn so it grips. Geared pegs, if your instrument has them, turn like machine heads and hold without pressure.'),
            ('How do I check a fifth by ear?',
             'Bow two adjacent strings together and listen for beating inside the sound. A fifth that is nearly right pulses slowly; as you close in the pulse slows further and stops, and the two notes lock into one steady sound. Bow lightly so both strings speak evenly, adjust only the string you are currently tuning, and work downward from A3 220.00 Hz so your reference is always the string above.'),
            ('One note on my cello howls and the tuner cannot read it.',
             'That is a wolf tone: a note whose frequency coincides with a strong resonance in the body, so the top and the string compete for the same energy and the sound stutters instead of sustaining. It usually lands around E, F or F&#9839; on the G or C string, and it is a property of the instrument rather than of your tuning. Tune on open strings and other notes, and fit a suppressor to the affected string if it is severe.'),
        ],
        sections=[
            ('Tuning from the playing position',
             '<p>Unlike a guitarist, you cannot see what you are doing. The pegbox sits above and behind your left shoulder while the tailpiece is between your knees, so the ergonomics of the two adjusters differ completely: fine tuners are in front of you and can be turned while you bow, pegs cannot.</p><p>That dictates an order. Get every string within reach of its fine tuner using the pegs, one at a time, with the instrument held steady and your left hand pushing the peg inward as it turns. Then sit properly, bow, and finish at the tailpiece while listening.</p><p>Keep the fine tuners near the middle of their travel. Run one to the bottom of its thread and you lose the ability to correct downward halfway through a rehearsal, and a screw driven too far can end up touching the belly of the instrument through the tailpiece.</p>'),
            ('The low C and what makes it awkward',
             '<p>Every difficulty on the C string traces back to 65.41 Hz being a slow wave. One cycle lasts about 15 milliseconds, so the tuner needs a longer stretch of continuous audio before it can measure a period at all, and you notice that as a reading which takes a beat to settle. Bow through it rather than stopping to look.</p><p>The string itself carries the most mass and the most winding on the instrument. It responds slowly to the bow, its fundamental is quieter than the harmonics stacked above it, and a heavy bow arm will drag the pitch flat at the exact moment you are trying to measure it. A light, steady stroke near the middle of the bow gives the cleanest reading.</p><p>Tune it last, then check A3 220.00 Hz again. Bringing the thickest string up to pitch adds several kilograms of pull across the top and neck, and the other three will have shifted in response.</p>'),
        ],
    ),
    'drop-d-tuner': dict(
        title='Drop D Tuner - DADGBE by Ear or Live Microphone',
        description='Drop the sixth string from E2 82.41 Hz to D2 73.42 Hz. Tap any string for its reference tone or use live mic detection, then check the octave against D3.',
        intro='Drop D changes exactly one string. The sixth falls from E2 82.41 Hz to D2 73.42 Hz, a whole tone, while the other five stay put at A2 110.00 Hz, D3 146.83 Hz, G3 196.00 Hz, B3 246.94 Hz and E4 329.63 Hz. Tap the sixth string in the chart to hear the target and match it by ear, or allow the microphone and watch the note fall through E&#9837; on its way down to D.',
        how_to=[
            'Tune the guitar to standard first if it is not already there, since the other five strings are unchanged.',
            'Tap D2 73.42 Hz in the chart and slacken the sixth string to it, arriving from below so the winding stays tight at the post.',
            'Check the octave: the open sixth string should sit exactly one octave below the open fourth string at D3 146.83 Hz, with no beating between the two.',
            'Run through the other five strings again, because they will have crept slightly sharp now that the neck is carrying less total tension.',
        ],
        faq=[
            ('How far is the sixth string moving?',
             'Two semitones, a whole tone, from E2 82.41 Hz down to D2 73.42 Hz. In frequency that is a drop of nearly 9 Hz, but the useful test is the octave: D3 146.83 Hz on the open fourth string is double D2, so the two strings sounded together should give one clean pitch. A slow pulse means you are close but not there yet, and the pulse rate is roughly how many Hz out you are at the upper octave.'),
            ('Why do the other strings go sharp?',
             'The neck carries the combined pull of six strings, which runs to many tens of kilograms, and it flexes under that load. Take a whole tone off the sixth string and the total drops, the neck straightens a fraction, and the remaining five come up slightly sharp in response. The shift is usually only a couple of cents, but it is real, and it is why you check all six after dropping rather than assuming five were left alone.'),
            ('What actually gets easier in drop D?',
             'Power chords on the bottom three strings collapse into a single barre. With the sixth string down a tone, root, fifth and octave line up on one fret, so one finger plays the shape and it slides without refingering. You also gain a low D2 73.42 Hz as an open pedal note, which is why so much riff writing in D and D minor lives here rather than in standard tuning.'),
            ('Does the sixth string buzz once it is slack?',
             'It can. Lower tension means a wider vibration arc for the same picking force, so a string that cleared the frets in standard may rattle against them in drop D, particularly with low action or a light gauge. Pick a little softer, or move to a set with a heavier sixth. Nothing on the guitar needs adjusting for one string down a tone, but a setup that suited standard is now slightly generous.'),
        ],
        sections=[
            ('One finger, one power chord',
             '<p>In standard tuning the bottom three strings sound E, A and D, which is not a shape you can barre into anything useful. Drop the sixth to D2 73.42 Hz and the gap from the sixth string to the fifth becomes a perfect fifth instead of a fourth, so the sixth, fifth and fourth strings at one fret give root, fifth and octave &mdash; a whole power chord under one finger.</p><p>Everything else follows from that. Riffs move quickly because the shape slides without refingering. The open sixth becomes a usable pedal, so hammering between the open D2 and a fretted shape above it produces the drone most drop D writing is built on.</p><p>Chords rooted on the fifth string and above are untouched, so most of your vocabulary survives intact. Only shapes that used the low E need rethinking, and E shape barre chords in particular now want the sixth string fretted two frets higher than before.</p>'),
            ('Getting there, and getting back, accurately',
             '<p>The reliable way in is to tune the sixth string against the fourth rather than against a display alone. A slack low string has a weak fundamental, so if you are watching the readout, let the note ring and give it a moment instead of judging the first flicker.</p><p>Two ear checks are worth knowing. Open sixth against open fourth: D2 73.42 Hz and D3 146.83 Hz are an exact octave, so the pair should sound as one note, and any pulsing is your error. Seventh fret of the sixth string against the open fifth: in drop D both are A2 110.00 Hz, and a unison is much easier to judge than an octave because the two tones share every harmonic.</p><p>Going back to standard, raise the string to E2 82.41 Hz from below, then check the other five, which will have drifted flat as the neck takes the tension again.</p>'),
        ],
    ),
    'dadgad-tuner': dict(
        title='DADGAD Tuner - Celtic and Fingerstyle Guitar Tuning',
        description='Tune to DADGAD: D2 73.42, A2 110.00, D3 146.83, G3 196.00, A3 220.00 and D4 293.66 Hz, by ear from reference tones or with live microphone detection.',
        intro='DADGAD is D2 73.42 Hz, A2 110.00 Hz, D3 146.83 Hz, G3 196.00 Hz, A3 220.00 Hz and D4 293.66 Hz. Coming from standard, three strings move and each drops a whole tone: the sixth, the second and the first. What you are left with is three D strings spanning two octaves and two As &mdash; a chord with no third in it, which is where the whole sound of the tuning comes from. Tap a string to hear it, or use the mic for live readings.',
        how_to=[
            'Lower the sixth string from E2 82.41 Hz to D2 73.42 Hz, which is the same move as drop D.',
            'Lower the second string from B3 246.94 Hz to A3 220.00 Hz, and the first from E4 329.63 Hz to D4 293.66 Hz.',
            'Leave the fifth, fourth and third strings alone at A2 110.00 Hz, D3 146.83 Hz and G3 196.00 Hz.',
            'Strum everything open and confirm the three D strings ring as clean octaves against each other before you play anything.',
        ],
        faq=[
            ('Is DADGAD major or minor?',
             'Neither, and that is the point. The open strings give you D, A and G, so there is no third to settle the question &mdash; the chord is Dsus4. Your ear hears a root and a fifth with the G hanging where a major or minor third would normally sit, so the sound reads as unresolved and modal. Fret a third anywhere and the tuning snaps into a key; leave it out and it keeps floating.'),
            ('How is it different from drop D?',
             'By two strings. Drop D lowers only the sixth to D2 73.42 Hz and leaves B3 246.94 Hz and E4 329.63 Hz on top. DADGAD takes those two down a whole tone as well, to A3 220.00 Hz and D4 293.66 Hz. That is why it is the easiest alternate tuning to reach if you already play in drop D, and why the bottom half feels identical while everything above the third string has changed.'),
            ('Will my top strings feel floppy?',
             'A little. Tension rises with the square of frequency, so dropping the first and second strings a whole tone takes roughly a fifth of the tension off each, and a light gauge set can feel slack and buzz under hard strumming. Players who live in DADGAD often move to slightly heavier plain strings or a heavier set overall. Nothing on the guitar needs adjusting unless the action is already very low.'),
            ('Can I use a capo in DADGAD?',
             'Yes, and it is common. A capo raises every string equally, so all the intervals and every shape you know are preserved; at the second fret DADGAD becomes Esus4, which is where a great many session tunes get played. Only the pitch changes, so a fingering learned in open position works identically further up. Retune after clamping, since a capo pushes strings slightly sharp.'),
        ],
        sections=[
            ('Why DADGAD sounds unfinished, usefully',
             '<p>Sort the open strings by pitch and you have D2 73.42, A2 110.00, D3 146.83, G3 196.00, A3 220.00 and D4 293.66 Hz: three Ds, two As and a single G. In interval terms that is a root, a fifth and a fourth, repeated over two octaves. There is no third anywhere, and a chord without a third is neither major nor minor.</p><p>That ambiguity is what suits it to modal music. Irish and Scottish melodies often sit in Dorian or Mixolydian, where the third of the key is not the one a guitar in standard tuning would assume, and an accompaniment that refuses to specify a quality can never contradict the tune. The same property makes it forgiving under fingerstyle arrangement, because open strings can ring through almost any fretted shape without clashing.</p><p>It also places open D strings above and below the middle of the instrument, so a melody on the third and fourth strings gets drones on both sides of it rather than only underneath.</p>'),
            ('Arriving at DADGAD without wrecking your intonation',
             '<p>Three strings move and all three move down, so the guitar sheds tension overall and the neck relaxes a fraction. Expect the fifth, fourth and third strings to drift sharp even though you never touched them, and plan on two passes rather than one.</p><p>The checks that confirm you have arrived are all octaves and unisons, which are far easier to judge than a needle. The open first string D4 293.66 Hz is one octave above the open fourth at D3 146.83 Hz and two octaves above the open sixth at D2 73.42 Hz; sound them in pairs and wait for the beating to disappear. The open second string A3 220.00 Hz is one octave above the open fifth at A2 110.00 Hz. If those relationships are clean, the tuning is right whatever a display says about the last cent.</p><p>Coming back to standard, raise the second and first strings before the sixth, and approach every note from below.</p>'),
        ],
    ),
    'open-g-tuner': dict(
        title='Open G Tuner - DGDGBD for Slide and Blues Guitar',
        description='Tune to open G: D2 73.42, G2 98.00, D3 146.83, G3 196.00, B3 246.94 and D4 293.66 Hz. Reference tones for every string plus live mic pitch detection.',
        intro='Open G is D2 73.42 Hz, G2 98.00 Hz, D3 146.83 Hz, G3 196.00 Hz, B3 246.94 Hz and D4 293.66 Hz. Three strings drop a whole tone from standard &mdash; the sixth, the fifth and the first &mdash; and the open set then spells a G major chord, so a bare strum is already music. Tap any string for its reference tone and tune by ear, or allow the microphone for live pitch detection.',
        how_to=[
            'Lower the sixth string from E2 82.41 Hz to D2 73.42 Hz and the fifth from A2 110.00 Hz to G2 98.00 Hz.',
            'Lower the first string from E4 329.63 Hz to D4 293.66 Hz, and leave the fourth, third and second strings exactly where they are.',
            'Strum all six open strings and listen for a G major chord that sits still &mdash; any beating means one string is not quite home.',
            'Lay a slide or a straight finger across the twelfth fret and check the chord is still in tune an octave up.',
        ],
        faq=[
            ('Which strings actually change?',
             'Three, all down a whole tone: the sixth from E2 82.41 Hz to D2 73.42 Hz, the fifth from A2 110.00 Hz to G2 98.00 Hz, and the first from E4 329.63 Hz to D4 293.66 Hz. The fourth, third and second stay exactly as they were, at D3 146.83 Hz, G3 196.00 Hz and B3 246.94 Hz. That half-unchanged set is why open G is quick to reach and quick to leave again.'),
            ('Why do some players take the sixth string off?',
             'Because the sixth is a D, a fifth below the root, so a full strum puts the chord in second inversion with D2 73.42 Hz at the bottom instead of G. Remove it and G2 98.00 Hz becomes the lowest note, so every open strum is a root position G and the rhythm playing sits square underneath a band. Five string electrics set up this way are a long tradition in open G rhythm guitar.'),
            ('Is open G the same as Spanish tuning?',
             'Yes. Open G has been called Spanish tuning since the nineteenth century, after a piece written in it, in the same way that open D is called Vestapol. Both names survive mostly among slide and blues players. There is also a raised variant that puts the sixth string up at G rather than dropping it, but the standard modern set is the one on this page.'),
            ('Do I need a special setup for slide?',
             'Higher action helps, because a slide rides on top of the strings and low action lets them rattle against the frets underneath it. Many players keep a second instrument with the action raised at nut and saddle and a heavier gauge fitted, which also stops the slackened sixth and fifth strings from buzzing. Slide on a normal setup is possible with a light touch, but you will be fighting the guitar.'),
        ],
        sections=[
            ('Barre it anywhere: open G under a slide',
             "<p>With the open strings sounding G major, a straight barre at any fret transposes the entire chord. The fifth fret gives C, the seventh gives D, the twelfth gives G an octave up. That is the whole harmonic vocabulary of a great deal of blues and rock rhythm playing, available without a single chord shape.</p><p>Under a slide the same idea applies with one hard rule: the slide sits directly over the fret wire, not behind it. No fret is doing the stopping, so the slide is the stopping point, and a slide placed where your finger would go sounds flat by half a fret. Keep it parallel to the fret as well, or the outer strings drift in opposite directions.</p><p>Damp behind the slide with the fingers of the fretting hand. In an open tuning every string is a chord tone, so anything left ringing rings in the chord &mdash; the tuning's greatest strength, and the reason it turns to mud without damping.</p>"),
            ('Into open G from standard, and back out',
             '<p>All three moves are downward, so the guitar sheds tension and the untouched strings drift slightly sharp. Tune the sixth, fifth and first, then check the fourth, third and second before you decide you have finished.</p><p>The reliable checks are octaves rather than a display. The open fifth string G2 98.00 Hz is an octave below the open third at G3 196.00 Hz; the open sixth D2 73.42 Hz is an octave below the open fourth at D3 146.83 Hz and two octaves below the open first at D4 293.66 Hz. Sound each pair and listen for the beats to stop.</p><p>Going back to standard means raising three strings, which is where intonation trouble starts: a string that sat slack for an hour keeps creeping after you bring it up. Approach each from below, play hard for a few seconds to seat the winding at the post, then check again before you trust it.</p>'),
        ],
    ),
    'half-step-down-tuner': dict(
        title='Half Step Down Tuner - E Flat Standard Guitar Tuning',
        description='Tune every string down one semitone to E flat standard: 77.78, 103.83, 138.59, 185.00, 233.08 and 311.13 Hz, by ear from reference tones or with the mic.',
        intro='Half step down keeps every interval of standard tuning and moves the whole instrument one semitone lower: E&#9837;2 77.78 Hz, A&#9837;2 103.83 Hz, D&#9837;3 138.59 Hz, G&#9837;3 185.00 Hz, B&#9837;3 233.08 Hz and E&#9837;4 311.13 Hz. Every shape you already know still works, it simply sounds a semitone below the name you call it. Tap a string for its reference tone, or allow the microphone for live detection.',
        how_to=[
            'Work from the sixth string to the first, taking each one down a single semitone from its standard pitch.',
            'Tap the reference tone for each string in the chart &mdash; flat spellings are used here, so the sixth string target reads E&#9837;2 77.78 Hz.',
            'Approach every note from below: slacken past the target, then bring it back up so the winding stays tight at the post.',
            'Go round twice, since taking a semitone off all six strings unloads the neck noticeably and everything moves together.',
        ],
        faq=[
            ('Is E flat the same as D sharp?',
             'The same pitches, spelled differently. E&#9837;2 77.78 Hz and D&#9839;2 77.78 Hz are one note on a guitar, but the flat spelling is the one that matches the music: guitarists in this tuning end up playing in E&#9837;, A&#9837; and B&#9837;, which are written with flats. Calling it D&#9839; standard forces sharp key names with double sharps inside them, which nobody wants to read off a chart.'),
            ('Do I need heavier strings?',
             'Not necessarily, but the guitar will feel different. String tension rises with the square of frequency, so a semitone down removes about eleven percent of the pull on every string. Bends get easier, which is usually the reason to be here at all, and buzz gets likelier, especially with a light gauge over low action. Many players move up one gauge to put the tension back roughly where it was.'),
            ('Will a capo bring me back to standard?',
             'Yes. A capo at the first fret raises every string a semitone, so the open strings sound E2 82.41 Hz through E4 329.63 Hz again and every standard shape lands at standard pitch. You lose a fret of range at the top and the open strings below the capo are no longer available, but for playing along with something recorded at standard pitch it is an instant fix.'),
            ('What happens to my floating tremolo?',
             'It tilts. A floating bridge balances string tension against spring tension, so removing eleven percent from the strings lets the springs win: the bridge sinks toward the body, which pulls the pitch down further and puts you into a loop of chasing it. Slacken the spring claw screws in the back cavity a little at a time, retuning between adjustments, until the bridge sits level again.'),
        ],
        sections=[
            ('What a semitone of slack actually changes',
             '<p>Tension on a string goes with the square of the frequency it is tuned to, so lowering everything one semitone removes about eleven percent of the pull. Across six strings that is several kilograms less load on the neck, and the effects show up roughly in this order.</p><ul><li>Bends take noticeably less effort, and a full tone bend on the second string stops being a workout. This is the main attraction for lead players.</li><li>Fret buzz appears sooner, because a slacker string swings through a wider arc for the same attack.</li><li>Neck relief drops slightly as the truss rod wins back some bow, which lowers the action further and makes the buzz worse.</li><li>A vibrato bridge that floats needs its springs slackened before it will sit level again.</li></ul>'),
            ('The key you are actually in',
             '<p>Nothing about your fingering changes, but everything about the names does. Play what you call an E shape and the room hears E&#9837;. Play in what feels like G and you are in G&#9837;, more usefully written F&#9839;. Anyone reading notation, and any piano or horn in the room, works from the sounding pitch rather than the shape your hand is making, so you have to translate.</p><p>That is also the point of the tuning for a lot of bands. A song sitting a semitone too high for a singer drops into range without anybody learning new shapes, and the guitars pick up a slacker, darker tone on the way. The cost is that everything you play along with has to be in the same place: a recording at standard pitch will clash unless you capo the first fret, and anything you write here needs transposing before you hand it to someone who does not detune.</p>'),
        ],
    ),
}


# ---------------------------------------------------------- tuner presets --

def more_tuners_html(current_slug):
    links = ""
    for slug, label in PRESET_NAV:
        if slug == current_slug:
            continue
        name = "Chromatic tuner" if slug == "tuner" else PRESET_BY_SLUG[slug]["h1"]
        links += f'        <a href="/{slug}/">{name} &rarr;</a>\n'
    return links


def build_preset_page(p):
    copy = PRESET_COPY[p["slug"]]
    t = TUNING_BY_ID[p["tuning"]]
    title = f'{copy["title"]} | perfecttune.net'
    description = copy["description"]
    json_ld = (
        '{"@context":"https://schema.org","@type":"WebApplication","name":"'
        + p["h1"] + " \\u2014 perfecttune.net" + '",'
        f'"url":"{SITE}/{p["slug"]}/",'
        '"applicationCategory":"MusicApplication",'
        '"operatingSystem":"Any (runs in browser)",'
        f'"description":"{description}",'
        '"offers":{"@type":"Offer","price":"0","priceCurrency":"USD"},'
        '"featureList":"Reference tone per string, microphone pitch detection, adjustable concert pitch",'
        '"publisher":{"@type":"Organization","name":"perfecttune.net"}}'
    )
    h = head(title, description, f"/{p['slug']}/", json_ld)
    b = header(p["slug"], section="tuner")

    body = f"""  <main>
    <section class="panel">
      <div class="wrap">
        <div class="panel-head">
          <h1 tabindex="-1">{p['h1']}</h1>
          <a class="back-to-tools" href="/" data-panel-link="">&larr; All tools</a>
        </div>
        <p>{copy['intro']}</p>
{privacy_note_html()}
{tuner_workspace(t, p['h1'])}
      </div>
    </section>

    <section class="content-section" id="how-it-works">
      <div class="wrap">
        <h2>How to use the {p['h1']}</h2>
        <div class="how-to">
          <ol>
"""
    for step in copy["how_to"]:
        body += f"        <li>{step}</li>\n"
    body += """          </ol>
        </div>
      </div>
    </section>
"""

    for heading, html in copy["sections"]:
        body += f"""
    <section class="content-section">
      <div class="wrap">
        <h2>{heading}</h2>
{html}
      </div>
    </section>
"""

    body += tuning_reference_html(p["ref"], p["ref_heading"], p["ref_blurb"], current=p["slug"])

    body += """
    <section class="content-section">
      <div class="wrap">
        <h2>FAQ</h2>
        <dl class="faq">
"""
    for q, a in copy["faq"]:
        body += f"        <dt>{q}</dt>\n        <dd>{a}</dd>\n"
    body += """        </dl>
      </div>
    </section>

    <section class="content-section">
      <div class="wrap">
        <h2>Other tuners</h2>
        <div class="related-links">
"""
    body += more_tuners_html(p["slug"])
    body += """        </div>
      </div>
    </section>

    <section class="content-section">
      <div class="wrap">
        <h2>Related tools</h2>
        <div class="related-links">
"""
    for rel in p["related"]:
        body += f'        <a href="/{rel}/">{TOOL_BY_SLUG[rel]["name"]} &rarr;</a>\n'
    body += """        </div>
      </div>
    </section>
  </main>
"""

    full = h + b + body + footer_and_close(scripts_for([TOOL_BY_SLUG["tuner"]]), faq_jsonld(copy["faq"]))
    write(f"{p['slug']}/index.html", full)
    write(f"{p['slug']}.html", full)


# ---------------------------------------------------------------- legal pages --

def build_legal(slug, title_text, body_html):
    title = f"{title_text} | perfecttune.net"
    description = f"{title_text} for perfecttune.net."
    json_ld = (
        '{"@context":"https://schema.org","@type":"WebPage","name":"'
        + title + '","url":"' + SITE + "/" + slug + '/"}'
    )
    h = head(title, description, f"/{slug}/", json_ld)
    b = header("")
    body = f"""  <main class="legal">
    <div class="wrap">
      <h1>{title_text}</h1>
{body_html}
    </div>
  </main>
"""
    full = h + b + body + footer_and_close([])
    write(f"{slug}/index.html", full)
    write(f"{slug}.html", full)


def build_privacy():
    body = f"""      <p><em>Last updated {UPDATED}.</em></p>
      <h2>What perfecttune.net does not collect</h2>
      <p>perfecttune.net has no accounts, no server-side database, and no analytics beacons. There is nothing to sign up for and nothing about your usage is logged anywhere we control.</p>
      <h2>Microphone audio (Tuner)</h2>
      <p>The Tuner requests microphone access only after you tap Start. The resulting audio stream is connected directly to a Web Audio <code>AnalyserNode</code> inside your own browser tab, analyzed frame by frame with an on-device pitch-detection algorithm, and immediately discarded &mdash; it is never recorded, saved, or transmitted anywhere. Tapping Stop releases the microphone; closing or navigating away from the tab does the same.</p>
      <h2>Everything else runs locally too</h2>
      <p>The Metronome's clicks, the Tone Generator's drone, the Ear Trainer's intervals and the Chord and Scale Dictionary's chords are all synthesized on-device with the Web Audio API &mdash; no audio files are downloaded, and no sound is uploaded. The BPM Tapper measures the timing of your own taps and uses no microphone at all, and the Chord Transposer is pure arithmetic in the page. Your theme preference (light/dark) is stored in your browser's <code>localStorage</code> and never leaves your device either.</p>
      <h2>Advertising</h2>
      <p>This site shows ads served by Google AdSense. Google may use cookies and similar technologies to serve ads based on your prior visits to this and other websites. You can learn more about how Google uses data and manage your ad settings at <a href="https://policies.google.com/technologies/ads" rel="noopener">policies.google.com/technologies/ads</a>.</p>
      <h2>Third parties</h2>
      <p>Other than the AdSense script above, this site makes no requests to any external server. There are no other third-party scripts, fonts, or trackers.</p>
      <h2>Contact</h2>
      <p>Questions about this policy can be sent through the contact details listed on our <a href="https://erabb.it">erabb.it</a> portfolio page.</p>
"""
    build_legal("privacy", "Privacy Policy", body)


def build_terms():
    body = f"""      <p><em>Last updated {UPDATED}.</em></p>
      <h2>Using the site</h2>
      <p>perfecttune.net's Tuner, Metronome, Tone Generator, Interval Ear Trainer, Chord and Scale Dictionary, BPM Tapper and Chord Transposer are provided free of charge, as-is, for anyone to use. There is no account to create and no fee to pay.</p>
      <h2>No warranty</h2>
      <p>These tools are built with care but are not a substitute for a professional-grade tuner or click track in a critical performance or recording setting. Pitch detection and timing accuracy depend on your microphone, browser, and device; chord, scale and transposition results follow standard equal-tempered theory but your chart's own notation conventions may differ. perfecttune.net is provided without warranty of any kind, express or implied.</p>
      <h2>Audio &amp; hearing</h2>
      <p>The Tone Generator and Metronome produce audible tones. Start at a low volume, especially when using headphones, and use your own judgment about safe listening levels and durations.</p>
      <h2>Acceptable use</h2>
      <p>Don't attempt to disrupt, reverse-engineer for malicious purposes, or scrape the site in a way that degrades it for other users.</p>
      <h2>Changes</h2>
      <p>These terms may be updated from time to time; continued use of the site after a change constitutes acceptance of the revised terms.</p>
"""
    build_legal("terms", "Terms of Service", body)


# ---------------------------------------------------------------- 404 --

def build_404():
    title = "Page not found | perfecttune.net"
    description = "This page doesn't exist. Find the tuner, metronome, ear trainer and the rest of the practice tools from the perfecttune.net homepage."
    json_ld = '{"@context":"https://schema.org","@type":"WebPage","name":"' + title + '","url":"' + SITE + '/404.html"}'
    # 404 may omit ads per convention; build a lightweight head manually.
    url = SITE + "/404.html"
    h = f"""<!doctype html>
<html lang="en">
<head>
  {THEME_SCRIPT}
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <link rel="canonical" href="{url}">
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
  <meta name="theme-color" content="#241a14">
  <link rel="stylesheet" href="/assets/style.css">
  <script type="application/ld+json">{json_ld}</script>
</head>
"""
    b = header("")
    body = """  <main>
    <div class="wrap notfound">
      <div class="big">&mdash;&mdash;</div>
      <h1>Page not found</h1>
      <p>That page doesn't exist &mdash; but the tuner, metronome, ear trainer and the rest of the practice tools are all one tap away.</p>
      <p><a href="/">&larr; Back to perfecttune.net</a></p>
    </div>
  </main>
"""
    full = h + b + body + footer_and_close([])
    write("404.html", full)


# ---------------------------------------------------------------- articles --

ARTICLE_BODIES = {
    "how-instrument-tuners-actually-work": """
      <p>Point a microphone at a guitar string and a browser tab can tell you, within a few milliseconds, exactly how many cents sharp or flat it is. No plugin, no upload, no round trip to a server &mdash; just a few hundred lines of math running on the same audio buffer your browser already has in memory. Here's what's actually happening underneath.</p>
      <h2>The problem: finding a fundamental frequency</h2>
      <p>A plucked string doesn't produce one clean sine wave; it produces a fundamental frequency plus a stack of quieter harmonics on top, all summed into one messy waveform. Pitch detection means recovering that one fundamental frequency &mdash; the number that determines what note you hear &mdash; from the combined signal.</p>
      <h2>Why autocorrelation works</h2>
      <p>Autocorrelation is a simple idea: take a chunk of the audio buffer, and compare it against a copy of itself shifted forward in time by some small delay. If the underlying wave is periodic &mdash; which a sustained musical note is &mdash; then at exactly one delay (the wave's period) the shifted copy lines up almost perfectly with the original, and the sum of the products spikes. Sweep the delay across a range of plausible values, find where that sum peaks, and you've found the period. Frequency is just the sample rate divided by that period in samples.</p>
      <p>perfecttune.net's Tuner does exactly this: it grabs a 2048-sample window from a Web Audio <code>AnalyserNode</code>, computes the autocorrelation across a range of lags, and picks the lag with the strongest correlation (after skipping the initial, always-strong zero-lag peak). A parabolic interpolation around that best lag refines the result to sub-sample precision, which is the difference between a needle that visibly jitters and one that sits still.</p>
      <h2>From frequency to note name</h2>
      <p>Once you have a frequency in Hz, converting it to a note name is pure equal-temperament math. Every note's frequency is a fixed ratio away from a reference pitch &mdash; conventionally A4 at 440 Hz &mdash; specifically <code>440 &times; 2^((n-69)/12)</code> where <code>n</code> is the note's MIDI number. Run that formula backward on a detected frequency, round to the nearest whole MIDI number, and you get the nearest note; the leftover fractional distance, converted to cents (1/100th of a semitone), is exactly the needle reading.</p>
      <h2>Why it has to run in the browser</h2>
      <p>A tuner needs to update dozens of times per second to feel responsive, and every one of those updates depends on raw, continuous microphone audio. Uploading that audio to a server for analysis would mean latency, bandwidth, and &mdash; far more importantly &mdash; sending a live mic feed off your device for no real benefit, since a modern browser's JavaScript engine can run this entire pipeline, autocorrelation and all, comfortably in real time on ordinary hardware. Keeping it local isn't a compromise; it's strictly the better design.</p>
""",
    "why-your-metronome-should-not-use-setinterval": """
      <p>The obvious way to build a metronome is <code>setInterval(click, 60000/bpm)</code>. It works &mdash; for about thirty seconds. Then it starts to drift, and on a long practice session the drift becomes audible. Here's why, and what a metronome that actually holds tempo has to do instead.</p>
      <h2>The problem with JavaScript timers</h2>
      <p><code>setInterval</code> and <code>setTimeout</code> are best-effort: the browser guarantees your callback won't fire <em>before</em> the requested delay, but makes no promise about exactly when after. If the tab is backgrounded, the OS is busy, garbage collection kicks in, or a dozen other timers are queued ahead of yours, your callback fires late &mdash; sometimes by a few milliseconds, sometimes by much more. Each late firing is a small timing error, and a metronome built this way accumulates those errors beat after beat. A tempo that's supposed to be locked at 120 BPM can wander by several BPM over a few minutes of continuous practice, exactly when a click track most needs to be trustworthy.</p>
      <h2>The lookahead scheduler pattern</h2>
      <p>Web Audio exposes its own high-precision clock, <code>audioCtx.currentTime</code>, and every audio node accepts an exact start time on that clock rather than "play now." The fix is to stop asking a timer to fire <em>at</em> each beat, and instead use a (still-imprecise) timer only to periodically check the clock and schedule any upcoming beats slightly ahead of when they're due:</p>
      <ul>
        <li>A loop runs roughly every 25 milliseconds &mdash; frequently, but its own imprecision no longer matters.</li>
        <li>Each time it wakes up, it schedules every click whose exact time falls within the next ~100&ndash;150 milliseconds, using <code>osc.start(exactAudioClockTime)</code>.</li>
        <li>Because the *audio hardware itself* fires the click at that exact sample-accurate time &mdash; not the JavaScript timer &mdash; the click's timing is immune to the timer's own jitter. The timer only has to be roughly on time; the clock reference it reads from is exact.</li>
      </ul>
      <p>This is the same technique described in Chris Wilson's well-known "A Tale of Two Clocks" article, and it's become the standard approach for any web app that needs a drum machine, sequencer, or metronome that actually holds time. perfecttune.net's Metronome uses exactly this pattern: a lookahead of about 100ms and a scheduler tick of 25ms, with every click's start time computed directly from tempo and time signature rather than counted one interval at a time.</p>
      <h2>Making the visuals match</h2>
      <p>It's not enough for the audio to be accurate if the pendulum on screen is animated by a separate, disconnected timer &mdash; you'd see drift even if you couldn't hear it. So the pendulum's position each frame is computed directly from the same schedule: which beat just played, which beat is coming next, and how far between those two real audio-clock timestamps the current moment falls. What you see is a direct readout of what's actually scheduled to play, not a decorative approximation of it.</p>
""",
    "practicing-with-a-drone-tone": """
      <p>Long before tuning apps existed, singers and string players practiced against a drone &mdash; a single sustained pitch held underneath everything else &mdash; to train their ear for intonation. It's one of the oldest and simplest practice tools in music, and it still works exactly as well against a Web Audio oscillator as it did against a tanpura or a pitch pipe.</p>
      <h2>What a drone is actually for</h2>
      <p>A drone gives you a fixed, unmoving reference. Instead of judging a note in isolation &mdash; which your ear is not naturally great at &mdash; you judge it <em>relative to</em> something constant, which your ear is very good at. Hold a drone at your tonic and sing or play a scale over it, and every note you land on either locks in with the drone (consonance) or clashes against it (dissonance) in a way that's immediately, physically obvious &mdash; you'll often feel a beating or shimmering sensation when you're a few cents off, and feel it disappear when you land exactly in tune.</p>
      <h2>Basic drone exercises</h2>
      <ul>
        <li><strong>Unison and octave matching.</strong> Set the drone to your instrument's open string or your vocal comfortable pitch, and practice landing exactly on it from above and below, listening for the beating to vanish.</li>
        <li><strong>Scale-against-drone.</strong> Keep the drone on the tonic and sing or play each scale degree over it, one at a time, holding each note until it feels stable before moving to the next.</li>
        <li><strong>Interval training.</strong> Set the drone to a reference pitch, then try to sing or play a specific interval above it &mdash; a third, a fifth, an octave &mdash; entirely from memory, and check yourself against the drone afterward.</li>
        <li><strong>Just-intonation listening.</strong> Equal temperament is a compromise; a drone lets you hear how a "pure," beatless fifth or third actually sounds compared to the slightly-off equal-tempered version your fretted or keyboard instrument normally gives you.</li>
      </ul>
      <h2>Choosing a waveform</h2>
      <p>A pure sine wave is the cleanest reference &mdash; no harmonics to distract from the fundamental &mdash; and is the best default for pitch-matching exercises. Square and sawtooth waves are harmonically richer and can make certain intervals easier to judge (their overtones will themselves beat against the notes you play), which some players find useful for advanced interval training once the basics feel comfortable on sine.</p>
      <h2>A note on volume</h2>
      <p>A drone is meant to sit underneath what you're doing, not compete with it. Start quieter than feels necessary, especially on headphones, and only bring the level up until you can just comfortably hear both the drone and your own instrument or voice at once.</p>
""",
}


def build_articles():
    for a in ARTICLES:
        title = f"{a['title']} | perfecttune.net"
        json_ld = (
            '{"@context":"https://schema.org","@type":"Article","headline":"'
            + a["title"] + '","description":"' + a["description"] + '",'
            f'"url":"{SITE}/articles/{a["slug"]}.html","datePublished":"{TODAY}",'
            '"author":{"@type":"Organization","name":"perfecttune.net"},'
            '"publisher":{"@type":"Organization","name":"perfecttune.net"}}'
        )
        h = head(title, a["description"], f"/articles/{a['slug']}.html", json_ld)
        b = header("")
        body = f"""  <main class="article">
    <div class="wrap">
      <h1>{a['title']}</h1>
      <p class="article-meta">perfecttune.net &middot; {TODAY}</p>
{ARTICLE_BODIES[a['slug']]}
      <p><a href="/">&larr; Back to perfecttune.net</a></p>
    </div>
  </main>
"""
        full = h + b + body + footer_and_close([])
        write(f"articles/{a['slug']}.html", full)


# ---------------------------------------------------------------- misc --

def build_misc():
    write("robots.txt", "User-agent: *\nAllow: /\nSitemap: https://perfecttune.net/sitemap.xml\n")
    write("CNAME", "perfecttune.net\n")
    write(".nojekyll", "")
    write("ads.txt", "google.com, pub-7560786263587509, DIRECT, f08c47fec0942fa0\n")

    urls = (
        ["/"]
        + [f"/{t['slug']}/" for t in TOOLS]
        + [f"/{p['slug']}/" for p in PRESET_PAGES]
        + ["/privacy/", "/terms/"]
        + [f"/articles/{a['slug']}.html" for a in ARTICLES]
    )
    entries = "\n".join(f"  <url><loc>{SITE}{u}</loc><lastmod>{UPDATED}</lastmod></url>" for u in urls)
    sitemap = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}\n</urlset>\n'
    write("sitemap.xml", sitemap)


if __name__ == "__main__":
    write("assets/tunings.js", build_tunings_js())
    build_homepage()
    for t in TOOLS:
        build_tool_page(t)
    for p in PRESET_PAGES:
        build_preset_page(p)
    build_privacy()
    build_terms()
    build_404()
    build_articles()
    build_misc()
    print(f"Built perfecttune.net — {len(TOOLS)} tools, {len(PRESET_PAGES)} tuner pages, {len(TUNINGS)} tunings")
