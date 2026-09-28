# Tareas: Página de Arriendo de Equipos

> Spec: [`docs/10-plan-arriendo-equipos.md`](../docs/10-plan-arriendo-equipos.md) · Plan: [`arriendo-plan.md`](arriendo-plan.md)
> Rama: corta desde `desarrollo` (p. ej. `benjamin/2026-09-28-arriendo`), con PR a `desarrollo`.
> Comandos (desde `bkb-platform/`): `npm run dev:web` · `npm run build:web` · `GITHUB_PAGES=true npm run build:web`
> El sitio no tiene tests automáticos. La verificación es con el build y en el navegador.

---

## Fase 1: Base

### Tarea 1: Datos de los equipos
**Descripción:** crear `data/arriendo.ts` con la interfaz `EquipoArriendo` y `gruposArriendo`: "Instrumentos de medición" (8 Fluke) y "Generadores" (200 kVA y 30 kVA), según la tabla de la spec. Cada equipo tiene `id`, `nombre`, `modelo` (salvo los generadores) y `uso` (una línea, con `TODO: validar con BKB`).

**Criterios de aceptación:**
- [x] 10 equipos en 2 grupos, con nombre y modelo idénticos a la tabla de la spec.
- [x] Los `id` son únicos y en kebab-case (`fluke-1775`, `generador-200kva`).
- [x] No aparece calibración ni alineación láser.

**Verificación:**
- [x] `npm run build:web` compila.

**Dependencias:** ninguna
**Archivos:** `apps/web/src/data/arriendo.ts`
**Tamaño:** XS

### Tarea 2: Página `/arriendo` con tarjetas expandibles (sin JavaScript)
**Descripción:** crear `pages/arriendo.astro` con `Layout` (`headerMode="solid"`, título y descripción propios). Lleva el encabezado que dice que **todo arriendo incluye técnico BKB**, los dos grupos con un `<details>` por equipo (nombre, modelo chico y ＋ a la derecha que rota a × al abrir; abierta, la línea de uso), un botón de WhatsApp general y el bloque de cierre con un link a `/#cotizar`. Los botones de agregar se incluyen en el HTML, ocultos sin JavaScript (`html:not(.js)`), pero todavía sin lógica.

**Criterios de aceptación:**
- [ ] Se ven los 10 equipos en 2 grupos. Abren y cierran con clic, con Enter y con Espacio. (pendiente navegador: el HTML tiene los 10 `<details>` en 2 grupos)
- [ ] El marcador nativo de `<summary>` está oculto. El ícono gira sin animación bajo `prefers-reduced-motion`. (pendiente navegador; las clases están en el HTML)
- [x] El WhatsApp general abre `wa.me/56961911593` (verificado en el HTML; `/BKB/#cotizar` en el build de Pages) con un texto genérico de arriendo. Los enlaces pasan por `getPath()`.

**Verificación:**
- [x] `npm run build:web` y `GITHUB_PAGES=true npm run build:web` pasan, y existe `dist/arriendo/index.html`.
- [ ] Manual: claro, oscuro, 375 px sin scroll horizontal, teclado y JavaScript desactivado. (pendiente navegador) (pendiente navegador)

**Dependencias:** T1
**Archivos:** `apps/web/src/pages/arriendo.astro`
**Tamaño:** S

## Checkpoint A: después de T1 y T2
- [x] Ambos builds pasan.
- [ ] La página se lee completa y se puede escribir por WhatsApp sin JavaScript.
- [ ] **El usuario revisa el diseño de las tarjetas antes de seguir.**

---

## Fase 2: Selección múltiple

### Tarea 3: Sumar equipos y armar el mensaje de WhatsApp
**Descripción:** agregar el `<script>` a la página. El botón "Agregar a la cotización" cambia a "✓ Agregado · Quitar" (`aria-pressed`) y la tarjeta queda marcada con borde salmón y ✓. La barra fija abajo aparece con 1 o más equipos, muestra "N equipos seleccionados" (`aria-live="polite"`), la lista con opción de quitar y "Cotizar por WhatsApp". El `href` se arma con `mensajeWhatsApp(labels)` en el orden de la lista. Mientras la barra está visible, la clase `has-cotizacion` en `<html>` oculta `.whatsapp-fab`.

**Criterios de aceptación:**
- [ ] Con 0 equipos no hay barra. Con 1 o más, el texto decodificado es `Hola, quisiera cotizar el arriendo con técnico BKB de:` seguido de una línea `- Nombre (Modelo)` por cada equipo agregado (los generadores sin modelo).
- [ ] Quitar un equipo desde la tarjeta o desde la barra actualiza las dos partes y el mensaje.
- [ ] La barra no tapa el último equipo ni choca con el aviso de emergencia a 375 px.

**Verificación:**
- [ ] Manual: agregar 1 y 3 equipos, y leer `decodeURIComponent(new URL(boton.href).searchParams.get('text'))` en la consola. (pendiente navegador)
- [ ] Manual: quitar desde los dos lugares. Recorrido completo solo con teclado. (pendiente navegador)
- [x] Ambos builds pasan.

**Dependencias:** T2
**Archivos:** `apps/web/src/pages/arriendo.astro` (y `styles/global.css` solo si la regla de `has-cotizacion` no cabe en el `<style>` de la página)
**Tamaño:** S

## Checkpoint B: después de T3
- [ ] El flujo completo funciona: abrir tarjeta → agregar varios → WhatsApp con la lista correcta.
- [ ] **El usuario prueba la página antes de enlazarla desde el sitio.**

---

## Fase 3: Acceso y cierre

### Tarea 4: Link "Arriendo" en el header
**Descripción:** agregar `{ href: getPath('/arriendo'), label: 'Arriendo' }` a `navLinks` en `SiteHeader.astro`. `MobileNav` lo hereda. En `/arriendo`, el link lleva `aria-current="page"` y se ve activo.

**Criterios de aceptación:**
- [ ] "Arriendo" aparece en el menú de escritorio y en el del celular, y lleva a `/arriendo` desde `/`, `/privacidad` y `/arriendo`. (pendiente navegador; el HTML tiene el link con `/arriendo` y `/BKB/arriendo`)
- [ ] En la landing, `initActiveNav` sigue marcando bien las secciones y nunca marca "Arriendo". (pendiente navegador; `dist/index.html` sin `aria-current`)
- [ ] A 1280 px el header no se desborda. Si se desborda, **se pregunta** antes de quitar "Inicio". (pendiente navegador; estimado ~1070 px de 1200 útiles)

**Verificación:**
- [ ] Manual a 1280 px, 1440 px y 375 px. (pendiente navegador)
- [x] `GITHUB_PAGES=true npm run build:web`: el link lleva a `/BKB/arriendo`.

**Dependencias:** T2 (la ruta tiene que existir)
**Archivos:** `apps/web/src/components/site/SiteHeader.astro`
**Tamaño:** XS

### Tarea 5: Enlace desde la tarjeta "Arriendo de Equipos"
**Descripción:** agregar `href?: string` a `ServicioItem` en `data/landing.ts` y ponérselo solo a la tarjeta de arriendo (`/arriendo`). En `Services.astro`, si la tarjeta tiene `href`, se muestra un link "Ver equipos →" (con `getPath()`). **El texto de la tarjeta no cambia.** Los clones del carrusel quedan `inert` para que su link no reciba el foco dos veces.

**Criterios de aceptación:**
- [ ] Solo la tarjeta de arriendo tiene el link, y lleva a `/arriendo`. (pendiente navegador; 1 solo "Ver equipos" en el HTML)
- [ ] Con Tab se llega una sola vez al link (los clones no reciben foco).
- [ ] El carrusel infinito sigue funcionando igual.

**Verificación:**
- [ ] Manual: Tab por el carrusel, clic en el link, flechas y scroll del carrusel. (pendiente navegador)
- [x] Ambos builds pasan.

**Dependencias:** T2
**Archivos:** `apps/web/src/data/landing.ts`, `apps/web/src/components/landing/Services.astro`
**Tamaño:** S

### Tarea 6: Documentación
**Descripción:** registrar la página nueva en la documentación.

**Criterios de aceptación:**
- [x] `docs/02-sitio-web-astro.md`: `/arriendo` en el mapa de rutas y `data/arriendo.ts` en la estructura de `src/`.
- [x] `docs/06-bitacora-avances.md`: entrada de la sesión. Se quita "además de calibración" de la línea 143.
- [x] La spec (`docs/10`) cambia su estado a "implementada".

**Verificación:**
- [x] Lectura.

**Dependencias:** T1 a T5
**Archivos:** `docs/02-sitio-web-astro.md`, `docs/06-bitacora-avances.md`, `docs/10-plan-arriendo-equipos.md`
**Tamaño:** XS

## Checkpoint final
- [ ] Se cumplen todos los criterios de éxito de la spec.
- [x] `npm run build:web` y `GITHUB_PAGES=true npm run build:web` pasan.
- [ ] El usuario revisa la página y la navegación.
- [ ] PR a `desarrollo`.
