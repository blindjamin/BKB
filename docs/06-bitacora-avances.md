# 06 · Bitácora Cronológica de Avances

> **Propósito de este archivo:**  
> Servir de memoria de trabajo para el equipo y para cualquier modelo de Inteligencia Artificial que retome el proyecto.  
> Cada sesión de trabajo debe cerrar con un nuevo registro fechado que resuma los avances y defina el punto de partida del día siguiente.

---

## Sesión 1 · 14 de Septiembre de 2026

### 1. Resumen de la Jornada
- **Alineación de Requerimientos:** Se ejecutó el proceso de `/grill-me` acordando arquitectura monorepo, tokens oficiales de UI Kit v1.0, sistema dual de documentación, y política estricta de ramas Git.
- **Creación de la Plataforma Base:** Se creó la subcarpeta `bkb-platform/` con workspaces de npm, configurando `.gitignore` y scripts de desarrollo.
- **Tokens de Diseño (`packages/tokens`):**
  - Implementación de variables CSS de marca (`copper-700 #B4470F`, `paper-50 #FBF8F5`, `ink-900 #1A1513`), tipografías (`Space Grotesk`, `IBM Plex Sans`, `IBM Plex Mono`) y semáforo normativo SEC.
- **Sitio Público (`apps/web`):**
  - Configuración con Astro 5+ en modo estático (`output: 'static'`).
  - Maquetación y desarrollo de las 8 rutas requeridas:
    - `/` (Inicio): Hero con titular industrial, badge SEC Clase A, 4 métricas de faena, banner del portal y CTA.
    - `/servicios`: Catálogo técnico de 5 especialidades (`SRV-01` a `SRV-05`) con checklists de alcance.
    - `/obras`: Portafolio de proyectos industriales con ubicaciones, etiquetas técnicas y credenciales.
    - `/nosotros`: Historia de BKB desde 1999, pilares de ejecución y sectores atendidos.
    - `/contacto`: Formulario estructurado con campo trampa honeypot anti-spam.
    - `/trabaja-con-nosotros`: Convocatorias y recepción de CVs cumpliendo con la Ley 21.719 de datos personales.
    - `/privacidad` y `/terminos`: Documentos legales adaptados al marco normativo chileno.
- **Integración de Estilos y Galería Fotográfica:**
  - Instalación e integración de Tailwind CSS v4 (`@tailwindcss/vite`).
  - Migración de 12 fotografías y planos reales a `apps/web/public/assets/images/`.
  - Hero actualizado con layout de 2 columnas y fotografía de faena (`hero-tablero.jpg`).
  - Tarjetas de obras y servicios enriquecidas con vistas previas fotográficas reales.
- **Portal de Clientes (`apps/portal`):**
  - Estructuración base en Django con configuración de seguridad ASVS Nivel 2 (Argon2id, cookies seguras, CSP, endpoint `/health/`).
  - Soporte dual para base de datos SQLite (desarrollo local) y PostgreSQL (producción).
- **Despliegue Continuo (CI/CD):**
  - Creación del workflow `.github/workflows/deploy-pages.yml` para publicación automática en GitHub Pages (`https://blindjamin.github.io/BKB/`).
  - Creación del helper `apps/web/src/utils/paths.ts` para resolución automática de rutas en local (`/`) y Pages (`/BKB/`).
- **Configuración de Git y Repositorio Remoto:**
  - Repositorio remoto vinculado: `https://github.com/blindjamin/BKB.git`.
  - Estructura de 3 niveles establecida:
    1. `main` (Producción)
    2. `desarrollo` (Integración activa)
    3. `[nombre]/[fecha]-[descripcion]` (Ramas de trabajo con Pull Request manual a `desarrollo`).

---

### 2. Estado de Ramas al Cierre del Día
- `main`: Establecida en GitHub (`origin/main`).
- `desarrollo`: Al día con la configuración base y el workflow de GitHub Pages (`origin/desarrollo`).
- `benjamin/2026-09-14-estilos-tailwind-web`: Rama con Tailwind v4 y fotografías de faena.
  - **Pull Request pendiente de merge manual por el usuario:**  
    [Ver Pull Request en GitHub](https://github.com/blindjamin/BKB/pull/new/benjamin/2026-09-14-estilos-tailwind-web).

---

### 3. Plan y Punto de Partida para Mañana (Sesión 2)

Cuando se retome el trabajo en la siguiente sesión, la IA o desarrollador debe realizar lo siguiente:

1. **Paso 1 · Verificar fusión del PR de estilos:**
   - Confirmar si el usuario ya aprobó y fusionó `benjamin/2026-09-14-estilos-tailwind-web` en `desarrollo`.
   - Si ya está fusionado: hacer `git checkout desarrollo && git pull origin desarrollo`.
2. **Paso 2 · Selección de siguiente bloque:**
   - **Opción A (Backend Portal):** Crear la rama `benjamin/YYYY-MM-DD-modelos-portal-django`, levantar el entorno virtual Python (`.venv`), instalar `requirements.txt`, definir los modelos `Empresa`, `Obra`, `Documento` y `DescargaLog`, y registrar el admin de Django.
   - **Opción B (Formularios y Funcionalidad Web):** Conectar los formularios de `/contacto` y `/trabaja-con-nosotros` con un backend serverless, endpoint de correo o Google Workspace relay, incorporando protección Cloudflare Turnstile.
3. **Paso 3 · Recordar protocolo:**
   - Crear siempre rama de tarea `benjamin/YYYY-MM-DD-descripcion`.
   - Push a la rama de tarea.
   - Entregar enlace de Pull Request al usuario para merge manual a `desarrollo`.

---

## Sesión 2 · 15 de Septiembre de 2026

### Resumen
- **Revisión del sitio:** se detectaron 10 pendientes (formularios que enviaban datos por la URL, header roto entre 1024 y 1240 px, contenido de relleno y otros). Se documentaron y el plan de rediseño los resolvió.
- **Corrección del portal:** `requirements.txt` pasó a usar el paquete correcto `rules`.
- **Handoff de Claude Design:** se incorporó a `docs/design/handoff-landing/` y se escribió `08-plan-rediseno-landing.md`.
- **Rediseño implementado** en la rama `benjamin/2026-09-15-rediseno-landing` (ya subida a GitHub), en 4 commits:
  1. Tokens v2: paleta salmón y temas oscuro y claro.
  2. Layout v2, header con menú móvil y footer oscuro.
  3. Landing ensamblada con animaciones, componentes de interfaz e imágenes.
  4. Redirecciones de las rutas antiguas, páginas legales reestilizadas, limpieza y control de calidad.

### Punto de partida
Verificar las fases 8 a 10 del plan 08 y validar el contenido de la lista D7.

---

## Sesión 3 · 20 de Septiembre de 2026

### Resumen
- **Definición del portal:** por entrevista se acordó que el portal es un repositorio de documentos y fotos por proyecto, con tres roles (admin, funcionario, cliente). Lo que sube el cliente es visible de inmediato para todo el proyecto. Lo que sube un funcionario queda interno hasta que se comparte.
- **Especificación aprobada:** `docs/03-portal-django.md` (sustituye al diseño anterior, en que el cliente no subía archivos).
- **Plan de implementación:** `tasks/plan.md` y `tasks/todo.md` (17 tareas en 4 fases, con checkpoints).
- **Decisiones técnicas:** Django 5.2 LTS (el entorno local traía 6.1.1), sin `pytest` (corredor de Django), se quitan `django-htmx`, `rules` y `django-allauth`, CSS propio con tokens en el portal, tema claro por defecto con conmutador, y los archivos antiguos del Space se dejan donde están (el portal usa el prefijo `portal/`).
- **Limpieza:** se eliminaron `docs/07` (revisión ya resuelta por el rediseño), las copias `scratch_buenosvientos.*` (sitio ajeno), `Handoff de pagina.zip` (idéntico a `docs/design/handoff-landing/`) y `UI Kit/BKB UI Kit completo.zip` (copia anterior a la carpeta).
- **Documentación actualizada:** `00`, `01`, `02`, `03`, `04`, `05`, `08` y los README del monorepo y del portal.

### Punto de partida para la próxima sesión
1. Crear la rama del portal desde `desarrollo` (tarea 0) y confirmar la limpieza y actualización de documentos.
2. Antes de la tarea 6, crear en DigitalOcean una clave del Space solo para el portal y configurar CORS.
3. Empezar por las tareas 1 y 2 (entorno y `settings.py`) y seguir el orden de `tasks/todo.md`.

---

## Sesión 4 · 21 de Septiembre de 2026

### Resumen
- **Cambio de requisito:** BKB indicó que el cliente **no puede subir archivos**, solo verlos. Se decidió: dos tipos de usuario (personal y cliente), sin marca interno/compartido (lo que sube el personal se ve de inmediato), el personal ve todos los proyectos y el cliente solo los que se le asignan. El administrador es el superusuario de Django.
- **Spec v1.1** (`docs/03-portal-django.md`) y plan reescritos: de 17 a **16 tareas**. Se eliminó la tarea "Compartir con el cliente", se achicó la matriz de permisos y la subida pasó a ir antes que la descarga. El antivirus dejó de ser condición del lanzamiento.
- **Documentación actualizada:** `00`, `03`, `04`, `tasks/plan.md`, `tasks/todo.md`, el README del portal y la nota de vigencia de `Plan-Implementacion-BKB.md`.

### Punto de partida
Igual que la sesión 3. Decisión posterior del mismo día: **el personal puede borrar lo que él subió y el administrador cualquier archivo** (el cliente nunca). Como el personal no entra al panel de Django, se agregó al plan la tarea 14 "Borrar lo propio": el plan queda en **17 tareas**.
