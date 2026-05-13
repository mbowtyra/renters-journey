#!/usr/bin/env python3
"""
Stitch mockup HTML files into renters-journey.html (single-page app).
Each screen's CSS is scoped to its screen ID to prevent cross-screen conflicts.
"""

import re
import json
from pathlib import Path

BASE    = Path("/Users/melissabowden/Documents/Dev/Renter's Journey")
MOCKUPS = BASE / "mockups"
MEMORY  = BASE / "memory"

# ── Content-file parser ─────────────────────────────────────────────────────

def _field(label, text):
    """Return first occurrence of **Label:** value on same line, or None."""
    m = re.search(r'\*\*' + re.escape(label) + r':\*\*\s*(.+)', text)
    return m.group(1).strip() if m else None

def _field_block(label, text):
    """Return multi-line content after **Label:** until next blank line or ## heading."""
    m = re.search(r'\*\*' + re.escape(label) + r':\*\*\s*\n([\s\S]+?)(?=\n\n|\n##|\Z)', text)
    if not m:
        return None
    return m.group(1).strip()

def _section_prose(heading, text):
    """Return the prose paragraph immediately after ### heading (until next ### or ## or ---)."""
    m = re.search(
        r'### ' + re.escape(heading) + r'\s*\n+([\s\S]+?)(?=\n###|\n##|\n---|\Z)',
        text
    )
    if not m:
        return None
    # Return first non-empty paragraph
    para = m.group(1).strip().split('\n\n')[0].strip()
    return para if para else None

def _parse_surface(surface_str):
    """Extract surface list from a markdown surface string."""
    if not surface_str:
        return []
    surfaces = []
    # Find all markdown links [text](url)
    for text, href in re.findall(r'\[([^\]]+)\]\(([^)]+)\)', surface_str):
        surfaces.append({'text': text, 'href': href})
    # Anything left after stripping links becomes a plain-text surface
    remainder = re.sub(r'\[[^\]]+\]\([^)]+\)', '', surface_str)
    remainder = re.sub(r'\s*[→,]\s*', ' ', remainder).strip(' ,→')
    if remainder and not surfaces:
        surfaces.append({'text': remainder, 'href': None})
    return surfaces

def _parse_steps(body):
    """Return list of action step strings from a bullet list after **Action steps:**."""
    m = re.search(r'\*\*Action steps:\*\*\s*\n((?:[-*]\s+.+\n?)+)', body)
    if not m:
        return []
    lines = m.group(1).strip().split('\n')
    return [re.sub(r'^[-*]\s+', '', l).strip() for l in lines if l.strip()]

def _parse_sit_with_it(body):
    """Return list of sit-with-it bullet strings (scenario quests)."""
    m = re.search(r'\*\*Sit with it:\*\*\s*\n((?:[-*]\s+.+\n?)+)', body)
    if not m:
        return []
    lines = m.group(1).strip().split('\n')
    return [re.sub(r'^[-*]\s+', '', l).strip() for l in lines if l.strip()]

def _parse_quest(body, optional=False):
    """Parse a single quest/side-quest block into a dict."""
    label    = _field('Label', body)
    title    = _field('Title', body)
    surface_raw = _field('Surface', body)
    headsup  = _field('Heads-up', body)
    scenario = _field_block('Scenario', body)
    steps    = _parse_steps(body)
    sit      = _parse_sit_with_it(body)
    refl     = _field('Reflection', body)
    # Some reflections span multiple sentences on the same line — get full text
    if not refl:
        m = re.search(r'\*\*Reflection:\*\*\s*\n(.+)', body)
        refl = m.group(1).strip() if m else None
    return {
        'label':    label,
        'title':    title,
        'optional': optional,
        'surfaces': _parse_surface(surface_raw) if surface_raw else [],
        'headsup':  headsup,
        'scenario': scenario,
        'steps':    steps,
        'sitWithIt': sit,
        'reflection': refl,
    }

def _parse_final_reflection(body):
    return {
        'heading': _field('Heading', body),
        'intro':   _field('Intro', body),
        'prompt':  _field('Prompt', body),
    }

def parse_content_file(fpath):
    """Parse a content-*.md file and return dict keyed by chapter number (int)."""
    text = open(fpath, encoding='utf-8').read()
    result = {}

    # Split on '## Chapter N:' headings
    ch_parts = re.split(r'## Chapter (\d+):', text)
    for i in range(1, len(ch_parts), 2):
        ch_num = int(ch_parts[i])
        ch_body = ch_parts[i + 1]

        # Tonight-card fields
        eyebrow   = _field('Eyebrow', ch_body)
        blurb     = _field_block('Blurb', ch_body)
        mapTeaser = _section_prose('Map teaser', ch_body)
        # Reflection labels (ch1 persona-specific)
        q1      = _field('Q1 label', ch_body)
        q2      = _field('Q2 label', ch_body)
        q2hint  = _field('Q2 hint', ch_body)
        refl_intro = _field('Intro', ch_body)  # first Intro = reflection heading intro

        quests      = []
        side_quests = []
        final_refl  = {}

        # Split on ### headings for quests
        sect_parts = re.split(r'### ((?:Quest \d+\.\d+|Side Quest|Final Reflection)[^\n]*)\n', ch_body)
        for j in range(1, len(sect_parts), 2):
            heading = sect_parts[j].strip()
            body    = sect_parts[j + 1]
            if heading.startswith('Final Reflection'):
                final_refl = _parse_final_reflection(body)
            elif heading.startswith('Side Quest'):
                sq = _parse_quest(body, optional=True)
                sq['sideLabel'] = re.sub(r'^Side Quest:\s*', '', heading).strip()
                side_quests.append(sq)
            elif re.match(r'Quest \d+\.\d+', heading):
                quests.append(_parse_quest(body, optional=False))

        result[ch_num] = {
            'eyebrow':       eyebrow,
            'blurb':         blurb,
            'mapTeaser':     mapTeaser,
            'q1':            q1,
            'q2':            q2,
            'q2hint':        q2hint,
            'reflectionIntro': refl_intro,
            'quests':        quests,
            'sideQuests':    side_quests,
            'finalReflection': final_refl,
        }

    return result

def parse_journals():
    """Extract each persona's ch1 journal paragraphs from memory/renter-journey.md."""
    text = open(MEMORY / 'renter-journey.md', encoding='utf-8').read()
    # Match headings like "### Alex's journal" or "### Taylor's journal"
    parts = re.split(r"### ([\w][\w &']+)'s journal", text)
    journals = {}
    for i in range(1, len(parts), 2):
        # First word lowercased = key: alex, jordan, taylor, jamie
        key = parts[i].strip().lower().split()[0]
        body = parts[i + 1]
        # Stop at next heading
        body = re.split(r'\n##', body)[0].strip()
        paras = [p.strip() for p in body.split('\n\n') if p.strip()]
        journals[key] = paras
    return journals

def build_persona_chapters():
    """Read all four content files and return a dict suitable for JSON serialisation."""
    files = [
        ('jordan',  MEMORY / 'content-jordan.md'),
        ('alex',    MEMORY / 'content-alex.md'),
        ('taylor',  MEMORY / 'content-taylor-riley.md'),
        ('jamie',   MEMORY / 'content-jamie.md'),
    ]
    data = {}
    for key, path in files:
        data[key] = parse_content_file(path)

    # Attach canonical journal paragraphs to each persona's ch1 entry
    journals = parse_journals()
    for persona_key, chapters in data.items():
        if 1 in chapters and persona_key in journals:
            chapters[1]['journalParas'] = journals[persona_key]

    return data

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

var PERSONA_CRITERIA = {
  alex: {
    mustHaves: [
      'One bedroom with a door that closes',
      'A real kitchen with counter space',
      'Twelve-minute commute to the office',
      'Monthly rent under $4,200'
    ],
    wants: [
      'Two bedrooms if Hayes Valley delivers under budget',
      'Hayes Valley neighborhood feel',
      'Bike storage that isn\'t a wall mount',
      'Building gym worth using'
    ]
  },
  jordan: {
    mustHaves: [
      'Pet-friendly (Max actually welcome, not tolerated)',
      'Move-in inside the eighteen-day window',
      'Leasing offices that reply within 24 hours',
      'Monthly rent under $2,400',
      'No ghost listings or units older than 30 days'
    ],
    wants: [
      'A yard for Max',
      'A park within walking distance',
      'A real home office (hybrid role, kitchen-table won\'t cut it)',
      'A short commute on hybrid days'
    ]
  },
  taylor: {
    mustHaves: [
      'Walkable neighborhood (their daily geography)',
      'Real local food scene (taquerias, markets, roasters)',
      'A street they can hear from the window',
      'Combined rent under $2,500'
    ],
    wants: [
      'Two-bedroom unit',
      'Natural light Riley can shoot in',
      'A photography scene that lives outside galleries',
      'Weekend tours bookable without a phone call'
    ]
  },
  jamie: {
    mustHaves: [
      'Two-bedroom (Emma\'s room is non-negotiable)',
      'Strong, verifiable school district',
      'Safe streets and a walkable park',
      'Move-in before Emma\'s kindergarten start',
      'Monthly rent under $3,200'
    ],
    wants: [
      'Pet-friendly (Emma keeps asking about a small dog)',
      'Transit-friendly to the family support network',
      'In-unit laundry',
      'A buzzing local park'
    ]
  }
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
  var existing = loadProfile();
  // Clear wiring so chapter screens re-render fresh for the new persona
  if (existing.persona && existing.persona !== key) {
    document.querySelectorAll('.screen').forEach(function(s) {
      s.removeAttribute('data-ch-wired');
      s.removeAttribute('data-wired-persona');
    });
  }
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
  localStorage.removeItem(NOTES_KEY);
  // Clear wiring state so all chapter screens fully re-render for the new persona
  document.querySelectorAll('.screen').forEach(function(s) {
    s.removeAttribute('data-ch-wired');
    s.removeAttribute('data-wired-persona');
  });
  selectPersona(key);
  var h = document.getElementById('rjSwitchDialogHolder');
  if (h) h.innerHTML = '';
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
  var mapEl = document.getElementById('screen-map');
  if (!mapEl) return;

  // Top-bar persona name
  var nameEl = mapEl.querySelector('.persona-context .name');
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
  mapEl.querySelectorAll('.avatar-frame .hair-style').forEach(function(g) {
    g.style.display = (g.getAttribute('data-style') === hs) ? '' : 'none';
  });

  // ── Persona-aware map copy (runs on every visit) ───────────────────────
  var poss = meta.shortName + (meta.shortName.slice(-1) === 's' ? "'" : "'s");
  var _MAP_NAMES = ['Jordan', 'Alex', 'Taylor', 'Jamie'];
  function _swapMapName(html) {
    _MAP_NAMES.forEach(function(n) {
      html = html.replace(new RegExp('\\b' + n + "'s\\b", 'g'), poss);
      html = html.replace(new RegExp('\\b' + n + '\\b', 'g'), meta.shortName);
    });
    return html;
  }

  // Hero lede — name-swap is sufficient here (generic narrative)
  var lede = mapEl.querySelector('.hero .lede');
  if (lede) lede.innerHTML = _swapMapName(lede.innerHTML);

  // Hero-meta chips: Field Notes count + current chapter
  var noteCount = getPersonaNotes(profile.persona).length;
  var noteChip = mapEl.querySelector('.hero-meta .chip-notes');
  if (noteChip) noteChip.innerHTML = '<strong>Field Notes:</strong> ' + noteCount + ' saved';

  var chChip = mapEl.querySelector('.hero-meta .chip-chapter');
  if (chChip) {
    var curCh = profile.unlockedChapter || 1;
    chChip.innerHTML = '<span class="dot"></span><strong>You\'re at:</strong> Chapter ' + curCh + ' \u00b7 ' + (CH_NAMES[curCh] || '');
  }

  // Chapter-card teasers: use fully persona-specific copy from PERSONA_CHAPTERS
  var pChapters = PERSONA_CHAPTERS[profile.persona] || PERSONA_CHAPTERS.jordan;
  mapEl.querySelectorAll('.chapter-card').forEach(function(card, idx) {
    var chNum = idx + 1;
    var chData = pChapters[chNum];
    var teaserEl = card.querySelector('.teaser');
    if (teaserEl && chData && chData.mapTeaser) {
      teaserEl.textContent = chData.mapTeaser;
    }
  });

  // Wire change-renter (once)
  var changeEl = mapEl.querySelector('.persona-context .change:not([data-wired])');
  if (changeEl) { changeEl.setAttribute('data-wired','1'); changeEl.style.cursor='pointer'; changeEl.addEventListener('click',function(){RJ.navigate('screen-intro');}); }

  // Apply lock/unlock state to chapter cards
  var cards = mapEl.querySelectorAll('.chapter-card');
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

// Persona-specific tonight-cards and reflection text for each chapter.
// Sourced verbatim from memory/content-{persona}.md.
var PERSONA_CHAPTERS = {
  alex: {
    1: {
      eyebrow: 'Where Alex is tonight',
      blurb: "Alex got the lease non-renewal today and they're at their studio desk, already running the numbers. Here's what was running through their head.",
      q1: "What stood out to you about the start of Alex's renter journey?",
      q2: 'What is Alex looking for in an apartment?',
      q2hint: "What's negotiable, and what's not?",
      reflectionIntro: 'Scan Alex\'s journal entry again and reread their "About Alex" bio in the upper right corner. When you\'re ready, reflect below.',
    },
    2: {
      eyebrow: 'Where Alex starts',
      blurb: 'After last night\u2019s spreadsheet session, Alex sits down with the laptop after work. Three browser tabs open: Apartment List, Zillow, Apartments.com. The spreadsheet is on the right monitor. Apartment List has about sixty seconds to make a first impression.',
      reflectionIntro: 'After the homepage, the Renter Tools, and the content, sit with one last question. Alex has a spreadsheet and standards.',
    },
    3: {
      eyebrow: 'Where Alex starts',
      blurb: 'Alex has cleared Sunday afternoon for the quiz. The spreadsheet is on the second monitor. Apartment List gets five minutes to prove it understands what \u201cone bedroom, Hayes Valley, $4,200 hard cap\u201d actually means.',
      reflectionIntro: 'After the quiz, the signup, and the first scroll through the matches, sit with one last question. Alex answered fourteen steps. Apartment List made its bets.',
    },
    4: {
      eyebrow: 'Where Alex starts',
      blurb: 'The cycling has been running in the background for two days. The shortlist has eight properties. Alex opens the spreadsheet, adds a comparison column, and starts reading LDPs slowly. Tonight eight becomes three.',
      reflectionIntro: 'After the shortlist, the deep read, and the outside research pass, sit with one last question.',
    },
    5: {
      eyebrow: 'Where Alex starts',
      blurb: 'Three contenders, three messages queued. Alex has one list of questions for all three leasing offices: smart home features, exact monthly cost, earliest move-in date. The 24-hour rule applies. Tonight they hit send.',
      reflectionIntro: "After the first message, the tour booking, and the walkthrough through a screen, sit with one last question. Alex's 24-hour rule is doing real work now.",
    },
    6: {
      eyebrow: 'Where Alex starts',
      blurb: 'The Hayes Valley place said yes. The Docusign link arrived at 6pm. Alex is reading the lease.',
      reflectionIntro: 'After the pick, the lease read, and the Renter Hub walk, sit with one last question.',
    },
    7: {
      eyebrow: 'Where Alex starts',
      blurb: 'Six months in. The Hayes Valley place feels like home now. The bike is on the wall mount, the kitchen has real counter space, the bedroom door closes. Alex hasn\u2019t opened the Apartment List app in three months, but they never deleted it. Today an email landed from Apartment List, and somewhere on Alex\u2019s phone there\u2019s a notification asking for a review.',
      reflectionIntro: 'After the stray email, the review moment, and the blog stroll, sit with one last question.',
    },
  },
  jordan: {
    1: {
      eyebrow: 'Where Jordan is tonight',
      blurb: "Jordan got a new job, and they're up late journaling and thinking about the move. Here's what was running through their head.",
      q1: "What stood out to you about the start of Jordan's renter journey?",
      q2: 'What is Jordan looking for in an apartment?',
      q2hint: "What's negotiable, and what's not?",
      reflectionIntro: 'Scan Jordan\'s journal entry again and reread their "About Jordan" bio in the upper right corner. When you\'re ready, reflect below.',
    },
    2: {
      eyebrow: 'Where Jordan starts',
      blurb: "The job starts in sixteen days. Jordan is on the couch in Portland with Max asleep at their feet, phone out, searching for Seattle apartments. Apartment List came up. They click in. They haven't taken the quiz and aren't sure they have time for it.",
      reflectionIntro: 'After the homepage, the Renter Tools, and the content, sit with one last question. Jordan has sixteen days.',
    },
    3: {
      eyebrow: 'Where Jordan starts',
      blurb: "Thirteen days. Jordan takes the quiz on their phone. Max is on the couch next to them. The quiz wants to know about Jordan's personality type. Jordan clicks through it.",
      reflectionIntro: 'After the quiz, the signup, and the first scroll through the matches, sit with one last question. Thirteen days is a short window.',
    },
    4: {
      eyebrow: 'Where Jordan starts',
      blurb: 'Ten days left. Jordan has eight properties in their shortlist, all in Seattle. They search each one on Reddit. Two have management complaints. One has a dog park within a quarter mile. Jordan moves that one to the top.',
      reflectionIntro: 'After the shortlist, the pet clause deep-read, and the outside research, sit with one last question.',
    },
    5: {
      eyebrow: 'Where Jordan starts',
      blurb: "Jordan has two live remote tours scheduled. The first is Tuesday morning. There's no time to wait three days for a property to respond. The eighteen-day window closes next Monday.",
      reflectionIntro: 'After the first message, the tour booking, and the walkthrough through a screen, sit with one last question. Jordan has eighteen days. One of these contenders has to start feeling like a place to land.',
    },
    6: {
      eyebrow: 'Where Jordan starts',
      blurb: 'The live remote tour was Tuesday morning. The agent walked through every closet and showed the back yard for Max. Jordan has been thinking about it since. The pet rent is $75 a month. The lease is due back by tomorrow.',
      reflectionIntro: 'After the pick, the lease read, and the Renter Hub walk, sit with one last question.',
    },
    7: {
      eyebrow: 'Where Jordan starts',
      blurb: "Three weeks in Seattle. Max has claimed a corner of the back yard. Jordan's new colleagues keep asking where they found their place. The five-star review went up the morning after signing. The app is still on the phone.",
      reflectionIntro: 'After the stray email, the review moment, and the blog stroll, sit with one last question.',
    },
  },
  taylor: {
    1: {
      eyebrow: 'Where Taylor & Riley are tonight',
      blurb: 'Riley said \u201cwhere next\u201d again last night. Taylor knew it was coming before they said it. Three years in Chicago, the Polaroids from Lisbon still on the fridge. Austin is winning. Here\'s what was running through Taylor\'s head.',
      q1: "What stood out to you about the start of Taylor & Riley's renter journey?",
      q2: 'What is Taylor & Riley looking for in an apartment?',
      q2hint: "What's negotiable, and what's not?",
      reflectionIntro: 'Scan Taylor\'s journal entry again and reread the "About Taylor & Riley" bio in the upper right corner. When you\'re ready, reflect below.',
    },
    2: {
      eyebrow: 'Where Taylor & Riley start',
      blurb: 'Taylor and Riley have been sending each other Google Maps links to Austin neighborhoods for two weeks. Tonight they sit down together with the laptop and open Apartment List for the first time. Riley is already asking about the map view.',
      reflectionIntro: 'After the homepage, the Renter Tools, and the content, sit with one last question. Two people, one city, no commitments yet.',
    },
    3: {
      eyebrow: 'Where Taylor & Riley start',
      blurb: "Taylor and Riley are on the laptop together. The quiz is open. The budget step is coming and they're already arguing about the number. $2,500 is where they've landed, but Riley keeps looking at $2,800 options in East Austin.",
      reflectionIntro: 'After the quiz, the welcome screen, and the first scroll through the matches, sit with one last question. Two people, one search, no commitments yet.',
    },
    4: {
      eyebrow: 'Where Taylor & Riley start',
      blurb: "Taylor and Riley have twelve properties in their shortlist. They review it over a shared screen on Sunday afternoon. Riley pulls up Street View on each one. They settle on six. Three feel like them. Three don't, but they're still arguing about which is which.",
      reflectionIntro: 'After the shortlist, the deep read, and the outside research, sit with one last question.',
    },
    5: {
      eyebrow: 'Where Taylor & Riley start',
      blurb: "One property on top. Taylor wants to schedule a Sunday morning tour. The in-app scheduler doesn't have Sunday slots. They call the leasing office. The agent picks up. The tour is booked for this weekend.",
      reflectionIntro: 'After the first message, the tour booking, and the walkthrough through a screen, sit with one last question.',
    },
    6: {
      eyebrow: 'Where Taylor & Riley start',
      blurb: 'Taylor and Riley spent two days on the lease. Riley pushed on the move-in date. Taylor pushed on the deposit. They got the move-in date. They accepted the deposit. Both of them sign on a Saturday morning, with coffee.',
      reflectionIntro: 'After the pick, the lease read, and the Renter Hub walk, sit with one last question.',
    },
    7: {
      eyebrow: 'Where Taylor & Riley start',
      blurb: "Six months in East Austin. Taylor's notebook is full. Riley has a wall of prints from the neighborhood. The Apartment List newsletter arrives most Tuesdays. They've told three people to use the app.",
      reflectionIntro: 'After the stray email, the review moment, and the blog stroll, sit with one last question.',
    },
  },
  jamie: {
    1: {
      eyebrow: 'Where Jamie is tonight',
      blurb: "Emma asked again where they're moving. Jamie hasn't said Jersey City yet, partly because they haven't said it to themselves yet. Here's what was running through their head.",
      q1: "What stood out to you about the start of Jamie's renter journey?",
      q2: 'What is Jamie looking for in an apartment?',
      q2hint: "What's negotiable, and what's not?",
      reflectionIntro: 'Scan Jamie\'s journal entry again and reread their "About Jamie" bio in the upper right corner. When you\'re ready, reflect below.',
    },
    2: {
      eyebrow: 'Where Jamie starts',
      blurb: 'Emma is asleep. Jamie is at the kitchen table with the laptop, GreatSchools open in one tab, Apartment List in another. The Rent Calculator is open too. The numbers have to work.',
      reflectionIntro: 'After the homepage, the Renter Tools, and the content, sit with one last question. Emma starts kindergarten in five months.',
    },
    3: {
      eyebrow: 'Where Jamie starts',
      blurb: 'Late Tuesday. Emma is in bed. Jamie takes the quiz on the laptop. The budget step is careful. The bedroom step is not flexible. The Personality step is confusing. Jamie clicks through it and hopes the matches surface something in the right school zone.',
      reflectionIntro: 'After the quiz, the signup, and the first scroll through the matches, sit with one last question. Emma starts kindergarten in five months.',
    },
    4: {
      eyebrow: 'Where Jamie starts',
      blurb: "It's 11pm. Emma's asleep, and the six properties Jamie has been chewing on are open in six tabs. They have a school-zone spreadsheet on the side. Three listings are in the right zone. The Google reviews for one have a complaint about water pressure.",
      reflectionIntro: 'After the shortlist, the deep read, and the outside research, sit with one last question.',
    },
    5: {
      eyebrow: 'Where Jamie starts',
      blurb: 'Jamie has three serious contenders. Each message to a leasing office asks the same three things: school zone, parking, playground within walking distance. The first reply came in four hours with specific answers. The second replied with a marketing pitch. The third said "come tour." Jamie books a tour at the first.',
      reflectionIntro: 'After the first message, the tour booking, and the walkthrough through a screen, sit with one last question. Emma starts kindergarten in five months.',
    },
    6: {
      eyebrow: 'Where Jamie starts',
      blurb: "Emma's school list is on the fridge. The deposit is counted. Jamie has been reading the same two listings for three days. Tonight they pick one. The lease is due by the end of the week.",
      reflectionIntro: 'After the pick, the lease read, and the Renter Hub walk, sit with one last question.',
    },
    7: {
      eyebrow: 'Where Jamie starts',
      blurb: "Emma has been in school for four months. They have a Tuesday evening routine: the park, then dinner. Jamie reads Apartment Living articles sometimes \u2014 the ones about decorating small spaces, budgeting after a move, setting up a home for two. Some are useful. Some aren't written for a single parent.",
      reflectionIntro: 'After the stray email, the review moment, and the blog stroll, sit with one last question.',
    },
  },
};

function _wireCopyBtns(container) {
  container.querySelectorAll('.copy-btn:not([data-wired])').forEach(function(btn) {
    btn.setAttribute('data-wired', '1');
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

function refreshNotesCard(chNum) {
  var screenEl = document.getElementById('screen-ch' + chNum);
  if (!screenEl) return;
  var notesCard = screenEl.querySelector('.notes-card');
  if (!notesCard) return;
  var profile = loadProfile();

  // All notes for this persona across all chapters, sorted oldest first
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

  // Group notes by chapter number
  var groups = {};
  var groupOrder = [];
  notes.forEach(function(note) {
    var key = note.chapter || 0;
    if (!groups[key]) { groups[key] = []; groupOrder.push(key); }
    groups[key].push(note);
  });

  var html = groupOrder.map(function(key) {
    var groupNotes = groups[key];
    var chLabel = key ? 'Ch. ' + key + ' \u00b7 ' + (CH_NAMES[key] || 'Chapter ' + key) : 'General';
    var isCurrentCh = (key === chNum);
    var openAttr = isCurrentCh ? ' open' : '';
    var items = groupNotes.map(function(note) {
      var questLabel = note.label ? escHtml(note.label) : '';
      return '<li class="note-item">'
        + (questLabel ? '<div class="note-quest-label">' + questLabel + '</div>' : '')
        + '<p class="note-text">' + escHtml(note.text) + '</p>'
        + '<button class="copy-btn" data-copy="' + escHtml(note.text) + '">Copy to Slack</button>'
        + '</li>';
    }).join('');
    return '<details class="notes-chapter-group"' + openAttr + '>'
      + '<summary class="notes-group-summary">' + escHtml(chLabel) + ' <span class="notes-group-count">(' + groupNotes.length + ')</span></summary>'
      + '<ul class="notes-bullet-list">' + items + '</ul>'
      + '</details>';
  }).join('');

  list.innerHTML = html;
  _wireCopyBtns(list);
}

// ── Quest rendering ────────────────────────────────────────────────────────

function _esc(s) {
  return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function _linkify(text) {
  // Convert markdown [label](url) links to <a> tags
  return String(text || '').replace(/\[([^\]]+)\]\(([^)]+)\)/g, function(_, label, href) {
    return '<a href="' + _esc(href) + '" target="_blank" rel="noopener">' + _esc(label) + '</a>';
  });
}

function renderQuestCard(q, chNum, qi) {
  var id = q.id || (chNum + '.' + (qi + 1));
  var cls = q.optional ? 'quest optional' : 'quest';

  // Surface section
  var surfaceHtml = '';
  if (q.surfaces && q.surfaces.length) {
    var surfaceItems = q.surfaces.map(function(s) {
      return '<li>' + (s.href ? '<a href="' + _esc(s.href) + '" target="_blank" rel="noopener">' + _esc(s.text) + '</a>' : _esc(s.text)) + '</li>';
    }).join('');
    surfaceHtml = '<section class="quest-section"><div class="section-label">Surface</div><ul class="surface-list">' + surfaceItems + '</ul></section>';
  }

  // Action steps or Sit-with-it bullets
  var actionHtml = '';
  if (q.steps && q.steps.length) {
    var stepItems = q.steps.map(function(s) {
      return '<li class="action-item"><label class="step-check-wrap"><input type="checkbox" class="step-check"/><span class="checkbox-pixel"></span></label><label>' + _linkify(_esc(s)) + '</label></li>';
    }).join('');
    actionHtml = '<section class="quest-section"><div class="section-label">Action</div><ul class="action-list">' + stepItems + '</ul></section>';
  } else if (q.sitWithIt && q.sitWithIt.length) {
    var sitItems = q.sitWithIt.map(function(s) {
      return '<li class="action-item"><label>' + _esc(s) + '</label></li>';
    }).join('');
    actionHtml = '<section class="quest-section"><div class="section-label">Sit with it</div><ul class="action-list sit-list">' + sitItems + '</ul></section>';
  }

  // Scenario block (scenario quests)
  var scenarioHtml = '';
  if (q.scenario) {
    scenarioHtml = '<section class="quest-section"><div class="section-label">Scenario</div><p class="quest-scenario">' + _esc(q.scenario) + '</p></section>';
  }

  // Heads-up note
  var headsupHtml = '';
  if (q.headsup) {
    headsupHtml = '<p class="quest-headsup"><strong>Heads-up:</strong> ' + _esc(q.headsup) + '</p>';
  }

  // Reflection input
  var reflHtml = '';
  if (q.reflection) {
    reflHtml = '<div class="reflection-prompt quest-reflection"><label>' + _esc(q.reflection) + '</label><textarea class="reflection-input" placeholder="Type here..."></textarea></div>';
  }

  var titleText = _esc(q.title || '');
  var labelText = _esc(q.label || '');

  return '<article class="' + cls + '" data-quest="' + _esc(id) + '">'
    + '<header class="quest-head">'
    + '<label class="quest-check-wrap" aria-label="Mark ' + titleText + ' complete">'
    + '<input type="checkbox" class="quest-check"/><span class="checkbox-pixel"></span></label>'
    + '<div class="quest-title-area"><div class="label">' + labelText + '</div><h3>' + titleText + '</h3></div>'
    + '</header>'
    + '<div class="quest-body">'
    + surfaceHtml + scenarioHtml + headsupHtml + actionHtml + reflHtml
    + '</div></article>';
}

function renderChapterQuests(screenEl, n, persona) {
  var chData = (PERSONA_CHAPTERS[persona] || PERSONA_CHAPTERS.jordan)[n];
  if (!chData) return;

  var allQuests  = (chData.quests || []);
  var sideQuests = (chData.sideQuests || []);

  // If this persona has no quest data for this chapter, the chapter HTML
  // (from the mockup) is already correct for them — leave it untouched.
  if (allQuests.length === 0 && sideQuests.length === 0) return;

  // Find the main content column
  var main = screenEl.querySelector('.main');
  if (!main) return;

  // Remove existing quest/sidequest articles and any previous type-headers
  // (keep tonight-card, framing-card, reflection-card)
  main.querySelectorAll('.quest, .side-quest-header').forEach(function(q) { q.remove(); });

  // Find anchor before which to insert (insert before the final reflection-card)
  var reflCard = main.querySelector('.reflection-card');

  function _insertBefore(html) {
    var tmp = document.createElement('div');
    tmp.innerHTML = html;
    var el = tmp.firstElementChild;
    if (reflCard) main.insertBefore(el, reflCard);
    else main.appendChild(el);
  }

  // Core quests
  allQuests.forEach(function(q, i) { _insertBefore(renderQuestCard(q, n, i)); });

  // Side quest separator + cards
  if (sideQuests.length > 0) {
    _insertBefore(
      '<div class="quest-type-header side-quest-header">'
      + '<div class="label">Side Quest \u00b7 Optional</div>'
      + '<h2>For the curious.</h2>'
      + '<p class="sub">Optional. Skip it without consequence, or take a small detour and see what\'s out there.</p>'
      + '</div>'
    );
    sideQuests.forEach(function(q, i) { _insertBefore(renderQuestCard(q, n, allQuests.length + i)); });
  }

  // Update final reflection card content
  var fr = chData.finalReflection;
  if (fr && reflCard) {
    var h2 = reflCard.querySelector('h2');
    if (h2 && fr.heading) h2.textContent = fr.heading;
    var intro = reflCard.querySelector('.reflection-intro');
    if (intro && fr.intro) intro.textContent = fr.intro;
    // Update or create the final reflection textarea prompt
    var prompts = reflCard.querySelectorAll('.reflection-prompt');
    // The last prompt is the "final" one
    var lastPrompt = prompts[prompts.length - 1];
    if (lastPrompt && fr.prompt) {
      var lbl = lastPrompt.querySelector('label');
      if (lbl) lbl.textContent = fr.prompt;
    }
  }
}

// ── Chapter screens ───────────────────────────────────────────────────────
function syncChapterScreen(n) {
  var profile  = loadProfile();
  var screenEl = document.getElementById('screen-ch' + n);
  if (!screenEl) return;
  applyPersonaTheme(profile.persona);

  // ── Persona-change detection: re-render quests when persona switches ──
  var prevPersona = screenEl.getAttribute('data-wired-persona');
  if (n > 1 && prevPersona !== profile.persona) {
    // Replace quest block with content for the current persona
    renderChapterQuests(screenEl, n, profile.persona);
    // Force re-wiring so new checkboxes and textareas are attached
    screenEl.removeAttribute('data-ch-wired');
    screenEl.setAttribute('data-wired-persona', profile.persona);
  } else if (n === 1 && prevPersona !== profile.persona) {
    // Ch1 has no quests but final reflection card still needs persona update
    var chData1 = (PERSONA_CHAPTERS[profile.persona] || PERSONA_CHAPTERS.jordan)[1];
    if (chData1 && chData1.finalReflection) {
      var reflCard1 = screenEl.querySelector('.reflection-card');
      if (reflCard1) {
        var h2 = reflCard1.querySelector('h2');
        if (h2 && chData1.finalReflection.heading) h2.textContent = chData1.finalReflection.heading;
      }
    }
    screenEl.removeAttribute('data-ch-wired');
    screenEl.setAttribute('data-wired-persona', profile.persona);
  }

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

  // ── Must-haves / Wants criteria block ───────────────────────────────────
  var criteriaWrap = screenEl.querySelector('.hud-criteria-wrap');
  if (criteriaWrap) {
    var crit = PERSONA_CRITERIA[profile.persona] || PERSONA_CRITERIA.jordan;
    var mustItems = (crit.mustHaves || []).map(function(s) { return '<li>' + escHtml(s) + '</li>'; }).join('');
    var wantItems = (crit.wants || []).map(function(s) { return '<li>' + escHtml(s) + '</li>'; }).join('');
    criteriaWrap.innerHTML =
      '<details class="hud-criteria" open>'
      + '<summary class="hud-criteria-summary">What ' + escHtml(meta.shortName) + ' is looking for</summary>'
      + '<div class="hud-criteria-body">'
      + '<div class="criteria-col criteria-must"><div class="criteria-col-label">Must-haves</div><ul>' + mustItems + '</ul></div>'
      + '<div class="criteria-col criteria-wants"><div class="criteria-col-label">Wants</div><ul>' + wantItems + '</ul></div>'
      + '</div></details>';
  }

  // ── Persona-specific tonight-card & reflection content ──────────────────
  var pChapters = PERSONA_CHAPTERS[profile.persona] || PERSONA_CHAPTERS.jordan;
  var chData = pChapters[n];
  var poss = meta.shortName + (meta.shortName.slice(-1) === 's' ? "'" : "'s"); // possessive

  if (chData) {
    // Tonight eyebrow
    var tonightEyebrow = screenEl.querySelector('.tonight-eyebrow');
    if (tonightEyebrow && chData.eyebrow) tonightEyebrow.textContent = '\u25b8 ' + chData.eyebrow;

    // Tonight blurb
    var tonightBlurb = screenEl.querySelector('.tonight-blurb');
    if (tonightBlurb && chData.blurb) tonightBlurb.textContent = chData.blurb;

    // Reflection intro
    var reflIntroEl = screenEl.querySelector('.reflection-intro');
    if (reflIntroEl && chData.reflectionIntro) reflIntroEl.textContent = chData.reflectionIntro;

    // Per-chapter reflection questions (ch1 has persona-specific labels)
    if (chData.q1 || chData.q2) {
      var prompts = screenEl.querySelectorAll('.reflection-prompt');
      if (prompts[0] && chData.q1) {
        var lbl1 = prompts[0].querySelector('label');
        if (lbl1) lbl1.textContent = chData.q1;
      }
      if (prompts[1] && chData.q2) {
        var lbl2 = prompts[1].querySelector('label');
        if (lbl2) lbl2.textContent = chData.q2;
        var hint2 = prompts[1].querySelector('.prompt-hint');
        if (hint2 && chData.q2hint) hint2.textContent = chData.q2hint;
      }
    }
  }

  // ── Persona name substitution in static chapter copy ───────────────────
  // Covers all four source-mockup persona names so the correct name
  // appears regardless of which mockup a chapter was stitched from.
  var _PERSONA_NAMES = ['Jordan', 'Alex', 'Taylor', 'Jamie'];
  function _swapName(html) {
    _PERSONA_NAMES.forEach(function(n) {
      var re_poss = new RegExp('\\b' + n + "'s\\b", 'g');
      var re_bare = new RegExp('\\b' + n + '\\b', 'g');
      html = html.replace(re_poss, poss).replace(re_bare, meta.shortName);
    });
    return html;
  }

  // hero lede
  var heroLede = screenEl.querySelector('.lede');
  if (heroLede) heroLede.innerHTML = _swapName(heroLede.innerHTML);

  // framing list (how to walk this chapter)
  screenEl.querySelectorAll('.framing-list li').forEach(function(li) {
    li.innerHTML = _swapName(li.innerHTML);
  });

  // journal meta ("Jordan's journal · Tuesday, late")
  var journalMeta = screenEl.querySelector('.journal-meta');
  if (journalMeta) journalMeta.innerHTML = _swapName(journalMeta.innerHTML);

  // ── Ch1 journal entry: swap to the active persona's canonical text ───────
  if (n === 1) {
    var entryEl = screenEl.querySelector('.tonight-card .journal .entry');
    var ch1Data = (PERSONA_CHAPTERS[profile.persona] || PERSONA_CHAPTERS.jordan)[1];
    if (entryEl && ch1Data && ch1Data.journalParas) {
      entryEl.innerHTML = ch1Data.journalParas.map(function(p) {
        return '<p>' + p.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</p>';
      }).join('');
    }
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

# ── Inject dynamic PERSONA_CHAPTERS (parsed from memory/content-*.md) ─────
_pc_raw = build_persona_chapters()
# json.dumps uses double-quotes which is valid JS; keys like 1,2 come out as "1","2" — fix to bare ints
_pc_json = json.dumps(_pc_raw, ensure_ascii=False, indent=2)
# Strip the old hardcoded PERSONA_CHAPTERS block (if still present) and replace
JS = re.sub(
    r'// Persona-specific tonight-cards.*?^};',
    '__PERSONA_CHAPTERS__',
    JS,
    flags=re.DOTALL | re.MULTILINE,
)
_pc_js = 'var PERSONA_CHAPTERS = ' + _pc_json + ';'
# JSON uses "1","2" for numeric keys — convert to bare int property names for clarity
_pc_js = re.sub(r'"(\d+)"\s*:', r'\1:', _pc_js)
JS = JS.replace('__PERSONA_CHAPTERS__', _pc_js)

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
