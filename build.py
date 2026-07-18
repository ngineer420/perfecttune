#!/usr/bin/env python3
"""
One-off static-page generator for perfecttune.net. The shipped site has
zero build step — this script just avoids hand-duplicating the shared
head/header/footer boilerplate (and the erabbit mark's exact placement)
across the homepage panels, three standalone tool pages, two legal pages,
the 404, and three articles.

Clean-path implementation: GitHub Pages 301-redirects "/slug" -> "/slug/"
and serves that directory's index.html with the correct text/html type
(an extensionless FILE gets served as application/octet-stream and forces
a download). So every tool/legal page ships as BOTH "<slug>/index.html"
(the true clean path) and "<slug>.html" (a flat alias, also text/html).
"""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = "https://perfecttune.net"
TODAY = "2026-07-18"
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

NAV_ITEMS = [
    ("", "Home"),
    ("tuner", "Tuner"),
    ("metronome", "Metronome"),
    ("tone-generator", "Tone Generator"),
]

# ---------------------------------------------------------------- tools --

TOOLS = [
    dict(
        slug="tuner",
        name="Tuner",
        tagline="Tune by ear's evil twin — real-time pitch, read off a brass needle.",
        description="Free real-time instrument tuner. Microphone-based pitch detection (autocorrelation) shows the detected note, a cents-off needle and the target frequency — 100% on-device, audio never leaves your browser.",
        icon='<path d="M4.5 16a7.5 7.5 0 0 1 15 0"/><path d="M12 16L16.2 7.6"/><circle cx="12" cy="16" r="1.6" fill="currentColor" stroke="none"/>',
        intro="Play a single sustained note — a guitar string, a violin open string, a hummed pitch, anything — and perfecttune listens through your microphone, estimates the fundamental frequency with an autocorrelation pitch detector, and swings a brass needle to show how many cents sharp or flat you are against the nearest equal-tempered note.",
        how_to=[
            "Tap Start and allow microphone access when your browser asks — audio is analyzed locally and never uploaded.",
            "Play or sing a single, sustained, reasonably loud note. Let it ring; avoid plucking staccato notes.",
            "Watch the note name and the needle: the needle centers and turns green within 5 cents of true pitch.",
            "Adjust concert pitch (A4) if you tune to something other than 440 Hz, then tap Stop when you're done to release the mic.",
        ],
        faq=[
            ("Does my microphone audio get uploaded anywhere?", "No. The microphone stream is only ever connected to a local Web Audio AnalyserNode in your own browser tab — it is analyzed and immediately discarded, frame by frame. Nothing is recorded, saved, or sent to any server."),
            ("Why does it say \"No clear pitch\"?", "The detector needs a single, sustained, reasonably clean tone. Chords, percussive plucks, background noise, or a very quiet signal won't produce a stable enough waveform to lock onto — let the note ring and try again a little louder."),
            ("What octave range can it detect?", "Roughly 55 Hz to 1500 Hz, which covers a standard 6-string guitar's low E up through several octaves above — comfortable range for guitar, bass, ukulele, violin, and most vocal ranges."),
            ("Can I tune to something other than A440?", "Yes — the concert pitch field accepts any value from 415–466 Hz, so you can match an orchestra tuning to A442 or a period-instrument ensemble tuning lower, and every note name and cents reading updates accordingly."),
        ],
        related=["metronome", "tone-generator"],
        workspace="""
    <div class="instrument">
      <div class="nameplate">
        <span class="nameplate-label">Tuner</span>
        <span class="status-led" id="tn-status" data-state="idle">Idle</span>
      </div>
      <div class="gauge-wrap"><div class="gauge-mount" id="tn-gauge"></div></div>
      <div class="screen">
        <div class="note-name" id="tn-note"><span class="octave">&mdash;</span></div>
        <div class="cents-readout" id="tn-cents">Waiting for a signal&hellip;</div>
      </div>
      <div class="field-row" style="margin-top:18px">
        <div class="field"><label>Detected</label><div class="readout-sub" id="tn-freq" style="font-size:15px">&mdash;</div></div>
        <div class="field"><label>Target</label><div class="readout-sub" id="tn-target" style="font-size:15px">&mdash;</div></div>
        <div class="field"><label for="tn-a4">Concert pitch (A4)</label><input type="number" id="tn-a4" min="415" max="466" value="440" inputmode="numeric"></div>
      </div>
      <div class="controls-row">
        <button type="button" class="ctrl-btn primary" id="tn-start">Start</button>
        <button type="button" class="ctrl-btn stop" id="tn-stop">Stop</button>
      </div>
      <p class="error-msg" id="tn-error"></p>
      <p class="hint">Microphone audio is processed on-device and never leaves your browser.</p>
    </div>
""",
    ),
    dict(
        slug="metronome",
        name="Metronome",
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
        related=["tuner", "tone-generator"],
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
        related=["tuner", "metronome"],
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
]

TOOL_BY_SLUG = {t["slug"]: t for t in TOOLS}

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


def header(current_slug):
    links = []
    for slug, label in NAV_ITEMS:
        href = "/" if slug == "" else f"/{slug}/"
        current = ' aria-current="page"' if slug == current_slug else ""
        panel = slug
        links.append(f'      <li><a href="{href}" data-panel-link="{panel}"{current}>{label}</a></li>')
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
"""


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


def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


# ---------------------------------------------------------------- homepage --

def build_homepage():
    title = "perfecttune.net &mdash; Tuner, Metronome &amp; Tone Generator for Musicians"
    description = "Free browser-based musician's toolkit: a real-time instrument tuner, a sample-accurate metronome, and a drone tone generator. 100% client-side &mdash; nothing you play or say ever leaves your device."
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
        <p class="eyebrow">Tuner &middot; Metronome &middot; Tone Generator</p>
        <h1>Three instruments, one brass panel.</h1>
        <p class="lede">A real-time tuner, a metronome that never drifts, and a drone tone generator &mdash; each built like a piece of analog gear, each running entirely in this browser tab.</p>
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
{t['workspace']}
        <p style="margin-top:16px;font-size:14px"><a href="/{t['slug']}/#how-it-works">Full guide &amp; FAQ for the {t['name']} &rarr;</a></p>
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

    body = b + hero + panels + learn_more
    scripts = ["tuner.js", "metronome.js", "tone-generator.js"]
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
{priv}{t['workspace']}
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

    scripts_map = {
        "tuner": ["tuner.js"],
        "metronome": ["metronome.js"],
        "tone-generator": ["tone-generator.js"],
    }
    full = h + b + body + footer_and_close(scripts_map[t["slug"]], faq_jsonld(t["faq"]))
    write(f"{t['slug']}/index.html", full)
    write(f"{t['slug']}.html", full)


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
    body = f"""      <p><em>Last updated {TODAY}.</em></p>
      <h2>What perfecttune.net does not collect</h2>
      <p>perfecttune.net has no accounts, no server-side database, and no analytics beacons. There is nothing to sign up for and nothing about your usage is logged anywhere we control.</p>
      <h2>Microphone audio (Tuner)</h2>
      <p>The Tuner requests microphone access only after you tap Start. The resulting audio stream is connected directly to a Web Audio <code>AnalyserNode</code> inside your own browser tab, analyzed frame by frame with an on-device pitch-detection algorithm, and immediately discarded &mdash; it is never recorded, saved, or transmitted anywhere. Tapping Stop releases the microphone; closing or navigating away from the tab does the same.</p>
      <h2>Everything else runs locally too</h2>
      <p>The Metronome's clicks and the Tone Generator's drone are synthesized entirely on-device with the Web Audio API &mdash; no audio files are downloaded, and no sound is uploaded. Your theme preference (light/dark) is stored in your browser's <code>localStorage</code> and never leaves your device either.</p>
      <h2>Advertising</h2>
      <p>This site shows ads served by Google AdSense. Google may use cookies and similar technologies to serve ads based on your prior visits to this and other websites. You can learn more about how Google uses data and manage your ad settings at <a href="https://policies.google.com/technologies/ads" rel="noopener">policies.google.com/technologies/ads</a>.</p>
      <h2>Third parties</h2>
      <p>Other than the AdSense script above, this site makes no requests to any external server. There are no other third-party scripts, fonts, or trackers.</p>
      <h2>Contact</h2>
      <p>Questions about this policy can be sent through the contact details listed on our <a href="https://erabb.it">erabb.it</a> portfolio page.</p>
"""
    build_legal("privacy", "Privacy Policy", body)


def build_terms():
    body = f"""      <p><em>Last updated {TODAY}.</em></p>
      <h2>Using the site</h2>
      <p>perfecttune.net's Tuner, Metronome, and Tone Generator are provided free of charge, as-is, for anyone to use. There is no account to create and no fee to pay.</p>
      <h2>No warranty</h2>
      <p>These tools are built with care but are not a substitute for a professional-grade tuner or click track in a critical performance or recording setting. Pitch detection and timing accuracy depend on your microphone, browser, and device; perfecttune.net is provided without warranty of any kind, express or implied.</p>
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
    description = "This page doesn't exist. Find the tuner, metronome or tone generator from the perfecttune.net homepage."
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
      <p>That page doesn't exist &mdash; but the tuner, metronome and tone generator are all one tap away.</p>
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

    urls = ["/"] + [f"/{t['slug']}/" for t in TOOLS] + ["/privacy/", "/terms/"] + [f"/articles/{a['slug']}.html" for a in ARTICLES]
    entries = "\n".join(f"  <url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod></url>" for u in urls)
    sitemap = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}\n</urlset>\n'
    write("sitemap.xml", sitemap)


if __name__ == "__main__":
    build_homepage()
    for t in TOOLS:
        build_tool_page(t)
    build_privacy()
    build_terms()
    build_404()
    build_articles()
    build_misc()
    print("Built perfecttune.net")
