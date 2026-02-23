# CLAUDE.md — ClearWay TTM v3.0

## Project Overview

ClearWay TTM (Traffic Management) v3.0 is a single-page web application for NSW (Australia) traffic management professionals. It provides tools for road work planning, traffic guidance scheme lookup, device selection, safety reporting, and on-site calculations. The app targets road workers, traffic controllers (ITCP), and facility access managers.

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
| AI        | Anthropic Claude API (claude-sonnet-4-20250514) |

### No Build Tools

- No npm/yarn/pnpm, no `package.json`, no `node_modules`
- No TypeScript, no transpilation, no bundler (webpack/vite/rollup)
- No ESLint, Prettier, or other linters
- No testing framework
- No CI/CD pipeline
- The file is served as-is to the browser

## Application Structure (within index.html)

The file is organized into clearly delimited sections:

### CSS (lines ~8–400)

- **CSS custom properties** defined on `:root` for the dark theme:
  - Colors: `--void`, `--deep`, `--surface`, `--panel`, `--blue`, `--cyan`, `--gold`, `--amber`, `--green`, `--red`, `--white`, `--grey`
  - Fonts: `--font` (Barlow Condensed), `--body` (Barlow), `--mono` (JetBrains Mono)
- Component styles: `.topbar`, `.sidebar`, `.nav-item`, `.card`, `.badge`, `.btn`, `.modal`, `.alert`
- Responsive breakpoints at `900px` for mobile layout
- Animation keyframes: `blink`, `fin` (fade-in)

### HTML Structure (lines ~400–1350)

Single-page app with hidden `.page` divs toggled via JavaScript:

| Page ID       | Nav Label       | Alt Key | Description |
|---------------|-----------------|---------|-------------|
| `dashboard`   | Dashboard       | Alt+1   | Overview with status badges, live indicators, weather |
| `plan`        | Plan            | Alt+2   | Pack checklists, preparation tracking |
| `briefing`    | Briefing        | Alt+3   | Multi-card carousel with site briefing |
| `implement`   | Implement       | Alt+4   | Task deployment checklist |
| `monitor`     | Monitor         | Alt+5   | Real-time monitoring, incident reporting |
| `tgs`         | TGS Library     | Alt+6   | Traffic Guidance Scheme lookup |
| `device`      | Device Advisor  | Alt+7   | Interactive product recommendation tree |
| `safety`      | Safety          | Alt+8   | Near-miss reporting, fatigue timer |

Modal dialogs: Taper Calculator (`Alt+T`), Speed Advisor (`Alt+S`), Near-Miss Report (`Alt+R`)

### JavaScript (lines ~1350–1752)

Organized by comment-delimited sections:

| Section               | Purpose |
|-----------------------|---------|
| `NAVIGATION`          | `nav()` function, page switching, mobile menu |
| `MODALS`              | `openModal()` / `closeModal()` with overlay |
| `TOASTS`              | Notification pop-ups |
| `CHECKLISTS`          | Pre-start and implement task tracking |
| `PACK CHECKLIST`      | Equipment pack preparation with progress bars |
| `TGS LIBRARY`         | Traffic Guidance Scheme data (9 schemes: A1-50 through C4-100) and filtering |
| `DEVICE ADVISOR`      | Decision tree for PORTABOOM PB4000 / MINIBOOM TZ30 recommendation |
| `TAPER CALCULATOR`    | Merge taper, lateral shift, buffer length per AS 1742.3 |
| `SPEED ADVISOR`       | Speed reduction step calculator (max 20 km/h per step) |
| `PTT`                 | Push-to-talk radio channel simulation |
| `NEAR MISS`           | Incident reporting form logic |
| `FATIGUE TIMER`       | 2-hour break interval tracking |
| `AI ADVISOR`          | Claude API integration for on-site queries |
| `OFFLINE DETECTION`   | Banner when no internet |
| `KEYBOARD SHORTCUTS`  | Alt+1-8 navigation, Alt+T/S/R modals |
| `INIT`                | Startup calls: `buildChecklists()`, `initAdvisor()`, `renderTGS()`, etc. |

## Code Conventions

### Naming

- **CSS classes:** kebab-case (`.nav-item`, `.card-title`, `.btn-sm`)
- **CSS prefix groups:** `adv-` (advisor), `tgs-` (TGS library), `ptt-` (push-to-talk), `nm-` (near-miss), `fat-` (fatigue), `ai-` (AI advisor), `tc-` (taper calculator), `sa-` (speed advisor)
- **JavaScript variables/functions:** camelCase (`tgsLib`, `renderTGS()`, `advHistory`, `calcTaper()`)
- **HTML IDs:** kebab-case (`tgs-spd`, `adv-q-wrap`, `ptt-btn`, `ai-chat-box`)

### CSS Pattern

- Dark theme with accent colors (cyan primary, blue secondary, gold CTA)
- Compact class names for common utilities (`.bg` = green badge, `.ba` = amber badge, `.br` = red badge, `.bb` = blue badge, `.bc` = cyan badge)
- Button variants: `.btn-p` (primary/blue), `.btn-g` (gold/CTA), `.btn-o` (outline), `.btn-r` (red/danger), `.btn-c` (cyan)
- Grid layout classes: `.g2`, `.g3`, `.g4` for multi-column grids

### JavaScript Pattern

- Event-driven UI with inline `onclick` handlers in HTML
- State stored in module-level variables (`packState`, `advHistory`, `tgsLib`)
- DOM manipulation via `document.getElementById()` and `innerHTML`
- No frameworks, no virtual DOM, no state management library
- Section markers: `// ── SECTION NAME ───────────────`

### HTML Pattern

- Pages are `<div class="page" id="pagename">` — only one has `.active` at a time
- Navigation switches pages via `nav('pagename')` which toggles `.active` class
- Modals use `.modal` class with `.open` toggled via JS
- Inline `style` attributes used for one-off layout adjustments

## Key Data Structures

### TGS Library (`tgsLib` array)
9 traffic guidance schemes with fields: `code`, `name`, `speed` (low/mid/high), `lane` (shoulder/one-lane/full), `desc`, `page` (TCAWS manual page number).

### Device Advisor (`advTree` object)
Nested decision tree with `q` (question), `opts` (options array), and terminal `result` keys pointing to `advResults` product recommendations.

### Product Data (`advResults` object)
Product recommendation cards: PORTABOOM PB4000 variants and MINIBOOM TZ30, each with `specs`, `note`, and `cta`.

## External Dependencies

| Dependency | URL | Purpose |
|------------|-----|---------|
| Google Fonts | `fonts.googleapis.com` | Barlow Condensed, Barlow, JetBrains Mono |
| Claude API | `api.anthropic.com/v1/messages` | AI Advisor chat (claude-sonnet-4-20250514) |
| TCAWS PDF | `roads-waterways.transport.nsw.gov.au/...` | Traffic Control at Work Sites Manual v6.1 links |

## Regulatory Standards Referenced

- **TCAWS 6.1** — NSW Traffic Control at Work Sites Manual
- **AS 1742.3:2019** — Australian standard for road works signing
- **PWZTMP** — Person With Zone Traffic Management Permit
- **ITCP** — In-Traffic Control Personnel
- **ROL** — Roads and Maritime Services (road occupancy licence)

## Development Workflow

### Running Locally

No build required. Open `index.html` directly in a browser, or serve with any static file server:

```bash
# Python
python3 -m http.server 8000

# Node (npx)
npx serve .
```

### Making Changes

1. Edit `index.html` directly — all code is in this single file
2. Refresh the browser to see changes
3. CSS is at the top (in `<style>`), HTML in the middle, JS at the bottom (in `<script>`)
4. Use the section comment markers to navigate (search for `// ──` in JS or `/* ──` in CSS)

### Deployment

Push to `main` branch — GitHub Pages serves `index.html` automatically.

## Security Notes

- The Claude API call in the AI Advisor section (`sendAI()`) makes client-side requests to `api.anthropic.com`. An API key would need to be supplied for this to work in production (currently no key is hardcoded in the source).
- User-generated content (near-miss reports, AI chat input) is rendered via `innerHTML` — be cautious about XSS if any content is persisted or shared.
- No authentication or authorization system exists.

## Common Modification Tasks

### Adding a new page/section
1. Add a `.nav-item` in the sidebar HTML with `onclick="nav('newpage')"`
2. Add a `<div class="page" id="newpage">` in the content area
3. Optionally add a keyboard shortcut in the `KEYBOARD SHORTCUTS` section

### Adding a new TGS scheme
Add an object to the `tgsLib` array following the existing shape: `{code, name, speed, lane, desc, page}`.

### Adding a new device advisor path
Extend the `advTree` nested object with new question nodes and add result entries to `advResults`.

### Modifying the theme
Edit CSS custom properties on `:root` (line ~9). All colors cascade through the variables.
