# 02 · Sitio Web Público (Astro)

> **Nota para IAs y desarrolladores frontend:**  
> Describe la arquitectura, las rutas y los componentes de `apps/web` después del rediseño según el handoff de Claude Design. La referencia visual está en `docs/design/handoff-landing/` y el plan de ejecución en `08-plan-rediseno-landing.md`.

---

## 1. Stack Tecnológico
- **Framework:** Astro 5, salida estática (`output: 'static'`), sin servidor.
- **Estilos:** Tailwind CSS v4 (`@tailwindcss/vite`) más `@bkb/tokens`, mapeados a utilidades en `src/styles/global.css`. Ver `01-tokens-y-sistema-diseno.md`.
- **Imágenes:** en `src/assets/` (`brand/`, `clients/`, `icons/`, `landing/`), optimizadas con `astro:assets`.
- **JavaScript:** solo dos scripts pequeños y vanilla: tema (`src/scripts/theme.ts`) y movimiento (`src/scripts/motion.ts`). El contenido se ve completo sin JS y con `prefers-reduced-motion`.
- **Hosting:** previsualización en GitHub Pages con base `/BKB`. Todo enlace interno y todo asset pasa por `getPath()` (`src/utils/paths.ts`).

---

## 2. Mapa de Rutas
| Ruta | Archivo | Propósito |
|---|---|---|
| `/` | `src/pages/index.astro` | Landing de una página con anclas: `#mercados`, `#servicios`, `#obras`, `#portal`, `#cotizar` |
| `/trabaja-con-nosotros` | `src/pages/trabaja-con-nosotros.astro` | Postulaciones, con consentimiento de la Ley 21.719 |
| `/privacidad` | `src/pages/privacidad.astro` | Política de datos personales |
| `/terminos` | `src/pages/terminos.astro` | Términos y condiciones |
| `404` | `src/pages/404.astro` | Página de error |

**Redirecciones** (definidas en `astro.config.mjs`, para no romper enlaces ya compartidos): `/servicios` → `/#servicios`, `/obras` → `/#obras`, `/nosotros` → `/#mercados`, `/contacto` → `/#cotizar`.

---

## 3. Estructura de `src/`
```
config/site.ts         Teléfono, correo, oficina, URLs del portal y endpoint del formulario
data/landing.ts        Datos de las secciones (servicios, métricas, mercados, obras, clientes)
layouts/Layout.astro   Shell: metadata, Schema.org, script anti-parpadeo del tema, prop headerMode
components/site/       SiteHeader, MobileNav, ThemeToggle, SiteFooter
components/landing/    Hero, ClientsMarquee, Services, Stats, Markets, Portfolio, PortalShowcase, QuoteSection
components/ui/         Card, Eyebrow, PillButton, SectionHeading
scripts/               theme.ts (tema claro/oscuro), motion.ts (revelado, contadores, header)
styles/global.css      Tailwind + tokens + keyframes
```

**Puntos clave**
- `Layout.astro` recibe `headerMode`: `'reveal'` en la landing (el header aparece al hacer scroll) y `'solid'` en las páginas internas.
- El tema se guarda en `localStorage['bkb-theme']` y un script `is:inline` lo aplica antes de pintar, para evitar el parpadeo. La landing es oscura por defecto.
- `config/site.ts` lee `PUBLIC_PORTAL_URL` (por defecto `https://portal.bkb.cl`) y `PUBLIC_QUOTE_ENDPOINT`. La plantilla está en `apps/web/.env.example`.
- **Formulario de cotización:** usa `method="POST"` con `action` igual a `PUBLIC_QUOTE_ENDPOINT`. Sin endpoint, el botón queda deshabilitado con un aviso. Nunca debe existir un `<form>` sin `method`, porque enviaría datos personales por la URL.
- Los enlaces al portal salen de `PORTAL_URLS`; no escribir `https://portal.bkb.cl` a mano.

---

## 4. Reglas de Desarrollo
1. Prohibido usar colores hex arbitrarios en clases (`bg-[#FA5A36]`): usar utilidades mapeadas a tokens (`bg-salmon-500`, `bg-page`, `text-muted`).
2. Todo enlace interno y todo asset pasa por `getPath()`.
3. Los elementos que se ocultan para animarse (`.reveal`, `.hero-in`) solo lo hacen bajo `html.js`, de modo que sin JavaScript todo se ve.
4. Cada página lleva título y metadescripción propios en las props de `Layout`.
5. Botones y textos pequeños con contraste AA: ver decisión D3 en `01-tokens-y-sistema-diseno.md`.
6. Validar con `npm run build:web` y con `GITHUB_PAGES=true npm run build:web` antes de confirmar cambios.

---

## 5. Pendientes conocidos
- El botón de envío del formulario de cotización usa `bg-salmon-500` con texto blanco (3,19:1), por debajo del mínimo AA. Corresponde `salmon-700` según D3.
- Validar el contenido de la lista D7 y verificar las fases 8 a 10 de `08-plan-rediseno-landing.md`.
