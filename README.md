# perfecttune.net

A musician's toolkit that runs in the browser. The site holds a chromatic
tuner, a metronome, a drone tone generator, an interval ear trainer, a chord
and scale dictionary, a BPM tapper and a chord transposer.

All audio stays on the device. The tuner connects the microphone to a Web
Audio `AnalyserNode` in the page and discards each frame immediately. The
site has no server-side application, no accounts and no analytics beacons.

## Repository layout

| Path | Contents |
| --- | --- |
| `build.py` | The generator. It writes every HTML page, `sitemap.xml`, `robots.txt` and `assets/tunings.js`. |
| `assets/*.js` | The runtime. One file per tool, plus the shared `notes.js`, `theory.js`, `audio.js`, `gauge.js`, `live-region.js` and `app.js`. |
| `assets/style.css` | The one stylesheet. |
| `test/pitch.test.js` | The pitch detector test suite. |
| `*.html`, `*/index.html` | Generated output. Do not edit these files. |
| `articles/` | Generated articles. Do not edit these files either. |

## Build

The site has no toolchain. Python 3 with the standard library is enough.

```sh
python3 build.py
```

The generator writes a page only when its bytes change. A rebuild that
changes nothing leaves every file, and therefore every date, alone.

To find a generated page that somebody edited by hand, compare without
writing:

```sh
python3 build.py --check      # exit 1 and name each stale file
```

Run `--check` before a deploy and in CI.

### Every page ships twice

GitHub Pages redirects `/slug` to `/slug/` and serves that directory's
`index.html` with the correct `text/html` type. An extensionless file gets
served as `application/octet-stream` and forces a download instead. So the
generator writes each tool page and each legal page to two paths:

- `slug/index.html` — the clean path the canonical points at.
- `slug.html` — a flat alias with the same bytes.

Keep both. The generator writes both from one render, so they cannot drift.

### Dates

`<lastmod>` in the sitemap, and `dateModified` in each article, come from the
date the page last changed. The generator works that date out in this order:

1. The build rewrote the page, or the page differs from the last commit, so
   the date is today.
2. Otherwise, the date of the last commit that touched the file.
3. Outside a git checkout, the file's own mtime.

Git comes before mtime because a fresh clone gives every file the same mtime.
That would date the whole sitemap to the day somebody cloned the repository.

## Tests

```sh
node --test test/pitch.test.js
```

The suite has no dependencies and no framework. It requires
`assets/pitch.js` directly, so it tests the exact function the browser runs.

The subject is the bottom octave. A 5-string bass low B is 30.87 Hz, its
fundamental is much quieter than its harmonics, and a naive 2048-sample
autocorrelation tuner gets it wrong every time. The synthesised test tones
therefore carry a plucked string's harmonic stack with a weak fundamental,
string inharmonicity, a decay envelope and broadband noise. Pure sines are
tested too, because they are the other hard case.

The suite prints every case with its error in cents, and it fails if any tone
detects outside tolerance.

## Add a page

The generator derives the nav, the homepage card, the page itself and the
sitemap entry from one list. To add:

- A tool — add one entry to `TOOLS`.
- A tuning page — add one entry to `PRESET_PAGES`, and its prose to
  `PRESET_COPY`.
- A tempo page — add the number to `BPM_VALUES`, and its prose to `BPM_COPY`.
- An article — add one entry to `ARTICLES`, its body to `ARTICLE_BODIES`, and
  the tool pages that must link to it to `ARTICLES_FOR`.

Then run `python3 build.py` and commit the generated output with the change.

## Accessibility

Each tool announces its headline result through a `role="status"` node.
`assets/live-region.js` guards every announcement: identical text never
reaches the node twice, and the node is written at most twice a second. The
tuner needs both guards, because its note and cents readings redraw on every
animation frame.
