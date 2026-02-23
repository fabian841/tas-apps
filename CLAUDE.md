# CLAUDE.md — ClearWay TTM v3.0

## Project Overview

ClearWay TTM (Traffic Management) v3.0 is a single-page web application for NSW (Australia) traffic management professionals. It provides tools for job planning, TGS (Traffic Guidance Scheme) lookup, device selection, weather-aware safety monitoring, compliance checklists, incident reporting, and on-site engineering calculations. The app targets road workers, traffic controllers (ITCP), facility access managers, and PWZTMP-qualified personnel.

**Live deployment:** GitHub Pages (static file hosting)

## Architecture

This is a **zero-dependency, single-file application** — all HTML, CSS, and JavaScript live in `index.html` (1,752 lines). There is no build step, no package manager, no bundler, and no framework.

```
/
├── index.html          # Entire application (HTML + CSS + JS inline)
└── CLAUDE.md           # This file
```

### Technology Stack

| Layer     | Technology                          |
|-----------|-------------------------------------|
| Markup    | HTML5                               |
| Styling   | CSS3 with custom properties (vars)  |
| Logic     | Vanilla JavaScript (ES6+)           |
| Fonts     | Google Fonts CDN (Barlow Condensed, Barlow, JetBrains Mono) |
| Weather   | Open-Meteo API (free, no API key)   |
| Geocoding | OpenStreetMap Nominatim (free, no API key) |
| Maps      | OpenStreetMap embed                 |
| AI        | Anthropic Claude API (claude-sonnet-4-20250514) |

### No Build Tools

- No npm/yarn/pnpm, no `package.json`, no `node_modules`
- No TypeScript, no transpilation, no bundler (webpack/vite/rollup)
- No ESLint, Prettier, or other linters
- No testing framework
- No CI/CD pipeline
- The file is served as-is to the browser

## Application Structure (within index.html)

The file is organized into three blocks separated by `<style>`, `</style>`, `<script>`, `</script>` tags:

### CSS (lines 8–334)

- **CSS custom properties** defined on `:root` (line 9) for the dark theme:
  - Colors: `--void`, `--deep`, `--surface`, `--panel`, `--blue`, `--blue-hi`, `--cyan`, `--gold`, `--amber`, `--green`, `--red`, `--white`, `--grey`
  - Semi-transparent variants: `--cyan-d`, `--gold-d`, `--green-d`, `--amber-d`, `--red-d` (used for badge/alert backgrounds)
  - Borders: `--border`, `--border-hi`
  - Fonts: `--font` (Barlow Condensed), `--body` (Barlow), `--mono` (JetBrains Mono)
- Responsive breakpoint at **768px** for mobile layout (line 325)
- Animation keyframes: `blink` (pulsing opacity), `fin` (fade-in slide-up on page switch)

### HTML Body (lines 336–1002)

Fixed-position elements rendered outside `.app`:
- `#offline-banner` (line 337) — offline warning
- `#toast` (line 338) — notification pop-up
- `#ptt-panel` (lines 341–352) — Push-to-Talk floating panel
- `#nm-modal` (lines 355–383) — Near-Miss Report modal
- `#taper-modal` (lines 386–411) — Taper Calculator modal
- `#speed-modal` (lines 414–432) — Speed Reduction Advisor modal
- `#fat-wrap` (lines 435–443) — Fatigue Timer (fixed top-right)
- `#ai-wrap` (lines 447–462) — AI Advisor chat (fixed bottom-left)

Main `.app` layout (lines 465–1002):
- `.topbar` — Brand, live status chip, ROL countdown, weather chip, AEDT clock
- `.sidebar` — Navigation grouped into 6 sections
- `.content` — Page container where `.page` divs toggle visibility

### JavaScript (lines 1004–1750)

Organized by `// ── SECTION NAME ───────────────` comment markers.

## Pages (13 total)

Page divs use `id="page-{name}"`. The `nav(name)` function (line 1006) adds `.active` to `#page-{name}` and highlights the matching sidebar item.

### Sidebar Navigation Structure

| Section      | Page ID            | Nav Label          | Alt Key | Description |
|-------------|--------------------|--------------------|---------|-------------|
| Overview    | `page-dashboard`   | Dashboard          | Alt+1   | Job overview, active sites, open issues, weather, quick tools |
| Planning    | `page-plan`        | New Job Plan       | Alt+2   | 6-step wizard: Location → Road → Work → Duration → Permits → Result |
| Planning    | `page-tgs`         | TGS Library        | Alt+6   | 9 traffic guidance schemes with speed/lane filtering, TCAWS PDF links |
| Planning    | `page-tmp`         | TMP Generator      | —       | Traffic Management Plan document template, auto-populated from wizard |
| Planning    | `page-briefing`    | Pre-Site Briefing  | Alt+3   | 8-card swipeable carousel with sign-off gate |
| On Site     | `page-implement`   | Implement          | Alt+4   | 3-tab checklists: Setup (12 items), Shift (6 items), Weekly (6 items) |
| On Site     | `page-monitor`     | Monitor            | Alt+5   | Live status cards, open issues, activity log |
| On Site     | `page-conditions`  | Conditions         | —       | Weather display, condition logging, TGS impact assessment |
| On Site     | `page-risk`        | Risk & Changes     | —       | TGS change requests, active risk register |
| Tools       | `page-device`      | Device Advisor     | Alt+7   | 5-step decision tree recommending PORTABOOM / MINIBOOM products |
| Reporting   | `page-incidents`   | Incidents          | —       | Full incident/near-miss reporting form with SafeWork NSW integration |
| Reporting   | `page-comms`       | Communications     | —       | Message history, send updates to parties |
| Reporting   | `page-packup`      | Site Completion    | —       | Pack-up checklists with progress tracking, final PWZTMP sign-off |
| Performance | `page-safety`      | Safety Score       | Alt+8   | Score ring, streaks, badges, monthly leaderboard |

### Modal Dialogs (not pages)

| Modal ID       | Trigger       | Description |
|----------------|---------------|-------------|
| `taper-modal`  | Alt+T         | AS 1742.3 taper calculator (8 speed options × 5 lane widths) |
| `speed-modal`  | Alt+S         | Speed reduction step advisor (max 20 km/h per step) |
| `nm-modal`     | Alt+R         | Quick near-miss report (6 categories, 3 severities, anonymous option) |

### Floating Panels

| Panel          | Position      | Description |
|----------------|---------------|-------------|
| `#ptt-panel`   | Bottom-right  | Push-to-talk radio (4 channels, hold-to-transmit button) |
| `#ai-wrap`     | Bottom-left   | Claude-powered AI Site Advisor chat |
| `#fat-wrap`    | Top-right     | Fatigue timer with 2-hour break countdown |

## JavaScript Sections (lines 1004–1750)

| Section (line)           | Key Functions | Purpose |
|--------------------------|---------------|---------|
| NAVIGATION (1005)        | `nav(name)` | Page switching — prepends `page-` to name, toggles `.active`, re-initializes page-specific content |
| SIDEBAR (1023)           | `toggleSidebar()`, `closeSidebar()` | Mobile hamburger menu toggle |
| MODALS (1027)            | `openModal(id)`, `closeModal(id)` | Toggle `.open` class; click-outside-to-close |
| CLOCK (1032)             | `updateClock()` | Live AEDT time in topbar, updates every 1s |
| TOAST (1039)             | `toast(msg)` | 2.2s notification pop-up |
| WEATHER (1046)           | `fetchWeather(lat,lon)`, `buildWxAlerts()` | Open-Meteo API, updates dashboard + conditions page + topbar chip, auto-refreshes every 10 min |
| GEOCODING (1095)         | `geocodeDebounce()`, `geocode(addr)` | Nominatim lookup with 800ms debounce, updates weather + embeds OSM map |
| ROL COUNTDOWN (1121)     | `setROL()`, `updateROL()` | Topbar ROL expiry chip with color escalation (green → amber → red → EXPIRED), updates every 10s |
| WIZARD STATE (1145)      | `selOpt()`, `togOpt()`, `nextStep()`, `prevStep()`, `resetWizard()` | 6-step job planning wizard with single/multi-select option cards |
| GENERATE PLAN (1186)     | `generatePlan()` | Auto-selects TGS code based on speed+lanes, calculates AS 1742.3 distances, lists required devices and qualifications |
| BRIEFING CARDS (1245)    | `initBriefing()`, `nextCard()`, `goCard()`, `signOffBriefing()` | 8-card carousel with view tracking and sign-off gate |
| CHECKLISTS (1291)        | `buildChecklists()`, `renderCL()`, `toggleCheck()` | 3 inspection types: setup (12 items), shift (6), weekly (6) with tab switching |
| PACK CHECKLIST (1350+)   | `buildPackUp()`, `togglePack()`, `togglePackItem()` | Expandable sections with per-item checkboxes and progress bars |
| TGS LIBRARY (1410)       | `filterTGS()`, `renderTGS()` | Speed/lane filtering, card rendering with TCAWS PDF page links |
| DEVICE ADVISOR (1453)    | `initAdvisor()`, `renderAdvQ()`, `advSelect()`, `advBack()`, `renderAdvResult()` | Decision tree navigation with back/restart, result cards |
| TAPER CALCULATOR (1562)  | `setTCspeed()`, `setTCwidth()`, `calcTaper()` | Merge taper (2D), lateral shift (D), W×S²/120 formula, cone spacing, buffer length |
| SPEED ADVISOR (1610)     | `calcSpeedAdvisor()` | Step-down calculation with 200m transition zones |
| PTT (1629)               | `setPTTch()`, `startPTT()`, `stopPTT()` | Channel selection, hold-to-transmit with visual/text feedback |
| NEAR MISS (1648)         | `selNMcat()`, `selNMsev()`, `submitNM()` | Category/severity selection, anonymous toggle, submit with toast |
| FATIGUE TIMER (1659)     | `toggleFat()`, `updateFat()`, `logBreak()` | Elapsed time counter, 2-hour break interval bar (green → amber → red), break-overdue alert |
| AI ADVISOR (1684)        | `toggleAI()`, `sendAI()` | Claude API chat with TCAWS/NSW-specific system prompt, error fallback |
| MISC (1716)              | `showIncForm()`, `triggerPhoto()` | Incident form toggle, photo capture placeholder |
| OFFLINE DETECTION (1720) | `checkOnline()` | Shows/hides `#offline-banner` on network events |
| KEYBOARD SHORTCUTS (1729)| — | Alt+1-8 page navigation, Alt+T/S/R modal shortcuts |
| INIT (1740)              | — | Calls `buildChecklists()`, `buildPackUp()`, `initBriefing()`, `initAdvisor()`, `renderTGS()`, sets date, shows welcome toast |

## Code Conventions

### Naming

- **CSS classes:** kebab-case (`.nav-item`, `.card-title`, `.btn-sm`)
- **CSS prefix groups:** `adv-` (advisor), `tgs-` (TGS library), `ptt-` (push-to-talk), `nm-` (near-miss), `fat-`/`ft-` (fatigue), `ai-` (AI advisor), `tc-` (taper calculator), `sa-` (speed advisor), `wx-` (weather), `bc-` (briefing card highlight), `cm-` (comms)
- **JavaScript variables/functions:** camelCase (`tgsLib`, `renderTGS()`, `advHistory`, `calcTaper()`)
- **HTML IDs:** kebab-case (`tgs-spd`, `adv-q-wrap`, `ptt-btn`, `ai-chat-box`), page IDs use `page-` prefix (`page-dashboard`, `page-plan`)

### CSS Class Shorthand System

The app uses a compact class naming system for frequently-used components:

**Badges:** `.badge` base + color suffix: `.bg` (green), `.ba` (amber), `.br` (red), `.bb` (blue), `.bc` (cyan), `.bx` (grey)

**Buttons:** `.btn` base + variant: `.btn-p` (primary/blue), `.btn-g` (gold/CTA), `.btn-o` (outline), `.btn-r` (red/danger), `.btn-c` (cyan), `.btn-sm` (small size)

**Alerts:** `.alert` base + type: `.al-w` (warning/amber), `.al-d` (danger/red), `.al-i` (info/blue), `.al-s` (success/green), `.al-c` (cyan)

**Forms:** `.fg` (form group), `.fl` (form label), `.fi` (form input), `.fs` (form select), `.ft` (form textarea), `.req` (required asterisk)

**Layout:** `.g2`, `.g3`, `.g4` (2/3/4-column CSS grids), `.ph` (page header), `.pt` (page title), `.ps` (page subtitle)

**Stat cards:** `.sc` (stat card container), `.sv` (stat value), `.sl` (stat label)

**Wizard:** `.wprog` (wizard progress), `.wstep` (step indicator), `.wq` (wizard question), `.wh` (wizard hint)

**Option cards:** `.ogrid` (option grid), `.ocard` (option card), `.oi` (option icon), `.ol` (option label), `.od` (option description), `.sel` (selected), `.multi-sel` (multi-selected)

**Navigation badges:** `.nbadge` base + `.nb-r` (red), `.nb-a` (amber), `.nb-g` (green), `.nb-c` (cyan)

### JavaScript Patterns

- Event-driven UI with inline `onclick` handlers in HTML
- State stored in module-level variables (`packState`, `advHistory`, `tgsLib`, `csState`, `sel`, `curStep`, `bIdx`, `bViewed`, `rolExpiry`, `aiOpen`)
- DOM manipulation via `document.getElementById()` and `innerHTML`
- No frameworks, no virtual DOM, no state management library
- Section markers: `// ── SECTION NAME ───────────────`
- `setInterval` for live updates: clock (1s), fatigue timer (1s), weather (10 min), ROL countdown (10s)

### HTML Patterns

- Pages are `<div class="page" id="page-{name}">` — only one has `.active` at a time
- `nav(name)` toggles `.active` and re-initializes page data (briefing, checklists, TGS, advisor)
- Modals use `.modal` class with `.open` toggled via JS; click-outside closes
- Inline `style` attributes used for one-off layout adjustments
- Tabs (on Implement page) use `switchTab()` to show/hide `<div>` sections

## Key Data Structures

### TGS Library (`tgsLib` array, line 1411)
9 traffic guidance schemes: `{code, name, speed, lane, desc, page}`. Speed values: `low`/`mid`/`high`. Lane values: `shoulder`/`one-lane`/`full`. Page = TCAWS PDF page number.

### Device Advisor Tree (`advTree` object, line 1454)
Nested decision tree with `{id, step, total, label, q, hint, opts}`. Each option has `{icon, label, desc, next}`. Terminal nodes: `{result: 'key'}` pointing to `advResults`.

### Product Data (`advResults` object, line 1494)
6 product recommendation cards keyed by: `pb4000-basic`, `pb4000-tastrack`, `pb4000-tma`, `miniboom`, `pb4000-event`, `pb4000-rapid`. Each has `{product, tag, specs[], note, cta}`.

### Checklist Items (lines 1292–1321)
- `setupItems` — 12 pre-opening verification items (INS-01)
- `shiftItems` — 6 shift inspection items (INS-02, twice per shift)
- `weeklyItems` — 6 weekly inspection items (INS-03, PWZTMP only)
- `csState` — `{setup:{}, shift:{}, weekly:{}}` tracks checked state by index

### Briefing Cards (`defaultCards` array, line 1246)
8 cards with `{icon, title, body}`. Cards cover: TGS scheme, distances, PORTABOOM requirement, ROL, weather, underground hazards, emergency contacts, readiness.

### Wizard State (`sel` object, `curStep` variable, line 1146)
`sel` stores user selections keyed by option group name (e.g. `sel['road-type']`, `sel['lanes']`, `sel['work-type']` as array). `curStep` tracks position (1-6).

### Plan Generation Logic (`generatePlan()`, line 1187)
Reads `loc-speed` + `sel['lanes']` to determine TGS code. Mapping:
- ≤50 + shoulder → A1-50
- ≤50 + one-lane/partial → A2-50
- ≤70 + full → B3-70
- ≤70 + other → B1-60
- ≥80 + full → C4-100
- ≥80 + other → C3-100

## External Dependencies

| Dependency | URL | Purpose |
|------------|-----|---------|
| Google Fonts | `fonts.googleapis.com` | Barlow Condensed, Barlow, JetBrains Mono |
| Open-Meteo | `api.open-meteo.com/v1/forecast` | Weather data: temp, wind, gusts, UV, humidity, weather code. Free, no API key |
| Nominatim | `nominatim.openstreetmap.org/search` | Address geocoding (NSW, Australia). Free, requires User-Agent header |
| OpenStreetMap | `openstreetmap.org/export/embed.html` | Embedded map preview in job plan wizard |
| Claude API | `api.anthropic.com/v1/messages` | AI Advisor chat (claude-sonnet-4-20250514, max_tokens 300) |
| TCAWS PDF | `roads-waterways.transport.nsw.gov.au/...` | Traffic Control at Work Sites Manual v6.1 — linked with `#page=` anchors |

### Weather Alert Thresholds (in `buildWxAlerts()`, line 1081)
- Gusts >90 km/h → **CEASE WORK** (danger alert)
- Gusts >60 km/h → Wind warning
- UV ≥11 → Extreme UV, limit outdoor exposure
- UV ≥8 → Very high UV, SPF50+ mandatory
- Temp ≥35°C → Heat stress protocol, mandatory shade every 45 min
- Temp ≥28°C → Hot conditions, hydrate now

## Regulatory Standards Referenced

- **TCAWS 6.1** — NSW Traffic Control at Work Sites Manual (v6.1)
- **AS 1742.3:2019** — Australian standard for road works signing
- **PWZTMP** — Person With Zone Traffic Management Permit
- **ITCP** — In-Traffic Control Personnel (RIIWHS302E)
- **ROL** — Road Occupancy Licence (required for TfNSW state roads)
- **INS-01/02/03** — TCAWS inspection types (setup, shift, weekly)
- **SafeWork NSW** — Serious injury reporting (13 10 50)

## Development Workflow

### Running Locally

No build required. Open `index.html` directly in a browser, or serve with any static file server:

```bash
# Python
python3 -m http.server 8000

# Node (npx)
npx serve .
```

Note: The AI Advisor requires a Claude API key to be added to the fetch headers in `sendAI()` (line 1700). Weather and geocoding work without API keys.

### Making Changes

1. Edit `index.html` directly — all code is in this single file
2. Refresh the browser to see changes
3. CSS is lines 8–334 (in `<style>`), HTML is lines 336–1002, JS is lines 1004–1750 (in `<script>`)
4. Use the section comment markers to navigate: search for `// ──` in JS

### Deployment

Push to `main` branch — GitHub Pages serves `index.html` automatically.

## Security Notes

- The Claude API call in `sendAI()` (line 1700) makes client-side requests to `api.anthropic.com`. No API key is currently set — one would need to be added in the `headers` object. **Do not hardcode API keys in client-side code for production.**
- User-generated content (near-miss reports, AI chat input) is rendered via `innerHTML` — XSS risk if content is persisted or shared.
- The Nominatim geocoder sends street addresses to OSM servers.
- No authentication or authorization system exists.
- No Content Security Policy (CSP) headers defined.

## Common Modification Tasks

### Adding a new page
1. Add a `.nav-item` in the sidebar HTML (inside the appropriate `nav-sec` group) with `onclick="nav('newpage')"`
2. Add a `<div class="page" id="page-newpage">` inside `.content` (the `page-` prefix is required)
3. Optionally add a keyboard shortcut in the `KEYBOARD SHORTCUTS` section (line 1730, add to the `map` object)

### Adding a new TGS scheme
Add an object to the `tgsLib` array (line 1411) following the shape: `{code, name, speed, lane, desc, page}`. Speed must be `'low'`/`'mid'`/`'high'`, lane must be `'shoulder'`/`'one-lane'`/`'full'`. Also update `generatePlan()` if the new scheme should be auto-recommended.

### Adding a new device advisor path
Extend `advTree` (line 1454) with new question nodes (`{id, step, total, label, q, hint, opts}`) and add result entries to `advResults` (line 1494) with `{product, tag, specs[], note, cta}`.

### Adding a new checklist
Add items to `setupItems`/`shiftItems`/`weeklyItems` (lines 1292–1321). Each item: `{t: 'title', s: 'subtitle', r: 'badge label'}`. Badge label maps to a color via `rc` object in `renderCL()`.

### Modifying the theme
Edit CSS custom properties on `:root` (line 9). All colors cascade through the variables. The `-d` suffixed variables are semi-transparent versions used for badge/alert backgrounds.

### Adding weather alert rules
Add conditions in `buildWxAlerts()` (line 1081). Use `al-d` for danger, `al-w` for warning. Alerts appear on both dashboard and conditions page.
