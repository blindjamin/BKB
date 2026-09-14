# apps/web · Sitio Público de BKB (Astro)

Aplicación web estática construida con **Astro 5+**, diseñada con cero JavaScript por defecto en el cliente, alta accesibilidad (WCAG 2.2 AA) y rendimiento superior (Lighthouse ≥ 95).

## Estructura de Páginas
- `src/pages/index.astro`: Portada principal, propuesta de valor de ingeniería, métricas clave y llamada al portal.
- `src/pages/servicios.astro`: Catálogo de 5 especialidades (Ingeniería, Tableros TDF/TDA, Automatización PLC, Obras Civiles Eléctricas, Mantención y SEC TE1).
- `src/pages/obras.astro`: Portafolio industrial de proyectos destacados en Chile con etiquetas técnicas.
- `src/pages/nosotros.astro`: Historia de BKB desde 1999, valores de faena, seguridad LOTO y sectores atendidos.
- `src/pages/contacto.astro`: Formulario de cotización con campo trampa anti-spam y contacto directo.
- `src/pages/trabaja-con-nosotros.astro`: Portal de vacantes laborales y recepción de CV con consentimiento explícito bajo Ley 21.719.
- `src/pages/privacidad.astro`: Política de Privacidad de datos personales (Ley 21.719).
- `src/pages/terminos.astro`: Términos del servicio.

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
