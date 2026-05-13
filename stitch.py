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

DYNAMIC_AVATAR_FRAME = '''\
        <div class="avatar-frame" onclick="RJ.navigate('screen-avatar')" title="Edit your avatar" style="cursor:pointer;position:relative;">
          <svg viewBox="0 0 32 48" shape-rendering="crispEdges">
            <g class="hair-style hair-short" data-style="short">
              <rect x="9" y="3" width="14" height="2" fill="var(--avatar-hair)"/>
              <rect x="8" y="5" width="16" height="3" fill="var(--avatar-hair)"/>
              <rect x="8" y="8" width="2" height="3" fill="var(--avatar-hair)"/>
              <rect x="22" y="8" width="2" height="3" fill="var(--avatar-hair)"/>
              <rect x="11" y="6" width="7" height="1" fill="var(--avatar-hair)" opacity="0.55"/>
            </g>
            <g class="hair-style hair-long" data-style="long" style="display:none">
              <rect x="9" y="3" width="14" height="2" fill="var(--avatar-hair)"/>
              <rect x="8" y="5" width="16" height="3" fill="var(--avatar-hair)"/>
              <rect x="9" y="8" width="14" height="2" fill="var(--avatar-hair)"/>
              <rect x="8" y="8" width="2" height="9" fill="var(--avatar-hair)"/>
              <rect x="22" y="8" width="2" height="9" fill="var(--avatar-hair)"/>
              <rect x="9" y="16" width="1" height="2" fill="var(--avatar-hair)"/>
              <rect x="22" y="16" width="1" height="2" fill="var(--avatar-hair)"/>
            </g>
            <g class="hair-style hair-bun" data-style="bun" style="display:none">
              <rect x="14" y="0" width="4" height="3" fill="var(--avatar-hair)"/>
              <rect x="13" y="1" width="6" height="2" fill="var(--avatar-hair)"/>
              <rect x="9" y="3" width="14" height="2" fill="var(--avatar-hair)"/>
              <rect x="8" y="5" width="16" height="3" fill="var(--avatar-hair)"/>
              <rect x="8" y="8" width="2" height="3" fill="var(--avatar-hair)"/>
              <rect x="22" y="8" width="2" height="3" fill="var(--avatar-hair)"/>
              <rect x="11" y="6" width="10" height="1" fill="var(--avatar-hair)" opacity="0.6"/>
            </g>
            <g class="hair-style hair-space-buns" data-style="space-buns" style="display:none">
              <rect x="9" y="0" width="3" height="3" fill="var(--avatar-hair)"/>
              <rect x="8" y="1" width="5" height="2" fill="var(--avatar-hair)"/>
              <rect x="20" y="0" width="3" height="3" fill="var(--avatar-hair)"/>
              <rect x="19" y="1" width="5" height="2" fill="var(--avatar-hair)"/>
              <rect x="9" y="3" width="14" height="2" fill="var(--avatar-hair)"/>
              <rect x="8" y="5" width="16" height="3" fill="var(--avatar-hair)"/>
              <rect x="8" y="8" width="2" height="3" fill="var(--avatar-hair)"/>
              <rect x="22" y="8" width="2" height="3" fill="var(--avatar-hair)"/>
              <rect x="11" y="6" width="3" height="1" fill="var(--avatar-hair)" opacity="0.6"/>
              <rect x="18" y="6" width="3" height="1" fill="var(--avatar-hair)" opacity="0.6"/>
            </g>
            <g class="hair-style hair-buzz" data-style="buzz" style="display:none">
              <rect x="10" y="5" width="12" height="2" fill="var(--avatar-hair)"/>
              <rect x="9" y="6" width="14" height="2" fill="var(--avatar-hair)"/>
              <rect x="9" y="8" width="1" height="2" fill="var(--avatar-hair)" opacity="0.5"/>
              <rect x="22" y="8" width="1" height="2" fill="var(--avatar-hair)" opacity="0.5"/>
            </g>
            <g class="hair-style hair-mohawk" data-style="mohawk" style="display:none">
              <rect x="15" y="0" width="2" height="2" fill="var(--avatar-hair)"/>
              <rect x="14" y="2" width="4" height="2" fill="var(--avatar-hair)"/>
              <rect x="13" y="4" width="6" height="2" fill="var(--avatar-hair)"/>
              <rect x="12" y="6" width="8" height="3" fill="var(--avatar-hair)"/>
              <rect x="10" y="6" width="2" height="2" fill="var(--avatar-hair)" opacity="0.35"/>
              <rect x="20" y="6" width="2" height="2" fill="var(--avatar-hair)" opacity="0.35"/>
              <rect x="9" y="7" width="1" height="2" fill="var(--avatar-hair)" opacity="0.3"/>
              <rect x="22" y="7" width="1" height="2" fill="var(--avatar-hair)" opacity="0.3"/>
            </g>
            <rect x="10" y="6" width="12" height="11" fill="var(--avatar-skin)"/>
            <rect x="9" y="7" width="1" height="9" fill="var(--avatar-skin)"/>
            <rect x="22" y="7" width="1" height="9" fill="var(--avatar-skin)"/>
            <rect x="12" y="10" width="1" height="3" fill="#1A0E2E"/>
            <rect x="19" y="10" width="1" height="3" fill="#1A0E2E"/>
            <rect x="14" y="14" width="1" height="1" fill="var(--avatar-lip)"/>
            <rect x="17" y="14" width="1" height="1" fill="var(--avatar-lip)"/>
            <rect x="15" y="15" width="2" height="1" fill="var(--avatar-lip)"/>
            <rect x="14" y="17" width="4" height="2" fill="var(--avatar-skin)"/>
            <rect x="8" y="19" width="16" height="9" fill="var(--avatar-shirt)"/>
            <rect x="6" y="19" width="2" height="9" fill="var(--avatar-shirt)"/>
            <rect x="24" y="19" width="2" height="9" fill="var(--avatar-shirt)"/>
            <rect x="6" y="28" width="2" height="2" fill="var(--avatar-skin)"/>
            <rect x="24" y="28" width="2" height="2" fill="var(--avatar-skin)"/>
            <rect x="8" y="28" width="16" height="11" fill="var(--avatar-pants)"/>
            <rect x="15" y="32" width="2" height="7" fill="var(--avatar-pants)"/>
            <rect x="15" y="34" width="2" height="5" fill="rgba(0,0,0,0.15)"/>
            <rect x="8" y="39" width="7" height="3" fill="var(--avatar-shoes)"/>
            <rect x="17" y="39" width="7" height="3" fill="var(--avatar-shoes)"/>
            <g class="hair-style hair-long-flow" data-style="long-flow" style="display:none">
              <rect x="9" y="3" width="14" height="2" fill="var(--avatar-hair)"/>
              <rect x="8" y="5" width="16" height="3" fill="var(--avatar-hair)"/>
              <rect x="9" y="8" width="14" height="2" fill="var(--avatar-hair)"/>
              <rect x="8" y="8" width="2" height="22" fill="var(--avatar-hair)"/>
              <rect x="22" y="8" width="2" height="22" fill="var(--avatar-hair)"/>
              <rect x="7" y="20" width="2" height="11" fill="var(--avatar-hair)"/>
              <rect x="23" y="20" width="2" height="11" fill="var(--avatar-hair)"/>
              <rect x="10" y="6" width="3" height="1" fill="var(--avatar-hair)" opacity="0.6"/>
              <rect x="19" y="6" width="3" height="1" fill="var(--avatar-hair)" opacity="0.6"/>
            </g>
            <g class="hair-style hair-long-wavy" data-style="long-wavy" style="display:none">
              <rect x="9" y="3" width="14" height="2" fill="var(--avatar-hair)"/>
              <rect x="8" y="5" width="16" height="2" fill="var(--avatar-hair)"/>
              <rect x="15" y="5" width="2" height="2" fill="var(--avatar-skin)"/>
              <rect x="8" y="7" width="3" height="2" fill="var(--avatar-hair)"/>
              <rect x="21" y="7" width="3" height="2" fill="var(--avatar-hair)"/>
              <rect x="8" y="9" width="2" height="22" fill="var(--avatar-hair)"/>
              <rect x="22" y="9" width="2" height="22" fill="var(--avatar-hair)"/>
              <rect x="7" y="22" width="1" height="3" fill="var(--avatar-hair)"/>
              <rect x="24" y="22" width="1" height="3" fill="var(--avatar-hair)"/>
              <rect x="7" y="20" width="2" height="11" fill="var(--avatar-hair)"/>
              <rect x="23" y="20" width="2" height="11" fill="var(--avatar-hair)"/>
              <rect x="6" y="27" width="1" height="3" fill="var(--avatar-hair)"/>
              <rect x="25" y="27" width="1" height="3" fill="var(--avatar-hair)"/>
              <rect x="10" y="6" width="3" height="1" fill="var(--avatar-hair)" opacity="0.6"/>
              <rect x="19" y="6" width="3" height="1" fill="var(--avatar-hair)" opacity="0.6"/>
            </g>
          </svg>
          <div style="position:absolute;bottom:4px;right:4px;background:rgba(26,14,46,0.7);color:#fff;font-family:\'VT323\',monospace;font-size:10px;letter-spacing:1px;padding:2px 4px;pointer-events:none;">EDIT</div>
        </div>'''

def fix_chapter_avatar(html):
    """Replace hardcoded avatar SVG in chapter sidebars with the dynamic CSS-var version."""
    return re.sub(
        r'<div class="avatar-frame">\s*<svg[^>]*>[\s\S]*?</svg>\s*</div>',
        DYNAMIC_AVATAR_FRAME,
        html,
    )

def process(path):
    return adapt(extract_body(path))

def process_chapter(path):
    return fix_chapter_avatar(process(path))

# ── Build scoped CSS blocks ────────────────────────────────────────────────

SCREEN_CSS_MAP = [
    # (scope_selector,  mockup_file)
    ("#screen-intro",   "persona-selection-mockup.html"),
    ("#screen-avatar",  "avatar-creation-mockup.html"),
    ("#screen-map",     "journey-map-mockup.html"),
    # All chapter screens share the same design system CSS.
    # Use chapter 2 as source: it has the full quest/action-item/checkbox CSS
    # that chapter 1 lacks (chapter 1 has no quests, so its CSS omits those rules).
    ("#screen-ch1, #screen-ch2, #screen-ch3, #screen-ch4, #screen-ch5, #screen-ch6, #screen-ch7",
                        "chapter-2-first-light-alex-mockup.html"),
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
html_ch = {n: process_chapter(MOCKUPS / f) for n, f in [
    (1, "chapter-1-long-night-jordan-mockup.html"),
    (2, "chapter-2-first-light-alex-mockup.html"),
    (3, "chapter-3-search-begins-taylor-mockup.html"),
    (4, "chapter-4-crossroads-jamie-mockup.html"),
    (5, "chapter-5-first-hello-jordan-mockup.html"),
    (6, "chapter-6-the-key-jamie-mockup.html"),
    (7, "chapter-7-welcome-mat-alex-mockup.html"),
]}
html_ultimate = fix_chapter_avatar(process(MOCKUPS / "ultimate-quest-mockup.html"))

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
  jordan: {
    fullName: 'Jordan the Rising Star', shortName: 'Jordan', color: '#FF974D',
    from: 'Portland, OR', to: 'Seattle, WA', timeframe: '18 days',
    currentRent: '$1,650', budget: '$2,400',
    bio: 'Jordan got the offer last week. New job in Seattle, three weeks to land. Right now they\'re standing in their Portland apartment looking at a corner about to fill with moving boxes, with Max the golden retriever asleep on the dog bed that has to get packed first. Excited about the role, slightly underslept, a little bit panicking.\n\nThe shortlist has shape but not edges. A yard would be ideal, a park within walking distance will do. A real home office matters because the new role is hybrid. Pet-friendly isn\'t a perk for Jordan\u2014Max needs to actually be welcome.\n\nEighteen days isn\'t a lot of time to chase ghost listings or wait three days for a property to respond.'
  },
  alex: {
    fullName: 'Alex the Ambitious', shortName: 'Alex', color: '#6105C4',
    from: 'San Francisco, CA', to: 'San Francisco, CA', timeframe: '~60 days',
    currentRent: '$2,500', budget: '$4,200',
    bio: 'Alex is a senior engineer in San Francisco. Three years in the same studio, the salary has gone up but the square footage hasn\'t. The lease non-renewal came last week, and Alex is treating it as permission to finally upgrade.\n\nThe wishlist is specific: a real kitchen with counter space, a bedroom door that closes, somewhere for the bike that isn\'t a wall mount. One bedroom is the floor. Hayes Valley keeps coming back if the budget can stretch.\n\nAlex hunts with a spreadsheet drafted before the lease notice came. Three platforms, one right monitor. The standards aren\'t flexible, but the budget might be.'
  },
  taylor: {
    fullName: 'Taylor & Riley', shortName: 'Taylor & Riley', color: '#C384F0',
    from: 'Chicago, IL', to: 'Austin, TX', timeframe: 'Open timeline',
    currentRent: '$2,200', budget: '$2,500',
    bio: 'Taylor and Riley have been in Chicago for three years, the longest they\'ve stayed anywhere. Polaroids from Lisbon are still on the fridge, Riley\'s camera lives next to the toaster. The plan\u2014forming for months\u2014is to leave Chicago for Austin.\n\nThey search together. Listings get screenshot-shared between phones. Riley reads Reddit threads about Austin neighborhoods. Taylor texts friends who\'ve lived there. They decide together.\n\nLow urgency, very high preference clarity on neighborhood vibe. The apartment has to feel right for both of them.'
  },
  jamie: {
    fullName: 'Jamie the Planner', shortName: 'Jamie', color: '#5C8841',
    from: 'Suburban Philadelphia, PA', to: 'Jersey City, NJ', timeframe: '~5 months',
    currentRent: '$1,500', budget: '$3,200',
    bio: 'Jamie is a single parent in suburban Philadelphia, but their family support system is in Jersey. Daughter Emma starts kindergarten in five months, which means whatever happens next has to happen fast. The plan is Jersey City. The schools are good, the transit is doable, but the budget is tight.\n\nEvery search filter does double duty. School zone and pet-friendly. Budget cap and laundry in-unit. Jamie hasn\'t fully committed yet because committing means it\'s real.\n\nThe clock is running. There\'s no room for ghost listings or slow agents.'
  },
};

function applyPersonaTheme(key) {
  var meta = PERSONA_META[key] || PERSONA_META.jordan;
  document.documentElement.style.setProperty('--persona-color', meta.color);
}

var VALID_SCREENS = ['screen-intro','screen-avatar','screen-map',
  'screen-ch1','screen-ch2','screen-ch3','screen-ch4',
  'screen-ch5','screen-ch6','screen-ch7','screen-ultimate'];

var RJ = window.RJ = {
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

// ── Field notes helpers ───────────────────────────────────────────────────
function noteIdFor(ta, chNum, idx) {
  var questEl = ta.closest('[data-quest]');
  var qId = questEl ? questEl.getAttribute('data-quest') : (chNum + '-' + idx);
  return 'note-ch' + chNum + '-q' + String(qId).replace(/\./g, '-');
}
function labelFor(ta, chNum, idx) {
  var questEl = ta.closest('[data-quest]');
  if (questEl) {
    var h = questEl.querySelector('h3');
    if (h && h.textContent.trim()) return h.textContent.trim();
    return 'Quest ' + questEl.getAttribute('data-quest');
  }
  // No quest wrapper (e.g. chapter 1 plain reflections): use the <label> sibling
  var prompt = ta.closest('.reflection-prompt');
  if (prompt) {
    var lbl = prompt.querySelector('label');
    if (lbl && lbl.textContent.trim()) return lbl.textContent.trim();
  }
  return 'Reflection ' + (idx + 1);
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

var CH_NAMES = ['','The Long Night','First Light','The Search Begins','The Crossroads','The First Hello','The Key','The Welcome Mat'];

function refreshNotesCard(chNum) {
  var screenEl = document.getElementById('screen-ch' + chNum);
  if (!screenEl) return;
  var notesCard = screenEl.querySelector('.notes-card');
  if (!notesCard) return;
  var profile = loadProfile();
  // Show ALL notes for this persona across every chapter, newest first
  var notes = getPersonaNotes(profile.persona).slice().sort(function(a, b) { return (a.ts || 0) - (b.ts || 0); });

  var h3 = notesCard.querySelector('h3');
  if (h3) {
    h3.innerHTML = 'Field Notes <span style="font-family:\'VT323\',monospace;font-size:13px;color:var(--ink-soft);letter-spacing:1px;">'
      + notes.length + ' saved</span>';
  }

  var list = notesCard.querySelector('.notes-list');
  if (!list) return;

  if (notes.length === 0) {
    list.innerHTML = '<div class="note empty"><p class="note-text">Nothing yet. Your reflections will appear here as you save them.</p></div>';
    return;
  }

  list.innerHTML = notes.map(function(note, idx) {
    var questLabel = note.label || ('Note ' + (idx + 1));
    var chLabel    = note.chapter ? 'Ch. ' + note.chapter + ' \u00b7 ' + (CH_NAMES[note.chapter] || '') : '';
    var metaLine   = chLabel ? escHtml(chLabel) + '<br>' + escHtml(questLabel) : escHtml(questLabel);
    return '<div class="note">'
      + '<div class="note-meta">' + metaLine + '</div>'
      + '<p class="note-text">' + escHtml(note.text) + '</p>'
      + '<div class="note-actions">'
      + '<button class="copy-btn" data-copy="' + escHtml(note.text) + '">Copy to Slack</button>'
      + '</div></div>';
  }).join('');

  list.querySelectorAll('.copy-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var text = btn.getAttribute('data-copy');
      if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(function() {
          btn.textContent = 'Copied!';
          setTimeout(function() { btn.textContent = 'Copy to Slack'; }, 1500);
        });
      } else {
        var ta = document.createElement('textarea');
        ta.value = text; document.body.appendChild(ta); ta.select(); document.execCommand('copy');
        document.body.removeChild(ta);
        btn.textContent = 'Copied!';
        setTimeout(function() { btn.textContent = 'Copy to Slack'; }, 1500);
      }
    });
  });
}

// ── Chapter screens ───────────────────────────────────────────────────────
function syncChapterScreen(n) {
  var profile  = loadProfile();
  var screenEl = document.getElementById('screen-ch' + n);
  if (!screenEl) return;
  applyPersonaTheme(profile.persona);

  var meta = PERSONA_META[profile.persona] || PERSONA_META.jordan;

  // Top bar: "Now Playing As ___"
  var topName = screenEl.querySelector('.persona-context .name');
  if (topName) topName.textContent = meta.fullName;

  // Sidebar HUD: name, class chip, move stats, bio
  var hudName = screenEl.querySelector('.hud-meta .name');
  if (hudName) hudName.textContent = meta.shortName;

  var hudChip = screenEl.querySelector('.hud-meta .class-chip');
  if (hudChip) hudChip.textContent = PERSONA_CHIPS[profile.persona] || '';

  var moveInfo = screenEl.querySelector('.move-info');
  if (moveInfo && meta.from) {
    moveInfo.innerHTML =
      '<dt>From</dt><dd>' + meta.from + '</dd>' +
      '<dt>To</dt><dd>' + meta.to + '</dd>' +
      '<dt>In</dt><dd>' + meta.timeframe + '</dd>' +
      '<dt>Current rent</dt><dd>' + meta.currentRent + '</dd>' +
      '<dt>Budget</dt><dd>' + meta.budget + '</dd>';
  }

  var bioSummaryName = screenEl.querySelector('.hud-bio-summary span:first-child');
  if (bioSummaryName) bioSummaryName.textContent = 'About ' + meta.shortName;

  var bioBody = screenEl.querySelector('.hud-bio-body');
  if (bioBody && meta.bio) {
    bioBody.innerHTML = meta.bio.split('\n\n').map(function(p) {
      return '<p>' + p + '</p>';
    }).join('');
  }

  // Apply saved avatar CSS vars to chapter HUD sprite
  Object.keys(AVATAR_VARS).forEach(function(k) {
    if (profile[k]) document.documentElement.style.setProperty(AVATAR_VARS[k], profile[k]);
  });
  if (profile.skin && SKIN_TO_LIP[profile.skin])
    document.documentElement.style.setProperty('--avatar-lip', SKIN_TO_LIP[profile.skin]);

  // Show the correct hair style in the chapter sidebar sprite
  var hs = profile.hairStyle || 'short';
  screenEl.querySelectorAll('.avatar-frame .hair-style').forEach(function(g) {
    g.style.display = (g.getAttribute('data-style') === hs) ? '' : 'none';
  });

  // Wire change-renter (once)
  var changeEl = screenEl.querySelector('.persona-context .change:not([data-wired])');
  if (changeEl) {
    changeEl.setAttribute('data-wired','1');
    changeEl.style.cursor = 'pointer';
    changeEl.addEventListener('click', function() { RJ.navigate('screen-intro'); });
  }

  // Quest checkbox wiring is deferred to the data-ch-wired block below

  // Gate + blur-save wiring (once per chapter screen lifetime)
  var continueBtn = screenEl.querySelector('#continueBtn');
  var reflInputs  = screenEl.querySelectorAll('.reflection-input');
  var coreChecks  = screenEl.querySelectorAll('.quest:not(.optional) .quest-check');
  var statusEl    = screenEl.querySelector('#reflectionStatus');

  function gateUpdate() {
    var reflOk   = Array.from(reflInputs).every(function(ta) { return ta.value.trim().length >= 4; });
    var questsOk = !coreChecks.length || Array.from(coreChecks).every(function(c) { return c.checked; });
    var allDone  = reflOk && questsOk;
    if (statusEl) {
      if (allDone) {
        statusEl.textContent = 'Reflection complete \u00b7 ready to walk on';
        statusEl.classList.add('complete');
      } else {
        var filled  = Array.from(reflInputs).filter(function(ta) { return ta.value.trim().length >= 4; }).length;
        var checked = Array.from(coreChecks).filter(function(c) { return c.checked; }).length;
        statusEl.textContent = 'Quests: ' + checked + '/' + coreChecks.length
          + ' \u00b7 Reflections: ' + filled + '/' + reflInputs.length;
        statusEl.classList.remove('complete');
      }
    }
    if (continueBtn) {
      if (allDone) { continueBtn.classList.remove('disabled'); continueBtn.removeAttribute('aria-disabled'); }
      else         { continueBtn.classList.add('disabled');    continueBtn.setAttribute('aria-disabled','true'); }
    }
  }

  // Restore saved textarea values from localStorage on every visit
  reflInputs.forEach(function(ta, i) {
    var savedNote = getPersonaNotes(profile.persona).filter(function(n_) { return n_.id === noteIdFor(ta, n, i); })[0];
    if (savedNote && !ta.value) ta.value = savedNote.text;
  });

  // Wire once
  if (!screenEl.getAttribute('data-ch-wired')) {
    screenEl.setAttribute('data-ch-wired', '1');

    // Quest checkboxes: step-check ↔ master quest-check
    screenEl.querySelectorAll('.quest').forEach(function(quest) {
      var steps  = quest.querySelectorAll('.step-check');
      var master = quest.querySelector('.quest-check');
      if (!steps.length || !master) return;
      steps.forEach(function(s) {
        s.addEventListener('change', function() {
          master.checked = Array.from(steps).every(function(c) { return c.checked; });
          gateUpdate();
        });
      });
      master.addEventListener('change', function() {
        if (master.checked) steps.forEach(function(s) { s.checked = true; });
        gateUpdate();
      });
    });

    reflInputs.forEach(function(ta) { ta.addEventListener('input', gateUpdate); });
    coreChecks.forEach(function(c)  { c.addEventListener('change', gateUpdate); });

    // Save to field notes on blur
    reflInputs.forEach(function(ta, i) {
      ta.addEventListener('blur', function() {
        var text = ta.value.trim();
        if (!text) return;
        saveNote({ id: noteIdFor(ta, n, i), persona: profile.persona, chapter: n, label: labelFor(ta, n, i), text: text, ts: Date.now() });
        refreshNotesCard(n);
      });
    });

    // Walk on
    if (continueBtn) {
      continueBtn.addEventListener('click', function(e) {
        e.preventDefault();
        if (continueBtn.classList.contains('disabled')) return;
        reflInputs.forEach(function(ta, i) {
          var text = ta.value.trim();
          if (!text) return;
          saveNote({ id: noteIdFor(ta, n, i), persona: profile.persona, chapter: n, label: labelFor(ta, n, i), text: text, ts: Date.now() });
        });
        var prof = loadProfile();
        if (n + 1 <= 7 && n + 1 > prof.unlockedChapter) saveProfile({ unlockedChapter: n + 1 });
        RJ.navigate(n < 7 ? 'screen-ch' + (n + 1) : 'screen-ultimate');
      });
    }
  }

  // Run gate on every visit (picks up restored values)
  gateUpdate();

  // Populate notes sidebar from localStorage (all chapters)
  refreshNotesCard(n);
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
  var _p = loadProfile();
  applyPersonaTheme(_p.persona);
  // Apply saved avatar CSS vars immediately so sprites render correctly
  Object.keys(AVATAR_VARS).forEach(function(k) {
    if (_p[k]) document.documentElement.style.setProperty(AVATAR_VARS[k], _p[k]);
  });
  if (_p.skin && SKIN_TO_LIP[_p.skin])
    document.documentElement.style.setProperty('--avatar-lip', SKIN_TO_LIP[_p.skin]);
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

for out_name in ["renters-journey.html", "index.html"]:
    out_path = BASE / out_name
    out_path.write_text(output, encoding="utf-8")
    print(f"Written {out_path}")
lines = output.count('\n')
print(f"  {len(output):,} bytes / {lines:,} lines")
