/* The Renter's Journey · shared demo glue
 *
 * One small script that gets included on every mockup. It does four things:
 *   1. Stores the player's persona + avatar in localStorage so the choice
 *      survives the page navigation that strings the mockups together.
 *   2. Paints the chosen avatar into every HUD it finds on the page,
 *      replacing the hard-coded sprite that ships with each mockup.
 *   3. Wires the persona-selection "Embark with X" buttons to the avatar
 *      builder, and the builder's "Begin the Journey" button to the map.
 *   4. Unlocks the journey map cards and rewires each chapter's "Walk on"
 *      so the click-through demo just flows.
 *
 * If the mockup is opened in isolation (no profile saved yet), defaults
 * kick in so the page still looks right.
 */
(function () {
  'use strict';

  // ---------------------------------------------------------------------
  // Profile storage
  // ---------------------------------------------------------------------
  var STORAGE_KEY = 'rj.profile.v1';

  var DEFAULTS = {
    persona: 'jordan',
    skin:    '#FCE0C2',
    hair:    '#3B2A1F',
    hairStyle: 'short',
    shirt:   '#6105C4',
    pants:   '#46137B',
    shoes:   '#0A0510',
    lip:     '#E07590',
    // Highest chapter number the player has reached. 1..7 corresponds to
    // the seven journey-map cards; cards above this number stay locked.
    unlockedChapter: 1
  };

  // Lip color paired with each skin swatch (lifted from the avatar mockup).
  var SKIN_TO_LIP = {
    '#FCE0C2': '#E07590',
    '#E8C5A4': '#C8576B',
    '#D4A57A': '#A8425A',
    '#A87A52': '#8B3548',
    '#7A5236': '#8B3548',
    '#4A3220': '#B85968'
  };

  function loadProfile() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return Object.assign({}, DEFAULTS);
      var parsed = JSON.parse(raw);
      return Object.assign({}, DEFAULTS, parsed);
    } catch (e) {
      return Object.assign({}, DEFAULTS);
    }
  }

  function saveProfile(patch) {
    var next = Object.assign(loadProfile(), patch || {});
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)); } catch (e) {}
    return next;
  }

  // ---------------------------------------------------------------------
  // Persona metadata (used to label the avatar creator and chapter HUDs
  // when the per-page hardcoded names don't already match)
  // ---------------------------------------------------------------------
  var PERSONAS = {
    alex: {
      key: 'alex',
      fullName: 'Alex the Ambitious',
      shortName: 'Alex',
      badge: 'Level Upper'
    },
    jordan: {
      key: 'jordan',
      fullName: 'Jordan the Rising Star',
      shortName: 'Jordan',
      badge: 'Achiever'
    },
    taylor: {
      key: 'taylor',
      fullName: 'Taylor & Riley',
      shortName: 'Taylor & Riley',
      badge: 'City Hopper'
    },
    jamie: {
      key: 'jamie',
      fullName: 'Jamie the Resilient Parent',
      shortName: 'Jamie',
      badge: 'Pathfinder'
    }
  };

  // ---------------------------------------------------------------------
  // Avatar sprite — exact same pixel art as the avatar-creation preview,
  // just templated so it can be rendered into any HUD.
  // ---------------------------------------------------------------------
  function spriteSVG(profile) {
    function hairGroup(key, content) {
      var visible = (profile.hairStyle === key);
      return '<g class="hair-style hair-' + key + '" data-style="' + key + '"' +
        (visible ? '' : ' style="display:none"') + '>' + content + '</g>';
    }

    var hairShort =
      '<rect x="9" y="3" width="14" height="2" fill="var(--avatar-hair)"/>' +
      '<rect x="8" y="5" width="16" height="3" fill="var(--avatar-hair)"/>' +
      '<rect x="8" y="8" width="2" height="3" fill="var(--avatar-hair)"/>' +
      '<rect x="22" y="8" width="2" height="3" fill="var(--avatar-hair)"/>' +
      '<rect x="11" y="6" width="7" height="1" fill="var(--avatar-hair)" opacity="0.55"/>';

    var hairLong =
      '<rect x="9" y="3" width="14" height="2" fill="var(--avatar-hair)"/>' +
      '<rect x="8" y="5" width="16" height="3" fill="var(--avatar-hair)"/>' +
      '<rect x="9" y="8" width="14" height="2" fill="var(--avatar-hair)"/>' +
      '<rect x="8" y="8" width="2" height="9" fill="var(--avatar-hair)"/>' +
      '<rect x="22" y="8" width="2" height="9" fill="var(--avatar-hair)"/>' +
      '<rect x="9" y="16" width="1" height="2" fill="var(--avatar-hair)"/>' +
      '<rect x="22" y="16" width="1" height="2" fill="var(--avatar-hair)"/>';

    var hairBun =
      '<rect x="14" y="0" width="4" height="3" fill="var(--avatar-hair)"/>' +
      '<rect x="13" y="1" width="6" height="2" fill="var(--avatar-hair)"/>' +
      '<rect x="9" y="3" width="14" height="2" fill="var(--avatar-hair)"/>' +
      '<rect x="8" y="5" width="16" height="3" fill="var(--avatar-hair)"/>' +
      '<rect x="8" y="8" width="2" height="3" fill="var(--avatar-hair)"/>' +
      '<rect x="22" y="8" width="2" height="3" fill="var(--avatar-hair)"/>' +
      '<rect x="11" y="6" width="10" height="1" fill="var(--avatar-hair)" opacity="0.6"/>';

    var hairSpaceBuns =
      '<rect x="9" y="0" width="3" height="3" fill="var(--avatar-hair)"/>' +
      '<rect x="8" y="1" width="5" height="2" fill="var(--avatar-hair)"/>' +
      '<rect x="20" y="0" width="3" height="3" fill="var(--avatar-hair)"/>' +
      '<rect x="19" y="1" width="5" height="2" fill="var(--avatar-hair)"/>' +
      '<rect x="9" y="3" width="14" height="2" fill="var(--avatar-hair)"/>' +
      '<rect x="8" y="5" width="16" height="3" fill="var(--avatar-hair)"/>' +
      '<rect x="8" y="8" width="2" height="3" fill="var(--avatar-hair)"/>' +
      '<rect x="22" y="8" width="2" height="3" fill="var(--avatar-hair)"/>' +
      '<rect x="11" y="6" width="3" height="1" fill="var(--avatar-hair)" opacity="0.6"/>' +
      '<rect x="18" y="6" width="3" height="1" fill="var(--avatar-hair)" opacity="0.6"/>';

    var hairBuzz =
      '<rect x="10" y="5" width="12" height="2" fill="var(--avatar-hair)"/>' +
      '<rect x="9" y="6" width="14" height="2" fill="var(--avatar-hair)"/>' +
      '<rect x="9" y="8" width="1" height="2" fill="var(--avatar-hair)" opacity="0.5"/>' +
      '<rect x="22" y="8" width="1" height="2" fill="var(--avatar-hair)" opacity="0.5"/>';

    var hairMohawk =
      '<rect x="15" y="0" width="2" height="2" fill="var(--avatar-hair)"/>' +
      '<rect x="14" y="2" width="4" height="2" fill="var(--avatar-hair)"/>' +
      '<rect x="13" y="4" width="6" height="2" fill="var(--avatar-hair)"/>' +
      '<rect x="12" y="6" width="8" height="3" fill="var(--avatar-hair)"/>' +
      '<rect x="10" y="6" width="2" height="2" fill="var(--avatar-hair)" opacity="0.35"/>' +
      '<rect x="20" y="6" width="2" height="2" fill="var(--avatar-hair)" opacity="0.35"/>' +
      '<rect x="9" y="7" width="1" height="2" fill="var(--avatar-hair)" opacity="0.3"/>' +
      '<rect x="22" y="7" width="1" height="2" fill="var(--avatar-hair)" opacity="0.3"/>';

    var hairLongFlow =
      '<rect x="9" y="3" width="14" height="2" fill="var(--avatar-hair)"/>' +
      '<rect x="8" y="5" width="16" height="3" fill="var(--avatar-hair)"/>' +
      '<rect x="9" y="8" width="14" height="2" fill="var(--avatar-hair)"/>' +
      '<rect x="8" y="8" width="2" height="22" fill="var(--avatar-hair)"/>' +
      '<rect x="22" y="8" width="2" height="22" fill="var(--avatar-hair)"/>' +
      '<rect x="7" y="20" width="2" height="11" fill="var(--avatar-hair)"/>' +
      '<rect x="23" y="20" width="2" height="11" fill="var(--avatar-hair)"/>' +
      '<rect x="10" y="6" width="3" height="1" fill="var(--avatar-hair)" opacity="0.6"/>' +
      '<rect x="19" y="6" width="3" height="1" fill="var(--avatar-hair)" opacity="0.6"/>';

    var hairLongWavy =
      '<rect x="9" y="3" width="14" height="2" fill="var(--avatar-hair)"/>' +
      '<rect x="8" y="5" width="16" height="2" fill="var(--avatar-hair)"/>' +
      '<rect x="15" y="5" width="2" height="2" fill="var(--avatar-skin)"/>' +
      '<rect x="8" y="7" width="3" height="2" fill="var(--avatar-hair)"/>' +
      '<rect x="21" y="7" width="3" height="2" fill="var(--avatar-hair)"/>' +
      '<rect x="8" y="9" width="2" height="22" fill="var(--avatar-hair)"/>' +
      '<rect x="22" y="9" width="2" height="22" fill="var(--avatar-hair)"/>' +
      '<rect x="7" y="22" width="1" height="3" fill="var(--avatar-hair)"/>' +
      '<rect x="24" y="22" width="1" height="3" fill="var(--avatar-hair)"/>' +
      '<rect x="7" y="20" width="2" height="11" fill="var(--avatar-hair)"/>' +
      '<rect x="23" y="20" width="2" height="11" fill="var(--avatar-hair)"/>' +
      '<rect x="6" y="27" width="1" height="3" fill="var(--avatar-hair)"/>' +
      '<rect x="25" y="27" width="1" height="3" fill="var(--avatar-hair)"/>' +
      '<rect x="10" y="6" width="3" height="1" fill="var(--avatar-hair)" opacity="0.6"/>' +
      '<rect x="19" y="6" width="3" height="1" fill="var(--avatar-hair)" opacity="0.6"/>';

    var bodyAndFace =
      // Head
      '<rect x="10" y="6" width="12" height="11" fill="var(--avatar-skin)"/>' +
      '<rect x="9"  y="7" width="1"  height="9"  fill="var(--avatar-skin)"/>' +
      '<rect x="22" y="7" width="1"  height="9"  fill="var(--avatar-skin)"/>' +
      // Eyes
      '<rect x="12" y="10" width="1" height="3" fill="#1A0E2E"/>' +
      '<rect x="19" y="10" width="1" height="3" fill="#1A0E2E"/>' +
      // Mouth
      '<rect x="14" y="14" width="1" height="1" fill="var(--avatar-lip)"/>' +
      '<rect x="17" y="14" width="1" height="1" fill="var(--avatar-lip)"/>' +
      '<rect x="15" y="15" width="2" height="1" fill="var(--avatar-lip)"/>' +
      // Neck
      '<rect x="14" y="17" width="4" height="2" fill="var(--avatar-skin)"/>' +
      // Shirt
      '<rect x="8"  y="19" width="16" height="9" fill="var(--avatar-shirt)"/>' +
      '<rect x="6"  y="19" width="2"  height="9" fill="var(--avatar-shirt)"/>' +
      '<rect x="24" y="19" width="2"  height="9" fill="var(--avatar-shirt)"/>' +
      // Hands
      '<rect x="6"  y="28" width="2"  height="2" fill="var(--avatar-skin)"/>' +
      '<rect x="24" y="28" width="2"  height="2" fill="var(--avatar-skin)"/>' +
      // Pants
      '<rect x="8"  y="28" width="16" height="11" fill="var(--avatar-pants)"/>' +
      '<rect x="15" y="32" width="2"  height="7"  fill="var(--avatar-pants)"/>' +
      '<rect x="15" y="34" width="2"  height="5"  fill="rgba(0,0,0,0.15)"/>' +
      // Shoes
      '<rect x="8"  y="39" width="7"  height="3" fill="var(--avatar-shoes)"/>' +
      '<rect x="17" y="39" width="7"  height="3" fill="var(--avatar-shoes)"/>';

    // Hair drawn BEFORE the body for short/structured styles, AFTER the body
    // for long styles that need to drape over shoulders/arms.
    var preHair =
      hairGroup('short', hairShort) +
      hairGroup('long', hairLong) +
      hairGroup('bun', hairBun) +
      hairGroup('space-buns', hairSpaceBuns) +
      hairGroup('buzz', hairBuzz) +
      hairGroup('mohawk', hairMohawk);

    var postHair =
      hairGroup('long-flow', hairLongFlow) +
      hairGroup('long-wavy', hairLongWavy);

    return '<svg viewBox="0 0 32 48" xmlns="http://www.w3.org/2000/svg" ' +
           'shape-rendering="crispEdges">' +
           preHair + bodyAndFace + postHair +
           '</svg>';
  }

  function applyAvatarVars(profile) {
    var root = document.documentElement.style;
    root.setProperty('--avatar-skin',  profile.skin);
    root.setProperty('--avatar-hair',  profile.hair);
    root.setProperty('--avatar-shirt', profile.shirt);
    root.setProperty('--avatar-pants', profile.pants);
    root.setProperty('--avatar-shoes', profile.shoes);
    root.setProperty('--avatar-lip',   profile.lip || SKIN_TO_LIP[profile.skin] || '#C8576B');
  }

  // Replace every .hud-card .avatar-frame on the page with the player sprite.
  function paintHUDs(profile) {
    var frames = document.querySelectorAll('.hud-card .avatar-frame');
    frames.forEach(function (frame) {
      frame.innerHTML = spriteSVG(profile);
    });
  }

  // ---------------------------------------------------------------------
  // Page initialisers — each one runs only if the page looks like it.
  // ---------------------------------------------------------------------

  // Persona selection: wire each "Embark with X" button to save the persona
  // choice and navigate to the avatar builder.
  function initPersonaSelection() {
    var cards = document.querySelectorAll('.card .btn-embark');
    if (!cards.length) return;
    cards.forEach(function (btn) {
      var card = btn.closest('.card');
      if (!card) return;
      // Determine persona from the card's class list (alex/jordan/taylor-riley/jamie)
      var personaKey = 'jordan';
      if (card.classList.contains('alex')) personaKey = 'alex';
      else if (card.classList.contains('jordan')) personaKey = 'jordan';
      else if (card.classList.contains('taylor-riley') || card.classList.contains('taylor')) personaKey = 'taylor';
      else if (card.classList.contains('jamie')) personaKey = 'jamie';

      btn.addEventListener('click', function (e) {
        e.preventDefault();
        // A new persona means a fresh playthrough: reset progress to Ch 1.
        saveProfile({ persona: personaKey, unlockedChapter: 1 });
        window.location.href = 'avatar-creation-mockup.html';
      });
    });
  }

  // Avatar creation: reflect the chosen persona in the header, persist
  // every swatch/hair pick to localStorage, and send "Begin the Journey"
  // onward to the map.
  function initAvatarCreation() {
    var beginBtn = document.querySelector('.btn-begin');
    if (!beginBtn) return; // not this page

    var profile = loadProfile();
    var persona = PERSONAS[profile.persona] || PERSONAS.jordan;

    // 1. Header: "Now Playing As" reflects chosen persona
    var nameEl = document.querySelector('.persona-context .name');
    if (nameEl) nameEl.textContent = persona.fullName;

    // 1b. "Change renter" link goes back to persona selection
    var changeLink = document.querySelector('.persona-context .change');
    if (changeLink) {
      changeLink.style.cursor = 'pointer';
      changeLink.addEventListener('click', function () {
        window.location.href = 'persona-selection-mockup.html';
      });
    }

    // 2. Pre-select swatches/hair to match the saved profile (so reopening
    //    the page shows the same avatar). The mockup's own script will then
    //    keep things in sync as the user clicks.
    function preselect(selector, value, attr) {
      attr = attr || 'data-color';
      var group = document.querySelector(selector);
      if (!group) return;
      var match = group.querySelector('[' + attr + '="' + value + '"]');
      if (!match) return;
      group.querySelectorAll('.swatch, .thumb').forEach(function (el) {
        el.classList.remove('selected');
      });
      match.classList.add('selected');
    }
    preselect('.swatches[data-target="skin"]',  profile.skin);
    preselect('.swatches[data-target="hair"]',  profile.hair);
    preselect('.swatches[data-target="shirt"]', profile.shirt);
    preselect('.swatches[data-target="pants"]', profile.pants);
    preselect('.swatches[data-target="shoes"]', profile.shoes);
    preselect('.thumbs[data-target="hair-style"]', profile.hairStyle, 'data-style');

    // Apply the saved colours to the live preview so the avatar reflects
    // what we have on file before the user touches anything.
    applyAvatarVars(profile);

    // Show only the saved hair style
    document.querySelectorAll('.avatar .hair-style').forEach(function (g) {
      g.style.display = (g.dataset.style === profile.hairStyle) ? '' : 'none';
    });

    // 3. Persist every click. The mockup's own listeners update the
    //    preview; ours just records the selection.
    document.querySelectorAll('.swatches').forEach(function (group) {
      var target = group.dataset.target; // skin | hair | shirt | pants | shoes
      group.querySelectorAll('.swatch').forEach(function (sw) {
        sw.addEventListener('click', function () {
          var patch = {};
          patch[target] = sw.dataset.color;
          if (target === 'skin' && SKIN_TO_LIP[sw.dataset.color]) {
            patch.lip = SKIN_TO_LIP[sw.dataset.color];
          }
          saveProfile(patch);
        });
      });
    });
    document.querySelectorAll('.thumbs[data-target="hair-style"] .thumb').forEach(function (thumb) {
      thumb.addEventListener('click', function () {
        saveProfile({ hairStyle: thumb.dataset.style });
      });
    });

    // 4. Begin button → journey map. The mockup's own script also binds an
    //    alert listener; capture-phase + stopImmediatePropagation lets ours win.
    beginBtn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopImmediatePropagation();
      window.location.href = 'journey-map-mockup.html';
    }, true);
  }

  // Journey map: render each card based on how far the player has walked.
  // Chapters at or below unlockedChapter are reachable; the rest stay locked.
  var CHAPTER_FILES = [
    'chapter-1-long-night-jordan-mockup.html',
    'chapter-2-first-light-alex-mockup.html',
    'chapter-3-search-begins-taylor-mockup.html',
    'chapter-4-crossroads-jamie-mockup.html',
    'chapter-5-first-hello-jordan-mockup.html',
    'chapter-6-the-key-jamie-mockup.html',
    'chapter-7-welcome-mat-alex-mockup.html'
  ];

  // Per-chapter "still locked" hints — keeps the original mockup's voice.
  var LOCK_HINTS = [
    null, // chapter 1 is never locked
    'Locked · finish Chapter 1 to unlock',
    'Locked · light the lantern in Chapter 2 first',
    'Locked · reach this clearing later',
    'Locked · keep walking',
    "Locked · the door's not yours yet",
    "Locked · you'll find this when you're settled in"
  ];

  function makeCardClickable(card, target) {
    if (card.tagName.toLowerCase() === 'a') {
      card.setAttribute('href', target);
    } else {
      card.setAttribute('role', 'link');
      if (!card._rjClickBound) {
        card.addEventListener('click', function () {
          window.location.href = target;
        });
        card._rjClickBound = true;
      }
    }
    card.style.cursor = 'pointer';
    card.removeAttribute('aria-disabled');
  }

  function lockCard(card, hint) {
    card.classList.add('locked');
    card.setAttribute('aria-disabled', 'true');
    card.style.cursor = 'not-allowed';
    if (card.tagName.toLowerCase() === 'a') {
      // Stop the anchor from navigating while locked.
      card.removeAttribute('href');
    }
    // Make sure the small lock pixel-icon is present in front of the chapter number.
    var chNum = card.querySelector('.ch-num');
    if (chNum && !chNum.querySelector('.lock-icon')) {
      var icon = document.createElement('span');
      icon.className = 'lock-icon';
      chNum.insertBefore(icon, chNum.firstChild);
    }
    var pill = card.querySelector('.status-pill');
    if (pill) pill.textContent = 'Still down the path';
    var open = card.querySelector('.open');
    if (open && hint) open.textContent = hint;
  }

  function unlockCard(card) {
    card.classList.remove('locked');
    var lockIcon = card.querySelector('.lock-icon');
    if (lockIcon) lockIcon.remove();
  }

  function initJourneyMap() {
    var cards = document.querySelectorAll('.chapter-card');
    if (!cards.length) return;

    var profile = loadProfile();
    var unlocked = Math.max(1, Math.min(7, profile.unlockedChapter || 1));

    cards.forEach(function (card, idx) {
      var chapterNum = idx + 1;
      var target = CHAPTER_FILES[idx];
      if (!target) return;

      // Reset state classes so we can re-render cleanly on each visit.
      card.classList.remove('current', 'complete');

      var pill = card.querySelector('.status-pill');
      var open = card.querySelector('.open');

      if (chapterNum < unlocked) {
        // Completed: green pill, "Revisit" affordance, still clickable.
        unlockCard(card);
        card.classList.add('complete');
        if (pill) pill.textContent = 'Walked';
        if (open) open.textContent = 'Revisit';
        makeCardClickable(card, target);
      } else if (chapterNum === unlocked) {
        // Current chapter — orange accent + blinking dot is already in CSS.
        unlockCard(card);
        card.classList.add('current');
        if (pill) pill.textContent = "You're here";
        if (open) open.textContent = 'Step in';
        makeCardClickable(card, target);
      } else {
        // Still locked.
        lockCard(card, LOCK_HINTS[idx]);
      }
    });
  }

  // Chapter pages: figure out the next chapter and rewire the "Walk on" link.
  // Also drop the alert() that the per-page script slips in.
  function initChapterNav() {
    var continueBtn = document.getElementById('continueBtn');
    if (!continueBtn) return;

    var here = location.pathname.split('/').pop();
    var nextMap = {
      'chapter-1-long-night-jordan-mockup.html':   'chapter-2-first-light-alex-mockup.html',
      'chapter-2-first-light-alex-mockup.html':    'chapter-3-search-begins-taylor-mockup.html',
      'chapter-3-search-begins-taylor-mockup.html':'chapter-4-crossroads-jamie-mockup.html',
      'chapter-4-crossroads-jamie-mockup.html':    'chapter-5-first-hello-jordan-mockup.html',
      'chapter-5-first-hello-jordan-mockup.html':  'chapter-6-the-key-jamie-mockup.html',
      'chapter-6-the-key-jamie-mockup.html':       'chapter-7-welcome-mat-alex-mockup.html',
      'chapter-7-welcome-mat-alex-mockup.html':    'ultimate-quest-mockup.html',
      'ultimate-quest-mockup.html':                'persona-selection-mockup.html'
    };

    // Each filename maps to a chapter number (1..7). Ultimate quest = 7 done.
    var chapterNumOf = {
      'chapter-1-long-night-jordan-mockup.html':   1,
      'chapter-2-first-light-alex-mockup.html':    2,
      'chapter-3-search-begins-taylor-mockup.html':3,
      'chapter-4-crossroads-jamie-mockup.html':    4,
      'chapter-5-first-hello-jordan-mockup.html':  5,
      'chapter-6-the-key-jamie-mockup.html':       6,
      'chapter-7-welcome-mat-alex-mockup.html':    7
    };

    var next = nextMap[here];
    if (next) continueBtn.setAttribute('href', next);

    // Visiting a chapter unlocks it — so direct-linking from the index, or
    // jumping ahead from a previous "Walk on" click, both keep the journey
    // map in sync with where the player actually is.
    var currentChapter = chapterNumOf[here];
    if (currentChapter) {
      var p = loadProfile();
      if ((p.unlockedChapter || 1) < currentChapter) {
        saveProfile({ unlockedChapter: currentChapter });
      }
    }

    // The per-page script attaches a click handler that calls
    // e.preventDefault() and alerts. We capture the click first and
    // navigate ourselves once the button is enabled.
    continueBtn.addEventListener('click', function (e) {
      if (continueBtn.classList.contains('disabled')) return; // let per-page handler scroll to reflection
      e.preventDefault();
      e.stopImmediatePropagation();
      // Bump the unlock counter so the next chapter is reachable from the map.
      var nextChapter = chapterNumOf[next];
      if (nextChapter) {
        var pNow = loadProfile();
        if ((pNow.unlockedChapter || 1) < nextChapter) {
          saveProfile({ unlockedChapter: nextChapter });
        }
      }
      if (next) window.location.href = next;
    }, true);

    // Also make the "← Back to the Map" link always reachable
    var backLink = document.querySelector('.nav-side .nav-link[href*="journey-map"]');
    if (backLink) backLink.setAttribute('href', 'journey-map-mockup.html');
  }

  // ---------------------------------------------------------------------
  // Must-haves / nice-to-haves per persona — drawn from memory/personas.md
  // so this stays the canonical, persona-grounded version of the renter's
  // criteria. Stays fixed across chapters (per Melissa's call).
  // ---------------------------------------------------------------------
  var CRITERIA = {
    alex: {
      eyebrow: "Alex's brief",
      lede: 'Senior engineer, three years in a studio, lease non-renewal in hand. Hunts with a spreadsheet.',
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
      eyebrow: "Jordan's brief",
      lede: 'New job in Seattle, eighteen days to land. Max the golden retriever is along for the ride.',
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
      eyebrow: "Taylor & Riley's brief",
      lede: 'Three years in Chicago, leaving for Austin. Vibe-driven, mutual veto, no rush.',
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
      eyebrow: "Jamie's brief",
      lede: 'Single parent in suburban Philly. Emma starts kindergarten in five months. Plan is Jersey City.',
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

  // Which persona each chapter stars (so the briefing card matches the
  // chapter's narrative renter, not the player's selected persona).
  var CHAPTER_PERSONA = {
    'chapter-1-long-night-jordan-mockup.html':    'jordan',
    'chapter-2-first-light-alex-mockup.html':     'alex',
    'chapter-3-search-begins-taylor-mockup.html': 'taylor',
    'chapter-4-crossroads-jamie-mockup.html':     'jamie',
    'chapter-5-first-hello-jordan-mockup.html':   'jordan',
    'chapter-6-the-key-jamie-mockup.html':        'jamie',
    'chapter-7-welcome-mat-alex-mockup.html':     'alex'
  };

  function ensureBriefingStyles() {
    if (document.getElementById('rj-briefing-styles')) return;
    var style = document.createElement('style');
    style.id = 'rj-briefing-styles';
    style.textContent = [
      '.briefing-card {',
      '  background: var(--paper, #FFFCF0);',
      '  border: 3px solid var(--ink, #2D1B0E);',
      '  box-shadow: 6px 6px 0 var(--ink-soft, #5D4037);',
      '  padding: 24px 28px 26px;',
      '  margin: 0 0 24px;',
      '  position: relative;',
      '  overflow: hidden;',
      '}',
      '.briefing-card::before {',
      '  content: ""; display: block; height: 6px;',
      '  background: var(--persona-color, var(--indigo, #6105C4));',
      '  margin: -24px -28px 16px;',
      '}',
      '.briefing-eyebrow {',
      '  font-family: "VT323", monospace;',
      '  font-size: 16px;',
      '  color: var(--persona-color, var(--indigo, #6105C4));',
      '  letter-spacing: 3px;',
      '  text-transform: uppercase;',
      '  margin-bottom: 6px;',
      '  display: flex; align-items: center; gap: 10px;',
      '}',
      '.briefing-eyebrow .pixel-dot {',
      '  display: inline-block; width: 8px; height: 8px;',
      '  background: var(--persona-color, var(--indigo, #6105C4));',
      '}',
      '.briefing-card h3 {',
      '  font-family: "Pixelify Sans", monospace;',
      '  font-size: 26px;',
      '  color: var(--ink, #2D1B0E);',
      '  margin: 0 0 6px;',
      '  letter-spacing: -0.3px;',
      '}',
      '.briefing-lede {',
      '  font-family: "Source Serif 4", Georgia, serif;',
      '  font-style: italic;',
      '  font-size: 15.5px;',
      '  color: var(--ink-soft, #5D4037);',
      '  margin: 0 0 20px;',
      '  max-width: 64ch;',
      '}',
      '.briefing-grid {',
      '  display: grid;',
      '  grid-template-columns: 1fr 1fr;',
      '  gap: 22px;',
      '}',
      '@media (max-width: 720px) {',
      '  .briefing-grid { grid-template-columns: 1fr; gap: 16px; }',
      '}',
      '.briefing-col {',
      '  background: rgba(245, 242, 237, 0.55);',
      '  border: 2px solid var(--ink, #2D1B0E);',
      '  padding: 14px 16px 16px;',
      '  position: relative;',
      '}',
      '.briefing-col .col-label {',
      '  font-family: "VT323", monospace;',
      '  font-size: 14px;',
      '  letter-spacing: 2.5px;',
      '  text-transform: uppercase;',
      '  color: var(--ink, #2D1B0E);',
      '  margin-bottom: 8px;',
      '  display: flex; align-items: center; gap: 8px;',
      '}',
      '.briefing-col .col-label::before {',
      '  content: ""; display: inline-block; width: 10px; height: 10px;',
      '  background: var(--col-accent, var(--persona-color, #6105C4));',
      '}',
      '.briefing-col.musts { --col-accent: var(--red, #FF0029); }',
      '.briefing-col.wants { --col-accent: var(--orange, #FF974D); }',
      '.briefing-col ul { list-style: none; margin: 0; padding: 0; }',
      '.briefing-col li {',
      '  font-family: "Source Serif 4", Georgia, serif;',
      '  font-size: 15px;',
      '  line-height: 1.45;',
      '  color: var(--ink, #2D1B0E);',
      '  padding: 4px 0 4px 18px;',
      '  position: relative;',
      '}',
      '.briefing-col li + li { border-top: 1px dashed rgba(45,27,14,0.18); }',
      '.briefing-col li::before {',
      '  content: ""; position: absolute;',
      '  left: 0; top: 11px;',
      '  width: 6px; height: 6px;',
      '  background: var(--col-accent, var(--persona-color, #6105C4));',
      '}'
    ].join('\n');
    document.head.appendChild(style);
  }

  function buildBriefingCard(criteria) {
    function listItems(items) {
      return items.map(function (it) { return '<li>' + it + '</li>'; }).join('');
    }
    return '' +
      '<article class="briefing-card" id="briefingCard">' +
      '  <div class="briefing-eyebrow"><span class="pixel-dot"></span>' + criteria.eyebrow + '<span class="pixel-dot"></span></div>' +
      '  <h3>What they\'re looking for</h3>' +
      '  <p class="briefing-lede">' + criteria.lede + '</p>' +
      '  <div class="briefing-grid">' +
      '    <div class="briefing-col musts">' +
      '      <div class="col-label">Must-haves</div>' +
      '      <ul>' + listItems(criteria.mustHaves) + '</ul>' +
      '    </div>' +
      '    <div class="briefing-col wants">' +
      '      <div class="col-label">Wants</div>' +
      '      <ul>' + listItems(criteria.wants) + '</ul>' +
      '    </div>' +
      '  </div>' +
      '</article>';
  }

  function initBriefingCard() {
    var here = location.pathname.split('/').pop();
    var personaKey = CHAPTER_PERSONA[here];
    if (!personaKey) return;
    var criteria = CRITERIA[personaKey];
    if (!criteria) return;

    // Don't inject twice if the page is hot-reloaded
    if (document.getElementById('briefingCard')) return;

    ensureBriefingStyles();

    var main = document.querySelector('main.stage > .main') || document.querySelector('main .main');
    if (!main) return;

    // Prefer to land just above the Core Quests header. Fall back to the
    // reflection card (chapter 1 has no quests block, just a reflection).
    var anchor = main.querySelector('.quests-header') ||
                 main.querySelector('.reflection-card');
    if (!anchor) return;

    var wrapper = document.createElement('div');
    wrapper.innerHTML = buildBriefingCard(criteria);
    var card = wrapper.firstElementChild;
    anchor.parentNode.insertBefore(card, anchor);
  }

  // ---------------------------------------------------------------------
  // Field Notes — storage, injection, sidebar rendering, export
  // ---------------------------------------------------------------------
  var NOTES_KEY = 'rj.notes.v1';

  var CHAPTER_TITLES = {
    'chapter-1-long-night-jordan-mockup.html':    'Ch 1 · The Long Night',
    'chapter-2-first-light-alex-mockup.html':     'Ch 2 · First Light',
    'chapter-3-search-begins-taylor-mockup.html': 'Ch 3 · The Search Begins',
    'chapter-4-crossroads-jamie-mockup.html':     'Ch 4 · The Crossroads',
    'chapter-5-first-hello-jordan-mockup.html':   'Ch 5 · The First Hello',
    'chapter-6-the-key-jamie-mockup.html':        'Ch 6 · The Key',
    'chapter-7-welcome-mat-alex-mockup.html':     'Ch 7 · The Welcome Mat'
  };

  var CHAPTER_NUMS = {
    'chapter-1-long-night-jordan-mockup.html':    1,
    'chapter-2-first-light-alex-mockup.html':     2,
    'chapter-3-search-begins-taylor-mockup.html': 3,
    'chapter-4-crossroads-jamie-mockup.html':     4,
    'chapter-5-first-hello-jordan-mockup.html':   5,
    'chapter-6-the-key-jamie-mockup.html':        6,
    'chapter-7-welcome-mat-alex-mockup.html':     7
  };

  function loadNotes() {
    try {
      var raw = localStorage.getItem(NOTES_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (e) { return {}; }
  }

  function saveNote(note) {
    var all = loadNotes();
    var persona = note.persona || 'jordan';
    if (!all[persona]) all[persona] = [];
    all[persona].push(note);
    try { localStorage.setItem(NOTES_KEY, JSON.stringify(all)); } catch (e) {}
  }

  function getPersonaNotes() {
    var profile = loadProfile();
    var all = loadNotes();
    return all[profile.persona] || [];
  }

  // Inject a Save button beneath each quest reflection textarea.
  // Reads quest metadata from the closest .quest ancestor.
  function injectSaveButtons() {
    var here = location.pathname.split('/').pop();
    var chapterTitle = CHAPTER_TITLES[here];
    var chapterNum   = CHAPTER_NUMS[here];
    if (!chapterTitle) return;

    // Only target quest-level reflections, not the final chapter reflection
    var questReflections = document.querySelectorAll('.quest .reflection-prompt.quest-reflection, .quest .reflection-prompt');
    if (!questReflections.length) return;

    questReflections.forEach(function (promptDiv) {
      var quest = promptDiv.closest('.quest');
      if (!quest) return;
      var textarea = promptDiv.querySelector('textarea');
      if (!textarea) return;

      // Extract quest metadata from DOM
      var questId    = quest.dataset.quest || 'unknown';
      var labelEl    = quest.querySelector('.quest-title-area .label');
      var titleEl    = quest.querySelector('.quest-title-area h3');
      var questLabel = labelEl  ? labelEl.textContent.trim()  : questId;
      var questTitle = titleEl  ? titleEl.textContent.trim()  : '';

      // Build the action row
      var actions = document.createElement('div');
      actions.className = 'rj-note-actions';
      actions.style.cssText = 'display:flex;align-items:center;gap:10px;margin-top:8px;';

      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'rj-save-btn';
      btn.textContent = 'Save to Field Notes';
      btn.style.cssText = [
        'font-family:"VT323",monospace',
        'font-size:14px',
        'letter-spacing:1.5px',
        'text-transform:uppercase',
        'padding:5px 14px',
        'background:var(--persona-color,#6105C4)',
        'color:var(--paper,#FFFCF0)',
        'border:2px solid var(--ink,#2D1B0E)',
        'box-shadow:2px 2px 0 var(--ink,#2D1B0E)',
        'cursor:pointer',
        'transition:transform 0.1s,box-shadow 0.1s'
      ].join(';');

      var hint = document.createElement('span');
      hint.className = 'rj-save-hint';
      hint.style.cssText = 'font-family:"VT323",monospace;font-size:13px;color:var(--ink-soft,#5D4037);letter-spacing:1px;';

      actions.appendChild(btn);
      actions.appendChild(hint);
      promptDiv.appendChild(actions);

      btn.addEventListener('click', function () {
        var text = textarea.value.trim();
        if (!text) {
          hint.textContent = 'Write something first.';
          setTimeout(function () { hint.textContent = ''; }, 2000);
          return;
        }

        var profile = loadProfile();
        saveNote({
          id:           questId + '-' + Date.now(),
          chapterNum:   chapterNum,
          chapterTitle: chapterTitle,
          questId:      questId,
          questLabel:   questLabel,
          questTitle:   questTitle,
          persona:      profile.persona,
          text:         text,
          savedAt:      Date.now()
        });

        btn.textContent = 'Saved ✓';
        btn.style.background = 'var(--grass,#7AAB58)';
        hint.textContent = '';
        setTimeout(function () {
          btn.textContent = 'Save to Field Notes';
          btn.style.background = '';
        }, 1600);

        renderNotesCard();
      });
    });
  }

  // Render the notes sidebar: grouped by chapter, current chapter expanded.
  function renderNotesCard() {
    var card = document.querySelector('.notes-card');
    if (!card) return;

    var here = location.pathname.split('/').pop();
    var currentChNum = CHAPTER_NUMS[here] || 0;
    var notes = getPersonaNotes();
    var profile = loadProfile();
    var personaName = (PERSONAS[profile.persona] || PERSONAS.jordan).fullName;

    // Group by chapter number
    var byChapter = {};
    notes.forEach(function (n) {
      var key = n.chapterNum || 0;
      if (!byChapter[key]) byChapter[key] = { title: n.chapterTitle || ('Ch ' + key), notes: [] };
      byChapter[key].notes.push(n);
    });

    var totalCount = notes.length;

    // Build header
    var countLabel = totalCount === 0 ? '0 saved' : totalCount + (totalCount === 1 ? ' note' : ' notes');
    var header = '<h3>Field Notes <span style="font-family:\'VT323\',monospace;font-size:13px;color:var(--ink-soft);letter-spacing:1px;">' + countLabel + '</span></h3>';

    if (totalCount === 0) {
      card.innerHTML = header +
        '<p class="meta" style="font-family:\'Source Serif 4\',serif;font-size:14px;font-style:italic;color:var(--ink-soft);margin-bottom:12px;">Your observations will appear here as you save them.</p>' +
        '<div class="notes-list"><div class="note empty"><p class="note-text" style="font-size:14px;color:var(--ink-soft);font-style:italic;">Nothing yet. Complete a quest and save your reflection.</p></div></div>';
      return;
    }

    // Build grouped list
    var groupsHTML = '';
    var chapterKeys = Object.keys(byChapter).map(Number).sort(function (a, b) { return a - b; });

    chapterKeys.forEach(function (chNum) {
      var group    = byChapter[chNum];
      var isOpen   = (chNum === currentChNum);
      var groupId  = 'rj-notes-ch-' + chNum;
      var notesHTML = group.notes.map(function (n) {
        var truncated = n.text.length > 90 ? n.text.slice(0, 90) + '…' : n.text;
        return '<div class="rj-note-item" style="padding:6px 0;border-bottom:1px dashed rgba(45,27,14,0.15);">' +
          '<div style="font-family:\'VT323\',monospace;font-size:12px;color:var(--ink-soft);letter-spacing:1px;text-transform:uppercase;margin-bottom:2px;">' + (n.questLabel || n.questId) + '</div>' +
          '<div style="font-family:\'Source Serif 4\',serif;font-size:13.5px;line-height:1.4;color:var(--ink);">' + truncated + '</div>' +
          '</div>';
      }).join('');

      groupsHTML +=
        '<div class="rj-note-group" style="margin-bottom:6px;">' +
        '<button onclick="(function(el){var body=el.nextElementSibling;var open=body.style.display!==\'none\';body.style.display=open?\'none\':\'\';el.querySelector(\'.rj-toggle\').textContent=open?\'▸\':\'▾\';})(this)" style="width:100%;display:flex;justify-content:space-between;align-items:center;background:var(--oat);border:2px solid var(--ink);padding:5px 10px;cursor:pointer;font-family:\'VT323\',monospace;font-size:14px;letter-spacing:1.5px;text-transform:uppercase;color:var(--ink);box-shadow:2px 2px 0 var(--ink-soft);">' +
        '<span>' + group.title + '</span>' +
        '<span style="display:flex;align-items:center;gap:8px;"><span style="font-size:12px;color:var(--ink-soft);">' + group.notes.length + '</span><span class="rj-toggle">' + (isOpen ? '▾' : '▸') + '</span></span>' +
        '</button>' +
        '<div id="' + groupId + '" style="padding:4px 0 2px;' + (isOpen ? '' : 'display:none;') + '">' + notesHTML + '</div>' +
        '</div>';
    });

    // Copy all button
    var copyBtn = '<button id="rjCopyAllBtn" style="width:100%;margin-top:12px;padding:8px 12px;background:var(--indigo,#6105C4);color:var(--paper,#FFFCF0);border:2px solid var(--ink,#2D1B0E);box-shadow:3px 3px 0 var(--ink,#2D1B0E);font-family:\'VT323\',monospace;font-size:15px;letter-spacing:2px;text-transform:uppercase;cursor:pointer;">Copy all notes for LLM</button>';
    var copyHint = '<p id="rjCopyHint" style="font-family:\'VT323\',monospace;font-size:12px;color:var(--grass-dark,#5C8841);letter-spacing:1px;text-align:center;margin-top:4px;min-height:16px;"></p>';

    card.innerHTML = header +
      '<div class="notes-list" style="margin:10px 0 4px;">' + groupsHTML + '</div>' +
      copyBtn + copyHint;

    // Wire copy button
    var btn = document.getElementById('rjCopyAllBtn');
    if (btn) {
      btn.addEventListener('click', function () {
        var text = buildExportText(personaName, notes);
        navigator.clipboard.writeText(text).then(function () {
          btn.textContent = 'Copied ✓';
          document.getElementById('rjCopyHint').textContent = 'Paste into Claude or ChatGPT.';
          setTimeout(function () {
            btn.textContent = 'Copy all notes for LLM';
            document.getElementById('rjCopyHint').textContent = '';
          }, 2500);
        }).catch(function () {
          // Fallback for browsers that block clipboard without interaction
          var ta = document.createElement('textarea');
          ta.value = buildExportText(personaName, notes);
          document.body.appendChild(ta);
          ta.select();
          document.execCommand('copy');
          document.body.removeChild(ta);
          btn.textContent = 'Copied ✓';
          setTimeout(function () { btn.textContent = 'Copy all notes for LLM'; }, 2500);
        });
      });
    }
  }

  // Build the plain-text LLM export string.
  function buildExportText(personaName, notes) {
    var dateStr = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    var lines = [];

    lines.push('You are helping a UX researcher synthesize dogfooding notes from a renter journey session on Apartment List. Summarize the notes below into key findings, grouped by theme (e.g. Bugs, Pain Points, Design Observations, Praise, Ideas). Note patterns, surprises, and anything that suggests a product opportunity or gap. Write in clear, concise prose suitable for a research readout.');
    lines.push('');
    lines.push('---');
    lines.push('');
    lines.push('RENTER\'S JOURNEY SESSION NOTES');
    lines.push('Persona: ' + personaName);
    lines.push('Date: ' + dateStr);
    lines.push('');

    // Group by chapter for readable output
    var byChapter = {};
    notes.forEach(function (n) {
      var key = n.chapterNum || 0;
      if (!byChapter[key]) byChapter[key] = [];
      byChapter[key].push(n);
    });

    var chapterKeys = Object.keys(byChapter).map(Number).sort(function (a, b) { return a - b; });
    chapterKeys.forEach(function (chNum) {
      var group = byChapter[chNum];
      group.forEach(function (n) {
        lines.push('[' + (n.chapterTitle || 'Ch ' + chNum) + ' · ' + (n.questLabel || n.questId) + ']');
        if (n.questTitle) lines.push('Quest: ' + n.questTitle);
        lines.push('Note: ' + n.text);
        lines.push('');
      });
    });

    return lines.join('\n');
  }

  // Persona-switch warning: intercept if current persona has saved notes.
  function initPersonaSwitchWarning() {
    var cards = document.querySelectorAll('.card .btn-embark');
    if (!cards.length) return;

    cards.forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        var profile = loadProfile();
        var currentNotes = getPersonaNotes();
        if (!currentNotes.length) return; // no notes, proceed normally

        var card = btn.closest('.card');
        var personaKey = 'jordan';
        if (card.classList.contains('alex'))   personaKey = 'alex';
        else if (card.classList.contains('jordan'))  personaKey = 'jordan';
        else if (card.classList.contains('taylor-riley') || card.classList.contains('taylor')) personaKey = 'taylor';
        else if (card.classList.contains('jamie'))   personaKey = 'jamie';

        // Same persona — no warning needed
        if (personaKey === profile.persona) return;

        // Different persona — intercept and warn
        e.stopImmediatePropagation();
        e.preventDefault();

        showSwitchWarning(currentNotes.length, profile, personaKey);
      }, true); // capture phase so we run before initPersonaSelection
    });
  }

  function showSwitchWarning(noteCount, currentProfile, nextPersonaKey) {
    var existingDialog = document.getElementById('rjSwitchDialog');
    if (existingDialog) existingDialog.remove();

    var personaName = (PERSONAS[currentProfile.persona] || PERSONAS.jordan).fullName;
    var noteWord = noteCount === 1 ? 'Field Note' : 'Field Notes';

    var dialog = document.createElement('div');
    dialog.id = 'rjSwitchDialog';
    dialog.style.cssText = [
      'position:fixed', 'inset:0', 'z-index:9999',
      'display:flex', 'align-items:center', 'justify-content:center',
      'background:rgba(45,27,14,0.55)'
    ].join(';');

    dialog.innerHTML = [
      '<div style="background:var(--paper,#FFFCF0);border:3px solid var(--ink,#2D1B0E);box-shadow:8px 8px 0 var(--ink,#2D1B0E);padding:28px 30px;max-width:400px;width:90%;font-family:\'Source Serif 4\',serif;">',
      '<div style="font-family:\'VT323\',monospace;font-size:15px;letter-spacing:3px;color:var(--indigo,#6105C4);text-transform:uppercase;margin-bottom:10px;">Before you switch</div>',
      '<p style="font-size:16px;line-height:1.5;color:var(--ink,#2D1B0E);margin-bottom:20px;">You have <strong>' + noteCount + ' ' + noteWord + '</strong> from your ' + personaName + ' session. They\'ll stay here waiting if you switch, but copying them now means you won\'t lose the thread.</p>',
      '<div style="display:flex;gap:12px;flex-wrap:wrap;">',
      '<button id="rjDialogCopy" style="flex:1;padding:10px 14px;background:var(--indigo,#6105C4);color:var(--paper,#FFFCF0);border:2px solid var(--ink,#2D1B0E);box-shadow:3px 3px 0 var(--ink,#2D1B0E);font-family:\'VT323\',monospace;font-size:15px;letter-spacing:1.5px;text-transform:uppercase;cursor:pointer;">Copy notes, then switch</button>',
      '<button id="rjDialogSwitch" style="flex:1;padding:10px 14px;background:var(--oat,#F5F2ED);color:var(--ink,#2D1B0E);border:2px solid var(--ink,#2D1B0E);box-shadow:3px 3px 0 var(--ink-soft,#5D4037);font-family:\'VT323\',monospace;font-size:15px;letter-spacing:1.5px;text-transform:uppercase;cursor:pointer;">Switch anyway</button>',
      '</div>',
      '</div>'
    ].join('');

    document.body.appendChild(dialog);

    function proceed() {
      dialog.remove();
      var currentNotes = getPersonaNotes();
      var allNotes = loadNotes();
      // Switch persona and reset chapter progress
      saveProfile({ persona: nextPersonaKey, unlockedChapter: 1 });
      window.location.href = 'avatar-creation-mockup.html';
    }

    document.getElementById('rjDialogCopy').addEventListener('click', function () {
      var currentNotes = getPersonaNotes();
      var personaName2 = (PERSONAS[currentProfile.persona] || PERSONAS.jordan).fullName;
      var text = buildExportText(personaName2, currentNotes);
      navigator.clipboard.writeText(text).then(proceed).catch(function () {
        var ta = document.createElement('textarea');
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        proceed();
      });
    });

    document.getElementById('rjDialogSwitch').addEventListener('click', proceed);

    // Click outside to cancel
    dialog.addEventListener('click', function (e) {
      if (e.target === dialog) dialog.remove();
    });
  }

  // The mockup index page: nothing to wire, but apply avatar vars anyway
  // so any preview hovers respect the saved profile.
  function init() {
    var profile = loadProfile();
    applyAvatarVars(profile);
    paintHUDs(profile);
    initPersonaSelection();
    initPersonaSwitchWarning();
    initAvatarCreation();
    initJourneyMap();
    initChapterNav();
    initBriefingCard();
    injectSaveButtons();
    renderNotesCard();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Expose a tiny global for debugging from the console.
  window.RJ = {
    load:      loadProfile,
    save:      saveProfile,
    loadNotes: loadNotes,
    reset: function () {
      try { localStorage.removeItem(STORAGE_KEY); } catch (e) {}
    },
    resetNotes: function () {
      try { localStorage.removeItem(NOTES_KEY); } catch (e) {}
    },
    paint: function () { paintHUDs(loadProfile()); }
  };
})();
