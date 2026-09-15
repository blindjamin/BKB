# BKB Platform — Monorepo

Repositorio central del ecosistema digital de **BKB Obras Eléctricas & Servicios**.

## Arquitectura del Monorepo

```
bkb-platform/
├── apps/
│   ├── web/        # Sitio web público estático (Astro 5+, Tailwind, WCAG 2.2 AA)
│   └── portal/     # Portal documental seguro para clientes (Django, PostgreSQL, Spaces)
├── packages/
│   └── tokens/     # Sistema de diseño y tokens CSS oficiales (UI Kit v1.0)
└── docs/           # Memoria técnica completa y contexto para IAs y desarrolladores
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

## Documentación y Contexto para IAs

Para asegurar la continuidad del proyecto al cambiar de modelo de lenguaje, asistente o desarrollador, consulte los archivos detallados en `docs/`:

- [00-contexto-proyecto.md](docs/00-contexto-proyecto.md): Propósito, historia y objetivos.
- [01-tokens-y-sistema-diseno.md](docs/01-tokens-y-sistema-diseno.md): Colores, fuentes y componentes.
- [02-sitio-web-astro.md](docs/02-sitio-web-astro.md): Arquitectura del sitio público y rutas.
- [03-portal-django.md](docs/03-portal-django.md): Backend, modelo de datos y permisos ASVS.
- [04-seguridad-y-cumplimiento.md](docs/04-seguridad-y-cumplimiento.md): Ley 21.719, CSP y URLs prefirmadas.
- [05-git-workflow.md](docs/05-git-workflow.md): Política estricta de ramas y despliegue a `desarrollo`.
- [06-bitacora-avances.md](docs/06-bitacora-avances.md): Bitácora cronológica de sesiones y próximos pasos.
