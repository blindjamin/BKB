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
