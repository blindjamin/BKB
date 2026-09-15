# Handoff: BKB Landing Page

## Overview
Marketing/landing page for **BKB, Obras Eléctricas & Servicios** (industrial electrical contractor, Chile). Communicates 25+ years of trayectoria, showcases service lines, real project portfolio, client roster, and routes visitors to a client/staff login and an RFQ (quote request) form.

## About the Design Files
The file in this bundle (`BKB-Landing-reference.dc.html`) is a **design reference built in HTML** — a working prototype of look, layout, and behavior, not production code to copy verbatim. It runs on an internal templating runtime (`{{ }}` bindings, `<sc-for>` loops, `<x-dc>` wrapper) that only works inside the design tool — **do not** try to ship this file or its script tags as-is.

**Your task**: recreate this design in the target codebase's existing stack (React, Vue, etc.), using its established component patterns, state management, and styling approach. If no frontend stack exists yet, React + plain CSS (or CSS-in-JS/Tailwind, per your team's preference) is a reasonable default given this design's structure (component-per-section, simple local UI state, no backend calls beyond form submission stubs).

## Fidelity
**High-fidelity.** Colors, type, spacing, and copy below are final. Recreate pixel-close using the values in "Design Tokens" and per-screen specs below.

## Screens / Views

### 1. Header
- **Purpose**: Persistent navigation + theme toggle + login/quote entry points.
- **Behavior**: Hidden at page load (the Hero is meant to be the full first impression). `position: fixed; top:0`, starts at `opacity:0; transform:translateY(-100%)`. Once `window.scrollY > 40`, add an "is-visible" state → `opacity:1; transform:translateY(0)`, transition `.3s ease`.
- **Visual state depends on the active theme** (see Design Tokens → Theme):
  - Dark theme, scrolled: background `rgba(8,12,20,0.92)`, blur `14px`, text stays white.
  - Light theme, scrolled: background `rgba(251,248,245,0.94)`, blur `14px`, border `rgba(26,21,19,0.08)`, nav text and icon-buttons switch to ink `#1A1513`.
  - Not scrolled (either theme): background `rgba(8,12,20,0.6)` (semi-transparent dark, sits over the hero photo), white text.
- **Layout**: single row, `max-width:1360px` centered, `padding:14px 40px`, `display:flex; justify-content:space-between; align-items:center; gap:24px`.
  - Left: logo (`bkb-logo-final.png`, `height:44px`) + "SEC CLASE A" pill badge (green-on-tint, `#10B981` text on `rgba(16,185,129,0.12)` bg, `IBM Plex Mono` 11px/700, hidden under 1180px).
  - Center: nav links — Inicio, Mercados, Servicios, Obras, Portal SEC, Contacto (14px/500, white, salmon `#FA5A36` on hover; hidden under 1180px).
  - Right: circular theme-toggle button (38×38px, ☀/☾ glyph) → "Acceso Portal" pill (hidden under 1180px) → "Cotizar Obra" filled salmon pill (always visible, never wraps/clips — this is the one element guaranteed visible at all widths).
- **Responsive**: below 1180px, hide nav links, SEC badge, and "Acceso Portal"; keep logo, theme toggle, and "Cotizar Obra".

### 2. Hero
- **Purpose**: First-impression full-bleed statement + entry point to client/staff portal.
- **Layout**: `min-height:100vh`, full-bleed background photo (`faena-hero.jpg`, `object-fit:cover`, slow 22s zoom-out keyframe from `scale(1.1)` to `scale(1)` on load) with a dark diagonal gradient overlay (`linear-gradient(115deg, rgba(8,12,20,.92) 20%, rgba(8,12,20,.72) 55%, rgba(8,12,20,.5) 100%)`) for text legibility — this overlay is constant regardless of site theme.
- Content grid: `max-width:1360px`, 2 columns (`1.1fr 0.9fr`, gap `56px`), stacks to 1 column under 900px.
- **Left column**:
  - Eyebrow pill: "⚡ Obras Eléctricas Industriales · Más de 25 años de trayectoria" (salmon-tinted, `rgba(250,90,54,.14)` bg, `rgba(250,90,54,.4)` border, text `#FFA580`).
  - H1 (Space Grotesk 800, 56px/1.08, white): "Energía que" / "no se detiene." (second line in salmon `#FA5A36`).
  - Paragraph (18px/1.6, `#94A3B8`, max 48ch): trayectoria + service description copy.
- **Right column — Portal access card** (glassmorphism): `background:rgba(15,23,42,.75)`, `backdrop-filter:blur(16px)`, border `rgba(255,255,255,.16)`, `border-radius:20px`, shadow `0 30px 60px rgba(0,0,0,.6), 0 0 40px rgba(250,90,54,.12)`, padding 32px.
  - Header row: shield icon badge (44×44, salmon-tinted) + "Portal Digital BKB" (Space Grotesk 700, 17px, white) + "Gestión Documental & SEC TE1" (12px, `#94A3B8`).
  - Subtext: "Selecciona tu perfil para ingresar al portal." (14px, `#94A3B8`).
  - Two stacked full-width buttons, 16px vertical padding, `border-radius:10px`: **"Soy Cliente →"** (filled salmon, white text) and **"Soy BKB →"** (outline, white text, salmon border on hover). Both should route to the real login flow.
- **Entrance animation**: each direct child (eyebrow, H1, paragraph, card) fades up (`translateY(16px)→0`, opacity 0→1) staggered ~90ms apart on mount.

### 3. Clientes (logo marquee)
- **Purpose**: Trust signal, right after the Hero.
- Centered eyebrow label "CONFÍAN EN BKB" (salmon, `IBM Plex Mono` 12px/600).
- Infinite horizontal marquee: 16 real client logos, each in a `150×84px` white rounded tile (`border-radius:12px`, `padding:16px`, `object-fit:contain`). Render the list twice back-to-back and animate `translateX(0) → translateX(-50%)` over 32s, `linear infinite`, for a seamless loop.
- Client roster: ESVAL, Sopraval, Castaño, Generadora Metropolitana, KSB, Cecinas Venezia, Algas Marinas, Tecfluid, Propal, Ecorriles, MAF, Soldes P, Energías Industriales, IngeFrío, IngenProyect, SHS.
- Section border-top/bottom: `1px solid rgba(255,255,255,.09)` (dark theme) — see theming note below on adapting to light theme borders.

### 4. Servicios ("Qué hacemos")
- Eyebrow "QUÉ HACEMOS" + H2 "Especialidades técnicas" (Space Grotesk 700, 36px, theme text color).
- 4-column grid (2 cols under 900px), gap 22px. Each card: `border-radius:16px`, padding 26px, background/border from theme tokens.
  - 52×52px icon badge (salmon-tinted bg `rgba(250,90,54,.12)`) with a representative icon/photo.
  - Title (16.5px/600), description (13.5px/1.55, muted), 1–2 capability bullets (12.5px, subtle text, salmon `·` marker) below a top divider.
  - Cards: Ingeniería Eléctrica, Automatización & PLC, Obras Civiles Industriales, Mantención & Guardia 24/7.
  - **Animation**: same fade-up reveal as other cards, but staggered by index (`transition-delay: index * 100ms`). On hover: border → salmon-tinted `rgba(250,90,54,.45)`, `translateY(-6px)`, soft salmon shadow `0 16px 32px rgba(250,90,54,.12)`; icon badge scales to 1.08 and lifts `-3px`, background deepens to `rgba(250,90,54,.2)`.

### 5. Métricas (stats band)
- Full-width band, background = page background (theme `--page-bg`, NOT the white/dark card color — it should blend with the page, only delimited by top/bottom 1px borders in the theme's border color).
- 4-column grid, gap 32px: `25+` Años de trayectoria continua · `150+` Proyectos de alta y baja tensión · `40+` Clientes corporativos activos · `100%` Certificaciones SEC aprobadas.
- Big number: Space Grotesk 700, 42px, salmon `#FA5A36`. Label: 14px, muted theme text.
- **Animation**: count up from 0 to target with cubic ease-out over ~1.1s, triggered when the element enters the viewport (IntersectionObserver, threshold 0.4, fires once).

### 6. Mercados
- Eyebrow "SECTORES ESTRATÉGICOS" + H2 "Mercados que atendemos".
- 3-column grid (1 col under 900px). Cards (theme card bg/border, `border-radius:16px`, padding 28px): title (18px/600), description (14px, muted), and a bottom line "Clientes: X · Y · Z" in `IBM Plex Mono` 12px, subtle color, above a top divider.
  - Agroindustria & Alimentos (Sopraval, Castaño, Venezia) · Recursos Hídricos & Sanitaria (ESVAL, KSB, Tecfluid) · Energía & Generación (Generadora Metropolitana).

### 7. Portafolio
- Eyebrow "OBRAS REALES" + H2 "Portafolio de proyectos".
- 3-column grid, cards with a 4:3 photo (real jobsite photos), a floating "SEC TE1 VIGENTE" pill badge (green `rgba(16,185,129,.9)` bg, dark green text, top-left over the photo) and, below, project title (15.5px/600) + spec line in `IBM Plex Mono` 12px.
  - Projects: Ampliación Planta Cecinas Sopraval (450 kVA · Quilpué) · Estación de Bombeo e Impulsión ESVAL (800 kVA · Valparaíso) · Línea de Envasado Alimentos Castaño (Control Siemens S7-1500 · Santiago).
  - Photo hover: `scale(1.06)` zoom, `.5s` cubic-bezier(.16,1,.3,1).

### 8. Portal SEC ("ecosistema digital")
- 2-column layout (stacks under 900px).
- **Left**: eyebrow "ECOSISTEMA DIGITAL" + H2 "El portal que mantiene su faena en regla" + 3 value-prop bullets (semáforo normativo SEC, descarga en terreno de planos, canal de solicitud de documentos).
- **Right**: a fake "app window" mockup — **always styled dark regardless of page theme** (it represents a software screenshot): traffic-light dots, fake URL bar "portal.bkb.cl/obras/sopraval-tdf", and 4 document rows (Certificado TE1 - vigente/green, Plano DWG As-Built, Informe Termográfico, and a greyed-out locked "Presupuesto Interno BKB" row with a 🔒).

### 9. Cotización + Guardia 24/7
- 2-column layout (`0.9fr 1.1fr`, stacks under 900px).
- **Left — Guardia 24/7 card**: always dark (gradient `#162035→#0F172A`, salmon border), "GUARDIA DE URGENCIA 24/7" pill, headline "Parada de planta no programada", phone number as a large tappable link (`tel:+56982491403`, Space Grotesk 700 28px, salmon), office/coverage text.
- **Right — Quote form card**: theme-aware card. Fields: Nombre, Empresa/Razón Social, Correo Corporativo, Teléfono (2×2 grid), a select for "Línea de Requerimiento" (Montaje TDF / Automatización / Trámite TE1 / Mantención), a textarea for job description, and a filled salmon "Enviar Solicitud →" pill button.

### 10. Footer
- Always dark (`#05080E`), regardless of page theme. 4-column grid (stacks responsively): brand blurb, "Especialidades" links, "Plataforma" links (Portal SEC / Acceso Clientes / Acceso Colaboradores), and contact block (Quilpué address, phone, email). Bottom bar: copyright, Términos, Privacidad (Ley 21.719), "Portal de clientes →".

## Interactions & Behavior
- **Theme toggle** (dark/light): a single circular header button flips a global theme flag. All theme-dependent colors are driven by one set of tokens (see below) — Hero, header-not-scrolled, Guardia 24/7 card, Portal SEC mockup window, and Footer are **exempt** and stay permanently dark by design.
- **Header show/hide**: fixed position, off-screen until `scrollY > 40px`, then slides/fades in. Its own light/dark skin follows the current theme (see Header screen spec).
- **Scroll-reveal**: every major content block/card fades up on first entering the viewport (IntersectionObserver, ~15–20% threshold, fires once, `translateY(22px)→0` over `.7s` cubic-bezier(.16,1,.3,1)). Respect `prefers-reduced-motion` (skip animation, show final state immediately).
- **Counters**: animate from 0 on first viewport entry (see Métricas).
- **Marquee**: pure CSS transform loop, no JS needed, pause-on-hover is optional (not currently implemented).
- **Card hovers**: border color → salmon-tinted, lift `translateY`, soft shadow (see each section for exact values).
- **Portal card CTAs** ("Soy Cliente" / "Soy BKB"): currently static links (`href="#"`) — wire to real client vs. staff login routes.

## State Management
- `theme`: `'dark' | 'light'`, toggled by the header button, defaults to `'dark'`.
- `headerScrolled`: boolean, derived from `window.scrollY > 40`.
- No form state/validation was implemented in the prototype — the quote form is presentational only; add real form state + validation + submission handling.
- No client-side routing was implemented — "Soy Cliente"/"Soy BKB"/"Acceso Portal"/nav links are placeholders.

## Design Tokens

### Brand — Naranja-Salmón (constant across both themes)
| Token | Hex | Use |
|---|---|---|
| salmon-500 | `#FA5A36` | Primary action buttons, CTAs, active accents |
| salmon-600 | `#E04825` | Hover of primary buttons |
| salmon-300 | `#FFA580` | Small accents on dark surfaces (eyebrow text, phone-link hover) |
| salmon-soft | `#FFF4EE` | Light theme's page background tint |

### Theme A — Dark (default)
| Token | Value |
|---|---|
| `--page-bg` | `#080C14` |
| `--card-bg` | `#0F172A` |
| `--card-border` | `rgba(255,255,255,0.09)` |
| `--text-main` | `#F8FAFC` |
| `--text-muted` | `#94A3B8` |
| `--text-subtle` | `#64748B` |
| `--input-bg` | `rgba(255,255,255,0.04)` |
| `--input-border` | `rgba(255,255,255,0.16)` |

### Theme B — Light
| Token | Value |
|---|---|
| `--page-bg` | `#FFF4EE` (light salmon tint) |
| `--card-bg` | `#FFFFFF` |
| `--card-border` | `#F5D9C7` |
| `--text-main` | `#1A1513` |
| `--text-muted` | `#7D6F64` |
| `--text-subtle` | `#9A8F86` |
| `--input-bg` | `#FAF6F2` |
| `--input-border` | `#F5D9C7` |

### Elements that ignore the theme toggle (always dark)
Hero background/overlay, un-scrolled header, Guardia 24/7 card, Portal SEC app-window mockup, Footer. These use fixed dark values, not the tokens above.

### Semantic
| Role | Value |
|---|---|
| Success / SEC vigente | `#10B981` text, `rgba(16,185,129,.08–.12)` bg |
| Warning | `#F59E0B` |
| Danger | `#EF4444` |
| Locked/reserved | `#7F7269` |

### Typography
- Display / headings: **Space Grotesk**, weights 600/700/800, tracking -0.01 to -0.02em.
- Body / UI: **IBM Plex Sans**, weights 400/500/600/700.
- Data / codes / mono labels: **IBM Plex Mono**, weights 500/600/700.
- Google Fonts import: `IBM+Plex+Mono:wght@500;600;700`, `IBM+Plex+Sans:wght@400;500;600;700`, `Space+Grotesk:wght@600;700;800`.
- Scale used: H1 56px/1.08, H2 34–36px, card titles 15.5–18px, body 13.5–18px, mono labels 10.5–12px.

### Spacing & Radius
- Content max-width: `1360px`, side padding `40px` (desktop).
- Card radius: `16px` (18px for the two quote-section cards). Pills/buttons: `999px`. Inputs/icon-badges: `10–13px`.
- Section vertical rhythm: `64–96px` top/bottom padding.

### Breakpoints
- `1180px`: collapse header nav/SEC badge/Acceso Portal (icon toggle + logo + Cotizar Obra remain).
- `900px`: 2-col grids → 1 col; 4-col grids → 2 cols.

## Assets
All in `assets/`, copied from the BKB brand kit / real jobsite photography supplied by the client:
- `bkb-logo-final.png` — final approved logo (circular badge, copper checkmark + "BKB" wordmark). Used in header (44px tall) and footer (42px tall).
- `faena-hero.jpg` — hero full-bleed background photo.
- `faena-1.jpg`, `faena-2.jpg`, `faena-3.jpg` — portfolio project photos (a 4th, `faena-4.jpg`, was shot but isn't currently placed — available if a 4th project card is added).
- `electric.png`, `electronic.png`, `civil.jpg`, `maintance.png` — service card icons/imagery.
- `brand-*.{png,jpg}` — 16 real client logos for the marquee (ESVAL, Sopraval, Castaño, Generadora Metropolitana, KSB, Cecinas Venezia, Algas Marinas, Tecfluid, Propal, Ecorriles, MAF, Soldes P, Energías Industriales, IngeFrío, IngenProyect, SHS).

## Files
- `BKB-Landing-reference.dc.html` — the full design reference (structure, inline styles, and interaction logic for every screen described above). Read it top-to-bottom as the source of truth for exact markup order, inline style values, and the JS behavior (theme tokens, scroll listener, IntersectionObserver reveals, counter animation) — just don't ship its templating syntax directly.
