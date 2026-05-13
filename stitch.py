#!/usr/bin/env python3
"""
Stitch mockup HTML files into renters-journey.html (single-page app).
Each screen's CSS is scoped to its screen ID to prevent cross-screen conflicts.
"""

import re
from pathlib import Path

BASE    = Path("/Users/melissabowden/Documents/Dev/Renter's Journey")
MOCKUPS = BASE / "mockups"

# ── CSS scoping ────────────────────────────────────────────────────────────

def _find_block_end(css, start):
    """Return the index just after the matching closing } starting from start (after opening {).
    Handles CSS comments (/* ... */) and quoted strings to avoid false brace matches."""
    depth = 1
    i = start
    n = len(css)
    in_str = None
    while i < n and depth > 0:
        # Skip CSS block comments (/* ... */)
        if not in_str and css[i] == '/' and i + 1 < n and css[i+1] == '*':
            end = css.find('*/', i + 2)
            i = end + 2 if end != -1 else n
            continue
        c = css[i]
        if in_str:
            if c == '\\':
                i += 2  # skip escaped character
                continue
            if c == in_str:
                in_str = None
        elif c in ('"', "'"):
            in_str = c
        elif c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
        i += 1
    return i  # points just past the closing }

def scope_css(css, scope):
    """
    Prefix every CSS selector block with `scope`, keeping global rules
    (:root, @keyframes, @font-face, @import, @charset, html/body resets) untouched.
    Handles nested @media / @supports by recursively scoping inner rules.
    """
    out = []
    pos = 0
    n = len(css)

    while pos < n:
        # Skip whitespace
        ws = re.match(r'\s+', css[pos:])
        if ws:
            out.append(ws.group(0))
            pos += len(ws.group(0))
            continue

        # Skip /* comments */
        cm = re.match(r'/\*.*?\*/', css[pos:], re.DOTALL)
        if cm:
            out.append(cm.group(0))
            pos += len(cm.group(0))
            continue

        # At-rules
        at_m = re.match(r'@([\w-]+)', css[pos:])
        if at_m:
            at_name = at_m.group(1).lower()
            # Simple at-rules (end with ;)
            if at_name in ('import', 'charset', 'namespace', 'layer'):
                end = css.find(';', pos)
                if end == -1:
                    out.append(css[pos:])
                    break
                out.append(css[pos:end+1])
                pos = end + 1
                continue
            # Block at-rules we pass through verbatim
            if at_name in ('keyframes', '-webkit-keyframes', '-moz-keyframes',
                           'font-face', 'counter-style', 'page'):
                open_b = css.find('{', pos)
                if open_b == -1:
                    out.append(css[pos:])
                    break
                end = _find_block_end(css, open_b + 1)
                out.append(css[pos:end])
                pos = end
                continue
            # Conditional at-rules (@media, @supports): scope inner rules
            if at_name in ('media', 'supports', 'layer'):
                open_b = css.find('{', pos)
                if open_b == -1:
                    out.append(css[pos:])
                    break
                header = css[pos:open_b+1]
                inner_start = open_b + 1
                end = _find_block_end(css, inner_start)
                inner = css[inner_start:end-1]
                out.append(header)
                out.append(scope_css(inner, scope))
                out.append('}')
                pos = end
                continue
            # Unknown at-rule: pass through verbatim
            open_b = css.find('{', pos)
            semi = css.find(';', pos)
            if semi != -1 and (open_b == -1 or semi < open_b):
                out.append(css[pos:semi+1])
                pos = semi + 1
            elif open_b != -1:
                end = _find_block_end(css, open_b + 1)
                out.append(css[pos:end])
                pos = end
            else:
                out.append(css[pos:])
                break
            continue

        # Regular selector { ... }
        open_b = css.find('{', pos)
        if open_b == -1:
            # No more rules
            out.append(css[pos:])
            break

        selector_raw = css[pos:open_b]
        # Skip empty selectors
        if not selector_raw.strip():
            pos = open_b + 1
            continue

        end = _find_block_end(css, open_b + 1)
        body = css[open_b:end]  # includes { ... }

        # Scope each comma-part of the selector
        # `scope` may itself be comma-separated (e.g. for chapters).
        # We need to produce a cross-product: each scope × each selector part.
        scope_ids = [s.strip() for s in scope.split(',')]
        sel_parts = [p.strip() for p in selector_raw.split(',')]
        scoped = []
        for p in sel_parts:
            if not p:
                continue
            if (p.startswith(':root') or
                    re.match(r'^html\b', p) or
                    re.match(r'^body\b', p) or
                    p.strip() == '*'):
                scoped.append(p)
            else:
                for sid in scope_ids:
                    scoped.append(sid + ' ' + p)

        if scoped:
            out.append(',\n'.join(scoped))
            out.append(' ')
        out.append(body)
        pos = end

    return ''.join(out)


# ── HTML helpers ───────────────────────────────────────────────────────────

def extract_css(path):
    html = Path(path).read_text(encoding="utf-8")
    m = re.search(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
    return m.group(1).strip() if m else ""

def extract_body(path):
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
    for fname, sid in NAV_MAP.items():
        html = re.sub(
            rf'href="{re.escape(fname)}"',
            f'href="#{sid}" onclick="RJ.navigate(\'{sid}\'); return false;"',
            html,
        )
    html = re.sub(
        r'(<span class="change"(?:[^>]*)>)(.*?)(</span>)',
        lambda m: m.group(1).rstrip('>') +
                  ' onclick="RJ.navigate(\'screen-intro\')" role="button" tabindex="0" style="cursor:pointer">' +
                  m.group(2) + m.group(3),
        html,
    )
    html = html.replace('src="footer-town-scene.svg"', 'src="mockups/footer-town-scene.svg"')
    for icon in ["icon-alex-bike","icon-jordan-dog","icon-taylor-camera","icon-jamie-drawing"]:
        html = html.replace(f'src="{icon}.png"', f'src="mockups/{icon}.png"')
    return html

def process(path):
    return adapt(extract_body(path))

# ── Build scoped CSS blocks ────────────────────────────────────────────────

SCREEN_CSS_MAP = [
    # (scope_selector,  mockup_file)
    ("#screen-intro",   "persona-selection-mockup.html"),
    ("#screen-avatar",  "avatar-creation-mockup.html"),
    ("#screen-map",     "journey-map-mockup.html"),
    # All chapter screens share the same design system CSS
    ("#screen-ch1, #screen-ch2, #screen-ch3, #screen-ch4, #screen-ch5, #screen-ch6, #screen-ch7",
                        "chapter-1-long-night-jordan-mockup.html"),
    ("#screen-ultimate","ultimate-quest-mockup.html"),
]

css_blocks = []
for scope_sel, fname in SCREEN_CSS_MAP:
    raw_css = extract_css(MOCKUPS / fname)
    scoped = scope_css(raw_css, scope_sel)
    css_blocks.append(f"/* === {fname} === */\n{scoped}")

combined_css = "\n\n".join(css_blocks)

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

# ── JS ────────────────────────────────────────────────────────────────────

JS = r"""<script>
(function() {
'use strict';

var STORAGE_KEY = 'rj.profile.v1';
var NOTES_KEY   = 'rj.notes.v1';

var DEFAULTS = {
  persona: 'jordan', unlockedChapter: 1,
  skin: '#FCE0C2', hair: '#A06940', shirt: '#6105C4',
  pants: '#3B2A1F', shoes: '#1A0E2E', hairStyle: 'short'
};

function loadProfile() {
  try { return Object.assign({}, DEFAULTS, JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')); }
  catch(e) { return Object.assign({}, DEFAULTS); }
}
function saveProfile(patch) {
  var p = loadProfile(); Object.assign(p, patch);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(p));
}
function loadNotes() {
  try { return JSON.parse(localStorage.getItem(NOTES_KEY) || '[]'); }
  catch(e) { return []; }
}
function saveNote(note) {
  var notes = loadNotes().filter(function(n) { return n.id !== note.id; });
  notes.push(note);
  localStorage.setItem(NOTES_KEY, JSON.stringify(notes));
}
function getPersonaNotes(persona) {
  return loadNotes().filter(function(n) { return n.persona === persona; });
}

var PERSONA_META = {
  jordan: { fullName: 'Jordan the Rising Star', shortName: 'Jordan', color: '#FF974D' },
  alex:   { fullName: 'Alex the Ambitious',     shortName: 'Alex',   color: '#6105C4' },
  taylor: { fullName: 'Taylor & Riley',         shortName: 'Taylor', color: '#C384F0' },
  jamie:  { fullName: 'Jamie the Planner',      shortName: 'Jamie',  color: '#5C8841' },
};

function applyPersonaTheme(key) {
  var meta = PERSONA_META[key] || PERSONA_META.jordan;
  document.documentElement.style.setProperty('--persona-color', meta.color);
}

var VALID_SCREENS = ['screen-intro','screen-avatar','screen-map',
  'screen-ch1','screen-ch2','screen-ch3','screen-ch4',
  'screen-ch5','screen-ch6','screen-ch7','screen-ultimate'];

var RJ = {
  navigate: function(screenId) {
    document.querySelectorAll('.screen').forEach(function(s) { s.style.display = 'none'; });
    var target = document.getElementById(screenId);
    if (target) { target.style.display = 'block'; window.scrollTo(0,0); window.location.hash = screenId; }
    applyPersonaTheme(loadProfile().persona);
    if (screenId === 'screen-avatar')   { syncAvatarScreen(); }
    if (screenId === 'screen-map')      { syncMapScreen(); }
    if (screenId === 'screen-ultimate') { syncUltimateScreen(); }
    var ch = screenId.match(/^screen-ch(\d+)$/);
    if (ch) { syncChapterScreen(parseInt(ch[1])); }
  }
};

// ── Persona selection ─────────────────────────────────────────────────────
var CARD_TO_KEY = { 'alex':'alex', 'jordan':'jordan', 'taylor-riley':'taylor', 'jamie':'jamie' };
function personaKey(card) {
  var cls = Array.from(card.classList);
  for (var i=0;i<cls.length;i++) { if (CARD_TO_KEY[cls[i]]) return CARD_TO_KEY[cls[i]]; }
  return card.getAttribute('data-persona');
}
function initPersonaSelection() {
  document.querySelectorAll('article.card').forEach(function(card) {
    var key = personaKey(card);
    if (!key) return;
    var btn = card.querySelector('.btn-embark');
    if (!btn) return;
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      var existing = loadProfile();
      var hasNotes = existing.persona && getPersonaNotes(existing.persona).length > 0;
      if (hasNotes && existing.persona !== key) { showSwitchWarning(key); }
      else { selectPersona(key); }
    });
  });
}
function selectPersona(key) {
  saveProfile({ persona: key, unlockedChapter: 1 });
  applyPersonaTheme(key);
  RJ.navigate('screen-avatar');
}
function showSwitchWarning(newKey) {
  var h = document.getElementById('rjSwitchDialogHolder');
  if (!h) return;
  h.innerHTML = '<div style="position:fixed;inset:0;background:rgba(0,0,0,0.55);z-index:9999;display:flex;align-items:center;justify-content:center;">'
    +'<div style="background:#F5F2ED;border:3px solid #1A0E2E;padding:28px 32px;max-width:360px;font-family:\'Source Serif 4\',serif;">'
    +'<h3 style="font-family:\'Pixelify Sans\',monospace;margin:0 0 12px;">Switch renters?</h3>'
    +'<p style="margin:0 0 20px;font-size:14px;">You have saved Field Notes for your current renter. Starting over will clear them.</p>'
    +'<div style="display:flex;gap:12px;">'
    +'<button onclick="window._rjConfirmSwitch(\''+newKey+'\')" style="font-family:\'VT323\',monospace;font-size:16px;padding:8px 16px;background:#6105C4;color:#fff;border:none;cursor:pointer;">Yes, switch</button>'
    +'<button onclick="document.getElementById(\'rjSwitchDialogHolder\').innerHTML=\'\'" style="font-family:\'VT323\',monospace;font-size:16px;padding:8px 16px;background:#fff;border:2px solid #1A0E2E;cursor:pointer;">Keep going</button>'
    +'</div></div></div>';
}
window._rjConfirmSwitch = function(key) {
  localStorage.removeItem(NOTES_KEY); selectPersona(key);
  var h=document.getElementById('rjSwitchDialogHolder'); if(h) h.innerHTML='';
};

// ── Avatar screen ─────────────────────────────────────────────────────────
var AVATAR_VARS = { skin:'--avatar-skin', hair:'--avatar-hair', shirt:'--avatar-shirt', pants:'--avatar-pants', shoes:'--avatar-shoes' };
var SKIN_TO_LIP = { '#FCE0C2':'#E07590','#E8C5A4':'#C8576B','#D4A57A':'#A8425A','#A87A52':'#8B3548','#7A5236':'#8B3548','#4A3220':'#B85968' };

function syncAvatarScreen() {
  var profile = loadProfile();
  var meta = PERSONA_META[profile.persona] || PERSONA_META.jordan;
  var nameEl = document.querySelector('#screen-avatar .persona-context .name');
  if (nameEl) nameEl.textContent = meta.fullName;
  // Restore CSS vars
  Object.keys(AVATAR_VARS).forEach(function(k) {
    if (profile[k]) document.documentElement.style.setProperty(AVATAR_VARS[k], profile[k]);
  });
  if (profile.skin && SKIN_TO_LIP[profile.skin])
    document.documentElement.style.setProperty('--avatar-lip', SKIN_TO_LIP[profile.skin]);
  // Hair style
  var hs = profile.hairStyle || 'short';
  document.querySelectorAll('#screen-avatar .avatar .hair-style').forEach(function(g) {
    g.style.display = (g.getAttribute('data-style') === hs) ? '' : 'none';
  });
  // Swatch selection highlights
  document.querySelectorAll('#screen-avatar .swatches').forEach(function(grp) {
    var t = grp.getAttribute('data-target'); var saved = profile[t];
    grp.querySelectorAll('.swatch').forEach(function(sw) {
      sw.classList.toggle('selected', sw.getAttribute('data-color') === saved);
    });
  });
  // Wire swatches (once)
  document.querySelectorAll('#screen-avatar .swatches:not([data-wired])').forEach(function(grp) {
    grp.setAttribute('data-wired','1');
    var target = grp.getAttribute('data-target');
    grp.querySelectorAll('.swatch').forEach(function(sw) {
      sw.addEventListener('click', function() {
        grp.querySelectorAll('.swatch').forEach(function(s){s.classList.remove('selected');});
        sw.classList.add('selected');
        var color = sw.getAttribute('data-color');
        document.documentElement.style.setProperty(AVATAR_VARS[target], color);
        if (target==='skin' && SKIN_TO_LIP[color])
          document.documentElement.style.setProperty('--avatar-lip', SKIN_TO_LIP[color]);
        var p={}; p[target]=color; saveProfile(p);
      });
    });
  });
  // Wire hair-style thumbs (once)
  var thumbsEl = document.querySelector('#screen-avatar .thumbs[data-target="hair-style"]:not([data-wired])');
  if (thumbsEl) {
    thumbsEl.setAttribute('data-wired','1');
    thumbsEl.querySelectorAll('.thumb').forEach(function(thumb) {
      thumb.addEventListener('click', function() {
        thumbsEl.querySelectorAll('.thumb').forEach(function(t){t.classList.remove('selected');});
        thumb.classList.add('selected');
        var style = thumb.getAttribute('data-style');
        document.querySelectorAll('#screen-avatar .avatar .hair-style').forEach(function(g){
          g.style.display=(g.getAttribute('data-style')===style)?'':'none';
        });
        saveProfile({ hairStyle: style });
      });
    });
  }
  document.querySelectorAll('#screen-avatar .thumbs[data-target="hair-style"] .thumb').forEach(function(t){
    t.classList.toggle('selected', t.getAttribute('data-style') === hs);
  });
  // Begin button (once)
  var beginBtn = document.querySelector('#screen-avatar .btn-begin:not([data-wired])');
  if (beginBtn) { beginBtn.setAttribute('data-wired','1'); beginBtn.addEventListener('click', function(){RJ.navigate('screen-map');}); }
}

// ── Map screen ────────────────────────────────────────────────────────────
var PERSONA_CHIPS = { jordan:'Achiever', alex:'Ambitious', taylor:'Duo Quest', jamie:'Planner' };

function syncMapScreen() {
  var profile = loadProfile();
  var meta = PERSONA_META[profile.persona] || PERSONA_META.jordan;

  // Top-bar persona name
  var nameEl = document.querySelector('#screen-map .persona-context .name');
  if (nameEl) nameEl.textContent = meta.fullName;

  // Sidebar HUD: persona name + class chip
  var hudName = document.getElementById('mapPersonaName');
  if (hudName) hudName.textContent = meta.shortName;
  var hudChip = document.getElementById('mapPersonaChip');
  if (hudChip) hudChip.textContent = PERSONA_CHIPS[profile.persona] || meta.badge || '';

  // Apply saved avatar CSS vars so the sprite reflects the designed avatar
  Object.keys(AVATAR_VARS).forEach(function(k) {
    if (profile[k]) document.documentElement.style.setProperty(AVATAR_VARS[k], profile[k]);
  });
  if (profile.skin && SKIN_TO_LIP[profile.skin])
    document.documentElement.style.setProperty('--avatar-lip', SKIN_TO_LIP[profile.skin]);

  // Show the correct hair style in the map sidebar sprite
  var hs = profile.hairStyle || 'short';
  document.querySelectorAll('#screen-map .avatar-frame .hair-style').forEach(function(g) {
    g.style.display = (g.getAttribute('data-style') === hs) ? '' : 'none';
  });

  // Wire change-renter (once)
  var changeEl = document.querySelector('#screen-map .persona-context .change:not([data-wired])');
  if (changeEl) { changeEl.setAttribute('data-wired','1'); changeEl.style.cursor='pointer'; changeEl.addEventListener('click',function(){RJ.navigate('screen-intro');}); }

  // Apply lock/unlock state to chapter cards
  var cards = document.querySelectorAll('#screen-map .chapter-card');
  cards.forEach(function(card, idx) {
    var chNum = idx+1; var unlocked = chNum <= profile.unlockedChapter;
    card.classList.toggle('locked', !unlocked);
    if (unlocked && !card.getAttribute('data-wired')) {
      card.setAttribute('data-wired','1'); card.style.cursor='pointer';
      (function(n){ card.addEventListener('click',function(e){ e.preventDefault(); if(!card.classList.contains('locked')) RJ.navigate('screen-ch'+n); }); })(chNum);
    }
  });
}

// ── Chapter screens ───────────────────────────────────────────────────────
function syncChapterScreen(n) {
  var profile = loadProfile();
  var screenEl = document.getElementById('screen-ch'+n);
  if (!screenEl) return;
  applyPersonaTheme(profile.persona);
  var changeEl = screenEl.querySelector('.persona-context .change:not([data-wired])');
  if (changeEl) { changeEl.setAttribute('data-wired','1'); changeEl.style.cursor='pointer'; changeEl.addEventListener('click',function(){RJ.navigate('screen-intro');}); }
  var continueBtn = screenEl.querySelector('#continueBtn:not([data-wired])');
  if (continueBtn) {
    continueBtn.setAttribute('data-wired','1');
    var tas = screenEl.querySelectorAll('.reflection-input');
    function checkFilled() {
      var ok = tas.length > 0;
      tas.forEach(function(ta){ if(!ta.value.trim()) ok=false; });
      if(ok){ continueBtn.classList.remove('disabled'); continueBtn.removeAttribute('aria-disabled'); }
      else  { continueBtn.classList.add('disabled');    continueBtn.setAttribute('aria-disabled','true'); }
    }
    tas.forEach(function(ta){ ta.addEventListener('input',checkFilled); });
    checkFilled();
    continueBtn.addEventListener('click',function(e){
      e.preventDefault();
      if(continueBtn.classList.contains('disabled')) return;
      var prof=loadProfile();
      if(n+1<=7 && n+1>prof.unlockedChapter) saveProfile({unlockedChapter:n+1});
      RJ.navigate(n<7?'screen-ch'+(n+1):'screen-ultimate');
    });
  }
}

// ── Ultimate quest ────────────────────────────────────────────────────────
function syncUltimateScreen() {
  applyPersonaTheme(loadProfile().persona);
  ['#screen-intro','#screen-map'].forEach(function(hash){
    var sid=hash.replace('#','');
    document.querySelectorAll('#screen-ultimate a[href="'+hash+'"]:not([data-wired])').forEach(function(el){
      el.setAttribute('data-wired','1');
      el.addEventListener('click',function(e){ e.preventDefault(); RJ.navigate(sid); });
    });
  });
}

// ── Init ──────────────────────────────────────────────────────────────────
function init() {
  applyPersonaTheme(loadProfile().persona);
  document.querySelectorAll('.screen').forEach(function(s){ s.style.display='none'; });
  var hash = window.location.hash.replace('#','');
  if (hash && VALID_SCREENS.indexOf(hash)!==-1) { RJ.navigate(hash); }
  else { RJ.navigate('screen-intro'); }
  initPersonaSelection();
  window.addEventListener('hashchange',function(){
    var h=window.location.hash.replace('#','');
    if(h && VALID_SCREENS.indexOf(h)!==-1) RJ.navigate(h);
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
/* Screen management — must come first */
*, *::before, *::after {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; }}
.screen {{ display: none; }}
</style>

<style>
/* Per-screen styles (scoped to each screen's ID) */
{combined_css}
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
