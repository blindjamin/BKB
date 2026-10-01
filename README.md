# BKB Platform — Monorepo

Repositorio central del ecosistema digital de **BKB Obras Eléctricas & Servicios**.

## Arquitectura del Monorepo

```
bkb-platform/
├── apps/
│   ├── web/        # Sitio público estático (Astro 5, Tailwind v4, WCAG 2.2 AA): landing, /arriendo y páginas legales
│   └── portal/     # Portal de proyectos con roles (Django 5.2 LTS, PostgreSQL, Spaces). Listo en local, sin desplegar
├── packages/
│   └── tokens/     # Sistema de diseño y tokens CSS (tema claro grafito y naranjo, tema oscuro)
├── docs/           # Memoria técnica y contexto para IAs y desarrolladores
├── tasks/todo.md   # Pendientes actuales, en orden
└── .do/app.yaml    # Especificación de DigitalOcean App Platform para el portal
```

## Estado actual (01-10-2026)

- **Sitio público (`apps/web`):** landing de una página (hero con carrusel de clientes, "Qué hacemos" con fotos reales, mercados, portafolio, testimonios provisorios, contacto con mapa y formulario "Cotizar obra" que llega a ingeniería), `/arriendo` (10 equipos, cotización por WhatsApp), `/trabaja-con-nosotros`, `/privacidad`, `/terminos` y `404`. Se publica en GitHub Pages (`https://blindjamin.github.io/BKB/`) con cada push a `desarrollo`.
- **Portal (`apps/portal`):** empresas → proyectos → carpetas, tres tipos de usuario (personal, jefe y cliente) y los 4 módulos de `docs/11`:
  1. **Encargados:** encargado cliente por empresa y proyecto, encargados BKB; solo ellos y el jefe editan.
  2. **Avance:** 7 hitos estándar con fechas; el cliente acepta o rechaza la Revisión y ve los archivos solo al finalizar.
  3. **Avisos:** correos HTML de inicio, término y rechazo (`manage.py vista_correos` para verlos).
  4. **Modificaciones:** se envían al cliente con adjuntos o enlaces, se responden desde un enlace firmado y tienen recordatorios (`manage.py enviar_recordatorios`, job diario en `.do/app.yaml`).
- **Ramas:** todo lo anterior está fusionado en `desarrollo` y en `main` (PR #21).

## Pendientes

Lista única y ordenada en [tasks/todo.md](tasks/todo.md): decidir 3 alertas de seguridad, verificación manual, despliegue del portal (tarea 16), piloto (tarea 17) y contenido de la landing.

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

## Flujo de trabajo

Ramas cortas `[nombre]/[fecha]-[descripcion]` desde `desarrollo` y Pull Request de vuelta a `desarrollo`; `main` es producción. Ver [05-git-workflow.md](docs/05-git-workflow.md).

## Documentación y Contexto para IAs

Para asegurar la continuidad del proyecto al cambiar de modelo de lenguaje, asistente o desarrollador, consulte los archivos detallados en `docs/`:

- [00-contexto-proyecto.md](docs/00-contexto-proyecto.md): Propósito, actores, estado actual y pendientes.
- [01-tokens-y-sistema-diseno.md](docs/01-tokens-y-sistema-diseno.md): Paleta, temas, contraste y tipografía.
- [02-sitio-web-astro.md](docs/02-sitio-web-astro.md): Arquitectura del sitio público, rutas y componentes.
- [03-portal-django.md](docs/03-portal-django.md): **Especificación del portal**: roles, visibilidad, modelo de datos, Space y criterios de éxito.
- [04-seguridad-y-cumplimiento.md](docs/04-seguridad-y-cumplimiento.md): Ley 21.719, controles de seguridad y manejo de archivos.
- [05-git-workflow.md](docs/05-git-workflow.md): Política de ramas y despliegue a `desarrollo`.
- [06-bitacora-avances.md](docs/06-bitacora-avances.md): Bitácora cronológica de sesiones y próximos pasos.
- [11-spec-avance-y-modificaciones.md](docs/11-spec-avance-y-modificaciones.md): Spec de encargados, avance, avisos y modificaciones del portal.

