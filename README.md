# BKB Platform — Monorepo

Repositorio central del ecosistema digital de **BKB Obras Eléctricas & Servicios**.

## Arquitectura del Monorepo

```
bkb-platform/
├── apps/
│   ├── web/        # Sitio público estático: landing de una página (Astro 5, Tailwind v4, WCAG 2.2 AA)
│   └── portal/     # Portal de archivos por proyecto, con roles (Django 5.2 LTS, PostgreSQL, Spaces). En construcción
├── packages/
│   └── tokens/     # Sistema de diseño y tokens CSS v2 (paleta salmón, temas oscuro y claro)
├── docs/           # Memoria técnica y contexto para IAs y desarrolladores
└── tasks/          # Plan de implementación y lista de tareas del portal
```

## Guía Rápida de Comandos

```bash
# Instalar todas las dependencias del monorepo
npm install

# Iniciar sitio web en desarrollo (puerto 3000)
npm run dev:web

# Compilar sitio web para producción
npm run build:web

# Previsualizar compilación
npm run preview:web
```

El portal (Django) tiene su propio entorno Python. Ver [apps/portal/README.md](apps/portal/README.md).

## Documentación y Contexto para IAs

Para asegurar la continuidad del proyecto al cambiar de modelo de lenguaje, asistente o desarrollador, consulte los archivos detallados en `docs/`:

- [00-contexto-proyecto.md](docs/00-contexto-proyecto.md): Propósito, actores, estado actual y pendientes.
- [01-tokens-y-sistema-diseno.md](docs/01-tokens-y-sistema-diseno.md): Paleta, temas, contraste y tipografía (v2).
- [02-sitio-web-astro.md](docs/02-sitio-web-astro.md): Arquitectura del sitio público, rutas y componentes.
- [03-portal-django.md](docs/03-portal-django.md): **Especificación del portal de archivos**: roles, visibilidad, modelo de datos, Space y criterios de éxito.
- [04-seguridad-y-cumplimiento.md](docs/04-seguridad-y-cumplimiento.md): Ley 21.719, controles de seguridad y manejo de archivos.
- [05-git-workflow.md](docs/05-git-workflow.md): Política estricta de ramas y despliegue a `desarrollo`.
- [06-bitacora-avances.md](docs/06-bitacora-avances.md): Bitácora cronológica de sesiones y próximos pasos.
- [08-plan-rediseno-landing.md](docs/08-plan-rediseno-landing.md): Plan de rediseño de la landing según el handoff de Claude Design.

Para el portal: [tasks/plan.md](tasks/plan.md) (decisiones, riesgos y orden) y [tasks/todo.md](tasks/todo.md) (17 tareas con criterios de aceptación).
