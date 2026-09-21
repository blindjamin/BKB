# 01 · Sistema de Diseño y Tokens BKB (v2)

> **Nota para IAs y diseñadores:**  
> La única fuente de verdad cromática y tipográfica es el paquete `packages/tokens` (`@bkb/tokens`, versión 2.0.0). No inventar colores hexadecimales arbitrarios en componentes o vistas: usar siempre los tokens.
>
> La v1.0 (paleta cobre sobre papel) fue **reemplazada** por el handoff de Claude Design. Lo único que se conserva de ella es el semáforo normativo SEC.

---

## 1. Principios
1. **Salmón como color de marca** (`--bkb-salmon-500` `#FA5A36`), para fondos grandes, acentos y texto sobre fondo oscuro.
2. **Dos temas** con el atributo `data-theme="dark|light"` en `<html>`. La landing es **oscura por defecto**. El portal es **claro por defecto**, con conmutador a oscuro.
3. **Superficies nocturnas fijas** (`--bkb-night-*`) para lo que siempre es oscuro sin importar el tema: hero, tarjeta de guardia, maqueta del portal y footer.
4. **Todo sale de variables CSS.** Los componentes usan variables como `--page-bg` y `--text-main`, nunca colores fijos, para que el tema cambie solo.
5. **Foco visible:** `outline: 3px solid var(--bkb-salmon-500)` con `outline-offset: 2px`.
6. **Contraste WCAG 2.2 AA** (4,5:1 para texto normal). Ver la sección 3.

---

## 2. Paleta

### Marca salmón
| Token | Hex | Uso |
|---|---|---|
| `--bkb-salmon-300` | `#FFA580` | Acentos pequeños sobre oscuro |
| `--bkb-salmon-500` | `#FA5A36` | **Color de marca** |
| `--bkb-salmon-600` | `#E04825` | Hover sobre el color de marca |
| `--bkb-salmon-700` | `#C2410C` | **Botón primario y texto salmón en tema claro** (blanco sobre este color: 5,18:1) |
| `--bkb-salmon-800` | `#9A3412` | Hover del botón primario |
| `--bkb-salmon-soft` | `#FFF4EE` | Fondos suaves |

### Superficies nocturnas (siempre oscuras)
| Token | Hex | Uso |
|---|---|---|
| `--bkb-night-950` | `#05080E` | Footer |
| `--bkb-night-900` | `#080C14` | Fondo oscuro y overlay del hero |
| `--bkb-night-800` | `#0F172A` | Tarjetas oscuras |
| `--bkb-night-700` | `#162035` | Barra de la maqueta y degradado de guardia |

### Tinta y neutros cálidos (tema claro)
`--bkb-ink-900` `#1A1513` · `--bkb-sand-600` `#7D6F64` · `--bkb-sand-500` `#9A8F86` · `--bkb-sand-300` `#F5D9C7` · `--bkb-paper-100` `#FAF6F2`

### Semánticos
`--bkb-success` `#10B981` · `--bkb-warning` `#F59E0B` · `--bkb-danger` `#EF4444` · `--bkb-locked` `#7F7269`

### Semáforo normativo SEC (lo usará el portal)
| Estado | Texto | Fondo | Borde |
|---|---|---|---|
| Vigente (`ok`) | `#1E6B47` | `#E6F4EC` | `#C3E6D2` |
| Por vencer (`warning`) | `#B85D0A` | `#FEF3E6` | `#FBD6B0` |
| Vencido (`danger`) | `#A8271B` | `#FDEEED` | `#F7C6C2` |
| Trámite SEC (`info`) | `#1B5887` | `#EBF3F9` | `#CBE0F0` |
| Reservado BKB (`reserved`) | `#7F7269` | `#F0EAE3` | `#DED5CC` |

Tokens: `--bkb-sec-{ok|warning|danger|info|reserved}-{text|bg|border}`.

---

## 3. Temas y contraste

Variables por tema (definidas en `src/themes.css`):

| Variable | Oscuro | Claro |
|---|---|---|
| `--page-bg` | `#080C14` | `#FFF4EE` |
| `--card-bg` | `#0F172A` | `#FFFFFF` |
| `--card-border` | `rgba(255,255,255,0.09)` | `#F5D9C7` |
| `--text-main` | `#F8FAFC` | `#1A1513` |
| `--text-muted` | `#94A3B8` | `#7D6F64` |
| `--text-subtle` | `#8391A7` | `#7D6F64` |
| `--input-bg` | `rgba(255,255,255,0.04)` | `#FAF6F2` |
| `--input-border` | `rgba(255,255,255,0.16)` | `#F5D9C7` |
| `--accent-text` | `--bkb-salmon-500` | `--bkb-salmon-700` |

**Reglas de contraste (decisión D3 del rediseño):**
- El texto blanco sobre `salmon-500` (3,19:1) **no cumple AA** en tamaños normales. Para botones y texto pequeño usar `salmon-700`.
- El texto salmón pequeño en tema claro usa `salmon-700` (`--accent-text` ya lo hace).
- Cualquier valor nuevo se verifica con una herramienta de contraste antes de fijarlo.

---

## 4. Tipografía y medidas

| Rol | Familia | Pesos |
|---|---|---|
| Títulos y números | `Space Grotesk` (`--bkb-font-display`) | 600, 700, 800 |
| Lectura y formularios | `IBM Plex Sans` (`--bkb-font-sans`) | 400, 500, 600, 700 |
| Códigos, RUT, SEC TE1 y mediciones | `IBM Plex Mono` (`--bkb-font-mono`) | 500, 600, 700 |

- **H1:** `clamp(2.25rem, 1.2rem + 4.2vw, 3.5rem)` (56 px en escritorio). **H2:** `clamp(1.75rem, 1.2rem + 1.8vw, 2.25rem)`.
- **Cuerpo:** 18, 15, 14 y 13,5 px. **Mono:** 12 y 10,5 px.
- **Radios:** tarjeta 16 px, tarjeta grande 18 px, campo 10 px, pastilla 999 px.
- **Contenedor:** 1360 px con márgenes laterales de 40 px.

---

## 5. Cómo usarlo
- **Sitio (`apps/web`):** `global.css` importa `@import "@bkb/tokens";` y mapea las variables a utilidades de Tailwind con `@theme inline` (`bg-page`, `text-main`, `bg-salmon-500`…).
- **Portal (`apps/portal`):** CSS propio, sin Tailwind. Como App Platform despliega solo `apps/portal`, los tokens se **copian** a `apps/portal/static/tokens/` con un comando documentado en su README, y se versionan.
