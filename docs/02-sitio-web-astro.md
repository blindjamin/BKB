# 02 · Sitio Web Público (Astro)

> **Nota para IAs y desarrolladores frontend:**  
> Describe la arquitectura, las rutas y los componentes de `apps/web` después del rediseño según el handoff de Claude Design. La referencia visual está en `docs/design/handoff-landing/` y el plan de ejecución en `08-plan-rediseno-landing.md`.

---

## 1. Stack Tecnológico
- **Framework:** Astro 5, salida estática (`output: 'static'`), sin servidor.
- **Estilos:** Tailwind CSS v4 (`@tailwindcss/vite`) más `@bkb/tokens`, mapeados a utilidades en `src/styles/global.css`. Ver `01-tokens-y-sistema-diseno.md`.
- **Imágenes:** en `src/assets/` (`brand/`, `clients/`, `icons/`, `landing/`), optimizadas con `astro:assets`.
- **JavaScript:** scripts pequeños y vanilla: tema (`src/scripts/theme.ts`), movimiento (`src/scripts/motion.ts`) y los propios de algunos componentes (sección activa del header, carrusel de servicios, aviso de emergencia, mapa bajo demanda). El contenido se ve completo sin JS y con `prefers-reduced-motion`.
- **Hosting:** previsualización en GitHub Pages con base `/BKB`. Todo enlace interno y todo asset pasa por `getPath()` (`src/utils/paths.ts`).

---

## 2. Mapa de Rutas
| Ruta | Archivo | Propósito |
|---|---|---|
| `/` | `src/pages/index.astro` | Landing de una página con anclas, en orden: `#top` (hero), `#servicios`, `#mercados`, `#testimonios`, `#obras`, `#cotizar` (contacto y ubicación) |
| `/trabaja-con-nosotros` | `src/pages/trabaja-con-nosotros.astro` | Postulaciones, con consentimiento de la Ley 21.719 |
| `/privacidad` | `src/pages/privacidad.astro` | Política de datos personales |
| `/terminos` | `src/pages/terminos.astro` | Términos y condiciones |
| `404` | `src/pages/404.astro` | Página de error |

**Redirecciones** (definidas en `astro.config.mjs`, para no romper enlaces ya compartidos): `/servicios` → `/#servicios`, `/obras` → `/#obras`, `/nosotros` → `/#mercados`, `/contacto` → `/#cotizar`.

---

## 3. Estructura de `src/`
```
config/site.ts         Teléfono, correo, oficina y dirección (officeAddress), URLs del portal y endpoint del formulario
data/landing.ts        Datos de las secciones (servicios, mercados, obras, clientes, testimonios, opciones del formulario)
layouts/Layout.astro   Shell: metadata, Schema.org, script anti-parpadeo del tema, prop headerMode, aviso de emergencia y WhatsApp
components/site/       SiteHeader, MobileNav, ThemeToggle, SiteFooter, EmergencyNotice, WhatsAppButton
components/landing/    Hero, ClientsMarquee, Services, Markets, Testimonials, Portfolio, QuoteSection
                       (Stats existe pero no se usa en la landing desde la sesión 9)
components/ui/         Card, Eyebrow, PillButton, SectionHeading
scripts/               theme.ts (tema claro/oscuro), motion.ts (revelado, contadores, header)
styles/global.css      Tailwind + tokens + keyframes
```

**Puntos clave**
- `Layout.astro` recibe `headerMode`. Desde la sesión 9 **todas las páginas usan `'solid'`** (header fijo y siempre visible). El modo `'reveal'` sigue en el código pero no se usa.
- **Header (`SiteHeader.astro`):** subrayado salmón animado al pasar el mouse y resaltado de la sección visible (IntersectionObserver sobre los `id` de las anclas). Los colores por tema salen de variables (`--hdr-text`, `--hdr-hover`, `--hdr-active`, `--pill-*`). Las reglas del tema claro llevan `#site-header` en el selector para ganarle en especificidad a las del oscuro; sin eso, el texto quedaba blanco sobre fondo claro. Los botones tipo pastilla (tema, Acceso Portal, menú móvil) comparten la clase `header-pill`.
- El tema se guarda en `localStorage['bkb-theme']` y un script `is:inline` lo aplica antes de pintar, para evitar el parpadeo. La landing es oscura por defecto.
- `config/site.ts` lee `PUBLIC_PORTAL_URL` (por defecto `https://portal.empresabkb.cl`) y `PUBLIC_QUOTE_ENDPOINT`. La plantilla está en `apps/web/.env.example`.
- **Formulario de cotización:** usa `method="POST"` con `action` igual a `PUBLIC_QUOTE_ENDPOINT`. Sin endpoint, el botón queda deshabilitado con un aviso. Nunca debe existir un `<form>` sin `method`, porque enviaría datos personales por la URL.
- Los enlaces al portal salen de `PORTAL_URLS`; no escribir `https://portal.empresabkb.cl` a mano.
- **Hero y carrusel de clientes:** el carrusel es una franja propia **debajo** del hero (ya no va superpuesto). El hero mide `calc(100svh - 310px)` de alto mínimo, con `pt/pb` de 64 px, para que la franja de logos quede completa en la primera pantalla (verificado a 1440×900 y 1366×768). La tarjeta "Portal Digital BKB" cambia con el tema (clases `portal-card*`).
- **Carrusel de clientes (`ClientsMarquee.astro`):** logos en tarjeta blanca con borde salmón de 2 px, en gris y al 60 %; al pasar el mouse toman color y crecen al 110 %. Vuelta completa en 55 s, con desvanecido en los bordes (`mask-image`). **Sin `gap` entre las dos copias:** cada lista lleva `padding-right` propio, así el `translateX(-50%)` calza exacto y no hay salto de 12 px al reiniciar.
- **Servicios (`Services.astro`):** carrusel manual e infinito, con tarjetas de foto de fondo y texto centrado. El script clona las tarjetas a cada lado (`[copia][originales][copia]`) y, cuando el scroll se detiene (120 ms), salta un ancho de set para volver al tramo original. El `reveal` va en el contenedor y no en las tarjetas, porque el `IntersectionObserver` no ve las tarjetas recortadas por el scroll horizontal. En celular (menos de 640 px) las flechas se ocultan: se desliza con el dedo.
- **`w-full` obligatorio en secciones con `mx-auto` directas en `<main>`:** `main` es flex en columna, y un hijo con márgenes automáticos toma el ancho de su contenido. En Servicios eso hacía que la sección midiera el ancho de todo el carrusel (1360 px en un celular de 360 px) y estiraba la página. `Services` y `Markets` llevan `w-full`.
- **`overflow-x: clip` en `html` y `body`** (`global.css`): evita el scroll horizontal que causaba el panel del menú móvil escondido fuera de pantalla. Se usa `clip` y no `hidden` para no romper el header `sticky`.
- **Contacto (`QuoteSection.astro`, `#cotizar`):** formulario a la izquierda; a la derecha, la tarjeta de la oficina (dirección, cobertura, teléfono, correo) y el mapa. **El mapa de Google se carga solo al hacer clic en "Ver mapa"** (privacidad y velocidad); hay además un enlace "Abrir en Google Maps". El iframe se crea con `referrerPolicy = 'strict-origin-when-cross-origin'`.
- **Aviso de emergencia (`EmergencyNotice.astro`):** tarjeta flotante abajo a la izquierda (WhatsApp va a la derecha). Aparece a los 2,5 s; al cerrarlo no vuelve en la sesión (`sessionStorage['bkb-emergency-closed']`). En celular se reduce a título y botón de llamada. Texto definido por el usuario: "Equipo para servicios de emergencia", fallas en MT y BT, y fallas en sistemas de fuerza, control y/o instrumentación. **No mencionar "24/7".**
- **WhatsApp (`WhatsAppButton.astro`):** botón flotante, traído de la rama de Lisandro. Abre `wa.me` con el número de `SITE.phoneHref` y un mensaje prellenado.
- **Testimonios (`Testimonials.astro`):** tres tarjetas con datos de `testimonials` en `data/landing.ts`. **Son ficticios** (marcados con `TODO: PLACEHOLDER FICTICIO`) y deben reemplazarse por reseñas reales antes de publicar a producción.
- **Logo:** `public/assets/bkb-logo-final.png` (PNG circular con fondo transparente), referenciado con `getPath('/assets/bkb-logo-final.png')`. Mide 52 px en el header, 56 px en el footer y 48 px en la tarjeta del portal. El archivo de `src/assets/brand/` no se usa.
- **Logos de clientes:** son PNG con **fondo transparente** (sesión 9), generados desde `src/assets/clients/originals/` con un relleno por inundación desde los bordes, que solo quita el blanco exterior y conserva el blanco interno del logo. Los 7 que eran JPG pasaron a PNG y `data/landing.ts` apunta a los `.png`.
- **Dev server compartido por túnel:** `astro.config.mjs` permite los hosts `.trycloudflare.com` y `.devtunnels.ms` (`vite.server.allowedHosts`). Solo afecta al servidor de desarrollo. Ver la advertencia de seguridad en la sección 5.

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
- El botón de envío del formulario de cotización usa `bg-salmon-500` con texto blanco (3,19:1), por debajo del mínimo AA. Corresponde `salmon-700` según D3.
- Validar el contenido de la lista D7 y verificar las fases 8 a 10 de `08-plan-rediseno-landing.md`.
- **Contenido sin respaldo** (no aparece en el sitio verificado `empresabkb.cl`): mercados, obras del portafolio y menciones a SEC TE1/Clase A. Ver `06-bitacora-avances.md`, sesión 5. Desde la sesión 9 las métricas ya no se muestran y el aviso de emergencia no menciona "24/7"; los testimonios son ficticios. Ver `10-avances-landing-desa.md`.
- Reemplazar por fotos reales de cada servicio las fotos de faena repetidas de las tarjetas de "Qué hacemos" (marcadas con `TODO` en `data/landing.ts`).
- El teléfono de `config/site.ts` (`+56 9 8249 1403`) no coincide con los teléfonos reales confirmados (`+56 9 8975 3095` y `+56 9 6191 1593`).
- La lista de servicios del footer aún menciona "Obras Civiles" y "Mantención 24/7".
