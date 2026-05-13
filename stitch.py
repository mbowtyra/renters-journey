#!/usr/bin/env python3
"""
Stitch mockup HTML files into renters-journey.html (single-page app).
Each mockup's body content becomes the inner HTML of its screen div.
Each mockup's CSS is added as a <style> block in the <head>.
The JS is a lean IIFE that syncs static HTML without overwriting it.
"""

import re
from pathlib import Path

BASE    = Path("/Users/melissabowden/Documents/Dev/Renter's Journey")
MOCKUPS = BASE / "mockups"

# ── helpers ────────────────────────────────────────────────────────────────

def extract_css(path):
    html = Path(path).read_text(encoding="utf-8")
    m = re.search(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
    return m.group(1).strip() if m else ""

def extract_body(path):
    """Extract <body> content; strip <style> and <script> blocks."""
    html = Path(path).read_text(encoding="utf-8")
    m = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL)
    if not m:
        return ""
    body = m.group(1)
    body = re.sub(r'\s*<style[^>]*>.*?</style>', "", body, flags=re.DOTALL)
    body = re.sub(r'\s*<script[^>]*>.*?</script>', "", body, flags=re.DOTALL)
    return body.strip()

NAV_MAP = {
    "persona-selection-mockup.html":              "screen-intro",
    "avatar-creation-mockup.html":                "screen-avatar",
    "journey-map-mockup.html":                    "screen-map",
    "chapter-1-long-night-jordan-mockup.html":    "screen-ch1",
    "chapter-2-first-light-alex-mockup.html":     "screen-ch2",
    "chapter-3-search-begins-taylor-mockup.html": "screen-ch3",
    "chapter-4-crossroads-jamie-mockup.html":     "screen-ch4",
    "chapter-5-first-hello-jordan-mockup.html":   "screen-ch5",
    "chapter-6-the-key-jamie-mockup.html":        "screen-ch6",
    "chapter-7-welcome-mat-alex-mockup.html":     "screen-ch7",
    "ultimate-quest-mockup.html":                 "screen-ultimate",
}

def adapt(html):
    """Adapt hrefs and asset paths for the SPA context."""
    for fname, sid in NAV_MAP.items():
        html = re.sub(
            rf'href="{re.escape(fname)}"',
            f'href="#{sid}" onclick="RJ.navigate(\'{sid}\'); return false;"',
            html,
        )
    # "Change renter" spans -> navigate to intro
    html = re.sub(
        r'(<span class="change"(?:[^>]*)>)(.*?)(</span>)',
        lambda m: m.group(1).rstrip('>') +
                  ' onclick="RJ.navigate(\'screen-intro\')" role="button" tabindex="0" style="cursor:pointer">' +
                  m.group(2) + m.group(3),
        html,
    )
    # Asset paths
    html = html.replace('src="footer-town-scene.svg"',   'src="mockups/footer-town-scene.svg"')
    for icon in ["icon-alex-bike","icon-jordan-dog","icon-taylor-camera","icon-jamie-drawing"]:
        html = html.replace(f'src="{icon}.png"', f'src="mockups/{icon}.png"')
    return html

def process(path):
    return adapt(extract_body(path))

# ── Extract CSS ────────────────────────────────────────────────────────────

css_intro    = extract_css(MOCKUPS / "persona-selection-mockup.html")
css_avatar   = extract_css(MOCKUPS / "avatar-creation-mockup.html")
css_map      = extract_css(MOCKUPS / "journey-map-mockup.html")
css_chapter  = extract_css(MOCKUPS / "chapter-1-long-night-jordan-mockup.html")
css_ultimate = extract_css(MOCKUPS / "ultimate-quest-mockup.html")

# ── Extract body HTML ──────────────────────────────────────────────────────

html_intro    = process(MOCKUPS / "persona-selection-mockup.html")
html_avatar   = process(MOCKUPS / "avatar-creation-mockup.html")
html_map      = process(MOCKUPS / "journey-map-mockup.html")
html_ch = {n: process(MOCKUPS / f) for n, f in [
    (1, "chapter-1-long-night-jordan-mockup.html"),
    (2, "chapter-2-first-light-alex-mockup.html"),
    (3, "chapter-3-search-begins-taylor-mockup.html"),
    (4, "chapter-4-crossroads-jamie-mockup.html"),
    (5, "chapter-5-first-hello-jordan-mockup.html"),
    (6, "chapter-6-the-key-jamie-mockup.html"),
    (7, "chapter-7-welcome-mat-alex-mockup.html"),
]}
html_ultimate = process(MOCKUPS / "ultimate-quest-mockup.html")

# ── Lean JS IIFE ──────────────────────────────────────────────────────────

JS = r"""<script>
(function() {
'use strict';

// ── State ─────────────────────────────────────────────────────────────
var STORAGE_KEY = 'rj.profile.v1';
var NOTES_KEY   = 'rj.notes.v1';

var DEFAULTS = {
  persona: 'jordan',
  unlockedChapter: 1,
  skin: '#FCE0C2',
  hair: '#A06940',
  shirt: '#6105C4',
  pants: '#3B2A1F',
  shoes: '#1A0E2E',
  hairStyle: 'short'
};

function loadProfile() {
  try { return Object.assign({}, DEFAULTS, JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')); }
  catch(e) { return Object.assign({}, DEFAULTS); }
}
function saveProfile(patch) {
  var p = loadProfile();
  Object.assign(p, patch);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(p));
}
function loadNotes() {
  try { return JSON.parse(localStorage.getItem(NOTES_KEY) || '[]'); }
  catch(e) { return []; }
}
function saveNote(note) {
  var notes = loadNotes();
  notes = notes.filter(function(n) { return n.id !== note.id; });
  notes.push(note);
  localStorage.setItem(NOTES_KEY, JSON.stringify(notes));
}
function getPersonaNotes(persona) {
  return loadNotes().filter(function(n) { return n.persona === persona; });
}

// ── Persona metadata ──────────────────────────────────────────────────
var PERSONA_META = {
  jordan: { fullName: 'Jordan the Rising Star', shortName: 'Jordan', color: '#FF974D',
            badge: 'Rising Star' },
  alex:   { fullName: 'Alex the Ambitious',     shortName: 'Alex',   color: '#6105C4',
            badge: 'Ambitious' },
  taylor: { fullName: 'Taylor & Riley',         shortName: 'Taylor', color: '#C384F0',
            badge: 'Duo Quest' },
  jamie:  { fullName: 'Jamie the Planner',      shortName: 'Jamie',  color: '#5C8841',
            badge: 'Planner' },
};

function applyPersonaTheme(key) {
  var meta = PERSONA_META[key] || PERSONA_META.jordan;
  document.documentElement.style.setProperty('--persona-color', meta.color);
}

// ── Navigation ────────────────────────────────────────────────────────
var VALID_SCREENS = ['screen-intro','screen-avatar','screen-map',
  'screen-ch1','screen-ch2','screen-ch3','screen-ch4',
  'screen-ch5','screen-ch6','screen-ch7','screen-ultimate'];

var RJ = {
  navigate: function(screenId) {
    document.querySelectorAll('.screen').forEach(function(s) {
      s.style.display = 'none';
    });
    var target = document.getElementById(screenId);
    if (target) {
      target.style.display = 'block';
      window.scrollTo(0, 0);
      window.location.hash = screenId;
    }
    var profile = loadProfile();
    applyPersonaTheme(profile.persona);

    if (screenId === 'screen-avatar')   { syncAvatarScreen(); }
    if (screenId === 'screen-map')      { syncMapScreen(); }
    if (screenId === 'screen-ultimate') { syncUltimateScreen(); }
    var chMatch = screenId.match(/^screen-ch(\d+)$/);
    if (chMatch) { syncChapterScreen(parseInt(chMatch[1])); }
  }
};

// ── Persona selection ─────────────────────────────────────────────────
function initPersonaSelection() {
  document.querySelectorAll('article.card[data-persona]').forEach(function(card) {
    var key = card.getAttribute('data-persona');
    var btn = card.querySelector('.btn-embark');
    if (!btn) return;
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      var existing = loadProfile();
      var hasNotes = existing.persona && getPersonaNotes(existing.persona).length > 0;
      if (hasNotes && existing.persona !== key) {
        showSwitchWarning(key);
      } else {
        selectPersona(key);
      }
    });
  });
}

function selectPersona(key) {
  saveProfile({ persona: key, unlockedChapter: 1 });
  applyPersonaTheme(key);
  RJ.navigate('screen-avatar');
}

function showSwitchWarning(newKey) {
  var holder = document.getElementById('rjSwitchDialogHolder');
  if (!holder) return;
  holder.innerHTML =
    '<div style="position:fixed;inset:0;background:rgba(0,0,0,0.55);z-index:9999;display:flex;align-items:center;justify-content:center;">'
    + '<div style="background:#F5F2ED;border:3px solid #1A0E2E;padding:28px 32px;max-width:360px;font-family:\'Source Serif 4\',serif;">'
    + '<h3 style="font-family:\'Pixelify Sans\',monospace;margin:0 0 12px;">Switch renters?</h3>'
    + '<p style="margin:0 0 20px;font-size:14px;">You have saved Field Notes for your current renter. Starting over will clear them.</p>'
    + '<div style="display:flex;gap:12px;">'
    + '<button onclick="window._rjConfirmSwitch(\'' + newKey + '\')" style="font-family:\'VT323\',monospace;font-size:16px;padding:8px 16px;background:#6105C4;color:#fff;border:none;cursor:pointer;">Yes, switch</button>'
    + '<button onclick="document.getElementById(\'rjSwitchDialogHolder\').innerHTML=\'\'" style="font-family:\'VT323\',monospace;font-size:16px;padding:8px 16px;background:#fff;border:2px solid #1A0E2E;cursor:pointer;">Keep going</button>'
    + '</div></div></div>';
}

window._rjConfirmSwitch = function(key) {
  localStorage.removeItem(NOTES_KEY);
  selectPersona(key);
  var h = document.getElementById('rjSwitchDialogHolder');
  if (h) h.innerHTML = '';
};

// ── Avatar screen ─────────────────────────────────────────────────────
var AVATAR_VARS = {
  skin: '--avatar-skin', hair: '--avatar-hair',
  shirt: '--avatar-shirt', pants: '--avatar-pants', shoes: '--avatar-shoes'
};
var SKIN_TO_LIP = {
  '#FCE0C2':'#E07590','#E8C5A4':'#C8576B','#D4A57A':'#A8425A',
  '#A87A52':'#8B3548','#7A5236':'#8B3548','#4A3220':'#B85968'
};

function applyAvatarVars(profile) {
  Object.keys(AVATAR_VARS).forEach(function(k) {
    if (profile[k]) document.documentElement.style.setProperty(AVATAR_VARS[k], profile[k]);
  });
  if (profile.skin && SKIN_TO_LIP[profile.skin])
    document.documentElement.style.setProperty('--avatar-lip', SKIN_TO_LIP[profile.skin]);
}

function applyHairStyle(style) {
  document.querySelectorAll('#screen-avatar .avatar .hair-style').forEach(function(g) {
    g.style.display = (g.getAttribute('data-style') === style) ? '' : 'none';
  });
}

function syncAvatarScreen() {
  var profile = loadProfile();
  var meta    = PERSONA_META[profile.persona] || PERSONA_META.jordan;

  // Persona name in top bar
  var nameEl = document.querySelector('#screen-avatar .persona-context .name');
  if (nameEl) nameEl.textContent = meta.fullName;

  // Restore saved appearance
  applyAvatarVars(profile);
  applyHairStyle(profile.hairStyle || 'short');

  // Restore selected swatch highlights
  document.querySelectorAll('#screen-avatar .swatches').forEach(function(grp) {
    var target = grp.getAttribute('data-target');
    var saved  = profile[target];
    grp.querySelectorAll('.swatch').forEach(function(sw) {
      sw.classList.toggle('selected', sw.getAttribute('data-color') === saved);
    });
  });

  // Wire swatches (once)
  document.querySelectorAll('#screen-avatar .swatches:not([data-wired])').forEach(function(grp) {
    grp.setAttribute('data-wired', '1');
    var target = grp.getAttribute('data-target');
    grp.querySelectorAll('.swatch').forEach(function(sw) {
      sw.addEventListener('click', function() {
        grp.querySelectorAll('.swatch').forEach(function(s) { s.classList.remove('selected'); });
        sw.classList.add('selected');
        var color = sw.getAttribute('data-color');
        document.documentElement.style.setProperty(AVATAR_VARS[target], color);
        if (target === 'skin' && SKIN_TO_LIP[color])
          document.documentElement.style.setProperty('--avatar-lip', SKIN_TO_LIP[color]);
        var patch = {}; patch[target] = color;
        saveProfile(patch);
      });
    });
  });

  // Wire hair-style thumbs (once)
  var thumbsEl = document.querySelector('#screen-avatar .thumbs[data-target="hair-style"]:not([data-wired])');
  if (thumbsEl) {
    thumbsEl.setAttribute('data-wired', '1');
    thumbsEl.querySelectorAll('.thumb').forEach(function(thumb) {
      thumb.addEventListener('click', function() {
        thumbsEl.querySelectorAll('.thumb').forEach(function(t) { t.classList.remove('selected'); });
        thumb.classList.add('selected');
        var style = thumb.getAttribute('data-style');
        applyHairStyle(style);
        saveProfile({ hairStyle: style });
      });
    });
  }
  // Restore selected hair thumb highlight
  var hs = profile.hairStyle || 'short';
  document.querySelectorAll('#screen-avatar .thumbs[data-target="hair-style"] .thumb').forEach(function(t) {
    t.classList.toggle('selected', t.getAttribute('data-style') === hs);
  });

  // Wire begin button (once)
  var beginBtn = document.querySelector('#screen-avatar .btn-begin:not([data-wired])');
  if (beginBtn) {
    beginBtn.setAttribute('data-wired', '1');
    beginBtn.addEventListener('click', function() { RJ.navigate('screen-map'); });
  }
}

// ── Map screen ────────────────────────────────────────────────────────
function syncMapScreen() {
  var profile = loadProfile();
  var meta    = PERSONA_META[profile.persona] || PERSONA_META.jordan;

  // Persona name
  var nameEl = document.querySelector('#screen-map .persona-context .name');
  if (nameEl) nameEl.textContent = meta.fullName;

  // Wire change-renter (once)
  var changeEl = document.querySelector('#screen-map .persona-context .change:not([data-wired])');
  if (changeEl) {
    changeEl.setAttribute('data-wired', '1');
    changeEl.style.cursor = 'pointer';
    changeEl.addEventListener('click', function() { RJ.navigate('screen-intro'); });
  }

  // Apply lock/unlock state to chapter cards
  var cards = document.querySelectorAll('#screen-map .chapter-card');
  cards.forEach(function(card, idx) {
    var chNum     = idx + 1;
    var unlocked  = chNum <= profile.unlockedChapter;
    card.classList.toggle('locked', !unlocked);
    card.setAttribute('aria-disabled', unlocked ? 'false' : 'true');

    if (unlocked && !card.getAttribute('data-wired')) {
      card.setAttribute('data-wired', '1');
      card.style.cursor = 'pointer';
      (function(n) {
        card.addEventListener('click', function(e) {
          e.preventDefault();
          if (!card.classList.contains('locked')) RJ.navigate('screen-ch' + n);
        });
      })(chNum);
    }
  });
}

// ── Chapter screens ───────────────────────────────────────────────────
function syncChapterScreen(n) {
  var profile  = loadProfile();
  var screenEl = document.getElementById('screen-ch' + n);
  if (!screenEl) return;

  applyPersonaTheme(profile.persona);

  // Wire "change renter" span (once)
  var changeEl = screenEl.querySelector('.persona-context .change:not([data-wired])');
  if (changeEl) {
    changeEl.setAttribute('data-wired', '1');
    changeEl.style.cursor = 'pointer';
    changeEl.addEventListener('click', function() { RJ.navigate('screen-intro'); });
  }

  // Gate & wire continue button (once)
  var continueBtn = screenEl.querySelector('#continueBtn:not([data-wired])');
  if (continueBtn) {
    continueBtn.setAttribute('data-wired', '1');
    var textareas = screenEl.querySelectorAll('.reflection-input');

    function checkFilled() {
      var allFilled = textareas.length > 0;
      textareas.forEach(function(ta) { if (!ta.value.trim()) allFilled = false; });
      if (allFilled) {
        continueBtn.classList.remove('disabled');
        continueBtn.removeAttribute('aria-disabled');
      } else {
        continueBtn.classList.add('disabled');
        continueBtn.setAttribute('aria-disabled', 'true');
      }
    }

    textareas.forEach(function(ta) { ta.addEventListener('input', checkFilled); });
    checkFilled();

    continueBtn.addEventListener('click', function(e) {
      e.preventDefault();
      if (continueBtn.classList.contains('disabled')) return;
      var prof = loadProfile();
      if (n + 1 <= 7 && n + 1 > prof.unlockedChapter) saveProfile({ unlockedChapter: n + 1 });
      RJ.navigate(n < 7 ? 'screen-ch' + (n + 1) : 'screen-ultimate');
    });
  }
}

// ── Ultimate quest screen ─────────────────────────────────────────────
function syncUltimateScreen() {
  applyPersonaTheme(loadProfile().persona);

  // Wire any navigation links in the ultimate screen
  ['#screen-intro','#screen-map'].forEach(function(hash) {
    var sid = hash.replace('#','');
    document.querySelectorAll('#screen-ultimate a[href="' + hash + '"]:not([data-wired])').forEach(function(el) {
      el.setAttribute('data-wired','1');
      el.addEventListener('click', function(e) { e.preventDefault(); RJ.navigate(sid); });
    });
  });
}

// ── Init ──────────────────────────────────────────────────────────────
function init() {
  var profile = loadProfile();
  applyPersonaTheme(profile.persona);

  document.querySelectorAll('.screen').forEach(function(s) { s.style.display = 'none'; });

  var hash = window.location.hash.replace('#', '');
  if (hash && VALID_SCREENS.indexOf(hash) !== -1) {
    RJ.navigate(hash);
  } else {
    RJ.navigate('screen-intro');
  }

  initPersonaSelection();

  window.addEventListener('hashchange', function() {
    var h = window.location.hash.replace('#', '');
    if (h && VALID_SCREENS.indexOf(h) !== -1) RJ.navigate(h);
  });
}

document.addEventListener('DOMContentLoaded', init);

})();
</script>"""

# ── Assemble screens ──────────────────────────────────────────────────────

SCREENS = [
    ("screen-intro",    "INTRO (Persona Selection)", html_intro,    True),
    ("screen-avatar",   "AVATAR CREATION",           html_avatar,   False),
    ("screen-map",      "JOURNEY MAP",               html_map,      False),
    ("screen-ch1",      "CHAPTER 1",                 html_ch[1],    False),
    ("screen-ch2",      "CHAPTER 2",                 html_ch[2],    False),
    ("screen-ch3",      "CHAPTER 3",                 html_ch[3],    False),
    ("screen-ch4",      "CHAPTER 4",                 html_ch[4],    False),
    ("screen-ch5",      "CHAPTER 5",                 html_ch[5],    False),
    ("screen-ch6",      "CHAPTER 6",                 html_ch[6],    False),
    ("screen-ch7",      "CHAPTER 7",                 html_ch[7],    False),
    ("screen-ultimate", "ULTIMATE QUEST",            html_ultimate, False),
]

screens_html = ""
for sid, label, content, active in SCREENS:
    cls = "screen active" if active else "screen"
    screens_html += f"""\n<!-- ================================================================
     SCREEN: {label}
     ================================================================ -->
<div class="{cls}" id="{sid}">
{content}
</div>
"""

# ── Final HTML ────────────────────────────────────────────────────────────

output = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Renter's Journey</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Pixelify+Sans:wght@400;500;600;700&family=Source+Serif+4:ital,wght@0,300;0,400;0,600;1,300;1,400&family=VT323&display=swap" rel="stylesheet">

<style>
/* Screen management */
*, *::before, *::after {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; }}
.screen {{ display: none; }}
</style>

<style id="css-intro">
/* Persona Selection */
{css_intro}
</style>

<style id="css-avatar">
/* Avatar Creation */
{css_avatar}
</style>

<style id="css-map">
/* Journey Map */
{css_map}
</style>

<style id="css-chapter">
/* Chapters (shared design system) */
{css_chapter}
</style>

<style id="css-ultimate">
/* Ultimate Quest */
{css_ultimate}
</style>

</head>
<body>

{screens_html}

<div id="rjSwitchDialogHolder"></div>

{JS}
</body>
</html>
"""

out_path = BASE / "renters-journey.html"
out_path.write_text(output, encoding="utf-8")

lines = output.count('\n')
print(f"Written {out_path}")
print(f"  {len(output):,} bytes / {lines:,} lines")
