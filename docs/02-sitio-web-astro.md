# 02 · Sitio Web Público (Astro)

> **Nota para IAs y desarrolladores frontend:**  
> Describe la arquitectura, las rutas y los componentes de `apps/web`. El handoff de diseño y el plan de rediseño ya se cumplieron y se borraron (quedan en el historial de git).

---

## 1. Stack Tecnológico
- **Framework:** Astro 5, salida estática (`output: 'static'`), sin servidor.
- **Estilos:** Tailwind CSS v4 (`@tailwindcss/vite`) más `@bkb/tokens`, mapeados a utilidades en `src/styles/global.css`. Ver `01-tokens-y-sistema-diseno.md`.
- **Imágenes:** en `src/assets/` (`brand/`, `clients/`, `icons/`, `landing/`), optimizadas con `astro:assets`.
- **JavaScript:** vanilla y mínimo: tema (`src/scripts/theme.ts`) y movimiento (`src/scripts/motion.ts`), más scripts chicos por componente o página (carrusel, aviso, header y la selección de `/arriendo`). El contenido se ve completo sin JS y con `prefers-reduced-motion`.
- **Hosting:** previsualización en GitHub Pages con base `/BKB`. Todo enlace interno y todo asset pasa por `getPath()` (`src/utils/paths.ts`).

---

## 2. Mapa de Rutas
| Ruta | Archivo | Propósito |
|---|---|---|
| `/` | `src/pages/index.astro` | Landing de una página con anclas: `#mercados`, `#servicios`, `#obras`, `#cotizar` |
| `/arriendo` | `src/pages/arriendo.astro` | Arriendo de equipos (siempre con técnico BKB). Se eligen varios y se cotizan en un solo mensaje de WhatsApp |
| `/trabaja-con-nosotros` | `src/pages/trabaja-con-nosotros.astro` | Postulaciones, con consentimiento de la Ley 21.719 |
| `/privacidad` | `src/pages/privacidad.astro` | Política de datos personales |
| `/terminos` | `src/pages/terminos.astro` | Términos y condiciones |
| `404` | `src/pages/404.astro` | Página de error |

**Redirecciones** (definidas en `astro.config.mjs`, para no romper enlaces ya compartidos): `/servicios` → `/#servicios`, `/obras` → `/#obras`, `/nosotros` → `/#mercados`, `/contacto` → `/#cotizar`.

---

## 3. Estructura de `src/`
```
config/site.ts         Teléfonos, correo, oficina y dirección, URLs del portal y endpoint del formulario
data/landing.ts        Datos de las secciones (servicios, mercados, testimonios, obras, clientes)
data/arriendo.ts       Equipos en arriendo: grupos, nombre, modelo y uso
layouts/Layout.astro   Shell: metadata, Schema.org, script anti-parpadeo del tema, prop headerMode
components/site/       SiteHeader, MobileNav, ThemeToggle, SiteFooter, EmergencyNotice, WhatsAppButton
components/landing/    Hero, ClientsMarquee, Services, Markets, Testimonials, Portfolio, QuoteSection
components/ui/         Card, Eyebrow, PillButton, SectionHeading
scripts/               theme.ts (tema claro/oscuro), motion.ts (revelado, contadores, header)
styles/global.css      Tailwind + tokens + keyframes
```

**Puntos clave**
- `Layout.astro` recibe `headerMode`: `'reveal'` en la landing y `'solid'` en las páginas internas. En modo `reveal` el header está oculto sobre el hero y aparece al llegar a "Qué hacemos" (`#servicios`); también aparece al recibir el foco con el teclado. Lo controla `motion.ts`.
- **Header:** viene de la rama de Lisandro. Tiene el link de la sección activa, el botón **"Soy cliente →"** (al login del portal) y "Cotizar Obra". El menú del celular también dice "Soy cliente".
- **Aviso de emergencia (`EmergencyNotice.astro`):** tarjeta flotante abajo a la izquierda con el botón para llamar al teléfono principal. Aparece al pasar el hero y, si se cierra, no vuelve en la sesión (`sessionStorage['bkb-emergency-closed']`).
- **WhatsApp (`WhatsAppButton.astro`):** botón flotante abajo a la derecha que abre un chat con el teléfono principal.
- **Teléfonos:** `SITE.phones` en `config/site.ts` tiene los dos confirmados, +56 9 6191 1593 (principal, llamadas y WhatsApp) y +56 9 6662 6540 (secundario). El +56 9 8975 3095 se eliminó el 2026-09-28. `SITE.phoneDisplay` y `SITE.phoneHref` son el principal. La tarjeta de contacto y el pie muestran los dos.
- **Contacto (`QuoteSection.astro`):** formulario más una tarjeta de la oficina central (Panamericana Norte 476, Artificio, La Calera) con teléfonos, correo y mapa. El mapa de Google se carga solo al hacer clic en "Ver mapa", para no cargar cookies de Google sin que la persona lo pida.
- El tema se guarda en `localStorage['bkb-theme']` y un script `is:inline` lo aplica antes de pintar, para evitar el parpadeo. La landing es oscura por defecto; el claro es grafito y naranjo.
- `config/site.ts` lee `PUBLIC_PORTAL_URL` (por defecto `https://portal.empresabkb.cl`) y `PUBLIC_QUOTE_ENDPOINT`. La plantilla está en `apps/web/.env.example`. En local, `apps/web/.env` con `PUBLIC_PORTAL_URL=http://localhost:8000` hace que los botones lleven al portal local.
- Todos los enlaces al portal (`PORTAL_URLS`) llevan a `/login/`. Clientes y colaboradores entran por el mismo login.
- **Formulario de cotización:** usa `method="POST"` con `action` igual a `QUOTE_ENDPOINT` (`PUBLIC_QUOTE_ENDPOINT` o, por defecto, `/cotizar/` del portal). El portal valida, aplica honeypot y un tope de 5 envíos por hora por IP, y envía la solicitud a `COTIZACION_CORREO` (`ingenieria@empresabkb.cl`) con Reply-To al cliente. La landing muestra si se envió o no. Nunca debe existir un `<form>` sin `method`, porque enviaría datos personales por la URL.
- Los enlaces al portal salen de `PORTAL_URLS`; no escribir `https://portal.empresabkb.cl` a mano.
- **Hero y carrusel de clientes:** `index.astro` los envuelve en un `div.relative`. El hero mide `100svh` y `ClientsMarquee` va `absolute bottom-0` encima, sin fondo. El hero deja `pb-[200px]` libres para que el contenido no quede tapado por la franja. El hero ya no tiene la tarjeta de acceso al portal: solo la información y el carrusel.
- **Servicios (`Services.astro`):** carrusel manual e infinito, con tarjetas de foto de fondo y texto centrado. El script clona las tarjetas a cada lado (`[copia][originales][copia]`) y, cuando el scroll se detiene (120 ms), salta un ancho de set para volver al tramo original. El `reveal` va en el contenedor y no en las tarjetas, porque el `IntersectionObserver` no ve las tarjetas recortadas por el scroll horizontal.
- **Arriendo (`/arriendo`):** una tarjeta por equipo con foto (`src/assets/arriendo/<id>.jpg`) y descripción siempre visible. La selección vive en memoria (no se guarda) y una barra fija abajo arma el mensaje de WhatsApp; mientras está visible, `has-cotizacion` en `<html>` oculta `.whatsapp-fab` y `.emergency-notice`. Los textos de uso salen de las fichas de Fluke. La tarjeta de "Qué hacemos" enlaza con "Ver equipos →" y los clones del carrusel van con `inert`.
- **Logo:** `public/assets/bkb-logo-final.png` (PNG circular con fondo transparente), referenciado con `getPath('/assets/bkb-logo-final.png')`. Mide 52 px en el header y 56 px en el footer. El archivo de `src/assets/brand/` no se usa.
- **Logos de clientes:** se les recortó el margen blanco para que se vean del mismo tamaño. Los originales están en `src/assets/clients/originals/` y en el historial de git.

---

## 4. Reglas de Desarrollo
1. Prohibido usar colores hex arbitrarios en clases (`bg-[#FA5A36]`): usar utilidades mapeadas a tokens (`bg-salmon-500`, `bg-page`, `text-muted`).
2. Todo enlace interno y todo asset pasa por `getPath()`.
3. Los elementos que se ocultan para animarse (`.reveal`, `.hero-in`) solo lo hacen bajo `html.js`, de modo que sin JavaScript todo se ve.
4. Cada página lleva título y metadescripción propios en las props de `Layout`.
5. Botones y textos pequeños con contraste AA: ver decisión D3 en `01-tokens-y-sistema-diseno.md`.
6. Validar con `npm run build:web` y con `GITHUB_PAGES=true npm run build:web` antes de confirmar cambios.
7. En Tailwind v4, `text-[var(--x)]` se interpreta como **color**. Para tamaños de fuente usar `text-[length:var(--x)]`. Si un título se ve de 16 px, revisar esto primero.

---

## 5. Pendientes conocidos
- Contenido por validar con BKB y contraste del botón de envío: ver `tasks/todo.md` §5.
- **Fuente verificada:** `https://empresabkb.cl/` (sitio antiguo) es información real. No respaldados por él: mercados, obras del portafolio, guardia 24/7 y SEC TE1/Clase A.
- "Soy cliente" y el formulario de cotización no funcionan en la landing publicada hasta que el portal esté en `portal.empresabkb.cl` (tarea 16).
- La lista de servicios del footer aún menciona "Obras Civiles" y "Mantención 24/7".
