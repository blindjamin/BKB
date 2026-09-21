# 00 · Contexto del Proyecto BKB

> **Nota para IAs y nuevos desarrolladores:**  
> Este documento resume el propósito, negocio, actores y decisiones estratégicas de la plataforma BKB. Léalo antes de realizar cualquier cambio arquitectónico.

---

## 1. ¿Qué es BKB?
**BKB Obras Eléctricas & Servicios** es una empresa chilena de ingeniería eléctrica industrial con más de 25 años de trayectoria (fundada en 1999). Sus principales áreas de negocio son:
1. **Montaje de Tableros Eléctricos:** Tableros de Distribución de Fuerza (TDF), Tableros de Alumbrado (TDA) y Centros de Control de Motores (CCM).
2. **Automatización y Control:** Programación de autómatas PLC (Siemens, Schneider, Allen-Bradley), telemetría y SCADA.
3. **Obras Civiles Eléctricas:** Tendido de escalerillas portacables, mallas de puesta a tierra y salas eléctricas.
4. **Regularizaciones Normativas:** Tramitación y obtención de declaraciones eléctricas **SEC TE1** (Superintendencia de Electricidad y Combustibles), contando con categoría máxima **SEC Clase A**.
5. **Mantención Industrial:** Termografía infrarroja certificada, ajuste de torque y guardia técnica 24/7.

> **Pendiente de definir:** el logo nuevo dice "Ingeniería Eléctrica & Servicios", pero los documentos y la metadata dicen "Obras Eléctricas & Servicios". Hay que decidir cuál es el nombre oficial (afecta `<title>`, Schema.org y footer). Ver lista D7 en `08-plan-rediseno-landing.md`.

---

## 2. Los Dos Productos Digitales
Son dos aplicaciones con objetivos distintos y técnicamente desacopladas:

1. **Sitio Público (`www.empresabkb.cl`):**
   - **Objetivo:** vender la empresa y generar confianza en futuros clientes corporativos (imagen profesional y llamativa), recibir solicitudes de cotización y postulaciones (CV), y posicionarse en buscadores.
   - **Tecnología:** Astro 5 (salida estática), Tailwind CSS v4 y `@bkb/tokens`. Sin servidor.
   - **Estado:** landing rediseñada en una sola página, aún no aprobada del todo.
   - **Hosting:** hoy se previsualiza en GitHub Pages; el destino es DigitalOcean App Platform (sitio estático).

2. **Portal de Archivos (`portal.empresabkb.cl`):**
   - **Objetivo:** que el personal de BKB suba los documentos y las fotos de cada proyecto en marcha, y que los clientes los consulten y descarguen, cada uno solo en los proyectos que se le asignan. **Es el propósito principal de la plataforma.**
   - **Tecnología:** Django 5.2 LTS, plantillas en servidor, PostgreSQL y los archivos en un DigitalOcean Space privado (`bkb-space`).
   - **Estado:** solo existe el esqueleto. La especificación está aprobada y el plan de implementación escrito (ver `03-portal-django.md` y `tasks/plan.md`).
   - **Hosting:** DigitalOcean App Platform, una sola instancia, más PostgreSQL gestionado.

---

## 3. Principales Actores y Roles
- **Visitante / Mandante potencial:** navega el sitio público, consulta especialidades y envía la solicitud de cotización o su postulación laboral.
- **Personal de BKB (portal):** ve todos los proyectos y archivos y es quien sube documentos y fotos. Lo que sube se ve de inmediato para los clientes del proyecto, y puede borrar lo que él mismo subió.
- **Cliente (portal):** entra con correo y contraseña. Solo ve y descarga los archivos de los proyectos que se le asignan. No puede subir.
- **Administrador (portal):** superusuario de Django (por ahora una sola persona). Crea usuarios, empresas, proyectos y asignaciones desde el panel, y puede borrar cualquier archivo.

---

## 4. Estado Actual del Repositorio (al 20-09-2026)
- **Estructura:** monorepo con `npm workspaces` en `bkb-platform/`.
- **Sistema de diseño (`packages/tokens`):** v2.0.0, paleta salmón, temas oscuro y claro, y semáforo normativo SEC (que usará el portal). Ver `01-tokens-y-sistema-diseno.md`.
- **Sitio público (`apps/web`):** landing de una página (Hero, Clientes, Servicios, Métricas, Mercados, Portafolio, Portal SEC y Cotización) más `/trabaja-con-nosotros`, `/privacidad`, `/terminos` y `404`. Las rutas antiguas (`/servicios`, `/obras`, `/nosotros`, `/contacto`) redirigen a su ancla. Ver `02-sitio-web-astro.md`.
- **Portal (`apps/portal`):** esqueleto de Django (`config/` y `/health/`). Sin modelos ni pantallas todavía. Spec en `03-portal-django.md`, plan en `tasks/plan.md` y tareas en `tasks/todo.md`.
- **Despliegue continuo:** GitHub Action que publica el sitio estático en GitHub Pages (`https://blindjamin.github.io/BKB/`) tras cada merge a `desarrollo`.
- **Jerarquía Git:** `main` (producción) → `desarrollo` (integración) → ramas de tarea `[nombre]/[fecha]-[descripcion]` con Pull Request manual. Ver `05-git-workflow.md`.
- **Ramas relevantes:** `benjamin/2026-09-15-rediseno-landing` contiene el rediseño de la landing y ya está subida a GitHub. El trabajo del portal parte en ramas nuevas desde `desarrollo`.

### Pendientes abiertos
- **Landing:** validar el contenido D7 (origen de las fotos, autorización de los 16 logos de clientes, nombre oficial, métricas, obras y datos de contacto) y verificar las fases 8 a 10 del plan de rediseño.
- **Formulario de cotización:** no tiene endpoint. El botón queda deshabilitado hasta definir `PUBLIC_QUOTE_ENDPOINT`.
- **Portal:** crear la clave de acceso del Space solo para el portal y configurar CORS. El DNS de `empresabkb.cl` está en DigitalOcean: `portal.empresabkb.cl` se crea ahí en el despliegue.
