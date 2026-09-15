# 08 · Plan de Desarrollo: Rediseño del Sitio según Handoff de Claude Design

> **Para el modelo que ejecute este plan:**
> Lee este documento completo antes de tocar código. Ejecuta las fases en orden, una rama y un commit por fase como mínimo, y marca las casillas `[ ]` a medida que avanzas.
> Si una **Decisión** (sección 2) no está confirmada por el usuario, usa la opción marcada como **(Recomendada)** y déjalo anotado en el PR.
> No inventes colores, textos ni datos: la fuente de verdad es la referencia del handoff (sección 1) y lo que este plan indique explícitamente.

---

## 0. Resumen

| | Estado actual (`apps/web`) | Objetivo (handoff) |
|---|---|---|
| Estructura | 8 páginas separadas | Landing de una página con anclas + páginas legales/empleo |
| Paleta | Cobre `#B4470F` sobre papel claro `#FBF8F5` (UI Kit v1.0) | Salmón `#FA5A36`, tema **oscuro por defecto** + tema claro conmutable |
| Header | Sticky, siempre visible, se rompe entre 1024–1240 px | Fijo, oculto sobre el hero y aparece al hacer scroll (> 40 px) |
| Movimiento | Ninguno | Revelado al hacer scroll, contadores, carrusel de logos, zoom del hero |
| Contenido | Obras y datos de relleno | Clientes reales (16 logos), 3 obras con nombre, teléfono real |

**Stack que se mantiene:** Astro 5 (salida estática), Tailwind CSS v4, `@bkb/tokens`, helper `getPath` para GitHub Pages. **No** introducir React ni otro framework: cada sección es un componente `.astro` y la interactividad es un script vanilla pequeño.

---

## 1. Referencia de diseño

La referencia está versionada en el repo:

```
docs/design/handoff-landing/
├── BKB-Landing-reference.dc.html   ← fuente de verdad (marcado, estilos inline, datos y lógica)
├── README.md                       ← especificación escrita por Claude Design (medidas, tokens, comportamiento)
├── support.js                      ← shim local para poder abrir la referencia (NO es parte del diseño)
└── assets/                         ← 28 imágenes (logo, fotos, íconos, 16 logos de clientes)
```

### 1.1 Cómo abrir la referencia en el navegador

El archivo usa una sintaxis de plantillas propia de Claude Design (`{{ }}`, `<sc-for>`, `<x-dc>`). El archivo `support.js` es un intérprete mínimo escrito para visualizarla fuera de esa herramienta. Necesita servirse por HTTP (no funciona con `file://`):

```bash
python -m http.server 8765 --directory docs/design/handoff-landing
```

- Tema oscuro: `http://localhost:8765/BKB-Landing-reference.dc.html`
- Tema claro: `http://localhost:8765/BKB-Landing-reference.dc.html?theme=light`

> ⚠️ **Nunca** copies a `apps/web` la sintaxis `{{ }}`, `<sc-for>`, `<x-dc>`, `style-hover`, ni el `support.js`. Son solo para mirar.

### 1.2 Mapa sección → líneas de la referencia → componente destino

| # | Sección | Líneas en `.dc.html` | Componente Astro destino |
|---|---|---|---|
| 1 | Header | 56–78 | `src/components/site/SiteHeader.astro` |
| 2 | Hero + tarjeta de acceso al portal | 81–120 | `src/components/landing/Hero.astro` |
| 3 | Carrusel de clientes | 123–136 | `src/components/landing/ClientsMarquee.astro` |
| 4 | Servicios ("Qué hacemos") | 139–161 | `src/components/landing/Services.astro` |
| 5 | Métricas | 164–173 | `src/components/landing/Stats.astro` |
| 6 | Mercados | 176–191 | `src/components/landing/Markets.astro` |
| 7 | Portafolio | 194–214 | `src/components/landing/Portfolio.astro` |
| 8 | Portal SEC (maqueta de app) | 217–263 | `src/components/landing/PortalShowcase.astro` |
| 9 | Cotización + Guardia 24/7 | 266–299 | `src/components/landing/QuoteSection.astro` |
| 10 | Footer | 302–336 | `src/components/site/SiteFooter.astro` |
| — | Estilos globales y keyframes | 15–50 | `src/styles/global.css` |
| — | Datos (servicios, métricas, mercados, obras, clientes, opciones) | 359–407 | `src/data/landing.ts` |
| — | Lógica (tema, reveal, contadores, header) | 346–357, 411–464 | `src/scripts/motion.ts` + `src/scripts/theme.ts` |

El README del handoff (sección "Screens / Views") trae los valores exactos de cada sección. Úsalo junto con la tabla.

---

## 2. Decisiones a confirmar con el usuario

Cada decisión tiene una opción **(Recomendada)**, que es la que asume el resto del plan. Si el usuario elige otra, ajusta las fases indicadas.

### D1 · Estructura de rutas
- **(Recomendada) A:** `/` pasa a ser la landing con anclas (`#mercados`, `#servicios`, `#obras`, `#portal`, `#cotizar`). Se conservan con el nuevo estilo `/trabaja-con-nosotros`, `/privacidad` y `/terminos`. Las rutas `/servicios`, `/obras`, `/nosotros` y `/contacto` se eliminan y **redirigen** a su ancla, para no romper enlaces ya compartidos.
- B: Conservar las 8 páginas y solo aplicarles el nuevo estilo (la landing sería `/` y el resto seguiría existiendo).
- *Afecta:* Fase 7.

### D2 · Sistema de diseño
- **(Recomendada) A:** El handoff reemplaza al UI Kit v1.0. `@bkb/tokens` sube a **v2.0.0** con la paleta salmón y los dos temas. Los tokens del semáforo SEC (`--bkb-sec-*`) se **conservan**, porque los usará el portal Django.
- B: Mantener cobre/papel y adaptar el handoff a esa paleta (se pierde fidelidad).
- *Afecta:* Fase 1 y `docs/01-tokens-y-sistema-diseno.md`.

### D3 · Contraste de color (WCAG 2.2 AA)
El proyecto declara cumplir WCAG 2.2 AA, pero varios pares de colores del handoff no llegan al mínimo de 4.5:1 para texto normal (medido):

| Par | Contraste | ¿AA texto normal? |
|---|---|---|
| Blanco sobre `#FA5A36` (botones de 14–15 px) | 3.19 | ❌ |
| Blanco sobre `#E04825` (hover) | 4.10 | ❌ |
| `#FA5A36` sobre `#FFF4EE` (eyebrows, tema claro) | 2.95 | ❌ |
| `#9A8F86` sobre `#FFFFFF` (texto sutil, tema claro) | 3.16 | ❌ |
| `#64748B` sobre `#0F172A` (texto sutil, tema oscuro) | 3.75 | ❌ |
| `#64748B` sobre `#05080E` (enlaces del footer) | 4.21 | ❌ |
| `#10B981` sobre `#FFFFFF` (badge SEC, tema claro) | 2.54 | ❌ |
| `#FA5A36` sobre `#080C14` (eyebrows, tema oscuro) | 6.13 | ✅ |
| `#94A3B8` sobre `#0F172A` (texto secundario, oscuro) | 6.96 | ✅ |

- **(Recomendada) A:** Mantener `#FA5A36` como color de marca para fondos grandes, acentos y texto sobre fondo oscuro, y agregar tokens accesibles para los casos que fallan:
  - Botones primarios: fondo `--bkb-salmon-700: #C2410C` y hover `--bkb-salmon-800: #9A3412` (blanco sobre `#C2410C` = 5.18 ✅).
  - Texto salmón pequeño en tema claro: `#C2410C` (4.79 sobre `#FFF4EE` ✅).
  - Texto sutil: subir a `#8391A7` en oscuro y a `#7D6F64` en claro. **Verificar cada valor final con una herramienta de contraste antes de fijarlo.**
  - Badge SEC en tema claro: texto `#047857` sobre `rgba(16,185,129,.12)`.
- B: Fidelidad exacta al handoff, aceptando el incumplimiento (anotarlo en `docs/04-seguridad-y-cumplimiento.md`).
- *Afecta:* Fase 1.

### D4 · Envío del formulario de cotización
El sitio es estático y el portal Django todavía no tiene endpoint.
- **(Recomendada) A:** Formulario con `method="post"` y `action` tomado de la variable de entorno `PUBLIC_QUOTE_ENDPOINT`. Si la variable está vacía, el botón queda deshabilitado y se muestra el aviso "Formulario en habilitación. Escríbenos a contacto@bkb.cl o llama al +56 9 8249 1403". **Nunca** debe quedar un `<form>` sin `method`, porque hace un GET con datos personales en la URL (pendiente #1 del doc 07).
- B: Integrar un servicio externo de formularios (requiere aprobar el proveedor por la Ley 21.719).
- *Afecta:* Fase 5, tarea 5.4.

### D5 · Destino de los botones del portal
"Soy Cliente", "Soy BKB", "Acceso Portal", "Acceso Clientes", "Acceso Colaboradores".
- **(Recomendada) A:** Centralizar en `src/config/site.ts` con `PUBLIC_PORTAL_URL` (por defecto `https://portal.bkb.cl`):
  - Cliente → `${PORTAL_URL}/accounts/login/?perfil=cliente`
  - BKB/colaborador → `${PORTAL_URL}/accounts/login/?perfil=colaborador`
- *Afecta:* Fases 2, 3, 4 y 5.

### D6 · Navegación bajo 1180 px
El handoff oculta el menú bajo 1180 px **sin ofrecer alternativa**: en tablet y móvil no hay forma de navegar.
- **(Recomendada) A:** Agregar un botón hamburguesa (44×44 px, junto al conmutador de tema) que abre un panel con los mismos enlaces, "Acceso Portal" y "Cotizar Obra". Se cierra con Escape, al tocar un enlace o al tocar fuera.
- B: Fidelidad exacta (sin menú móvil).
- *Afecta:* Fase 3.

### D7 · Contenido que el usuario debe validar antes de publicar
Estos puntos **no bloquean el desarrollo**. Implementa con lo que trae el handoff y deja la lista en el PR:
- [ ] **Fotos de faena** (`faena-hero.jpg`, `faena-1..4.jpg`): el README dice que son fotos reales, pero parecen de banco de imágenes. Confirmar origen y licencia.
- [ ] **`faena-4.jpg` es inutilizable:** es una captura de pantalla con el aviso del navegador "Pulsa F11 para salir del modo de pantalla completa". No usarla.
- [ ] **`civil.jpg`** es un dibujo de casco y lentes. En el handoff solo se usa como ícono de 52 px (aceptable), no como foto.
- [ ] **Logos de 16 clientes:** confirmar autorización comercial para mostrarlos.
- [ ] **Legibilidad del logo:** `bkb-logo-final.png` es un sello circular con texto pequeño. A 44 px de alto (header) el texto "BKB" e "Ingeniería Eléctrica & Servicios" no se lee; en la referencia se ve como un círculo oscuro. Pedir una versión horizontal o solo isotipo + "BKB" para el header, idealmente en SVG.
- [ ] **Nombre de la empresa:** el logo nuevo dice "Ingeniería Eléctrica & Servicios", pero la documentación y la metadata dicen "Obras Eléctricas & Servicios". Definir cuál va en `<title>`, Schema.org y footer.
- [ ] **Métricas:** 150+ proyectos, 40+ clientes y 100 % de certificaciones aprobadas.
- [ ] **Obras:** Sopraval 450 kVA (Quilpué), ESVAL 800 kVA (Valparaíso) y Castaño con S7-1500 (Santiago).
- [ ] **Datos de contacto:** teléfono `+56 9 8249 1403`, oficina en Quilpué y `contacto@bkb.cl`. El handoff resuelve el pendiente #3 del doc 07, pero hay que confirmarlo.

---

## 3. Arquitectura objetivo

```
packages/tokens/src/
├── colors.css          ← REESCRIBIR: marca salmón, superficies nocturnas fijas, semánticos, SEC (conservar)
├── themes.css          ← NUEVO: variables por tema en [data-theme="dark"] / [data-theme="light"]
├── typography.css      ← AJUSTAR: escala del handoff
└── index.css           ← importar themes.css; radios, foco, contenedor

apps/web/src/
├── config/site.ts              ← NUEVO: teléfono, email, dirección, URLs del portal, endpoint del formulario
├── data/landing.ts             ← NUEVO: servicios, métricas, mercados, portafolio, clientes, opciones de cotización
├── assets/                     ← NUEVO: imágenes optimizables con astro:assets
│   ├── brand/bkb-logo.png
│   ├── landing/faena-hero.jpg, faena-1.jpg, faena-2.jpg, faena-3.jpg
│   ├── icons/electric.png, electronic.png, civil.jpg, maintance.png
│   └── clients/esval.png … shs.jpg   (16 archivos)
├── layouts/Layout.astro        ← REESCRIBIR: fuentes, script de tema anti-parpadeo, metadata, prop headerMode
├── components/
│   ├── site/SiteHeader.astro   ← NUEVO (reemplaza Header.astro)
│   ├── site/MobileNav.astro    ← NUEVO (D6)
│   ├── site/ThemeToggle.astro  ← NUEVO
│   ├── site/SiteFooter.astro   ← NUEVO (reemplaza Footer.astro)
│   ├── ui/Eyebrow.astro, SectionHeading.astro, PillButton.astro, Card.astro
│   └── landing/Hero.astro, ClientsMarquee.astro, Services.astro, Stats.astro,
│       Markets.astro, Portfolio.astro, PortalShowcase.astro, QuoteSection.astro
├── scripts/theme.ts            ← NUEVO: conmutador de tema + persistencia
├── scripts/motion.ts           ← NUEVO: reveal, entrada del hero, contadores, header al hacer scroll
├── styles/global.css           ← REESCRIBIR: @theme de Tailwind mapeado a tokens, keyframes, utilidades
└── pages/
    ├── index.astro             ← REESCRIBIR: compone las 8 secciones
    ├── trabaja-con-nosotros.astro, privacidad.astro, terminos.astro  ← REESTILIZAR
    └── 404.astro               ← NUEVO
```

**Se eliminan al final (Fase 7):** `components/Header.astro`, `components/Footer.astro`, `components/Button.astro`, `pages/servicios.astro`, `pages/obras.astro`, `pages/nosotros.astro`, `pages/contacto.astro` y las imágenes de `public/assets/images/` que ya no se usen.

### 3.1 Mecanismo de tema
- Atributo `data-theme="dark|light"` en `<html>`. Por defecto `dark`.
- Script **inline y bloqueante** en `<head>` (antes de pintar) que lee `localStorage['bkb-theme']`, envuelto en `try/catch`, y fija el atributo. Así se evita el parpadeo de tema al cargar.
- Todas las superficies usan variables CSS (`--page-bg`, `--card-bg`, etc.). Tailwind las consume vía `@theme inline`, sin colores hex arbitrarios en los componentes.
- **Siempre oscuros** (ignoran el tema): el hero, el header sin scroll, la tarjeta de Guardia 24/7, la maqueta del Portal SEC y el footer. Usan tokens fijos `--bkb-night-*`.

### 3.2 Reglas que aplican a todas las fases
1. Todo enlace interno y todo asset pasa por `getPath()`. En páginas distintas de `/`, las anclas se construyen como `` `${getPath('/')}#servicios` ``.
2. Prohibido usar clases con hex arbitrario (`bg-[#FA5A36]`). Usar utilidades mapeadas a tokens (`bg-salmon-500`, `bg-page`, `text-muted`…). Esto resuelve el pendiente #10 del doc 07.
3. El contenido debe verse **sin JavaScript**. Las clases que ocultan elementos para animarlos (`.reveal`, `.hero-in`) solo aplican bajo `html.js`, y el script de `<head>` agrega la clase `js`.
4. Respetar `prefers-reduced-motion: reduce`: sin animaciones, estado final inmediato.
5. Toda imagen decorativa lleva `alt=""`, y toda imagen con contenido, un `alt` descriptivo.
6. Emojis del handoff (⚡ 🛡 🔒 ☀ ☾): reemplazarlos por SVG inline con `aria-hidden="true"`, porque el emoji se ve distinto en cada sistema operativo. El texto accesible va en `aria-label`.
7. Validar `npm run build:web` al terminar cada fase.

---

## 4. Fases de ejecución

### Fase 0 · Preparación
- [ ] **0.1** Confirmar que `benjamin/2026-09-15-revision-frontend-web` ya se fusionó en `desarrollo` (contiene la bitácora, el fix de `requirements.txt` y los docs 07/08). Si no, pedir al usuario que haga el merge primero.
- [ ] **0.2** Crear la rama desde `desarrollo` actualizado, según `docs/05-git-workflow.md`:
  ```bash
  git checkout desarrollo && git pull origin desarrollo
  git checkout -b benjamin/AAAA-MM-DD-rediseno-landing
  ```
- [ ] **0.3** Abrir la referencia (sección 1.1) en oscuro y claro, a 1360, 1180, 900 y 375 px. Tomar capturas como línea base de comparación.
- [ ] **0.4** Verificar que el build actual pasa: `npm run build:web`.

**Criterio de aceptación:** rama creada, referencia visible y build en verde.

---

### Fase 1 · Tokens v2 y estilos globales
**Archivos:** `packages/tokens/src/*`, `packages/tokens/package.json`, `apps/web/src/styles/global.css`

- [ ] **1.1** Reescribir `colors.css` con este contenido base (ajustar los tokens accesibles según D3):
  ```css
  :root {
    /* Marca salmón (constante en ambos temas) */
    --bkb-salmon-300: #FFA580;  /* acentos pequeños sobre oscuro */
    --bkb-salmon-500: #FA5A36;  /* color de marca */
    --bkb-salmon-600: #E04825;
    --bkb-salmon-700: #C2410C;  /* D3: botón primario / texto salmón en claro */
    --bkb-salmon-800: #9A3412;  /* D3: hover botón primario */
    --bkb-salmon-soft: #FFF4EE;

    /* Superficies nocturnas fijas (hero, guardia, maqueta portal, footer) */
    --bkb-night-950: #05080E;   /* footer */
    --bkb-night-900: #080C14;   /* fondo oscuro / overlay hero */
    --bkb-night-800: #0F172A;   /* tarjetas oscuras */
    --bkb-night-700: #162035;   /* barra de maqueta / degradado guardia */

    /* Semánticos */
    --bkb-success: #10B981;
    --bkb-warning: #F59E0B;
    --bkb-danger:  #EF4444;
    --bkb-locked:  #7F7269;

    /* Tinta y neutros cálidos (tema claro) */
    --bkb-ink-900: #1A1513;
    --bkb-sand-600: #7D6F64;
    --bkb-sand-500: #9A8F86;
    --bkb-sand-300: #F5D9C7;
    --bkb-paper-100: #FAF6F2;

    /* Semáforo normativo SEC: CONSERVAR los --bkb-sec-* actuales sin cambios (los usa el portal) */
  }
  ```
- [ ] **1.2** Crear `themes.css` con las variables de ambos temas, copiadas **exactas** de la referencia (líneas 350–351) y ajustadas por D3:
  ```css
  :root, [data-theme="dark"] {
    color-scheme: dark;
    --page-bg: #080C14; --card-bg: #0F172A; --card-border: rgba(255,255,255,0.09);
    --text-main: #F8FAFC; --text-muted: #94A3B8; --text-subtle: #64748B; /* D3: subir subtle */
    --input-bg: rgba(255,255,255,0.04); --input-border: rgba(255,255,255,0.16);
    --accent-text: var(--bkb-salmon-500);
  }
  [data-theme="light"] {
    color-scheme: light;
    --page-bg: #FFF4EE; --card-bg: #FFFFFF; --card-border: #F5D9C7;
    --text-main: #1A1513; --text-muted: #7D6F64; --text-subtle: #9A8F86; /* D3: subir subtle */
    --input-bg: #FAF6F2; --input-border: #F5D9C7;
    --accent-text: var(--bkb-salmon-700);
  }
  ```
- [ ] **1.3** Ajustar `typography.css`: familias iguales y escala del handoff. H1 56 px, pero **fluido**: `clamp(2.25rem, 1.2rem + 4.2vw, 3.5rem)`. H2 36 px como `clamp(1.75rem, 1.2rem + 1.8vw, 2.25rem)`. Cuerpo 18/15/14/13.5 px. Mono de 10.5 a 12 px.
- [ ] **1.4** En `index.css`: importar `themes.css` y definir radios (`--bkb-radius-card: 16px`, `--bkb-radius-card-lg: 18px`, `--bkb-radius-input: 10px`, `--bkb-radius-pill: 999px`), el foco (`outline: 3px solid var(--bkb-salmon-500); outline-offset: 2px`), `--bkb-container: 1360px` y `--bkb-gutter: 40px`.
- [ ] **1.5** Subir la versión a `2.0.0` en `packages/tokens/package.json` y actualizar su descripción y el `README.md` del paquete.
- [ ] **1.6** Reescribir `apps/web/src/styles/global.css`:
  - Quitar el `@import` de Google Fonts (pasa a `<link>` en el Layout, Fase 2).
  - `@import "tailwindcss"; @import "@bkb/tokens";`
  - `@theme inline { … }` mapeando utilidades: `--color-page: var(--page-bg)`, `--color-card`, `--color-card-border`, `--color-main`, `--color-muted`, `--color-subtle`, `--color-input`, `--color-input-border`, `--color-salmon-300/500/600/700/800`, `--color-night-700/800/900/950`, `--color-success`; `--font-display`, `--font-sans`, `--font-mono`; `--radius-card`, `--radius-pill`.
  - Keyframes `heroZoom`, `pulseDot` y `marqueeScroll`, y las clases `.reveal`, `.hero-in` y `.is-visible` (referencia, líneas 20–30), **anidadas bajo `html.js`**.
  - Bloque `@media (prefers-reduced-motion: reduce)` (referencia, línea 39).
  - `::selection { background: var(--bkb-salmon-500); color: #fff; }`
  - Mantener temporalmente las clases antiguas (`.btn`, `.card-bkb`, `.display-*`…) hasta la Fase 7, para no romper las páginas que aún no se migran.

**Criterio de aceptación:** build en verde. Cambiar `data-theme` a mano en DevTools altera `bg-page` y `text-main`. Ningún `--bkb-sec-*` se eliminó.
**Commit:** `feat(tokens): sistema de diseño v2 con paleta salmón y temas oscuro/claro`

---

### Fase 2 · Layout, configuración, datos y tema
**Archivos:** `src/layouts/Layout.astro`, `src/config/site.ts`, `src/data/landing.ts`, `src/scripts/theme.ts`, `src/components/site/ThemeToggle.astro`, `.env.example`

- [ ] **2.1** Crear `src/config/site.ts`:
  ```ts
  export const SITE = {
    name: 'BKB Obras Eléctricas & Servicios',        // D7: confirmar nombre
    phoneDisplay: '+56 9 8249 1403',
    phoneHref: 'tel:+56982491403',
    email: 'contacto@bkb.cl',
    office: 'Quilpué, Región de Valparaíso',
    coverage: 'Valparaíso y Región Metropolitana',
  } as const;
  const PORTAL = import.meta.env.PUBLIC_PORTAL_URL || 'https://portal.bkb.cl';
  export const PORTAL_URLS = {
    home: PORTAL,
    cliente: `${PORTAL}/accounts/login/?perfil=cliente`,
    colaborador: `${PORTAL}/accounts/login/?perfil=colaborador`,
  } as const;
  export const QUOTE_ENDPOINT = import.meta.env.PUBLIC_QUOTE_ENDPOINT || '';
  ```
  Agregar `.env.example` en `apps/web` con `PUBLIC_PORTAL_URL=` y `PUBLIC_QUOTE_ENDPOINT=`.
- [ ] **2.2** Crear `src/data/landing.ts` copiando **literalmente** los arreglos de la referencia (líneas 359–407): `stats`, `mercados`, `servicios`, `portafolio`, `brands` (sin duplicar; la duplicación del carrusel se hace en el componente) y `quoteOptions`. Tipar cada arreglo con interfaces. Las rutas de imagen pasan a ser **imports** de `src/assets/…` (ver Fase 8).
- [ ] **2.3** Reescribir `Layout.astro`:
  - Props: `title`, `description?`, `headerMode?: 'reveal' | 'solid'` (por defecto `'solid'`; la landing usa `'reveal'`).
  - `<html lang="es" data-theme="dark">`.
  - En `<head>`, primero un `<script is:inline>` de 3 líneas: agrega la clase `js` a `<html>`, lee `localStorage['bkb-theme']` con `try/catch` y fija `data-theme`.
  - `<link rel="preconnect">` a `fonts.googleapis.com` y `fonts.gstatic.com` (con `crossorigin`), más la hoja de fuentes con los pesos del README: Mono 500/600/700, Sans 400/500/600/700, Grotesk 600/700/800, con `display=swap`.
  - `<meta name="theme-color">` con `#080C14`.
  - Conservar canonical, Open Graph y el enlace para saltar al contenido.
  - Actualizar Schema.org con `SITE`: `telephone: '+56-9-8249-1403'` y `address` con `addressLocality: 'Quilpué'` y `addressRegion: 'Valparaíso'`.
  - Body: `bg-page text-main font-sans`.
  - Renderizar `<SiteHeader mode={headerMode} />`, `<main id="main-content">` y `<SiteFooter />`.
- [ ] **2.4** `ThemeToggle.astro`: `<button type="button">` circular de 38×38 px (referencia, línea 73) con un SVG de sol y otro de luna, `aria-label` dinámico ("Cambiar a tema claro" / "Cambiar a tema oscuro") y `title`.
- [ ] **2.5** `src/scripts/theme.ts`: al hacer clic en `[data-theme-toggle]`, alterna `document.documentElement.dataset.theme`, lo guarda en `localStorage` (con `try/catch`) y actualiza el `aria-label`. Soportar varios botones (header y menú móvil).

**Criterio de aceptación:** al recargar se mantiene el tema elegido sin parpadeo. Con JS desactivado, la página se ve en tema oscuro y completa.
**Commit:** `feat(web): layout v2 con sistema de temas, configuración de sitio y datos de la landing`

---

### Fase 3 · Header y footer
**Archivos:** `src/components/site/SiteHeader.astro`, `MobileNav.astro`, `SiteFooter.astro`, `src/scripts/motion.ts` (parte del header)

- [ ] **3.1** `SiteHeader.astro` (referencia, líneas 56–78, y README §1):
  - `position: fixed`, contenedor de 1360 px, `padding: 14px 40px` (bajar a 16 px de lateral bajo 640 px), `gap: 24px`, sin salto de línea.
  - Izquierda: logo de 44 px de alto + badge "SEC CLASE A" (oculto bajo 1180 px).
  - Centro: Inicio, Mercados, Servicios, Obras, Portal SEC, Contacto (oculto bajo 1180 px). En la landing los `href` son anclas; en otras páginas, `` `${getPath('/')}#ancla` ``.
  - Derecha: ThemeToggle, "Acceso Portal" (oculto bajo 1180 px, apunta a `PORTAL_URLS.home`) y "Cotizar Obra" (siempre visible, `white-space: nowrap`, apunta a `#cotizar`).
  - Pieles según tema y scroll: copiar exacto de la referencia, líneas 32–36, y del README §1.
  - **Modo `reveal`** (landing): empieza con `opacity: 0; transform: translateY(-100%)` y aparece al pasar `scrollY > 40`. **Accesibilidad:** si recibe foco (`focusin`) también se muestra, y mientras está oculto lleva `visibility: hidden`, aplicado al terminar la transición para que el foco del teclado no caiga en enlaces invisibles.
  - **Modo `solid`** (páginas internas): siempre visible con la piel "scrolled" del tema actual, y el `<main>` recibe `padding-top` igual a la altura del header.
- [ ] **3.2** `MobileNav.astro` (D6): botón hamburguesa visible bajo 1180 px, con `aria-expanded` y `aria-controls`. Panel a pantalla completa bajo 640 px o lateral en tablet, con fondo `--card-bg`, los 6 enlaces, "Acceso Portal" y "Cotizar Obra". Se cierra con Escape, al tocar un enlace o al tocar fuera. El foco vuelve al botón al cerrar.
- [ ] **3.3** `SiteFooter.astro` (referencia, líneas 302–336): siempre oscuro (`bg-night-950`) y grilla `1.3fr 1fr 1fr 1fr`. Pasa a 2 columnas bajo 900 px y a 1 bajo 560 px. Enlaces:
  - Especialidades → `#servicios`.
  - Plataforma → `#portal`, `PORTAL_URLS.cliente` y `PORTAL_URLS.colaborador`.
  - Contacto con datos de `SITE`.
  - Barra inferior: © con año dinámico, Términos → `getPath('/terminos')`, Privacidad (Ley 21.719) → `getPath('/privacidad')`, "Portal de clientes →" y **agregar** "Trabaja con nosotros" → `getPath('/trabaja-con-nosotros')` (esa página existe y el handoff no la enlaza).
  - Color de enlaces según D3.

**Criterio de aceptación:** a 1360, 1180, 1100, 1024, 900, 768 y 375 px, nada se parte en dos líneas ni se desborda (esto resuelve el pendiente #2 del doc 07). Navegable completo con teclado. En tablet y móvil, el menú hamburguesa llega a todas las secciones.
**Commit:** `feat(web): header con aparición por scroll, menú móvil y footer oscuro`

---

### Fase 4 · Secciones de la landing (parte 1)
**Archivos:** `src/components/landing/Hero.astro`, `ClientsMarquee.astro`, `Services.astro`, `Stats.astro`, `src/components/ui/*`, `src/pages/index.astro`

- [ ] **4.1** Componentes UI reutilizables:
  - `Eyebrow.astro`: mono de 12 px, peso 600, tracking de 0.08em y color `--accent-text`.
  - `SectionHeading.astro`: eyebrow + H2, con máximo de 640 px y margen inferior de 48 px.
  - `PillButton.astro`: variantes `primary` (fondo salmón según D3) y `ghost` (borde blanco translúcido), como `<a>` o `<button>`, con alto mínimo de 44 px.
  - `Card.astro`: fondo `--card-bg`, borde `--card-border`, radio de 16 px y prop de hover opcional.
- [ ] **4.2** `Hero.astro` (líneas 81–120, README §2):
  - `min-height: 100svh` (con respaldo `100vh`).
  - Imagen de fondo con `<Image>` de `astro:assets`, `loading="eager"`, `fetchpriority="high"`, clase `hero-bg-img` (zoom de 22 s) y overlay en degradado de 115°, exacto de la referencia.
  - Grilla `1.1fr 0.9fr` con gap de 56 px; pasa a 1 columna bajo 900 px.
  - Eyebrow con ícono de rayo en SVG, `<h1>` en dos líneas (la segunda en salmón) y párrafo de máximo 48ch.
  - Tarjeta de acceso al portal: glassmorphism exacto (fondo, `backdrop-filter`, borde, sombra y radio de 20 px), ícono de escudo en SVG, "Soy Cliente →" → `PORTAL_URLS.cliente` y "Soy BKB →" → `PORTAL_URLS.colaborador`.
  - Cada hijo lleva la clase `hero-in`.
  - Padding `96px 40px 110px`, reduciendo los laterales en móvil.
- [ ] **4.3** `ClientsMarquee.astro` (líneas 123–136, README §3):
  - Eyebrow centrado "CONFÍAN EN BKB" y 16 tarjetas blancas de 150×84 px con `object-fit: contain`.
  - Renderizar la lista dos veces: la **segunda copia** va dentro de un contenedor con `aria-hidden="true"` y sus imágenes con `alt=""`, para que un lector de pantalla no la lea dos veces.
  - Animación `marqueeScroll` de 32 s lineal infinita. **Agregar** pausa con hover y con `:focus-within`.
  - Con movimiento reducido: sin animación y grilla con salto de línea.
  - Bordes superior e inferior de 1 px con `--card-border`.
- [ ] **4.4** `Services.astro` (líneas 139–161, README §4): `id="servicios"` y grilla de 4 columnas con gap de 22 px (2 columnas bajo 900 px y **1 bajo 560 px**). Cada tarjeta:
  - Ícono de 52×52 px con radio de 13 px y fondo salmón tenue. El tamaño de la imagen viene de `iconSize` y `iconFit`.
  - Título, descripción y viñetas separadas por un divisor superior.
  - `transition-delay: index * 100ms`.
  - Hover exacto: borde, `translateY(-6px)`, sombra, y el ícono escala a 1.08 y sube 3 px.
- [ ] **4.5** `Stats.astro` (líneas 164–173, README §5): banda con fondo `--page-bg` y bordes de 1 px, grilla de 4 columnas con gap de 32 px (2 bajo 900 px). Número en Grotesk 700, 42 px y salmón, con `data-target` y `data-suffix`. **El HTML renderiza el valor final** ("25+"), y el script lo reinicia a 0 solo justo antes de animar.
- [ ] **4.6** `index.astro`: `<Layout headerMode="reveal">` con las secciones en el **orden de la referencia**: Hero → Clientes → Servicios → Métricas → Mercados → Portafolio → Portal → Cotización.

**Criterio de aceptación:** comparación lado a lado con la referencia a 1360 px (oscuro y claro) sin diferencias apreciables de espaciado, color ni tipografía. Sin desborde horizontal a 375 px.
**Commit:** `feat(web): hero, carrusel de clientes, servicios y métricas de la landing`

---

### Fase 5 · Secciones de la landing (parte 2)
**Archivos:** `src/components/landing/Markets.astro`, `Portfolio.astro`, `PortalShowcase.astro`, `QuoteSection.astro`

- [ ] **5.1** `Markets.astro` (líneas 176–191, README §6): `id="mercados"`, grilla de 3 columnas con gap de 24 px (1 bajo 900 px), tarjetas con radio de 16 px, padding de 28 px, hover `translateY(-4px)` y línea "Clientes: …" en mono.
- [ ] **5.2** `Portfolio.astro` (líneas 194–214, README §7): `id="obras"`, grilla de 3 columnas. Cada tarjeta:
  - Foto en 4:3 con `<Image>`, `loading="lazy"` y `sizes`.
  - Badge "SEC TE1 VIGENTE" flotante en la esquina superior izquierda.
  - Zoom de 1.06 en hover con `.5s cubic-bezier(.16,1,.3,1)`.
  - Título de 15.5 px y especificación en mono de 12 px.
  - **No usar `faena-4.jpg`** (D7).
- [ ] **5.3** `PortalShowcase.astro` (líneas 217–263, README §8): `id="portal"`, dos columnas.
  - Izquierda: eyebrow, H2 y 3 viñetas con punto salmón de 8 px.
  - Derecha: maqueta de ventana **siempre oscura** con puntos rojo/ámbar/verde, URL falsa `portal.bkb.cl/obras/sopraval-tdf` y 4 filas (TE1 vigente en verde, Plano DWG 2.4 MB, Informe termográfico 1.1 MB y fila bloqueada con candado en SVG).
  - Toda la maqueta lleva `aria-hidden="true"` y, junto a ella, una descripción `sr-only`: "Ejemplo ilustrativo del portal documental".
- [ ] **5.4** `QuoteSection.astro` (líneas 266–299, README §9): `id="cotizar"`, grilla `0.9fr 1.1fr` con gap de 40 px (1 columna bajo 900 px).
  - **Tarjeta de Guardia 24/7** (siempre oscura): degradado de 155°, borde salmón, pill "GUARDIA DE URGENCIA 24/7", título, texto, teléfono como enlace grande `SITE.phoneHref` y datos de oficina y cobertura.
  - **Formulario** con fondo `--card-bg` y radio de 18 px:
    - Cada campo con `<label>` visible o `sr-only` asociada; **los placeholders no reemplazan a las etiquetas**.
    - Atributos `name`, `autocomplete` (`name`, `organization`, `email`, `tel`) y `required`.
    - Filas de 2 columnas que pasan a **1 columna bajo 640 px**; la referencia desborda 7 px a 375 px por no hacerlo.
    - `<select>` con `quoteOptions` y una opción inicial vacía; `<textarea>`.
    - Campo trampa anti-bots oculto.
    - Casilla de consentimiento obligatoria con enlace a `/privacidad` (Ley 21.719); no está en el handoff, pero es requisito legal.
    - Botón `type="submit"` "Enviar Solicitud →" y foco exacto (`outline: 3px solid #FA5A36; outline-offset: 2px`).
    - **Comportamiento de envío según D4:** `method="post"` y `action={QUOTE_ENDPOINT}`. Si el endpoint está vacío, el botón queda `disabled` y se muestra el aviso con correo y teléfono.
- [ ] **5.5** Verificar que las anclas de header y footer llevan a cada sección, con `scroll-margin-top` igual a la altura del header y `scroll-behavior: smooth` salvo con movimiento reducido.

**Criterio de aceptación:** las 8 secciones coinciden con la referencia en ambos temas. El formulario nunca genera una URL con datos personales (probar enviándolo).
**Commit:** `feat(web): mercados, portafolio, vitrina del portal y sección de cotización`

---

### Fase 6 · Movimiento e interacciones
**Archivo:** `src/scripts/motion.ts`, importado desde `Layout.astro` con `<script>` (Astro lo empaqueta)

- [ ] **6.1** Reveal: `IntersectionObserver` con `threshold: 0.15` sobre `.reveal`; agrega `is-visible` y deja de observar el elemento (referencia, líneas 416–426).
- [ ] **6.2** Entrada del hero: `.hero-in` con un escalonado de `90 + i * 90` ms (líneas 428–432).
- [ ] **6.3** Contadores: `threshold: 0.4`, ease-out cúbico de 1100 ms y `requestAnimationFrame` (líneas 434–453). Al terminar, el texto debe quedar idéntico al renderizado en el HTML.
- [ ] **6.4** Header: listener de scroll `passive` con umbral de 40 px (líneas 455–463) + `focusin` + manejo de `visibility` (Fase 3.1). Solo en modo `reveal`.
- [ ] **6.5** `prefers-reduced-motion`: todo en su estado final sin observers ni animaciones. Escuchar el cambio de la media query en caliente.
- [ ] **6.6** Scripts idempotentes: sin listeners duplicados si Astro navega con transiciones en el futuro; exponer una función `init()`.

**Criterio de aceptación:** con reduced motion activado (DevTools → Rendering) no hay movimiento y todo es visible. Con JS desactivado, todo el contenido es visible. Consola sin errores.
**Commit:** `feat(web): animaciones de revelado, contadores y header con accesibilidad de movimiento`

---

### Fase 7 · Rutas, páginas internas y limpieza
- [ ] **7.1** (D1-A) En `astro.config.mjs`, agregar `redirects`:
  ```js
  redirects: {
    '/servicios': '/#servicios',
    '/obras': '/#obras',
    '/nosotros': '/#mercados',
    '/contacto': '/#cotizar',
  }
  ```
  Verificar que con `GITHUB_PAGES=true` el HTML de redirección apunte a `/BKB/#…`. Si Astro no aplica `base` a los destinos, generar las páginas de redirección manualmente con `<meta http-equiv="refresh">` y `getPath`.
- [ ] **7.2** Eliminar `pages/servicios.astro`, `obras.astro`, `nosotros.astro` y `contacto.astro`. Esto deja sin efecto los pendientes #6 y #7 del doc 07, porque su contenido desaparece.
- [ ] **7.3** Reestilizar `trabaja-con-nosotros.astro`, `privacidad.astro` y `terminos.astro` con `headerMode="solid"`, tokens v2, `Card`, `PillButton` y `SectionHeading`.
  - En el formulario de CV aplicar la misma regla que D4: `method="post"` y `enctype="multipart/form-data"`; si no hay endpoint, deshabilitado con aviso.
  - Corregir la clase inválida `border-[#sand-200]` si sobrevive algún resto (pendiente #8).
- [ ] **7.4** Crear `404.astro` con el estilo nuevo: título, texto y botón a `/`.
- [ ] **7.5** Eliminar `components/Header.astro`, `Footer.astro` y `Button.astro`, y las clases antiguas de `global.css` (`.btn*`, `.card-bkb`, `.display-*`, `.body-*`, `.badge*`, `.bg-grid-technical`, `.container-bkb`). Buscar referencias antes de borrar:
  ```bash
  grep -rn "card-bkb\|btn-primary\|display-lg\|container-bkb\|Button.astro" apps/web/src
  ```
- [ ] **7.6** Unificar todos los enlaces al portal a través de `PORTAL_URLS` (pendiente #9 del doc 07).
- [ ] **7.7** Confirmar que no queda ningún hex arbitrario: `grep -rn "\[#" apps/web/src` debe devolver 0 resultados (pendiente #10).

**Criterio de aceptación:** las rutas antiguas redirigen a su ancla en local y con base `/BKB`. Build sin advertencias. No hay código muerto.
**Commit:** `refactor(web): consolidar landing, redirigir rutas antiguas y reestilizar páginas internas`

---

### Fase 8 · Imágenes y rendimiento
- [ ] **8.1** Mover los assets del handoff a `apps/web/src/assets/` (estructura de la sección 3) y usar `<Image>` / `<Picture>` de `astro:assets` con salida `webp` (y `avif` para el hero), `widths` y `sizes` adecuados. **No** copiar `faena-4.jpg`.
- [ ] **8.2** Logo: `bkb-logo-final.png` pesa 235 KB y se muestra a 44 px de alto. Generar la versión optimizada con `<Image height={88}>` (2x) y crear `public/favicon.png` / `apple-touch-icon.png` a partir de él. Si el usuario entrega un SVG del logo, preferir el SVG.
- [ ] **8.3** Borrar de `public/assets/images/` lo que ya no se referencie, y `logo.svg`, `logo-dark.svg` y `favicon.svg` antiguos si se reemplazan. Verificar con grep antes de borrar.
- [ ] **8.4** Todas las imágenes con `width` y `height` explícitos, para evitar saltos de diseño al cargar.

**Criterio de aceptación:** Lighthouse móvil en la landing con Performance ≥ 95, Accessibility ≥ 95 (el mínimo es 100 si se aplicó D3-A), Best Practices ≥ 95 y SEO = 100. El hero es el LCP y carga en menos de 2.5 s con 4G simulado.
**Commit:** `perf(web): optimizar imágenes con astro:assets y renovar favicon`

---

### Fase 9 · Control de calidad
- [ ] **9.1** Build normal y build para GitHub Pages:
  ```bash
  npm run build:web
  GITHUB_PAGES=true npm run build:web
  ```
  En PowerShell: `$env:GITHUB_PAGES='true'; npm run build:web`. Revisar que ningún `href` o `src` interno de `apps/web/dist` empiece con `/` sin `/BKB`.
- [ ] **9.2** Comparación visual contra la referencia (sección 1.1) a 1360, 1280, 1180, 1024, 900, 768 y 375 px, en tema oscuro y claro. Anotar en el PR cualquier diferencia intencional (D3, D6, formularios accesibles).
- [ ] **9.3** Sin desborde horizontal en ningún ancho: `document.documentElement.scrollWidth === innerWidth`.
- [ ] **9.4** Recorrido con teclado: enlace de salto al contenido → header (aparece al recibir foco) → tarjeta del portal → carrusel (pausa) → formulario → footer. Foco siempre visible.
- [ ] **9.5** Revisión con axe DevTools en los dos temas: 0 violaciones serias o críticas.
- [ ] **9.6** Probar `prefers-reduced-motion`, JS desactivado y el conmutador de tema con recarga (persistencia sin parpadeo).
- [ ] **9.7** Consola del navegador sin errores ni 404 en todas las rutas.

---

### Fase 10 · Documentación y PR
- [ ] **10.1** Actualizar `docs/01-tokens-y-sistema-diseno.md` a v2: paleta salmón, temas, superficies nocturnas fijas, tabla de contraste final (D3) y reglas de uso.
- [ ] **10.2** Actualizar `docs/02-sitio-web-astro.md`: nuevo mapa de rutas y redirecciones, componentes y scripts de tema y movimiento.
- [ ] **10.3** Actualizar `docs/00-contexto-proyecto.md` (estado del repositorio) y agregar una entrada con fecha a `docs/06-bitacora-avances.md`.
- [ ] **10.4** Actualizar `docs/07-revision-frontend-pendientes.md` marcando cada pendiente según corresponda:

  | # del doc 07 | Resolución con este plan |
  |---|---|
  | 1 Formularios GET | Fase 5.4 / 7.3 (D4) |
  | 2 Header 1024–1240 px | Fase 3.1 (header nuevo) |
  | 3 Teléfono inconsistente | Fase 2.1 (`SITE`, dato del handoff; confirmar en D7) |
  | 4 `civil.jpg` clipart | Se usa solo como ícono (D7) |
  | 5 Obras sin validar | Reemplazadas por las del handoff (confirmar en D7) |
  | 6 Preselección de servicio | Desaparece con D1-A |
  | 7 Errores de tipeo | Desaparecen con D1-A |
  | 8 Clase Tailwind inválida | Fase 7.3 |
  | 9 Enlaces al portal | Fase 7.6 |
  | 10 Colores hardcodeados | Fases 1.6 y 7.7 |

- [ ] **10.5** Push a la rama de tarea y PR hacia `desarrollo` con:
  - Resumen por fase.
  - Capturas antes/después a 1360 y 375 px en ambos temas.
  - Decisiones D1–D6 aplicadas.
  - Lista D7 de contenido pendiente de validar.
  - Puntajes de Lighthouse.

---

## 5. Definición de terminado

- [ ] La landing reproduce la referencia en ambos temas, con las desviaciones justificadas (D3, D6 y accesibilidad de formularios) documentadas en el PR.
- [ ] Build local y build para GitHub Pages en verde, sin enlaces rotos.
- [ ] Sin desborde horizontal de 375 a 1920 px.
- [ ] Navegable al 100 % con teclado y lector de pantalla; axe sin violaciones serias.
- [ ] Contenido visible sin JavaScript y con movimiento reducido.
- [ ] Ningún formulario puede enviar datos personales por GET.
- [ ] Ningún color hex arbitrario en `apps/web/src`; todo sale de `@bkb/tokens`.
- [ ] Documentación 00, 01, 02, 06 y 07 actualizada.
