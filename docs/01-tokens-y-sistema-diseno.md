# 01 · Sistema de Diseño y Tokens BKB (v2)

> **Nota para IAs y diseñadores:**  
> La única fuente de verdad cromática y tipográfica es el paquete `packages/tokens` (`@bkb/tokens`, versión 2.0.0). No inventar colores hexadecimales arbitrarios en componentes o vistas: usar siempre los tokens.
>
> La v1.0 (paleta cobre sobre papel) fue **reemplazada** por el handoff de Claude Design. Lo único que se conserva de ella es el semáforo normativo SEC.

---

## 1. Principios
1. **Salmón como color de marca** (`--bkb-salmon-500` `#FA5A36`), para fondos grandes, acentos y texto sobre fondo oscuro.
2. **Dos temas** con el atributo `data-theme="dark|light"` en `<html>`. La landing es **oscura por defecto**. El portal es **claro por defecto**, con conmutador a oscuro.
3. **Superficies nocturnas fijas** (`--bkb-night-*`) para lo que siempre es oscuro sin importar el tema: overlay del hero, tarjetas de servicios con foto, maqueta del portal y footer.
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
| `--bkb-salmon-600` | `#E04825` | Ya no se usa en el sitio (los hovers pasaron a `salmon-700`) |
| `--bkb-salmon-700` | `#C2410C` | **Botón primario, texto salmón en tema claro y hover de botones** (blanco sobre este color: 5,18:1) |
| `--bkb-salmon-800` | `#9A3412` | Hover del botón primario (`PillButton`) |
| `--bkb-salmon-soft` | `#FDF1E8` | Fondos suaves (igual al fondo del tema claro) |

**Regla de uso en el sitio (sesión 9):** tres tonos con rol fijo: `500` para botones y marca, `700` para texto, enlaces y hovers en tema claro, `300` para acentos sobre fondo oscuro. En tema claro el salmón fuerte queda reservado para lo accionable (botones, enlaces, teléfono); los bordes de tarjetas son neutros.

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
`--bkb-success` `#C2410C` · `--bkb-warning` `#F59E0B` · `--bkb-danger` `#EF4444` · `--bkb-locked` `#7F7269`

- `--bkb-success` pasó de verde (`#10B981`) a naranjo (`#C2410C`, igual a `salmon-700`) a pedido del usuario (sesión 9). En el sitio solo lo usa la etiqueta "SEC TE1 VIGENTE" del portafolio. **Ojo al copiar los tokens al portal:** allí "éxito" dejaría de verse verde.
- `success`, `warning` y `danger` están registrados en `@theme` de `apps/web/src/styles/global.css` (`bg-danger`, `text-warning`…). Antes `danger` y `warning` no lo estaban y esas clases no pintaban nada.

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
| `--page-bg` | `#18181A` (negro carbón) | `#FDF1E8` (durazno tenue) |
| `--page-gradient` | Degradado carbón `#2A2A2D` → `#1B1B1D` → `#131314` con brillo salmón tenue arriba a la derecha | `none` |
| `--card-bg` | `#232326` | `#FFFAF6` |
| `--card-border` | `rgba(255,255,255,0.1)` | `#E8DCD2` (neutro cálido) |
| `--text-main` | `#F8FAFC` | `#1A1513` |
| `--text-muted` | `#A1A1AA` (gris neutro) | `#6B5D52` |
| `--text-subtle` | `#8E8E96` | `#6B5D52` |
| `--input-bg` | `rgba(255,255,255,0.04)` | `#FFFDFB` |
| `--input-border` | `rgba(255,255,255,0.16)` | `#DDCFC3` |
| `--accent-text` | `--bkb-salmon-500` | `--bkb-salmon-700` (4,7:1 sobre `#FDF1E8`) |

- **Historial:** hasta la sesión 8 el tema oscuro era casi negro azulado (`#080C14`, tarjetas `#0F172A`) y el claro `#FFF4EE` con tarjetas blancas. En la sesión 9 se probó un azul noche (`#121A2A`) y el usuario eligió el negro carbón.
- **Degradado de fondo:** `body` aplica `background-image: var(--page-gradient)` con `background-attachment: fixed`, así todas las secciones comparten un fondo continuo. Por eso las secciones **no** deben llevar `bg-page` propio (lo taparía).
- Los grises del tema oscuro son neutros (sin tinte azul) para combinar con el carbón. Los componentes con colores oscuros propios (tarjeta del portal en el hero, aviso de emergencia) usan el mismo carbón en degradado.

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
