# apps/web · Sitio Público de BKB (Astro)

Aplicación web estática construida con **Astro 5+**, diseñada con cero JavaScript por defecto en el cliente, alta accesibilidad (WCAG 2.2 AA) y rendimiento superior (Lighthouse ≥ 95).

## Estructura de Páginas
- `src/pages/index.astro`: Landing de una página con anclas (`#mercados`, `#servicios`, `#obras`, `#cotizar`): hero con carrusel de clientes, "Qué hacemos" (carrusel de servicios), métricas, mercados, portafolio y cotización.
- `src/pages/trabaja-con-nosotros.astro`: Vacantes laborales y recepción de CV con consentimiento explícito bajo Ley 21.719.
- `src/pages/privacidad.astro`: Política de Privacidad de datos personales (Ley 21.719).
- `src/pages/terminos.astro`: Términos del servicio.
- `src/pages/404.astro`: Página de error.

Las rutas antiguas `/servicios`, `/obras`, `/nosotros` y `/contacto` redirigen a su ancla en la landing. Detalle en `docs/02-sitio-web-astro.md`.

## Comandos
Desde la raíz del monorepo (`bkb-platform/`):
```bash
# Iniciar servidor de desarrollo
npm run dev:web

# Compilar sitio estático para producción
npm run build:web

# Previsualizar build de producción
npm run preview:web
```
O directamente dentro de `apps/web/`:
```bash
npm run dev
npm run build
```
